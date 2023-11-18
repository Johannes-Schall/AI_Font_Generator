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
import argparse
import json
import re

METADATA = 'METADATA.pb'
FONTTYPE = '.ttf'
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

    fonts_metadata = []
    description_json = os.path.join(destination_directory, DESCRIPTION_JSON)

    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    # Durchlaufe alle Ordner und Unterordner im Quellverzeichnis
    for root, _, files in os.walk(source_directory):
        if METADATA in files:
            with open(os.path.join(root, METADATA), 'r') as metafile:
                metadata = parse_metadata(metafile.read())

                for file in files:
                    if file.endswith(FONTTYPE):
                        source_file = os.path.join(root, file)
                        destination_file = os.path.join(
                            destination_directory, file)

                        # Copy ttf to destination directory
                        shutil.copy2(source_file, destination_file)
                        print(f"Copy: {source_file} -> {destination_file}")

                        # Collect metadata
                        font_metadata = metadata.copy()
                        font_metadata['filename'] = file
                        fonts_metadata.append(font_metadata)

    # Write json
    os.makedirs(os.path.dirname(description_json), exist_ok=True)

    with open(description_json, 'w', encoding='utf-8') as jsonfile:
        json.dump(fonts_metadata, jsonfile, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('source_directory', type=str, help='Source directory')
    parser.add_argument('destination_directory',
                        type=str, help='Target directory')
    args = parser.parse_args()

    try:
        collectfonts(args.source_directory, args.destination_directory)
    except Exception as e:
        print(f"Error: {e}")
