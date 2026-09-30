import io
import warnings

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError


st.set_page_config(
    page_title="Skin Lesion Classification",
    page_icon="🔬",
    layout="wide",
)

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


def load_image(uploaded_file):
    """Validate the uploaded file and return an RGB preview."""
    if uploaded_file.size > MAX_FILE_BYTES:
        raise ValueError("Please upload an image smaller than 10 MB.")

    data = uploaded_file.getvalue()

    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)

        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise ValueError("Please upload a genuine JPG or PNG image.")

            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError(
                    "This image is too large. Please use an image "
                    "with no more than 20 million pixels."
                )

            image.verify()

        # Reopen after verification to decode the image.
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            return ImageOps.exif_transpose(image).convert("RGB")


with st.sidebar:
    st.header("About the project")
    st.write(
        "A CNN-based research project for classifying skin lesion "
        "images into three target categories."
    )
    st.markdown(
        "- Melanoma\n"
        "- Basal Cell Carcinoma (BCC)\n"
        "- Squamous Cell Carcinoma (SCC)"
    )

    st.divider()
    st.subheader("Application status")
    st.info("Interface prototype — model integration pending.")

    st.caption(
        "The current prototype previews uploaded images. "
        "It does not produce a diagnosis."
    )


st.title("Skin Lesion Classification")
st.write(
    "Upload a skin lesion image to preview it and explore "
    "the application's analysis workflow."
)

st.warning(
    "Research prototype only. This application does not provide "
    "a medical diagnosis or replace assessment by a qualified "
    "healthcare professional."
)

upload_column, results_column = st.columns(2, gap="large")

image = None

with upload_column:
    st.subheader("1. Upload an image")
    st.caption("Accepted formats: JPG, JPEG and PNG. Maximum size: 10 MB.")

    uploaded_file = st.file_uploader(
        "Choose a skin lesion image",
        type=["jpg", "jpeg", "png"],
        help="Use an image without identifying patient information.",
    )

    if uploaded_file is None:
        st.info("Upload an image to begin.")
    else:
        try:
            image = load_image(uploaded_file)

        except ValueError as exc:
            st.error(str(exc))

        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            Image.DecompressionBombWarning,
            Image.DecompressionBombError,
        ):
            st.error(
                "The image could not be read safely. "
                "Please choose another JPG or PNG file."
            )

        if image is not None:
            st.subheader("2. Image preview")
            st.image(
                image,
                caption=uploaded_file.name,
                use_column_width=True,
            )

            st.caption(
                f"Dimensions: {image.width} × {image.height} pixels "
                f"• File size: {uploaded_file.size / 1024:.1f} KB"
            )
            st.success("Image loaded successfully.")


with results_column:
    st.subheader("3. Analysis results")

    st.write(
        "The trained model will eventually display a predicted "
        "category and model scores here."
    )

    analyse = st.button(
        "Analyse image",
        type="primary",
        disabled=image is None,
        use_container_width=True,
    )

    if analyse and image is not None:
        st.info(
            "Your image is ready. Classification is unavailable "
            "because a trained model has not yet been integrated."
        )
        st.write("**Predicted category:** Unavailable")
        st.write("**Model score:** Unavailable")

    elif image is not None:
        st.info("Click Analyse image to demonstrate the next step.")
    else:
        st.info("Results will appear here after a valid image is uploaded.")


st.divider()

with st.expander("How to use this prototype"):
    st.markdown(
        "1. Upload a JPG or PNG image.\n"
        "2. Check the image preview.\n"
        "3. Click **Analyse image**.\n"
        "4. Review the model availability message."
    )
    st.write(
        "Image validation checks file readability and size. "
        "It does not establish whether the image depicts a skin lesion."
    )

st.caption(
    "Prototype uploads are processed in memory; this code does not "
    "write uploaded images to disk."
)