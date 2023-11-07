#!/usr/bin/python
# coding: utf-8
# ---------------------------------------
# 堡塔应用管理器 - 应用持久化运行和管理
# Author:
#    backend: linxiao
#    frontend: akai
# ---------------------------------------
from __future__ import print_function, absolute_import, division

import json
import os, sys, io
import signal
import uuid
import time

try:
    import configparser as configparser
except:
    import ConfigParser as configparser

from configparser import RawConfigParser

BASE_PATH = "/www/server/panel"
NAME = "btappmanager"
PLUGIN_DIR = os.path.join(BASE_PATH, "plugin", NAME)
CONFIG_FILE = os.path.join(PLUGIN_DIR, "{}.conf".format(NAME))
DB_NAME = NAME+".db"
CONFIG_DB = os.path.join(BASE_PATH, "data", DB_NAME)
DEFAULT_PYTHON_PATH = "/www/server/panel/pyenv/bin/python3.7"
MONITOR_PID_FILE = os.path.join(PLUGIN_DIR, "monitor.pid")

os.chdir(BASE_PATH)
sys.path.insert(0, "class/")

import public

import psutil
import threading
import logging
import logging.handlers
import logging as syslogging

DEBUG = True
global_logger = None

_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

if is_py2:
    reload(sys)
    sys.setdefaultencoding('utf-8')


class Logger:
    _logger = None

    @classmethod
    def instance(cls, *args, **kwargs):
        name = kwargs.get("name")
        log_file = kwargs.get("log_file")
        log_level = kwargs.get("log_level")
        if not cls._logger or cls._logger.name != kwargs.get("name"):
            logger = syslogging.getLogger(name)
            # if not logger.handlers:
            formatter = syslogging.Formatter(
                "%(asctime)s - %(levelname)s: %(message)s")

            logger.setLevel(log_level)
            fh = syslogging.FileHandler(log_file, "a")
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            if logger.handlers:
                for handler in logger.handlers:
                    handler.close()
                    logger.handlers.remove(handler)

            logger.addHandler(fh)
            cls._logger = logger

        return cls._logger

class Tool:

    def __init__(self):
        self.lock = threading.Lock()

    def expand(self, s, expansions):
        """解析扩展字符"""
        return s % expansions

    def get_uuid(self):
        return str(uuid.uuid1()).replace("-", "")

    def read_config(self, config_file):
        """读取配置文件"""
        try:
            self.lock.acquire()
            conf = RawConfigParser()
            if not os.path.exists(config_file):
                with io.open(config_file, "w", encoding="utf-8"):
                    pass
            with io.open(config_file, "r", encoding="utf-8") as fp:
                conf.read_file(fp, config_file)
            return conf
        except Exception as e:
            pass
        finally:
            self.lock.release()

    def write_config(self, config_file, conf):
        try:
            self.lock.acquire()
            with io.open(config_file, "w", encoding="utf-8") as fp:
                conf.write(fp)
        except:
            pass
        finally:
            self.lock.release()

    def clear_log(self, log_dir, name, backups):
        """按照备份数量删除日志文件"""

        # clear backup log
        count = backups
        while count > 0:
            file_name = os.path.join(log_dir, "{}-{}.log".format(name, count))
            if os.path.isfile(file_name):
                os.remove(file_name)
            count -= 1

        # clear error log
        error_log_file = os.path.join(log_dir, "{}_err.log".format(name))
        print("Clear error log file: {}".format(error_log_file))
        with io.open(error_log_file, "w", encoding="utf-8") as fp:
            fp.write(u"")

        # clear base log
        base_file_name = os.path.join(log_dir, "{}.log".format(name))
        print("Clear log file: {}".format(base_file_name))
        with io.open(base_file_name, "w", encoding="utf-8") as fp:
            fp.write(u"")
        return True

    def get_global_logger(self, name, logfile, maxbytes=5*1024,
                   backups=2, log_level=logging.DEBUG):
        # 初始化日志记录器
        logfile = self.init_logfile(
            logfile,
            {"plugin_dir": PLUGIN_DIR},
            logfile_max_size=self.get_size(maxbytes),
            backups=backups,
        )
        return Logger.instance(name=name, log_file=logfile, log_level=log_level)

    def parse_str_variables(self, str_vars):
        """字符形式的环境变量解析

        :param str_vars 字符形式的键值对。期望格式参考：foo=abc;f002=edf;
        :return dict()
        """
        variables = {}
        error_msg = "变量字符串格式不正确。"
        try:
            if str_vars and str_vars != "None":
                pair_arr = str_vars.split(";")
                for pair in pair_arr:
                    if pair.find("=") <= 0:
                        raise ValueError("未找到=号。")
                    key, value = pair.split("=")
                    variables.update({key: value})
        except:
            print("Str vars:")
            print(str_vars)
            raise ValueError(error_msg)
        return variables

    def split_args(self, args):
        """分隔参数，处理包含的特殊空白字符"""
        if args.find(u"\xa0") != -1:
            args = args.split(u"\xa0")
        else:
            args = args.split(u" ")
        return [x.strip() for x in args if x]

    def parse_str_args(self, str_args):
        """字符形式的命令行参数

        :param str_args 字符形式的运行参数。期望格式（以空格分隔）：--f --foo2=efg -p
        :return []
        """
        try:
            if str_args:
                if str_args != "None":
                    return self.split_args(str_args)
        except:
            raise ValueError("参数字符串格式不正确。")
        return []

    def get_size(self, value, default=None):
        """根据带单位的文件大小文本转换成数值形式
        
        :param value 字符串形式的文件大小，支持MB、KB。
        :param default 默认值
        :return 数值形式的字节数大小
        """

        if type(value) == int:
            return value

        value = value.upper()
        size = 0
        try:
            size = float(value)
        except ValueError:
            try:
                if value.find("MB") > 0:
                    size = float(value[:value.find("MB")]) * 1024 * 1024
                    return size

                if value.find("KB") > 0:
                    size = float(value[:value.find("KB")]) * 1024
                    return size
            except:
                pass
            return default
        return size

    def get_current_text_date(self):
        import datetime
        return datetime.datetime.now().strftime("%y%m%d %H:%M:%S")

    def parse_text_date(self, text_date):
        import datetime
        return datetime.datetime.strptime(text_date, "%y%m%d %H:%M:%S")

    def init_logfile(self, filename, expansions={},
                     logfile_max_size=1024 * 1024 * 50, backups=2):
        """初始化日志文件
        
        :param filename 基础文件名称
        :param expansions 变量扩展参数和值
        :param logfile_max_size 单个文件的最大大小限制
        :param backups 备份数量
        :return 日志文件路径
        """
        import io
        logfile = self.expand(filename, expansions)
        logfile = os.path.abspath(logfile)
        dirname = os.path.dirname(logfile)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if not os.path.exists(logfile):
            with io.open(logfile, "w", encoding="utf-8"):
                pass
        else:
            if os.path.getsize(logfile) >= logfile_max_size:
                # 日志文件备份逻辑
                # 根据备份数量backups对日志文件进行拷贝备份，备份文件名按照数字后缀的方式
                # 命名，并且数字的升序表示备份文件内容的产生由近到远。
                # 比如： logfile: test.log, backups: 2
                # 如果记录到一定时间总共会存在三个日志文件: test.log test-1.log
                # test-2.log, 并且test.log是当前最新的日志记录，test-2.log的日志内容是产
                # 生时间最久的。
                # 实现逻辑：
                # 1. 查找拷贝文件的边界。
                # 2. 循环执行拷贝。
                # 拷贝输出记录(backups>=3)：
                # Copy D:\test-2.log to D:\test-3.log
                # Copy D:\test-1.log to D:\test-2.log
                # Copy D:\test.log to D:\test-1.log
                # 3. 清空当前文件，开始记录新的内容。

                # find existing files
                num_of_backup = 0
                log_border = -1
                while backups > num_of_backup:
                    _filename, suffix = os.path.splitext(logfile)
                    next_num_suffix = num_of_backup + 1
                    new_log_file = _filename + "-%d" % next_num_suffix + suffix
                    if not os.path.exists(new_log_file):
                        log_border = next_num_suffix
                        break
                    else:
                        num_of_backup += 1
                        if num_of_backup >= backups:
                            log_border = backups
                            break

                if DEBUG:
                    print("Log border:")
                    print(log_border)

                # copy files cyclically
                from shutil import copyfile
                for i in range(log_border, 0, -1):
                    _filename, suffix = os.path.splitext(logfile)
                    previous_num_suffix = i - 1
                    if previous_num_suffix == 0:
                        previous_log_file = logfile
                    else:
                        previous_log_file = _filename + "-%d" % previous_num_suffix + suffix
                    new_log_file = _filename + "-%d" % i + suffix

                    if DEBUG:
                        print("Copy {} to {}".format(previous_log_file,
                                                     new_log_file))
                    copyfile(previous_log_file, new_log_file)

                # clear logs
                with io.open(logfile, "w", encoding="utf-8") as fp:
                    pass
                    fp.write(u"")
                    # fp.write("-"*20 + "OVERWRITE LOG %d" % round + "-"*20)
        return logfile
        
class NewConfigParser(RawConfigParser):
    def optionxform(self, str):
        """保持配置文件节点和选项的大小写敏感"""
        return str


class GlobalConfig:
    log_dir = os.path.join(PLUGIN_DIR, "logs")
    logfile_maxbytes = "5MB"
    logfile_backups = 2
    monitor_frequency = 20
    monitor_app = True
    section_name = "global"

    first_run = True

    def __init__(self):
        print("初始化全局配置。")
        self.config_file = CONFIG_FILE

        conf = self.get_global_config()
        if not conf:
            return
        # 日志文件路径
        self.log_dir = conf.get("log_dir", self.log_dir)
        # 单个日志文件大小最大限制(bytes)
        self.logfile_maxbytes = conf["logfile_maxbytes"]
        # 日志文件备份数量
        self.logfile_backups = conf.get("logfile_backups")
        # 是否开启监控应用
        self.monitor_app = conf.get("monitor_app")
        # 监控频率
        self.monitor_frequency = conf.get("monitor_frequency")
        self.first_run = conf.get("first")

        self.init_global_logger()

    def get_global_config(self):
        """获取插件配置参数"""
        conf = {}
        try:
            if not os.path.exists(CONFIG_DB):
                return conf
            db = public.M('manager_config').dbfile(NAME)
            res = db.field('log_dir,logfile_maxbytes,logfile_backups,monitor_app,monitor_frequency').where('name=?', "manager").find()
            if type(res) == str:
                return conf
            if res:
                return res
        except Exception as e:
            print("获取插件配置出现错误:" + str(e))
        return conf

    def update(self, kwargs):
        """更新全局配置"""

        rowcount = public.M("manager_config").dbfile(NAME).update(kwargs)
        if rowcount>0:
            return True
        return False

    def init_global_logger(self):
        global global_logger
        if global_logger is None:
            tool = Tool()
            global_logger = tool.get_global_logger(
                NAME, os.path.join(PLUGIN_DIR, "logs", "{}.log".format(NAME)),
                self.logfile_maxbytes, self.logfile_backups, logging.INFO)
            return global_logger

class AppStatus:
    Initial = "initial"
    Stopping = "stopping"
    Stopped = "stopped"
    Starting = "starting"
    Running = "running"
    Abnormal = "abnormal"
    Stopfailed = "stop_failed"
    Shutdown = "shutdown"

    _status = {
        "initial": Initial,
        "stopping": Stopping,
        "stopped": Stopped,
        "starting": Starting,
        "running": Running,
        "stop_failed": Stopfailed,
        "shutdown": Shutdown,
        "abnormal": Abnormal
    }

    @classmethod
    def get_status(cls, key):
        return cls._status[key]

class Environment:
    id = -1
    name = None
    main = ""
    verison = ""
    environment_args = ""
    app_args = ""
    _variables = {}
    remark = ""
    count = 0  # 引用该环境的应用数量

    @property
    def variables(self):
        return self._variables

    @variables.setter
    def variables(self, str_vars):
        if Tool().parse_str_variables(str_vars):
            self._variables = str_vars
        else:
            self._variables = ""

    def get_path(self):
        if self.main == "/dev/null":
            return ""
        return self.main
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "main": self.main,
            "version": self.verison,
            "environment_args": self.environment_args,
            "app_args": self.app_args,
            "variables": self.variables,
            "count": self.count,
            "remark": self.remark
        }

    def __str__(self):
        return self.name


class EnvironmentManager:

    def __init__(self):
        gc = GlobalConfig()
        gc.init_global_logger()

    def add(self, env_dict):
        """添加环境配置

        :param env 环境信息
        """

        if "name" not in env_dict.keys():
            if "environment_name" in env_dict.keys():
                env_dict["name"] = env_dict.get("environment_name")
                del env_dict["environment_name"]

        environment_name = env_dict.get("name")
        db = public.M("environment").dbfile(NAME)
        if not db.where("name=?", environment_name).count():
            if not "id" in env_dict.keys():
                env_dict["id"] = Tool().get_uuid()
            key = ",".join(env_dict.keys())
            param = tuple(env_dict.values())
            print("add res:")
            print(key, param)
            add_res = db.add(key, param)
            print(add_res)
            if type(add_res) == int and add_res > 0:
                return {
                    "status": True,
                    "msg": "添加成功！",
                    "new_id": env_dict["id"]
                }
            return public.returnMsg(False, "添加失败")
        else:
            return public.returnMsg(False, "目标环境已存在，请勿添加同名环境。")

    def find_environment(self, id, name=None):
        """查找环境"""

        db = public.M("environment").dbfile(NAME)
        if id:
            find_res = db.where("id=?", (id,)).find()
        elif name:
            find_res = db.where("name=?", (name,)).find()

        if find_res:
            env = Environment()
            conf = find_res
            env.id = conf.get("id")
            env.name = conf.get("name")
            env.main = conf.get("main")
            env.verison = conf.get("verison")
            env.environment_args = conf.get("environment_args")
            env.app_args = conf.get("app_args")
            env.variables = conf.get("variables")
            env.remark = conf.get("remark")
            env.count = conf.get("count")
            return env
        return None

    def update(self, env_dict):
        """修改环境信息"""
        if "id" not in env_dict.keys():
            return public.returnMsg(False, "参数错误")

        print("update env dict:")
        print(env_dict)
        id = env_dict["id"]
        env = self.find_environment(id)
        if not env:
            return public.returnMsg(False, "目标环境不存在！")

        if "environment_name" in env_dict.keys():
            env_dict["name"] = env_dict["environment_name"]
            del env_dict["environment_name"]
        del env_dict["id"]
        db = public.M("environment").dbfile(NAME)
        rows = db.where("id=?", id).update(env_dict) 
        print("update rows:")
        print(rows)
        if rows == 1:
            msg = "{} 修改环境信息成功！".format(env.name)
            return public.returnMsg(True, msg)
        msg = "{} 修改环境信息失败！".format(env.name)
        global_logger.error(msg)
        return public.returnMsg(False, msg)

    def delete(self, id):
        """删除环境信息"""
        env = self.find_environment(id)
        if env is not None:
            if env.count > 0:
                msg = "环境: {} 被其他应用引用，无法删除!".format(env.name)
                logging.error(msg)
                return public.returnMsg(False, msg)

            db = public.M("environment").dbfile(NAME)
            rows = db.delete(id=id)
            if rows>0:
                msg = "环境: {} 已被删除。".format(env.name)
                logging.info(msg)
                return public.returnMsg(True, msg)
            msg = "环境: {} 删除失败！".format(env.name)
            logging.info(msg)
            return public.returnMsg(False, msg)
        else:
            msg = "删除的目标环境：{} 不存在。".format(id)
            logging.info(msg)
            return public.returnMsg(False, msg)

    def list_environments(self, pager=True, page=1, page_size=20, **kwargs):
        """环境列表
        :param pager: 是否分页
        :param page: int 页
        :param page_size: int 单页结果数
        """
        db = public.M("environment").dbfile(NAME)
        if "environment_name" in kwargs.keys():
            filter_by_name = kwargs.get("environment_name")
            db = db.where("name=?", (filter_by_name,))
        import copy

        if pager:
            total_sql = copy.deepcopy(db)
            total = total_sql.count()
            page_start = (page - 1) * page_size
            limit = "{},{}".format(page_start, page_size)
            data_sql = db.limit(limit).order("count desc")

            # print("get data:")
            data = data_sql.select()
        else:
            data = db.select()
            total = len(data)

        envirs = []
        for conf in data:
            env = Environment()
            env.id = conf.get("id")
            env.name = conf.get("name")
            env.main = conf.get("main")
            env.verison = conf.get("verison")
            env.environment_args = conf.get("environment_args")
            env.app_args = conf.get("app_args")
            env.variables = conf.get("variables")
            env.remark = conf.get("remark")
            env.count = conf.get("count")
            # logging.info("Environment name: " + name)
            # 统计应用引用数量
            envirs.append(env)

        total_page = 1
        if pager:
            total_page = total // page_size
            if total % page_size > 0:
                total_page += 1
        return envirs, total_page, total

class App:
    NOPID = -1
    id = None
    name = ""
    pid = NOPID
    environment_id = None  # 环境
    environment = None  # 环境对象
    main = ""  # 主文件
    args = ""  # 启动参数
    exec_dir = ""  # 执行目录
    daemon = True
    _environment_variables = ""  # 环境变量
    cpu_percent = 0
    mem_bytes = 0
    start_at = 0
    running_day = 0

    # log
    redirect_stderr = True
    bufsize = 1  # 日志输出缓冲控制，1：行缓冲，0：不缓冲，其他：缓冲字节大小
    log_dir = ""
    stdout_logfile = "{}.log"
    stderr_logfile = "{}_err.log"
    max_retry = 10
    _logger = None
    logfile_maxbytes = 1024 * 1024 * 5
    logfile_backups = 2
    log_level = logging.DEBUG

    port = -1

    config_file = ""
    start_at = None
    user = ""

    def init_app(self, app_dict, load_environment=True):
        """加载应用配置信息

        :param app_dict 包含以下字段
        :param name 应用名称，同一个配置文件下唯一
        :param environment_name 环境名称
        :param main 启动主文件
        :param args 启动参数
        :param exec_dir 运行时目录
        :param daemon 进程守护
        :param environment_variables 环境变量配置
        :param log_dir 标准输出日志文件, 文件路径支持当前目录和应用名称作为变量配置。
            默认为%(plugin_dir)s/logs/%(name)s.log，变量的格式参考: %(var)s。
        :param redirect_stderr 是否转发错误日志到标准输出
        :param max_retry 自动重启时的最大重试次数
        :return App / None
        """
        if "id" in app_dict.keys():
            self.id = app_dict.get("id")
        self.name = app_dict.get("name")
        if "environment_id" in app_dict.keys():
            environment_id = app_dict.get("environment_id")
            self.environment_id = environment_id
            if load_environment:
                self.environment = EnvironmentManager() \
                    .find_environment(environment_id)

        self.main = app_dict.get("main")
        self.args = app_dict.get("args", "")
        self.exec_dir = app_dict.get("exec_dir")
        self.daemon = app_dict.get("daemon", True)
        self.environment_variables = app_dict.get("environment_variables", "")
        self.redirect_stderr = app_dict.get("redirect_stderr")

        log_dir = app_dict.get("log_dir", None)
        gc = GlobalConfig()
        if not log_dir:
            log_dir = gc.log_dir
        self.log_dir = log_dir
        self.max_retry = app_dict.get("max_retry", 10)
        status = app_dict.get("status", AppStatus.Initial)
        self.status = status
        logfile_backups = app_dict.get("logfile_backups")
        if not logfile_backups:
            self.logfile_backups = gc.logfile_backups
        logfile_maxbytes = app_dict.get("logfile_maxbytes")
        if not logfile_maxbytes:
            self.logfile_maxbytes = gc.logfile_maxbytes
        self.user = app_dict.get("user", "")
        self.remark = app_dict.get("remark", "")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "main": self.main,
            "environment_id": self.environment_id,
            "args": self.args,
            "exec_dir": self.exec_dir,
            "daemon": self.daemon,
            "environment_variables": self.environment_variables,
            "redirect_stderr": self.redirect_stderr,
            "log_dir": self.log_dir,
            "max_retry": self.max_retry,
            "status": self.status,
            "logfile_maxbytes": self.logfile_maxbytes,
            "logfile_backups": self.logfile_backups,
            "user": self.user,
            "remark": self.remark
        }

    @property
    def environment_variables(self):
        return self._environment_variables

    @environment_variables.setter
    def environment_variables(self, str_vars):
        if Tool().parse_str_variables(str_vars):
            self._environment_variables = str_vars
        else:
            self._environment_variables = ""

    @property
    def logger(self):
        if self._logger:
            return self._logger

        logger = logging.getLogger(self.id)
        # if not global_logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s: %(message)s")

        stdout_logfile = os.path.join(self.log_dir, self.stdout_logfile.format(self.id))
        global_logger.setLevel(self.log_level)
        fh = logging.handlers.RotatingFileHandler(
            stdout_logfile,
            mode="a",
            maxBytes=self.logfile_maxbytes,
            backupCount=self.logfile_backups)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        self._logger = logger
        return self._logger

    def merge_environment_variables(self):
        """合并环境配置的环境变量

        APP的环境变量配置优先级高于环境
        """
        tool = Tool()
        variables = {}
        if self.environment and self.environment.variables:
            environment_variables = tool.parse_str_variables(
                self.environment.variables)
            variables = environment_variables

        if self.environment_variables:
            app_variables = tool.parse_str_variables(self.environment_variables)
            variables.update(app_variables)

        return variables

    def merge_environment_args(self):
        """合并环境配置运行参数"""
        tool = Tool()
        e_args_arr = []
        args_arr = []
        if self.environment and self.environment.app_args:
            e_args_arr = tool.parse_str_args(self.environment.app_args)
        if self.args:
            args_arr = tool.parse_str_args(self.args)
        new_args_arr = args_arr + e_args_arr
        return new_args_arr

    def get_logfile(self):
        """根据全局配置获取日志文件路径"""
        return os.path.join(self.log_dir, self.stdout_logfile.format(self.id))

    def get_pid_file(self):
        pid_dir = os.path.join(PLUGIN_DIR, "pids")
        if not os.path.exists(pid_dir):
            os.mkdir(pid_dir)
        return os.path.join(pid_dir, self.id+".pid") 

    def start(self, waitsecs=3):
        """开启子进程
        """
        try:
            tool = Tool()
            if DEBUG:
                global_logger.info("正在启动App: {}".format(self.name))
            running_status = [
                AppStatus.Running,
                AppStatus.Starting,
            ]
            if self.is_running() and self.get_status() not in running_status:
                raise RuntimeError("应用正在运行。")

            ori_status = self.status
            env_path = ""
            environment_args = []
            app_args = self.merge_environment_args()
            if self.environment:
                env_path = self.environment.get_path()
                environment_args = tool.parse_str_args(
                    self.environment.environment_args)
            # 根据是否依赖环境，拼接不同的执行参数
            if env_path:
                if environment_args:
                    cmd = [env_path] + environment_args + [self.main] + app_args
                else:
                    cmd = [env_path, self.main] + app_args
            else:
                cmd = [self.main] + app_args
            # 转发日志
            expansions = {"plugin_dir": PLUGIN_DIR, "name": self.id}
            stdout_logfile = os.path.join(
                self.log_dir, 
                self.stdout_logfile.format(self.id)
            )
            logfile_maxbytes = tool.get_size(self.logfile_maxbytes)
            logfile_backups = int(self.logfile_backups)

            tool.init_logfile(
                stdout_logfile, 
                expansions,
                logfile_max_size=logfile_maxbytes,
                backups=logfile_backups
            )
            # print("stdout logfile:")
            # print(stdout_logfile)

            stderr_logfile = None
            stdout_fp = io.open(stdout_logfile, "ab")
            stderr_fp = None
            self.redirect_stderr = True
            if self.redirect_stderr:
                stderr_logfile = stdout_logfile
                stderr_fp = stdout_fp
            else:
                stderr_logfile = os.path.join(
                    self.log_dir, self.stderr_logfile.format(self.id))
                stderr_logfile = tool.init_logfile(
                    stderr_logfile, 
                    expansions,
                    logfile_max_size=logfile_maxbytes,
                    backups=logfile_backups
                )
                stderr_fp = io.open(stderr_logfile, "ab")

            # 开启子进程
            proces_variables = self.merge_environment_variables()
            process_exec_dir = None if not self.exec_dir else self.exec_dir
            if DEBUG:
                print("Check process variables:")
                print(proces_variables)
                print("Check process exec dir:")
                print(process_exec_dir)
                print("Check CMD:")
                print(cmd)
            import subprocess
            proc = psutil.Popen(cmd,
                                cwd=process_exec_dir,
                                env=proces_variables,
                                bufsize=self.bufsize,
                                shell=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

            pidfile = self.get_pid_file()
            pid = proc.pid
            start_time = time.time()
            public.writeFile(pidfile, "{},{},{}".format(pid,AppStatus.Starting,start_time))
            
            started = False
            if DEBUG:
                print("started pid：%d" % proc.pid)

            import select
            if True:
                dataend = False
                sel_timeout = 1.0
                check_count = 0
                exit_normally = True
                while True:
                    # 异常检测
                    if proc.returncode is not None:
                        global_logger.info("应用: {} 异常退出,returncode: {}。进程ID: {}。".format(self.name, proc.returncode, str(pid)))
                        exit_normally = False
                        break
                    
                    # 退出检测
                    if dataend:
                        break

                    # 监听日志输出
                    proc.poll()
                    dataend = False

                    if True:
                        ready = select.select([proc.stdout], [], [], sel_timeout)
                        if check_count >= 3:
                            sel_timeout = 1.0
                            if not started:
                                pid = proc.pid
                                start_time = time.time()
                                ret = self.change_status(AppStatus.Running)
                                if not ret:
                                    global_logger.error("启动应用时，修改应用运行状态失败！")
                                    break
                                else:
                                    public.writeFile(pidfile, "{},{},{}".format(pid,AppStatus.Running,start_time))
                                    global_logger.info("应用: {} 已成功启动。进程ID: {}。".format(self.name, str(pid)))
                                    started = True
                        else:
                            # print("check count: {}".format(check_count))
                            check_count += 1
                        # if proc.stderr in ready[0]:
                        #     data = proc.stderr.read(1)
                        #     if len(data) > 0:
                        #         print("error data: {}".format(data))
                            # handle_stderr_data(data)

                        if proc.stdout in ready[0]:
                            data = proc.stdout.read(1)
                            if len(data) == 0:
                                dataend = True
                            else:
                                stdout_fp.write(data)
                                stdout_fp.flush()
                                # print("file size:{}/max: {}".format(os.path.getsize(stdout_logfile), logfile_maxbytes))
                                # 日志文件超过指定大小，转移日志
                                if os.path.getsize(stdout_logfile) >= logfile_maxbytes:
                                    stdout_fp.close()

                                    tool.init_logfile(
                                        stdout_logfile, 
                                        expansions=expansions,
                                        logfile_max_size=logfile_maxbytes,
                                        backups=logfile_backups
                                    )
                                    stdout_fp = io.open(stdout_logfile, "ab")
                        
            end_time = time.time()
            pid = -1
            if not started:
                if not exit_normally and ori_status == AppStatus.Abnormal:
                    public.writeFile(pidfile, "{},{},{}".format(pid, AppStatus.Abnormal,end_time))
                    self.change_status(AppStatus.Abnormal)
                    global_logger.info("应用: {} 尝试恢复启动失败，详情请查看应用日志。".format(self.name))
                else:
                    public.writeFile(pidfile, "{},{},{}".format(-1, AppStatus.Stopped,end_time))
                    self.change_status(AppStatus.Stopped)
                    global_logger.error("应用：{} 启动失败，详情请查看应用日志。".format(self.name))
            else:
                if not exit_normally:
                    public.writeFile(pidfile, "{},{},{}".format(pid, AppStatus.Abnormal,end_time))
                    self.change_status(AppStatus.Abnormal)
                    global_logger.info("应用: {} 异常退出。".format(self.name))
                else:
                    # 手动终止检测
                    status = self.get_status()
                    if status == AppStatus.Stopping:
                        public.writeFile(pidfile, "{},{},{}".format(pid, AppStatus.Stopped,end_time))
                        global_logger.info("应用: {} 已停止运行。".format(self.name))
        except Exception as e:
            error_msg = "应用启动出错: {}".format(str(e))
            global_logger.error(error_msg)
            pidfile = self.get_pid_file()
            public.writeFile(pidfile, "{},{},{}".format(-1, AppStatus.Abnormal,time.time()))
            self.change_status(AppStatus.Abnormal)
        finally:
            try:
                stderr_fp.close()
            except:
                pass
            try:
                stdout_fp.close()
            except:
                pass
        return False

    def refresh_running_info(self):
        """刷新运行信息

        包括：端口号、CPU占用、内存占用、IO读取速度。
        """
        global_logger.info("refresh before status: {}".format(self.status))
        self.get_status()
        if self.is_running():
            self.get_port()
            self.get_load_info()
        global_logger.info("refresh after status: {}".format(self.status))

    def change_status(self, status):
        if not status:
            global_logger.error("status is null.")
            status = AppStatus.Initial
        db = public.M("app").dbfile(NAME)
        rows = db.where("id=?", self.id).update(
            {"status": status}
        )
        if rows == 1:
            self.status = status
            return True
        global_logger.error("状态修改异常: {}".format(rows))
        return False

    def stop(self, waitsecs=5, status=None):
        """停止应用

        停止APP进程后，删除掉APP配置文件节点下的PID。
        """

        exited = False
        
        pid = -1
        pid_file = self.get_pid_file()
        if not self.is_running():
            global_logger.info("The process ({}/{}) does not exist."
                             .format(self.name, self.pid))
            exited = True
        else:
            if not status:
                status = AppStatus.Stopped
                global_logger.info("应用: {} 正在停止...".format(self.name))
            else:
                global_logger.info("应用: {} 正在停止，将标记为{}状态。".format(self.name, status))

            if not os.path.exists(pid_file):
                return False

            pid_content = public.readFile(pid_file)
            pid, _status, start_time = pid_content.split(",")

            pid_content_new = "{},{},{}".format(pid, AppStatus.Stopping, time.time())
            public.writeFile(pid_file, pid_content_new)

            pid = int(pid)
            process = psutil.Process(pid)
            process.kill()
            
            count = waitsecs * 10
            exception = None
            if is_py3:
                exception = ChildProcessError
            if is_py2:
                exception = Exception

            while count > 0:
                try:
                    _pid, sts = os.waitpid(pid, os.WNOHANG)
                except exception as e:
                    exited = True
                    break
                if sts == 9:
                    exited = True
                    break

                if os.WEXITSTATUS(sts):
                    exited = True
                    break

                time.sleep(waitsecs / 10)
                count -= 1

            # print("Check pid status:")
            # print(exited)

        # TODO 检验停止异常处理和结果判定，是否满足大部分的进程停止
        if exited:
            global_logger.info("应用: {} 已停止。".format(self.name))
            if status:
                pid_content = "{},{},{}".format(pid, status, time.time())
                self.change_status(status)
            return True
        else:
            pid_content = "{},{},{}".format(pid, AppStatus.Stopfailed, time.time())
            self.change_status(AppStatus.Stopfailed)
            public.writeFile(pid_file, pid_content)
        return False

    def get_status(self):
        pid_file = self.get_pid_file()
        pid_content = public.readFile(pid_file)
        status = self.status
        global_logger.info("get status: {}".format(status))

        if status == AppStatus.Running:
            if pid_content and pid_content.find(",") != -1:
                pid, status, _time = pid_content.split(",")
                pid = int(pid)
                if pid>0 and psutil.pid_exists(pid):
                    self.pid = pid
                    self.start_at = float(_time)
                else:
                    self.status = AppStatus.Stopped
                    pid_content = "{},{},{}".format(-1, status, time.time())
                    public.writeFile(pid_file, pid_content)
                    return self.status
            else:
                self.status = AppStatus.Stopped
                return self.status
        return status 

    def is_running(self):
        """运行状态判断"""
        self.get_status()
        if self.status == AppStatus.Running:
            return True
        return False

    def get_load_info(self):
        """负载信息"""
        pidfile = self.get_pid_file()
        if not os.path.exists(pidfile):
            return

        pid_content = public.readFile(pidfile)
        pid = -1
        if pid_content and pid_content.find(",") != -1:
            pid, status, _start_at = pid_content.split(",")
            _process = psutil.Process(int(pid))
            self.cpu_percent = _process.cpu_percent(interval=0.1)
            self.mem_bytes = _process.memory_percent(memtype="rss")
            self.start_at = float(_start_at)
            now = time.time()
            self.running_day = int((now - self.start_at) // 3600)

    def get_port(self):
        """通过pid获取端口号"""
        port = -1
        try:
            cmd = 'netstat -anp | grep ' + str(self.pid)
            if DEBUG:
                print(cmd)
            a = os.popen(cmd)
            text = a.read()
            first_line = text.split(':')
            ab = first_line[1]
            cd = ab.split(' ')
            port = int(cd[0])
            if DEBUG:
                print(port)
        except:
            pass
        self.port = port

    def clear_log(self):
        tool = Tool()
        tool.clear_log(self.log_dir, self.id, self.logfile_backups)
        return True


class AppManager:
    logfile = "{}.log".format(NAME)
    section_name = NAME
    RetryRecord = {}

    def __init__(self):
        gc = GlobalConfig()
        gc.init_global_logger()
        self.log_dir = gc.log_dir
        self.monitor_frequency = gc.monitor_frequency
        self.logfile_backups = gc.logfile_backups
        self.logfile_maxbytes = gc.logfile_maxbytes

    def add(self, app_dict):
        """添加应用"""
        db = public.M("app").dbfile(NAME)
        if not "name" in app_dict.keys():
            return public.returnMsg(False, "参数错误！")

        app_name = app_dict["name"]
        if not db.where("name=?", app_name).count():
            if not "id" in app_dict.keys():
                app_dict["id"] = Tool().get_uuid()
            app_dict["addtime"] = time.time()
            key = ",".join(app_dict.keys())
            param = tuple(app_dict.values())

            new_environment_id = app_dict["environment_id"]
            em = EnvironmentManager()
            env = em.find_environment(new_environment_id)
            if not env:
                return public.returnMsg(False, "环境不存在！")

            add_res = db.add(key, param)
            if add_res > 0:
                env.count += 1
                res = em.update(env.to_dict())
                if res["status"] != True:
                    return public.returnMsg(False, "添加应用时修改环境引用失败！")

                msg = "应用：{} 添加成功".format(app_dict["name"])
                global_logger.info(msg)
                return {
                    "status": True,
                    "msg": msg,
                    "new_id": app_dict["id"]
                }
            msg = "应用添加失败"
            global_logger.info(msg)
            return public.returnMsg(False, msg)
        else:
            return public.returnMsg(False, "已存在同名应用，请修改应用名称。")

    def find_app(self, id, name=None):
        """查找应用"""
        db = public.M("app").dbfile(NAME)
        sql = db
        if id:
            sql = sql.where("id=?", id)
        elif name:
            sql = sql.where("name=?", name)
        selector = sql.find() 
        app = None
        if selector:
            app = App()
            app.init_app(selector)
        return app

    def delete(self, id):
        """删除不在运行状态的应用
        
        同时减少环境的引用次数"""

        app = self.find_app(id)
        if app is None:
            return public.returnMsg(False, "应用不存在。")

        app_name = app.name
        if app.is_running():
            msg = "应用: {} 正在运行，无法删除。".format(app_name)
            global_logger.error(msg)
            return public.returnMsg(False, msg)

        db = public.M("app").dbfile(NAME)
        del_rows = db.delete(id)
        if del_rows > 0:
            em = EnvironmentManager()
            environment_id = app.environment_id
            env = em.find_environment(environment_id)
            env_dict = env.to_dict()
            env_dict["count"] -= 1
            update_res = em.update(env_dict)
            if update_res["status"] != True:
                return public.returnMsg(False, "删除应用时，减少环境引用数失败！")

            pid_file = app.get_pid_file()
            if os.path.exists(pid_file):
                os.remove(pid_file)

            msg = "应用: {} 已被删除。".format(app_name)
            global_logger.info(msg)
            return public.returnMsg(True, msg)
        else:
            msg = "应用: {} 删除失败！".format(app_name)
            global_logger.info(msg)
            return public.returnMsg(False, msg)

    def update(self, app_dict):
        """更新应用配置信息 """
        if "id" not in app_dict.keys():
            return public.returnMsg(False, "参数错误。")

        id = app_dict["id"]
        app = self.find_app(id)
        if app is None:
            return public.returnMsg(False, "应用不存在。")

        app_name = app.name
        if app.is_running():
            msg = "应用: {} 正在运行，无法修改配置。".format(app_name)
            global_logger.error(msg)
            return public.returnMsg(False, msg)

        if "environment_id" in app_dict.keys():
            new_environment_id = app_dict["environment_id"]
            if new_environment_id != app.environment_id:
                em = EnvironmentManager()
                env = em.find_environment(new_environment_id)
                if env is not None:
                    env.count += 1
                    res = em.update(env.to_dict())
                    if res["status"] != True:
                        return public.returnMsg(False, "修改环境引用失败！")
                    ori_env = em.find_environment(app.environment_id)
                    ori_env.count -= 1
                    res = em.update(ori_env.to_dict())
                    if res["status"] != True:
                        return public.returnMsg(False, "减少原环境引用失败！")
                else:
                    return public.returnMsg(False, "环境不存在！")

        if "app_name" in app_dict.keys():
            app_dict["name"] = app_dict["app_name"]
            del app_dict["app_name"]
        del app_dict["id"]
        db = public.M("app").dbfile(NAME)
        rows = db.where("id=?", id).update(app_dict)
        if rows == 1:
            msg = "应用: {} 配置修改成功。".format(app_name)
            global_logger.info(msg)
            return public.returnMsg(True, msg)
        else:
            if "environment_id" in app_dict.keys():
                environment_id = app_dict["environment_id"]
                if environment_id != app.environment_id:
                    em = EnvironmentManager()
                    env = em.find_environment(environment_id)
                    if env is not None:
                        env.count -= 1
                        res = em.update(env.to_dict())
                        if res["status"] != True:
                            return public.returnMsg(False, "修改应用失败，修改环境引用失败！")
                        ori_env = em.find_environment(app.environment_id)
                        ori_env.count += 1
                        res = em.update(ori_env.to_dict())
                        if res["status"] != True:
                            return public.returnMsg(False, "修改应用失败，减少原环境引用失败！")

        msg = "应用：{} 修改失败！".format(app_name)
        global_logger.error(msg)
        return public.returnMsg(False, msg)

    def list_apps(self, pager=True, page=1, page_size=20, silent=False,
                  **kwargs):
        """应用列表

        TODO 在DEBUG模式加入监控进程的资源占用情况
        :param pager: 是否分页
        :param page: 页码
        :param page_size: 单页结果数
        :param silent：打印输出
        :return 当前的应用列表
        """

        db = public.M("app").dbfile(NAME)
        sql = db
        if "app_name" in kwargs:
            db = db.where("name=?", kwargs["name"])
        import copy
        total_sql = copy.deepcopy(sql)

        page_start = (page - 1) * page_size
        limit = "{},{}".format(page_start, page_size)
        data_sql = db.limit(limit).order("addtime")
        
        total = total_sql.count()
        data = data_sql.select()

        apps = []
        total_page = 1
        if pager:
            total_page = total // page_size
            if total % page_size > 0:
                total_page += 1

        for obj in data: 
            app = App()
            app.init_app(obj)
            apps.append(app)
        return apps, total_page, total

    def run_server(self):
        pid = os.fork()
        if pid:
            sys.exit(0)

        global_logger.info("*" * 40)
        global_logger.info("正在开启后台服务进程。。。")
        self.monitor()
        global_logger.info("后台服务进程已开启。进程ID: {}。".format(os.getpid()))

        # 保存监控进程ID
        monitor_process_id = os.getpid()
        public.writeFile(MONITOR_PID_FILE, str(monitor_process_id))

    def start_app(self, id):
        """开启进程

        进程开启之后，在APP配置文件节点下存储进程ID，用于判断该APP是否已经启动。
        """
        managerd = os.path.join(PLUGIN_DIR, "btappmanagerd")
        app = self.find_app(id)
        # app.change_status(AppStatus.Starting)
        cmd = "{cmd} start {app_id}".format(cmd=managerd, app_id=id)
        result = public.ExecShell(cmd)
        if DEBUG:
            global_logger.info("Exec shell result:")
            global_logger.info(result)
        if result:
            self.RetryRecord.update({app.id: app.max_retry})
            app.change_status(AppStatus.Starting)
            if DEBUG:
                print("Retry record:")
                print(self.RetryRecord)
            return result
        else:
            global_logger.warning("进程{}启动失败！".format(app.name))
        return False

    def stop_app(self, id, waitsecs=-1, status=None):
        """停止运行APP"""
        app = self.find_app(id)
        if waitsecs > 0:
            return app.stop(waitsecs=waitsecs, status=status)
        return app.stop(status=status)

    def restart_app(self, id):
        """重启启动应用"""
        app = self.find_app(id)
        if not app:
            # return public(False, "应用不存在。")
            return False

        global_logger.info("应用：{} 正在重启...".format(app.name))
        ret = self.stop_app(id)
        if ret:
            ret = self.start_app(id)
        return ret

    def waitpid(self, pid, waitsecs):
        """检测进程是否异常退出"""

        count = waitsecs * 10
        exited = False
        import time
        while count > 0:
            _pid, sts = os.waitpid(pid, os.WNOHANG)
            if os.WEXITSTATUS(sts):
                exited = True
                break

            time.sleep(waitsecs / 10)
            count -= 1

        return exited

    def monitor(self):
        """监控已开启的应用运行状态, 在必要的时候自动重启。"""
        while True:
            gc = GlobalConfig()
            gc.init_global_logger()
            apps, _page, _total = self.list_apps(pager=False, silent=True)
            if DEBUG:
                process = psutil.Process(os.getpid())
                global_logger.info(
                    "监控进程：{}|{} 正在守护应用...".format(os.getpid(), process.name()))
            # global_logger.info("监控进程测试输出, 应用数量:{}".format(len(apps)))
            for app in apps:
                # global_logger.info("app status: {}".format(app.status))
                # global_logger.info("app name: {}/daemon: {}/status: {}/ is running: {}".format(app.name, app.daemon, app.status, app.is_running()))
                if app.daemon:
                    if (not app.is_running() and app.status == AppStatus.Running) or (AppStatus.Abnormal == app.status):
                        retry = self.RetryRecord.get(app.id, app.max_retry)
                        if DEBUG:
                            print("Retry:")
                            print(retry)
                        if retry > 0:
                            if retry < app.max_retry:
                                time.sleep(5)
    
                            global_logger.info(
                                "应用 {} 已退出，正在重新启动 ({}/{})."
                                    .format(app.name, str(retry),
                                            str(app.max_retry)))
                            self.start_app(app.id)
                            self.RetryRecord.update({app.id: retry - 1})
                        else:
                            global_logger.info(
                                "App quit abnormally, and retry more than %d times." % app.max_retry)
                    elif not app.is_running() and app.status == AppStatus.Shutdown:
                        global_logger.info("正在开机启动应用 {}".format(app.name))
    
                        pid = os.fork()
                        if not pid:
                            self.start_app(app.id)
                    else:
                        self.RetryRecord.update({app.id: app.max_retry})

            time.sleep(self.monitor_frequency)
            # timer = threading.Timer(self.monitor_frequency, self.monitor)
            # timer.start()

    def start_monitor_service(self):
        """开启监控服务"""
        global_logger.info("正在开启监控服务...")
        start_cmd = "systemctl start btappmanagerd.service"
        public.ExecShell(start_cmd)
        global_logger.info("监控服务已开启。")

    def stop_monitor(self):
        """停止监控服务"""
        global_logger.info("正在停止监控服务...")
        stop_cmd = "systemctl stop btappmanagerd.service"
        public.ExecShell(stop_cmd)
        global_logger.info("监控服务已停止。")

    def enable_monitor(self):
        """启用监控服务和开机启动"""
        global_logger.info("正在启用监控服务...")
        enable_cmd = "systemctl enable btappmanagerd.service"
        public.ExecShell(enable_cmd)
        global_logger.info("监控服务已启用。")

    def enable_shutdown_service(self):
        global_logger.info("正在启用关机监听服务...")
        enable_cmd = "systemctl enable btappmanagerd_shutdown.service"
        public.ExecShell(enable_cmd)
        global_logger.info("关机服务已启用。")

    def disable_monitor(self):
        """取消开机启动"""
        global_logger.info("正在取消监控服务...")
        disable_cmd = "systemctl disable btappmanagerd.service"
        public.ExecShell(disable_cmd)
        global_logger.info("监控服务已取消。")

    def disable_shutdown_service(self):
        """取消关机监听服务"""
        global_logger.info("正在取消关机监听服务...")
        disable_cmd = "systemctl disable btappmanagerd_shutdown.service"
        public.ExecShell(disable_cmd)
        global_logger.info("关机监听服务已取消。")

    def restart_monitor(self):
        """重新启动监控服务"""
        global_logger.info("正在重新启动监控服务...")

        # 读取监控进程ID
        monitor_process_pid = -1
        if os.path.exists(MONITOR_PID_FILE):
            monitor_process_pid = int(public.readFile(MONITOR_PID_FILE))
        global_logger.info("后台进程: {} 将被杀死。".format(monitor_process_pid))
        # 杀掉进程
        if monitor_process_pid > 0:
            try:
                os.kill(monitor_process_pid, signal.SIGKILL)
            except Exception as e:
                if DEBUG:
                    print("结束后台服务进程异常：")
                    print(e)

            global_logger.info("监控服务已重启。")
        else:
            global_logger.info("未找到后台监控进程。")

    def clear_log(self):
        tool = Tool()
        return tool.clear_log(self.log_dir, NAME, self.logfile_backups)

    def clear_app_log(self, id):
        app = self.find_app(id)
        if not app:
            return public.returnMsg(False, "应用不存在")
        ret = app.clear_log()
        if ret:
            msg = "应用：{} 日志已被清理。".format(app.name)
            global_logger.info(msg)
            return public.returnMsg(True, msg)
        else:
            msg = "应用：{} 日志清理出错。".format(app.name)
            global_logger.info(msg)
            return public.returnMsg(False, msg)

    def get_logfile(self):
        return os.path.join(self.log_dir, self.logfile.format(NAME))

    def generate_shutdown_service_config(self):

        systemd_path = "/etc/systemd/system"
        conf = NewConfigParser()
        unit_section = "Unit"
        conf.add_section(unit_section)
        conf.set(unit_section, "Description", "Shutdown BT App Manager")
        conf.set(unit_section, "DefaultDependencies", "no")
        conf.set(unit_section, "Before",
                 "shutdown.target reboot.target halt.target")

        service_section = "Service"
        conf.add_section(service_section)
        conf.set(service_section, "Type", "simple")
        conf.set(service_section, "User", "root")
        conf.set(service_section, "Group", "root")
        exec_path = os.path.join(PLUGIN_DIR, "btappmanagerd")
        conf.set(service_section, "ExecStart", "{} shutdown".format(exec_path))

        install_section = "Install"
        conf.add_section(install_section)
        conf.set(install_section, "WantedBy",
                 "shutdown.target reboot.target halt.target")

        service_file_name = "btappmanagerd_shutdown.service"
        global_logger.info("正在生成 {} 文件...".format(service_file_name))
        service_path = os.path.join(systemd_path, service_file_name)
        with io.open(service_path, "w", encoding="utf-8") as fp:
            conf.write(fp)

        if os.path.exists(service_path):
            global_logger.info("{} 生成成功。".format(service_file_name))
            return True

        global_logger.info("{} 生成失败。".format(service_file_name))
        return False

    def generate_service_config(self):
        """生成btappmanagerd.service文件"""

        systemd_path = "/etc/systemd/system"
        conf = NewConfigParser()
        unit_section = "Unit"
        conf.add_section(unit_section)
        conf.set(unit_section, "Description", "BT App Manager")
        conf.set(unit_section, "After", "network.service")

        service_section = "Service"
        conf.add_section(service_section)
        conf.set(service_section, "Type", "forking")
        conf.set(service_section, "User", "root")
        conf.set(service_section, "Group", "root")
        exec_path = os.path.join(PLUGIN_DIR, "btappmanagerd")
        # conf.set(service_section, "ExecStop", "{} shutdown".format(exec_path))
        conf.set(service_section, "ExecStart",
                 "{} run_server".format(exec_path))
        conf.set(service_section, "Restart", "on-abort")
        # conf.set(service_section, "RestartSec", self.monitor_frequency)

        install_section = "Install"
        conf.add_section(install_section)
        conf.set(install_section, "WantedBy", "multi-user.target")

        global_logger.info("正在生成btappmanagerd.service文件...")
        service_path = os.path.join(systemd_path, "btappmanagerd.service")
        with io.open(service_path, "w", encoding="utf-8") as fp:
            conf.write(fp)

        if os.path.exists(service_path):
            global_logger.info("btappmanagerd.service 生成成功。")
            if self.generate_shutdown_service_config():
                return True

        global_logger.info("配置文件生成失败。")
        return False

    def write_process_white(self):
        """往堡塔加固添加进程白名单"""
        try:
            sysafe_config = "plugin/syssafe/config.json"
            if os.path.isfile(sysafe_config):
                config = None
                config = json.loads(public.readFile(sysafe_config))
                process_white = config["process"]["process_white"]
                btappmanager = "btappmanagerd"
                if btappmanager not in process_white:
                    process_white.append(btappmanager)

                if config:
                    public.writeFile(sysafe_config, json.dumps(config))
        except:
            pass

    def install(self):
        """安装插件操作

        0. 生成服务配置文件。
        1. 启用开机服务和关机监听服务。
        2. 添加进程白名单到堡塔加固。
        3. 启动后台监听服务。
        """

        if self.generate_service_config():
            self.enable_monitor()
            self.enable_shutdown_service()
            self.write_process_white()
            self.start_monitor_service()

    def uninstall(self):
        """卸载插件

        0. 关闭日志文件记录器。
        1. 停止监听进程。 停止正在运行的应用。
        2. 取消开机启动。
        3. 删除服务文件。
        4. 清理日志文件。
        """

        gc = GlobalConfig()
        global global_logger
        gc.init_global_logger()
        if global_logger:
            handlers = global_logger.handlers[:]
            for log_handler in handlers:
                try:
                    log_handler.close()
                    global_logger.handlers.remove(log_handler)
                except Exception as e:
                    print("Exception:")
                    print(e)

        # 停止监听进程
        self.stop_monitor()
        self.disable_monitor()
        self.disable_shutdown_service()

        self.stop_all()

        # 清理服务文件
        service_file = "/etc/systemd/system/btappmanagerd.service"
        if os.path.isfile(service_file):
            os.remove(service_file)
        service_file = "/etc/systemd/system/btappmanagerd_shutdown.service"
        if os.path.isfile(service_file):
            os.remove(service_file)

        # 清理日志文件
        global_logger.info("清理日志文件...")
        rmlog_cmd = "rm -rf {}".format(self.log_dir)
        public.ExecShell(rmlog_cmd)

        db_path = "/www/server/panel/data/%s.db" % NAME
        if os.path.exists(db_path):
            os.remove(db_path)

        global_logger.info("卸载插件完成。")

    def shutdown_all(self):
        """关掉所有应用

        与stop_all的区别：
        1. 先标记所有正在运行应用的状态为shutdown，避免在关机时没有足够的时间去停止应用。
        2. 标记shtudown和stopped区别是shutdown标记后的应用在服务器重启的时候必定会重启，
        stopped的应用有可能在重启后有新的进程ID和原应用进程ID相同。
        """
        global_logger.info("正在停掉所有应用...")
        # tool = Tool()
        # conf = tool.read_config(self.config_file)

        # 标记状态为shutdown
        shutdown_status = AppStatus.Shutdown
        # for section in conf.sections():
        #     if section.startswith("app:"):
        #         app_section = section
        #         pid = conf.getint(app_section, "pid", fallback=-1)
        #         if pid > 0:
        #             conf.set(app_section, "status", shutdown_status)

        # tool.write_config(self.config_file, conf)
        # 停掉所有应用
        return self.stop_all(status=shutdown_status)

    def stop_all(self, status=None):
        """停止所有正在运行的应用

        :param status 标记停止状态
        """

        apps, _, _1 = self.list_apps(pager=False, slient=True)
        for app in apps:
            if app.is_running():
                self.stop_app(app.id, status=status)
        return True

    def shutdown(self):
        """关机或者停止 btappmanagerd.service调用"""

        if self.shutdown_all():
            global_logger.info("所有应用已暂停运行。")
        else:
            global_logger.info("停止所有应用出现异常。")


class btappmanager_main:
    name = NAME
    _appManager = None
    _environmentManager = None

    @property
    def appManager(self):
        if self._appManager is None:
            self._appManager = AppManager()
        return self._appManager

    # 方便测试用
    @appManager.setter
    def appManager(self, am):
        if isinstance(am, AppManager):
            self._appManager = am

    @property
    def environmentManager(self):
        if self._environmentManager is None:
            self._environmentManager = EnvironmentManager()
        return self._environmentManager

    # 方便测试用
    @environmentManager.setter
    def environmentManager(self, em):
        if isinstance(em, EnvironmentManager):
            self._environmentManager = em

    def run_server(self, get):
        # self.appManager.run_server()
        pid = os.fork()
        if pid:
            sys.exit(0)

        self.appManager.monitor()

    def shutdown(self, get):
        self.appManager.shutdown()

    def install(self, get):
        self.appManager.install()

    def add_app(self, get):
        """面板添加应用"""

        app_name = get.app_name
        main = get.main
        environment_id = None
        if "environment_id" in get:
            environment_id = get.environment_id
        args = ""
        if "args" in get:
            args = get.args
        exec_dir = ""
        if "exec_dir" in get:
            exec_dir = get.exec_dir
        environment_variables = ""
        if "environment_variables" in get:
            environment_variables = get.environment_variables
        daemon = True
        if "daemon" in get:
            daemon = True if get.daemon.lower() == "true" else False

        app_dict = {
            "name": app_name,
            "environment_id": environment_id,
            "main": main,
            "args": args,
            "environment_variables": environment_variables,
            "exec_dir": exec_dir,
            "daemon": daemon
        }

        ret = self.appManager.add(app_dict)
        if ret and "status" in ret and ret["status"]:
            return public.returnMsg(True, "应用添加成功！")
        if ret and "msg" in ret:
            return ret
        return public.returnMsg(False, "应用添加失败。")

    def get_app(self, get):
        """根据名称获取应用信息"""

        if "id" not in get:
            return public.returnMsg(False, "参数有误。")

        id = get.id
        app = self.appManager.find_app(id)
        if app:
            response_obj = {
                "id": id,
                "app_name": app.name,
                "environment_id": app.environment_id,
                "main": app.main,
                "args": app.args,
                "exec_dir": app.exec_dir,
                "daemon": app.daemon,
                "environment_variables": app.environment_variables,
            }
            return response_obj
        return public.returnMsg(False, "应用不存在，或者请求参数有误。")

    def start_app(self, get):
        id = get.id
        ret = self.appManager.start_app(id)
        if ret:
            app = self.appManager.find_app(id)
            if app.get_status() == AppStatus.Starting:
                return public.returnMsg(True, "应用正在启动。")
            elif app.status == AppStatus.Running:
                return public.returnMsg(True, "应用启动成功！")
        return public.returnMsg(False, "应用启动失败。")

    def restart_app(self, get):
        name = get.id
        ret = self.appManager.restart_app(name)
        if ret:
            return public.returnMsg(True, "重新启动应用成功！")
        return public.returnMsg(False, "重新启动应用失败。")

    def stop_app(self, get):
        name = get.id
        waitsecs = -1
        if hasattr(get, "waitsecs"):
            waitsecs = get.waitsecs

        try:
            if "waitsecs" in get.keys():
                waitsecs = get.waitsecs
        except:
            pass

        ret = self.appManager.stop_app(name, waitsecs=waitsecs)
        if ret:
            return public.returnMsg(True, "应用已暂停！")
        return public.returnMsg(False, "应用暂停失败。")

    def update_app(self, get):
        """面板更新应用"""
        if "id" not in get:
            return public.returnMsg(False, "参数有误。")
        if "environment_variables" in get:
            try:
                Tool().parse_str_variables(get.environment_variables)
            except:
                return public.returnMsg(False, "更新失败，环境变量格式有误！")

        allow_update_attr = [
            "id",
            "app_name",
            "environment_name",
            "environment_id",
            "main",
            "args",
            "exec_dir",
            "daemon",
            "environment_variables"
        ]
        update_dict = {}
        for attr in allow_update_attr:
            if hasattr(get, attr):
                update_dict[attr] = getattr(get, attr).strip()

        ret = self.appManager.update(update_dict)
        if ret and "status" in ret:
            return public.returnMsg(True, "应用更新成功。")
        if "msg" in ret:
            return ret
        return public.returnMsg(False, "应用修改失败。")

    def delete_app(self, get):
        id = get.id
        ret = self.appManager.delete(id)
        if ret:
            return public.returnMsg(True, "应用已被删除。")
        if "msg" in ret:
            msg = ret["msg"]
            return public.returnMsg(False, msg)
        else: 
            return public.returnMsg(False, "应用无法被删除。")

    def get_app_loginfo(self, get):
        id = get.id
        app = self.appManager.find_app(id)
        logfile = app.get_logfile()
        content = ""
        import io
        if os.path.isfile(logfile):
            with io.open(logfile, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
        return {
            "logfile": logfile,
            "content": content
        }

    def clear_app_log(self, get):
        id = get.id
        ret = self.appManager.clear_app_log(id)
        if ret and "status" in ret and ret["status"]:
            return public.returnMsg(True, "日志清除成功!")
        if ret and "msg" in ret:
            return ret
        return public.returnMsg(False, "日志清理失败。")

    def list_apps(self, get):
        page = int(get.page)
        page_size = int(get.page_size)
        kwargs = {}
        if "app_name" in get:
            kwargs["app_name"] = get.id

        apps, total_page, total = self.appManager.list_apps(
            pager=True, page=page, page_size=page_size, **kwargs)
        data = []
        for app in apps:
            app.refresh_running_info()
            data.append({
                "id": app.id,
                "app_name": app.name,
                "environment_id": app.environment_id,
                "pid": app.pid,
                "status": app.status,
                "exec_dir": app.exec_dir,
                "port": app.port,
                "cpu_percent": app.cpu_percent,
                "mem_bytes": app.mem_bytes,
                "running_time": app.running_day,
                "daemon": app.daemon
            })

        response_obj = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_page": total_page,
            "data": data
        }
        return response_obj

    def list_environments(self, get):
        kwargs = {}
        pager = True
        page = 1
        page_size = 20
        if "page" in get:
            page = int(get.page)
        if "page_size" in get:
            page_size = int(get.page_size)
        if "environment_name" in get:
            kwargs["environment_name"]  = get.environment_name
        if "get_all" in get:
            print("get all.")
            pager = False

        envirs, total_page, total = self.environmentManager.list_environments(
            pager=pager, page=page, page_size=page_size, **kwargs)

        data = []
        for env in envirs:
            d = env.to_dict()
            d["environment_name"] = d["name"]
            del d["name"]
            data.append(d)
        if pager:
            response_obj = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_page": total_page,
            "data": data
            }
        else:
            response_obj = {
            "total": total,
            "page": 1,
            "page_size": 1,
            "total_page": 1,
            "data": data
            }
        return response_obj

    def add_environment(self, get):
        name = get.environment_name
        main = get.main
        environment_args = getattr(get, "environment_args", "")
        app_args = getattr(get, "app_args", "")
        variables = getattr(get, "variables", "")
        try:
            Tool().parse_str_variables(variables)
        except:
            return public.returnMsg(False, "添加失败，环境变量有误。")
        remark = getattr(get, "remark", "")
        env_dict = {
            "name": name,
            "main": main,
            "environment_args": environment_args,
            "app_args": app_args,
            "variables": variables,
            "remark": remark
        }

        try:
            ret = self.environmentManager.add(env_dict)
            if ret and "status" in ret and ret["status"]:
                return public.returnMsg(True, "添加环境成功！")
            if ret and "msg" in ret:
                return ret
        except Exception as e:
            return public.returnMsg(False, str(e))
        return public.returnMsg(False, "添加环境失败。")

    def get_environment(self, get):
        id = get.id
        env = self.environmentManager.find_environment(id)
        response_obj = {
            "id": env.id,
            "environment_name": env.name,
            "main": env.main,
            "environment_args": env.environment_args,
            "app_args": env.app_args,
            "variables": env.variables,
            "remark": env.remark,
        }
        return response_obj

    def update_environment(self, get):
        id = get.id

        try:
            if "variables" in get:
                Tool().parse_str_variables(get.variables)
        except:
            return public.returnMsg(False, "修改失败，环境变量有误。")

        allow_update_attr = [
            "main", "environment_args", "app_args", "variables", "remark", "environment_name"
        ]
        update_kv = {}
        for attr in allow_update_attr:
            if hasattr(get, attr):
                update_kv[attr] = getattr(get, attr)

        update_kv["id"] = id
        ret = self.environmentManager.update(update_kv)
        if ret and ret["status"]:
            return public.returnMsg(True, "修改环境信息成功！")
        if ret and "msg" in ret:
            return ret
        return public.returnMsg(False, "修改环境信息失败。")

    def delete_environment(self, get):
        id = get.id
        ret = self.environmentManager.delete(id)
        if ret and "status" in ret and ret["status"]:
            return public.returnMsg(True, "删除环境信息成功！")
        if ret and "msg" in ret:
            return ret
        return public.returnMsg(False, "环境无法被删除。")

    def get_global_config(self, get):
        return GlobalConfig().get_global_config()

    def set_global_config(self, get):
        allow_update_attr = [
            "log_dir", 
            "logfile_maxbytes",
            "logfile_backups", 
            "monitor_frequency"
        ]
        update_kv = {}
        for attr in allow_update_attr:
            if hasattr(get, attr):
                update_kv[attr] = getattr(get, attr)
        gc = GlobalConfig()
        ret = gc.update(update_kv)
        if ret:
            # 重新启动监控服务 使配置生效
            self.appManager.restart_monitor()
            return public.returnMsg(True, "修改全局配置成功！")
        return public.returnMsg(False, "修改全局配置失败。")

    def get_manager_log(self, get):
        logfile = self.appManager.get_logfile()
        content = ""
        if os.path.isfile(logfile):
            with io.open(logfile, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
        response_obj = {
            "logfile": logfile,
            "content": content,
        }
        return response_obj

    def clear_manager_log(self, get):
        ret = self.appManager.clear_log()
        if ret:
            return public.returnMsg(True, "删除管理器日志成功！")
        return public.returnMsg(False, "删除管理器日志失败。")


if __name__ == "__main__":

    operate = sys.argv[1]
    env_manager = EnvironmentManager()
    manager = AppManager(CONFIG_FILE)
    if operate != "environment":
        if operate == "start":
            # 开启应用
            if len(sys.argv) > 2:
                app_id = sys.argv[2]
                if app_id.lower() == "all":
                    pass
                else:
                    manager.start_app(app_id)
        elif operate == "list":
            # 应用列表
            manager.list_apps()
        elif operate == "stop":
            # 停止应用
            if len(sys.argv) > 2:
                app_id = sys.argv[2]
                if app_id.lower() == "all":
                    pass
                else:
                    manager.stop_app(app_id)
        elif operate == "run_server":
            manager.run_server()
        elif operate == "monitor":
            # 监控
            manager.monitor()
        elif operate == "delete":
            # 删除
            if len(sys.argv) > 2:
                app_name = sys.argv[2]
                manager.delete_app(app_name)
        elif operate == "update":
            # 修改
            if len(sys.argv) > 3:
                app_name = sys.argv[2]
                kwargs = dict()
                for arg in sys.argv[3:]:
                    equal_index = arg.find("=")
                    key = arg[:equal_index]
                    value = arg[equal_index + 1:]
                    kwargs.update({key: value})
                print("Debug update:")
                print(kwargs)
                manager.update_app(app_name, kwargs)
        elif operate == "add_test":
            manager.add_test_app()

        elif operate == "install":
            manager.install()

        elif operate == "uninstall":
            manager.uninstall()

        elif operate == "shutdown":
            manager.shutdown()
    else:
        # 环境管理
        if len(sys.argv) > 2:
            env_op = sys.argv[2]
            if env_op == "list":
                page = None
                page_size = None
                if len(sys.argv) > 3:
                    page = int(sys.argv[3])
                    print("page: %d" % page)
                if len(sys.argv) > 4:
                    page_size = int(sys.argv[4])
                    print("page size: %d" % page_size)
                if page and page_size:
                    results = env_manager.list_environments(
                        page=page, page_size=page_size)
                else:
                    results = env_manager.list_environments()
                print("Environments:")
                for i, env in enumerate(results):
                    print("No.%d" % i)
                    print("Name: %s" % env.name)
                    print("Verison: %s" % env.verison)
                    print("Path: %s" % env.main)
                    print("=" * 20)
            elif env_op == "add":
                env_manager.add(*sys.argv[3:])
            elif env_op == "update":
                if len(sys.argv) > 5:
                    env_name = sys.argv[3]
                    kwargs = dict()
                    for arg in sys.argv[4:]:
                        equal_index = arg.find("=")
                        key = arg[:equal_index]
                        value = arg[equal_index + 1:]
                        kwargs.update({key: value})

                    env_manager.update(env_name, **kwargs)
            elif env_op == "delete":
                if len(sys.argv) > 3:
                    env_name = sys.argv[3]
                    env_manager.delete(env_name)
