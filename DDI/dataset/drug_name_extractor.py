import json
import re
from pathlib import Path

# INPUT FOLDER CONTAINING ALL JSON FILES
INPUT_FOLDER = Path("/Users/tanishahuja/Downloads/P4-LUCAT_API/DDI/gpt/output")

# OUTPUT FOLDER
OUTPUT_FOLDER = Path("/Users/tanishahuja/Downloads/P4-LUCAT_API/DDI/gpt/drug_names_dataset")

# Create output folder if not exists
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Process every JSON file in input folder
for input_file in INPUT_FOLDER.glob("*.json"):

    print(f"\nProcessing: {input_file.name}")

    # Load JSON
    with open(input_file, "r") as f:
        data = json.load(f)

    summary = {}

    # Same logic as your original script
    for patient in data:

        for patient_id, treatments_dict in patient.items():

            summary[patient_id] = {}

            for treatment_id, treatment_list in treatments_dict.items():

                unique_drugs = set()
                status = None

                for treatment in treatment_list:

                    for progression_key, progression_list in treatment.items():

                        status = progression_key

                        for entry in progression_list:

                            drugbank_string = entry.get("DDI_DrugBank")

                            if drugbank_string:
                                db_codes = re.findall(r'DB\d+', drugbank_string)
                                unique_drugs.update(db_codes)

                summary[patient_id][treatment_id] = {
                    "status": status,
                    "unique_drugs": sorted(list(unique_drugs))
                }

    # Output filename SAME as input filename
    output_file = OUTPUT_FOLDER / input_file.name

    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved: {output_file.name}")

print("\nDONE")
print("All processed files saved in:")
print(OUTPUT_FOLDER)