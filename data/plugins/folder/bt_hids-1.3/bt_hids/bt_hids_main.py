# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkq <lkq@qq.com>
# +-------------------------------------------------------------------
import glob
import gzip
# +--------------------------------------------------------------------
# |   主机型入侵检测系统
# +--------------------------------------------------------------------
import os
import re
import shutil
import sys

BASE_PATH = "/www/server/panel"
os.chdir(BASE_PATH)
sys.path.insert(0, "class/")

import public
import io, yaml
import os
import time
import libs
import json
from cachelib import SimpleCache
import db


class bt_hids_main:
    __plugin_path = "/www/server/panel/plugin/bt_hids"
    cache = SimpleCache(50000)
    __PIPE_PATH = "/proc/elkeid-endpoint"
    __firte_file = ["/www/server/panel/pyenv/bin/python3.7", "/www/server/nginx/sbin/nginx", "/usr/sbin/rsyslogd"]
    __PATH = "/www/server/panel/data/hids_data"
    __process_file = __PATH + "/process.pkl"
    __result = __PATH + "/result.json"
    __pid_file = __PATH + "/pid.pl"
    __hids_status = __PATH + "/status.pl"
    __id_file = __PATH + "/id.pl"
    __ignore_file = __PATH + "/ignore.json"
    __white_file = __PATH + "/white.json"
    __remove_file = __PATH + "/remove.json"
    __push_file = __PATH + "/push.pl"
    __uname = ''
    __sql = None

    def __init__(self):
        if not os.path.exists(self.__PATH):
            os.makedirs(self.__PATH, 384)
        # if not os.path.exists(self.__result):
        #     tmp_dict = {"risk": [], "count": {"serious": 0, "high_risk": 0, "medium_risk": 0, "low_risk": 0},
        #                 "repair_count": 0, "white_count": 0, "all_count": 0}
        #     public.WriteFile(self.__result, json.dumps(tmp_dict))
        # if not os.path.exists(self.__id_file):
        #     public.WriteFile(self.__id_file, '0')
        # if not os.path.exists(self.__white_file):
        #     public.WriteFile(self.__white_file, json.dumps([]))
        # if not os.path.exists(self.__remove_file):
        #     public.WriteFile(self.__remove_file, json.dumps([]))
        self.__uname = public.ExecShell('uname -r')[0].strip()
        # 创建数据库
        self.__sql = db.Sql().dbfile("bt_hids")  # 初始化数据库
        if not self.__sql.table('sqlite_master').where('type=? AND name=?', ('table', 'overview')).count():
            overview_sql = '''
            CREATE TABLE IF NOT EXISTS `overview` (
            `all_count` INTEGER,
            `serious` INTEGER,
            `high_risk` INTEGER,
            `medium_risk` INTEGER,
            `low_risk` INTEGER,
            `repair_count` INTEGER
            )
            '''
            self.__sql.execute(overview_sql)
            overview_data = {
                'all_count': 0,
                'serious': 0,
                'high_risk': 0,
                'medium_risk': 0,
                'low_risk': 0,
                'repair_count': 0
            }
            self.__sql.table('overview').insert(overview_data)
        if not self.__sql.table('sqlite_master').where('type=? AND name=?', ('table', 'risk')).count():
            risk_sql = '''
            CREATE TABLE IF NOT EXISTS `risk` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `data_type` CHAR(20),
            `level` CHAR(20),
            `msg` VARCHAR(50),
            `repair` VARCHAR(50),
            `time` VARCHAR(30),
            `type` CHAR(20),
            `vulnname` VARCHAR(50),
            `other` VARCHAR(4000)
            )
            '''
            self.__sql.execute(risk_sql)
        if not self.__sql.table('sqlite_master').where('type=? AND name=?', ('table', 'white')).count():
            white_sql = '''
            CREATE TABLE IF NOT EXISTS `white` (
            `vulnname` VARCHAR(50),
            `ps` VARCHAR(1000),
            `rules` VARCHAR(4000),
            `time` CHAR(40)
            )
            '''
            self.__sql.execute(white_sql)
        if not self.__sql.table('sqlite_master').where('type=? AND name=?', ('table', 'log')).count():
            log_sql = '''
            CREATE TABLE IF NOT EXISTS `log` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `log` VARCHAR(4000)
            )
            '''
            self.__sql.execute(log_sql)

    def bt_hids(self):
        pass

    def set_pid_trer_cache(self, tgid, tty):
        '''
            pid_tree_cache: LruCache::new(2048),
            self.pid_tree_self.cache.insert(values[5].to_vec(), values[21].to_vec());
        '''
        self.cache.set("pid_tree" + tgid, tty)

    def get_pid_trer_cache(self, tgid):
        tgid_s = tgid
        if self.cache.has("pid_tree" + tgid_s):
            return self.cache.get("pid_tree" + tgid_s)
        else:
            return "-3"

    def hash_cache(self, exe):
        if self.cache.has(exe):
            return self.cache.get(exe)
        else:
            if os.path.exists(exe):
                if os.path.getsize(exe) > 1024 * 1024 * 5:
                    return "-4"
                md5 = public.Md5(exe)
                self.cache.set(exe, md5)
                return md5

            else:
                return "-3"

    def user_cache(self, uid):
        if self.cache.has("user_id" + uid):
            return self.cache.get("user_id" + uid)
        else:
            if uid.isdigit():
                uid = int(uid)
                import pwd
                try:
                    user = pwd.getpwuid(uid)
                    self.cache.set("user_id" + str(uid), user.pw_name)
                    return user.pw_name
                except:
                    return "-3"
            else:
                return "-3"

    def ns_cache(self, pns, pid):
        if self.cache.has("ns" + pns):
            return self.cache.get("ns" + pns)
        else:
            if pid.isdigit():
                pid = int(pid)
                if os.path.exists("/proc/%s/environ" % pid):
                    if os.path.getsize("/proc/%s/environ" % pid) > 1024 * 1024 * 5:
                        return "-4"
                    envs = public.ReadFile("/proc/%s/environ" % pid).split("\0")
                    pod_name = ""
                    for env in envs:
                        if env.find("MY_POD_NAME") != -1:
                            pod_name = env.split("=")[1]
                            break
                        if env.find("POD_NAME") != -1:
                            pod_name = env.split("=")[1]
                            break
                    if pod_name:
                        self.cache.set("ns" + pns, pod_name)
                        return pod_name
                    else:
                        return "-3"
                else:
                    return "-3"
            else:
                return "-3"

    def args_cache(self, pid):
        '''
        @name args_cache
        @name 获取pid的命令行参数
        @args pid string
        @return string
        '''
        try:
            pidnum = int(pid)
        except:
            return "-3"
        if pidnum < 0:
            return "-3"
        if self.cache.has(pid):
            return self.cache.get(pid)
        else:
            try:
                cmdline = public.ReadFile("/proc/%s/cmdline" % pidnum)
                if cmdline:
                    cmdline = cmdline if len(cmdline) > 256 else cmdline[:256]
                    cmdline = cmdline.replace("\0", " ")
                    cmdline = cmdline.strip()
                    self.cache.set(pid, cmdline)
                    return cmdline
                else:
                    return "-4"
            except:
                return "-4"

    def get_info(self, count, data):
        '''
            @name get_info 获取数据
            @args count int
            @args data bytes
            @return list
        '''
        values = [""] * count
        index = 0
        base_index = 0
        for i in range(len(data)):
            if data[i] == 0x1e:
                if index >= len(values):
                    break
                values[index] = data[base_index:i].decode("utf-8")
                index += 1
                base_index = i + 1
        return values

    def get_reults(self, values, keys):
        '''
        @name get_reults 获取结果
        @args values list
        @args keys list
        @return dict
        '''

        result = {}
        co = 0
        for i in values:
            result[keys[co]] = i
            co += 1
        return result

    def get42(self, data):
        '''
            @name hook 42 Connect 事件
            @args data dict
        '''
        keys = libs.SCHEMA.get(42)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[18] = self.args_cache(values[5])
        values[19] = self.args_cache(values[3])
        values[20] = self.args_cache(values[4])
        values[21] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[22] = self.ns_cache(values[10], values[6])
        else:
            values[22] = "-3"
        values[23] = self.hash_cache(values[1])
        values[24] = self.get_pid_trer_cache(values[5])
        # 获取结果
        return self.get_reults(values, keys)

    def get49(self, data):
        '''
            @name hook 49 Bind 事件
            @args data dict
        '''
        keys = libs.SCHEMA.get(49)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[16] = self.args_cache(values[5])
        values[17] = self.args_cache(values[3])
        values[18] = self.args_cache(values[4])
        values[19] = self.args_cache(values[0])
        if values[10] != values[11]:
            values[20] = self.ns_cache(values[10], values[6])
        else:
            values[20] = "-3"
        values[21] = self.hash_cache(values[1])
        values[22] = self.get_pid_trer_cache(values[5])
        # 获取结果
        return self.get_reults(values, keys)

    def get_59(self, data):
        '''
               @name hook 59 Execve 事件
               @args data dict
        '''
        keys = libs.SCHEMA.get(59)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        self.cache.set(int(values[5]), values[12])
        self.set_pid_trer_cache(values[5], values[21])
        values[27] = self.args_cache(values[23])
        values[28] = self.args_cache(values[3])
        values[29] = self.args_cache(values[4])
        values[30] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[31] = self.ns_cache(values[10], values[6])
        else:
            values[31] = "-3"
        values[32] = self.hash_cache(values[1])

        # 获取结果
        return self.get_reults(values, keys)

    def get82(self, data, type_id):
        '''
            @name hook 82 Rename 82 Link 事件
            @args data dict
        '''

        keys = libs.SCHEMA.get(int(type_id))
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[15] = self.args_cache(values[5])
        values[16] = self.args_cache(values[3])
        values[17] = self.args_cache(values[4])
        values[18] = self.args_cache(values[0])
        if values[10] != values[11]:
            values[19] = self.ns_cache(values[10], values[6])
        else:
            values[19] = "-3"
        values[20] = self.hash_cache(values[1])
        values[21] = self.get_pid_trer_cache(values[5])
        # 获取结果
        return self.get_reults(values, keys)

    def get101(self, data):
        '''
            @name hook 101 Ptrace 事件

        '''
        keys = libs.SCHEMA.get(101)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[17] = self.args_cache(values[5])
        values[18] = self.args_cache(values[3])
        values[19] = self.args_cache(values[4])
        values[20] = self.args_cache(values[0])
        if values[10] != values[11]:
            values[21] = self.ns_cache(values[10], values[6])
        else:
            values[21] = "-3"
        values[22] = self.hash_cache(values[1])
        values[23] = self.args_cache(values[13])
        self.set_pid_trer_cache(values[5], values[16])

        # 获取结果
        return self.get_reults(values, keys)

    def get112(self, data):
        '''
            @name hook 112 SetSid 事件
        '''
        keys = libs.SCHEMA.get(112)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[12] = self.args_cache(values[5])
        values[13] = self.args_cache(values[3])
        values[14] = self.args_cache(values[4])
        values[15] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[16] = self.ns_cache(values[10], values[6])
        else:
            values[16] = "-3"
        values[17] = self.hash_cache(values[1])
        values[18] = self.get_pid_trer_cache(values[5])
        # 获取结果
        return self.get_reults(values, keys)

    def get157(self, data):
        '''
            @name hook 157 Prctl 事件
        '''
        keys = libs.SCHEMA.get(157)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[14] = self.args_cache(values[5])
        if values[14] != "-3":
            if self.cache.has("argv_dyn_filter" + values[14]):
                if self.cache.get("argv_dyn_filter" + values[14]) > 6000:
                    return {}
                self.cache.inc("argv_dyn_filter" + values[14])
            else:
                self.cache.set("argv_dyn_filter" + values[14], 0, 60)
        values[15] = self.args_cache(values[3])
        values[16] = self.args_cache(values[4])
        values[17] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[18] = self.ns_cache(values[10], values[6])
        else:
            values[18] = "-3"
        values[19] = self.hash_cache(values[1])
        values[20] = self.get_pid_trer_cache(values[5])
        # 获取结果
        return self.get_reults(values, keys)

    def get165(self, data):
        '''
            @name hook 165 Mount 事件
        '''
        keys = libs.SCHEMA.get(165)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[17] = self.args_cache(values[5])
        values[18] = self.args_cache(values[3])
        values[19] = self.args_cache(values[4])
        values[20] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[21] = self.ns_cache(values[10], values[6])
        else:
            values[21] = "-3"
        values[22] = self.hash_cache(values[1])
        self.set_pid_trer_cache(values[5], values[12])

        # 获取结果

        return self.get_reults(values, keys)

    def get356(self, data):
        '''
            @name 356 hook MemfdCreate	 事件
        '''
        kyes = libs.SCHEMA.get(356)
        values = self.get_info(len(kyes), data)
        if values[1] in self.__firte_file: return {}
        values[14] = self.args_cache(values[5])
        values[15] = self.args_cache(values[3])
        values[16] = self.args_cache(values[4])
        values[17] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[18] = self.ns_cache(values[10], values[6])
        else:
            values[18] = "-3"
        values[19] = self.hash_cache(values[1])
        values[20] = self.get_pid_trer_cache(values[5])
        # 获取结果
        return self.get_reults(values, kyes)

    def get601(self, data):
        '''
            @name 356 hook DNS Query 	 事件
        '''
        keys = libs.SCHEMA.get(601)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[20] = self.args_cache(values[5])
        values[21] = self.args_cache(values[3])
        values[22] = self.args_cache(values[4])
        values[23] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[24] = self.ns_cache(values[10], values[6])
        else:
            values[24] = "-3"
        values[25] = self.hash_cache(values[1])
        values[26] = self.get_pid_trer_cache(values[5])
        # 获取结果
        return self.get_reults(values, keys)

    def get602(self, data):
        '''
            @name 356 hook CreateFile 事件
        '''
        keys = libs.SCHEMA.get(602)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[20] = self.args_cache(values[5])
        if values[20] != "-3":
            if self.cache.has("argv_dyn_filter" + values[20]):
                if self.cache.get("argv_dyn_filter" + values[20]) > 6000:
                    return
                self.cache.inc("argv_dyn_filter" + values[20])
            else:
                self.cache.set("argv_dyn_filter" + values[20], 0, 60)
        values[21] = self.args_cache(values[3])
        values[22] = self.args_cache(values[4])
        values[23] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[24] = self.ns_cache(values[10], values[6])
        else:
            values[24] = "-3"
        values[25] = self.hash_cache(values[1])
        values[26] = self.get_pid_trer_cache(values[5])
        values[27] = self.args_cache(values[18])
        # 获取结果
        return self.get_reults(values, keys)

    def get603(self, data):
        '''
            @name 356 hook LoadModule 事件
        '''
        keys = libs.SCHEMA.get(603)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}
        values[15] = self.args_cache(values[5])
        values[16] = self.args_cache(values[3])
        values[17] = self.args_cache(values[4])
        values[18] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[19] = self.ns_cache(values[10], values[6])
        else:
            values[19] = "-3"
        values[20] = self.hash_cache(values[1])
        self.set_pid_trer_cache(values[5], values[13])
        # 获取结果
        return self.get_reults(values, keys)

    def get604(self, data):
        '''
            @name 356 hook CommitCred 事件

        '''
        keys = libs.SCHEMA.get(604)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}

        values[15] = self.args_cache(values[5])
        values[16] = self.args_cache(values[3])
        values[17] = self.args_cache(values[4])
        values[18] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[19] = self.ns_cache(values[10], values[6])
        else:
            values[19] = "-3"
        values[20] = self.hash_cache(values[1])
        self.set_pid_trer_cache(values[5], values[13])
        values[21] = self.user_cache(values[13])

        # 获取结
        return self.get_reults(values, keys)

    def get607(self, data):
        '''
            @name hook call_usermode    事件


        '''
        keys = libs.SCHEMA.get(607)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}

        return self.get_reults(values, keys)

    def get608(self, data, id):
        '''
            @name hook ReadFile 608  WriteFile 609  事件 默认hook 不开
        '''
        keys = libs.SCHEMA.get(int(id))
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}

        values[14] = self.args_cache(values[5])
        values[15] = self.args_cache(values[3])
        values[16] = self.args_cache(values[4])
        values[17] = self.user_cache(values[0])

        if values[10] != values[11]:
            values[18] = self.ns_cache(values[10], values[6])
        else:
            values[18] = "-3"
        values[19] = self.hash_cache(values[1])
        values[20] = self.get_pid_trer_cache(values[5])
        # 获取结果
        return self.get_reults(values, keys)

    def get610(self, data):
        '''
            @name hook USB Event 610  事件
        '''
        keys = libs.SCHEMA.get(610)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}

        values[16] = self.args_cache(values[5])
        values[17] = self.args_cache(values[3])
        values[18] = self.args_cache(values[4])
        values[19] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[20] = self.ns_cache(values[10], values[6])
        else:
            values[20] = "-3"
        values[21] = self.hash_cache(values[1])
        values[22] = self.get_pid_trer_cache(values[5])
        # 获取结果
        return self.get_reults(values, keys)

    def get611(self, data):
        '''
            @name PrivilegeEscalation hook
        '''
        keys = libs.SCHEMA.get(611)
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}

        values[16] = self.args_cache(values[5])
        values[17] = self.args_cache(values[3])
        values[18] = self.args_cache(values[4])
        values[19] = self.user_cache(values[0])
        if values[10] != values[11]:
            values[20] = self.ns_cache(values[10], values[6])
        else:
            values[20] = "-3"
        values[21] = self.hash_cache(values[1])
        values[22] = self.get_pid_trer_cache(values[5])
        values[23] = self.args_cache(values[12])

        # 获取结果
        return self.get_reults(values, keys)

    def get700(self, data, id):
        keys = libs.SCHEMA.get(int(id))
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}

        # 获取结果
        print("700 ProcFileHook LkmHidden 702")
        print(self.get_reults(values, keys))
        return self.get_reults(values, keys)

    def get701(self, data, id):
        print("701 SyscallHook InterruptsHook 702")
        keys = libs.SCHEMA.get(int(id))
        values = self.get_info(len(keys), data)
        if values[1] in self.__firte_file: return {}

        # 获取结果
        return self.get_reults(values, keys)

    def transform(self, data):
        '''
            @name 处理消息的函数
            @param data 消息
        '''

        length = len(data)
        index = 0
        while index < length:
            if data[index] == 0x1e:
                break
            index += 1
        data_type = data[:index].decode("utf-8")
        if not data_type.isdigit():
            return data_type, time.time(), {}
        timestamp = time.time()
        data = data[index + 1:]
        result = {}
        if data_type == "42":
            result = self.get42(data)
        elif data_type == "59":
            result = self.get_59(data)
        elif data_type == "49":
            result = self.get49(data)
        elif data_type == "82" or data_type == "86":
            result = self.get82(data, data_type)
        elif data_type == "101":
            result = self.get101(data)
        elif data_type == "112":
            result = self.get112(data)
        elif data_type == "157":
            result = self.get157(data)
        elif data_type == "165":
            result = self.get165(data)
        elif data_type == "356":
            result = self.get356(data)
        elif data_type == "601":
            result = self.get601(data)
        elif data_type == "602":
            result = self.get602(data)
        elif data_type == "603":
            result = self.get603(data)
        elif data_type == "604":
            result = self.get604(data)
        elif data_type == "607":
            result = self.get607(data)
        elif data_type == "608" or data_type == "609":
            result = self.get608(data, data_type)
        elif data_type == "610":
            result = self.get610(data)
        elif data_type == "611":
            result = self.get611(data)
        elif data_type == "700" or data_type == "702":
            result = self.get700(data, data_type)
        elif data_type == "701" or data_type == "703":
            result = self.get701(data, data_type)

        return data_type, timestamp, result

    def get_yaml_data(self, yaml_file):
        # 打开yaml文件
        file = open(yaml_file, 'r', encoding="utf-8")
        file_data = file.read()
        file.close()
        # 将字符串转化为字典或列表
        data = yaml.safe_load(file_data)
        return data

    def hids_process(self, args):
        yaml_list = []
        path = self.__plugin_path + "/config"
        filter_strings = {
            "ppid_argv": "bash -c while true; do sleep 1;head -v -n 8 /proc/meminfo; head -v -n 2 /proc/stat "
                         "/proc/version /proc/uptime /proc/loadavg /proc/sys/fs/file-nr /proc/sys/kernel/hostname; "
                         "tail -v -n 16 /proc/net/dev;echo '==> /proc/df <==';df -l;echo '==> /proc/who <==';who;echo "
                         "'==> /proc/end <==';echo '##Moba##'; done",
            "socket_argv": "/www/server/panel/pyenv/bin/python3 /www/server/panel/BT-Panel",
            "exe": ["/usr/bin/head", "/usr/bin/tail", "/usr/bin/df", "/usr/bin/sleep"]
        }
        log_size = 500 * 1024 * 1024  # 500M
        log_retention = 30  # retain 30 day or numbers
        log_directory = "/www/wwwlogs/bt_hids/"

        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        # 遍历当前目录，显示当前目录下的所有文件名
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".yaml"):
                    yaml_path = os.path.join(path, file)
                    yaml_list.append(self.get_yaml_data(yaml_path))

        with open(self.__PIPE_PATH, "rb", buffering=0) as f:  # 不对文件进行缓冲，直接从文件中读取数据而不缓存到内存中
            buf_reader = io.BufferedReader(f)  # 创建一个缓冲读取器对象，用于缓存和提高读取问及那效率
            fd = buf_reader.fileno()
            while True:
                data = os.read(fd, 1024)
                if not data:
                    break
                try:
                    data_type, timestamp, result = self.transform(data)
                    if result == {}:
                        continue
                    # log
                    # 过滤
                    if any(result.get(key) == value for key, value in filter_strings.items()):
                        # Skip writing the log if any filter string is found
                        continue

                    # writing log
                    # public.print_log(json.dumps(result))
                    path_log = time.strftime('%Y-%m-%d', time.localtime()) + ".json"
                    time_local = time.localtime(timestamp)
                    time_s = time.strftime('%Y-%m-%d %H:%M:%S', time_local)
                    public.WriteFile(log_directory + path_log,
                                     time_s + " type:" + str(data_type) + " info:" + json.dumps(result) + "\n", 'a+')
                    # 压缩
                    if os.stat(log_directory + path_log).st_size >= log_size:
                        compressed_file = time.strftime('%Y-%m-%d', time.localtime()) + "[" + time.strftime(
                            '%H-%M') + "]" + ".tar.gz"
                        compressed_cmd = 'cd {} && tar -czf {} {}'.format(log_directory, compressed_file, path_log)
                        public.ExecShell(compressed_cmd) #cmd
                        os.remove(log_directory + path_log)

                    # delete
                    log_files = [f for f in os.listdir(log_directory) if f.endswith((".gz", ".json"))]
                    # public.print_log("----start---", str(log_files))
                    if len(log_files) > log_retention:
                        # sort
                        sorted_log_files = sorted(log_files, key=lambda f: os.path.getctime(os.path.join(log_directory, f)))
                        # public.print_log("----sort---", str(sorted_log_files))
                        files_to_delete = sorted_log_files[:len(sorted_log_files) - log_retention]
                        # public.print_log("----delete---", str(files_to_delete))
                        for file_to_delete in files_to_delete:
                            os.remove(os.path.join(log_directory, file_to_delete))

                    # 删除过期压缩包&json 文件
                    # current_time = time.time()
                    # public.print_log("----time---", current_time)
                    #
                    # log_files2 = os.listdir(log_directory)
                    # public.print_log("---list---", log_files2)
                    # for log_file in log_files2:
                    #     log_file_path = os.path.join(log_directory, log_file)
                    #     file_age = current_time - os.path.getmtime(log_file_path)
                    #     if file_age > log_retention * 86400:  # Convert days to seconds (1 day = 86400 seconds)
                    #         os.remove(log_file_path)
                    # public.print_log(json.dumps(result))
                except:
                    continue

                #  过滤白名单
                # tmptmp = 0
                # white_list = json.loads(public.ReadFile(self.__white_file))
                # for wl in white_list:
                #     tmp = 0
                #     for rl in wl["rule_list"]:
                #         try:
                #             if result[rl["key"]] == rl["value"]:
                #                 tmp += 1
                #         except:
                #             continue
                #     if tmp == len(wl["rule_list"]):
                #         tmptmp = 1
                #         break
                # if tmptmp:
                #     continue
                # if data_type == "59":
                #     print(data_type)
                #     print(result)
                #     print()
                # print(data_type)
                # print(result)
                # print()

                for i in yaml_list:
                    # if data_type=="59" and 'dip' in result and result["dip"]=="192.168.221.132":
                    #     print(result)
                    # public.print_log(data).encode('UTF-8')
                    # if data_type == "59" and 'dip' in result and result["dip"] == "192.168.10.168":
                    #     public.print_log("test:" + str(result))
                    # if 'dip' in result and result['dip'] == "192.168.10.168":
                    #     public.print_log("test:" + str(result))
                    # if 'comm' in result and result['comm'] == "openssl":
                    #     public.print_log("test:" + str(result))

                    # if not any(result.get(key) == value for key, value in filter_strings.items()):
                    #     public.print_log("test:" + str(result))
                    if data_type == i["detect_id"]:
                        count = 0
                        for i2 in i["rule"]:
                            if i2 not in result:
                                break
                            # 检测规则
                            if re.search(i["rule"][i2], result[i2]):
                                count += 1
                            else:
                                break
                        # 匹配规则处理
                        if count == len(i["rule"]):
                            pmtpmt = 0
                            white_list = self.__sql.table('white').select()
                            for w in white_list:
                                if w["vulnname"] == i["vulnname"]:
                                    tmp_rules = json.loads(w["rules"])
                                    pmt = 0
                                    for t in tmp_rules:
                                        try:
                                            if result[t["key"]] == t["value"]:
                                                pmt += 1
                                        except:
                                            break
                                    if pmt == len(tmp_rules):
                                        pmtpmt = 1
                                        break
                            if pmtpmt == 1:
                                continue
                            # if data_type == "59" and 'dip' in result and result["dip"] == "192.168.10.168":
                            #     public.print_log("-------test---------:" + str(result))
                            # print("匹配到规则：" + i["systemname"])
                            # print(result)
                            risk_dict = {}
                            risk_dict["other"] = []
                            if data_type == '59':
                                risk_dict["other"].append(
                                    {"key": "socket_argv", "value": result["socket_argv"]})  # 外联进程命令行
                                risk_dict["other"].append({"key": "ssh", "value": result["ssh"]})  # 外联ssh登录信息
                                risk_dict["other"].append({"key": "run_path", "value": result["run_path"]})  # 执行目录
                                risk_dict["other"].append({"key": "stdin", "value": result["stdin"]})  # 进程输入
                                risk_dict["other"].append({"key": "stdout", "value": result["stdout"]})  # 进程输出
                                risk_dict["other"].append({"key": "sport", "value": result["sport"]})  # 监听端口
                                risk_dict["other"].append({"key": "dip", "value": result["dip"]})  # 攻击IP
                                risk_dict["type"] = "代码执行"  # 告警类型
                                if result["argv"].startswith("/usr/libexec/pk-command-not-found "):
                                    risk_dict["msg"] = i["msg"].replace("bt_ip", result["dip"]).replace("bt_cmd",
                                                                                                        result[
                                                                                                            "argv"].replace(
                                                                                                            "/usr/libexec/pk-command-not-found ",
                                                                                                            ""))  # 告警描述
                                else:
                                    risk_dict["msg"] = i["msg"].replace("bt_ip", result["dip"]).replace("bt_cmd",
                                                                                                        result[
                                                                                                            "argv"])  # 告警描述
                            elif data_type == '611':
                                risk_dict["msg"] = i["msg"].replace("bt_pe_cmd", result["argv"])  # 告警描述
                                risk_dict["type"] = "提权攻击"  # 告警类型
                            elif data_type == '42':
                                risk_dict["other"].append({"key": "dip", "value": result["dip"]})  # 攻击IP
                                risk_dict["msg"] = i["msg"].replace("bt_ip", result["dip"])  # 告警描述
                                risk_dict["type"] = "恶意连接"  # 告警类型
                            elif data_type == '601':
                                risk_dict["msg"] = i["msg"].replace("bt_cmd", result["argv"])  # 告警描述
                                risk_dict["type"] = "带外攻击"  # 告警类型
                            else:
                                break
                            # risk_dict["id"] = int(public.ReadFile(self.__id_file)) # id主键
                            # public.WriteFile(self.__id_file, str(risk_dict["id"]+1))
                            risk_dict["other"].append({"key": "pid", "value": result["pid"]})  # 进程PID
                            risk_dict["other"].append({"key": "exe", "value": result["exe"]})  # 进程二进制文件
                            risk_dict["other"].append({"key": "argv", "value": result["argv"]})  # 进程命令行
                            risk_dict["other"].append({"key": "username", "value": result["username"]})  # 进程所属用户名
                            risk_dict["other"].append({"key": "pid_tree", "value": result["pid_tree"]})  # 进程树
                            risk_dict["vulnname"] = i["vulnname"]  # 告警名称
                            risk_dict["data_type"] = data_type  # 规则类型
                            risk_dict["level"] = i["level"]  # 风险级别
                            risk_dict["time"] = self.get_time()  # 发生时间
                            risk_dict["repair"] = i["repair"].replace("bt_pid", result["ppid"])  # 修复建议
                            # result_dict["risk"].append(risk_dict)
                            # public.WriteFile(self.__result, json.dumps(result_dict))
                            risk_dict["other"] = json.dumps(risk_dict["other"])
                            msg_result = public.M("risk").dbfile("bt_hids").insert(risk_dict)
                            self.send_news(risk_dict["vulnname"], risk_dict["level"], risk_dict["type"],
                                           risk_dict["time"])
                            break

    def set_process(self, get):
        import subprocess
        if not self.check_lkm():
            return public.returnMsg(False, '当前内核版本不支持使用堡塔入侵检测')
        old_pid = public.ReadFile(self.__pid_file)
        new_pid = public.ExecShell("ps aux |grep '/bt_hids/load_hids.py'|grep -v grep|awk '{print $2}'")[0].strip()
        lkm = public.ExecShell("lsmod | grep hids_driver")[0].strip()
        # 启动hids监测
        if not new_pid:
            if not lkm:
                public.ExecShell('insmod {}/hids_driver_1.7.0.10_{}_amd64.ko'.format(self.__plugin_path, self.__uname))
                # public.ExecShell('insmod {}/hids_driver_1.7.0.11_{}_amd64.ko'.format(self.__plugin_path, self.__uname))
            hids_p = subprocess.Popen(['btpython', '{}/load_hids.py'.format(self.__plugin_path)],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
            public.WriteFile(self.__pid_file, str(hids_p.pid).strip())
            public.WriteFile(self.__hids_status, 'True')
        # 关闭hids监测
        elif old_pid == new_pid:
            public.ExecShell("kill -9 {}".format(new_pid))
            public.ExecShell("rmmod hids_driver")
            public.WriteFile(self.__hids_status, 'False')
            return public.returnMsg(True, '关闭【入侵检测】成功')
        # hids重启过后
        else:
            public.WriteFile(self.__pid_file, new_pid)
            public.WriteFile(self.__hids_status, 'True')
        return public.returnMsg(True, '启动【入侵检测】成功')

    def get_result(self, get):
        import page
        if not self.check_lkm():
            return public.returnMsg(False, '当前内核版本不支持使用堡塔入侵检测')
        page = page.Page()
        level = json.loads(get['type'])
        where_sql = ''
        for i, l in enumerate(level):
            if i == len(level) - 1:
                where_sql += "level='{}'".format(l)
            else:
                where_sql += "level='{}' OR ".format(l)
        all_count = public.M("risk").dbfile("bt_hids").count()
        count = public.M("risk").dbfile("bt_hids").where(where_sql, ()).count()
        limit = 10
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        if hasattr(get, 'rows'):
            info['row'] = int(get['rows'])
        data = {}
        public.M('overview').dbfile('bt_hids').update({'all_count': all_count})
        serious = public.M('risk').dbfile('bt_hids').where('level=?', ('serious',)).count()
        public.M('overview').dbfile('bt_hids').update({'serious': serious})
        high_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('high',)).count()
        public.M('overview').dbfile('bt_hids').update({'high_risk': high_risk})
        medium_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('medium',)).count()
        public.M('overview').dbfile('bt_hids').update({'medium_risk': medium_risk})
        low_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('low',)).count()
        public.M('overview').dbfile('bt_hids').update({'low_risk': low_risk})
        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        overview = public.M('overview').dbfile("bt_hids").select()[0]
        data['all_count'] = overview['all_count']
        data['repair_count'] = overview['repair_count']
        data['white_count'] = public.M('white').dbfile('bt_hids').count()
        data['count'] = {'serious': overview['serious'], 'high_risk': overview['high_risk'],
                         'medium_risk': overview['medium_risk'], 'low_risk': overview['low_risk']}
        if not public.M('risk').dbfile('bt_hids').count():
            data['risk'] = []
            return data

        data['risk'] = public.M('risk').dbfile("bt_hids").order('id desc').where(where_sql, ()).limit(
            str(page.SHIFT) + ',' + str(page.ROW)).select()
        # data['risk']['other'] = json.loads(data['risk']['other'])
        return data

    def check_status(self):
        new_pid = public.ExecShell("ps aux |grep '/bt_hids/load_hids.py'|grep -v grep|awk '{print $2}'")[0].strip()
        lkm = public.ExecShell("lsmod | grep hids")[0].strip()
        if not lkm.startswith("hids_driver"):
            return False
        if new_pid == '':
            return False
        return True

    def get_status(self, get):
        if not self.check_status():
            public.WriteFile(self.__hids_status, 'False')
        status = public.ReadFile(self.__hids_status)
        if status == 'True':
            return {"status": True}
        else:
            return {"status": False}

    def set_white(self, args):
        # white_list = json.loads(public.ReadFile(self.__white_file))
        white_list = public.M('white').dbfile("bt_hids").select()
        white_dict = {
            "vulnname": args.vulnname,
            "ps": args.ps,
            "rules": json.dumps(json.loads(args.rules))
        }
        if args.time == '':
            white_dict["time"] = self.get_time()
        else:
            white_dict["time"] = args.time
        if white_dict in white_list:
            # white_list.remove(white_dict)
            try:
                # public.WriteFile(self.__white_file, json.dumps(white_list))
                public.M('white').dbfile("bt_hids").where("vulnname=? and ps=? and rules=? and time=?", (
                    white_dict["vulnname"], white_dict["ps"], white_dict["rules"], white_dict["time"])).delete()
                return public.returnMsg(True, '删除白名单成功')
            except Exception as e:
                return public.returnMsg(False, '删除白名单失败')

        # white_list.append(white_dict)
        # risk_dict = json.loads(public.ReadFile(self.__result))
        # risk_list = risk_dict["risk"]
        # new_risk_list = risk_list.copy()

        # for risk in risk_list:
        #     tmp = 0
        #     if risk["vulnname"] != white_dict["vulnname"]:
        #         continue
        #     for ro in risk["other"]:
        #         if ro in white_dict["rules"]:
        #             tmp += 1
        #     if tmp == len(white_dict["rules"]):
        #         new_risk_list.remove(risk)
        #     break
        # risk_dict["risk"] = new_risk_list
        # public.WriteFile(self.__result, json.dumps(risk_dict))
        try:
            public.M('white').dbfile("bt_hids").insert(white_dict)
            public.M('risk').dbfile('bt_hids').where('vulnname=? and other=?',
                                                     (white_dict['vulnname'], white_dict['rules'])).delete()
            public.M('risk').dbfile('bt_hids').where('vulnname=? and other=?',
                                                     (white_dict['vulnname'], white_dict['rules'],)).select()
            # public.WriteFile(self.__white_file, json.dumps(white_list))
            return public.returnMsg(True, '添加白名单成功')
        except:
            return public.returnMsg(True, '添加白名单失败')

    def get_white(self, get):
        import page
        page = page.Page()
        count = public.M("white").dbfile("bt_hids").count()
        limit = 10
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        if hasattr(get, 'rows'):
            info['row'] = int(get['rows'])
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['white'] = public.M('white').dbfile('bt_hids').limit(str(page.SHIFT) + ',' + str(page.ROW)).select()
        return data

    def remove(self, args):
        # remove_list = json.loads(public.ReadFile(self.__remove_file))
        # remove_list += args.id_list
        id_list = json.loads(args.id_list)
        if isinstance(id_list, int):
            try:
                public.M('risk').dbfile('bt_hids').where('id=?', id_list).delete()
                repair_count = self.__sql.table('overview').field('repair_count').select()[0]['repair_count']
                self.__sql.table('overview').update({"repair_count": repair_count + 1})
                return public.returnMsg(True, '处理成功')
            except Exception as e:
                return public.returnMsg(True, '处理失败' + str(e))
        result = []
        for id in id_list:
            try:
                public.M('risk').dbfile('bt_hids').where('id=?', id).delete()
                result.append({"status": True, "id": id, "msg": "处理成功"})
                repair_count = self.__sql.table('overview').field('repair_count').select()[0]['repair_count']
                self.__sql.table('overview').update({"repair_count": repair_count + 1})
            # public.WriteFile(self.__remove_file, json.dumps(remove_list))
            # if len(id_list)>1:
            #     return
            except:
                result.append({"status": False, "id": id, "msg": "处理失败"})
                continue
        return result

    def get_time(self):
        return public.format_date()

    def set_send(self, get):
        login_send_type_conf = self.__push_file
        set_type = get.type.strip()
        if set_type == "error":
            public.writeFile(login_send_type_conf, set_type)
            return public.returnMsg(True, '关闭成功')
        import config
        config = config.config()
        msg_configs = config.get_msg_configs(get)
        if set_type not in msg_configs.keys():
            return public.returnMsg(False, '不支持该发送类型')
        _conf = msg_configs[set_type]
        if "data" not in _conf or not _conf["data"]:
            return public.returnMsg(False, "该通道未配置, 请重新选择。")
        from panelMessage import panelMessage
        pm = panelMessage()
        obj = pm.init_msg_module(set_type)
        if not obj:
            return public.returnMsg(False, "消息通道未安装。")
        public.writeFile(login_send_type_conf, set_type)
        return public.returnMsg(True, '设置成功')

    def send_news(self, name, risk, type, time):
        login_send_type_conf = self.__push_file
        if os.path.exists(login_send_type_conf):
            send_type = public.ReadFile(login_send_type_conf).strip()
        else:
            return False
        if send_type == 'error':
            return False

        if not send_type:
            return False
        object = public.init_msg(send_type.strip())
        if not object: return False
        # send_data = {
        #     'time':time,
        #     'vulnname':name,
        #     'type':type,
        #     'level':risk
        # }
        if risk == 'serious':
            risk = "紧急"
            p_risk = '<span style="color:#F50606;">紧急</span>'
        elif risk == 'high':
            risk = "高危"
            p_risk = '<span style="color:#FF5A5A;">高危</span>'
        elif risk == 'medium':
            risk = "中危"
            p_risk = '<span style="color:#FF9900;">中危</span>'
        else:
            risk = "低危"
            p_risk = '<span style="color:#DDC400;">低危</span>'
        data = {'log': '告警名称：【{}】 告警类型：【{}】 风险等级：【{}】 发送时间：【{}】'.format(name, type, p_risk, time)}
        public.M('log').dbfile('bt_hids').insert(data)

        plist = [
            ">告警名称：" + name,
            ">告警类型：" + type,
            ">风险等级：" + risk
        ]

        info = public.get_push_info("入侵检测", plist)
        reuslt = object.push_data(info)
        return reuslt

    def check_lkm(self):
        if not os.path.exists('{}/hids_driver_1.7.0.10_{}_amd64.ko'.format(self.__plugin_path, self.__uname)):
            result = public.ExecShell(
                'wget "https://download.bt.cn/install/plugin/bt_hids/ko/hids_driver_1.7.0.10_{}_amd64.ko" -O {}/hids_driver_1.7.0.10_{}_amd64.ko'.format(
                    self.__uname, self.__plugin_path, self.__uname))
            if not os.path.exists(
                    '{}/hids_driver_1.7.0.10_{}_amd64.ko'.format(self.__plugin_path, self.__uname)) and "Not Found" in \
                    result[1]:
                public.ExecShell('rmmod hids_driver')
                return False
            else:
                return True
        size = public.get_path_size("{}/hids_driver_1.7.0.10_{}_amd64.ko".format(self.__plugin_path, self.__uname))
        if size == 0:
            return False
        return True

    def get_send(self, get):
        send_type = "error"
        if os.path.exists(self.__push_file):
            send_type = public.ReadFile(self.__push_file)
        return public.returnMsg(True, send_type)

    def get_log(self, get):
        import page
        page = page.Page()
        count = public.M("log").dbfile("bt_hids").count()
        limit = 10
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        if hasattr(get, 'rows'):
            info['row'] = int(get['rows'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['log'] = public.M('log').dbfile('bt_hids').order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).select()
        return data

    # 入侵检测日志
    def get_hids_log(self, get):
        file_local = '/www/wwwlogs/bt_hids/'
        path_log = time.strftime('%Y-%m-%d', time.localtime()) + ".json"  # 看当天的日志情况
        filename = file_local + path_log
        if not os.path.exists(filename):
            return public.returnMsg(True, '')
        result = public.GetNumLines(filename, 1000)
        return public.returnMsg(True, self.xsssec(result))

    # xss 防御
    def xsssec(self, text):
        return text.replace('<', '&lt;').replace('>', '&gt;')


if __name__ == "__main__":
    hm = bt_hids_main()
    json.loads(public.ReadFile('/www/server/panel/data/hids_data/white.pl'))
