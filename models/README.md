# Saved model packages

Drive root: `MyDrive/cnn-skin-cancer-classification/Models/`

- `Transfer_Learning/<run_id>/<architecture>/best.keras`: trained checkpoint, with `metadata.json`, checkpoint metadata and weights.
- `Selected/<package>/model.keras`: candidate package with `metadata.json` and `class_names.json`.

The final notebook writes a new selected package and preserves prior packages. Metadata `run_id` is the actual training source; `comparison_run_id` is the comparison that selected it. They may differ.

Before integration verify:

- Exact artifact SHA-256 and class order **BCC, Melanoma, SCC**.
- Metadata input size: candidates may use 224 × 224 or 320 × 320.
- RGB decoding, bilinear stretching and architecture-specific external preprocessing. Do not apply generic `/255` to every model.
- Compatible TensorFlow/Keras versions. Earlier Colab runs used TensorFlow 2.21 / Keras 3.13; TensorFlow 2.15 is not a verified loading environment.
- Reference outputs from the source training run.

Training decoded pixels without EXIF orientation changes. The app currently orients previews with EXIF: integration must explicitly resolve that difference before claiming preprocessing parity.

Inference must use a completed, verified, versioned checkpoint, never a file being overwritten during training. Scores are not calibrated clinical probabilities; no benign/no-cancer class exists. Integration remains pending. Do not commit weights or add dummy predictions.
