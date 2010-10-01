import MySQLdb
import sys

# Local Imports
from functions import AttributeAdapter
from innoparse import Transaction, InnodbStatus

MySQLError = MySQLdb.MySQLError

def convert(value):
    try:
        # convert anything that looks like a number to a number
        return float(value)
    except ValueError:
        pass
    try:
        # convert anything that looks like a boolean to a bool
        return bool(['OFF','ON'].index(value))
    except ValueError:
        pass
    try:
        # another bool format
        return bool(['NO','YES'].index(value))
    except ValueError:
        pass
    if value == '':
        return None
    # otherwise, remain as normal text
    return value

class MySQL:
    my_mysql_info = None

    def __init__(self, *args, **kwargs):
        self._connection = MySQLdb.connect(*args, **kwargs)

    """ Obtained from Holland """
    def server_version(self):
        """
        server_version(self)
        returns a numeric tuple: major, minor, revision versions (respectively)
        """
        version = self.get_server_info()
        m = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
        if m:
            return tuple([int(v) for v in m.groups()])
        else:
            raise MySQLError("Could not match server version: %r" % version)

    def collect(self):
        if self.my_mysql_info is None:
            print "Gathering MySQL information...",
            # Grab the STATUS and VARIABLES from MySQL and put them both into dictionaries
            try:
                cursor = self._connection.cursor()
                cursor.execute("SHOW GLOBAL STATUS")
                status = AttributeAdapter(dict([(key.lower(), convert(value))
                        for key, value in cursor.fetchall()]))
                cursor.execute("SHOW GLOBAL VARIABLES")
                vars = AttributeAdapter(dict([(key.lower(), convert(value))
                         for key, value in cursor.fetchall()]))

                cursor.execute("SHOW SLAVE STATUS")
                if cursor.rowcount > 0:
                    fields = [f[0].lower() for f in cursor.description]
                    slave_status = AttributeAdapter(dict(zip(fields, cursor.fetchone())))
                else:
                    slave_status = None
    
                if(vars.have_innodb == True):
                    cursor.execute("SHOW ENGINE INNODB STATUS")
#                    fields = [f[0] for f in cursor.description]
#                    innodb_status = dict(zip(fields, cursor.fetchone()))['Status']
                    innodb_status = InnodbStatus(cursor.fetchone()[-1])
                    cursor.close()
                else:
                    innodb_status = "Disabled"
                    
                self.my_mysql_info = MySQLInfo(status, vars, slave_status, innodb_status)
                print "done!"
            except MySQLdb.MySQLError, exc:
                print '[%d] %s' % exc.args
                print 'Unable to gather information from MySQL!\nPerhaps the MySQL ' \
                    'user we are connecting with doese not have proper permissions?'
                sys.exit()
        return self.my_mysql_info
    
    @property
    def mysql_info(self):
        self.collect()
        return self.my_mysql_info
        
    ###############
    # Schema Info #
    ###############
    @property
    def schema_engine_summary(self):
        try:
            cursor = self._connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT ENGINE AS Engine, COUNT(ENGINE) AS Count, \
                SUM(DATA_LENGTH) AS 'Data Length', \
                SUM(INDEX_LENGTH) AS 'Index Length' \
                FROM information_schema.TABLES WHERE ENGINE IS NOT NULL \
                GROUP BY ENGINE")
            engine_summary = cursor.fetchall()
            cursor.close()
            return engine_summary
        except MySQLError, exc:
            self.mysql_schema_error()
            
    def schema_largest_dbs(self, limit=10):
        try:
            cursor = self._connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT TABLE_SCHEMA AS 'Database', \
                SUM(DATA_LENGTH) AS 'Data Length', \
                SUM(INDEX_LENGTH) AS 'Index Length' \
                FROM information_schema.TABLES \
                WHERE TABLE_SCHEMA != 'information_schema' \
                GROUP BY TABLE_SCHEMA \
                ORDER BY SUM(DATA_LENGTH) DESC, SUM(INDEX_LENGTH) DESC \
                LIMIT %s", limit)
            largest_dbs = cursor.fetchall()
            cursor.close()
            return largest_dbs
        except Exception:
            self.mysql_schema_error()
    
    def schema_largest_tables(self, limit=10):
        try:
            cursor = self._connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT \
                CONCAT(TABLE_SCHEMA, '.', TABLE_NAME) AS 'Table', \
                DATA_LENGTH AS 'Data Length', \
                INDEX_LENGTH AS 'Index Length' \
                FROM information_schema.TABLES \
                WHERE \
                TABLE_SCHEMA != 'information_schema' \
                ORDER BY DATA_LENGTH DESC, INDEX_LENGTH DESC \
                LIMIT %s", limit)
            largest_tables = cursor.fetchall()
            cursor.close()
            return largest_tables
        except Exceptoion:
                self.mysql_schema_error()
            
    def mysql_schema_error(self):
        print 'Unable to schema information from MySQL!\nPerhaps the MySQL ' \
            'user we are connecting with doese not have proper permissions?'
        raise

class MySQLInfo(object):
    def __init__(self, status, vars, slave_status, ibstatus):
        self.status = status
        self.vars = vars
        self.ibstatus = ibstatus        
        self.slave_status = slave_status

    @property
    def key_buffer_used_pct(self):
        status = self.status
        try:
            return (status.key_blocks_used / status.key_blocks_unused) * 100
        except ZeroDivisionError:
            return 0

    @property
    def key_buffer_used(self):
        status = self.status
        key_buffer_size = self.vars.key_buffer_size
        try:
            return (status.key_blocks_used / 
                    status.key_blocks_unused * 
                    key_buffer_size)
        except ZeroDivisionError:
            return 0

    @property
    def key_buffer_hitrate(self):
        status = self.status
        try:
            return ((1 - status.key_reads) / status.key_read_requests)*100
        except ZeroDivisionError:
            return 0

    @property
    def innodb_buffer_pool_used(self):
        status = self.status
        return (status.innodb_buffer_pool_pages_total - 
                status.innodb_buffer_pool_pages_free) * \
                status.innodb_page_size

    @property
    def innodb_buffer_pool_used_pct(self):
        status = self.status
        try:
            return (1 - status.innodb_buffer_pool_pages_free  /
                        status.innodb_buffer_pool_pages_total) * 100
        except ZeroDivisionError:
            return 0
    
    @property
    def innodb_buffer_pool_hit_rate(self):
        status = self.status
        try:
            return (1 - status.innodb_buffer_pool_reads / 
                        status.innodb_buffer_pool_read_requests) * 100
        except ZeroDivisionError:
            return 0

    @property
    def innodb_log_file_size_total(self):
        vars = self.vars
        return (vars.innodb_log_file_size * 
                vars.innodb_log_files_in_group)
                
    @property
    def innodb_flush_method(self):
        vars = self.vars
        if vars.innodb_flush_method == None:
            return 'FSYNC'
        else:
            return vars.innodb_flush_method
        
    @property
    def slow_query_pct(self):
        status = self.status
        total_queries = sum([status[key] for key in ('com_select', 
                                                    'com_insert',
                                                    'com_update',
                                                    'com_delete')])
        try:
            return (status.slow_queries / total_queries) * 100
        except ZeroDivisionError:
            return 0

    @property
    def read_pct(self):
        status = self.status
        total_queries = sum([status[key] for key in ('com_select',
                                                    'com_insert',
                                                    'com_update',
                                                    'com_delete')])
        try:
            return (status.com_select / total_queries) * 100
        except ZeroDivisionError:
            return 0

    @property
    def tmp_tables_disk_pct(self):
        status = self.status
        try:
            return (status.created_tmp_disk_tables / 
                    status.created_tmp_tables) * 100
        except ZeroDivisionError:
            return 0

    @property
    def table_locks_total(self):
        status = self.status
        return(status.table_locks_waited + status.table_locks_immediate)

    @property
    def table_lock_wait_pct(self):
        status = self.status
        try:
            return (status.table_locks_waited /
                    (status.table_locks_waited +
                    status.table_locks_immediate)) * 100
        except ZeroDivisionError:
            return 0

    @property
    def table_scans_pct(self):
        status = self.status
        try:
            return (status.handler_read_rnd_next + \
                    status.handler_read_rnd) / \
                    (status.handler_read_rnd_next + 
                     status.handler_read_rnd + status.handler_read_first +
                     status.handler_read_next + status.handler_read_key + 
                     status.handler_read_prev) * 100
        except ZeroDivisionError:
            return 0
            
    @property
    def query_cache_hitrate(self):
        status = self.status
        try:
            return (status.qcache_hits / 
                    (status.qcache_hits + 
                    status.com_select)) * 100
        except ZeroDivisionError:
            return 0
