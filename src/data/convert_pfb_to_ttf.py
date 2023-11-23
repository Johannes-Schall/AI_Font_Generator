""" Tool to convert pfb files to ttf files.
    Run this script from the command line with
    ffpython (requires fontforge python bindings).
"""

import os
import fontforge


def convert_pfb_to_ttf(input_dir, output_dir):
    """ Convert pfb files to ttf files.

    Args:
        input_dir (String): Directory to pfb files
        output_dir (String): Directory for output ttf files
    """
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pfb'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(
                output_dir, filename.lower().replace('.pfb', '.ttf'))

            font = fontforge.open(input_path)
            font.generate(output_path)


# Setzen Sie hier den Pfad zu Ihrem Eingabe- und Ausgabeverzeichnis
INPUT = 'pfb/'
OUTPUT = 'pfb/'

convert_pfb_to_ttf(INPUT, OUTPUT)
