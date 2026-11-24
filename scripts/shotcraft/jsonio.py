"""Small JSON helpers.

API:
    read_json(path, default=None)      parsed JSON, or `default` when the file is missing or empty
    write_json(path, data)             atomic write (temp file + rename), makes parent folders
    append_jsonl(path, record)         append one JSON line
    read_jsonl(path) -> list           every JSON line (bad lines skipped)
    now_iso() -> str                   local time with UTC offset, seconds precision
    today() -> str                     YYYY-MM-DD
"""
import datetime
import json
import os
import tempfile

from . import ShotcraftError


def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        return default
    if not text.strip():
        return default
    try:
        return json.loads(text)
    except ValueError as exc:
        raise ShotcraftError("%s is not valid JSON: %s" % (path, exc))


def write_json(path, data):
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_jsonl(path, record):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path):
    out = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return out


def now_iso():
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


def today():
    return datetime.date.today().isoformat()
