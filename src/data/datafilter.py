import os
import shutil
from tqdm import tqdm
from fontTools import ttLib

def has_not_all_chars(font: ttLib.TTFont, chars_to_check: str, *args, **kwargs):
    # chars_in_font = {chr(c) for c in font['cmap'].tables[1].cmap.keys()}
    chars_in_font = {chr(c) for c in font['cmap'].getBestCmap().keys()}
    chars_to_check = {c for c in chars_to_check}
    return not chars_to_check.issubset(chars_in_font)

def has_empty_glyphs(font: ttLib.TTFont, chars_to_check: str = None, *args, **kwargs):
    if chars_to_check is None:
        chars_to_check = {chr(c) for c in font['cmap'].getBestCmap().keys()}

    for char in chars_to_check:
        #print(char)
        glyph = font['glyf'].glyphs[font['cmap'].getBestCmap()[ord(char)]]
        if glyph_is_empty(glyph):
            return True
    return False

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
    return font['cmap'].getBestCmap() is None

def filter_fonts(font_files_path, 
               processed_fonts_path=None,
               required_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß",
               filter_funcs=[has_no_glyf, 
                             glyf_is_corrupted, 
                             cmap_is_corrupted, 
                             no_good_cmap, 
                             has_not_all_chars, 
                             has_empty_glyphs, 
                             out_of_bounds]):
    if processed_fonts_path is None:
        processed_fonts_path = os.join(font_files_path, 'processed')
    os.makedirs(processed_fonts_path, exist_ok=True)
    
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

            kwargs = {'chars_to_check': required_chars, 'font': font}

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





