# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: 1249648969@qq.com
# -------------------------------------------------------------------
# 数据库管理运维工具
# ------------------------------
import copy
import sys
sys.path.insert(0,"/www/server/panel/class")
sys.path.insert(0, "/www/server/panel")

import json
import os
import time
import re
import datetime
from typing import Tuple, Union


os.chdir("/www/server/panel")
import public
import panelMysql
import psutil
import data
import crontab
import db
import panelTask

class database_mater_main():
    old_path = "/tmp/bt_task_old2.json"
    index_optimization = "/tmp/index_optimization.log"
    execute_optimization_func = os.path.join(public.get_panel_path(), "plugin/database_mater/execute_func.py")

    # 解析扫描结果存放路径
    data_dir = os.path.join(public.get_setup_path(), 'database_mater')
    database_db_path = os.path.join(public.get_setup_path(), 'database_mater/data.db')
    config_path = os.path.join(public.get_setup_path(), 'database_mater/config.json')
    db_sql = None

    mysql_conf = "/etc/my.cnf"
    mysql_data = "/www/server/data"
    mysql_slow_log = "/www/server/data/mysql-slow.log"
    mysql_bin_backup = "/www/backup/mysql_bin_backup"

    __mysql_bin_log = "/www/server/mysql/bin/mysqlbinlog"

    slow_sql_table_name = f"slow_sql_{datetime.datetime.now().year}_{datetime.datetime.now().month}"
    slow_details_table_name = f"slow_details_{datetime.datetime.now().year}_{datetime.datetime.now().month}"
    index_log = "index_log"
    operate_log = "operate_log"


    run_status_list = [
        "Innodb_log_writes", # 向日志文件的物理写数量
        "Innodb_data_reads", # 从磁盘读取的InnoDB数据页数
        "Innodb_data_writes", # 写入磁盘的InnoDB数据页数
        "Innodb_dblwr_writes", # InnoDB双写缓冲区的写入次数
        "Max_used_connections", # 服务器运行期间使用的最大连接数
        "Com_commit", # 执行的COMMIT语句次数
        "Com_rollback", # 执行的ROLLBACK语句次数
        "Questions", # 收到的请求总数
        "Innodb_buffer_pool_reads", # 从磁盘读取到InnoDB缓冲池的页数
        "Innodb_buffer_pool_read_requests", # 请求从InnoDB缓冲池读取的次数
        "Innodb_buffer_pool_write_requests",  # InnoDB缓冲池的写请求次数
        "Key_reads", # 从磁盘读取的索引页数
        "Key_read_requests", # 请求从缓存读取的索引页数
        "Key_writes", # 写入磁盘的索引页数
        "Key_write_requests", # 请求写入磁盘的索引页数
        "Qcache_hits", # 查询缓存命中次数
        "Qcache_inserts", # 查询缓存插入次数
        "Bytes_received", # 接收到的总字节数
        "Bytes_sent", # 发送的总字节数
        "Aborted_clients", # 客户端连接异常终止的次数
        "Aborted_connects", # 由于连接错误导致的连接尝试失败的次数
        "Created_tmp_disk_tables", # 在磁盘上创建的临时表的数量
        "Created_tmp_tables", # 创建的临时表的数量
        "Innodb_buffer_pool_pages_dirty", # 当前在InnoDB缓冲池中脏页的数量
        "Opened_files", # 打开的文件数
        "Open_tables", # 当前打开的表数
        "Opened_tables", # 总共打开的表数
        "Select_full_join", # 执行的全表连接次数
        "Select_range_check", # 执行的范围检查次数
        "Sort_merge_passes", # 执行的排序合并次数
        "Table_locks_waited", # 等待表锁的次数
        "Threads_cached", # 缓存的线程数
        "Threads_connected", # 当前连接的线程数
        "Threads_created", # 创建的线程数
        "Threads_running", # 当前正在运行的线程数
        "Connections", # 成功建立的连接数
        "Uptime" # 服务器运行的时间（以秒为单位）
    ]

    def __init__(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if self.db_sql is None:
            self.db_sql = db.Sql().dbfile(self.database_db_path)
        if not os.path.isfile(self.config_path):
            public.writeFile(self.config_path, json.dumps({}))

        # 删除往期的
        table_list = self.db_sql.table("sqlite_master").field("name").where("type=?", ("table")).select()
        for table in table_list:
            if table == self.slow_sql_table_name: continue
            if table == self.slow_details_table_name: continue
            if not str(table).startswith("slow"): continue
            self.db_sql.execute(f"drop table {table}")

        # 慢查询表
        if self.db_sql.table("sqlite_master").where("type=? AND name=?", ("table", self.slow_sql_table_name)).count() == 0:
            create_sql = f"""
                CREATE TABLE "{self.slow_sql_table_name}" (
                      "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, -- 主键id
                      "db_name" TEXT, -- 数据库名称
                      "query_sql" TEXT -- 查询的sql语句
                ); -- 慢查询语句表
            """
            self.db_sql.execute(create_sql)
            self.db_sql.execute("PRAGMA foreign_keys = ON;")

        if self.db_sql.table("sqlite_master").where("type=? AND name=?", ("table", self.slow_details_table_name)).count() == 0:
            create_sql = f"""
                CREATE TABLE "{self.slow_details_table_name}" (
                      "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, -- 主键id
                      "sql_id" INTEGER, -- 所属sql的id
                      "user" TEXT, -- 查询的用户
                      "host" TEXT, -- 登录的地址
                      "query_time" REAL, -- 查询耗时
                      "lock_time" REAL, -- 锁表时间
                      "log_time" TEXT, -- 记录时间
                      "time_stamp" INTEGER, -- 执行时间
                      "rows_sent" INTEGER, -- 返回条数
                      "rows_examined" INTEGER, -- 扫描行数
                      "connect_id" INTEGER, -- 连接id
                      "status" INTEGER, -- 状态(0:未优化,1:已优化)
                      FOREIGN KEY (sql_id) REFERENCES {self.slow_sql_table_name} (id)
                )-- 慢查询语句出现时间详情表
            """
            self.db_sql.execute(create_sql)

        # 索引优化记录
        if self.db_sql.table("sqlite_master").where("type=? AND name=?", ("table", self.index_log)).count() == 0:
            create_sql = f"""
                CREATE TABLE "{self.index_log}" (
                      "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, -- 主键id
                      "db_name" TEXT, -- 所属数据库
                      "tb_name" TEXT, -- 表
                      "field" TEXT, -- 字段
                      "add_time" TEXT -- 添加时间
                )-- 索引优化记录
            """
            self.db_sql.execute(create_sql)

        # 操作日志
        if self.db_sql.table("sqlite_master").where("type=? AND name=?", ("table", self.operate_log)).count() == 0:
            create_sql = f"""
                CREATE TABLE "{self.operate_log}" (
                      "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, -- 主键id
                      "type" INTEGER, -- 类型 0 慢查询，1 binlog
                      "log" TEXT, -- 操作日志
                      "add_time" TEXT -- 添加时间
                )-- 慢查询语句出现时间详情表
            """
            self.db_sql.execute(create_sql)

        self.update_5_1()

    # 5.1 更新
    def update_5_1(self):
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'database_mater',)).count():
            return
        data_list = public.M('database_mater').select()
        for data in data_list:
            date_time = datetime.datetime.strptime(data["time"], "%Y-%m-%d:%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            if data.get("type") == "file":
                self.db_sql.table(self.operate_log).add("type,log,add_time", (1, data["ps"], date_time))
            else:
                self.db_sql.table(self.operate_log).add("type,log,add_time", (0, data["ps"], date_time))
        public.M('').execute("drop table database_mater")

    # 获取配置
    @classmethod
    def __get_conf(cls, name: Union[str, None]) -> dict:
        try:
            config = json.loads(public.readFile(cls.config_path))
        except:
            config = {
                "mysql_slow": {}
            }
        if name is not None:
            return config.get(name, {})
        return config

    # 保存配置
    @classmethod
    def __set_conf(cls, name: Union[str], info: dict):
        config = cls.__get_conf(None)
        if name is not None:
            config[name] = info
        public.writeFile(cls.config_path, json.dumps(config))

    # 获取数据库配置信息
    @classmethod
    def __get_mysql_info(cls):
        datadir = cls.mysql_data
        port = "3306"
        log_bin = "mysql-bin"

        public.CheckMyCnf()
        mycnf = public.readFile(cls.mysql_conf)

        obj = re.search("datadir\s*=\s*(.+)\n", mycnf)
        if obj: datadir = obj.group(1)
        obj = re.search("port\s*=\s*(\d+)\s*\n", mycnf)
        if obj: port = obj.group(1)
        obj = re.search("log-bin\s*=\s*(.+)\s*\n", mycnf)
        if obj: log_bin = obj.group(1)

        data = {
            "datadir": datadir,
            "port": port,
            "log-bin": log_bin,
        }
        return data

    # 获取当前数据库全局状态
    @classmethod
    def __get_show_global_status(cls) -> Union[dict, None]:
        """
        获取 Mysql 数据库全局状态
        @return:
        """
        data_list = panelMysql.panelMysql().query("show global status")
        
        if not isinstance(data_list, list):
            data_list = str(data_list)
            if data_list.find("2003"):
                return None
        result = {}
        for info in data_list:
            result[info[0]] = info[1]
        return result

    # 获取当前数据库系统变量
    @classmethod
    def __get_show_variables(cls) -> Union[dict, None]:
        """
        获取 Mysql 数据库系统变量
        @return:
        """
        data_list = panelMysql.panelMysql().query("show variables")
        if not isinstance(data_list, list):
            data_list = str(data_list)
            if data_list.find("2003"):
                return None
            
        result = {}
        for info in data_list:
            result[info[0]] = info[1]
        return result

    @classmethod
    def __get_old(cls) -> dict:
        if not os.path.exists(cls.old_path): return {}
        data = public.readFile(cls.old_path)
        if not data: return {}
        data = json.loads(data)
        if not data: return {}
        return data

    @classmethod
    def __get_cpu_time(cls):
        s = psutil.cpu_times()
        cpu_time = s.user + s.system + s.nice + s.idle
        return cpu_time

    @classmethod
    def __get_cpu_percent(cls, pid, cpu_times, cpu_time):
        old_info = cls.__get_old()
        percent = 0.00

        process_cpu_time = 0.00
        for s in cpu_times: process_cpu_time += s
        if old_info.get(pid) is None:
            return percent
        percent = round(100.00 * (process_cpu_time - old_info[pid]["cpu_time"]) / (cpu_time - old_info["cpu_time"]), 2)
        if percent > 0: return percent
        return 0.00

    @classmethod
    def __get_process_list(cls):
        processList = []
        new_info = {}
        new_info["cpu_time"] = cls.__get_cpu_time()
        new_info["time"] = time.time()

        # info = {}
        # info["activity"] = 0
        # info["cpu"] = 0.00
        # info["mem"] = 0
        # info["disk"] = 0
        status_ps = {"sleeping": "睡眠", "running": "活动"}
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
            except:
                continue
            with p.oneshot():
                if p.name() != "mysqld": continue
                tmp = {}
                p_mem = p.memory_full_info()
                if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: continue;
                pio = p.io_counters()
                p_cpus = p.cpu_times()
                tmp["create_time"] = int(p.create_time())
                tmp["memory_used"] = p_mem.uss


                old_info = cls.__get_old()
                cpu_percent = 0.00
                disk_io_write = 0
                disk_io_read = 0

                process_cpu_time = 0.00
                for s in p_cpus: process_cpu_time += s
                if old_info.get(pid) is not None:
                    cpu_percent = round(100.00 * (process_cpu_time - old_info[pid]["cpu_time"]) / (new_info["cpu_time"] - old_info["cpu_time"]), 2)

                    io_write_end = (pio.write_bytes - old_info[pid]["io_write"])
                    if io_write_end > 0:
                        disk_io_write = io_write_end / (time.time() - old_info["time"])

                    io_read_end = (pio.read_bytes - old_info[pid]["io_read"])
                    if io_read_end > 0:
                        disk_io_read = io_read_end / (time.time() - old_info["time"])
                tmp["cpu_percent"] = cpu_percent
                tmp["io_write_speed"] = disk_io_write
                tmp["io_read_speed"] = disk_io_read
            processList.append(tmp)
            del (p)
            del (tmp)
        if len(processList) == 0: return False
        return processList[0]

    @classmethod
    # 数据库大小
    def __get_mysql_size(cls):
        data_size = panelMysql.panelMysql().query("select concat(round(sum((data_length+index_length)/1024/1024),2),'MB') as data from information_schema.TABLES;")
        if len(data_size) == 0:
            return "0M"
        else:
            return data_size[0][0]

    @classmethod
    # 慢查询检查
    def __get_slow_info(cls):
        data = panelMysql.panelMysql().query("show variables like 'slow_query%'")
        result = {
            "slow_query_log": data[0],
            "slow_query_log_file": data[1],
        }
        return result

    # 设置慢查询
    @classmethod
    def __set_slow_info(cls):
        result = cls.__get_slow_info()
        if result["slow_query_log"] != "ON":
            panelMysql.panelMysql().query("set global slow_query_log='ON';")
            panelMysql.panelMysql().query("set global slow_query_log_file='/www/server/data/mysql-slow.log';")
            panelMysql.panelMysql().query("set global long_query_time=3;")
        return True

    # 获取 mysql 运行状态监控
    def get_run_status(self, get):

        show_global_status = self.__get_show_global_status()
        if show_global_status is None:
            return public.returnMsg(False, "数据库连接失败！请检查数据库状态！")
        result = {}
        for field in self.run_status_list:
            result[field] = show_global_status.get(field)

        result["Run"] = int(time.time()) - int(result["Uptime"])
        result["qps"] = int(result["Questions"]) / int(result["Uptime"])
        result["InnoDB_IO"] = int(result["Innodb_data_reads"]) + int(result["Innodb_data_writes"]) + int(result["Innodb_dblwr_writes"]) + int(result["Innodb_log_writes"])
        result["MyISAM_IO"] = int(result["Key_reads"]) * 2 + int(result["Key_writes"]) * 2 + int(result["Key_read_requests"]) * 2
        mysql_system = self.__get_process_list()
        result["mysql_create_time"] = mysql_system.get("create_time", int(time.time()))
        result["mysql_system_cpu"] = mysql_system.get("cpu_percent", 0)
        result["mysql_memory"] = mysql_system.get("memory_used", 0)
        result["mysql_io_write_speed"] = mysql_system.get("io_write_speed", 0)
        result["mysql_io_read_speed"] = mysql_system.get("io_read_speed", 0)

        result["mysql_count_size"] = self.__get_mysql_size()
        result["slow_query_log"] = self.__get_slow_info()
        data = panelMysql.panelMysql().query("show master status")
        result["File"] = data[0][0]
        result["Position"] = data[0][1]
        return {"status": True, "msg": "OK", "data": result}

    """综合评分"""
    # 综合评分
    """
    1.是否开启对外开放 10
    2.查询缓存是否启用 10
    3.查询缓存命中率 10
    4.没有使用索引的量 10
    5.Innodb索引命中率 10
    6.线程缓存命中率  10
    7.cpu 开销  10
    8.内存开销   10
    9.IO    10
    10.慢查询  10
    线程缓存命中率	  = ((1 - rdata.Threads_created / rdata.Connections) * 100).toFixed(2);
    索引命中率	= ((1 - rdata.Key_reads / rdata.Key_read_requests) * 100).toFixed(2);
    Innodb索引命中率	= ((1 - rdata.Innodb_buffer_pool_reads / rdata.Innodb_buffer_pool_read_requests) * 100).toFixed(2);
    查询缓存命中率	   =((parseInt(rdata.Qcache_hits) / (parseInt(rdata.Qcache_hits) + parseInt(rdata.Qcache_inserts))) * 100).toFixed(2) + '%';
    创建临时表到磁盘=((rdata.Created_tmp_disk_tables / rdata.Created_tmp_tables) * 100).toFixed(2);
    锁表次数  Table_locks_waited
    """
    def get_comprehensive_score(self, get):
        show_global_status = self.__get_show_global_status()
        show_variables_status = self.__get_show_variables()
        if show_global_status is None or show_variables_status is None:
            return public.returnMsg(False, "数据库连接失败！请检查数据库状态！")

        result = {
            "msg_list": [],
            "fraction": 100,
        }

        data = panelMysql.panelMysql().query("show master status")
        result["File"] = data[0][0]
        if data[0][0] == "OFF": public.returnMsg(False, "数据库未启动")


        # 1、3306端口
        port_open = public.M("firewall").where("port=?", ('3306',)).count()
        if port_open:
            result["fraction"] -= 10
            result["msg_list"].append("风险提醒【10分】：3306端口开启了对外连接")

        # 2、 对开开放的用户
        mysql_user_data = panelMysql.panelMysql().query("select User,Host from mysql.user where Host not in ('localhost','127.0.0.1')")
        if len(mysql_user_data) >= 1:
            result["fraction"] -= 10

            user_msg = []
            for i in mysql_user_data:
                user = i[0]
                host = i[1]
                if host == "%":
                    host = "所有人"
                msg = f"{user} 允许 【{host}】 连接"
                user_msg.append(msg)
            user_msg = "<br/>".join(user_msg)
            result["msg_list"].append(f"风险提醒【10分】：mysql 存在{len(mysql_user_data)}个对外开放的用户<br/>{user_msg}")

        # 3、查询缓存是否启用
        if show_variables_status:
            result["fraction"] -= 10
            result["msg_list"].append("风险提醒【10分】：查询缓存未启用。请在配置中配置query_cache_size该项")
        elif show_variables_status.get("query_cache_size") is not None and show_variables_status.get("query_cache_size") == 0:
            result["fraction"] -= 10
            result["msg_list"].append("风险提醒【10分】：查询缓存未启用。建议修改query_cache_size")

        # 4、线程缓存命中率
        # ((1 - rdata.Threads_created / rdata.Connections) * 100)
        if show_global_status.get("Threads_created") is not None and int(show_global_status.get("Connections", 0)) != 0:
            thread_cache_size = int((1 - int(show_global_status["Threads_created"]) / int(show_global_status["Connections"])) * 100)
            if thread_cache_size <= 50:
                result["fraction"] -= - 5
                result["msg_list"].append("风险提醒【5分】：线程缓存命中率小于百分之50,建议增加thread_cache_size")

        # 5、索引命中率
        if show_global_status.get("Key_reads") is not None and int(show_global_status.get("Key_read_requests", 0)) != 0:
            key_buffer_size = int((1 - int(show_global_status["Key_reads"]) / int(show_global_status["Key_read_requests"])) * 100)
            if key_buffer_size <= 30:
                result["fraction"] -= - 5
                result["msg_list"].append("风险提醒【5分】：索引命中率小于百分之30,建议增加key_buffer_size")

        # 6、Innodb索引命中率
        if show_global_status.get("Innodb_buffer_pool_reads") is not None and int(show_global_status.get("Innodb_buffer_pool_read_requests")) != 0:
            innodb_buffer_pool_size = int((1 - int(show_global_status["Innodb_buffer_pool_reads"]) / int(show_global_status["Innodb_buffer_pool_read_requests"])) * 100)
            if innodb_buffer_pool_size <= 50:
                result["fraction"] -= - 5
                result["msg_list"].append("风险提醒【5分】：Innodb索引命中率小于百分之50,建议增加innodb_buffer_pool_size")

        # 7\查询缓存命中率
        if show_global_status.get("Qcache_hits") is not None and show_global_status.get("Qcache_inserts") is not None:
            query_cache_size = int(float(show_global_status["Qcache_hits"]) / (float(show_global_status["Qcache_hits"]) + float(show_global_status["Qcache_inserts"])) * 100)
            if query_cache_size <= 20:
                result["fraction"] -= - 5
                result["msg_list"].append("风险提醒【5分】：查询缓存命中率小于百分之20,建议增加query_cache_size")

        # 8、创建临时表到磁盘
        if show_global_status.get("Created_tmp_disk_tables") is not None and int(show_global_status.get("Created_tmp_tables")) != 0:
            tmp_table_size = int((int(show_global_status["Created_tmp_disk_tables"]) / int(show_global_status["Created_tmp_tables"])) * 100)
            if tmp_table_size >= 50:
                result["fraction"] -= 5
                result["msg_list"].append("风险提醒【5分】：创建临时表到磁盘大于百分之50,建议增加tmp_table_size")

        return {"status": True, "msg": "OK", "data": result}

    """慢查询"""
    # 保存慢查询记录
    def __slave_slow(self, info_str: str):
        try:
            info_str = info_str.strip()
            log_time = re.search(r"#\s*Time:\s*(.*)\n", info_str).group(1)
            user_host_obj = re.search(r"#\s*User@Host:\s*(.*)\[(.*)\]\s*@\s*(localhost)?\s*\[(.*)\]\s*Id:\s*(.*)\n", info_str)
            user = user_host_obj.group(1)
            db_name = user_host_obj.group(2)
            is_localhost = user_host_obj.group(3)
            login_ip = user_host_obj.group(4)
            connect_id = user_host_obj.group(5)
            query_time_obj = re.search(r"#\s*Query_time:\s*(\d*\.?\d*)\s*Lock_time:\s*(\d*\.?\d*)\s*Rows_sent:\s*(\d*)\s*Rows_examined:\s*(\d*)\n", info_str)
            query_time = query_time_obj.group(1)
            lock_time = query_time_obj.group(2)
            rows_sent = query_time_obj.group(3)
            rows_examined = query_time_obj.group(4)
            time_stamp = re.search(r"SET\s*timestamp=(.*);\n", info_str).group(1)

            use_obj = re.search(r"use\s*`?(.*)`?;\n", info_str, re.I)
            if use_obj and db_name == "root":
                db_name = use_obj.group(1)

            query_sql = re.findall(r"select.*where.*;", info_str, re.I)[0]
            host = login_ip if is_localhost is None else is_localhost
            sql_info = self.db_sql.table(self.slow_sql_table_name).field("id").where("db_name=? and query_sql=?", (db_name, query_sql)).find()
            if not sql_info:
                sql_id = self.db_sql.table(self.slow_sql_table_name).add("db_name,query_sql",(db_name, query_sql))
            else:
                sql_id = sql_info["id"]
            self.db_sql.table(self.slow_details_table_name).add(
                "sql_id,user,host,query_time,lock_time,log_time,time_stamp,rows_sent,rows_examined,connect_id,status",
                (sql_id, user, host,  query_time, lock_time, log_time, time_stamp, rows_sent, rows_examined, connect_id, 0))
        except Exception as err:
            public.print_log(f">>err:{err}")


    # 解析慢查询日志
    def __analysis_slow_log(self):
        """
        解析慢查询日志
        @param get:
        @return:
        """
        mysql_slow = self.__get_conf("mysql_slow")
        last_analysis_datetime = mysql_slow.get("last_analysis_datetime")
        if last_analysis_datetime is not None:
            last_analysis_datetime = datetime.datetime.strptime(last_analysis_datetime, "%Y-%m-%d %H:%M:%S.%f")

        new_last_analysis_datetime = None
        blk_size_max = 4096
        with open(self.mysql_slow_log, 'r') as f:
            f.seek(0, os.SEEK_END)
            cur_pos = f.tell()
            log_data = ""

            while cur_pos > 0:
                blk_size = min(cur_pos, blk_size_max)
                cur_pos -= blk_size
                f.seek(cur_pos, os.SEEK_SET)
                log_data = f.read(blk_size) + log_data
                if log_data.find("# Time:") != -1:
                    log_data_list = log_data.split("# Time:")[::-1]
                    log_data = log_data_list.pop()

                    for info in log_data_list:
                        data = "# Time:" + info
                        log_time = re.search(r"#\s*Time:\s*(.*)\n", data).group(1)
                        log_time = datetime.datetime.strptime(log_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                        if last_analysis_datetime is not None:
                            if log_time <= last_analysis_datetime:
                                if new_last_analysis_datetime is not None:
                                    mysql_slow["last_analysis_datetime"] = str(new_last_analysis_datetime)
                                    self.__set_conf("mysql_slow", mysql_slow)
                                return
                        self.__slave_slow(data)
                        if new_last_analysis_datetime is None:
                            new_last_analysis_datetime = log_time

        if new_last_analysis_datetime is not None:
            mysql_slow["last_analysis_datetime"] = str(new_last_analysis_datetime)
        self.__set_conf("mysql_slow", mysql_slow)
        return public.returnMsg(True, "解析完成！")

    # 获取慢查询记录
    def get_slow_log(self, get):
        if not hasattr(get, "db_name"):
            return public.returnMsg(False, "缺少参数！db_name")
        if not hasattr(get, "page"):
            return public.returnMsg(False, "缺少参数！page")
        if not hasattr(get, "page_size"):
            return public.returnMsg(False, "缺少参数！page_size")
        db_name = get.db_name
        page = int(get.page)
        page_size = int(get.page_size)

        # 解析查询日志
        self.__analysis_slow_log()

        total_num = self.db_sql.query(f"select count(desc.id) from {self.slow_sql_table_name} as sql, {self.slow_details_table_name} as desc where sql.id = desc.sql_id and sql.db_name != 'root' and desc.status = 0")[0][0]
        data_list = self.db_sql.query(f"select sql.db_name, count(desc.id) from {self.slow_sql_table_name} as sql, {self.slow_details_table_name} as desc where sql.id = desc.sql_id and sql.db_name != 'root' and desc.status = 0 group by sql.db_name")
        db_list = [{"db_name": data[0], "total": data[1]} for data in data_list]

        where = ""
        if db_name:
            where = f" and db_name='{db_name}'"
        sql_id_list = self.db_sql.query(f"select sql.id from {self.slow_sql_table_name} as sql, {self.slow_details_table_name} as desc where sql.id = desc.sql_id and sql.db_name != 'root' and desc.status = 0{where} group by sql.id")
        sql_id_list = [str(data[0]) for data in sql_id_list]
        slow_query_num = len(sql_id_list)
        page_info = public.get_page(slow_query_num, page, page_size)


        slow_query_list = self.db_sql.table(self.slow_sql_table_name).where(f"id in ({','.join(sql_id_list)}) and db_name != 'root'{where}", ()).order("id desc").limit(page_info["row"], page_info["shift"]).select()
        for db in slow_query_list:
            sql_id = db["id"]
            desc_data = self.db_sql.table(self.slow_details_table_name).where("sql_id=? and status=0", (sql_id)).order("id desc").select()
            db["list"] = desc_data

        result = {
            "total_num": total_num,
            "page": page_info,
            "db_list": db_list,
            "slow_query_list": slow_query_list,
        }
        public.set_module_logs('database_mater', 'get_slow_log', 1)
        return {"status": True, "msg": "OK", "data": result}

    def __optimization_sql(self, sql_id: int, db_name, query_sql) -> int:
        add_num = 0

        mysql_obj = panelMysql.panelMysql()

        query_sql_obj = re.search(r"select\s*(.+)\s*from\s*(.+)\s*where\s*(.*)\s*(limit.*|order.*|group.*)*", query_sql, re.I)
        table_from = query_sql_obj.group(2)
        where_sql = query_sql_obj.group(3)
        table_from = table_from.replace("`", "").strip()
        for tb_name in table_from.split(","):
            if tb_name.find(".") == -1:
                db = db_name
            else:
                db = tb_name.split(".")[0]
                tb_name = tb_name.split(".")[1]
            # 获取字段列表
            data_list = mysql_obj.query(f"show columns from `{db}`.`{tb_name}`;")
            if not isinstance(data_list, list): continue
            for data in data_list:
                field = data[0]
                field_type = str(data[1]).lower()
                is_null = data[2]
                key = data[3]
                if field not in where_sql: continue
                start_time = time.time()
                index_list = mysql_obj.query(f"show index from `{db}`.`{tb_name}` where Column_name='{field}';")
                if len(index_list) != 0:
                    if self.db_sql.table(self.index_log).where("db_name=? and tb_name=? and field=?", (db, tb_name, field)).count() == 0:
                        self.db_sql.table(self.index_log).add("db_name,tb_name,field,add_time", (db, tb_name, field, str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
                        public.writeFile(self.index_optimization, f"\n检测到：{db}.{tb_name} {field} 存在索引 {key} 已跳过该字段！", "a")
                elif field_type.startswith("varchar") or field_type.startswith("char") or field_type in ["int","bigint","date","datetime"]:
                    public.writeFile(self.index_optimization, f"\n正在添加索引：{db}.{tb_name} 字段 {field}", "a")
                    mysql_obj.query(f"ALTER TABLE `{db}`.`{tb_name}` ADD INDEX(`{field}`);")
                    elapsed_time = time.time() - start_time

                    time_second = round(elapsed_time % 60, 2)
                    time_minute = f"{int(elapsed_time // 60 % 60)}分" if int(elapsed_time // 60 % 60) != 0 else ''
                    time_hour = f"{int(elapsed_time // 60 // 60 % 60)}时" if int(elapsed_time // 60 // 60 % 60) != 0 else ''
                    time_day = f"{int(elapsed_time // 60 // 60 // 60 % 24)}天" if int(elapsed_time // 60 // 60 // 60 % 24) != 0 else ''
                    public.writeFile(self.index_optimization, f" 成功！耗时：{time_day}{time_hour}{time_minute}{time_second}秒", "a")
                    add_num += 1
                    self.db_sql.table(self.index_log).add("db_name,tb_name,field,add_time", (db, tb_name, field, str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
                self.db_sql.table(self.slow_details_table_name).where("sql_id=?", (sql_id)).update({"status": 1})
        return add_num

    # 一键优化
    def all_optimization(self, get):
        if os.path.isfile(self.index_optimization):
            index_optimization_log = public.readFile(self.index_optimization)
            if str(index_optimization_log).endswith("优化完成!"):
                os.remove(self.index_optimization)
                return {"status": True, "msg": index_optimization_log}
            return {"status": True, "msg": index_optimization_log, "type": 1}
        
        db_name = getattr(get, "db_name", None)
        if not hasattr(get, "func"):
            if not hasattr(get, "db_name"):
                return public.returnMsg(False, "缺少参数！db_name")
            # 后台执行
            task_obj = panelTask.bt_task()
            task_obj.create_task('优化索引', 0, f"btpython {self.execute_optimization_func} --db_name={db_name} --api=all_optimization")
            return {"status": True, "msg": "开始一键优化索引", "type": 1}
        
        try:
            public.writeFile(self.index_optimization, f"开始一键优化索引", "w")
    
            where = ""
            if db_name:
                where = f" and sql.db_name = '{db_name}'"
    
            slow_query_list = self.db_sql.query(f"select sql.id,sql.db_name,sql.query_sql from {self.slow_sql_table_name} as sql, {self.slow_details_table_name} as desc where sql.id = desc.sql_id and sql.db_name != 'root' and desc.status = 0{where} group by sql.id")
            total_add_num = 0
    
            for sql in slow_query_list:
                total_add_num += self.__optimization_sql(sql[0], sql[1], sql[2])
    
            msg = f"一键优化索引成功！本次优化了 {f'{db_name} 数据库中' if db_name else '所有数据库'} {total_add_num} 个字段"
            if total_add_num != 0:
                self.db_sql.table(self.operate_log).add("type,log,add_time", (0, msg, str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
            public.writeFile(self.index_optimization, f"\n{datetime.datetime.now()} 一键优化完成!", "a")
        except Exception as err:
            public.print_log(f"err:{err}")
            public.writeFile(self.index_optimization, f"\n异常：{err}0", "a")

    # 优化单条语句
    def optimization_sql(self, get):
        if os.path.isfile(self.index_optimization):
            index_optimization_log = public.readFile(self.index_optimization)
            if str(index_optimization_log).endswith("优化完成！"):
                os.remove(self.index_optimization)
                return {"status": True, "msg": index_optimization_log}
            return {"status": True, "msg": index_optimization_log, "type": 1}
        
        sql_id = getattr(get, "sql_id", "[]")
        if not hasattr(get, "func"):
            if not hasattr(get, "sql_id"):
                return public.returnMsg(False, "缺少参数！sql_id")
            # 后台执行
            task_obj = panelTask.bt_task()
            task_obj.create_task('优化索引', 0, f"btpython {self.execute_optimization_func} --sql_id={sql_id} --api=optimization_sql")
            return {"status": True, "msg": "开始优化索引", "type": 1}
        
        try:
            sql_id_list = json.loads(get.sql_id)
            
            public.writeFile(self.index_optimization, f"开始优化索引", "w")

            for sql_id in sql_id_list:
                data_list = self.db_sql.table(self.slow_sql_table_name).where("id=? and db_name != 'root'", (sql_id)).find()
                if not data_list:
                    return public.writeFile(self.index_optimization, f"\n该记录不存在！sql_id\n0", "a")
                try:
                    add_num = self.__optimization_sql(data_list["id"], data_list["db_name"], data_list["query_sql"])
                except Exception as err:
                    return public.writeFile(self.index_optimization, f"\n优化失败！ [{data_list['db_name']}] 数据库, 优化sql {data_list['query_sql']}\n0", "a")
                msg = f"优化 [{data_list['db_name']}] 数据库, 共 {add_num} 个字段"
                if add_num != 0:
                    self.db_sql.table(self.operate_log).add("type,log,add_time", (0, msg, str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
            
            public.writeFile(self.index_optimization, f"\n{datetime.datetime.now()} 优化完成!", "a")
        except Exception as err:
            public.print_log(f"err:{err}")
            public.writeFile(self.index_optimization, f"\n异常：{err}0", "a")

    # 执行方法
    def execute_func(self, get):
        if not hasattr(get, "api"):
            return public.returnMsg(False, "缺少参数！ api")
        fun = getattr(self, get.api)
        fun(get)

    # 获取索引优化记录
    def get_optimization_index_log(self, get):
        if not hasattr(get, "page"):
            return public.returnMsg(False, "缺少参数！page")
        if not hasattr(get, "page_size"):
            return public.returnMsg(False, "缺少参数！page_size")
        page = int(get.page)
        page_size = int(get.page_size)

        total_num = self.db_sql.table(self.index_log).count()
        page_info = public.get_page(total_num, page, page_size)
        index_log = self.db_sql.table(self.index_log).order("add_time desc").limit(page_info["row"], page_info["shift"]).select()

        result = {
            "total_num": total_num,
            "page": page_info,
            "index_log": index_log,
        }
        return {"status": True, "msg": "OK", "data": result}

    # 删除索引
    def del_optimization_index(self, get):
        if not hasattr(get, "index_id"):
            return public.returnMsg(False, "缺少参数！sql_id")

        index_id_list = json.loads(get.index_id)

        mysql_obj = panelMysql.panelMysql()

        success = []
        error = {}
        db_set = set()
        total_del_num = 0
        for index_id in index_id_list:
            data = self.db_sql.table(self.index_log).where("id=?", (index_id)).find()
            if not data: continue

            is_index = mysql_obj.query(f"show index from {data['db_name']}.{data['tb_name']} where Column_name='{data['field']}';")
            if len(is_index) != 0:
                try:
                    mysql_obj.query(f"ALTER TABLE `{data['db_name']}`.`{data['tb_name']}` DROP INDEX `{data['field']}`;")
                except Exception as err:
                    msg = ""
                    error[msg] = "失败"
                    continue
                total_del_num += 1
                db_set.add(data['db_name'])
                msg = f"删除 {data['db_name']}.{data['tb_name']} 索引字段 {data['field']}"
                success.append(msg)
            self.db_sql.table(self.index_log).where("id=?", (index_id)).delete()
        msg = f"删除索引成功！本次删除了 [{']['.join(db_set)}] 数据库, 共 {total_del_num} 个索引"
        self.db_sql.table(self.operate_log).add("type,log,add_time", (0, msg, str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
        return {"status": True, "msg": "OK", "success": success, "error": error}

    # 获取优化记录
    def get_optimization_log(self, get):
        if not hasattr(get, "page"):
            return public.returnMsg(False, "缺少参数！page")
        if not hasattr(get, "page_size"):
            return public.returnMsg(False, "缺少参数！page_size")
        page = int(get.page)
        page_size = int(get.page_size)

        total_num = self.db_sql.table(self.operate_log).where("type=0", ()).count()
        page_info = public.get_page(total_num, page, page_size)
        operate_log = self.db_sql.table(self.operate_log).where("type=0", ()).order("add_time desc").limit(page_info["row"], page_info["shift"]).select()

        result = {
            "total_num": total_num,
            "page": page_info,
            "operate_log": operate_log,
        }
        return {"status": True, "msg": "OK", "data": result}

    """配置优化"""
    # 配置优化
    def get_db_config(self, get):
        show_variables_status = self.__get_show_variables()
        if show_variables_status is None:
            return public.returnMsg(False, "数据库连接失败！请检查数据库状态！")

        variables_status = ["able_open_cache", "thread_cache_size", "query_cache_type", "key_buffer_size", "query_cache_size",
                "tmp_table_size", "max_heap_table_size", "innodb_buffer_pool_size", "innodb_additional_mem_pool_size",
                "innodb_log_buffer_size", "max_connections", "sort_buffer_size", "read_buffer_size",
                "read_rnd_buffer_size", "join_buffer_size", "thread_stack", "binlog_cache_size"]
        result = {}
        for field in variables_status:
            result[field] = show_variables_status.get(field)
        if "query_cache_type" in result:
            if result["query_cache_type"] != "ON": result["query_cache_size"] = "0"

        return {"status": True, "msg": "OK", "data": result}

    """二进制管理"""
    # 查看当前所有的二进制文件
    def get_mysql_bin(self, get):
        mysql_info = self.__get_mysql_info()

        mysql_bin_index = os.path.join(mysql_info["datadir"], "mysql-bin.index")
        mysql_bin_index_content = public.readFile(mysql_bin_index)
        mysql_bin_list = []
        for name in str(mysql_bin_index_content).strip().split("\n"):
            path = os.path.join(mysql_info["datadir"], os.path.basename(name))
            mysql_bin_list.append(path)

        return {"status": True, "msg": "OK", "data": mysql_bin_list}

    #备份二进制
    def backup_mysql_bin(self, get):
        if not hasattr(get, "path"):
            return public.returnMsg(False, "缺少参数！path")
        path = get.path

        if not os.path.isfile(path):
            return public.returnMsg(False, "二进制文件路径不存在！")

        backup_path = os.path.join(self.mysql_bin_backup, os.path.basename(path))

        if os.path.isfile(backup_path):
            if os.path.getsize(path) == os.path.getsize(backup_path):
                return public.returnMsg(True, f"已备份在[{self.mysql_bin_backup}]目录中！")

        public.ExecShell(f"cp -p {path} {backup_path}")

        ps = f"备份二进制文件成功:文件{os.path.basename(path)}备份文件存放在[{self.mysql_bin_backup}]目录中"
        self.db_sql.table(self.operate_log).add("type,log,add_time", (1, ps, str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))

        return public.returnMsg(True, f"备份完成,备份文件存放在[{self.mysql_bin_backup}]目录中")

    # 查看备份二进制文件
    def get_backup_mysql_bin(self, get):

        result = []
        for name in os.listdir(self.mysql_bin_backup):
            path = os.path.join(self.mysql_bin_backup, name)
            result.append(path)
        return {"status": True, "msg": "OK", "data": result}

    # 查看备份日志
    def get_backup_log(self, get):
        if not hasattr(get, "p"):
            return public.returnMsg(False, "缺少参数！p")

        page = get.p
        if not str(page).isdigit():
            return public.returnMsg(False, f"参数值错误！page：{page}")

        page = int(page)
        result = {}

        count = self.db_sql.table(self.operate_log).where("type=1", ()).count()
        result['page'] = public.get_page(count, page, 10)
        result['data'] = self.db_sql.table(self.operate_log).field('id,log').where("type=1", ()).order("id desc").limit(
            '{},{}'.format(result['page']['shift'], result['page']['row'])).select()


        return {"status": True, "msg": "OK", "data": result}

    # 查看操作日志
    def get_local_log(self, get):
        if not hasattr(get, "p"):
            return public.returnMsg(False, "缺少参数！path")

        page = int(get.p)
        result = {}
        count = public.M('logs').where("type=?", ('堡塔数据库运维工具',)).order("id desc").count()
        result['page'] = public.get_page(count, page, 10)
        result['data'] = public.M('logs').where("type=?", ('堡塔数据库运维工具',)).order("id desc").limit('{},{}'.format(result['page']['shift'], result['page']['row'])).select()
        return {"status": True, "msg": "OK", "data": result}

    # 导出数据库sql
    def export_db_sql(self, get):
        if not hasattr(get, "path"):
            return public.returnMsg(False, "缺少参数！path")

        path_list = json.loads(get.path)
        database = getattr(get, "database", None)
        start_datetime = getattr(get, "start_datetime", None)
        stop_datetime = getattr(get, "stop_datetime", None)

        file_name = f"mysql_bin_{int(time.time() * 100_0000)}.sql"
        file_path = os.path.join(self.mysql_bin_backup, file_name)


        path_str = " ".join(path_list)

        shell = f"{self.__mysql_bin_log} -v"

        if database is not None:
            shell += f" --database={database}"
        if start_datetime is not None:
            shell += f" --start-datetime='{start_datetime}'"
        if stop_datetime is not None:
            shell += f" --stop-datetime='{stop_datetime}'"

        shell += f" --base64-output=decode-rows {path_str} > {file_path}"
        public.ExecShell(shell)

        path_ps = ""
        for path in path_list:
            path_ps += os.path.basename(path)

        ps = f"{path_ps} 导出sql保存于{file_path}"
        self.db_sql.table(self.operate_log).add("type,log,add_time", (1, ps, str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))

        public.WriteLog('堡塔数据库运维工具', f"导出sql文件成功：{file_path}")

        return {"status": True, "msg": f"导出sql文件成功：{file_path}"}

    # 分析
    def analysis_bin_log(self, get):
        if not hasattr(get, "path"):
            return public.returnMsg(False, "缺少参数！path")

        path = get.path

        public.ExecShell(f"rm -rf /var/tmp/689.log && /www/server/mysql/bin/mysqlbinlog -v --base64-output=decode-rows {path} > /var/tmp/689.log")
        if not os.path.exists('/var/tmp/689.log'):
            return public.returnMsg(False, "分析失败！")

        result = public.GetNumLines("/var/tmp/689.log", 2000)
        if len(result) < 1:
            return public.returnMsg(False, public.getMsg('TASK_SLEEP'))
        return {"status": True, "msg": "OK", "data": result}

    # 删除二进制文件
    def del_bin_log_file(self, get):
        if not hasattr(get, "path"):
            return public.returnMsg(False, "缺少参数！path")

        path = get.path
        if not os.path.isfile(path):
            return public.returnMsg(False, f"二进制文件不存在！{path}")
        os.remove(path)
        public.WriteLog('堡塔数据库运维工具', f"删除二进制文件成功：{path}")
        return public.returnMsg(True, "删除成功!")

    # 查看自动备份
    def get_automatic_status(self, get):
        is_start = public.M('crontab').where('name=?', ('堡塔数据库运维工具二进制文件备份',)).count() != 0

        return {"status": True, "msg": "OK", "data": is_start}

    # 自动备份防止被误删
    def set_automatic_backup(self, get):
        if not hasattr(get, "status"):
            return public.returnMsg(False, "缺少参数！status")

        status = get.status == "true"

        is_start = public.M('crontab').where('name=?', ('堡塔数据库运维工具二进制文件备份',)).count() != 0

        is_status = True
        if status is True and is_start is False: # 开启
            p = crontab.crontab()
            args = {
                "name": "堡塔数据库运维工具二进制文件备份",
                "type": "day",
                "where1": "",
                "hour": "1",
                "minute": "30",
                "week": "",
                "sType": "toShell",
                "sName": "",
                "backupTo": "localhost",
                "save": "",
                "sBody": "python /www/server/panel/plugin/database_mater/task_local.py",
                "urladdress": "undefined"
            }
            is_status = p.AddCrontab(args).get("status", False)
        elif is_start is True: # 关闭
            data = public.M('crontab').where('name=?', ('堡塔数据库运维工具二进制文件备份',)).getField('id')
            if type(data) == list: return public.returnMsg(False, '你没有启用该计划任务')
            p = crontab.crontab()
            is_status = p.DelCrontab(get={'id': data}).get("status", False)

        return {"status": True, "msg": f"{'开启' if status else '关闭'} {'成功' if is_status else '失败'}！", "data": status}

























