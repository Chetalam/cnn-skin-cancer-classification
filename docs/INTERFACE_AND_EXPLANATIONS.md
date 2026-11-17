# Interface and explanation update

The application brand is **DermaLens**, used in the sidebar and Word footer. The welcome banner greets users with **Welcome to DermaLens**. The full academic project title remains **A CNN Transfer Learning System for Multi-Class Skin Cancer Classification to Support Healthcare Workers in Low-Resource Settings** in the Word report body.

## Interface and reports

Authenticated pages use navy (#103F53), teal (#087F79), coral (#F07868), warm amber (#F2B84B), soft mint (#DDF3ED) and off-white (#F5F8FA) for consistent headings, metrics, controls, forms, navigation and tables. These protected-page refinements do **not** change the existing login and registration styling. Existing role permissions, account handling and review archiving remain in place. Word reports include the saved class, all three scores, model version, referral guidance and handover fields. When a visual explanation has been generated, the report includes it on a separate page. Reports always use the saved prediction, rather than running a new classification for download.

## Visual explanations

The optional **Generate visual explanation** action uses occlusion sensitivity. It covers each of 49 non-overlapping image regions with the image's mean RGB colour, runs the same model and records the change in the saved predicted-class score. Red indicates that covering a region reduced that score; blue indicates an increase. Intensity is relative to the largest absolute change in that image. Changes are given in percentage points. Changes below 0.01 percentage points are shown without coloured emphasis.

Both the signed-in explanation screen and the optional Word explanation page now include a plain-language guide to the red and blue overlays: red regions made the saved predicted-class score decrease when covered, blue regions made it increase, stronger colours represent larger relative changes, and uncoloured regions had little measured effect. A clearly labelled 75% to 55% example illustrates a **20 percentage-point model-score drop**, not a change in cancer risk. The guide explicitly warns that **red does not mean cancer** and **blue does not mean healthy or safe**. The guide is available in English and Kiswahili. Reports without a generated visual explanation do not include a coloured-map explanation page.\n\nThis is an explanation of model behaviour, not a clinical explanation or lesion segmentation. It cannot verify borders, texture, cancer, normal skin or skin-tone reliability. The masking colour, background, image lighting and grid size affect the result. No clinical validation of these maps is claimed.

The original bytes, original preprocessing, active model checksum and saved scores must match the review before an explanation is generated. Old reviews require the original upload again; a stored thumbnail is never used for inference. Replacing the active checkpoint does not overwrite an old review or explain it with a different model. Explanations are kept only in the signed-in session unless included in a downloaded report; they are not written to the application database.

Method reference: https://captum.ai/api/occlusion.html. This project implements the method directly with TensorFlow and NumPy; it does not install Captum or PyTorch.

## Normal skin and benign lesions

**Automatic normal-skin or benign detection remains unimplemented.** The current checkpoint has only BCC, Melanoma and SCC outputs. Renaming a score or using a confidence threshold would not create a validated benign class.

The Analyse Image page asks one lesion-visibility question (Not sure / No lesion / normal skin / Yes). Not sure and No lesion / normal skin block classification. Selecting Yes shows a short three-class limitation notice and an unchecked acknowledgement: a visible lesion is not necessarily cancer, and the model classifies only BCC, Melanoma and SCC. Only Yes plus the explicit acknowledgement unlock experimental classification when the model is installed and preview consent is given. The backend checks both strict Boolean confirmations before model loading. Saving without a prediction remains available for all answers. These are worker assessments, **not automated benign, normal-skin or cancer recognition**; an unsuitable image can still be submitted following an incorrect human assessment.

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

Tests cover known-region sensitivity, neutral maps for unchanged scores, invalid model outputs, strict lesion-visibility and acknowledgement gating before loading, wrong-image rejection, historical model/score mismatch rejection and Word export identity. A small serialized TensorFlow fixture checks decoding, loading and the complete 49-region path; it is a software test, not a clinical model. Streamlit AppTest checks the login page, Kiswahili and worker/administrator pages against disposable accounts and a disposable database. Existing account, inference, reporting, analytics and archiving tests remain part of the suite.

The developer environment does not contain the private deployed checkpoint or user database. The two local verification scripts therefore remain necessary on the deployment computer. Local tests do not establish clinical performance or automatic normal-skin detection.
