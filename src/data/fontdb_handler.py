""" Module for handling the json font database. """
import json
from . import global_consts as g

def font_file_list():
    """ Output all usable fonts.

    Returns:
        List: Returns list of paths to all used fonts.
    """

    path_to_json = g.PATH_TO_JSON_FONT_DB

    with open(path_to_json, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Extract paths of all usable fonts
    return [font_path for font_path in data.keys() if data[font_path].get("usable", True)]


def write_filter_results(path_font_db_json, filter_dictionary):
    """Writes filter results to a log file.

    Args:
        path_font_db_json (String): Path to the font database json file.
        filter_dictionary (Dictionary): Dictionary with filter results.
    """

    with open(path_font_db_json, 'r', encoding='utf-8') as file:
        font_db = json.load(file)

    for font_path in font_db.keys():
        for filter_font_path, value in filter_dictionary.items():
            if filter_font_path == font_path:
                font_db[font_path].update(value)
                break

    with open(path_font_db_json, 'w', encoding='utf-8') as file:
        json.dump(font_db, file, indent=4)


def is_glyph_usable(path_fonts: list, char: str) -> dict:
    """ Checks whether a glpyh was classified as usable.
        Returns True if the glyph is usable OR if the glyph was not classified

    Args:
        path_fonts (list): List of paths to the fonts
        char (str): The glyph to check

    Returns:
        dict: Dictionary with path to font as key and True/False as value
    """

    with open(g.PATH_TO_JSON_FONT_DB, 'r', encoding='utf-8') as file:
        data = json.load(file)

    return {font_path: data[font_path]["clip_filter"].get(char, True)
            if "clip_filter" in data[font_path] else True
            for font_path in path_fonts}