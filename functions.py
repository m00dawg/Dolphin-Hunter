# Generic Helper Functions

#from colorize import color_print

# Convert Seconds to a human readable format
# Contributed from Holland
def format_interval(seconds):
    """ Format an integer number of seconds to a human readable string."""
    units = [
        (('week', 'weeks'), 604800),
        (('day', 'days'), 86400),
        (('hour', 'hours'), 3600),
        (('minute', 'minutes'), 60),
        #(('second', 'seconds'), 1)
    ]
    result = []
    for names, value in units:
        n, seconds = divmod(seconds, value)
        if n > 0:
            result.append('%d %s' % (n, names[n > 1]))
    if seconds:
        result.append("%.2f %s" % (seconds, ['second', 'seconds'][seconds != 1.0]))
    return ', '.join(result)
    
# Format a number (presumably bytes) into a more human readable format.
# Contributed from Holland
def format_bytes(bytes, precision=2):
   """Format an integer number of bytes to a human readable string."""
   import math
   bytes = float(bytes)

   if bytes != 0:
       exponent = int(math.log(abs(bytes), 1024))
   else:
       exponent = 0

   return "%.*f%s" % (precision,
    bytes / (1024.0 ** exponent),
    ['  B',' KB',' MB',' GB',' TB',' PB',' EB',' ZB',' YB'][exponent]
    )

def format_percent(percentage, precision=2):
    return "%.2f%%" % round(percentage, precision)

# Print an ASCII-art header
def print_header(text, level=1):
    if level == 1:
        seperator = '-' * (len(text) + 2)
        print "%s%s%s" % ('+', seperator, '+') 
        print "|", text, "|"
#        print "|",
#        color_print(text, 'WHITE'),
#        print "|"
        print "%s%s%s" % ('+', seperator, '+')    
    elif level == 2:
        print text
        print '-' * len(text)
        
def print_stat(item, value = '', level=1):
    if level == 1:
        print '-',
        #color_print('-', 'BLUE')
    elif level == 2:
        print '  +',
        #color_print('  +', 'RED')
    elif level == 3:
        print '    >',
        #color_print('    >', 'YELLOW')
    print "%s: %s" % (item, value)
    
class AttributeAdapter(dict):
    def __getattr__(self, key):
        return dict.__getitem__(self, key)

    def __setattr__(self, key, value):
        dict.__setitem__(self, key, value)