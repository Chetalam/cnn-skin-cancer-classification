# Private active experimental model

Extract notebook 10's exported ZIP into `app/models/active/`. Required: model.keras, metadata.json; include test_metrics.json and per_class_metrics.csv for evaluation analytics and the three reference files for verification. Do not create an extra nested export folder.

Set SKIN_MODEL_DIR to use another package directory. The model checksum identifies cached loading and stored prediction versions. Retain historical packages. Replace the active package while the app is stopped, verify it, then restart. Training writes to separate Drive run folders and never modifies a checkpoint while the app is using it.

No model artifacts, reference images or database files belong in GitHub. Runtime packages are ignored. Run `python scripts/verify_model_package.py` before a demonstration.
