#!/usr/bin/env python

"""
Dolphin Hunter
MySQL Runtime Analyzer

Author: Tim "Sweetums" Soderstrom
With contributions from BJ Dierkes and Andrew Garner

For questions, contact the Rackspace MySQL DBA team.
"""

import sys

if sys.version_info < (2, 4):
    print "Python 2.4 or later required. Sorry"
    sys.exit(1)

import platform
import os
import string
from optparse import OptionParser, OptionGroup
import warnings

warnings.simplefilter("ignore")

import MySQLdb

# Local Imports
from mysqlinfo import MySQL, MySQLError
from functions import format_interval, format_bytes, format_percent
from functions import print_header, print_stat
from functions import AttributeAdapter
#from colorize import color_print

##################
# Global Variables
##################
version = '0.7.0'
# How many items to list from list output
# (Such as information_schema reuslts)
limit = 10
TWO_DAYS_IN_SECONDS = 60 * 60 * 24 * 2

####################
# Display Functions
###################
def display_system_info(mysql):
    system_info = dict()
    print "Gathering system information...",

    system_info['architecture'] = platform.machine()
    if platform.system() == 'Linux':
        system_info['totalMemory'] = format_bytes(round(os.sysconf('SC_PHYS_PAGES') * \
            os.sysconf('SC_PAGE_SIZE')), 0)
        system_info['freeMemory'] = format_bytes(os.sysconf('SC_AVPHYS_PAGES') * \
            os.sysconf('SC_PAGE_SIZE'))
        system_info['cpuCores'] = os.sysconf('SC_NPROCESSORS_CONF')
    else:
        system_info['totalMemory'] = 'Unknown'
        system_info['freeMemory'] = 'Unknown'
        system_info['cpuCores'] = 'Unknown'
    print "done!\n"

    print_header('Local System Information', 1)
    print_stat('CPU Cores', system_info['cpuCores'], 1)
    print_stat('Total Memory', system_info['totalMemory'], 1)
    print_stat('System Architecture', system_info['architecture'], 1)

def display_mysql_global_results(mysql_info):
    print_header('Global Information', 2)
    print_stat('Server ID', int(mysql_info.vars.server_id))
    print_stat('MySQL Architecture',
        mysql_info.vars.version_compile_machine, 1)
    print_stat('MySQL Version', mysql_info.vars.version, 1)
    print_stat('Data Directory', mysql_info.vars.datadir)
    print_stat("Uptime", format_interval(mysql_info.status.uptime))
    print_stat('Max Allowed Packet',
        format_bytes(mysql_info.vars.max_allowed_packet))
    print_stat("Connections", "%s of %s" % \
        (int(mysql_info.status.max_used_connections),
         int(mysql_info.vars.max_connections)))
    print_stat("Disk Based Temp Tables", "%s of %s (%s)" % \
        (int(mysql_info.status.created_tmp_disk_tables),
         int(mysql_info.status.created_tmp_tables),
         format_percent(mysql_info.tmp_tables_disk_pct)))
    print_stat("Sort Merge Passes",
        int(mysql_info.status.sort_merge_passes))
    print_stat("Non-Indexed Joins",
        int(mysql_info.status.select_full_join))
    print_stat("Open Files", '%s (limit %s)' % \
        (int(mysql_info.status.open_files),
         int(mysql_info.vars.open_files_limit)))
    print_stat("Open Tables",
        int(mysql_info.status.open_tables))
    if mysql_info.vars.query_cache_size == 0:
	print_stat("Query Cache", "Disabled")
    else:
    	print_stat("Query Cache"),
        print_stat("Size",
            format_bytes(mysql_info.vars.query_cache_size), 2)
        print_stat("Hit Rate",
            format_percent(mysql_info.query_cache_hitrate), 2)
    print_stat("Table Lock Waits", "%s of %s (%s)" % \
        (int(mysql_info.status.table_locks_waited),
         int(mysql_info.table_locks_total),
         format_percent(mysql_info.table_lock_wait_pct)))
    print_stat("Estimated Table Scans",
        format_percent(mysql_info.table_scans_pct))
    print_stat("Slow Queries")
    print_stat("Queries", "%s of %s (%s)" % \
        (int(mysql_info.status.slow_queries),
         int(mysql_info.status.com_select),
         format_percent(mysql_info.slow_query_pct)), 2)
    print_stat("Long Query Time",
        format_interval(mysql_info.vars.long_query_time), 2)
    print_stat("Log Non-Indexed Queries",
        mysql_info.vars.log_queries_not_using_indexes, 2)
    print_stat('Binary Log', '')
    print_stat('Binary Logging',
        mysql_info.vars.log_bin, 2)
    try:
        print_stat('Binlog Format',
            mysql_info.vars.binlog_format, 2)
    except KeyError:
        print_stat('Binlog Format', 'Not-Detected / Pre 5.1', 2)
    print_stat("Read Frequency", format_percent(mysql_info.read_pct))

def display_mysql_myisam_results(mysql_info):
    print_header("MyISAM", 2)
    print_stat("Key Buffer")
    print_stat("Size", format_bytes(mysql_info.vars.key_buffer_size), 2)
    print_stat("Used",  "%s (%s)" % \
        (format_bytes(mysql_info.key_buffer_used),
         format_percent(mysql_info.key_buffer_used_pct)), 2)

def display_mysql_innodb_results(mysql_info):
    print_header("InnoDB", 2)
    if mysql_info.vars.have_innodb  == ('DISABLED' or False):
        print "Disabled"
    else:
        try:
            print_stat('Version', mysql_info.vars.innodb_version)
        except KeyError:
            print_stat('Version', 'Default')
        print_stat('Paths','')
        print_stat('InnoDB Home Directory',
            mysql_info.vars.innodb_data_home_dir, 2)
        print_stat("InnoDB Log Directory",
            mysql_info.vars.innodb_log_group_home_dir, 2)
        print_stat("InnoDB Data File Path",
            mysql_info.vars.innodb_data_file_path, 2)
        print_stat('Buffer Pool', '')
        print_stat("Usage", "%s of %s (%s)" % \
            (format_bytes(mysql_info.innodb_buffer_pool_used),
             format_bytes(mysql_info.vars.innodb_buffer_pool_size),
             format_percent(mysql_info.innodb_buffer_pool_used_pct)), 2)
        print_stat("Hit Rate",
            format_percent(mysql_info.innodb_buffer_pool_hit_rate), 2)
        print_stat('History List', mysql_info.ibstatus.history_list_length)
        print_stat("File Per Table",
            mysql_info.vars.innodb_file_per_table)
        if mysql_info.vars.innodb_file_per_table:
            print_stat("InnoDB Open Files",
                int(mysql_info.vars.innodb_open_files), 2)
        print_stat("Flush Log At Commit",
            int(mysql_info.vars.innodb_flush_log_at_trx_commit))
        print_stat("Flush Method",
            mysql_info.innodb_flush_method)
        print_stat("Thread Concurrency",
            int(mysql_info.vars.innodb_thread_concurrency))
        print_stat("Log File Size", "%s x %s logs (%s total)" % \
            (format_bytes(mysql_info.vars.innodb_log_file_size),
             int(mysql_info.vars.innodb_log_files_in_group),
             format_bytes(mysql_info.innodb_log_file_size_total)))

def display_mysql_thread_results(mysql_info):
    print_header("Threads", 2)
    print_stat("Buffers")
    print '      %-9s : %-9s : %-9s : %-9s' % \
        ('Read', 'Read RND', 'Sort', 'Join')
    print '      %-9s : %-9s : %-9s : %-9s' % \
        (format_bytes(mysql_info.vars.read_buffer_size),
         format_bytes(mysql_info.vars.read_rnd_buffer_size),
         format_bytes(mysql_info.vars.sort_buffer_size),
         format_bytes(mysql_info.vars.join_buffer_size))
    print_stat("Threads")
    print '      %-9s : %-9s : %-9s : %-9s' % \
         ('Size', 'Cached', 'Running', 'Created')
    print '      %-9s : %-9s : %-9s : %-9s' % \
        (int(mysql_info.vars.thread_cache_size),
        int(mysql_info.status.threads_cached),
        int(mysql_info.status.threads_running),
        int(mysql_info.status.threads_created))

def display_slave_info(mysql_info):
    print_header('Replication', 2)
    if mysql_info.slave_status is None:
        print "Not Enabled"
        return
    print_stat('Master',
        mysql_info.slave_status.master_host)
    print_stat('Logs', '')
    print_stat('Spooled Master Log File',
        '%s (pos: %s)' % \
        (mysql_info.slave_status.master_log_file,
         mysql_info.slave_status.read_master_log_pos), 2)
    print_stat('Executed Master Log File',
        '%s (pos: %s)' % \
        (mysql_info.slave_status.relay_master_log_file,
         mysql_info.slave_status.exec_master_log_pos), 2)
    print_stat('Relay Log File',
        '%s (pos: %s)' % \
        (mysql_info.slave_status.relay_log_file,
         mysql_info.slave_status.relay_log_pos), 2)
    # Using a long-style if for Python 2.4 compatibility
    #print_stat('Relay Log Space Limit',
    #(format_bytes(mysql_info.vars.relay_log_space_limit))
    # if mysql_info.vars.relay_log_space_limit != 0 else 'Unlimited')
    if mysql_info.vars.relay_log_space_limit != 0:
        print_stat('Relay Log Space Limit',
            format_bytes(mysql_info.vars.relay_log_space_limit))
    else:
        print_stat('Relay Log Space Limit', 'Unlimited')
    print_stat('IO Thread Running',
        mysql_info.slave_status.slave_io_running)
    print_stat('SQL Thread Running',
        mysql_info.slave_status.slave_sql_running)
    print_stat('Seconds Behind Master',
        mysql_info.slave_status.seconds_behind_master)
    print_stat('Last Error',
        mysql_info.slave_status.last_error)

def display_mysql_results(mysql):
    print ""
    mysql_info = mysql.mysql_info
    print ""
    print_header('MySQL Information', 1)
    print ""
    display_mysql_global_results(mysql_info)
    print ""
    display_mysql_thread_results(mysql_info)
    print ""
    display_mysql_myisam_results(mysql_info)
    print ""
    display_mysql_innodb_results(mysql_info)
    print ""
    display_slave_info(mysql_info)


def display_innodb_transactions(mysql):
    print ""
    print_header("InnoDB Transactions")
    try:
        for i, txn in enumerate(mysql.mysql_info.ibstatus.transactions):
            print "TRANSACTION(%d)" % i
            print txn
    except ValueError:
        print "Unable To Parse SHOW ENGINE INNODB STATUS"

def display_schema_info(mysql):
    print ""
    print_header("Schema Information")
    print ""
    print_header("Engine Breakdown", 2)
    print '%-8s : %8s : %12s : %12s' % \
        ('Engine', '# Tables', 'Data Length', 'Index Length')
    for row in mysql.schema_engine_summary:
        print '%-8s : %8s : %12s : %12s' % \
            (row['Engine'],
            row['Count'],
            format_bytes(row['Data Length']),
            format_bytes(row['Index Length']))
    print ""
    print_header('%s Largest Databases' % limit, 2)
    print '%-32s : %12s : %12s' % \
        ('Database', 'Data Length', 'Index Length')
    for row in mysql.schema_largest_dbs(limit):
        print '%-32s : %12s : %12s' % \
            (row['Database'],
            format_bytes(row['Data Length']),
            format_bytes(row['Index Length']))
    print ""
    print_header('%s Largest Tables' % limit, 2)
    print '%-32s : %12s : %12s' % \
        ('Table', 'Data Length', 'Index Length')
    for row in mysql.schema_largest_tables(limit):
        print '%-32s : %12s : %12s' % \
            (row['Table'],
            format_bytes(row['Data Length']),
            format_bytes(row['Index Length']))


#################
# Meat & Potatoes
#################

# Preamble
print("""
                        |
                        |
                        |
                        |          __
                        |      _.-~  )
                    _..-|~~~~,'   ,-/     _
                 .-'. . | .'   ,-','    ,' )
               ,'. . . _|  ,--~,-'__..-'  ,'
             ,'. . .  (@|' ---~~~~      ,'
------------------------+------------------------
           /. . . . .   |         ,-'
          ; . . . .  - .|       ,'
         : . . . .      |_     /
        . . . . .       |  `-.:
       . . . ./  - .    |     )
      .  . . |  _____..-|-.._/ _____
~---~~~~----~~~~        |    ~~
                        |
                        |

Dolphin Hunter v%s
MySQL Runtime Analyzer
Author: Tim "Sweetums" Soderstrom
With contributions from BJ Dierkes and Andrew Garner

For questions, contact the Rackspace MySQL DBA team.
""" % version)

# Callback for OptionParser when -a is used
def set_all(option, opt, value, parser):
    parser.values.actions.extend([
        (10, display_system_info),
        (20, display_mysql_results),
        (30, display_innodb_transactions),
        (40, display_schema_info),
        ])

# For Python 2.4 compatibility
def append_const_callback(priority, const):
    def callback( option, opt_str, value, parser ):
        getattr(parser.values, option.dest).append((priority, const))
    return callback

# Main
def main():
    # The numbers before the function in const denote priority to make sure
    # the output is always in the same order. It also helps avoid priting
    # information more than once.
    parser = OptionParser()
    parser.add_option('-a', '--all', action='callback', type=None,
        callback=set_all,
        help="Gather all possible information")
    parser.add_option('-y', '--system', action='callback',
        dest="actions", callback=append_const_callback(10,display_system_info),
        help="Print System Information")
    parser.add_option('-i', '--info', action='callback',
        dest="actions", callback=append_const_callback(20,display_mysql_results),
        help="MySQL Information")
    parser.add_option('-t', '--transactions', action='callback',
        dest="actions", callback=append_const_callback(30, display_innodb_transactions),
        help='Display InnoDB transactions')
    parser.add_option('-s', '--schema', action='callback',
        dest="actions", callback=append_const_callback(40, display_schema_info),
        help="Print Schema Statistics (Avoid For Large #'s of Tables/DBs)")
    parser.add_option('-h', '--health', action='callback',
        dest="actions", callback=append_const_callback(50, check_health),
        help="Look at various metrics in MySQL and bomb if there is a problem. Useful for things like Monit")

    mysql_health_group = OptionGroup(parser, "MySQL Health Check Options")
    mysql_login_group.add_option('-d', '--delay', dest="delay",
        help="MySQL Slave Delay")
mysql_login_group.add_option('-d', '--delay', dest="delay",
    help="MySQL Slave Delay")
      parser.add_option_group(mysql_health_group)

    mysql_login_group = OptionGroup(parser, "MySQL Login Options")
    mysql_login_group.add_option('-u', '--username', dest="user",
        help="MySQL User")
    mysql_login_group.add_option('-p', '--password', dest="passwd",
        help="MySQL Password")
    mysql_login_group.add_option('-H', '--hostname', dest="host",
        help="MySQL host to connect to")
    mysql_login_group.add_option('-P', '--port', dest='port',
        type='int', help="MySQL port to connect to")
    mysql_login_group.add_option('-S', '--socket', dest="unix_socket",
        help="Path to MySQL unix socket")
    parser.add_option_group(mysql_login_group)

    parser.set_defaults(actions=[])
    opts, args = parser.parse_args()

    # Pull out MySQL login information passed from command-line
    connection_args = {}
    for key in ('user', 'passwd', 'host', 'port', 'unix_socket'):
        value = getattr(opts, key)
        if value is not None:
            connection_args[key] = value

    # Display help by default
    if not opts.actions:
        parser.print_help()
        return 0

    # Iterate through actions and call functions magically
    mysql = MySQL(read_default_group='client', charset='utf8', **connection_args)
    for priority, action in sorted(set(opts.actions)):
        action(mysql)
    return 0

if __name__ == "__main__":
    sys.exit(main())
