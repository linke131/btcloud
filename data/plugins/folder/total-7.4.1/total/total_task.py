# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表定时任务
# +-------------------------------------------------------------------
# TODO: 日报生成的数据查询范围
from __future__ import absolute_import, print_function, division
import os
import sys
import time

import json

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(0, "/www/server/panel")

import public
from crontab import crontab
import total_tools as tool

task_config = "/www/server/panel/plugin/total/task_config.json"


def get_config():
    try:
        return json.loads(public.readFile(task_config))
    except:
        pass
    return {
        "task_id": -1,
        "task_list": ["record_log_size", "generate_report", "migrate_hot_logs", "update_spiders"],
        "default_execute_hour": 3,
        "default_execute_minute": 10,
    }


def create_background_task():
    config = get_config()
    name = tool.getMsg("SCHEDULED_TASK_NAME")
    res = public.M("crontab").field("id, name").where("name=?", (name,)).find()
    if res:
        return True

    if "task_id" in config.keys() and config["task_id"] > 0:
        res = public.M("crontab").field("id, name").where("id=?", (config["task_id"],)).find()
        if res and res["id"] == config["task_id"]:
            # print("计划任务已存在。")
            print(tool.getMsg("SCHEDULED_TASK_EXISTS"))
            return True

    # name = "[勿删]宝塔网站监控报表插件定时任务"
    name = tool.getMsg("SCHEDULED_TASK_NAME")
    c = crontab()
    get = public.dict_obj()
    get.type = "day"
    get.hour = config["default_execute_hour"]
    get.minute = config["default_execute_minute"]
    get.sBody = "nice -n 10 " + public.get_python_bin() + " /www/server/panel/plugin/total/total_task.py execute"
    get.sType = "toShell"
    get.name = name
    get.sName = ""
    get.urladdress = ""
    get.backupTo = ""
    res = c.AddCrontab(get)
    if "id" in res.keys():
        config["task_id"] = res["id"]
        public.writeFile(task_config, json.dumps(config))
        return True

    return False


def remove_background_task():
    config = get_config()
    if "task_id" in config.keys() and config["task_id"] > 0:
        res = public.M("crontab").field("id, name").where("id=?", (config["task_id"],)).find()
        if res and res["id"] == config["task_id"]:
            c = crontab()
            get = public.dict_obj()
            get.id = res["id"]
            del_res = c.DelCrontab(get)
            if del_res and "status" in del_res.keys():
                if del_res["status"]:
                    print(del_res["msg"])
                    return True
    return False


def record_log_size():
    pass


# def compress_logs(log_dir, compress_date):
#     """压缩站点日志
#
#     Args:
#         log_dir (str): 日志目录
#         compress_date: 压缩日期
#     """
#     # print("compress date: {}".format(time.strftime("%Y-%m-%d", compress_date)))
#     # 压缩文件
#     print(compress_date)
#     print(log_dir)
#     for f in os.listdir(log_dir):
#         fname, suffix = os.path.splitext(f)
#         if suffix != ".txt": continue
#         print(f)
#         log_date = None
#         try:
#             log_date = time.strptime(fname[0:8], "%Y%m%d")
#         except:
#             log_date = None
#         if log_date:
#             try:
#                 # print("log_date: {}".format(fname))
#                 if log_date < compress_date:
#                     # 压缩历史日志
#                     compress_type, c_suffix = tool.get_default_compress_type()
#                     # compress_type, c_suffix = "tar.gz", "tar.gz"
#                     compress_file = os.path.splitext(f)[0] + "." + c_suffix
#                     if os.path.exists(compress_file):
#                         # print("{} exists.".format(compress_file))
#                         continue
#                     compress_cmd = "cd {} && tar -czf {} {}".format(log_dir, compress_file, f)
#                     print("压缩文件: {} --> {}".format(f, compress_file))
#                     exec_res = public.ExecShell(compress_cmd)
#                     db_full_path = os.path.join(log_dir, f)
#                     if os.path.exists(db_full_path):
#                         os.remove(db_full_path)
#             except Exception as e:
#                 print("exception: {}".format(e))
#                 continue

def compress_logs(log_dir, compress_date):
    """压缩站点日志

    Args:
        log_dir (str): 日志目录
        compress_date: 压缩日期
    """
    # 压缩文件
    for f in os.listdir(log_dir):
        fname, suffix = os.path.splitext(f)
        if suffix != ".txt": continue
        log_date = None
        try:
            log_date = time.strptime(fname[0:8], "%Y%m%d")
        except:
            log_date = None
        if log_date:
            try:
                if log_date < compress_date:
                    # 压缩历史日志
                    compress_type, c_suffix = tool.get_default_compress_type()
                    # compress_type, c_suffix = "tar.gz", "tar.gz"
                    compress_file = os.path.splitext(f)[0] + "." + c_suffix
                    if os.path.exists(compress_file):
                        # print("{} exists.".format(compress_file))
                        continue
                    compress_cmd = "cd {} && tar -czf {} {}".format(log_dir, compress_file, f)
                    print("压缩文件: {} --> {}".format(f, compress_file))
                    exec_res = public.ExecShell(compress_cmd)
                    db_full_path = os.path.join(log_dir, f)
                    if os.path.exists(db_full_path):
                        os.remove(db_full_path)
            except Exception as e:
                print("exception: {}".format(e))
                continue

def compress_cursor_logs(log_dir, compress_date):
    """压缩站点游标日志

    Args:
        log_dir (str): 日志目录
        compress_date: 压缩日期
    """
    # 压缩文件
    for f in os.listdir(log_dir):
        fname, suffix = os.path.splitext(f)
        if suffix != ".db": continue
        log_date = None
        try:
            log_date = time.strptime(fname[0:8], "%Y%m%d")
        except:
            log_date = None
        if log_date:
            try:
                if log_date < compress_date:
                    # 压缩历史日志
                    compress_type, c_suffix = tool.get_default_compress_type()
                    # compress_type, c_suffix = "tar.gz", "tar.gz"
                    compress_file = os.path.splitext(f)[0] + "." + c_suffix
                    if os.path.exists(compress_file):
                        # print("{} exists.".format(compress_file))
                        continue
                    compress_cmd = "cd {} && tar -czf {} {}".format(log_dir, compress_file, f)
                    print("压缩文件: {} --> {}".format(f, compress_file))
                    exec_res = public.ExecShell(compress_cmd)
                    db_full_path = os.path.join(log_dir, f)
                    if os.path.exists(db_full_path):
                        os.remove(db_full_path)
            except Exception as e:
                print("exception: {}".format(e))
                continue


def clear_logs(log_dir, save_date):
    """清理日志

    Args:
        log_dir (str): 日志目录
        save_date (time): 保留日期
    """
    start_time = save_date
    # possible_types = tool.get_compress_types()
    # print("log dir: {}".format(log_dir))
    # print("clear start date: {}".format(time.strftime("%Y-%m-%d", start_time)))
    to_be_delete = []
    scan_days = 180
    for i in range(0, scan_days):
        date_str = time.strftime("%Y%m%d", start_time)
        to_be_delete.append(date_str)
        start_time = time.localtime(time.mktime((start_time.tm_year, start_time.tm_mon, start_time.tm_mday - 1, 0, 0, 0, 0, 0, 0)))
    # 先删除文件
    for f in os.listdir(log_dir):
        fname, _suffix = os.path.splitext(f)
        if fname.find(".") != -1:
            _ = _suffix
            fname, _suffix = os.path.splitext(fname)
            _suffix = _ + _suffix
        if fname in to_be_delete:
            # print("Reading to delete file: {}".format(f))
            old_file = os.path.join(log_dir, f)
            if os.path.exists(old_file):
                os.remove(old_file)


def clear_cursor_logs(cursor_log_dir, save_date):
    """清理日志

    Args:
        log_dir (str): 日志目录
        save_date (time): 保留日期
    """
    start_time = save_date
    to_be_delete = []
    scan_days = 180
    for i in range(0, scan_days):
        date_str = time.strftime("%Y%m%d", start_time)
        to_be_delete.append(date_str)
        start_time = time.localtime(
            time.mktime((start_time.tm_year, start_time.tm_mon, start_time.tm_mday - 1, 0, 0, 0, 0, 0, 0)))
    # 先删除文件
    for f in os.listdir(cursor_log_dir):
        fname, _suffix = os.path.splitext(f)
        if fname.find(".") != -1:
            _ = _suffix
            fname, _suffix = os.path.splitext(fname)
            _suffix = _ + _suffix
        if fname in to_be_delete:
            # print("Reading to delete file: {}".format(f))
            old_file = os.path.join(cursor_log_dir, f)
            if os.path.exists(old_file):
                os.remove(old_file)


def clear_total(site_name):
    tag_file = "/www/server/total/logs/" + site_name + "/migrating"
    if os.path.exists(tag_file):
        return True
    try:
        conn = None
        cur = None

        public.writeFile(tag_file, "x")
        db_file = "/www/server/total/logs/" + site_name + "/total.db"
        if not os.path.exists(db_file):
            return True
        save_day = 180
        now = time.localtime()
        border_day = time.localtime(time.mktime((now.tm_year, now.tm_mon, now.tm_mday - save_day, 0, 0, 0, 0, 0, 0)))
        time_key = int(time.strftime("%Y%m%d", border_day))

        import sqlite3
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()

        conn.execute("BEGIN TRANSACTION;")

        # print("delete request_stat res:", cur.execute("delete from request_stat where time/100 < ?", (time_key,)))
        cur.execute("delete from client_stat where time/100 < ?", (time_key,))
        cur.execute("delete from spider_stat where time/100 < ?", (time_key,))

        day_columns = ""
        for i in range(1, 32):
            if day_columns:
                day_columns += "+"
            day_columns += "day" + str(i)

        sql_template = "delete from {} where (" + day_columns + ")={}"
        delete_ip_stat_sql = sql_template.format("ip_stat", 0)
        # print("delete ip stat sql: ", delete_ip_stat_sql)
        cur.execute(delete_ip_stat_sql)
        delete_uri_stat_sql = sql_template.format("uri_stat", 0)
        cur.execute(delete_uri_stat_sql)
        delete_referer_stat_sql = sql_template.format("referer2_stat", 0)
        cur.execute(delete_referer_stat_sql)
        try:
            conn.commit()
            cur.execute("VACUUM")
        except:
            pass

    except Exception as e:
        print("Clear site:{} total data err: {}".format(site_name, str(e)))
    finally:
        if os.path.exists(tag_file):
            os.remove(tag_file)
        cur and cur.close()
        conn and conn.close()
    return True


def clear_space(site_name, save_day=0, compress_day=0):
    """清理已过期的日志, 压缩很少查询的日志，释放空间

    Args:
        site_name (str): 网站名
    """
    config = tool.get_site_settings(site_name)
    if not save_day:
        save_day = config["save_day"]

    if not compress_day:
        compress_day = 30
        if "compress_day" in config:
            compress_day = config["compress_day"]

    data_dir = config["data_dir"]
    log_dir = os.path.join(data_dir, site_name)
    cursor_log_dir = os.path.join(data_dir, site_name, 'cursor_log')
    time_now = time.localtime()
    save_date = time.localtime(time.mktime((time_now.tm_year, time_now.tm_mon, time_now.tm_mday - save_day - 1, 0, 0, 0, 0, 0, 0)))
    # 清理网站日志
    clear_logs(log_dir, save_date)
    if os.path.exists(cursor_log_dir):
        # 清理网站游标日志
        clear_cursor_logs(cursor_log_dir, save_date)

    # 压缩网站游标日志
    if not compress_day:
        compress_day = 30
    if compress_day > save_day:
        compress_day = save_day
    if compress_day != -1:
        compress_date = time.localtime(time.mktime((time_now.tm_year, time_now.tm_mon, time_now.tm_mday - compress_day - 1, 0, 0, 0, 0, 0, 0)))
        compress_cursor_logs(cursor_log_dir, compress_date)

    else:
        print("日志不压缩。")

    # 压缩网站日志
    compress_date = time.localtime(time.mktime((time_now.tm_year, time_now.tm_mon, time_now.tm_mday - 7, 0, 0, 0, 0, 0, 0)))
    compress_logs(log_dir, compress_date)

    # 移动昨日的db文件到历史目录 可重复执行
    d = tool.get_data_dir()
    h = tool.get_history_data_dir()
    if d != h:
        import shutil
        yesterday = time.localtime(time.mktime((time_now.tm_year, time_now.tm_mon, time_now.tm_mday - 1, 0, 0, 0, 0, 0, 0)))
        _date_str = time.strftime("%Y%m%d", yesterday)
        db_name = _date_str + ".txt"
        yesterday_db = os.path.join(d, db_name)
        history_yesterday_db = os.path.join(h, db_name)
        shutil.move(yesterday_db, history_yesterday_db)

    clear_total(site_name)


def execute():
    try:
        import time
        now = time.strftime("%Y-%m-%d", time.localtime())
        # print("[{}]网站监控报表插件定时执行以下任务：".format(now))
        print(tool.getMsg("TIPS_SCHEDULED_TASK", args=(now,)))
        # print("1. 生成数据周报和数据月报。此任务需要分析日志数据，会占用服务器计算资源，请选择在服务器闲时执行。")
        print(tool.getMsg("TIPS_SCHEDULED_TASK_1"))
        print(tool.getMsg("TIPS_SCHEDULED_TASK_2"))
        print(tool.getMsg("TIPS_SCHEDULED_TASK_3"))
        print(tool.getMsg("TIPS_SCHEDULED_TASK_NOTICE"))
        print("-" * 30)

        config = get_config()
        task_list = config["task_list"]
        for task in task_list:
            if task == "record_log_size":
                try:
                    record_log_size()
                except:
                    pass
            elif task == "generate_report":
                try:
                    from total_report import automatic_generate_report
                    # 当前日期为周一或每月一号时执行方法
                    month_time = time.localtime().tm_mday
                    week_time = time.localtime().tm_wday
                    if month_time == 1 or week_time == 0:
                        automatic_generate_report(week_time, month_time)
                except:
                    pass
            elif task == "clear_space":
                sites = public.M('sites').field('name').order("addtime").select()
                for site_info in sites:
                    site_name = ""
                    try:
                        site_name = site_info["name"]
                        clear_space(site_name)
                    except Exception as e:
                        print("清理网站: {} 磁盘空间异常: {}".format(site_name, e))
            elif task == "update_spiders":
                try:
                    from total_tools import request_plugin
                    latest_update = public.readFile("/www/server/total/xspiders/latest_update.log")
                    if latest_update:
                        fnow = time.time()
                        fupdate = float(latest_update)
                        if fnow - fupdate < 604800:
                            # print("距离上次更新未超过一个星期。")
                            continue
                    update_res = request_plugin("update_spiders_from_cloud", [])
                    if 'status' in update_res and update_res["status"]:
                        print(tool.getMsg("UPDATE_SPIDERS_SUCCESSFULLY"))
                    else:
                        print(tool.getMsg("UPDATE_SPIDERS_FAILED", args=(update_res.get("msg", ""),)))
                except Exception as e:
                    print(tool.getMsg("UPDATE_SPIDERS_EXCEPTION", args=(str(e),)))
    except Exception as e:
        print(e)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "execute":
            execute()
        elif action == "remove":
            remove_background_task()
        elif action == "clear_space":
            arg_len = len(sys.argv)
            save_day = 0
            compress_day = 0
            if arg_len > 2:
                target_site = sys.argv[2]
            if arg_len > 3:
                save_day = int(sys.argv[3])
            if arg_len > 4:
                compress_day = int(sys.argv[4])
            clear_space(target_site, save_day=save_day, compress_day=compress_day)
