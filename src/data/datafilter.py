import os
from tqdm import tqdm
from fontTools import ttLib
from . import global_consts as g
from . import datarenderer, fontdb_handler
import numpy as np


def has_not_all_chars(font: ttLib.TTFont, chars_to_check: str, *args, **kwargs):
    # chars_in_font = {chr(c) for c in font['cmap'].tables[1].cmap.keys()}
    try:
        chars_in_font = {chr(c) for c in font['cmap'].getBestCmap().keys()}
    except OverflowError:
        # This happens when the cmap is too large
        # OverflowError: Python int too large to convert to C int
        # TODO: Clarify if this is a problem futher down the line. Can this be fixed without excluding the font?
        print("OverflowError: Python int too large to convert to C int")
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


def out_of_bounds(font, bounds=(-0.4, -0.4, 1.8, 1.3), *args, **kwargs):
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
        _ = font['cmap']
        cmap = font['cmap'].getBestCmap() # cmap is None if cmap is corrupted? Maybe a little picky, but ok for now.
        return cmap is None
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


def filter_fonts(required_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß",
                 filter_funcs=[
                                #cmap_is_corrupted,
                                #no_good_cmap,
                                has_not_all_chars,
                                has_empty_glyphs,
                                out_of_bounds
                 ]):
    """ Filters fonts in json font database and writes a log file with the results.

    Args:
        required_chars (str, optional): Characterset that is required for font to be considered complete. Defaults to "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß".
        filter_funcs (list, optional): List of filters that are getting applied to fonts. Defaults to [ cmap_is_corrupted, no_good_cmap, has_not_all_chars, has_empty_glyphs, out_of_bounds ].

    Returns:
        Dictionary: Returns dictionary with filter results.
    """
    
    path_raw_dir = g.PATH_RAW
    path_font_db_json = g.PATH_TO_JSON_FONT_DB
    
    
    # with open(path_font_db_json, 'r', encoding='utf-8') as file:
    #     font_db = json.load(file)
    
    # Result of filtering is stored in a dictionary. At the end of this function,
    # this dictionary is written to the json font database.    
    filter_dictionary = {}
    
    font_files_pathes = fontdb_handler.font_file_list()
    #font_files_pathes = [font_db[font_path] for font_path in font_db.keys()]

    filter_counter_dict = {}
    filter_counter_dict['num_font_files_processed'] = len(font_files_pathes)
    filter_counter_dict['num_usable_fonts'] = 0

    # Writing a log file
    num_log_file = 0
    log_file_name = f'log_filter_fonts{num_log_file}.txt'
    while os.path.exists(os.path.join(path_raw_dir, log_file_name)):
        num_log_file += 1
        log_file_name = f'log_filter_fonts{num_log_file}.txt'

    with open(os.path.join(path_raw_dir, log_file_name), 'a', encoding='utf-8') as log_file:

        for idx, font_file_path in tqdm(enumerate(font_files_pathes)):

            log_file.write(f"{idx},{font_file_path},")
            # Checking for common errors and exclude the font if it has one
            # Check if file is corrupted
            if font_file_is_corrupted(font_file_path):
                log_file.write("EXCLUDED, corrupted file\n")
                filter_counter_dict['corrupted_file'] = filter_counter_dict.get(
                    'corrupted_file', 0) + 1
                
                if font_file_path not in filter_dictionary:
                    filter_dictionary[font_file_path] = {}
                filter_dictionary[font_file_path].setdefault(
                    "usable", False)
                filter_dictionary[font_file_path].setdefault(
                        "filters", []).append("corrupted")
                continue

            font = ttLib.TTFont(font_file_path)


            kwargs = {'chars_to_check': required_chars,
                      'font': font,
                      'font_file_path': font_file_path}

            filtered = False
            for func in filter_funcs:
                if func(**kwargs):
                    log_file.write(f"EXCLUDED, {func.__name__}\n")
                    filter_counter_dict[func.__name__] = filter_counter_dict.get(
                        func.__name__, 0) + 1
                    filtered = True
                    
                    if font_file_path not in filter_dictionary:
                        filter_dictionary[font_file_path] = {}
                    
                    filter_dictionary[font_file_path].setdefault(
                        "usable", False)
                    filter_dictionary[font_file_path].setdefault(
                        "filters", []).append(str(func.__name__))

                    if filtered and func.__name__ == 'has_not_all_chars':
                        if font_file_path not in filter_dictionary:
                            filter_dictionary[font_file_path] = {}
                        
                        try:
                            chars_in_font = {chr(c) for c in font['cmap'].getBestCmap().keys()}
                            chars_missing = [c for c in required_chars if c not in chars_in_font]
                            # Carful: Here are only missing chars that we checked for. There might be more missing chars.
                            # A cmap can include 1000s of chars from different languages.   
                            filter_dictionary[font_file_path].setdefault('chars_not_in_font_cmap', chars_missing)
                        except OverflowError:
                            # TODO: Clarify if this is a problem futher down the line. Can this be fixed without excluding the font?
                            filter_dictionary[font_file_path].setdefault(
                                "filters", []).append("Not all chars: OverflowError")
                    if filtered and func.__name__ == 'has_empty_glyphs':
                        if font_file_path not in filter_dictionary:
                            filter_dictionary[font_file_path] = {}                        
                        
                        
                        try:
                            glyph_array = datarenderer.render_font(font_file_path,
                                                                   chars=required_chars,
                                                                   size=2,
                                                                   normalize=True)
                            glyph_array = 1. - glyph_array
                            empty_entries = (np.sum(glyph_array, axis=(0, 1)) == 0)
                            empty_chars = [c for i, c in enumerate(required_chars) if empty_entries[i]]
                            filter_dictionary[font_file_path].setdefault('chars_with_empty_glyphs', empty_chars)
                        except:
                            filter_dictionary[font_file_path].setdefault("filters", []).append("Empty glyphs: Exception")
                # else:
                #     filter_detail_dictionary[func.__name__] = False
            if filtered:
                continue

            log_file.write("INCLUDED\n")
            filter_counter_dict['num_usable_fonts'] = filter_counter_dict['num_usable_fonts'] + 1
            
        log_file.write("\n\nFilter results:\n")
        for key, value in filter_counter_dict.items():
            log_file.write(f"{key}: {value}\n")
            
        # Write filter results to json font database
        fontdb_handler.write_filter_results(filter_dictionary)

    print(
        f"Processed {idx+1} fonts. Found {filter_counter_dict['num_usable_fonts']} usable fonts.")
    return filter_counter_dict


def analyse_font_file(
        font_file,
        required_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄäÖöÜüß",
        filter_funcs=[
                    has_not_all_chars,
                    has_empty_glyphs,
                    out_of_bounds
        ]):
    filter_dictionary = {}

    try:
        font = ttLib.TTFont(font_file)
    except:
        return "Corrupted file! File could not be opened."
    try:
        cmap = font['cmap'].getBestCmap()
        if cmap is None:
            return "Corrupted file! Cmap could not be opened."
        chars_in_font = {chr(c) for c in font['cmap'].getBestCmap().keys()}
    except:
        return "Corrupted file! Cmap could not be opened."
    
    kwargs = {'chars_to_check': required_chars,
              'font': font,
              'font_file_path': font_file}
    
    for func in filter_funcs:
        if func(**kwargs):
            filter_dictionary[func.__name__] = True
        else:
            filter_dictionary[func.__name__] = False

    if filter_dictionary['has_not_all_chars']:
        chars_missing = [c for c in required_chars if c not in chars_in_font]
        filter_dictionary['chars_not_in_font_cmap'] = chars_missing
    if filter_dictionary['has_empty_glyphs']:
        glyph_array = datarenderer.render_font(font_file,
                                                chars=required_chars,
                                                size=2,
                                                normalize=True)
        glyph_array = 1. - glyph_array
        empty_entries = (np.sum(glyph_array, axis=(0, 1)) == 0)
        empty_chars = [c for i, c in enumerate(required_chars) if empty_entries[i]]
        filter_dictionary['chars_with_empty_glyphs'] = empty_chars

    # Check if chars of chars_with_empty_glyphs are also in chars_not_in_font_cmap and remove them from chars_with_empty_glyphs
    # TODO: make this work around obsolete
    if filter_dictionary['has_empty_glyphs'] and filter_dictionary['has_not_all_chars']:
        chars_with_empty_glyphs = filter_dictionary['chars_with_empty_glyphs']
        chars_not_in_font_cmap = filter_dictionary['chars_not_in_font_cmap']
        chars_with_empty_glyphs = [c for c in chars_with_empty_glyphs if c not in chars_not_in_font_cmap]
        filter_dictionary['chars_with_empty_glyphs'] = chars_with_empty_glyphs
        if len(chars_with_empty_glyphs) == 0:
            filter_dictionary['has_empty_glyphs'] = False
            # erase chars_with_empty_glyphs from filter_dictionary
            filter_dictionary.pop('chars_with_empty_glyphs')

    analysis_string = ""
    for key, value in filter_dictionary.items():
        if key == 'has_not_all_chars' and value:
            analysis_string += f"Found missing characters: {filter_dictionary['chars_not_in_font_cmap']}\n"
        if key == 'has_empty_glyphs' and value:
            analysis_string += f"Found empty glyph entries: {filter_dictionary['chars_with_empty_glyphs']}\n"
        if key == 'out_of_bounds' and value:
            analysis_string += f"The characters of this font are not well defined within the metrics.\n"
    if analysis_string == "":
        analysis_string = "This is a good font file. No need to worry."

    return analysis_string