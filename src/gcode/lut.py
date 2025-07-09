import numpy as np


def _build_image_lut_interpolated() -> np.ndarray:
    """
    Builds a lookup table (LUT) for interpolating lithophane layer values into two layers.
    The LUT is constructed based on known values for specific quantization levels from rendered images.
    """
    known = {
        0:   np.array([[51, 102,   0],
                       [102, 102,   0]], dtype=np.float32),
        127: np.array([[51, 204,   0],
                       [255, 102,   0]], dtype=np.float32),
        255: np.array([[255, 204,   0],
                       [255, 204,   0]], dtype=np.float32),
    }

    # 2. Extract sorted keys and stack values into shape (K, 2, 3)
    keys = np.array(sorted(known.keys()), dtype=np.float32)           # (K,)
    vals = np.stack([known[k] for k in keys], axis=0)               # (K, 2, 3)

    # 3. Prepare the full index and empty LUT
    xs = np.arange(256, dtype=np.float32)                            # (256,)
    lut = np.empty(
        (256, vals.shape[1], vals.shape[2]), dtype=np.uint8)  # (256,2,3)

    # 4. For each layer and each “channel”, interpolate
    for layer in range(vals.shape[1]):
        for ch in range(vals.shape[2]):
            lut[:, layer, ch] = np.interp(xs, keys, vals[:, layer, ch])

    return lut


LUT = _build_image_lut_interpolated()
