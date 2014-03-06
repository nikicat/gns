import sys
import socket
import platform
import logging
import functools
import time

try:
    import cffi
except ImportError:
    cffi = None


##### Public classes #####
class LogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        logging.LogRecord.__init__(self, *args, **kwargs)
        self.tid = _gettid()
        self.fqdn = _cached_getfqdn(int(time.time() / 60)) # Cached value FQDN, updated every minute
        self.node = platform.uname()[1] # Nodename from uname


##### Private methods #####
def _make_gettid():
    fallback = ( lambda: None )
    if sys.platform.startswith("linux") and cffi is not None:
        try:
            ffi = cffi.FFI()
            ffi.cdef("int linux_gettid(void);")
            lib = ffi.verify("""
                    #include <unistd.h>
                    #include <sys/syscall.h>
                    int linux_gettid(void) {
                        return syscall(SYS_gettid);
                    }
                """)
            # Lambda is needed because without it segfault happens
            gettid = ( lambda: lib.linux_gettid() ) # pylint: disable=E1101,W0108
        except Exception:
            logging.getLogger().exception("Cannot construct CFFI interface to gettid(), logging of TID will be unavailable")
            gettid = fallback
    else:
        gettid = fallback
    return gettid
_gettid = _make_gettid()

@functools.lru_cache(1)
def _cached_getfqdn(every):
    return socket.getfqdn()
