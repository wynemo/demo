from worker import TCPLoggingThread
import threading
import Queue as queue
import logging
import os



class TLSSysLogHandler(logging.Handler):
    """
    A handler class which sends formatted logging records to a syslog
    server over a TCP socket with TLS. Uses threading so that logging
    does not block the main thread.

    Based on the Python stdlib `SyslogHandler <https://github.com/python/cpython/blob/master/Lib/logging/handlers.py>`_
    """

    # from <linux/sys/syslog.h>:
    # ======================================================================
    # priorities/facilities are encoded into a single 32-bit quantity, where
    # the bottom 3 bits are the priority (0-7) and the top 28 bits are the
    # facility (0-big number). Both the priorities and the facilities map
    # roughly one-to-one to strings in the syslogd(8) source code.  This
    # mapping is included in this file.

    # Priorities (these are ordered)
    LOG_EMERG = 0  # system is unusable
    LOG_ALERT = 1  # action must be taken immediately
    LOG_CRIT = 2  # critical conditions
    LOG_ERR = 3  # error conditions
    LOG_WARNING = 4  # warning conditions
    LOG_NOTICE = 5  # normal but significant condition
    LOG_INFO = 6  # informational
    LOG_DEBUG = 7  # debug-level messages

    # Facility codes
    LOG_KERN = 0  # kernel messages
    LOG_USER = 1  # random user-level messages
    LOG_MAIL = 2  # mail system
    LOG_DAEMON = 3  # system daemons
    LOG_AUTH = 4  # security/authorization messages
    LOG_SYSLOG = 5  # messages generated internally by syslogd
    LOG_LPR = 6  # line printer subsystem
    LOG_NEWS = 7  # network news subsystem
    LOG_UUCP = 8  # UUCP subsystem
    LOG_CRON = 9  # clock daemon
    LOG_AUTHPRIV = 10  # security/authorization messages (private)
    LOG_FTP = 11  # FTP daemon

    # Other codes through 15 reserved for system use
    LOG_LOCAL0 = 16  # reserved for local use
    LOG_LOCAL1 = 17  # reserved for local use
    LOG_LOCAL2 = 18  # reserved for local use
    LOG_LOCAL3 = 19  # reserved for local use
    LOG_LOCAL4 = 20  # reserved for local use
    LOG_LOCAL5 = 21  # reserved for local use
    LOG_LOCAL6 = 22  # reserved for local use
    LOG_LOCAL7 = 23  # reserved for local use

    # Priority Names
    priority_names = {
        "alert": LOG_ALERT,
        "crit": LOG_CRIT,
        "critical": LOG_CRIT,
        "debug": LOG_DEBUG,
        "emerg": LOG_EMERG,
        "err": LOG_ERR,
        "error": LOG_ERR,  # DEPRECATED
        "info": LOG_INFO,
        "notice": LOG_NOTICE,
        "panic": LOG_EMERG,  # DEPRECATED
        "warn": LOG_WARNING,  # DEPRECATED
        "warning": LOG_WARNING,
    }

    # Facility Names
    facility_names = {
        "auth": LOG_AUTH,
        "authpriv": LOG_AUTHPRIV,
        "cron": LOG_CRON,
        "daemon": LOG_DAEMON,
        "ftp": LOG_FTP,
        "kern": LOG_KERN,
        "lpr": LOG_LPR,
        "mail": LOG_MAIL,
        "news": LOG_NEWS,
        "security": LOG_AUTH,  # DEPRECATED
        "syslog": LOG_SYSLOG,
        "user": LOG_USER,
        "uucp": LOG_UUCP,
        "local0": LOG_LOCAL0,
        "local1": LOG_LOCAL1,
        "local2": LOG_LOCAL2,
        "local3": LOG_LOCAL3,
        "local4": LOG_LOCAL4,
        "local5": LOG_LOCAL5,
        "local6": LOG_LOCAL6,
        "local7": LOG_LOCAL7,
    }

    # The map below appears to be trivially lowercasing the key. However,
    # there's more to it than meets the eye - in some locales, lowercasing
    # gives unexpected results. See SF #1524081: in the Turkish locale,
    # "INFO".lower() != "info"
    priority_map = {
        "DEBUG": "debug",
        "INFO": "info",
        "WARNING": "warning",
        "ERROR": "error",
        "CRITICAL": "critical"
    }

    # Prepended to all messages
    ident = ''

    # Appended to all messages
    msg_terminator = '\n'


    def __init__(self, address, timeout=3, facility=LOG_USER, ssl_kwargs={}):
        """
        Initialize a handler.
        """
        super(TLSSysLogHandler, self).__init__()

        self.address = address
        self.timeout = timeout
        self.facility = facility
        self.ssl_kwargs = ssl_kwargs

        self._queue = None
        self._thread_should_terminate = None
        self._sender_thread = None
        self._pid = None

        self.ensure_sender_thread_running()


    @property
    def queue(self):
        if not self._queue:
            self._queue = queue.Queue()
        return self._queue


    @property
    def thread_should_terminate(self):
        if not self._thread_should_terminate:
            self._thread_should_terminate = threading.Event()
        return self._thread_should_terminate


    def purge_forked_caches(self):
        current_pid = os.getpid()
        if not self._pid or self._pid != current_pid:
            self._queue = None
            self._thread_should_terminate = None
            self._sender_thread = None
            self._pid = current_pid


    def ensure_sender_thread_running(self):
        self.purge_forked_caches()
        if not self._sender_thread:
            self._sender_thread = TCPLoggingThread(self.address, self.timeout, self.queue, self.thread_should_terminate, self.ssl_kwargs)
            self._sender_thread.start()
        return self._sender_thread


    def encode_priority(self, facility, priority):
        """
        Encode the facility and priority. You can pass in strings or
        integers - if strings are passed, the facility_names and
        priority_names mapping dictionaries are used to convert them to
        integers.
        """
        if isinstance(facility, str):
            facility = self.facility_names[facility]
        if isinstance(priority, str):
            priority = self.priority_names[priority]
        return (facility << 3) | priority


    def close(self):
        """
        Blocks until all log lines have been sent to the syslog server, then closes the socket.
        """
        self.ensure_sender_thread_running()
        self.acquire()
        try:
            self.thread_should_terminate.set()  # Signal the thread to close it's socket connection and terminate
            self._sender_thread.join()  # Wait for the thread to terminate
            super(TLSSysLogHandler, self).close()
        finally:
            self.release()


    def map_priority(self, levelName):
        """
        Map a logging level name to a key in the priority_names map.
        This is useful in two scenarios: when custom levels are being
        used, and in the case where you can't do a straightforward
        mapping by lowercasing the logging level name because of locale-
        specific issues (see SF #1524081).
        """
        return self.priority_map.get(levelName, "warning")


    def emit(self, record):
        """
        Emit a record.

        The record is formatted, and then sent to the syslog server. If
        exception information is present, it is NOT sent to the server.
        """
        try:
            # Make sure the sender thread is running (it might need to restart if the process was forked)
            self.ensure_sender_thread_running()

            # Format the log record
            msg = self.format(record)
            if self.ident:
                msg = self.ident + msg

            # Match SysLogHandler behavior
            # https://gitlab.com/thelabnyc/python-tls-syslog/-/issues/2
            msg = msg.replace("\n", " ")

            if self.msg_terminator:
                msg += self.msg_terminator

            # We need to convert record level to lowercase, maybe this will change in the future.
            prio = '<%d>' % self.encode_priority(self.facility, self.map_priority(record.levelname))
            prio = prio.encode('utf-8')

            # Message is a string. Convert to bytes as required by RFC 5424
            msg = msg.encode('utf-8')
            msg = prio + msg

            # Append message into thread queue
            self.queue.put(msg)
        except Exception:
            self.handleError(record)

