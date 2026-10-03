"""Keep the adventure webhook in the current user's Windows Credential Manager."""

import ctypes
from ctypes import wintypes
import os


TARGET = "Truthammer/Discord/958554312185884723/1497086827365142530"
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ERROR_NOT_FOUND = 1168


class _Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def _credential_api():
    api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    credential_pointer = ctypes.POINTER(_Credential)
    api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                             ctypes.POINTER(credential_pointer)]
    api.CredReadW.restype = wintypes.BOOL
    api.CredWriteW.argtypes = [credential_pointer, wintypes.DWORD]
    api.CredWriteW.restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    api.CredFree.restype = None
    return api


def read_webhook():
    if os.name != "nt":
        return None
    api = _credential_api()
    credential = ctypes.POINTER(_Credential)()
    if not api.CredReadW(TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(credential)):
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return None
        raise OSError(error, "Windows Credential Manager could not read the adventure webhook.")

    try:
        value = credential.contents
        return ctypes.string_at(value.CredentialBlob, value.CredentialBlobSize).decode("utf-16-le")
    finally:
        api.CredFree(credential)


def save_webhook(value):
    if os.name != "nt":
        raise OSError("Saving the adventure webhook requires Windows Credential Manager.")
    encoded = value.encode("utf-16-le")
    if not encoded or len(encoded) > 2560:
        raise ValueError("The adventure webhook does not fit in Windows Credential Manager.")

    # Persist across logons for this user on this computer, outside every checkout.
    blob = ctypes.create_string_buffer(encoded)
    credential = _Credential(
        Type=CRED_TYPE_GENERIC,
        TargetName=TARGET,
        Comment="Truthammer adventure-log webhook",
        CredentialBlobSize=len(encoded),
        CredentialBlob=ctypes.cast(blob, ctypes.POINTER(wintypes.BYTE)),
        Persist=CRED_PERSIST_LOCAL_MACHINE,
        UserName="Truthammer Adventure Log",
    )
    api = _credential_api()
    if not api.CredWriteW(ctypes.byref(credential), 0):
        raise OSError(ctypes.get_last_error(), "Windows Credential Manager could not save the adventure webhook.")
