############
# Colorize #
############

# Setup Code and Functions To Deal With ANSI Color

import sys
import os
import curses
import string

try:
    import curses
    curses.setupterm()
except ImportError:
    curses = None

__all__ = [
    'TERM_CODES',
    'colorize'
]

# Setup terminal colors
TERM_CODES = {}

_COLORS = "BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE".split()
for n, name in enumerate(_COLORS):
    if not os.isatty(sys.stdout.fileno()) or not curses:
        TERM_CODES[name] = ''
    else:
        TERM_CODES[name] = curses.tparm(curses.tigetstr('setaf'), n)
del n, name
del _COLORS

_CAPABILITIES = "NORMAL=sgr0 BOLD=bold UNDERLINE=smul REVERSE=rev DIM=dim".split()
for capability in _CAPABILITIES:
    name, termcap = capability.split('=')
    if not os.isatty(sys.stdout.fileno()) or not curses:
        TERM_CODES[name] = ''
    else:
        TERM_CODES[name] = curses.tigetstr(termcap)
del capability, name, termcap
del _CAPABILITIES

#############
# Functions #
#############

# Wrapper to help print pretty colors
def color_print(text, color, capability = 'BOLD'):
    print string.Template('${' + capability + '}' + '${' + color + '}' + text + '${NORMAL}').safe_substitute(TERM_CODES), 
