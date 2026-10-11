"""Compatibility shim for QuickUMLS' optional legacy leveldb backend.

QuickUMLS imports leveldb even when its database was created with the
unqlite backend. Reuse a real installation when one exists; on Windows with
Python 3.11 the module intentionally remains an empty shim because only the
unqlite backend is supported.
"""

from importlib.machinery import PathFinder
from importlib.util import module_from_spec
from pathlib import Path
import sys

_project_dir = Path(__file__).resolve().parent
_search_path = [
    entry for entry in sys.path
    if Path(entry or ".").resolve() != _project_dir
]
_spec = PathFinder.find_spec("leveldb", _search_path)
if _spec is not None and _spec.loader is not None:
    _module = module_from_spec(_spec)
    sys.modules[__name__] = _module
    _spec.loader.exec_module(_module)
    globals().update(_module.__dict__)
