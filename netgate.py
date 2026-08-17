#!/usr/bin/env python3
"""netgate.py — pause a transfer when the signal dies. Never abort.

Cody's spec, 2026-08-17: "it doesn't even need to know the shape of the
interruption... just if the signal dies, it pauses the download and quietly
waits... until the signal returns."

So this class deliberately does NOT classify interruptions. It does not care
whether you switched from wifi to tethering, suspended the laptop, walked out of
range, or the far end hiccuped. It asks one question -- **is the signal up?** --
and if not, it sleeps and asks again later.

WHY PAUSING BEATS RESTARTING

Restarting re-runs the whole query stage. For the JWST downloader that means a
fresh MAST observation query plus ~20 batched product-list calls, which took
about three minutes of wall time and real server load, before a single byte moves.
Pausing keeps the process alive and the product list in memory, so resumption
costs one TCP handshake. That is the "less computationally intensive" part.

DESIGN

  probe        one TCP connect to the host you are actually talking to. No DNS
               lookup of a third party, no ICMP, no HTTP request. Cheapest
               liveness signal that means anything.
  quiet        logs only STATE TRANSITIONS (up->down, down->up) and a heartbeat
               at long intervals. A backgrounded process that waits six hours
               should not produce six hours of log.
  backoff      exponential from min_wait to max_wait. While down, the loop costs
               one socket attempt per interval -- effectively zero CPU.
  patience     unbounded by default. It waits as long as it takes.

  The one guard against a true infinite loop: if the signal is UP and repeated
  attempts still make no progress, that is not a network problem, and the caller
  is told to give up on that item (see ``no_progress_limit``).

USAGE

    gate = NetworkGate('mast.stsci.edu', 443)

    while True:
        try:
            ...stream some bytes...
            break
        except Exception as e:
            if not gate.pause(e, progressed=(bytes_now > bytes_before)):
                raise                      # real error, or truly stuck
            continue                       # signal returned; retry/resume
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional, Tuple

__all__ = ['NetworkGate', 'GateStats', 'NETWORK_ERRORS']

#: Exception types treated as "possibly the signal". Kept deliberately broad --
#: the point of this class is NOT to classify interruptions. requests wraps most
#: transport failures in its own hierarchy, so it is imported lazily and its base
#: class added if available.
NETWORK_ERRORS: Tuple[type, ...] = (OSError, socket.timeout, socket.gaierror)

try:                                        # pragma: no cover - optional dep
    import requests as _rq
    NETWORK_ERRORS = NETWORK_ERRORS + (_rq.exceptions.RequestException,)
except Exception:                           # pragma: no cover
    pass


@dataclass
class GateStats:
    """What the gate did, for the end-of-run report."""
    pauses:          int = 0
    paused_seconds:  float = 0.0
    longest_pause:   float = 0.0
    retries:         int = 0
    no_progress_run: int = 0

    def __str__(self) -> str:
        return (f'{self.pauses} pause(s), {self.paused_seconds:.0f}s total '
                f'waiting, longest {self.longest_pause:.0f}s, '
                f'{self.retries} retries')


class NetworkGate:
    """Blocks while the signal is down. Returns when it is back.

    :param host: the host you are actually transferring from.
    :param port: TCP port to probe (443 for https).
    :param probe_timeout: seconds to allow a single connect attempt.
    :param min_wait: first backoff interval.
    :param max_wait: backoff ceiling -- the steady-state poll interval.
    :param heartbeat: while down, emit one log line no more often than this.
    :param no_progress_limit: consecutive retries that make no progress *while
        the signal is up* before the gate advises giving up. ``None`` = never
        give up.
    :param log: callable taking one string. Defaults to a timestamped print.
    """

    def __init__(self, host: str, port: int = 443, *,
                 probe_timeout: float = 5.0,
                 min_wait: float = 5.0,
                 max_wait: float = 300.0,
                 heartbeat: float = 900.0,
                 no_progress_limit: Optional[int] = 6,
                 log: Optional[Callable[[str], None]] = None) -> None:
        self.host = host
        self.port = int(port)
        self.probe_timeout = float(probe_timeout)
        self.min_wait = float(min_wait)
        self.max_wait = float(max_wait)
        self.heartbeat = float(heartbeat)
        self.no_progress_limit = no_progress_limit
        self._log = log or self._default_log
        self.stats = GateStats()
        self._was_up: Optional[bool] = None

    # -- logging -----------------------------------------------------------
    @staticmethod
    def _default_log(msg: str) -> None:
        print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}', flush=True)

    # -- the probe ---------------------------------------------------------
    def is_up(self) -> bool:
        """One TCP connect to the target host. True if it completes.

        Not a ping and not an HTTP request: a connect is the cheapest thing that
        actually proves a route to the host you care about exists. A captive
        portal or a half-open wifi association will fail this, which is correct
        -- those are exactly the "switched networks" cases.
        """
        try:
            with socket.create_connection((self.host, self.port),
                                          timeout=self.probe_timeout):
                return True
        except OSError:
            return False

    # -- the wait ----------------------------------------------------------
    def wait_until_up(self) -> float:
        """Block until the probe succeeds. Quiet. Returns seconds waited.

        Logs the down transition once, then at most one heartbeat per
        ``heartbeat`` seconds, then the up transition. Nothing else.
        """
        if self.is_up():
            return 0.0

        t0 = time.monotonic()
        self._log(f'signal DOWN ({self.host}:{self.port}) — pausing, will wait')
        wait = self.min_wait
        last_beat = time.monotonic()
        while True:
            time.sleep(wait)
            if self.is_up():
                waited = time.monotonic() - t0
                self._log(f'signal UP — resuming after {waited:.0f}s paused')
                return waited
            now = time.monotonic()
            if now - last_beat >= self.heartbeat:
                self._log(f'still waiting — {(now - t0) / 60:.0f} min paused')
                last_beat = now
            wait = min(wait * 2.0, self.max_wait)

    # -- the caller's entry point ------------------------------------------
    def pause(self, exc: Optional[BaseException] = None, *,
              progressed: bool = False) -> bool:
        """Handle an interruption. Returns True if the caller should retry.

        Deliberately does not inspect ``exc``. The decision procedure is:

        1. Is the signal down? -> wait for it, then retry. Unbounded patience.
        2. Signal is up. Did we make progress since last time? -> short backoff
           and retry; a slow or flaky far end is still worth retrying.
        3. Signal is up and no progress, ``no_progress_limit`` times running ->
           return False. This is not a network problem and waiting cannot fix it.

        :param exc: the exception that interrupted, for logging only.
        :param progressed: True if bytes moved since the previous attempt.
        :returns: True = retry, False = give up on this item.
        """
        if progressed:
            self.stats.no_progress_run = 0

        if not self.is_up():
            waited = self.wait_until_up()
            self.stats.pauses += 1
            self.stats.paused_seconds += waited
            self.stats.longest_pause = max(self.stats.longest_pause, waited)
            self.stats.retries += 1
            return True

        # signal is up, so this was not the network
        if not progressed:
            self.stats.no_progress_run += 1
            if (self.no_progress_limit is not None
                    and self.stats.no_progress_run >= self.no_progress_limit):
                self._log(f'signal is UP but {self.stats.no_progress_run} attempts '
                          f'made no progress — not a network fault, giving up'
                          + (f' ({type(exc).__name__}: {exc})' if exc else ''))
                return False
        self.stats.retries += 1
        time.sleep(min(self.min_wait * self.stats.no_progress_run or self.min_wait,
                       self.max_wait))
        return True

    # -- convenience -------------------------------------------------------
    def guard(self, fn: Callable, *args, **kwargs):
        """Call ``fn``, pausing and retrying while the signal is down.

        Only for operations that are safe to repeat. Streaming downloads should
        drive :meth:`pause` directly so they can resume from a byte offset rather
        than restarting the transfer.
        """
        while True:
            try:
                return fn(*args, **kwargs)
            except NETWORK_ERRORS as e:
                if not self.pause(e):
                    raise

    def __repr__(self) -> str:
        return (f'<NetworkGate {self.host}:{self.port} '
                f'up={self._was_up} {self.stats}>')


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else 'mast.stsci.edu'
    g = NetworkGate(host, 443, min_wait=2.0, max_wait=30.0, heartbeat=20.0)
    print(f'probing {host}:443 ...')
    print(f'  is_up() -> {g.is_up()}')
    print('\nsimulating an interruption (pause with signal presumed up):')
    print(f'  pause(progressed=True) -> {g.pause(RuntimeError("test"), progressed=True)}')
    print(f'  stats: {g.stats}')
    print('\nTo watch a real pause: unplug the network and run')
    print(f'  python3 netgate.py {host}')
    print('It will log one DOWN line, heartbeat quietly, then one UP line.')
