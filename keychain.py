"""Local macOS credential storage; secrets never appear in command arguments."""
import ctypes

SERVICE = 'com.widechaos.turnproof.nebius'
ACCOUNT = 'TurnProof-local-v3'


def store(key):
    api = ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
    add = api.SecKeychainAddGenericPassword
    add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p,
                   ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32,
                   ctypes.c_void_p, ctypes.c_void_p]
    add.restype = ctypes.c_int32
    service, account, secret = SERVICE.encode(), ACCOUNT.encode(), key.encode()
    result = add(None, len(service), service, len(account), account,
                 len(secret), secret, None)
    if result:
        raise RuntimeError('Keychain storage failed, OS status ' + str(result))


def load():
    api = ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
    find = api.SecKeychainFindGenericPassword
    find.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p,
                    ctypes.c_uint32, ctypes.c_char_p,
                    ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_void_p),
                    ctypes.c_void_p]
    find.restype = ctypes.c_int32
    service, account = SERVICE.encode(), ACCOUNT.encode()
    length, data = ctypes.c_uint32(), ctypes.c_void_p()
    result = find(None, len(service), service, len(account), account,
                  ctypes.byref(length), ctypes.byref(data), None)
    if result:
        raise RuntimeError('TurnProof credential unavailable, OS status ' + str(result))
    try:
        return ctypes.string_at(data, length.value).decode()
    finally:
        api.SecKeychainItemFreeContent(None, data)
