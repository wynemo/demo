import logging
import ssl

from handlers import TLSSysLogHandler

# class MyTCPLoggingThread(TCPLoggingThread):

#     def _open_socket(self):

#         if getattr(self, 'socket', None):
#             self._close_socket()
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.settimeout(self.timeout)
#         if self.ssl_kwargs.get('cert_reqs') == ssl.CERT_REQUIRED: 
#             _context = ssl.create_default_context(cadata=self.ssl_kwargs['ca_data'])
#             _context.check_hostname = False
#         else:
#             _context = ssl.create_default_context()
#             _context.check_hostname = False
#             _context.verify_mode = ssl.CERT_NONE
#         self.socket = _context.wrap_socket(sock)
#         self.socket.connect(self.address)



# class MyTLSSysLogHandler(TLSSysLogHandler):
#     def ensure_sender_thread_running(self):
#         self.purge_forked_caches()
#         if not self._sender_thread:
#             self._sender_thread = MyTCPLoggingThread(self.address, self.timeout, self.queue, self.thread_should_terminate, self.ssl_kwargs)
#             self._sender_thread.start()
#         return self._sender_thread

# with open('ca-cert.pem') as f:
    # s = f.read()
ssl_kwargs = {'cert_reqs': ssl.CERT_REQUIRED, 'ca_certs': 'ca-cert.pem'}
#ssl_kwargs = {}
h = TLSSysLogHandler(address=('10.0.10.141', 6514),
                     facility=TLSSysLogHandler.LOG_SYSLOG,
                     ssl_kwargs=ssl_kwargs)

formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
h.setFormatter(formatter)
logger = logging.getLogger('spam_application')
logger.setLevel(logging.INFO)
logger.addHandler(h)
logger.info('test')
