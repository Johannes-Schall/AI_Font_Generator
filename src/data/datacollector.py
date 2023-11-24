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
import json
import zipfile
import re

METADATA = 'METADATA.pb'
ZIPTYPE = '.zip'
FONTTYPES = ['.ttf', '.otf']
DESCRIPTION_JSON = '00dataset.json'
DIR_CONVERTED = 'converted'
IGNORED_KEYS = ['designer', 'date_added', 'full_name', 'copyright']


def parse_metadata(metadata_path, filename):
    """Parses the metadata file and extracts required fields."""

    with open(metadata_path, 'r', encoding='utf-8') as file:
        content = file.read()

    general_info = {}

    lines = content.split('\n')
    for line in lines:
        if line.startswith('license:'):
            general_info['license'] = line.split(':')[1].strip().strip('"')
        if line.startswith('category:'):
            general_info['category'] = line.split(':')[1].strip().strip('"')
        if line.startswith('subsets:'):
            if 'subsets' not in general_info:
                general_info['subsets'] = [
                    line.split(':')[1].strip().strip('"')]
            else:
                general_info['subsets'].append(
                    line.split(':')[1].strip().strip('"'))

    specific_info = {}
    fonts_data = re.findall(r'fonts \{(.*?)\}', content, re.DOTALL)
    for font_data in fonts_data:
        font_info = {}
        for line in font_data.split('\n'):
            if line.strip() and ':' in line:
                key, value = line.split(':', 1)
                # Speichern aller Schlüssel, aber später nur 'style' und 'weight' verwenden
                font_info[key.strip()] = value.strip().strip('"')
        if font_info.get('filename') == filename:
            # Auswahl nur der spezifischen Informationen 'style' und 'weight'
            specific_info = {k: v for k, v in font_info.items() if k in [
                'style', 'weight']}
            break

    metadata = {**general_info, **specific_info}
    return metadata


def collectfonts(source_directory):
    """Goes through source directory and all subdirectories
    and writes a json file with all the font information.

    Args:
        source_directory (String): Relative path to source directory,
                font files must be in subdirectories. JSON file will be
                written to this directory.
    """

    file_counter = 0
    file_ttf = 0
    file_otf = 0
    file_usable = 0

    fonts_metadata = {}

    # Go through hierarchy and unzip all zip files
    print("Unpacking all zip files...")
    search_zips(source_directory)

    # Search all folders and subfolders in source directory
    print("Collecting fonts...")
    for root, _, files in os.walk(source_directory):
        for file in files:
            file_counter += 1
            if file.lower().endswith(tuple(FONTTYPES)):
                if file.lower().endswith('.ttf'):
                    file_ttf += 1
                elif file.lower().endswith('.otf'):
                    file_otf += 1

                if file.lower()[:-4] not in fonts_metadata:
                    filepath = os.path.join(root, file)
                    normalized_filepath = os.path.normpath(filepath)
                    # Write general info about font to dict/later json
                    font_info = {'path': normalized_filepath,
                                 'usable': True}

                    file_usable += 1

                    metadata_path = os.path.join(root, METADATA)
                    if os.path.exists(metadata_path):
                        font_info['metadata'] = parse_metadata(
                            metadata_path, file)

                    fonts_metadata[file.lower()[:-4]] = font_info

    # Write json
    description_json = os.path.join(source_directory, DESCRIPTION_JSON)
    os.makedirs(os.path.dirname(description_json), exist_ok=True)

    with open(description_json, 'w', encoding='utf-8') as jsonfile:
        json.dump(fonts_metadata, jsonfile, indent=4)

    print(f"Total files: {file_counter}")
    print(f"Fonts files: {file_ttf + file_otf}")
    print(f"- TTF files: {file_ttf}")
    print(f"- OTF files: {file_otf}")
    print(f"Usable files: {file_usable}")


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
