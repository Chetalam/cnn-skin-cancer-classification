# CNN Skin Cancer Classification System

Student: Limo, Laura Chetalam | 169388 | BBIT 4D
Supervisor: Dr. Henry Muchiri
Institution: Strathmore University, School of Computing and Engineering Sciences

Research prototype for BCC, Melanoma and SCC classification, with an English/Kiswahili Streamlit interface. This is a closed three-class research task: there is no benign/no-cancer class and no clinical diagnosis is provided.

## Current status

- Experiments 1–5 and Fitzpatrick representation/subgroup audits are recorded in notebook 05.
- Experiment 2 ResNet50 follow-up test accuracy: **85.78%**; macro F1: **0.7443**; SCC sensitivity: **48.28%**. Macro F1 and per-class sensitivity targets remain unmet.
- Experiment 5 ResNet50 has the highest recorded validation macro F1 (**0.6994**) and validation accuracy **87.44%**. These are not new test scores. SCC validation recall was **6/26**.
- Existing IV–VI validation support is just **3 BCC images and 1 SCC image**, with no Melanoma. Darker-skin and Kenyan-patient performance are **not established**. HAM images without skin metadata remain unknown.
- Model integration is pending. The app saves reviews as **Awaiting model**, without fabricated predictions.

## Run locally

From the repository root using the existing Python 3.11/3.12 environment:

```bash
python -m pip install -r app/requirements.txt
python -m streamlit run app/streamlit_app.py
```

Healthcare workers manage only their own reviews. Administrators manage centre accounts and dataset metadata. Registration roles/centre names are self-declared; open administrator registration does not verify professional identity and is unsuitable as a production authorisation policy. Profile deactivation retains reviews and revokes sessions; an active same-centre administrator can restore access. The last active administrator at a centre cannot self-deactivate.

Passwords use salted PBKDF2 hashes. App data defaults to `app/storage/application.db`, overridable with `SKIN_APP_DB`. This differs from the Colab training database. Do not delete databases during code updates.

## Final training review

Open [notebook 07 in Colab](https://colab.research.google.com/github/Chetalam/cnn-skin-cancer-classification/blob/main/notebooks/07_final_training_and_evaluation.ipynb) after merging its reviewed PR, or use the branch URL in that PR.

Use a fresh T4 runtime and run top to bottom; no notebook 05 variables are needed. It trains one bounded 224px ResNet50 focal-loss configuration, compares recorded validation checkpoints and exports a verified candidate. The winner can remain an earlier run. Earlier notebooks/runs/packages are preserved.

Fix the candidate before explicitly enabling follow-up test evaluation. The evaluation uses metadata input size/preprocessing and saved validation-reference checks. The existing test set has already been inspected: this is **follow-up evaluation**, not an untouched independent final estimate.

| Declared requirement | Criterion |
|---|---|
| Test accuracy | ≥0.85 |
| Test macro F1 | >0.80 |
| Sensitivity per class | ≥0.80 (existing project README target) |
| Skin-tone evidence | Report coverage, independent cases and subgroup limitations; current data is insufficient |

Report numerical targets separately from skin-tone evidence. Integration remains paused under the user's stated requirement until the results and intended use are reviewed. See [completion checklist](docs/COMPLETION_CHECKLIST.md).

## Drive locations

Root: `MyDrive/cnn-skin-cancer-classification/`

- `Datasets/HAM10000/`, `Datasets/PAD-UFES-20/`
- `Datasets/Cleaned/clean_metadata.csv`, `Datasets/Splits/`
- `Database/skin_cancer.db` — training metadata database
- `Models/Transfer_Learning/<run_id>/<architecture>/`
- `Models/Selected/<package>/`
- `Reports/Training/`, `Reports/Evaluation/`, `Reports/Skin_Tone_Audit/`

See [data selection](data/README.md), [model packages](models/README.md), and [external-data review](docs/ADDITIONAL_DATA_REVIEW.md). GitHub access does not include Drive datasets, weights or the user's Colab GPU.

## Checks

```bash
python -m compileall -q app scripts tests
python -m unittest discover -s tests -v
```

Checks cover account/ownership boundaries, deactivation/retention, migration relationships, notebook syntax and metadata aggregation. They do not execute GPU training, establish diagnostic performance or replace browser testing. Keep datasets, model weights, databases, backups and secrets out of ordinary Git commits.

## SCC and Fitzpatrick follow-up

Experiment 6 achieved 87.50% test accuracy and 0.736995 macro F1; SCC sensitivity was 10/29 (34.48%). Requirements remain unmet. See [reported results](docs/EXPERIMENT_6_RESULTS.md). Run [notebook 08](notebooks/08_scc_decision_and_fitzpatrick_audit.ipynb) for the validation-only SCC decision experiment and recorded Fitzpatrick audit. It does not retrain or change the existing model.
