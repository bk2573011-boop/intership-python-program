#!/bin/bash
#
# Harbor agent entrypoint. Calls the solution CLI with task-default paths
# (/app/data/** inputs, /app/output/** outputs).
set -euo pipefail
python3 /solution/solve.py
