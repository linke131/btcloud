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
import datetime
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
        "task_list": ["record_log_size", "generate_report", "migrate_hot_logs", "update_spiders", "clear_uri_logs"],
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


def compress_logs(log_dir, compress_date):
    """压缩站点日志

    Args:
        log_dir (str): 日志目录
        compress_date: 压缩日期
    """
    # print("compress date: {}".format(time.strftime("%Y-%m-%d", compress_date)))
    # 压缩文件
    for f in os.listdir(log_dir):
        fname, suffix = os.path.splitext(f)
        if suffix != ".db": continue
        log_date = None
        try:
            log_date = time.strptime(fname[0:8], "%Y%m%d")
        except:
            log_date = None
        if log_date and log_date < compress_date:
            try:
                # 压缩历史日志
                compress_type, c_suffix = tool.get_default_compress_type()
                compress_file = os.path.splitext(f)[0] +"."+c_suffix
                if os.path.exists(compress_file): continue
                compress_cmd = "cd {} && tar -czf {} {}".format(log_dir, compress_file, f)
                print("压缩文件: {} --> {}".format(f, compress_file))
                exec_res = public.ExecShell(compress_cmd)
                db_full_path = os.path.join(log_dir, f)
                if os.path.exists(db_full_path): os.remove(db_full_path)
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
        start_time = time.localtime(time.mktime((start_time.tm_year,
                                                 start_time.tm_mon, start_time.tm_mday - 1, 0, 0, 0, 0, 0, 0)))

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
    clear_total(site_name)
    config = tool.get_site_settings(site_name)
    if not save_day:
        save_day = config["save_day"]
    # print("save day: {}".format(save_day))
    if not compress_day:
        compress_day = 30
        if "compress_day" in config:
            compress_day = config["compress_day"]

    data_dir = config["data_dir"]
    log_dir = os.path.join(data_dir, site_name)
    time_now = time.localtime()
    save_date = time.localtime(time.mktime((time_now.tm_year, time_now.tm_mon,
                                            time_now.tm_mday - save_day - 1, 0, 0, 0, 0, 0, 0)))

    clear_logs(log_dir, save_date)

    # 清理logs.info记录
    info_file = "/www/server/total/logs/{}/logs.info".format(site_name)
    log_info_str = public.readFile(info_file)
    if log_info_str:
        to_write = False
        log_info = json.loads(log_info_str)
        _d = []

        # 检查延迟任务执行时间
        to_compression_history_file = False
        if "delay_compression" in log_info.keys():
            delay = log_info["delay_compression"]
            now = time.time()
            if delay != 0 and now > delay:
                to_compression_history_file = True

        # print("To compression: {}".format(to_compression_history_file))

        for fkey, info in log_info.items():
            if not type(info) == dict: continue
            f_end = time.localtime(float(info["end"]))
            real_file = os.path.join(log_dir, fkey)
            if f_end < save_date:
                if os.path.exists(real_file):
                    # print("即将删除: {}".format(fkey))
                    os.remove(real_file)
                _d.append(fkey)

            # 执行延迟压缩任务
            elif to_compression_history_file \
                    and "compressed" in info and not info["compressed"]:
                if not os.path.exists(real_file): continue
                if real_file.find("history_logs.db") == -1: continue
                # print("执行延迟任务。")
                _, c_suffix = tool.get_default_compress_type()
                compress_file = os.path.splitext(fkey)[0] + "." + c_suffix
                if os.path.exists(compress_file):
                    continue
                compress_cmd = "cd {} && tar -czf {} {}".format(log_dir, compress_file, fkey)
                # print("压缩命令:")
                # print(compress_cmd)
                public.ExecShell(compress_cmd)
                if os.path.exists(real_file):
                    os.remove(real_file)
                info["compressed"] = compress_file
                to_write = True

        if to_compression_history_file:
            # 延迟任务只检测一次
            log_info["delay_compression"] = 0
            to_write = True

        if _d:
            for d in _d:
                del log_info[d]
            to_write = True

        if to_write:
            if not log_info:
                if os.path.exists(info_file):
                    os.remove(info_file)
            else:
                public.writeFile(info_file, json.dumps(log_info))

    # 压缩日志
    if not compress_day:
        compress_day = 30
    if compress_day > save_day:
        compress_day = save_day
    if compress_day != -1:
        compress_date = time.localtime(time.mktime((time_now.tm_year,
                                                    time_now.tm_mon, time_now.tm_mday - compress_day - 1, 0, 0, 0, 0, 0,
                                                    0)))
        compress_logs(log_dir, compress_date)
    else:
        print("日志不压缩。")

    # 移动昨日的db文件到历史目录 可重复执行
    d = tool.get_data_dir()
    h = tool.get_history_data_dir()
    if d != h:
        import shutil
        yesterday = time.localtime(
            time.mktime((time_now.tm_year, time_now.tm_mon, time_now.tm_mday - 1, 0, 0, 0, 0, 0, 0)))
        _date_str = time.strftime("%Y%m%d", yesterday)
        db_name = _date_str + ".db"
        yesterday_db = os.path.join(d, site_name, db_name)
        history_yesterday_db = os.path.join(h, site_name, db_name)
        if not os.path.isdir(os.path.dirname(history_yesterday_db)): os.makedirs(os.path.dirname(history_yesterday_db))
        if os.path.exists(yesterday_db): shutil.move(yesterday_db, history_yesterday_db)

        # 移动所有/www/server/total/logs/site_name目录下的tar.gz到history_data目录中
        d_site = os.path.join(d, site_name)
        h_site = os.path.join(h, site_name)
        if not os.path.isdir(h_site): os.makedirs(h_site)
        for f in os.listdir(d_site):
            if f.endswith(".tar.gz"):
                shutil.move(os.path.join(d_site, f), os.path.join(h_site, f))

    clear_total(site_name)


def construct_query_date(query_date):
    '''
    构造查询时间
    @param query_date:
    @return: start_date:2023-06-26 end_date:2023-06-26
    '''
    today = datetime.date.today()
    date_ranges = {
        'h1': (today - datetime.timedelta(hours=1), today),
        'today': (today, today),
        'yesterday': (today - datetime.timedelta(days=1), today - datetime.timedelta(days=1)),
        'l7': (today - datetime.timedelta(days=7), today),
        'l30': (today - datetime.timedelta(days=30), today),
        'l120': (today - datetime.timedelta(days=120), today),
        'l180': (today - datetime.timedelta(days=180), today)
    }
    start_date, end_date = date_ranges.get(query_date, (None, None))
    return start_date, end_date


def construct_table_names(start_date, end_date, table_type_tup):
    '''
    构造表名
    @param start_date:
    @param end_date:
    @param table_type_tup:
    @return: {'uri_count_stat': ['uri_count_stat_202306'],...}
    '''
    tables = {}
    for table_type in table_type_tup:
        current_date = start_date
        construct_table_names = []
        while current_date <= end_date:
            table_name = table_type + '_' + current_date.strftime('%Y%m')
            if table_name not in construct_table_names: construct_table_names.append(table_name)
            current_date += datetime.timedelta(days=1)
        if construct_table_names: tables[table_type] = construct_table_names
    return tables


def clear_uri_logs(site):
    '''
    删除3个月前的uri独立统计表，仅保留最近3个月的
    @param site:
    @return:
    '''
    from tsqlite import tsqlite
    from itertools import chain
    db_path = "/www/server/total/logs/{}/total.db".format(site)
    ts = tsqlite()
    ts.dbfile(db_path)
    if not ts:
        print("数据库连接失败!")
        return

    table_names = [row[0] for row in ts.query("SELECT name FROM sqlite_master WHERE type='table'")]

    start_date, end_date = construct_query_date("l120")
    table_type_tup = ("uri_count_stat", "uri_client_stat", "uri_spider_stat", "uri_flow_stat", "uri_ip_stat")
    table_names_dict = construct_table_names(start_date, end_date, table_type_tup)

    data = {key: value[:2] for key, value in table_names_dict.items()}

    for table_name in chain(*data.values()):
        if table_name not in table_names: continue
        ts.query("DROP TABLE IF EXISTS {}".format(table_name))
        print("删除表:{}".format(table_name))

    ts.close()


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
            elif task == "clear_uri_logs":
                print("正在清理过期的uri独立统计日志...")
                sites = public.M('sites').field('name').order("addtime").select()
                for site_info in sites:
                    site_name = ""
                    try:
                        site_name = site_info["name"]
                        clear_uri_logs(site_name)
                    except Exception as e:
                        print("清理网站: {} 日志异常: {}".format(site_name, e))
            elif task == "generate_report":
                try:
                    from total_report import automatic_generate_report
                    automatic_generate_report()
                except:
                    pass
            elif task == "clear_space":
                sites = public.M('sites').field('name').order("addtime").select()
                for site_info in sites:
                    site_name = site_info["name"] if "name" in site_info else ""
                    try:
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
