"""One palette for every presentation pass. CBRE green is the baseline.

Colour carries meaning everywhere in the workbook:
  input  = white          wired from another tab = celadon tint
  calc   = green tint     governance / QA        = wheat tint
"""
FONT = 'Roboto'

# CBRE brand
CBRE_GREEN = '#003F2D'      # primary: title bands, primary headers, tab colour
ACCENT = '#17E88F'          # bright green: emphasis on dark bands
MIDNIGHT = '#032842'
SAGE = '#538184'            # secondary headers (wired zones)
CELADON = '#80BBAD'
WHEAT = '#DBD99A'
LIGHT = '#CAD1D3'           # light grey: rules, machinery tab colour
DARK_GREEN = '#012A1E'      # subtitle bands
FOREST = '#1F6F55'          # tertiary headers (computed zones)
OLIVE = '#7A6E1F'           # governance headers

# neutrals
INK = '#0B1F18'
MUTED = '#4B5F58'
RULE = '#D5DDDB'
PAPER = '#F4F7F6'
WHITE = '#FFFFFF'

# zone tints (data cells)
WIRE = '#E9F3F0'
WIRE_ALT = '#DCEBE6'
CALC = '#E8F4EE'
CALC_ALT = '#DAEDE3'
GOV = '#F7F5E3'
GOV_ALT = '#EFECCF'
INPUT_ALT = '#F4F7F6'

# status
OK_BG, OK_FG = '#DDF3E8', '#003F2D'
WARN_BG, WARN_FG = '#F7F0C8', '#6B5E00'
BAD_BG, BAD_FG = '#F9E0DB', '#8A2E1E'
NEUTRAL_BG, NEUTRAL_FG = '#E6EBEA', '#4B5F58'

# tab colours
TAB_PRIMARY, TAB_INPUT, TAB_MACHINERY = CBRE_GREEN, SAGE, LIGHT


def hx(h):
    h = h.lstrip('#')
    return {'red': int(h[0:2], 16) / 255, 'green': int(h[2:4], 16) / 255,
            'blue': int(h[4:6], 16) / 255}
