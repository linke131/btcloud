# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 王佳函
# +-------------------------------------------------------------------
# --------------------------------
# Mysql主从复制
# --------------------------------

import os, sys
sys.path.append("class/")
os.chdir("/www/server/panel")

import copy
import datetime
from typing import Tuple, Union

import hashlib, time, json, re
import public
import db_mysql
import panelMysql
import panelTask

my_cnf = '/etc/my.cnf'
plugin_dir = os.path.join(public.get_panel_path(), "plugin/mysql_replicate")
plugin_conf_file = os.path.join(plugin_dir, "config.json")

# 从库执行调用
execute_slave = os.path.join(plugin_dir, "execute_slave.py")
logs_dir = "/tmp"
logs_file = "/tmp/mysql_replicate.log"
#
# CHANGE MASTER TO
# MASTER_HOST='192.168.69.148',
# MASTER_USER='y50dvIyP',
# MASTER_PASSWORD='vZp24QXwYN5R',
# MASTER_AUTO_POSITION=1;

# change master to
# master_host='192.168.69.148',
# master_user='y50dvIyP',
# master_password='vZp24QXwYN5R',
# master_log_file='binlog.000001',
# master_log_pos=156;

# SELECT @@GLOBAL.GTID_PURGED;
# SET @@GLOBAL.GTID_PURGED='GTID值';
# SELECT @@GLOBAL.GTID_EXECUTED;
# SET @@SESSION.GTID_NEXT = 'GTID值';

# 主从复制添加流程

# add_replicate_info: 填写信息,点击添加

# status
# test_connect: 测试连接面板及数据库
# check_slave_versions: 检查主从版本信息
# check_slave_database: 检查主从库数据库一致性
# export_dump_database: 导出数据库
# upload_database_file: 上传数据库文件
# import_dump_database: 导入数据库文件
# check_master_conf: 检查并设置主库配置信息
# check_slave_conf: 检查并设置从库配置信息
# create_replicate_user: 检查并创建主从同步用户
# check_firewall_set: 检查并设置防火墙放行端口

# start_replicate: 开启主从复制

# 生成随机密码
def new_password() -> str:
    """
    帮助方法生成随机密码
    """
    import random
    import string
    # 生成随机密码
    password = "".join(random.sample(string.ascii_letters + string.digits, 16))
    return password

def get_size_ext(size: int) -> Tuple[Union[int, float], str]:
    ext_list = ('b', 'KB', 'MB', 'GB', 'TB')
    for ext in ext_list:
        if size < 1024:
            return f"{size}{ext}"
        size = round(size / 1024, 2)
    return f"{size}{ext_list[-1]}"
# 主体
class mysql_replicate_main():
    # 主从复制流程
    conf_info = [
        {
            "msg": "【主从】版本信息检查",
            "api": "check_slave_versions",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【主从】检查从库是否存在同名数据库",
            "api": "check_slave_database",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【主库】数据库同步到从库",
            "api": "sync_database",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【主库】配置信息检查并配置",
            "api": "check_master_conf",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【主库】主从复制用户创建",
            "api": "create_replicate_user",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【从库】配置信息检查并配置",
            "api": "check_slave_conf",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【主库】防火墙放行",
            "api": "check_firewall_set",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "启动",
            "api": "start_replicate",
            "msg_list": [],
            "status": False,
        },
    ]

    # 从库配置信息
    slave_status_ps = {
        "Slave_IO_State": "Slave I/O 状态",
        "Master_Host": "主服务器主机",
        "Master_User": "主服务器用户",
        "Master_Port": "主服务器端口",
        "Connect_Retry": "连接重试时间",
        "Master_Log_File": "主服务器日志文件名",
        "Read_Master_Log_Pos": "读取主服务器日志文件位置",
        "Relay_Log_File": "中转日志文件名",
        "Relay_Log_Pos": "中转日志位置",
        "Relay_Master_Log_File": "中转日志正在读取的主服务器日志文件名",
        "Slave_IO_Running": "IO线程是否正在运行",
        "Slave_SQL_Running": "SQL线程是否正在运行",
        "Replicate_Do_DB": "需要复制的数据库",
        "Replicate_Ignore_DB": "需要忽略复制的数据库",
        "Replicate_Do_Table": "需要复制的表",
        "Replicate_Ignore_Table": "需要忽略复制的表",
        "Replicate_Wild_Do_Table": "需要复制的通配符表",
        "Replicate_Wild_Ignore_Table": "需要忽略复制的通配符表",
        "Last_Errno": "最后一个错误号",
        "Last_Error": "最后一个错误信息",
        "Skip_Counter": "跳过事件数量",
        "Exec_Master_Log_Pos": "执行主服务器日志文件位置",
        "Relay_Log_Space": "中转日志空间大小",
        "Until_Condition": "复制停止条件",
        "Until_Log_File": "复制停止日志文件名",
        "Until_Log_Pos": "复制停止日志位置",
        "Master_SSL_Allowed": "是否允许使用SSL",
        "Master_SSL_CA_File": "SSL CA文件路径",
        "Master_SSL_CA_Path": "SSL CA路径",
        "Master_SSL_Cert": "SSL证书路径",
        "Master_SSL_Cipher": "SSL加密算法",
        "Master_SSL_Key": "SSL密钥路径",
        "Seconds_Behind_Master": "主从延迟时间",
        "Master_SSL_Verify_Server_Cert": "是否验证SSL服务器证书",
        "Last_IO_Errno": "最后一个IO错误号",
        "Last_IO_Error": "最后一个IO错误信息",
        "Last_SQL_Errno": "最后一个SQL错误号",
        "Last_SQL_Error": "最后一个SQL错误信息",
        "Replicate_Ignore_Server_Ids": "需要忽略的主服务器ID",
        "Master_Server_Id": "主服务器ID",
        "Master_UUID": "主服务器UUID",
        "Master_Info_File": "主服务器信息文件路径",
        "SQL_Delay": "SQL延迟时间",
        "SQL_Remaining_Delay": "SQL剩余延迟时间",
        "Slave_SQL_Running_State": "SQL线程状态",
        "Master_Retry_Count": "主服务器重试次数",
        "Master_Bind": "主服务器IP地址",
        "Last_IO_Error_Timestamp": "最后一个IO错误时间戳",
        "Last_SQL_Error_Timestamp": "最后一个SQL错误时间戳",
        "Master_SSL_Crl": "SSL CRL路径",
        "Master_SSL_Crlpath": "SSL CRL路径",
        "Retrieved_Gtid_Set": "已检索的GTID集合",
        "Executed_Gtid_Set": "已执行的GTID集合",
        "Auto_Position": "是否开启自动定位",
        "Replicate_Rewrite_DB": "需要重写的数据库",
        "Channel_Name": "通道名称",
        "Master_TLS_Version": "主服务器TLS版本",
        "Master_public_key_path": "主服务器公钥路径",
        "Get_master_public_key": "是否获取主服务器公钥",
        "Network_Namespace": "网络命名空间"
    }

    def __init__(self):
        if not os.path.exists(plugin_conf_file):
            conf = {
              "master": {},
              "slave": {}
            }
            public.writeFile(plugin_conf_file, json.dumps(conf))

        self.update_versions_2_0()
        self.update_versions_2_1()

    # 卸载插件
    def uninstall_check(self, get=None):
        conf = self.get_conf()

        for slave_ip in conf["slave"].keys():
            mysql_slave_obj = mysql_slave(slave_ip)
            if mysql_slave_obj.bt_api_obj is None:
                continue
            # 删除从库配置文件
            resp = mysql_slave_obj.bt_api_obj.get_slave_conf()
            if resp["status"] is False:
                continue

            # 关闭主从复制
            mysql_slave_obj.exec_shell_sql("stop slave")
            mysql_slave_obj.exec_shell_sql("reset slave")
            mysql_slave_obj.exec_shell_sql("reset slave all")

            slave_conf = resp["data"]

            slave_conf = re.sub(r"#\s*主从复制配置\n", "", slave_conf)
            slave_conf = re.sub(r"#\s*------\n", "", slave_conf)
            slave_conf = re.sub(r"replicate[-_]do[-_]db\s*=\s*.+\n", "", slave_conf)
            slave_conf = re.sub(r"replicate[-_]ignore[-_]db\s*=\s*.+\n", "", slave_conf)
            slave_conf = re.sub(r"replicate[-_]do[-_]table\s*=\s*.+\n", "", slave_conf)
            slave_conf = re.sub(r"replicate[-_]ignore[-_]table\s*=\s*.+\n", "", slave_conf)
            slave_conf = re.sub(r"replicate[-_]wild[-_]do[-_]table\s*=\s*.+\n", "", slave_conf)
            slave_conf = re.sub(r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.+\n", "", slave_conf)
            mysql_slave_obj.bt_api_obj.save_slave_conf(slave_conf)


            # 删除从库信息
            self.del_slave_info(slave_ip)
            # 删除防火墙放行端口
            mysql_master().delete_port_release(slave_ip)

        mysql_obj = panelMysql.panelMysql()
        slave_user = conf["master"].get("slave_user")
        host_list = mysql_obj.query(f"select Host from mysql.user where User='{slave_user}'")
        for host in host_list:
            mysql_obj.query(f"drop user `{slave_user}`@`{host[0]}`")

        return public.returnMsg(False, "已删除所有主从")

    def update_versions_2_0(self):
        try:
            mysql_obj = panelMysql.panelMysql()

            # 初始化配置文件
            conf = self.get_conf()
            if isinstance(conf["slave"], dict): # 已更新
                return

            public.print_log(f"2.0 更新配置文件！")

            slave_dict = {}
            for slave in conf["slave"]:
                slave_ip = slave["ip"]

                replicate_do_db = []
                replicate_do_table = []
                ignore_tbs = slave.get("ignore_tbs", [])
                replicate_slave_dbs = slave.get("replicate_dbs", [])

                database_list = mysql_obj.query(f"show databases;")
                for db in replicate_slave_dbs:
                    if db == "all":
                        for db in database_list:
                            db_name = db[0]
                            if db_name in ["information_schema","performance_schema","mysql","sys"]: continue

                            tb_list = mysql_obj.query(f"show tables from `{db_name}`;")
                            if isinstance(tb_list, list):
                                for tb in tb_list:
                                    if f"{db_name}.{tb[0]}" in ignore_tbs:
                                        continue
                                    replicate_do_table.append(f"{db_name}.{tb[0]}")
                            replicate_do_db.append(db_name)
                        break
                    else:
                        db_name = db['name']
                        tb_list = mysql_obj.query(f"show tables from `{db_name}`;")
                        if isinstance(tb_list, list):
                            for tb in tb_list:
                                if f"{db_name}.{tb[0]}" in ignore_tbs:
                                    continue
                                replicate_do_table.append(f"{db_name}.{tb[0]}")

                        replicate_do_db.append(db_name)

                bt_api_obj = bt_api(slave["panel_addr"], slave["panel_key"])
                resp = bt_api_obj.get_slave_conf()
                my_conf = resp["data"]
                server_obj = re.search(r"server-id\s*=\s*\d+\n", my_conf)
                server_id = server_obj.group()
                server_id = server_id.split("=")[1].strip()

                sql = "show slave status\G;"
                root_password = bt_api_obj.get_root_passowrd()
                shell = f"export MYSQL_PWD={root_password} &&/usr/bin/mysql -uroot -e '{sql}' && export MYSQL_PWD=''"
                slave_status = bt_api_obj.slave_execute_command(shell, "/tmp")

                slave_status = slave_status["msg"]
                replicate_status = copy.deepcopy(self.conf_info)
                if re.search("Slave_IO_Running: Yes", slave_status, re.I) and re.search("Slave_SQL_Running: Yes", slave_status, re.I):
                    for info in replicate_status:
                        info["status"] = True

                slave_info = {
                    "panel_key": slave["panel_key"],
                    "panel_addr": slave["panel_addr"],
                    "replicate_do_db": replicate_do_db,
                    "replicate_ignore_db": [],
                    "replicate_do_table": replicate_do_table,
                    "replicate_ignore_table": [],
                    "replicate_wild_do_table": [],
                    "replicate_wild_ignore_table": [],
                    "server-id": server_id,
                    "replicate_status": replicate_status
                }
                slave_dict[slave_ip] = slave_info
            conf["slave"] = slave_dict
            public.writeFile(plugin_conf_file, json.dumps(conf))
        except Exception as err:
            public.print_log(f">>更新 2.1 错误:{err}")

    def update_versions_2_1(self):
        try:
            # 初始化配置文件
            conf = self.get_conf()
            if conf["master"].get("version") == "2.1":
                return

            if not isinstance(conf["slave"], dict):
                return

            if os.path.isfile("/tmp/mysql_replicate.log"):
                os.remove("/tmp/mysql_replicate.log")

            public.print_log(f"2.1 更新配置文件！")
            conf["master"]["version"] = "2.1"

            for slave in conf["slave"].values():
                db_dict = {}
                for db in slave.get("replicate_do_db"):
                    db_dict[db] = []

                for tb in slave["replicate_do_table"]:
                    db, tb = str(tb).split(".")

                    if db_dict.get(db) is None:
                        db_dict[db] = []
                    db_dict[db].append({"name": tb, "is_exist": True})

                db_list = []
                for db, table_list in db_dict.items():
                    data = {
                        "name": db,
                        "is_exist": True,
                        "table_list": table_list,
                    }
                    db_list.append(data)
                slave["replicate_db"] = db_list
                slave["replicate_wild_table"] = []
                slave["replicate_db_type"] = 0
                slave["replicate_table_type"] = 0

                replicate_status = []
                for status in slave["replicate_status"]:
                    if status["api"] == "export_dump_database":
                        for data in self.conf_info:
                            if data["api"] == "sync_database":
                                replicate_status.append(data)
                    if status["api"] in ["export_dump_database", "upload_database_file", "import_dump_database", "create_replicate_user"]:
                        continue

                    if status["api"] == "check_master_conf":
                        status["msg"] = "【主库】配置信息检查并配置"
                        replicate_status.append(status)

                        for t_status in slave["replicate_status"]:
                            if t_status["api"] == "create_replicate_user":
                                replicate_status.append(t_status)
                    replicate_status.append(status)
                slave["replicate_status"] = replicate_status
                if slave.get("replicate_do_db") is not None: del slave["replicate_do_db"]
                if slave.get("replicate_ignore_db") is not None: del slave["replicate_ignore_db"]
                if slave.get("replicate_do_table") is not None: del slave["replicate_do_table"]
                if slave.get("replicate_ignore_table") is not None: del slave["replicate_ignore_table"]
                if slave.get("replicate_wild_do_table") is not None: del slave["replicate_wild_do_table"]
                if slave.get("replicate_wild_ignore_table") is not None: del slave["replicate_wild_ignore_table"]
                if slave.get("export_path") is not None: del slave["export_path"]
                if slave.get("export_dump_database_task_id") is not None: del slave["export_dump_database_task_id"]
                if slave.get("upload_database_file_task_id") is not None: del slave["upload_database_file_task_id"]
                if slave.get("import_dump_database_task_id") is not None: del slave["import_dump_database_task_id"]
            public.writeFile(plugin_conf_file, json.dumps(conf))
        except Exception as err:
            public.print_log(f">>更新 2.1 错误:{err}")

    def get_logs(self,get):
        import files
        return files.files().GetLastLine(logs_file, 20)

    # 获取配置文件
    @classmethod
    def get_conf(cls):
        conf = public.readFile(plugin_conf_file)
        try:
            conf = json.loads(conf)
        except:
            conf = {
                "master": {},
                "slave": {}
            }
        return conf

    # 获取主从信息
    @classmethod
    def get_slave_info(cls, slave_ip: str):
        conf = cls.get_conf()
        return conf["slave"].get(slave_ip) # type: dict, None

    # 修改主从信息
    @classmethod
    def set_slave_info(cls, slave_ip:str, slave_info: str):
        conf = cls.get_conf()
        conf["slave"][slave_ip] = slave_info
        public.writeFile(plugin_conf_file, json.dumps(conf))
        return True

    # 删除主从信息
    @classmethod
    def del_slave_info(cls, slave_ip: str):
        conf = cls.get_conf()
        if conf['slave'].get(slave_ip):
            del conf['slave'][slave_ip]
            public.writeFile(plugin_conf_file, json.dumps(conf))
        return True

    # 设置主从同步状态
    @classmethod
    def set_slave_satuts(cls, slave_ip: str, method: str, status: bool):
        conf = cls.get_conf()
        slave = conf['slave'].get(slave_ip)
        if slave is not None:
            for info in slave["replicate_status"]:
                if info["api"] == method:
                    info["status"] = status
                    public.writeFile(plugin_conf_file, json.dumps(conf))
                    break

    # 设置主从同步状态
    @classmethod
    def get_slave_satuts(cls, slave_ip: str, method: str) -> bool:
        conf = cls.get_conf()
        slave = conf['slave'].get(slave_ip)
        if slave is not None:
            for info in slave["replicate_status"]:
                if info["api"] == method:
                    return info.get("status", False)
        return False


    # 获取所有主从信息
    def get_slave_list(self, get):
        slave_list = []
        conf = self.get_conf()

        for slave_ip, slave_info in conf['slave'].items():
            # 获取从库读写状态
            mysql_slave_obj = mysql_slave(slave_ip)
            if mysql_slave_obj.bt_api_obj is None: continue
            slave_readonly = mysql_slave_obj.get_mysql_readonly()

            status = 0 # 启动状态 0 关闭 1 开启
            slave_status = 0 # 同步状态 0 异常 1 正常 2 连接中 3 需要配置 4 连接从库异常
            config_status = True
            for info in slave_info["replicate_status"]:
                if info["api"] == "start_replicate": continue
                if info["status"] == False:
                    config_status = False
                    break

            # 获取主从状态
            slave_status_info = mysql_slave_obj.get_slave_status()
            if slave_status_info is False:  # 请求错误
                status = 0
                slave_status = 4
            elif config_status is False: # 未配置完成
                status = 0
                slave_status = 3
            elif slave_status_info.get("Slave_IO_Running") == "Yes" and slave_status_info.get("Slave_SQL_Running") == "Yes": # 开启状态
                status = 1
                slave_status = 1
            elif slave_status_info.get("Slave_IO_Running") == "Connecting" or slave_status_info.get("Slave_SQL_Running") == "Connecting": # 连接中
                status = 1
                slave_status = 2
            elif slave_status_info.get("Slave_IO_Running", "No") == "No" and slave_status_info.get("Slave_SQL_Running", "No") == "No": # 关闭
                status = 0
                slave_status = 0
            else:
                status = 1
                slave_status = 0
            slave_info = {
                "status": status,
                "slave_status": slave_status,
                "slave_readonly": slave_readonly,
                "config_status": config_status,
                "ip": slave_ip,
            }
            slave_list.append(slave_info)
        return {"status": True, "data": slave_list}

    # 获取同步流程
    def get_replicate_conf(self, get):
        """
        :param get.slave_ip: 从库ip
        :return:
        """
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, "缺少参数! slave_ip")
        slave_ip = get.slave_ip
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        replicate_status = slave_info.get("replicate_status", copy.deepcopy(self.conf_info))
        return {"status": True,  "data": replicate_status}

    # 获取主从所有数据库信息
    def get_database(self, get):
        mysql_obj = panelMysql.panelMysql()
        db_list = mysql_obj.query("show databases;")
        database_list = []
        for db in db_list:
            db_name = db[0]
            if db_name in ["sys","mysql","information_schema","performance_schema"]: continue

            db_size = 0
            table_list = []
            tb_list = mysql_obj.query(f"show tables from `{db_name}`;")
            for tb in tb_list:
                data = mysql_obj.query(f'select data_length + index_length from information_schema.TABLES where table_schema = "{db_name}" and table_name = "{tb[0]}";')
                table = {
                    "name": tb[0],
                    "size": data[0][0],
                }
                db_size += data[0][0]
                table_list.append(table)
            table_list = sorted(table_list, key=lambda data: data['size'], reverse=True)
            database = {
                "name": db_name,
                "size": db_size,
                "table_list": table_list
            }
            database_list.append(database)
        database_list = sorted(database_list, key=lambda data: data['size'], reverse=True)
        return {"status": True, "data": database_list}

    # 检查从库信息
    def check_slave(self, get):
        """
        :param get.panel_addr: 从库面板地址
        :param get.panel_key: 从库面板key
        :return:
        """
        # 校验参数
        if not hasattr(get, "panel_addr"):
            return public.returnMsg(False, "缺少参数！ panel_addr")
        if not hasattr(get, "panel_key"):
            return public.returnMsg(False, "缺少参数！ panel_key")

        addr_list = re.findall("https?://.*:\d+/?", get.panel_addr)
        if len(addr_list) == 0:
            return public.returnMsg(False, "请输入正确的面板地址！ 如：http://1.1.1.1:8888/ http://www.bt.cn:8888/")
        panel_addr = addr_list[0]
        panel_addr = panel_addr if str(panel_addr).endswith("/") else panel_addr + "/"

        ipv4_list = re.findall("https?://(.*):\d+/?", panel_addr)
        slave_ip = ipv4_list[0]

        if self.get_slave_info(slave_ip) is not None:
            return public.returnMsg(False, f"从库【{slave_ip}】已经存在！")
        panel_key = get.panel_key

        # 逻辑处理
        # 创建远程连接
        mysql_slave_obj = mysql_slave(slave_ip)
        mysql_slave_obj.bt_api_obj = bt_api(panel_addr, panel_key)
        result = mysql_slave_obj.bt_api_obj.get_config()
        if result.get("status") is False:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库 {slave_ip} API接口的IP白名单")
        if "windows" in result.get("distribution").lower():
            return public.returnMsg(False, "Mysql 主从复制暂不支持 Windows 系统！")
        return public.returnMsg(True, "从库地址或密钥正确！")

    # 添加主从信息
    def add_replicate_info(self, get):
        """
        :param get.panel_addr: 从库面板地址
        :param get.panel_key: 从库面板key
        :param get.replicate_db: 选择数据库
        :param get.replicate_wild_table: 使用通配符来控制需要复制的表
        :param get.replicate_db_type: # 数据库是否选择 0 选择 1 排除
        :param get.replicate_table_type: # 表是否选择 0 选择 1 排除
        :return:
        """

        # 校验参数
        if not hasattr(get, "panel_addr"):
            return public.returnMsg(False, "缺少参数！ panel_addr")
        if not hasattr(get, "panel_key"):
            return public.returnMsg(False, "缺少参数！ panel_key")

        if not hasattr(get, "replicate_db") and not hasattr(get, "replicate_wild_table"):
            return public.returnMsg(False, "请选择您要同步的数据库或要排除的数据库！")
        if not hasattr(get, "replicate_db_type"):
            return public.returnMsg(False, f"缺少参数！ replicate_db_type")
        if not hasattr(get, "replicate_table_type"):
            return public.returnMsg(False, f"缺少参数！ replicate_table_type")

        if get.replicate_db_type not in ["0", "1"]:
            return public.returnMsg(False, f"参数错误！ replicate_db_type")
        if get.replicate_table_type not in ["0", "1"]:
            return public.returnMsg(False, f"参数错误！ replicate_table_type")

        addr_list = re.findall("https?://.*:\d+/?", get.panel_addr)
        if len(addr_list) == 0:
            return public.returnMsg(False, "请输入正确的面板地址！ 如：http://1.1.1.1:8888/ http://www.bt.cn:8888/")
        panel_addr = addr_list[0]
        panel_addr = panel_addr if str(panel_addr).endswith("/") else panel_addr + "/"

        ipv4_list = re.findall("https?://(.*):\d+/?", panel_addr)
        slave_ip = ipv4_list[0]

        if self.get_slave_info(slave_ip) is not None:
            return public.returnMsg(False, f"从库【{slave_ip}】已经存在！")
        panel_key = get.panel_key

        replicate_db = json.loads(getattr(get, "replicate_db", "[]"))
        replicate_wild_table = json.loads(getattr(get, "replicate_wild_table", "[]"))
        replicate_db_type = int(get.replicate_db_type)  # 0 选择 1 排除
        replicate_table_type = int(get.replicate_table_type)  # 0 选择 1 排除

        if len(replicate_db) == 0 and len(replicate_wild_table) == 0:
            return public.returnMsg(False, "请选择您要同步的数据库或要排除的数据库！")

        master_ip = public.GetLocalIp()

        # 逻辑处理
        # 创建远程连接
        mysql_slave_obj = mysql_slave(slave_ip)
        mysql_slave_obj.bt_api_obj = bt_api(panel_addr, panel_key)
        result = mysql_slave_obj.bt_api_obj.get_config()
        if result.get("status") is False:
            return public.returnMsg(False, f"主库请求从库错误：{result.get('msg')}")
        if "windows" in result.get("distribution").lower():
            return public.returnMsg(False, "Mysql 主从复制暂不支持 Windows 系统！")

        # 保存配置
        conf = self.get_conf()
        master = conf.get("master", {})
        if not master.get("slave_user"):
            master["slave_user"] = public.GetRandomString(8)
        if not master.get("password"):
            master["password"] = public.gen_password(12)
        if not master.get("master_ip"):
            master["master_ip"] = master_ip
        if not master.get("master_port"):
            try:
                port = panelMysql.panelMysql().query("show global variables like 'port'")[0][1]
            except:
                port = 3306
            master["master_port"] = port
        conf["master"] = master
        if not conf.get("slave"):
            conf["slave"] = {}

        # 主从配置信息
        slave_info = {
            "panel_addr": panel_addr,
            "panel_key": panel_key,
            "replicate_db": replicate_db, # 需要复制的数据库
            "replicate_wild_table": replicate_wild_table, # 使用通配符来动态控制需要复制的表
            "replicate_db_type": replicate_db_type,  # 是否同步新增数据库
            "replicate_table_type": replicate_table_type,  # 是否同步新增表
            "replicate_status": self.conf_info
         }
        conf["slave"][slave_ip] = slave_info


        public.writeFile(plugin_conf_file, json.dumps(conf))

        public.set_module_logs('msyql_replicate', 'add_replicate_info', 1)
        return {"status": True, "msg": "添加成功!请点击开始配置！"}

    # 主从复制
    def replicate_main(self, get):
        if not hasattr(get, "action_name"):
            return public.returnMsg(False, f"缺少参数! action_name")

        # Mysql主从复制api
        replicate_api_fun = {
            "get_replicate_conf": self.get_replicate_conf,
            "check_slave_versions": self.check_slave_versions,
            "check_slave_database": self.check_slave_database,
            "sync_database": self.sync_database,
            "check_master_conf": self.check_master_conf,
            "check_slave_conf": self.check_slave_conf,
            "create_replicate_user": self.create_replicate_user,
            "check_firewall_set": self.check_firewall_set,
            "start_replicate": self.start_replicate,
        }

        return replicate_api_fun[get.action_name](get)

    # 检查主从版本信息
    def check_slave_versions(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 获取从库方法
        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 获取主库版本
        master_version = mysql_master.get_master_version()
        if mysql_master.version_compare(master_version,"5.6.0") == -1:
            return public.returnMsg(False, f"主库 Mysql{master_version} 版本不支持 gtid 同步方式! <br/>请将主库升级到 5.6 版本及以上！")

        slave_version = mysql_slave_obj.get_slave_version()
        if not slave_version:
            return public.returnMsg(False, f"获取从库版本失败!<br/>请尝试重启从库 Mysql 数据库")
        if not slave_version.startswith(master_version):
            return public.returnMsg(False, f"Mysql 主从版本不一致!<br/>主库版本:{master_version},<br/>从库版本:{slave_version}")

        for info in slave_info["replicate_status"]:
            if info["api"] == "check_slave_versions":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": "检查主库 Mysql 版本是否支持 gtid"},
                    {"msg": "检查 Mysql 版本一致性"}
                ]
        self.set_slave_info(slave_ip, slave_info)
        return {"status": True, "msg": "主从版本信息检查完成!"}

    # 检查主从库数据库一致性
    def check_slave_database(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "check_slave_versions") is False:
            return public.returnMsg(False, "请先检查主从版本信息！")

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 用户是否确定
        if hasattr(get, "type"):
            if str(get.type) == "1": # 用户确认覆盖或同步
                self.set_slave_satuts(slave_ip, "check_slave_database", True)
                self.set_slave_satuts(slave_ip, "sync_database", True)
                return {"status": True, "msg": "已跳过主库数据库同步到从库!"}

        # 获取配置信息
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        replicate_db = slave_info["replicate_db"]
        replicate_wild_table = slave_info["replicate_wild_table"]

        if len(replicate_wild_table) != 0:
            pass

        elif len(replicate_db) == 0:
            return public.returnMsg(False, "您未选择同步的数据库！")

        mysql_obj = panelMysql.panelMysql()

        slave_db_dict = {}
        data_list = mysql_slave_obj.exec_shell_sql(f'show databases;')
        data_list = str(data_list).lstrip("Database\n")
        data_list = data_list.split("\n")
        for db_name in data_list:
            if db_name in ["sys","mysql","performance_schema","information_schema"]: continue
            data = mysql_slave_obj.exec_shell_sql(f'show tables from `{db_name}`;')
            # data = str(data).lstrip(f"Tables_in_{db_name}\n")
            tb_list = str(data).split("\n")[1:]
            slave_db_dict[db_name] = tb_list

        total_row = 0
        exist_dict = {} # 从库已存在的数据库
        for db in replicate_db:
            db_name = db["name"]

            for tb in db["table_list"]:
                tb_name = tb["name"]
                if tb.get("is_exist", False) is True:  # 跳过已存在的
                    continue

                row_data = mysql_obj.query(f"select count(*) from `{db_name}`.`{tb_name}`;")
                if not isinstance(row_data, list): return public.returnMsg(False, str(row_data))
                row = row_data[0][0]
                tb["row"] = row
                total_row += row

                if tb_name in slave_db_dict.get(db_name, []):

                    if exist_dict.get(db_name) is None:
                        exist_dict[db_name] = []

                        data = mysql_slave_obj.exec_shell_sql(f"select count(*) from `{db_name}`.`{tb_name}`;")
                        data = str(data).split("\n")[-1]
                        row = int(data) if data.isdigit() else 0
                        table = {
                            "name": tb_name,
                            "row": row,
                        }
                        exist_dict[db_name].append(table)

        if exist_dict:
            exist_list = []
            for db_name, table_list in exist_dict.items():
                slave_row = sum([int(tb['row']) for tb in table_list])
                database = {"msg": f"数据库：{db_name}，总记录：{slave_row}"}
                exist_list.append(database)
                for tb in table_list:
                    database = {"msg": f"&emsp;&emsp;表：{tb['name']}，记录：{tb['row']}"}
                    exist_list.append(database)
            for info in slave_info["replicate_status"]:
                if info["api"] == "check_slave_database":
                    info["msg_list"] = [
                        {"msg": "从库已存在同名数据库，无法进行主从！"},
                        {"msg": f"从库【{slave_ip}】上存在的数据库:"},
                    ]
                    info["msg_list"].extend(exist_list)
                self.set_slave_info(slave_ip, slave_info)
            return {"status": False, "msg": f"从库已存在同名数据库，无法进行主从！<br/>{'<br/>'.join([db['msg'] for db in exist_list])}"}

        add_list = []
        for db in replicate_db:
            master_row = sum([int(tb['row']) for tb in db['table_list'] if tb.get("is_exist", False) is False])
            tmp_list = []
            for tb in db['table_list']:
                if tb.get("is_exist", False) is True: continue
                database = {"msg": f"&emsp;&emsp;表：{tb['name']}，记录：{tb['row']}"}
                tmp_list.append(database)
            if len(tmp_list) != 0:
                add_list.append({"msg": f"数据库：{db['name']}，总记录：{master_row}"})
                add_list.extend(tmp_list)
        for info in slave_info["replicate_status"]:
            if info["api"] == "check_slave_database":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": "【主库】需要同步到从库的数据库"},
                ]
                info["msg_list"].extend(add_list)
        self.set_slave_info(slave_ip, slave_info)

        return {
            "status": True,
            "msg": f"您需要同步的数据库,总记录:{total_row}<br/>" \
                   f"请问您是否跳过把主库数据库同步到从库?<br/>" \
                   f"1. 主库二进制日志一直开启并且完好,选择【跳过】<br/>" \
                   f"2. 稍后手动同步过主从数据库,选择【跳过】<br/>" \
                   f"默认选择【跳过】",
            "type": 1
        }

    # 同步数据库
    def sync_database(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "check_slave_versions") is False:
            return public.returnMsg(False, "请先检查主从版本信息！")

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 获取配置信息
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 重新上传
        if hasattr(get, "type"):
            if str(get.type) == "1":
                if slave_info.get("sync_database_task_id") is not None:
                    del slave_info["sync_database_task_id"]
                for info in slave_info["replicate_status"]:
                    if info["api"] == "sync_database_task_id":
                        info["status"] = False
                        info["msg_list"] = []
                self.set_slave_info(slave_ip, slave_info)

        # 后台执行
        task_obj = panelTask.bt_task()
        task_id = slave_info.get("sync_database_task_id")  # 获取任务id
        if task_id is not None:
            task = task_obj.get_task_find(task_id)
            if not task:
                if slave_info.get("sync_database_task_id") is not None: del slave_info["sync_database_task_id"]
                if slave_info.get("sync_database_log") is not None: del slave_info["sync_database_log"]
                self.set_slave_info(slave_ip, slave_info)
                return {"status": False, "msg": "任务不存在！请重新执行！"}

            # 后台执行日志
            sync_database_log = slave_info.get("sync_database_log", "")
            # 任务未完成
            if task.get("status", 0) != 1:
                # 文件不存在
                if not os.path.exists(sync_database_log):
                    return {"status": True, "msg": "正在初始化,请稍后...", "type": 2}
                export_log = public.readFile(sync_database_log)
                end_line = str(export_log).split("\n")[-1]  # 取出最后一条执行记录
                status, msg = end_line.split("|")
                # 获取同步日志
                if status == "0": # 前端停止请求
                    os.remove(sync_database_log)
                    if slave_info.get("sync_database_task_id") is not None: del slave_info["sync_database_task_id"]
                    if slave_info.get("sync_database_log") is not None: del slave_info["sync_database_log"]
                    self.set_slave_info(slave_ip, slave_info)
                    return {"status": False, "msg": msg}
                else:
                    return {"status": True, "msg": msg, "type": 2}

            # 任务完成
            msg_list = []
            if os.path.exists(sync_database_log):
                export_log = public.readFile(sync_database_log)
                execute_list = str(export_log).split("\n")
                for info in execute_list:
                    status, msg = info.split("|")
                    if status == "0":
                        os.remove(sync_database_log)
                        if slave_info.get("sync_database_task_id") is not None: del slave_info["sync_database_task_id"]
                        if slave_info.get("sync_database_log") is not None: del slave_info["sync_database_log"]
                        self.set_slave_info(slave_ip, slave_info)
                        return {"status": False, "msg": msg}
                    if status == "2":
                        msg_list.append({"msg": f"{msg}"})
                # 导入成功 删除执行日志
                os.remove(sync_database_log)
                if slave_info.get("sync_database_log") is not None: del slave_info["sync_database_log"]
                self.set_slave_info(slave_ip, slave_info)
                # 保存执行记录
                for info in slave_info["replicate_status"]:
                    if info["api"] == "sync_database":
                        info["status"] = True
                        info["msg_list"] = msg_list
                self.set_slave_info(slave_ip, slave_info)

            if self.get_slave_satuts(slave_ip, "sync_database") is False:
                if slave_info.get("sync_database_task_id") is not None: del slave_info["sync_database_task_id"]
                if slave_info.get("sync_database_log") is not None: del slave_info["sync_database_log"]
                self.set_slave_info(slave_ip, slave_info)
                return public.returnMsg(False, "请重试！")
            return public.returnMsg(True, "数据库已同步完成！")


        replicate_db = slave_info["replicate_db"]
        replicate_wild_table = slave_info["replicate_wild_table"]

        if len(replicate_wild_table) != 0:
            pass

        elif len(replicate_db) == 0:
            return public.returnMsg(False, "您未选择同步的数据库！")

        # 后台上传
        # if export_path_size / 1024 / 1024 > 1024:
        task_id = task_obj.create_task('同步主从数据库', 0, f"btpython {execute_slave} --slave_ip={slave_ip} --api=sync_slave_database")
        slave_info["sync_database_task_id"] = task_id  # 保存任务id
        self.set_slave_info(slave_ip, slave_info)

        return {"status": True, "msg": "已开始同步数据库!"}

    # 检查并设置主库配置
    def check_master_conf(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "sync_database") is False:
            return public.returnMsg(False, "请先同步主从数据库！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        mysql_master_obj = mysql_master()

        is_update = False

        # 检查并设置 gtid
        if mysql_master_obj.get_master_gtid_status() is False:
            is_update = True
            result = mysql_master_obj.set_master_gtid_conf()
            if result is not True:
                return public.returnMsg(False, f"设置 gtid 错误！{result}")

        # 检查并设置 binlog
        if mysql_master_obj.get_master_binlog() is False:
            is_update = True
            result = mysql_master_obj.set_master_binlog()
            if result is not True:
                return public.returnMsg(False, f"设置 binlog 错误！{result}")

        # 设置server_id
        server_id = mysql_master_obj.get_master_server_id()
        if server_id is False:
            is_update = True
            server_id = self.__new_generate_number(9)
            mysql_master_obj.set_master_server_id(server_id)

        conf = self.get_conf()
        if conf["master"].get("server-id") is None:
            conf["master"]["server-id"] = server_id
            public.writeFile(plugin_conf_file, json.dumps(conf))

        if is_update is True:
            public.writeFile(plugin_conf_file, json.dumps(conf))

            # 重启服务
            public.ExecShell("/etc/init.d/mysqld restart")

        for info in slave_info["replicate_status"]:
            if info["api"] == "check_master_conf":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": "检查 server-id"},
                    {"msg": "检查 gtid"},
                    {"msg": "检查 binlog"}
                ]
        self.set_slave_info(slave_ip, slave_info)
        return {"status": True, "msg": "主库配置信息检查完成!"}


    # 生成server-id
    @classmethod
    def __new_generate_number(self,num_len):
        import random
        return "".join(map(lambda x: random.choice("123456789"), range(num_len)))

    # 检查并设置主从同步用户
    def create_replicate_user(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "check_master_conf") is False:
            return public.returnMsg(False, "请先检查并设置主库配置信！")

        # 获取配置信息
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        conf = self.get_conf()
        user = conf['master']['slave_user']
        password = conf['master']['password']

        # 获取主库版本
        master_version = mysql_master.get_master_version()

        mysql_obj = panelMysql.panelMysql()

        # 检查同步用户
        is_user = mysql_obj.query(f"select count(User) from mysql.user where User='{user}' and Host='{slave_ip}';")
        if is_user[0][0] == 0:
            mysql_obj.execute(f"flush privileges;")
            mysql_obj.execute(f"create user '{user}'@'{slave_ip}' identified by '{password}'")
            if mysql_master.version_compare(master_version, "8.0.0") != -1:
                mysql_obj.execute(f"grant replication slave on *.* to '{user}'@'{slave_ip}'")
            else:
                mysql_obj.execute(f"grant replication slave on *.* to '{user}'@'{slave_ip}' identified by '{password}'")
            mysql_obj.execute(f"flush privileges;")


        for info in slave_info["replicate_status"]:
            if info["api"] == "create_replicate_user":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": f"创建用户：{user}，权限：主从复制（replication），允许访问ip：{slave_ip}"},
                ]
        self.set_slave_info(slave_ip, slave_info)
        return public.returnMsg(True, "主从复制用户已创建完成！")

    # 检查并设置从库配置信息
    def check_slave_conf(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "create_replicate_user") is False:
            return public.returnMsg(False, "请先检查并设置主从同步用户！")

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        conf_list = []

        # 检查 server_id
        conf = self.get_conf()
        server_id_list = [conf["master"].get("server-id", 1)] # 获取所有 server-id
        for ip,slave in conf["slave"].items():
            if ip == slave_ip: continue
            server_id_list.append(slave.get("server-id", 0))

        server_id = mysql_slave_obj.get_slave_server_id()
        if server_id is False:
            server_id = self.__new_generate_number(9)
        while True: # 生成新的 server-id
            if server_id not in server_id_list:
                break
            server_id = self.__new_generate_number(9)

        mysql_slave_obj.set_slave_server_id(server_id)
        slave_info["server-id"] = server_id
        # 保存主从信息
        self.set_slave_info(slave_ip, slave_info)

        conf_list.append({"msg": f"检查 server-id"})

        resp = mysql_slave_obj.bt_api_obj.get_slave_conf()
        if resp["status"] is False:
            return public.returnMsg(False, f"获取从库配置错误！ {resp['msg']}")
        mysql_conf = resp["data"]

        # 是否确定覆盖
        if hasattr(get, "type"):
            if str(get.type) == "1":
                mysql_conf = re.sub(r"replicate[-_]do[-_]db\s*=\s*.*\n", "", mysql_conf)
                mysql_conf = re.sub(r"replicate[-_]ignore[-_]db\s*=\s*.*\n", "", mysql_conf)
                mysql_conf = re.sub(r"replicate[-_]do[-_]table\s*=\s*.*\n", "", mysql_conf)
                mysql_conf = re.sub(r"replicate[-_]ignore[-_]table\s*=\s*.*\n", "", mysql_conf)
                mysql_conf = re.sub(r"replicate[-_]wild[-_]do[-_]table\s*=\s*.*\n", "", mysql_conf)
                mysql_conf = re.sub(r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.*\n", "", mysql_conf)

        # 检查从库是否已经设置主从配置
        db_re = r"(replicate[-_]do[-_]db\s*=\s*.*\n|" \
                r"replicate[-_]ignore[-_]db\s*=\s*.*\n)"
        table_re = r"(replicate[-_]do[-_]table\s*=\s*.*\n|" \
                   r"replicate[-_]ignore[-_]table\s*=\s*.*\n|" \
                   r"replicate[-_]wild[-_]do[-_]table\s*=\s*.*\n|" \
                   r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.*\n)"
        replicate_db_list = re.findall(db_re, mysql_conf)
        replicate_table_list = re.findall(table_re, mysql_conf)
        if len(replicate_db_list) != 0 or len(replicate_table_list) != 0:
            return {"status": True, "msg": f"您已设置主从配置，是否覆盖?", "type": 1}

        # 停止从库同步
        mysql_slave_obj.exec_shell_sql("stop slave;")
        # mysql_slave_obj.exec_shell_sql("reset master")

        # 检查 gtid
        # 检查并设置 gtid
        if not re.search("\n\s*gtid-mode\s*=\s*on", mysql_conf):
            # 设置从库的gtid支持
            gtid_conf = """
log-slave-updates=on
enforce-gtid-consistency=on
read-only=on
relay-log=relay-log-server
gtid-mode=on"""
            mysql_conf = resp["data"]
            mysql_conf = re.sub("log-slave-updates\s*=\s*.*\n", "", mysql_conf)
            mysql_conf = re.sub("enforce-gtid-consistency\s*=\s*.*\n", "", mysql_conf)
            mysql_conf = re.sub("read-only\s*=\s*.*\n", "", mysql_conf)
            mysql_conf = re.sub("relay-log\s*=\s*.*\n", "", mysql_conf)
            mysql_conf = re.sub("gtid-mode\s*=\s*.*\n", "", mysql_conf)
            mysql_conf = re.sub("\[mysqld\]", "[mysqld]" + gtid_conf, mysql_conf)

        conf_list.append({"msg": f"检查 gtid"})

        # 检查并设置 binlog
        if not re.search("\n\s*log-bin\s*=\s*mysql-bin", mysql_conf):
            bin_log = """
log-bin=mysql-bin
binlog_format=mixed"""
            if not re.search('\n\s*#\s*log-bin\s*=\s*mysql-bin', mysql_conf):
                mysql_conf = re.sub("log-bin\s*=\s*.*\n", "", mysql_conf)
                mysql_conf = re.sub("binlog_format\s*=\s*.*\n", "", mysql_conf)
                mysql_conf = re.sub("\[mysqld\]", "[mysqld]" + bin_log, mysql_conf)
            else:
                mysql_conf = mysql_conf.replace('#log-bin=mysql-bin', 'log-bin=mysql-bin')
                mysql_conf = mysql_conf.replace('#binlog_format=mixed', 'binlog_format=mixed')

        conf_list.append({"msg": f"检查 binlog"})

        mysql_conf = re.sub(r"#\s*主从复制配置\n", "", mysql_conf)
        mysql_conf = re.sub(r"#\s*------\n", "", mysql_conf)

        replicate_db = slave_info["replicate_db"]
        replicate_wild_table = slave_info["replicate_wild_table"]
        replicate_db_type = slave_info["replicate_db_type"]
        replicate_table_type = slave_info["replicate_table_type"]

        if len(replicate_db) == 0 and len(replicate_wild_table) == 0:
            return public.returnMsg(False, "您未选择同步的数据库！")

        # 设置同步数据库，表
        replicate_do_db = []
        replicate_ignore_db = []
        replicate_do_table = []
        replicate_ignore_table = []
        replicate_wild_do_table = []
        replicate_wild_ignore_table = []

        mysql_obj = panelMysql.panelMysql()

        # 通配符匹配
        if len(replicate_wild_table) != 0:
            if replicate_db_type == 0:
                replicate_wild_do_table = replicate_wild_table
            else:
                replicate_wild_ignore_table = replicate_wild_table

        # 选择数据库
        elif len(replicate_db) != 0:
            # 数据库
            if replicate_db_type == 0: # 同步数据库
                replicate_do_db = [db["name"] for db in replicate_db]
            else: # 不同步数据库
                db_list = [db["name"] for db in replicate_db]
                db_list.extend(["sys", "mysql", "information_schema", "performance_schema"])
                db_sql = "'" + "','".join(db_list) + "'"
                db_list = mysql_obj.query(f"select schema_name from information_schema.schemata where schema_name not in ({db_sql});")
                replicate_ignore_db = [db[0] for db in db_list]

            # 表
            for db in replicate_db:
                db_name = db["name"]

                tb_list = [tb["name"] for tb in db["table_list"]]
                if replicate_table_type == 0:
                    replicate_do_table.extend([f"{db_name}.{tb_name}" for tb_name in tb_list])
                else:
                    tb_sql = "'" + "','".join(tb_list) + "'"
                    tb_list = mysql_obj.query(f"select table_name from information_schema.tables where table_schema = '{db_name}' and table_name not in ({tb_sql});")
                    replicate_ignore_table.extend([f"{db_name}.{tb[0]}" for tb in tb_list])

        replicate_conf = "\n# 主从复制配置"
        if len(replicate_do_db) != 0:
            conf_list.append({"msg": "设置同步数据库：replicate-do-db"})
            for db_name in replicate_do_db:
                replicate_conf += f"\nreplicate-do-db={db_name}"

        elif len(replicate_ignore_db) != 0:
            conf_list.append({"msg": "设置排除数据库：replicate-ignore-db"})
            for db_name in replicate_ignore_db:
                replicate_conf += f"\nreplicate-ignore-db={db_name}"

        if len(replicate_do_table) != 0:
            conf_list.append({"msg": "设置同步表：replicate-do-table"})
            for tb_name in replicate_do_table:
                replicate_conf += f"\nreplicate-do-table={tb_name}"

        elif len(replicate_ignore_table) != 0:
            conf_list.append({"msg": "设置排除表：replicate-ignore-table"})
            for tb_name in replicate_ignore_table:
                replicate_conf += f"\nreplicate-ignore-table={tb_name}"

        if len(replicate_wild_do_table) != 0:
            conf_list.append({"msg": "设置通配符同步表：replicate-wild-do-table"})
            for tb_name in replicate_wild_do_table:
                replicate_conf += f"\nreplicate-wild-do-table={tb_name}"

        elif len(replicate_wild_ignore_table) != 0:
            conf_list.append({"msg": "设置通配符排除表：replicate-wild-ignore-table"})
            for tb_name in replicate_wild_ignore_table:
                replicate_conf += f"\nreplicate-wild-ignore-table={tb_name}"

        replicate_conf += "\n# ------"
        mysql_conf = re.sub("\[mysqld\]", "[mysqld]" + replicate_conf, mysql_conf)

        # 保存配置
        resp = mysql_slave_obj.bt_api_obj.save_slave_conf(mysql_conf)
        if resp["status"] is False:
            return public.returnMsg(False, f"保存从库配置错误！{resp['msg']}")

        # 获取远程数据库读写状态
        resp = mysql_slave_obj.set_mysql_readonly(status=1)
        if resp is not None:
            return public.returnMsg(False, resp)

        conf_list.append({"msg": "设置从库 Mysql 只读状态（除超级用户root外）"})

        mysql_slave_obj.bt_api_obj.control_mysqld_service()

        is_sysc_database = False
        for db in replicate_db:
            if db.get("is_exist", False) is False or is_sysc_database is True:
                is_sysc_database = True
                break
            for tb in db["table_list"]:
                if tb.get("is_exist", False) is False:
                    is_sysc_database = True
                    break
        if is_sysc_database is True:
            mysql_slave_obj.exec_shell_sql("stop slave;reset slave all;")
            # 设置排除 gtid
            gtid = slave_info.get("executed_gtid_set")
            if gtid is not None:
                msg = mysql_slave_obj.exec_shell_sql(f"SELECT @@GLOBAL.GTID_PURGED;")
                msg = str(msg).lstrip("@@GLOBAL.GTID_PURGED").strip()
                if msg:
                    mysql_slave_obj.exec_shell_sql("reset master")

                mysql_slave_obj.exec_shell_sql(f"SET @@GLOBAL.GTID_PURGED='{gtid}'", True)
                conf_list.append({"msg": f"设置 @@GLOBAL.GTID_PURGED={gtid}"})

                del slave_info["executed_gtid_set"]

            master = self.get_conf()["master"]
            master_log_file = slave_info.get("master_log_file")
            master_log_pos = slave_info.get("master_log_pos")
            if master_log_file is not None and master_log_pos is not None:
                create_replicate_sql = f"""
                                change master to
                                master_host="{master['master_ip']}",
                                master_user="{master['slave_user']}",
                                master_password="{master['password']}",
                                master_log_file="{master_log_file}",
                                master_log_pos={master_log_pos};
                            """
                del slave_info["master_log_file"]
                del slave_info["master_log_pos"]
                conf_list.append({"msg": f"设置主从同步【指定同步位置】binlog_file={master_log_file} pos={master_log_pos}"})
            else:
                create_replicate_sql = f"""
                                change master to
                                master_host="{master['master_ip']}",
                                master_user="{master['slave_user']}",
                                master_password="{master['password']}",
                                master_port={master['master_port']},
                                master_auto_position=1;
                            """
                conf_list.append({"msg": f"设置主从【自动同步】AUTO_POSITION=1"})
            mysql_slave_obj.exec_shell_sql(create_replicate_sql)

        mysql_slave_obj.bt_api_obj.control_mysqld_service()
        conf_list.append({"msg": f"重启从库Mysql数据库服务"})

        for info in slave_info["replicate_status"]:
            if info["api"] == "check_slave_conf":
                info["status"] = True
                info["msg_list"] = conf_list

        slave_info["addtime"] = time.time()
        self.set_slave_info(slave_ip, slave_info)
        return {"status": True, "msg": "从库配置信息检查并配置完成!"}

    # 检查并设置防火墙放行端口
    def check_firewall_set(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "check_slave_conf") is False:
            return public.returnMsg(False, "请先检查并设置从库配置信息！")

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 获取配置信息
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 获取配置文件
        resp = mysql_slave_obj.bt_api_obj.get_slave_conf()
        if resp["status"] is False:
            return public.returnMsg(False, resp["msg"])
        # 获取从库端口
        temp_port = re.findall("\n\s*port\s*=\s*(\d+)", resp["data"])
        if len(temp_port) != 0:
            slave_port = temp_port[0]
        else:
            slave_port =  3306

        mysql_master_obj = mysql_master()

        is_start = mysql_master_obj.check_port(slave_ip, slave_port)
        if is_start is True:
            for info in slave_info["replicate_status"]:
                if info["api"] == "check_firewall_set":
                    info["status"] = True
                    info["msg_list"] = [
                        {"msg": f"防火墙已放行：{slave_ip} 端口：{slave_port}"},
                    ]
            self.set_slave_info(slave_ip, slave_info)
            return public.returnMsg(True, f"防火墙已放行 {slave_ip} 访问 {slave_port} 端口！")

        mysql_master_obj.add_port_release(slave_ip, slave_port)

        is_start = mysql_master_obj.check_port(slave_ip, slave_port)
        if is_start is False:
            return public.returnMsg(True, f"防火墙设置失败！请手动放行 {slave_ip}:{slave_port}")

        for info in slave_info["replicate_status"]:
            if info["api"] == "check_firewall_set":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": f"防火墙已放行：{slave_ip} 端口：{slave_port}"},
                ]
        self.set_slave_info(slave_ip, slave_info)
        return public.returnMsg(True, f"防火墙已放行 {slave_ip} 访问 {slave_port} 端口！")


    # 开启主从复制
    def start_replicate(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "check_firewall_set") is False:
            return public.returnMsg(False, "请先检查并设置防火墙放行端口！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        for info in slave_info["replicate_status"]:
            if info["api"] == "start_replicate": continue
            if info["status"] == False:
                return public.returnMsg(False, f"请先 【{info['msg']}】")

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        mysql_slave_obj.exec_shell_sql("start slave")
        time.sleep(0.3)

        if self.get_slave_satuts(slave_ip, "start_replicate") is False:
            self.set_slave_satuts(slave_ip, "start_replicate", True)

        slave_status_info = mysql_slave_obj.get_slave_status()
        if slave_status_info is False:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库 {slave_ip} API接口的IP白名单")
        elif not slave_status_info:
            return public.returnMsg(False, f"启动失败！请在状态中查看错误信息！")
        elif slave_status_info.get("Slave_IO_Running") == "No" and slave_status_info.get("Slave_SQL_Running") == "No":
            return public.returnMsg(False, f"启动失败！请在状态中查看错误信息！")

        return public.returnMsg(True, "启动完成！")

    # 停止主从复制
    def stop_replicate(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        resp = mysql_slave_obj.exec_shell_sql("stop slave", True)
        if resp["status"] is False:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库 {slave_ip} API接口的IP白名单")

        slave_status_info = mysql_slave_obj.get_slave_status()
        if slave_status_info is False:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库 {slave_ip} API接口的IP白名单")
        elif not slave_status_info:
            return public.returnMsg(True, "停止成功！")
        elif slave_status_info.get("Slave_IO_Running") != "No" or slave_status_info.get("Slave_SQL_Running") != "No":
            return public.returnMsg(False, f"停止失败！请在状态中查看错误信息！！")

        return public.returnMsg(True, "停止成功！")

    # 设置从库状态
    def setup_readonly_status(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        if not hasattr(get, "status"):
            return public.returnMsg(False, f"缺少参数! status")
        if get.status not in ["0","1"]:
            return public.returnMsg(False, f"status 参数错误!")

        slave_ip = get.slave_ip
        status = int(get.status)

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False,"主从信息不存在！")

        # 获取远程数据库读写状态
        result = mysql_slave_obj.set_mysql_readonly(status=status)
        if result is not None:
            return public.returnMsg(False, result)
        return public.returnMsg(True, f"设置从库 {slave_ip} {'只读' if status == 1 else '读写'} 状态成功！")

    # 删除主从复制
    def remove_replicate_info(self,get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False,"主从信息不存在！")

        if hasattr(get, "type"):
            if str(get.type) == "1":
                # 删除从库信息
                self.del_slave_info(slave_ip)
                # 删除防火墙放行端口
                mysql_master().delete_port_release(slave_ip)
                return public.returnMsg(True, "删除主库配置成功！")

        # 删除从库配置文件
        resp = mysql_slave_obj.bt_api_obj.get_slave_conf()
        if resp["status"] is False:
            return {"status": True, "msg": "请求从库错误!是否仅删除主库配置", "type": 1}

        # 关闭主从复制
        mysql_slave_obj.exec_shell_sql("stop slave")
        mysql_slave_obj.exec_shell_sql("reset slave")
        mysql_slave_obj.exec_shell_sql("reset slave all")

        mysql_conf = resp["data"]

        mysql_conf = re.sub(r"#\s*主从复制配置\n", "", mysql_conf)
        mysql_conf = re.sub(r"#\s*------\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]do[-_]db\s*=\s*.+\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]ignore[-_]db\s*=\s*.+\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]do[-_]table\s*=\s*.+\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]ignore[-_]table\s*=\s*.+\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]wild[-_]do[-_]table\s*=\s*.+\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.+\n", "", mysql_conf)
        mysql_slave_obj.bt_api_obj.save_slave_conf(mysql_conf)

        # 重启数据库
        mysql_slave_obj.bt_api_obj.control_mysqld_service()

        conf = self.get_conf()
        slave_user = conf["master"].get("slave_user")
        panelMysql.panelMysql().query(f"drop user `{slave_user}`@`{slave_ip}`")
        # 删除从库信息
        self.del_slave_info(slave_ip)
        # 删除防火墙放行端口
        mysql_master().delete_port_release(slave_ip)

        return public.returnMsg(True, "删除成功！")

    # 获取主从详情
    def get_replicate_info(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, "缺少参数! slave_ip")
        slave_ip = get.slave_ip
        slave_info = self.get_slave_info(slave_ip)

        replicate_db = slave_info["replicate_db"]
        replicate_wild_table = slave_info["replicate_wild_table"]
        replicate_db_type = slave_info["replicate_db_type"]
        replicate_table_type = slave_info["replicate_table_type"]

        info = {
            "replicate_db": replicate_db,
            "replicate_wild_table": replicate_wild_table,
            "replicate_db_type": replicate_db_type,
            "replicate_table_type": replicate_table_type,
            "server_id": slave_info.get("server-id"),
        }

        return {"status": True, "data": info}

    # 获取主从状态
    def get_replicate_status(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, "缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 获取从库状态
        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        slave_status_info = mysql_slave_obj.get_slave_status()

        if slave_status_info is False:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库 {slave_ip} API接口的IP白名单")

        slave_status_list = []
        for name,value in slave_status_info.items():
            value = str(value).replace("\\n", "").split(",")
            value = "<br/>".join(value)
            slave_status_list.append({"name": name, "value": value, "ps": self.slave_status_ps.get(name)})

        return {"status": True, "data": slave_status_list}

    # 获取编辑数据库
    def get_set_database(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        addtime = slave_info.get("addtime")
        replicate_db = slave_info["replicate_db"]
        replicate_wild_table = slave_info["replicate_wild_table"]
        replicate_db_type = slave_info["replicate_db_type"]
        replicate_table_type = slave_info["replicate_table_type"]

        # 组织临时数据
        replicate_database_tmp = {}
        for db in replicate_db:
            db_name = db["name"]
            if replicate_database_tmp.get(db_name) is None:
                replicate_database_tmp[db_name] = []
            for tb in db["table_list"]:
                replicate_database_tmp[db_name].append(tb["name"])

        mysql_obj = panelMysql.panelMysql()
        db_list = mysql_obj.query("show databases;")

        database_list = []
        for db in db_list:
            db_name = db[0]
            if db_name in ["sys", "mysql", "information_schema", "performance_schema"]: continue

            db_size = 0
            db_is_exist = replicate_database_tmp.get(db_name) is not None # 数据库是否选中
            db_tb_is_exist = False # 数据库不是全选
            db_is_add = False # 是否是新增数据库
            table_list = []
            tb_list = mysql_obj.query(f"show tables from `{db_name}`;")

            # 后续新增数据库
            if replicate_db_type == 1 and db_is_exist is False and addtime is not None:
                bt_data = public.M('databases').where("accept='127.0.0.1' and LOWER(type)=LOWER('mysql') and name=?", (db_name)).field("addtime").find()
                if isinstance(bt_data, dict) and bt_data:
                    dt = time.strptime(bt_data["addtime"], '%Y-%m-%d %H:%M:%S')
                    if time.mktime(dt) > int(addtime):
                        db_is_exist = True
                        db_is_add = True

            for tb in tb_list:
                tb_name = tb[0]
                data = mysql_obj.query(f'select data_length + index_length from information_schema.TABLES where table_schema = "{db_name}" and table_name = "{tb_name}";')

                # 是否已存在
                tb_is_exist = db_is_add

                # 后续新增表
                if addtime is not None and replicate_table_type == 1 and tb_is_exist is False:
                    tmp_is_exist = mysql_obj.query(f'select count(*) from information_schema.TABLES where table_schema = "{db_name}" and table_name = "{tb_name}" and create_time > "{datetime.datetime.fromtimestamp(addtime)}";')
                    if tmp_is_exist[0][0] != 0:
                        tb_is_exist = True

                if tb_name in replicate_database_tmp.get(db_name, []):
                    tb_is_exist = True
                    db_is_exist = True

                if db_is_exist is True and tb_is_exist is False:
                    db_tb_is_exist = True

                db_size += data[0][0]
                table = {
                    "name": tb_name,
                    "size": data[0][0],
                    "active": "active" if tb_is_exist == True else "",
                    "is_exist": tb_is_exist,
                }
                table_list.append(table)
            table_list = sorted(table_list, key=lambda tb: tb['size'], reverse=True)

            active = ""
            if db_is_exist is True: active = "active"
            if db_tb_is_exist is True: active = "active1"
            database = {
                "name": db_name,
                "size": db_size,
                "active": active,
                "is_exist": db_is_exist,
                "table_list": table_list
            }
            database_list.append(database)
        database_list = sorted(database_list, key=lambda db: db['size'], reverse=True)

        info = {
            "replicate_db": database_list,
            "replicate_wild_table": replicate_wild_table,
            "replicate_db_type": replicate_db_type,
            "replicate_table_type": replicate_table_type,
            "server_id": slave_info.get("server-id"),
        }
        return {"status": True, "data": info}

    # 修改是否同步新增数据库
    def set_slave_conf(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        if not hasattr(get, "replicate_type"):
            return public.returnMsg(False, f"缺少参数！ replicate_type")
        if not hasattr(get, "replicate_type_value"):
            return public.returnMsg(False, f"缺少参数！ replicate_type_value")

        if get.replicate_type not in ["replicate_db_type", "replicate_table_type"]:
            return public.returnMsg(False, f"参数错误！ replicate_type")
        if get.replicate_type_value not in ["0", "1"]:
            return public.returnMsg(False, f"参数错误！ replicate_type_value")

        replicate_type = get.replicate_type
        replicate_type_value = int(get.replicate_type_value)

        slave_ip = get.slave_ip

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        resp = mysql_slave_obj.bt_api_obj.get_slave_conf()
        if resp["status"] is False:
            return public.returnMsg(False, f"获取从库配置错误！ {resp['msg']}")
        mysql_conf = resp["data"]
        mysql_conf = re.sub(r"replicate[-_]do[-_]db\s*=\s*.*\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]ignore[-_]db\s*=\s*.*\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]do[-_]table\s*=\s*.*\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]ignore[-_]table\s*=\s*.*\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]wild[-_]do[-_]table\s*=\s*.*\n", "", mysql_conf)
        mysql_conf = re.sub(r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.*\n", "", mysql_conf)


        mysql_conf = re.sub(r"#\s*主从复制配置\n", "", mysql_conf)
        mysql_conf = re.sub(r"#\s*------\n", "", mysql_conf)

        slave_info[replicate_type] = replicate_type_value

        replicate_db = slave_info["replicate_db"]
        replicate_wild_table = slave_info["replicate_wild_table"]
        replicate_db_type = slave_info["replicate_db_type"]
        replicate_table_type = slave_info["replicate_table_type"]

        if len(replicate_db) == 0 and len(replicate_wild_table) == 0:
            return public.returnMsg(False, "您未选择同步的数据库！")

        # 设置同步数据库，表
        replicate_do_db = []
        replicate_ignore_db = []
        replicate_do_table = []
        replicate_ignore_table = []
        replicate_wild_do_table = []
        replicate_wild_ignore_table = []

        mysql_obj = panelMysql.panelMysql()

        # 通配符匹配
        if len(replicate_wild_table) != 0:
            if replicate_db_type == 0:
                replicate_wild_do_table = replicate_wild_table
            else:
                replicate_wild_ignore_table = replicate_wild_table

        # 选择数据库
        elif len(replicate_db) != 0:
            # 数据库
            if replicate_db_type == 0: # 同步数据库
                replicate_do_db = [db["name"] for db in replicate_db]
            else: # 不同步数据库
                db_list = [db["name"] for db in replicate_db]
                db_list.extend(["sys", "mysql", "information_schema", "performance_schema"])
                db_sql = "'" + "','".join(db_list) + "'"
                db_list = mysql_obj.query(f"select schema_name from information_schema.schemata where schema_name not in ({db_sql});")
                replicate_ignore_db = [db[0] for db in db_list]

            # 表
            for db in replicate_db:
                db_name = db["name"]

                tb_list = [tb["name"] for tb in db["table_list"]]
                if replicate_table_type == 0:
                    replicate_do_table.extend([f"{db_name}.{tb_name}" for tb_name in tb_list])
                else:
                    tb_sql = "'" + "','".join(tb_list) + "'"
                    tb_list = mysql_obj.query(f"select table_name from information_schema.tables where table_schema = '{db_name}' and table_name not in ({tb_sql});")
                    replicate_ignore_table.extend([f"{db_name}.{tb[0]}" for tb in tb_list])

        replicate_conf = "\n# 主从复制配置"
        if len(replicate_do_db) != 0:
            for db_name in replicate_do_db:
                replicate_conf += f"\nreplicate-do-db={db_name}"

        elif len(replicate_ignore_db) != 0:
            for db_name in replicate_ignore_db:
                replicate_conf += f"\nreplicate-ignore-db={db_name}"

        if len(replicate_do_table) != 0:
            for tb_name in replicate_do_table:
                replicate_conf += f"\nreplicate-do-table={tb_name}"

        elif len(replicate_ignore_table) != 0:
            for tb_name in replicate_ignore_table:
                replicate_conf += f"\nreplicate-ignore-table={tb_name}"

        if len(replicate_wild_do_table) != 0:
            for tb_name in replicate_wild_do_table:
                replicate_conf += f"\nreplicate-wild-do-table={tb_name}"

        elif len(replicate_wild_ignore_table) != 0:
            for tb_name in replicate_wild_ignore_table:
                replicate_conf += f"\nreplicate-wild-ignore-table={tb_name}"

        replicate_conf += "\n# ------"
        mysql_conf = re.sub("\[mysqld\]", "[mysqld]" + replicate_conf, mysql_conf)

        mysql_slave_obj.exec_shell_sql("stop slave;")
        # 保存配置
        resp = mysql_slave_obj.bt_api_obj.save_slave_conf(mysql_conf)
        if resp["status"] is False:
            return public.returnMsg(False, f"保存从库配置错误！{resp['msg']}")

        # 重启数据库
        mysql_slave_obj.bt_api_obj.control_mysqld_service()

        mysql_slave_obj.exec_shell_sql("start slave;")

        slave_info["addtime"] = time.time()
        self.set_slave_info(slave_ip, slave_info)
        return {"status": True, "msg": "设置成功!"}

    # 修改同步数据库
    def set_replicate_info(self, get):
        """
        :param get.slave_ip: 从库 ip
        :param get.replicate_db: 选择数据库
        :param get.replicate_wild_table: 使用通配符来控制需要复制的表
        :param get.replicate_db_type: # 数据库是否选择 0 选择 1 排除
        :param get.replicate_table_type: # 表是否选择 0 选择 1 排除
        :return:
        """

        # 校验参数
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")

        if not hasattr(get, "replicate_db") and not hasattr(get, "replicate_wild_table"):
            return public.returnMsg(False, "请选择您要同步的数据库或要排除的数据库！")
        if not hasattr(get, "replicate_db_type"):
            return public.returnMsg(False, f"缺少参数！ replicate_db_type")
        if not hasattr(get, "replicate_table_type"):
            return public.returnMsg(False, f"缺少参数！ replicate_table_type")

        if get.replicate_db_type not in ["0", "1"]:
            return public.returnMsg(False, f"参数错误！ replicate_db_type")
        if get.replicate_table_type not in ["0", "1"]:
            return public.returnMsg(False, f"参数错误！ replicate_table_type")

        slave_ip = get.slave_ip
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")
        # 停止主从复制
        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")
        resp = mysql_slave_obj.exec_shell_sql("stop slave", True)
        if resp["status"] is False:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库 {slave_ip} API接口的IP白名单")

        replicate_db = json.loads(getattr(get, "replicate_db", "[]"))
        replicate_wild_table = json.loads(getattr(get, "replicate_wild_table", "[]"))
        replicate_db_type = int(get.replicate_db_type)  # 0 选择 1 排除
        replicate_table_type = int(get.replicate_table_type)  # 0 选择 1 排除

        if len(replicate_db) == 0 and len(replicate_wild_table) == 0:
            return public.returnMsg(False, "请选择您要同步的数据库或要排除的数据库！")

        # 是否需要同步数据库
        is_sysc_database = False
        for db in replicate_db:
            if db.get("is_exist", False) is False or is_sysc_database is True:
                is_sysc_database = True
                break
            for tb in db["table_list"]:
                if tb.get("is_exist", False) is False:
                    is_sysc_database = True
                    break

        mysql_slave_obj = mysql_slave(slave_ip)
        result = mysql_slave_obj.bt_api_obj.get_config()
        if result.get("status") is False:
            return public.returnMsg(False, f"主库请求从库错误：{result.get('msg')}")

        for info in slave_info["replicate_status"]:
            if is_sysc_database is True and info["api"] in ["check_slave_database", "sync_database"]:
                info["status"] = False
                info["msg_list"] = []
                if slave_info.get("sync_database_task_id") is not None:
                    del slave_info["sync_database_task_id"]
            if info["api"] in ["check_slave_conf","start_replicate"]:
                info["status"] = False
                info["msg_list"] = []

        slave_info["replicate_db"] = replicate_db
        slave_info["replicate_wild_table"] = replicate_wild_table
        slave_info["replicate_db_type"] = replicate_db_type
        slave_info["replicate_table_type"] = replicate_table_type
        self.set_slave_info(slave_ip, slave_info)

        public.set_module_logs('msyql_replicate', 'set_replicate_info', 1)
        return {"status": True, "msg": "修改成功!正在配置同步信息！"}

    # 修复主从
    def repair_replicate(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 获取配置信息
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        if hasattr(get, "type"):
            if str(get.type) == "1":
                if slave_info.get("repair_replicate_task_id") is not None:
                    del slave_info["repair_replicate_task_id"]
                    self.set_slave_info(slave_ip, slave_info)

        # 后台执行
        task_obj = panelTask.bt_task()
        task_id = slave_info.get("repair_replicate_task_id")  # 获取任务id
        if task_id is not None:
            task = task_obj.get_task_find(task_id)
            if not task:
                del slave_info["repair_replicate_task_id"]
                self.set_slave_info(slave_ip, slave_info)
                return {"status": False, "msg": "任务不存在！请重新执行！"}

            # 后台执行日志
            repair_replicate_log = slave_info.get("repair_replicate_log", "")
            # 任务未完成
            if task.get("status", 0) != 1:
                # 文件不存在
                if not os.path.exists(repair_replicate_log):
                    return {"status": True, "msg": "初始化中，请稍后...！", "type": 2}
                export_log = public.readFile(repair_replicate_log)
                return {"status": True, "msg": export_log, "type": 2}

            # 任务完成
            if os.path.exists(repair_replicate_log):
                export_log = public.readFile(repair_replicate_log)
                # 导入成功 删除执行日志
                os.remove(repair_replicate_log)
                return {"status": True, "msg": export_log}

            del slave_info["repair_replicate_task_id"]
            self.set_slave_info(slave_ip, slave_info)

        slave_status_info = mysql_slave_obj.get_slave_status()
        if slave_status_info is False:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库 {slave_ip} API接口的IP白名单")
        if not slave_status_info:
            return public.returnMsg(False, f"请先启动主从然后再进行修复！")
        if slave_status_info.get("Slave_IO_Running") == "Yes" and slave_status_info.get("Slave_SQL_Running") == "Yes": # 开启状态
            return public.returnMsg(True, "当前主从状态正常!无需修复!")

        # 修复日志丢失
        Last_IO_Errno = slave_status_info['Last_IO_Errno']
        last_sql_errno  = slave_status_info['Last_SQL_Errno']

        api = None
        if last_sql_errno == "1062": # 主键冲突处理
            api = "repair_primary_key"
        if last_sql_errno == "1146": # 修复表丢失
            api = "fix_table_not_exist"
        if last_sql_errno == "1872":
            api = "reset_master_info"
        if api is not None:
            task_id = task_obj.create_task('修复主从', 0, f"btpython {execute_slave} --slave_ip={slave_ip} --api={api}")
            slave_info["repair_replicate_task_id"] = task_id  # 保存任务id
            self.set_slave_info(slave_ip, slave_info)
            return {"status": True, "msg": "正在修复请稍后!", "type": 1}
        return public.returnMsg(False, "目前无法修复，请将同步详情提交给宝塔官方人员")

    # 获取从库密钥
    def get_addr_key(self, get):
        # 校验参数
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, "缺少参数！ slave_ip")

        slave_ip = get.slave_ip
        slave_info = self.get_slave_info(slave_ip)
        return {"status": True ,"msg": "ok", "data" : {"panel_addr": slave_info.get("panel_addr"), "panel_key": slave_info.get("panel_key")}}

    # 修改从库密钥
    def set_slave_addr_key(self, get):
        # 校验参数
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, "缺少参数！ slave_ip")
        if not hasattr(get, "panel_addr"):
            return public.returnMsg(False, "缺少参数！ panel_addr")
        if not hasattr(get, "panel_key"):
            return public.returnMsg(False, "缺少参数！ panel_key")

        slave_ip = get.slave_ip

        addr_list = re.findall("https?://.*:\d+/?", get.panel_addr)
        if len(addr_list) == 0:
            return public.returnMsg(False, "请输入正确的面板地址！ 如：http://1.1.1.1/8888 http://www.bt.cn/8888")
        panel_addr = addr_list[0]
        panel_addr = panel_addr if str(panel_addr).endswith("/") else panel_addr + "/"

        ipv4_list = re.findall("https?://(.*):\d+", panel_addr)
        new_slave_ip = ipv4_list[0]
        panel_key = get.panel_key

        # 创建远程连接
        mysql_slave_obj = mysql_slave(new_slave_ip)
        mysql_slave_obj.bt_api_obj = bt_api(panel_addr, panel_key)
        result = mysql_slave_obj.bt_api_obj.get_config()
        if result.get("status") is False:
            return public.returnMsg(False, f"主库请求从库错误：{result.get('msg')}")

        slave_info = self.get_slave_info(slave_ip)

        slave_info["panel_addr"] = panel_addr
        slave_info["panel_key"] = panel_key
        self.del_slave_info(slave_ip)
        self.set_slave_info(new_slave_ip, slave_info)
        return public.returnMsg(True, "修改成功！")

    # 执行后台任务
    def execite_fun(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, "缺少参数！ slave_ip")
        if not hasattr(get, "api"):
            return public.returnMsg(False, "缺少参数！ api")
        mysql_slave_obj = mysql_slave(get.slave_ip)
        fun = getattr(mysql_slave_obj, get.api)
        fun()
# 主库类
class mysql_master():
    __is_firewalld = False
    __is_ufw = False
    mysqldump_complete_file = '/tmp/mysqldump.txt'

    def __init__(self):
        if os.path.exists('/usr/sbin/firewalld'): self.__is_firewalld = True
        if os.path.exists('/usr/sbin/ufw'): self.__is_ufw = True

    @classmethod
    def get_master_version(cls) -> str:
        """
            @name 获取数据库版本号
            @author zhwen<zhw@bt.cn>
            @return master_version str
        """
        master_version = panelMysql.panelMysql().query("select version()")[0][0].split(".")
        master_version = master_version[0] + "." + master_version[1]
        return master_version

    # 版本比较
    @classmethod
    def version_compare(cls, version_1: str, version_2: str) -> int:
        """
        版本比较
        :param version_1:
        :param version_2:
        :return: -1 version_1 < version_2
        :return: 0 version_1 == version_2
        :return: 1 version_1 > version_2
        """
        version_1 = version_1.split(".")
        version_2 = version_2.split(".")
        for v_1, v_2 in zip(version_1, version_2):
            v_1 = int(v_1)
            v_2 = int(v_2)
            if v_1 < v_2:
                return -1
            if v_1 > v_2:
                return 1
        return 0


    # 获取数据库端口号
    def get_master_port(self):
        """
            @name  获取数据库端口号
            @author zhwen<zhw@bt.cn>
            @return port int
        """
        try:
            port = panelMysql.panelMysql().query("show global variables like 'port'")[0][1]
            return int(port)
        except:
            return 3306

    # 检查防火墙
    def check_port(self, slave_ip: str, port: str):
        if not self.__is_firewalld and not self.__is_ufw: return True
        if self.__is_firewalld:
            check_status = public.ExecShell("firewall-cmd --state")[1]
            # 检查防火墙是否开启
            if check_status.find("not running")!=-1: return True
            a, e = public.ExecShell(f'firewall-cmd --list-all|grep -E "ports?.*{port}"')
            if a:
                return True
            a, e = public.ExecShell(f'firewall-cmd --list-all|grep -E "rule\s*family.*address=.?{slave_ip}.?.*{port}.*accept"')
            if a:
                return True
            return False
        else:
            check_status = public.ExecShell('ufw status')[0].split('\n')[0]
            if check_status.find('inactive')!=-1: return True
            a, e = public.ExecShell('ufw status|grep -E "{}/tcp\s*ALLOW\s*Anywhere"'.format(port))
            if a:
                return True
            a, e = public.ExecShell('ufw status|grep -E "{}/tcp\s*ALLOW\s*{}"'.format(port,slave_ip))
            if a:
                return True
            return False

    # 重载防火墙配置
    def firewall_reload(self):
        if self.__is_ufw:
            public.ExecShell('/usr/sbin/ufw reload')
        else:
            public.ExecShell('firewall-cmd --reload')

    # 添加防火墙放行接口
    def add_port_release(self, slave_ip: str, port: str):
        if self.__is_ufw:
            public.ExecShell(f"ufw allow proto tcp from {slave_ip} to any port {port}")
        else:
            public.ExecShell(f"firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=\'{slave_ip}\' port protocol=\'tcp\' port=\'{port}\' accept'")
        self.firewall_reload()

    # 删除防火墙放行端口
    def delete_port_release(self, slave_ip: str):
        port = self.get_master_port()
        if self.__is_ufw:
            public.ExecShell(f"ufw delete allow proto tcp from {slave_ip} to any port {port}")
        else:
            public.ExecShell(f"firewall-cmd --permanent --remove-rich-rule='rule family=ipv4 source address=\'{slave_ip}\' port protocol=\'tcp\' port=\'{port}\' accept'")
        self.firewall_reload()

    # 获取远程数据库读写状态
    def get_master_readonly(self):
        data = panelMysql.panelMysql().query('show global variables like "read_only"')
        read_only = data[0][1]
        if read_only == "ON":
            return True
        return False

    # 设置从库只读
    def set_master_readonly_temp(self, status: int):
        try:
            if self.get_master_readonly() is True and status == 0:  # 允许写
                panelMysql.panelMysql().query("set global read_only=0;")
            elif self.get_master_readonly() is False and status == 1:  # 只读
                panelMysql.panelMysql().query("set global read_only=1;")
        except Exception as err:
            return err

    # 获取主库gtid
    def get_master_gtid(self):
        data = panelMysql.panelMysql().query("show master status;")
        # [['mysql-bin.000002', 156, '', '', 'cdec3c0b-dff4-11ed-8f11-269cf8d8a9be:1-5']]
        return data[0][4] if data[0][4] else None

    # 获取主库 server-id
    def get_master_server_id(self):
        conf = public.readFile(my_cnf)
        server_obj = re.search(r"server-id\s*=\s*.+\n", conf)
        if server_obj:
            server_id = server_obj.group()
            server_id = server_id.split("=")[1].strip()
            return server_id
        else:
            return False

    # 设置主库 server-id
    def set_master_server_id(self, server_id: str):
        try:
            conf = public.readFile(my_cnf)
            conf = re.sub("server-id\s*=\s*\d+\n", "", conf)
            conf = re.sub("\[mysqld\]", "[mysqld]" + f"\nserver-id={server_id}", conf)
            public.writeFile(my_cnf,conf)
            return True
        except Exception as err:
            return err

    # 获取主库gtid状态
    def get_master_gtid_status(self):
        gtid_mode = panelMysql.panelMysql().query("show global variables like 'gtid_mode'")[0]
        if 'ON' in gtid_mode:
            return True
        return False

    # 设置主库的gtid支持
    def set_master_gtid_conf(self):
        gtid_conf = """
log-slave-updates=on
enforce-gtid-consistency=on
gtid-mode=on"""
        try:
            conf = public.readFile(my_cnf)
            conf = re.sub("log-slave-updates\s*=\s*.*\n", "", conf)
            conf = re.sub("enforce-gtid-consistency\s*=\s*.*\n", "", conf)
            conf = re.sub("gtid-mode\s*=\s*.*\n", "", conf)
            conf = re.sub("\[mysqld\]", "[mysqld]" + gtid_conf, conf)
            public.writeFile(my_cnf,conf)
            return True
        except Exception as err:
            return err

    # 检查数据库二进制日志是否已经开启
    def get_master_binlog(self):
        binlog_status = panelMysql.panelMysql().query("show variables like 'log_bin'")[0]
        if 'ON' in binlog_status:
            return True
        return False

    # 设置主库binlog
    def set_master_binlog(self):
        bin_log = """
log-bin=mysql-bin
binlog_format=mixed"""
        try:
            conf = public.readFile(my_cnf)
            if not re.search('\n\s*#\s*log-bin\s*=\s*mysql-bin',conf):
                conf = re.sub("log-bin\s*=\s*.+\n", "", conf)
                conf = re.sub("binlog_format\s*=\s*.+\n", "", conf)
                conf = re.sub("\[mysqld\]", "[mysqld]" + bin_log, conf)
            else:
                conf = conf.replace('#log-bin=mysql-bin', 'log-bin=mysql-bin')
                conf = conf.replace('#binlog_format=mixed', 'binlog_format=mixed')
            public.writeFile(my_cnf, conf)
            return True
        except Exception as err:
            return err


# 从库类
class mysql_slave:

    def __init__(self, slave_ip: str):
        self.slave_ip = slave_ip
        self.bt_api_obj = self.get_bt_api(slave_ip)
        self.root_password = None

    @classmethod
    # 获取 api 对象
    def get_bt_api(cls, slave_ip: str):
        slave = mysql_replicate_main.get_slave_info(slave_ip)
        if slave is None: return None
        return bt_api(slave["panel_addr"], slave["panel_key"])

    # 在从库执行sql语句:
    def exec_shell_sql(self, sql: str, is_resp: bool = False):
        get_time = 2  # 超时间
        if self.bt_api_obj is None:
            return False

        if self.root_password is None:
            self.root_password = self.bt_api_obj.get_root_passowrd()

        sql = sql.replace("'",'"')
        shell = f"export MYSQL_PWD={self.root_password} && /usr/bin/mysql -uroot --default-character-set=utf8 -e 'SET sql_notes = 0;{sql}'"
        resp = self.bt_api_obj.slave_execute_command(shell, "/tmp")
        start_time = int(time.time()) + get_time
        while resp["status"] is False and not resp["msg"] and int(time.time()) < start_time:
            resp = self.bt_api_obj.get_execute_msg()
            if resp["msg"]:
                break
            time.sleep(0.5)

        if is_resp is True:
            return resp
        if resp["status"] is False:
            # public.print_log(f"err:{resp['msg']}")
            return resp["msg"]
        return resp["msg"]

    def get_slave_version(self):
        """
            @name 获取数据库版本号
            @author zhwen<zhw@bt.cn>
            @return master_version str
        """

        slave_version = self.exec_shell_sql("select version()")
        if slave_version.find("\n") != -1:
            slave_version = str(slave_version).split("\n")[-1]
        slave_version = str(slave_version).lstrip("version()").strip()
        return slave_version

    # 同步数据库
    def sync_slave_database(self):

        slave_info = mysql_replicate_main.get_slave_info(self.slave_ip)
        if slave_info is None:
            return "主从信息不存在！"
        if self.bt_api_obj is None:
            return "主从信息不存在"

        replicate_db = slave_info["replicate_db"]
        replicate_wild_table = slave_info["replicate_wild_table"]

        # 同步日志
        sync_database_log = slave_info.get("sync_database_log")
        if sync_database_log is None:
            sync_database_log = f"{logs_dir}/mysql_replicate_export_{int(time.time() * 100_0000)}.log"
            slave_info["sync_database_log"] = sync_database_log
            mysql_replicate_main.set_slave_info(self.slave_ip, slave_info)

        public.writeFile(sync_database_log, f"1|开始同步数据库", "w")


        if len(replicate_wild_table) != 0:
            pass

        elif len(replicate_db) == 0:
            public.writeFile(sync_database_log, f"\n0|您未选择同步的数据库", "a")

        insert_num = 1000 # 每次插入条数
        total_row = 0 # 总条数
        executed_total_row = 0 # 操作条数
        start_time = time.time()

        root_password = self.bt_api_obj.get_root_passowrd()
        execute_url = self.bt_api_obj.BT_PANEL + '/files?action=ExecShell'

        self.bt_api_obj.control_mysqld_service()

        public.writeFile(sync_database_log, f"\n1|正在计算需要同步的总条数", "a")
        for db in replicate_db:
            for tb in db["table_list"]:
                if tb.get("is_exist", False) is True:  # 跳过已存在的
                    continue

                tb_row = panelMysql.panelMysql().query(f"select count(*) from `{db['name']}`.`{tb['name']}`;")[0][0]
                tb["row"] = tb_row
                total_row += tb_row

        for db in replicate_db:
            db_name = db["name"]

            if db.get("is_exist", False) is False:  # 创建未存在的数据库
                # 创建数据库
                public.writeFile(sync_database_log, f"\n1|正在创建数据库：{db_name}", "a")
                resp = self.bt_api_obj.create_database(db_name, new_password())
                if resp["status"] is False:  # 创建失败
                    return public.writeFile(sync_database_log, f"\n0|{db_name} {resp['msg']}", "a")

            for tb in db["table_list"]:
                if tb.get("is_exist", False) is True:  # 跳过已存在的
                    continue

                start_sync_table_time = time.time()

                tb_name = tb["name"]
                # public.print_log(f">>db_name:{db_name}.{tb_name}")
                create_sql = panelMysql.panelMysql().query(f"show create table `{db_name}`.`{tb_name}`;")
                if not isinstance(create_sql, list):
                    return public.writeFile(sync_database_log, f"0|主库数据库：{db_name},表：{tb_name}不存在！")

                public.writeFile(sync_database_log, f"\n1|正在创建表：{db_name}.{tb_name}", "a")
                create_sql = create_sql[0][1]

                # 创建表
                resp = self.exec_shell_sql(f"use `{db_name}`;{create_sql}", is_resp=True)
                if resp["status"] is False or resp['msg'].find("ERROR") != -1:  # 创建失败
                    return public.writeFile(sync_database_log, f"\n0|{db_name} {resp['msg']}", "a")

                table_row_num = tb["row"]
                row_num = copy.deepcopy(table_row_num)

                executed_num = 0
                insert_row_num = insert_num if row_num > insert_num else row_num
                while row_num > 0:
                    start_sync_time = time.time()
                    data_list = panelMysql.panelMysql().query(f"select * from `{db_name}`.`{tb_name}` limit {executed_num},{insert_row_num};")

                    # 插入从库数据库
                    # 组织数据
                    create_list = []
                    for data in data_list:
                        t_data = []
                        for value in data:
                            value = str(value) if isinstance(value, int) else f'"{value}"'
                            t_data.append(value)
                        create_list.append("(" + ",".join(t_data) + ")")
                    sql = f"""insert into `{db_name}`.`{tb_name}` values {','.join(create_list)};"""
                    # 执行
                    shell = f"export MYSQL_PWD={root_password} && /usr/bin/mysql -uroot --default-character-set=utf8 -e 'SET sql_notes = 0;{sql}'"
                    pdata = self.bt_api_obj.get_key_data()
                    pdata["shell"] = shell
                    pdata["path"] = "/tmp"
                    self.bt_api_obj.http_post_cookie(execute_url, pdata)

                    row_num -= insert_row_num
                    executed_num += insert_row_num
                    executed_total_row += insert_row_num

                    end_sync_time = time.time() - start_sync_time
                    residue_time = round((total_row - executed_total_row) / (insert_row_num / end_sync_time))
                    time_second = round(residue_time % 60, 2)
                    time_minute = f"{int(residue_time // 60 % 60)}分" if int(residue_time // 60 % 60) != 0 else ''
                    time_hour = f"{int(residue_time // 60 // 60 % 60)}时" if int(residue_time // 60 // 60 % 60) != 0 else ''
                    time_day = f"{int(residue_time // 60 // 60 // 60 % 24)}天" if int(residue_time // 60 // 60 // 60 % 24) != 0 else ''
                    public.writeFile(sync_database_log, f"\n1|总进度：{executed_total_row}/{total_row}，预计剩余：{time_day}{time_hour}{time_minute}{time_second}秒，正在同步：{db_name}.{tb_name}", "a")
                    if row_num < insert_row_num and row_num > 0: # 是否到末尾
                        insert_row_num = row_num

                end_sync_table_time = time.time() - start_sync_table_time
                time_second = round(end_sync_table_time % 60, 2)
                time_minute = f"{int(end_sync_table_time // 60 % 60)}分" if int(end_sync_table_time // 60 % 60) != 0 else ''
                time_hour = f"{int(end_sync_table_time // 60 // 60 % 60)}时" if int(end_sync_table_time // 60 // 60 % 60) != 0 else ''
                time_day = f"{int(end_sync_table_time // 60 // 60 // 60 % 24)}天" if int(end_sync_table_time // 60 // 60 // 60 % 24) != 0 else ''
                public.writeFile(sync_database_log, f"\n2|已同步：{db_name}.{tb_name}，已同步记录：{executed_total_row}，耗时：{time_day}{time_hour}{time_minute}{time_second}秒", "a")

        end_time = time.time() - start_time
        time_second = round(end_time % 60, 2)
        time_minute = f"{int(end_time // 60 % 60)}分" if int(end_time // 60 % 60) != 0 else ''
        time_hour = f"{int(end_time // 60 // 60 % 60)}时" if int(end_time // 60 // 60 % 60) != 0 else ''
        time_day = f"{int(end_time // 60 // 60 // 60 % 24)}天" if int(end_time // 60 // 60 // 60 % 24) != 0 else ''
        public.writeFile(sync_database_log, f"\n2|共同步记录：{executed_total_row}，总耗时：{time_day}{time_hour}{time_minute}{time_second}秒", "a")

        data_list = panelMysql.panelMysql().query("show master status;")
        master_log_file = data_list[0][0]
        master_log_pos = data_list[0][1]
        executed_gtid_set = data_list[0][4]
        if executed_gtid_set.find(",") != -1:
            executed_gtid_set = str(executed_gtid_set).split(",")[0]
        uuid, num = str(executed_gtid_set).split(":")
        num = str(num).split("-")[-1]
        slave_info["master_log_file"] = master_log_file
        slave_info["master_log_pos"] = master_log_pos
        slave_info["executed_gtid_set"] = f"{uuid}:{num}"
        mysql_replicate_main.set_slave_info(self.slave_ip, slave_info)

    # 获取从库 server-id
    def get_slave_server_id(self):
        resp = self.bt_api_obj.get_slave_conf()
        conf = resp["data"]
        server_obj = re.search(r"server-id\s*=\s*\d+\n", conf)
        if server_obj:
            server_id = server_obj.group()
            server_id = server_id.split("=")[1].strip()
            return server_id
        else:
            return False

    # 设置从库 server-id
    def set_slave_server_id(self, server_id: int):
        try:
            resp = self.bt_api_obj.get_slave_conf()
            conf = resp["data"]
            conf = re.sub("server-id\s*=\s*\d+\n", "", conf)
            conf = re.sub("\[mysqld\]", "[mysqld]" + f"\nserver-id={server_id}", conf)
            self.bt_api_obj.save_slave_conf(conf)
            return True
        except Exception as err:
            return err

    # 获取远程数据库读写状态
    def get_mysql_readonly(self):
        resp = self.exec_shell_sql('show global variables like "read_only"')
        if "\tON" in resp:
            return True
        return False

    # 设置从库只读
    def set_mysql_readonly(self, status: int):
        try:
            if self.get_mysql_readonly() is True and status == 0: # 允许所有用户写
                self.exec_shell_sql("set global read_only=0")
            elif self.get_mysql_readonly() is False and status == 1: # 只读
                self.exec_shell_sql("set global read_only=1")
        except Exception as err:
            return err

    # 获取从库状态
    def get_slave_status(self) -> [dict, bool]:
        slave_status_info = {}
        resp = self.exec_shell_sql("show slave status;", True)
        if resp["status"] is False:
            return False
        if not resp["msg"]:
            return {}

        slave_status = resp["msg"]
        if str(slave_status).find("\n") == -1:
            return {}
        field_list, value_list = slave_status.split("\n")
        field_list = field_list.split("\t")
        value_list = value_list.split("\t")
        if len(field_list) > len(value_list):
            while len(field_list) - len(value_list):
                value_list.append("")

        for i in range(len(field_list)):
            name, value = field_list[i], value_list[i]
            slave_status_info[name] = value
        return slave_status_info


    # 修复主键错误
    def repair_primary_key(self):
        slave_info = mysql_replicate_main.get_slave_info(self.slave_ip)
        if slave_info is None:
            return "主从信息不存在！"

        # 同步日志
        repair_replicate_log = slave_info.get("repair_replicate_log")
        if repair_replicate_log is None:
            repair_replicate_log = f"{logs_dir}/repair_replicate_{int(time.time() * 100_0000)}.log"
            slave_info["repair_replicate_log"] = repair_replicate_log
            mysql_replicate_main.set_slave_info(self.slave_ip, slave_info)

        public.writeFile(repair_replicate_log, f"检测到主从错误:从库【主键冲突】", "w")

        slave_status_info = self.get_slave_status()
        if slave_status_info is False or not slave_status_info:
            return public.writeFile(repair_replicate_log, f"\n请求从库错误！获取从库状态失败!", "a")
        last_sql_error = slave_status_info['Last_SQL_Error']
        while True:
            primary = re.search("entry\s'(\w+)'", last_sql_error).group(1)
            db_name = re.search("database:\s'(\w*)'", last_sql_error).group(1)
            tb_name = re.search(f"(insert|INSERT)\s+(into|INTO)\s+`{db_name}`\.?`([\w\_\-\.]+)`", last_sql_error)
            if not tb_name:
                tb_name = re.search(f"(insert|INSERT)\s+(into|INTO)\s+`([\w\_\-\.]+)`", last_sql_error).group(3)
            else:
                tb_name = tb_name.group(3)
            data_list = panelMysql.panelMysql().query(f"desc `{db_name}`.`{tb_name}`")
            for i in data_list:
                if "PRI" in i:
                    prikey = i[0]

            public.writeFile(repair_replicate_log, f"\n正在删除从库主键:{db_name}.{tb_name}表,删除记录:{prikey}={primary}", "a")
            self.exec_shell_sql(f"delete from `{db_name}`.`{tb_name}` where {prikey}={primary};")
            self.exec_shell_sql("stop slave")
            self.exec_shell_sql("start slave")
            time.sleep(0.5)
            slave_status_info = self.get_slave_status()
            if slave_status_info is False or not slave_status_info:
                slave_status_info = self.get_slave_status()
                if slave_status_info is False or not slave_status_info:
                    return public.writeFile(repair_replicate_log, f"\n请求从库错误！获取从库状态失败请重试!", "a")
            last_sql_errno = slave_status_info['Last_SQL_Errno']
            if last_sql_errno != "1062":
                return public.writeFile(repair_replicate_log, f"\n修复成功!", "a")

            last_sql_error_new = slave_status_info['Last_SQL_Error']
            if last_sql_error == last_sql_error_new:
                return public.writeFile(repair_replicate_log, f"\n修复失败!", "a")
            last_sql_error = last_sql_error_new

    # 修复表丢失
    def fix_table_not_exist(self):
        """
        :param status:mysql的同步状态
        :param slave_ip: 192.168.1.41 从库IP
        :return:
        """
        slave_info = mysql_replicate_main.get_slave_info(self.slave_ip)
        if slave_info is None:
            return "主从信息不存在！"

        # 同步日志
        repair_replicate_log = slave_info.get("repair_replicate_log")
        if repair_replicate_log is None:
            repair_replicate_log = f"{logs_dir}/repair_replicate_{int(time.time() * 100_0000)}.log"
            slave_info["repair_replicate_log"] = repair_replicate_log
            mysql_replicate_main.set_slave_info(self.slave_ip, slave_info)

        public.writeFile(repair_replicate_log, f"检测到主从错误:从库【表丢失】,开始同步丢失表到从库", "w")

        slave_status_info = self.get_slave_status()
        if slave_status_info is False or not slave_status_info:
            return public.writeFile(repair_replicate_log, f"\n请求从库错误!获取从库状态失败!", "a")
        last_sql_error = slave_status_info['Last_SQL_Error']
        err_list = re.findall("Error\s*'Table\s*'(.*)'\s*doesn't\s*exist'\s*on\s*query", last_sql_error)
        if len(err_list) == 0:
            return public.writeFile(repair_replicate_log, f"\n从库有数据表丢失但没有匹配到，请检查同步详情！将丢失的数据表手动导入到从库或重做主从复制", "a")
        root_password = self.bt_api_obj.get_root_passowrd()
        execute_url = self.bt_api_obj.BT_PANEL + '/files?action=ExecShell'

        start_time = time.time()
        total_row = 0
        insert_num = 1000  # 每次插入条数
        for table_name in err_list:
            db_name, tb_name = table_name.split('.')

            create_sql = panelMysql.panelMysql().query(f"show create table `{db_name}`.`{tb_name}`;")
            if not isinstance(create_sql, list): continue
            public.writeFile(repair_replicate_log, f"\n正在创建表：{db_name}.{tb_name}", "a")
            create_sql = create_sql[0][1]

            # 创建表
            resp = self.exec_shell_sql(f"use `{db_name}`;{create_sql}", is_resp=True)
            if resp["status"] is False or resp['msg'].find("ERROR") != -1:  # 创建失败
                return public.writeFile(repair_replicate_log, f"\n{db_name} {resp['msg']}", "a")

            table_row_num = panelMysql.panelMysql().query(f"select count(*) from `{db_name}`.`{tb_name}`;")[0][0]
            row_num = copy.deepcopy(table_row_num)

            executed_num = 0
            insert_row_num = insert_num if row_num > insert_num else row_num
            while row_num > 0:
                start_sync_time = time.time()
                data_list = panelMysql.panelMysql().query(f"select * from `{db_name}`.`{tb_name}` limit {executed_num},{insert_row_num} ;")

                # 插入从库数据库
                # 组织数据
                create_list = []
                for data in data_list:
                    t_data = []
                    for value in data:
                        value = f"{value}" if isinstance(value, int) else f'"{value}"'
                        t_data.append(value)
                    create_list.append("(" + ",".join(t_data) + ")")
                sql = f"""insert into `{db_name}`.`{tb_name}` values {','.join(create_list)};"""
                # 执行
                shell = f"export MYSQL_PWD={root_password} && /usr/bin/mysql -uroot --default-character-set=utf8 -e 'SET sql_notes = 0;{sql}'"
                pdata = self.bt_api_obj.get_key_data()
                pdata["shell"] = shell
                pdata["path"] = "/tmp"
                self.bt_api_obj.http_post_cookie(execute_url, pdata)

                row_num -= insert_row_num
                executed_num += insert_row_num

                end_sync_time = time.time() - start_sync_time
                residue_time = round(row_num / (insert_row_num / end_sync_time))
                time_second = round(residue_time % 60, 2)
                time_minute = f"{int(residue_time // 60)}分" if int(residue_time // 60) != 0 else ''
                time_hour = f"{int(residue_time // 60 // 60)}时" if int(residue_time // 60 // 60) != 0 else ''
                public.writeFile(repair_replicate_log, f"\n正在同步：{db_name}.{tb_name}，已同步记录：{executed_num}/{table_row_num}，预计剩余：{time_hour}{time_minute}{time_second}秒", "a")
                if row_num < insert_row_num and row_num > 0:  # 是否到末尾
                    insert_row_num = row_num

        end_time = time.time() - start_time
        time_second = round(end_time % 60, 2)
        time_minute = f"{int(end_time // 60)}分" if int(end_time // 60) != 0 else ''
        time_hour = f"{int(end_time // 60 // 60)}时" if int(end_time // 60 // 60) != 0 else ''
        public.writeFile(repair_replicate_log, f"\n共同步记录：{total_row}，总耗时：{time_hour}{time_minute}{time_second}秒", "a")

        self.exec_shell_sql("stop slave")
        self.exec_shell_sql("start slave")
        slave_status_info = self.get_slave_status()
        if slave_status_info is False or not slave_status_info:
            return public.writeFile(repair_replicate_log, f"\n请求从库错误!获取从库状态失败", "a")
        if str(slave_status_info['Last_SQL_Errno']) != '1146':
            return public.writeFile(repair_replicate_log, f"修复成功", "a")
        return public.writeFile(repair_replicate_log, f"修复失败!", "a")

    # 重置 mysql 的同步状态
    def reset_master_info(self):
        """
        :param status:mysql的同步状态
        :return:
        """
        slave_status_info = self.get_slave_status()
        last_sql_error = slave_status_info['Last_SQL_Errno']
        rep = "Slave\s*failed\s*to\s*initialize\s*relay\s*log\s*info\s*structure\s*from\s*the\s*repository"
        res = re.search(rep, last_sql_error)
        if not res:
            return public.returnMsg(False, "检查到数据库同步配置丢失，但无法匹配详情")

        master = mysql_replicate_main.get_conf()["master"]
        create_replicate_sql = f"""
            CHANGE MASTER TO
            MASTER_HOST="{master['master_ip']}",
            MASTER_USER="{master['slave_user']}",
            MASTER_PASSWORD="{master['password']}",
            MASTER_PORT={master['master_port']},
            MASTER_AUTO_POSITION=1;
        """
        self.exec_shell_sql(create_replicate_sql)
        slave_status_info = self.get_slave_status()
        if slave_status_info['Last_SQL_Errno'] != 1872:
            return public.returnMsg(True, "修复成功！")
        return public.returnMsg(True, "修复失败！")

# 请求从库
class bt_api():

    def __init__(self, panel_addr: str, panel_key: str):
        self.BT_PANEL = panel_addr if str(panel_addr).endswith("/") else panel_addr + "/"
        self.BT_KEY = panel_key

        import requests
        self._REQUESTS = None
        if not self._REQUESTS:
            self._REQUESTS = requests.session()

    # 计算MD5
    def __get_md5(self, s:str):
        m = hashlib.md5() # type:hashlib.md5
        m.update(s.encode('utf-8'))
        return m.hexdigest() # type:str

    # 构造带有签名的关联数组
    def get_key_data(self):
        now_time = int(time.time())
        pdata = {
            'request_token': self.__get_md5(str(now_time) + '' + self.__get_md5(self.BT_KEY)),
            'request_time': now_time
        }
        return pdata # type: dict

    # 发送POST请求并保存Cookie
    # @url 被请求的URL地址(必需)
    # @data POST参数，可以是字符串或字典(必需)
    # @timeout 超时时间默认1800秒
    # return string
    def http_post_cookie(self, url:str, pdata: dict, timeout: int=1800):
        try:
            res = self._REQUESTS.post(url, params=self.get_key_data(), data=pdata, timeout=timeout, verify=False)
            return res.text
        except Exception as ex:
            ex = str(ex)
            if ex.find('Max retries exceeded with') != -1:
                return public.returnJson(False, '连接服务器失败!')
            if ex.find('Read timed out') != -1 or ex.find('Connection aborted') != -1:
                return public.returnJson(False, '连接超时!')
            return public.returnJson(False, '连接服务器失败!')

    # 获取从库配置信息
    def get_config(self):
        try:
            info_url = self.BT_PANEL + 'config?action=get_config'
            info_data = self.get_key_data()
            result = self.http_post_cookie(info_url, info_data)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 获取从库root密码
    def get_root_passowrd(self):
        try:
            info_url = self.BT_PANEL + 'data?action=getKey'
            info_data = self.get_key_data()
            info_data['table'] = "config"
            info_data['key'] = "mysql_root"
            info_data['id'] = "1"
            result = self.http_post_cookie(info_url, info_data)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 从库执行 shell
    def slave_execute_command(self,shell: str, path: str='/tmp') -> dict:
        url = self.BT_PANEL+'/files?action=ExecShell'
        pdata = self.get_key_data()
        pdata["shell"] = shell
        pdata["path"] = path
        self.http_post_cookie(url, pdata)
        return self.get_execute_msg()

    # 获取 shell 执行结果
    def get_execute_msg(self) -> dict:
        try:
            url = self.BT_PANEL+'/files?action=GetExecShellMsg'
            pdata = self.get_key_data()
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return {"status": False, "msg": f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单"}

    # 获取从库配置文件
    def get_slave_conf(self, path: str = None) -> dict:
        try:
            url = self.BT_PANEL + '/files?action=GetFileBody'
            pdata = self.get_key_data()
            pdata['path'] = '/etc/my.cnf'
            if path:
                pdata['path'] = path
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 保存从库配置文件
    def save_slave_conf(self, content: str, path: str = None) -> dict:
        try:
            url = self.BT_PANEL + '/files?action=SaveFileBody'
            pdata = self.get_key_data()
            pdata['path'] = '/etc/my.cnf'
            if path:
                pdata['path'] = path
            pdata['encoding'] = 'utf-8'
            pdata['data'] = content
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 删除目录
    def delete_dir(self, path: str) -> dict:
        try:
            url = self.BT_PANEL + '/files?action=DeleteDir'
            pdata = self.get_key_data()
            pdata["path"] = path
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 删除文件
    def delete_file(self, path: str) -> dict:
        try:
            url = self.BT_PANEL + '/files?action=DeleteFile'
            pdata = self.get_key_data()
            pdata["path"] = path
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 解压文件前判断文件是否存在
    def upload_file_exists(self, path: str) -> dict:
        try:
            url = self.BT_PANEL + '/files?action=upload_file_exists'
            pdata = self.get_key_data()
            pdata["filename"] = path
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 解压文件
    def unzip_file(self, sfile: str, dfile: str, zip_type: str, coding: str="UTF-8") -> dict:
        try:
            url = self.BT_PANEL + '/files?action=UnZip'
            pdata = self.get_key_data()
            pdata["sfile"] = sfile
            pdata["dfile"] = dfile
            pdata["type"] = zip_type
            pdata["coding"] = coding
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 创建数据库
    def create_database(self, db_name: str, password: str) -> dict:
        try:
            url = self.BT_PANEL + '/database?action=AddDatabase'
            pdata = {
                "name": db_name,
                "codeing": "utf8mb4",
                "db_user": db_name,
                "password": password,
                "dataAccess": "127.0.0.1",
                "sid": "0",
                "address": "127.0.0.1",
                "ps": "主从复制从库",
                "dtype": "MySQL",
            }
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # mysql导入sql数据文件
    def import_sql(self, path: str, name: str) -> dict:
        try:
            url = self.BT_PANEL + '/database?action=InputSql'
            pdata = {
                "file": path,
                "name": name,
            }
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 重启数据库
    def control_mysqld_service(self,type=None):
        try:
            url = self.BT_PANEL+'/system?action=ServiceAdmin'
            p_data = self.get_key_data()
            p_data["name"] = 'mysqld'
            p_data["type"] = 'restart'
            if type:
                p_data["type"] = type
            result = self.http_post_cookie(url, p_data)
            return result
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")