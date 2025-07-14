import numpy as np

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
