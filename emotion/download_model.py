"""
Downloads the pretrained Emotion FER+ ONNX model on first run.

Model: emotion-ferplus-8.onnx
Source: Barsoum et al., "Training Deep Networks for Facial Expression
Recognition with Crowd-Sourced Label Distribution" (FER+ dataset),
distributed via the ONNX Model Zoo / Hugging Face mirror.
License: Apache-2.0.

The model is ~35MB and is cached locally after the first download, so
this only needs internet access once.
"""

import os
import urllib.request

# Hugging Face now hosts the file the ONNX Model Zoo used to serve
# directly (the original GitHub LFS copies were retired in mid-2025).
MODEL_MIRRORS = [
    "https://huggingface.co/onnxmodelzoo/emotion-ferplus-8/resolve/main/emotion-ferplus-8.onnx",
]


def ensure_model_downloaded(model_path: str) -> str:
    """
    Makes sure the FER+ ONNX model exists at model_path, downloading it
    from the first working mirror if it doesn't. Returns model_path.
    Raises RuntimeError with a clear message if every mirror fails
    (e.g. no internet on first run).
    """
    if os.path.exists(model_path) and os.path.getsize(model_path) > 1_000_000:
        return model_path

    os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
    tmp_path = model_path + ".part"

    last_error = None
    for url in MODEL_MIRRORS:
        try:
            print(f"Downloading emotion recognition model from {url} ...")
            urllib.request.urlretrieve(url, tmp_path)
            if os.path.getsize(tmp_path) < 1_000_000:
                raise RuntimeError("Downloaded file looks too small / incomplete.")
            os.replace(tmp_path, model_path)
            print("Emotion model downloaded successfully.")
            return model_path
        except Exception as e:  # noqa: BLE001 - we want to try every mirror
            last_error = e
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    raise RuntimeError(
        "Couldn't download the emotion recognition model "
        f"(last error: {last_error}). Check your internet connection, or "
        "manually download 'emotion-ferplus-8.onnx' from "
        "https://huggingface.co/onnxmodelzoo/emotion-ferplus-8 and place it at "
        f"'{model_path}'."
    )
