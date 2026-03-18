"""Core functions for pycisTarget and the SCENIC tool suite."""

import contextlib

from importlib.metadata import PackageNotFoundError, version

with contextlib.suppress(PackageNotFoundError):
    __version__ = version("ctxcore")