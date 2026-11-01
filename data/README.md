# Dataset selection

Data lives in `MyDrive/cnn-skin-cancer-classification/Datasets/`, outside Git.

## HAM10000

Original metadata: 10,015 images across seven categories. This project uses `mel` → **Melanoma** (1,113) and `bcc` → **BCC** (514).

**`akiec` is not selected or relabelled as SCC.** The previous README mapping `akiec (SCC)` was incorrect. Selected HAM images have no recorded skin-tone/patient identifiers available in this workflow. Keep them unknown; available lesion IDs and hashes are used for grouping.

## PAD-UFES-20

Original metadata: 2,298 clinical image records. Selected classes: BCC, MEL and SCC, mapped to BCC, Melanoma and SCC. After documented duplicate/conflicting-label exclusions: BCC 839, Melanoma 52, SCC 185.

The original skin-type field is spelled `fitspatrick`. Preserve recorded values; never infer missing categories from nationality or image brightness.

## Clean selection and splits

2,703 clean images: BCC 1,353, Melanoma 1,165, SCC 185. Fixed grouped splits: train 1,905; validation 390; test 408. Manifest hashes are verified against saved training metadata. Known patient/lesion/hash relationships stay within one split. HAM patient separation cannot be established without patient identifiers.

Sources: [HAM10000](https://doi.org/10.1038/sdata.2018.161), [PAD-UFES-20](https://doi.org/10.17632/zr7vgbcyr2.1). Verify use conditions before acquisition or redistribution.

Additional data requires permitted use, a verified diagnosis mapping, overlap review and a defined training versus independent-evaluation assignment before training. Never move existing held-out cases into training to increase rare-group counts. See `docs/ADDITIONAL_DATA_REVIEW.md`.
