# Installing BulletCluster

See the repository README. Use the `.venv`, never the system Python.

<!-- system-software:begin -->
## System software (not Python)

Programs this repository's own files call, found by scanning its source (`ValaQuenta/tools/repo_venv.py`). Install them with the system package manager; they are not pip packages.

| software | command | here | install |
|---|---|---|---|
| a C compiler (gcc, make) for the C code | `gcc` | installed | `sudo apt install build-essential` |
| git | `git` | installed | `sudo apt install git` |
| curl | `curl` | installed | `sudo apt install curl` |
<!-- system-software:end -->
