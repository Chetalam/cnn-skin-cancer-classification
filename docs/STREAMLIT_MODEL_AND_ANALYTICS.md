# Experimental Streamlit integration and analytics

The completed Experiment 6 ResNet50 may be used for development while further training continues in separate Drive folders. It does not meet macro-F1, SCC sensitivity or representative skin-type evaluation requirements. App integration does not change that status.

## 1. Get the code

Changes are on `codex/final-training-review`, in PR #1. Save local work before switching branches. In the existing project terminal:

```bash
git status
git fetch origin
git switch codex/final-training-review
git pull --ff-only origin codex/final-training-review
```

If Git reports local modifications preventing checkout, stop and preserve those edits rather than forcing the switch. Pulling main does not retrieve this unmerged branch.

## 2. Export your existing completed model

Open `notebooks/10_export_streamlit_model.ipynb` in Colab from this branch, save a Drive copy and run all cells on CPU. It exports the fixed `final_review_exp06_7fe97493900f` package and one private validation reference into a ZIP in `MyDrive/cnn-skin-cancer-classification/Models/Exports/`.

Download the ZIP and extract its contents into the local project's `app/models/active/`. The directory must directly contain:

- model.keras
- metadata.json
- test_metrics.json
- per_class_metrics.csv
- reference_image.bin
- reference_scores.npy
- reference_manifest.json

Do not create `app/models/active/<zip-name>/model.keras`. Keep these artifacts outside GitHub; this directory is ignored. Do not copy or replace app/storage/application.db.

## 3. Install in an isolated environment

Use Python 3.12 on Windows. The old Streamlit 1.32 protobuf constraint conflicts with the training TensorFlow environment; the new requirements use Streamlit 1.50, TensorFlow 2.21 and Keras 3.13.2. The dependency resolver passes in the development environment. In Git Bash at the project root:

```bash
py -3.12 -m venv .venv
source .venv/Scripts/activate
python -m pip install -r app/requirements.txt
python scripts/verify_model_package.py
python -m streamlit run app/streamlit_app.py
```

Only continue to predictions after the verification script prints PASS. It compares decoding, resizing, ResNet50 preprocessing, class order, serialized loading and scores against the saved Colab reference (rtol 0.001, atol 0.0001). Failure is an integration issue to investigate, not a reason to retrain or alter the expected scores.

## 4. Verify the interface

Sign in as a Healthcare Worker. Upload a de-identified JPG/PNG, select the preview-storage consent box, and choose Analyse and save. Confirm the class, three uncalibrated model scores, model version and saved History entry. Repeated clicks do not create another result or overwrite the historical model version. Save without prediction remains available. If inference fails after saving, the review stays awaiting_model; no fake prediction is created. Earlier reviews require the original image to be uploaded again; prediction never uses a stored 320px thumbnail.

Inference uses original bytes without EXIF rotation, matching the notebook. The preview may follow EXIF; its orientation difference is disclosed. A three-class model must assign scores even to unrelated images; image readability does not establish lesion suitability. This app does not diagnose disease or estimate calibrated cancer risk.

## Analytics

The Analytics sidebar page provides date-filtered UTC daily review counts, pending/completed totals, predicted-class distribution, model-score bins and model-version counts. Workers see their own aggregates; administrators see their healthcare centre's aggregates without case references, images, names or emails. These are workload and prediction statistics, not accuracy or prevalence.

The active checkpoint's saved development evaluation is displayed separately and must match its model checksum and source run. No live accuracy is computed from unlabelled uploads. Subgroup fairness is not inferred from app activity.

## Model updates during training

Keep the app's installed model fixed while training writes to different Drive run folders. To replace it, stop Streamlit, retain the old package, install and verify a complete new package, then restart. Historical predictions keep their original version. Updating an active checkpoint is a manual reviewed action; the app never selects the latest training file automatically.

## Validation limits

Local source compilation and 20 isolated database/inference-contract tests passed. Dependency resolution passed. Inference-contract tests use a stub model because the private trained artifact is not available in the coding environment. Real checkpoint parity must pass on the user's machine before a demonstration; no claim of actual inference parity is made until then. No new performance targets are declared met.

Streamlit AppTest smoke checks passed for the sign-in page, authenticated Analytics, and Analyse Image with the model unavailable. The actual private model has not been exercised in this environment.

## Chart compatibility fix

PyArrow is pinned to 19.0.1 alongside NumPy 1.26.4. An unpinned newer PyArrow can require NumPy 2 at runtime even when pip's dependency resolver accepts the installation. After pulling this change, stop Streamlit, activate the project .venv, run `python -m pip install -r app/requirements.txt`, and restart Streamlit. No model export, database replacement or retraining is required. A regression test renders the actual prediction bar chart, analytics line chart and dataframe rather than checking imports alone.
