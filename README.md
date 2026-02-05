# certo: Turn conversations into verifiable specifications.

> **⚠️ Experimental pre-release software.** APIs and formats may change without notice.

<p align="center">
  <a href="https://github.com/metaist/certo/actions/workflows/ci.yaml"><img alt="Build" src="https://img.shields.io/github/actions/workflow/status/metaist/certo/.github/workflows/ci.yaml?branch=main&logo=github"/></a>
  <a href="https://pypi.org/project/certo"><img alt="PyPI" src="https://img.shields.io/pypi/v/certo.svg?color=blue" /></a>
  <a href="https://pypi.org/project/certo"><img alt="Supported Python Versions" src="https://img.shields.io/pypi/pyversions/certo" /></a>
</p>

## Why?

AI-generated code is overwhelming human verification capacity. The gap between what humans intend and what code does has always existed, but it's now at a breaking point.

Certo bridges this gap by capturing intent through conversation, expanding it into testable implications, and checking code against those implications using multiple verification strategies.

## Install

```bash
pip install certo
# or
uv add certo
```

## Example

```bash
# Check your project against its blueprint
certo check

# Start an interview to capture intent
certo interview
```

## License

[MIT License](https://github.com/metaist/certo/blob/main/LICENSE.md)
