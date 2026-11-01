"""Check a private checkpoint against its saved Colab validation reference."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from inference import inspect_package, predict_image

if __name__ == '__main__':
    folder, metadata, checksum = inspect_package()
    reference = json.loads((folder / 'reference_manifest.json').read_text())
    raw = (folder / 'reference_image.bin').read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference['image_sha256'] or checksum != reference['model_sha256']:
        raise ValueError('Reference or model checksum mismatch.')
    result = predict_image(raw, lesion_confirmed=True)
    expected = np.load(folder / 'reference_scores.npy', allow_pickle=False)
    actual = np.array([[result['scores'][name] for name in metadata['class_names']]])
    np.testing.assert_allclose(actual, expected, rtol=1e-3, atol=1e-4)
    print('PASS: local preprocessing, checkpoint loading, class order and scores match the saved Colab reference.')
    print('Model:',result['run_id'])
    print('This checks integration parity, not medical performance.')
