import os
import time


class SessionStatus:
    def __init__(self, file_path, use_defaults=False, config=None):
        self.file_path = file_path
        self.is_active = True
        self.last_used = None
        if use_defaults and config and config.has_section('Settings'):
            self.cooldown_time = config.getint(
                'Settings', 'cooldown_time', fallback=180)
            self.batch_size = config.getint(
                'Settings', 'batch_size', fallback=10)
        else:
            self.cooldown_time = 180
            self.batch_size = 10
        self.error_count = 0
        self.total_checks = 0
        self._status = "空闲"

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def name(self):
        return os.path.basename(self.file_path)

    def can_use(self):
        if self._status != "空闲" and self._status != "可用":
            return False
        if self.last_used is None:
            return True
        elapsed = time.time() - self.last_used
        return elapsed >= self.cooldown_time

    def to_dict(self):
        return {
            'file_path': self.file_path,
            'is_active': self.is_active,
            'cooldown_time': self.cooldown_time,
            'batch_size': self.batch_size,
            'error_count': self.error_count,
            'total_checks': self.total_checks,
            'status': self._status
        }

    @classmethod
    def from_dict(cls, data):
        session = cls(data['file_path'])
        session.is_active = data.get('is_active', True)
        session.cooldown_time = data.get('cooldown_time', 180)
        session.batch_size = data.get('batch_size', 10)
        session.error_count = data.get('error_count', 0)
        session.total_checks = data.get('total_checks', 0)
        session._status = data.get('status', '空闲')
        return session

    def add_error(self, error_msg):
        self.error_count += 1
        self._status = "错误" if "未授权" not in error_msg else "未授权"
        return f"{self.name}: {error_msg} (错误次数: {self.error_count})"

    def reset_error(self):
        if self._status == "错误":
            self._status = "空闲"

    @property
    def is_error(self):
        return self._status == "错误" or self._status == "未授权"
