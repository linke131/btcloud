#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 王张杰 <750755014@qq.com>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   企业级备份
# +--------------------------------------------------------------------
import sys
import os
import re
import json
import time
import shutil

os.chdir("/www/server/panel")
sys.path.append("/www/server/panel/class/")
import public
try:
    import crontab
except:
    pass

from panelMysql import panelMysql


class MyPanelMysql:
    __DB_PASS = None
    __DB_USER = 'root'
    __DB_PORT = 3306
    __DB_HOST = 'localhost'
    __DB_CONN = None
    __DB_CUR = None
    __DB_ERR = None
    __DB_NET = None

    # 连接MYSQL数据库
    def __Conn(self):
        if self.__DB_NET: return True
        try:
            socket = '/tmp/mysql.sock'
            try:
                if sys.version_info[0] != 2:
                    try:
                        import pymysql
                    except:
                        public.ExecShell("pip install pymysql")
                        import pymysql
                    pymysql.install_as_MySQLdb()
                import MySQLdb
                if sys.version_info[0] == 2:
                    reload(MySQLdb)
            except Exception as ex:
                try:
                    import pymysql
                    pymysql.install_as_MySQLdb()
                    import MySQLdb
                except Exception as e:
                    self.__DB_ERR = e
                    return False
            try:
                myconf = public.readFile('/etc/my.cnf')
                rep = r"port\s*=\s*([0-9]+)"
                self.__DB_PORT = int(re.search(rep, myconf).groups()[0])
            except:
                self.__DB_PORT = 3306
            self.__DB_PASS = public.M('config').where('id=?', (1,)).getField('mysql_root')

            try:
                self.__DB_CONN = MySQLdb.connect(host=self.__DB_HOST, user=self.__DB_USER, passwd=self.__DB_PASS, port=self.__DB_PORT, charset="utf8", connect_timeout=1, unix_socket=socket)
            except MySQLdb.Error as e:
                self.__DB_HOST = '127.0.0.1'
                self.__DB_CONN = MySQLdb.connect(host=self.__DB_HOST, user=self.__DB_USER, passwd=self.__DB_PASS, port=self.__DB_PORT, charset="utf8", connect_timeout=1, unix_socket=socket)
            self.__DB_CUR = self.__DB_CONN.cursor()
            return True
        except MySQLdb.Error as e:
            self.__DB_ERR = e
            return False

    # 关闭连接
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()

    # 执行多条SQL语句
    def execute_many(self, sql):
        if not self.__Conn(): return self.__DB_ERR
        try:
            sql_list = sql.split(';')
            result = []
            for sql_str in sql_list:
                self.__DB_CUR.execute(sql_str)
                result = self.__DB_CUR.fetchall()
                self.__DB_CONN.commit()
            self.__Close()
            return result
        except Exception as ex:
            return ex


class enterprise_backup_main(object):
    __log_type = '企业级备份'
    __mysql_conf_file = "/etc/my.cnf"
    __plugin_path = '/www/server/panel/plugin/enterprise_backup'
    __configPath = os.path.join(__plugin_path, 'config')
    __encrypt_file = os.path.join(__configPath, 'encrypt.pl')
    __tar_pass_file = "/www/server/panel/data/tar_pass"
    __tar_pass = ""
    __mysql_backup_log_file = os.path.join(__plugin_path, 'mysql_backup_log_')
    __mysql_restore_log_file = os.path.join(__plugin_path, 'mysql_restore_log')
    __path_backup_log_file = os.path.join(__plugin_path, 'path_backup_log_')
    __path_restore_log_file = os.path.join(__plugin_path, 'path_restore_log')
    __log_backup_output_file = os.path.join(__plugin_path, 'log_backup_output')

    def __init__(self):
        if not os.path.exists(self.__configPath):
            os.makedirs(self.__configPath)
        # 生成随机的tar命令压缩密码
        self.__tar_pass = public.readFile(self.__tar_pass_file)
        if not self.__tar_pass:
            self.__tar_pass = public.GetRandomString(6)
            public.writeFile(self.__tar_pass_file, self.__tar_pass)
        # 创建表
        self.create_table()

        self.__backup_path = public.readFile(self.__configPath + '/local.conf')
        if not self.__backup_path:
            return

        # mysql备份相关配置
        self.__database_path = os.path.join(self.__backup_path, 'database')
        self.__full_backup_path = os.path.join(self.__database_path, 'full')
        self.__ddl_backup_path = os.path.join(self.__database_path, 'ddl')
        self.__last_full_backup_path = os.path.join(self.__full_backup_path, 'last')
        self.__inc_backup_path = os.path.join(self.__database_path, 'inc')

        # 目录备份相关配置
        self.__dir_backup = os.path.join(self.__backup_path, 'path')
        self.__dir_full_backup = os.path.join(self.__dir_backup, 'full')
        self.__dir_last_full_backup = os.path.join(self.__dir_full_backup, 'last')
        self.__dir_inc_backup = os.path.join(self.__dir_backup, 'inc')

        # 日志备份相关配置
        self.__log_backup_path = os.path.join(self.__backup_path, 'log')
        self.__website_log_backup_path = os.path.join(self.__log_backup_path, 'website')
        self.__mysql_log_backup_path = os.path.join(self.__log_backup_path, 'mysql')
        self.__secure_log_backup_path = os.path.join(self.__log_backup_path, 'secure')
        self.__messages_log_backup_path = os.path.join(self.__log_backup_path, 'messages')

        # 保存数据库记录的文件夹
        self.__db_record_path = os.path.join(self.__plugin_path, 'data')
        if not os.path.exists(self.__db_record_path):
            os.makedirs(self.__db_record_path, 384)
        # 创建备份目录
        if not os.path.exists(self.__backup_path):
            os.makedirs(self.__backup_path, 384)
        # 创建数据库备份目录
        if not os.path.exists(self.__database_path):
            os.makedirs(self.__database_path, 384)
        # 创建数据库全量备份目录
        if not os.path.exists(self.__full_backup_path):
            os.makedirs(self.__full_backup_path, 384)
        # 创建数据库ddl备份目录
        if not os.path.exists(self.__ddl_backup_path):
            os.makedirs(self.__ddl_backup_path, 384)
        # 创建数据库全量备份最后一次备份目录
        if not os.path.exists(self.__last_full_backup_path):
            os.makedirs(self.__last_full_backup_path, 384)
        # 创建数据库增量备份目录
        if not os.path.exists(self.__inc_backup_path):
            os.makedirs(self.__inc_backup_path, 384)
        # 创建目录备份相关目录
        if not os.path.exists(self.__dir_backup):
            os.makedirs(self.__dir_backup, 384)
        if not os.path.exists(self.__dir_full_backup):
            os.makedirs(self.__dir_full_backup, 384)
        if not os.path.exists(self.__dir_last_full_backup):
            os.makedirs(self.__dir_last_full_backup, 384)
        if not os.path.exists(self.__dir_inc_backup):
            os.makedirs(self.__dir_inc_backup, 384)
        # 创建日志备份相关目录
        if not os.path.exists(self.__log_backup_path):
            os.makedirs(self.__log_backup_path, 384)
        if not os.path.exists(self.__website_log_backup_path):
            os.makedirs(self.__website_log_backup_path, 384)
        if not os.path.exists(self.__mysql_log_backup_path):
            os.makedirs(self.__mysql_log_backup_path, 384)
        if not os.path.exists(self.__secure_log_backup_path):
            os.makedirs(self.__secure_log_backup_path, 384)
        if not os.path.exists(self.__messages_log_backup_path):
            os.makedirs(self.__messages_log_backup_path, 384)

        # 将xtrabackup进程添加到系统加固白名单
        self._add_process_white('xtrabackup')

    # 增加进程到系统加固白名单
    def _add_process_white(self, process_name):
        if os.path.exists('/www/server/panel/plugin/syssafe'):
            sys.path.append('/www/server/panel/plugin/syssafe')
            from syssafe_main import syssafe_main

            get = public.dict_obj()
            c = syssafe_main()
            get.process_name = process_name
            c.add_process_white(get)

    # 创建表
    def create_table(self):
        # 创建mysql_backup_setting表储存需要备份的数据库
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'mysql_backup_setting')).count():
            public.M('').execute('''CREATE TABLE "mysql_backup_setting" (
                        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                        "database" TEXT,
                        "full_backup_type" TEXT,
                        "full_backup_week" INTEGER,
                        "full_backup_hour" INTEGER,
                        "full_backup_minute" INTEGER,
                        "full_backup_save" INTEGER,
                        "inc_backup_need" INTEGER DEFAULT 1,
                        "inc_backup_type" TEXT,
                        "inc_backup_hour" INTEGER,
                        "inc_backup_minute" INTEGER,
                        "inc_backup_save" INTEGER,
                        "upload_local" INTEGER DEFAULT 1,
                        "upload_ftp" INTEGER DEFAULT 0,
                        "upload_alioss" INTEGER DEFAULT 0,
                        "upload_txcos" INTEGER DEFAULT 0,
                        "upload_qiniu" INTEGER DEFAULT 0,
                        "upload_aws" INTEGER DEFAULT 0,
                        "status"  INTEGER DEFAULT 1,
                        "addtime" INTEGER);''')
        # 修复之前已经创建的mysql_backup_setting表无upload_local字段的问题
        create_table_str = public.M('sqlite_master').where('type=? AND name=?', ('table', 'mysql_backup_setting')).getField('sql')
        if 'upload_local' not in create_table_str:
            public.M('').execute('ALTER TABLE "mysql_backup_setting" ADD "upload_local" INTEGER DEFAULT 1')
        # 修复之前已经创建的mysql_backup_setting表无inc_backup_need字段的问题
        if 'inc_backup_need' not in create_table_str:
            public.M('').execute('ALTER TABLE "mysql_backup_setting" ADD "inc_backup_need" INTEGER DEFAULT 1')
        # 修复之前已经创建的mysql_backup_setting表无upload_aws字段的问题
        if 'upload_aws' not in create_table_str:
            public.M('').execute('ALTER TABLE "mysql_backup_setting" ADD "upload_aws" INTEGER DEFAULT 0')

        # 创建mysql_full_backup表储存mysql全量备份记录
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'mysql_full_backup')).count():
            public.M('').execute('''CREATE TABLE "mysql_full_backup" (
                        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                        "sid" INTEGER,
                        "file_path" TEXT,
                        "tar_pass" TEXT,
                        "addtime" INTEGER,
                        "cost_time" INTEGER);''')

        # 创建mysql_inc_backup表储存mysql增量备份记录
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'mysql_inc_backup')).count():
            public.M('').execute('''CREATE TABLE "mysql_inc_backup" (
                            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                            "fid" INTEGER,
                            "sid" INTEGER,
                            "inc_file_path" TEXT,
                            "full_file_path" TEXT,
                            "tar_pass" TEXT,
                            "addtime" INTEGER,
                            "cost_time" INTEGER);''')

        # 创建path_backup_setting表储存需要进行备份的目录以及排除规则
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'path_backup_setting')).count():
            public.M('').execute('''CREATE TABLE "path_backup_setting" (
                                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                "path" TEXT,
                                "exclude" TEXT,
                                "full_backup_type" TEXT,
                                "full_backup_week" INTEGER,
                                "full_backup_hour" INTEGER,
                                "full_backup_minute" INTEGER,
                                "full_backup_save" INTEGER,
                                "inc_backup_need" INTEGER DEFAULT 1,
                                "inc_backup_type" TEXT DEFAULT '',
                                "inc_backup_hour" INTEGER DEFAULT 0,
                                "inc_backup_minute" INTEGER DEFAULT 0,
                                "inc_backup_save" INTEGER DEFAULT 0,
                                "upload_local" INTEGER DEFAULT 1,
                                "upload_ftp" INTEGER DEFAULT 0,
                                "upload_alioss" INTEGER DEFAULT 0,
                                "upload_txcos" INTEGER DEFAULT 0,
                                "upload_qiniu" INTEGER DEFAULT 0,
                                "upload_aws" INTEGER DEFAULT 0,
                                "status"  INTEGER DEFAULT 1,
                                "addtime" INTEGER);''')
        # 修复之前已经创建的path_backup_setting表无upload_local字段的问题
        create_table_str = public.M('sqlite_master').where('type=? AND name=?', ('table', 'path_backup_setting')).getField('sql')
        if 'upload_local' not in create_table_str:
            public.M('').execute('ALTER TABLE "path_backup_setting" ADD "upload_local" INTEGER DEFAULT 1')
        # 修复之前已经创建的path_backup_setting表无inc_backup_need字段的问题
        if 'inc_backup_need' not in create_table_str:
            public.M('').execute('ALTER TABLE "path_backup_setting" ADD "inc_backup_need" INTEGER DEFAULT 1')
        # 修复之前已经创建的path_backup_setting表无upload_aws字段的问题
        if 'upload_aws' not in create_table_str:
            public.M('').execute('ALTER TABLE "path_backup_setting" ADD "upload_aws" INTEGER DEFAULT 0')

        # 创建path_full_backup表储存目录全量备份的记录
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'path_full_backup')).count():
            public.M('').execute('''CREATE TABLE "path_full_backup" (
                        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                        "sid" INTEGER,
                        "file_path" TEXT,
                        "tar_pass" TEXT,
                        "addtime" INTEGER,
                        "cost_time" INTEGER);''')

        # 创建path_inc_backup表储存目录增量备份记录
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'path_inc_backup')).count():
            public.M('').execute('''CREATE TABLE "path_inc_backup" (
                                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                "fid" INTEGER,
                                "sid" INTEGER,
                                "inc_file_path" TEXT,
                                "full_file_path" TEXT,
                                "tar_pass" TEXT,
                                "addtime" INTEGER,
                                "cost_time" INTEGER);''')

    # 获取mysql端口
    def get_mysql_port(self, get=None):
        try:
            port = panelMysql().query("show global variables like 'port'")[0][1]
            if not port:
                return 0
            else:
                return int(port)
        except:
            return 0

    # 获取mysql版本
    def get_mysql_version(self, get=None):
        try:
            return panelMysql().query("select version()")[0][0].split("-")[0].strip()
        except:
            return ''

    # 获取xtrabackup版本
    def get_xtra_version(self, get=None):
        if os.path.exists('/etc/redhat-release'):
            return public.ExecShell("rpm -qa | grep xtrabackup | awk -F '-' '{print $3}'")[0].strip()
        else:
            return public.ExecShell("dpkg -l | grep xtrabackup | awk '{print $2}'")[0].strip()

    # 获取系统信息
    def get_system_version(self, get=None):
        '''
        获取操作系统版本
        :return:
        '''
        version = public.readFile('/etc/redhat-release')
        if not version:
            version = public.readFile('/etc/issue').strip().split("\n")[0].replace('\\n', '').replace('\l', '').strip()
        else:
            version = version.replace('release ', '').replace('Linux', '').replace('(Core)', '').strip()
        return version.replace(' ', '')

    # 检查xtrabackup版本是否与mysql版本匹配
    def check_version_suitable(self, get=None):
        mysql_version = self.get_mysql_version()
        xtra_version = self.get_xtra_version()
        if not mysql_version:
            return True
        if mysql_version.startswith('5.') and '24' in xtra_version:
            return True
        if mysql_version.startswith('8.') and '80' in xtra_version:
            return True
        return False

    # 修复xtrabackup与mysql版本不匹配的问题
    def repair_version_suitable(self, get=None):
        xtra_version = self.get_xtra_version()
        if os.path.exists('/usr/bin/yum'):
            if '24' in xtra_version:
                public.ExecShell('yum remove percona-xtrabackup-24 -y')
            elif '80' in xtra_version:
                public.ExecShell('yum remove percona-xtrabackup-80 -y')
        elif os.path.exists('/usr/bin/apt-get'):
            if '24' in xtra_version:
                public.ExecShell('apt remove percona-xtrabackup-24 -y')
            elif '80' in xtra_version:
                public.ExecShell('apt remove percona-xtrabackup-80 -y')
        mysql_version = self.get_mysql_version()
        system_version = self.get_system_version().lower()
        if 'centos8' in system_version or ('redhat' in system_version and '8.' in system_version):
            if mysql_version.startswith('5.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-24-2.4.18-1.el8.x86_64.rpm {}/install/plugin/enterprise_backup/rpm/percona-xtrabackup-24-2.4.18-1.el8.x86_64.rpm -T 10
                    yum localinstall /tmp/percona-xtrabackup-24-2.4.18-1.el8.x86_64.rpm -y
                    '''.format(public.get_url())
                public.ExecShell(cmd)
            elif mysql_version.startswith('8.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-80-8.0.9-1.el8.x86_64.rpm {}/install/plugin/enterprise_backup/rpm/percona-xtrabackup-80-8.0.9-1.el8.x86_64.rpm -T 10
                    yum localinstall /tmp/percona-xtrabackup-80-8.0.9-1.el8.x86_64.rpm -y
                    '''.format(public.get_url())
                public.ExecShell(cmd)
        elif 'centos7' in system_version or ('redhat' in system_version and '7.' in system_version):
            if mysql_version.startswith('5.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-24-2.4.18-1.el7.x86_64.rpm {}/install/plugin/enterprise_backup/rpm/percona-xtrabackup-24-2.4.18-1.el7.x86_64.rpm -T 10
                    yum localinstall /tmp/percona-xtrabackup-24-2.4.18-1.el7.x86_64.rpm -y
                    '''.format(public.get_url())
                public.ExecShell(cmd)
            elif mysql_version.startswith('8.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-80-8.0.9-1.el7.x86_64.rpm {}/install/plugin/enterprise_backup/rpm/percona-xtrabackup-80-8.0.9-1.el7.x86_64.rpm -T 10
                    yum localinstall /tmp/percona-xtrabackup-80-8.0.9-1.el7.x86_64.rpm -y
                    '''.format(public.get_url())
                public.ExecShell(cmd)
        elif 'ubuntu16' in system_version:
            if mysql_version.startswith('5.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-24_2.4.18-1.xenial_amd64.deb {}/install/plugin/enterprise_backup/deb/percona-xtrabackup-24_2.4.18-1.xenial_amd64.deb -T 10
                    apt-get -f -y install
                    apt-get install libaio1 libaio-dev -y
                    dpkg -i /tmp/percona-xtrabackup-24_2.4.18-1.xenial_amd64.deb
                    '''.format(public.get_url())
                public.ExecShell(cmd)
            elif mysql_version.startswith('8.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-80_8.0.9-1.xenial_amd64.deb {}/install/plugin/enterprise_backup/deb/percona-xtrabackup-80_8.0.9-1.xenial_amd64.deb -T 10
                    apt-get -f -y install
                    apt-get install libaio1 libaio-dev -y
                    dpkg -i /tmp/percona-xtrabackup-80_8.0.9-1.xenial_amd64.deb
                    '''.format(public.get_url())
                public.ExecShell(cmd)
        elif 'ubuntu18' in system_version:
            if mysql_version.startswith('5.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-24_2.4.18-1.bionic_amd64.deb {}/install/plugin/enterprise_backup/deb/percona-xtrabackup-24_2.4.18-1.bionic_amd64.deb -T 10
                    apt-get -f -y install
                    apt-get install libaio1 libaio-dev -y
                    dpkg -i /tmp/percona-xtrabackup-24_2.4.18-1.bionic_amd64.deb
                    '''.format(public.get_url())
                public.ExecShell(cmd)
            elif mysql_version.startswith('8.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-80_8.0.9-1.bionic_amd64.deb {}/install/plugin/enterprise_backup/deb/percona-xtrabackup-80_8.0.9-1.bionic_amd64.deb -T 10
                    apt-get -f -y install
                    apt-get install libaio1 libaio-dev -y
                    dpkg -i /tmp/percona-xtrabackup-80_8.0.9-1.bionic_amd64.deb
                    '''.format(public.get_url())
                public.ExecShell(cmd)
        elif 'ubuntu20' in system_version:
            if mysql_version.startswith('5.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-24_2.4.20-1.focal_amd64.deb {}/install/plugin/enterprise_backup/deb/percona-xtrabackup-24_2.4.20-1.focal_amd64.deb -T 10
                    apt-get -f -y install
                    apt-get install libaio1 libaio-dev -y
                    dpkg -i /tmp/percona-xtrabackup-24_2.4.20-1.focal_amd64.deb
                    '''.format(public.get_url())
                public.ExecShell(cmd)
            elif mysql_version.startswith('8.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-80_8.0.12-1.focal_amd64.deb {}/install/plugin/enterprise_backup/deb/percona-xtrabackup-80_8.0.12-1.focal_amd64.deb -T 10
                    apt-get -f -y install
                    apt-get install libaio1 libaio-dev -y
                    dpkg -i /tmp/percona-xtrabackup-80_8.0.12-1.focal_amd64.deb
                    '''.format(public.get_url())
                public.ExecShell(cmd)
        elif 'debiangnu/linux10' in system_version:
            if mysql_version.startswith('5.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-24_2.4.20-1.buster_amd64.deb {}/install/plugin/enterprise_backup/deb/percona-xtrabackup-24_2.4.20-1.buster_amd64.deb -T 10
                    apt-get -f -y install
                    apt-get install libaio1 libaio-dev -y
                    dpkg -i /tmp/percona-xtrabackup-24_2.4.20-1.buster_amd64.deb
                    '''.format(public.get_url())
                public.ExecShell(cmd)
            elif mysql_version.startswith('8.'):
                cmd = '''
                    wget -O /tmp/percona-xtrabackup-80_8.0.12-1.buster_amd64.deb {}/install/plugin/enterprise_backup/deb/percona-xtrabackup-80_8.0.12-1.buster_amd64.deb -T 10
                    apt-get -f -y install
                    apt-get install libaio1 libaio-dev -y
                    dpkg -i /tmp/percona-xtrabackup-80_8.0.12-1.buster_amd64.deb
                    '''.format(public.get_url())
                public.ExecShell(cmd)
        return public.returnMsg(True, '修复完成!')

    # 检查binlog是否开启并配置为row模式
    def get_binlog_format(self, get=None):
        try:
            return panelMysql().query("show global variables like '%binlog_format%'")[0][1]
        except Exception as e:
            return str(e)

    # 检查innodb_file_per_table是否开启
    def get_innodb_file_per_table(self, get=None):
        try:
            return panelMysql().query("show global variables like '%per_table%'")[0][1]
        except Exception as e:
            return str(e)

    # 开启innodb_file_per_table设置
    def open_innodb_file_per_table(self, get=None):
        if self.get_innodb_file_per_table().upper() == 'ON':
            return public.returnMsg(True, 'innodb_file_per_table设置已经是ON状态')
        mysql_version = self.get_mysql_version()
        mycnf = public.readFile('/etc/my.cnf')
        if '5.5.' in mysql_version:
            if 'innodb_file_per_table' not in mycnf:
                mycnf = mycnf.replace("[mysqld]\n", "[mysqld]\ninnodb_file_per_table = 1\n")
                public.writeFile('/etc/my.cnf', mycnf)
                public.ExecShell('/etc/init.d/mysqld restart')
            else:
                public.ExecShell('sed -i "s#^innodb_file_per_table.*#innodb_file_per_table = 1#" /etc/my.cnf')
                public.ExecShell('/etc/init.d/mysqld restart')
        else:
            public.ExecShell('sed -i "s#^innodb_file_per_table.*#innodb_file_per_table = 1#" /etc/my.cnf')
            public.ExecShell('/etc/init.d/mysqld restart')
        return public.returnMsg(True, '开启innodb_file_per_table设置完成。注意: 开启之前的表依然使用的是共享存储空间，如果要进行备份，要使用mysqldump导出这些表的数据之后再导入')

    # 获取mysql数据库root账号密码
    def get_mysql_root(self):
        return public.M('config').where('id=?', 1).getField('mysql_root')

    # 获取mysql和xtrabackup的一些状态信息
    def get_soft_status(self, get=None):
        system_version = self.get_system_version().lower()
        if not ('centos8' in system_version or 'centos7' in system_version or 'redhat' in system_version
                or 'ubuntu16' in system_version or 'ubuntu18' in system_version or 'ubuntu20' in system_version or 'debiangnu/linux10' in system_version):
            return public.returnMsg(False, '本插件只支持CentOS7, CentOS8, Ubuntu16, Ubuntu18, Ubuntu20和debian10')
        # if not self.check_version_suitable():
        #     self.repair_version_suitable()

        soft_status = os.path.join(self.__plugin_path, 'soft_status.json')
        if int(get.act) == 1:
            data = {
                'local_path': self.__backup_path,
                'mysql_version': self.get_mysql_version(),
                'mysql_port': self.get_mysql_port(),
                'binlog_format': self.get_binlog_format(),
                'innodb_file_per_table': self.get_innodb_file_per_table(),
                'xtra_version': self.get_xtra_version(),
                'is_suitable': self.check_version_suitable()
            }
            public.writeFile(soft_status, json.dumps(data))
        else:
            if not os.path.exists(soft_status):
                data = {
                    'local_path': self.__backup_path,
                    'mysql_version': self.get_mysql_version(),
                    'mysql_port': self.get_mysql_port(),
                    'binlog_format': self.get_binlog_format(),
                    'innodb_file_per_table': self.get_innodb_file_per_table(),
                    'xtra_version': self.get_xtra_version(),
                    'is_suitable': self.check_version_suitable()
                }
                public.writeFile(soft_status, json.dumps(data))
            data = json.loads(public.readFile(soft_status))
        return data

    # 获取数据库列表
    def get_databases(self, get):
        # 判断mysql是否启动
        if not self.get_mysql_port():
            return public.returnMsg(False, '请确定数据库是否已经开启或root密码错误')
        mysql_version = self.get_mysql_version()
        if "5.1." in mysql_version or '5.5.' in mysql_version:
            return public.returnMsg(False, '本插件不支持5.6以下版本MySQL，请安装5.6或以上版本')

        data = panelMysql().query("show databases")
        databases = []
        sql = public.M('mysql_backup_setting')
        for i in data:
            if i[0] in ["information_schema", "performance_schema", "sys", "mysql"]: continue
            tmp = {}
            tmp['name'] = i[0]
            # tmp['tables'] = self.get_database_tables(i[0])
            tmp['checked'] = True if sql.where('database=?', tmp['name']).count() else False
            databases.append(tmp)
        return databases

    # 获取指定数据库包含的表
    def get_database_tables(self, db_name):
        tables = self.map_to_list(panelMysql().query('show tables from `%s`' % db_name))
        data = [item[0] for item in tables]
        return data

    # map to list
    def map_to_list(self, map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except:
            return []

    # 获取数据库备份设置列表
    def get_mysql_backup_setting_list(self, get):
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 8
        callback = get.callback if 'callback' in get else ''

        count = public.M('mysql_backup_setting').count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('mysql_backup_setting').order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    # 增加数据库备份设置
    def add_mysql_backup_setting(self, get):
        pdata = {}
        pdata['database'] = get.database.strip()
        if public.M('mysql_backup_setting').where('database=?', get.database).count():
            return public.returnMsg(False, '指定的数据库或者表已经存在备份，不能重复设置')
        pdata['full_backup_type'] = get.full_backup_type
        pdata['full_backup_week'] = get.full_backup_week if 'full_backup_week' in get else ''
        pdata['full_backup_hour'] = get.full_backup_hour
        pdata['full_backup_minute'] = get.full_backup_minute
        pdata['full_backup_save'] = get.full_backup_save
        pdata['inc_backup_need'] = get.inc_backup_need
        if get.inc_backup_need == '1':
            pdata['inc_backup_type'] = get.inc_backup_type
            pdata['inc_backup_hour'] = get.inc_backup_hour if 'inc_backup_hour' in get else ''
            pdata['inc_backup_minute'] = get.inc_backup_minute
            pdata['inc_backup_save'] = get.inc_backup_save
        if 'upload_ftp' in get: pdata['upload_ftp'] = get.upload_ftp
        if 'upload_alioss' in get: pdata['upload_alioss'] = get.upload_alioss
        if 'upload_txcos' in get: pdata['upload_txcos'] = get.upload_txcos
        if 'upload_qiniu' in get: pdata['upload_qiniu'] = get.upload_qiniu
        if 'upload_aws' in get: pdata['upload_aws'] = get.upload_aws
        if 'upload_local' in get: pdata['upload_local'] = get.upload_local
        pdata['status'] = 1
        pdata['addtime'] = int(time.time())
        pdata['id'] = public.M('mysql_backup_setting').insert(pdata)
        self.add_mysql_full_backup_task(pdata)
        if get.inc_backup_need == '1':
            self.add_mysql_inc_backup_task(pdata)
        public.WriteLog(self.__log_type, "创建数据库备份[{}]".format(pdata['database']))
        return public.returnMsg(True, '添加成功!')

    # 批量添加数据库备份
    def batch_add_mysql_backup_setting(self, get):
        database_list = json.loads(get.database)
        for database in database_list:
            get.database = database.strip()
            self.add_mysql_backup_setting(get)
        return public.returnMsg(True, '批量添加成功!')

    # 增加mysql全量备份定时任务
    def add_mysql_full_backup_task(self, pdata):
        p = crontab.crontab()
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        args = {
            "name": "[勿删]企业级备份-数据库全量备份任务[{}]".format(pdata['database']),
            "type": pdata['full_backup_type'],
            "where1": '',
            "hour": pdata['full_backup_hour'],
            "minute": pdata['full_backup_minute'],
            "week": pdata['full_backup_week'],
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": pdata['full_backup_save'],
            "sBody": '{} {}/crontab_tasks/mysql_full_backup.py {}'.format(python_path, self.__plugin_path, pdata['id']),
            "urladdress": "undefined"
        }
        p.AddCrontab(args)

    # 增加mysql增量备份定时任务
    def add_mysql_inc_backup_task(self, pdata):
        p = crontab.crontab()
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        args = {
            "name": "[勿删]企业级备份-数据库增量备份任务[{}]".format(pdata['database']),
            "type": pdata['inc_backup_type'],
            "where1": '',
            "hour": pdata['inc_backup_hour'],
            "minute": pdata['inc_backup_minute'],
            "week": '',
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": pdata['inc_backup_save'],
            "sBody": '{} {}/crontab_tasks/mysql_inc_backup.py {}'.format(python_path, self.__plugin_path, pdata['id']),
            "urladdress": "undefined"
        }
        p.AddCrontab(args)

    # 更新数据库备份设置
    def modify_mysql_backup_setting(self, get):
        if 'id' not in get: return public.returnMsg(False, '错误的参数!')
        pdata = {}
        pdata['full_backup_type'] = get.full_backup_type
        pdata['full_backup_week'] = get.full_backup_week if 'full_backup_week' in get else ''
        pdata['full_backup_hour'] = get.full_backup_hour
        pdata['full_backup_minute'] = get.full_backup_minute
        pdata['full_backup_save'] = get.full_backup_save
        pdata['inc_backup_need'] = get.inc_backup_need
        old_data = public.M('mysql_backup_setting').where('id=?', get.id).find()
        if get.inc_backup_need == '1':
            pdata['inc_backup_type'] = get.inc_backup_type
            pdata['inc_backup_hour'] = get.inc_backup_hour if 'inc_backup_hour' in get else ''
            pdata['inc_backup_minute'] = get.inc_backup_minute
            pdata['inc_backup_save'] = get.inc_backup_save
            pdata['database'] = old_data['database']
            pdata['id'] = int(get.id)
            if int(old_data['inc_backup_need']) == 0:
                self.add_mysql_inc_backup_task(pdata)
        else:
            # 如果之前设置了增量备份，删除之前的增量备份计划任务
            if int(old_data['inc_backup_need']) == 1:
                p = crontab.crontab()
                c_id = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(old_data['database'])).getField('id')
                args = {"id": c_id}
                p.DelCrontab(args)
        if 'upload_ftp' in get: pdata['upload_ftp'] = get.upload_ftp
        if 'upload_alioss' in get: pdata['upload_alioss'] = get.upload_alioss
        if 'upload_txcos' in get: pdata['upload_txcos'] = get.upload_txcos
        if 'upload_qiniu' in get: pdata['upload_qiniu'] = get.upload_qiniu
        if 'upload_aws' in get: pdata['upload_aws'] = get.upload_aws
        if 'upload_local' in get: pdata['upload_local'] = get.upload_local
        if 'status' in get: pdata['status'] = get.status

        public.M('mysql_backup_setting').where('id=?', int(get.id)).update(pdata)
        pdata = public.M('mysql_backup_setting').where('id=?', get.id).find()
        self.modify_mysql_full_backup_task(pdata)
        if get.inc_backup_need == '1':
            self.modify_mysql_inc_backup_task(pdata)
        public.WriteLog(self.__log_type, "修改数据库备份[{}]".format(pdata['database']))
        return public.returnMsg(True, '编辑成功')

    # 修改mysql全量备份定时任务
    def modify_mysql_full_backup_task(self, pdata):
        p = crontab.crontab()
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        args = {
            "id": public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(pdata['database'])).getField('id'),
            "name": "[勿删]企业级备份-数据库全量备份任务[{}]".format(pdata['database']),
            "type": pdata['full_backup_type'],
            "where1": '',
            "hour": pdata['full_backup_hour'],
            "minute": pdata['full_backup_minute'],
            "week": pdata['full_backup_week'],
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": pdata['full_backup_save'],
            "sBody": '{} {}/crontab_tasks/mysql_full_backup.py {}'.format(python_path, self.__plugin_path, pdata['id']),
            "urladdress": "undefined",
            "status": pdata['status']
        }
        p.modify_crond(args)

    # 修改mysql增量备份定时任务
    def modify_mysql_inc_backup_task(self, pdata):
        p = crontab.crontab()
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        args = {
            "id": public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(pdata['database'])).getField('id'),
            "name": "[勿删]企业级备份-数据库增量备份任务[{}]".format(pdata['database']),
            "type": pdata['inc_backup_type'],
            "where1": '',
            "hour": pdata['inc_backup_hour'],
            "minute": pdata['inc_backup_minute'],
            "week": '',
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": pdata['inc_backup_save'],
            "sBody": '{} {}/crontab_tasks/mysql_inc_backup.py {}'.format(python_path, self.__plugin_path, pdata['id']),
            "urladdress": "undefined",
            "status": pdata['status']
        }
        p.modify_crond(args)

    # 更新数据库备份任务状态
    def modify_mysql_backup_setting_status(self, get):
        if 'id' not in get: return public.returnMsg(False, '错误的参数!')
        pdata = {}
        pdata['status'] = get.status

        public.M('mysql_backup_setting').where('id=?', int(get.id)).setField('status', pdata['status'])
        pdata = public.M('mysql_backup_setting').where('id=?', get.id).find()
        self.modify_mysql_full_backup_task_status(pdata)
        if int(pdata['inc_backup_need']) == 1:
            self.modify_mysql_inc_backup_task_status(pdata)
        public.WriteLog(self.__log_type, "修改数据库备份[{}]状态为{}".format(pdata['database'], pdata['status']))
        return public.returnMsg(True, '编辑成功')

    # 修改mysql全量备份定时任务
    def modify_mysql_full_backup_task_status(self, pdata):
        p = crontab.crontab()
        args = {
            "id": public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(pdata['database'])).getField('id'),
        }
        p.set_cron_status(args)

    # 修改mysql增量备份定时任务
    def modify_mysql_inc_backup_task_status(self, pdata):
        p = crontab.crontab()
        args = {
            "id": public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(pdata['database'])).getField('id'),
        }
        p.set_cron_status(args)

    # 删除数据库备份设置
    def delete_mysql_backup_setting(self, get):
        if 'id' not in get: return public.returnMsg(False, '错误的参数!')
        id = get.id
        pdata = public.M('mysql_backup_setting').where('id=?', id).find()
        # 删除计划任务
        self.remove_mysql_backup_task(pdata)

        self.remove_dir(os.path.join(self.__last_full_backup_path, pdata['database']))
        self.remove_dir(os.path.join(self.__ddl_backup_path, pdata['database']))
        # 删除与之关联的全量备份记录
        full_backup_delete = public.M('mysql_full_backup').where('sid=?', get.id).field('id').select()
        for item in full_backup_delete:
            self.delete_mysql_full_backup(item['id'])

        # 删除与之关联的增量备份记录
        inc_backup_delete = public.M('mysql_inc_backup').where('sid=?', get.id).field('id').select()
        for item in inc_backup_delete:
            self.delete_mysql_inc_backup(item['id'])

        public.M('mysql_backup_setting').where('id=?', id).delete()
        public.WriteLog(self.__log_type, "删除数据库备份[{}]".format(pdata['database']))
        return public.returnMsg(True, '删除成功!')

    # 删除计划任务
    def remove_mysql_backup_task(self, pdata):
        p = crontab.crontab()
        id = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(pdata['database'])).getField('id')
        args = {"id": id}
        p.DelCrontab(args)
        id = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(pdata['database'])).getField('id')
        args = {"id": id}
        p.DelCrontab(args)

    # 获取mysql数据存储路径
    def get_mysql_datadir(self, get=None):
        from database import database
        mysql_info = database().GetMySQLInfo(get)
        return mysql_info['datadir'] if 'datadir' in mysql_info else '/www/server/data'

    # 删除目录
    def remove_dir(self, dir):
        if os.path.exists(dir):
            shutil.rmtree(dir)

    # 删除数据库或者指定表的表空间
    def discard_tablespace(self, database):
        # 如果是数据库，删除数据库所有表的表空间
        if '.' not in database:
            db_tables = self.get_database_tables(database)
            print('删除数据库', database, '所有表的表空间：', db_tables)
            for table_name in db_tables:
                public.writeFile(self.__mysql_restore_log_file, '删除数据库[{}]中表[{}]的表空间\n'.format(database, table_name), 'a+')
                MyPanelMysql().execute_many('set session sql_log_bin = 0;alter table `%s`.`%s` discard tablespace' % (database, table_name))
        else:
            MyPanelMysql().execute_many('set session sql_log_bin = 0;alter table `%s` discard tablespace' % database)

    # 从备份中拷贝表信息文件到数据库目录下
    def copy_back(self, database, backup_path):
        mysql_datadir = self.get_mysql_datadir()
        # 拷贝数据库的所有表信息文件
        if '.' not in database:
            src = os.path.join(backup_path, database)
            dst = os.path.join(mysql_datadir, database)
            public.writeFile(self.__mysql_restore_log_file, '将数据库[{}]的数据文件从[{}]拷贝到[{}]\n'.format(database, src, dst), 'a+')
            public.ExecShell('\cp -a -r {}/* {}'.format(src, dst))
            public.ExecShell('cd {} && rm -rf *.cfg && rm -rf *.exp'.format(os.path.join(mysql_datadir, database)))
        else:
            db_name, table_name = database.split('.')
            public.ExecShell('\cp -a -r {}/{}* {}'.format(os.path.join(backup_path, db_name), table_name, os.path.join(mysql_datadir, db_name)))
            public.ExecShell('cd {} && rm -rf *.cfg && rm -rf *.exp'.format(os.path.join(mysql_datadir, db_name)))

    # 导入表空间
    def import_tablespace(self, database):
        # 如果是数据库，导入数据库所有表的表空间
        if '.' not in database:
            db_tables = self.get_database_tables(database)
            print('导入数据库', database, '所有表的表空间：', db_tables)
            for table_name in db_tables:
                public.writeFile(self.__mysql_restore_log_file, '导入数据库[{}]中表[{}]的表空间\n'.format(database, table_name), 'a+')
                MyPanelMysql().execute_many('set session sql_log_bin = 0;alter table `%s`.`%s` import tablespace' % (database, table_name))
        else:
            MyPanelMysql().execute_many('set session sql_log_bin = 0;alter table `%s` import tablespace' % database)

    # mysql全量备份恢复
    def mysql_full_backup_restore(self, get):
        if os.path.exists(self.__mysql_restore_log_file):
            return public.returnMsg(False, '有其他数据库恢复任务在执行，请等待其执行完成')

        backup_info = public.M('mysql_full_backup').where('id=?', get.id).find()
        setting_info = public.M('mysql_backup_setting').where('id=?', backup_info['sid']).find()
        backup_obj = setting_info['database']
        backup_file = backup_info['file_path']
        tar_pass = backup_info['tar_pass']
        public.writeFile(self.__mysql_restore_log_file, "数据库[{}]使用文件[{}]开始全量备份恢复\n".format(backup_obj, backup_file))

        # 如果此数据库有全量备份任务在执行，等待全量备份任务完成
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(backup_obj)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '数据库[{}]全量备份任务正在进行中，此时无法进行恢复操作'.format(backup_obj))

        if int(setting_info['inc_backup_need']) == 1:
            # 如果此数据库有增量备份任务在执行，等待增量备份任务完成
            echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(backup_obj)).getField('echo')
            execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
            if self.process_exists(execstr):
                os.remove(self.__mysql_restore_log_file)
                return public.returnMsg(False, '数据库[{}]增量备份任务正在进行中，此时无法进行恢复操作'.format(backup_obj))

        # 如果本地不存在数据库全量备份文件，先从云端下载
        self.get_mysql_full_backup_info(get.id)
        if not os.path.exists(backup_file):
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '请检查本地和云端是否都不存在全量备份文件{}'.format(backup_file))

        # 解压全量备份文件
        full_backup_path = backup_file.replace('.tar.gz', '')
        result = self.uncompress_dir(backup_file, tar_pass, self.__mysql_restore_log_file)
        if not result['status']:
            self.remove_dir(full_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return result

        date_time = time.strftime("%Y-%m-%d-%H", time.localtime(backup_info['addtime']))
        # 恢复数据
        try:
            # 导出表信息
            export_cmd = 'xtrabackup --prepare --export --target-dir={0} >> {1} 2>&1'.format(full_backup_path, self.__mysql_restore_log_file)
            public.writeFile(self.__mysql_restore_log_file, '导出表信息命令：{}\n'.format(export_cmd), 'a+')
            public.ExecShell(export_cmd)
            output = public.GetNumLines(self.__mysql_restore_log_file, 10)
            if 'completed OK!' not in output:
                self.remove_dir(full_backup_path)
                os.remove(self.__mysql_restore_log_file)
                return public.returnMsg(False, '导出表信息失败，原因：{0}'.format(output))
            # 恢复数据库或者表的表结构
            result = self.mysql_ddl_restore(backup_obj, date_time)
            if not result['status']:
                self.remove_dir(full_backup_path)
                os.remove(self.__mysql_restore_log_file)
                return result
            # 删除表空间
            self.discard_tablespace(backup_obj)
            mysql_datadir = self.get_mysql_datadir()
            # # 备份旧的数据库文件
            # self.remove_dir(mysql_datadir + '_bak')
            # shutil.copytree(mysql_datadir, mysql_datadir + '_bak')
            # 拷贝表信息文件到数据库目录下
            self.copy_back(backup_obj, full_backup_path)
            # 修改目录权限
            public.ExecShell('chown -R mysql.mysql {}'.format(mysql_datadir))
            # 导入表空间
            self.import_tablespace(backup_obj)
            # 删除解压出来的备份目录
            self.remove_dir(full_backup_path)
            # 如果恢复的是mysql数据库或者mysql.user表，要恢复之前的root密码
            if 'mysql' == backup_obj or 'mysql.user' == backup_obj:
                from database import database
                get.password = self.get_mysql_root()
                database().SetupPassword(get)
            public.writeFile(self.__mysql_restore_log_file, "备份恢复之后要进行一次全量备份", 'a+')
            self.start_mysql_full_backup_task_d(backup_obj)
            public.writeFile(self.__mysql_restore_log_file, "数据库[{}]使用文件[{}]完成全量备份恢复\n".format(backup_obj, backup_file), 'a+')
            os.remove(self.__mysql_restore_log_file)
            public.WriteLog(self.__log_type, "数据库[{}]使用文件[{}]完成全量备份恢复".format(backup_obj, backup_file))
            return public.returnMsg(True, '恢复[{}]的数据完成'.format(backup_obj))
        except:
            self.remove_dir(full_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '恢复[{}]的数据发生错误：{}'.format(backup_obj, public.get_error_info()))

    # 检查全量备份和增量备份是否匹配
    def check_backup_suitabe(self, get=None):
        full_checkpoints = public.readFile(os.path.join(get.full_backup_path, 'xtrabackup_checkpoints'))
        full_to_lsn = re.search('to_lsn = (\d+)', full_checkpoints).group(1)
        return full_to_lsn

    # 使用指定路径进行mysql全量备份恢复
    def mysql_restore_by_file(self, get):
        if os.path.exists(self.__mysql_restore_log_file):
            return public.returnMsg(False, '有其他数据库恢复任务在执行，请等待其执行完成')

        backup_obj = get.database.strip()
        setting_info = public.M('mysql_backup_setting').where('database=?', backup_obj).find()
        backup_file = get.path.strip()
        public.writeFile(self.__mysql_restore_log_file, "数据库[{}]使用文件[{}]开始全量备份恢复\n".format(backup_obj, backup_file))

        # 如果此数据库有全量备份任务在执行，等待全量备份任务完成
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(backup_obj)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '数据库[{}]全量备份任务正在进行中，此时无法进行恢复操作'.format(backup_obj))

        if int(setting_info['inc_backup_need']) == 1:
            # 如果此数据库有增量备份任务在执行，等待增量备份任务完成
            echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(backup_obj)).getField('echo')
            execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
            if self.process_exists(execstr):
                os.remove(self.__mysql_restore_log_file)
                return public.returnMsg(False, '数据库[{}]增量备份任务正在进行中，此时无法进行恢复操作'.format(backup_obj))

        if not os.path.exists(backup_file):
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '请检查本地和云端是否都不存在全量备份文件{}'.format(backup_file))

        # 解压全量备份文件
        full_backup_path = backup_file.replace('.tar.gz', '')
        result = self.uncompress_dir(backup_file, '', self.__mysql_restore_log_file)
        if not result['status']:
            self.remove_dir(full_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return result

        # 恢复数据
        try:
            # 导出表信息
            export_cmd = 'xtrabackup --prepare --export --target-dir={0} >> {1} 2>&1'.format(full_backup_path, self.__mysql_restore_log_file)
            public.writeFile(self.__mysql_restore_log_file, '导出表信息命令：{}\n'.format(export_cmd), 'a+')
            public.ExecShell(export_cmd)
            output = public.GetNumLines(self.__mysql_restore_log_file, 10)
            if 'completed OK!' not in output:
                self.remove_dir(full_backup_path)
                os.remove(self.__mysql_restore_log_file)
                return public.returnMsg(False, '导出表信息失败，原因：{0}'.format(output))
            # 恢复数据库或者表的表结构
            date_time = '-'.join(os.path.basename(backup_file).replace('_', '-').split('-')[:4])
            print(date_time)
            result = self.mysql_ddl_restore(backup_obj, date_time)
            if not result['status']:
                self.remove_dir(full_backup_path)
                os.remove(self.__mysql_restore_log_file)
                return result
            # 删除表空间
            self.discard_tablespace(backup_obj)
            mysql_datadir = self.get_mysql_datadir()
            # 拷贝表信息文件到数据库目录下
            self.copy_back(backup_obj, full_backup_path)
            # 修改目录权限
            public.ExecShell('chown -R mysql.mysql {}'.format(mysql_datadir))
            # 导入表空间
            self.import_tablespace(backup_obj)
            # 删除解压出来的备份目录
            self.remove_dir(full_backup_path)
            public.writeFile(self.__mysql_restore_log_file, "备份恢复之后要进行一次全量备份", 'a+')
            self.start_mysql_full_backup_task_d(backup_obj)
            public.writeFile(self.__mysql_restore_log_file, "数据库[{}]使用文件[{}]完成全量备份恢复\n".format(backup_obj, backup_file), 'a+')
            os.remove(self.__mysql_restore_log_file)
            public.WriteLog(self.__log_type, "数据库[{}]使用文件[{}]完成全量备份恢复".format(backup_obj, backup_file))
            return public.returnMsg(True, '恢复[{}]的数据完成'.format(backup_obj))
        except:
            self.remove_dir(full_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '恢复[{}]的数据发生错误：{}'.format(backup_obj, public.get_error_info()))

    # mysql增量备份恢复
    def mysql_inc_backup_restore(self, get):
        if os.path.exists(self.__mysql_restore_log_file):
            return public.returnMsg(False, '有其他数据库恢复任务在执行，请等待其执行完成')

        backup_info = public.M('mysql_inc_backup').where('id=?', get.id).find()
        inc_file_path = backup_info['inc_file_path']
        full_file_path = backup_info['full_file_path']
        setting_info = public.M('mysql_backup_setting').where('id=?', backup_info['sid']).find()
        backup_obj = setting_info['database']
        public.writeFile(self.__mysql_restore_log_file, "数据库[{}]使用文件[{}]开始增量备份恢复\n".format(backup_obj, inc_file_path))

        # 如果此数据库有全量备份任务在执行，等待全量备份任务完成
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(backup_obj)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '数据库[{}]全量备份任务正在进行中，此时无法进行恢复操作'.format(backup_obj))

        # 如果此数据库有增量备份任务在执行，等待增量备份任务完成
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(backup_obj)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '数据库[{}]增量备份任务正在进行中，此时无法进行恢复操作'.format(backup_obj))

        # 如果本地不存在全量备份文件，先从云端下载
        self.get_mysql_full_backup_info(backup_info['fid'])
        if not os.path.exists(full_file_path):
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '请检查本地和云端是否都不存在全量备份文件{}'.format(full_file_path))
        # 解压全量备份文件
        full_tar_pass = public.M('mysql_full_backup').where('file_path=?', full_file_path).order('id desc').field('tar_pass').find()['tar_pass']
        full_backup_path = full_file_path.replace('.tar.gz', '')
        result = self.uncompress_dir(full_file_path, full_tar_pass, self.__mysql_restore_log_file)
        if not result['status']:
            self.remove_dir(full_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return result

        # 如果本地不存在增量备份文件，先从云端下载
        self.get_mysql_inc_backup_info(get.id)
        if not os.path.exists(inc_file_path):
            self.remove_dir(full_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '请检查本地和云端是否都不存在增量备份文件{}'.format(inc_file_path))
        # 解压增量备份文件
        inc_tar_pass = backup_info['tar_pass']
        inc_backup_path = inc_file_path.replace('.tar.gz', '')
        result = self.uncompress_dir(inc_file_path, inc_tar_pass, self.__mysql_restore_log_file)
        if not result['status']:
            self.remove_dir(full_backup_path)
            self.remove_dir(inc_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return result

        # 合并增量备份到全量备份目录
        # 准备全备份
        prepare_full_cmd = 'xtrabackup --prepare --apply-log-only --target-dir={0} >> {1} 2>&1'.format(full_backup_path, self.__mysql_restore_log_file)
        public.writeFile(self.__mysql_restore_log_file, '准备全量备份命令：{}\n'.format(prepare_full_cmd), 'a+')
        public.ExecShell(prepare_full_cmd)
        output = public.GetNumLines(self.__mysql_restore_log_file, 10)
        if 'completed OK!' not in output:
            self.remove_dir(full_backup_path)
            self.remove_dir(inc_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '准备全备份失败，原因：{0}'.format(output))
        # 准备增量备份
        prepare_inc_cmd = 'xtrabackup --prepare --apply-log-only --target-dir={0} --incremental-dir={1} >> {2} 2>&1'.format(full_backup_path, inc_backup_path, self.__mysql_restore_log_file)
        public.writeFile(self.__mysql_restore_log_file, '准备增量备份命令：{}\n'.format(prepare_inc_cmd), 'a+')
        public.ExecShell(prepare_inc_cmd)
        output = public.GetNumLines(self.__mysql_restore_log_file, 10)
        if 'completed OK!' not in output:
            self.remove_dir(full_backup_path)
            self.remove_dir(inc_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '准备增量备份失败，原因：{0}'.format(output))

        # 恢复数据
        date_time = time.strftime("%Y-%m-%d-%H", time.localtime(backup_info['addtime']))
        try:
            # 导出表信息
            export_cmd = 'xtrabackup --prepare --export --target-dir={0} >> {1} 2>&1'.format(full_backup_path, self.__mysql_restore_log_file)
            public.writeFile(self.__mysql_restore_log_file, '导出表信息命令：{}\n'.format(export_cmd), 'a+')
            public.ExecShell(export_cmd)
            output = public.GetNumLines(self.__mysql_restore_log_file, 10)
            if 'completed OK!' not in output:
                self.remove_dir(full_backup_path)
                self.remove_dir(inc_backup_path)
                os.remove(self.__mysql_restore_log_file)
                return public.returnMsg(False, '导出表信息失败，原因：{0}'.format(output))
            # 恢复数据库或者表的表结构
            result = self.mysql_ddl_restore(backup_obj, date_time)
            if not result['status']:
                self.remove_dir(full_backup_path)
                self.remove_dir(inc_backup_path)
                os.remove(self.__mysql_restore_log_file)
                return result
            # 删除表空间
            self.discard_tablespace(backup_obj)
            mysql_datadir = self.get_mysql_datadir()
            # # 备份旧的数据库文件
            # self.remove_dir(mysql_datadir + '_bak')
            # shutil.copytree(mysql_datadir, mysql_datadir + '_bak')
            # 拷贝表信息文件到数据库目录下
            self.copy_back(backup_obj, full_backup_path)
            # 修改目录权限
            public.ExecShell('chown -R mysql.mysql {}'.format(mysql_datadir))
            # 导入表空间
            self.import_tablespace(backup_obj)
            # 删除解压出来的备份目录
            self.remove_dir(full_backup_path)
            self.remove_dir(inc_backup_path)
            # 如果恢复的是mysql数据库或者mysql.user表，要恢复之前的root密码
            if 'mysql' == backup_obj or 'mysql.user' == backup_obj:
                from database import database
                get.password = self.get_mysql_root()
                database().SetupPassword(get)
            public.writeFile(self.__mysql_restore_log_file, "备份恢复之后要进行一次全量备份", 'a+')
            self.start_mysql_full_backup_task_d(backup_obj)
            public.writeFile(self.__mysql_restore_log_file, "数据库[{}]使用文件[{}]完成增量备份恢复\n".format(backup_obj, inc_file_path), 'a+')
            os.remove(self.__mysql_restore_log_file)
            public.WriteLog(self.__log_type, "数据库[{}]使用文件[{}]完成增量备份恢复".format(backup_obj, inc_file_path))
            return public.returnMsg(True, '恢复[{}]的数据完成'.format(backup_obj))
        except:
            self.remove_dir(full_backup_path)
            self.remove_dir(inc_backup_path)
            os.remove(self.__mysql_restore_log_file)
            return public.returnMsg(False, '恢复[{}]的数据发生错误：{}'.format(backup_obj, public.get_error_info()))

    # 获取mysql数据库备份日志
    def get_mysql_backup_output(self, get):
        inc_backup_log_file = self.__mysql_backup_log_file + str(get.id) + '_inc'
        full_backup_log_file = self.__mysql_backup_log_file + str(get.id) + '_full'
        # 判断备份是否进行
        setting_info = public.M('mysql_backup_setting').where('id=?', get.id).find()
        backup_obj = setting_info['database']
        if int(setting_info['inc_backup_need']) == 1:
            echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(backup_obj)).getField('echo')
        else:
            echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(backup_obj)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(True, public.GetNumLines(inc_backup_log_file, 500) + public.GetNumLines(full_backup_log_file, 500))
        else:
            return public.returnMsg(False, '')

    # 获取mysql数据库恢复日志
    def get_mysql_restore_output(self, get):
        if os.path.exists(self.__mysql_restore_log_file):
            return public.returnMsg(True, public.GetNumLines(self.__mysql_restore_log_file, 500))
        else:
            return public.returnMsg(False, '')

    # 解压加密压缩的文件夹
    def uncompress_dir(self, tgz_file, tar_pass, backup_log_file=None):
        encrypt = False
        if os.path.exists(self.__encrypt_file):
            encrypt = True
        if not os.path.exists('/usr/bin/openssl'):
            if os.path.exists('/usr/bin/yum'):
                public.ExecShell('yum install openssl -y')
            elif os.path.exists('/usr/bin/apt'):
                public.ExecShell('apt install openssl -y')
        tgz_file = tgz_file.strip()
        try:
            public.writeFile(backup_log_file, '解压文件[{}]\n'.format(tgz_file), 'a+')
            if encrypt:
                cmd = 'cd {0} && openssl des3 -d -k {1} -salt -in {2} | tar xzvf - >> {3} 2>&1'.format(os.path.dirname(tgz_file), tar_pass, tgz_file, backup_log_file)
            else:
                cmd = 'cd {0} && tar xzvf {1} >> {2} 2>&1'.format(os.path.dirname(tgz_file), tgz_file, backup_log_file)
            public.ExecShell(cmd)
            path_size = public.get_path_size(tgz_file.replace('.tar.gz', ''))
            # 检查解压出来的文件夹是否有效
            if path_size > 100:
                return public.returnMsg(True, '解压缩文件{}完成'.format(tgz_file))
            else:
                if not encrypt:
                    cmd = 'cd {0} && openssl des3 -d -k {1} -salt -in {2} | tar xzvf - >> {3} 2>&1'.format(os.path.dirname(tgz_file), tar_pass, tgz_file, backup_log_file)
                else:
                    cmd = 'cd {0} && tar xzvf {1} >> {2} 2>&1'.format(os.path.dirname(tgz_file), tgz_file, backup_log_file)
                public.ExecShell(cmd)
                path_size = public.get_path_size(tgz_file.replace('.tar.gz', ''))
                if path_size > 100:
                    return public.returnMsg(True, '解压缩文件{}完成'.format(tgz_file))
                return public.returnMsg(False, '解压缩文件{}解压出来的文件夹过小'.format(tgz_file))
        except Exception as e:
            return public.returnMsg(False, '解压缩文件{}出错，错误原因：{}'.format(tgz_file, str(e)))

    # 获取云端存储的状态
    def get_cloud_storage_status(self, storage_type, backup_type, local_filename, database):
        get = public.dict_obj()
        if backup_type == 'full':
            get.path = '/enterprise_backup/database/full/' + database
        elif backup_type == 'inc':
            get.path = '/enterprise_backup/database/inc/' + database
        elif backup_type == 'ddl':
            get.path = '/enterprise_backup/database/ddl/' + database

        data = {}
        try:
            if storage_type == 'ftp':
                from upload_ftp import ftp_main
                myftp = ftp_main()
                data = myftp.getList(get)
            elif storage_type == 'alioss':
                from upload_alioss import alioss_main
                myalioss = alioss_main()
                data = myalioss.get_list(get)
            elif storage_type == 'txcos':
                from upload_txcos import txcos_main
                mytxcos = txcos_main()
                data = mytxcos.get_list(get)
            elif storage_type == 'qiniu':
                from upload_qiniu import qiniu_main
                myqiniu = qiniu_main()
                data = myqiniu.get_list(get.path)
            elif storage_type == 'aws':
                from upload_aws import aws_main
                myaws = aws_main()
                data = myaws.get_list(get)
        except:
            print(storage_type)

        cloud_file_size = 0
        cloud_download_url = ''
        if data and 'list' in data:
            for item in data['list']:
                if local_filename == item['name']:
                    cloud_file_size = int(item['size'])
                    cloud_download_url = item['download']
        return cloud_file_size, cloud_download_url

    # 获取mysql全量备份数据列表
    def get_mysql_full_backup_list(self, get):
        if 'sid' not in get: return public.returnMsg(False, '缺少参数sid')
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 8
        callback = get.callback if 'callback' in get else ''

        count = public.M('mysql_full_backup').where('sid=?', get.sid).count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('mysql_full_backup').where('sid=?', get.sid).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        setting_info = public.M('mysql_backup_setting').where('id=?', get.sid).find()
        database = setting_info['database']
        for item in data_list:
            item['local_file_size'] = public.get_path_size(item['file_path'])
            if setting_info['upload_ftp']:
                item['ftp_file_size'], item['ftp_download'] = self.get_cloud_storage_status('ftp', 'full', os.path.basename(item['file_path']), database)
            if setting_info['upload_alioss']:
                item['alioss_file_size'], item['alioss_download'] = self.get_cloud_storage_status('alioss', 'full', os.path.basename(item['file_path']), database)
            if setting_info['upload_txcos']:
                item['txcos_file_size'], item['txcos_download'] = self.get_cloud_storage_status('txcos', 'full', os.path.basename(item['file_path']), database)
            if setting_info['upload_qiniu']:
                item['qiniu_file_size'], item['qiniu_download'] = self.get_cloud_storage_status('qiniu', 'full', os.path.basename(item['file_path']), database)
            if setting_info['upload_aws']:
                item['aws_file_size'], item['aws_download'] = self.get_cloud_storage_status('aws', 'full', os.path.basename(item['file_path']), database)
        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    # 大文件下载
    def download_big_file(self, local_file, url, file_size):
        import requests

        # 小于100M的文件直接下载
        if int(file_size) < 1024 * 1024 * 100:
            print('小文件下载')
            r = requests.get(url)
            with open(local_file, "wb") as f:
                f.write(r.content)
        # 大于100M的文件分片下载
        else:
            r = requests.get(url, stream=True)
            with open(local_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

    # 获取指定mysql全量备份信息
    def get_mysql_full_backup_info(self, id):
        try:
            backup_info = public.M('mysql_full_backup').where('id=?', id).find()
            setting_info = public.M('mysql_backup_setting').where('id=?', backup_info['sid']).find()
            database = setting_info['database']
            if not os.path.exists(os.path.dirname(backup_info['file_path'])):
                os.makedirs(os.path.dirname(backup_info['file_path']), 384)
            backup_info['local_file_size'] = public.get_path_size(backup_info['file_path'])
            if backup_info['local_file_size'] == 0:
                backup_info['ftp_file_size'], backup_info['ftp_download'] = self.get_cloud_storage_status('ftp', 'full', os.path.basename(backup_info['file_path']), database)
                backup_info['alioss_file_size'], backup_info['alioss_download'] = self.get_cloud_storage_status('alioss', 'full', os.path.basename(backup_info['file_path']), database)
                backup_info['txcos_file_size'], backup_info['txcos_download'] = self.get_cloud_storage_status('txcos', 'full', os.path.basename(backup_info['file_path']), database)
                backup_info['qiniu_file_size'], backup_info['qiniu_download'] = self.get_cloud_storage_status('qiniu', 'full', os.path.basename(backup_info['file_path']), database)
                backup_info['aws_file_size'], backup_info['aws_download'] = self.get_cloud_storage_status('aws', 'full', os.path.basename(backup_info['file_path']), database)
                tmp_dict = {'ftp_file_size': backup_info['ftp_file_size'], 'alioss_file_size': backup_info['alioss_file_size'],
                            'txcos_file_size': backup_info['txcos_file_size'], 'qiniu_file_size': backup_info['qiniu_file_size'], 'aws_file_size': backup_info['aws_file_size']}
                max_key = max(tmp_dict, key=tmp_dict.get)
                if max_key == 'ftp_file_size' and backup_info['ftp_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从ftp下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从ftp下载文件到[{}]'.format(backup_info['file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['file_path'], backup_info['ftp_download']))
                    self.download_big_file(backup_info['file_path'], backup_info['ftp_download'], backup_info['ftp_file_size'])
                if max_key == 'alioss_file_size' and backup_info['alioss_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从阿里云OSS下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从阿里云OSS下载文件到[{}]'.format(backup_info['file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['file_path'], backup_info['alioss_download']))
                    self.download_big_file(backup_info['file_path'], backup_info['alioss_download'], backup_info['alioss_file_size'])
                if max_key == 'txcos_file_size' and backup_info['txcos_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从腾讯云COS下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从腾讯云COS下载文件到[{}]'.format(backup_info['file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['file_path'], backup_info['txcos_download']))
                    self.download_big_file(backup_info['file_path'], backup_info['txcos_download'], backup_info['txcos_file_size'])
                if max_key == 'qiniu_file_size' and backup_info['qiniu_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从七牛云存储下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从七牛云存储下载文件到[{}]'.format(backup_info['file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['file_path'], backup_info['qiniu_download']))
                    self.download_big_file(backup_info['file_path'], backup_info['qiniu_download'], backup_info['qiniu_file_size'])
                if max_key == 'aws_file_size' and backup_info['aws_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从亚马逊S3云存储下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从亚马逊S3云存储下载文件到[{}]'.format(backup_info['file_path']))
                    self._mysql_download_file_aws('full', database, backup_info['file_path'])

            backup_info['local_file_size'] = public.get_path_size(backup_info['file_path'])
            return backup_info
        except:
            public.writeFile(self.__mysql_restore_log_file, '从云存储下载文件报错：{}'.format(public.get_error_info()), 'a+')
            print(public.get_error_info())

    # aws存储不提供外链下载，使用api接口进行下载
    def _mysql_download_file_aws(self, backup_type, database, local_file):
        filename = os.path.basename(local_file)
        if backup_type == 'full':
            key = 'enterprise_backup/database/full/{}/{}'.format(database, filename)
        elif backup_type == 'inc':
            key = 'enterprise_backup/database/inc/{}/{}'.format(database, filename)
        elif backup_type == 'ddl':
            key = 'enterprise_backup/database/ddl/{}/{}'.format(database, filename)

        from upload_aws import aws_main
        myaws = aws_main()
        myaws.download_file(key, local_file)

    # 删除mysql全量备份记录
    def delete_mysql_full_backup(self, id, delete_cloud=False):
        backup_info = public.M('mysql_full_backup').where('id=?', id).find()
        file_path = backup_info['file_path']
        filename = os.path.basename(file_path)
        setting_info = public.M('mysql_backup_setting').where('id=?', backup_info['sid']).find()
        database = setting_info['database']
        if os.path.exists(file_path): os.remove(file_path)
        if delete_cloud:
            # 删除ftp备份
            if setting_info['upload_ftp']:
                self.mysql_delete_cloud_backup('ftp', 'full', filename, database)
            # 删除阿里云oss备份
            if setting_info['upload_alioss']:
                self.mysql_delete_cloud_backup('alioss', 'full', filename, database)
            # 删除腾讯cos备份
            if setting_info['upload_txcos']:
                self.mysql_delete_cloud_backup('txcos', 'full', filename, database)
            # 删除七牛云存储备份
            if setting_info['upload_qiniu']:
                self.mysql_delete_cloud_backup('qiniu', 'full', filename, database)
            # 删除亚马逊S3云存储备份
            if setting_info['upload_aws']:
                self.mysql_delete_cloud_backup('aws', 'full', filename, database)
        public.M('mysql_full_backup').where('id=?', id).delete()
        return public.returnMsg(True, '删除成功')

    # 对外接口
    def delete_mysql_full_backup_api(self, get):
        return self.delete_mysql_full_backup(get.id)

    # 获取mysql增量备份数据列表
    def get_mysql_inc_backup_list(self, get=None):
        if 'sid' not in get: return public.returnMsg(False, '缺少参数sid')
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 8
        callback = get.callback if 'callback' in get else ''

        count = public.M('mysql_inc_backup').where('sid=?', get.sid).count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('mysql_inc_backup').where('sid=?', get.sid).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        setting_info = public.M('mysql_backup_setting').where('id=?', get.sid).find()
        database = setting_info['database']
        for item in data_list:
            item['local_file_size'] = public.get_path_size(item['inc_file_path'])
            if setting_info['upload_ftp']:
                item['ftp_file_size'], item['ftp_download'] = self.get_cloud_storage_status('ftp', 'inc', os.path.basename(item['inc_file_path']), database)
            if setting_info['upload_alioss']:
                item['alioss_file_size'], item['alioss_download'] = self.get_cloud_storage_status('alioss', 'inc', os.path.basename(item['inc_file_path']), database)
            if setting_info['upload_txcos']:
                item['txcos_file_size'], item['txcos_download'] = self.get_cloud_storage_status('txcos', 'inc', os.path.basename(item['inc_file_path']), database)
            if setting_info['upload_qiniu']:
                item['qiniu_file_size'], item['qiniu_download'] = self.get_cloud_storage_status('qiniu', 'inc', os.path.basename(item['inc_file_path']), database)
            if setting_info['upload_aws']:
                item['aws_file_size'], item['aws_download'] = self.get_cloud_storage_status('aws', 'inc', os.path.basename(item['inc_file_path']), database)
        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    # 获取指定mysql增量备份信息
    def get_mysql_inc_backup_info(self, id):
        try:
            backup_info = public.M('mysql_inc_backup').where('id=?', id).find()
            setting_info = public.M('mysql_backup_setting').where('id=?', backup_info['sid']).find()
            database = setting_info['database']
            if not os.path.exists(os.path.dirname(backup_info['inc_file_path'])):
                os.makedirs(os.path.dirname(backup_info['inc_file_path']), 384)
            backup_info['local_file_size'] = public.get_path_size(backup_info['inc_file_path'])
            if backup_info['local_file_size'] == 0:
                backup_info['ftp_file_size'], backup_info['ftp_download'] = self.get_cloud_storage_status('ftp', 'inc', os.path.basename(backup_info['inc_file_path']), database)
                backup_info['alioss_file_size'], backup_info['alioss_download'] = self.get_cloud_storage_status('alioss', 'inc', os.path.basename(backup_info['inc_file_path']), database)
                backup_info['txcos_file_size'], backup_info['txcos_download'] = self.get_cloud_storage_status('txcos', 'inc', os.path.basename(backup_info['inc_file_path']), database)
                backup_info['qiniu_file_size'], backup_info['qiniu_download'] = self.get_cloud_storage_status('qiniu', 'inc', os.path.basename(backup_info['inc_file_path']), database)
                backup_info['aws_file_size'], backup_info['aws_download'] = self.get_cloud_storage_status('aws', 'inc', os.path.basename(backup_info['inc_file_path']), database)
                tmp_dict = {'ftp_file_size': backup_info['ftp_file_size'], 'alioss_file_size': backup_info['alioss_file_size'],
                            'txcos_file_size': backup_info['txcos_file_size'], 'qiniu_file_size': backup_info['qiniu_file_size'], 'aws_file_size': backup_info['aws_file_size']}
                print(tmp_dict)
                max_key = max(tmp_dict, key=tmp_dict.get)
                print(max_key)
                if max_key == 'ftp_file_size' and backup_info['ftp_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从ftp下载文件到[{}]...'.format(backup_info['inc_file_path']), 'a+')
                    print('从ftp下载文件到[{}]'.format(backup_info['inc_file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['inc_file_path'], backup_info['ftp_download']))
                    self.download_big_file(backup_info['inc_file_path'], backup_info['ftp_download'], backup_info['ftp_file_size'])
                if max_key == 'alioss_file_size' and backup_info['alioss_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从阿里云OSS下载文件到[{}]...'.format(backup_info['inc_file_path']), 'a+')
                    print('从阿里云OSS下载文件到[{}]'.format(backup_info['inc_file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['inc_file_path'], backup_info['alioss_download']))
                    self.download_big_file(backup_info['inc_file_path'], backup_info['alioss_download'], backup_info['alioss_file_size'])
                if max_key == 'txcos_file_size' and backup_info['txcos_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从腾讯云COS下载文件到[{}]...'.format(backup_info['inc_file_path']), 'a+')
                    print('从腾讯云COS下载文件到[{}]'.format(backup_info['inc_file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['inc_file_path'], backup_info['txcos_download']))
                    self.download_big_file(backup_info['inc_file_path'], backup_info['txcos_download'], backup_info['txcos_file_size'])
                if max_key == 'qiniu_file_size' and backup_info['qiniu_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从七牛云存储下载文件到[{}]....'.format(backup_info['inc_file_path']), 'a+')
                    print('从七牛云存储下载文件到[{}]'.format(backup_info['inc_file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['inc_file_path'], backup_info['qiniu_download']))
                    self.download_big_file(backup_info['inc_file_path'], backup_info['qiniu_download'], backup_info['qiniu_file_size'])
                if max_key == 'aws_file_size' and backup_info['aws_file_size'] > 0:
                    public.writeFile(self.__mysql_restore_log_file, '正在从亚马逊S3云存储下载文件到[{}]...'.format(backup_info['inc_file_path']), 'a+')
                    print('从亚马逊S3云存储下载文件到[{}]'.format(backup_info['inc_file_path']))
                    self._mysql_download_file_aws('inc', database, backup_info['inc_file_path'])
            backup_info['local_file_size'] = public.get_path_size(backup_info['inc_file_path'])
            return backup_info
        except:
            public.writeFile(self.__mysql_restore_log_file, '从云存储下载文件报错：{}'.format(public.get_error_info()), 'a+')
            print(public.get_error_info())

    # 删除mysql增量备份记录
    def delete_mysql_inc_backup(self, id, delete_cloud=False):
        backup_info = public.M('mysql_inc_backup').where('id=?', id).find()
        file_path = backup_info['inc_file_path']
        filename = os.path.basename(file_path)
        setting_info = public.M('mysql_backup_setting').where('id=?', backup_info['sid']).find()
        database = setting_info['database']
        if os.path.exists(file_path): os.remove(file_path)
        if delete_cloud:
            # 删除ftp备份
            if setting_info['upload_ftp']:
                self.mysql_delete_cloud_backup('ftp', 'inc', filename, database)
            # 删除阿里云oss备份
            if setting_info['upload_alioss']:
                self.mysql_delete_cloud_backup('alioss', 'inc', filename, database)
            # 删除腾讯cos备份
            if setting_info['upload_txcos']:
                self.mysql_delete_cloud_backup('txcos', 'inc', filename, database)
            # 删除七牛云存储备份
            if setting_info['upload_qiniu']:
                self.mysql_delete_cloud_backup('qiniu', 'inc', filename, database)
            # 删除亚马逊S3云存储备份
            if setting_info['upload_aws']:
                self.mysql_delete_cloud_backup('aws', 'inc', filename, database)
        public.M('mysql_inc_backup').where('id=?', id).delete()
        return public.returnMsg(True, '删除成功')

    # 对外接口
    def delete_mysql_inc_backup_api(self, get):
        return self.delete_mysql_inc_backup(get.id)

    # 删除mysql云端存储的备份文件
    def mysql_delete_cloud_backup(self, storage_type, backup_type, filename, database):
        get = public.dict_obj()
        get.filename = filename
        if backup_type == 'full':
            get.path = '/enterprise_backup/database/full/' + database
        elif backup_type == 'inc':
            get.path = '/enterprise_backup/database/inc/' + database
        elif backup_type == 'ddl':
            get.path = '/enterprise_backup/database/ddl/' + database

        if storage_type == 'ftp':
            from upload_ftp import ftp_main
            myftp = ftp_main()
            myftp.rmFile(get)
        elif storage_type == 'alioss':
            from upload_alioss import alioss_main
            myalioss = alioss_main()
            myalioss.remove_file(get)
        elif storage_type == 'txcos':
            from upload_txcos import txcos_main
            mytxcos = txcos_main()
            mytxcos.remove_file(get)
        elif storage_type == 'qiniu':
            from upload_qiniu import qiniu_main
            myqiniu = qiniu_main()
            myqiniu.remove_file(get)
        elif storage_type == 'aws':
            from upload_aws import aws_main
            myaws = aws_main()
            myaws.remove_file(get)

    # 处理本地备份文件不存在的问题
    def mysql_ddl_download(self, file_path, database):
        try:
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path), 384)
            local_file_size = public.get_path_size(file_path)
            if local_file_size == 0:
                ftp_file_size, ftp_download = self.get_cloud_storage_status('ftp', 'ddl', os.path.basename(file_path), database)
                alioss_file_size, alioss_download = self.get_cloud_storage_status('alioss', 'ddl', os.path.basename(file_path), database)
                txcos_file_size, txcos_download = self.get_cloud_storage_status('txcos', 'ddl', os.path.basename(file_path), database)
                qiniu_file_size, qiniu_download = self.get_cloud_storage_status('qiniu', 'ddl', os.path.basename(file_path), database)
                aws_file_size, aws_download = self.get_cloud_storage_status('aws', 'ddl', os.path.basename(file_path), database)
                tmp_dict = {'ftp_file_size': ftp_file_size, 'alioss_file_size': alioss_file_size,
                            'txcos_file_size': txcos_file_size, 'qiniu_file_size': qiniu_file_size, 'aws_file_size': aws_file_size}
                max_key = max(tmp_dict, key=tmp_dict.get)
                if max_key == 'ftp_file_size':
                    print('从ftp下载文件到[{}]'.format(file_path))
                    # public.ExecShell('wget -O {} {} -T 10'.format(file_path, ftp_download))
                    self.download_big_file(file_path, ftp_download, ftp_file_size)
                if max_key == 'alioss_file_size':
                    print('从阿里云OSS下载文件到[{}]'.format(file_path))
                    # public.ExecShell('wget -O {} {} -T 10'.format(file_path, alioss_download))
                    self.download_big_file(file_path, alioss_download, alioss_file_size)
                if max_key == 'txcos_file_size':
                    print('从腾讯云COS下载文件到[{}]'.format(file_path))
                    # public.ExecShell('wget -O {} {} -T 10'.format(file_path, txcos_download))
                    self.download_big_file(file_path, txcos_download, txcos_file_size)
                if max_key == 'qiniu_file_size':
                    print('从七牛云存储下载文件到[{}]'.format(file_path))
                    # public.ExecShell('wget -O {} {} -T 10'.format(file_path, qiniu_download))
                    self.download_big_file(file_path, qiniu_download, qiniu_file_size)
                if max_key == 'aws_file_size':
                    print('从亚马逊S3云存储下载文件到[{}]'.format(file_path))
                    self._mysql_download_file_aws('ddl', database, file_path)
        except:
            print(public.get_error_info())

    # 恢复指定数据库或者表的表结构
    def mysql_ddl_restore(self, database, date_time):
        backup_path = os.path.join(self.__ddl_backup_path, database)
        filename = os.path.join(backup_path, '{}.sql.gz'.format(date_time))
        self.mysql_ddl_download(filename, database)
        if not os.path.exists(filename):
            return public.returnMsg(False, '数据库[{0}]ddl备份文件[{1}]不存在, 请先从云端下载!\n'.format(database, filename))
        backup_file = filename.replace('.gz', '')
        cmd = 'cd {} && gzip -dc {} > {}'.format(backup_path, os.path.basename(filename), os.path.basename(backup_file))
        public.writeFile(self.__mysql_restore_log_file, '解压ddl备份文件[{}], 命令: {}\n'.format(filename, cmd), 'a+')
        public.ExecShell(cmd)
        if not os.path.exists(backup_file):
            return public.returnMsg(False, '解压数据库[{}]ddl备份文件[{}]失败\n'.format(database, filename))

        root_pass = self.get_mysql_root()
        cmd = '/www/server/mysql/bin/mysql -uroot -p{} -f < {}'.format(root_pass, backup_file)
        public.writeFile(self.__mysql_restore_log_file, '恢复数据库{}表结构语句：{}\n'.format(database, cmd), 'a+')
        public.ExecShell(cmd)
        # public.writeFile(self.__mysql_restore_log_file, '恢复数据库{}表结构输出：{}'.format(database, result), 'a+')
        os.remove(backup_file)
        public.writeFile(self.__mysql_restore_log_file, "数据库[{}]使用文件[{}]完成表结构恢复\n".format(database, filename), 'a+')
        return public.returnMsg(True, "数据库[{}]使用文件[{}]完成表结构恢复\n".format(database, filename))

    def mysql_ddl_restore_api(self, get):
        self.mysql_ddl_restore(get.database, get.date_time)
        return public.returnMsg(True, '恢复数据库[{}]表结构完成'.format(get.database))

    # 获取文件夹所在分区的磁盘空间信息
    def get_disk_info(self, path):
        import psutil

        if not os.path.exists(path):
            return public.returnMsg(False, '目录不存在')
        data = psutil.disk_usage(path)._asdict()
        data['total'] = public.to_size(data['total'])
        data['used'] = public.to_size(data['used'])
        data['free'] = public.to_size(data['free'])
        return data

    # 获取文件夹所在分区的磁盘空间信息
    def get_disk_info_api(self, get):
        return self.get_disk_info(get.path)

    # 设置本地存储路径
    def set_local_config(self, get):
        if self.__backup_path:
            return public.returnMsg(True, '已经设置的不能更改')
        config_path = self.__configPath + '/local.conf'
        backup_path = self.get_path(get.path)
        public.writeFile(config_path, backup_path)
        return public.returnMsg(True, '设置成功!')

    def get_path(self, path):
        if path[-1] == '/': path = path[:-1]
        return path.replace('//', '/')

    # 获取本地存储路径
    def get_local_config(self, get):
        return [self.__backup_path, self.get_disk_info(self.__backup_path)]

    # ftp账号设置
    def set_ftp_config(self, get):
        from upload_ftp import ftp_main
        myftp = ftp_main()
        return myftp.SetConfig(get)

    # 获取ftp账号设置
    def get_ftp_config(self, get):
        from upload_ftp import ftp_main
        myftp = ftp_main()
        return myftp.GetConfig(get)

    # alioss账号设置
    def set_alioss_config(self, get):
        from upload_alioss import alioss_main
        myalioss = alioss_main()
        return myalioss.SetConfig(get)

    # 获取alioss账号设置
    def get_alioss_config(self, get):
        from upload_alioss import alioss_main
        myalioss = alioss_main()
        return myalioss.GetConfig(get)

    # txcos账号设置
    def set_txcos_config(self, get):
        from upload_txcos import txcos_main
        mytxcos = txcos_main()
        return mytxcos.SetConfig(get)

    # 获取txcos账号设置
    def get_txcos_config(self, get):
        from upload_txcos import txcos_main
        mytxcos = txcos_main()
        return mytxcos.GetConfig(get)

    # 七牛云存储账号设置
    def set_qiniu_config(self, get):
        from upload_qiniu import qiniu_main
        myqiniu = qiniu_main()
        return myqiniu.SetConfig(get)

    # 获取七牛云存储账号设置
    def get_qiniu_config(self, get):
        from upload_qiniu import qiniu_main
        myqiniu = qiniu_main()
        return myqiniu.GetConfig(get)

    # aws云存储账号设置
    def set_aws_config(self, get):
        from upload_aws import aws_main
        myaws = aws_main()
        return myaws.SetConfig(get)

    # 获取aws云存储账号设置
    def get_aws_config(self, get):
        from upload_aws import aws_main
        myaws = aws_main()
        return myaws.GetConfig(get)

    # 获取可用的云端存储列表
    def get_available_cloud(self, get):
        from upload_ftp import ftp_main
        from upload_alioss import alioss_main
        from upload_txcos import txcos_main
        from upload_qiniu import qiniu_main
        from upload_aws import aws_main

        cloud_status = os.path.join(self.__plugin_path, 'cloud_status.json')
        if int(get.act) == 1:
            data = {}
            data['local'] = {'name': '本地', 'status': os.path.exists(self.__configPath + '/local.conf')}
            data['ftp'] = {'name': 'FTP', 'status': ftp_main().check_config()}
            data['alioss'] = {'name': '阿里云OSS', 'status': alioss_main().check_config()}
            data['txcos'] = {'name': '腾讯云COS', 'status': txcos_main().check_config()}
            data['qiniu'] = {'name': '七牛云存储', 'status': qiniu_main().check_config()}
            data['aws'] = {'name': '亚马逊S3云存储', 'status': aws_main().check_config()}
            public.writeFile(cloud_status, json.dumps(data))
        else:
            if not os.path.exists(cloud_status):
                data = {}
                data['local'] = {'name': '本地', 'status': os.path.exists(self.__configPath + '/local.conf')}
                data['ftp'] = {'name': 'FTP', 'status': ftp_main().check_config()}
                data['alioss'] = {'name': '阿里云OSS', 'status': alioss_main().check_config()}
                data['txcos'] = {'name': '腾讯云COS', 'status': txcos_main().check_config()}
                data['qiniu'] = {'name': '七牛云存储', 'status': qiniu_main().check_config()}
                data['aws'] = {'name': '亚马逊S3云存储', 'status': aws_main().check_config()}
                public.writeFile(cloud_status, json.dumps(data))
            data = json.loads(public.readFile(cloud_status))
        return data

    # 判断进程是否存在qiniu
    def process_exists(self, cmdline=None):
        try:
            import psutil
            pids = psutil.pids()
            for pid in pids:
                try:
                    p = psutil.Process(pid)
                    if cmdline in p.cmdline(): return True
                except: pass
            return False
        except:
            return False

    # 执行数据库全量备份
    def start_mysql_full_backup_task(self, database):
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(database)).getField('echo')
        if not echo: return public.returnMsg(False, '请检查计划任务是否存在')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(False, '数据库[{}]全量备份任务正在进行中'.format(database))
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell(execstr + ' >> ' + execstr + '.log 2>&1')
        return public.returnMsg(True, '数据库[{}]全量备份任务执行完成'.format(database))

    # 后台执行数据库全量备份
    def start_mysql_full_backup_task_d(self, database):
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(database)).getField('echo')
        if not echo: return public.returnMsg(False, '请检查计划任务是否存在')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(False, '数据库[{}]全量备份任务正在进行中'.format(database))
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell('nohup ' + execstr + ' >> ' + execstr + '.log 2>&1 &')
        return public.returnMsg(True, '数据库[{}]全量备份任务执行完成'.format(database))

    # 执行数据库增量备份任务
    def start_mysql_inc_backup_task(self, database):
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(database)).getField('echo')
        if not echo: return public.returnMsg(False, '请检查计划任务是否存在')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(False, '数据库[{}]增量备份任务正在进行中'.format(database))
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell(execstr + ' >> ' + execstr + '.log 2>&1')
        return public.returnMsg(True, '数据库[{}]增量备份任务执行完成'.format(database))

    # 执行数据库备份任务
    def start_mysql_backup_task(self, get):
        setting_info = public.M('mysql_backup_setting').where('id=?', get.id).find()
        database = setting_info['database']
        if int(setting_info['inc_backup_need']) == 1:
            return self.start_mysql_inc_backup_task(database)
        else:
            return self.start_mysql_full_backup_task(database)

    # mysql获取备份任务执行日志
    def get_mysql_backup_logs(self, get):
        if 'id' not in get: return public.returnMsg(False, '错误的参数!')
        id = get.id
        pdata = public.M('mysql_backup_setting').where('id=?', id).find()

        p = crontab.crontab()
        # 获取全量备份计划任务执行日志
        id = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库全量备份任务[{}]".format(pdata['database'])).getField('id')
        if not id: return public.returnMsg(False, '请检查计划任务是否存在')
        args = {"id": id}
        full_backup_logs = p.GetLogs(args)['msg']
        if int(pdata['inc_backup_need']) == 1:
            # 获取增量备份计划任务执行日志
            id = public.M('crontab').where("name=?", "[勿删]企业级备份-数据库增量备份任务[{}]".format(pdata['database'])).getField('id')
            if not id: return public.returnMsg(False, '请检查计划任务是否存在')
            args = {"id": id}
            inc_backup_logs = p.GetLogs(args)['msg']
        else:
            inc_backup_logs = ''
        return {'full_backup_logs': full_backup_logs, 'inc_backup_logs': inc_backup_logs}

    # *****************目录备份相关******************
    # 获取目录备份设置列表
    def get_path_backup_setting_list(self, get):
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 8
        callback = get.callback if 'callback' in get else ''

        count = public.M('path_backup_setting').count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('path_backup_setting').order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    # 增加目录备份设置
    def add_path_backup_setting(self, get):
        pdata = {}
        pdata['path'] = get.path[:-1] if get.path[-1] == '/' else get.path
        if public.M('path_backup_setting').where('path=?', pdata['path']).count():
            return public.returnMsg(False, '该目录已存在备份设置')
        tmp = []
        for item in json.loads(get.exclude):
            if not item: continue
            if item[-1] == '/': tmp.append(item[:-1])
            else: tmp.append(item)
        pdata['exclude'] = json.dumps(tmp)
        pdata['full_backup_type'] = get.full_backup_type
        pdata['full_backup_week'] = get.full_backup_week if 'full_backup_week' in get else ''
        pdata['full_backup_hour'] = get.full_backup_hour
        pdata['full_backup_minute'] = get.full_backup_minute
        pdata['full_backup_save'] = get.full_backup_save
        pdata['inc_backup_need'] = get.inc_backup_need
        if get.inc_backup_need == '1':
            pdata['inc_backup_type'] = get.inc_backup_type
            pdata['inc_backup_hour'] = get.inc_backup_hour if 'inc_backup_hour' in get else ''
            pdata['inc_backup_minute'] = get.inc_backup_minute
            pdata['inc_backup_save'] = get.inc_backup_save
        if 'upload_ftp' in get: pdata['upload_ftp'] = get.upload_ftp
        if 'upload_alioss' in get: pdata['upload_alioss'] = get.upload_alioss
        if 'upload_txcos' in get: pdata['upload_txcos'] = get.upload_txcos
        if 'upload_qiniu' in get: pdata['upload_qiniu'] = get.upload_qiniu
        if 'upload_aws' in get: pdata['upload_aws'] = get.upload_aws
        if 'upload_local' in get: pdata['upload_local'] = get.upload_local
        pdata['status'] = 1
        pdata['addtime'] = int(time.time())
        pdata['id'] = public.M('path_backup_setting').insert(pdata)
        res = self.add_path_full_backup_task(pdata)
        if not res:
            return public.returnMsg(False, "全量备份任务添加失败！")
        if get.inc_backup_need == '1':
            self.add_path_inc_backup_task(pdata)
        public.WriteLog(self.__log_type, "创建目录备份[{}]".format(pdata['path']))
        return public.returnMsg(True, '添加成功!')

    # 增加目录全量备份定时任务
    def add_path_full_backup_task(self, pdata):
        p = crontab.crontab()
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        args = {
            "name": "[勿删]企业级备份-目录全量备份任务[{}]".format(pdata['path']),
            "type": pdata['full_backup_type'],
            "where1": '',
            "hour": pdata['full_backup_hour'],
            "minute": pdata['full_backup_minute'],
            "week": pdata['full_backup_week'],
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": pdata['full_backup_save'],
            "sBody": '{} {}/crontab_tasks/path_full_backup.py {}'.format(python_path, self.__plugin_path, pdata['id']),
            "urladdress": "undefined"
        }
        res = p.AddCrontab(args)
        if res and "id" in res.keys():
            return True
        return False

    # 增加目录增量备份定时任务
    def add_path_inc_backup_task(self, pdata):
        p = crontab.crontab()
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        args = {
            "name": "[勿删]企业级备份-目录增量备份任务[{}]".format(pdata['path']),
            "type": pdata['inc_backup_type'],
            "where1": '',
            "hour": pdata['inc_backup_hour'],
            "minute": pdata['inc_backup_minute'],
            "week": '',
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": pdata['inc_backup_save'],
            "sBody": '{} {}/crontab_tasks/path_inc_backup.py {}'.format(python_path, self.__plugin_path, pdata['id']),
            "urladdress": "undefined"
        }
        p.AddCrontab(args)

    # 更新目录备份设置
    def modify_path_backup_setting(self, get):
        if 'id' not in get: return public.returnMsg(False, '错误的参数!')
        pdata = {}
        tmp = []
        for item in json.loads(get.exclude):
            if not item: continue
            if item[-1] == '/': tmp.append(item[:-1])
            else: tmp.append(item)
        pdata['exclude'] = json.dumps(tmp)
        pdata['full_backup_type'] = get.full_backup_type
        pdata['full_backup_week'] = get.full_backup_week if 'full_backup_week' in get else ''
        pdata['full_backup_hour'] = get.full_backup_hour
        pdata['full_backup_minute'] = get.full_backup_minute
        pdata['full_backup_save'] = get.full_backup_save
        pdata['inc_backup_need'] = get.inc_backup_need
        old_data = public.M('path_backup_setting').where('id=?', get.id).find()
        if get.inc_backup_need == '1':
            pdata['inc_backup_type'] = get.inc_backup_type
            pdata['inc_backup_hour'] = get.inc_backup_hour if 'inc_backup_hour' in get else ''
            pdata['inc_backup_minute'] = get.inc_backup_minute
            pdata['inc_backup_save'] = get.inc_backup_save
            pdata['path'] = old_data['path']
            pdata['id'] = int(get.id)
            if int(old_data['inc_backup_need']) == 0:
                self.add_path_inc_backup_task(pdata)
        else:
            # 如果之前设置了增量备份，删除之前的增量备份计划任务
            if int(old_data['inc_backup_need']) == 1:
                p = crontab.crontab()
                c_id = public.M('crontab').where("name=?", "[勿删]企业级备份-目录增量备份任务[{}]".format(old_data['path'])).getField('id')
                args = {"id": c_id}
                p.DelCrontab(args)
        if 'upload_ftp' in get: pdata['upload_ftp'] = get.upload_ftp
        if 'upload_alioss' in get: pdata['upload_alioss'] = get.upload_alioss
        if 'upload_txcos' in get: pdata['upload_txcos'] = get.upload_txcos
        if 'upload_qiniu' in get: pdata['upload_qiniu'] = get.upload_qiniu
        if 'upload_aws' in get: pdata['upload_aws'] = get.upload_aws
        if 'upload_local' in get: pdata['upload_local'] = get.upload_local
        if 'status' in get: pdata['status'] = get.status

        public.M('path_backup_setting').where('id=?', int(get.id)).update(pdata)
        pdata = public.M('path_backup_setting').where('id=?', get.id).find()
        self.modify_path_full_backup_task(pdata)
        if get.inc_backup_need == '1':
            self.modify_path_inc_backup_task(pdata)
        public.WriteLog(self.__log_type, "修改目录备份[{}]".format(pdata['path']))
        return public.returnMsg(True, '编辑成功')

    # 修改目录全量备份定时任务
    def modify_path_full_backup_task(self, pdata):
        p = crontab.crontab()
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        args = {
            "id": public.M('crontab').where("name=?", "[勿删]企业级备份-目录全量备份任务[{}]".format(pdata['path'])).getField('id'),
            "name": "[勿删]企业级备份-目录全量备份任务[{}]".format(pdata['path']),
            "type": pdata['full_backup_type'],
            "where1": '',
            "hour": pdata['full_backup_hour'],
            "minute": pdata['full_backup_minute'],
            "week": pdata['full_backup_week'],
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": pdata['full_backup_save'],
            "sBody": '{} {}/crontab_tasks/path_full_backup.py {}'.format(python_path, self.__plugin_path, pdata['id']),
            "urladdress": "undefined",
            "status": pdata['status']
        }
        p.modify_crond(args)

    # 修改目录增量备份定时任务
    def modify_path_inc_backup_task(self, pdata):
        p = crontab.crontab()
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        id = public.M('crontab').where("name=?", "[勿删]企业级备份-目录增量备份任务[{}]".format(pdata['path'])).getField('id')
        if id:
            args = {
                "id": id,
                "name": "[勿删]企业级备份-目录增量备份任务[{}]".format(pdata['path']),
                "type": pdata['inc_backup_type'],
                "where1": '',
                "hour": pdata['inc_backup_hour'],
                "minute": pdata['inc_backup_minute'],
                "week": '',
                "sType": "toShell",
                "sName": "",
                "backupTo": "",
                "save": pdata['inc_backup_save'],
                "sBody": '{} {}/crontab_tasks/path_inc_backup.py {}'.format(python_path, self.__plugin_path, pdata['id']),
                "urladdress": "undefined",
                "status": pdata['status']
            }
            p.modify_crond(args)
        else:
            self.add_path_inc_backup_task(pdata)

    # 更新目录备份任务状态
    def modify_path_backup_setting_status(self, get):
        if 'id' not in get: return public.returnMsg(False, '错误的参数!')
        pdata = {}
        pdata['status'] = get.status

        public.M('path_backup_setting').where('id=?', int(get.id)).setField('status', pdata['status'])
        pdata = public.M('path_backup_setting').where('id=?', get.id).find()
        self.modify_path_full_backup_task_status(pdata)
        if int(pdata['inc_backup_need']) == 1:
            self.modify_path_inc_backup_task_status(pdata)
        public.WriteLog(self.__log_type, "修改目录备份[{}]状态为{}".format(pdata['path'], pdata['status']))
        return public.returnMsg(True, '编辑成功')

    # 修改目录全量备份定时任务状态
    def modify_path_full_backup_task_status(self, pdata):
        p = crontab.crontab()
        args = {
            "id": public.M('crontab').where("name=?", "[勿删]企业级备份-目录全量备份任务[{}]".format(pdata['path'])).getField('id'),
        }
        p.set_cron_status(args)

    # 修改目录增量备份定时任务状态
    def modify_path_inc_backup_task_status(self, pdata):
        p = crontab.crontab()
        args = {
            "id": public.M('crontab').where("name=?", "[勿删]企业级备份-目录增量备份任务[{}]".format(pdata['path'])).getField('id'),
        }
        p.set_cron_status(args)

    # 删除目录备份设置
    def delete_path_backup_setting(self, get):
        if 'id' not in get: return public.returnMsg(False, '错误的参数!')
        id = get.id
        pdata = public.M('path_backup_setting').where('id=?', id).find()
        # 删除计划任务
        self.remove_path_backup_task(pdata)

        self.remove_dir(os.path.join(self.__dir_last_full_backup, pdata['path'].replace('/', '_')))
        # 删除与之关联的全量备份记录
        full_backup_delete = public.M('path_full_backup').where('sid=?', get.id).field('id').select()
        for item in full_backup_delete:
            self.delete_path_full_backup(item['id'])

        # 删除与之关联的增量备份记录
        inc_backup_delete = public.M('path_inc_backup').where('sid=?', get.id).field('id').select()
        for item in inc_backup_delete:
            self.delete_path_inc_backup(item['id'])

        public.M('path_backup_setting').where('id=?', id).delete()
        public.WriteLog(self.__log_type, "删除目录备份[{}]".format(pdata['path']))
        return public.returnMsg(True, '删除成功!')

    # 删除计划任务
    def remove_path_backup_task(self, pdata):
        p = crontab.crontab()
        id = public.M('crontab').where("name=?", "[勿删]企业级备份-目录增量备份任务[{}]".format(pdata['path'])).getField('id')
        args = {"id": id}
        p.DelCrontab(args)
        id = public.M('crontab').where("name=?", "[勿删]企业级备份-目录全量备份任务[{}]".format(pdata['path'])).getField('id')
        args = {"id": id}
        p.DelCrontab(args)

    # 获取排除规则
    def get_exclude(self, exclude_str):
        tmp_exclude = json.loads(exclude_str)
        if not tmp_exclude: return ""
        exclude = ''
        for ex in tmp_exclude:
            exclude += " --exclude=\"" + ex + "\""
        exclude += " "
        return exclude

    # 获取目录全量备份数据列表
    def get_path_full_backup_list(self, get=None):
        if 'sid' not in get: return public.returnMsg(False, '缺少参数sid')
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 8
        callback = get.callback if 'callback' in get else ''

        count = public.M('path_full_backup').where('sid=?', get.sid).count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('path_full_backup').where('sid=?', get.sid).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        setting_info = public.M('path_backup_setting').where('id=?', get.sid).find()
        for item in data_list:
            item['local_file_size'] = public.get_path_size(item['file_path'])
            if setting_info['upload_ftp']:
                item['ftp_file_size'], item['ftp_download'] = self.get_path_cloud_storage_status('ftp', 'full', os.path.basename(item['file_path']))
            if setting_info['upload_alioss']:
                item['alioss_file_size'], item['alioss_download'] = self.get_path_cloud_storage_status('alioss', 'full', os.path.basename(item['file_path']))
            if setting_info['upload_txcos']:
                item['txcos_file_size'], item['txcos_download'] = self.get_path_cloud_storage_status('txcos', 'full', os.path.basename(item['file_path']))
            if setting_info['upload_qiniu']:
                item['qiniu_file_size'], item['qiniu_download'] = self.get_path_cloud_storage_status('qiniu', 'full', os.path.basename(item['file_path']))
            if setting_info['upload_aws']:
                item['aws_file_size'], item['aws_download'] = self.get_path_cloud_storage_status('aws', 'full', os.path.basename(item['file_path']))
        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    # 获取目录增量备份数据列表
    def get_path_inc_backup_list(self, get=None):
        if 'sid' not in get: return public.returnMsg(False, '缺少参数sid')
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 8
        callback = get.callback if 'callback' in get else ''

        count = public.M('path_inc_backup').where('sid=?', get.sid).count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('path_inc_backup').where('sid=?', get.sid).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        setting_info = public.M('path_backup_setting').where('id=?', get.sid).find()
        for item in data_list:
            item['local_file_size'] = public.get_path_size(item['inc_file_path'])
            if setting_info['upload_ftp']:
                item['ftp_file_size'], item['ftp_download'] = self.get_path_cloud_storage_status('ftp', 'inc', os.path.basename(item['inc_file_path']))
            if setting_info['upload_alioss']:
                item['alioss_file_size'], item['alioss_download'] = self.get_path_cloud_storage_status('alioss', 'inc', os.path.basename(item['inc_file_path']))
            if setting_info['upload_txcos']:
                item['txcos_file_size'], item['txcos_download'] = self.get_path_cloud_storage_status('txcos', 'inc', os.path.basename(item['inc_file_path']))
            if setting_info['upload_qiniu']:
                item['qiniu_file_size'], item['qiniu_download'] = self.get_path_cloud_storage_status('qiniu', 'inc', os.path.basename(item['inc_file_path']))
            if setting_info['upload_aws']:
                item['aws_file_size'], item['aws_download'] = self.get_path_cloud_storage_status('aws', 'inc', os.path.basename(item['inc_file_path']))
        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    # aws存储不提供外链下载，使用api接口进行下载
    def _path_download_file_aws(self, backup_type, local_file):
        filename = os.path.basename(local_file)
        if backup_type == 'full':
            key = 'enterprise_backup/path/full/{}'.format(filename)
        elif backup_type == 'inc':
            key = 'enterprise_backup/path/inc/{}'.format(filename)

        from upload_aws import aws_main
        myaws = aws_main()
        myaws.download_file(key, local_file)

    # 获取指定目录全量备份信息
    def get_path_full_backup_info(self, id):
        try:
            backup_info = public.M('path_full_backup').where('id=?', id).find()
            backup_info['local_file_size'] = public.get_path_size(backup_info['file_path'])
            backup_info['ftp_file_size'], backup_info['ftp_download'] = self.get_path_cloud_storage_status('ftp', 'full', os.path.basename(backup_info['file_path']))
            backup_info['alioss_file_size'], backup_info['alioss_download'] = self.get_path_cloud_storage_status('alioss', 'full', os.path.basename(backup_info['file_path']))
            backup_info['txcos_file_size'], backup_info['txcos_download'] = self.get_path_cloud_storage_status('txcos', 'full', os.path.basename(backup_info['file_path']))
            backup_info['qiniu_file_size'], backup_info['qiniu_download'] = self.get_path_cloud_storage_status('qiniu', 'full', os.path.basename(backup_info['file_path']))
            backup_info['aws_file_size'], backup_info['aws_download'] = self.get_path_cloud_storage_status('aws', 'full', os.path.basename(backup_info['file_path']))
            if backup_info['local_file_size'] == 0:
                tmp_dict = {'ftp_file_size': backup_info['ftp_file_size'], 'alioss_file_size': backup_info['alioss_file_size'],
                            'txcos_file_size': backup_info['txcos_file_size'], 'qiniu_file_size': backup_info['qiniu_file_size'], 'aws_file_size': backup_info['aws_file_size']}
                max_key = max(tmp_dict, key=tmp_dict.get)
                if max_key == 'ftp_file_size' and backup_info['ftp_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从ftp下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从ftp下载文件到[{}]'.format(backup_info['file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['file_path'], backup_info['ftp_download']))
                    self.download_big_file(backup_info['file_path'], backup_info['ftp_download'], backup_info['ftp_file_size'])
                if max_key == 'alioss_file_size' and backup_info['alioss_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从阿里云OSS下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从阿里云OSS下载文件到[{}]'.format(backup_info['file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['file_path'], backup_info['alioss_download']))
                    self.download_big_file(backup_info['file_path'], backup_info['alioss_download'], backup_info['alioss_file_size'])
                if max_key == 'txcos_file_size' and backup_info['txcos_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从腾讯云COS下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从腾讯云COS下载文件到[{}]'.format(backup_info['file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['file_path'], backup_info['txcos_download']))
                    self.download_big_file(backup_info['file_path'], backup_info['txcos_download'], backup_info['txcos_file_size'])
                if max_key == 'qiniu_file_size' and backup_info['qiniu_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从七牛云存储下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从七牛云存储下载文件到[{}]'.format(backup_info['file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['file_path'], backup_info['qiniu_download']))
                    self.download_big_file(backup_info['file_path'], backup_info['qiniu_download'], backup_info['qiniu_file_size'])
                if max_key == 'aws_file_size' and backup_info['aws_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从亚马逊S3云存储下载文件到[{}]...'.format(backup_info['file_path']), 'a+')
                    print('从亚马逊S3云存储下载文件到[{}]'.format(backup_info['file_path']))
                    self._path_download_file_aws('full', backup_info['file_path'])
            backup_info['local_file_size'] = public.get_path_size(backup_info['file_path'])
            return backup_info
        except:
            public.writeFile(self.__path_restore_log_file, '从云存储下载文件报错：{}'.format(public.get_error_info()), 'a+')
            print(public.get_error_info())

    # 获取指定目录增量备份信息
    def get_path_inc_backup_info(self, id):
        try:
            backup_info = public.M('path_inc_backup').where('id=?', id).find()
            backup_info['local_file_size'] = public.get_path_size(backup_info['inc_file_path'])
            backup_info['ftp_file_size'], backup_info['ftp_download'] = self.get_path_cloud_storage_status('ftp', 'inc', os.path.basename(backup_info['inc_file_path']))
            backup_info['alioss_file_size'], backup_info['alioss_download'] = self.get_path_cloud_storage_status('alioss', 'inc', os.path.basename(backup_info['inc_file_path']))
            backup_info['txcos_file_size'], backup_info['txcos_download'] = self.get_path_cloud_storage_status('txcos', 'inc', os.path.basename(backup_info['inc_file_path']))
            backup_info['qiniu_file_size'], backup_info['qiniu_download'] = self.get_path_cloud_storage_status('qiniu', 'inc', os.path.basename(backup_info['inc_file_path']))
            backup_info['aws_file_size'], backup_info['aws_download'] = self.get_path_cloud_storage_status('aws', 'inc', os.path.basename(backup_info['inc_file_path']))
            if backup_info['local_file_size'] == 0:
                tmp_dict = {'ftp_file_size': backup_info['ftp_file_size'], 'alioss_file_size': backup_info['alioss_file_size'],
                            'txcos_file_size': backup_info['txcos_file_size'], 'qiniu_file_size': backup_info['qiniu_file_size'], 'aws_file_size': backup_info['aws_file_size']}
                max_key = max(tmp_dict, key=tmp_dict.get)
                if max_key == 'ftp_file_size' and backup_info['ftp_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从ftp下载文件到[{}]...'.format(backup_info['inc_file_path']), 'a+')
                    print('从ftp下载文件到[{}]'.format(backup_info['inc_file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['inc_file_path'], backup_info['ftp_download']))
                    self.download_big_file(backup_info['inc_file_path'], backup_info['ftp_download'], backup_info['ftp_file_size'])
                if max_key == 'alioss_file_size' and backup_info['alioss_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从阿里云OSS下载文件到[{}]...'.format(backup_info['inc_file_path']), 'a+')
                    print('从阿里云OSS下载文件到[{}]'.format(backup_info['inc_file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['inc_file_path'], backup_info['alioss_download']))
                    self.download_big_file(backup_info['inc_file_path'], backup_info['alioss_download'], backup_info['alioss_file_size'])
                if max_key == 'txcos_file_size' and backup_info['txcos_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从腾讯云COS下载文件到[{}]...'.format(backup_info['inc_file_path']), 'a+')
                    print('从腾讯云COS下载文件到[{}]'.format(backup_info['inc_file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['inc_file_path'], backup_info['txcos_download']))
                    self.download_big_file(backup_info['inc_file_path'], backup_info['txcos_download'], backup_info['txcos_file_size'])
                if max_key == 'qiniu_file_size' and backup_info['qiniu_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从七牛云存储下载文件到[{}]...'.format(backup_info['inc_file_path']), 'a+')
                    print('从七牛云存储下载文件到[{}]'.format(backup_info['inc_file_path']))
                    # public.ExecShell('wget -O {} {} -T 10'.format(backup_info['inc_file_path'], backup_info['qiniu_download']))
                    self.download_big_file(backup_info['inc_file_path'], backup_info['qiniu_download'], backup_info['qiniu_file_size'])
                if max_key == 'aws_file_size' and backup_info['aws_file_size'] > 0:
                    public.writeFile(self.__path_restore_log_file, '正在从亚马逊S3云存储下载文件到[{}]...'.format(backup_info['inc_file_path']), 'a+')
                    print('从亚马逊S3云存储下载文件到[{}]'.format(backup_info['inc_file_path']))
                    self._path_download_file_aws('full', backup_info['inc_file_path'])
            backup_info['local_file_size'] = public.get_path_size(backup_info['inc_file_path'])
            return backup_info
        except:
            public.writeFile(self.__path_restore_log_file, '从云存储下载文件报错：{}'.format(public.get_error_info()), 'a+')
            print(public.get_error_info())

    # 获取目录备份云端存储的状态
    def get_path_cloud_storage_status(self, storage_type, backup_type, local_filename):
        get = public.dict_obj()
        if backup_type == 'full':
            get.path = '/enterprise_backup/path/full'
        else:
            get.path = '/enterprise_backup/path/inc'

        data = {}
        try:
            if storage_type == 'ftp':
                from upload_ftp import ftp_main
                myftp = ftp_main()
                data = myftp.getList(get)
            elif storage_type == 'alioss':
                from upload_alioss import alioss_main
                myalioss = alioss_main()
                data = myalioss.get_list(get)
            elif storage_type == 'txcos':
                from upload_txcos import txcos_main
                mytxcos = txcos_main()
                data = mytxcos.get_list(get)
            elif storage_type == 'qiniu':
                from upload_qiniu import qiniu_main
                myqiniu = qiniu_main()
                data = myqiniu.get_list(get.path)
            elif storage_type == 'aws':
                from upload_aws import aws_main
                myaws = aws_main()
                data = myaws.get_list(get)
        except:
            print(storage_type)

        cloud_file_size = 0
        cloud_download_url = ''
        if data and 'list' in data:
            for item in data['list']:
                if local_filename == item['name']:
                    cloud_file_size = int(item['size'])
                    cloud_download_url = item['download']
        return cloud_file_size, cloud_download_url

    # 目录全量备份还原
    def path_full_backup_restore(self, get):
        if os.path.exists(self.__path_restore_log_file):
            return public.returnMsg(False, '有其他目录恢复任务在执行，请等待其执行完成')

        backup_info = public.M('path_full_backup').where('id=?', get.id).find()
        setting_info = public.M('path_backup_setting').where('id=?', backup_info['sid']).find()
        backup_file = backup_info['file_path']
        tar_pass = backup_info['tar_pass']
        path = setting_info['path']
        public.writeFile(self.__path_restore_log_file, "目录[{}]使用文件[{}]开始全量备份恢复\n".format(path, backup_file))

        # 如果此目录有全量备份任务在执行，等待全量备份任务完成
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-目录全量备份任务[{}]".format(path)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            os.remove(self.__path_restore_log_file)
            return public.returnMsg(False, '目录[{}]全量备份任务正在进行中，此时无法进行恢复操作'.format(path))

        # 如果本地不存在全量备份文件，先从云端下载
        self.get_path_full_backup_info(get.id)
        if not os.path.exists(backup_file):
            os.remove(self.__path_restore_log_file)
            return public.returnMsg(False, '请检查本地和云端是否都不存在全量备份文件{}'.format(backup_file))

        # 解压全量备份文件
        backup_path = backup_file.replace('.tar.gz', '')
        result = self.uncompress_dir(backup_file, tar_pass, self.__path_restore_log_file)
        if not result['status']:
            self.remove_dir(backup_path)
            os.remove(self.__path_restore_log_file)
            return result

        # 恢复数据
        try:
            tar_file = backup_path + '/full_backup.tar.gz'
            snapshot_file = backup_path + '/snapshot'
            cmd = 'cd {} && tar -g {} -zxvf {} >> {} 2>&1'.format(os.path.dirname(path), snapshot_file, tar_file, self.__path_restore_log_file)
            public.writeFile(self.__path_restore_log_file, '目录[{}]全量备份恢复命令：{}'.format(path, cmd), 'a+')
            public.ExecShell(cmd)
            self.remove_dir(backup_path)
            public.writeFile(self.__path_restore_log_file, "备份恢复之后要进行一次全量备份", 'a+')
            self.start_path_full_backup_task_d(path)
            public.writeFile(self.__path_restore_log_file, "目录[{}]使用文件[{}]完成全量备份恢复".format(path, backup_file), 'a+')
            public.WriteLog(self.__log_type, "目录[{}]使用文件[{}]完成全量备份恢复".format(path, backup_file))
            os.remove(self.__path_restore_log_file)
            return public.returnMsg(True, '恢复目录[{}]数据完成'.format(path))
        except:
            self.remove_dir(backup_path)
            os.remove(self.__path_restore_log_file)
            return public.returnMsg(False, '恢复目录[{}]数据失败，原因：{}'.format(path, public.get_error_info()))

    # 目录增量备份还原
    def path_inc_backup_restore(self, get):
        if os.path.exists(self.__path_restore_log_file):
            return public.returnMsg(False, '有其他目录恢复任务在执行，请等待其执行完成')

        backup_info = public.M('path_inc_backup').where('id=?', get.id).find()
        setting_info = public.M('path_backup_setting').where('id=?', backup_info['sid']).find()
        path = setting_info['path']
        inc_file_path = backup_info['inc_file_path']
        full_file_path = backup_info['full_file_path']
        public.writeFile(self.__path_restore_log_file, "目录[{}]使用文件[{}]开始增量备份恢复\n".format(path, inc_file_path))

        # 如果此目录有全量备份任务在执行，等待全量备份任务完成
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-目录全量备份任务[{}]".format(path)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(False, '目录[{}]全量备份任务正在进行中，此时无法进行恢复操作'.format(path))
        # 如果此目录有增量备份任务在执行，等待增量备份任务完成
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-目录增量备份任务[{}]".format(path)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(False, '目录[{}]增量备份任务正在进行中，此时无法进行恢复操作'.format(path))

        # 如果本地不存在全量备份文件，先从云端下载
        self.get_path_full_backup_info(backup_info['fid'])
        if not os.path.exists(full_file_path):
            os.remove(self.__path_restore_log_file)
            return public.returnMsg(False, '请检查本地和云端是否都不存在全量备份文件{}'.format(full_file_path))
        # 解压全量备份文件
        full_tar_pass = public.M('path_full_backup').where('file_path=?', full_file_path).order('id desc').field('tar_pass').find()['tar_pass']
        full_backup_path = full_file_path.replace('.tar.gz', '')
        result = self.uncompress_dir(full_file_path, full_tar_pass, self.__path_restore_log_file)
        if not result['status']:
            self.remove_dir(full_backup_path)
            os.remove(self.__path_restore_log_file)
            return result

        # 如果本地不存在增量备份文件，先从云端下载
        self.get_path_inc_backup_info(get.id)
        if not os.path.exists(inc_file_path):
            self.remove_dir(full_backup_path)
            os.remove(self.__path_restore_log_file)
            return public.returnMsg(False, '请检查本地和云端是否都不存在增量备份文件{}'.format(inc_file_path))
        # 解压增量备份文件
        inc_tar_pass = backup_info['tar_pass']
        inc_backup_path = inc_file_path.replace('.tar.gz', '')
        result = self.uncompress_dir(inc_file_path, inc_tar_pass, self.__path_restore_log_file)
        if not result['status']:
            self.remove_dir(full_backup_path)
            self.remove_dir(inc_backup_path)
            os.remove(self.__path_restore_log_file)
            return result

        # 恢复数据
        try:
            # 先还原全量备份
            tar_file = full_backup_path + '/full_backup.tar.gz'
            snapshot_file = full_backup_path + '/snapshot'
            cmd = 'cd {} && tar -g {} -zxvf {} >> {} 2>&1'.format(os.path.dirname(path), snapshot_file, tar_file, self.__path_restore_log_file)
            public.writeFile(self.__path_restore_log_file, '目录[{}]全量备份恢复命令：{}'.format(path, cmd), 'a+')
            public.ExecShell(cmd)
            # 再还原增量备份
            tar_file = inc_backup_path + '/inc_backup.tar.gz'
            snapshot_file = inc_backup_path + '/snapshot'
            cmd = 'cd {} && tar -g {} -zxvf {} >> {} 2>&1'.format(os.path.dirname(path), snapshot_file, tar_file, self.__path_restore_log_file)
            public.writeFile(self.__path_restore_log_file, '目录[{}]增量备份恢复命令：{}'.format(path, cmd), 'a+')
            public.ExecShell(cmd)
            # 删除解压出来的文件夹
            self.remove_dir(full_backup_path)
            self.remove_dir(inc_backup_path)
            public.writeFile(self.__path_restore_log_file, "备份恢复之后要进行一次全量备份", 'a+')
            self.start_path_full_backup_task_d(path)
            public.writeFile(self.__path_restore_log_file, "目录[{}]使用文件[{}]完成增量备份恢复".format(path, inc_file_path), 'a+')
            public.WriteLog(self.__log_type, "目录[{}]使用文件[{}]完成增量备份恢复".format(path, inc_file_path))
            os.remove(self.__path_restore_log_file)
            return public.returnMsg(True, '恢复目录[{}]数据完成'.format(path))
        except:
            self.remove_dir(full_backup_path)
            self.remove_dir(inc_backup_path)
            os.remove(self.__path_restore_log_file)
            return public.returnMsg(False, '恢复目录[{}]数据失败，原因：{}'.format(path, public.get_error_info()))

    # 删除云端存储的目录备份文件
    def path_delete_cloud_backup(self, storage_type, backup_type, filename):
        get = public.dict_obj()
        get.filename = filename
        if backup_type == 'full':
            get.path = '/enterprise_backup/path/full'
        elif backup_type == 'inc':
            get.path = '/enterprise_backup/path/inc'

        if storage_type == 'ftp':
            from upload_ftp import ftp_main
            myftp = ftp_main()
            myftp.rmFile(get)
        elif storage_type == 'alioss':
            from upload_alioss import alioss_main
            myalioss = alioss_main()
            myalioss.remove_file(get)
        elif storage_type == 'txcos':
            from upload_txcos import txcos_main
            mytxcos = txcos_main()
            mytxcos.remove_file(get)
        elif storage_type == 'qiniu':
            from upload_qiniu import qiniu_main
            myqiniu = qiniu_main()
            myqiniu.remove_file(get)
        elif storage_type == 'aws':
            from upload_aws import aws_main
            myaws = aws_main()
            myaws.remove_file(get)

    # 删除目录全量备份记录
    def delete_path_full_backup(self, id, delete_cloud=False):
        backup_info = public.M('path_full_backup').where('id=?', id).find()
        file_path = backup_info['file_path']
        filename = os.path.basename(file_path)
        setting_info = public.M('path_backup_setting').where('id=?', backup_info['sid']).find()
        path = setting_info['path']
        if os.path.exists(file_path): os.remove(file_path)
        if delete_cloud:
            # 删除ftp备份
            if setting_info['upload_ftp']:
                self.path_delete_cloud_backup('ftp', 'full', filename)
            # 删除阿里云oss备份
            if setting_info['upload_alioss']:
                self.path_delete_cloud_backup('alioss', 'full', filename)
            # 删除腾讯cos备份
            if setting_info['upload_txcos']:
                self.path_delete_cloud_backup('txcos', 'full', filename)
            # 删除七牛云存储备份
            if setting_info['upload_qiniu']:
                self.path_delete_cloud_backup('qiniu', 'full', filename)
            # 删除亚马逊S3云存储备份
            if setting_info['upload_aws']:
                self.path_delete_cloud_backup('aws', 'full', filename)
        public.M('path_full_backup').where('id=?', id).delete()
        return public.returnMsg(True, '删除成功')

    # 对外接口
    def delete_path_full_backup_api(self, get):
        return self.delete_path_full_backup(get.id)

    # 删除目录增量备份记录
    def delete_path_inc_backup(self, id, delete_cloud=False):
        backup_info = public.M('path_inc_backup').where('id=?', id).find()
        file_path = backup_info['inc_file_path']
        filename = os.path.basename(file_path)
        setting_info = public.M('path_backup_setting').where('id=?', backup_info['sid']).find()
        path = setting_info['path']
        if os.path.exists(file_path): os.remove(file_path)
        if delete_cloud:
            # 删除ftp备份
            if setting_info['upload_ftp']:
                self.path_delete_cloud_backup('ftp', 'inc', filename)
            # 删除阿里云oss备份
            if setting_info['upload_alioss']:
                self.path_delete_cloud_backup('alioss', 'inc', filename)
            # 删除腾讯cos备份
            if setting_info['upload_txcos']:
                self.path_delete_cloud_backup('txcos', 'inc', filename)
            # 删除七牛云存储备份
            if setting_info['upload_qiniu']:
                self.path_delete_cloud_backup('qiniu', 'inc', filename)
            # 删除亚马逊S3云存储备份
            if setting_info['upload_aws']:
                self.path_delete_cloud_backup('aws', 'inc', filename)
        public.M('path_inc_backup').where('id=?', id).delete()
        return public.returnMsg(True, '删除成功')

    # 对外接口
    def delete_path_inc_backup_api(self, get):
        return self.delete_path_inc_backup(get.id)

    # 获取目录备份任务执行日志
    def get_path_backup_logs(self, get):
        if 'id' not in get: return public.returnMsg(False, '错误的参数!')
        id = get.id
        pdata = public.M('path_backup_setting').where('id=?', id).find()

        try:
            p = crontab.crontab()
            # 获取全量备份计划任务执行日志
            id = public.M('crontab').where("name=?", "[勿删]企业级备份-目录全量备份任务[{}]".format(pdata['path'])).getField('id')
            if not id: return public.returnMsg(False, '请检查计划任务是否存在')
            args = {"id": id}
            full_backup_logs = p.GetLogs(args)['msg']
            if int(pdata['inc_backup_need']) == 1:
                # 获取增量备份计划任务执行日志
                id = public.M('crontab').where("name=?", "[勿删]企业级备份-目录增量备份任务[{}]".format(pdata['path'])).getField('id')
                if not id: return public.returnMsg(False, '请检查计划任务是否存在')
                args = {"id": id}
                inc_backup_logs = p.GetLogs(args)['msg']
            else:
                inc_backup_logs = ''
            return {'full_backup_logs': full_backup_logs, 'inc_backup_logs': inc_backup_logs}
        except:
            return public.returnMsg(False, '目录备份加入了增量备份功能，请重新编辑一下此备份任务')

    # 执行目录全量备份任务
    def start_path_full_backup_task(self, path):
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-目录全量备份任务[{}]".format(path)).getField('echo')
        if not echo: return public.returnMsg(False, '请检查计划任务是否存在')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(False, '目录[{}]全量备份任务正在进行中'.format(path))
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell(execstr + ' >> ' + execstr + '.log 2>&1')
        return public.returnMsg(True, '目录[{}]全量备份任务执行完成'.format(path))

    # 后台执行目录全量备份任务
    def start_path_full_backup_task_d(self, path):
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-目录全量备份任务[{}]".format(path)).getField('echo')
        if not echo: return public.returnMsg(False, '请检查计划任务是否存在')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(False, '目录[{}]全量备份任务正在进行中'.format(path))
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell('nohup ' + execstr + ' >> ' + execstr + '.log 2>&1 &')
        return public.returnMsg(True, '目录[{}]全量备份任务执行完成'.format(path))

    # 执行目录全量备份任务
    def start_path_inc_backup_task(self, path):
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-目录增量备份任务[{}]".format(path)).getField('echo')
        if not echo: return public.returnMsg(False, '请检查计划任务是否存在')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(False, '目录[{}]增量备份任务正在进行中'.format(path))
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell(execstr + ' >> ' + execstr + '.log 2>&1')
        return public.returnMsg(True, '目录[{}]增量备份任务执行完成'.format(path))

    def start_path_backup_task(self, get):
        try:
            setting_info = public.M('path_backup_setting').where('id=?', get.id).find()
            path = setting_info['path']
            if int(setting_info['inc_backup_need']) == 1:
                return self.start_path_inc_backup_task(path)
            else:
                return self.start_path_full_backup_task(path)
        except:
            return public.returnMsg(False, '目录备份加入了增量备份功能，请重新编辑一下此备份任务')

    # 获取执行目录备份日志输出
    def get_path_backup_output(self, get):
        inc_backup_log_file = self.__path_backup_log_file + str(get.id) + '_inc'
        full_backup_log_file = self.__path_backup_log_file + str(get.id) + '_full'
        # 判断备份是否进行
        setting_info = public.M('path_backup_setting').where('id=?', get.id).find()
        backup_obj = setting_info['path']
        if int(setting_info['inc_backup_need']) == 1:
            echo = public.M('crontab').where("name=?", "[勿删]企业级备份-目录增量备份任务[{}]".format(backup_obj)).getField('echo')
        else:
            echo = public.M('crontab').where("name=?", "[勿删]企业级备份-目录全量备份任务[{}]".format(backup_obj)).getField('echo')
        if not echo: return public.returnMsg(False, '请检查计划任务是否存在')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(True, public.GetNumLines(inc_backup_log_file, 500) + public.GetNumLines(full_backup_log_file, 500))
        else:
            return public.returnMsg(False, '')

    # 获取目录恢复日志
    def get_path_restore_output(self, get):
        if os.path.exists(self.__path_restore_log_file):
            return public.returnMsg(True, public.GetNumLines(self.__path_restore_log_file, 500))
        else:
            return public.returnMsg(False, '')

    # 导出企业级备份插件相关数据库记录
    def export_sql_data(self, get):
        data = {}
        data['mysql_backup_setting'] = public.M('mysql_backup_setting').select()
        data['mysql_full_backup'] = public.M('mysql_full_backup').select()
        data['mysql_inc_backup'] = public.M('mysql_inc_backup').select()
        data['path_backup_setting'] = public.M('path_backup_setting').select()
        data['path_full_backup'] = public.M('path_full_backup').select()
        data['path_inc_backup'] = public.M('path_inc_backup').select()
        file_name = os.path.join(self.__db_record_path, time.strftime('%Y%m%d%H%M%S', time.localtime()) + '.json')
        public.writeFile(file_name, json.dumps(data))
        return public.returnMsg(True, '导出记录到{}成功'.format(file_name))

    # 导入企业级备份插件相关数据库记录和计划任务
    def import_sql_data(self, get):
        file_path = get.file_path.strip()
        if not os.path.exists(file_path):
            return public.returnMsg(False, '文件[%s]不存在' % file_path)
        if public.M('mysql_backup_setting').count() or public.M('path_backup_setting').count():
            return public.returnMsg(False, '请确保您的插件是新安装的')
        data = json.loads(public.readFile(file_path))
        print(data)
        # 还原mysql_backup_setting表的数据
        for pdata in data['mysql_backup_setting']:
            if public.M('mysql_backup_setting').where('database=?', pdata['database']).count():
                continue
            print(pdata)
            public.M('mysql_backup_setting').insert(pdata)
            self.add_mysql_full_backup_task(pdata)
            if int(pdata['inc_backup_need']) == 1:
                self.add_mysql_inc_backup_task(pdata)
        # 还原mysql_full_backup表的数据
        for pdata in data['mysql_full_backup']:
            if public.M('mysql_full_backup').where('id=?', pdata['id']).count():
                continue
            print(pdata)
            public.M('mysql_full_backup').insert(pdata)
        # 还原mysql_inc_backup表的数据
        for pdata in data['mysql_inc_backup']:
            if public.M('mysql_inc_backup').where('id=?', pdata['id']).count():
                continue
            print(pdata)
            public.M('mysql_inc_backup').insert(pdata)
        # 还原path_backup_setting表的数据
        for pdata in data['path_backup_setting']:
            if public.M('path_backup_setting').where('path=?', pdata['path']).count():
                continue
            print(pdata)
            public.M('path_backup_setting').insert(pdata)
            self.add_path_full_backup_task(pdata)
            if int(pdata['inc_backup_need']) == 1:
                self.add_path_inc_backup_task(pdata)
        # 还原path_full_backup表的数据
        for pdata in data['path_full_backup']:
            if public.M('path_full_backup').where('id=?', pdata['id']).count():
                continue
            print(pdata)
            public.M('path_full_backup').insert(pdata)
        # 还原path_inc_backup表的数据
        for pdata in data['path_inc_backup']:
            if public.M('path_inc_backup').where('id=?', pdata['id']).count():
                continue
            print(pdata)
            public.M('path_inc_backup').insert(pdata)
        return public.returnMsg(True, '导入成功')

    def get_log_backup_conf(self, get):
        '''
        获取日志备份任务设置
        :param get:
        :return:
        '''
        log_backup_conf = os.path.join(self.__configPath, 'log_backup_conf.json')
        if not os.path.exists(log_backup_conf):
            data = {'save': 180, 'upload_local': 1, 'upload_ftp': 0, 'upload_alioss': 0, 'upload_txcos': 0, 'upload_qiniu': 0, 'upload_aws': 0, 'select_website': 'ALL',
                    'backup_website': 1, 'backup_mysql': 1, 'backup_secure': 1, 'backup_messages': 1, 'where_hour': 0, 'where_minute': 0, 'type': 'day', 'where_week': '', 'where1': ''}
        else:
            data = json.loads(public.readFile(log_backup_conf))
        if 'select_website' not in data: data['select_website'] = 'ALL'
        if 'upload_local' not in data: data['upload_local'] = 1
        if 'backup_website' not in data: data['backup_website'] = 1
        if 'backup_mysql' not in data: data['backup_mysql'] = 1
        if 'backup_secure' not in data: data['backup_secure'] = 1
        if 'backup_messages' not in data: data['backup_messages'] = 1
        if 'where_hour' not in data: data['where_hour'] = 0
        if 'where_minute' not in data: data['where_minute'] = 0
        if 'type' not in data: data['type'] = 'day'
        if 'where_week' not in data: data['where_week'] = ''
        if 'where1' not in data: data['where1'] = ''
        public.writeFile(log_backup_conf, json.dumps(data))
        if public.M('crontab').where('name=?', '[勿删]企业级备份-日志备份任务').count():
            data['open'] = True
        else:
            data['open'] = False
        return data

    def get_site_list(self, get):
        '''
        获取网站列表
        :param get:
        :return:
        '''
        data = public.M('sites').field('name,ps').select()
        select_website = self.get_log_backup_conf(get)['select_website']
        site_list = []
        for i in data:
            tmp = {}
            tmp['name'] = i['name']
            tmp['checked'] = False
            if select_website == 'ALL':
                tmp['checked'] = True
            else:
                if tmp['name'] in select_website.split(','):
                    tmp['checked'] = True
            site_list.append(tmp)
        return site_list

    def set_log_backup_conf(self, get):
        '''
        设置日志备份任务
        :param self:
        :param get:
        :return:
        '''
        conf = {}
        conf['save'] = int(get.save)
        conf['type'] = get.type
        conf['where1'] = int(get.where1) if 'where1' in get else ''
        conf['where_week'] = int(get.where_week) if 'where_week' in get else ''
        conf['where_hour'] = int(get.where_hour) if 'where_hour' in get else ''
        conf['where_minute'] = int(get.where_minute) if 'where_minute' in get else ''
        conf['upload_local'] = int(get.upload_local) if 'upload_local' in get else 1
        conf['upload_ftp'] = int(get.upload_ftp) if 'upload_ftp' in get else 0
        conf['upload_alioss'] = int(get.upload_alioss) if 'upload_alioss' in get else 0
        conf['upload_txcos'] = int(get.upload_txcos) if 'upload_txcos' in get else 0
        conf['upload_qiniu'] = int(get.upload_qiniu) if 'upload_qiniu' in get else 0
        conf['upload_aws'] = int(get.upload_aws) if 'upload_aws' in get else 0
        conf['backup_website'] = int(get.backup_website) if 'backup_website' in get else 1
        conf['select_website'] = get.select_website.strip(',') if 'select_website' in get else 'ALL'
        conf['backup_mysql'] = int(get.backup_mysql) if 'backup_mysql' in get else 1
        conf['backup_secure'] = int(get.backup_secure) if 'backup_secure' in get else 1
        conf['backup_messages'] = int(get.backup_messages) if 'backup_messages' in get else 1
        public.writeFile(os.path.join(self.__configPath, 'log_backup_conf.json'), json.dumps(conf))
        public.WriteLog(self.__log_type, '设置日志备份配置')
        self.open_log_backup_task(get)
        return public.returnMsg(True, '设置成功')

    def open_log_backup_task(self, get):
        '''
        打开日志备份任务
        :param get:
        :return:
        '''
        p = crontab.crontab()
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        c_id = public.M('crontab').where('name=?', '[勿删]企业级备份-日志备份任务').getField('id')
        if c_id:
            args = {
                "id": c_id,
                "name": '[勿删]企业级备份-日志备份任务',
                "type": get.type,
                "where1": int(get.where1) if 'where1' in get else '',
                "hour": int(get.where_hour) if 'where_hour' in get else '',
                "minute": int(get.where_minute) if 'where_minute' in get else '',
                "week": int(get.where_week) if 'where_week' in get else '',
                "sType": 'toShell',
                "sName": '',
                "backupTo": '',
                "save": get.save,
                "sBody": '{} {}/crontab_tasks/log_backup.py'.format(python_path, self.__plugin_path),
                "urladdress": ''
            }
            p.modify_crond(args)
            public.WriteLog(self.__log_type, '修改日志备份任务')
        else:
            args = {
                "name": '[勿删]企业级备份-日志备份任务',
                "type": get.type,
                "where1": int(get.where1) if 'where1' in get else '',
                "hour": int(get.where_hour) if 'where_hour' in get else '',
                "minute": int(get.where_minute) if 'where_minute' in get else '',
                "week": int(get.where_week) if 'where_week' in get else '',
                "sType": 'toShell',
                "sName": '',
                "backupTo": '',
                "save": get.save,
                "sBody": '{} {}/crontab_tasks/log_backup.py'.format(python_path, self.__plugin_path),
                "urladdress": ''
            }
            p.AddCrontab(args)
            public.WriteLog(self.__log_type, '开启日志备份任务')
        return public.returnMsg(True, '设置成功')

    def close_log_backup_task(self, get):
        '''
        关闭日志备份任务
        :param get:
        :return:
        '''
        id = public.M('crontab').where('name=?', '[勿删]企业级备份-日志备份任务').getField('id')
        if id: crontab.crontab().DelCrontab({'id': id})
        public.WriteLog(self.__log_type, '关闭日志备份任务')
        return public.returnMsg(True, '关闭成功')

    def start_log_backup_task(self, get):
        '''
        执行日志备份任务
        :param get:
        :return:
        '''
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-日志备份任务").getField('echo')
        if not echo: return public.returnMsg(False, '请检查计划任务是否存在')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(False, '日志备份任务正在进行中')
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell(execstr + ' >> ' + execstr + '.log 2>&1')
        return public.returnMsg(True, '日志备份任务执行完成')

    def get_log_backup_output(self, get):
        '''
        获取日志备份任务执行输出
        :param get:
        :return:
        '''
        # 判断任务是否进行
        echo = public.M('crontab').where("name=?", "[勿删]企业级备份-日志备份任务").getField('echo')
        if not echo: return public.returnMsg(False, '请检查计划任务是否存在')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        if self.process_exists(execstr):
            return public.returnMsg(True, public.GetNumLines(self.__log_backup_output_file, 500))
        else:
            return public.returnMsg(False, '')

    def get_log_backup_logs(self, get):
        '''
        获取日志备份任务执行日志
        :param get:
        :return:
        '''
        p = crontab.crontab()
        id = public.M('crontab').where("name=?", "[勿删]企业级备份-日志备份任务").getField('id')
        if not id: return public.returnMsg(False, '请检查计划任务是否存在')
        args = {"id": id}
        backup_logs = p.GetLogs(args)['msg']
        return public.returnMsg(True, backup_logs)

    def open_tar_pass(self, get):
        '''
        打开压缩加密设置
        :param get:
        :return:
        '''
        if not os.path.exists(self.__encrypt_file):
            public.writeFile(self.__encrypt_file, '')
        return public.returnMsg(True, '设置成功')

    def close_tar_pass(self, get):
        '''
        关闭压缩加密设置
        :param get:
        :return:
        '''
        if os.path.exists(self.__encrypt_file):
            os.remove(self.__encrypt_file)
        return public.returnMsg(True, '关闭成功')

    def get_tar_pass(self, get):
        '''
        获取压缩加密是否打开
        :param get:
        :return:
        '''
        if os.path.exists(self.__encrypt_file):
            return {'open': True, 'password': self.__tar_pass}
        else:
            return {'open': False, 'password': self.__tar_pass}
