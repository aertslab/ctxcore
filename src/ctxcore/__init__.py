"""
Core functions for pycisTarget and the SCENIC tool suite
"""

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution("ctxcore").version
except DistributionNotFound:
    pass
