""" Module for handling the json font database. """
import json


def font_file_list(path_to_json):
    """ Loads font database from json file.

    Args:
        path_to_json (String): Path to the font database json file.

    Returns:
        List: Returns list of paths to all used fonts.
    """
    with open(path_to_json, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Extract paths of all used fonts
    paths_list = []
    for entry in data.values():
        if entry["usable"]:
            paths_list.append(entry["path"])
    return paths_list


def write_filter_results(path_font_db_json, filter_dictionary):
    """Writes filter results to a log file.

    Args:
        path_font_db_json (String): Path to the font database json file.
        filter_dictionary (Dictionary): Dictionary with filter results.
    """

    with open(path_font_db_json, 'r', encoding='utf-8') as file:
        font_db = json.load(file)

    for db_font_data in font_db.values():
        for filter_font_path, value in filter_dictionary.items():
            if filter_font_path == db_font_data["path"]:
                db_font_data.update(value)
                break

    with open(path_font_db_json, 'w', encoding='utf-8') as file:
        json.dump(font_db, file, indent=4)
