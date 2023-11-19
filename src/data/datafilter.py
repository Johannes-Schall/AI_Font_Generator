import os
import shutil
from tqdm import tqdm
from fontTools import ttLib


def filter_fonts(font_files_path, 
               processed_fonts_path=None,
               required_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß"):
    if processed_fonts_path is None:
        processed_fonts_path = os.join(font_files_path, 'processed')
    os.makedirs(processed_fonts_path, exist_ok=True)
    
    files = os.listdir(font_files_path)
    # only font files with ttf or otf or pfb extension
    font_files = [file for file in files if file.endswith(('.ttf', '.otf'))]

    usable_fonts = 0
    for idx, font_file in tqdm(enumerate(font_files)):
        font_file_path = os.path.join(font_files_path, font_file)
        # print(font_file_path)

        try:
            font = ttLib.TTFont(font_file_path)
        except:
            os.remove(font_file_path)
            print(f"Removed corrupted file: {font_file_path}")
            continue

        # Checking for common errors and exclude the font if it has one
        #TODO: Understand fonts without key "glyf" and possibly include them
        if 'glyf' not in font.keys():
            continue
        try:
            _ = font['glyf']
            if font['cmap'].getBestCmap() is None:
                continue
        except:
            continue

        # Check if the font has all it needs to become a good font for training
        if not has_all_chars(font, required_chars):
            continue
        if has_empty_glyphs(font, required_chars):
            continue
        if out_of_bounds(font):
            continue
            
        usable_fonts += 1
        processed_file_path = os.path.join(processed_fonts_path, font_file)
        # if file exists, remove it
        if os.path.exists(processed_file_path):
            os.remove(processed_file_path)
        shutil.move(font_file_path, processed_fonts_path)  # Move the new file

    print(f"Processed {idx} fonts. Found {usable_fonts} usable fonts and moved them to {processed_fonts_path}.")

def has_all_chars(font: ttLib.TTFont, chars_to_check: str):
    # chars_in_font = {chr(c) for c in font['cmap'].tables[1].cmap.keys()}
    chars_in_font = {chr(c) for c in font['cmap'].getBestCmap().keys()}
    return set(chars_to_check).issubset(chars_in_font) and not has_empty_glyphs(font, chars_to_check)

def has_empty_glyphs(font: ttLib.TTFont, chars_to_check: str = None):
    if chars_to_check is None:
        chars_to_check = {chr(c) for c in font['cmap'].getBestCmap().keys()}

    for char in chars_to_check:
        glyph = font['glyf'].glyphs[font['cmap'].getBestCmap()[ord(char)]]
        if glyph_is_empty(glyph):
            return True
    return False

def glyph_is_empty(glyph):
    return not hasattr(glyph, 'data')

def out_of_bounds(font, bounds=(-0.2, -0.3, 1.5 ,0.95 )):
    xMin_rel, yMin_rel, xMax_rel, yMax_rel = bounds

    font_header = font['head']
    font_width = font_header.unitsPerEm
    font_limits = [font_header.xMin, 
                   font_header.yMin, 
                   font_header.xMax, 
                   font_header.yMax]
    font_limits_rel = [font_limits[i] / font_width for i in range(4)]
    return (font_limits_rel[0] < xMin_rel or
            font_limits_rel[1] < yMin_rel or
            font_limits_rel[2] > xMax_rel or
            font_limits_rel[3] > yMax_rel)