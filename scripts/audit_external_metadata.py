"""Print aggregate metadata counts before deciding whether an external dataset fits.

This tool neither copies images nor changes labels, splits, or training manifests.
Follow the data owner's access and use conditions. Do not publish restricted files.
"""
import argparse
import csv
from collections import Counter
import json
from pathlib import Path


def audit(path, diagnosis_column, tone_column, patient_column=None):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        required = {diagnosis_column, tone_column}
        if patient_column:
            required.add(patient_column)
        if not required.issubset(columns):
            raise ValueError(f"Requested fields missing. Available columns: {columns}")
        counts = Counter()
        patient_sets = {}
        missing_patients = Counter()
        total = 0
        for row in reader:
            diagnosis = (row.get(diagnosis_column) or "").strip() or "<missing>"
            tone = (row.get(tone_column) or "").strip() or "<missing>"
            key = diagnosis, tone
            counts[key] += 1
            total += 1
            patient = (row.get(patient_column) or "").strip() if patient_column else ""
            if patient:
                patient_sets.setdefault(key, set()).add(patient)
            else:
                missing_patients[key] += 1
    return {
        "records": total,
        "patient_identifiers_available": bool(patient_column),
        "note": "Original diagnosis and skin-group values retained; no automatic mapping to BCC/Melanoma/SCC.",
        "counts": [{
            "diagnosis": diagnosis, "recorded_skin_group": tone,
            "images": count,
            "recorded_patients": len(patient_sets.get((diagnosis, tone), set())) if patient_column else None,
            "images_without_patient_id": missing_patients[(diagnosis, tone)],
        } for (diagnosis, tone), count in sorted(counts.items())],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--diagnosis-column", default="disease")
    parser.add_argument("--tone-column", default="skin_tone")
    parser.add_argument("--patient-column")
    options = parser.parse_args()
    print(json.dumps(audit(options.csv, options.diagnosis_column,
                           options.tone_column, options.patient_column), indent=2))


if __name__ == "__main__":
    main()
