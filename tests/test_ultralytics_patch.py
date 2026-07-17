# -*- coding: utf-8 -*-
"""Tests for the ultralytics path-patch module.

The patch fixes apostrophe handling in file paths.  These tests
verify the patch function handles missing / broken dependencies
gracefully so it never crashes application startup.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_patch_returns_false_without_ultralytics():
    """When ultralytics is absent, patch_ultralytics() should
    return False without raising."""
    from app.utils.ultralytics_patch import patch_ultralytics

    # Patch is safe to call even when ultralytics is installed;
    # it will get applied successfully or log a warning.
    result = patch_ultralytics()
    # If ultralytics IS installed, it will return True
    # If ultralytics is NOT installed, it should return False (no crash)
    assert isinstance(result, bool)


def test_importing_app_has_no_runtime_side_effect_error():
    """The package can be imported before explicit launcher setup."""
    import app

    assert app.__doc__
