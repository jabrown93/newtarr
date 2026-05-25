"""Test-package init. Runs once when any test module is loaded.

Production code touches `/config/...` at import time (auth.py does
`USER_DIR.mkdir`, utils/logger.py opens a FileHandler under /config/logs).
Patch both so importing the modules in a test environment without /config
falls back to a tempdir instead of crashing.
"""
import sys
import pathlib
import logging
import tempfile

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_TEST_DIR = pathlib.Path(tempfile.mkdtemp(prefix='newtarr-test-'))

_real_mkdir = pathlib.Path.mkdir


def _safe_mkdir(self, *args, **kwargs):
    try:
        return _real_mkdir(self, *args, **kwargs)
    except (PermissionError, OSError):
        return None


pathlib.Path.mkdir = _safe_mkdir

_real_fh_init = logging.FileHandler.__init__
_fallback_log = str(_TEST_DIR / 'fallback.log')


def _safe_fh_init(self, filename, *args, **kwargs):
    try:
        _real_fh_init(self, filename, *args, **kwargs)
    except (FileNotFoundError, PermissionError):
        _real_fh_init(self, _fallback_log, *args, **kwargs)


logging.FileHandler.__init__ = _safe_fh_init
