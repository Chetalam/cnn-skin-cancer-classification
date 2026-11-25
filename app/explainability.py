"""Occlusion sensitivity on the exact image and checkpoint of a saved review.

Method reference: https://captum.ai/api/occlusion.html
No training, diagnostic feature labels, or database writes occur here.
"""
from io import BytesIO
import hashlib
import numpy as np
from PIL import Image
from inference import CLASS_NAMES, inspect_package, _load_model
from images import validate_image

METHOD = 'Occlusion sensitivity v1; 7 x 7 tiles; mean RGB replacement'
LIMITATION = ('This map shows how masking image regions changes a model score. It does not identify a lesion boundary or prove a diagnosis. Background, lighting and the replacement colour can affect the result. It cannot establish normal skin or rule out cancer.')

# Plain-language colour guide shared by the app and the Word referral report.
# These describe changes in MODEL SCORES, never cancer locations or cancer risk.
COLOUR_GUIDE_TITLE = 'How to read the red and blue areas'
COLOUR_GUIDE_INTRO = (
    'The system checks 49 small parts of the image. It hides one part at a '
    'time and measures how the model score for its predicted class changes.'
)
COLOUR_GUIDE_RED = (
    'RED areas: When the system hid one of these areas, the model score '
    'went down. Information in this area helped produce the original score.'
)
COLOUR_GUIDE_BLUE = (
    'BLUE areas: When the system hid one of these areas, the model score '
    'went up. Information in this area had reduced the original score.'
)
COLOUR_GUIDE_STRENGTH = (
    'Stronger red or blue means a larger score change compared with other '
    'areas in this image. Uncoloured areas had little or no measured effect.'
)
COLOUR_GUIDE_EXAMPLE = (
    'Example: A Melanoma model score of 75% falls to 55% when one area is '
    'hidden. That is a drop of 20 percentage points in the MODEL SCORE, '
    'not a 20% change in a person\'s risk of cancer.'
)
COLOUR_GUIDE_CAUTION = (
    'IMPORTANT: Red does NOT mean cancer. Blue does NOT mean healthy or '
    'safe. The colours do not show where cancer is located, confirm '
    'a diagnosis, or replace a healthcare worker\'s assessment.'
)


def validate_scores(scores, count):
    scores = np.asarray(scores, dtype=float)
    if (scores.shape != (count, 3) or not np.isfinite(scores).all()
            or (scores < 0).any() or (scores > 1).any()
            or not np.allclose(scores.sum(axis=1), 1, atol=1e-5)):
        raise ValueError('Model returned invalid class scores.')
    return scores


def occlusion_map(rgb, score_fn, class_index, grid=7, batch_size=4):
    rgb = np.asarray(rgb, dtype=np.float32)
    if rgb.ndim != 3 or rgb.shape[2] != 3 or not np.isfinite(rgb).all():
        raise ValueError('Invalid RGB image.')
    if not 0 <= class_index < 3 or not 1 <= grid <= min(rgb.shape[:2]) or batch_size < 1:
        raise ValueError('Invalid occlusion configuration.')
    baseline = validate_scores(score_fn(rgb[None].copy()), 1)[0]
    ys = np.linspace(0, rgb.shape[0], grid + 1, dtype=int)
    xs = np.linspace(0, rgb.shape[1], grid + 1, dtype=int)
    fill = rgb.mean(axis=(0, 1))
    regions = [(r, c) for r in range(grid) for c in range(grid)]
    deltas = np.zeros((grid, grid))
    for start in range(0, len(regions), batch_size):
        subset = regions[start:start + batch_size]
        batch = np.repeat(rgb[None], len(subset), axis=0)
        for n, (r, c) in enumerate(subset):
            batch[n, ys[r]:ys[r+1], xs[c]:xs[c+1]] = fill
        scores = validate_scores(score_fn(batch), len(subset))
        for n, (r, c) in enumerate(subset):
            deltas[r, c] = baseline[class_index] - scores[n, class_index]
    return baseline, deltas


def png(image):
    stream = BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


def overlay_png(rgb, deltas):
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    maximum = float(np.abs(deltas).max())
    # Do not exaggerate numerical noise into a colourful explanation.
    if maximum < .0001:
        return png(Image.fromarray(rgb))
    # Use the same integer tile boundaries as the masking experiment.
    field = np.zeros(rgb.shape[:2])
    ys = np.linspace(0, rgb.shape[0], deltas.shape[0]+1, dtype=int)
    xs = np.linspace(0, rgb.shape[1], deltas.shape[1]+1, dtype=int)
    for r in range(deltas.shape[0]):
        for c in range(deltas.shape[1]):
            field[ys[r]:ys[r+1], xs[c]:xs[c+1]] = deltas[r, c] / maximum
    colour = np.where((field > 0)[..., None], [230, 55, 55], [35, 100, 220])
    alpha = (.6 * np.abs(field))[..., None]
    return png(Image.fromarray(np.uint8(np.clip(rgb * (1-alpha) + colour * alpha, 0, 255))))


def explain_saved_image(raw, prediction, expected_image_hash):
    validate_image(raw)
    digest = hashlib.sha256(raw).hexdigest()
    if not expected_image_hash or digest != expected_image_hash:
        raise ValueError('Upload the exact original image for this saved review. A thumbnail or edited image cannot be used.')
    if prediction.get('status') != 'predicted' or prediction.get('cancer_class') not in CLASS_NAMES:
        raise ValueError('A saved prediction is required for a visual explanation.')
    folder, metadata, checksum = inspect_package()
    identity = str(metadata.get('model_name', 'ResNet50')) + ' / ' + metadata['run_id'] + ' / ' + checksum
    if prediction.get('model_name') != identity:
        raise ValueError('The active model differs from this saved review. Restore its exact model package to explain it.')
    import tensorflow as tf
    model, lock = _load_model(str(folder), checksum)
    decoded = tf.io.decode_image(raw, channels=3, expand_animations=False)
    rgb = tf.image.resize(tf.cast(decoded, tf.float32), metadata['image_size'], method='bilinear').numpy()
    def score_fn(batch):
        inputs = tf.keras.applications.resnet50.preprocess_input(batch.copy())
        with lock:
            return np.asarray(model(inputs, training=False), dtype=float)
    scores = validate_scores(score_fn(rgb[None]), 1)[0]
    saved = np.array([prediction['scores'][name] for name in CLASS_NAMES])
    if not np.allclose(scores, saved, rtol=.001, atol=.0001):
        raise ValueError('Original scores do not match the saved review. Verify the package and preprocessing before generating an explanation.')
    index = CLASS_NAMES.index(prediction['cancer_class'])
    _, deltas = occlusion_map(rgb, score_fn, index)
    regions = sorted([dict(row=r+1, column=c+1, drop_pp=float(deltas[r,c]*100))
                      for r in range(7) for c in range(7)], key=lambda x: x['drop_pp'], reverse=True)
    return dict(method=METHOD, image_id=prediction['image_id'], image_hash=digest,
                model_name=identity, cancer_class=prediction['cancer_class'], scores=dict(prediction['scores']),
                regions=regions, max_abs_pp=float(np.abs(deltas).max()*100),
                overlay=overlay_png(rgb, deltas), original=png(Image.fromarray(np.uint8(np.clip(rgb,0,255)))))


def prediction_image_digest(prediction):
    return prediction.get('preview_sha256') or prediction.get('image_sha256')


def validate_explanation(explanation, prediction):
    if (explanation.get('method') != METHOD or not prediction_image_digest(prediction)
            or explanation.get('image_hash') != prediction_image_digest(prediction)
            or any(explanation.get(k) != prediction.get(k) for k in ('image_id','model_name','cancer_class'))):
        raise ValueError('The explanation does not belong to this saved prediction.')
    try:
        actual = [explanation['scores'][k] for k in CLASS_NAMES]
        saved = [prediction['scores'][k] for k in CLASS_NAMES]
        if not np.allclose(actual, saved, rtol=.001, atol=.0001):
            raise ValueError('Explanation scores do not match the saved prediction.')
    except (KeyError, TypeError) as exc:
        raise ValueError('Explanation scores are incomplete.') from exc
