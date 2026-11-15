import stat
import zipfile
import zlib
from io import BytesIO

import pyzipper

from filemanager.errors import FMError
from filemanager.security.names import logical_name


def extract(data: bytes, limits: dict, password: str | None = None) -> list[tuple[str, bytes]]:
    opener = pyzipper.AESZipFile if password else zipfile.ZipFile
    try:
        with opener(BytesIO(data)) as archive:
            if password:
                archive.setpassword(password.encode("utf-8"))
            entries = archive.infolist()
            if len(entries) > limits["max_zip_files"]:
                raise FMError("ZIP_TOO_MANY_FILES")
            names, files, declared_total = set(), [], 0
            for info in entries:
                # Check the original name too: zipfile truncates NUL in .filename.
                original = getattr(info, "orig_filename", info.filename)
                is_directory = info.is_dir()
                name = logical_name(original[:-1] if is_directory else original)
                key = name.casefold()
                if key in names:
                    raise FMError("ZIP_DUPLICATE_NAME")
                names.add(key)
                mode = info.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if kind not in {0, stat.S_IFREG, stat.S_IFDIR} or info.external_attr & 0x400:
                    raise FMError("ZIP_SPECIAL_FILE")
                if kind == stat.S_IFDIR and not is_directory:
                    raise FMError("ZIP_SPECIAL_FILE")
                if info.flag_bits & 1 and not password:
                    raise FMError("ZIP_PASSWORD_REQUIRED")
                # Bounded CPU/memory policy: only STORED/DEFLATE (and AES wrapping them).
                compression = getattr(info, "wz_aes_compression_method", None) or info.compress_type
                if compression not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                    raise FMError("ZIP_COMPRESSION_UNSUPPORTED")
                if info.file_size > limits["max_file_bytes"]:
                    raise FMError("FILE_TOO_LARGE")
                if info.file_size > max(1, info.compress_size) * limits["max_zip_ratio"]:
                    raise FMError("ZIP_RATIO_LIMIT")
                declared_total += info.file_size
                if declared_total > limits["max_total_zip_bytes"]:
                    raise FMError("ZIP_TOTAL_LIMIT")
                if not is_directory:
                    files.append((name, info))
            # A file and a directory cannot share a logical namespace.
            file_keys = {name.casefold() for name, _ in files}
            for name in names:
                components = name.split("/")
                if any("/".join(components[:i]) in file_keys for i in range(1, len(components))):
                    raise FMError("ZIP_NAME_CONFLICT")
            output, total = [], 0
            for name, info in files:
                chunks, actual = [], 0
                with archive.open(info) as source:
                    while chunk := source.read(64 * 1024):
                        actual += len(chunk)
                        total += len(chunk)
                        if actual > limits["max_file_bytes"]:
                            raise FMError("FILE_TOO_LARGE")
                        if total > limits["max_total_zip_bytes"]:
                            raise FMError("ZIP_TOTAL_LIMIT")
                        if actual > max(1, info.compress_size) * limits["max_zip_ratio"]:
                            raise FMError("ZIP_RATIO_LIMIT")
                        chunks.append(chunk)
                if actual != info.file_size:
                    raise FMError("ZIP_SIZE_MISMATCH")
                output.append((name, b"".join(chunks)))
            return output
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError, ValueError, zlib.error) as exc:
        raise FMError("INVALID_ZIP") from exc


def create(files: list[tuple[str, bytes]], max_bytes: int, password: str | None = None) -> bytes:
    if password and not 15 <= len(password) <= 128:
        raise FMError("PASSWORD_LENGTH_15_128")
    buffer = BytesIO()
    opener = pyzipper.AESZipFile if password else zipfile.ZipFile
    kwargs = {"compression": zipfile.ZIP_DEFLATED}
    if password:
        kwargs["encryption"] = pyzipper.WZ_AES
    with opener(buffer, mode="w", **kwargs) as archive:
        if password:
            archive.setpassword(password.encode("utf-8"))
            archive.setencryption(pyzipper.WZ_AES, nbits=256)
        names = set()
        for name, data in files:
            name = logical_name(name)
            if name.casefold() in names:
                raise FMError("ZIP_DUPLICATE_NAME")
            names.add(name.casefold())
            archive.writestr(name, data)
            if buffer.tell() > max_bytes:
                raise FMError("FILE_TOO_LARGE")
    result = buffer.getvalue()
    if len(result) > max_bytes:
        raise FMError("FILE_TOO_LARGE")
    return result

