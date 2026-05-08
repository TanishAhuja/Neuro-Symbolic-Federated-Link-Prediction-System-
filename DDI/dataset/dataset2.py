"""
Fetch one JSON file per (Gender, Smoking Habit, Cancer Stage) combination
from the P4-LUCAT DDI API.

Output filenames: <Gender>_<Smoking>_<Stage>.json
e.g. Male_CurrentSmoker_I.json, Female_NonSmoker_IIIA.json

Usage:
    python3 fetch_combinations.py <output_dir>
    python3 fetch_combinations.py <output_dir> --url http://localhost:8000/DDI

The script:
- Skips any combination whose output file already exists (resumable).
- Logs failures to a fetch_failures.txt file but keeps going.
- Pauses briefly between calls to be nice to the API.
"""

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

import requests

GENDERS = ["Male", "Female"]
SMOKING = ["CurrentSmoker", "ExSmoker", "NonSmoker"]
STAGES = ["I", "IIA", "IIB", "IIIA", "IIIB", "IV"]

# Fields we leave blank — the API expects them in the body even when unused.
BLANK_FIELDS = {
    "Organ affected by the familiar cancer": "",
    "Histology": "",
    "Molecular Markers": "",
    "PDL1 result": "",
}


def build_payload(gender, smoking, stage):
    return {
        "Input": {
            "Variables": {
                "Gender": gender,
                "Smoking Habit": smoking,
                "Cancer Stage": stage,
                **BLANK_FIELDS,
            }
        }
    }


def fetch_one(url, gender, smoking, stage, timeout=120):
    payload = build_payload(gender, smoking, stage)
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", help="directory to write per-combination JSON files")
    ap.add_argument("--url", default="http://localhost:8000/DDI",
                    help="DDI endpoint (default: http://localhost:8000/DDI)")
    ap.add_argument("--sleep", type=float, default=0.5,
                    help="seconds to sleep between calls (default: 0.5)")
    ap.add_argument("--overwrite", action="store_true",
                    help="re-fetch combinations whose file already exists")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    failures_log = out_dir / "fetch_failures.txt"

    combos = list(itertools.product(GENDERS, SMOKING, STAGES))
    total = len(combos)
    print(f"Planned: {total} combinations  ->  {out_dir}")

    saved = skipped = failed = 0
    for i, (gender, smoking, stage) in enumerate(combos, start=1):
        name = f"{gender}_{smoking}_{stage}.json"
        path = out_dir / name

        if path.exists() and not args.overwrite:
            print(f"[{i}/{total}] skip   {name} (already exists)")
            skipped += 1
            continue

        try:
            data = fetch_one(args.url, gender, smoking, stage)
        except Exception as e:
            msg = f"[{i}/{total}] FAIL   {name}: {e}"
            print(msg)
            with open(failures_log, "a") as f:
                f.write(msg + "\n")
            failed += 1
            time.sleep(args.sleep)
            continue

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[{i}/{total}] saved  {name}")
        saved += 1
        time.sleep(args.sleep)

    print()
    print(f"Done. saved={saved}  skipped={skipped}  failed={failed}")
    if failed:
        print(f"See {failures_log} for details. Re-run the script to retry "
              f"failed combinations.")


if __name__ == "__main__":
    main()