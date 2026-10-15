"""Give legacy GCC an ASCII SDK prefix without copying or changing its files."""
import atexit
import ctypes
import os
from pathlib import Path
import subprocess


def device_target(drive):
    buffer = ctypes.create_unicode_buffer(32768)
    if not ctypes.windll.kernel32.QueryDosDeviceW(drive, buffer, len(buffer)):
        return None
    return buffer.value


class SDKPath:
    def __init__(self, source):
        self.original = os.path.abspath(source)
        self.path = Path(self.original)
        self.drive = None
        if self.original.isascii() and len(self.original) <= 80:
            return
        drives = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in reversed('DEFGHIJKLMNOPQRSTUVWXYZ'):
            drive = letter + ':'
            if drives & (1 << (ord(letter) - ord('A'))) or device_target(drive):
                continue
            result = subprocess.run(['subst.exe', drive, self.original], capture_output=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
            if result.returncode:
                continue
            self.drive = drive
            self.path = Path(drive + '/')
            atexit.register(self.close)
            return
        raise RuntimeError('旧版编译器需要一个空闲盘符来访问中文安装路径，请释放一个盘符后重试。')

    def close(self):
        if not self.drive:
            return
        target = device_target(self.drive)
        expected = '\\??\\' + self.original
        # Never remove a drive whose target has changed since this service created it.
        if target and os.path.normcase(target.rstrip('\\')) == os.path.normcase(expected.rstrip('\\')):
            try:
                subprocess.run(['subst.exe', self.drive, '/D'], capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
        self.drive = None
