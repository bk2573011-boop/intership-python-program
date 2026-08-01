You are tasked with repairing corrupted archive data and a corrupted MP4 file, then validating the outputs.

Inputs:
- Multi-part gzip-compressed tar archive parts at `/app/data/parts/*.tar.gz.part-*` (e.g.
  `archive.tar.gz.part-aa`, `archive.tar.gz.part-ab`, …).
- A corrupted MP4 at `/app/data/video_corrupted.mp4` (its top-level `moov` size field and
  `mdat` 4CC field are damaged, and possibly other top-level 4CCs too).
- SHA-256 manifest at `/app/data/sha256_manifest.json`:
  `{"repaired_video.mp4": "<64-hex-chars>"}`.

Perform the following steps in order:

1. **Concatenate multi-part gzip** parts in alphabetical order into a single `.tar.gz`, then
   gunzip to obtain the raw tar stream bytes in memory.
2. **Repair ustar tar headers** in the raw tar stream (it is 512-byte block aligned):
   - Force the magic field (offset 257, 6 bytes) to `"ustar"` (NUL padded → `"ustar\0"`).
   - Force the version field (offset 263, 2 bytes) to `"00"`.
   - Recompute the header checksum (offset 148, 8 bytes): treat the 512-byte header as if
     the checksum field is 8 ASCII spaces (`0x20`), sum every byte as unsigned, then format
     the result as a 6-digit zero-padded octal followed by `\0 ` and write it back.
   - Data blocks after a header are untouched; only header blocks (every 512 bytes where the
     block is not a zero trailer) are repaired.
   - Write the repaired tar to `/app/output/repaired_archive.tar`.
3. **Extract repaired archive** into `/app/output/extracted/` (preserve files + subdirs). Identify
   the extracted MP4 file (largest `.mp4` file).
4. **Repair MP4 top-level atoms**:
   - Walk the file in 8+N byte chunks reading (size, fourcc, data).
   - If size is `0`: treat atom as running to EOF (only valid for the final `mdat`).
   - If size is `1`: use the 8-byte `largesize` that follows fourcc.
   - If a box's fourcc is non-printable / unknown AND its adjacent sibling by offset would
     otherwise leave unaccounted-for bytes, infer it is `"mdat"` if it is the large final box
     or `"moov"` if it contains child boxes (`mvhd`, `trak`, `udta` inside).
   - If a box's size would exceed EOF but its fourcc is `"moov"`, compute size as: end of
     previous box → EOF (or until the next known-box start).
   - Write the fully-repaired MP4 with corrected size + fourcc headers to
     `/app/output/repaired_video.mp4`.
5. **SHA-256 validate**: Compute `sha256sum(/app/output/repaired_video.mp4)` and compare with
   the manifest entry. Fail loudly if they don't match.
6. **ffprobe check**: Run `ffprobe -v error -show_entries format=duration,size -of json
   /app/output/repaired_video.mp4`. The output JSON must have `.format.duration > 0` and
   `.format.size > 0`; ffprobe must exit 0.
7. **Validation report**: Write `/app/output/validation_report.json` with keys:
   - `ustar_repaired_count` (int — number of header blocks repaired)
   - `mp4_moov_repaired` (bool)
   - `mp4_mdat_repaired` (bool)
   - `mp4_fourccs_found` (list[str])
   - `sha256_match` (bool)
   - `sha256_expected` (str)
   - `sha256_actual` (str)
   - `ffprobe_exit` (int)
   - `ffprobe_duration` (float — 0 if missing)
   - `ffprobe_size` (int — 0 if missing)
   - `extracted_files` (list[str] — paths relative to extracted/)
   - `all_checks_passed` (bool — logical AND of the above being OK)

Ensure all outputs are placed exactly under `/app/output/`.
