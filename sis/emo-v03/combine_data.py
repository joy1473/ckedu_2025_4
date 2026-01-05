"""
Simple script to concatenate all .txt files in DATA/ into DATA/all.txt
This avoids importing pandas and avoids the circular import caused by
having a file named `pandas.py` in the working directory.
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
