import MySQLdb

mysql_conn = None

def connect_to_mysql():
    global mysql_conn
    
    if mysql_conn is None:
        # Connect to MySQL (this could likely be much improved to, say, read
        # the .my.cnf, etc.
        try:
            mysql_conn = MySQLdb.connect(
            read_default_group = 'client')
        except MySQLdb.MySQLError, exc:
            print "[%d] %s" % exc.args
            print "Cannot Connect to MySQL"
            print "Is MySQL running? If your .my.cnf correct?"
            print "Do you need to configure the script with a username and password?"
            sys.exit()

class AttributeAdapter(dict):
    def __getattr__(self, key):
        return dict.__getitem__(self, key)

    def __setattr__(self, key, value):
        dict.__setitem__(self, key, value)

# Gather Information From MySQL
def gather_mysql_info():
    connect_to_mysql()
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
            
        # otherwise, remain as normal text
        return value
        
    # Grab the STATUS and VARIABLES from MySQL and put them both into dictionaries
    try:
        cursor = mysql_conn.cursor()
        cursor.execute("SHOW GLOBAL STATUS")
        status = dict([(key.lower(), convert(value)) 
                      for key, value in cursor.fetchall()])

        cursor.execute("SHOW GLOBAL VARIABLES")
        vars = dict([(key.lower(), convert(value))
                    for key, value in cursor.fetchall()])

        cursor.execute("SHOW ENGINE INNODB STATUS")
        fields = [f[0] for f in cursor.description]
        innodb_engine_status = dict(zip(fields, cursor.fetchone()))['Status']
        cursor.close()
    except MySQLdb.MySQLError, exc:
        print '[%d] %s' % exc.args
        print 'Unable to gather information from MySQL!\nPerhaps the MySQL ' \
            'user we are connecting with doese not have proper permissions?'
        sys.exit()
    return MySQLInfo(status, vars, innodb_engine_status)

class MySQLInfo(object):
    def __init__(self, status, vars, ibstatus):
        self.status = AttributeAdapter(status)
        self.vars = AttributeAdapter(vars)
        self.ibstatus = ibstatus

    @property
    def key_buffer_used(self):
        status = self.status
        key_buffer_size = self.vars.key_buffer_size
        try:
            return (status.key_blocks_used / 
                    status.key_blocks_unused * 
                    100 * key_buffer_size)
        except ZeroDivisionError:
            return 0

    @property
    def key_buffer_used_pct(self):
        status = self.status
        try:
            return (status.key_blocks_used / status.key_blocks_unused) * 100
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
    def buffer_pool_used(self):
        status = self.status
        return (status.innodb_buffer_pool_pages_total - 
                status.innodb_buffer_pool_pages_free) * \
                status.innodb_page_size
 
    @property
    def buffer_pool_used_pct(self):
        status = self.status
        return (1 - status.innodb_buffer_pool_pages_free  /
                    status.innodb_buffer_pool_pages_total) * 100

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
    def table_lock_wait_pct(self):
        status = self.status
        try:
            return (status.table_locks_waited /
                    status.table_locks_waited +
                    status.table_locks_immediate) * 100
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
