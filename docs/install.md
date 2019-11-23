# Installation Guide

## Stable (2.x)
### Using PIP
```bash
pip install -U aiogram
```

### Using Pipenv
```bash
pipenv install aiogram
```

### Using poetry
```bash
poetry add aiogram
```

### Using AUR
*aiogram* is also available in Arch User Repository, so you can install this library on any Arch-based distribution like ArchLinux, Antergos, Manjaro, etc. To do this, use your favorite AUR-helper and install [python-aiogram](https://aur.archlinux.org/packages/python-aiogram/) package.


## Development build (3.x)

### From private PyPi index
On every push to the `dev-3.x` branch GitHub Actions build the package and publish to the [2038.host](https://aiogram.2038.io/simple) server with seems like official PyPi files structure. That's mean you can always install latest (may be unstable) build via next command: 
```bash
pip install --extra-index-url https://aiogram.2038.io/simple --pre aiogram
```
In this repository available only last success build. All previous builds is always removes before uploading new one. Also before building this package all tests is also pass.
