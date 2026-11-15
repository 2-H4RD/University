import json
import math
import multiprocessing
import os
import time
from dataclasses import asdict
from uuid import uuid4

import defusedxml.ElementTree as safe_et
from defusedxml.common import DefusedXmlException

from filemanager.archives import zipops
from filemanager.errors import FMError


def validate_json(raw: bytes, limits: dict) -> bytes:
    if len(raw) > limits["max_document_bytes"]:
        raise FMError("DOCUMENT_TOO_LARGE")

    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise FMError("JSON_DUPLICATE_KEY")
            value[key] = item
        return value

    def constant(_value):
        raise FMError("JSON_NONFINITE")

    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
        if not isinstance(result, (dict, list)):
            raise FMError("JSON_OBJECT_OR_ARRAY_REQUIRED")
        stack, count = [(result, 1)], 0
        while stack:
            value, depth = stack.pop()
            count += 1
            if count > 10000 or depth > 32:
                raise FMError("DOCUMENT_COMPLEXITY_LIMIT")
            if isinstance(value, float) and not math.isfinite(value):
                raise FMError("JSON_NONFINITE")
            if isinstance(value, dict):
                stack.extend((item, depth + 1) for item in value.values())
                if any(len(key) > 1024 for key in value):
                    raise FMError("DOCUMENT_COMPLEXITY_LIMIT")
            elif isinstance(value, list):
                stack.extend((item, depth + 1) for item in value)
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8")
        if len(encoded) > limits["max_document_bytes"]:
            raise FMError("DOCUMENT_TOO_LARGE")
        return encoded
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise FMError("INVALID_JSON") from exc


def validate_xml(raw: bytes, limits: dict) -> bytes:
    if len(raw) > limits["max_document_bytes"]:
        raise FMError("DOCUMENT_TOO_LARGE")
    try:
        root = safe_et.fromstring(raw, forbid_dtd=True, forbid_entities=True, forbid_external=True)
        stack, count = [(root, 1)], 0
        while stack:
            node, depth = stack.pop()
            count += 1
            if count > 10000 or depth > 32 or len(node.attrib) > 32:
                raise FMError("DOCUMENT_COMPLEXITY_LIMIT")
            if node.tag == "{http://www.w3.org/2001/XInclude}include":
                raise FMError("XML_XINCLUDE_FORBIDDEN")
            stack.extend((child, depth + 1) for child in node)
        encoded = safe_et.tostring(root, encoding="utf-8", xml_declaration=True)
        if len(encoded) > limits["max_document_bytes"]:
            raise FMError("DOCUMENT_TOO_LARGE")
        return encoded
    except (safe_et.ParseError, DefusedXmlException, ValueError, RecursionError) as exc:
        raise FMError("INVALID_XML") from exc


def _child(pipe, ready, task, payload, limits):
    # Parent installs the OS memory/CPU job before any attacker-controlled parsing.
    if not ready.wait(5):
        return
    for name in list(os.environ):
        if name.startswith("FM_") or name == "PGPASSWORD":
            os.environ.pop(name, None)
    try:
        if os.name != "nt":
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (limits["worker_memory_bytes"],) * 2)
        if task == "json":
            result = validate_json(payload, limits)
        elif task == "xml":
            result = validate_xml(payload, limits)
        elif task == "zip_extract":
            result = zipops.extract(payload[0], limits, payload[1])
        elif task == "zip_create":
            result = zipops.create(payload[0], limits["max_file_bytes"], payload[1])
        elif task == "_timeout_test" and limits.get("testing"):
            time.sleep(limits["worker_timeout"] + 5)
            result = None
        elif task == "_memory_test" and limits.get("testing"):
            result = bytes(limits["worker_memory_bytes"] * 2)
        else:
            raise FMError("INVALID_TASK")
        pipe.send(("ok", result))
    except FMError as exc:
        pipe.send(("error", exc.code))
    except MemoryError:
        pipe.send(("error", "WORKER_MEMORY_LIMIT"))
    except Exception:  # noqa: BLE001 - isolate parser failures and return only a fixed public code
        pipe.send(("error", "INVALID_DOCUMENT"))
    finally:
        pipe.close()


def run(task, payload, settings):
    limits = asdict(settings)
    limits.pop("db_password")
    ctx = multiprocessing.get_context("spawn")
    receiver, sender = ctx.Pipe(duplex=False)
    ready = ctx.Event()
    process = ctx.Process(target=_child, args=(sender, ready, task, payload, limits), daemon=True)
    job = None
    try:
        process.start()
        sender.close()
        if os.name == "nt":
            import win32api
            import win32con
            import win32job
            job = win32job.CreateJobObject(None, "Local\\securefm-" + uuid4().hex)
            info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
            info["BasicLimitInformation"]["LimitFlags"] = (
                win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY)
            info["ProcessMemoryLimit"] = settings.worker_memory_bytes
            win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, info)
            handle = win32api.OpenProcess(win32con.PROCESS_SET_QUOTA | win32con.PROCESS_TERMINATE,
                                          False, process.pid)
            try:
                win32job.AssignProcessToJobObject(job, handle)
            finally:
                handle.Close()
        ready.set()
        if not receiver.poll(settings.worker_timeout):
            raise FMError("WORKER_TIMEOUT")
        # The child executes only our code and sends primitive validated values.
        # The pipe is private, never a socket or attacker-supplied pickle stream.
        try:
            status, result = receiver.recv()  # nosec B301
        except EOFError as exc:
            raise FMError("WORKER_RESOURCE_LIMIT") from exc
        if status != "ok":
            raise FMError(result)
        return result
    finally:
        if process.pid is not None:
            process.join(timeout=0.2)
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
            process.close()
        receiver.close()
        sender.close()
        if job is not None:
            job.Close()

