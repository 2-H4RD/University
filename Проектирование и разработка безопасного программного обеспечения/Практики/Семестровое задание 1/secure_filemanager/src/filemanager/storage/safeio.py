import os
import stat
from contextlib import ExitStack, contextmanager
from pathlib import Path

from filemanager.errors import FMError


def _win_create(path, access, sharing, disposition, flags):
    import pywintypes
    import win32file
    try:
        # Explicit extended-length prefix also supports the long Cyrillic project path.
        native_path = "\\\\?\\" + str(path.absolute())
        return win32file.CreateFile(native_path, access, sharing, None, disposition, flags, None)
    except pywintypes.error as exc:
        if exc.winerror in {2, 3}:
            raise FileNotFoundError(str(path)) from exc
        if exc.winerror in {80, 183}:
            raise FileExistsError(str(path)) from exc
        raise OSError("WINDOWS_FILE_ACCESS_FAILED") from exc


def reject_link(path: Path):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise FMError("LINK_FORBIDDEN")


@contextmanager
def pin_directory(path: Path):
    """Hold every ancestor without FILE_SHARE_DELETE, then validate each handle."""
    path = path.absolute()
    if os.name != "nt":
        for item in (path, *path.parents):
            reject_link(item)
        yield
        return
    import win32con
    import win32file
    with ExitStack() as stack:
        for item in reversed((path, *path.parents)):
            handle = _win_create(
                item, 0x0081,  # FILE_LIST_DIRECTORY | FILE_READ_ATTRIBUTES; attributes alone do not pin
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE, win32con.OPEN_EXISTING,
                win32con.FILE_FLAG_BACKUP_SEMANTICS | win32file.FILE_FLAG_OPEN_REPARSE_POINT,
            )
            stack.callback(handle.Close)
            attrs = win32file.GetFileInformationByHandle(handle)[0]
            if attrs & win32con.FILE_ATTRIBUTE_REPARSE_POINT:
                raise FMError("LINK_FORBIDDEN")
            if not attrs & win32con.FILE_ATTRIBUTE_DIRECTORY:
                raise FMError("DIRECTORY_REQUIRED")
        yield


@contextmanager
def open_regular(path: Path, create: bool = False):
    with pin_directory(path.parent):
        if os.name == "nt":
            import msvcrt

            import win32con
            import win32file
            handle = _win_create(
                path, win32con.GENERIC_READ | (win32con.GENERIC_WRITE if create else 0),
                win32con.FILE_SHARE_READ,
                win32con.CREATE_NEW if create else win32con.OPEN_EXISTING,
                win32file.FILE_FLAG_OPEN_REPARSE_POINT,
            )
            try:
                info = win32file.GetFileInformationByHandle(handle)
                if info[0] & (win32con.FILE_ATTRIBUTE_REPARSE_POINT | win32con.FILE_ATTRIBUTE_DIRECTORY):
                    raise FMError("LINK_FORBIDDEN")
                if info[7] != 1:
                    raise FMError("HARDLINK_FORBIDDEN")
                final = win32file.GetFinalPathNameByHandle(handle, 0)
                expected = os.path.normcase(os.path.abspath(path))
                if os.path.normcase(final.removeprefix("\\\\?\\")) != expected:
                    raise FMError("PATH_MISMATCH")
                fd = msvcrt.open_osfhandle(handle.Detach(),
                                          os.O_BINARY | (os.O_RDWR if create else os.O_RDONLY))
            finally:
                handle.Close()
        else:
            flags = os.O_RDWR | os.O_CREAT | os.O_EXCL if create else os.O_RDONLY
            fd = os.open(path, flags | os.O_NOFOLLOW, 0o600)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                os.close(fd)
                raise FMError("LINK_FORBIDDEN")
        with os.fdopen(fd, "w+b" if create else "rb") as stream:
            yield stream

