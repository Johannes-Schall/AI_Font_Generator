import os
import shutil
from tqdm import tqdm
from fontTools import ttLib
import src.data.datarenderer as datarenderer
import numpy as np

def has_not_all_chars(font: ttLib.TTFont, chars_to_check: str, *args, **kwargs):
    # chars_in_font = {chr(c) for c in font['cmap'].tables[1].cmap.keys()}
    try:
        chars_in_font = {chr(c) for c in font['cmap'].getBestCmap().keys()}
    except OverflowError:
        # This happens when the cmap is too large
        # OverflowError: Python int too large to convert to C int
        # TODO: Clarify if this is a problem futher down the line. Can this be fixed without excluding the font?
        print(f"OverflowError: Python int too large to convert to C int")
        return True
    chars_to_check = {c for c in chars_to_check}
    return not chars_to_check.issubset(chars_in_font)

def has_empty_glyphs(font_file_path, chars_to_check: str = None, *args, **kwargs):
    if chars_to_check is None:
        font = ttLib.TTFont(font_file_path)
        chars_to_check = {chr(c) for c in font['cmap'].getBestCmap().keys()}

    try:
        glyph_array = datarenderer.render_font(font_file_path, 
                                            chars=chars_to_check, 
                                            size=2, 
                                            normalize=True)
        glyph_array = 1. - glyph_array
        empty_entries = (np.sum(glyph_array, axis=(0, 1)) == 0)
        return np.any(empty_entries)
    except:
        return True

def glyph_is_empty(glyph):
    return not hasattr(glyph, 'data')

def out_of_bounds(font, bounds=(-0.4, -0.4, 1.8 ,1.3 ), *args, **kwargs):
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

def font_file_is_corrupted(font_file_path, *args, **kwargs):
    try:
        font = ttLib.TTFont(font_file_path)
        return False
    except:
        return True
    
def has_no_glyf(font, *args, **kwargs):
    #TODO: Understand fonts without key "glyf" and possibly include them
    return 'glyf' not in font.keys()

def glyf_is_corrupted(font, *args, **kwargs):
    try:
        _ = font['glyf']
        return False
    except:
        return True
    
def cmap_is_corrupted(font, *args, **kwargs):
    try:
        _ = font['cmap']
        return False
    except:
        return True
    
def no_good_cmap(font, *args, **kwargs):
    try:
        cmap = font['cmap'].getBestCmap()
    except:
        return True
    return cmap is None

def filter_fonts(font_files_path = None,
                 path_to_json = None, 
                 processed_fonts_path=None,
                 required_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß",
                 filter_funcs=[
                                #has_no_glyf, 
                                #glyf_is_corrupted, 
                                cmap_is_corrupted, 
                                no_good_cmap, 
                                has_not_all_chars, 
                                has_empty_glyphs, 
                                out_of_bounds
                                ]):
    
    if processed_fonts_path is None:
        processed_fonts_path = os.path.join(font_files_path, 'processed')
    os.makedirs(processed_fonts_path, exist_ok=True)
    
    
    if font_files_path is None:
        # TODO: json loader here
        pass
    else:
        files = os.listdir(font_files_path)
    # only font files with ttf or otf or pfb extension
    font_files = [file for file in files if file.endswith(('.ttf', '.otf'))]

    filter_counter_dict = {}
    filter_counter_dict['num_font_files_processed'] = len(font_files)
    filter_counter_dict['num_usable_fonts'] = 0

    # Writing a log file
    num_log_file = 0
    log_file_name = f'log_filter_fonts{num_log_file}.txt'
    while os.path.exists(os.path.join(font_files_path, log_file_name)):
        num_log_file += 1
        log_file_name = f'log_filter_fonts{num_log_file}.txt'

    with open(os.path.join(font_files_path, log_file_name), 'a') as log_file:

        for idx, font_file in tqdm(enumerate(font_files)):
            font_file_path = os.path.join(font_files_path, font_file)
            # print(font_file_path)
            
            log_file.write(f"{idx},{font_file},")
            # Checking for common errors and exclude the font if it has one
            # Check if file is corrupted
            if font_file_is_corrupted(font_file_path):
                log_file.write(f"EXCLUDED, corrupted file\n")
                continue
            else:
                font = ttLib.TTFont(font_file_path)

            kwargs = {'chars_to_check': required_chars, 
                      'font': font,
                      'font_file_path': font_file_path}

            filtered = False
            for func in filter_funcs:
                if func(**kwargs):
                    log_file.write(f"EXCLUDED, {func.__name__}\n")
                    filter_counter_dict[func.__name__] = filter_counter_dict.get(func.__name__, 0) + 1
                    filtered = True
                    break
            if filtered:
                continue
                
            log_file.write(f"INCLUDED\n")
            filter_counter_dict['num_usable_fonts'] = filter_counter_dict['num_usable_fonts'] + 1

            processed_file_path = os.path.join(processed_fonts_path, font_file)
            # if file exists, remove it
            if os.path.exists(processed_file_path):
                os.remove(processed_file_path)
            shutil.move(font_file_path, processed_fonts_path)  # Move the new file

        log_file.write(f"\n\nFilter results:\n")
        for key, value in filter_counter_dict.items():
            log_file.write(f"{key}: {value}\n")

    print(f"Processed {idx+1} fonts. Found {filter_counter_dict['num_usable_fonts']} usable fonts and moved them to {processed_fonts_path}.")
    return filter_counter_dict





