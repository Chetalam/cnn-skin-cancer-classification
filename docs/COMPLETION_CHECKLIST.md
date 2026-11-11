# Completion checklist and blockers

## Concurrent tasks

1. Run notebook 07's bounded focal-loss training and validation comparison in Colab T4. No earlier training runs need to execute again.
2. Obtain permitted external-data access and inspect aggregate diagnosis/skin-group counts. Access approval, relevant class counts and patient identifiers are not assumed.
3. Run backend checks and manually verify both roles, English/Kiswahili navigation, review CRUD, deactivation/reactivation and database health.

GPU availability, data access and measured scores determine completion. A six-hour work window does not establish performance.

## Fix and evaluate one candidate

Review validation macro F1 and SCC precision/recall/F1. Fix the exact artifact hash, source run, class order, preprocessing and input size before enabling one follow-up test evaluation. Retain results even if targets fail. Report accuracy ≥0.85, macro F1 >0.80 and each class's sensitivity ≥0.80 separately.

The test set was previously inspected, so do not call new results an untouched final assessment. Current IV–VI support cannot establish skin-tone reliability; missing metadata remains unknown.

## Integration gate

The user requested integration remain paused until requirements are met. Current known results miss macro F1/per-class sensitivity targets and lack adequate darker-skin evidence. Report unmet requirements rather than silently lowering thresholds, changing labels, moving held-out cases or generating passing results.

If targets remain unmet, pursue a justified data/model change or discuss an explicitly limited research-prototype scope with the supervisor/user.

## Integration after the decision

- Verify a compatible local TensorFlow/Keras environment and load the real model with `compile=False`.
- Match decoding, EXIF handling, resize and preprocessing to saved reference outputs.
- Cache a verified completed package outside Git.
- Atomically save model version, class and all three scores in existing SQLite tables, with worker ownership enforced.
- Test invalid images, missing/corrupt models, repeat submissions, history export/deletion and account controls.
- Update English and Kiswahili messages and retain the research-use notice.
- Run end-to-end tests; individual uploads do not replace dataset evaluation.

## Handover

Save notebooks with actual outputs to Drive/GitHub. Keep weights, datasets, databases and backups private. Document successful and unsuccessful experiments, subgroup sample sizes, installation steps, verified package hash/path and remaining limitations. Describe integration according to what actually ran.
