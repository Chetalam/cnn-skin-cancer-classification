import hashlib
import io
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError

def validate_image(data):
    if not data or len(data)>10*1024*1024:
        raise ValueError('Choose a nonempty image smaller than 10 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as img:
                if img.format not in {'JPEG','PNG'}:
                    raise ValueError('Choose a genuine JPG or PNG image.')
                if img.width*img.height>20_000_000:
                    raise ValueError('Use an image with no more than 20 million pixels.')
                if getattr(img,'n_frames',1)>1:
                    raise ValueError('Choose a still image rather than an animation.')
                img.verify()
            with Image.open(io.BytesIO(data)) as img:
                img.load()
                image = ImageOps.exif_transpose(img).convert('RGB')
        return image, hashlib.sha256(data).hexdigest()
    except (UnidentifiedImageError,OSError,SyntaxError,Image.DecompressionBombError,Image.DecompressionBombWarning) as exc:
        raise ValueError('The image could not be read. Choose another JPG or PNG.') from exc