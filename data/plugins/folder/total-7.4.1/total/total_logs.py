#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# | Date: 2021/7/17
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表 - 站点日志管好理工具
# +--------------------------------------------------------------------
from __future__ import absolute_import, print_function, division
from codecs import encode
import shutil
import sqlite3
import sys
import time
import os
import gevent
from gevent.monkey import patch_subprocess
import gevent.pool
import json

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(0, "/www/server/panel")
import public
from crontab import crontab

from total_migrate import total_migrate
import total_tools as tool


def import_data_from_sql(filename, target_db):
    conn = None
    cur = None
    try:
        conn = sqlite3.connect(target_db)
        cur = conn.cursor()
        conn.execute("BEGIN TRANSACTION;")
        columns = []

        with open(filename, "r") as fp:
            while True:
                line = fp.readline().strip()
                if not line:
                    # print("exit.")
                    break
                if line.lower() == "begin transaction;": continue
                if line.lower() == "commit;": continue
                if line.lower().find("pragma") >= 0: continue
                try:
                    cur.execute(line)
                except Exception as e:
                    error = str(e)
                    if error.find("UNIQUE") >= 0:
                        values = line[line.find("VALUES (") + 8:-2]
                        # print(values)
                        table_name = os.path.splitext(filename)[0]
                        if not columns:
                            res = cur.execute(
                                "PRAGMA table_info([{}])".format(table_name))
                            columns = [c[1] for c in res]

                        num_values = values.split(",")
                        if len(columns) != len(num_values):
                            # print("列数异常。")
                            print(columns)
                            print(num_values)
                        else:
                            time_key = num_values[0]
                            update_sql = "UPDATE " + table_name + " SET "
                            fields = ""
                            for i, c in enumerate(columns):
                                if c == "time": continue
                                if fields:
                                    fields += ","
                                fields += c + "=" + c + "+" + num_values[i]
                            update_sql += fields + " WHERE time=" + time_key
                            # print(update_sql)
                            cur.execute(update_sql)
                            # print("Update success.")
                # break

        conn.execute("COMMIT;")
    except:
        pass
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# 移动到回收站
def remove_file_to_recycle_bin(path):
    recycle_bin_status_file = "/www/server/panel/data/recycle_bin.pl"
    if not os.path.isfile(recycle_bin_status_file):
        try:
            os.remove(path)
        except:
            public.ExecShell("rm -f " + path)
        return True

    rPath = '/www/Recycle_bin/'
    if not os.path.exists(rPath):
        public.ExecShell('mkdir -p ' + rPath)
    rFile = rPath + path.replace('/', '_bt_') + '_t_' + str(time.time())
    try:
        import shutil
        shutil.move(path, rFile)
        public.WriteLog('TYPE_FILE', 'FILE_MOVE_RECYCLE_BIN', (path,))
        return True
    except:
        public.WriteLog('TYPE_FILE', 'FILE_MOVE_RECYCLE_BIN_ERR', (path,))
    return False


def change_site2(site_name, data_dir, new_data_dir):
    """更换数据存储目录，只迁移日志文件

    Args:
        site_name (str): 网站名称
        data_dir (str): 原目录
        new_data_dir (str): 新目录
    """
    if not os.path.exists(data_dir): return
    site_name = site_name.replace("_", ".")
    data_dir = os.path.join(data_dir, site_name)
    new_data_dir = os.path.join(new_data_dir, site_name)
    if not os.path.exists(new_data_dir):
        os.makedirs(new_data_dir)
    blacklist = [
        "total.db",
        "flow_sec.json",
        "req_sec.json",
        "update_day.log",
        tool.get_logs_txt_name()
    ]
    whitelist = [
        "logs.db",
        "history_logs.db",
        "logs.info"
    ]

    error = False
    for orif in os.listdir(data_dir):
        if orif in blacklist: continue
        to_copy = False
        if orif in whitelist:
            to_copy = True
        else:
            pre_name = orif[0:8]
            try:
                time.strptime(pre_name, "%Y%m%d")
                to_copy = True
            except:
                pass

        if to_copy:
            real_file = os.path.join(data_dir, orif)
            target_file = os.path.join(new_data_dir, orif)
            print("正在移动文件: {} --> {}".format(real_file, target_file))
            try:
                shutil.move(real_file, target_file)
            except Exception as e:
                error = True
                msg = "移动文件异常: {}".format(e)
                print(msg)
                public.WriteLog("网站监控报表", msg)
    return not error


def change_site(site_name, data_dir, new_data_dir, quick_mode=False):
    """快速复制数据文件到新目录，丢弃网站日志数据"""
    time_start = time.time()
    print("开始迁移站点: {} 的网站数据".format(site_name))
    site_name = site_name.replace("_", ".")
    to_be_delete_files = []
    new_paths = []
    db_path = os.path.join(data_dir, site_name, "logs.db")
    new_db = os.path.join(new_data_dir, site_name, "logs.db")
    # print("旧db:{}".format(db_path))
    # print("新db:{}".format(new_db))
    # print("Quick mode: {}".format(quick_mode))
    if db_path != new_db:
        if os.path.isfile(new_db):
            remove_file_to_recycle_bin(new_db)
        total_migrate().init_site_db(site_name, target_data_dir=new_data_dir)
        # os.remove(new_db)

    if not os.path.isfile(db_path):
        if not os.path.isfile(new_db):
            total_migrate().init_site_db(site_name, target_data_dir=new_data_dir)
    else:
        if quick_mode:
            request_stat_file = "/tmp/{}_request_stat.sql".format(site_name)
            spider_stat_file = "/tmp/{}_spider_stat.sql".format(site_name)
            client_stat_file = "/tmp/{}_client_stat.sql".format(site_name)
            ip_stat_file = "/tmp/{}_ip_stat.sql".format(site_name)
            uri_stat_file = "/tmp/{}_uri_stat.sql".format(site_name)

            os.system(
                "sqlite3 {} \".dump request_stat\" > {}".format(db_path,
                                                                request_stat_file))
            os.system(
                "sqlite3 {} \".dump spider_stat\" > {}".format(db_path,
                                                               spider_stat_file))
            os.system(
                "sqlite3 {} \".dump client_stat\"  > {}".format(db_path,
                                                                client_stat_file))
            os.system(
                "sqlite3 {} \".dump ip_stat\" > {}".format(db_path, ip_stat_file))
            os.system(
                "sqlite3 {} \".dump uri_stat\" > {}".format(db_path,
                                                            uri_stat_file))

            if db_path == new_db:
                remove_file_to_recycle_bin(new_db)
                total_migrate().init_site_db(site_name, target_data_dir=new_data_dir)

            import_data_from_sql(request_stat_file, new_db)
            import_data_from_sql(spider_stat_file, new_db)
            import_data_from_sql(client_stat_file, new_db)
            import_data_from_sql(ip_stat_file, new_db)
            import_data_from_sql(uri_stat_file, new_db)

            # os.remove(request_stat_file)
            # os.remove(spider_stat_file)
            # os.remove(client_stat_file)
            # os.remove(ip_stat_file)
            # os.remove(uri_stat_file)
            if db_path != new_db:
                to_be_delete_files.append(db_path)
        else:
            import shutil
            if db_path != new_db:
                shutil.move(db_path, new_db)

    new_paths.append(os.path.join(new_data_dir, site_name))
    return True, to_be_delete_files, new_paths


def change_data_dir(data_dir, new_data_dir, quick_mode=False):
    """
    更换数据存储目录
    :data_dir 源数据目录
    :new_data_dir 新数据目录
    :quick_mode 是否快速更换；快速更换将丢弃网站日志数据。
    """
    site_conn = None
    site_cur = None
    try:
        if not os.path.isdir(data_dir):
            return False

        new_data_dir = os.path.abspath(new_data_dir)
        if not os.path.isdir(new_data_dir):
            os.makedirs(new_data_dir)
        site_conn = sqlite3.connect("/www/server/panel/data/default.db")
        site_cur = site_conn.cursor()
        sites = site_cur.execute("select name from sites;").fetchall()
        pool_size = min(20, len(sites))
        # print("pool size:"+str(pool_size))
        pool = gevent.pool.Pool(pool_size)
        jobs = [pool.spawn(change_site2, site_info[0], data_dir, new_data_dir) for site_info
                in sites]
        gevent.joinall(jobs)
        has_error = False
        for job in jobs:
            status = job.value
            if not status:
                has_error = True

        public.ExecShell("chown -R www:www {}".format(new_data_dir))
        return not has_error
    except Exception as e:
        public.WriteLog("网站监控报表", "更换目录执行异常:" + str(e))
    finally:
        if site_cur:
            site_cur.close()
        if site_conn:
            site_conn.close()
    return False


def add_backgroud_task(archive_config):
    name = "网站监控报表定时归档任务"
    c = crontab()
    get = public.dict_obj()
    get.type = archive_config["execute_type"]
    get.where1 = archive_config["execute_day"]
    get.hour = archive_config["execute_hour"]
    get.minute = archive_config["execute_minute"]
    get.sBody = public.get_python_bin() + " /www/server/panel/plugin/total/total_logs.py"
    get.sType = "toShell"
    get.name = name
    get.sName = ""
    get.urladdress = ""
    get.backupTo = ""
    res = c.AddCrontab(get)
    return res


def get_log_db_path(site):
    data_dir = "/www/server/total/logs"
    site = site.replace("_", ".")
    db_path = os.path.join(data_dir, site, "logs.db")
    return db_path


def select_uri_stat(db, fields):
    selector = db.execute("select {} from uri_stat;".format(fields))
    return selector


def select_ip_stat(db, fields):
    selector = db.execute("select {} from ip_stat;".format(fields))
    return selector


def select_spider_stat(db, total_start, total_end, fields):
    selector = db.execute("select {} from spider_stat where time>={} and time<={}".format(fields, total_start, total_end))
    return selector


def select_client_stat(db, total_start, total_end, fields):
    selector = db.execute("select {} from client_stat where time>={} and time<={}".format(fields, total_start, total_end))
    return selector


def select_request_stat(db, total_start, total_end, fields):
    selector = db.execute("select {} from request_stat where time>={} and time<={}".format(fields, total_start, total_end))
    return selector


def select_site_logs(db, start, end, fields):
    sql = "select {} from site_logs where time>={} and time<={}".format(fields, start, end)
    print("site logs sql:")
    print(sql)
    selector = db.execute(sql)
    return selector


def get_table_columns(db, table):
    selector = db.execute("PRAGMA table_info([{}]);".format(table))
    return [column[1] for column in selector.fetchall()]


def archive_day(site, db, start, end, archive_dir):
    try:
        # select
        file_name = "{}-{}".format(site, time.strftime("%Y%m%d", time.localtime(start)))
        db_name = file_name + ".db"
        db_path = os.path.join(archive_dir, site, db_name)
        if os.path.exists(db_path):
            os.remove(db_path)

        total_migrate().init_site_db(site, target_data_dir=archive_dir, db_name=db_name)
        new_conn = sqlite3.connect(db_path)
        new_cur = new_conn.cursor()

        ## prepare fields
        site_logs_fields = get_table_columns(new_cur, "site_logs")
        if "id" in site_logs_fields:
            site_logs_fields.remove("id")
        print("site logs fields:")
        print(site_logs_fields)
        request_stat_fields = get_table_columns(new_cur, "request_stat")
        client_stat_fields = get_table_columns(new_cur, "client_stat")
        spider_stat_fields = get_table_columns(new_cur, "spider_stat")

        day = int(time.strftime("%d", time.localtime(start)))
        day_column = "day" + str(day)
        flow_column = "flow" + str(day)
        ip_stat_fields = ["ip", day_column, flow_column]
        uri_stat_fields = ["uri", day_column, flow_column]

        ## get selector
        site_logs_selector = select_site_logs(db, start, end, ",".join(site_logs_fields))
        total_start = int(time.strftime("%Y%m%d00", time.localtime(start)))
        total_end = int(time.strftime("%Y%m%d23", time.localtime(end)))
        request_stat_selector = select_request_stat(db, total_start, total_end, ",".join(request_stat_fields))
        client_stat_selector = select_client_stat(db, total_start, total_end, ",".join(client_stat_fields))
        spider_stat_selector = select_spider_stat(db, total_start, total_end, ",".join(spider_stat_fields))
        ip_stat_selector = select_ip_stat(db, ",".join(ip_stat_fields))
        uri_stat_selector = select_uri_stat(db, ",".join(uri_stat_fields))

        # insert

        new_cur.execute("BEGIN TRANSACTION;")

        ## to insert
        print("site logs ?:" + ",".join(["?" for i in range(len(site_logs_fields))]))
        insert_site_logs_sql = "INSERT INTO site_logs({}) VALUES({});".format(
            ",".join(site_logs_fields), ",".join(["?" for i in range(len(site_logs_fields))]))
        print("insert site logs sql:" + insert_site_logs_sql)
        logs = site_logs_selector.fetchall()
        for log in logs:
            # uri_index = site_logs_fields.index("uri")
            # new_line = log
            # new_line[uri_index] = str(log[uri_index], encoing="utf-8", errors="ignore")

            if len(log) != len(site_logs_fields):
                print(log)
                continue
            new_cur.execute(insert_site_logs_sql, log)
        # new_cur.executemany(insert_site_logs_sql, site_logs_selector.fetchall())

        insert_request_stat_sql = "INSERT INTO request_stat({}) VALUES({});".format(
            ",".join(request_stat_fields), ",".join(["?" for i in range(len(request_stat_fields))]))
        new_cur.executemany(insert_request_stat_sql, request_stat_selector.fetchall())

        insert_client_stat_sql = "INSERT INTO client_stat({}) VALUES({});".format(
            ",".join(client_stat_fields), ",".join(["?" for i in range(len(client_stat_fields))]))
        new_cur.executemany(insert_client_stat_sql, client_stat_selector.fetchall())

        insert_spider_stat_sql = "INSERT INTO spider_stat({}) VALUES({});".format(
            ",".join(spider_stat_fields), ",".join(["?" for i in range(len(spider_stat_fields))]))
        new_cur.executemany(insert_spider_stat_sql, spider_stat_selector.fetchall())

        insert_ip_stat_sql = "INSERT INTO ip_stat({}) VALUES({});".format(
            ",".join(ip_stat_fields), ",".join(["?" for i in range(len(ip_stat_fields))]))
        new_cur.executemany(insert_ip_stat_sql, ip_stat_selector.fetchall())

        insert_uri_stat_sql = "INSERT INTO uri_stat({}) VALUES({});".format(
            ",".join(uri_stat_fields), ",".join(["?" for i in range(len(uri_stat_fields))]))
        new_cur.executemany(insert_uri_stat_sql, uri_stat_selector.fetchall())

        new_conn.commit()
        if new_cur:
            new_cur.close()
        if new_conn:
            new_conn.close()
        new_tar_file = os.path.join(archive_dir, site, file_name + ".tar.gz")
        os.system("tar -zcvf {} {}".format(new_tar_file, db_path))
        # os.system("rm -f {}".format(db_path))
        # deletor = db.execute("delete from site_logs where time>={} and time<={}".format(start, end))
    except KeyError as e:
        print(str(e))
        pass


def text_factory(text):
    try:
        return str(text, encoding="utf-8", errors="strict")
    except:
        return str(text)


def archive_site(site, save_day, archive_interval, archive_dir):
    try:
        import sqlite3
        conn = None
        cur = None
        db_path = get_log_db_path(site)
        test_db = "/www/server/total/logs/www.bt.cn/logs.db"
        db_path = test_db
        ori_file_size = public.get_path_size(db_path)
        print("原站点数据库文件大小: {}".format(ori_file_size))
        conn = sqlite3.connect(db_path)
        if sys.version_info[0] == 3:
            conn.text_factory = text_factory
        else:
            conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
        cur = conn.cursor()
        cur.execute("BEGIN TRANSACTION;")
        now = time.localtime()
        sep_time = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - archive_interval + 1, 0, 0, 0, 0, 0, 0))
        count = 1
        total_count = 0
        max = 0

        for i in range(save_day, archive_interval, -1):
            start_of_day = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - i + 1, 0, 0, 0, 0, 0, 0))
            end_of_day = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - i + 1, 23, 59, 59, 0, 0, 0))
            select_sql = "select count(*) from site_logs where time>={} and time<={}".format(start_of_day, end_of_day)
            # print(select_sql)
            selector = cur.execute(select_sql)
            result = selector.fetchall()
            res_count = result[0][0]
            if result and res_count > 0:
                archive_day(site, cur, start_of_day, end_of_day, archive_dir)
                break
            #     # print(start_of_day)
            #     start = time.strftime("%Y%m%d", time.localtime(start_of_day))
            #     # end = time.strftime("%Y%m%d", end_of_day)
            #     print("{}: {}".format(start, res_count))
            #     count += 1
            #     total_count += res_count
            #     if res_count > max:
            #         max = res_count
        # total_selector = cur.execute("select count(*) from site_logs")
        # total_count_by_sql = total_selector.fetchall()[0][0]
        # print("总日志行数: {}/ 平均每天产生: {} 行/单天最多: {} 行。".format(total_count, total_count/count, max))
        print("正在提交站点日志归档。")
        conn.commit()
        print("站点日志归档已提交。")
        print("开始重新构建数据库清理空间...")
        # cur.execute("VACUUM;")
        print("重新构建数据库完成。")
        new_file_size = public.get_path_size(db_path)
        print("请求后文件大小: {}".format(new_file_size))
        print("减少空间占用: {}".format(new_file_size - ori_file_size))
    except KeyError as e:
        print(str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def archive_log():
    archive_config_file = "/www/server/panel/plugin/total/config.json"
    archive_config = None
    default_config = {
        "archive_interval": 31,
        "archive_dir": "/www/server/total/logs",
        "execute_day": 1,
        "execute_hour": 3,
        "execute_minute": 0,
        "execute_type": "month",
    }
    if not os.path.isfile(archive_config_file):
        public.writeFile(archive_config_file, json.dumps(default_config))
        archive_config = default_config

    if not archive_config:
        archive_config = json.loads(public.readFile(archive_config_file))
        if "archive_interval" not in archive_config.keys():
            archive_config.update(default_config)
    # 检查定时任务是否存在
    if "background_task_id" not in archive_config.keys():
        res = add_backgroud_task(archive_config)
        # print("Add res:"+str(res))
        if "status" in res.keys() and res["status"]:
            task_id = res["id"]
            archive_config["background_task_id"] = task_id
            public.writeFile(archive_config_file, json.dumps(archive_config))

    background_task_id = archive_config["background_task_id"]
    c = crontab()
    get = public.dict_obj()
    get.id = background_task_id
    res = c.get_crond_find(get)
    if "id" not in res.keys():
        res = add_backgroud_task(archive_config)
        if "status" in res.keys() and res["status"]:
            task_id = res["id"]
            archive_config["background_task_id"] = task_id
            public.writeFile(archive_config_file, json.dumps(archive_config))

    # 开始归档
    server_config_file = "/www/server/total/config.json"
    server_config = json.loads(public.readFile(server_config_file))
    save_day = server_config["global"]["save_day"]

    site_conn = sqlite3.connect("/www/server/panel/data/default.db")
    site_cur = site_conn.cursor()
    sites = site_cur.execute("select name from sites;").fetchall()
    pool_size = min(20, len(sites))
    # print("pool size:"+str(pool_size))
    pool = gevent.pool.Pool(pool_size)
    archive_interval = archive_config["archive_interval"]
    archive_dir = archive_config["archive_dir"]
    jobs = [pool.spawn(archive_site, site_info[0], save_day, archive_interval, archive_dir) for site_info
            in sites]
    gevent.joinall(jobs)
    has_error = False
    for job in jobs:
        if not job.value: continue
        _v = job.value
        print(_v)


if __name__ == "__main__":
    # change_data_dir("/www/server/total/logs", None, quick_mode=False)
    # archive_log()
    # archive_site("www.bt.cn", 180, 31, "/www/backup/total")
    # os.system("touch /tmp/linxiao.txt")
    # remove_file_to_recycle_bin("/tmp/linxiao.txt")
    new_data_dir = "/home/dev/test"
    if not os.path.exists(new_data_dir):
        os.makedirs(new_data_dir)
    change_site2("btunknownbt", "/www/server/total/logs", new_data_dir)
