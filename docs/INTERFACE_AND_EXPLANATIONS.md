# Interface and explanation update

The system title is **A CNN Transfer Learning System for Multi-Class Skin Cancer Classification to Support Healthcare Workers in Low-Resource Settings**. The login page and downloadable Word reports use this title. The sidebar uses the shorter label Skin Lesion Review.

## Interface and reports

The app uses teal, navy and light backgrounds, clearer cards and a responsive login banner. Existing role permissions, account handling and review archiving remain in place. Word reports include the saved class, all three scores, model version, referral guidance and handover fields. When a visual explanation has been generated, the report includes it on a separate page. Reports always use the saved prediction, rather than running a new classification for download.

## Visual explanations

The optional **Generate visual explanation** action uses occlusion sensitivity. It covers each of 49 non-overlapping image regions with the image's mean RGB colour, runs the same model and records the change in the saved predicted-class score. Red indicates that covering a region reduced that score; blue indicates an increase. Intensity is relative to the largest absolute change in that image. Changes are given in percentage points. Changes below 0.01 percentage points are shown without coloured emphasis.

This is an explanation of model behaviour, not a clinical explanation or lesion segmentation. It cannot verify borders, texture, cancer, normal skin or skin-tone reliability. The masking colour, background, image lighting and grid size affect the result. No clinical validation of these maps is claimed.

The original bytes, original preprocessing, active model checksum and saved scores must match the review before an explanation is generated. Old reviews require the original upload again; a stored thumbnail is never used for inference. Replacing the active checkpoint does not overwrite an old review or explain it with a different model. Explanations are kept only in the signed-in session unless included in a downloaded report; they are not written to the application database.

Method reference: https://captum.ai/api/occlusion.html. This project implements the method directly with TensorFlow and NumPy; it does not install Captum or PyTorch.

## Normal skin and benign lesions

**Automatic normal-skin or benign detection remains unimplemented.** The current checkpoint has only BCC, Melanoma and SCC outputs. Renaming a score or using a confidence threshold would not create a validated benign class.

Both a visible-lesion check and an explicit healthcare-worker scope assessment are required. Normal skin, benign-looking lesions, other conditions and uncertain assessments block classification. Saving without prediction remains available. The backend requires explicit Boolean confirmations before model loading. These are human checks, not automated recognition; incorrect confirmation can still allow an unsuitable image through.

A real automated solution requires labelled examples of normal skin, benign lesions and unrelated images, alongside the existing cancer classes. Normal skin and benign lesions should remain distinct; neither is synonymous with proven absence of cancer. Train and evaluate a suitability model or expanded classifier with patient/lesion-separated development and held-out evaluation data. Report false acceptance of unsuitable images and missed cancer cases, per-class metrics and subgroup sample counts. Choose thresholds on development data, not the existing repeatedly inspected test set. No dataset, training run or measured improvement is claimed by this UI update.

## Local verification

From the project root with the Python 3.12 virtual environment activated:

```bash
python -m pip install -r app/requirements.txt
python scripts/verify_model_package.py
python scripts/verify_explanation.py
python -m streamlit run app/streamlit_app.py
```

Both verification scripts must print PASS before checking predictions. The explanation script uses the existing private validation reference and makes no database writes. A mismatch is an integration issue; do not change expected scores to force a pass. Keep `app/models/active/` and `app/storage/` private and retain their contents.

## Test evidence

Tests cover known-region sensitivity, neutral maps for unchanged scores, invalid model outputs, explicit scope gating before loading, wrong-image rejection, historical model/score mismatch rejection and Word export identity. A small serialized TensorFlow fixture checks decoding, loading and the complete 49-region path; it is a software test, not a clinical model. Streamlit AppTest checks the login page, Kiswahili and worker/administrator pages against disposable accounts and a disposable database. Existing account, inference, reporting, analytics and archiving tests remain part of the suite.

The developer environment does not contain the private deployed checkpoint or user database. The two local verification scripts therefore remain necessary on the deployment computer. Local tests do not establish clinical performance or automatic normal-skin detection.
