"""Project Dynamo verifier for mp4-ustar-repair task.

Asserts that the agent entrypoint produced all four required artifacts at the
canonical paths named in ``task.toml``, and that the validation report signals
successful ustar repairs, SHA match, and a passing ffprobe run.
"""

from __future__ import annotations

import json
import os
import tarfile

REPAIRED_TAR = "/app/output/repaired_archive.tar"
REPAIRED_MP4 = "/app/output/repaired_video.mp4"
REPORT_PATH = "/app/output/validation_report.json"
EXTRACT_DIR = "/app/output/extracted"


def test_artifact_files_and_directory_exist():
    outputs = [REPAIRED_TAR, REPAIRED_MP4, REPORT_PATH]
    for fp in outputs:
        assert os.path.isfile(fp), f"Missing expected artifact: {fp}"
    assert os.path.isdir(EXTRACT_DIR), f"Missing extracted directory: {EXTRACT_DIR}"


def test_repaired_tar_is_valid_ustar_tar():
    assert os.path.getsize(REPAIRED_TAR) % 512 == 0, "Tar must be block-aligned"
    with tarfile.open(REPAIRED_TAR, "r") as tf:
        members = tf.getmembers()
        names = [m.name for m in members]
        assert len(names) >= 1, "Expected at least one member in repaired tar"
        # Validate each header's magic/version/chksum by reading the raw file.
        with open(REPAIRED_TAR, "rb") as f:
            data = f.read()
        for m in members:
            if not m.offset:
                continue
            header = data[m.offset:m.offset + 512]
            assert len(header) == 512
            magic = header[257:263]
            assert magic == b"ustar\x00", f"Header for {m.name} wrong magic: {magic!r}"
            version = header[263:265]
            assert version == b"00", f"Header for {m.name} wrong version: {version!r}"
            chkfield = bytes(header[148:156]).rstrip(b"\x00").rstrip()
            assert chkfield, f"Header for {m.name} empty checksum field"


def test_repaired_video_is_mp4_with_moov_and_mdat():
    with open(REPAIRED_MP4, "rb") as f:
        data = f.read()
    assert len(data) > 16, "Repaired MP4 too small to be valid"
    found: set[str] = set()
    i = 0
    n = len(data)
    while i < n - 8:
        size = int.from_bytes(data[i:i + 4], "big")
        fourcc = data[i + 4:i + 8].decode("latin-1", errors="replace")
        hlen = 8
        if size == 1:
            if i + 16 > n:
                break
            size = int.from_bytes(data[i + 8:i + 16], "big")
            hlen = 16
        elif size == 0:
            size = n - i
        if all(0x20 <= ord(c) <= 0x7e for c in fourcc) and size >= hlen:
            found.add(fourcc)
        i += max(hlen, size) if size >= hlen else n
    assert "moov" in found, f"moov atom not found in repaired MP4; found={sorted(found)}"
    assert "mdat" in found, f"mdat atom not found in repaired MP4; found={sorted(found)}"


def test_validation_report_looks_good():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)
    # Structural keys required by instruction.md
    required_keys = {
        "ustar_repaired_count",
        "mp4_moov_repaired",
        "mp4_mdat_repaired",
        "mp4_fourccs_found",
        "sha256_match",
        "sha256_expected",
        "sha256_actual",
        "ffprobe_exit",
        "ffprobe_duration",
        "ffprobe_size",
        "extracted_files",
        "all_checks_passed",
    }
    missing = required_keys - set(report.keys())
    assert not missing, f"Report missing keys: {missing}"
    assert isinstance(report["ustar_repaired_count"], int)
    assert report["ustar_repaired_count"] >= 0
    assert isinstance(report["mp4_moov_repaired"], bool)
    assert isinstance(report["mp4_mdat_repaired"], bool)
    assert isinstance(report["mp4_fourccs_found"], list)
    assert "moov" in report["mp4_fourccs_found"] or report["mp4_moov_repaired"]
    assert isinstance(report["sha256_match"], bool)
    assert report["sha256_match"] is True, (
        f"SHA256 did not match: expected={report['sha256_expected']!r} "
        f"actual={report['sha256_actual']!r}"
    )
    assert len(report["sha256_actual"]) == 64, "sha256_actual should be 64 hex chars"
    assert report["ffprobe_exit"] == 0, f"ffprobe exited non-zero: {report['ffprobe_exit']}"
    assert report["ffprobe_duration"] > 0, f"ffprobe duration invalid: {report['ffprobe_duration']}"
    assert report["ffprobe_size"] > 0, f"ffprobe size invalid: {report['ffprobe_size']}"
    assert isinstance(report["extracted_files"], list)
    assert len(report["extracted_files"]) >= 1
    assert report["all_checks_passed"] is True
