# VLA full-polarization Crab Nebula datasets to request from NRAO (2026-11-16)

Source: NRAO TAP (`tap_schema.obscore`), EVLA, `pol_states` containing RL (full cross-hand polarization), within 3' of the Crab. Read-only query; **no email or login was sent**; you request, then give me the links and I download them one at a time.
`access_estsize` in the archive overcounts (it is per row, not per dataset): real sizes show on the NRAO portal; I list scale only. Each line is one *execution block* (the unit the NRAO archive lets you request).

## A. First choice: same sky, same band, a time series (what you asked for: polarization over time)
| epoch | band (cm) | target name in archive | hours | execution block |
|---|---|---|---|---|
| 2012-08-20 | 6.5 | Crab J2000 | 4.0 | uid://evla/execblock/7e3183fb-bd32-430c-bb25-9b0d2fcda88d |
| 2012-08-26 | 6.5 | Crab J2000 | 3.9 | uid://evla/execblock/6cabf419-c681-40c9-a611-941398c87fbd |
| 2012-11-26 | 14.2 | Crab Nebula | 3.3 | uid://evla/execblock/503f83a8-0a1c-4011-808e-40a3e0ef813b |
| 2012-11-27 | 14.2 | Crab Nebula | 3.3 | uid://evla/execblock/5f07e182-5a7b-4e91-a2c0-dcc82e2e2afb |
| 2014-11-12 | 9.1 | crabnebula | 2.8 | uid://evla/execblock/f37df820-6c15-4aeb-aa00-a2080b789611 |
| 2014-11-12 | 23.5 | crabnebula | 2.8 | uid://evla/execblock/3e1763d4-f910-47dd-b8bd-ba3b51e32f03 |

## B. Second choice: the multi-band 2010–2011 set (wavelength dependence)
| epoch | band (cm) | hours | execution block |
|---|---|---|---|
| 2010-07-18 | 3.7 / 6.6 / 11.7 | 3.5 | uid://evla/execblock/11f7a75d-261c-4600-9051-cfa14725311d |
| 2010-08-07 | 3.7 / 6.6 / 11.7 | 6.6 | uid://evla/execblock/e758afd9-57f2-40e2-a8e7-b00bb0b716dd |
| 2010-12-02 | 3.7 / 6.6 / 11.7 | 6.6 | uid://evla/execblock/f0e4943c-be33-4f9d-96ff-a28cb47164dd |
| 2011-04-22 | 3.7 / 7.3 / 28.5 | 5.0 | uid://evla/execblock/957ab30c-3f4e-4a11-a9be-819e515b6785 |

## C. Third choice: high frequency (K/Ku band, 1.7 and 2.2 cm), very large
| 2014-10-19 | 2.2 | 3.5 | uid://evla/execblock/9f6372f8-616b-47bc-924b-34d7c5364ff7 |
| 2014-10-21 | 1.7 | 3.5 | uid://evla/execblock/fabe9781-ad8c-4520-87f9-fc52add51346 |

Not requested: 3C144 and Taurus A calibrator blocks (listed only for calibration), the 2016-2025 B0531+21 pulsar-timing blocks, the 2026 Crab/HOLORASTER pointing blocks, and the 2015B-305 block (circular RR/LL only, no cross-hand).
Order I would take them in: A first (6 blocks), tell me when they are ready, then B.
