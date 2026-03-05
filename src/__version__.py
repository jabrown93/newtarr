"""
Version information for Newtarr.

This module provides version metadata for the application.
Import version information from here rather than hardcoding it elsewhere.
"""

__version__ = "0.0.5"
__version_info__ = (0, 0, 5, "patch")
__author__ = "jabrown93"
__license__ = "GPL-3.0"
__url__ = "https://github.com/jabrown93/newtarr"
__description__ = "Media hunting orchestration for *arr applications"


def get_version_string() -> str:
    """
    Get formatted version string for display.

    Returns:
        Formatted version string (e.g., "Newtarr v1.0.0")
    """
    return f"Newtarr v{__version__}"


def get_version_tuple() -> tuple:
    """
    Get version as a tuple for comparison.

    Returns:
        Version tuple (major, minor, patch, pre-release)
    """
    return __version_info__
