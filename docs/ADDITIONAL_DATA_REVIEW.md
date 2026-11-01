# Additional SCC and skin-tone data review

## Existing evidence

SCC training: 130 images from 93 recorded patients / 103 lesions. Training has zero recorded V–VI SCC or Melanoma images; HAM skin metadata is unknown. IV–VI validation contains 3 BCC and 1 SCC images, no Melanoma. Experiments 2 and 5 missed that SCC case. This cannot support reliable subgroup claims.

## Candidate external data

Use the [official DDI page](https://aimi.stanford.edu/datasets/ddi-diverse-dermatology-images) and current access conditions. DDI is a candidate for assessment, not an already approved training source. Its groups I–II, III–IV and V–VI cannot be split into individual categories or exactly recreated as IV–VI. Malignancy alone cannot be assigned to BCC/Melanoma/SCC. Published terms restrict redistribution and derivative works; verify permitted evaluation, training, augmentation and app distribution before those uses.

Do not publish restricted images, patient metadata or private links. Share aggregate counts only where permitted. If patient IDs are absent, record that limitation rather than treating every image as an independent patient.

Inspect a locally obtained CSV without changing it:

```bash
python scripts/audit_external_metadata.py /path/to/ddi_metadata.csv --diagnosis-column disease --tone-column skin_tone
```

Add `--patient-column <actual_column>` only if provided. Original diagnosis/group values stay unchanged; inspect exact labels before approving a mapping. Never relabel unrelated malignancies as SCC.

Before merging, record permission/provenance, diagnosis compatibility, clinical versus dermoscopic image differences, exact/near-duplicate overlap and patient/lesion relationships. Define external training versus independent-evaluation assignments first. Preserve existing held-out cases. Adding training cases alone does not provide independent evaluation evidence.

## Synthetic SCC is separate

Focal loss is the current real-only experiment. Do not add synthetic samples simultaneously. A synthetic experiment needs training-only generator fitting/conditioning, permitted source/model use, provenance, memorisation/duplicate/artifact screening and qualified assessment of preserved diagnostic features.

Synthetic images are not new biopsy-confirmed patients and cannot establish real darker-skin performance. Keep them out of validation/testing. Compare real-only and real-plus-synthetic training using the same real validation cases before fixing a candidate for follow-up evaluation. Brightness changes or colouring skin darker do not replace labelled real cases. Generating more images from the same small cohort does not increase its independent patient count.
