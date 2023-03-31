import platform
import os

from cffi import FFI

ffibuilder = FFI()

lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), platform.machine())
print('-------', lib_path)

ffibuilder.set_source("_daslic",
   r""" // passed to the real C compiler,
        // contains implementation of things declared in cdef()
        #include "daslic_api.h"

    """,
    include_dirs = ['include'],
    library_dirs = ['daslic/' + platform.machine()],
    libraries=['dasapi'])   # or a list of libraries to link with
    # (more arguments like setup.py's Extension class:
    # include_dirs=[..], extra_objects=[..], and so on)

ffibuilder.cdef("""
    // declarations that are shared between Python and C
    int daslicSignOnline(char *code, char *email, char *post_back, char *proxy);

    int daslicSignOffline(char *code, char *email, char **result, int *rlen, char *post_back);

    int daslicSignManual(char *email, char **result, int *rlen, char *post_back);

    int daslicInitLog(char *path, int level);

    int daslicInitWorkDir(char *path, char *product_name, char *product_model);

    int daslicGetSn(char **result);

    int daslicVerifyLicense(char *lic_path, char **result, int *len, int strict);

    int daslicVerifyLicenseDef(char **result, int *rlen, int strict);

    void daslicFree(void *data);
""")

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)