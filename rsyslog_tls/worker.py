import socket
import ssl
import threading
import Queue as queue
import sys
import traceback

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None


#def eprint(*args, **kwargs):
#    print(*args, file=sys.stderr, **kwargs)
def eprint(args):
    print(args)


def captureException():
    if sentry_sdk is not None:
        try:
            sentry_sdk.capture_exception()
        except Exception:
            eprint('Unexpected error occurred while trying to report error with Raven.')
            traceback.print_exc()


class TCPLoggingThread(threading.Thread):
    """
    A daemon-thread used to send messages to syslog over a TCP/TLS socket in the background, so that
    the TCP socket doesn't block the application's main thread.
    """

    # Block for 500ms when waiting for a message in the queue. ``self.should_terminate`` will therefore
    # be checked at least this often, even in the queue is completely empty.
    queue_block_timeout = 0.5


    def __init__(self, address, timeout, queue, should_terminate, ssl_kwargs):
        super(TCPLoggingThread, self).__init__()
        self.daemon=True
        self.address = address
        self.timeout = timeout
        self.queue = queue
        self.should_terminate = should_terminate
        self.ssl_kwargs = ssl_kwargs
        try:
            self._open_socket()
        except OSError:
            self.socket = None


    def run(self):
        """
        Run the daemon-thread.

        Consumers messages from the queue and sends them over the TLS socket until both the
        queue is empty and the should_terminate event is set.
        """
        while True:
            # If should_terminate, close the socket and exist
            if self.queue.empty() and self.should_terminate.is_set():
                self._close_socket()
                return

            # Get a message and log it
            try:
                self._run_loop_inner()
            except Exception:
                eprint('Unexpected error occurred while trying to send message to syslog collector.')
                traceback.print_exc()
                captureException()


    def _run_loop_inner(self):
        # Block waiting for a log message to write
        try:
            message = self.queue.get(block=True, timeout=self.queue_block_timeout)
        except queue.Empty:
            return

        # Make sure we have a socket
        if not getattr(self, 'socket', None):
            try:
                self._open_socket()
            except Exception:
                eprint('Failed to open socket to syslog collector {} while trying to send message: {}'.format(self.address, message))
                traceback.print_exc()
                captureException()

        # Write the message to the socket
        if getattr(self, 'socket', None):
            try:
                self._send_message(message)
            except Exception:
                eprint('Failed to write to syslog ({}) socket while trying to send message: {}'.format(self.address, message))
                traceback.print_exc()
                captureException()

        # Register with the queue that the item has completed
        self.queue.task_done()


    def _open_socket(self):
        if getattr(self, 'socket', None):
            self._close_socket()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        self.socket = ssl.wrap_socket(sock, **self.ssl_kwargs)
        self.socket.connect(self.address)


    def _close_socket(self):
        if getattr(self, 'socket', None):
            self.socket.close()


    def _send_message(self, message):
        try:
            self.socket.sendall(message)
        except OSError:
            self._open_socket()
            self.socket.sendall(message)

