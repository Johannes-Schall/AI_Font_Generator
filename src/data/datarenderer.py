import numpy as np
from PIL import Image, ImageFont, ImageDraw
import os
import matplotlib.pyplot as plt


def render_font(font_path, 
                size: int, 
                chars: str="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß",
                normalize: bool=False,
                invert: bool=False):
    """
    Renders glyphs of a font as a numpy array.

    Args:
        font_path (str): Path to font file (ttf, otf)
        size (int): Size of the image (size x size)
        chars (str, optional): Characters to render. Defaults to "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß".

    Returns:
        np.array: Array of shape (size, size, len(chars))
    """
    font_size = int(0.7*size)
    text_start = (int(0.15*size), int(0.15*size))
    font = ImageFont.truetype(font_path, font_size)
    # Reserve memory for the arrays
    arrays = np.empty((size, size, len(chars)))
    
    for idx, char in enumerate(chars):
        # Modes: 1 (1-bit pixels, black and white, stored with one pixel per byte)
        #        L (8-bit pixels, black and white)
        image = Image.new('L', (size, size), 255)
        draw = ImageDraw.Draw(image)
        draw.text(text_start, char, font=font, fill=0)
        arrays[:, :, idx] = np.array(image)

    if normalize:
        arrays = arrays / 255.
    if invert:
        if normalize:
            arrays = 1. - arrays
        else:
            arrays = 255 - arrays

    return arrays

def render_fonts(font_file_paths: list,
                 size: int=64,
                 chars: str="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß",
                 normalize: bool=False,
                 invert: bool=False):
    """
    Renders glyphs of multiple fonts as a numpy array.
    
    Args:
        font_file_paths (list): List of font file paths
        size (int, optional): Size of the image (size x size). Defaults to 64.
        chars (str, optional): Characters to render. Defaults to "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß".
        normalize (bool, optional): Normalize the array. Defaults to False.
    
    Returns:
        np.array: Array of shape (len(font_file_paths), size, size, len(chars))
    """
    # reserve memory for the arrays
    arrays = np.empty((len(font_file_paths), size, size, len(chars)))
    for idx, font_file_path in enumerate(font_file_paths):
        arrays[idx, :, :, :] = render_font(font_file_path, size, chars, normalize, invert)
    return arrays

def plot_glyphs(font_file_paths,
                size: int=64,
                chars: str="Äß",
                figsize=(20, 20),
                show_index: bool=False):
    """
    Plots the same glyphs of different fonts.

    Args:
        font_file_paths (list): List of font file paths
        size (int, optional): Size of the image (size x size). Defaults to 64.
        chars (str, optional): Characters to render. Defaults to "Äß".
        figsize (tuple, optional): Size of the figure. Defaults to (20, 20).

    Returns:
        None
    """
    num_fonts = len(font_file_paths)
    size_port_grid = int(np.ceil(np.sqrt(num_fonts)))

    for char in chars:
        fig, ax = plt.subplots(size_port_grid, 
                               size_port_grid, 
                               figsize=figsize)

        for idx, font_file_path in enumerate(font_file_paths):
            font_array = render_font(font_file_path, size, char)
            ax[idx // size_port_grid, idx % size_port_grid].imshow(font_array[:, :, 0], cmap='gray')
            #turing the axis ticks off
            ax[idx // size_port_grid, idx % size_port_grid].set_xticks([])
            ax[idx // size_port_grid, idx % size_port_grid].set_yticks([])
            if show_index:
                ax[idx // size_port_grid, idx % size_port_grid].set_title(idx)

        plt.show()