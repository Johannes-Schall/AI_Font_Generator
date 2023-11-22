""" 
    Helper script to collect fonts from directories and subdirectories,
    collect information from METADATA.pb files and copy the fonts to a
    destination directory.
    
+   The script also creates a description.json file in the destination directory
+   that contains all the information from the METADATA.pb files.
+
+   The script is based on the fonts from the Google Fonts project

    Usage:
    python datacollector.py <source_directory> <destination_directory>
"""

import os
import shutil
# import json
import re
import zipfile

METADATA = 'METADATA.pb'
ZIPTYPE = '.zip'
FONTTYPES = ['.ttf', '.otf']
DESCRIPTION_JSON = '00dataset.json'
IGNORED_KEYS = ['designer', 'date_added', 'full_name', 'copyright']


def parse_metadata(contents):
    """Parses the metadata file and extracts required fields."""
    metadata = {}

    lines = contents.split('\n')

    # Remove spaces at the beginning of the line (e.g. in fonts{xxxx})
    for entry in lines:
        if entry.startswith(' '):
            line = entry.strip()
        else:
            line = entry
        key_value_match = re.match(r'(\w+):[ ]*"?(.*?)"?$', line)
        if key_value_match:
            # This should catch all values that are written in the style of key: value
            key, value = key_value_match.groups()

            if key not in IGNORED_KEYS:
                if key not in metadata:
                    metadata[key] = value
                else:
                    if metadata[key] != value:
                        # Some keys have more than just one value, e.g. subsets and classifications
                        # In this case, the value might be a list, so we have to check for that
                        # If not a list, we have to create a list and append the existing value
                        if not isinstance(metadata[key], list):
                            # Turn existing value into list
                            data = [metadata[key]]
                        else:
                            data = metadata[key]  # Use existing list

                        data.append(value)  # Append new value
                        metadata[key] = data

    metadata['used'] = True

    return metadata


def collectfonts(source_directory, destination_directory):
    """Goes through source directory and all subdirectories
    and copies all font files to destination directory.

    Args:
        source_directory (String): Relative path to source directory
        destination_directory (String): Relative path to destination directory
    """

    file_counter = 0

    fonts_metadata = []
    description_json = os.path.join(destination_directory, DESCRIPTION_JSON)

    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    # Go through hierarchy and unzip all zip files
    search_zips(source_directory)

    # Search all folders and subfolders in source directory
    for root, _, files in os.walk(source_directory):
        for file in files:
            if file.endswith(tuple(FONTTYPES)):
                source_file = os.path.join(root, file)
                destination_file = os.path.join(
                    destination_directory, file)

                # Copy file to destination directory
                shutil.copy2(source_file, destination_file)
                print(f"Copy: {source_file} -> {destination_file}")
                file_counter += 1
    print(f"Total files copied: {file_counter}")
    #          Metadata not availabe in databases and not yet used in project
    #
    #             if METADATA in files:
    #                 with open(os.path.join(root, METADATA), 'r', encoding='utf-8') as metafile:
    #                     metadata = parse_metadata(metafile.read())

    #             # Collect metadata
    #             font_metadata = metadata.copy()
    #             font_metadata['filename'] = file
    #             fonts_metadata.append(font_metadata)

    # # Write json
    # os.makedirs(os.path.dirname(description_json), exist_ok=True)

    # with open(description_json, 'w', encoding='utf-8') as jsonfile:
    #     json.dump(fonts_metadata, jsonfile, indent=4)


def search_zips(source_directory):
    """ Call to recursively search for zip files in a directory and unpack them

    Args:
        source_directory (String): Path to hierarchy of directories
    """
    for root, _, files in os.walk(source_directory):
        for file in files:
            if file.endswith(ZIPTYPE):
                file_path = os.path.join(root, file)

                unpack(file_path, root)
                # Delete zip file after unpacking
                os.remove(file_path)
                # Recursively search for zip files in unpacked directory
                search_zips(root)


def unpack(file_path, extract_to):
    """ Unpacks zip files to a destination directory

    Args:
        file_path (String): Path to zip file
        extract_to (String): Path to destination directory
    """
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
