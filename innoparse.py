import re
import time

class Transaction(object):
    """Simple representation of an InnoDB Transaction"""
    # transaction id
    xid = None
    # transaction status (ACTIVE, not started, etc.)
    status = None 
    # how long the transaction has been active in seconds
    active_time = None 
    # mysqld pid (useless :P)
    pid = None 
    # OS level thread id (also likely useless for most cases :P)
    os_tid = None

    def __repr__(self):
        """Pretty-format for this transaciton.  List all the attributes set 
        on this instance.
        """
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join(['%s=%r' % (name, getattr(self, name)) 
                     for name in dir(self) if not name.startswith('_')])
        )

class InnodbStatus(object):
    def __init__(self, status_text):
        self.status_text = status_text

    @property
    def timestamp(self):
        """Timestamp this was generated at"""
        cre = re.compile(r'^(?P<timestamp>\d{6} (?:\d| )\d:\d{2}:\d{2}) '
                         r'INNODB MONITOR OUTPUT$', re.M|re.U)
        m = cre.search(self.status_text)
        if not m:
            raise ValueError("Failed to parse innodb status")

        timestamp = time.strptime(m.group('timestamp'), '%m%d%y %H:%M:%S') 
        return time.strftime('%Y-%m-%d %H:%M:%S', timestamp)

    @property
    def time_secs(self):
        """Time period this output was calculated over for per second averages"""
        cre = re.compile(r'^Per second averages calculated from the last '
                         r'(\d+) seconds$', re.M|re.U)
        m = cre.search(self.status_text)

        if not m:
            raise ValueError("Failed to parse innodb status text")

        return int(m.group(1))

    @property
    def history_list_length(self):
        """How large is the purge thread lagging behind?"""
        cre = re.compile('^History list length (\d+)', re.M|re.U)
        m = cre.search(self.status_text)
        if not m:
            raise ValueError()

        return int(m.group(1))

    @property
    def complete(self):
        """Whether all the output was included here
        Output may be truncated to 64K
        """
        cre = re.compile(r'^END OF INNODB MONITOR OUTPUT$', re.M|re.U)
        m = cre.search(self.status_text)

        return m is not None

    @property
    def transactions(self):
        """Iterate over transactions
        
        Yields Transaction instances for any transactions (active or not)
        """
        tx_cre = re.compile(r'(---TRANSACTION \d.*?)(?=\n---T|--------|$)',
                         re.S)

        def parse_transaction(txn):
            """Parse an individual transaction"""
            tx_dtl_cre = re.compile(r'(?:---)?TRANSACTION (?P<xid>\d+ \d+), '
                                    r'(?P<status>\D*?)'
                                    r'(?: (?P<active_time>\d+) sec)?, '
                                    r'(?:process no (?P<pid>\d+), )?'
                                    r'OS thread id (?P<os_tid>\d+)')

            m = tx_dtl_cre.match(txn)
            if not m:
                raise ValueError(txn)
            else:
                txn_obj = Transaction()
                for attr in ('xid', 'status', 'active_time', 'pid', 'os_tid'):
                    value = m.group(attr)
                    try:
                        if value is not None:
                            value = int(value)
                    except ValueError:
                        pass
                    setattr(txn_obj, attr, value)
                return txn_obj

        for txn in tx_cre.findall(self.status_text):
            yield parse_transaction(txn)

"""
if __name__ == '__main__':
    import warnings
    warnings.simplefilter('ignore')
    import MySQLdb

    class Client(object):
        def __init__(self, *args, **kwargs):
            self._connection = MySQLdb.connect(*args, **kwargs)

        def ibstatus(self):
            cursor = self._connection.cursor()
            cursor.execute('show engine innodb status')
            return cursor.fetchone()[-1]

    client = Client(read_default_group='client')
    status = InnodbStatus(client.ibstatus())

    import pprint
    for i, txn in enumerate(status.transactions):
        print "TRANSACTION(%d)" % i
        print txn
"""