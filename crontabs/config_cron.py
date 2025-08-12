from config import Settings


class SettingsCron(Settings):
    PIDFILE_UPDATE_STAT: str = "update_stat.pid"
    PIDFILE_REMINDER: str = "reminder.pid"
    TEST_SERVER: str = "nl4"


settings = SettingsCron()
