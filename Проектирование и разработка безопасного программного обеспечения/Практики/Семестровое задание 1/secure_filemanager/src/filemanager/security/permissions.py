import os
from pathlib import Path


def protect(path: Path):
    """Only the current Windows SID and SYSTEM; inheritable for directories."""
    if os.name != "nt":
        path.chmod(0o700 if path.is_dir() else 0o600)
        return
    import win32api
    import win32con
    import win32security
    volume_flags = win32api.GetVolumeInformation(path.anchor)[3]
    if not volume_flags & 0x00000008:  # FILE_PERSISTENT_ACLS; exFAT cannot enforce DACLs
        return False
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    try:
        sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
    finally:
        token.Close()
    system = win32security.CreateWellKnownSid(win32security.WinLocalSystemSid, None)
    acl = win32security.ACL()
    flags = win32con.OBJECT_INHERIT_ACE | win32con.CONTAINER_INHERIT_ACE if path.is_dir() else 0
    for principal in (sid, system):
        acl.AddAccessAllowedAceEx(win32security.ACL_REVISION_DS, flags,
                                 win32con.GENERIC_ALL, principal)
    win32security.SetNamedSecurityInfo(
        str(path), win32security.SE_FILE_OBJECT,
        win32security.DACL_SECURITY_INFORMATION | win32security.PROTECTED_DACL_SECURITY_INFORMATION,
        None, None, acl, None,
    )
    return True

