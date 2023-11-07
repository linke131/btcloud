#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# | Date: 2021/3/3 18:18
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表 - 数据迁移工具
# +--------------------------------------------------------------------
from __future__ import absolute_import, print_function, division
import os
import sys
import time
import json
import re
import sqlite3

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public
import total_tools as tool

data_dir = "/www/server/total"
logs_dir = data_dir + "/logs"
history_db_file = "logs.db"
isolation_level = "EXCLUSIVE"

class total_migrate:
    debug_mode = False

    def __get_file_json(self, filename, defaultv={}):
        try:
            if not os.path.exists(filename): return defaultv;
            return json.loads(public.readFile(filename))
        except:
            os.remove(filename)
            return defaultv

    def get_data_dir(self):
        settings = self.__get_file_json("/www/server/total/config.json")
        data_dir = None
        if settings:
            if "global" in settings:
                global_settings = settings["global"]
                data_dir = global_settings["data_dir"]
        if not data_dir:
            data_dir = logs_dir
        return data_dir

    def init_site_db(self, server_name, target_data_dir=None, db_name="logs.db"):
        self.init_logs_db(server_name, target_data_dir)
        self.init_total_db3(server_name, target_data_dir)

    def init_logs_db(self, server_name, target_data_dir=None):
        try:
            if target_data_dir is None:
                db_path = os.path.join(self.get_data_dir(), server_name, 'cursor_log')
            else:
                db_path = os.path.join(target_data_dir, server_name, 'cursor_log')

            if not os.path.exists(db_path):
                os.makedirs(db_path)

            db_name = tool.get_logs_db_name()
            db_file = os.path.join(db_path, db_name)

            if os.path.exists(db_file):
                return
            conn = sqlite3.connect(db_file, isolation_level=isolation_level)
            cur = conn.cursor()
            go_init = False
            results = cur.execute("SELECT name FROM sqlite_master where type='table'")
            tables = []
            for result in results:
                tables.append(result[0])
            # total_tables = ["site_logs"]
            total_tables = ["request_headers", "uri_cursor", "ip_cursor", "user_agent", "request_uri", "error_logs", "referer"]
            # print(len(total_tables) == len(tables))
            for table in total_tables:
                if table not in tables:
                    go_init = True
                    # public.WriteLog("监控报表", "Table:{} 需要初始化。".format(table))
                    # print("监控报表", "Table:{} 需要初始化。".format(table))
                    break

            if not go_init: return

            # public.WriteLog("init check", "{}数据库需要初始化。".format(server_name))
            # print("{}数据库需要初始化。".format(server_name))
            cur.execute("PRAGMA synchronous = 0")
            cur.execute("PRAGMA page_size = 4096")
            cur.execute("PRAGMA journal_mode = wal")
            # cur.execute("PRAGMA wal_autocheckpoint = 1000")
            # cur.execute("PRAGMA journal_size_limit = 1073741824")
            # cur.execute("""CREATE TABLE site_logs (
    		# 	time INTEGER,
    		# 	ip TEXT,
    		# 	domain TEXT,
    		# 	server_name TEXT,
    		# 	method TEXT,
    		# 	status_code INTEGER,
    		# 	uri TEXT,
    		# 	body_length INTEGER,
    		# 	referer TEXT DEFAULT "",
    		# 	user_agent TEXT,
            #     is_spider INTEGER DEFAULT 0,
    		# 	protocol TEXT,
    		# 	request_time INTEGER,
            #     request_headers TEXT DEFAULT '',
            #     ip_list TEXT DEFAULT "",
            #     client_port INTEGER DEFAULT -1
            # )""")
            # cur.execute("CREATE INDEX time_inx ON site_logs(time)")
            cur.execute("""CREATE TABLE request_headers(
                         id CHAR(32) PRIMARY KEY,
                         request_headers TEXT DEFAULT ""
                     )""")

            cur.execute("""CREATE TABLE referer(
                          id CHAR(32) PRIMARY KEY,
                          referer TEXT DEFAULT ""
                              )""")

            cur.execute("""CREATE TABLE uri_cursor(
                  id INTEGER PRIMARY KEY,
                  cursor TEXT DEFAULT 's',
                  uri TEXT
              )""")

            cur.execute("""CREATE TABLE ip_cursor(
                  id INTEGER PRIMARY KEY,
                  cursor TEXT DEFAULT 's',
                  ip_list TEXT
              )""")

            cur.execute("""CREATE TABLE user_agent(
                  id INTEGER PRIMARY KEY,
                  user_agent TEXT DEFAULT ''
              )""")

            cur.execute("CREATE UNIQUE INDEX user_agent_inx on user_agent(user_agent)")

            cur.execute("""CREATE TABLE request_uri(
                 id INTEGER PRIMARY KEY,
                 request_uri TEXT DEFAULT ''
             )""")

            cur.execute("CREATE UNIQUE INDEX request_uri_inx on request_uri(request_uri)")

            cur.execute("""CREATE TABLE error_logs(
                status_code INTEGER PRIMARY KEY,
                cursor TEXT DEFAULT 's'
            )""")

            public.ExecShell("chown -R www:www "+db_path)
            public.ExecShell("chmod 755 "+db_file)
        except Exception as e:
            print("初始化日志数据库异常: {}".format(e))
        finally:
            try:
                cur and cur.close()
                conn and conn.close()
            except:
                pass

    def init_total_db3(self, server_name, target_data_dir=None):
        try:
            if target_data_dir is None:
                db_path = os.path.join(self.get_data_dir(), server_name)
            else:
                db_path = os.path.join(target_data_dir, server_name)

            if not os.path.exists(db_path):
                os.makedirs(db_path)

            db_name = "total.db"
            db_file = os.path.join(db_path, db_name)
            if os.path.exists(db_file):
                # print("文件已存在。")
                return
            conn = sqlite3.connect(db_file, isolation_level=isolation_level)
            cur = conn.cursor()
            go_init = False
            results = cur.execute("SELECT name FROM sqlite_master where type='table'")
            tables = []
            for result in results:
                tables.append(result[0])
            total_tables = ["request_stat", "client_stat", "spider_stat", "ip_stat", "uri_stat", "referer2_stat"]
            # print(len(total_tables) == len(tables))
            for table in total_tables:
                if table not in tables:
                    go_init = True
                    # public.WriteLog("监控报表", "Table:{} 需要初始化。".format(table))
                    print("监控报表", "Table:{} 需要初始化。".format(table))
                    break

            if not go_init: return

            # public.WriteLog("init check", "{}数据库需要初始化。".format(server_name))
            # print("{}数据库需要初始化。".format(server_name))
            cur.execute("PRAGMA synchronous = 0")
            cur.execute("PRAGMA page_size = 4096")
            cur.execute("PRAGMA journal_mode = wal")

            cur.execute("""
            CREATE TABLE client_stat(
    				time INTEGER PRIMARY KEY,
    				weixin INTEGER DEFAULT 0,
    				android INTEGER DEFAULT 0,
    				iphone INTEGER DEFAULT 0,
    				mac INTEGER DEFAULT 0,
    				windows INTEGER DEFAULT 0,
    				linux INTEGER DEFAULT 0,
    				edeg INTEGER DEFAULT 0,
    				firefox INTEGER DEFAULT 0,
    				msie INTEGER DEFAULT 0,
    				metasr INTEGER DEFAULT 0,
    				qh360 INTEGER DEFAULT 0,
    				theworld INTEGER DEFAULT 0,
    				tt INTEGER DEFAULT 0,
    				maxthon INTEGER DEFAULT 0,
    				opera INTEGER DEFAULT 0,
    				qq INTEGER DEFAULT 0,
    				uc INTEGER DEFAULT 0,
    				pc2345 INTEGER DEFAULT 0, 
    				safari INTEGER DEFAULT 0,
    				chrome INTEGER DEFAULT 0,
    				machine INTEGER DEFAULT 0,
    				other INTEGER DEFAULT 0,
                    mobile INTEGER DEFAULT 0
    			)
            """)
            cur.execute("""
            CREATE TABLE request_stat(
    				time INTEGER PRIMARY KEY,
    				req INTEGER DEFAULT 0,
    				pv INTEGER DEFAULT 0,
    				uv INTEGER DEFAULT 0,
    				ip INTEGER DEFAULT 0,
    				length INTEGER DEFAULT 0,
                    spider INTEGER DEFAULT 0,
                    fake_spider INTEGER DEFAULT 0,
                    status_500 INTEGER DEFAULT 0, 
                    status_501 INTEGER DEFAULT 0, 
                    status_502 INTEGER DEFAULT 0, 
                    status_503 INTEGER DEFAULT 0, 
                    status_504 INTEGER DEFAULT 0, 
                    status_505 INTEGER DEFAULT 0, 
                    status_506 INTEGER DEFAULT 0, 
                    status_507 INTEGER DEFAULT 0, 
                    status_509 INTEGER DEFAULT 0, 
                    status_510 INTEGER DEFAULT 0, 
                    status_400 INTEGER DEFAULT 0, 
                    status_401 INTEGER DEFAULT 0, 
                    status_402 INTEGER DEFAULT 0, 
                    status_403 INTEGER DEFAULT 0, 
                    status_404 INTEGER DEFAULT 0, 
                    status_405 INTEGER DEFAULT 0, 
                    status_406 INTEGER DEFAULT 0, 
                    status_407 INTEGER DEFAULT 0, 
                    status_408 INTEGER DEFAULT 0, 
                    status_409 INTEGER DEFAULT 0, 
                    status_410 INTEGER DEFAULT 0, 
                    status_411 INTEGER DEFAULT 0, 
                    status_412 INTEGER DEFAULT 0, 
                    status_413 INTEGER DEFAULT 0, 
                    status_414 INTEGER DEFAULT 0, 
                    status_415 INTEGER DEFAULT 0, 
                    status_416 INTEGER DEFAULT 0, 
                    status_417 INTEGER DEFAULT 0, 
                    status_418 INTEGER DEFAULT 0, 
                    status_421 INTEGER DEFAULT 0, 
                    status_422 INTEGER DEFAULT 0, 
                    status_423 INTEGER DEFAULT 0, 
                    status_424 INTEGER DEFAULT 0, 
                    status_425 INTEGER DEFAULT 0, 
                    status_426 INTEGER DEFAULT 0, 
                    status_449 INTEGER DEFAULT 0, 
                    status_451 INTEGER DEFAULT 0, 
                    status_499 INTEGER DEFAULT 0,
                    http_get INTEGER DEFAULT 0, 
                    http_post INTEGER DEFAULT 0, 
                    http_put INTEGER DEFAULT 0, 
                    http_patch INTEGER DEFAULT 0, 
                    http_delete INTEGER DEFAULT 0)
    			""")

            cur.execute("""
            CREATE TABLE spider_stat(
    				time INTEGER PRIMARY KEY,
    				bytes INTEGER DEFAULT 0,
    				bing INTEGER DEFAULT 0,
    				soso INTEGER DEFAULT 0,
    				yahoo INTEGER DEFAULT 0,
    				sogou INTEGER DEFAULT 0,
    				google INTEGER DEFAULT 0,
    				baidu INTEGER DEFAULT 0,
    				qh360 INTEGER DEFAULT 0,
    				youdao INTEGER DEFAULT 0,
    				yandex INTEGER DEFAULT 0,
    				dnspod INTEGER DEFAULT 0,
    				yisou INTEGER DEFAULT 0,
                    mpcrawler INTEGER DEFAULT 0,
                    duckduckgo INTEGER DEFAULT 0,
                    bytes_flow INTEGER DEFAULT 0, 
                    bing_flow INTEGER DEFAULT 0, 
                    soso_flow INTEGER DEFAULT 0, 
                    yahoo_flow INTEGER DEFAULT 0, 
                    sogou_flow INTEGER DEFAULT 0, 
                    google_flow INTEGER DEFAULT 0, 
                    baidu_flow INTEGER DEFAULT 0, 
                    qh360_flow INTEGER DEFAULT 0, 
                    youdao_flow INTEGER DEFAULT 0, 
                    yandex_flow INTEGER DEFAULT 0, 
                    dnspod_flow INTEGER DEFAULT 0, 
                    yisou_flow INTEGER DEFAULT 0, 
                    other_flow INTEGER DEFAULT 0, 
                    mpcrawler_flow INTEGER DEFAULT 0, 
                    duckduckgo_flow INTEGER DEFAULT 0,
    				other INTEGER DEFAULT 0
    			)""")

            cur.execute("""
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
					flow31 INTEGER DEFAULT 0,
                    spider_flow1 INTEGER DEFAULT 0,
					spider_flow2 INTEGER DEFAULT 0,
					spider_flow3 INTEGER DEFAULT 0,
					spider_flow4 INTEGER DEFAULT 0,
					spider_flow5 INTEGER DEFAULT 0,
					spider_flow6 INTEGER DEFAULT 0,
					spider_flow7 INTEGER DEFAULT 0,
					spider_flow8 INTEGER DEFAULT 0,
					spider_flow9 INTEGER DEFAULT 0,
					spider_flow10 INTEGER DEFAULT 0,
					spider_flow11 INTEGER DEFAULT 0,
					spider_flow12 INTEGER DEFAULT 0,
					spider_flow13 INTEGER DEFAULT 0,
					spider_flow14 INTEGER DEFAULT 0,
					spider_flow15 INTEGER DEFAULT 0,
					spider_flow16 INTEGER DEFAULT 0,
					spider_flow17 INTEGER DEFAULT 0,
					spider_flow18 INTEGER DEFAULT 0,
					spider_flow19 INTEGER DEFAULT 0,
					spider_flow20 INTEGER DEFAULT 0,
					spider_flow21 INTEGER DEFAULT 0,
					spider_flow22 INTEGER DEFAULT 0,
					spider_flow23 INTEGER DEFAULT 0,
					spider_flow24 INTEGER DEFAULT 0,
					spider_flow25 INTEGER DEFAULT 0,
					spider_flow26 INTEGER DEFAULT 0,
					spider_flow27 INTEGER DEFAULT 0,
					spider_flow28 INTEGER DEFAULT 0,
					spider_flow29 INTEGER DEFAULT 0,
					spider_flow30 INTEGER DEFAULT 0,
					spider_flow31 INTEGER DEFAULT 0,
                    day_hour1 INTEGER DEFAULT 0,
                    flow_hour1 INTEGER DEFAULT 0,
                    spider_flow_hour1 INTEGER DEFAULT 0
				)""")
            cur.execute("""CREATE TABLE ip_stat(
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
					flow31 INTEGER DEFAULT 0,
                    day_hour1 INTEGER DEFAULT 0,
                    flow_hour1 INTEGER DEFAULT 0
				)""")

            cur.execute("""CREATE TABLE referer2_stat(
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
                flow31 INTEGER DEFAULT 0,
                day_hour1 INTEGER DEFAULT 0,
                flow_hour1 INTEGER DEFAULT 0
			)""")

            # print("调整新数据目录权限：")
            public.ExecShell("chown -R www:www "+db_path)
            public.ExecShell("chmod 755 "+db_file)
            return True
        except KeyError as e:

            print("监控报表", "初始化数据库异常: {}".format(str(e)))
        finally:
            try:
                if cur:
                    cur.close()
                if conn:
                    conn.close()
            except:
                pass
        return False

    def migrate_spider_total(self, site_name):
        data_path = "/www/server/total/total/{}/spider/".format(site_name)
        if not os.path.isdir(data_path):
            # print("目录: {}为空。".format(data_path))
            return
        db_path = "/www/server/total/logs/{}/logs.db".format(site_name)
        if not os.path.isfile(db_path):
            self.init_site_db(site_name)

        new_spiders_config = "/www/server/total/config/spiders.json"
        new_spiders = json.loads(public.readFile(new_spiders_config))

        for json_file in os.listdir(data_path):
            if not json_file.endswith(".json"): continue
            data = {}
            ts = None
            conn = None
            try:
                data_file = os.path.join(data_path, json_file)
                self.write_progress(site_name, data_file)
                if self.is_completed(data_file):
                    print("文件: {}已迁移过。".format(data_file))
                    continue
                if json_file == "total.json":
                    data = json.loads(public.readFile(data_file))
                    # with open(data_file, "r", encoding="gb18030") as fp:
                    #     data = json.load(fp)
                    total = 0
                    for spider, num in data.items():
                        total += num
                    total_sql = "UPDATE total_stat SET spider=spider+{num} where id=1".format(
                        num=total)

                    print("总计:", str(num))
                    total_db = sqlite3.connect(total_db_path, isolation_level=isolation_level)
                    total_cur = total_db.cursor()
                    total_cur.execute(total_sql)
                    total_db.commit()
                    total_cur.close()
                    total_db.close()
                    self.mark_complete(data_file)
                    continue

                file_name = os.path.splitext(json_file)[0]
                time_key = 0
                try:
                    _time = time.strptime(file_name, "%Y-%m-%d")
                    time_key = time.strftime("%Y%m%d", _time)
                except Exception as e:
                    print(e)
                    print("无法解释文件名:", file_name)
                    continue

                print("正在迁移文件: ", json_file)
                # ts = tsqlite()
                # ts.dbfile(db_path)
                file_content = public.readFile(data_file).strip()
                if not file_content:
                    self.mark_complete(data_file)
                    continue
                conn = sqlite3.connect(db_path, isolation_level=isolation_level)
                ts = conn.cursor()
                ts.execute("BEGIN TRANSACTION;")
                data = json.loads(file_content)
                # with open(data_file, "r", encoding="gb18030") as fp:
                #     data = json.load(fp)
                for hour, total in data.items():
                    _time_key = time_key + hour
                    update_sql = "INSERT INTO {table}(time) SELECT {time} WHERE NOT EXISTS(SELECT time FROM {table} WHERE time={time});"
                    update_sql = update_sql.format(table="spider_stat",
                                                   time=_time_key)
                    ts.execute(update_sql)
                    for spider, num in total.items():
                        # print("spider:", spider)
                        for new_spider in new_spiders:
                            if re.search(new_spider["pattern"], spider):
                                # print("new_spider:", new_spider)
                                sql = "UPDATE {table} SET {spider}={spider}+{num} WHERE time={time_key};"
                                sql = sql.format(table="spider_stat",
                                           spider=new_spider["column"],
                                           num=num,
                                           time_key=_time_key)
                                ts.execute(sql)
                                break
                ts.execute("COMMIT;")
            except KeyError as e:
                print(e)
            else:
                self.mark_complete(data_file)
            finally:
                if ts:
                    ts.close()
                if conn:
                    conn.close()


    def migrate_request_total(self, site_name):
        data_path = "/www/server/total/total/{}/request/".format(site_name)
        if not os.path.isdir(data_path):
            # print("目录: {}为空。".format(data_path))
            return
        db_path = "/www/server/total/logs/{}/logs.db".format(site_name)
        if not os.path.isfile(db_path):
            self.init_site_db(site_name)

        columns = ["ip", "pv", "uv"]
        http_methods = ["get", "post", "put", "patch", "delete"]

        total_stat = { "req":0, "pv":0, "uv":0, "ip":0}
        for json_file in os.listdir(data_path):


            if not json_file.endswith(".json"): continue
            data = {}
            ts = None
            conn = None
            try:
                data_file = os.path.join(data_path, json_file)
                self.write_progress(site_name, data_file)
                if self.is_completed(data_file):
                    print("文件: {}已迁移过。".format(data_file))
                    continue
                if json_file == "total.json":
                    continue

                file_name = os.path.splitext(json_file)[0]
                time_key = 0
                try:
                    _time = time.strptime(file_name, "%Y-%m-%d")
                    time_key = time.strftime("%Y%m%d", _time)
                except Exception as e:
                    print(e)
                    print("无法解释文件名:", file_name)
                    continue

                print("正在迁移文件: ", json_file)
                file_content = public.readFile(data_file).strip()
                if not file_content:
                    self.mark_complete(data_file)
                    continue
                # ts = tsqlite()
                # ts.dbfile(db_path)
                conn = sqlite3.connect(db_path, isolation_level=isolation_level)
                ts = conn.cursor()
                ts.execute("BEGIN TRANSACTION;")
                data = json.loads(file_content)
                # with open(data_file, "r", encoding="gb18030") as fp:
                #     data = json.load(fp)
                for item, num in data.items():
                        if item.lower() in columns:
                            if item.lower() not in total.keys():
                                total[item.lower()] = num
                            else:
                                total[item.lower()] = total[item.lower()] + num
                for hour, total in data.items():
                    _request_num = 0
                    _time_key = time_key + hour
                    update_sql = "INSERT INTO {table}(time) SELECT {time} WHERE NOT EXISTS(SELECT time FROM {table} WHERE time={time});"
                    update_sql = update_sql.format(table="request_stat",
                                                   time=_time_key)
                    ts.execute(update_sql)

                    sql = "UPDATE {table} SET {column}={column}+{num} WHERE time={time_key};"
                    for item, num in total.items():
                        if item.lower() in columns:
                            total_stat[item.lower()] = total_stat[item.lower()] + num
                            _sql = sql.format(table="request_stat",
                                           column=item.lower(),
                                           num=num,
                                           time_key=_time_key)
                            ts.execute(_sql)
                        if item.lower() in http_methods:
                            _request_num += num
                    _sql = sql.format(table="request_stat",
                        column="req",
                        num=_request_num,
                        time_key=_time_key)

                    total_stat["req"] = total_stat["req"] + _request_num
                    ts.execute(_sql)

                ts.execute("COMMIT;")
            except RuntimeError as e:
                print(e)

            else:
                self.mark_complete(data_file)
            finally:
                if ts:
                    ts.close()
                if conn:
                    conn.close()

        total_sql = "UPDATE total_stat SET "
        fields = ""
        for key, value in total_stat.items():
            if fields:
                fields += ","
            fields += "{column}={column}+{value}".format(column=key, value=value)
        total_sql += fields + " where id=1;"

        # print("总计:", str(total_stat))
        # print("总计SQL:", total_sql)
        total_db = sqlite3.connect(total_db_path, isolation_level=isolation_level)
        total_cur = total_db.cursor()
        total_cur.execute(total_sql)
        total_db.commit()
        total_cur.close()
        total_db.close()


    def migrate_network_total(self, site_name):
        data_path = "/www/server/total/total/{}/network/".format(site_name)
        if not os.path.isdir(data_path):
            # print("目录: {}为空。".format(data_path))
            return
        db_path = "/www/server/total/logs/{}/logs.db".format(site_name)
        if not os.path.isfile(db_path):
            self.init_site_db(site_name)

        for json_file in os.listdir(data_path):
            if not json_file.endswith(".json"): continue
            data = {}
            ts = None
            conn = None
            try:
                data_file = os.path.join(data_path, json_file)
                self.write_progress(site_name, data_file)
                if self.is_completed(data_file):
                    print("文件: {}已迁移过。".format(data_file))
                    continue
                if json_file == "total.json":
                    data = json.loads(public.readFile(data_file))
                    # with open(data_file, "r", encoding="gb18030") as fp:
                    #     data = json.load(fp)
                    total = int(data)
                    total_sql = "UPDATE total_stat SET length=length+{num} where id=1".format(
                        num=total)
                    print("总计:", str(total))
                    total_db = sqlite3.connect(total_db_path, isolation_level=isolation_level)
                    total_cur = total_db.cursor()
                    total_cur.execute(total_sql)
                    total_db.commit()
                    total_cur.close()
                    total_db.close()
                    self.mark_complete(data_file)
                    continue

                file_name = os.path.splitext(json_file)[0]
                time_key = 0
                try:
                    _time = time.strptime(file_name, "%Y-%m-%d")
                    time_key = time.strftime("%Y%m%d", _time)
                except Exception as e:
                    print(e)
                    print("无法解释文件名:", file_name)
                    continue

                print("正在迁移文件: ", json_file)
                # ts = tsqlite()
                # ts.dbfile(db_path)
                file_content = public.readFile(data_file).strip()
                if not file_content:
                    self.mark_complete(data_file)
                    continue
                conn = sqlite3.connect(db_path, isolation_level=isolation_level)
                ts = conn.cursor()
                ts.execute("BEGIN TRANSACTION;")
                data = json.loads(file_content)
                # with open(data_file, "r", encoding="gb18030") as fp:
                #     data = json.load(fp)
                for hour, num in data.items():
                    _time_key = time_key + hour
                    update_sql = "INSERT INTO {table}(time) SELECT {time} WHERE NOT EXISTS(SELECT time FROM {table} WHERE time={time});"
                    update_sql = update_sql.format(table="request_stat",
                                                   time=_time_key)
                    ts.execute(update_sql)
                    sql = "UPDATE {table} SET {column}={column}+{num} WHERE time={time_key};"
                    sql = sql.format(table="request_stat",
                                    column="length",
                                    num=num,
                                    time_key=_time_key)
                    ts.execute(sql)
                ts.execute("COMMIT;")
            except RuntimeError as e:
                print(e)
            else:
                self.mark_complete(data_file)
            finally:
                if ts:
                    ts.close()
                if conn:
                    conn.close()


    def migrate_client_total(self, site_name):
        data_path = "/www/server/total/total/{}/client/".format(site_name)
        if not os.path.isdir(data_path):
            # print("目录: {}为空。".format(data_path))
            return
        db_path = "/www/server/total/logs/{}/logs.db".format(site_name)
        if not os.path.isfile(db_path):
            self.init_site_db(site_name)

        client_json = "/www/server/total/config/clients.json"
        _clients = json.loads(public.readFile(client_json))
        clients = []
        for _cls, clist in _clients.items():
            for c in clist:
                clients.append(c)

        for json_file in os.listdir(data_path):
            if not json_file.endswith(".json"): continue
            data = {}
            conn = None
            ts = None
            try:
                data_file = os.path.join(data_path, json_file)
                self.write_progress(site_name, data_file)
                if self.is_completed(data_file):
                    print("文件:{} 已迁移过。".format(data_file))
                    continue
                if json_file == "total.json":
                    continue

                file_name = os.path.splitext(json_file)[0]
                time_key = 0
                try:
                    _time = time.strptime(file_name, "%Y-%m-%d")
                    time_key = time.strftime("%Y%m%d", _time)
                except Exception as e:
                    print(e)
                    print("无法解释文件名:", file_name)
                    continue

                print("正在迁移文件: ", json_file)
                # ts = tsqlite()
                # ts.dbfile(db_path)
                file_content = public.readFile(data_file).strip()
                if not file_content:
                    self.mark_complete(data_file)
                    continue
                conn = sqlite3.connect(db_path, isolation_level=isolation_level)
                ts = conn.cursor()
                ts.execute("BEGIN TRANSACTION;")
                data = json.loads(file_content)
                # with open(data_file, "r", encoding="gb18030") as fp:
                #     data = json.load(fp)
                for hour, client_data in data.items():
                    _time_key = time_key + hour
                    update_sql = "INSERT INTO {table}(time) SELECT {time} WHERE NOT EXISTS(SELECT time FROM {table} WHERE time={time});"
                    _sql = update_sql.format(table="client_stat", time=_time_key)
                    ts.execute(_sql)
                    for client, num in client_data.items():
                        column = ""
                        for cli in clients:
                            if re.search(cli["pattern"], client):
                                column = cli["column"]
                                break
                            if client == "Mac OS X":
                                column = "mac"
                                break
                        if column:
                            # print("client:", column, num)
                            sql = "UPDATE {table} SET {column}={column}+{num} WHERE time={time_key};"
                            sql = sql.format(table="client_stat", column=column, num=num, time_key=_time_key)
                            ts.execute(sql)

                ts.execute("COMMIT;")
            except RuntimeError as e:
                print(e)
            else:
                self.mark_complete(data_file)
            finally:
                if ts:
                    ts.close()
                if conn:
                    conn.close()

    migrate_logs = {}
    def mark_complete(self, file):
        log_path = "/www/server/panel/plugin/total/migrate.log"
        origin_content = ""
        if os.path.isfile(log_path):
            origin_content = public.readFile(log_path)
        public.writeFile(log_path, origin_content + file +"\n")
        # with open(log_path, "a", encoding="gb18030") as fp:
        #     fp.write(file+"\n")
        self.migrate_logs[file] = True

    def is_completed(self, file):
        log_path = "/www/server/panel/plugin/total/migrate.log"
        if not os.path.isfile(log_path):
            return False
        if not self.migrate_logs:
            lines = public.readFile(log_path)
            if lines:
                lines = lines.split("\n")
                for line in lines:
                    self.migrate_logs[line.strip()] = True
        if file in self.migrate_logs.keys():
            return True
        return False

    def write_progress(self, site, file):
        progress_file = "/www/server/panel/plugin/total/migrate_progress.log"
        progress = "{},{}".format(site, file)
        public.writeFile(progress_file, progress)

    def set_migrate_status(self, status):
        status_file = "/www/server/panel/plugin/total/migrate_status.log"
        public.writeFile(status_file, status)

    def get_migrate_status(self):
        status_file = "/www/server/panel/plugin/total/migrate_status.log"
        site = ""
        file = ""
        status = ""
        if not os.path.isfile(status_file):
            status = "unknown"
        else:
            status = public.readFile(status_file)
            progress_file = "/www/server/panel/plugin/total/migrate_progress.log"
            progress = public.readFile(progress_file)
            if progress and progress.find(",")>=0:
                site = progress.split(",")[0]
                file = progress.split(",")[1]
        data = {
            "status": status,
            "site": site,
            "file": file
        }
        return data

    def init_all_db(self):
        sites = public.M('sites').field('name').order("addtime").select()
        for site_info in sites:
            site = site_info["name"]
            db_path = "/www/server/total/logs/{}".format(site)
            db_file = db_path + "/logs.db"
            if not os.path.isfile(db_path):
                self.init_site_db(site)
        # self.init_total_db3()

    def migrate_total(self):
        """迁移所有站点统计数据 """
        print("正在迁移旧版插件统计数据到新版本...")
        print("本次迁移可能会耗费较长时间(与数据量、站点数量相关)，请耐心等待。")
        status = self.get_migrate_status()
        if status["status"] == "completed":
            print("数据已迁移。")
            return
        self.init_all_db()
        check_path = "/www/server/total/total"
        if not os.path.isdir(check_path) or public.get_path_size(check_path) == 0:
            print("数据为空。")
            self.set_migrate_status("completed")
            return
        migrating_file = "/www/server/total/migrating"
        try:
            public.writeFile(migrating_file, "migrating")
            config_db = "/www/server/panel/data/default.db"
            if not os.path.isfile(config_db):
                return public.returnMsg(False, "default.db不存在。")

            self.set_migrate_status("migrating")
            sites = public.M('sites').field('name').order("addtime").select()
            for site in sites:
                site_name = site["name"]
                import time
                s = time.time()
                print("正在迁移站点:"+ site_name)
                # 迁移spider_stat数据
                self.migrate_spider_total(site_name)
                # 迁移request_stat数据
                self.migrate_request_total(site_name)
                # 迁移request_stat表length数据
                self.migrate_network_total(site_name)
                # 迁移client_stat数据
                self.migrate_client_total(site_name)
                e = time.time()
                diff = e - s
                if diff > 59:
                    print("站点:{} 数据迁移完成，耗时:{}分{}秒".format(site_name, int(diff/60), round(diff%60)))
                else:
                    print("站点:{} 数据迁移完成，耗时:{}秒".format(site_name, round(diff)))
            progress_file = "/www/server/panel/plugin/total/migrate_progress.log"
            if os.path.isfile(progress_file):
                os.remove(progress_file)
            self.set_migrate_status("completed")
        except RuntimeError as e:
            print("迁移站点出现错误:", str(e))
        finally:
            if os.path.isfile(migrating_file):
                # print("删除迁移状态文件...")
                os.remove(migrating_file)

    def migrate_hot_logs(self, query_date="today"):
        sites = public.M('sites').field('name').order("addtime").select();
        for site_info in sites:
            site_name = tool.get_site_name(site_info['name'])
            migrate_res = self.migrate_site_hot_logs(site_name, query_date)
            if not migrate_res["status"]:
                print(migrate_res["msg"])
                return False
        return True

    def debug(self, msg):
        if self.debug:
            print(msg)

    def migrate_site_hot_logs(self, site_name, query_date="today"):
        """迁移最新的日志到历史数据"""

        self.debug_mode = True

        flag_file = "/www/server/panel/plugin/total/split_failed.pl"
        if os.path.exists(flag_file):
            os.remove(flag_file)

        data_dir = tool.get_data_dir()
        hot_db_tmp = os.path.join(data_dir, site_name, "logs_tmp.db")
        hot_db = tool.get_log_db_path(site_name)
        if not os.path.exists(hot_db):
            self.init_site_db(site_name)

        history_logs_db = tool.get_log_db_path(site_name, history=True)
        from total_patch import check_history_db, split_site_data
        if not check_history_db(site_name):
            print("待初始化history logs db.")
            # self.init_site_db(site_name, target_data_dir=tool.get_history_data_dir(), db_name="history_logs.db")
            split_site_data(site_name)

        migrating_flag = "/www/server/total/logs/%s/migrating" % site_name

        # 1. 拷贝一份临时文件
        try:
            import shutil
            self.debug("正在拷贝{} 到 {}...".format(hot_db, hot_db_tmp))
            public.writeFile(migrating_flag, "yes")
            shutil.copy(hot_db, hot_db_tmp)
            if not os.path.exists(hot_db_tmp):
                return public.returnMsg(False, "迁移数据失败，无法拷贝临时文件。")
        except:
            return public.returnMsg(False, "{} 迁移数据失败，拷贝临时文件出错。".format(site_name))
        finally:
            if os.path.exists(migrating_flag):
                os.remove(migrating_flag)

        # 2. 从临时备份中迁移热日志数据到历史日志
        self.debug("开始从备份日志中迁移热数据...")
        his_conn = None
        his_cur = None
        hot_tmp_conn = None
        hot_tmp_cur = None
        try:
            print("历史日志数据文件: {}".format(history_logs_db))
            his_conn = sqlite3.connect(history_logs_db)
            his_cur = his_conn.cursor()

            hot_tmp_conn = sqlite3.connect(hot_db_tmp)
            if sys.version_info[0] == 3:
                hot_tmp_conn.text_factory = lambda x: str(x, encoding="utf-8", errors='ignore')
            else:
                hot_tmp_conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
            hot_tmp_cur = hot_tmp_conn.cursor()

            host_db_columns_selector = hot_tmp_cur.execute("PRAGMA table_info([site_logs])")
            hot_db_columns = ",".join([c[1] for c in host_db_columns_selector if c[1]!="id"])
            # print("site log columns:")
            # print(hot_db_columns)

            # select strftime('%Y-%m-%d', datetime(time, 'unixepoch', 'localtime')) as time1 from site_logs group by time1;
            query_start, query_end = tool.get_query_timestamp("today")

            logs_sql = "select {} from site_logs where time<{};".format(hot_db_columns, query_start)
            selector = hot_tmp_cur.execute(logs_sql)
            log = selector.fetchone()
            while log:
                params = ""
                for field in log:
                    if params:
                        params += ","
                    if field is None:
                        field = "\'\'"
                    elif type(field) == str:
                        field = "\'" + field.replace("\'", "\”") + "\'"
                    params += str(field)
                insert_sql = "insert into site_logs("+hot_db_columns+") values("+params+")"
                his_cur.execute(insert_sql)
                log = selector.fetchone()

            # 3. 删除保存天数以外的历史数据
            site_config = tool.get_site_settings("global")
            save_day = site_config["save_day"]
            self.debug("删除{}天以前的历史数据...".format(save_day))
            time_now = time.localtime()
            save_timestamp = time.mktime((time_now.tm_year, time_now.tm_mon, time_now.tm_mday - save_day, 0,0,0,0,0,0))
            delete_sql = "delete from site_logs where time <= {}".format(save_timestamp)
            his_cur.execute(delete_sql)

            his_conn.commit()

            # 4. 最耗时操作：整理历史部分的数据
            self.debug("正在整理历史数据, 此动作耗时较长...")
            his_conn.execute("VACUUM;")

            hot_tmp_cur and hot_tmp_cur.close()
            hot_tmp_conn and hot_tmp_conn.close()
            his_cur and his_cur.close()
            his_conn and his_conn.close()

            hot_tmp_cur = None
            hot_tmp_conn = None
            his_cur = None
            his_conn = None

            # 5. 删除已合并的数据、清理统计数据
            hot_conn = None
            hot_cur = None
            try:
                migrating_flag = "/www/server/total/logs/%s/migrating" % site_name
                self.debug("删除已合并的热数据...")
                public.writeFile(migrating_flag, "yes")
                hot_conn = sqlite3.connect(hot_db)
                hot_cur = hot_conn.cursor()

                hot_cur.execute("delete from site_logs where time<{}".format(query_start))

                # 统计数据暂时保留180天
                self.debug("正在删除超过180天的统计数据...")
                total_data_save_timestamp = time.mktime((time_now.tm_year, time_now.tm_mon, time_now.tm_mday - 180, 0,0,0,0,0,0))
                save_date = time.localtime(total_data_save_timestamp)
                save_time_key = tool.get_time_key(save_date)

                delete_request_stat_sql = "delete from request_stat where time<={}".format(save_time_key)
                hot_cur.execute(delete_request_stat_sql)

                hot_cur.execute("delete from spider_stat where time<={}".format(save_time_key))
                hot_cur.execute("delete from client_stat where time<={}".format(save_time_key))
                hot_cur.execute("delete from referer_stat where time<={}".format(save_time_key))

                hot_conn.commit()
                self.debug("清理热数据库...")
                hot_conn.execute("VACUUM;")
                # TODO: 清理统计数据
            except:
                return public.returnMsg(False, "{} 删除热数据出错！".format(site_name))
            finally:
                hot_cur and hot_cur.close()
                hot_conn and hot_conn.close()

                hot_cur = None
                hot_conn = None

                if os.path.exists(migrating_flag):
                    os.remove(migrating_flag)
        except Exception as e:
            if site_name:
                print("{} 日志合并到历史日志出现错误：{}".format(site_name, e))
            else:
                print("日志合并到历史日志出现错误：{}".format(e))
        finally:
            hot_tmp_cur and hot_tmp_cur.close()
            hot_tmp_conn and hot_tmp_conn.close()
            his_cur and his_cur.close()
            his_conn and his_conn.close()

            if os.path.exists(hot_db_tmp):
                os.remove(hot_db_tmp)

        self.debug("{} 迁移日志完成。".format(site_name))
        return public.returnMsg(True, "{} 日志合并成功！".format(site_name))

if __name__ == "__main__":
    total_migrate().migrate_total()
    # total_migrate().init_total_db3("192.168.1.67")
    # total_migrate().migrate_site_hot_logs(site_name="192.168.1.61")
