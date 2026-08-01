"""Dynamo task: repair ustar tar (multi-part gz) + MP4 atom headers + SHA-256 + ffprobe.

Provides both a CLI entrypoint and pure library functions:
  - concat_multipart_gz()
  - repair_ustar_headers()
  - extract_tar()
  - find_mp4()
  - repair_mp4_atoms()
  - sha256_file()
  - run_ffprobe_check()
  - build_validation_report()
  - process_pipeline() — orchestrates everything according to instruction.md
"""

from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tarfile
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Default paths (matches instruction.md)
# ---------------------------------------------------------------------------
DATA_DIR = "/app/data"
PARTS_GLOB = os.path.join(DATA_DIR, "parts", "*.tar.gz.part-*")
CORRUPTED_MP4 = os.path.join(DATA_DIR, "video_corrupted.mp4")
SHA_MANIFEST = os.path.join(DATA_DIR, "sha256_manifest.json")

OUT_DIR = "/app/output"
REPAIRED_TAR = os.path.join(OUT_DIR, "repaired_archive.tar")
EXTRACT_DIR = os.path.join(OUT_DIR, "extracted")
REPAIRED_MP4 = os.path.join(OUT_DIR, "repaired_video.mp4")
REPORT_PATH = os.path.join(OUT_DIR, "validation_report.json")

USTAR_MAGIC = b"ustar\x00"
USTAR_VERSION = b"00"
BLOCK_SIZE = 512

KNOWN_MP4_FOURCCS = {
    b"ftyp", b"moov", b"mdat", b"free", b"skip", b"widc", b"uuid",
    b"moof", b"mvex", b"traf", b"mfhd", b"tfhd", b"trun", b"mdhd",
    b"sidx", b"styp", b"mvhd", b"trak", b"mdia", b"udta", b"stbl",
    b"hdlr", b"tkhd", b"minf", b"stsd", b"stts", b"stsc", b"stsz",
    b"stco", b"dinf", b"dref", b"smhd", b"vmhd", b"hmhd",
}
TOP_LEVEL_PRINTABLE = {b"ftyp", b"moov", b"mdat", b"free", b"skip", b"moof", b"sidx", b"styp"}
# FourCCs that are NEVER top-level (child-boxes inside moov/traf/etc). They
# MUST NOT be recorded as PASS-1 anchors, otherwise a corrupted moov-size
# combined with byte-by-byte scanning can pick up child headers inside moov
# as spurious "next top-level boxes".
CHILD_ONLY_FOURCCS = KNOWN_MP4_FOURCCS - TOP_LEVEL_PRINTABLE
PRINTABLE = set(range(0x20, 0x7F))


# ---------------------------------------------------------------------------
# Multi-part gzip concat + gunzip into raw tar bytes
# ---------------------------------------------------------------------------
def concat_multipart_gz(glob_pattern: str = PARTS_GLOB) -> bytes:
    """Concatenate multi-part .tar.gz.part-* files in sorted order and gunzip."""
    parts = sorted(glob.glob(glob_pattern))
    if not parts:
        raise FileNotFoundError(f"No parts matched {glob_pattern}")
    buf = io.BytesIO()
    for p in parts:
        with open(p, "rb") as f:
            shutil.copyfileobj(f, buf)
    buf.seek(0)
    with gzip.GzipFile(fileobj=buf, mode="rb") as gz:
        return gz.read()


# ---------------------------------------------------------------------------
# USTAR header repair (operates on a bytearray of the raw tar stream)
# ---------------------------------------------------------------------------
def _ustar_header_checksum(header: bytes) -> bytes:
    """Compute the ustar header checksum.

    The checksum is computed as if the 8-byte chksum field (offset 148..156)
    contained 8 ASCII spaces. Returns the 8-byte field suitable to write back:
    6 octal digits (zero-padded) + b'\\0 '.
    """
    if len(header) != BLOCK_SIZE:
        raise ValueError("header must be exactly 512 bytes")
    h = bytearray(header)
    for i in range(148, 156):
        h[i] = 0x20
    total = sum(h) & 0o777777777777
    field = f"{total:06o}\0 ".encode("ascii")
    assert len(field) == 8
    return field


def _is_zero_block(block: bytes) -> bool:
    return all(b == 0 for b in block)


def repair_ustar_headers(raw_tar: bytes) -> Tuple[bytearray, int]:
    """Repair ustar magic, version and checksum on every non-zero header block.

    Returns (repaired_tar_bytes, number_of_headers_repaired).
    """
    if len(raw_tar) % BLOCK_SIZE != 0:
        # Pad to block boundary — verifiers expect block-aligned tar files.
        padding = BLOCK_SIZE - (len(raw_tar) % BLOCK_SIZE)
        raw_tar = raw_tar + b"\x00" * padding
    out = bytearray(raw_tar)
    repaired = 0
    i = 0
    n = len(out)
    while i < n:
        header_block = bytes(out[i:i + BLOCK_SIZE])
        if _is_zero_block(header_block):
            i += BLOCK_SIZE
            continue
        # --- fix magic
        out[i + 257:i + 263] = USTAR_MAGIC
        # --- fix version
        out[i + 263:i + 265] = USTAR_VERSION
        # --- recalc checksum
        new_chk = _ustar_header_checksum(bytes(out[i:i + BLOCK_SIZE]))
        out[i + 148:i + 156] = new_chk
        repaired += 1
        # --- compute payload size from size field (octal) and advance
        size_field = bytes(out[i + 124:i + 136]).rstrip(b"\x00").strip() or b"0"
        try:
            data_size = int(size_field, 8)
        except ValueError:
            data_size = 0
        data_blocks = (data_size + BLOCK_SIZE - 1) // BLOCK_SIZE
        i += BLOCK_SIZE + data_blocks * BLOCK_SIZE
    return out, repaired


def extract_tar(repaired_tar_path: str, extract_dir: str) -> List[str]:
    """Extract the repaired tar to extract_dir, returning relative paths."""
    os.makedirs(extract_dir, exist_ok=True)
    extracted: List[str] = []
    with tarfile.open(repaired_tar_path, "r") as tf:
        # Safe extraction: reject absolute paths and up-references.
        for member in tf.getmembers():
            member_path = member.name
            if member_path.startswith("/") or ".." in member_path.split(os.sep):
                continue
            tf.extract(member, extract_dir)
            if member.isfile():
                extracted.append(member_path)
    # Also walk the directory in case member list had issues with nested dirs.
    all_files: List[str] = []
    for root, _, files in os.walk(extract_dir):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, extract_dir)
            all_files.append(rel)
    return sorted(set(extracted + all_files))


def find_mp4(extract_dir: str) -> Optional[str]:
    """Largest .mp4 inside extract_dir; returns absolute path or None."""
    best = None
    best_size = -1
    for root, _, files in os.walk(extract_dir):
        for name in files:
            if name.lower().endswith(".mp4"):
                full = os.path.join(root, name)
                sz = os.path.getsize(full)
                if sz > best_size:
                    best = full
                    best_size = sz
    return best


# ---------------------------------------------------------------------------
# MP4 top-level atom parsing + repair
# ---------------------------------------------------------------------------
def _printable_fourcc(b: bytes) -> bool:
    return len(b) == 4 and all(c in PRINTABLE for c in b)


def _atom_header(data: bytes, offset: int) -> Optional[Tuple[int, bytes, int]]:
    """Return (size, fourcc, header_len) for atom starting at offset, or None.

    size=0 means "runs to EOF" (header_len stays 8).
    size=1 means 64-bit largesize follows fourcc (header_len=16).
    """
    if offset + 8 > len(data):
        return None
    size = struct.unpack(">I", data[offset:offset + 4])[0]
    fourcc = data[offset + 4:offset + 8]
    header_len = 8
    if size == 1:
        if offset + 16 > len(data):
            return None
        size = struct.unpack(">Q", data[offset + 8:offset + 16])[0]
        header_len = 16
    elif size == 0:
        size = len(data) - offset
    return size, fourcc, header_len


def _child_scan(box_body: bytes) -> Dict[str, int]:
    """Return {fourcc: count} for first-level child boxes (used to detect moov)."""
    counts: Dict[str, int] = {}
    i = 0
    n = len(box_body)
    while i < n:
        info = _atom_header(box_body, i)
        if info is None:
            break
        size, fourcc, hlen = info
        if size < hlen or size == 0:
            break
        key = fourcc.decode("latin-1", errors="replace")
        counts[key] = counts.get(key, 0) + 1
        i += size
        if i > n:
            break
    return counts


def repair_mp4_atoms(data: bytes) -> Tuple[bytearray, bool, bool, List[str]]:
    """Repair corrupted size/4cc fields for top-level moov/mdat boxes.

    Returns (repaired_bytes, moov_repaired, mdat_repaired, list_of_top_level_fourccs).
    """
    repaired_buf = bytearray()
    moov_repaired = False
    mdat_repaired = False
    found_ccs: List[str] = []

    n = len(data)
    i = 0

    known_starts: List[Tuple[int, int, bytes]] = []  # (offset, size, fourcc)

    # ---- PASS 1: record positions of plausible top-level atoms to serve as
    # size-anchors in PASS 2. This prevents a box with a corrupted huge-size
    # field from gobbling up the rest of the file (and every box inside it).
    j = 0
    while j < n:
        info = _atom_header(data, j)
        if info is None:
            break
        size, fourcc, hlen = info
        remaining = n - j
        # Read the RAW 4-byte size field to distinguish "size==0 means EOF"
        # from a genuinely specified size. Raw-size-zero is a red flag that
        # this "header" is actually just zeroes inside a box body.
        raw_size = struct.unpack(">I", data[j:j + 4])[0]
        raw_size_nonzero = raw_size != 0
        # If a recently-added anchor is within 7 bytes (i.e., we're reading
        # the same header shifted by 1..7 bytes), skip this position to avoid
        # recording a spurious misaligned header right next to a real one.
        close_to_existing = any(abs(j - off) < 8 for off, _, _ in known_starts)
        # Anchor condition 1: known + printable top-level fourcc.
        # Even if the size field is garbage, we still record the OFFSET of a
        # known-good fourcc as an anchor (the size will be recomputed in
        # pass 2 from neighboring anchors). We only advance j by the minimal
        # header so we don't skip over other real boxes that a bad size would
        # have skipped.
        if _printable_fourcc(fourcc) and fourcc in TOP_LEVEL_PRINTABLE:
            if not close_to_existing:
                known_starts.append((j, size, fourcc))
            if raw_size_nonzero and size >= hlen and size <= remaining:
                j += size
            else:
                j += hlen
            continue
        # Anchor condition 2: corrupted-fourcc big / final box.
        #
        # This catches the SPECIFIC scenario described in the task: the final
        # ``mdat`` box has its 4CC trashed but its size field is still correct
        # (i.e. size == remaining bytes because mdat runs to EOF, or mdat is
        # simply large).  Tight thresholds prevent accidentally recording a
        # misaligned 8-byte window near a box boundary (which would otherwise
        # look valid: raw_size non-zero + small size + non-zero fourcc bytes).
        if (
            raw_size_nonzero
            and not close_to_existing
            and size >= hlen
            and size <= remaining
            and fourcc not in CHILD_ONLY_FOURCCS
            and not _printable_fourcc(fourcc)
            and any(b != 0 for b in fourcc)
            and (size == remaining or size >= 4096)
        ):
            known_starts.append((j, size, fourcc))
            j += size
            continue
        # Unrecoverable position: advance by 1 to scan for the next plausible
        # header. (Step by 1 because real boxes may not be 4-aligned in a
        # damaged file; the close-to-existing check above mitigates noise.)
        j += 1

    known_by_offset = {off: (sz, cc) for off, sz, cc in known_starts}

    # ---- PASS 2: walk and repair top-level atoms
    i = 0
    while i < n:
        info = _atom_header(data, i)
        if info is None:
            # Pad the remainder to at least 0 bytes and bail.
            repaired_buf.extend(data[i:])
            break
        size, fourcc, hlen = info

        # Determine next known-box offset after i
        next_known_offsets = [off for off in known_by_offset if off > i]
        next_off = min(next_known_offsets) if next_known_offsets else n

        size_ok = (size >= hlen) and (i + size <= n)
        bad_cc = not _printable_fourcc(fourcc) or fourcc not in TOP_LEVEL_PRINTABLE

        inferred_cc = fourcc
        inferred_size = size if size_ok else next_off - i

        if not size_ok and _printable_fourcc(fourcc) and fourcc in TOP_LEVEL_PRINTABLE:
            if fourcc == b"moov":
                moov_repaired = True
            if fourcc == b"mdat":
                mdat_repaired = True
            inferred_size = next_off - i if next_off >= i + hlen else n - i

        if bad_cc:
            # Try to infer based on position / body content
            body_start = i + hlen
            body_end_guess = i + inferred_size
            if body_end_guess > n:
                body_end_guess = n
            body = data[body_start:body_end_guess]
            children = _child_scan(body)
            has_mvhd = "mvhd" in children or b"mvhd" in body[:BLOCK_SIZE]
            has_trak = "trak" in children or b"trak" in body[:BLOCK_SIZE * 8]
            is_last_box = not next_known_offsets
            if (has_mvhd or has_trak) and len(body) > 64:
                inferred_cc = b"moov"
                moov_repaired = True
            elif is_last_box and (inferred_size > hlen):
                inferred_cc = b"mdat"
                mdat_repaired = True
            elif len(body) < 32 and _printable_fourcc(fourcc):
                # small printable free/skip — keep as-is
                inferred_cc = fourcc
            else:
                inferred_cc = b"free"

        # Build the header back with corrected size + fourcc
        new_hlen = 8
        new_size = new_hlen + max(0, inferred_size - hlen)
        # Sanity: size must fit in 32-bit uint (size==1 was already expanded)
        if new_size >= 0xFFFFFFFF:
            header = struct.pack(">I", 1) + inferred_cc + struct.pack(">Q", new_size)
            new_hlen = 16
        else:
            header = struct.pack(">I", new_size) + inferred_cc
        repaired_buf.extend(header)
        body_original_start = i + hlen
        body_wanted = new_size - new_hlen
        if body_wanted > 0:
            body_end = min(body_original_start + body_wanted, n)
            repaired_buf.extend(data[body_original_start:body_end])
            actual_body = body_end - body_original_start
            if actual_body < body_wanted:
                repaired_buf.extend(b"\x00" * (body_wanted - actual_body))
        try:
            found_ccs.append(inferred_cc.decode("latin-1"))
        except Exception:  # noqa: BLE001
            found_ccs.append(repr(inferred_cc))
        i += inferred_size
        if i < 0 or i > n:
            break

    return repaired_buf, moov_repaired, mdat_repaired, found_ccs


# ---------------------------------------------------------------------------
# SHA-256 + ffprobe checks
# ---------------------------------------------------------------------------
def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def run_ffprobe_check(mp4_path: str) -> Tuple[int, float, int, Optional[dict]]:
    """Return (exit_code, duration, size_bytes, parsed_json)."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size",
        "-of", "json", mp4_path,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1, 0.0, 0, None
    duration = 0.0
    size = 0
    payload: Optional[dict] = None
    try:
        payload = json.loads(proc.stdout)
        fmt = (payload or {}).get("format", {}) or {}
        dur_raw = fmt.get("duration")
        if dur_raw is not None:
            duration = float(dur_raw)
        sz_raw = fmt.get("size")
        if sz_raw is not None:
            size = int(sz_raw)
    except (ValueError, TypeError):
        payload = None
    return proc.returncode, duration, size, payload


# ---------------------------------------------------------------------------
# Pipeline + report
# ---------------------------------------------------------------------------
def build_validation_report(
    *,
    ustar_repaired_count: int,
    moov_repaired: bool,
    mdat_repaired: bool,
    fourccs: List[str],
    sha_expected: str,
    sha_actual: str,
    ff_exit: int,
    ff_duration: float,
    ff_size: int,
    extracted_files: List[str],
) -> Dict[str, object]:
    sha_match = (sha_expected == sha_actual) and bool(sha_actual)
    ff_ok = (ff_exit == 0) and ff_duration > 0 and ff_size > 0
    all_ok = bool(ustar_repaired_count >= 0) and sha_match and ff_ok
    return {
        "ustar_repaired_count": int(ustar_repaired_count),
        "mp4_moov_repaired": bool(moov_repaired),
        "mp4_mdat_repaired": bool(mdat_repaired),
        "mp4_fourccs_found": list(fourccs),
        "sha256_match": bool(sha_match),
        "sha256_expected": str(sha_expected),
        "sha256_actual": str(sha_actual),
        "ffprobe_exit": int(ff_exit),
        "ffprobe_duration": float(ff_duration),
        "ffprobe_size": int(ff_size),
        "extracted_files": list(extracted_files),
        "all_checks_passed": bool(all_ok),
    }


def _load_manifest(manifest_path: str) -> Dict[str, str]:
    if not os.path.exists(manifest_path):
        return {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        return {k.lower(): v for k, v in (json.load(f) or {}).items()}


def process_pipeline(
    *,
    parts_glob: str = PARTS_GLOB,
    corrupted_mp4: str = CORRUPTED_MP4,
    manifest_path: str = SHA_MANIFEST,
    repaired_tar: str = REPAIRED_TAR,
    extract_dir: str = EXTRACT_DIR,
    repaired_mp4: str = REPAIRED_MP4,
    report_path: str = REPORT_PATH,
) -> Dict[str, object]:
    """Run the whole instruction.md pipeline end-to-end. Writes all artifacts.

    Returns the validation report dictionary.
    """
    os.makedirs(os.path.dirname(repaired_tar), exist_ok=True)
    os.makedirs(extract_dir, exist_ok=True)

    # 1) + 2) Concatenate gz parts → gunzip → repair ustar headers
    raw_tar = concat_multipart_gz(parts_glob)
    repaired_bytes, ustar_repairs = repair_ustar_headers(raw_tar)
    with open(repaired_tar, "wb") as f:
        f.write(bytes(repaired_bytes))

    # 3) Extract repaired tar
    extracted = extract_tar(repaired_tar, extract_dir)

    # 4) MP4 repair: prefer extracted MP4 (if any), fall back to input corrupted MP4
    inner_mp4 = find_mp4(extract_dir)
    input_mp4 = inner_mp4 if inner_mp4 else corrupted_mp4
    if not os.path.exists(input_mp4):
        raise FileNotFoundError(f"No MP4 found for repair at {input_mp4}")
    with open(input_mp4, "rb") as f:
        mp4_data = f.read()
    repaired_mp4_bytes, moov_r, mdat_r, fccs = repair_mp4_atoms(mp4_data)
    with open(repaired_mp4, "wb") as f:
        f.write(bytes(repaired_mp4_bytes))

    # 5) SHA-256 validate (keyed by either basename or absolute)
    manifest = _load_manifest(manifest_path)
    sha_expected = (
        manifest.get("repaired_video.mp4")
        or manifest.get(repaired_mp4.lower())
        or manifest.get(repaired_mp4)
        or ""
    )
    sha_actual = sha256_file(repaired_mp4)

    # 6) ffprobe
    ff_exit, ff_dur, ff_sz, _ = run_ffprobe_check(repaired_mp4)

    # 7) Write validation report
    report = build_validation_report(
        ustar_repaired_count=ustar_repairs,
        moov_repaired=moov_r,
        mdat_repaired=mdat_r,
        fourccs=fccs,
        sha_expected=sha_expected or "",
        sha_actual=sha_actual,
        ff_exit=ff_exit,
        ff_duration=ff_dur,
        ff_size=ff_sz,
        extracted_files=extracted,
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Repair multi-part gz tar (ustar) + MP4 headers, "
            "validate with SHA-256/ffprobe."
        ),
    )
    p.add_argument("--parts-glob", default=PARTS_GLOB)
    p.add_argument("--corrupted-mp4", default=CORRUPTED_MP4)
    p.add_argument("--manifest", default=SHA_MANIFEST)
    p.add_argument("--repaired-tar", default=REPAIRED_TAR)
    p.add_argument("--extract-dir", default=EXTRACT_DIR)
    p.add_argument("--repaired-mp4", default=REPAIRED_MP4)
    p.add_argument("--report", default=REPORT_PATH)
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(list(sys.argv[1:]) if argv is None else argv)
    report = process_pipeline(
        parts_glob=args.parts_glob,
        corrupted_mp4=args.corrupted_mp4,
        manifest_path=args.manifest,
        repaired_tar=args.repaired_tar,
        extract_dir=args.extract_dir,
        repaired_mp4=args.repaired_mp4,
        report_path=args.report,
    )
    ok = bool(report.get("all_checks_passed"))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
