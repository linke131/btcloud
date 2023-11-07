# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 王佳函
# +-------------------------------------------------------------------
import copy
import datetime
# --------------------------------
# Mysql主从复制
# --------------------------------

import typing
import os, sys, hashlib, time, json, re
import public
import db_mysql
import panelMysql
import panelTask

sys.path.append("class/")
os.chdir("/www/server/panel")

backup_path = '/www/backup/database'
my_cnf = '/etc/my.cnf'
plugin_dir = "/www/server/panel/plugin/mysql_replicate"
plugin_conf_file = plugin_dir+"/config.json"
logs_file = "/tmp/mysql_replicate.log"

# CHANGE MASTER TO
# MASTER_HOST='192.168.69.148',
# MASTER_USER='Dv1yKyHw',
# MASTER_PASSWORD='1TcXptRXWI7J',
# MASTER_AUTO_POSITION=1

# change master to
# master_host='192.168.69.148',
# master_user='Dv1yKyHw',
# master_password='1TcXptRXWI7J',
# master_log_file='mysql-bin.000019',
# master_log_pos=196;

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
            "msg": "【主从】数据库一致性检查",
            "api": "check_slave_database",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【主库】数据库导出",
            "api": "export_dump_database",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【主库】上传数据库文件到【从库】",
            "api": "upload_database_file",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【从库】导入数据库",
            "api": "import_dump_database",
            "msg_list": [],
            "status": False,
        },
        {
            "msg": "【主库】配置信息检查",
            "api": "check_master_conf",
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
            "msg": "【主库】主从复制用户创建",
            "api": "create_replicate_user",
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
        self.init()

    def init(self):
        try:
            mysql_obj = panelMysql.panelMysql()

            # 初始化配置文件
            conf = self.__get_conf()
            if isinstance(conf["slave"], dict):
                return

            public.print_log(f"更新配置文件！")

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
            public.print_log(f">>err:{err}")
            return

    # 获取配置文件
    @classmethod
    def __get_conf(cls):
        conf = public.readFile(plugin_conf_file)
        try:
            conf = json.loads(conf)
        except:
            conf = {}
        return conf

    # 获取主从信息
    @classmethod
    def get_slave_info(cls, slave_ip: str):
        conf = cls.__get_conf()
        return conf["slave"].get(slave_ip) # type: dict,None

    # 修改主从信息
    @classmethod
    def set_slave_info(cls, slave_ip:str, slave_info: str):
        conf = cls.__get_conf()
        conf["slave"][slave_ip] = slave_info
        public.writeFile(plugin_conf_file, json.dumps(conf))
        return True

    # 删除主从信息
    @classmethod
    def del_slave_info(cls, slave_ip: str):
        conf = cls.__get_conf()
        if conf['slave'].get(slave_ip):
            del conf['slave'][slave_ip]
            public.writeFile(plugin_conf_file, json.dumps(conf))
        return True

    # 设置主从同步状态
    @classmethod
    def set_slave_satuts(cls, slave_ip: str, method: str, status: bool):
        conf = cls.__get_conf()
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
        conf = cls.__get_conf()
        slave = conf['slave'].get(slave_ip)
        if slave is not None:
            for info in slave["replicate_status"]:
                if info["api"] == method:
                    return info.get("status", False)
        return False


    # 获取所有主从信息
    def get_slave_list(self, get):
        self.init()
        slave_list = []
        conf = self.__get_conf()

        for slave_ip, slave_info in conf['slave'].items():
            # 获取从库读写状态
            mysql_slave_obj = mysql_slave(slave_ip)
            if mysql_slave_obj.bt_api_obj is None: continue
            slave_readonly = mysql_slave_obj.get_mysql_readonly()

            status = 0
            slave_status = 3
            config_status = True
            for info in slave_info["replicate_status"]:
                if info["api"] == "start_replicate": continue
                if info["status"] == False:
                    config_status = False
                    break
            if config_status is True:
                # 获取主从状态
                resp = mysql_slave_obj.exec_shell_sql("show slave status\G;", True)
                slave_status_data = resp["msg"]
                if resp["status"] is False:
                    status = 2
                elif re.search("Slave_IO_Running: Yes", slave_status_data, re.I) and re.search("Slave_SQL_Running: Yes", slave_status_data, re.I):
                    status = 1
                    slave_status = 1
                elif re.search("Slave_IO_Running: Connecting", slave_status_data, re.I) or re.search("Slave_SQL_Running: Connecting", slave_status_data, re.I):
                    status = 1
                    slave_status = 2
                else:
                    status = 0
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
            tb_list = mysql_obj.query(f"SELECT table_name, data_length FROM information_schema.TABLES WHERE table_schema = '{db_name}';")
            # tb_list = mysql_obj.query(f"show tables from `{db_name}`;")
            for tb in tb_list:
                db_size += tb[1]
                table = {
                    "name": tb[0],
                    "size": tb[1],
                }
                table_list.append(table)
            table_list = sorted(table_list, key=lambda tb: tb['size'], reverse=True)
            database = {
                "name": db_name,
                "size": db_size,
                "table_list": table_list
            }
            database_list.append(database)
        database_list = sorted(database_list, key=lambda db: db['size'], reverse=True)
        return {"status": True, "data": database_list}

    # 获取主从数据库表信息
    def get_table(self, get):
        """
        :param get.db_name: 数据库名称
        :return:
        """
        if not hasattr(get, "db_name"):
            return public.returnMsg(False, "缺少参数! db_name")
        db_name = get.db_name

        mysql_obj = panelMysql.panelMysql()

        db_size = 0
        table_list = []
        tb_list = mysql_obj.query(f"SELECT table_name, data_length FROM information_schema.TABLES WHERE table_schema = '{db_name}';")
        for tb in tb_list:
            db_size += tb[1]
            table = {
                "name": tb[0],
                "size": tb[1],
            }
            table_list.append(table)
        return {"status": True, "data": table_list, "size": db_size}

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

        # rep_ip = "^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$"
        # rep_ipv6 = "^\s*((([0-9A-Fa-f]{1,4}:){7}(([0-9A-Fa-f]{1,4})|:))|(([0-9A-Fa-f]{1,4}:){6}(:|((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})|(:[0-9A-Fa-f]{1,4})))|(([0-9A-Fa-f]{1,4}:){5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){4}(:[0-9A-Fa-f]{1,4}){0,1}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){3}(:[0-9A-Fa-f]{1,4}){0,2}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){2}(:[0-9A-Fa-f]{1,4}){0,3}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:)(:[0-9A-Fa-f]{1,4}){0,4}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(:(:[0-9A-Fa-f]{1,4}){0,5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})))(%.+)?\s*$"
        panel_ipv4 = "https?://(.*):\d+"

        ipv4_list = re.findall(panel_ipv4, get.panel_addr)
        if len(ipv4_list) == 0:
            return public.returnMsg(False, "请输入正确的面板地址！ 如：http://1.1.1.1/8888")
        slave_ip = ipv4_list[0]

        if self.get_slave_info(slave_ip) is not None:
            return public.returnMsg(False, f"从库【{slave_ip}】已经存在！")

        panel_addr = get.panel_addr if str(get.panel_addr).endswith("/") else get.panel_addr + "/"
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
        :param get.replicate_do_db: 需要复制的数据库
        :param get.replicate_ignore_db: 不需要复制的数据库
        :param get.replicate_do_table: 需要复制的表
        :param get.replicate_ignore_table: 不需要复制的表
        :param get.replicate_wild_do_table: 使用通配符来动态控制需要复制的表
        :param get.replicate_wild_ignore_table: 使用通配符来动态控制不需要复制的表
        :return:
        """

        # 校验参数
        if not hasattr(get, "panel_addr"):
            return public.returnMsg(False, "缺少参数！ panel_addr")
        if not hasattr(get, "panel_key"):
            return public.returnMsg(False, "缺少参数！ panel_key")

        panel_ipv4 = "https?://(.*):\d+"

        ipv4_list = re.findall(panel_ipv4, get.panel_addr)
        if len(ipv4_list) == 0:
            return public.returnMsg(False, "请输入正确的面板地址！ 如：http://1.1.1.1/8888")
        slave_ip = ipv4_list[0]

        if self.get_slave_info(slave_ip) is not None:
            return public.returnMsg(False, f"从库【{slave_ip}】已经存在！")

        if not hasattr(get, "replicate_do_db") and not hasattr(get, "replicate_ignore_db"):
            return public.returnMsg(False, "请选择您要同步的数据库或要排除的数据库！")
        if not hasattr(get, "replicate_do_table") and not hasattr(get, "replicate_ignore_table") and not hasattr(get, "replicate_wild_do_table") and not hasattr(get, "replicate_wild_ignore_table"):
            return public.returnMsg(False, "请选择您要同步的表或要排除的表！")

        replicate_do_db = getattr(get, "replicate_do_db", "[]")
        replicate_ignore_db = getattr(get, "replicate_ignore_db", "[]")
        replicate_do_table = getattr(get, "replicate_do_table", "[]")
        replicate_ignore_table = getattr(get, "replicate_ignore_table", "[]")
        replicate_wild_do_table = getattr(get, "replicate_wild_do_table", "[]")
        replicate_wild_ignore_table = getattr(get, "replicate_wild_ignore_table", "[]")

        replicate_do_db = json.loads(replicate_do_db)
        replicate_ignore_db = json.loads(replicate_ignore_db)
        replicate_do_table = json.loads(replicate_do_table)
        replicate_ignore_table = json.loads(replicate_ignore_table)
        replicate_wild_do_table = json.loads(replicate_wild_do_table)
        replicate_wild_ignore_table = json.loads(replicate_wild_ignore_table)
        if len(replicate_do_db) == 0 and len(replicate_ignore_db) == 0:
            return public.returnMsg(False, "请选择您要同步的数据库或要排除的数据库！")
        if len(replicate_do_table) == 0 and len(replicate_ignore_table) == 0 and len(
                replicate_wild_do_table) == 0 and len(replicate_wild_ignore_table) == 0:
            return public.returnMsg(False, "请选择您要同步的表或要排除的表！")

        panel_addr = get.panel_addr if str(get.panel_addr).endswith("/") else get.panel_addr + "/"
        panel_key = get.panel_key
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
        conf = self.__get_conf()
        if not conf.get("master"):
            try:
                port = panelMysql.panelMysql().query("show global variables like 'port'")[0][1]
            except:
                port = 3306
            conf["master"] = {
                "slave_user": public.GetRandomString(8),
                "password": public.gen_password(12),
                "master_ip": master_ip,
                "master_port": port
            }
        if not conf.get("slave"):
            conf["slave"] = {}

        # 主从配置信息
        slave_info = {
            "panel_key": panel_key,
            "panel_addr": panel_addr,
            "replicate_do_db": replicate_do_db, # 需要复制的数据库
            "replicate_ignore_db": replicate_ignore_db, # 不需要复制的数据库
            "replicate_do_table": replicate_do_table, # 需要复制的表
            "replicate_ignore_table": replicate_ignore_table, # 不需要复制的表
            "replicate_wild_do_table": replicate_wild_do_table, # 使用通配符来动态控制需要复制的表
            "replicate_wild_ignore_table": replicate_wild_ignore_table, # 使用通配符来动态控制不需要复制的表
            "replicate_status": self.conf_info
         }
        conf["slave"][slave_ip] = slave_info


        public.writeFile(plugin_conf_file, json.dumps(conf))
        master_backup = os.path.join(backup_path, "mysql_replicate.sql.gz")
        if os.path.isfile(master_backup): public.ExecShell("rm -rf {}".format(master_backup))

        public.set_module_logs('msyql_replicate', 'add_replicate_info', 1)
        return {"status": True, "msg": "添加成功!正在配置同步信息！"}

    # 主从复制
    def replicate_main(self, get):
        if not hasattr(get, "action_name"):
            return public.returnMsg(False, f"缺少参数! action_name")

        # Mysql主从复制api
        replicate_api_fun = {
            "get_replicate_conf": self.get_replicate_conf,
            "check_slave_versions": self.check_slave_versions,
            "check_slave_database": self.check_slave_database,
            "export_dump_database": self.export_dump_database,
            "upload_database_file": self.upload_database_file,
            "import_dump_database": self.import_dump_database,
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

        if "5." in master_version:
            for i in range(6):
                if f"5.{i}" in master_version:
                    return public.returnMsg(False, f"主库 Mysql{master_version} 版本不支持 gtid 同步方式! <br/>请将主库升级到 5.6 版本及以上！")

        # 获取从库版本
        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False,"主从信息不存在！")

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
        # if hasattr(get, "type"):
        #     if str(get.type) == "1": # 用户确认覆盖或同步
        #         self.set_slave_satuts(slave_ip, "check_slave_database", True)
        #         return {"status": True, "msg": "确认同步数据库!"}

        # 获取配置信息
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        cover_dict = {}

        if len(slave_info["replicate_do_table"]) != 0:
            for table in slave_info["replicate_do_table"]:
                if str(table).find(".") == -1:
                    continue
                db_name, table_name = str(table).split(".")

                t_db = mysql_slave_obj.exec_shell_sql(f'SELECT table_name,table_rows,data_length,table_collation,create_time,update_time FROM information_schema.TABLES WHERE table_schema = "{db_name}" and table_name = "{table_name}";')
                if str(t_db).find("bash: warning: setlocale: LC_ALL: cannot change locale (en_US.UTF-8)") != -1:
                    return public.returnMsg(False, f"从库编码错误！{t_db}")
                elif str(t_db).find("请检查") != -1:
                    return public.returnMsg(False, t_db)
                if t_db:
                    t_db = t_db.split("\n")[1]
                    t_db = t_db.split("\t")
                    table = {
                        "table_name": t_db[0],
                        "table_rows": t_db[1],
                        "data_length": t_db[2],
                        "table_collation": t_db[3],
                        "create_time": t_db[4],
                        "update_time": t_db[5] if t_db[5] != "NULL" else None,
                    }
                    if cover_dict.get(db_name) is None:
                        cover_dict[db_name] = []
                    cover_dict[db_name].append(table)
        elif len(slave_info["replicate_ignore_table"]) != 0:
            # replicate_ignore_table = slave_info["replicate_ignore_table"]
            return public.returnMsg(False, f"您未选择复制的表！")
        else:
            return public.returnMsg(False, f"您未选择复制的表！")

        if cover_dict:
            database_list = []
            for db_name, table_list in cover_dict.items():
                size, ext = round(sum([int(tb['data_length']) for tb in table_list]) / 1024, 2), "KB"
                if size > 1024: size, ext = round(size / 1024, 2), "MB"
                if size > 1024: size, ext = round(size / 1024, 2), "GB"

                database = {
                    "msg": f"{db_name}，大小：{size}{ext}"
                }
                database_list.append(database)
            for info in slave_info["replicate_status"]:
                if info["api"] == "check_slave_database":
                    info["msg_list"] = [
                        {"msg": "从库已存在同名数据库，无法进行主从，请删除从库数据库或取消同步该数据库！"},
                        {"msg": "从库同名数据库:"},
                    ]
                    info["msg_list"].extend(database_list)
                self.set_slave_info(slave_ip, slave_info)
            return {"status": False, "msg": f"从库已存在同名数据库，无法进行主从，请删除从库数据库或取消同步该数据库！<br/>{'<br/>'.join([db['msg'] for db in database_list])}", "database_list": database_list}

        for info in slave_info["replicate_status"]:
            if info["api"] == "check_slave_database":
                info["status"] = True
                info["msg_list"] = []
        self.set_slave_info(slave_ip, slave_info)
        return {"status": True, "msg": "开始同步数据库!"}

    # 导出数据库
    def export_dump_database(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "check_slave_database") is False:
            return public.returnMsg(False, "请先检查数据库一致性！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 用户是否确定
        if hasattr(get, "type"):
            if str(get.type) == "1":  # 重新导入
                if slave_info.get("export_dump_database_task_id") is not None:
                    del slave_info["export_dump_database_task_id"]
                for info in slave_info["replicate_status"]:
                    if info["api"] == "export_dump_database":
                        info["msg_list"] = []
                self.set_slave_info(slave_ip, slave_info)

        password = public.M('config').where('id=?', (1,)).getField('mysql_root')
        mysqldump_bin = public.get_mysqldump_bin()

        task_obj = panelTask.bt_task()
        task_id = slave_info.get("export_dump_database_task_id") # 获取任务id
        if task_id is not None:
            task = task_obj.get_task_find(task_id)
            if not task:
                del slave_info["export_dump_database_task_id"]
                self.set_slave_info(slave_ip, slave_info)
                return {"status": True, "msg": "任务不存在！"}

            if task.get("status", 0) == 1:
                export_path = slave_info["export_path"]
                if not os.path.isfile(export_path):
                    return public.returnMsg(False, f"导出文件不存在！")

                size, ext = round(os.path.getsize(export_path) / 1024, 2), "KB"
                if size > 1024: size, ext = round(size / 1024, 2), "MB"
                if size > 1024: size, ext = round(size / 1024, 2), "GB"

                slave_info["export_path"] = export_path  # 保存导出路径

                for info in slave_info["replicate_status"]:
                    if info["api"] == "export_dump_database":
                        info["status"] = True
                        info["msg_list"] = [
                            {"msg": f"文件路径：{export_path}"},
                            {"msg": f"文件大小：{size}{ext}"},
                            {"msg": f"导出时间：{datetime.datetime.fromtimestamp(task['exectime'])}"},
                            {"msg": f"结束时间：{datetime.datetime.fromtimestamp(task['endtime'])}"},
                        ]
                self.set_slave_info(slave_ip, slave_info)
                return {"status": True, "msg": "数据库已导出完成！"}
            return {"status": True, "msg": "正在导出数据中！刷新页面可见任务队列！", "type": 2}

        if len(slave_info["replicate_do_db"]) != 0:
            replicate_do_db = slave_info["replicate_do_db"]
        elif len(slave_info["replicate_ignore_db"]) != 0:
            return public.returnMsg(False, f"您未选择复制的数据库！")
        else:
            return public.returnMsg(False, f"您未选择复制的数据库！")

        if len(slave_info["replicate_do_table"]) != 0:
            replicate_do_table = slave_info["replicate_do_table"]
        elif len(slave_info["replicate_ignore_table"]) != 0:
            replicate_ignore_table = slave_info["replicate_ignore_table"]
            return public.returnMsg(False, f"您未选择复制的表！")
        else:
            return public.returnMsg(False, f"您未选择复制的表！")

        time_num = int(time.time() * 100_0000)
        export_name = f"mysql_replicate_export_{time_num}"
        export_dir = os.path.join(backup_path, export_name)
        export_path = f"{export_dir}.zip"
        if os.path.isdir(export_dir):
            os.remove(export_dir)
        os.makedirs(export_dir)

        total_size = 0

        export_sql_list = []
        for db_name in replicate_do_db:
            table_list = []
            for table in replicate_do_table:
                if str(table).find(".") == -1:
                    continue
                name, table_name = str(table).split(".")
                if db_name != name: continue
                database_size = panelMysql.panelMysql().query(f"SELECT data_length FROM information_schema.TABLES WHERE table_schema='{db_name}' and table_name='{table_name}';")
                for table in database_size:
                    total_size += table[0]

                table_list.append(table_name)

            sql_path = os.path.join(export_dir, f"{db_name}.sql")

            table_shell = f"--tables {db_name} {' '.join(table_list)}"

            shell = f"{mysqldump_bin} -R -E --skip-lock-tables --set-gtid-purged=off --routines --events --triggers=false --single-transaction " \
                    f"-uroot -p{password} --force {table_shell} > {sql_path}"
            export_sql_list.append(shell)

        zip_shell = f"cd {backup_path} && zip -rqm {export_path} ./{export_name}"
        export_sql_list.append(zip_shell)

        export_shell = " && ".join(export_sql_list)

        # 判断大小
        # 大于 1G 返回提示
        if int((total_size / 1024 / 1024)) > 1024:
            task_id = task_obj.create_task('导出数据库文件', 0, export_shell)
            slave_info["export_dump_database_task_id"] = task_id  # 保存任务id
            slave_info["export_path"] = export_path  # 保存导出路径
            self.set_slave_info(slave_ip, slave_info)
            size, ext = round(total_size / 1024, 2), "KB"
            if size > 1024: size, ext = round(size / 1024, 2), "MB"
            if size > 1024: size, ext = round(size / 1024, 2), "GB"
            return {"status": True, "msg": f"您导出的数据大于 1GB，大小为 {size}{ext}，已放入后台运行！请导出完成后重新点击【重新配置】按钮", "type": 1, "export_shell": export_shell, "total_size": total_size}

        exectime = int(time.time())
        public.ExecShell(export_shell)
        endtime = int(time.time())

        if not os.path.isfile(export_path):
            return public.returnMsg(False, f"导出失败！")

        size, ext = round(os.path.getsize(export_path) / 1024, 2), "KB"
        if size > 1024: size, ext = round(size / 1024, 2), "MB"
        if size > 1024: size, ext = round(size / 1024, 2), "GB"

        slave_info["export_path"] = export_path  # 保存导出路径
        for info in slave_info["replicate_status"]:
            if info["api"] == "export_dump_database":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": f"文件路径：{export_path}"},
                    {"msg": f"文件大小：{size}{ext}"},
                    {"msg": f"导出时间：{datetime.datetime.fromtimestamp(exectime)}"},
                    {"msg": f"结束时间：{datetime.datetime.fromtimestamp(endtime)}"},
                ]
        self.set_slave_info(slave_ip, slave_info)
        return {"status": True, "msg": "数据库导出完成！"}

    # 上传数据库文件
    def upload_database_file(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "export_dump_database") is False:
            return public.returnMsg(False, "请先导出数据库文件！")

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        is_continue = False
        # 用户是否确定跳过
        if hasattr(get, "type"):
            if str(get.type) == "1": # 确认继续
                is_continue = True
            if str(get.type) == "2":
                self.set_slave_satuts(slave_ip, "upload_database_file", True)
                return public.returnMsg(True, "上传文件已跳过！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        size, ext = round(os.path.getsize(slave_info["export_path"]) / 1024, 2), "KB"
        if size > 1024: size, ext = round(size / 1024, 2), "MB"
        if size > 1024: size, ext = round(size / 1024, 2), "GB"

        if is_continue is False and os.path.getsize(slave_info["export_path"]) / 1024 / 1024 > 1024:
            return {"status": True, "msg": f"您的要上传的文件大于 1G，请选择上传方式？<br/>文件大小：{size}{ext}<br/>立即上传：保持当前页面请勿关闭，请耐心等待（推荐文件大小10G以内使用）<br/>手动上传：请将 {slave_info['export_path']} 文件手动上传至从服务器上，文件路径需保持一致，上传完成后再点击【已手动上传】！", "type": 1}


        resp = mysql_slave_obj.bt_api_obj.upload_file(slave_info["export_path"])
        if resp is not True:
            return public.returnMsg(False, resp)

        for info in slave_info["replicate_status"]:
            if info["api"] == "upload_database_file":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": f"上传文件路径：{slave_info['export_path']}"},
                    {"msg": f"上传文件大小：{size}{ext}"}
                ]
        self.set_slave_info(slave_ip, slave_info)
        return public.returnMsg(True, "文件上传完成！")

    # 导入数据库文件
    def import_dump_database(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "upload_database_file") is False:
            return public.returnMsg(False, "请先上传数据库文件！")

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 判断文件
        resp = mysql_slave_obj.bt_api_obj.upload_file_exists(slave_info["export_path"])
        if resp["status"] is False:
            return public.returnMsg(False, f"从库服务器导入数据库文件不存在！<br/>手动上传：请将 {slave_info['export_path']} 文件手动上传至从服务器上，文件路径需保持一致！")

        file_info = resp["msg"]
        mtime = file_info["mtime"]
        size, ext = round(file_info["size"] / 1024, 2), "KB"
        if size > 1024: size, ext = round(size / 1024, 2), "MB"
        if size > 1024: size, ext = round(size / 1024, 2), "GB"

        resp = mysql_slave_obj.exec_shell_sql(f"show databases;", True)
        if resp["status"] is False or not resp["msg"]:
            return public.returnMsg(False, "请求从服务器错误！请重试！")
        database_list = resp["msg"]
        database_list = str(database_list).split("\n")
        database_list = [str(db).strip() for db in database_list]

        export_dir = str(slave_info['export_path']).rstrip(".zip")
        # 删除解压目录
        mysql_slave_obj.bt_api_obj.delete_dir(export_dir)

        # 解压数据文件
        unzip_shell = f"unzip -qo {slave_info['export_path']} -d {backup_path}"
        resp = mysql_slave_obj.bt_api_obj.slave_execute_command(unzip_shell)
        while resp["status"] is False and not resp["msg"]:
            resp = mysql_slave_obj.bt_api_obj.get_execute_msg()
            if resp["msg"]:
                return public.returnMsg(False, resp["msg"])
            time.sleep(1)

        if len(slave_info["replicate_do_db"]) != 0:
            replicate_do_db = slave_info["replicate_do_db"]
        elif len(slave_info["replicate_ignore_db"]) != 0:
            return public.returnMsg(False, f"您未选择复制的数据库！")
        else:
            return public.returnMsg(False, f"您未选择复制的数据库！")

        create_err_msg_list = []
        import_err_msg_list = []
        # 创建数据库
        for db_name in replicate_do_db:
            if db_name not in database_list:
                new_password = self.__new_password()
                create_resp = mysql_slave_obj.bt_api_obj.create_database(db_name,new_password)
                if create_resp["status"] is False:
                    create_err_msg_list.append(f"{db_name} {create_resp['msg']}")
                    continue

            db_path = os.path.join(export_dir, f"{db_name}.sql")

            # 导入数据
            import_resp = mysql_slave_obj.bt_api_obj.import_sql(db_path, db_name)
            if import_resp["status"] is False:
                import_err_msg_list.append(f"导入 {db_name}： {import_resp['msg']}")

        mysql_slave_obj.bt_api_obj.delete_dir(export_dir)
        mysql_slave_obj.bt_api_obj.delete_file(slave_info['export_path'])
        if len(create_err_msg_list) != 0:
            return public.returnMsg(False, f"从库创建数据库时失败！<br/>{' '.join(create_err_msg_list)}")
        if len(import_err_msg_list) != 0:
            return public.returnMsg(False, f"从库导入数据库时失败！<br/>{' '.join(import_err_msg_list)}")

        for info in slave_info["replicate_status"]:
            if info["api"] == "import_dump_database":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": f"文件路径：{slave_info['export_path']}"},
                    {"msg": f"文件大小：{size}{ext}"},
                    {"msg": f"最后修改时间：{datetime.datetime.fromtimestamp(mtime)}"}
                ]
        self.set_slave_info(slave_ip, slave_info)
        return public.returnMsg(True, "数据库导入成功！")

    @classmethod
    def __new_password(cls):
        """
        帮助方法生成随机密码
        """
        import random
        import string
        # 生成随机密码
        password = "".join(random.sample(string.ascii_letters + string.digits, 16))
        return password

    # 检查并设置主库配置信
    def check_master_conf(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "import_dump_database") is False:
            return public.returnMsg(False, "请先导入数据库文件！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        mysql_master_obj = mysql_master()

        is_update = False

        # 检查并设置 gtid
        if mysql_master_obj.get_master_gtid() is False:
            is_update = True
            result = mysql_master_obj.set_master_gtid()
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

        conf = self.__get_conf()
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

    # 检查并设置从库配置信息
    def check_slave_conf(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "check_master_conf") is False:
            return public.returnMsg(False, "请先检查并设置主库配置信！")

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        # 检查 server_id
        conf = self.__get_conf()
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

        # 停止从库同步
        mysql_slave_obj.exec_shell_sql("stop slave")
        mysql_slave_obj.exec_shell_sql("reset slave all")

        # 检查 gtid
        # 检查并设置 gtid
        if mysql_slave_obj.get_slave_gtid() is False:
            result = mysql_slave_obj.set_slave_gtid()
            if result is not True:
                return public.returnMsg(False, f"设置 gtid 错误！{result}")

        # 检查并设置 binlog
        if mysql_slave_obj.get_slave_binlog() is False:
            result = mysql_slave_obj.set_slave_binlog()
            if result is not True:
                return public.returnMsg(False, f"设置 binlog 错误！{result}")

        resp = mysql_slave_obj.bt_api_obj.get_slave_conf()
        if resp["status"] is False:
            return public.returnMsg(False, f"获取从库配置错误！ {resp['msg']}")
        conf = resp["data"]

        # 是否确定覆盖
        if hasattr(get, "type"):
            if str(get.type) == "1":
                conf = re.sub(r"replicate[-_]do[-_]db\s*=\s*.+\n", "", conf)
                conf = re.sub(r"replicate[-_]ignore[-_]db\s*=\s*.+\n", "", conf)
                conf = re.sub(r"replicate[-_]do[-_]table\s*=\s*.+\n", "", conf)
                conf = re.sub(r"replicate[-_]ignore[-_]table\s*=\s*.+\n", "", conf)
                conf = re.sub(r"replicate[-_]wild[-_]do[-_]table\s*=\s*.+\n", "", conf)
                conf = re.sub(r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.+\n", "", conf)

        # 检查从库是否已经设置主从配置
        db_re = r"(replicate[-_]do[-_]db\s*=\s*.+\n|" \
                r"replicate[-_]ignore[-_]db\s*=\s*.+\n)"
        table_re = r"(replicate[-_]do[-_]table\s*=\s*.+\n|" \
                r"replicate[-_]ignore[-_]table\s*=\s*.+\n|" \
                r"replicate[-_]wild[-_]do[-_]table\s*=\s*.+\n|" \
                r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.+\n)"
        replicate_db_list = re.findall(db_re, conf)
        replicate_table_list = re.findall(table_re, conf)
        if len(replicate_db_list) != 0 or len(replicate_table_list) != 0:
            return {"status": True, "msg": "您已设置主从配置，是否覆盖?", "type": 1, "database_num": len(replicate_db_list), "table_num": len(replicate_table_list)}

        # 设置同步数据库，表
        replicate_conf = ""
        if len(slave_info["replicate_do_db"]) != 0:
            conf = re.sub(r"replicate[-_]do[-_]db\s*=\s*.+\n", "", conf)
            for db_name in slave_info["replicate_do_db"]:
                replicate_conf += f"\nreplicate_do_db={db_name}"

        elif len(slave_info["replicate_ignore_db"]) != 0:
            conf = re.sub(r"replicate[-_]ignore[-_]db\s*=\s*.+\n", "", conf)
            for db_name in slave_info["replicate_ignore_db"]:
                replicate_conf += f"\nreplicate_ignore_db={db_name}"
        else:
            return public.returnMsg(False, f"您未选择复制的数据库！")

        if len(slave_info["replicate_do_table"]) != 0:
            conf = re.sub(r"replicate[-_]do[-_]table\s*=\s*.+\n", "", conf)
            for tb_name in slave_info["replicate_do_table"]:
                replicate_conf += f"\nreplicate_do_table={tb_name}"

        elif len(slave_info["replicate_ignore_table"]) != 0:
            conf = re.sub(r"replicate[-_]ignore[-_]table\s*=\s*.+\n", "", conf)
            for tb_name in slave_info["replicate_ignore_table"]:
                replicate_conf += f"\nreplicate_ignore_table={tb_name}"

        elif len(slave_info["replicate_wild_do_table"]) != 0:
            conf = re.sub(r"replicate[-_]wild[-_]do[-_]table\s*=\s*.+\n", "", conf)
            for tb_name in slave_info["replicate_wild_do_table"]:
                replicate_conf += f"\nreplicate_wild_do_table={tb_name}"

        elif len(slave_info["replicate_wild_ignore_table"]) != 0:
            conf = re.sub(r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.+\n", "", conf)
            for tb_name in slave_info["replicate_wild_ignore_table"]:
                replicate_conf += f"\nreplicate_wild_ignore_table={tb_name}"
        else:
            return public.returnMsg(False, f"您未选择复制的表！")

        conf = re.sub("\[mysqld\]", "[mysqld]" + replicate_conf, conf)

        # 保存配置
        resp = mysql_slave_obj.bt_api_obj.save_slave_conf(conf)
        if resp["status"] is False:
            return public.returnMsg(False, f"保存从库配置错误！{resp['msg']}")

        # 获取远程数据库读写状态
        resp = mysql_slave_obj.set_mysql_readonly_temp(status=1)
        if resp is not None:
            return public.returnMsg(False, resp)

        mysql_slave_obj.bt_api_obj.control_mysqld_service()


        for info in slave_info["replicate_status"]:
            if info["api"] == "check_slave_conf":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": "检查 server-id"},
                    {"msg": "检查 gtid"},
                    {"msg": "检查 binlog"},
                    {"msg": "设置同步数据库信息"},
                    {"msg": "设置从库 Mysql 只读状态（除超级用户root外）"},
                    {"msg": "重启Mysql数据库服务"}
                ]
        self.set_slave_info(slave_ip, slave_info)
        return {"status": True, "msg": "从库配置信息检查并配置完成!"}

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
        if self.get_slave_satuts(slave_ip, "check_slave_conf") is False:
            return public.returnMsg(False, "请先检查并设置从库配置信息！")

        # 获取配置信息
        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        conf = self.__get_conf()
        user = conf['master']['slave_user']
        password = conf['master']['password']

        # 获取主库版本
        master_version = mysql_master.get_master_version()

        mysql_obj = panelMysql.panelMysql()

        # 检查同步用户
        is_user = mysql_obj.query(f"select count(User) from mysql.user where User='{user}' and Host='{slave_ip}';")
        if is_user[0][0] == 0:
            mysql_obj.execute(f"flush privileges;")
            mysql_obj.execute(f"create user {user}@'{slave_ip}' identified by '{password}'")
            if "8." in master_version:
                mysql_obj.execute(f"grant replication slave on *.* to {user}@'{slave_ip}'")
            else:
                mysql_obj.execute(f"grant replication slave on *.* to {user}@'{slave_ip}' identified by '{password}'")
            mysql_obj.execute(f"flush privileges;")


        for info in slave_info["replicate_status"]:
            if info["api"] == "create_replicate_user":
                info["status"] = True
                info["msg_list"] = [
                    {"msg": f"创建用户：{user}，权限：主从复制（replication），允许访问ip：{slave_ip}"},
                ]
        self.set_slave_info(slave_ip, slave_info)
        return public.returnMsg(True, "主从复制用户已创建完成！")

    # 检查并设置防火墙放行端口
    def check_firewall_set(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        # 检查上一步是否完成
        if self.get_slave_satuts(slave_ip, "create_replicate_user") is False:
            return public.returnMsg(False, "请先检查并设置主从同步用户！")

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

        master = self.__get_conf()["master"]
        create_replicate_sql = f"""
            CHANGE MASTER TO
            MASTER_HOST="{master['master_ip']}",
            MASTER_USER="{master['slave_user']}",
            MASTER_PASSWORD="{master['password']}",
            MASTER_PORT={master['master_port']},
            MASTER_AUTO_POSITION=1;
        """
        mysql_slave_obj.exec_shell_sql("stop slave")
        mysql_slave_obj.exec_shell_sql("reset slave")
        mysql_slave_obj.exec_shell_sql(create_replicate_sql)
        mysql_slave_obj.exec_shell_sql("start slave")
        time.sleep(0.3)
        slave_status = mysql_slave_obj.exec_shell_sql("show slave status\G;")

        if not re.search("Slave_IO_Running: Yes",slave_status, re.I) and not re.search("Slave_IO_Running: Connecting",slave_status, re.I):
            return public.returnMsg(False, f"启动失败！请在状态中查看错误信息！")
        if not re.search("Slave_SQL_Running: Yes",slave_status, re.I):
            return public.returnMsg(False, f"启动失败！请在状态中查看错误信息！")

        if slave_info.get('export_path') is not None:
            if os.path.exists(slave_info.get('export_path')):
                os.remove(slave_info['export_path'])
        if self.get_slave_satuts(slave_ip, "start_replicate") is False:
            self.set_slave_satuts(slave_ip, "start_replicate", True)
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
        mysql_slave_obj.exec_shell_sql("reset slave")

        slave_status = mysql_slave_obj.exec_shell_sql("show slave status\G;")

        if not re.search("Slave_IO_Running: No",slave_status, re.I):
            return public.returnMsg(False, f"停止失败！")
        if not re.search("Slave_SQL_Running: No",slave_status, re.I):
            return public.returnMsg(False, f"停止失败！")

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
        result = mysql_slave_obj.set_mysql_readonly_temp(status=status)
        if result is not None:
            return public.returnMsg(False, result)
        return public.returnMsg(True, f"设置从库 {slave_ip} {'只读' if status == 1 else '只写'} 状态成功！")

    # 删除主从复制
    def remove_replicate_info(self,get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, f"缺少参数! slave_ip")
        slave_ip = get.slave_ip

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False,"主从信息不存在！")

        # 关闭主从复制
        mysql_slave_obj.exec_shell_sql("stop slave")
        mysql_slave_obj.exec_shell_sql("reset slave")
        mysql_slave_obj.exec_shell_sql("reset slave all")

        # 删除从库配置文件
        resp = mysql_slave_obj.bt_api_obj.get_slave_conf()
        if resp["status"] is False:
            return public.returnMsg(False, resp["msg"])
        conf = resp["data"]

        conf = re.sub(r"replicate[-_]do[-_]db\s*=\s*.+\n", "", conf)
        conf = re.sub(r"replicate[-_]ignore[-_]db\s*=\s*.+\n", "", conf)
        conf = re.sub(r"replicate[-_]do[-_]table\s*=\s*.+\n", "", conf)
        conf = re.sub(r"replicate[-_]ignore[-_]table\s*=\s*.+\n", "", conf)
        conf = re.sub(r"replicate[-_]wild[-_]do[-_]table\s*=\s*.+\n", "", conf)
        conf = re.sub(r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.+\n", "", conf)
        mysql_slave_obj.bt_api_obj.save_slave_conf(conf)

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

        if len(slave_info["replicate_do_db"]) != 0:
            replicate_do_db = slave_info["replicate_do_db"]
        elif len(slave_info["replicate_ignore_db"]) != 0:
            # replicate_ignore_db = slave_info["replicate_ignore_db"]
            return public.returnMsg(False, f"您未选择复制的数据库！")
        else:
            return public.returnMsg(False, f"您未选择复制的数据库！")

        if len(slave_info["replicate_do_table"]) != 0:
            replicate_do_table = slave_info["replicate_do_table"]
        elif len(slave_info["replicate_ignore_table"]) != 0:
            # replicate_ignore_table = slave_info["replicate_ignore_table"]
            return public.returnMsg(False, f"您未选择复制的表！")
        else:
            return public.returnMsg(False, f"您未选择复制的表！")

        replicate_database = []
        for db_name in replicate_do_db:
            table_list = []
            for table in replicate_do_table:
                if str(table).find(".") == -1:
                    continue
                name, table_name = str(table).split(".")
                if db_name == name:
                    table_list.append(table_name)
            database = {
                "name": db_name,
                "table_list": table_list
            }
            replicate_database.append(database)

        info = {
            "database": replicate_database,
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

        # 获取从库root密码
        resp = mysql_slave_obj.exec_shell_sql("show slave status;", True)
        if resp["status"] is False:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库 {slave_ip} API接口的IP白名单")

        slave_status = resp["msg"]

        field_list = []
        for field in self.slave_status_ps.keys():
            if slave_status.find(field) != -1:
                field_list.append(field)
                slave_status = slave_status.lstrip(f"{field}").strip()

        slave_status = slave_status.split("\t")


        slave_status_list = []
        idx = 0
        for name in field_list:
            if idx < len(slave_status):
                value = slave_status[idx]
                value = str(value).replace("\\n", "").split(",")
                value = "<br/>".join(value)
                slave_status_list.append({"name": name, "value": value, "ps": self.slave_status_ps.get(name)})
                idx += 1
            else:
                slave_status_list.append({"name": name, "value": "", "ps": self.slave_status_ps.get(name)})
        return {"status": True, "data": slave_status_list}

    # 修改主从信息
    def set_replicate_info(self, get):
        if not hasattr(get, "slave_ip"):
            return public.returnMsg(False, "缺少参数! slave_ip")
        if not hasattr(get, "replicate_do_db") and not hasattr(get, "replicate_ignore_db"):
            return public.returnMsg(False, "缺少参数！ replicate_do_db")
        if (not hasattr(get, "replicate_do_table") and not hasattr(get, "replicate_ignore_table")) or (not hasattr(get, "replicate_wild_do_table") and not hasattr(get, "replicate_wild_ignore_table")):
            return public.returnMsg(False, "缺少参数！ replicate_do_db")

        replicate_do_db = getattr(get,"replicate_do_db", "[]")
        replicate_ignore_db = getattr(get,"replicate_ignore_db", "[]")
        replicate_do_table = getattr(get,"replicate_do_table", "[]")
        replicate_ignore_table = getattr(get,"replicate_ignore_table", "[]")
        replicate_wild_do_table = getattr(get,"replicate_wild_do_table", "[]")
        replicate_wild_ignore_table = getattr(get,"replicate_wild_ignore_table", "[]")

        replicate_do_db = json.loads(replicate_do_db)
        replicate_ignore_db = json.loads(replicate_ignore_db)
        replicate_do_table = json.loads(replicate_do_table)
        replicate_ignore_table = json.loads(replicate_ignore_table)
        replicate_wild_do_table = json.loads(replicate_wild_do_table)
        replicate_wild_ignore_table = json.loads(replicate_wild_ignore_table)
        if len(replicate_do_db) == 0 and len(replicate_ignore_db) == 0:
            return public.returnMsg(False, "请选择您要同步的数据库或要排除的数据库！")
        if (len(replicate_do_table) == 0 and len(replicate_ignore_table) == 0) or (len(replicate_wild_do_table) == 0 and len(replicate_wild_ignore_table) == 0):
            return public.returnMsg(False, "请选择您要同步的表或要排除的表！")

        slave_ip = get.slave_ip

        slave_info = self.get_slave_info(slave_ip)
        if slave_info is None:
            return public.returnMsg(False, "主从信息不存在！")

        mysql_slave_obj = mysql_slave(slave_ip)
        if mysql_slave_obj.bt_api_obj is None:
            return public.returnMsg(False, "主从信息不存在！")

        resp = mysql_slave_obj.bt_api_obj.get_slave_conf()
        if resp["status"] is False:
            return public.returnMsg(False, resp["msg"])

        conf = resp["data"]

        # 设置同步数据库，表
        replicate_conf = ""
        if len(replicate_do_db) != 0:
            conf = re.sub(r"replicate[-_]do[-_]db\s*=\s*.+\n", "", conf)
            for db_name in replicate_do_db:
                replicate_conf += f"\nreplicate_do_db={db_name}"

        elif len(replicate_ignore_db) != 0:
            conf = re.sub(r"replicate[-_]ignore[-_]db\s*=\s*.+\n", "", conf)
            for db_name in replicate_ignore_db:
                replicate_conf += f"\nreplicate_ignore_db={db_name}"
        else:
            return public.returnMsg(False, f"您未选择复制的数据库！")

        if len(replicate_do_table) != 0:
            conf = re.sub(r"replicate[-_]do[-_]table\s*=\s*.+\n", "", conf)
            for tb_name in replicate_do_table:
                replicate_conf += f"\nreplicate_do_table={tb_name}"

        elif len(replicate_ignore_table) != 0:
            conf = re.sub(r"replicate[-_]ignore[-_]table\s*=\s*.+\n", "", conf)
            for tb_name in replicate_ignore_table:
                replicate_conf += f"\nreplicate_ignore_table={tb_name}"

        elif len(replicate_wild_do_table) != 0:
            conf = re.sub(r"replicate[-_]wild[-_]do[-_]table\s*=\s*.+\n", "", conf)
            for tb_name in replicate_wild_do_table:
                replicate_conf += f"\nreplicate_wild_do_table={tb_name}"

        elif len(replicate_wild_ignore_table) != 0:
            conf = re.sub(r"replicate[-_]wild[-_]ignore[-_]table\s*=\s*.+\n", "", conf)
            for tb_name in replicate_wild_ignore_table:
                replicate_conf += f"\nreplicate_wild_ignore_table={tb_name}"
        else:
            return public.returnMsg(False, f"您未选择复制的表！")

        conf = re.sub("\[mysqld\]", "[mysqld]" + replicate_conf, conf)

        # 保存配置
        resp = mysql_slave_obj.bt_api_obj.save_slave_conf(conf)
        if resp["status"] is False:
            return public.returnMsg(False, f"保存从库配置错误！{resp['msg']}")

        slave_info["replicate_do_db"] = replicate_do_db
        slave_info["replicate_ignore_db"] = replicate_ignore_db
        slave_info["replicate_do_table"] = replicate_do_table
        slave_info["replicate_ignore_table"] = replicate_ignore_table
        slave_info["replicate_wild_do_table"] = replicate_wild_do_table
        slave_info["replicate_wild_ignore_table"] = replicate_wild_ignore_table
        self.set_slave_info(slave_ip, slave_info)

        mysql_slave_obj.bt_api_obj.control_mysqld_service()

        return {"status": True, "msg": "设置!"}

    def get_logs(self,get):
        import files
        return files.files().GetLastLine(logs_file, 20)

# 主库类
class mysql_master():
    __is_firewalld = False
    __is_ufw = False
    mysqldump_complete_file = '/tmp/mysqldump.txt'

    def __init__(self):
        if os.path.exists('/usr/sbin/firewalld'): self.__is_firewalld = True
        if os.path.exists('/usr/sbin/ufw'): self.__is_ufw = True

    @classmethod
    def get_master_version(self):
        """
            @name 获取数据库版本号
            @author zhwen<zhw@bt.cn>
            @return master_version str
        """
        master_version = panelMysql.panelMysql().query("select version()")[0][0].split(".")
        master_version = master_version[0] + "." + master_version[1]
        return master_version

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

    # 检查主库版本号是否支持gtid同步
    def mysql_replicate_version(self):
        status = False
        if "5.7" in self.get_master_version():
            status = True
        if "8." in self.get_master_version():
            status = True
        return status

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
    def get_master_gtid(self):
        gtid_mode = panelMysql.panelMysql().query("show global variables like 'gtid_mode'")[0]
        if 'ON' in gtid_mode:
            return True
        return False

    # 设置主库的gtid支持
    def set_master_gtid(self):
        gtid_conf = """
log-slave-updates=true
enforce-gtid-consistency=1
gtid-mode=on"""
        try:
            conf = public.readFile(my_cnf)
            conf = re.sub("log-slave-updates\s*=\s*.+\n", "", conf)
            conf = re.sub("enforce-gtid-consistency.*\n", "", conf)
            conf = re.sub("gtid-mode\s*=\s*.+\n", "", conf)
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

    @classmethod
    # 获取 api 对象
    def get_bt_api(cls, slave_ip: str):
        slave = mysql_replicate_main.get_slave_info(slave_ip)
        if slave is None: return None
        return bt_api(slave["panel_addr"], slave["panel_key"])

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

    # 获取主库gtid状态
    def get_slave_gtid(self):
        resp = self.bt_api_obj.get_slave_conf()
        conf = resp["data"]
        if re.search("\n\s*gtid-mode\s*=\s*on", conf):
            return True
        return False

    # 设置主库的gtid支持
    def set_slave_gtid(self):
        # 设置从库的gtid支持
        gtid_conf = """
log-slave-updates=true
enforce-gtid-consistency=1
read-only=on
relay-log=relay-log-server
gtid-mode=on"""
        try:
            resp = self.bt_api_obj.get_slave_conf()
            conf = resp["data"]
            conf = re.sub("log-slave-updates\s*=\s*.+\n", "", conf)
            conf = re.sub("enforce-gtid-consistency.*\n", "", conf)
            conf = re.sub("read-only\s*=\s*.+\n", "", conf)
            conf = re.sub("relay-log\s*=\s*.+\n", "", conf)
            conf = re.sub("gtid-mode\s*=\s*.+\n", "", conf)
            conf = re.sub("\[mysqld\]", "[mysqld]" + gtid_conf, conf)
            self.bt_api_obj.save_slave_conf(conf)
            return True
        except Exception as err:
            return err

    # 检查数据库二进制日志是否已经开启
    def get_slave_binlog(self):
        resp = self.bt_api_obj.get_slave_conf()
        conf = resp["data"]
        if re.search("\n\s*log-bin\s*=\s*mysql-bin", conf):
            return True
        return False

    # 设置主库binlog
    def set_slave_binlog(self):
        bin_log = """
log-bin=mysql-bin
binlog_format=mixed"""
        try:
            resp = self.bt_api_obj.get_slave_conf()
            conf = resp["data"]
            if not re.search('\n\s*#\s*log-bin\s*=\s*mysql-bin', conf):
                conf = re.sub("log-bin\s*=\s*.+\n", "", conf)
                conf = re.sub("binlog_format\s*=\s*.+\n", "", conf)
                conf = re.sub("\[mysqld\]", "[mysqld]" + bin_log, conf)
            else:
                conf = conf.replace('#log-bin=mysql-bin', 'log-bin=mysql-bin')
                conf = conf.replace('#binlog_format=mixed', 'binlog_format=mixed')
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

    def set_mysql_readonly_temp(self, status: int):
        try:
            if self.get_mysql_readonly() is True and status == 0: # 允许所有用户写
                self.exec_shell_sql(f'set global read_only=0')
            elif self.get_mysql_readonly() is False and status == 1: # 只读
                self.exec_shell_sql('set global read_only=1')
        except Exception as err:
            return err

    # 在从库执行sql语句:
    def exec_shell_sql(self, sql: str, is_resp: bool=False):
        get_time = 2 # 超时间
        if self.bt_api_obj is None:
            return False

        root_password = self.bt_api_obj.get_root_passowrd()
        shell = f"export MYSQL_PWD={root_password} && /usr/bin/mysql -uroot --default-character-set=utf8 -e 'SET sql_notes = 0;{sql}'"
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
            public.print_log(f"err:{resp['msg']}")
            return resp["msg"]
        return resp["msg"]


# 请求从库
class bt_api():

    def __init__(self, panel_addr: str, panel_key: str):
        self.__BT_PANEL = panel_addr
        self.__BT_KEY = panel_key

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
    def __get_key_data(self):
        now_time = int(time.time())
        pdata = {
            'request_token': self.__get_md5(str(now_time) + '' + self.__get_md5(self.__BT_KEY)),
            'request_time': now_time
        }
        return pdata # type: dict

    # 发送POST请求并保存Cookie
    # @url 被请求的URL地址(必需)
    # @data POST参数，可以是字符串或字典(必需)
    # @timeout 超时时间默认1800秒
    # return string
    def __http_post_cookie(self, url:str, pdata: dict, timeout: int=1800):
        try:
            res = self._REQUESTS.post(url, params=self.__get_key_data(), data=pdata, timeout=timeout, verify=False)
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
            info_url = self.__BT_PANEL + 'config?action=get_config'
            info_data = self.__get_key_data()
            result = self.__http_post_cookie(info_url, info_data)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 获取从库root密码
    def get_root_passowrd(self):
        try:
            info_url = self.__BT_PANEL + 'data?action=getKey'
            info_data = self.__get_key_data()
            info_data['table'] = "config"
            info_data['key'] = "mysql_root"
            info_data['id'] = "1"
            result = self.__http_post_cookie(info_url, info_data)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 从库执行 shell
    def slave_execute_command(self,shell: str, path: str='/tmp'):
        url = self.__BT_PANEL+'/files?action=ExecShell'
        pdata = self.__get_key_data()
        pdata["shell"] = shell
        pdata["path"] = path
        self.__http_post_cookie(url, pdata)
        return self.get_execute_msg()

    # 获取 shell 执行结果
    def get_execute_msg(self) -> dict:
        try:
            url = self.__BT_PANEL+'/files?action=GetExecShellMsg'
            pdata = self.__get_key_data()
            result = self.__http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 获取从库配置文件
    def get_slave_conf(self, path: str=None):
        try:
            url = self.__BT_PANEL + '/files?action=GetFileBody'
            pdata = self.__get_key_data()
            pdata['path'] = '/etc/my.cnf'
            if path:
                pdata['path'] = path
            result = self.__http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 保存从库配置文件
    def save_slave_conf(self,content: str,path: str=None) -> dict:
        try:
            url = self.__BT_PANEL + '/files?action=SaveFileBody'
            pdata = self.__get_key_data()
            pdata['path'] = '/etc/my.cnf'
            if path:
                pdata['path'] = path
            pdata['encoding'] = 'utf-8'
            pdata['data'] = content
            result = self.__http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    #上传文件
    def upload_file(self, export_path: str):
        pdata = self.__get_key_data()
        pdata['f_name'] = os.path.basename(export_path)
        pdata['f_path'] = os.path.dirname(export_path)
        pdata['f_size'] = os.path.getsize(export_path)
        pdata['f_start'] = 0
        f = open(export_path, 'rb')
        return self.send_file(pdata, f)

    # 发送文件
    def send_file(self, pdata, f):
        success_num = 0  # 连续发送成功次数
        upload_buff_size = 1024 * 1024 * 2 # 上传大小
        max_buff_size = int(1024 * 1024 * 8)  # 最大分片大小
        min_buff_size = int(1024 * 32)  # 最小分片大小
        err_num = 0  # 连接错误计数
        max_err_num = 5  # 最大连接错误重试次数
        up_buff_num = 5  # 调整分片的触发次数
        timeout = 30  # 每次发送分片的超时时间
        split_num = 0
        split_done = 0
        total_time = 0

        while True:
            max_buff = int(pdata['f_size'] - pdata['f_start'])
            if max_buff < upload_buff_size: upload_buff_size = max_buff  # 判断是否到文件尾
            files = {"blob": f.read(upload_buff_size)}
            try:
                res = self._REQUESTS.post(self.__BT_PANEL + '/files?action=upload', data=pdata, files=files, timeout=timeout, verify=False)
                success_num += 1
                err_num = 0
                # 连续5次分片发送成功的情况下尝试调整分片大小, 以提升上传效率
                if success_num > up_buff_num and upload_buff_size < max_buff_size:
                    upload_buff_size = int(upload_buff_size * 2)
                    success_num = up_buff_num - 3  # 如再顺利发送3次则继续提升分片大小
                    if upload_buff_size > max_buff_size: upload_buff_size = max_buff_size
            except Exception as err:
                err = str(err)
                if err.find('Read timed out') != -1 or err.find('Connection aborted') != -1:
                    if upload_buff_size > min_buff_size:
                        # 发生超时的时候尝试调整分片大小, 以确保网络情况不好的时候能继续上传
                        upload_buff_size = int(upload_buff_size / 2)
                        if upload_buff_size < min_buff_size: upload_buff_size = min_buff_size
                        success_num = 0
                    continue
                # 如果连接超时
                if err.find('Max retries exceeded with') != -1 and err_num <= max_err_num:
                    err_num += 1
                    time.sleep(0.5)
                    continue
                return "上传失败"
            result = res.json()
            if isinstance(result, int):
                if result == split_done:
                    split_num += 1
                else:
                    split_num = 0
                split_done = result
                if split_num > 10 or result > pdata['f_size']:
                    return "上传失败！"
                pdata['f_start'] = result  # 设置断点
            else:
                if result["status"] is True:
                    return True
                return result["msg"]
        return True

    # 删除目录
    def delete_dir(self, path: str) -> dict:
        try:
            url = self.__BT_PANEL + '/files?action=DeleteDir'
            pdata = self.__get_key_data()
            pdata["path"] = path
            result = self.__http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 删除文件
    def delete_file(self, path: str) -> dict:
        try:
            url = self.__BT_PANEL + '/files?action=DeleteFile'
            pdata = self.__get_key_data()
            pdata["path"] = path
            result = self.__http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 解压文件前判断文件是否存在
    def upload_file_exists(self, path: str) -> dict:
        try:
            url = self.__BT_PANEL + '/files?action=upload_file_exists'
            pdata = self.__get_key_data()
            pdata["filename"] = path
            result = self.__http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 解压文件
    def unzip_file(self, sfile: str, dfile: str, zip_type: str, coding: str="UTF-8") -> dict:
        try:
            url = self.__BT_PANEL + '/files?action=UnZip'
            pdata = self.__get_key_data()
            pdata["sfile"] = sfile
            pdata["dfile"] = dfile
            pdata["type"] = zip_type
            pdata["coding"] = coding
            result = self.__http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 创建数据库
    def create_database(self, db_name: str, new_password: str) -> dict:
        try:
            url = self.__BT_PANEL + '/database?action=AddDatabase'
            pdata = {
                "name": db_name,
                "codeing": "utf8mb4",
                "db_user": db_name,
                "password": new_password,
                "dataAccess": "127.0.0.1",
                "sid": "0",
                "address": "127.0.0.1",
                "ps": db_name,
                "dtype": "MySQL",
            }
            result = self.__http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # mysql导入sql数据文件
    def import_sql(self, path: str, name: str) -> dict:
        try:
            url = self.__BT_PANEL + '/database?action=InputSql'
            pdata = {
                "file": path,
                "name": name,
            }
            result = self.__http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")

    # 重启数据库
    def control_mysqld_service(self,type=None):
        try:
            url = self.__BT_PANEL+'/system?action=ServiceAdmin'
            p_data = self.__get_key_data()
            p_data["name"] = 'mysqld'
            p_data["type"] = 'restart'
            if type:
                p_data["type"] = type
            result = self.__http_post_cookie(url, p_data)
            return result
        except:
            return public.returnMsg(False, f"请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {public.GetLocalIp()} 是否加入从库API接口的IP白名单")