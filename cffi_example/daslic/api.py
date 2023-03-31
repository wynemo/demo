import sys

import cffi

from _daslic import lib

ffi = cffi.FFI()

# def daslicInitWorkDir(path, product_name=None, product_model=None):
#     return lib.daslicInitWorkDir(path, product_name, product_model)

# def daslicInitLog(path, level):
#     return lib.daslicInitLog(path, level)

# if __name__ == '__main__':
#     daslicInitWorkDir('/tmp')
#     daslicInitLog('/tmp', 4)

#//int daslicInitLog(char *path, int level);

#//int daslicInitWorkDir(char *path, char *product_name, char *product_model);

#//int daslicGetSn(char **result);
PY3 = sys.version_info[0] == 3
if PY3:
    text_type = str
    binary_type = bytes
else:
    text_type = unicode
    binary_type = str


def to_bytes(s):
    if isinstance(s, binary_type):
        return s
    return text_type(s).encode("utf-8")


def to_unicode(s):
    if isinstance(s, text_type):
        return s
    return binary_type(s).decode("utf-8")

def daslicInitWorkDir(path, product_name='', product_model=''):
    product_name = to_bytes(product_name) if product_name else ffi.NULL
    product_model = to_bytes(product_model) if product_model else ffi.NULL
    return lib.daslicInitWorkDir(path.encode(), product_name, product_model)

def daslicInitLog(path, level):
    return lib.daslicInitLog(path.encode(), level)

def daslicGetSn():
    result = ffi.new("char **", ffi.NULL)
    sn_result = lib.daslicGetSn(result)
    print('result is', sn_result)
    rv = ffi.string(result[0])
    lib.daslicFree(result)
    return rv


def daslicSignManual(email, post_back='', result_len=0):
    email = to_bytes(email) if email else ffi.NULL
    post_back = to_bytes(post_back) if post_back else ffi.NULL
    result = ffi.new("char **", ffi.NULL)
    rlen = ffi.new("int *", result_len)
    sign_result = lib.daslicSignManual(email, result, rlen, post_back)
    print('result is', sign_result)
    rv = ffi.string(result[0])
    lib.daslicFree(result[0])
    return rv

def daslicVerifyLicense(lic_path, strict=0, result_len=0):
    lic_path = to_bytes(lic_path) if lic_path else ffi.NULL
    result = ffi.new("char **", ffi.NULL)
    rlen = ffi.new("int *", result_len)
    verify_result = lib.daslicVerifyLicense(lic_path, result, rlen, strict)
    print('result is', verify_result)
    rv = ffi.string(result[0])
    lib.daslicFree(result[0])
    return rv

if __name__ == '__main__':
    rv = daslicInitWorkDir('/tmp')
    print('rv is', rv)
    rv = daslicInitLog('/tmp', 4)
    # print('rv is', rv)
    # rv = daslicGetSn()
    print('rv is', rv)
    with open('test.req', 'w+b') as f:
        rv = daslicSignManual('tommy.zhang@dbappsecurity.com.cn')
        # print('daslicSignManual rv is', rv)
        f.write(to_bytes(rv))
