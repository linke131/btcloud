#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 王佳函 <mr_jia_han@qq.com>
# +-------------------------------------------------------------------
import datetime
#+--------------------------------------------------------------------
#|   磁盘文件分析
#+--------------------------------------------------------------------
import sys
import os
import time

import public
os.chdir(public.get_panel_path())
sys.path.append("class/")

import json
from typing import Union

class disk_analysis_main:
    ncdu_exe = 'ncdu'
    # 扫描结果存放路径
    scan_data_path = os.path.join(public.get_setup_path(), 'disk_analysis/data/')

    scan_log_path = os.path.join(public.get_setup_path(), 'disk_analysis/scan_log.json')
    scan_config_path = os.path.join(public.get_setup_path(), 'disk_analysis/scan_config.json')

    scan_config_data = {
        "scan_config": {
            "exclude_path_list": ["/proc/kcore","/www/server/panel"],
        },
        "scan_show": {
            "show_type": "1",
        },
        "file_show": {  # show_type=2
            "exts": "",
            "total_num": "100",
        }
    }

    def __init__(self):
        if not os.path.exists(self.scan_data_path):
            os.makedirs(self.scan_data_path)

        self.update_1_7()

        if not os.path.isfile(self.scan_log_path):
            public.writeFile(self.scan_log_path, json.dumps({}))
        if not os.path.isfile(self.scan_config_path):
            public.writeFile(self.scan_config_path, json.dumps(self.scan_config_data))
        if os.getenv('BT_PANEL'):
            self.ncdu_exe = os.path.join(public.get_panel_path(),"plugin/disk_analysis/ncdu")


    def update_1_7(self):
        try:
            if os.path.isfile(self.scan_log_path) and os.path.isfile(self.scan_config_path):
                return
            public.print_log(f"更新磁盘扫描配置文件！")


            public.writeFile(self.scan_config_path, json.dumps(self.scan_config_data))

            conf_file = os.path.join(public.get_panel_path(), "plugin/disk_analysis/config.json")
            data = json.loads(public.readFile(conf_file))

            log_path = os.path.join(public.get_setup_path(), 'disk_analysis/scan/')

            scan_log_data = {}
            for k,v in data.items():
                file_path = os.path.join(log_path, k)
                if not os.path.isfile(file_path):
                    continue
                public.ExecShell(f"cp {file_path} {os.path.join(self.scan_data_path, k)}")
                f_stat = os.stat(file_path)
                scan_log_data[k] = {
                    "scan_path": v,
                    "exclude_path_list": [],
                    "size": f_stat.st_size,
                    "scan_time": f_stat.st_mtime,
                }
            public.writeFile(self.scan_log_path, json.dumps(scan_log_data))
            os.remove(conf_file)
            public.ExecShell(f"rm -rf {log_path}")
            public.ExecShell(f"rm -rf {os.path.join(public.get_panel_path(), 'data/scan')}")
        except Exception as err:
            public.print_log(f"update_err:{err}")

    @classmethod
    def __check_disk(cls):
        # 校验磁盘大小
        df_data = public.ExecShell("df -T | grep '/'")[0]
        for data in str(df_data).split("\n"):
            data_list = data.split()
            if not data_list: continue
            use_size = data_list[4]
            size = data_list[5]
            disk_path = data_list[6]
            if int(use_size) < 1024 * 50 and str(size).rstrip("%") == "100" and disk_path in ["/", "/www"]:
                return f"您的磁盘已满！'{disk_path}' 可用: {use_size}K,请先清理出一些空间!(建议50MB及以上)"
        return True

    # 获取扫描配置
    @classmethod
    def __get_scan_config(cls, config_type: str=None, field: str=None, default=None) -> Union[dict, str, int]:
        """
        获取扫描配置
        @param config_type: 配置类型
        @param field: 配置名称
        @param default: 默认值
        @return:
        """
        try:
            scan_config_data = json.loads(public.readFile(cls.scan_config_path))
        except:
            scan_config_data = {
                "scan_config": {
                    "exclude_path_list": ["/proc/kcore","/www/server/panel"],
                },
                "scan_show": {
                    "show_type": "1",
                },
                "file_show": {
                    "exts": "",
                    "total_num": "100",
                }
            }

        if config_type is not None:
            scan_config_data = scan_config_data.get(config_type)
        if field is not None:
            scan_config_data = scan_config_data.get(field, default)
        return scan_config_data

    # 设置扫描配置
    @classmethod
    def __set_scan_config(cls, config: dict) -> None:
        """
        设置扫描配置
        @param config: 扫描配置
        @return:
        """
        public.writeFile(cls.scan_config_path, json.dumps(config))

    # 获取扫描配置
    def get_scan_config(self, get):
        scan_config = self.__get_scan_config()

        return {"status": True, "msg": "ok", "data": scan_config}

    # 设置扫描配置
    def set_scan_config(self, get):
        exclude_path_list = json.loads(getattr(get, "exclude_path_list", "[]"))
        show_type = getattr(get, "show_type", None)
        total_num = getattr(get, "total_num", None)

        scan_config = self.__get_scan_config()

        # 扫描设置
        if exclude_path_list:
            scan_config["scan_config"]["exclude_path_list"] = exclude_path_list

        # 目录结构
        if show_type is not None:
            scan_config["scan_show"]["show_type"] = show_type

        # show_type = 2 文件展示
        if total_num is not None:
            scan_config["file_show"]["total_num"] = total_num
        self.__set_scan_config(scan_config)

        return {"status": True, "msg": "设置扫描配置成功！", "data": scan_config}

    # 获取扫描记录
    @classmethod
    def __get_scan_log(cls, scan_id: Union[str, None] = None) -> Union[dict, list]:
        """
        获取扫描记录
        @param scan_id:
        @return:
        """
        try:
            scan_log = json.loads(public.readFile(cls.scan_log_path))
        except:
            scan_log = {}

        if scan_id is not None:
            return scan_log.get(scan_id)
        return scan_log

    # 设置扫描记录
    @classmethod
    def __set_scan_log(cls, scan_id: str, info: dict) -> None:
        """
        设置扫描记录
        @param scan_id:
        @param info:
        @return:
        """
        try:
            scan_log = json.loads(public.readFile(cls.scan_log_path))
        except:
            scan_log = {}

        scan_log[scan_id] = info
        public.writeFile(cls.scan_log_path, json.dumps(scan_log))

    # 判断记录是否存在
    @classmethod
    def __exist_scan_log(cls, scan_id: str) -> bool:
        """
        判断记录是否存在
        @param scan_id:
        @return:
        """
        try:
            scan_log = json.loads(public.readFile(cls.scan_log_path))
        except:
            scan_log = {}

        return scan_log.get(scan_id) is not None

	# 获取权限状态信息
    @classmethod
    def __get_stat(cls, path, info) -> None:
        if not os.path.exists(path):
            info["status"] = 0
            info["accept"] = None
            info["user"] = None
            info["atime"] = None
            info["ctime"] = None
            info["mtime"] = None
            info["ps"] = None
            return

        info["status"] = 1
        # 获取文件信息
        stat_file = os.stat(path)

        info["accept"] = oct(stat_file.st_mode)[-3:]
        import pwd
        try:
            info["user"] = pwd.getpwuid(stat_file.st_uid).pw_name
        except:
            info["user"] = str(stat_file.st_uid)
        info["atime"] = int(stat_file.st_atime)
        info["ctime"] = int(stat_file.st_ctime)
        info["mtime"] = int(stat_file.st_mtime)

	# 扫描磁盘
    def start_scan(self, get):
        """
        @name 扫描磁盘
        @param path 扫描目录
        """
        # 校验磁盘大小
        resp = self.__check_disk()
        if isinstance(resp, str):
            return public.returnMsg(False, resp)

        if not hasattr(get, "scan_path"):
            return public.returnMsg(False, f"缺少参数! scan_path")

        scan_path = get.scan_path
        exclude_path = json.loads(getattr(get, "exclude_path", "[]"))

        exclude_path = [path for path in exclude_path if path]
        if len(exclude_path) == 0: # 获取默认排除路径
            exclude_path = self.__get_scan_config("scan_config", "exclude_path_list", [])

        exclude_path_list = ['--exclude {}'.format(os.path.join(scan_path,url)) for url in exclude_path]

        if not os.path.isdir(scan_path):
            return public.returnMsg(False, '目录不存在.')

        # 生成 id
        scan_id = str(int(time.time() * 1000_000))
        while self.__exist_scan_log(scan_id):
            scan_id = str(int(time.time() * 1000_000))

        scan_result_file = os.path.join(self.scan_data_path, scan_id)

        exec_shell = "{} {} -o {} {} ".format(self.ncdu_exe, scan_path, scan_result_file, " ".join(exclude_path_list)).replace('\\','/').replace('//','/')
        scan_time = int(time.time())
        result = public.ExecShell(exec_shell)[1]

        if result.find("Permission denied") != -1: # 无权限授权
            public.ExecShell("chmod +x /usr/bin/ncdu")
            result = public.ExecShell(exec_shell)[1]
        if result.find("ncdu: command not found") != -1: # 连接不存在
            public.ExecShell("ln -s /www/server/panel/plugin/disk_analysis/ncdu /usr/bin/ncdu && chmod +x /usr/bin/ncdu")
            result = public.ExecShell(exec_shell)[1]

        if not os.path.isfile(scan_result_file):
            return public.returnMsg(False, f"扫描错误！请检查：<br/>1. 服务器磁盘是否已满，请确保 / 或 /www 磁盘有可用空间！")

        log_size = os.path.getsize(scan_result_file)

        scan_log_info = {
            "scan_path": scan_path,
            "exclude_path_list": exclude_path,
            "size": log_size,
            "scan_time": scan_time,
        }
        self.__set_scan_log(scan_id, scan_log_info)
        public.set_module_logs('disk_analysis', 'start_scan', 1)
        return {"status": True, "msg": "扫描完成!", "data": {"scan_id": scan_id, "show_type": self.__get_scan_config("scan_show", "show_type")}}

    # 获取扫描日志
    def get_scan_log(self, get):
        """
        获取扫描日志
        @param get:
        @return:
        """
        scan_log = self.__get_scan_log()

        scan_log_list = []
        for scan_id, info in scan_log.items():
            info["scan_id"] = scan_id
            info["status"] = False
            if os.path.isfile(os.path.join(self.scan_data_path, scan_id)):
                info["status"] = True
            scan_log_list.append(info)
        scan_log_list = sorted(scan_log_list, key=lambda data: data["scan_time"], reverse=True)
        return {"status": True, "msg": "ok", "data": scan_log_list}

    # 删除指定扫描记录
    def del_scan_log(self, get):
        """
        删除指定扫描记录
        @param get:
        @return:
        """
        if not hasattr(get, "scan_id"):
            return public.returnMsg(False, "缺少参数! scan_id")

        scan_id = get.scan_id
        try:
            scan_log = json.loads(public.readFile(self.scan_log_path))
        except:
            scan_log = {}

        # 删除配置
        if scan_log.get(scan_id) is not None:
            del scan_log[scan_id]
        public.writeFile(self.scan_log_path, json.dumps(scan_log))

        # 删除文件
        scan_data_file = os.path.join(self.scan_data_path, scan_id)
        if os.path.isfile(scan_data_file):
            os.remove(scan_data_file)
        return public.returnMsg(True, '删除成功!')

    # 获取扫描结果
    def get_scan_result(self, get):
        """
        获取扫描结果
        @param get:
        @return:
        """
        if not hasattr(get, "scan_id"):
            return public.returnMsg(False, "缺少参数! scan_id")

        scan_id = get.scan_id
        sub_path = getattr(get, "sub_path", None)
        file_name = getattr(get, "file_name", None)
        sort = getattr(get, "sort", "total_asize")
        reverse = getattr(get, "reverse", "true")

        if not sort: sort = "total_asize"
        if not reverse: reverse = "true"
        reverse = reverse == "true"

        # 扫描结果文件
        scan_data_file = os.path.join(self.scan_data_path, scan_id)
        if not os.path.isfile(scan_data_file):
            return public.returnMsg(False, "扫描结果不存在！")

        data = public.readFile(scan_data_file)
        data = json.loads(data)

        scan_result = {}
        for info in data:
            if not isinstance(info, list): continue

            full_path = info[0]["name"]
            if sub_path and sub_path != full_path:
                info  = self.__get_sub_path_data(info[1:], full_path, sub_path)
                if info is None: continue
                info[0]["full_path"] = sub_path
            else:
                info[0]["full_path"] = full_path
            scan_result = self.__analysis_scan_result(info)

        scan_result["scan_time"] = self.__get_scan_log(scan_id).get("scan_time")
        tmp_list = []
        for info in scan_result.get("list", []):
            if file_name and file_name not in info["name"]:
                continue
            tmp_list.append(info)

        tmp_list.sort(key=lambda data: (data["status"],data[sort]), reverse=reverse)
        scan_result["list"] = tmp_list
        scan_info = self.__get_scan_log(scan_id)
        return {"status": True, "msg": "ok", "scan_info": scan_info, "data": scan_result}


    # 获取子目录数据
    @classmethod
    def __get_sub_path_data(cls, scan_result: dict, root_path: str, sub_path: str) -> Union[list, None]:
        sub_path = sub_path.replace("//","/")
        for info in scan_result:
            if not isinstance(info, list): continue
            full_path = os.path.join(root_path, info[0]["name"])
            if full_path == sub_path:
                return info
            elif len(info) > 1:
                info = cls.__get_sub_path_data(info[1:], full_path, sub_path)
                if info is not None:
                    return info
        return None

	# 解析扫描结果信息
    @classmethod
    def __analysis_scan_result(cls, analysis_data: list) -> dict:
        """
        @name 解析扫描结果信息
        @param analysis_data 扫描结果
        @param result 结果
        """
        scan_result = analysis_data[0]
        scan_result["type"] = 1
        scan_result["asize"] = scan_result.get("asize", 0)
        scan_result["dsize"] = scan_result.get("dsize", 0)
        scan_result["dirs"] = 0
        scan_result["files"] = 0
        scan_result["dir_num"] = 0
        scan_result["file_num"] = 0
        scan_result["total_asize"] = scan_result.get("asize", 0)
        scan_result["total_dsize"] = scan_result.get("dsize", 0)
        cls.__get_stat(scan_result["name"], scan_result)
        scan_result["list"] = []

        for info in analysis_data[1:]:
            if isinstance(info, list): # 目录
                scan_result["dirs"] += 1
                scan_result["dir_num"] += 1
                info[0]["full_path"] = os.path.join(scan_result["full_path"], info[0]["name"])
                cls.__get_dir_size(info)
                info = info[0]
                scan_result["dir_num"] += info["dir_num"]
                scan_result["file_num"] += info["file_num"]
                scan_result["total_asize"] += info["total_asize"]
                scan_result["total_dsize"] += info["total_dsize"]
            else:
                info["full_path"] = os.path.join(scan_result["full_path"], info["name"])
                if info.get("excluded") == "pattern":
                    info["excluded"] = True
                    info["type"] = int(os.path.isdir(info["full_path"]))
                    if info["type"] == 1: # 排除目录
                        info["files"] = 0
                        info["file_num"] = 0
                        info["dirs"] = 0
                        info["dir_num"] = 0
                else:
                    info["excluded"] = False
                    info["type"] = 0
                    info["files"] = -1
                    info["file_num"] = -1
                    info["dirs"] = -1
                    info["dir_num"] = -1
                scan_result["files"] += 1
                scan_result["file_num"] += 1
                if info.get("asize") is None: info["asize"] = 0
                if info.get("dsize") is None: info["dsize"] = 0
                info["total_asize"] = info["asize"]
                info["total_dsize"] = info["dsize"]
                scan_result["total_asize"] += info["asize"]
                scan_result["total_dsize"] += info["dsize"]

            cls.__get_stat(info["full_path"], info)
            scan_result["list"].append(info)
        total_max = scan_result["total_asize"]
        for info in scan_result["list"]:
            if total_max == 0:
                info["percent"] = 0
            else:
                info["percent"] = round(info['total_asize'] / total_max * 100, 2)
        return scan_result

	# 计算目录大小信息
    @classmethod
    def __get_dir_size(cls, analysis_data):
        """
        @param analysis_data 计算目录大小信息
        """
        dir_info = analysis_data[0]
        dir_info["type"] = 1
        dir_info["asize"] = dir_info.get("asize", 0)
        dir_info["dsize"] = dir_info.get("dsize", 0)
        dir_info["dirs"] = 0
        dir_info["files"] = 0
        dir_info["dir_num"] = 0
        dir_info["file_num"] = 0
        dir_info["total_asize"] = dir_info.get("asize", 0)
        dir_info["total_dsize"] = dir_info.get("dsize", 0)
        for info in analysis_data[1:]:
            if isinstance(info, list):  # 目录
                dir_info["dirs"] += 1
                dir_info["dir_num"] += 1
                cls.__get_dir_size(info)
                temp_info = info[0]
                dir_info["dir_num"] += temp_info["dir_num"]
                dir_info["file_num"] += temp_info["file_num"]
                dir_info["total_asize"] += temp_info["total_asize"]
                dir_info["total_dsize"] += temp_info["total_dsize"]
            else:
                if info.get("excluded") == "pattern":
                    continue
                dir_info["files"] += 1
                dir_info["file_num"] += 1
                if info.get("asize") is None: info["asize"] = 0
                if info.get("dsize") is None: info["dsize"] = 0
                info["type"] = 0
                dir_info["total_asize"] += info["asize"]
                dir_info["total_dsize"] += info["dsize"]

    # 过滤所有文件
    def filter_file(self, get):
        if not hasattr(get, "scan_id"):
            return public.returnMsg(False, "缺少参数! scan_id")

        scan_id = get.scan_id

        sub_path = getattr(get , "sub_path", None)
        file_name = getattr(get , "file_name", None)
        exts = getattr(get , "exts", "")
        sort = getattr(get , "sort", "total_asize")
        reverse = getattr(get, "reverse", "true")
        total_num = getattr(get , "total_num", self.__get_scan_config("file_show", "total_num"))

        if not sort: sort = "total_asize"
        if not reverse: reverse = "true"
        reverse = reverse == "true"

        scan_data_file = os.path.join(self.scan_data_path, scan_id)
        if not os.path.exists(scan_data_file):
            return public.returnMsg(False, '扫描结果不存在.')

        data = public.readFile(scan_data_file)
        data = json.loads(data)

        ext_list = str(exts).split("|")
        scan_result = {}
        for info in data:
            if not isinstance(info, list): continue
            full_path = info[0]["name"]
            if sub_path and sub_path != full_path:
                info = self.__get_sub_path_data(info[1:], full_path, sub_path)
                if info is None: continue
                info[0]["full_path"] = sub_path
            else:
                info[0]["full_path"] = full_path

            scan_result = self.__analysis_filter_data(info, file_name, ext_list, int(total_num), sort, reverse)

        scan_result["scan_time"] = self.__get_scan_log(scan_id).get("scan_time")
        total_max = scan_result["total_asize"]
        for info in scan_result["list"]:
            self.__get_stat(info["full_path"], info)
            if total_max == 0:
                info["percent"] = 0
            else:
                info["percent"] = round(info['total_asize'] / total_max * 100, 2)
        return {"status": True, "msg": "ok", "data": scan_result}

    # 过滤指定路径下所有文件
    @classmethod
    def __analysis_filter_data(cls, analysis_data: list, file_name: Union[str, None], ext_list: list, total_num: int, sort: str, reverse: bool) -> dict:
        """
        过滤指定路径下所有文件
        @param analysis_data: 扫描结果信息
        @param file_name: 过滤文件名
        @param ext_list: 过滤文件后缀
        @param total_num: 过滤文件数量
        @param sort: 排序字段
        @param reverse: 是否降序
        @return: dict
        """
        scan_result = analysis_data[0]
        scan_result["type"] = 1
        scan_result["asize"] = scan_result.get("asize", 0)
        scan_result["dsize"] = scan_result.get("dsize", 0)
        scan_result["dirs"] = 0
        scan_result["files"] = 0
        scan_result["dir_num"] = 0
        scan_result["file_num"] = 0
        scan_result["total_asize"] = scan_result.get("asize", 0)
        scan_result["total_dsize"] = scan_result.get("dsize", 0)
        cls.__get_stat(scan_result["name"], scan_result)
        scan_result["list"] = []

        for info in analysis_data[1:]:
            if isinstance(info, list):  # 目录
                info[0]["full_path"] = os.path.join(scan_result["full_path"], info[0]["name"])
                cls.__filter_file_data(info, file_name, ext_list, total_num, sort, reverse, scan_result)
            else:
                if info.get("excluded") == "pattern": continue

                info["full_path"] = os.path.join(scan_result["full_path"], info["name"])
                info["status"] = int(os.path.exists(info["full_path"]))
                info["type"] = 0
                if info.get("asize") is None: info["asize"] = 0
                if info.get("dsize") is None: info["dsize"] = 0
                info["total_asize"] = info["asize"]
                info["total_dsize"] = info["dsize"]
                scan_result["total_asize"] += info["total_asize"]
                scan_result["total_dsize"] += info["total_dsize"]

                if file_name and file_name not in info["name"]:
                    continue

                if ext_list:
                    for ext in ext_list:
                        if str(info["name"]).endswith(ext):
                            break
                    else:
                        continue

                scan_result["list"].append(info)
                scan_result["list"].sort(key=lambda data: (data["status"], data[sort]), reverse=reverse)
                if len(scan_result["list"]) > total_num:
                    del scan_result["list"][-1]

        return scan_result

    # 过滤文件
    @classmethod
    def __filter_file_data(cls, analysis_data: list, file_name: Union[str, None], ext_list: list, total_num: int, sort: str, reverse: bool, scan_result: dict) -> None:
        """
        过滤文件
        @param analysis_data: 扫描结果信息
        @param file_name: 过滤文件名
        @param ext_list: 过滤文件后缀
        @param total_num: 过滤文件数量
        @param sort: 排序字段
        @param reverse: 是否降序
        @param scan_result: 过滤路径信息
        @return:
        """
        full_path = analysis_data[0]["full_path"]
        for info in analysis_data[1:]:
            if isinstance(info, list):  # 目录
                info[0]["full_path"] = os.path.join(full_path, info[0]["name"])
                cls.__filter_file_data(info, file_name, ext_list, total_num, sort, reverse, scan_result)
            else:
                if info.get("excluded") == "pattern": continue

                info["full_path"] = os.path.join(full_path, info["name"])
                info["status"] = int(os.path.exists(info["full_path"]))
                info["type"] = 0
                if info.get("asize") is None: info["asize"] = 0
                if info.get("dsize") is None: info["dsize"] = 0
                info["total_asize"] = info["asize"]
                info["total_dsize"] = info["dsize"]
                scan_result["total_asize"] += info["total_asize"]
                scan_result["total_dsize"] += info["total_dsize"]

                if file_name and file_name not in info["name"]:
                    continue

                if ext_list:
                    for ext in ext_list:
                        if str(info["name"]).endswith(ext):
                            break
                    else:
                        continue

                scan_result["list"].append(info)
                scan_result["list"].sort(key=lambda data: (data["status"], data[sort]), reverse=reverse)
                if len(scan_result["list"]) > total_num:
                    del scan_result["list"][-1]