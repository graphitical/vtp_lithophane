import numpy as np
from PySide6.QtWidgets import QMessageBox

# for (1.5, 4.5) dL pair
# def _build_image_lut() -> dict[int, dict[int, np.ndarray]]:
#     """
#     Builds a lookup table (LUT) for interpolating lithophane layer values into two layers.
#     The LUT is constructed based on known values for specific quantization levels from rendered images.
#     """
#     return {
#         2: {
#             0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
#             1: np.array([[0, 0, 0], [50, 153, 0]], dtype=np.uint8),
#         },
#         3: {
#             0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
#             1: np.array([[101, 102, 0], [204, 204, 0]], dtype=np.uint8),
#             2: np.array([[0, 0, 0], [50, 153, 0]], dtype=np.uint8),
#         },
#         4: {
#             0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
#             1: np.array([[153, 204, 0], [204, 51, 0]], dtype=np.uint8),
#             2: np.array([[50, 153, 0], [255, 51, 0]], dtype=np.uint8),
#             3: np.array([[0, 0, 0], [50, 153, 0]], dtype=np.uint8),
#         },
#         5: {
#             0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
#             1: np.array([[204, 0, 0], [204, 153, 0]], dtype=np.uint8),
#             2: np.array([[101, 102, 0], [204, 204, 0]], dtype=np.uint8),
#             3: np.array([[50, 102, 0], [101, 204, 0]], dtype=np.uint8),
#             4: np.array([[0, 0, 0], [50, 153, 0]], dtype=np.uint8),
#         }
#     }


# for (1.5, 1.5) dL pair
# def _build_image_lut() -> dict[int, dict[int, np.ndarray]]:
#     """
#     Builds a lookup table (LUT) for interpolating lithophane layer values into two layers.
#     The LUT is constructed based on known values for specific quantization levels from rendered images.
#     """
#     return {
#         2: {
#             0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
#             1: np.array([[0, 0, 0], [0, 0, 0]], dtype=np.uint8),
#         },
#         3: {
#             0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
#             1: np.array([[101, 255, 0], [101, 153, 0]], dtype=np.uint8),
#             2: np.array([[0, 0, 0], [0, 0, 0]], dtype=np.uint8),
#         },
#         4: {
#             0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
#             1: np.array([[153, 51, 0], [204, 102, 0]], dtype=np.uint8),
#             2: np.array([[204, 153, 0], [153, 0, 0]], dtype=np.uint8),
#             3: np.array([[0, 0, 0], [0, 0, 0]], dtype=np.uint8),
#         },
#         5: {
#             0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
#             1: np.array([[255, 204, 0], [0, 51, 0]], dtype=np.uint8),
#             2: np.array([[101, 255, 0], [101, 153, 0]], dtype=np.uint8),
#             3: np.array([[101, 153, 0], [204, 153, 0]], dtype=np.uint8),
#             4: np.array([[0, 0, 0], [0, 0, 0]], dtype=np.uint8),
#         }
#     }

# 1.5/4.5 LUT, but new as of 250714
def _build_image_lut() -> dict[int, dict[int, np.ndarray]]:
    """
    Builds a lookup table (LUT) for interpolating lithophane layer values into two layers.
    The LUT is constructed based on known values for specific quantization levels from rendered images.
    """
    return {
        # value of -1 is used for naive interpolation
        -1: {
            0: np.array([[255, 255, 0], [255, 255, 0]], dtype=np.uint8),
            1: np.array([[0, 0, 0], [0, 0, 0]], dtype=np.uint8),
        },
        2: {
            0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
            1: np.array([[0, 0, 0], [0, 255, 0]], dtype=np.uint8),
        },
        3: {
            0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
            1: np.array([[101, 153, 0], [153, 0, 0]], dtype=np.uint8),
            2: np.array([[0, 0, 0], [0, 255, 0]], dtype=np.uint8),
        },
        4: {
            0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
            1: np.array([[204, 0, 0], [101, 102, 0]], dtype=np.uint8),
            2: np.array([[50, 255, 0], [255, 51, 0]], dtype=np.uint8),
            3: np.array([[0, 0, 0], [0, 255, 0]], dtype=np.uint8),
        },
        5: {
            0: np.array([[255, 255, 0], [204, 153, 0]], dtype=np.uint8),
            1: np.array([[204, 255, 0], [101, 153, 0]], dtype=np.uint8),
            2: np.array([[101, 153, 0], [153, 0, 0]], dtype=np.uint8),
            3: np.array([[0, 255, 0], [255, 153, 0]], dtype=np.uint8),
            4: np.array([[0, 0, 0], [0, 255, 0]], dtype=np.uint8),
        }
    }


LUT = _build_image_lut()


def interpolate_lut(num_levels: int) -> np.ndarray:
    tmp_lut = LUT.get(num_levels)
    if tmp_lut is None:
        raise ValueError(f"LUT for level {num_levels} not found.")

    keys = np.array(sorted(tmp_lut.keys()), dtype=np.float32)
    vals = np.stack([tmp_lut[k] for k in keys], axis=0, dtype=np.float32)
    # Normalize keys to 0-255 range now that we've referenced created vals
    keys = (keys / np.max(keys) * 255.0).astype(dtype=np.uint8)
    print(np.max(keys), np.min(keys))
    xs = np.arange(256, dtype=np.float32)
    # print(xs.shape)
    level_lut = np.empty(
        (256, vals.shape[1], vals.shape[2]), dtype=np.uint8)
    # print(level_lut.shape)
    for layer in range(vals.shape[1]):
        for ch in range(vals.shape[2]):
            # Interpolate the values for each channel
            level_lut[:, layer, ch] = np.interp(
                xs, keys, vals[:, layer, ch])

    tmp_lut_str = ''
    for i in range(len(tmp_lut)):
        tmp_lut_str += f'{i}: {tmp_lut[i]}\n'
    QMessageBox.warning(
        None,
        "Warning",
        f"Using fallback interpolation between {len(tmp_lut)} levels.\n{tmp_lut_str}",
    )

    return level_lut
