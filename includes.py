#!/usr/bin/env python
import sys

if sys.version_info < (2, 4):
    print "Python 2.4 or later required. Sorry"
    sys.exit(1)

import re
import time
import platform
import os
import string
from optparse import OptionParser, OptionGroup
import warnings

warnings.simplefilter("ignore")

import MySQLdb

# Local Imports
#from mysqlinfo import MySQL, MySQLError
#from functions import format_interval, format_bytes, format_percent
#f#rom functions import print_header, print_stat
#from functions import AttributeAdapter
#from innoparse import Transaction, InnodbStatus
#from colorize import color_print

