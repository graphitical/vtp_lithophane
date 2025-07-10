import numpy as np


def _build_image_lut_interpolated() -> dict[int, dict[int, np.ndarray]]:
    """
    Builds a lookup table (LUT) for interpolating lithophane layer values into two layers.
    The LUT is constructed based on known values for specific quantization levels from rendered images.
    """
    return {
        2: {
            0: np.array([[255.0, 255.0, 0.0], [204.0, 153.0, 0.0]], dtype=np.float32),
            1: np.array([[0.0, 0.0, 0.0], [50.0, 153.0, 0.0]], dtype=np.float32),
        },
        3: {
            0: np.array([[255.0, 255.0, 0.0], [204.0, 153.0, 0.0]], dtype=np.float32),
            1: np.array([[101.0, 102.0, 0.0], [204.0, 204.0, 0.0]], dtype=np.float32),
            2: np.array([[0.0, 0.0, 0.0], [50.0, 153.0, 0.0]], dtype=np.float32),
        },
        4: {
            0: np.array([[255.0, 255.0, 0.0], [204.0, 153.0, 0.0]], dtype=np.float32),
            1: np.array([[153.0, 204.0, 0.0], [204.0, 51.0, 0.0]], dtype=np.float32),
            2: np.array([[50.0, 153.0, 0.0], [255.0, 51.0, 0.0]], dtype=np.float32),
            3: np.array([[0.0, 0.0, 0.0], [50.0, 153.0, 0.0]], dtype=np.float32),
        },
        5: {
            0: np.array([[255.0, 255.0, 0.0], [204.0, 153.0, 0.0]], dtype=np.float32),
            1: np.array([[204.0, 0.0, 0.0], [204.0, 153.0, 0.0]], dtype=np.float32),
            2: np.array([[101.0, 102.0, 0.0], [204.0, 204.0, 0.0]], dtype=np.float32),
            3: np.array([[50.0, 102.0, 0.0], [101.0, 204.0, 0.0]], dtype=np.float32),
            4: np.array([[0.0, 0.0, 0.0], [50.0, 153.0, 0.0]], dtype=np.float32),
        }
    }


LUT = _build_image_lut_interpolated()
