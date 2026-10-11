"""Compatibility import for QuickUMLS on Windows/Python 3.11.

QuickUMLS imports ``quickumls_simstring``. The maintained ``pysimstring``
wheel exposes the same API from ``pysimstring.simstring`` without requiring
the obsolete Windows iconv library.
"""

from pysimstring import simstring

__all__ = ["simstring"]
