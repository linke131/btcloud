#!/usr/bin/python
# coding: utf-8
# ---------------------------------------
# 堡塔应用管理器 - 初始化配置
# ---------------------------------------
# Author:
#    backend: linxiao
#    frontend: akai
# ---------------------------------------
import os
import sys
import uuid
import time

import psutil
BASE_PATH = "/www/server/panel"
NAME = "btappmanager"
PLUGIN_DIR = os.path.join(BASE_PATH, "plugin", NAME)
DB_NAME = NAME+".db"
CONFIG_DB = os.path.join(BASE_PATH, "data", DB_NAME)
CONFIG_FILE = os.path.join(PLUGIN_DIR, "{}.conf".format(NAME))
FLAG_DIR = os.path.join(PLUGIN_DIR, "flags")
if not os.path.exists(FLAG_DIR):
    os.mkdir(FLAG_DIR)

os.chdir(BASE_PATH)
sys.path.insert(0, "class/")

import public

def init_config_db():

    conn = None
    cur = None

    try:
        import sqlite3
        conn = sqlite3.connect(CONFIG_DB)
        cur = conn.cursor()
        try:
            res = cur.execute("select name from sqlite_master where type='table'").fetchall()
            res = [r[0] for r in res]
        except Exception as e:
            res = []
        if "manager_config" in res:
            print("数据库配置表已经初始化")
            return True

        cur.execute("BEGIN TRANSACTION;")
        cur.execute("""
                    CREATE TABLE manager_config( 
                        name TEXT DEFAULT 'manager', 
                        log_dir TEXT,
                        logfile_maxbytes INTEGER DEFAULT 5120,
                        logfile_backups INTEGER DEFAULT 2,
                        monitor_app BOOLEAN DEFAULT true,
                        monitor_frequency INTEGER DEFAULT 20
                    )""")

        cur.execute("""
                    CREATE TABLE environment(
                        id CHAR(32) PRIMARY KEY,
                        name TEXT,  
                        main TEXT,
                        version TEXT DEFAULT '',
                        environment_args TEXT DEFAULT '',
                        app_args TEXT DEFAULT '', 
                        variables TEXT DEFAULT '',  
                        count INTEGER DEFAULT 0,
                        remark TEXT DEFAULT ''
                    )""")

        cur.execute("""
                    CREATE TABLE app(
                        id CHAR(32) PRIMARY KEY,
                        name TEXT,  
                        main TEXT,
                        environment_id CHAR(32),
                        args TEXT DEFAULT '', 
                        exec_dir TEXT DEFAULT '',
                        daemon BOOLEAN DEFAULT true,
                        environment_variables TEXT DEFAULT '',  
                        redirect_stderr BOOLEAN DEFAULT true,                
                        log_dir TEXT DEFAULT '',
                        max_retry INTEGER DEFAULT 10,
                        status TEXT DEFAULT '',
                        logfile_maxbytes INTEGER DEFAULT 0,
                        logfile_backups INTEGER DEFAULT 0,
                        user TEXT DEFAULT '',
                        remark TEXT DEFAULT '',
                        addtime INTEGER DEFAULT 0
                    )""")
        conn.commit()
        return True
    except Exception as e:
        print("初始化配置数据库失败:"+str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return False


def sync_db():
    conn = None
    cur = None
    from btappmanager_main import AppStatus, Tool
    flag_file = os.path.join(FLAG_DIR, "synchronized_successfully")
    try:
        if not os.path.exists(CONFIG_FILE):
            return True
        if os.path.exists(flag_file):
            return True

        import sqlite3
        conn = sqlite3.connect(CONFIG_DB)
        cur = conn.cursor()
        # log_dir, logfile_maxbytes, logfile_backups,
        # monitor_app, monitor_frequency, first
        tool = Tool()
        conf = tool.read_config(CONFIG_FILE)
        if len(conf.sections()) == 0:
            os.remove(CONFIG_FILE)
            return True

        log_dir = os.path.join(PLUGIN_DIR, "logs") 
        logfile_maxbytes = 61200
        logfile_backups = 2
        monitor_app = 1
        monitor_frequency = 20
        if conf.has_section("golbal"):
            log_dir = conf.get("global", "log_dir")
            logfile_maxbytes = conf.get("global", "logfile_maxbytes")
            logfile_backups = tool.get_size(conf.get("global", "logfile_backups"))
            monitor_app = True if conf.get("global", "monitor_app") == "1" else False
            monitor_frequency = conf.get("global", "monitor_frequency")

        init_manager_sql = "INSERT INTO manager_config VALUES('{}', '{}', {}, {}, {}, {});"
        init_manager_sql = init_manager_sql.format(
            "manager",
            log_dir,
            logfile_maxbytes,
            logfile_backups,
            monitor_app,
            monitor_frequency
         )
        cur.execute(init_manager_sql)

        envir_count = 0
        sections = conf.sections()
        for section in sections:
            if section.startswith("environment:"):
                environment_id = str(uuid.uuid1()).replace("-", "")
                environment_name = conf.get(section, "name")
                main_file = conf.get(section, "main")
                version = conf.get(section, "verison")
                environment_args = conf.get(section, "environment_args")
                app_args = conf.get(section, "app_args")
                variables = conf.get(section, "variables")
                remark = conf.get(section, "remark", fallback="")

                init_environment_sql = """
                INSERT INTO environment(
                    id, name, main, version, environment_args, app_args,
                    variables, remark
                ) VALUES (
                    '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'
                )
                """
                init_environment_sql = init_environment_sql.format(
                    environment_id,
                    environment_name, 
                    main_file,
                    version,
                    environment_args,
                    app_args,
                    variables,
                    remark
                )
                cur.execute(init_environment_sql)
                envir_count += 1
        conn.commit()

        for section in sections:
            if section.startswith("app:"):
                app_id = str(uuid.uuid1()).replace("-", "")
                app_name = conf.get(section, "name")
                main_file = conf.get(section, "main")

                environment_name = conf.get(section, "environment_name")
                selector = cur.execute("select id from environment where name='{}'".format(environment_name)).fetchone()
                environment_id = None
                if selector:
                    environment_id = selector[0]

                args = conf.get(section, "args")
                exec_dir = conf.get(section, "exec_dir")
                daemon = 1 if conf.get(section, "daemon") == "true" else 0
                environment_variables = conf.get(section, "environment_variables")
                redirect_stderr = 1 if conf.get(section, "redirect_stderr") == "True" else 0
                max_retry = conf.get(section, "max_retry")
                status = conf.get(section, "status", fallback=AppStatus.Initial)
                log_dir = "" 
                logfile_maxbytes = 0
                logfile_backups = 0
                remark = conf.get(section, "remark", fallback="")
                addtime = time.time()

                pid = conf.get(section, "pid", fallback=0)
                if pid:
                    pid = int(pid)
                    if psutil.pid_exists(pid):
                        pid_dir = os.path.join(PLUGIN_DIR, "pids")
                        if not os.path.exists(pid_dir):
                            os.mkdir(pid_dir)
                        pid_content = "{},{},{}".format(pid, AppStatus.Running, time.time())
                        public.writeFile(os.path.join(pid_dir, app_id+".pid"), pid_content)
                        status = AppStatus.Running

                init_app_sql = """INSERT INTO app(
                id, name, main, environment_id,args,exec_dir,daemon
                ,environment_variables,redirect_stderr, log_dir, max_retry
                ,status, logfile_maxbytes, logfile_backups, remark, addtime
                ) VALUES('{}','{}', '{}', '{}' , '{}', '{}', {}, '{}', {}, '{}', {}, '{}', {}, {}, '{}', {})
                """
                init_app_sql = init_app_sql.format(
                    app_id, app_name, main_file, environment_id, args, 
                    exec_dir, daemon, environment_variables, redirect_stderr, log_dir, 
                    max_retry, status, logfile_maxbytes, logfile_backups, remark, addtime
                )
                cur.execute(init_app_sql)
                if environment_id:
                    cur.execute("update environment set count=count+1 where id='{}'".format(environment_id))
                
                    
        conn.commit()

        public.writeFile(flag_file, "yes")

        if envir_count > 0:
            init_environment_flag = os.path.join(FLAG_DIR, "environment_inited")
            public.writeFile(init_environment_flag, "yes")
    except Exception as e:
        print("初始化配置数据库失败:"+str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_panel_php_environments():
    """获取已安装php环境

    面板安装php路径：/www/server/php
    """

    envirs = []
    base_dir = "/www/server/php"
    dirs = os.listdir(base_dir)
    base_name = "PHP"
    for _dir in dirs:
        main = None
        version = None
        version_file = os.path.join(base_dir, _dir, "version.pl")
        if os.path.isfile(version_file):
            version = public.readFile(version_file)
        else:
            continue

        main_file = os.path.join(base_dir, _dir, "bin", "php")
        if os.path.isfile(main_file):
            main = main_file

        if version and main:
            environment_name = base_name + version.strip()
            envirs.append({
                "environment_name": environment_name,
                "main": main,
                "remark": "通过堡塔面板安装的{}，版本为{}".format(base_name, version)
            })

    return envirs

def get_python_environments():
    """获取python版本

    获取/usr/bin目录下的所有python版本，除此之外会额外检查当前插件运行的python版本是否
    被添加。
    """

    base_dir = "/usr/bin"
    envirs = []
    current_main = sys.executable
    current_environment_has_been_added = False
    current_python_remark = "当前插件执行环境"
    main_records = []
    reg = r'^(python|btpython)[0-9.]*$'
    import re
    for _dir in os.listdir(base_dir):
        if re.match(reg, _dir):
            if _dir.find("config") >= 0:
                continue
            main = os.path.join(base_dir, _dir)
            if not os.access(main, os.X_OK):
                continue
            if main in main_records:
                continue
            else:
                main_records.append(main)

            result = "".join(public.ExecShell(main + " -V"))
            if result.find("usage") != -1 or result.find("Usage") != -1:
                continue
            result = result.split()
            version = result[1]
            environment_name = "".join(result)
            if current_main == main:
                remark = current_python_remark
                current_environment_has_been_added = True
            else:
                remark = "Python执行环境，版本为{}".format(version)
            envirs.append({
                "environment_name": environment_name,
                "main": main,
                "remark": remark,
            })

    if not current_environment_has_been_added:
        current_version = sys.version.split()[0]
        envirs.append({
            "environment_name": "BTPython" + current_version,
            "main": current_main,
            "remark": current_python_remark
        })

    return envirs

def get_null_environment():
    return [{
        "environment_name": "Null",
        "main": "/dev/null",
        "remark": "空白运行环境, 适合不需要附加运行环境的应用。"
    }]


def init_environments():
    """初始化应用环境"""
    from btappmanager_main import EnvironmentManager
    flag_file = os.path.join(FLAG_DIR, "environment_inited")
    if os.path.exists(flag_file):
        print("flag true.")
        return True

    php_envirs = python_envirs = []
    try:
        php_envirs = get_panel_php_environments()
    except:
        pass

    try:
        python_envirs = get_python_environments()
    except:
        pass

    environments = php_envirs + python_envirs + \
                       get_null_environment()

    em = EnvironmentManager()
    for environment in environments:
        print("添加系统环境：")
        print(environment)
        res = em.add(environment)
        if res["status"]:
            print("添加成功！")
    public.writeFile(flag_file, "yes")

def init_config():
    try:
        inited = init_config_db()
        if not inited:
            print("初始化失败。")
            return False

        sync_db()
        init_environments()
        db = public.M("manager_config").dbfile(NAME)
        if not db.where("name=?", "manager").count():
            db.add("name, log_dir", ("manager", os.path.join(PLUGIN_DIR, "logs")))
    except Exception as e:
        print("初始化异常: {}".format(e))

if __name__ == "__main__":
    init_config()
    # init_config_db()
    # sync_db()