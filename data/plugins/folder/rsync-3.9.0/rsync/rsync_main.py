# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2014-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <1191604998@qq.com>
# +-------------------------------------------------------------------

import shutil
from importlib import import_module
from concurrent.futures import ThreadPoolExecutor
from itertools import chain

import psutil
import os, sys, time, base64, json, re
from datetime import date, datetime
from typing import Callable, Dict, Tuple, Optional, List, Union

sys.path.append("/www/server/panel/class/")
sys.path.append("/www/server/panel/")
import public, db, crontab, files


class Sender:
    _default_ = {
        "later": False,
        "status": True,
        "source": "",
        "binary": "/usr/bin/rsync",
        "delay": 5,
        "exclude": [
            "/**.upload.tmp",
            "**/*.log",
            "**/*.tmp",
            "**/*.temp",
            "**/*.user.ini"
        ],
        "bwlimit": 1024,
        "delete": True,
        "archive": True,
        "compress": True,
        "id": None,
        "title": "",
        "verbose": True,
        "realtime": True,
    }
    error_path_list = ["/www/server/bt_sync", "/www/server/panel"]

    def __init__(self, data: dict, ):
        self._data = {}
        self._receivers: List[Receiver] = []
        for k, v in self._default_.items():
            if k in data:
                self._data[k] = data[k]
            else:
                self._data[k] = v

    def get_title(self):
        return self._data["title"]

    def check_data(self) -> Tuple[bool, str]:
        if not os.path.exists(self._data["source"]):
            return False, "指定源文件夹【{}】不存在".format(self._data["source"])
        # if cfg.check_sender_source_exists(self._data["source"]):
        #     return False, "该监听路径已经存在"

        for p in self.error_path_list:
            if p.startswith(self._data["source"]):
                return False, "源文件不能是【{}】或【{}】".format(*self.error_path_list)

        try:
            if not (0 < int(self._data["delay"]) < 600):
                return False, "延迟时间设置不合理，应该在1-600之间"
            else:
                self._data["delay"] = int(self._data["delay"])
            if not (0 < int(self._data["bwlimit"]) < 1024 * 50):
                return False, "限速设置不合理，应该在1KB-50MB之间"
            else:
                self._data["bwlimit"] = int(self._data["bwlimit"])
            if not isinstance(self._data["exclude"], list):
                self._data["exclude"] = json.loads(self._data["exclude"])
        except (ValueError, TypeError, json.JSONDecodeError):
            return False, '参数设置错误'

        for item in ("delete", "archive", "compress"):
            if not isinstance(self._data[item], bool):
                return False, '参数设置错误'

        if not self._data["title"]:
            path = self._data["source"].rstrip("/")
            self._data["title"] = os.path.basename(path)

        return True, ''

    def check_repeat_recv_name(self) -> bool:
        if self._receivers:
            return False
        use_name = set()
        for r in self._receivers:
            if r.get_name() not in use_name:
                use_name.add(r.get_name())
            else:
                return True
        return False

    def add_receivers(self, list_receivers: List["Receiver"]) -> None:
        for receiver in list_receivers:
            if isinstance(receiver, Receiver):
                self._receivers.append(receiver)

    def to_bt_sync_config_map(self, debug: bool = False):
        if not self._receivers:
            raise ValueError("没有接受者数据")

        target_list = [target.to_bt_sync_config_map(debug=debug) for target in self._receivers if target.get_status()]
        result = {
            "source": self._data["source"],
            "binary": self._data["binary"], "delay": self._data["delay"],
            "exclude": self._data["exclude"],
            "target_list": target_list,
        }
        return result

    def _get_send_cmd(self, receiver_data, first_send=False) -> str:
        """
        获取同步命令; 一次获取一组
        """
        exclude_list: list = self._data["exclude"].copy()
        if "**.user.ini" not in self._data["exclude"]:
            exclude_list.append("**.user.ini")

        exclude = "--exclude={%s}" % ','.join('"' + e + '"' for e in exclude_list)
        delete = "--delete" if receiver_data["delete"] else ""
        bw_limit = "--bwlimit=" + str(receiver_data["bwlimit"])

        # backup = "b" if first_send and not receiver_data["delete"] else ""
        compress = "z" if receiver_data["compress"] else ""
        archive = "a" if receiver_data["archive"] else ""
        # p = "-{}{}{}uPv".format(backup, compress, archive)
        p = "-{}{}uPv".format(compress, archive)

        if receiver_data["work_type"] == 0:
            cmd = "/usr/bin/rsync {} {} {} {} {} {}".format(
                p, delete, exclude, bw_limit, self._data["source"], receiver_data["target"])
        elif receiver_data["work_type"] == 1:
            pass_file_path = "{}/sclient/{}_pass".format(cfg.rsync_plugin_path, receiver_data['name'])
            public.writeFile(pass_file_path, receiver_data['password'])
            public.ExecShell("chmod 600 " + pass_file_path)
            receiver_data["password_file"] = pass_file_path

            pass_cmd = "--password-file=" + pass_file_path
            target = "{}@{}::{}".format(receiver_data["name"], receiver_data["ip"], receiver_data["name"])

            cmd = "/usr/bin/rsync {} {} {} {} {} {} {}".format(
                p, delete, exclude, pass_cmd, bw_limit, self._data["source"], target)
        else:
            pass_file_path = "{}/sclient/{}_pass".format(cfg.rsync_plugin_path, receiver_data['name'])
            public.writeFile(pass_file_path, receiver_data['password'])
            public.ExecShell("chmod 600 " + pass_file_path)
            receiver_data["password_file"] = pass_file_path

            ssh = "ssh -p {} -i {}".format(receiver_data["port"], pass_file_path)
            target = "root@{}:{}".format(receiver_data["ip"], receiver_data["target"])

            cmd = "/usr/bin/rsync {} {} {} {} -e \"{}\" {} {}".format(
                p, delete, exclude, bw_limit, ssh, self._data["source"], target)
        logfile = cfg.rsync_plugin_path + "/sclient/" + receiver_data["name"] + "_exec.log"
        cmd_file = cfg.rsync_plugin_path + '/sclient/' + receiver_data["name"] + '_cmd'
        public.writeFile(cmd_file, cmd + " >> " + logfile + " 2>&1")
        get_time_str = "执行时间=========>{}<=========".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        cmd_str = (
            "echo \"{}\" >> {} &&"
            "nohup sh -c '{} >> {} 2>&1; echo 执行结束======================================= >> {}' & > /dev/null"
        ).format(get_time_str, logfile, cmd, logfile, logfile)
        # cmd_str = "echo \"{}\" >> {} && nohup {} >> {} 2>&1 &".format(get_time_str, logfile, cmd, logfile)
        return cmd_str

    def get_send_cmd(self, receiver_names: List[str] = None, first_send=False) -> List[str]:
        result = []
        for receiver in self._receivers:
            if receiver_names is None:
                result.append(self._get_send_cmd(receiver.get_data(), first_send=first_send))
                continue
            if receiver.get_data()["name"] in receiver_names:
                result.append(self._get_send_cmd(receiver.get_data(), first_send=first_send))
        return result

    @classmethod
    def get_default(cls):
        return cls._default_.copy()

    def set_id(self):
        if self._data["id"] is None:
            self._data["id"] = cfg.get_next_sender_id()
        receiver_id = cfg.get_next_receiver_id()
        for r in self._receivers:
            if r.set_id(receiver_id):
                receiver_id += 1

    def save_data_to_config(self, later=False):
        """later 控制是否稍后同步"""
        save_data = self._data.copy()
        if later:
            save_data["later"] = True
            save_data["status"] = False
        save_data["target_list"] = [r.save_data_to_config(later=later) for r in self._receivers]
        for i in range(len(cfg.config["senders"])):
            if cfg.config["senders"][i]["id"] == self._data["id"]:
                cfg.config["senders"][i] = save_data
                break
        else:
            cfg.config["senders"].append(save_data)

    def modify_data(self, data: dict) -> Union[bool, dict]:
        """检查发送方修改的信息"""
        change_source = False
        if "source" in data and data["source"] != self._data["source"]:
            if not os.path.exists(data["source"]):
                return public.returnMsg(False, "指定源文件夹【{}】不存在".format(data["source"]))
            # if cfg.check_sender_source_exists(data["source"]):
            #     return public.returnMsg(False, "该发送路径已经存在对应任务")
            self._data["source"] = data["source"]
            change_source = True

        if "delay" in data and int(data["delay"]) != self._data["delay"]:
            if not (0 < int(data["delay"]) < 600):
                return public.returnMsg(False, "延迟时间设置不合理，应该在1-600秒之间")

            self._data["delay"] = int(data["delay"])

        if "exclude" in data and data["exclude"] != self._data["exclude"]:
            if isinstance(data["exclude"], list):
                self._data["exclude"] = []
                for e in data["exclude"]:
                    if isinstance(e, str):
                        self._data["exclude"].append(e)

        return change_source

    def modify_receivers(self, receivers_data: List[Dict], not_verify_conn: bool = False):
        """
        检查接收方信息, 返回所有需要初始化处理的接收方
        """
        new_receivers = []  # 新建立的接收方
        for i in range(len(receivers_data) - 1, -1, -1):  # 倒序移除新增的
            if receivers_data[i]["id"] is None:
                new_r = Receiver(receivers_data[i])
                flag, msg = new_r.check_data(not_verify_conn=not_verify_conn)
                if flag is False:
                    return False, msg
                new_receivers.append(new_r)
                del receivers_data[i]

        need_init_name = []  # 需要重现发送的接收方
        for i in range(len(self._receivers) - 1, -1, -1):
            r_id = self._receivers[i].get_id()
            have_this = False  # 是否已被删除
            for rc in receivers_data:
                if rc["id"] != r_id:
                    continue
                have_this = True
                check_msg = self._receivers[i].modify_receiver_data(rc)
                if isinstance(check_msg, dict):
                    return check_msg
                if check_msg is True:
                    need_init_name.append(rc["name"])
            if not have_this:
                self._receivers[i].remove_file()
                del self._receivers[i]

        need_init_name.extend([r.get_name() for r in new_receivers])
        self._receivers.extend(new_receivers)
        self.set_id()

        return need_init_name

    def has_receivers(self) -> bool:
        if self._receivers is None:
            return False
        return len(self._receivers) > 0

    def close_later(self) -> None:
        """关闭稍后执行的标记"""
        if "later" in self._data and self._data["later"] is True:
            self._data["later"] = False
            self._data["status"] = True
            for r in self._receivers:
                getattr(r, "_data")["status"] = True


class Receiver(object):
    """
    work_type:工作方式，0: 本地, 1: Rsync, 2: SSH
    target: 目标文件夹， rsync方式没有该项，是name
    name:rsync目标用户和文件夹代称
    password_file: Rsync情况下表示目标用户的密码文件，SSH情况下表示ssh秘钥文件，权限要设为600
    ip: 目标客户机器的ip
    port: 目标客户机器开放的端口, ssh默认22，rsync默认873
    cron: 周期信息
    bwlimit: 限速，可在接收单独设置
    delete: 默认的是否同步删除文件，可在接收中再设置
    archive: 全部同步，默认为True
    compress: 使用压缩，默认为True
    """
    _ip_regx = r"^((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$"
    _rsync_tmp_path = "/tmp/bt_rsync"
    _default_ = {
        "secret_key": "",
        "work_type": 0,
        "target": "",
        "name": "",
        "password_file": "",
        "ip": "",
        "port": 873,
        "id": None,
        "title": "",
        "bwlimit": 1024,
        "delete": True,
        "archive": True,
        "compress": True,
        "verbose": True,
        "password": "",
        "realtime": True,
        "status": True,
        "cron": {
            "type": "minute-n",
            "where1": "5",
            "hour": "",
            "minute": "",
            "seconds": ""
        }
    }

    def __init__(self, data: dict):
        self._data: Dict[str, Union[dict, bool, int, str]] = {}
        self._receivers = []
        for k, v in self._default_.items():
            if k in data:
                self._data[k] = data[k]
            else:
                self._data[k] = v
        if not self._data["title"]:
            self._data["title"] = self._data["name"]

    @classmethod
    def get_default(cls):
        return cls._default_.copy()

    def check_cron(self) -> bool:
        if self._data["realtime"]:
            return True
        data_test_func: Dict[str, Callable] = {
            "type": lambda x: x in ("seconds-n", "minute-n", "hour", "hour-n", "day", "day-n"),
            # 为空字符串或者为有效的数据
            "hour": lambda x: isinstance(x, str) and (x == "" or x.isdigit() and 0 <= int(x) <= 24),
            "minute": lambda x: isinstance(x, str) and (x == "" or x.isdigit() and 0 <= int(x) <= 60),
            "seconds": lambda x: isinstance(x, str) and (x == "" or x.isdigit() and 0 <= int(x) <= 60),
            # where1为有效的数据时应该大于0
            "where1": lambda x: isinstance(x, str) and (x == "" or x.isdigit() and 0 < int(x) <= 60),
        }
        for k, func in data_test_func.items():
            if not (k in self._data["cron"] and func(self._data["cron"][k])):
                return False
        return True

    def check_data(self, not_verify_conn: bool = False) -> Tuple[bool, Union[str, dict]]:
        if self._data["work_type"] not in (0, 1, 2):
            return False, "模式选择错误"

        if not self.check_cron():
            return False, "周期设置参数错误"
        if bool(self._data["secret_key"]) and self._data["work_type"] == 1:
            data, err = self.parser_secret_key(self._data["secret_key"])
            if err:
                return False, err
            self._data["name"] = data["A"]
            self._data["password"] = data["B"]
            self._data["port"] = data["C"]
            self._data["ip"] = data["D"]
            self._data["target"] = data["E"]

        if isinstance(self._data["port"], str) and self._data["port"].isdigit():
            self._data["port"] = int(self._data["port"])

        if not isinstance(self._data["port"], int):
            self._data["port"] = 0

        if bool(self._data["secret_key"]) and self._data["work_type"] == 2:
            data, err = self.parser_secret_key(self._data["secret_key"], is_ssh=True)
            if err:
                return False, err
            self._data["password"] = self._data["secret_key"]

        try:
            if not (0 < int(self._data["bwlimit"]) < 1024 * 50):
                return False, "限速设置不合理，应该在1KB-50MB之间"
            else:
                self._data["bwlimit"] = int(self._data["bwlimit"])
        except (ValueError, TypeError):
            return False, '参数设置错误'

        for item in ("delete", "archive", "compress"):
            if not isinstance(self._data[item], bool):
                return False, '参数设置错误'

        if not self._data["name"]:
            return False, "缺少名称"
        # 有id 编辑的时候不用改
        elif cfg.check_receiver_name_exists(self._data["name"]) and self._data["id"] is None:
            return False, "该名称的接收任务已存在"

        if self._data["work_type"] != 1 and self._data["target"]:
            if self._data["target"][-1] != "/":
                self._data["target"] = self._data["target"] + "/"

        if self._data["work_type"] == 0:
            # 本地同步且有文件
            if os.path.exists(self._data["target"]) and sum((1 for _ in os.listdir(self._data["target"]))) != 0:
                if self._data.get("delete", True):
                    return False, "本地被同步的目录中含有文件，完全同步的会覆盖这些文件，请注意"
        # 检查ip
        else:
            if not self._data["ip"]:
                return False, "没有目标ip信息"
            if not re.search(self._ip_regx, self._data["ip"].strip()):
                return False, "IP格式错误"

        if not_verify_conn:
            return True, ""
        return self.verify_communication(self._data["password"])

    def to_bt_sync_config_map(self, debug):
        # 更改权限
        if self._data["work_type"] != 0:
            if os.path.exists(self._data["password_file"]):
                os.chmod(self._data["password_file"], 0o600)
            else:
                self.write_pass(self._data["password"])
        res = self._data.copy()
        res.pop("secret_key", ""), res.pop("password", ""), res.pop("status", "")
        if self._data["realtime"] is True:
            res.pop("cron", "")
        res.pop("realtime", "")
        res["verbose"] = debug
        return res

    def verify_communication(self, password: str) -> Tuple[bool, Union[str, dict]]:
        if self._data["work_type"] == 0:
            return self._verify_local()
        flag, err_msg = self._check_port()
        if not flag:
            return False, err_msg
        if self._data["work_type"] == 1:
            return self._verify_rsync(password)
        else:
            return self._verify_ssh(password)

    def _verify_local(self) -> Tuple[bool, Union[str, dict]]:
        _cmd = '/usr/bin/rsync -n --port=873 --stats {}'.format(self._data["target"])
        result = public.ExecShell(_cmd)
        if result[0].find('Number of files') != -1:
            return True, self._parse_target_dir(result[0])
        else:
            return False, '链接错误：{}'.format(result[1])

    def _verify_rsync(self, password: str) -> Tuple[bool, Union[str, dict]]:
        local_ip = self.get_local_ip()
        if local_ip is None:
            local_ips = ("0.0.0.0", "127.0.0.1")
        else:
            local_ips = ("0.0.0.0", "127.0.0.1", local_ip)
        if self._data["ip"] in local_ips:
            return False, "本地同步，请建立本地同步任务"
        tmp_file = "{}/{}_pass".format(self._rsync_tmp_path, self._data["name"])
        if not os.path.exists(self._rsync_tmp_path):
            os.makedirs(self._rsync_tmp_path, 0o755)
        if not public.writeFile(tmp_file, password):
            return False, "测试文件写入失败，请检查/tmp/bt_rsync目录的权限"
        else:
            os.chmod(tmp_file, 0o600)
        total_size_num_cmd = '/usr/bin/rsync -n --port=873 --stats --password-file={} {}@{}::{}'.format(
            tmp_file, self._data["name"], self._data["ip"], self._data["name"])
        result = public.ExecShell(total_size_num_cmd)
        os.remove(tmp_file)
        if result[1].lower().find('permission denied') != -1:
            return False, '登录密钥连接不上远程服务器或服务未启动'
        elif result[1].lower().find('error') != -1:
            return False, '连接出错了:{}'.format(result[1])
        elif result[0].find('Number of files') != -1:
            return True, self._parse_target_dir(result[0])
        else:
            return False, '链接错误：{}'.format(result[1])

    def _verify_ssh(self, password: str) -> Tuple[bool, Union[str, dict]]:
        local_ip = self.get_local_ip()
        if local_ip is None:
            local_ips = ("0.0.0.0", "127.0.0.1")
        else:
            local_ips = ("0.0.0.0", "127.0.0.1", local_ip)
        if self._data["ip"] in local_ips:
            return False, "本地同步，请建立本地同步任务"
        if not os.path.exists(self._rsync_tmp_path):
            os.makedirs(self._rsync_tmp_path, 0o755)
        tmp_file = "{}/{}_sshpass".format(self._rsync_tmp_path, self._data["name"])
        if not public.writeFile(tmp_file, password):
            return False, "测试文件写入失败，请检查/tmp/bt_rsync目录的权限"
        else:
            os.chmod(tmp_file, 0o600)
        if not bool(self._data["name"].strip()):
            self._data["name"] = "root"
        _cmd = '/usr/bin/rsync -n --timeout=60 --stats -e "ssh -p {} -o StrictHostKeyChecking=no -i {}" root@{}:{}' \
            .format(self._data["port"], tmp_file, self._data["ip"], self._data["target"])
        result = public.ExecShell(_cmd)
        os.remove(tmp_file)
        if result[1].lower().find('permission denied') != -1:
            return False, '登录密钥连接不上远程服务器或服务未启动'
        elif result[0].find('Number of files') != -1:
            return True, self._parse_target_dir(result[0])
        else:
            return False, '链接错误：{}'.format(result[1])

    def write_pass(self, passwd, force=True):
        """
        设置rsync的任务传输密码
        @param passwd: 密码
        @param force:强制操作
        @return:
        """
        auth_pass = cfg.rsync_plugin_path + '/sclient/' + self._data["name"] + '_pass'
        if os.path.exists(auth_pass) and not force:
            return
        public.writeFile(auth_pass, passwd)
        public.ExecShell("chmod 600 " + auth_pass)

    @staticmethod
    def parser_secret_key(secret_key: str, is_ssh: bool = False) -> Tuple[Optional[dict], Optional[str]]:
        """
        第一项返回解析的信息，shh为空
        第二项返回是否通过验证信息， 为空表示验证无误，为str时，是错误信息
        """
        if not is_ssh:
            secret_key = secret_key.strip()
            try:
                if sys.version_info[0] == 3:
                    server_conf: dict = json.loads(base64.b64decode(secret_key).decode('utf-8'))
                else:
                    server_conf: dict = json.loads(base64.b64decode(secret_key))
            except:
                return None, "错误的接收密钥"
            return server_conf, None
        else:
            key_list = ('END RSA PRIVATE KEY', '-----END OPENSSH PRIVATE KEY-----', '-----END EC PRIVATE KEY-----')
            for i in key_list:
                if secret_key.find(i) != -1:
                    break
            else:
                return None, '错误的ssh登录密钥'
            return None, None

    def _check_port(self, timeout: float = 5) -> Tuple[bool, str]:
        """
        检查通信是否正常
        @param timeout: 超时时间
        @return:
        """
        import socket
        try:
            s = socket.socket()
            s.settimeout(timeout)
            s.connect((self._data["ip"], int(self._data["port"])))
            s.close()
        except:
            return False, "无法连接[{}],请检查IP地址是否正确,若正确无误，请检查远程服务器的安全组及防火墙是否正确放行[{}]端口!".format(
                self._data["ip"], self._data["port"]
            )
        return True, ""

    def get_data(self):
        return self._data

    def set_password_file(self, filename):
        self._data["password_file"] = filename

    @classmethod
    def get_local_ip(cls) -> Optional[str]:
        try:
            local_ip = public.GetLocalIp()
        except:
            return None
        if isinstance(local_ip, str) and re.match(cls._ip_regx, local_ip):
            return local_ip
        return None

    def set_id(self, the_id) -> bool:
        if self._data["id"] is None:
            self._data["id"] = the_id
            return True
        return False

    def get_id(self) -> int:
        return self._data["id"]

    def get_name(self) -> int:
        return self._data["name"]

    def modify_receiver_data(self, data: dict):
        """检查接收方修改的信息"""
        # target bwlimit delete compress
        change_node = False
        if "target" in data and data["target"] != self._data["target"]:
            if self._data["work_type"] == 0 and not os.path.exists(data["target"]):
                return public.returnMsg(False, "无效的目标路径")
            self._data["target"] = data["target"]
            change_node = True

        if "bwlimit" in data and int(data["bwlimit"]) != self._data["bwlimit"]:
            if not (1 < int(data["bwlimit"]) < 1024 * 50):
                return public.returnMsg(False, "限速设置不合理，应该在1KB-50MB之间")
            self._data["bwlimit"] = int(data["bwlimit"])

        if "delete" in data and data["delete"] != self._data["delete"] and isinstance(data["delete"], bool):
            self._data["delete"] = data["delete"]

        if "compress" in data and data["compress"] != self._data["compress"] and isinstance(data["compress"], bool):
            self._data["compress"] = data["compress"]

        if "realtime" in data and data["realtime"] != self._data["realtime"] and isinstance(data["realtime"], bool):
            self._data["realtime"] = data["realtime"]

        if "cron" in data and not data["realtime"]:
            data_test_func: List[Tuple[str, Callable]] = [
                ("type", lambda x: x in ("seconds-n", "minute-n", "hour", "hour-n", "day", "day-n")),
                # 为空字符串或者为有效的数据
                ("hour", lambda x: isinstance(x, str) and (x == "" or x.isdigit() and 0 <= int(x) <= 24)),
                ("minute", lambda x: isinstance(x, str) and (x == "" or x.isdigit() and 0 <= int(x) <= 60)),
                ("seconds", lambda x: isinstance(x, str) and (x == "" or x.isdigit() and 0 <= int(x) <= 60)),
                # where1为有效的数据时应该大于0
                ("where1", lambda x: isinstance(x, str) and (x == "" or x.isdigit() and 0 < int(x) <= 60)),
            ]
            for k, func in data_test_func:
                if not (k in data["cron"] and func(data["cron"][k])):
                    return public.returnMsg(False, "周期时间设置错误")
            self._data["cron"] = data["cron"]

        return change_node

    def get_status(self):
        return self._data["status"]

    def save_data_to_config(self, later):
        res_data = self._data.copy()
        if later:
            res_data['status'] = False
        return res_data

    def remove_file(self):
        """删除相关文件"""
        pass_file = self._data["password_file"]
        if os.path.exists(pass_file):
            os.remove(pass_file)

        status_file = cfg.bt_sync_status_path + "/" + self._data["name"]
        if os.path.exists(status_file):
            os.remove(status_file)

        log_file = "{}/{}_log.log".format(cfg.bt_sync_log_path, self._data["name"])
        if os.path.exists(log_file):
            os.remove(log_file)

        exec_log_file = "{}/sclient/{}_exec.log".format(cfg.rsync_plugin_path, self._data["name"])
        if os.path.exists(exec_log_file):
            os.remove(exec_log_file)

    @staticmethod
    def _parse_target_dir(data: str) -> dict:
        rep = re.compile(r"\s*Number\s*of\s*files:\s*(?P<total>\d+)\s*(\(.*dir:\s*(?P<dir>\d+).*\))?")
        res = rep.search(data)
        public.print_log(data)
        if not res:
            return public.returnMsg(False, "连接检测错误")
        total, _dir = int(res.group("total")), res.group("dir")
        if _dir is not None:
            _dir = int(_dir)
        return {
            "status": True,
            "have_file": not (total == 1 and _dir == 1) or (total == 0 and _dir is None)
        }


class ConfigUtil:
    """
    操作配置文件的工具类
    """
    rsync_file = "/etc/rsyncd.conf"
    rsync_plugin_path = '{}/plugin/rsync'.format(public.get_panel_path())
    bt_sync_path = "/www/server/bt_sync"
    bt_sync_bin = "{}/bin/btsync".format(bt_sync_path)
    bt_sync_file = bt_sync_path + "/bt_sync_config.conf"
    bt_sync_log_path = bt_sync_path + "/logs"
    bt_sync_status_path = bt_sync_path + "/status"
    client_path = rsync_plugin_path + '/sclient'
    old_config_file = rsync_plugin_path + '/config.json'
    config_file = rsync_plugin_path + '/config4.json'
    debug_tip = rsync_plugin_path + '/debug.tip'
    push_cmd_list = [
        '{}/pyenv/bin/python3.7'.format(public.get_panel_path()),
        '{}/class/push/rsync_push.py'.format(public.get_panel_path())
    ]

    def __init__(self):
        self._config: Optional[dict] = None

    @property
    def config(self) -> dict:
        if self._config is not None:
            return self._config
        self._get_config()
        return self._config

    def conf_reload(self):
        """刷新数据， 从文件中再次读取"""
        self._config = None

    @classmethod
    def to_4x_config(cls) -> dict:
        """
        讲旧的配置文件转化会新的配置文件
        不删除源配置文件
        """
        # 当拥有旧的配置文件，并且没有新配置文件时
        if not os.path.exists(cls.old_config_file):
            raise ValueError("Old file not found")
        try:
            old_data: dict = json.loads(public.readFile(cls.old_config_file))
        except (json.JSONDecodeError, TypeError):
            raise ValueError("Old file Error")
        new_data = {
            "global": old_data["global"],
            "modules": old_data["modules"],
        }
        senders = []
        for idx, task in enumerate(old_data.get("client", [])):
            receiver = cls.get_default_receiver_conf()
            sender = cls.get_default_sender_conf()
            receiver["id"] = idx
            receiver["title"] = task["ps"] or task["name"]
            sender["id"] = idx
            sender["title"] = task["ps"] or task["name"]
            # 把默认项优先放入sender
            sender["exclude"] = task["exclude"]
            sender["source"] = task["path"]
            sender["delay"] = int(task["delay"])
            receiver["bwlimit"] = sender["bwlimit"] = int(task["rsync"]["bwlimit"])
            receiver["delete"] = sender["delete"] = task["delete"] == "true"

            receiver["archive"] = sender["archive"] = task["rsync"]["archive"] == "true"
            receiver["compress"] = sender["compress"] = task["rsync"]["compress"] == "true"
            receiver["verbose"] = sender["verbose"] = task["rsync"]["verbose"] == "true"
            receiver["realtime"] = sender["realtime"] = task["realtime"]

            receiver["password"] = task['password']
            # 定时任务做特殊处理, 原本地没有周期
            receiver["cron"] = task["cron"] if len(task["cron"]) > 0 else receiver["cron"]
            receiver["cron"]["seconds"] = ""
            receiver["cron"].pop("id", 0), receiver["cron"].pop("port", 0)

            # 必定有name
            receiver["name"] = task["name"]
            # 本地同步
            if task["model"] == "default.direct":
                receiver["work_type"] = 0
                receiver["target"] = task["to"]
            # ssh + rsync
            elif int(task["ssh_type"]) in (3, 4):
                receiver["work_type"] = 2
                receiver["target"] = task["to"]
                receiver["ip"] = task["ip"]
                receiver["port"] = int(task["rsync"]["port"])
                receiver["password_file"] = "{}/{}_pass".format(cls.client_path, task["name"])
                if not os.path.exists(receiver["password_file"]):
                    continue
                else:
                    os.chmod(receiver["password_file"], 0o600)
            # rsync
            else:
                receiver["work_type"] = 1
                receiver["ip"] = task["ip"]
                receiver["port"] = int(task["rsync"]["port"]) if bool(task["rsync"]["port"]) else 0
                receiver["password_file"] = "{}/{}_pass".format(cls.client_path, task["name"])
                if not os.path.exists(receiver["password_file"]):
                    continue
                else:
                    os.chmod(receiver["password_file"], 0o600)

            statu = public.readFile(cls.rsync_plugin_path + '/sclient/' + task["name"] + '_status')
            if statu == "False":
                statu = False
            else:
                statu = True
            sender["status"] = statu
            receiver["status"] = True
            sender["target_list"] = [receiver, ]
            senders.append(sender)

        new_data["senders"] = senders
        public.writeFile(cls.config_file, json.dumps(new_data))
        return new_data

    def _get_config(self):
        if not os.path.exists(self.config_file):
            try:
                config = self.to_4x_config()
            except:
                config = self.default_config()
            else:
                self.save_conf(is_rsyncd=True, is_bt_sync=True)
        else:
            try:
                config: dict = json.loads(public.readFile(self.config_file))
            except (json.JSONDecodeError, TypeError):
                config = self.default_config()

        self._config = config

    def get_old_config(self):
        try:
            old_data: dict = json.loads(public.readFile(self.old_config_file))
            return old_data
        except (json.JSONDecodeError, TypeError):
            return self.config

    def save_conf(self, is_rsyncd: bool = False, is_bt_sync: bool = False):
        """
        写配置文件
        """
        if not self._config:  # 理论不会出现的情况
            self._get_config()
        public.writeFile(self.config_file, json.dumps(self._config))
        if is_rsyncd:
            self._write_rsync_conf()
        if is_bt_sync:
            self._write_bt_sync_conf()
        return True

    @staticmethod
    def default_config() -> dict:
        return {
            "global": {
                "uid": "root",
                "use chroot": "no",
                "dont compress": "*.gz *.tgz *.zip *.z *.Z *.rpm *.deb *.bz2 *.mp4 *.avi *.swf *.rar",
                "hosts allow": "",
                "max connections": 200,
                "gid": "root",
                "timeout": 600,
                "lock file": "/var/run/rsync.lock",
                "pid file": "/var/run/rsyncd.pid",
                "log file": "/var/log/rsyncd.log",
                "port": 873
            },
            "modules": [],
            "senders": []
        }

    @staticmethod
    def get_default_receiver_conf() -> dict:
        return Receiver.get_default()

    @staticmethod
    def get_default_sender_conf() -> dict:
        return Sender.get_default()

    @classmethod
    def _write_rsyncd_passfile(cls, name, user, passwd):
        """
        @param name:
        @param user:
        @param passwd:
        @return:
        """
        auth_pass = cls.rsync_plugin_path + '/secrets/' + name + '.db'
        public.writeFile(auth_pass, user + ':' + passwd)
        public.ExecShell("chmod 600 " + auth_pass)
        return True

    def _write_rsync_conf(self):
        """
        写rsync的配置文件
        """
        conf_str_list = []
        for g_k, g_v in self.config['global'].items():
            if type(g_v) == bool and g_v is True:
                conf_str_list.append(g_k)
            else:
                conf_str_list.append("{} = {}".format(g_k, str(g_v)))
        conf_str_list.append("")

        for mod in self.config['modules']:
            if mod.get("recv_status", True) is False:  # 跳过未开启的
                continue
            self._write_rsyncd_passfile(mod['name'], mod['auth users'], mod['password'])
            if not os.path.exists(mod['path']):
                public.ExecShell("mkdir -p " + mod['path'])

            mod_conf = (
                "[{}]\n"
                "path = {}\n"
                "comment = {}\n"
                "read only = {}\n"
                "auth users = {}\n"
                "secrets file = {}\n"
                "{}"
            ).format(
                mod['name'],
                mod["path"],
                mod["comment"],
                mod["read only"],
                mod["auth users"],
                mod["secrets file"],
                "ignore errors\n" if mod["ignore errors"] else "",
            )
            conf_str_list.append(mod_conf)

        conf_str = '\n'.join(conf_str_list)

        public.writeFile(self.rsync_file, conf_str)
        # os.system("/etc/init.d/rsynd stop")
        # os.system(
        #     "pid=`ps -ef|grep rsync|grep -v grep|awk '{print $2}'` && [[ $pid != \"\" ]] && for i in $pid;do kill -9 $i;done")
        # os.system("/etc/init.d/rsynd start")
        out, _ = public.ExecShell("/etc/init.d/rsynd restart")
        if out.find("Starting rsync...  done"):
            return True
        return False

    def get_next_sender_id(self):
        if not self.config["senders"]:
            return 0
        next_id = max((s["id"] for s in self.config["senders"])) + 1
        return next_id

    def get_next_receiver_id(self):
        if not self.config["senders"]:
            return 0
        ids = []
        for s in self.config["senders"]:
            for r in s["target_list"]:
                ids.append(r["id"])
        if not ids:
            return 0
        return max(ids) + 1

    def get_sender_by_id(self, sender_id) -> Optional[dict]:
        for sender_data in self.config["senders"]:
            if sender_data["id"] == sender_id:
                return sender_data
        return None

    def check_sender_source_exists(self, source) -> bool:
        if not self.config["senders"]:
            return False
        for sender_data in self.config["senders"]:
            if source == sender_data["source"]:
                return True
        return False

    def check_receiver_name_exists(self, name) -> bool:
        for receiver_data in chain(*(s["target_list"] for s in self.config["senders"])):
            if name == receiver_data["name"]:
                return True
        return False

    @classmethod
    def bt_sync_running(cls) -> bool:
        try:
            pid_file = cls.bt_sync_path + "/bt_sync.pid"
            pid = int(public.readFile(pid_file))
            if pid in psutil.pids():
                return True
        except ValueError:
            pass
        return False

    @staticmethod
    def _merge_rsync_configs(rsync_configs: List[dict]) -> List[dict]:
        merge_dict = dict()
        for conf in rsync_configs:
            if conf["source"] not in merge_dict:
                merge_dict[conf["source"]] = conf
            else:
                merge_dict[conf["source"]]["target_list"].extend(conf["target_list"])

        return list(merge_dict.values())

    def _write_bt_sync_conf(self):
        rsync_configs = []
        log_level = 0 if os.path.exists(self.debug_tip) else 1
        for send_data in self.config["senders"]:
            if send_data.get("later", False):
                continue
            if send_data["status"] is False:
                continue
            sender = Sender(send_data)
            receivers = [Receiver(r) for r in send_data["target_list"] if r["status"]]
            if not receivers:
                continue
            sender.add_receivers(receivers)
            rsync_configs.append(sender.to_bt_sync_config_map(debug=(log_level == 0)))

        # rsync_configs = self._merge_rsync_configs(rsync_configs)

        conf = {
            "base": {
                "log_file": self.bt_sync_path + "/run_logs.log",
                "logs_path": self.bt_sync_log_path,
                "status_path": self.bt_sync_status_path,
                "push_cmd": self.push_cmd_list,
                "log_level": log_level,
            },
            "rsync_configs": rsync_configs
        }

        public.writeFile(self.bt_sync_file, json.dumps(conf))
        if self.bt_sync_running():
            out, err = public.ExecShell(self.bt_sync_bin + " -s reload")
            public.print_log("重启btsync")
            public.print_log(out)
            public.print_log(err)
        else:
            exec_log = self.bt_sync_path + "/exec_logs.log"
            cmd_str = "nohup {} -c {} 2>&1 >> {} &".format(self.bt_sync_bin, self.bt_sync_file, exec_log)
            out, err = public.ExecShell(cmd_str)
            public.print_log("启动btsync")
            public.print_log(out)
            public.print_log(err)


cfg = ConfigUtil()


class rsync_main:
    _log_name = '文件同步工具'
    filter_template_path = "{}/data/rsync_filter_template.json".format(public.get_panel_path())

    def __init__(self):
        # self.create_table()
        s_dir = cfg.rsync_plugin_path + '/sclient'
        if not os.path.exists(s_dir):
            public.ExecShell("mkdir -p " + s_dir)
        s_dir = cfg.rsync_plugin_path + '/secrets'
        if not os.path.exists(s_dir):
            public.ExecShell("mkdir -p " + s_dir)

        self._create_bt_sync_cron()

        s_push_file = "{}/rsync_push.py".format(cfg.rsync_plugin_path)
        d_push_file = "{}/class/push/rsync_push.py".format(public.get_panel_path())
        if not os.path.exists(d_push_file):
            shutil.copy(s_push_file, d_push_file)
        else:
            data = public.readFile(d_push_file)
            if data.find("# | Version: 4.0") == -1:
                os.remove(d_push_file)
                shutil.copy(s_push_file, d_push_file)

    @staticmethod
    def get_global_conf(get: public.dict_obj = None):
        """
        获取rsync全局设置
        """
        cfg.conf_reload()
        global_conf = cfg.config['global']
        global_conf["dont compress"] = global_conf["dont compress"].replace(" ", ",")
        result = {
            'modules': cfg.config['modules'],
            'global': global_conf,
            'open': (len(public.ExecShell("/etc/init.d/rsynd status|grep 'already running'")[0]) > 1) | False,
            'port_status': firewall_tool.get_port_status(global_conf.get("port"))
        }
        return result

    def modify_global_conf(self, get: public.dict_obj):
        cfg.conf_reload()
        config = cfg.config
        # 解决修改端口导致已存在的接收任务无法正常传输的问题
        if len(config['modules']) > 0:
            if 'port' in get and int(get.port) != config['global']['port']:
                return public.returnMsg(False, "禁止修改端口,已存在接收任务时修改端口会导致传输失败!")
        if 'port' in get:
            config['global']['port'] = int(get.port)
        if 'hosts_allow' in get:
            config['global']['hosts allow'] = " ".join(get.hosts_allow.split())
        if 'timeout' in get:
            config['global']['timeout'] = int(get.timeout)
        if 'max_connections' in get:
            config['global']['max connections'] = int(get.max_connections)
        if 'dont_compress' in get:
            config['global']['dont compress'] = getattr(get, "dont_compress", "").replace(",", " ")
        cfg.save_conf(is_rsyncd=True)
        self._write_logs('修改rsync服务器全局配置')
        return public.returnMsg(True, '设置成功!')

    @staticmethod
    def make_secretkey(name, passwd, port, path, ip=None) -> str:
        """
        生成base64加密密钥
        @param name: 用户名
        @param passwd: 密码
        @param port: 端口
        @param path: 路劲
        @param ip: ip
        @return:
        """
        data = json.dumps({'A': re.sub(r"(\d+\.){3}\d+_", '', name), 'B': passwd, 'C': port, 'D': ip, 'E': path})
        if sys.version_info[0] == 2:
            return str(base64.b64encode(data))
        result = base64.b64encode(data.encode('utf-8'))
        if type(result) == bytes:
            result = result.decode('utf-8')
        return str(result)

    def get_secretkey(self, get):
        module = self.get_module(get)
        if "password" not in module:
            return module
        get_ip = public.GetLocalIp()
        secretkey = self.make_secretkey(module['name'], module['password'], module['port'], module['path'], get_ip)
        return secretkey

    @staticmethod
    def _check_module_path(path) -> Optional[str]:
        """
        检查路径是否已有接收任务
        """
        for mod in cfg.config.get('modules', []):
            if path == mod.get("path", None):
                return mod["name"]
        return None

    @staticmethod
    def _check_module_name_exists(name) -> bool:
        """
        检查是否存在相同用户名
        @param name:
        """
        for mod in cfg.config.get('modules', []):
            if name == mod.get("name", None):
                return True
        return False

    @staticmethod
    def _check_is_system_path(path) -> bool:
        """
        检查是否为系统关键目录
        @param path: 路径名
        """
        if not path:
            return False
        if path[-1] != '/':
            path += '/'
        for dir_name in ('/usr/', '/var/', '/proc/', '/boot/', '/etc/', '/dev/', '/root/', '/run/', '/sys/', '/tmp/'):
            if path.startswith(dir_name):
                return True
        if path in ['/', '/www/', '/www/server/', '/home/']:
            return True
        return False

    def add_module(self, get):
        cfg.conf_reload()
        exists_name = self._check_module_path(get.path)
        if exists_name is not None:
            return public.returnMsg(False, '同步接收目录已存在任务！')
        if self._check_is_system_path(get.path):
            error_msg = '不能同步系统关键目录！同步系统关键目录可能会导致系统崩溃、产生安全隐患（系统关键信息泄漏）' \
                        '<br/>不能同步的系统关键目录有：<br/>["/usr/", "/var/", "/proc/", "/boot/", "/etc/", ' \
                        '"/dev/", "/root/", "/run/", "/sys/", "/tmp/", "/", "/www/", "/www/server/", "/home/"]'
            return public.returnMsg(False, error_msg)
        if self._check_module_name_exists(get.mName):
            return public.returnMsg(False, '您输入的用户名已存在')
        if "open_port" in get:
            open_port = getattr(get, "open_port", None) in ["1", "open"]
        else:
            open_port = False
        auth_pass = '{}/secrets/{}.db'.format(cfg.rsync_plugin_path, get.mName)
        module = {
            'name': get.mName,
            'recv_status': True,
            'path': get.path,
            'password': get.password,
            'comment': get.comment,
            'read only': 'false',
            'ignore errors': True,
            'auth users': get.mName,
            'secrets file': auth_pass,
            'addtime': int(time.time())
        }
        cfg.config['modules'].insert(0, module)
        cfg.save_conf(is_rsyncd=True)
        self._write_logs('添加rsync接收帐户[' + get.mName + ']')
        if open_port and firewall_tool.can_use_firewall():
            rsync_port = cfg.config["global"]["prot"]
            if firewall_tool.get_port_status(rsync_port) is False:
                firewall_tool.set_port(rsync_port)
                return public.returnMsg(True, '添加成功! <br> 已执行防火墙放行操作，请注意!')

        return public.returnMsg(True, '添加成功!')

    def modify_module(self, get):
        if self._check_is_system_path(get.path):
            error_msg = '不能同步系统关键目录！同步系统关键目录可能会导致系统崩溃、产生安全隐患（系统关键信息泄漏）' \
                        '<br/>不能同步的系统关键目录有：<br/>["/usr/", "/var/", "/proc/", "/boot/", "/etc/", ' \
                        '"/dev/", "/root/", "/run/", "/sys/", "/tmp/", "/", "/www/", "/www/server/", "/home/"]'
            return public.returnMsg(False, error_msg)
        cfg.conf_reload()
        data = cfg.config
        for i in range(len(data['modules'])):
            if data['modules'][i]['name'] == get.mName:
                data['modules'][i]['password'] = get.password
                exists_name = self._check_module_path(get.path)
                if exists_name != get.mName:
                    return public.returnMsg(False, '同步接收目录已存在任务！')
                data['modules'][i]['path'] = get.path
                data['modules'][i]['comment'] = get.comment
                cfg.save_conf(is_rsyncd=True)
                self._write_logs('修改rsync接收帐户[' + get.mName + ']')
                return public.returnMsg(True, '编辑成功!')
        return public.returnMsg(False, '指定模块不存在!')

    def start_stop_module(self, get):
        """开启和关闭 接收的 module"""
        get.exec_action = getattr(get, 'exec_action', 'start')
        if get.exec_action == 'start':
            set_status = True
        else:
            set_status = False
        module_name = getattr(get, 'module_name', None)
        if module_name is None:
            return public.returnMsg(False, '参数module_name丢失')
        else:
            module_name = module_name.strip()
        cfg.conf_reload()
        for mod in cfg.config["modules"]:
            if mod["name"] != module_name:
                continue
            mod["recv_status"] = set_status
            break
        else:
            return public.returnMsg(False, '没有指定名称的接收任务')

        cfg.save_conf(is_rsyncd=True)

        self._write_logs("修改接收任务:{}的状态为：{}".format(module_name, "接收" if set_status else "拒收"))
        if get.exec_action == 'start':
            return public.returnMsg(True, '开启任务成功！')
        else:
            return public.returnMsg(True, '暂停任务成功！')

    def remove_module(self, get):
        """
        删除指定名称的接收任务
        @param get:
        @return:
        """
        cfg.conf_reload()
        data = cfg.config
        for i in range(len(data['modules'])):
            if data['modules'][i]['name'] == get.mName:
                del (data['modules'][i])
                cfg.save_conf(is_rsyncd=True)
                auth_pass = cfg.rsync_plugin_path + '/secrets/' + get.mName + '.db'
                if os.path.exists(auth_pass):
                    os.remove(auth_pass)
                self._write_logs('删除rsync接收帐户[' + get.mName + ']')
                return public.returnMsg(True, '删除成功!')
        return public.returnMsg(False, '指定模块不存在!')

    @staticmethod
    def get_module(get, name=None):
        """
        获取rsync指定接收任务的配置信息
        """
        name = getattr(get, "mName", name)
        if name is None:
            return public.returnMsg(False, '指定模块不存在!')
        cfg.conf_reload()
        config = cfg.config
        for mod in config['modules']:
            if mod['name'] == name:
                mod['port'] = config['global']['port']
                return mod
        return public.returnMsg(False, '指定模块不存在!')

    def _write_logs(self, log):
        public.WriteLog(self._log_name, log)

    def rsync_service(self, get):
        """
        rsync服务管理
        @param get: dict_obj < get.state: start|stop >
        @return:
        """
        cfg.conf_reload()
        if get.state == 'start' and not cfg.config['modules']:
            return public.returnMsg(False, '至少需要添加1个接收任务才能开启接收服务!')
        s_cmd = "/etc/init.d/rsynd " + get.state
        public.ExecShell(s_cmd)
        # self._check_port_appect(get)
        self._write_logs(s_cmd + '已执行')
        return public.returnMsg(True, '操作成功!')

    @staticmethod
    def check_dir_status(get):
        """
        检查目录是否为空，如果不为空则检查是否为mysql数据目录，如果不是则返回该目录的目录结构
        @parm get.path 传入接收路径
        return result(dict_obj)
        """
        result = {'dirs': '', 'files': '', 'isMysqlData': 0, 'isEmpty': 0}
        if not get.path:
            return public.returnMsg(False, "参数错误")
        if not os.path.exists(get.path):
            os.makedirs(get.path)
        if len(os.listdir(get.path)) == 0:
            result['isEmpty'] = 1
            return result
        try:
            my_file = '/etc/my.cnf'
            my_conf = public.readFile(my_file)
            dataDir = re.search(r"datadir\s*=\s*(.+)\n", my_conf).groups()[0]
        except:
            dataDir = '/www/server/data'
        if dataDir[-1] != "/":
            dataDir = dataDir + "/"
        if get.path[-1] != "/":
            get.path = get.path + "/"
        if get.path == dataDir:
            result['isMysqlData'] = 1
            return result
        if os.path.isdir(get.path):
            dirNames = []
            filesNames = []
            for filename in os.listdir(get.path):
                try:
                    json.dumps(filename)
                    if sys.version_info[0] == 2:
                        filename = filename.encode('utf-8')
                    else:
                        filename.encode('utf-8')
                    filePath = get.path + '/' + filename
                    if os.path.islink(filePath):
                        continue
                    if os.path.isdir(filePath):
                        dirNames.append(filename)
                    if os.path.isfile(filePath):
                        filesNames.append(filename)
                except:
                    pass
            result['dirs'] = dirNames
            result['files'] = filesNames
        return result

    @staticmethod
    def check_receiver_conn(get: public.dict_obj = None):
        receiver_data = getattr(get, "sender_data", None)
        if receiver_data is None:
            return public.returnMsg(False, "参数错误")
        if isinstance(receiver_data, str):
            try:
                receiver_data: dict = json.loads(receiver_data)
            except json.JSONDecodeError:
                return public.returnMsg(False, "参数错误")
        if not isinstance(receiver_data, dict):
            return public.returnMsg(False, "参数错误")
        receiver = Receiver(receiver_data)
        flag, msg = receiver.check_data(not_verify_conn=False)
        if not flag:
            return public.returnMsg(False, msg)
        return msg

    def add_send_task(self, get):
        data = json.loads(get.data)
        check_connection = data.get("check_connection", True)
        later = data.get("later", False)
        sender_data = data.get("sender_data", None)
        if sender_data is None and not isinstance(sender_data, dict):
            return public.returnMsg(False, "参数错误")
        receivers_data = sender_data.get("target_list", None)
        if sender_data is None or receivers_data is None:
            return public.returnMsg(False, "参数错误")
        if "id" in sender_data and sender_data["id"] is not None:
            return public.returnMsg(False, "新建id应该为空")

        sender = Sender(sender_data)
        flag, msg = sender.check_data()
        if not flag:
            return public.returnMsg(False, msg)
        receivers = []
        for r in receivers_data:
            receiver = Receiver(r)
            flag, msg = receiver.check_data(not_verify_conn=not check_connection)
            if not flag:
                return public.returnMsg(False, msg)
            receivers.append(receiver)
        if len(receivers) == 0:
            return public.returnMsg(False, "没有接收方配置信息")

        sender.add_receivers(receivers)
        if sender.check_repeat_recv_name():
            return public.returnMsg(False, "接收方设置中存在重复名称")
        sender.set_id()
        # 组合初次同步指令
        cmd_strs = sender.get_send_cmd(first_send=True)
        if not cmd_strs:
            return public.returnMsg(False, "没有接收方数据")

        def run_command(command):
            # 执行指令并返回结果
            result = public.ExecShell(command)
            return result[0], result[1]

        if not later:
            with ThreadPoolExecutor(max_workers=len(cmd_strs)) as executor:
                futures = [executor.submit(run_command, command) for command in cmd_strs]
                results = [future.result() for future in futures]

        cfg.conf_reload()
        sender.save_data_to_config(later=later)
        cfg.save_conf(is_bt_sync=True)
        self._write_logs("添加发送任务:{}".format(sender.get_title()))
        return public.returnMsg(True, '添加成功! 同步指令执行中...')

    def modify_send_task(self, get):
        data = json.loads(get.data)
        check_connection = data.get("check_connection", True)
        sender_data = data.get("sender_data", None)
        if sender_data is None and not isinstance(sender_data, dict):
            return public.returnMsg(False, "参数错误")
        receivers_data = sender_data.get("target_list", None)
        if sender_data is None or receivers_data is None:
            return public.returnMsg(False, "参数错误")

        if "id" not in sender_data:
            return public.returnMsg(False, '参数错误')
        cfg.conf_reload()
        send_conf = cfg.get_sender_by_id(sender_data["id"])
        if send_conf is None:
            return public.returnMsg(False, '没有指定的发送配置')
        if len(receivers_data) == 0:
            return public.returnMsg(False, "接收方配置信息不能为空")

        sender = Sender(send_conf)
        sender.add_receivers([Receiver(r) for r in send_conf["target_list"]])

        # 检查发送方信息
        check_sender_msg = sender.modify_data(sender_data)
        if isinstance(check_sender_msg, dict):
            return check_sender_msg

        # 检查接收方信息
        check_receiver_msg = sender.modify_receivers(receivers_data, not check_connection)
        if isinstance(check_receiver_msg, dict):
            return check_receiver_msg

        if sender.check_repeat_recv_name():
            return public.returnMsg(False, "接收方设置中存在重复名称")

        if not sender.has_receivers():
            return public.returnMsg(False, "没有接收方配置信息")

        # 如果修改了发送路径，则都需要重新发送
        init_list = check_receiver_msg if not check_sender_msg else None
        cmd_strs = sender.get_send_cmd(receiver_names=init_list, first_send=True)

        def run_command(command):
            # 执行指令并返回结果
            result = public.ExecShell(command)
            return result[0], result[1]

        if cmd_strs:
            with ThreadPoolExecutor(max_workers=len(cmd_strs)) as executor:
                futures = [executor.submit(run_command, command) for command in cmd_strs]
                results = [future.result() for future in futures]

        sender.save_data_to_config()
        cfg.save_conf(is_bt_sync=True)
        self._write_logs("修改发送任务:{}的配置文件".format(send_conf["title"]))
        return public.returnMsg(True, '修改成功!' + ("同步指令执行中..." if cmd_strs else ""))

    def run_later_task(self, get):
        """执行延时任务"""
        if "send_id" in get:
            send_id = getattr(get, "send_id")
        else:
            return public.returnMsg(False, '参数错误')

        cfg.conf_reload()
        send_conf = cfg.get_sender_by_id(send_id)
        if send_conf is None:
            return public.returnMsg(False, '没有指定的发送配置')
        if not (send_conf.get("later", False) is True):  # 含有later项，且later是True
            return public.returnMsg(False, "该任务已执行，无法进行操作")

        sender = Sender(send_conf)
        sender.add_receivers([Receiver(r) for r in send_conf["target_list"]])
        sender.close_later()

        # 对所有子任务执行初次同步
        self._exec_cmd(sender, receiver_names=None, first_send=True)

        sender.save_data_to_config()
        cfg.save_conf(is_bt_sync=True)

        return public.returnMsg(True, "初次同步执行中...")

    def remove_send_task(self, get):
        if "send_id" not in get:
            return public.returnMsg(False, '参数错误')
        cfg.conf_reload()
        config = cfg.config
        for i in range(len(config["senders"]) - 1, -1, -1):
            if config["senders"][i]["id"] == int(get["send_id"]):
                send_data = config["senders"][i]
                for r in send_data["target_list"]:
                    pass_file = r["password_file"]
                    if os.path.exists(pass_file):
                        os.remove(pass_file)

                    status_file = cfg.bt_sync_status_path + "/" + r["name"]
                    if os.path.exists(status_file):
                        os.remove(status_file)

                    log_file = "{}/{}_log.log".format(cfg.bt_sync_log_path, r["name"])
                    if os.path.exists(log_file):
                        os.remove(log_file)

                    exec_log_file = "{}/sclient/{}_exec.log".format(cfg.rsync_plugin_path, r["name"])
                    if os.path.exists(exec_log_file):
                        os.remove(exec_log_file)

                self._write_logs("发送任务:{}已删除".format(send_data["title"]))
                del config["senders"][i]
                break
        cfg.save_conf(is_bt_sync=True)
        return public.returnMsg(True, '删除成功')

    def remove_recv_task(self, get):
        if "send_id" not in get:
            return public.returnMsg(False, '参数错误')
        if "receiver_name" not in get:
            return public.returnMsg(False, '参数错误')
        else:
            receiver_name = get.receiver_name

        cfg.conf_reload()
        sender_data = cfg.get_sender_by_id(int(get["send_id"]))
        if sender_data is None:
            return public.returnMsg(False, '没有指定的任务')

        if len(sender_data["target_list"]) == 1:
            return public.returnMsg(False, '不能单独删除所有的接收端配置')

        for i in range(len(sender_data["target_list"]) - 1, -1, -1):
            name = sender_data["target_list"][i]["name"]
            if name != receiver_name:
                continue
            pass_file = sender_data["target_list"][i]["password_file"]
            if os.path.exists(pass_file):
                os.remove(pass_file)

            status_file = cfg.bt_sync_status_path + "/" + name
            if os.path.exists(status_file):
                os.remove(status_file)

            log_file = "{}/{}_log.log".format(cfg.bt_sync_log_path, name)
            if os.path.exists(log_file):
                os.remove(log_file)

            exec_log_file = "{}/sclient/{}_exec.log".format(cfg.rsync_plugin_path, name)
            if os.path.exists(exec_log_file):
                os.remove(exec_log_file)

            self._write_logs("接收端配置:{}已删除".format(name))
            del sender_data["target_list"][i]

        cfg.save_conf(is_bt_sync=True)
        return public.returnMsg(True, '删除成功')

    def start_stop_task(self, get):
        """
        开启暂停同步任务
        """
        get.exec_action = getattr(get, 'exec_action', 'start')
        if get.exec_action == 'start':
            set_status = True
        else:
            set_status = False
        send_id = getattr(get, 'send_id', None)
        if send_id is None:
            return public.returnMsg(False, "参数错误，没有指定任务id")
        else:
            send_id = int(send_id)

        receiver_name = getattr(get, 'receiver_name', "")
        if receiver_name == "" or receiver_name == "all":
            receiver_name = None

        cfg.conf_reload()
        sender_data = cfg.get_sender_by_id(send_id)
        if sender_data is None:
            return public.returnMsg(False, "参数错误，没有指定的任务")

        if set_status is True or (set_status is False and receiver_name is None):
            sender_data["status"] = set_status

        for recv_data in sender_data["target_list"]:
            if receiver_name is not None and recv_data["name"] == receiver_name:
                recv_data["status"] = set_status
                continue
            if receiver_name is None:
                recv_data["status"] = set_status

        cfg.save_conf(is_bt_sync=True)
        self._write_logs("修改任务:{}下的{}的状态".format(
            sender_data["title"], "所有任务" if receiver_name is None else "接收任务：" + receiver_name))
        if get.exec_action == 'start':
            return public.returnMsg(True, '开启同步任务成功！')
        else:
            return public.returnMsg(True, '暂停同步任务成功！')

    def _exec_cmd(self, sender: Sender, receiver_names: Optional[List[str]], first_send: bool):
        cmd_strs = sender.get_send_cmd(receiver_names=receiver_names, first_send=first_send)
        if not cmd_strs:
            return public.returnMsg(False, "没有查询到接收方信息")

        def run_command(command):
            # 执行指令并返回结果
            result = public.ExecShell(command)
            return result[0], result[1]

        with ThreadPoolExecutor(max_workers=len(cmd_strs)) as executor:
            futures = [executor.submit(run_command, command) for command in cmd_strs]
            results = [future.result() for future in futures]

        if receiver_names is None:
            log_str = "手动执行任务:[{}]下的所有同步指令".format(sender.get_title())
        else:
            log_str = "手动执行任务:[{}]下的[{}]同步指令".format(sender.get_title(), receiver_names)

        self._write_logs(log_str)

    def exec_cmd(self, get):
        """
        执行的同步命令
        """
        send_id, receiver_names = None, None
        if "send_id" in get:
            send_id = int(get["send_id"])
        else:
            return public.returnMsg(False, "参数错误")
        if "receiver_name" in get and bool(get["receiver_name"]):
            receiver_names = [get["receiver_name"], ]
            if get["receiver_name"] == "all":
                receiver_names = None
        cfg.conf_reload()
        sender_config = cfg.get_sender_by_id(send_id)
        if not sender_config:
            return public.returnMsg(False, "没有该任务")
        sender = Sender(sender_config)
        sender.add_receivers([Receiver(r) for r in sender_config["target_list"]])

        self._exec_cmd(sender, receiver_names, first_send=False)

        return public.returnMsg(True, '同步指令已发送!')

    def get_send_conf(self, get=None):
        """
        获取所有的发送任务列表
        """
        cfg.conf_reload()
        data = cfg.config["senders"]
        for sender_conf in data:
            later_status = None
            if "later" in sender_conf and sender_conf["later"] is True:
                later_status = {
                    'status': True,
                    'later': True,
                    'running': False,
                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'err_msg': ''
                }
            for recv_conf in sender_conf["target_list"]:
                if recv_conf["work_type"] == 2:
                    recv_conf["secret_key"] = recv_conf["password"]
                if later_status is None:
                    recv_conf["last_status"] = self._get_recv_status(recv_conf["name"])
                else:
                    recv_conf["last_status"] = later_status

        return data

    def _get_recv_status(self, name: str) -> dict:
        default = {
            'status': True,
            'later': False,
            'running': False,
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'err_msg': ''
        }

        exec_status = self._get_recv_status_by_exec_log(name)
        by_sync_status = self._get_recv_status_by_bt_sync(name)

        if by_sync_status is None and exec_status is None:
            return default

        if by_sync_status is not None and exec_status is not None:
            run_time: datetime = datetime.strptime(by_sync_status["time"], "%Y-%m-%d %H:%M:%S")
            exec_time: datetime = datetime.strptime(exec_status["time"], "%Y-%m-%d %H:%M:%S")
            if exec_time > run_time:
                return exec_status
            else:
                return by_sync_status
        else:
            return exec_status or by_sync_status

    @staticmethod
    def _get_recv_status_by_bt_sync(name: str) -> Optional[dict]:
        try:
            status_path = cfg.bt_sync_status_path + "/" + name
            status_dict: dict = json.loads(public.readFile(status_path))
        except (json.JSONDecodeError, TypeError):
            return None
        else:
            return {
                'status': not bool(status_dict.get("error", "")),
                'running': status_dict.get("running", False),
                'time': status_dict["time"],
                'later': False,
                'err_msg': status_dict.get("error", "")
            }

    @staticmethod
    def _get_recv_status_by_exec_log(name: str) -> Optional[dict]:
        """从手动执行日志中确定"""
        exec_log_file = "{}/sclient/{}_exec.log".format(cfg.rsync_plugin_path, name)
        if not os.path.exists(exec_log_file):
            return None
        re_compile = re.compile(r"={9}>(?P<time>.*)<={9}")
        file_size = os.stat(exec_log_file).st_size - 1
        time_str = None
        with open(exec_log_file, mode="rb") as fp:
            fp.seek(-1, 2)
            _buf = b""
            last_msg = []
            while file_size and time_str is None:
                read_size = min(1024, file_size)
                fp.seek(-read_size, 1)
                buf: bytes = fp.read(read_size) + _buf
                if file_size > 1024:
                    idx = buf.find(ord("\n"))
                    _buf, buf = buf[:idx], buf[idx + 1:]
                read_str = buf.decode()
                for log_line in read_str.split("\n")[::-1]:
                    res = re_compile.search(log_line)  # 找到最后一次执行就放弃
                    if res:
                        time_str = res.group("time")
                        break
                    last_msg.append(log_line)  # 将最后一次执行的信息记录下来
                fp.seek(-read_size, 1)
                file_size -= read_size

        if time_str is None:
            return None
        err_list = ("rsync error:",  "err: @ERROR", "exitcode = 10", "rsync failed:")
        msg = "\n".join(last_msg[::-1])
        status = True
        for err in err_list:
            if err in msg:
                status = False
        return {
            'later': False,
            "status": status,
            "time": time_str,
            "running": msg.find("执行结束") == -1,
            "err_msg": msg
        }

    def get_send_byid(self, get):
        """
        获取指定的发送任务
        @param get: dict_obj < get.send_id >
        """
        try:
            send_id = int(get["send_id"])
        except (ValueError, TypeError):
            return public.returnMsg(False, "参数错误")
        cfg.conf_reload()
        data = cfg.get_sender_by_id(send_id)
        if data is None:
            return public.returnMsg(False, '指定任务不存在!')
        for conf in data["target_list"]:
            if conf["work_type"] == 1:
                conf["secret_key"] = conf["secret_key"] if conf["secret_key"] else \
                    self.make_secretkey(conf["name"], conf["password"], conf["port"], conf["target"], conf["ip"])
            elif conf["work_type"] == 2:
                conf["secret_key"] = conf["password"]
            conf["last_status"] = self._get_recv_status(conf["name"])

        return data

    def get_log(self, get: public.dict_obj):
        """获取指定的发送任务的日志"""
        log_type, send_id, receiver_name = "", None, None
        if "log_type" in get:
            log_type = get["log_type"]
        if "send_id" in get:
            send_id = int(get["send_id"])
        if "receiver_name" in get:
            receiver_name = get["receiver_name"]
            if not bool(receiver_name) or receiver_name == "all":
                receiver_name = None

        if log_type != "service" and send_id is None:
            return public.returnMsg(False, "参数错误")
        if log_type == "service":
            return self._get_bync_log()
        cfg.conf_reload()
        sender_config = cfg.get_sender_by_id(send_id)
        if not sender_config:
            return public.returnMsg(False, "没有该任务")
        res = []
        for recv in sender_config["target_list"]:
            if receiver_name is not None and receiver_name != recv["name"]:
                continue
            if log_type == "exec" or log_type == "all":
                exec_log_file = "{}/sclient/{}_exec.log".format(cfg.rsync_plugin_path, recv["name"])
                res.append({
                    "name": recv["name"],
                    "log_type": "exec",
                    "log": '' if not os.path.exists(exec_log_file) else public.GetNumLines(exec_log_file, 3000)
                })
            if log_type == "watch" or log_type == "all":
                run_log_file = "{}/{}_log.log".format(cfg.bt_sync_log_path, recv["name"])
                res.append({
                    "name": recv["name"],
                    "log_type": "watch",
                    "log": '' if not os.path.exists(run_log_file) else public.GetNumLines(run_log_file, 3000)
                })

        return res

    @staticmethod
    def _get_bync_log():
        log_file = cfg.bt_sync_path + "/run_logs.log"
        log_data = '' if not os.path.exists(log_file) else public.GetNumLines(log_file, 3000)
        return [{
            "name": "service",
            "log_type": "service",
            "log": log_data
        }]

    def remove_log(self, get):
        """删除指定日志"""
        log_type, send_id, receiver_name = "", None, None
        if "log_type" in get:
            log_type = get["log_type"]
        if "send_id" in get:
            send_id = int(get["send_id"])
        if "receiver_name" in get:
            receiver_name = get["receiver_name"]
            if not bool(receiver_name) or receiver_name == "all":
                receiver_name = None

        if log_type != "service" and send_id is None:
            return public.returnMsg(False, "参数错误")
        if log_type == "service":
            return self._remove_bync_log()
        cfg.conf_reload()
        sender_config = cfg.get_sender_by_id(send_id)
        if not sender_config:
            return public.returnMsg(False, "没有该任务")
        for recv in sender_config["target_list"]:
            if receiver_name is not None and receiver_name != recv["name"]:
                continue
            if log_type == "exec":
                log_file = "{}/sclient/{}_exec.log".format(cfg.rsync_plugin_path, recv["name"])
            else:
                log_file = "{}/{}_log.log".format(cfg.bt_sync_log_path, recv["name"])

            if os.path.exists(log_file):
                os.remove(log_file)

        return public.returnMsg(True, "清除成功")

    @staticmethod
    def _remove_bync_log():
        log_file = cfg.bt_sync_path + "/run_logs.log"
        if os.path.exists(log_file):
            public.writeFile(log_file, "")
        return public.returnMsg(True, "清除成功")

    # -------------------------#
    # -------过滤器设置----------#
    # -------------------------#
    def add_exclude(self, get):
        """
        添加指定排除规则
        """
        cfg.conf_reload()
        send_id, exclude = None, None
        if "send_id" in get:
            send_id = int(get["send_id"])
        if "exclude" in get:
            exclude = get["exclude"].strip()
        sender_config = cfg.get_sender_by_id(send_id)
        if not sender_config:
            return public.returnMsg(False, "没有该任务")
        if not exclude:
            return public.returnMsg(False, "不能设置空格为排除方式")
        if exclude not in sender_config["exclude"]:
            sender_config["exclude"].insert(0, exclude)
        else:
            return public.returnMsg(True, '已存在!')
        cfg.save_conf(is_bt_sync=True)
        self._write_logs('添加排除规则[' + exclude + ']到[' + sender_config["title"] + ']')
        return public.returnMsg(True, '添加成功!')

    def remove_exclude(self, get):
        """
        删除指定排除规则
        """
        cfg.conf_reload()
        send_id, exclude = None, None
        if "send_id" in get:
            send_id = int(get["send_id"])
        if "exclude" in get:
            exclude = get["exclude"].strip()
        sender_config = cfg.get_sender_by_id(send_id)
        if not sender_config:
            return public.returnMsg(False, "没有该任务")
        if not exclude:
            return public.returnMsg(False, "没有指定排除规则")
        if exclude in sender_config["exclude"]:
            sender_config["exclude"].remove(exclude)
        else:
            return public.returnMsg(True, '不存在该排除规则!')
        cfg.save_conf(is_bt_sync=True)
        self._write_logs('从[' + sender_config["title"] + ']删除排除规则[' + exclude + ']')
        return public.returnMsg(True, '删除成功!')

    def get_filters(self, get: public.dict_obj = None):
        default = {"默认模板": ['/**.upload.tmp', '**/*.log', '**/*.tmp', '**/*.temp']}
        try:
            filters = json.loads(public.readFile(self.filter_template_path))
        except (json.JSONDecodeError, TypeError):
            filters = {}
        filters.update(default)
        if not isinstance(get, public.dict_obj):
            return filters
        return [{
            "name": k,
            "template": v
        } for k, v in filters.items()]

    # 也可以用于设置
    def add_filter_template(self, get: public.dict_obj):
        try:
            excludes = json.loads(get.excludes)
            template_name = get.template.strip()
        except (json.JSONDecodeError, AttributeError, TypeError):
            return public.returnMsg(False, '请求信息错误！')
        filters = self.get_filters()
        # if template_name in filters:
        #     return public.returnMsg(False, '名称为{}的模板已经存在！'.format(template_name))
        filters[template_name] = excludes
        public.writeFile(self.filter_template_path, json.dumps(filters))

        return public.returnMsg(True, '保存成功')

    def remove_filter_template(self, get: public.dict_obj):
        filters = self.get_filters()
        if "template" not in get:
            return public.returnMsg(False, '请求信息错误！')
        template_name = get.template.strip()
        if template_name not in filters:
            return public.returnMsg(False, '名称为{}的模板不存在！'.format(template_name))
        del filters[template_name]

        public.writeFile(self.filter_template_path, json.dumps(filters))
        return public.returnMsg(True, '删除成功')

    def export_filters(self, get: public.dict_obj):
        filters_str = public.readFile(self.filter_template_path)
        if filters_str is False:
            public.returnMsg(False, '没有除【默认模板】之外的模板信息')

        data = base64.b64encode(filters_str.encode('utf-8')).decode('utf-8')
        return public.returnMsg(True, data)

    def recover_filters(self, get: public.dict_obj):
        if "template_data" not in get:
            return public.returnMsg(False, '请求信息错误！')
        template_data = get.template_data.strip()
        try:
            data_str = base64.b64decode(template_data.encode('utf-8')).decode('utf-8')
            data = json.loads(data_str)
            if not isinstance(data, dict):
                return public.returnMsg(False, '导入信息错误！')
        except Exception:
            return public.returnMsg(False, '导入信息错误！')
        filters = self.get_filters()
        for k, v in data.items():
            if not isinstance(v, list):
                continue
            if k in filters:
                k += "（导入:{}）".format(str(date.today()))
            filters[k] = v

        public.writeFile(self.filter_template_path, json.dumps(filters))
        return public.returnMsg(True, "导入成功")

    def get_logs(self, get):
        """获取操作日志"""
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (self._log_name,)).count()
        limit = 10
        info = {
            'count': count,
            'row': limit,
            'p': 1
        }
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        page_info = page.GetPage(info, '1,2,3,4,5,8'),
        limit_str = "{},{}".format(str(page.SHIFT), str(page.ROW))
        sql = public.M('logs')
        data = {
            'page': page_info,
            'data': sql.where('type=?', (self._log_name,)).order('id desc').limit(limit_str).field(
                'log,addtime').select()
        }

        return data

    # 从更久的版本中继承过来的
    @staticmethod
    def to_new_version(get=None):
        if not os.path.exists(cfg.rsync_plugin_path + '/secrets'):
            os.mkdir(cfg.rsync_plugin_path + '/secrets')

        if not os.path.exists(cfg.rsync_file):
            os.mknod(cfg.rsync_file)
            data_conf = '''uid = root
gid = root
use chroot = yes
port = 873
hosts allow =
log file = /var/log/rsyncd.log
pid file = /var/run/rsyncd.pid
            '''
            public.ExecShell('echo "%s" > %s' % (data_conf, cfg.rsync_file))
        rsync_conf = {}
        with open(cfg.rsync_file, "r") as conf:
            section = 'is_global'
            rsync_conf[section] = {}
            for row in conf:
                if not re.match(r"^\s*?#", row) and row != "\n":
                    is_section = re.findall(r"\[(.*?)\]", row)
                    if is_section:
                        section = is_section[0]
                        rsync_conf[section] = {}
                    else:
                        try:
                            info = row.split('=')
                            key = info[0].strip()
                            value = info[1].strip()
                            if section == 'is_global' and key in ["log file", "pid file", "uid", "gid", "use chroot"]:
                                continue
                            if key == "secrets file":
                                passwd = re.findall(
                                    r":(\w+)", public.readFile(value))[0]
                                rsync_conf[section]["passwd"] = passwd
                                continue
                            if key == "auth users":
                                key = "user"
                                continue
                            if key == "hosts allow":
                                key = "ip"
                                value = value.replace(",", "\n")
                            if key == "dont commpress":
                                key = "dont_commpress"
                                value = value.replace(' *.', ',')[2:]
                            key = key.replace(" ", "_")
                            rsync_conf[section][key] = value
                        except:
                            pass

            if not 'port' in rsync_conf['is_global'].keys():
                rsync_conf['is_global']['port'] = 873
            if not 'ip' in rsync_conf['is_global'].keys():
                rsync_conf['is_global']['ip'] = ''

            data = cfg.get_old_config()
            data['global']['port'] = rsync_conf['is_global']['port']
            del (rsync_conf['is_global'])
            for k in rsync_conf.keys():
                auth_pass = cfg.rsync_plugin_path + '/secrets/' + k + '.db'
                com = True
                for m in data['modules']:
                    if m['name'] == k:
                        com = False
                        break
                if not com: continue
                module = {
                    'name': k,
                    'path': rsync_conf[k]['path'],
                    'password': rsync_conf[k]['passwd'],
                    'comment': rsync_conf[k]['comment'],
                    'read only': 'false',
                    'ignore errors': True,
                    'auth users': k,
                    'secrets file': auth_pass,
                    'addtime': time.time()
                }
                data['modules'].insert(0, module)

            serverDict = public.readFile(cfg.rsync_plugin_path + '/serverdict.json')
            if serverDict:
                serverDict = json.loads(serverDict)
                for k in serverDict.keys():
                    del (serverDict[k]['cron_info']['id'])
                    tmp = k.split('_')
                    sclient = {
                        'model': 'default.rsync',
                        'name': k,
                        'ip': tmp[0],
                        'password': public.readFile(cfg.rsync_plugin_path + '/sclient/' + k + '.db'),
                        'path': serverDict[k]['path'],
                        'to': '',
                        'exclude': [],
                        'delete': 'false',
                        'realtime': serverDict[k]['inotify_info'],
                        'delay': 3,
                        'rsync': {
                            'bwlimit': '200',
                            'port': str(serverDict[k]['port']),
                            'compress': 'true',
                            'archive': 'true',
                            'verbose': 'true'
                        },
                        'ps': '',
                        'cron': serverDict[k]['cron_info'],
                        'addtime': time.time()
                    }
                    data['client'].insert(0, sclient)
                os.remove(cfg.rsync_plugin_path + '/serverdict.json')
            public.writeFile(cfg.rsync_plugin_path + '/config.json', json.dumps(data))

    @staticmethod
    def _create_bt_sync_cron():
        if public.M('crontab').where('name=?', '[勿删]宝塔文件同步工具进程守护').find():
            return

        import crontab
        crontabs = crontab.crontab()

        old_task = public.M('crontab').where('name=?', '[勿删]文件同步工具进程守护任务').find()
        if old_task and isinstance(old_task, dict):
            res = crontabs.DelCrontab({"id": old_task["id"]})

        s_body = '{}/pyenv/bin/python3.7 {}/rsync_cron.py'.format(public.get_panel_path(), cfg.rsync_plugin_path)
        args = {
            "name": "[勿删]宝塔文件同步工具进程守护",
            "type": 'minute-n',
            "where1": '3',
            "hour": '',
            "minute": '',
            "sName": 'toShell',
            "sType": 'toShell',
            "notice": '',
            "notice_channel": '',
            "save": '',
            "save_local": '1',
            "backupTo": '',
            "sBody": s_body,
            "urladdress": ''
        }
        res = crontabs.AddCrontab(args)
        if res and "id" in res.keys():
            return True
        return False

    @staticmethod
    def cron_test_bt_sync_running(null=None):
        if not cfg.bt_sync_running():
            cfg.save_conf(is_bt_sync=True)
            print("重启文件同步工具")
        else:
            print("运行中，无需重启")
        log_file = cfg.bt_sync_path + "/run_logs.log"
        if os.path.exists(log_file) and os.path.getsize(log_file) > 1024 * 1024 * 50:
            public.writeFile(log_file, public.GetNumLines(log_file, 2000))

    def add_ormodify_send(self, get):
        """
        创建发送任务
        兼容文件系统
        """
        request_data: Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool, dict]]]]] = {
            "source": getattr(get, "path", "None"),
            "binary": "/usr/bin/rsync",
            "delay": int(getattr(get, "delay", 3)),
            "exclude": [
                "/**.upload.tmp",
                "**/*.log",
                "**/*.tmp",
                "**/*.temp"
            ],
            "bwlimit": int(getattr(get, "bwlimit", 1024)),
            "delete": getattr(get, "delete", "false") == "true",
            "archive": True,
            "compress": getattr(get, "compress", "false") == "true",
            "id": None,
            "title": "",
            "verbose": True,
            "realtime": getattr(get, "realtime", "true") == "true",
            "target_list": [
                {
                    "secret_key": getattr(get, "secret_key", ""),
                    "work_type": 1,
                    "target": "",
                    "name": getattr(get, "sname", "false"),
                    "password_file": "/www/server/panel/plugin/rsync/sclient/aaa_pass",
                    "ip": getattr(get, "ip", ""),
                    "port": int(getattr(get, "port", 873)),
                    "id": None,
                    "title": "",
                    "bwlimit": int(getattr(get, "bwlimit", 1024)),
                    "delete": getattr(get, "delete", "false") == "true",
                    "archive": True,
                    "compress": getattr(get, "compress", "false") == "true",
                    "verbose": True,
                    "password": getattr(get, "password", ""),
                    "realtime": getattr(get, "realtime", "true") == "true",
                    "cron": {
                        "type": "minute-n",
                        "where1": "5",
                        "hour": "",
                        "minute": "",
                        "seconds": ""
                    }
                }
            ]
        }
        if "cron" in get:
            input_cron = get["cron"]
            if isinstance(input_cron, str):
                input_cron = json.loads(input_cron)
            if isinstance(input_cron, dict):
                target_cron = request_data["target_list"][0]["cron"]
                target_cron["type"] = input_cron.get("type", "minute-n")
                target_cron["where1"] = input_cron.get("where1", "5")
                target_cron["hour"] = input_cron.get("hour", "")
                target_cron["minute"] = input_cron.get("minute", "")
                target_cron["seconds"] = input_cron.get("seconds", "")

        request_json = json.dumps({"sender_data": request_data, "check_connection": False})
        get_obj = public.dict_obj()
        get_obj.data = request_json
        return self.add_send_task(get_obj)


class FirewallTool(object):
    # 优先使用新版模块内的添加方法
    _MODULES = (
        ('.safeModel.firewallModel', 'main'),
        # ('.firewall_new', 'firewalls'),  # 这个模块中有bug，不使用
        ('.firewalls', 'firewalls'),
    )

    def __init__(self):
        self._firewall_main = None
        self._idx = -1
        for mod, mod_name in self._MODULES:
            self._idx += 1
            try:
                mod = import_module(mod, package="class")
                self._firewall_main = getattr(mod, mod_name)()
            except Exception:
                pass
            else:
                break

    def can_use_firewall(self):
        return self._firewall_main is not None

    def get_port_status(self, port) -> bool:
        if self._idx == 0:
            return self._get_port_status_by_model(port)
        else:
            return self._get_port_status_by_firewalls(port)

    def _get_port_status_by_model(self, port) -> bool:
        get_obj = public.dict_obj()
        get_obj.p = 1
        get_obj.limit = 99
        get_obj.query = str(port)
        res_data = self._firewall_main.get_rules_list(get_obj)
        if len(res_data) == 0:
            return False
        for rule in res_data:
            if rule.get("ports", "") != str(port):
                return False
            if rule.get("types", "") != "accept":
                return False

        return True

    def _get_port_status_by_firewalls(self, port) -> bool:
        return self._firewall_main.CheckDbExists(str(port)) is not False

    def set_port(self, port):
        if self._idx == 0:
            return self._set_port_status_by_model(port)
        else:
            return self._set_port_status_by_firewalls(port)

    def _set_port_status_by_model(self, port):
        get_obj = public.dict_obj()
        get_obj.ports = str(port)
        get_obj.choose = "all"
        get_obj.address = ""
        get_obj.domain = ""
        get_obj.types = "accept"
        get_obj.brief = "文件同步rsync服务端口"
        get_obj.source = ""
        self._firewall_main.create_rules(get_obj)

    def _set_port_status_by_firewalls(self, port):
        get_obj = public.dict_obj()
        get_obj.port = str(port)
        get_obj.ps = "文件同步rsync服务端口"
        self._firewall_main.AddAcceptPort(get_obj)


firewall_tool = FirewallTool()


if __name__ == "__main__":
    cfg.save_conf(is_bt_sync=True)
