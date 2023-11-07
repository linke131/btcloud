#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# | Date: 2021/4/21 
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表 - 更新补丁
# +--------------------------------------------------------------------
from __future__ import absolute_import, print_function, division
import datetime
import os
import sys
import time
import json
import sqlite3

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public
from tsqlite import tsqlite
from lua_maker import LuaMaker
import total_tools as tool
ISOLATION_LEVEL = "EXCLUSIVE"
BASE_DIR = "/www/server/total"
TOTAL_DB_NAME = "total.db"

_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

keep_indexes = ['id_inx', 'time_inx']
migrating_file = "/www/server/total/migrating"

def check_database():
    return True

keep_columns = {
    "request_stat":["time", "req", "pv", "uv", "ip", "length", "spider", "fake_spider"],
    "site_logs": ["is_spider", "request_headers", "ip_list", "client_port"],
    "client_stat": ["other", "machine", "mobile"],
    "spider_stat": ["other", "mpcrawler", "yahoo", "duckduckgo"],
    "ip_stat": ["day_hour1", "flow_hour1"],
    "referer2_stat": ["day_hour1", "flow_hour1"],
    "uri_stat": ["day_hour1", "flow_hour1", "spider_flow_hour1"]
}
keep_columns_info = {
    "request_headers": "request_headers TEXT DEFAULT ''",
    "spider": "spider INTEGER DEFAULT 0",
    "fake_spider": "fake_spider INTEGER DEFAULT 0",
    "is_spider": "is_spider INTEGER DEFAULT 0",
    "other": "other INTEGER DEFAULT 0",
    "machine": "machine INTEGER DEFAULT 0",
    "mobile": "mobile INTEGER DEFAULT 0",
    "ip_list": "ip_list TEXT DEFAULT ''",
    "mpcrawler": "mpcrawler INTEGER DEFAULT 0",
    "yahoo": "yahoo INTEGER DEFAULT 0",
    "duckduckgo": "duckduckgo INTEGER DEFAULT 0",
    "client_port": "client_port INTEGER DEFAULT -1",
    "day_hour1": "day_hour1 INTEGER DEFAULT 0",
    "flow_hour1": "flow_hour1 INTEGER DEFAULT 0",
    "spider_flow_hour1": "spider_flow_hour1 INTEGER DEFAULT 0"
}
status_code_50x = [500, 501, 502, 503, 504, 505, 506, 507, 509, 510]
status_code_40x = [400, 401, 402, 403, 404, 405, 406, 407, 408, 409,
                   410, 411, 412, 413, 414, 415, 416, 417, 418, 421, 
                   422, 423, 424, 425, 426, 449, 451, 499]
http_methods = ["get", "post", "put", "patch", "delete"]

# 添加状态列
for s in status_code_50x:
    column = "status_"+repr(s)
    keep_columns["request_stat"].append(column)
    keep_columns_info.update({column: column + " INTEGER DEFAULT 0"})

for s in status_code_40x:
    column = "status_"+repr(s)
    keep_columns["request_stat"].append(column)
    keep_columns_info.update({column: column + " INTEGER DEFAULT 0"})

# 添加请求方法列
for method in http_methods:
    column = "http_"+method
    keep_columns["request_stat"].append(column)
    keep_columns_info.update({column: column+" INTEGER DEFAULT 0"})

# 添加流量统计列
for i in range(1, 32):
    column = "flow"+repr(i)
    keep_columns["ip_stat"].append(column)
    keep_columns["uri_stat"].append(column)
    keep_columns_info.update({column: column+" INTEGER DEFAULT 0"})


# 添加URI蜘蛛流量列
for i in range(1, 32):
    column = "spider_flow"+repr(i)
    keep_columns["uri_stat"].append(column)
    keep_columns_info.update({column: column+" INTEGER DEFAULT 0"})


def get_timestamp_interval(local_time):
    start = None
    end = None
    start = time.mktime((local_time.tm_year, local_time.tm_mon, local_time.tm_mday, 0, 0, 0, 0, 0, 0))
    end = time.mktime((local_time.tm_year, local_time.tm_mon, local_time.tm_mday, 23, 59, 59, 0, 0, 0))
    return start, end

def get_last_days_by_timestamp(day):
    now = time.localtime()
    t1 = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - day + 1, 0, 0, 0, 0, 0, 0))
    t2 = time.localtime(t1)
    start, _ = get_timestamp_interval(t2)
    _, end = get_timestamp_interval(now)
    return start, end

def get_time_interval(local_time):
    start = None
    end = None
    time_key_format = "%Y%m%d00"
    start = int(time.strftime(time_key_format, local_time))
    time_key_format = "%Y%m%d23"
    end = int(time.strftime(time_key_format, local_time))
    return start, end

def get_last_days(day):
    now = time.localtime()
    t1 = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - day + 1, 0, 0, 0, 0, 0, 0))
    t2 = time.localtime(t1)
    start, _ = get_time_interval(t2)
    _, end = get_time_interval(now)
    return start, end

sync_logs = {}
def mark_sync(site, item):
    log_path = "/www/server/panel/plugin/total/sync.log"
    key = site+"_"+item
    origin_content = ""
    if os.path.isfile(log_path):
        origin_content = public.readFile(log_path)
    public.writeFile(log_path, origin_content + key+"\n")
    sync_logs[key] = True

def is_synced(site, item):
    log_path = "/www/server/panel/plugin/total/sync.log"
    if not os.path.isfile(log_path):
        return False
    if not sync_logs:
        lines = public.readFile(log_path)
        if lines:
            lines = lines.split("\n")
            for line in lines:
                sync_logs[line.strip()] = True
    key = site+"_"+item
    if key in sync_logs.keys():
        return True
    return False    

keep_tables = ["uri_stat", "ip_stat", "referer2_stat"]
table_create_sqls = {
    "uri_stat": """
            CREATE TABLE uri_stat (
					uri_md5 CHAR(32) PRIMARY KEY,
					uri TEXT,
					day1 INTEGER DEFAULT 0,
					day2 INTEGER DEFAULT 0,
					day3 INTEGER DEFAULT 0,
					day4 INTEGER DEFAULT 0,
					day5 INTEGER DEFAULT 0,
					day6 INTEGER DEFAULT 0,
					day7 INTEGER DEFAULT 0,
					day8 INTEGER DEFAULT 0,
					day9 INTEGER DEFAULT 0,
					day10 INTEGER DEFAULT 0,
					day11 INTEGER DEFAULT 0,
					day12 INTEGER DEFAULT 0,
					day13 INTEGER DEFAULT 0,
					day14 INTEGER DEFAULT 0,
					day15 INTEGER DEFAULT 0,
					day16 INTEGER DEFAULT 0,
					day17 INTEGER DEFAULT 0,
					day18 INTEGER DEFAULT 0,
					day19 INTEGER DEFAULT 0,
					day20 INTEGER DEFAULT 0,
					day21 INTEGER DEFAULT 0,
					day22 INTEGER DEFAULT 0,
					day23 INTEGER DEFAULT 0,
					day24 INTEGER DEFAULT 0,
					day25 INTEGER DEFAULT 0,
					day26 INTEGER DEFAULT 0,
					day27 INTEGER DEFAULT 0,
					day28 INTEGER DEFAULT 0,
					day29 INTEGER DEFAULT 0,
					day30 INTEGER DEFAULT 0,
					day31 INTEGER DEFAULT 0,
					day32 INTEGER DEFAULT 0
				) """,
    "ip_stat": """CREATE TABLE ip_stat (
					ip CHAR(15) PRIMARY KEY,
					area CHAR(8) DEFAULT "",
					day1 INTEGER DEFAULT 0,
					day2 INTEGER DEFAULT 0,
					day3 INTEGER DEFAULT 0,
					day4 INTEGER DEFAULT 0,
					day5 INTEGER DEFAULT 0,
					day6 INTEGER DEFAULT 0,
					day7 INTEGER DEFAULT 0,
					day8 INTEGER DEFAULT 0,
					day9 INTEGER DEFAULT 0,
					day10 INTEGER DEFAULT 0,
					day11 INTEGER DEFAULT 0,
					day12 INTEGER DEFAULT 0,
					day13 INTEGER DEFAULT 0,
					day14 INTEGER DEFAULT 0,
					day15 INTEGER DEFAULT 0,
					day16 INTEGER DEFAULT 0,
					day17 INTEGER DEFAULT 0,
					day18 INTEGER DEFAULT 0,
					day19 INTEGER DEFAULT 0,
					day20 INTEGER DEFAULT 0,
					day21 INTEGER DEFAULT 0,
					day22 INTEGER DEFAULT 0,
					day23 INTEGER DEFAULT 0,
					day24 INTEGER DEFAULT 0,
					day25 INTEGER DEFAULT 0,
					day26 INTEGER DEFAULT 0,
					day27 INTEGER DEFAULT 0,
					day28 INTEGER DEFAULT 0,
					day29 INTEGER DEFAULT 0,
					day30 INTEGER DEFAULT 0,
					day31 INTEGER DEFAULT 0,
					day32 INTEGER DEFAULT 0
				) """,
    "referer2_stat": """
        CREATE TABLE referer2_stat (
				referer_md5 CHAR(32) PRIMARY KEY,
				referer TEXT,
				day1 INTEGER DEFAULT 0,
				day2 INTEGER DEFAULT 0,
				day3 INTEGER DEFAULT 0,
				day4 INTEGER DEFAULT 0,
				day5 INTEGER DEFAULT 0,
				day6 INTEGER DEFAULT 0,
				day7 INTEGER DEFAULT 0,
				day8 INTEGER DEFAULT 0,
				day9 INTEGER DEFAULT 0,
				day10 INTEGER DEFAULT 0,
				day11 INTEGER DEFAULT 0,
				day12 INTEGER DEFAULT 0,
				day13 INTEGER DEFAULT 0,
				day14 INTEGER DEFAULT 0,
				day15 INTEGER DEFAULT 0,
				day16 INTEGER DEFAULT 0,
				day17 INTEGER DEFAULT 0,
				day18 INTEGER DEFAULT 0,
				day19 INTEGER DEFAULT 0,
				day20 INTEGER DEFAULT 0,
				day21 INTEGER DEFAULT 0,
				day22 INTEGER DEFAULT 0,
				day23 INTEGER DEFAULT 0,
				day24 INTEGER DEFAULT 0,
				day25 INTEGER DEFAULT 0,
				day26 INTEGER DEFAULT 0,
				day27 INTEGER DEFAULT 0,
				day28 INTEGER DEFAULT 0,
				day29 INTEGER DEFAULT 0,
				day30 INTEGER DEFAULT 0,
				day31 INTEGER DEFAULT 0,
				day32 INTEGER DEFAULT 0,
                flow1 INTEGER DEFAULT 0,
                flow2 INTEGER DEFAULT 0,
                flow3 INTEGER DEFAULT 0,
                flow4 INTEGER DEFAULT 0,
                flow5 INTEGER DEFAULT 0,
                flow6 INTEGER DEFAULT 0,
                flow7 INTEGER DEFAULT 0,
                flow8 INTEGER DEFAULT 0,
                flow9 INTEGER DEFAULT 0,
                flow10 INTEGER DEFAULT 0,
                flow11 INTEGER DEFAULT 0,
                flow12 INTEGER DEFAULT 0,
                flow13 INTEGER DEFAULT 0,
                flow14 INTEGER DEFAULT 0,
                flow15 INTEGER DEFAULT 0,
                flow16 INTEGER DEFAULT 0,
                flow17 INTEGER DEFAULT 0,
                flow18 INTEGER DEFAULT 0,
                flow19 INTEGER DEFAULT 0,
                flow20 INTEGER DEFAULT 0,
                flow21 INTEGER DEFAULT 0,
                flow22 INTEGER DEFAULT 0,
                flow23 INTEGER DEFAULT 0,
                flow24 INTEGER DEFAULT 0,
                flow25 INTEGER DEFAULT 0,
                flow26 INTEGER DEFAULT 0,
                flow27 INTEGER DEFAULT 0,
                flow28 INTEGER DEFAULT 0,
                flow29 INTEGER DEFAULT 0,
                flow30 INTEGER DEFAULT 0,
                flow31 INTEGER DEFAULT 0
			) """
}

def check_table(ts):
    select_res = ts.execute("select name from sqlite_master where type='table';").fetchall()
    cur_tables = [t[0] for t in select_res]
    for new_table in keep_tables:
        if new_table not in cur_tables:
            if new_table in table_create_sqls.keys():
                sql = table_create_sqls[new_table]
                ts.execute(sql)

def alter_history_columns():
    return True
    ts = None
    conn = None
    sites = public.M('sites').field('name').order("addtime").select()
    error_count = 0
    for site_info in sites:
        try:
            site = site_info["name"]
            site = site.replace("_", ".")
            db_path = tool.get_log_db_path(site, history=True)
            if not os.path.isfile(db_path):
                continue
            print("调整历史数据库: {}".format(db_path))
            import sqlite3
            conn = sqlite3.connect(db_path, isolation_level=ISOLATION_LEVEL)
            ts = conn.cursor()
            conn.execute("BEGIN TRANSACTION;")
            change_table = False
            for table_name, kcolumns in keep_columns.items():
                if table_name == "site_logs":
                    columns = ts.execute("PRAGMA table_info([{}])".format(table_name))
                    columns = [column[1] for column in columns]
                    for column_name in kcolumns:
                        if column_name not in columns:
                            # print("检查列:" + column_name)
                            if column_name in keep_columns_info.keys():
                                column_info = keep_columns_info[column_name]
                                alter_sql = "ALTER TABLE {} ADD COLUMN {};".format(
                                    table_name, column_info)
                                ts.execute(alter_sql)
                                print("调整列:{}".format(column_name))
                                change_table = True
            if change_table:
                conn.execute("COMMIT;")
        except Exception as e:
            print("调整历史日志数据库结构错误: {}".format(e))
            error_count += 1
        finally:
            ts and ts.close()
            conn and conn.close()
    return error_count == 0

def alter_columns():
    try:
        ts = None
        conn = None
        error_count = 0
        # print("正在同步数据...")
        print(tool.getMsg("TIPS_SYNC_DATA"))
        # print("可能会耗费较长时间(与数据量、站点数量相关)，请耐心等待。")
        print(tool.getMsg("TIPS_WAITING"))
        sites = public.M('sites').field('name').order("addtime").select()
        # logs db patch
        for site_info in sites:
            try:
                public.writeFile(migrating_file, "migrating")
                site = site_info["name"]
                site = site.replace("_", ".")
                print(tool.getMsg("TIPS_SYNC_SITE_DATA", args=(site,)))
                db_path = os.path.join(tool.get_data_dir(), site, tool.get_logs_db_name())
                if not os.path.exists(db_path):
                    continue
                import sqlite3
                conn = sqlite3.connect(db_path, isolation_level=ISOLATION_LEVEL)
                ts = conn.cursor()
                conn.execute("BEGIN TRANSACTION;")

                for table_name, kcolumns in keep_columns.items():
                    # 去掉site_logs兼容性检查
                    if table_name != "site_logs": continue
                    columns = ts.execute(
                        "PRAGMA table_info([{}])".format(table_name))
                    columns = [column[1] for column in columns]
                    for column_name in kcolumns:
                        if column_name not in columns:
                            # print("检查列:" + column_name)
                            if column_name in keep_columns_info.keys():
                                column_info = keep_columns_info[column_name]
                                alter_sql = "ALTER TABLE {} ADD COLUMN {};".format(
                                    table_name, column_info)
                                ts.execute(alter_sql)
                try:
                    conn.execute("COMMIT;")
                except Exception as e: 
                    pass
            except Exception as e:
                print("调整日志数据库结构出现错误: {}".format(e))
            finally:
                if os.path.isfile(migrating_file):
                    os.remove(migrating_file)
                try:
                    if ts:
                        ts.close()
                    if conn:
                        conn.close()
                except:
                    pass

        for site_info in sites:
            try:
                public.writeFile(migrating_file, "migrating")
                site = site_info["name"]
                print(tool.getMsg("TIPS_SYNC_SITE_DATA", args=(site,)))
                site = site.replace("_", ".")
                db_path = os.path.join(BASE_DIR, "logs", site, TOTAL_DB_NAME)
                if not os.path.isfile(db_path):
                    continue
                import sqlite3
                conn = sqlite3.connect(db_path, isolation_level=ISOLATION_LEVEL)
                ts = conn.cursor()
                conn.execute("BEGIN TRANSACTION;")

                check_table(ts)

                for table_name, kcolumns in keep_columns.items():
                    # 去掉site_logs兼容性检查
                    if table_name == "site_logs": continue
                    columns = ts.execute(
                        "PRAGMA table_info([{}])".format(table_name))
                    columns = [column[1] for column in columns]
                    for column_name in kcolumns:
                        if column_name not in columns:
                            # print("检查列:" + column_name)
                            if column_name in keep_columns_info.keys():
                                column_info = keep_columns_info[column_name]
                                alter_sql = "ALTER TABLE {} ADD COLUMN {};".format(
                                    table_name, column_info)
                                ts.execute(alter_sql)

                    if table_name == "spider_stat":
                        for column_name in columns:
                            if column_name.find("_flow") > 0: continue
                            if column_name == "time":continue
                            flow_column = column_name+"_flow"
                            if flow_column in columns: continue
                            alter_sql = "ALTER TABLE {} ADD COLUMN {} INTEGER DEFAULT 0".format("spider_stat", flow_column)
                            ts.execute(alter_sql)
                try:
                    conn.execute("COMMIT;")
                except Exception as e:
                    err_msg = str(e)
                    if err_msg.find("no transaction is active") < 0:
                        print(site+" error:" + str(e))
            except Exception as e:
                print(site+" error:" + str(e))
                error_count += 1

        if os.path.isfile(migrating_file):
            os.remove(migrating_file)
        # print("数据同步完成。")
        print(tool.getMsg("TIPS_SYNC_COMPLETED"))
        return error_count == 0
    except Exception as e:
        print(tool.getMsg("TIPS_SYNC_ERROR", args=(str(e),)))
    finally:
        if os.path.isfile(migrating_file):
            os.remove(migrating_file)
        try:
            if ts:
                ts.close()
            if conn:
                conn.close()
        except:
            pass
    return False

def sync_config():
    # print("正在同步配置...")
    print(tool.getMsg("TIPS_SYNC_SETTINGS"))
    config = json.loads(public.readFile("/www/server/total/config.json"))
    if "global" not in config.keys():
        os.system("mv /www/server/total/config.json /www/server/total/config.json.bak")
        os.system("cp /www/server/total/config/default_config.json /www/server/total/config.json")
        time.sleep(1)
        config = json.loads(public.readFile("/www/server/total/config.json"))

    global_config = config["global"]
    if "statistics_machine_access" not in global_config.keys():
        global_config["statistics_machine_access"] = True
    if "exclude_url" not in global_config.keys():
        global_config["exclude_url"] = []
    if "statistics_ip" not in global_config.keys():
        global_config["statistics_ip"] = True
    if "statistics_uri" not in global_config.keys():
        global_config["statistics_uri"] = True
    if "record_post_args" not in global_config.keys():
        global_config["record_post_args"] = False
    if "record_get_403_args" not in global_config.keys():
        global_config["record_get_403_args"] = False
    if "data_dir" not in global_config.keys():
        global_config["data_dir"] = "/www/server/total/logs"
    if "history_data_dir" not in global_config.keys():
        global_config["history_data_dir"] = "/www/server/total/logs"
    if "ip_top_num" not in global_config.keys():
        global_config["ip_top_num"] = 50
    if "uri_top_num" not in global_config.keys():
        global_config["uri_top_num"] = 50
    if "referer_top_num" not in global_config.keys():
        global_config["referer_top_num"] = 50
    if "push_report" not in global_config.keys():
        global_config["push_report"] = False
    if "exclude_ip" not in global_config.keys():
        global_config["exclude_ip"] = []
    if "compress_day" not in global_config.keys():
        global_config["compress_day"] = 30
    # config["global"] = global_config
    for site, site_config in config.items():
        if site.find("_") >= 0:
            config[site.replace("_", ".")] = site_config
            del config[site]
        
    task_config = "/www/server/panel/plugin/total/task_config.json"
    if os.path.exists(task_config):
        tconfig = json.loads(public.readFile(task_config))
        if "task_list" in tconfig:
            task_list = tconfig["task_list"]
            change = False
            if "migrate_hot_logs" in task_list:
                task_list.remove("migrate_hot_logs")
                change = True
            if "update_spiders" not in task_list:
                task_list.append("update_spiders")
                change = True
            if "clear_space" not in task_list:
                task_list.append("clear_space")
                change = True
            if "clear_uri_logs" not in task_list:
                task_list.append("clear_uri_logs")
                change = True

            if change:
                tconfig["task_list"] = task_list
                print("new task config:")
                print(tconfig)
                public.WriteFile(task_config, json.dumps(tconfig))

    public.writeFile("/www/server/total/config.json", json.dumps(config))

    write_lua_config(config)
    # lua_config = LuaMaker.makeLuaTable(config_data)
    # lua_config = "return " + lua_config
    # public.WriteFile("/www/server/total/total_config.lua", lua_config)
    # public.WriteFile("/www/server/total/total_config2.lua", lua_config)
    tool.write_site_domains()
    # print("配置同步完成。")
    print(tool.getMsg("TIPS_SYNC_SETTINGS_COMPLETED"))
    return True

def split_total_data(ori_db, new_db):
    """分离出统计表和所有数据"""
    total_tables = ["request_stat", "client_stat", "referer_stat", "uri_stat", "ip_stat", "spider_stat"]
    for table in total_tables:
        ori_conn = None
        ori_cur = None
        new_conn = None
        new_cur = None
        insert_sql = ""
        try:
            # 初始化表
            if not tool.init_db_from(ori_db, new_db, tables=table):
                return False

            # 逐行拷贝数据
            ori_conn = sqlite3.connect(ori_db)
            if sys.version_info[0] == 3:
                ori_conn.text_factory = lambda x: str(x, encoding="utf-8", errors='ignore')
            else:
                ori_conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
            ori_cur = ori_conn.cursor()

            new_conn = sqlite3.connect(new_db)
            new_cur = new_conn.cursor()
            new_cur.execute("BEGIN TRANSACTION")

            data_sql = "select * from {};".format(table)
            selector = ori_cur.execute(data_sql)
            data_line = selector.fetchone()
            while data_line:
                # params = ",".join(["\'"+str(field).replace("\'", "\\\'")+"\'" for field in data_line])
                params = ""
                for field in data_line:
                    if params:
                        params += ","
                    if type(field) == str:
                        field = "\'" + field.replace("\'", "\”") + "\'"
                    params += str(field)
                    
                insert_sql = "INSERT INTO {} VALUES({})".format(table, params)
                new_cur.execute(insert_sql)

                data_line = selector.fetchone()
            new_conn.commit()
            # print("统计数据: {} 已迁移完成。".format(table))
        except Exception as e:
            print("统计数据: {} 迁移失败: {}".format(table, e))
            print(insert_sql)
            return False
        finally:
            ori_cur and ori_cur.close()
            ori_conn and ori_conn.close() 
            new_cur and new_cur.close()
            new_conn and new_conn.close()
    return True

def split_site_data(site_name, query_date="today"):
    """分离原日志数据库(logs.db)成两部分:
        历史日志(history_logs.db): 只包含今天以前的日志
        统计、今日日志(logs.db): 包含所有统计数据和今天的日志

        分离过程：
        从原logs.db中提取出所有统计数据和今天的日志数据,输出到new_logs.db
        重命名logs.db为history_logs.db,
        重命名new_logs.db为logs.db

        说明：
        分离只适合在用户首次升级时进行，不进行对历史部分的数据整理操作。

        @author: linxiao
        @time: 2021/12/3
    """
    query_start, query_end = tool.get_query_timestamp(query_date)
    data_dir = "/www/server/total/logs/%s/" % (site_name)
    ori_db_path = data_dir + "logs.db" 
    if not os.path.exists(ori_db_path):
        return public.returnMsg(True, "数据库未初始化。")

    new_logs_db = data_dir + "new_logs.db"
    from total_tools import get_history_data_dir
    history_data_dir = get_history_data_dir()
    history_logs_db = os.path.join(history_data_dir, site_name, "history_logs.db")

    new_conn = None
    new_cur = None
    conn = None
    cur = None
    
    insert_sql = ""
    try:
        import sqlite3

        # 只供测试
        # if os.path.exists(new_logs_db):
        #     os.remove(new_logs_db)

        new_conn = sqlite3.connect(new_logs_db)
        new_cur = new_conn.cursor()
        new_cur.execute("PRAGMA synchronous = 0")
        new_cur.execute("PRAGMA page_size = 4096")
        new_cur.execute("PRAGMA journal_mode = wal")
        new_cur.close()
        new_conn.close()

        # TODO: 处理失败情况
        # 1. 迁移统计数据
        if not split_total_data(ori_db_path, new_logs_db):
            return tool.returnMsg(False, "统计数据迁移失败！")

        # 2. 迁移当天日志数据
        # 初始化日志表
        if not tool.init_db_from(ori_db_path, new_logs_db, tables="site_logs"):
            return tool.returnMsg(False, "日志表初始化失败！")

        # 迁移日志
        new_conn = sqlite3.connect(new_logs_db)
        new_cur = new_conn.cursor()

        new_cur.execute("CREATE INDEX time_inx ON site_logs(time)")

        conn = sqlite3.connect(ori_db_path)
        if sys.version_info[0] == 3:
            conn.text_factory = lambda x: str(x, encoding="utf-8", errors='ignore')
        else:
            conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
        cur =  conn.cursor()
        logs_sql = "select * from site_logs where time>={} and time<={}".format(query_start, query_end)
        selector = cur.execute(logs_sql)
        log = selector.fetchone()
        count = 0
        while log:
            # params = ",".join(("\'" +str(field)+ "\'" for field in log))
            params = ""
            # p = False
            for field in log:
                if params:
                    params += ","
                if field is None:
                    field = "\'\'"
                    # p = True
                elif type(field) == str:
                    field = "\'" + field.replace("\'", "\”") + "\'"
                params += str(field)
            insert_sql = "INSERT INTO site_logs values("+params+")"
            # if p:
            #     print(insert_sql)
            new_cur.execute(insert_sql)
            log = selector.fetchone()
            count += 1
        new_conn.commit()
        print("累计迁移: {} 条日志记录。".format(count))

        # 删除已迁移过的日志
        cur.execute("delete from site_logs where time>={} and time<={}".format(query_start, query_end))
        conn.commit()

        cur and cur.close()
        conn and conn.close()
        new_cur and new_cur.close()
        new_conn and new_conn.close()

        cur = None
        conn = None
        new_cur = None
        new_conn = None
        print("网站:{} 日志和统计数据已分离完成。".format(site_name))

        # 3. 调换日志文件

        public.ExecShell("mv -f {} {}".format(ori_db_path, history_logs_db))
        public.ExecShell("mv -f {} {}".format(new_logs_db, ori_db_path))

        public.ExecShell("chown -R www:www "+ history_logs_db)
        public.ExecShell("chown -R www:www "+ ori_db_path)

        if os.path.exists(ori_db_path) and os.path.exists(history_logs_db):
            return public.returnMsg(True, "迁移数据成功！")
    except Exception as e:
        if insert_sql:
            print(insert_sql)
        print("分隔数据库异常: {}".format(e))
    finally:
        try:
            cur and cur.close()
            conn and conn.close()
            new_cur and new_cur.close()
            new_conn and new_conn.close()
        
        except:
            print("分离数据关闭连接异常.")
            pass
        try:
            if os.path.exists(new_logs_db):
                os.remove(new_logs_db)
        except:
            print("分离数据关闭连接异常2.")
            pass
    return public.returnMsg(False, "迁移数据失败！")

def check_history_db(site):
    conn = None
    cur = None
    try:
        from total_tools import get_log_db_path
        history_db_file = get_log_db_path(site, history=True)
        if not os.path.exists(history_db_file):
            return False
        import sqlite3 
        conn = sqlite3.connect(history_db_file)
        cur = conn.cursor()
        res = cur.execute("select count(*) from sqlite_master where type='table' and name='site_logs';").fetchone()
        # print("select site_logs count: {}".format(res))
        if res and int(res[0]) == 1:
            return True
        else:
            if os.path.exists(history_db_file) and os.path.getsize(history_db_file) > 0:
                os.rename(history_db_file, history_db_file+".bak")
    except:
        print("检测历史数据库异常，可能数据库已损坏。")
        if os.path.exists(history_db_file):
            os.rename(history_db_file, history_db_file+".bak")
    finally:
        cur and cur.close()
        conn and conn.close()
    return False

def split_data():
    return True
    """分离所有站点数据库"""
    split_status = True
    try:
        sites = public.M('sites').field('name').order("addtime").select()
        for site_info in sites:
            try:
                site = site_info["name"]
                # print("正在检查网站:{} 是否已分离".format(site))

                _split = check_history_db(site)
                if _split:
                    print("站点: {} 已完成迁移。".format(site))
                    continue

                split_res = split_site_data(site, query_date="today")
                if not split_res["status"]:
                    split_status = False
            except:
                print("站点: {} 分离日志数据库失败！".format(site))
    except Exception as e:
        split_status = False
    return split_status

def write_process_white():
    """往堡塔加固添加进程白名单"""
    try:
        sysafe_config = "/www/server/panel/plugin/syssafe/config.json"
        if os.path.isfile(sysafe_config):
            config = None
            config = json.loads(public.readFile(sysafe_config))
            process_white = config["process"]["process_white"]
            process_name = "total_bloomd"
            change = False
            if process_name in process_white:
                process_white.remove(process_name)
                change = True

            process_name = "wkhtmltopdf"
            if process_name not in process_white:
                process_white.append(process_name)
                change = True

            process_name = "bt_total_server"
            if process_name not in process_white:
                process_white.append(process_name)
                change = True

            if config and change:
                public.writeFile(sysafe_config, json.dumps(config))
        return True
    except Exception as e:
        print(tool.getMsg("WRITE_SETTINGS_ERROR", args=(str(e),)))
    return False

def set_monitor_status(status):
    close_file = "/www/server/total/closing"
    if status == True:
        if os.path.isfile(close_file):
            os.remove(close_file)
        if os.path.isfile("/www/server/nginx/sbin/nginx"):
            os.system("cp /www/server/panel/plugin/total/total_nginx.conf /www/server/panel/vhost/nginx/total.conf")
        if os.path.isfile("/www/server/apache/bin/httpd"):
            os.system("cp /www/server/panel/plugin/total/total_httpd.conf /www/server/panel/vhost/apache/total.conf")
    else:
        public.WriteFile(close_file, "closing")
        os.system("rm -f /www/server/panel/vhost/nginx/total.conf")
        os.system("rm -f /www/server/panel/vhost/apache/total.conf")
    public.serviceReload()


def get_site_settings(site):
    """获取站点配置"""

    config_path = "/www/server/total/config.json"
    config = json.loads(public.readFile(config_path))

    res_config = {}
    if site not in config.keys():
        res_config = config["global"]
    else:
        res_config = config[site]

    for k, v in config["global"].items():
        if k not in res_config:
            res_config[k] = v
    return res_config

def write_lua_config(config=None):
    if not config:
        config = json.loads(public.readFile("/www/server/total/config.json"))
            
    config_data = config
    # lua配置文件写入前置处理
    for xsite, conf in config_data.items():
        if "exclude_url" in conf.keys():
            url_conf = {}
            for i, _o in enumerate(conf["exclude_url"]):
                if _o["mode"] == "regular":
                    # print("ori url: {}".format(_o["url"]))
                    _o["url"] = tool.parse_regular_url(_o["url"])
                    # print("parsed url: {}".format(_o["url"]))
                url_conf[str(i+1)] = _o
            config_data[xsite]["exclude_url"] = url_conf

        if "exclude_ip" in conf.keys() and len(conf["exclude_ip"]) >0:
            ips = []
            for ip in conf["exclude_ip"]:
                if ip.find("-")>0:
                    for xip in tool.parse_ips(ip):
                        ips.append(xip)
                else:
                    ips.append(ip)
            config_data[xsite]["exclude_ip"] = ips

        if "old_exclude_ip" in conf.keys() and len(conf["old_exclude_ip"]) >0:
            if xsite != "global":
                reload_exclude_url_file = os.path.join(tool.get_data_dir(), xsite, "reload_exclude_ip.pl")
            else:
                reload_exclude_url_file = os.path.join(tool.get_data_dir(), "reload_exclude_ip.pl")
            if not os.path.isfile(reload_exclude_url_file):
                del config_data[xsite]["old_exclude_ip"]
            else:
                ips = []
                for ip in conf["old_exclude_ip"]:
                    if ip.find("-")>0:
                        for xip in tool.parse_ips(ip):
                            ips.append(xip)
                    else:
                        ips.append(ip)
                if ips:
                    config_data[xsite]["old_exclude_ip"] = ips

    lua_config = LuaMaker.makeLuaTable(config_data)
    lua_config = "return " + lua_config
    public.WriteFile("/www/server/total/total_config.lua", lua_config)

def get_spiders_from_cloud():
    try:
        if os.path.exists("/www/server/total/xspiders/1.json"):
            return True

        from total_tools import request_plugin
        update_res = request_plugin("update_spiders_from_cloud",[])
        if 'status' in update_res and update_res["status"]:
            print(tool.getMsg("UPDATE_SPIDERS_SUCCESSFULLY"))
            return True
        else:
            print(tool.getMsg("UPDATE_SPIDERS_FAILED", args=(update_res.get("msg", ""),)))
    except Exception as e:
        print(tool.getMsg("UPDATE_SPIDERS_EXCEPTION", args=(str(e),)))
    return False

def compress_logs(db_file):
    """压缩日志文件

    Args:
        db_file (str): 目标日志文件路径

    Returns:
        dict: 文件压缩后相关信息
    """
    info = {}

    # 压缩
    compress_type, suffix = tool.get_default_compress_type()
    new_file = os.path.splitext()[0] + "." + suffix
    c_res = tool.compress_file(db_file, new_file, ctype=compress_type)
    file_size = os.path.getsize(new_file)
    if c_res and file_size > 0:
        info["compressed"] = new_file
        info["file_size"] = file_size
        info["time"] = time.time()
    return info

def upgrade_db_storage(site_name):
    """ 升级数据存储方案
    1. 对已有的history_logs.db和logs.db中存储的日志数据建立时间区间索引。
    2. 对logs.db中的统计数据进行分离。

    info文件以文件名为Key，内容定义如下:
    start_time: 日志开始时间
    end_time: 日志终止时间
    file_name: 原文件路径
    compressed: 空或者文件路径
    file_size: 文件大小
    """

    info_file = "/www/server/total/logs/{}/logs.info".format(site_name)
    log_info = {}
    if os.path.exists(info_file):
        log_info = json.loads(public.readFile(info_file))

    to_write = False
    # 处理history
    history_db_file_name = "history_logs.db"
    need_compress = False
    history_db_file = tool.get_log_db_path(
        site_name, 
        db_name=history_db_file_name, 
        history=True)
    if os.path.exists(history_db_file) and \
        not history_db_file_name in log_info.keys():
        start, end = tool.get_db_time_interval(history_db_file)
        if start == 0 or end == 0:
            if os.path.exists(history_db_file):
                os.remove(history_db_file)
        else:
            x = {}
            # start, _ = tool.get_timestamp_interval(time.localtime(start))
            # _, end = tool.get_timestamp_interval(time.localtime(end))
            x["start"] = start
            x["end"] = end
            x["file_name"] = history_db_file_name
            x["compressed"] = ""
            x["file_size"] = os.path.getsize(history_db_file)

            log_info[history_db_file_name] = x
            need_compress = True
            to_write = True

    now = time.localtime()
    # 处理热数据
    logs_db_name = "logs.db"
    logs_db_file = tool.get_log_db_path(site_name, db_name=logs_db_name)
    # 新统计数据库名是固定的
    if "split_total" not in log_info:
        to_write = True
        new_db_name = "/www/server/total/logs/{}/{}".format(site_name, 
            TOTAL_DB_NAME)
        logs_db_size = 0
        if os.path.exists(logs_db_file):
            logs_db_size = os.path.getsize(logs_db_file)
        if logs_db_size == 0:
            if os.path.exists(logs_db_file):
                os.remove(logs_db_file)
            log_info["split_total"] = True
        elif os.path.exists(new_db_name):
            print("{}:新统计db文件已存在，无法自动完成分离统计数据。".format(site_name))
            log_info["split_total"] = False
        else:
            # 分离统计数据和昨日日志
            if os.path.exists(logs_db_file):
                split_res = split_total_data(logs_db_file, new_db_name)
                public.ExecShell("chown www:www {}".format(new_db_name))
                public.ExecShell("chmod +x {}".format(new_db_name))
                if not split_res:
                    print("分离统计数据失败！")
                    log_info["split_total"] = False
                else:
                    log_info["split_total"] = True

                # 修改logs.db为today.db
                today_db_name = time.strftime("%Y%m%d", now) + ".db"
                today_db_path = tool.get_log_db_path(site_name, db_name=today_db_name)
                os.rename(logs_db_file, today_db_path)
                db_file = today_db_path

                # 手动记录today.db的时间区间
                # print("db file: {}".format(db_file))
                start, end = tool.get_db_time_interval(db_file)
                if start != 0 and end != 0:
                    z = {}
                    z["start"] = start
                    _, z["end"] = tool.get_timestamp_interval(now)
                    z["file_name"] = today_db_name
                    z["compressed"] = ""
                    z["file_size"] = os.path.getsize(db_file)

                    log_info[today_db_name] = z
                    need_compress = True
            else:
                from total_migrate import total_migrate
                tm = total_migrate()
                tm.init_site_db(site_name)
                log_info["split_total"] = True

    if need_compress and "delay_compression" not in log_info:
        # 延迟3天执行归档任务
        _, end = tool.get_timestamp_interval(now)
        log_info["delay_compression"] = end + 86400*3
        to_write = True

    if to_write:
        public.writeFile(info_file, json.dumps(log_info))
    return True


if __name__ == "__main__":
    now = ""
    monitor_status = True 
    config_path = "/www/server/total/config.json"
    try:
        settings = {}
        global_settings = {}
        if os.path.isfile(config_path):
            settings = json.loads(public.readFile(config_path))
            # print(settings)
            if "global" in settings:
                global_settings = settings["global"]
                monitor_status = global_settings["monitor"]

        # print("原监控状态:"+str(monitor_status))
        if monitor_status and global_settings:
            global_settings["monitor"] = False
            public.writeFile(config_path, json.dumps(settings))
            write_lua_config(settings)
            set_monitor_status(False)
            # print("监控报表已关闭。")
            print(tool.getMsg("TIPS_MONITOR_CLOSED"))

        # excute_res1 = check_database()  
        excute_res1 = True
        excute_res21 = alter_columns() 
        # excute_res22 = alter_history_columns()
        excute_res22 = True
        excute_res2 = excute_res21 and excute_res22
        excute_res3 = sync_config()
        excute_res4 = write_process_white()
        from total_task import create_background_task
        excute_res5 = create_background_task()
        # excute_res6 = split_data()
        
        sites = public.M('sites').field('name').order("addtime").select()
        upgrade_res = []
        for site_info in sites:
            site_name = site_info["name"]
            site_name = site_name.replace("_", ".")
            try:
                r = upgrade_db_storage(site_name)
                if not r:
                    upgrade_res.append(site_name)
            except Exception as e:
                upgrade_res.append(site_name)
                print("站点: {} db升级失败。".format(e))
        excute_res6 = True
        if upgrade_res:
            excute_res6 = False
            print("以下站点数据存储升级失败:")
            print("\n".join(upgrade_res))

        from total_report import init_db as init_report_db
        init_report_db()
        get_spiders_from_cloud()
        now = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
        if excute_res1 and excute_res2 and excute_res3 and excute_res4 and excute_res5 and excute_res6:
            # print("[{}] 补丁执行成功。".format(now))
            print(tool.getMsg("TIPS_PATCH_SUCCESSFUL", args=(now,)))
        else:
            # print("优化数据结构:{}".format(excute_res1))
            print(tool.getMsg("TIPS_OPTIMIZE_RESULT", args=(excute_res1,)))
            # print("同步数据:{}".format(excute_res2))
            print(tool.getMsg("TIPS_SYNC_RESULT", args=(excute_res2,)))
            # print("同步配置:{}".format(excute_res3))
            print(tool.getMsg("TIPS_SYNC_SETTING_RESULT", args=(excute_res3,)))
            # print("写入白名单进程:{}".format(excute_res4))
            print(tool.getMsg("TIPS_WRITE_SETTINGS_RESULT", args=(excute_res4,)))
            # print("加入后台定时任务:{}".format(excute_res5))
            print(tool.getMsg("TIPS_ADD_BACKGROUND_TASK_RESULT", args=(excute_res5,)))
            # print("[{}] ******补丁执行失败！可能会影响到插件正常使用，请在https://www.bt.cn/bbs发帖或者联系开发者寻求支持。******".format(now))
            print(tool.getMsg("TIPS_SEPARATION_FAILURE", args=(excute_res6,)))
            print(tool.getMsg("TIPS_PATCH_FAILED", args=(now,)))
    except Exception as e:
        print(tool.getMsg("TIPS_PATCH_ERROR", args=(now, str(e),)))
    finally:
        if monitor_status and settings:
            settings = json.loads(public.readFile(config_path))
            global_settings = settings["global"]
            global_settings["monitor"] = True
            public.writeFile(config_path, json.dumps(settings))
            write_lua_config(settings)
            set_monitor_status(True)
            print(tool.getMsg("TIPS_MONITOR_OPENED"))