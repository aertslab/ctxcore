"""Core functions for pycisTarget and the SCENIC tool suite."""

import contextlib

from pkg_resources import DistributionNotFound, get_distribution

with contextlib.suppress(DistributionNotFound):
    __version__ = get_distribution("ctxcore").version
