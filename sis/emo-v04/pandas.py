"""
This file was previously importing the 'pandas' package and failed when run as
`python pandas.py` because the script name shadows the installed package (circular import).

To fix the immediate issue and still provide the desired functionality, this script
concatenates all .txt files in the `DATA/` folder into `DATA/all.txt` WITHOUT using pandas.
If you prefer a pandas-based approach, rename this file to something other than `pandas.py` (e.g. `merge_with_pandas.py`) and reintroduce pandas code.
"""

import glob
import os

INPUT_DIR = "DATA"
OUTPUT_FILE = os.path.join(INPUT_DIR, "all.txt")

all_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.txt")))
# Exclude the output file itself (e.g. all.txt) to avoid self-inclusion on re-runs
all_files = [f for f in all_files if os.path.basename(f) != os.path.basename(OUTPUT_FILE)]

if not all_files:
    print(f"No .txt files found in '{INPUT_DIR}'.")
    raise SystemExit(1)

with open(OUTPUT_FILE, "w", encoding="utf-8") as fout:
    total_lines = 0
    for fname in all_files:
        with open(fname, "r", encoding="utf-8") as fin:
            contents = fin.read()
            if contents and not contents.endswith("\n"):
                contents += "\n"
            fout.write(contents)
            total_lines += contents.count("\n")

print(f"Merged {len(all_files)} files into '{OUTPUT_FILE}' ({total_lines} lines).")
