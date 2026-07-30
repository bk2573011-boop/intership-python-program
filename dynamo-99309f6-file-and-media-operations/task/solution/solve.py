"""Solution for the Dynamo file-and-media-operations task.

Extract /app/data/archive.zip and group .txt/.jpg/.csv files into separate
.tar.gz archives under /app/output/.
"""

from __future__ import annotations

import os
import shutil
import tarfile
import zipfile
from typing import Dict, List


ZIP_PATH = "/app/data/archive.zip"
OUT_DIR = "/app/output"
EXTRACT_DIR = "/tmp/extracted"

EXTENSION_MAP: Dict[str, str] = {
    ".txt": os.path.join(OUT_DIR, "text_files.tar.gz"),
    ".jpg": os.path.join(OUT_DIR, "image_files.tar.gz"),
    ".csv": os.path.join(OUT_DIR, "data_files.tar.gz"),
}


def _collect_files(root: str, extension: str) -> List[str]:
    """Return absolute paths of files below ``root`` ending in ``extension``."""
    collected: List[str] = []
    if not os.path.exists(root):
        return collected
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(extension):
                collected.append(os.path.join(dirpath, name))
    return collected


def _build_tar(tar_path: str, files: List[str]) -> None:
    """Create a gzipped tar containing each file using its basename."""
    os.makedirs(os.path.dirname(tar_path), exist_ok=True)
    with tarfile.open(tar_path, "w:gz") as tar:
        for full_path in files:
            tar.add(full_path, arcname=os.path.basename(full_path))


def process_archive(
    zip_path: str = ZIP_PATH,
    out_dir: str = OUT_DIR,
    extract_dir: str = EXTRACT_DIR,
    extension_map: Dict[str, str] | None = None,
) -> Dict[str, int]:
    """Extract the zip and build per-extension tar.gz files.

    When ``extension_map`` is ``None``, the tarball paths are derived from
    ``out_dir`` using the canonical mapping:
        .txt -> <out_dir>/text_files.tar.gz
        .jpg -> <out_dir>/image_files.tar.gz
        .csv -> <out_dir>/data_files.tar.gz

    Returns:
        A mapping of extension -> number of files packed into the tarball.
    """
    if extension_map is None:
        ext_map: Dict[str, str] = {
            ".txt": os.path.join(out_dir, "text_files.tar.gz"),
            ".jpg": os.path.join(out_dir, "image_files.tar.gz"),
            ".csv": os.path.join(out_dir, "data_files.tar.gz"),
        }
    else:
        ext_map = dict(extension_map)
    os.makedirs(out_dir, exist_ok=True)

    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)

    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

    counts: Dict[str, int] = {}
    for ext, tar_path in ext_map.items():
        files = _collect_files(extract_dir, ext)
        _build_tar(tar_path, files)
        counts[ext] = len(files)
    return counts


if __name__ == "__main__":
    result = process_archive()
    for ext, count in result.items():
        print(f"{ext}: {count} file(s) archived")
