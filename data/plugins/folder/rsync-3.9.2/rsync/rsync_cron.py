import os
import sys
os.chdir("/www/server/panel")
sys.path.insert(0, "class/")


def main_crontab():
    """执行定时任务"""
    import PluginLoader
    PluginLoader.plugin_run("rsync", "cron_test_bt_sync_running", None)


if __name__ == '__main__':
    main_crontab()
