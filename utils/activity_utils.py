from datetime import datetime, timedelta
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth


class UserActivityStatus:
    def __init__(self, phone_number: str, user_id=None):
        self.phone_number = phone_number
        self.user_id = user_id
        self.last_seen = None
        self.activity_status = "未知"
        self.check_time = None
        self.username = None
        self.first_name = None
        self.last_name = None
        self.is_premium = False
        self.is_bot = False
        self.is_verified = False
        self.photo_url = None

    def update_from_user(self, user):
        if user:
            self.user_id = user.id
            self.username = user.username if hasattr(
                user, 'username') and user.username else ""
            self.first_name = user.first_name if hasattr(
                user, 'first_name') and user.first_name else ""
            self.last_name = user.last_name if hasattr(
                user, 'last_name') and user.last_name else ""
            self.is_premium = getattr(user, 'premium', False)
            self.is_bot = getattr(user, 'bot', False)
            self.is_verified = getattr(user, 'verified', False)
            self.check_time = datetime.now()
            status = getattr(user, 'status', None)
            if status:
                if isinstance(status, UserStatusOnline):
                    self.activity_status = "在线"
                    self.last_seen = datetime.now()
                elif isinstance(status, UserStatusRecently):
                    self.activity_status = "最近在线"
                    self.last_seen = datetime.now() - timedelta(days=1)
                elif isinstance(status, UserStatusLastWeek):
                    self.activity_status = "一周内在线"
                    self.last_seen = datetime.now() - timedelta(days=7)
                elif isinstance(status, UserStatusLastMonth):
                    self.activity_status = "一月内在线"
                    self.last_seen = datetime.now() - timedelta(days=30)
                elif isinstance(status, UserStatusOffline) and status.was_online:
                    self.activity_status = "离线"
                    try:
                        self.last_seen = datetime.fromtimestamp(
                            status.was_online.timestamp())
                    except:
                        self.last_seen = None
                else:
                    self.activity_status = "很久未在线"
            else:
                self.activity_status = "未知"

    def to_dict(self):
        return {
            'phone_number': self.phone_number,
            'user_id': self.user_id,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'activity_status': self.activity_status,
            'check_time': self.check_time.isoformat() if self.check_time else None,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_premium': self.is_premium,
            'is_bot': self.is_bot,
            'is_verified': self.is_verified
        }

    @classmethod
    def from_dict(cls, data):
        status = cls(data['phone_number'], data.get('user_id'))
        status.activity_status = data.get('activity_status', "未知")
        if data.get('last_seen'):
            try:
                status.last_seen = datetime.fromisoformat(data['last_seen'])
            except:
                status.last_seen = None
        if data.get('check_time'):
            try:
                status.check_time = datetime.fromisoformat(data['check_time'])
            except:
                status.check_time = None
        status.username = data.get('username')
        status.first_name = data.get('first_name')
        status.last_name = data.get('last_name')
        status.is_premium = data.get('is_premium', False)
        status.is_bot = data.get('is_bot', False)
        status.is_verified = data.get('is_verified', False)
        return status

    @property
    def display_name(self):
        return self.phone_number

    @property
    def is_active(self):
        return self.activity_status in ["在线", "最近在线", "一周内在线"]

    @property
    def status_color(self):
        status_colors = {
            "在线": "#4CAF50",
            "最近在线": "#8BC34A",
            "一周内在线": "#FFC107",
            "一月内在线": "#FF9800",
            "离线": "#9E9E9E",
            "很久未在线": "#F44336",
            "未知": "#607D8B"
        }
        return status_colors.get(self.activity_status, "#607D8B")
