# vtp_lithophane/image_utils.py
import math
import os

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


class LithophaneImage:
    """
    Handles loading and querying image data for lithophane generation,
    including scaling based on physical print width and image aspect ratio.
    """

    def __init__(self, filepath: str, physical_print_width_mm: float):
        """
        Initializes the LithophaneImage by loading the image and calculating
        scaling parameters. The physical print height is derived from the
        physical width and the image's aspect ratio.

        Args:
            filepath: The path to the image file.
            physical_print_width_mm: The physical width of the total print volume in mm.

        Raises:
            FileNotFoundError: If the image file does not exist.
            IOError: If Pillow cannot open or process the image file.
            ValueError: If physical print width is not positive or image has invalid dimensions/aspect ratio.
        """
        if physical_print_width_mm <= 0:
            raise ValueError("Physical print width must be positive.")

        self.filepath = filepath
        self.physical_print_width_mm = physical_print_width_mm
        # Physical print height will be derived from image aspect ratio
        self.physical_print_height_mm = 0.0  # Will be calculated after image load
        self._image = None  # Store the Pillow image internally

        self._load_and_process_image()

    def _load_and_process_image(self):
        """Loads the image and calculates scaling parameters."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Image file not found: {self.filepath}")

        try:
            img = Image.open(self.filepath)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            self._image = img
        except Exception as e:
            raise IOError(
                f"Could not open or process image file {self.filepath}: {e}")

        img_width_px, img_height_px = self._image.size

        if img_width_px <= 0 or img_height_px <= 0:
            raise ValueError("Image dimensions must be positive.")

        img_aspect_ratio = img_width_px / img_height_px

        # Handle potential division by zero or non-finite aspect ratio
        if img_aspect_ratio == 0 or not math.isfinite(img_aspect_ratio):
            raise ValueError("Invalid image aspect ratio.")

        # --- Calculate physical print height based on width and image aspect ratio ---
        self.physical_print_height_mm = self.physical_print_width_mm / img_aspect_ratio

        # --- Calculate scaled image dimensions (will match physical print dimensions) ---
        self.scaled_img_physical_width_mm = self.physical_print_width_mm
        self.scaled_img_physical_height_mm = self.physical_print_height_mm  # Derived height

        # --- Calculate offset for centering (will be 0,0 as it fills the bounds) ---
        self.offset_x_mm = 0.0
        self.offset_y_mm = 0.0

        # Calculate scaling factors from physical mm to image pixels
        self.scale_x_mm_to_px = img_width_px / self.scaled_img_physical_width_mm
        self.scale_y_mm_to_px = img_height_px / self.scaled_img_physical_height_mm

    def get_pixel_value(self, query_x_mm: float, query_y_mm: float, binarize: bool = True) -> np.ndarray:
        """
        Maps a physical (X, Y) coordinate within the print bounds to an image pixel.
        Returns a (3,) numpy array representing RGB values. 
        If binarize is True, then this is mapped to zeros or ones. 
        If binarize is not True, then returns values 0-1.

        Args:
            query_x_mm: The X coordinate in mm within the physical print bounds (0 to physical_print_width_mm).
            query_y_mm: The Y coordinate in mm within the physical print bounds (0 to physical_print_height_mm).
            binarize: If True, returns 0 or 1. If False, returns the pixel value mapped to 0-1.

        Returns:
            0 or 1 if binarizing, float between 0 and 1 otherwise.
            Returns 1.0 if query is outside the defined physical print bounds.
        """
        WHITE = np.ones(3)

        if self._image is None:
            print("Error: Image not loaded.")
            return WHITE  # Return white/max value if not loaded

        img_width_px, img_height_px = self._image.size

        # --- Map query physical coordinate to pixel coordinate ---
        pixel_x = int(
            round(query_x_mm / self.physical_print_width_mm * (img_width_px - 1)))
        pixel_y = int(
            round(query_y_mm / self.physical_print_height_mm * (img_height_px - 1)))

        pixel_x = min(max(pixel_x, 0), img_width_px - 1)
        pixel_y = min(max(pixel_y, 0), img_height_px - 1)

        try:
            # Ensure pixel coordinates are non-negative
            if pixel_x < 0:
                pixel_x = 0
            if pixel_y < 0:
                pixel_y = 0

            rgb_values = WHITE
            if self._image.mode == 'RGB':
                rgb_values = np.array(self._image.getpixel((pixel_x, pixel_y)))
        except IndexError:
            # Safeguard against unexpected out of bounds
            print(
                f"Warning: Pixel query resulted in invalid pixel coordinates ({pixel_x}, {pixel_y}). Image size was {img_width_px}x{img_height_px}. Query was ({query_x_mm}, {query_y_mm}) mm. Treating as white/max value.")
            return WHITE  # Treat as white/max value on error

        # --- Return value based on binarize flag ---
        # Map 0-255 pixel value to 0-1 range
        rgb_values_normalized = rgb_values / 255.0

        if binarize:
            # Round to nearest integer (0 or 1) for binarization
            return np.round(np.mean(rgb_values_normalized)) * np.ones(3)
        else:
            # Return the normalized 0-1 value
            return rgb_values_normalized


# Example usage within the script
if __name__ == '__main__':
    # Create dummy image files
    dummy_filename = "dummy_binary_image_v6.png"
    dummy_gray_filename = "dummy_gray_image_v6.png"

    # Create a dummy binary image file (white with a black square)
    dummy_img_size_px = (200, 150)  # Example image size
    # Start with white (255 in 'L')
    dummy_img_data = Image.new('L', dummy_img_size_px, color=255)
    pixels = dummy_img_data.load()
    if pixels is None:
        raise RuntimeError("No data loaded for binary image.")
    # Draw a black square in the center (0 in 'L')
    square_size_px = (50, 50)
    square_start_x = (dummy_img_size_px[0] - square_size_px[0]) // 2
    square_start_y = (dummy_img_size_px[1] - square_size_px[1]) // 2
    for x in range(square_start_x, square_start_x + square_size_px[0]):
        for y in range(square_start_y, square_start_y + square_size_px[1]):
            pixels[x, y] = 0  # Black pixel
    dummy_img_data.save(dummy_filename)

    # Create a dummy grayscale image file (gradient)
    dummy_gray_img_size_px = (200, 150)
    dummy_gray_img_data = Image.new('L', dummy_gray_img_size_px)
    gray_pixels = dummy_gray_img_data.load()
    if gray_pixels is None:
        raise RuntimeError("No data loaded for gray image.")
    for i in range(dummy_gray_img_size_px[0]):
        for j in range(dummy_gray_img_size_px[1]):
            # Create a horizontal gradient from black (0) on left to white (255) on right
            gray_pixels[i, j] = int((i / dummy_gray_img_size_px[0]) * 255)
    dummy_gray_img_data.save(dummy_gray_filename)

    try:
        # Define physical print width
        physical_w = 100.0  # mm

        print(f"--- Testing with Binary Image ({dummy_filename}) ---")
        print(
            f"Dummy image pixel size: {dummy_img_size_px[0]}x{dummy_img_size_px[1]}")
        print(f"Physical print width input: {physical_w} mm")

        # Instantiate the LithophaneImage class with binary image
        lithophane_image_obj_binary = LithophaneImage(
            dummy_filename, physical_w)
        physical_h_binary = lithophane_image_obj_binary.physical_print_height_mm
        print(f"Derived physical print height: {physical_h_binary:.2f} mm")

        # Define query points for binary test
        query_points_binary = [
            (physical_w / 2.0, physical_h_binary / 2.0),  # Center (black square)
            (physical_w * 0.1, physical_h_binary * 0.1),  # Bottom-left white area
            (physical_w * 0.9, physical_h_binary * 0.9),  # Top-right white area
            (physical_w + 10.0, physical_h_binary / 2.0)  # Outside print area
        ]

        # --- Plotting for Binary Image ---
        fig_binary, ax_binary = plt.subplots()
        ax_binary.set_title(f"Binary Image Query Test ({dummy_filename})")
        ax_binary.set_xlabel("Physical X (mm)")
        ax_binary.set_ylabel("Physical Y (mm)")
        ax_binary.set_aspect('equal', adjustable='box')  # Keep aspect ratio

        # Display the image in the background, scaled to physical dimensions
        # Need to flip the image vertically for correct orientation on plot
        if lithophane_image_obj_binary._image is not None:
            ax_binary.imshow(lithophane_image_obj_binary._image,
                             extent=(0, physical_w, 0, physical_h_binary), origin='lower', cmap='gray')
        else:
            raise RuntimeError("Binary Image does not exist.")

        # Plot query points and annotations
        for i, (qx, qy) in enumerate(query_points_binary):
            ax_binary.plot(qx, qy, 'ro')  # Plot point as red circle

            # Get values from the LithophaneImage object
            val_bin = lithophane_image_obj_binary.get_pixel_value(
                qx, qy, binarize=True)
            val_raw = lithophane_image_obj_binary.get_pixel_value(
                qx, qy, binarize=False)

            # Get the actual pixel value at the mapped location for verification
            # Need to map physical query point back to pixel coordinates
            actual_pixel_values = "N/A"
            actual_pixel_values_norm = "N/A"
            try:
                if 0 <= qx < physical_w and 0 <= qy < physical_h_binary:
                    # Calculate pixel coordinates within the image
                    img_query_x_mm = qx - lithophane_image_obj_binary.offset_x_mm  # Should be 0
                    img_query_y_mm = qy - lithophane_image_obj_binary.offset_y_mm  # Should be 0
                    px = min(int(img_query_x_mm * lithophane_image_obj_binary.scale_x_mm_to_px),
                             lithophane_image_obj_binary._image.size[0] - 1)
                    py = min(int((lithophane_image_obj_binary.scaled_img_physical_height_mm - img_query_y_mm) *
                             lithophane_image_obj_binary.scale_y_mm_to_px), lithophane_image_obj_binary._image.size[1] - 1)

                    # Ensure pixel coordinates are non-negative before getting pixel
                    if px >= 0 and py >= 0:
                        actual_pixel_values = np.array(lithophane_image_obj_binary._image.getpixel(
                            (px, py)))
                        actual_pixel_values_norm = actual_pixel_values / 255.0

                # If outside print bounds, leave as "N/A"
            except Exception as e:
                actual_pixel_values = f"Error: {e}"
                actual_pixel_values_norm = f"Error: {e}"

            # Safely format actual_pixel_value_norm
            if isinstance(actual_pixel_values_norm, np.ndarray):
                norm_display = '(' + \
                    ", ".join(f"{v:.2f}" for v in actual_pixel_values_norm)
            elif isinstance(actual_pixel_values_norm, (int, float)):
                norm_display = f"{actual_pixel_values_norm:.2f}"
            else:
                norm_display = str(actual_pixel_values_norm)

            annotation_text = f"Q{i+1}: ({qx:.1f}, {qy:.1f}) mm\nReturned: Bin={val_bin},\nRaw={val_raw},\nNorm: {norm_display}"
            ax_binary.annotate(annotation_text, (qx, qy), textcoords="offset points", xytext=(
                10, 10), ha='left', fontsize=8, bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

        ax_binary.set_xlim(0, physical_w)
        ax_binary.set_ylim(0, physical_h_binary)
        ax_binary.grid(True)

        print(
            f"\n--- Testing with Grayscale Image ({dummy_gray_filename}) ---")
        print(
            f"Dummy image pixel size: {dummy_gray_img_size_px[0]}x{dummy_gray_img_size_px[1]}")
        print(f"Physical print width input: {physical_w} mm")

        # Instantiate the LithophaneImage class with grayscale image
        lithophane_image_obj_gray = LithophaneImage(
            dummy_gray_filename, physical_w)
        physical_h_gray = lithophane_image_obj_gray.physical_print_height_mm
        print(f"Derived physical print height: {physical_h_gray:.2f} mm")

        # Define query points for grayscale test
        query_points_gray = [
            (physical_w * 0.1, physical_h_gray / 2.0),  # Left side (dark)
            (physical_w * 0.5, physical_h_gray / 2.0),  # Center (mid-gray)
            (physical_w * 0.9, physical_h_gray / 2.0),  # Right side (light)
            (physical_w / 2.0, physical_h_gray + 10.0)  # Outside print area
        ]

        # --- Plotting for Grayscale Image ---
        fig_gray, ax_gray = plt.subplots()
        ax_gray.set_title(
            f"Grayscale Image Query Test ({dummy_gray_filename})")
        ax_gray.set_xlabel("Physical X (mm)")
        ax_gray.set_ylabel("Physical Y (mm)")
        ax_gray.set_aspect('equal', adjustable='box')  # Keep aspect ratio

        # Display the image in the background, scaled to physical dimensions
        # Need to flip the image vertically for correct orientation on plot
        if lithophane_image_obj_gray._image is not None:
            ax_gray.imshow(lithophane_image_obj_gray._image,
                           extent=(0, physical_w, 0, physical_h_gray), origin='lower', cmap='gray')
        else:
            raise RuntimeError("No data for grayscale image.")

        # Plot query points and annotations
        for i, (qx, qy) in enumerate(query_points_gray):
            ax_gray.plot(qx, qy, 'ro')  # Plot point as red circle

            # Get values from the LithophaneImage object
            val_bin = lithophane_image_obj_gray.get_pixel_value(
                qx, qy, binarize=True)
            val_raw = lithophane_image_obj_gray.get_pixel_value(
                qx, qy, binarize=False)

            # Get the actual pixel value at the mapped location for verification
            actual_pixel_values = "N/A"
            actual_pixel_values_norm = "N/A"
            try:
                if 0 <= qx < physical_w and 0 <= qy < physical_h_gray:
                    # Calculate pixel coordinates within the image
                    img_query_x_mm = qx - lithophane_image_obj_gray.offset_x_mm  # Should be 0
                    img_query_y_mm = qy - lithophane_image_obj_gray.offset_y_mm  # Should be 0
                    px = min(int(img_query_x_mm * lithophane_image_obj_gray.scale_x_mm_to_px),
                             lithophane_image_obj_gray._image.size[0] - 1)
                    py = min(int((lithophane_image_obj_gray.scaled_img_physical_height_mm - img_query_y_mm) *
                             lithophane_image_obj_gray.scale_y_mm_to_px), lithophane_image_obj_gray._image.size[1] - 1)

                    # Ensure pixel coordinates are non-negative before getting pixel
                    if px >= 0 and py >= 0:
                        actual_pixel_values = np.array(lithophane_image_obj_gray._image.getpixel(
                            (px, py)))
                        actual_pixel_values_norm = actual_pixel_values / 255.0
                    else:
                        actual_pixel_values = "Negative Coords"
                        actual_pixel_values_norm = "Negative Coords"
                # If outside print bounds, leave as "N/A"
            except Exception as e:
                actual_pixel_values = f"Error: {e}"
                actual_pixel_values_norm = f"Error: {e}"

            # Safely format actual_pixel_value_norm
            if isinstance(actual_pixel_values_norm, np.ndarray):
                norm_display = '(' + \
                    ", ".join(f"{v:.2f}" for v in actual_pixel_values_norm)
            elif isinstance(actual_pixel_values_norm, (int, float)):
                norm_display = f"{actual_pixel_values_norm:.2f}"
            else:
                norm_display = str(actual_pixel_values_norm)

            annotation_text = f"Q{i+1}: ({qx:.1f}, {qy:.1f}) mm\nReturned: Bin={val_bin},\nRaw={val_raw},\nNorm: {norm_display}"
            ax_gray.annotate(annotation_text, (qx, qy), textcoords="offset points", xytext=(
                10, 10), ha='left', fontsize=8, bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

        ax_gray.set_xlim(0, physical_w)
        ax_gray.set_ylim(0, physical_h_gray)
        ax_gray.grid(True)

        # Show both plots
        plt.show()

    except (FileNotFoundError, IOError, ValueError) as e:
        print(f"Error during LithophaneImage initialization or usage: {e}")
    except ImportError:
        print("Pillow or Matplotlib library not found. Please install them: pip install Pillow matplotlib")
    except Exception as e:
        print(f"An unexpected error occurred during example usage: {e}")
    finally:
        # Clean up the dummy files
        if os.path.exists(dummy_filename):
            os.remove(dummy_filename)
        if os.path.exists(dummy_gray_filename):
            os.remove(dummy_gray_filename)
