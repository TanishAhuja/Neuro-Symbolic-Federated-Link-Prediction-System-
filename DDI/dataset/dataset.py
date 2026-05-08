import hashlib
import json
import time
from pathlib import Path

import requests

API_URL = "http://localhost:8000/DDI"

OUT_DIR = Path("ddi_filtered_dataset")
INDEX = Path("ddi_filtered_index.json")

OUT_DIR.mkdir(exist_ok=True)

# ONLY THESE THREE WILL VARY
VALUE_SPACE = {
    "Gender": ["Male", "Female"],
    "Smoking Habit": ["CurrentSmoker", "ExSmoker", "NonSmoker"],
    "Cancer Stage": ["I", "IIA", "IIB", "IIIA", "IIIB", "IV"],
}

FIELDS = list(VALUE_SPACE.keys())


def combo_key(variables: dict) -> str:
    blob = json.dumps(variables, sort_keys=True).encode()
    return hashlib.md5(blob).hexdigest()[:12]


def load_index():
    if INDEX.exists():
        return json.loads(INDEX.read_text())
    return {}


def save_index(idx):
    INDEX.write_text(json.dumps(idx, indent=2))


def build_payload(variables):
    """
    IMPORTANT:
    API still expects ALL keys to exist.
    We only vary 3 fields but keep the others empty.
    """

    payload = {
        "Input": {
            "Variables": {
                # our actual variables
                "Gender": variables["Gender"],
                "Smoking Habit": variables["Smoking Habit"],
                "Cancer Stage": variables["Cancer Stage"],

                # REQUIRED EMPTY FIELDS
                "Organ affected by the familiar cancer": "",
                "Histology": "",
                "Molecular Markers": [],
                "PDL1 result": "",
                "Therapy": [],
                "Biomarkers": [],
                "Comorbidities": []
            }
        }
    }

    return payload


def fetch_one(variables, retries=3):
    payload = build_payload(variables)

    print("\nSending Payload:")
    print(json.dumps(payload, indent=2))

    last_err = None

    for attempt in range(retries):
        try:
            response = requests.post(
                API_URL,
                json=payload,
                timeout=300
            )

            response.raise_for_status()

            return response.json()

        except Exception as e:
            last_err = e
            print(f"Retry {attempt + 1} failed: {e}")
            time.sleep(2)

    raise last_err


def save_response(variables, response, idx):
    key = combo_key(variables)

    out_file = OUT_DIR / f"{key}.json"

    out_file.write_text(
        json.dumps(
            {
                "input": variables,
                "response": response
            },
            indent=2
        )
    )

    idx[key] = {
        "input": variables,
        "file": str(out_file)
    }


def build_combinations():
    for gender in VALUE_SPACE["Gender"]:
        for smoking in VALUE_SPACE["Smoking Habit"]:
            for stage in VALUE_SPACE["Cancer Stage"]:

                yield {
                    "Gender": gender,
                    "Smoking Habit": smoking,
                    "Cancer Stage": stage
                }


def main():
    idx = load_index()

    combinations = list(build_combinations())

    print(f"Total combinations: {len(combinations)}")

    for i, variables in enumerate(combinations, 1):

        key = combo_key(variables)

        if key in idx:
            print(f"[{i}] Skipping existing {key}")
            continue

        try:
            response = fetch_one(variables)

            save_response(variables, response, idx)

            print(f"[{i}] Saved {key}")

        except Exception as e:
            print(f"[{i}] FAILED: {e}")

        if i % 5 == 0:
            save_index(idx)

        time.sleep(0.2)

    save_index(idx)

    print("\nDONE")
    print(f"Saved responses in: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()