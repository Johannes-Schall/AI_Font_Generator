from fontTools.ttLib import TTFont
from fontTools.psfLib import PSF


def convert_pfb_to_otf(pfb_path, otf_path):
    font = PSF(pfb_path)
    font.flavor = 'otf'
    font.save(otf_path)

def convert_ttf_to_otf(ttf_path, otf_path):
    font = TTFont(ttf_path)
    font.flavor = 'otf'
    font.save(otf_path)