"""Experimental, versioned inference on original bytes; no model training in the app."""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import threading
import numpy as np

CLASS_NAMES = ['BCC', 'Melanoma', 'SCC']
DEFAULT_PACKAGE = Path(__file__).parent / 'models' / 'active'


def package_path():
    return Path(os.environ.get('SKIN_MODEL_DIR', str(DEFAULT_PACKAGE))).resolve()


def inspect_package():
    folder = package_path()
    try:
        metadata = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError('Model package unavailable. Install model.keras and metadata.json in app/models/active.') from exc
    if metadata.get('class_names') != CLASS_NAMES:
        raise ValueError('Model class order must be BCC, Melanoma, SCC.')
    if metadata.get('preprocessing') != 'resnet50' or metadata.get('preprocessing_location') != 'outside saved model':
        raise ValueError('This integration supports the ResNet50 external preprocessing contract only.')
    if metadata.get('decode') != 'tf.io.decode_image channels=3; no EXIF orientation transform':
        raise ValueError('Model image decoding contract is unsupported.')
    if not isinstance(metadata.get('run_id'), str) or not metadata['run_id'].strip():
        raise ValueError('Model run identifier is missing.')
    size = metadata.get('image_size')
    if not isinstance(size, list) or len(size) != 2 or any(type(x) is not int or not 16 <= x <= 1024 for x in size):
        raise ValueError('Invalid model input dimensions.')
    artifact = folder / 'model.keras'
    if not artifact.is_file():
        raise ValueError('model.keras is missing from the model package.')
    digest = _sha256(artifact)
    if digest != metadata.get('model_sha256'):
        raise ValueError('Model checksum verification failed. Copy the complete original package.')
    return folder, metadata, digest


def _sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


@lru_cache(maxsize=2)
def _load_model(folder, checksum):
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise ValueError('Install the app inference requirements before analysing images.') from exc
    # The cache key includes the verified checksum, so a new checkpoint loads separately.
    path = Path(folder) / 'model.keras'
    if _sha256(path) != checksum:
        raise ValueError('Model changed while loading. Retry with a complete package.')
    try:
        model = tf.keras.models.load_model(path, compile=False, safe_mode=True)
    except Exception as exc:
        raise ValueError('The model could not be loaded. Check the TensorFlow/Keras environment and package.') from exc
    return model, threading.Lock()


def prepare_image(raw, metadata):
    # Match notebook 07 exactly: original bytes, RGB, no EXIF transpose, bilinear stretch.
    import tensorflow as tf
    image = tf.io.decode_image(raw, channels=3, expand_animations=False)
    image.set_shape([None, None, 3])
    image = tf.image.resize(tf.cast(image, tf.float32), metadata['image_size'], method='bilinear')
    return tf.keras.applications.resnet50.preprocess_input(image)[None, ...]


def predict_image(raw, *, lesion_confirmed=False):
    if lesion_confirmed is not True:
        raise ValueError('A clearly visible lesion must be confirmed before experimental classification. This is a user check, not automated lesion detection.')
    # Reuse upload validation for byte size, genuine type and pixel-limit enforcement.
    from images import validate_image
    validate_image(raw)
    folder, metadata, checksum = inspect_package()
    model, lock = _load_model(str(folder), checksum)
    if tuple(model.input_shape[1:]) != (*metadata['image_size'], 3) or model.output_shape[-1] != 3:
        raise ValueError('Loaded model shape differs from its metadata.')
    try:
        inputs = prepare_image(raw, metadata)
        with lock:
            scores = np.asarray(model(inputs, training=False), dtype=float)
    except Exception as exc:
        raise ValueError('Inference failed. The review can be saved without a prediction.') from exc
    if scores.shape != (1, 3) or not np.isfinite(scores).all() or (scores < 0).any() or (scores > 1).any() or not np.allclose(scores.sum(), 1, atol=1e-5):
        raise ValueError('Model returned invalid class scores.')
    return dict(scores=dict(zip(CLASS_NAMES, map(float, scores[0]))),
                model_name=str(metadata.get('model_name', 'ResNet50')),
                run_id=str(metadata['run_id']), model_sha256=checksum,
                artifact_path=str(folder / 'model.keras'),
                preprocessing='resnet50; RGB original bytes; no EXIF transform; bilinear ' + str(metadata['image_size']))


def evaluation_metrics():
    folder, metadata, checksum = inspect_package()
    path = folder / 'test_metrics.json'
    if not path.exists():
        return None
    metrics = json.loads(path.read_text(encoding='utf-8'))
    if metrics.get('model_sha256') != checksum or metrics.get('source_run_id') != metadata['run_id']:
        raise ValueError('Evaluation report does not match the active checkpoint.')
    return metrics
