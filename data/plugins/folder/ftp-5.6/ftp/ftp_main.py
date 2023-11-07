#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 宝塔Linux面板网站备份工具 TO FTP
# -----------------------------
from __future__ import print_function, absolute_import, division

import platform
import sys, os, re, json
import time
import paramiko
import ftplib

BASE_PATH = "/www/server/panel"

os.chdir(BASE_PATH)
sys.path.insert(0, "class/")

import public, db

DEBUG = False
BLOCK_SIZE = 1024 * 1024 * 2
PROGRESS_FILE_NAME = "PROGRESS_FILE_NAME"

_ver = sys.version_info
#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)

if is_py2:
    reload(sys)
    sys.setdefaultencoding('utf-8')


def report_progress(consumed_bytes, total_bytes):
    """上传进度回调函数

    本函数依赖系统环境变量 PROGRESS_FILE_NAME 所指定的文件，进度信息会写入到该文件当中
    进度格式:
    上传百分比|速度(Mb/s)|时间(s)|上传字节|总字节|开始时间戳
    :param consumed_bytes: 已上传字节数
    :param total_bytes: 总字节数
    """
    import public
    p_file = os.environ[PROGRESS_FILE_NAME]
    rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
    if consumed_bytes == 0:
        start_time = time.time()
    else:
        p_text = public.readFile(p_file)
        if not p_text:
            return
        start_time = float(p_text.split("|")[-1])
    now = time.time()
    diff = round(now - start_time, 2)
    speed = round(consumed_bytes / diff / 1024 / 1024, 2) if diff > 0 else 0
    progress_text = "{0}%|{1}Mb/s|{2}|{3}|{4}|{5}".format(
        rate, speed, diff, consumed_bytes, total_bytes, start_time
    )
    if consumed_bytes == total_bytes:
        progress_text += "\n"
    public.writeFile(p_file, progress_text)
    sys.stdout.write("\r" + progress_text)
    sys.stdout.flush()


def percentage(consumed_bytes, total_bytes):
    """命令行进度回调

    :param consumed_bytes:
    :param total_bytes:
    :return:
    """
    if total_bytes:
        rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
        display_consumed = round(consumed_bytes / 1024 / 1024, 2)
        display_total = round(total_bytes / 1024 / 1024, 2)
        progress_text = '{0}%|{1}M|{2}M'.format(
            rate, display_consumed, display_total)
        sys.stdout.write("\r" + progress_text)
        sys.stdout.flush()


def get_tmpdir_path():
    """获取本地临时目录

    兼容: linux,windows
    """
    sysstr = platform.system().lower()
    tmp_dir = ""
    if sysstr == "linux":
        tmp_dir = "/tmp/"
    elif sysstr == "windows":
        base_path = os.getenv("BT_PANEL")
        tmp_dir = os.path.join(base_path, "tmp")

    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    return tmp_dir


def get_text_timestamp():
    import time
    timestamp = time.time()
    text = "" + repr(timestamp)
    text = text.replace(".", "")
    return text


def generate_random_str():
    text = get_text_timestamp()
    rand_text = "".join(random.sample(string.ascii_letters, 5))
    rand_text = text + rand_text
    return rand_text


def convert_time(tmsp):
    import datetime
    if tmsp:
        mtime = datetime.datetime.fromtimestamp(tmsp)
        mtime += datetime.timedelta(hours=8)
        ts = int(
            (time.mktime(mtime.timetuple()) + mtime.microsecond / 1000000.0))
        return ts
    return tmsp


def verify_dir_name(dir_name):
    """验证目录名是否包含非法字符

    """
    invalid_symbol = [
        "%2F",  # 防止被替换成/
    ]
    for s in invalid_symbol:
        if dir_name.find(s) != -1:
            return False
    return True


"""
=============自定义异常===================
"""


class OsError(Exception):
    """OS端异常"""


class ObjectNotFound(OsError):
    """对象不存在时抛出的异常"""

    def __init__(self, *args, **kwargs):
        message = "文件对象不存在。"
        super(ObjectNotFound, self).__init__(message, *args, **kwargs)


class APIError(Exception):
    """API参数错误异常"""

    def __init__(self, *args, **kwargs):
        _api_error_msg = 'API资料校验失败，请核实!'
        super(APIError, self).__init__(_api_error_msg, *args, **kwargs)


"""
=============FTPClient===================
"""


class FTPClient(object):
    _name = ""
    _title = ""
    default_backup_path = "/bt_backup/"
    backup_path = default_backup_path
    CONFIG_SEPARATOR = "|"
    config_file = "config.conf"
    delimiter = "/"
    exclude = ""
    auth = None
    _inode_min = 10
    _exclude = ""
    _db_mysql = None
    _err_log = '/tmp/backup_err.log'
    error_msg = ""
    _panel_path = public.get_panel_path()
    _aes_status = os.path.join(_panel_path, 'plugin/ftp/aes_status')
    _a_pass = os.path.join(_panel_path, 'data/a_pass.pl')

    def __init__(self, load_config=True, config_file=None):
        if config_file:
            self.config_file = config_file
        self.__auth = None

        # 控制客户端是否从配置文件加载配置
        if load_config:
            data = self.get_config()
            self.init_config(data)

    #########################
    #####OS客户端自定义实现#####
    #########################

    def init_config(self, data):
        return False

    def get_config(self):
        return {}

    def get_list(self, path="/"):
        """子类实现获取文件列表

        参考以下字段返回文件列表
        """
        mlist = {
            "list": [
                # 1. 文件夹
                {
                    "name": "",  # 文件名称
                    "type": None,  # type为None表示是文件夹
                },
                # 2. 文件
                {
                    "name": "",  # 文件名称
                    "download": "",
                    "size": "",  # 文件大小
                    "time": "",  # 上传时间
                }
            ],
            "path": "/",
        }
        return mlist

    def generate_download_url(self, object_name):
        """os客户端实现生成下载链接"""
        return ""

    def resumable_upload(self, *arg, **kwargs):
        """断点续传子类实现"""
        raise RuntimeError("不支持上传操作！")

    def delete_dir_by_client(self, dir_name):
        raise RuntimeError("暂时不支持文件夹删除！")

    def delete_file_by_client(self, object_name):
        """OS客户端实现删除操作"""
        raise RuntimeError("文件无法被删除！")

    def get_lib(self):
        """注册计划任务"""
        return True

    #########################
    ######OS客户端通用实现######
    #########################

    def get_base_path(self):
        """根据操作系统获取运行基础路径"""
        return "/www/server/panel"

    def get_setup_path(self):
        """插件安装路径"""
        return os.path.join("plugin", self._name)

    def get_config_file(self):
        """获取配置文件路径"""

        path = os.path.join(self.get_setup_path(), self.config_file);
        return path

    def get_bak_config_file(self):
        """备份配置文件路径"""
        return os.path.join(self.get_base_path(), "data",
                            self._name + "AS.conf")

    def set_config(self, conf):
        """写入配置文件"""

        public.writeFile(self._aes_status, 'True')
        path = os.path.join(self.get_base_path(), self.get_config_file())
        if not os.path.isfile(self._a_pass):
            public.writeFile(self._a_pass, 'VE508prf' + public.GetRandomString(10))
        aes_key = public.readFile(self._a_pass)
        w_data = public.aes_encrypt(conf, aes_key)
        public.writeFile(path, w_data)

        bak_path = self.get_bak_config_file()
        public.writeFile(bak_path, w_data)
        return True

    # 取目录路径
    def get_path(self, path):
        if path[-1:] != '/': path += '/';
        if path[:1] != '/': path = '/' + path;
        return path.replace('//', '/');

    def build_object_name(self, data_type, file_name):
        """根据数据类型构建对象存储名称

        :param data_type:
        :param file_name:
        :return:
        """

        import re
        prefix_dict = {
            "site": "web",
            "database": "db",
            "path": "path",
        }
        file_regx = prefix_dict.get(data_type) + "_(.+)_20\d+_\d+(?:\.|_)"
        sub_search = re.search(file_regx, file_name)
        sub_path_name = ""
        if sub_search:
            sub_path_name = sub_search.groups()[0]
            sub_path_name += '/'

        # 构建OS存储路径
        object_name = self.backup_path + \
                      data_type + '/' + \
                      sub_path_name + \
                      file_name
        return object_name

    def upload_file(self, file_name, data_type=None, *args, **kwargs):
        """按照数据类型上传文件

        针对 panelBackup v1.2以上调用
        :param file_name: 上传文件名称
        :param data_type: 数据类型 site/database/path
        :return: True/False
        """
        try:
            import re
            # 根据数据类型提取子分类名称
            # 比如data_type=database，子分类名称是数据库的名称。
            # 提取方式是从file_name中利用正则规则去提取。
            self.error_msg = ""

            if not file_name or not data_type:
                self.error_msg = "文件参数错误。"
                print(self.error_msg)
                return False

            file_name = os.path.abspath(file_name)
            temp_name = os.path.split(file_name)[1]
            object_name = self.build_object_name(data_type, temp_name)

            return self.resumable_upload(file_name,
                                         object_name=object_name,
                                         *args,
                                         **kwargs)
        except Exception as e:
            if self.error_msg:
                self.error_msg += r"\n"
            self.error_msg += "文件上传出现错误：{}".format(str(e))
            return False

    def delete_object(self, object_name, retries=2):
        """删除对象

        :param object_name:
        :param retries: 重试次数，默认2次
        :return: True 删除成功
                其他 删除失败
        """

        try:
            return self.delete_file_by_client(object_name)
        except Exception as e:
            print("删除文件异常：")
            print(e)

        # 重试
        if retries > 0:
            print("重新尝试删除文件{}...".format(object_name))
            return self.delete_object(
                object_name,
                retries=retries - 1)
        return False

    def delete_file(self, file_name, data_type=None):
        """删除文件

        针对 panelBackup v1.2以上调用
        根据传入的文件名称和文件数据类型构建对象名称，再删除
        :param file_name:
        :param data_type: 数据类型 site/database/path
        :return: True 删除成功
                其他 删除失败
        """

        object_name = self.build_object_name(data_type, file_name)
        return self.delete_object(object_name)

    def delete_dir(self, dir_name):
        """删除文件夹

        :return: True 删除成功
                其他 删除失败
        """
        return self.delete_dir_by_client(dir_name)

    # 备份网站
    def backupSite(self, name, count, exclude=[]):
        self.echo_start()
        data_type = "site"
        sql = db.Sql();
        path = sql.table('sites').where('name=?', (name,)).getField('path');
        self.echo_info('备份网站：{}'.format(name))
        self.echo_info('网站根目录：{}'.format(path))

        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "网站[" + name + "]不存在!"
            self.echo_error("★[" + endDate + "] " + log)
            self.echo_end()
            return;

        p_size = public.get_path_size(path)
        self.echo_info("目录大小：{}".format(public.to_size(p_size)))

        backup_path = sql.table('config').where("id=?", (1,)).getField(
            'backup_path') + '/site';
        if not os.path.exists(backup_path): public.ExecShell(
            "mkdir -p " + backup_path);

        base_file_name = "web_" + name + "_" + time.strftime(
            '%Y%m%d_%H%M%S', time.localtime()) + '.tar.gz'
        filename = backup_path + "/" + base_file_name

        self.get_exclude(exclude)
        exclude_config = self._exclude
        if not self._exclude:
            exclude_config = "未设置"

        disk_path, disk_free, disk_inode = self.get_disk_free(filename)
        self.echo_info("分区{}可用磁盘空间为：{}，可用Inode为：{}".format(
            disk_path,
            public.to_size(disk_free),
            disk_inode))
        if disk_path:
            if disk_free < p_size:
                self.echo_error(
                    "目标分区可用的磁盘空间小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(
                        public.to_size(p_size)))
                return False

            if disk_inode < self._inode_min:
                self.echo_error(
                    "目标分区可用的Inode小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(
                        self._inode_min))
                return False

        public.ExecShell("cd " +
                         os.path.dirname(path) +
                         " && tar zcvf '" + filename +
                         "' " + self._exclude + " '" +
                         os.path.basename(path) +
                         "' 2>{err_log} 1> /dev/null".format(
                             err_log=self._err_log))
        endDate = time.strftime('%Y/%m/%d %X', time.localtime())

        if not os.path.exists(filename):
            log = "网站[" + name + "]备份失败!"
            self.echo_error("★[" + endDate + "] " + log)
            self.echo_end()
            return;

        self.echo_info("站点已备份到:" + filename)

        # 上传文件
        self.echo_info("正在上传到{}，请稍候...".format(self._title))
        if self.upload_file(filename, data_type=data_type):
            self.echo_info("已成功上传到{}".format(self._title))
        else:
            self.echo_error('错误：文件上传失败，跳过本次备份!')
            if os.path.exists(filename):
                os.remove(filename)
            return False

        object_name = self.build_object_name(data_type, base_file_name)
        outTime = time.time() - startTime
        tag = self.CONFIG_SEPARATOR + self._name
        db_filename = object_name + tag
        pid = sql.table('sites').where('name=?', (name,)).getField('id');
        sql.table('backup').add('type,name,pid,filename,addtime,size', (
            '0', base_file_name, pid, db_filename, endDate,
            os.path.getsize(filename)))
        log = "网站[" + name + "]已成功备份到" + self._title + ",用时[" + str(
            round(outTime, 2)) + "]秒";
        public.WriteLog('计划任务', log)
        self.echo_info(u"★[" + endDate + "] " + log)
        self.echo_info(u"保留最新的[" + count + "]份备份")
        self.echo_info(u"排除规则: " + exclude_config)

        # 清理多余备份
        backups = sql.table('backup').where(
            'type=? and pid=? and '
            'filename LIKE \'%{}%\''.format(tag),
            ('0', pid)).field('id,name,filename').select();

        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                _base_file_name = backup["name"]
                _local_file_name = os.path.join(backup_path,
                                                _base_file_name)

                if os.path.isfile(_local_file_name):
                    public.ExecShell("rm -f " + _local_file_name);
                    self.echo_info("已清理本地备份文件:" + _local_file_name)

                _file_name = backup["filename"]
                if _file_name.find(self.CONFIG_SEPARATOR) != -1:
                    os_file_name = _file_name.split(self.CONFIG_SEPARATOR)[0]
                else:
                    os_file_name = self.build_object_name(data_type,
                                                          _base_file_name)
                self.delete_object(os_file_name)
                sql.table('backup').where('id=?', (backup['id'],)).delete();
                num -= 1;
                self.echo_info("已清理{}过期备份文件：".format(self._title) +
                               os_file_name)
                if num < 1: break;

        if os.path.exists(self._err_log):
            os.remove(self._err_log)
        self.echo_end()
        return None

    # 配置
    def mypass(self, act, root):
        conf_file = '/etc/my.cnf'
        public.ExecShell("sed -i '/user=root/d' {}".format(conf_file))
        public.ExecShell("sed -i '/password=/d' {}".format(conf_file))
        if act:
            mycnf = public.readFile(conf_file);
            src_dump = "[mysqldump]\n"
            sub_dump = src_dump + "user=root\npassword=\"{}\"\n".format(root);
            if not mycnf: return False
            mycnf = mycnf.replace(src_dump, sub_dump)
            if len(mycnf) > 100: public.writeFile(conf_file, mycnf);
            return True
        return True

    # 备份数据库
    def backupDatabase(self, name, count):
        self.echo_start()
        os_title = self._title
        data_type = "database"

        self.echo_info('备份数据库：{}'.format(name))
        sql = db.Sql();
        path = sql.table('databases').where('name=?', (name,)).getField('id');

        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "数据库[" + name + "]不存在!"
            self.echo_error("★[" + endDate + "] " + log)
            self.echo_end()
            return;

        import panelMysql
        if not self._db_mysql: self._db_mysql = panelMysql.panelMysql()
        d_tmp = self._db_mysql.query(
            "select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from "
            "information_schema.tables where table_schema='%s'" % name)
        p_size = self.map_to_list(d_tmp)[0][0]

        if p_size is None:
            self.echo_error('指定数据库 `{}` 没有任何数据!'.format(name))
            self.echo_end()
            return

        self.echo_info("数据库大小：{}".format(public.to_size(p_size)))

        character = public.get_database_character(name)
        self.echo_info("数据库字符集：{}".format(character))

        backup_path = sql.table('config').where("id=?", (1,)).getField(
            'backup_path') + '/database';
        if not os.path.exists(backup_path): public.ExecShell(
            "mkdir -p " + backup_path);

        base_file_name = "db_" + name + "_" + time.strftime(
            '%Y%m%d_%H%M%S', time.localtime()) + ".sql.gz"
        filename = backup_path + "/" + base_file_name

        disk_path, disk_free, disk_inode = self.get_disk_free(filename)
        self.echo_info("分区{}可用磁盘空间为：{}，可用Inode为：{}".format(
            disk_path,
            public.to_size(disk_free),
            disk_inode))
        if disk_path:
            if disk_free < p_size:
                self.echo_error(
                    "目标分区可用的磁盘空间小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(
                        public.to_size(p_size)))
                return False

            if disk_inode < self._inode_min:
                self.echo_error(
                    "目标分区可用的Inode小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(
                        self._inode_min))
                return False

        stime = time.time()
        self.echo_info("开始导出数据库：{}".format(public.format_date(times=stime)))

        if os.path.exists(filename):
            os.remove(filename)

        mysql_root = sql.table('config').where("id=?", (1,)).getField(
            'mysql_root')
        self.mypass(True, mysql_root)

        public.ExecShell(
            "/www/server/mysql/bin/mysqldump --default-character-set=" +
            character + " --force --opt " + name + " | gzip > " + filename)

        self.mypass(False, mysql_root)

        if not os.path.exists(filename):
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "数据库[" + name + "]备份失败!"
            self.echo_error("★[" + endDate + "] " + log)
            self.echo_end()
            return;

        gz_size = os.path.getsize(filename)
        if gz_size < 400:
            self.echo_error("数据库导出失败!")
            self.echo_info(public.readFile(self._err_log))
            return False

        self.echo_info("数据库已备份到本地:" + filename)

        # 上传文件
        self.echo_info("正在上传到{}，请稍候...".format(self._title))
        if self.upload_file(filename, data_type=data_type):
            self.echo_info("已成功上传到{}".format(self._title))
        else:
            self.echo_error('错误：文件上传失败，跳过本次备份!')
            if os.path.exists(filename):
                os.remove(filename)
            return False

        object_name = self.build_object_name(data_type, base_file_name)
        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        outTime = time.time() - startTime
        pid = sql.table('databases').where('name=?', (name,)).getField('id');

        tag = self.CONFIG_SEPARATOR + self._name
        db_filename = object_name + tag
        sql.table('backup').add('type,name,pid,filename,addtime,size', (
            1, base_file_name, pid, db_filename, endDate,
            os.path.getsize(filename)))
        log = "数据库[" + name + "]已成功备份到" + os_title + ",用时[" + str(
            round(outTime, 2)) + "]秒";
        public.WriteLog('计划任务', log)
        self.echo_info("★[" + endDate + "] " + log)
        self.echo_info("保留最新的[" + count + "]份备份")

        # 清理本地备份
        if os.path.isfile(filename):
            os.remove(filename)

        # 清理多余备份
        backups = sql.table('backup').where(
            'type=? and pid=? and filename '
            'LIKE \'%{}%\''.format(tag),
            ('1', pid)).field('id,name,filename').select();

        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                _base_file_name = backup["name"]
                _local_file_name = os.path.join(backup_path, _base_file_name)
                if os.path.isfile(_local_file_name):
                    public.ExecShell("rm -f " + _local_file_name);
                    self.echo_info("已清理本地备份文件:" + _local_file_name)

                _file_name = backup["filename"]
                if _file_name.find(self.CONFIG_SEPARATOR) != -1:
                    _object_name = _file_name.split(self.CONFIG_SEPARATOR)[0]
                else:
                    _object_name = self.build_object_name(data_type,
                                                          _base_file_name)
                self.delete_object(_object_name)

                sql.table('backup').where('id=?', (backup['id'],)).delete();
                num -= 1;
                self.echo_info(
                    "已清理{}过期备份文件：".format(self._title) + _object_name)
                if num < 1: break;

        if os.path.exists(self._err_log):
            os.remove(self._err_log)
        self.echo_end()

    # 备份指定目录
    def backupPath(self, path, count, exclude=[]):
        self.echo_start()
        data_type = "path"

        sql = db.Sql();
        startTime = time.time();
        if path[-1:] == '/': path = path[:-1]

        self.echo_info('备份目录：{}'.format(path))
        p_size = public.get_path_size(path)
        self.echo_info("目录大小：{}".format(public.to_size(p_size)))

        self.get_exclude(exclude)
        exclude_config = self._exclude
        if not self._exclude:
            exclude_config = "未设置"

        name = os.path.basename(path)
        backup_path = sql.table('config').where("id=?", (1,)).getField(
            'backup_path') + '/path';
        if not os.path.exists(backup_path): os.makedirs(backup_path, 384);
        base_file_name = "path_" + name + "_" + time.strftime(
            '%Y%m%d_%H%M%S', time.localtime()) + '.tar.gz'
        filename = os.path.join(backup_path, base_file_name)

        disk_path, disk_free, disk_inode = self.get_disk_free(filename)
        self.echo_info("分区{}可用磁盘空间为：{}，可用Inode为：{}".format(disk_path,
                                                                       public.to_size(
                                                                           disk_free),
                                                                       disk_inode))
        if disk_path:
            if disk_free < p_size:
                self.echo_error(
                    "目标分区可用的磁盘空间小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(
                        public.to_size(p_size)))
                return False

            if disk_inode < self._inode_min:
                self.echo_error(
                    "目标分区可用的Inode小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(
                        self._inode_min))
                return False

        stime = time.time()
        self.echo_info("开始压缩文件：{}".format(public.format_date(times=stime)))

        if os.path.exists(filename):
            os.remove(filename)

        os.system("cd " + os.path.dirname(path) +
                  " && tar zcvf '" + filename + "' " +
                  self._exclude + " '" + os.path.basename(path) +
                  "' 2>{err_log} 1> /dev/null".format(
                      err_log=self._err_log))

        if not os.path.exists(filename):
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = u"目录[" + path + "]备份失败"
            self.echo_info(u"★[" + endDate + "] " + log)
            self.echo_end()
            return;

        tar_size = os.path.getsize(filename)
        if tar_size < 1:
            self.echo_error("数据压缩失败")
            self.echo_info(public.readFile(self._err_log))
            self.echo_end()
            return False

        self.echo_info("文件压缩完成，耗时{:.2f}秒，压缩包大小：{}".format(time.time() - stime,
                                                                        public.to_size(
                                                                            tar_size)))
        self.echo_info("目录已备份到：{}".format(filename))

        # 上传文件
        self.echo_info("正在上传到{}，请稍候...".format(self._title))
        if self.upload_file(filename, data_type=data_type):
            self.echo_info("已成功上传到{}".format(self._title))
        else:
            self.echo_error('错误：文件上传失败，跳过本次备份!')
            if os.path.exists(filename):
                os.remove(filename)
            return False

        # 添加备份记录
        object_name = self.build_object_name(data_type, base_file_name)
        tag_name = self.CONFIG_SEPARATOR + self._name
        db_filename = object_name + tag_name

        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        outTime = time.time() - startTime
        sql.table('backup').add('type,name,pid,filename,addtime,size', (
            '2', path, '0', db_filename, endDate,
            os.path.getsize(filename)))
        log = u"目录[" + path + "]备份成功,用时[" + str(round(outTime, 2)) + "]秒";
        public.WriteLog(u'计划任务', log)
        self.echo_info(u"★[" + endDate + "] " + log)
        self.echo_info(u"保留最新的[" + count + u"]份备份")
        self.echo_info(u"排除规则: " + exclude_config)

        # 清理本地文件
        if os.path.exists(filename):
            os.remove(filename)

        # 清理多余备份
        backups = sql.table('backup').where(
            'type=? and pid=? and name=? and filename LIKE "%{}%"'.format(
                tag_name),
            ('2', 0, path)).field('id,name,filename').select();

        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                _base_file_name = backup["name"]
                _local_file_name = os.path.join(backup_path, _base_file_name)
                if os.path.isfile(_local_file_name):
                    os.remove(_local_file_name)
                    self.echo_info("已清理本地备份文件:" + _local_file_name)

                _filename = backup["filename"]
                if _filename.find(self.CONFIG_SEPARATOR) != -1:
                    info = _filename.split(self.CONFIG_SEPARATOR)
                    os_file_name = info[0]
                else:
                    os_file_name = _filename
                self.delete_object(os_file_name)
                sql.table('backup').where('id=?', (backup['id'],)).delete();
                num -= 1;
                self.echo_info(
                    u"已清理{}过期备份文件：".format(self._title) + os_file_name)
                if num < 1: break;

        if os.path.exists(self._err_log):
            os.remove(self._err_log)
        self.echo_end()

    def backupSiteAll(self, save):
        sites = public.M('sites').field('name').select()
        for site in sites:
            self.backupSite(site['name'], save)

    def backupDatabaseAll(self, save):
        databases = public.M('databases').field('name').select()
        for database in databases:
            self.backupDatabase(database['name'], save)

    # 构造排除
    def get_exclude(self, exclude=[]):
        if not exclude:
            tmp_exclude = os.getenv('BT_EXCLUDE')
            if tmp_exclude:
                exclude = tmp_exclude.split(',')
        if not exclude: return ""
        for ex in exclude:
            self._exclude += " --exclude=\"" + ex + "\""
        self._exclude += " "
        return self._exclude

    # 取数据库字符集
    def get_database_character(self, db_name):
        try:
            import panelMysql
            tmp = panelMysql.panelMysql().query(
                "show create database `%s`" % db_name.strip())
            c_type = str(re.findall("SET\s+([\w\d-]+)\s", tmp[0][1])[0])
            c_types = ['utf8', 'utf-8', 'gbk', 'big5', 'utf8mb4']
            if not c_type.lower() in c_types: return 'utf8'
            return c_type
        except:
            return 'utf8'

    def get_object_info(self, object_name):
        """获取文件对象信息"""
        return True

    def echo_start(self):
        print("=" * 90)
        print("★开始备份[{}]".format(public.format_date()))
        print("=" * 90)

    def echo_end(self):
        print("=" * 90)
        print("☆备份完成[{}]".format(public.format_date()))
        print("=" * 90)
        print("\n")

    def echo_info(self, msg):
        print("|-{}".format(msg))

    def echo_error(self, msg):
        print("=" * 90)
        print("|-错误：{}".format(msg))

    def GetDiskInfo2(self):
        # 取磁盘分区信息
        temp = public.ExecShell("df -T -P|grep '/'|grep -v tmpfs")[0]
        tempInodes = public.ExecShell("df -i -P|grep '/'|grep -v tmpfs")[0]
        temp1 = temp.split('\n')
        tempInodes1 = tempInodes.split('\n')
        diskInfo = []
        n = 0
        cuts = []
        for tmp in temp1:
            n += 1
            try:
                inodes = tempInodes1[n - 1].split()
                disk = re.findall(
                    r"^(.+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\d%]{2,4})\s+(/.{0,50})$",
                    tmp.strip())
                if disk: disk = disk[0]
                if len(disk) < 6: continue
                if disk[2].find('M') != -1: continue
                if disk[2].find('K') != -1: continue
                if len(disk[6].split('/')) > 10: continue
                if disk[6] in cuts: continue
                if disk[6].find('docker') != -1: continue
                if disk[1].strip() in ['tmpfs']: continue
                arr = {}
                arr['filesystem'] = disk[0].strip()
                arr['type'] = disk[1].strip()
                arr['path'] = disk[6]
                tmp1 = [disk[2], disk[3], disk[4], disk[5]]
                arr['size'] = tmp1
                arr['inodes'] = [inodes[1], inodes[2], inodes[3], inodes[4]]
                diskInfo.append(arr)
            except:
                continue
        return diskInfo

    # 取磁盘可用空间
    def get_disk_free(self, dfile):
        diskInfo = self.GetDiskInfo2()
        if not diskInfo: return '', 0, 0
        _root = None
        for d in diskInfo:
            if d['path'] == '/':
                _root = d
                continue
            if re.match("^{}/.+".format(d['path']), dfile):
                return d['path'], float(d['size'][2]) * 1024, int(
                    d['inodes'][2])
        if _root:
            return _root['path'], float(_root['size'][2]) * 1024, int(
                _root['inodes'][2])
        return '', 0, 0

    # map to list
    def map_to_list(self, map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(
                map_obj)
            return map_obj
        except:
            return []

    def get_function_args(self, func):
        import sys
        if sys.version_info[0] == 3:
            import inspect
            return inspect.getfullargspec(func).args
        else:
            return func.__code__.co_varnames

    def execute_by_comandline(self, args):
        """命令行或计划任务调用

        针对panelBackup._VERSION >=1.2命令行调用
        :param args: 脚本参数
        """

        import panelBackup
        client = self
        cls_args = self.get_function_args(panelBackup.backup.__init__)
        if "cron_info" in cls_args and len(args) == 5:
            cron_name = args[4]
            cron_info = {
                "echo": cron_name
            }
            backup_tool = panelBackup.backup(cloud_object=client,
                                             cron_info=cron_info)
        else:
            backup_tool = panelBackup.backup(cloud_object=client)
        _type = args[1];
        data = None
        if _type == 'site':
            if args[2].lower() == "all":
                backup_tool.backup_site_all(save=int(args[3]), echo_id=args[4])
            else:
                backup_tool.backup_site(args[2], save=int(args[3]), echo_id=args[4])
            exit()
        elif _type == 'database':
            if args[2].lower() == "all":
                backup_tool.backup_database_all(int(args[3]), echo_id=args[4])
            else:
                backup_tool.backup_database(args[2], save=int(args[3]), echo_id=args[4])
            exit()
        elif _type == 'path':
            backup_tool.backup_path(args[2], save=int(args[3]), echo_id=args[4])
            exit()
        elif _type == 'upload':
            data = client.resumable_upload(args[2]);
        elif _type == 'download':
            data = client.generate_download_url(args[2]);
        # elif _type == 'get':
        #     data = client.get_files(args[2]);
        elif _type == 'list':
            path = "/"
            if len(args) == 3:
                path = args[2]
            data = client.get_list(path);
        elif _type == 'lib':
            data = client.get_lib()
        elif _type == 'delete_file':
            result = client.delete_object(args[2]);
            if result:
                print("文件{}删除成功。".format(args[2]))
            else:
                print("文件{}删除失败!".format(args[2]))
        else:
            data = 'ERROR: 参数不正确!';
        if data:
            print()
            print(json.dumps(data))


"""
=============btftp==========================
"""


class BTFTPClient(FTPClient, object):
    _title = "FTP"
    _name = "ftp"
    __host = None
    __port = None
    __user = None
    __password = None
    default_port = 21
    config_file = "ftp.config.conf"

    def __init__(self, load_config=True, timeout=None, config_file=None):
        super(BTFTPClient, self).__init__(
            load_config=load_config,
            config_file=config_file
        )
        self.timeout = timeout

    def init_config(self, data):

        if not data:
            return

        host = data.get("ftp_host").strip()
        if host.find(':') == -1:
            host += ':' + repr(self.default_port);

        _host, _port = host.split(":")
        self.__host = _host.strip()
        self.__port = _port.strip()
        self.__user = data.get("ftp_user").strip()
        self.__password = data.get("ftp_pass").strip()
        bp = data.get("backup_path").strip()
        if bp:
            self.backup_path = self.get_path(bp)
        else:
            self.backup_path = self.get_path(self.default_backup_path)

    def get_config(self):
        default_config = {
            "ftp_host": '',
            "ftp_user": '',
            "ftp_pass": '',
            "backup_path": self.default_backup_path
        }

        try:
            path = self.get_config_file()
            bak_config_path = self.get_bak_config_file()
            if not os.path.exists(path):
                if os.path.exists(bak_config_path):
                    path = bak_config_path
                else:
                    return default_config

            decrypt_key = public.readFile(self._a_pass)
            conf = public.readFile(path)
            if os.path.isfile(self._aes_status): conf = public.aes_decrypt(conf, decrypt_key)
            try:
                # 兼容上一个版本配置文件
                _c = json.loads(conf)
                conf = _c
            except:
                pass

            if isinstance(conf, str):
                try:
                    conf = public.aes_decrypt(conf, decrypt_key)
                    if not os.path.isfile(self._aes_status): public.writeFile(self._aes_status, 'True')
                except:
                    pass
                if conf.find(self.CONFIG_SEPARATOR) != -1:
                    # 兼容旧格式配置文件
                    # conf = ftp_host + '|' + \
                    #        ftp_user + '|' + \
                    #        ftp_pass + '|' + \
                    #        backup_path;
                    old_conf = conf.split(self.CONFIG_SEPARATOR)
                    if len(old_conf) < 4: old_conf.append(self.default_backup_path);
                    if not old_conf[3] or not old_conf[3].strip():
                        old_conf[3] = self.default_backup_path;

                    data = {
                        "ftp_host": old_conf[0],
                        "ftp_user": old_conf[1],
                        "ftp_pass": old_conf[2],
                        "backup_path": old_conf[3],
                    }
                    conf = data

            if not conf: return default_config
            if "backup_path" not in conf or not conf['backup_path']:
                conf['backup_path'] = self.get_path(self.default_backup_path)

            if not os.path.exists(bak_config_path):
                add_str = data['ftp_host'] + '|' + data['ftp_user'] + '|' + data['ftp_pass'] + '|' + data['backup_path']
                add_str = public.encrypt(add_str, decrypt_key)
                public.writeFile(bak_config_path, add_str)
            return conf
        except Exception:
            return default_config

    def get_decrypt_config(self):
        """
        @name 取加密配置信息
        """
        conf = self.get_config()
        if not conf['ftp_host'] or not conf['ftp_user'] or not conf['ftp_pass']: return conf
        conf['ftp_host'] = conf['ftp_host'][:4] + '*' * 10 + conf['ftp_host'][-4:]
        conf['ftp_user'] = conf['ftp_user'][:2] + '*' * 10 + conf['ftp_user'][-2:]
        conf['ftp_pass'] = conf['ftp_pass'][:2] + '*' * 10 + conf['ftp_pass'][-2:]
        return conf

    def authorize(self):
        try:
            if self.timeout is not None:
                ftp = ftplib.FTP(timeout=self.timeout)
            else:
                ftp = ftplib.FTP()
            debuglevel = 0
            if DEBUG:
                debuglevel = 3
            ftp.set_debuglevel(debuglevel)
            # ftp.set_pasv(True)
            ftp.connect(self.__host, int(self.__port))
            ftp.login(self.__user, self.__password)
            return ftp
        except Exception as e:
            raise OsError("无法连接FTP客户端，请检查配置参数是否正确。")

    def get_list(self, path="/"):
        ftp = self.authorize()
        path = self.get_path(path)
        ftp.cwd(path)
        mlsd = False
        try:
            files = ftp.nlst(path)
        except:
            try:
                files = list(ftp.mlsd())
                files = files[1:]
                mlsd = True
            except:
                raise RuntimeError("ftp服务器数据返回异常。")
        f_list = []
        dirs = []
        data = []
        default_time = '1971/01/01 01:01:01'
        for dt in files:
            if mlsd:
                dt = dt[0]
            else:
                if dt.find("/") >= 0:
                    dt = dt.split("/")[-1]
            tmp = {}
            tmp['name'] = dt
            if dt == '.' or dt == '..': continue;
            sfind = public.M('backup').where('name=?', (dt,)).field(
                'size,addtime').find();
            if not sfind:
                sfind = {}
                sfind['addtime'] = default_time
            time_format_list = ["%Y-%m-%d %H:%M:%S", '%Y/%m/%d %H:%M:%S']
            file_update_time = None
            for format in time_format_list:
                try:
                    file_update_time = time.strptime(sfind['addtime'], format)
                except:
                    continue
                else:
                    break
            if file_update_time is None:
                file_update_time = default_time

            tmp['time'] = int(time.mktime(file_update_time))
            try:
                tmp['size'] = ftp.size(dt);
                tmp['type'] = "File";
                tmp['download'] = self.generate_download_url(path + dt);
                f_list.append(tmp)
            except:
                tmp['size'] = 0;
                tmp['type'] = None;
                tmp['download'] = '';
                dirs.append(tmp);
        data = dirs + f_list

        mlist = {}
        mlist['path'] = path;
        mlist['list'] = data;
        return mlist;

    def generate_download_url(self, object_name):

        return 'ftp://' + \
            self.__user + ':' + \
            self.__password + '@' + \
            self.__host + ':' + \
            "/" + object_name;

    def delete_dir(self, dir_name, retries=2):

        try:
            ftp = self.authorize()
            ftp.rmd(dir_name);
            return True
        except ftplib.error_perm as e:
            raise RuntimeError(str(e) + ":" + dir_name)
        except Exception as e:
            print(e)

        # 重试
        if retries > 0:
            print("重新尝试删除文件{}...".format(dir_name))
            return self.delete_dir(
                dir_name,
                retries=retries - 1)
        raise RuntimeError("目录删除失败！");

    def delete_file_by_client(self, object_name):
        try:
            ftp = self.authorize()
            ftp.delete(object_name);
            return True;
        except Exception as ex:
            return False;

    def create_dir(self, dir_name):
        """创建远程目录

        :param dir_name: 目录名称
        :return:
        """
        try:
            dirnames = dir_name.split('/');
            ftp = self.authorize()
            # ftp.cwd(get.path);
            for dirname in dirnames:
                if not dirname or not dirname.strip(): continue;
                try:
                    flist = ftp.nlst()
                    if not dirname in flist: ftp.mkd(dirname);
                except:
                    # print("mlsd mode.")
                    try:
                        flist = list(ftp.mlsd())[1:]
                        for f in flist:
                            if dirname == f[0]:
                                break
                        else:
                            ftp.mkd(dirname)
                    except:
                        return False
                ftp.cwd(dirname)
            return True
        except:
            return False

    def close_client(self):
        """关闭客户端连接"""
        try:
            if self.auth:
                self.auth.close()
            self.auth = None
        except:
            pass

    def resumable_upload(self,
                         local_file_name,
                         object_name=None,
                         progress_callback=None,
                         progress_file_name=None,
                         retries=5,
                         *arg, **kwargs):
        """断点续传文件

        :param retries:  重试次数
        :param local_file_name:
        :param object_name:
        :param progress_callback: 回调函数
            该回调接收一个block_size大小的数据块
        :param progress_file_name:
        :param arg:
        :param kwargs:
        :return:
        """

        self.timeout = 60
        try:
            client = self.authorize()
            local_backup_path = public.M('config'). \
                where("id=?", (1,)).getField('backup_path')
            upload_tmp_dir = os.path.join(local_backup_path, ".upload_tmp")
            if not os.path.exists(upload_tmp_dir):
                os.mkdir(upload_tmp_dir)

            if not object_name:
                _temp = os.path.split(local_file_name)[1]
                object_name = self.backup_path + _temp
            print("|-正在上传文件到 {}".format(object_name))

            total_bytes = os.path.getsize(local_file_name)
            object_md5_name = public.md5(object_name)
            pg_file = os.path.join(upload_tmp_dir,
                                   object_md5_name + ".pl")

            block_size = BLOCK_SIZE
            if kwargs.get("block_size"):
                try:
                    block_size = float(kwargs.get("block_size"))
                except:
                    pass

            def calc_file_md5(file_name):
                import hashlib
                file_md5 = hashlib.md5()
                with open(file_name, "rb") as f:
                    by = f.read()
                file_md5.update(by)
                return file_md5.hexdigest()

            remote_file_size = None
            if not os.path.exists(pg_file):
                # import uuid
                # uid = str(uuid.uuid1())
                progress_info = {
                    "filename": local_file_name,
                    "total_bytes": total_bytes,
                    "uploaded_bytes": 0,
                }
                public.writeFile(pg_file, json.dumps(progress_info))
            else:
                progress_info = json.loads(public.readFile(pg_file))
                if total_bytes == progress_info.get("total_bytes"):
                    # 取远程文件大小
                    _max_loop = 10
                    while _max_loop > 0:
                        try:
                            time.sleep(1)
                            remote_file_size = client.size(object_name)
                            if remote_file_size > total_bytes:
                                remote_file_size = None
                            break
                        except Exception as e:
                            if DEBUG:
                                print(type(e))
                                print(e)
                            _max_loop -= 1
                else:
                    remote_file_size = None

            uploaded_bytes = 0 if remote_file_size is None else remote_file_size

            def ftp_progress_callback(buf):
                """回调进度更新和打印"""
                p_file = pg_file
                if not os.path.exists(p_file):
                    return
                info = json.loads(public.readFile(p_file))
                consumed_bytes = info.get("uploaded_bytes") + len(buf)
                info.update({"uploaded_bytes": consumed_bytes})
                public.writeFile(p_file, json.dumps(info))

                total = info.get("total_bytes")
                start_time = float(info.get("current_upload_time"))
                rate = int(100 * (float(consumed_bytes) / float(total)))
                now = time.time()
                diff = round((now - start_time) / 60, 2)
                calc_consumed_bytes = consumed_bytes - uploaded_bytes
                speed = round(calc_consumed_bytes / (diff * 60) / 1024 / 1024,
                              2) if diff > 0 else 0
                display_consumed_bytes = round(
                    consumed_bytes / 1024 / 1024, 2
                )
                display_total = round(
                    total / 1024 / 1024, 2
                )
                progress_text = "{0}% " \
                                "速度：{1} Mb/s " \
                                "耗时：{2} min " \
                                "已上传：{3} Mb " \
                                "总大小：{4} Mb" \
                                "{5}".format(
                    rate, speed, diff, display_consumed_bytes, display_total,
                    start_time
                )
                if consumed_bytes == total_bytes:
                    progress_text += "\n"
                if DEBUG:
                    print("\r" + progress_text)
                    sys.stdout.flush()

            dir_name = os.path.split(object_name)[0]
            if dir_name:
                self.create_dir(dir_name)
            if DEBUG:
                print("开始上传。。。")
            upload_start = time.time()

            try:
                if total_bytes > 1024 * 1024 * 1024:
                    with open(local_file_name, 'rb') as file_handler:
                        if remote_file_size is not None:
                            file_handler.seek(remote_file_size)
                        client.voidcmd("TYPE I")
                        datasock = ''
                        esize = ''
                        datasock, esize = client.ntransfercmd(
                            "STOR " + object_name,
                            remote_file_size)
                        while True:
                            buf = file_handler.read(block_size)
                            if not len(buf):
                                break
                            datasock.sendall(buf)
                            if progress_callback:
                                progress_callback(buf)
                            uploaded_bytes += len(buf)
                            if DEBUG:
                                print('\ruploading %.2f%%' % (
                                        float(
                                            uploaded_bytes) / total_bytes * 100))
                            if uploaded_bytes == total_bytes:
                                break
                        datasock.close()

                    if DEBUG:
                        print('close data handle')

                    try:
                        client.voidcmd('NOOP')
                    except Exception as e:
                        if DEBUG:
                            print("Send NOOP command error:")
                            print(e)
                    else:
                        if DEBUG:
                            print('keep alive cmd success')
                    client.voidresp()
                    if DEBUG:
                        print('No loop cmd')
                else:
                    # 小于1G文件直接上传
                    file_handler = open(local_file_name, "rb")
                    client.storbinary('STOR %s' % object_name,
                                      file_handler,
                                      blocksize=block_size)
                    file_handler.close()
            except EOFError as e:
                print("EOF ERROR({}): {}".format(public.format_date(), str(e)))
                # client.storbinary(
                #     'STOR %s' % object_name,
                #     file_handler,
                #     blocksize=block_size,
                #     callback=ftp_progress_callback,
                #     rest=remote_file_size,
                # )

            completed_file_size = None
            _max_loop = 10
            while _max_loop > 0:
                try:
                    time.sleep(1)
                    completed_file_size = client.size(object_name)
                    break
                except Exception as e:
                    if DEBUG:
                        print(type(e))
                        print(e)
                    _max_loop -= 1

            # 上传完成
            if completed_file_size == total_bytes:
                if DEBUG:
                    upload_completed = time.time()
                    upload_diff = upload_completed - upload_start
                    print("文件上传成功, 耗时: {}s。".format(upload_diff))
                if os.path.exists(pg_file):
                    os.remove(pg_file)
                return True
            else:
                if os.path.exists(pg_file):
                    os.remove(pg_file)
                raise OsError("文件上传后大小不一致！")
        except OsError as oe:
            raise
        except Exception as e:
            upload_diff = 0
            if upload_start:
                upload_completed = time.time()
                upload_diff = upload_completed - upload_start
            print("上传文件{}出现错误：{}，耗时:{}s。".format(local_file_name, str(e),
                                                           upload_diff))
        finally:
            self.close_client()

        if retries > 0:
            print("重试上传：")
            return self.resumable_upload(
                local_file_name,
                object_name=object_name,
                progress_callback=progress_callback,
                progress_file_name=progress_file_name,
                retries=retries - 1,
                *arg, **kwargs
            )
        raise RuntimeError("文件上传失败。")

    def convert_time(self, time_str):
        import datetime
        import time
        time_format = "%Y%m%d%H%M%S"
        mtime = datetime.datetime.strptime(time_str, time_format)
        mtime += datetime.timedelta(hours=8)
        ts = int((time.mktime(mtime.timetuple()) +
                  mtime.microsecond / 1000000.0))
        return ts


"""
=============btsftp===================
"""


class BTSFTPClient(FTPClient, object):
    _title = "SFTP"
    _name = "SSHFileTransferProtocol"
    __host = None
    __port = None
    __user = None
    __password = None
    default_port = 22
    config_file = "sftp.config.conf"

    def __init__(self, load_config=True, config_file=None):
        super(BTSFTPClient, self).__init__(
            load_config=load_config,
            config_file=config_file
        )

    def get_setup_path(self):
        """插件安装路径"""
        return os.path.join("plugin", "ftp")

    def get_decrypt_config(self):
        """
        @name 取加密配置信息
        """
        conf = self.get_config()
        if not conf['ftp_host'] or not conf['ftp_user'] or not conf['ftp_pass']: return conf
        conf['ftp_host'] = conf['ftp_host'][:4] + '*' * 10 + conf['ftp_host'][-4:]
        conf['ftp_user'] = conf['ftp_user'][:2] + '*' * 10 + conf['ftp_user'][-2:]
        conf['ftp_pass'] = conf['ftp_pass'][:2] + '*' * 10 + conf['ftp_pass'][-2:]
        return conf

    def get_config_file(self):
        """获取配置文件路径"""

        path = os.path.join(self.get_setup_path(), self.config_file);
        return path

    def init_config(self, data):

        if not data:
            return

        host = data.get("ftp_host").strip()
        if host.find(':') == -1:
            host += ':' + repr(self.default_port);

        _host, _port = host.split(":")
        self.__host = _host.strip()
        self.__port = _port.strip()
        self.__user = data.get("ftp_user").strip()
        self.__password = data.get("ftp_pass").strip()
        bp = data.get("backup_path").strip()
        if bp:
            self.backup_path = self.get_path(bp)
        else:
            self.backup_path = self.get_path(self.default_backup_path)

    def get_config(self):
        default_config = {
            "ftp_host": '',
            "ftp_user": '',
            "ftp_pass": '',
            "backup_path": self.default_backup_path
        }

        try:
            path = self.get_config_file()
            bak_config_path = self.get_bak_config_file()
            if not os.path.exists(path):
                if os.path.exists(bak_config_path):
                    path = bak_config_path
                else:
                    return default_config
            decrypt_key = public.readFile(self._a_pass)
            conf = public.readFile(path)
            try:
                # 兼容上一个版本配置文件
                _c = json.loads(conf)
                conf = _c
            except:
                pass

            if isinstance(conf, str):
                try:
                    conf = public.aes_decrypt(conf, decrypt_key)
                    if not os.path.isfile(self._aes_status): public.writeFile(self._aes_status, 'True')
                except:
                    return default_config
                if conf.find(self.CONFIG_SEPARATOR) != -1:
                    # 兼容旧格式配置文件
                    # conf = ftp_host + '|' + \
                    #        ftp_user + '|' + \
                    #        ftp_pass + '|' + \
                    #        backup_path;
                    old_conf = conf.split(self.CONFIG_SEPARATOR)
                    if len(old_conf) < 4: old_conf.append(self.default_backup_path);
                    if not old_conf[3] or not old_conf[3].strip():
                        old_conf[3] = self.default_backup_path;

                    data = {
                        "ftp_host": old_conf[0],
                        "ftp_user": old_conf[1],
                        "ftp_pass": old_conf[2],
                        "backup_path": old_conf[3],
                    }
                    conf = data

            if not conf: return default_config
            if "backup_path" not in conf or not conf['backup_path']:
                conf['backup_path'] = self.get_path(self.default_backup_path)

            if not os.path.exists(bak_config_path):
                add_str = data['ftp_host'] + '|' + data['ftp_user'] + '|' + data['ftp_pass'] + '|' + data['backup_path']
                add_str = public.encrypt(add_str, decrypt_key)
                public.writeFile(bak_config_path, add_str)
            return conf
        except Exception:
            return default_config

    def authorize(self):
        try:
            transport = paramiko.Transport((self.__host, int(self.__port)))
            transport.connect(username=self.__user, password=self.__password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            return sftp
        except Exception as e:
            raise OsError("无法连接到SFTP客户端: {}".format(str(e)))

    def get_list(self, path="/"):
        sftp = self.authorize()
        path = self.get_path(path)
        sftp.chdir(path)
        files = sftp.listdir_iter()
        data = []
        dirs = []
        others = []
        for lf in files:
            tmp = {}
            name = lf.filename
            tmp['name'] = name

            # 判断目录
            mode = oct(lf.st_mode)
            if mode[:-3] in ['0040', '0o40', '040'] or \
                    name in ['/tmp',
                             '/sbin',
                             '/bin',
                             '/lib',
                             '/lib64']:
                tmp["type"] = None
                dirs.append(tmp)
            else:
                tmp["size"] = lf.st_size
                tmp['download'] = self.generate_download_url(
                    path + name);
                tmp["type"] = "File"
                tmp['time'] = lf.st_mtime
                others.append(tmp)

        data = dirs + others
        mlist = {}
        mlist['path'] = path;
        mlist['list'] = data;
        return mlist;

    def generate_download_url(self, object_name):

        return 'ssh://' + \
            self.__user + ':' + \
            self.__password + '@' + \
            self.__host + ':' + \
            self.__port + \
            object_name;

    def delete_dir(self, dir_name, retries=2):

        try:
            sftp = self.authorize()
            sftp.rmdir(dir_name);
            return True
        except Exception as e:
            print(e)

        # 重试
        if retries > 0:
            print("重新尝试删除文件{}...".format(dir_name))
            return self.delete_dir(
                dir_name,
                retries=retries - 1)
        raise RuntimeError("目录删除失败！");

    def delete_file_by_client(self, object_name):
        try:
            sftp = self.authorize()
            sftp.remove(object_name);
            return True;
        except Exception as ex:
            return False;

    def create_dir(self, dir_name):
        """创建远程目录

        :param dir_name: 目录名称
        :return:
        """
        try:
            sftp = self.authorize()
            if dir_name[:1] == "/":
                sftp.chdir("/")
            dirnames = dir_name.split('/');
            for sub_dir in dirnames:
                if not sub_dir: continue
                try:
                    sftp.stat(sub_dir)
                except:
                    sftp.mkdir(sub_dir)
                sftp.chdir(sub_dir);
            return True
        except:
            return False

    def close_client(self):
        """关闭客户端连接"""
        try:
            if self.auth:
                self.auth.close()
            self.auth = None
        except:
            pass

    def resumable_upload(self,
                         local_file_name,
                         object_name=None,
                         progress_callback=None,
                         progress_file_name=None,
                         *arg, **kwargs):
        """SFTP上传文件

        :param local_file_name:
        :param object_name:
        :param progress_callback:
        :param progress_file_name:
        :param arg:
        :param kwargs:
        :return: True/False
        """
        '''TODO：支持断点续传, 加入重试机制'''

        client = self.authorize()
        try:
            print("|-正在上传文件到 {}".format(object_name))
            if not object_name:
                _temp = os.path.split(local_file_name)[1]
                object_name = self.backup_path + _temp

            upload_tmp_dir = os.path.split(object_name)[0]
            self.create_dir(upload_tmp_dir)
            client.put(local_file_name, object_name)
            return True
        except Exception as e:
            raise RuntimeError(str(e))
        finally:
            try:
                # 清除上个版本的文件上传了临时目录
                store_dir = "/.upload_tmp"
                client.rmdir(store_dir)
            except:
                pass
            self.close_client()

    def convert_time(self, time_str):
        import datetime
        import time
        time_format = "%Y%m%d%H%M%S"
        mtime = datetime.datetime.strptime(time_str, time_format)
        ts = int((time.mktime(mtime.timetuple()) +
                  mtime.microsecond / 1000000.0))
        return ts


"""
=============插件主文件Main===================
"""

PLUGIN_CONFIG = "settings.conf"


def get_config_path():
    _dir = os.path.abspath("plugin/ftp")
    _path = os.path.join(_dir, PLUGIN_CONFIG)
    return _path


def get_settings():
    settings = {}
    try:
        _path = get_config_path()
        if not os.path.exists(_path):
            if os.path.exists(get_bak_setting_file()):
                _path = get_bak_setting_file()
        if os.path.exists(_path):
            settings = json.loads(public.readFile(_path))
    except:
        settings = {}
    return settings


def get_bak_setting_file():
    return os.path.join("data", "ftp_settingsAS.conf")


def save_settings(settings):
    _settings = json.dumps(settings)
    public.writeFile(get_config_path(), _settings)
    public.writeFile(get_bak_setting_file(), _settings)


def get_client(use_sftp=None, load_config=True, timeout=None):
    if use_sftp is None:
        _settings = get_settings()
        if _settings:
            use_sftp = _settings.get("use_sftp")
        # if use_sftp is None:
        #     raise RuntimeError("Please configure first!")
    if use_sftp is None:
        use_sftp = False
    if use_sftp:
        _client = BTSFTPClient(load_config=load_config)
    else:
        _client = BTFTPClient(load_config=load_config, timeout=timeout)
    return _client


class ftp_main:
    __client = None
    __before_error_msg = "ERROR: 检测到有*号，输入信息为加密信息或者信息输入不正确！请检查[" \
                         "Host/用户名/密码]设置是否正确!"

    def __init__(self):
        try:
            self.get_lib()
        except:
            pass

    @property
    def client(self):
        if self.__client and not self.reload:
            return self.__client;

        self.__client = get_client()

        self.reload = False
        return self.__client

    def get_config(self, get):
        default_backup_path = "/bt_backup/"
        # default_config = [False, '', '', '', default_backup_path]
        default_config = {
            "use_sftp": False,
            "ftp_host": '',
            "ftp_user": '',
            "ftp_pass": '',
            "backup_path": default_backup_path,
        }
        _settings = get_settings()
        if _settings:
            use_sftp = _settings["use_sftp"]
            conf = self.client.get_decrypt_config()
            conf.update({"use_sftp": use_sftp})
        else:
            conf = default_config
        return conf

    def check_ip(self, address):
        """
        验证IP合法性

        """
        try:
            if address.find('.') == -1: return False
            iptmp = address.split('.')
            if len(iptmp) != 4: return False
            for ip in iptmp:
                if int(ip) > 255: return False
            return True
        except:
            return False

    def set_config(self, get):
        try:
            ftp_host = get.ftp_host.strip()
            ftp_user = get.ftp_user.strip()
            ftp_pass = get.ftp_pass.strip()
            backup_path = get.backup_path.strip()
            # 验证前端输入
            values = [ftp_host,
                      ftp_user,
                      ftp_pass]
            for v in values:
                if not v:
                    return public.returnMsg(False, '必填资料不能为空，请核实!');
            if ftp_host.find('*') != -1 or ftp_user.find('*') != -1 or ftp_pass.find(
                    '*') != -1: return public.returnMsg(False, self.__before_error_msg)
            tmp_host = ftp_host.split(':')[0]
            if not self.check_ip(tmp_host) and not public.is_domain(tmp_host): return public.returnMsg(False,
                                                                                                       '域名格式错误或IP地址格式错误，请核实!<br/>域名格式：x.x（根域名格式）<br/>域名示例：bt.cn<br/>IP地址+端口格式：x.x.x.x:x<br/>IP地址+端口示例：192.168.1.36:21');
            if not backup_path:
                backup_path = "/bt_backup"
            data = {
                "ftp_host": ftp_host,
                "ftp_user": ftp_user,
                "ftp_pass": ftp_pass,
                "backup_path": backup_path,
            }

            _use_sftp = get.use_sftp
            _use_sftp = True if _use_sftp.lower() == "true" else False
            _client = get_client(_use_sftp, load_config=False, timeout=10)
            _client.init_config(data)

            if _client.get_list():
                add_str = data['ftp_host'] + '|' + data['ftp_user'] + '|' + data['ftp_pass'] + '|' + data['backup_path']
                _client.set_config(add_str)
                settings = {"use_sftp": _use_sftp}
                save_settings(settings)
                return public.returnMsg(True, '设置成功!');
        except:
            import traceback
            public.print_log(traceback.format_exc())
        return public.returnMsg(False, '用户名或密码错误，请核实!');

    # 创建目录
    def create_dir(self, get):
        path = get.path + "/" + get.dirname;
        if self.client.create_dir(path):
            return public.returnMsg(True, '创建成功!');
        else:
            return public.returnMsg(False, "创建失败！")

    # 获取列表
    def get_list(self, get):
        try:
            return self.client.get_list(get.path)
        except:
            return public.returnMsg(False, "获取列表失败！")

    def delete_dir(self, get):
        try:
            path = get.path
            if path[-1] != "/":
                path += "/"
            dir_name = path + get.dir_name
            if self.client.delete_dir(dir_name):
                return public.returnMsg(True, '文件夹删除成功!')
            return public.returnMsg(False, '文件夹{}删除失败！'.format(dir_name))
        except Exception as e:
            return public.returnMsg(False, '文件夹删除失败!' + str(e))

    # 删除文件
    def delete_file(self, get):
        try:
            path = get.path
            filename = get.filename
            if path[-1] != "/":
                file_name = path + "/" + filename
            else:
                file_name = path + filename

            if self.client.delete_object(file_name):
                return public.returnMsg(True, '删除成功!')
            return public.returnMsg(False, '文件{}删除失败！'.format(file_name))
        except Exception as e:
            return public.returnMsg(False, '文件删除失败!')

    # 下载文件
    def download_file(self, filename):
        import re
        _result = re.search("([^_]+)_.+", filename)
        if _result:
            file_type = _result.group(1)
            reversal_prefix_dict = {
                "web": "site",
                "db": "database",
                "path": "path",
            }
            data_type = reversal_prefix_dict.get(file_type)
            object_name = self.client.build_object_name(data_type,
                                                        filename)
            if object_name[:1] != '/':
                object_name = "/" + object_name
            return self.client.generate_download_url(object_name)
        else:
            return filename

    def get_lib(self):
        import json
        info = {
            "name": "FTP存储空间",
            "type": "计划任务",
            "ps": "将网站或数据库打包备份到FTP或者SFTP存储空间.",
            "status": 'false',
            "opt": "ftp",
            "module": "paramiko==2.7.1",
            "script": "ftp",
            "help": "http://www.bt.cn/bbs",
            "USE_SFTP": "是否使用SFTP进行数据传输",
            "Host": "服务器地址",
            "用户名": "用户名",
            "密码": "登录密码",
            "backup_path": "备份保存路径, 默认是/bt_backup",
            "check": [
                "/usr/lib/python2.7/site-packages/paramiko/__init__.py",
                "/www/server/panel/pyenv/bin/python3.7/site-packages/paramiko"
                "/__init__.py"
            ]
        }
        lib = '/www/server/panel/data/libList.conf'
        lib_dic = json.loads(public.readFile(lib))
        used_name = ["FTP/SFTP存储空间"]
        update = False
        count = 0
        # 及时更新和避免重复的lib记录
        found = False
        for i in lib_dic:
            if info['name'] == i['name'] or i["name"] in used_name:
                found = True
                if count > 0:
                    lib_dic.remove(i)
                    update = True
                else:
                    count += 1
                    for key, value in info.items():
                        if key not in i.keys() or i[key] != info[key]:
                            update = True
                            i.update({key: value})
        if not found:
            update = True
            lib_dic.append(info)

        if update:
            public.writeFile(lib, json.dumps(lib_dic))
        return lib_dic


if __name__ == "__main__":
    import json

    import panelBackup

    client = get_client(use_sftp=None)

    new_version = True if hasattr(panelBackup, "_VERSION") \
                          and panelBackup._VERSION >= 1.2 else False
    data = None
    if not new_version:
        _type = sys.argv[1];
        if _type == 'site':
            if sys.argv[2].lower() == "all":
                client.backupSiteAll(sys.argv[3])
            else:
                client.backupSite(sys.argv[2], sys.argv[3])
            exit()
        elif _type == 'database':
            if sys.argv[2].lower() == "all":
                client.backupDatabaseAll(sys.argv[3])
            else:
                client.backupDatabase(sys.argv[2], sys.argv[3])
            exit()
        elif _type == 'path':
            client.backupPath(sys.argv[2], sys.argv[3])
        elif _type == 'upload':
            data = client.upload_file(sys.argv[2]);
        elif _type == 'download':
            data = client.generate_download_url(sys.argv[2]);
        elif _type == 'get':
            data = client.get_object_info(sys.argv[2]);
        elif _type == 'list':
            path = "/"
            if len(sys.argv) == 3:
                path = sys.argv[2]
            data = client.get_list(path);
        elif _type == 'delete_file':
            data = client.delete_file(sys.argv[2]);
        else:
            data = 'ERROR: 参数不正确!';

        if data:
            print(json.dumps(data))
    else:
        client.execute_by_comandline(sys.argv)
