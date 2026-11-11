# External data access and the two unresolved gaps

Experiment 6: SCC sensitivity 10/29, macro F1 0.736995. Neither requirement is repaired by a code change alone. Notebook 08's validation decision experiment retained multiplier 1.0.

## Implemented training workflow

`notebooks/09_external_clinical_data_training.ipynb` verifies an externally obtained Fitzpatrick17k image package, excludes disagreements between its two phototype annotations, screens duplicates against all existing splits, augments training only, and trains ResNet50 from ImageNet with weighted cross-entropy. Validation and test assignments remain unchanged. Image bytes and manifest provenance are fingerprinted. Tests verify resumed downloads, corruption rejection, metadata matching and notebook syntax.

## Observed blocker

On 1 November 2026, three eligible original-image URLs spot checked (one for each class) returned HTTP 404. This is not evidence every source URL is broken. The source authors acknowledge broken links and provide a package request form:

- Authors: https://github.com/mattgroh/fitzpatrick17k
- Form linked by authors: https://forms.gle/4fS35Kg8x9pkG2Bn9
- Academic data-quality mirror: https://www.sfu.ca/~kabhishe/SkinDatasetsCritique/ — its image link redirected to Microsoft sign-in when checked.

Obtain the package through an authorized source and extract images under:
`MyDrive/cnn-skin-cancer-classification/Datasets/External_Fitzpatrick17k/images/`.
Then run notebook 09 on T4. No original-source downloads are attempted by default. Training stops if there are fewer than 20 additional verified SCC images or no additional recorded IV–VI examples for any of the three classes. The 20-image gate prevents an effectively empty experiment; it is not a statistical guarantee of sufficiency.

Agreement of image-based phototype annotations does not make labels clinically verified. Atlas diagnoses are not represented as biopsy-confirmed. External patient IDs are unavailable; duplicate screening cannot establish complete patient independence. More training representation does not itself establish reliable subgroup performance. Independent representative evaluation is still required before declaring the two gaps closed.

License stated by dataset authors: CC BY-NC-SA 3.0. Noncommercial research workflow only; cite Groh et al. 2021 and 2022 and preserve source attribution. Images remain outside GitHub. No access-request messages were sent on the user's behalf.
