# Experiment 6: reported follow-up evaluation

Source run: `exp06_7fe97493900f`; selected model: ResNet50. Results supplied from the executed Colab notebook, 408 test records. This test set was previously inspected; these are follow-up development results, not an independent final holdout.

| Requirement | Observed | Met |
|---|---:|---|
| Accuracy >= 0.85 | 0.875000 | Yes |
| Macro F1 > 0.80 | 0.736995 | No |
| BCC sensitivity >= 0.80 | 178/197 = 0.903553 | Yes |
| Melanoma sensitivity >= 0.80 | 169/182 = 0.928571 | Yes |
| SCC sensitivity >= 0.80 | 10/29 = 0.344828 | No |

Darker-skin performance remains unestablished. No integration readiness claim is made.

## Implemented follow-up

Open `notebooks/08_scc_decision_and_fitzpatrick_audit.ipynb` in Colab and run all cells. It requires the completed Experiment 6 package and saved validation predictions on Drive, not notebook 07's runtime variables. CPU is sufficient. It does not retrain or rescore test images.

The notebook freezes a small validation-only SCC decision-weight experiment, retains the baseline on exact ties, exports SCC review rows, joins PAD's recorded `fitspatrick` metadata, preserves unknown types, and reports subgroup counts and class metrics. It optionally reads existing original test predictions solely for descriptive subgroup reporting. It does not apply the selected adjustment to that test set. Do not deploy a changed rule based solely on these validation results.

A threshold adjustment may trade false negatives for false positives and may fail to improve the model. No additional real or synthetic patients have been added. Classifier training augmentation already performed does not replace representative real skin-type data. Additional real SCC data and an independent evaluation remain necessary to substantiate the unmet requirements.
