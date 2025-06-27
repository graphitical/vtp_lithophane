# vtp_lithophane/parameters.py
import math  # Import math for pi
import os
from dataclasses import dataclass, field


@dataclass
class PrintParameters:
    """
    A dataclass to hold all user-definable parameters for lithophane generation.
    """
    # Image and Physical Dimensions
    image_filepath: str
    physical_print_width_mm: float
    num_layers: int

    # VTP Parameters (High Density / Low Density)
    v_star_hd: float
    v_star_ld: float
    h_star_hd: float
    h_star_ld: float

    # Physical Constants and Flow Rate
    alpha: float  # Die swell constant
    e_dot: float  # Material flow rate (mm/min) - Units clarified

    # Toolpath Parameters
    line_spacing_mm: float  # Your 'dL' or lambda
    # Physical distance step for image sampling in adaptive segmentation - Renamed
    sampling_resolution_mm: float
    dz_mm: float  # Nominal layer height increment

    # Gcode Files
    start_gcode_filepath: str
    end_gcode_filepath: str

    # Travel speed (mm/min) - Default value
    f_travel: float = field(default=3000.0)
    D_N: float = field(default=0.4)  # Nozzle diameter (mm)
    D_F: float = field(default=1.75)  # Filament diameter (mm)

    # Printer temperature settings
    bed_temp: float = field(default=60.0)  # Bed temperature (°C)
    nozzle_temp: float = field(default=200.0)  # Nozzle temperature (°C)
    # Multiplier for extrusion flow rate
    extrusion_multiplier: float = field(
        default=100.0)  # M221 value in percentage

    # Retraction settings
    retract_length: float = field(default=5.0)  # Retraction length (mm)
    retract_speed: float = field(default=2000.0)  # Retraction speed (mm/min)

    # Optional/Advanced Parameters
    printer_bed_size_mm: tuple[float, float] = field(
        default=(250.0, 210.0))  # Default to common bed size

    param_change_threshold: float = field(default=0.05)

    def __post_init__(self):
        """Perform validation after initialization."""
        # if not os.path.exists(self.image_filepath):
        #     raise FileNotFoundError(
        #         f"Image file not found: {self.image_filepath}")
        # if not os.path.exists(self.start_gcode_filepath):
        #     raise FileNotFoundError(
        #         f"Start Gcode file not found: {self.start_gcode_filepath}")
        # if not os.path.exists(self.end_gcode_filepath):
        #     raise FileNotFoundError(
        #         f"End Gcode file not found: {self.end_gcode_filepath}")

        # Filament cross-sectional area
        self.A_F = math.pi * (self.D_F / 2) ** 2
        self.A_T = math.pi * (self.alpha * self.D_N / 2) ** 2

        # Add more validation for numerical parameters (e.g., must be positive)
        if self.physical_print_width_mm <= 0:
            raise ValueError("Physical print width must be positive.")
        if self.num_layers <= 0:
            raise ValueError("Number of layers must be positive.")
        if self.v_star_hd < 0 or self.v_star_ld < 0:  # Assuming V* should be non-negative
            raise ValueError("V* values must be non-negative.")
        if self.h_star_hd < 0 or self.h_star_ld < 0:  # Assuming H* should be non-negative
            raise ValueError("H* values must be non-negative.")
        if self.alpha <= 0 or self.D_N <= 0 or self.A_F <= 0 or self.A_T <= 0 or self.e_dot <= 0:
            raise ValueError(
                "Physical constants (alpha, D_N, A_F, A_T, e_dot) must be positive.")
        if self.line_spacing_mm <= 0:
            raise ValueError("Line spacing must be positive.")
        if self.sampling_resolution_mm <= 0:  # Updated validation for new name
            raise ValueError("Sampling resolution must be positive.")
        if self.dz_mm <= 0:
            raise ValueError("Layer height increment (dZ) must be positive.")


# Example Usage (optional, for testing the dataclass itself)
if __name__ == '__main__':
    # Create dummy files for testing
    dummy_image_path = "dummy_image.png"
    dummy_start_gcode_path = "dummy_start.gcode"
    dummy_end_gcode_path = "dummy_end.gcode"

    with open(dummy_image_path, "w") as f:
        pass  # Dummy file
    with open(dummy_start_gcode_path, "w") as f:
        pass  # Dummy file
    with open(dummy_end_gcode_path, "w") as f:
        pass  # Dummy file

    try:
        print("--- Testing valid PrintParameters ---")
        params = PrintParameters(
            image_filepath=dummy_image_path,
            physical_print_width_mm=50.0,
            num_layers=100,
            v_star_hd=0.2,
            v_star_ld=0.8,
            h_star_hd=5.0,
            h_star_ld=10.0,
            alpha=1.18,  # Example value from paper
            D_N=0.4,    # Example nozzle diameter
            D_F=1.75,
            e_dot=5.0,  # Example flow rate mm/min
            line_spacing_mm=0.5,
            sampling_resolution_mm=0.25,  # Updated parameter name
            dz_mm=0.2,
            start_gcode_filepath=dummy_start_gcode_path,
            end_gcode_filepath=dummy_end_gcode_path
        )
        print("PrintParameters object created successfully:")
        print(params)

    except (FileNotFoundError, ValueError) as e:
        print(f"Caught unexpected error during valid params test: {e}")
    except Exception as e:
        print(f"Caught unexpected error during valid params test: {e}")

    print("\n--- Testing invalid PrintParameters (should raise error) ---")
    try:
        # Example of validation error - non-existent image file
        invalid_params = PrintParameters(
            image_filepath="non_existent_image.png",  # This file does not exist
            physical_print_width_mm=50.0, num_layers=100, v_star_hd=0.2, v_star_ld=0.8,
            h_star_hd=5.0, h_star_ld=10.0, alpha=1.0, D_N=0.4, e_dot=1.0,
            line_spacing_mm=0.5, sampling_resolution_mm=0.25, dz_mm=0.2,  # Updated parameter name
            start_gcode_filepath="dummy_start.gcode", end_gcode_filepath="dummy_end.gcode"
        )
        print("This should not be printed if validation works.")

    except (FileNotFoundError, ValueError) as e:
        print(f"Caught expected error during invalid params test: {e}")
    except Exception as e:
        print(f"Caught unexpected error during invalid params test: {e}")
    finally:
        # Clean up dummy files
        if os.path.exists(dummy_image_path):
            os.remove(dummy_image_path)
        if os.path.exists(dummy_start_gcode_path):
            os.remove(dummy_start_gcode_path)
        if os.path.exists(dummy_end_gcode_path):
            os.remove(dummy_end_gcode_path)
