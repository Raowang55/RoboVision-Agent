# -*- coding: utf-8 -*-
"""
Monkey-patch for ultralytics to fix apostrophe handling in file paths.

The original ultralytics.utils.downloads.attempt_download_asset() function
contains this line:
    file = Path(file.strip().replace("'", ""))

This removes ALL apostrophes from the path, which breaks paths like:
    C:/Users/rao'wang/...
turning it into:
    C:/Users/raowang/...

This patch fixes the issue by checking if the file exists locally FIRST,
before doing any path manipulation.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def patch_ultralytics():
    """Apply monkey-patch to ultralytics to fix apostrophe in paths."""
    try:
        from urllib import parse

        from ultralytics.utils import checks, downloads
        from ultralytics.utils.downloads import (
            GITHUB_ASSETS_STEMS,
            safe_download,
            url2file,
        )

        def patched_attempt_download_asset(file, repo='ultralytics/assets', release='latest', **kwargs):
            """
            Patched version that checks if file exists locally FIRST,
            before doing any path manipulation that strips apostrophes.
            """
            raw_file = Path(str(file)).expanduser()
            # Check the untouched path before Ultralytics normalizes filenames.
            if raw_file.is_file():
                return str(raw_file.resolve())

            file = checks.check_yolov5u_filename(str(file))

            # Only strip apostrophes from filename for download attempts
            file_path = Path(file)
            filename = file_path.name.replace("'", "")
            if file_path.parent != Path('.'):
                file = str(file_path.parent / filename)
            else:
                file = filename

            name = Path(parse.unquote(str(file))).name
            url = str(file).replace(":/", "://")
            file = url2file(name)

            if Path(file).is_file():
                return str(Path(file).resolve())

            if file in GITHUB_ASSETS_STEMS:
                download_url = f'https://github.com/{repo}/releases/download'
                safe_download(url=f'{download_url}/{release}/{name}', file=file, min_bytes=1e5, **kwargs)
                return str(Path(file).resolve())

            safe_download(url=url, file=file, min_bytes=1e5, **kwargs)
            return str(Path(file).resolve())

        downloads.attempt_download_asset = patched_attempt_download_asset
        logger.info('Applied ultralytics apostrophe patch')
        return True

    except Exception as e:
        logger.warning(f'Failed to apply ultralytics apostrophe patch: {e}')
        return False
