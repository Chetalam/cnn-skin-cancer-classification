"""Verify the private active package without database writes."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from inference import inspect_package, predict_image, CLASS_NAMES
from explainability import explain_saved_image, validate_explanation

if __name__ == '__main__':
    folder, metadata, checksum = inspect_package()
    raw = (folder / 'reference_image.bin').read_bytes()
    manifest = json.loads((folder / 'reference_manifest.json').read_text())
    digest = hashlib.sha256(raw).hexdigest()
    if digest != manifest['image_sha256'] or checksum != manifest['model_sha256']:
        raise ValueError('Reference or model checksum mismatch.')
    # The packaged validation reference is a known in-scope fixture.
    result = predict_image(raw, lesion_confirmed=True, limitation_acknowledged=True)
    reference = np.load(folder / 'reference_scores.npy', allow_pickle=False).reshape(-1)
    np.testing.assert_allclose([result['scores'][k] for k in CLASS_NAMES], reference, rtol=.001, atol=.0001)
    label = max(CLASS_NAMES, key=result['scores'].get)
    prediction = dict(image_id=0, status='predicted', cancer_class=label, scores=result['scores'],
                      image_sha256=digest, model_name=result['model_name']+' / '+result['run_id']+' / '+checksum)
    explanation = explain_saved_image(raw, prediction, digest)
    validate_explanation(explanation, prediction)
    assert len(explanation['regions']) == 49
    print('PASS: reference scores, image/model binding and 49-region explanation verified.')
    print('This checks implementation, not clinical reliability or normal-skin detection.')
