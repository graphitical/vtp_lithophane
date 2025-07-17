#!/usr/bin/env python3
"""
Script to compare grayscale histogram distributions of two RGB images.
Supports images of different dimensions and provides statistical comparison metrics.
Can work with both file paths and PIL Image objects directly.
"""

import argparse
from pathlib import Path
from typing import Union

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import stats

white_threshold_global = 160
black_threshold_global = 80


def set_plot_style():
    # from matplotlib import font_manager

    # # Path to the Lato font file (ensure this path is correct)
    # font_path = '/Users/Bluefish_/Library/Fonts/LinBiolinum_Rah.ttf'

    # # Add the font to Matplotlib's font manager
    # font_manager.fontManager.addfont(font_path)
    # linbiolium_font = font_manager.FontProperties(fname=font_path)

    # # Load the Lato font
    # plt.rcParams['font.family'] = linbiolium_font.get_name()

    # # Customize font sizes
    # plt.rcParams['axes.labelsize'] = 14  # Axis labels
    # plt.rcParams['axes.titlesize'] = 16  # Plot title
    # plt.rcParams['figure.titlesize'] = 16  # Figure title
    # plt.rcParams['legend.fontsize'] = 6  # Legend
    # plt.rcParams['legend.title_fontsize'] = 8  # Legend title
    # plt.rcParams['xtick.labelsize'] = 12  # X-axis tick labels
    # plt.rcParams['ytick.labelsize'] = 12  # Y-axis tick labels

    # plt.rcParams['svg.fonttype'] = 'none'

    plot_color_palette = ['#d1eeea', '#A8DBD9', '#85C4C9',
                          '#68ABB8', '#4F90A6', '#3B738F', '#2a5674']
    return plot_color_palette


def rgb_to_grayscale(image_input: Union[str, Image.Image]):
    """
    Convert RGB image to grayscale and return the pixel values.

    Args:
        image_input (Union[str, Image.Image]): Path to image file or PIL Image object

    Returns:
        numpy.ndarray: Grayscale pixel values (0-255)
    """
    # Handle both file paths and PIL Image objects
    if isinstance(image_input, str):
        # Load image from file path
        img = Image.open(image_input).convert('RGB')
    else:
        # Use provided PIL Image object
        img = image_input.convert('RGB')

    # Convert to numpy array
    img_array = np.array(img)

    # Convert to grayscale using OpenCV (more accurate than PIL's convert)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    return gray


def compute_histogram(gray_image, bins=256):
    """
    Compute histogram of grayscale image.

    Args:
        gray_image (numpy.ndarray): Grayscale image
        bins (int): Number of histogram bins

    Returns:
        tuple: (histogram values, bin edges)
    """
    hist, bin_edges = np.histogram(
        gray_image.flatten(), bins=bins, range=(0, 256))
    return hist, bin_edges


def normalize_histogram(hist):
    """
    Normalize histogram to sum to 1 (probability distribution).

    Args:
        hist (numpy.ndarray): Histogram values

    Returns:
        numpy.ndarray: Normalized histogram
    """
    return hist / np.sum(hist)


def register_custom_metric(metric_name: str, metric_function):
    """
    Register a custom metric function for histogram comparison.

    Args:
        metric_name (str): Name of the metric
        metric_function (callable): Function that takes two histograms (h1, h2) and returns a scalar value

    Example:
        def my_custom_metric(h1, h2):
            return np.sum(np.abs(h1 - h2)) / len(h1)

        register_custom_metric('my_custom_metric', my_custom_metric)
    """
    global _custom_metrics
    if '_custom_metrics' not in globals():
        global _custom_metrics
        _custom_metrics = {}

    _custom_metrics[metric_name] = metric_function


def black_white_ratio_metric(h1, h2, black_threshold=black_threshold_global, white_threshold=white_threshold_global):
    """
    Compute the ratio of black to white pixels in two histograms.

    Args:
        h1 (numpy.ndarray): First histogram
        h2 (numpy.ndarray): Second histogram  
        black_threshold (int): Threshold below which pixels are considered black (0-255)
        white_threshold (int): Threshold above which pixels are considered white (0-255)

    Returns:
        float: Ratio of black to white pixels (black_count / white_count)
    """
    # Create grayscale values corresponding to histogram bin centers
    grayscale_values = np.linspace(0, 255, len(h1), dtype=float) + 0.5

    # Count black pixels (below threshold)
    black_pixels_h1 = np.sum(h1[grayscale_values < black_threshold])
    black_pixels_h2 = np.sum(h2[grayscale_values < black_threshold])

    # Count white pixels (above threshold)
    white_pixels_h1 = np.sum(h1[grayscale_values > white_threshold])
    white_pixels_h2 = np.sum(h2[grayscale_values > white_threshold])

    # Compute ratios for each histogram
    # ratio_h1 = black_pixels_h1 / (white_pixels_h1 + 1e-10)
    ratio_h1 = black_pixels_h1 / (black_pixels_h1 + white_pixels_h1)
    # ratio_h2 = black_pixels_h2 / (white_pixels_h2 + 1e-10)
    ratio_h2 = black_pixels_h2 / (black_pixels_h2 + white_pixels_h2)

    # Return the absolute difference between ratios
    return ratio_h2 - ratio_h1


def black_white_ratio_percentage_metric(h1, h2, black_threshold=black_threshold_global, white_threshold=white_threshold_global):
    """
    Compute the ratio of black to white pixels in two histograms.

    Args:
        h1 (numpy.ndarray): First histogram
        h2 (numpy.ndarray): Second histogram  
        black_threshold (int): Threshold below which pixels are considered black (0-255)
        white_threshold (int): Threshold above which pixels are considered white (0-255)

    Returns:
        float: Ratio of black to white pixels (black_count / white_count)
    """
    # Create grayscale values corresponding to histogram bin centers
    grayscale_values = np.linspace(0, 255, len(h1), dtype=float) + 0.5

    # Count black pixels (below threshold)
    black_pixels_h1 = np.sum(h1[grayscale_values < black_threshold])
    black_pixels_h2 = np.sum(h2[grayscale_values < black_threshold])

    # Count white pixels (above threshold)
    white_pixels_h1 = np.sum(h1[grayscale_values > white_threshold])
    white_pixels_h2 = np.sum(h2[grayscale_values > white_threshold])

    # Compute ratios for each histogram
    # ratio_h1 = black_pixels_h1 / (white_pixels_h1 + 1e-10)
    ratio_h1 = black_pixels_h1 / (black_pixels_h1 + white_pixels_h1)
    # ratio_h2 = black_pixels_h2 / (white_pixels_h2 + 1e-10)
    ratio_h2 = black_pixels_h2 / (black_pixels_h2 + white_pixels_h2)

    # Return the relative difference between ratios
    return (ratio_h2 - ratio_h1) / (ratio_h1)


def create_black_white_ratio_metric(black_threshold=black_threshold_global, white_threshold=white_threshold_global):
    """
    Create a black-white ratio metric function with specified thresholds.

    Args:
        black_threshold (int): Threshold below which pixels are considered black (0-255)
        white_threshold (int): Threshold above which pixels are considered white (0-255)

    Returns:
        callable: Metric function that can be registered
    """
    def metric_function(h1, h2):
        return black_white_ratio_metric(h1, h2, black_threshold, white_threshold)

    return metric_function


def create_black_white_ratio_percentage_metric(black_threshold=black_threshold_global, white_threshold=white_threshold_global):
    """
    Create a black-white ratio metric function with specified thresholds.

    Args:
        black_threshold (int): Threshold below which pixels are considered black (0-255)
        white_threshold (int): Threshold above which pixels are considered white (0-255)

    Returns:
        float: Ratio of black to white pixels (black_count / white_count)
    """
    def metric_function(h1, h2):
        return black_white_ratio_percentage_metric(h1, h2, black_threshold, white_threshold)

    return metric_function


def earth_movers_distance_robust(h1, h2):
    """
    Robust implementation of Earth Mover's Distance (Wasserstein distance).

    Args:
        h1 (numpy.ndarray): First histogram (normalized)
        h2 (numpy.ndarray): Second histogram (normalized)

    Returns:
        float: Earth Mover's Distance
    """
    try:
        # Ensure histograms have the same length
        min_len = min(len(h1), len(h2))
        h1 = h1[:min_len]
        h2 = h2[:min_len]

        # Check if histograms are valid
        if np.sum(h1) == 0 or np.sum(h2) == 0:
            return 0.0

        # Create positions (bin centers)
        positions = np.arange(min_len)

        # Use scipy's wasserstein_distance with positions and weights
        distance = stats.wasserstein_distance(positions, positions, h1, h2)

        return distance

    except Exception as e:
        print(f"Warning: Could not compute Earth Mover's Distance: {e}")
        return None


def earth_movers_distance_raw(h1_raw, h2_raw):
    """
    Earth Mover's Distance using raw histogram counts (not normalized).

    Args:
        h1_raw (numpy.ndarray): First histogram (raw counts)
        h2_raw (numpy.ndarray): Second histogram (raw counts)

    Returns:
        float: Earth Mover's Distance
    """
    try:
        # Ensure histograms have the same length
        min_len = min(len(h1_raw), len(h2_raw))
        h1_raw = h1_raw[:min_len]
        h2_raw = h2_raw[:min_len]

        # Check if histograms are valid
        if np.sum(h1_raw) == 0 or np.sum(h2_raw) == 0:
            return 0.0

        # Create positions (bin centers)
        positions = np.arange(min_len)

        # Use scipy's wasserstein_distance with raw counts
        distance = stats.wasserstein_distance(
            positions, positions, h1_raw, h2_raw)

        return distance

    except Exception as e:
        print(f"Warning: Could not compute Earth Mover's Distance (raw): {e}")
        return None


def compare_histograms(hist1, hist2, metrics_list=None, hist1_raw=None, hist2_raw=None):
    """
    Compare two histograms using specified metrics.

    Args:
        hist1 (numpy.ndarray): First histogram (normalized)
        hist2 (numpy.ndarray): Second histogram (normalized)
        metrics_list (list, optional): List of metric names to compute. 
                                     If None, computes all available metrics.
        hist1_raw (numpy.ndarray, optional): First histogram (raw counts)
        hist2_raw (numpy.ndarray, optional): Second histogram (raw counts)

    Returns:
        dict: Dictionary containing comparison metrics
    """
    # Ensure histograms have the same length
    min_len = min(len(hist1), len(hist2))
    hist1 = hist1[:min_len]
    hist2 = hist2[:min_len]

    # Also ensure raw histograms have same length if provided
    if hist1_raw is not None and hist2_raw is not None:
        hist1_raw = hist1_raw[:min_len]
        hist2_raw = hist2_raw[:min_len]

    # Define all available metrics
    all_metrics = {
        'bhattacharyya_distance': lambda h1, h2: 1 - np.sum(np.sqrt(h1 * h2)),
        'chi_square_distance': lambda h1, h2: np.sum((h1 - h2) ** 2 / (h1 + h2 + 1e-10)),
        'jensen_shannon_divergence': lambda h1, h2: stats.entropy((h1 + h2) / 2) - (stats.entropy(h1) + stats.entropy(h2)) / 2,
        'correlation': lambda h1, h2: np.corrcoef(h1, h2)[0, 1],
        'mean_absolute_difference': lambda h1, h2: np.mean(np.abs(h1 - h2)),
        'rmse': lambda h1, h2: np.sqrt(np.mean((h1 - h2) ** 2)),
        'earth_movers_distance': lambda h1, h2: earth_movers_distance_robust(h1, h2),
        'earth_movers_distance_raw': lambda h1, h2: earth_movers_distance_raw(hist1_raw, hist2_raw) if hist1_raw is not None and hist2_raw is not None else None,
        'kl_divergence': lambda h1, h2: stats.entropy(h1 + 1e-10, h2 + 1e-10),
        'cosine_similarity': lambda h1, h2: np.dot(h1, h2) / (np.linalg.norm(h1) * np.linalg.norm(h2) + 1e-10),
        'intersection': lambda h1, h2: np.sum(np.minimum(h1, h2)),
        'euclidean_distance': lambda h1, h2: np.sqrt(np.sum((h1 - h2) ** 2)),
        'black_white_ratio': lambda h1, h2: black_white_ratio_metric(h1, h2),
        'black_white_ratio_percentage': lambda h1, h2: black_white_ratio_percentage_metric(h1, h2)
    }

    # Add custom metrics if any are registered
    if '_custom_metrics' in globals():
        all_metrics.update(_custom_metrics)

    # If no metrics specified, use all available metrics
    if metrics_list is None:
        metrics_list = list(all_metrics.keys())

    # Validate metrics
    invalid_metrics = [m for m in metrics_list if m not in all_metrics]
    if invalid_metrics:
        raise ValueError(
            f"Invalid metrics: {invalid_metrics}. Available metrics: {list(all_metrics.keys())}")

    # Compute requested metrics
    results = {}
    for metric_name in metrics_list:
        try:
            results[metric_name] = all_metrics[metric_name](hist1, hist2)
        except Exception as e:
            print(f"Warning: Could not compute {metric_name}: {e}")
            results[metric_name] = None

    return results


def compute_black_white_ratio_single(hist, black_threshold=black_threshold_global, white_threshold=white_threshold_global):
    """
    Compute the black to white pixel ratio for a single histogram.

    Args:
        hist (numpy.ndarray): Histogram (normalized)
        black_threshold (int): Threshold below which pixels are considered black (0-255)
        white_threshold (int): Threshold above which pixels are considered white (0-255)

    Returns:
        dict: Dictionary containing black count, white count, and ratio
    """
    # Create grayscale values corresponding to histogram bin centers
    grayscale_values = np.linspace(0, 255, len(hist), dtype=float) + 0.5

    # Count black pixels (below threshold)
    black_pixels = np.sum(hist[grayscale_values < black_threshold])

    # Count white pixels (above threshold)
    white_pixels = np.sum(hist[grayscale_values > white_threshold])

    # Count mid-tone pixels
    mid_pixels = np.sum(hist[(grayscale_values >= black_threshold) & (
        grayscale_values <= white_threshold)])

    # Compute ratio
    # ratio = black_pixels / (white_pixels + 1e-10)
    ratio = black_pixels / (black_pixels + white_pixels)

    # Compute intensity mean
    intensity_mean = np.mean(grayscale_values)

    return {
        'black_pixels': black_pixels,
        'white_pixels': white_pixels,
        'mid_pixels': mid_pixels,
        'ratio': ratio,
        'intensity_mean': intensity_mean
    }


def plot_comparison(image1_input, image2_input, hist1, hist2, bin_edges, metrics, output_path=None, title_info=None):
    """
    Create a full visualization comparing the two images and their histograms.

    Args:
        image1_input (Union[str, Image.Image]): First image (path or PIL Image)
        image2_input (Union[str, Image.Image]): Second image (path or PIL Image)
        hist1 (numpy.ndarray): Histogram of first image
        hist2 (numpy.ndarray): Histogram of second image
        bin_edges (numpy.ndarray): Bin edges for histograms
        metrics (dict): Comparison metrics
        output_path (str, optional): Path to save the plot
    """
    plot_color_palette = set_plot_style()

    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    if title_info:
        fig.suptitle(
            f'Grayscale Histogram Comparison - {title_info}', fontsize=12, fontweight='bold')
    else:
        fig.suptitle('Grayscale Histogram Comparison',
                     fontsize=12, fontweight='bold')

    # Get image names for display
    if isinstance(image1_input, str):
        img1_name = Path(image1_input).name
    else:
        img1_name = "Physical Photo"

    if isinstance(image2_input, str):
        img2_name = Path(image2_input).name
    else:
        img2_name = "Rendered Image"

    # Convert to grayscale for display
    gray1 = rgb_to_grayscale(image1_input)
    gray2 = rgb_to_grayscale(image2_input)

    # Compute black-white ratios for each image
    bw1 = compute_black_white_ratio_single(hist1)
    bw2 = compute_black_white_ratio_single(hist2)

    # Plot original images
    axes[0, 0].imshow(gray1, cmap='gray')
    axes[0, 0].set_title(f'Image 1: {img1_name}\nShape: {gray1.shape}')
    axes[0, 0].axis('off')

    axes[0, 1].imshow(gray2, cmap='gray')
    axes[0, 1].set_title(f'Image 2: {img2_name}\nShape: {gray2.shape}')
    axes[0, 1].axis('off')

    # Plot black-white ratio comparison
    categories = ['Black', 'Mid', 'White']
    values1 = [bw1['black_pixels'], bw1['mid_pixels'], bw1['white_pixels']]
    values2 = [bw2['black_pixels'], bw2['mid_pixels'], bw2['white_pixels']]

    x = np.arange(len(categories))
    width = 0.35

    axes[0, 2].bar(x - width/2, values1, width, label='Image 1', alpha=0.8)
    axes[0, 2].bar(x + width/2, values2, width, label='Image 2', alpha=0.8)
    axes[0, 2].set_xlabel('Pixel Categories')
    axes[0, 2].set_ylabel('Normalized Frequency')
    axes[0, 2].set_title('Black/White/Mid Distribution')
    axes[0, 2].set_xticks(x)
    axes[0, 2].set_xticklabels(categories)
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)

    # Plot histograms
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    axes[1, 0].plot(bin_centers, hist1, 'b-', label='Image 1', linewidth=2)
    axes[1, 0].plot(bin_centers, hist2, 'r-', label='Image 2', linewidth=2)
    axes[1, 0].set_xlabel('Grayscale Value')
    axes[1, 0].set_ylabel('Normalized Frequency')
    axes[1, 0].set_title('Histogram Comparison')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Add threshold lines to histogram
    axes[1, 0].axvline(x=black_threshold_global, color='k',
                       linestyle='--', alpha=0.5, label='Black threshold')
    axes[1, 0].axvline(x=white_threshold_global, color='k',
                       linestyle='--', alpha=0.5, label='White threshold')
    axes[1, 0].legend()

    # Plot difference
    axes[1, 1].plot(bin_centers, hist1 - hist2, 'g-', linewidth=2)
    axes[1, 1].axhline(y=0, color='k', linestyle='--', alpha=0.5)
    axes[1, 1].set_xlabel('Grayscale Value')
    axes[1, 1].set_ylabel('Difference (Image 1 - Image 2)')
    axes[1, 1].set_title('Histogram Difference')
    axes[1, 1].grid(True, alpha=0.3)

    # Plot black-white ratio comparison
    axes[1, 2].bar(['Physical Photo', 'Rendered Image'], [bw1['ratio'], bw2['ratio']],
                   color=['blue', 'red'], alpha=0.7)
    axes[1, 2].set_ylabel('Black/White Ratio')
    axes[1, 2].set_title('Black to White Pixel Ratio')
    axes[1, 2].grid(True, alpha=0.3)

    # Add ratio values on bars
    axes[1, 2].text(0, bw1['ratio'] + 0.01, f'{bw1["ratio"]:.3f}',
                    ha='center', va='bottom', fontweight='bold')
    axes[1, 2].text(1, bw2['ratio'] + 0.01, f'{bw2["ratio"]:.3f}',
                    ha='center', va='bottom', fontweight='bold')

    # Add metrics text
    metrics_text = '\n'.join([
        f'{metric.replace("_", " ").title()}: {value:.4f}'
        for metric, value in metrics.items()
        if value is not None
    ])

    # Add black-white analysis text
    bw_text = f'\nBlack/White Analysis:\n'
    bw_text += f'Image 1 - Black: {bw1["black_pixels"]:.3f}, White: {bw1["white_pixels"]:.3f}, Ratio: {bw1["ratio"]:.3f}\n'
    bw_text += f'Image 2 - Black: {bw2["black_pixels"]:.3f}, White: {bw2["white_pixels"]:.3f}, Ratio: {bw2["ratio"]:.3f}'

    fig.text(0.02, 0.02, metrics_text + bw_text, fontsize=9, family='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")

    plt.show()


def plot_comparison_simple(image1_input, image2_input, hist1, hist2, bin_edges, metrics, output_path=None, title_info=None):
    """
    Create a simplified visualization comparing the two images and their histograms.
    Shows only: Image 1, Image 2, and Histogram Overlay.

    Args:
        image1_input (Union[str, Image.Image]): First image (path or PIL Image)
        image2_input (Union[str, Image.Image]): Second image (path or PIL Image)
        hist1 (numpy.ndarray): Histogram of first image
        hist2 (numpy.ndarray): Histogram of second image
        bin_edges (numpy.ndarray): Bin edges for histograms
        metrics (dict): Comparison metrics
        output_path (str, optional): Path to save the plot
    """
    plot_color_palette = set_plot_style()

    fig, axes = plt.subplots(1, 3, figsize=(7, 3))
    if title_info:
        fig.suptitle(f'{title_info}', fontsize=12, fontweight='bold')
    else:
        fig.suptitle('Grayscale Histogram Comparison',
                     fontsize=12, fontweight='bold')

    # Get image names for display
    if isinstance(image1_input, str):
        img1_name = Path(image1_input).name.replace(".png", "")
    else:
        img1_name = "Physical Photo"

    if isinstance(image2_input, str):
        img2_name = Path(image2_input).name.replace(".png", "")
    else:
        img2_name = "Rendered Image"

    # Convert to grayscale for display
    gray1 = rgb_to_grayscale(image1_input)
    gray2 = rgb_to_grayscale(image2_input)

    # Compute black-white ratios for each image
    bw1 = compute_black_white_ratio_single(hist1)
    bw2 = compute_black_white_ratio_single(hist2)

    # Plot original images
    axes[0].imshow(gray1, cmap='gray')
    axes[0].set_title(
        f'{img1_name}\nDark Pixel Percentage: {bw1["ratio"]:.3f}', fontsize=10)
    axes[0].axis('off')

    axes[1].imshow(gray2, cmap='gray')
    axes[1].set_title(
        f'{img2_name}\nDark Pixel Percentage: {bw2["ratio"]:.3f}', fontsize=10)
    axes[1].axis('off')

    # Plot histogram overlay
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    axes[2].plot(bin_centers, hist1, 'b-',
                 label=f'{img1_name}', linewidth=2, alpha=0.8)
    axes[2].plot(bin_centers, hist2, 'r-',
                 label=f'{img2_name}', linewidth=2, alpha=0.8)
    axes[2].set_xlabel('Grayscale Value', fontsize=10)
    axes[2].set_ylabel('Normalized Frequency', fontsize=10)
    axes[2].set_title('Histogram Overlay', fontsize=10)
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    # Add threshold lines to histogram
    axes[2].axvline(x=black_threshold_global, color='k',
                    linestyle='--', alpha=0.5, label='Dark Pixel Threshold')
    axes[2].axvline(x=white_threshold_global, color='k',
                    linestyle='--', alpha=0.5, label='Light Pixel Threshold')

    # Add metrics text
    metrics_text = ''  # 'Comparison Metrics:\n'
    metrics_text += '\n'.join([
        f'{metric.replace("_", " ").title()}: {value * 100:.2f}%'
        for metric, value in metrics.items()
        if value is not None
    ])
    metrics_text = metrics_text.replace(
        'Black White Ratio Percentage', 'Percentage Difference in Dark Pixel Percentage')

    # Add black-white analysis text
    # bw_text = f'\n\nBlack/White Analysis:\n'
    # bw_text += f'{img1_name} - Black White Ratio: {bw1["ratio"]:.3f}\n'
    # bw_text += f'{img2_name} - Black White Ratio: {bw2["ratio"]:.3f}'

    # Position text box in the lower left of the figure
    fig.text(0.02, 0.02, metrics_text, fontsize=10,
             bbox=dict(boxstyle="round,pad=0.5",
                       facecolor="lightgray", alpha=0.9),
             verticalalignment='bottom')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")

    plt.show()


def compare_images(image1_input: Union[str, Image.Image],
                   image2_input: Union[str, Image.Image],
                   title_info: str = None,
                   bins: int = 256,
                   metrics: list = None,
                   plot: bool = True,
                   simple_plot: bool = True,
                   output_path: str = None):
    """
    Compare grayscale histogram distributions of two images.

    Args:
        image1_input (Union[str, Image.Image]): First image (path or PIL Image)
        image2_input (Union[str, Image.Image]): Second image (path or PIL Image)
        bins (int): Number of histogram bins
        metrics (list, optional): List of metric names to compute. If None, computes all available metrics.
        plot (bool): Whether to create visualization
        simple_plot (bool): Whether to use simplified plot (3 panels) or full plot (6 panels)
        output_path (str, optional): Path to save the comparison plot

    Returns:
        dict: Comparison metrics
    """
    try:
        # Convert images to grayscale
        # print("Converting images to grayscale...")
        gray1 = rgb_to_grayscale(image1_input)
        gray2 = rgb_to_grayscale(image2_input)

        # print(f"Image 1 shape: {gray1.shape}")
        # print(f"Image 2 shape: {gray2.shape}")

        # Compute histograms (raw counts)
        # print("Computing histograms...")
        hist1_raw, bin_edges = compute_histogram(gray1, bins)
        hist2_raw, _ = compute_histogram(gray2, bins)

        # Normalize histograms
        hist1_norm = normalize_histogram(hist1_raw)
        hist2_norm = normalize_histogram(hist2_raw)

        # Compare histograms (pass both normalized and raw)
        # print("Comparing histograms...")
        metrics_result = compare_histograms(
            hist1_norm, hist2_norm, metrics, hist1_raw, hist2_raw)

        # Print results
        # print("\n" + "="*50)
        # print("GRAYSCALE HISTOGRAM COMPARISON RESULTS")
        # print("="*50)

        # Get image names for display
        # if isinstance(image1_input, str):
        #     img1_name = image1_input
        # else:
        #     img1_name = "Image 1 (Physical Photo)"

        # if isinstance(image2_input, str):
        #     img2_name = image2_input
        # else:
        #     img2_name = "Image 2 (Rendered Image)"

        # print(f"Image 1: {img1_name}")
        # print(f"Image 2: {img2_name}")
        # print(f"Histogram bins: {bins}")
        # print(f"Total pixels - Image 1: {np.sum(hist1_raw)}, Image 2: {np.sum(hist2_raw)}")
        # if metrics:
        #     print(f"Metrics computed: {', '.join(metrics)}")
        # else:
        #     print("All available metrics computed")

        # print("\nComparison Metrics:")
        # for metric_name, value in metrics_result.items():
        #     if value is not None:
        #         print(f"  {metric_name.replace('_', ' ').title()}: {value:.6f}")
        #     else:
        #         print(f"  {metric_name.replace('_', ' ').title()}: Could not compute")

        # Interpretation for key metrics
        # print("\nInterpretation:")
        # if 'bhattacharyya_distance' in metrics_result and metrics_result['bhattacharyya_distance'] is not None:
        #     bd = metrics_result['bhattacharyya_distance']
        #     if bd < 0.1:
        #         print("  • Histograms are very similar (Bhattacharyya < 0.1)")
        #     elif bd < 0.3:
        #         print("  • Histograms are moderately similar (Bhattacharyya < 0.3)")
        #     else:
        #         print("  • Histograms are quite different (Bhattacharyya >= 0.3)")

        # if 'correlation' in metrics_result and metrics_result['correlation'] is not None:
        #     corr = metrics_result['correlation']
        #     if abs(corr) > 0.8:
        #         print("  • Strong correlation between distributions")
        #     elif abs(corr) > 0.5:
        #         print("  • Moderate correlation between distributions")
        #     else:
        #         print("  • Weak correlation between distributions")

        # if 'earth_movers_distance' in metrics_result and metrics_result['earth_movers_distance'] is not None:
        #     emd = metrics_result['earth_movers_distance']
        #     if emd < 0.01:
        #         print("  • Low Earth Mover's Distance - distributions are similar")
        #     elif emd < 0.05:
        #         print("  • Moderate Earth Mover's Distance - some differences")
        #     else:
        #         print("  • High Earth Mover's Distance - distributions are quite different")

        # if 'earth_movers_distance_raw' in metrics_result and metrics_result['earth_movers_distance_raw'] is not None:
        #     emd_raw = metrics_result['earth_movers_distance_raw']
        #     if emd_raw < 10:
        #         print("  • Low Earth Mover's Distance - distributions are similar")
        #     elif emd_raw < 50:
        #         print("  • Moderate Earth Mover's Distance - some differences")
        #     else:
        #         print("  • High Earth Mover's Distance - distributions are quite different")

        # Create visualization
        if plot:
            if simple_plot:
                plot_comparison_simple(image1_input, image2_input, hist1_norm, hist2_norm,
                                       bin_edges, metrics_result, output_path, title_info)
            else:
                plot_comparison(image1_input, image2_input, hist1_norm, hist2_norm,
                                bin_edges, metrics_result, output_path, title_info)

        return metrics_result

    except Exception as e:
        print(f"Error: {e}")
        return None


def compare_images_robust(
        image1_input: Union[str, Image.Image],
        image2_input: Union[str, Image.Image],
        title_info: str = None,
        bins: int = 256,
        metrics: list = ['black_white_ratio', 'black_white_ratio_percentage'],
        plot: bool = True,
        simple_plot: bool = True,
        output_path: str = None,
        crop_size: int = 200,
        window_size: int = 2,
        outlier_removal: bool = True,
        outlier_fraction: float = 0.2):
    """
    Robust comparison of grayscale histogram distributions using sliding window approach.

    Args:
        image1_input (Union[str, Image.Image]): First image (path or PIL Image) - typically physical photo
        image2_input (Union[str, Image.Image]): Second image (path or PIL Image) - typically rendered image
        title_info (str): Title information for plots
        bins (int): Number of histogram bins
        metrics (list, optional): List of metric names to compute. If None, computes key metrics.
        plot (bool): Whether to create visualization
        simple_plot (bool): Whether to use simplified plot (3 panels) or full plot (6 panels)
        output_path (str, optional): Path to save the comparison plot
        crop_size (int): Size of the crop region (square)
        window_size (int): Size of the sliding window step
        outlier_removal (bool): Whether to remove outliers before averaging
        outlier_fraction (float): Fraction of outliers to remove from each end

    Returns:
        dict: Robust comparison metrics
    """
    try:
        # # Register custom metrics to ensure they're available
        # register_custom_metric('black_white_ratio', create_black_white_ratio_metric())
        # register_custom_metric('black_white_ratio_percentage', create_black_white_ratio_percentage_metric())

        # Convert to PIL Images if needed
        if isinstance(image1_input, str):
            img1 = Image.open(image1_input).convert('RGB')
        else:
            img1 = image1_input.convert('RGB')

        if isinstance(image2_input, str):
            img2 = Image.open(image2_input).convert('RGB')
        else:
            img2 = image2_input.convert('RGB')

        # Convert to grayscale arrays
        gray1 = rgb_to_grayscale(img1)
        gray2 = rgb_to_grayscale(img2)

        # Determine valid crop regions
        max_y1, max_x1 = gray1.shape
        max_y2, max_x2 = gray2.shape

        # Find the maximum crop size that fits in both images
        max_crop_x = min(max_x1, max_x2) - crop_size
        max_crop_y = min(max_y1, max_y2) - crop_size

        if max_crop_x <= 0 or max_crop_y <= 0:
            print(f"Warning: Crop size {crop_size} is too large for image dimensions: "
                  f"img1={gray1.shape}, img2={gray2.shape}. Falling back to standard comparison.")
            return compare_images(image1_input, image2_input, title_info, bins, metrics, plot, simple_plot, output_path)

        # Generate sliding window positions
        positions = []
        for y in range(0, max_crop_y + 1, window_size):
            for x in range(0, max_crop_x + 1, window_size):
                positions.append((y, x))

        print(f"Generating {len(positions)} sliding window comparisons...")

        # Store results for each position
        all_results = []

        for i, (y, x) in enumerate(positions):
            # Crop both images at this position
            crop1 = gray1[y:y+crop_size, x:x+crop_size]
            crop2 = gray2[y:y+crop_size, x:x+crop_size]

            # Convert back to PIL Images for comparison
            crop1_pil = Image.fromarray(crop1).convert('RGB')
            crop2_pil = Image.fromarray(crop2).convert('RGB')

            # Compute comparison metrics
            result = compare_images(
                crop1_pil, crop2_pil,
                title_info=f"{title_info}_window_{i:03d}" if title_info else None,
                bins=bins,
                metrics=metrics,
                plot=False  # Don't plot individual windows
            )

            if result is not None:
                result['position'] = (y, x)
                result['window_index'] = i
                all_results.append(result)

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(positions)} windows")

        if not all_results:
            raise ValueError("No valid comparison results obtained")

        print(f"Successfully processed {len(all_results)} windows")

        # Aggregate results
        robust_metrics = {}

        for metric_name in metrics:
            values = [r[metric_name]
                      for r in all_results if r[metric_name] is not None]

            if not values:
                robust_metrics[metric_name] = None
                continue

            values = np.array(values)

            # Filter out non-finite values (NaN, inf, -inf)
            finite_mask = np.isfinite(values)
            values = values[finite_mask]

            if len(values) == 0:
                robust_metrics[metric_name] = None
                continue

            # Remove outliers if requested
            if outlier_removal and len(values) > 4:
                # Calculate number of outliers to remove from each end
                n_outliers = int(len(values) * outlier_fraction / 2)
                if n_outliers > 0:
                    # Sort values and remove outliers
                    sorted_values = np.sort(values)
                    trimmed_values = sorted_values[n_outliers:-n_outliers]

                    robust_metrics[f"{metric_name}_robust_mean"] = np.mean(
                        trimmed_values)
                    robust_metrics[f"{metric_name}_robust_std"] = np.std(
                        trimmed_values)
                    robust_metrics[f"{metric_name}_robust_median"] = np.median(
                        trimmed_values)
                    robust_metrics[f"{metric_name}_outliers_removed"] = n_outliers * 2
                    robust_metrics[f"{metric_name}_total_samples"] = len(
                        values)
                else:
                    # Not enough samples for outlier removal
                    robust_metrics[f"{metric_name}_robust_mean"] = np.mean(
                        values)
                    robust_metrics[f"{metric_name}_robust_std"] = np.std(
                        values)
                    robust_metrics[f"{metric_name}_robust_median"] = np.median(
                        values)
                    robust_metrics[f"{metric_name}_outliers_removed"] = 0
                    robust_metrics[f"{metric_name}_total_samples"] = len(
                        values)
            else:
                # No outlier removal
                robust_metrics[f"{metric_name}_robust_mean"] = np.mean(values)
                robust_metrics[f"{metric_name}_robust_std"] = np.std(values)
                robust_metrics[f"{metric_name}_robust_median"] = np.median(
                    values)
                robust_metrics[f"{metric_name}_outliers_removed"] = 0
                robust_metrics[f"{metric_name}_total_samples"] = len(values)

            # Store additional statistics
            robust_metrics[f"{metric_name}_min"] = np.min(values)
            robust_metrics[f"{metric_name}_max"] = np.max(values)
            robust_metrics[f"{metric_name}_range"] = np.max(
                values) - np.min(values)
            robust_metrics[f"{metric_name}_coefficient_of_variation"] = (
                np.std(values) /
                np.mean(values) if np.mean(values) != 0 else float('inf')
            )

        # Add metadata
        robust_metrics['crop_size'] = crop_size
        robust_metrics['window_size'] = window_size
        robust_metrics['total_windows'] = len(all_results)
        robust_metrics['outlier_fraction'] = outlier_fraction if outlier_removal else 0

        # Create visualization using the mean values from robust comparison
        if plot:
            # Create representative histograms using the mean from all windows
            # For plotting, we'll use the full images but show the robust metrics
            hist1_raw, bin_edges = compute_histogram(gray1, bins)
            hist2_raw, _ = compute_histogram(gray2, bins)
            hist1_norm = normalize_histogram(hist1_raw)
            hist2_norm = normalize_histogram(hist2_raw)

            # Create a display-friendly metrics dict with robust means
            display_metrics = {}
            for metric_name in metrics:
                if f"{metric_name}_robust_mean" in robust_metrics:
                    display_metrics[f"{metric_name}_robust_mean"] = robust_metrics[f"{metric_name}_robust_mean"]
                    display_metrics[f"{metric_name}_robust_std"] = robust_metrics[f"{metric_name}_robust_std"]

            if simple_plot:
                plot_comparison_simple(image1_input, image2_input, hist1_norm, hist2_norm,
                                       bin_edges, display_metrics, output_path,
                                       f"{title_info} (Robust)" if title_info else "Robust Comparison")
            else:
                plot_comparison(image1_input, image2_input, hist1_norm, hist2_norm,
                                bin_edges, display_metrics, output_path,
                                f"{title_info} (Robust)" if title_info else "Robust Comparison")

        return robust_metrics

    except Exception as e:
        print(f"Error in robust comparison: {e}")
        return None


def get_available_metrics():
    """
    Get a list of all available metrics (built-in and custom).

    Returns:
        list: List of available metric names
    """
    built_in_metrics = [
        'bhattacharyya_distance', 'chi_square_distance', 'jensen_shannon_divergence',
        'correlation', 'mean_absolute_difference', 'rmse', 'earth_movers_distance',
        'earth_movers_distance_raw', 'kl_divergence', 'cosine_similarity', 'intersection',
        'euclidean_distance', 'black_white_ratio'
    ]

    custom_metrics = list(_custom_metrics.keys(
    )) if '_custom_metrics' in globals() else []

    return built_in_metrics + custom_metrics


def main():
    # Register custom metrics
    register_custom_metric('black_white_ratio',
                           create_black_white_ratio_metric())
    register_custom_metric('black_white_ratio_percentage',
                           create_black_white_ratio_percentage_metric())

    parser = argparse.ArgumentParser(
        description='Compare grayscale histogram distributions of two RGB images')
    parser.add_argument('image1', help='Path to first RGB image')
    parser.add_argument('image2', help='Path to second RGB image')
    parser.add_argument('--bins', type=int, default=256,
                        help='Number of histogram bins (default: 256)')
    parser.add_argument('--metrics', nargs='+',
                        help='Specific metrics to compute (default: all metrics). Use --list-metrics to see available options.')
    parser.add_argument('--list-metrics', action='store_true',
                        help='List all available metrics and exit')
    parser.add_argument('--output', help='Path to save the comparison plot')
    parser.add_argument('--no-plot', action='store_true',
                        help='Skip plotting and only print metrics')
    parser.add_argument('--full-plot', action='store_true',
                        help='Use full 6-panel plot instead of simplified 3-panel plot')
    parser.add_argument('--robust', action='store_true',
                        help='Use robust sliding window comparison')
    parser.add_argument('--crop-size', type=int, default=250,
                        help='Size of crop region for robust comparison (default: 350)')
    parser.add_argument('--window-size', type=int, default=20,
                        help='Sliding window step size for robust comparison (default: 20)')
    parser.add_argument('--outlier-fraction', type=float, default=0.2,
                        help='Fraction of outliers to remove for robust comparison (default: 0.2)')
    parser.add_argument('--no-outlier-removal', action='store_true',
                        help='Disable outlier removal for robust comparison')

    args = parser.parse_args()

    # Handle list-metrics option
    if args.list_metrics:
        print("Available metrics:")
        for metric in get_available_metrics():
            print(f"  - {metric}")
        return

    # Check if files exist
    for img_path in [args.image1, args.image2]:
        if not Path(img_path).exists():
            print(f"Error: Image file '{img_path}' not found.")
            return

    # Validate metrics if specified
    if args.metrics:
        available_metrics = get_available_metrics()
        invalid_metrics = [
            m for m in args.metrics if m not in available_metrics]
        if invalid_metrics:
            print(f"Error: Invalid metrics: {invalid_metrics}")
            print("Use --list-metrics to see available options.")
            return

    # Choose comparison method
    if args.robust:
        # Use robust comparison
        compare_images_robust(
            image1_input=args.image1,
            image2_input=args.image2,
            bins=args.bins,
            metrics=args.metrics,
            plot=not args.no_plot,
            simple_plot=not args.full_plot,
            output_path=args.output,
            crop_size=args.crop_size,
            window_size=args.window_size,
            outlier_removal=not args.no_outlier_removal,
            outlier_fraction=args.outlier_fraction
        )
    else:
        # Use standard comparison
        compare_images(
            image1_input=args.image1,
            image2_input=args.image2,
            bins=args.bins,
            metrics=args.metrics,
            plot=not args.no_plot,
            simple_plot=not args.full_plot,
            output_path=args.output
        )


if __name__ == "__main__":
    main()
    main()
