"""Private server-side credential loading and the observed Windows native bootstrap."""
import ctypes
import importlib
import os
from pathlib import Path

_HANDLES = []


def load_credentials():
    path = Path(os.environ.get('AGAIN_ENV_FILE', Path(__file__).resolve().parents[1] / '.env'))
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            key, sep, value = line.strip().partition('=')
            if sep and key in ('MOSS_PROJECT_ID', 'MOSS_PROJECT_KEY') and not os.environ.get(key, '').strip():
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('\"', "'"):
                    value = value[1:-1]
                os.environ[key] = value
    return all(os.environ.get(k, '').strip() for k in ('MOSS_PROJECT_ID', 'MOSS_PROJECT_KEY'))


def load_sdk():
    # Process-local preload only: never changes PATH, installed DLLs, or security settings.
    if os.name == 'nt':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetSystemDirectoryW.argtypes = (ctypes.c_wchar_p, ctypes.c_uint)
        kernel.GetSystemDirectoryW.restype = ctypes.c_uint
        buffer = ctypes.create_unicode_buffer(32768)
        count = kernel.GetSystemDirectoryW(buffer, len(buffer))
        if not count or count >= len(buffer):
            raise RuntimeError('Windows native runtime path is unavailable')
        for name in ('MSVCP140.dll', 'VCRUNTIME140.dll', 'VCRUNTIME140_1.dll'):
            _HANDLES.append(ctypes.WinDLL(str(Path(buffer.value) / name)))
    return importlib.import_module('moss')
