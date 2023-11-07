#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   磁盘文件分析
#+--------------------------------------------------------------------
import sys, os, time

panelPath = '/www/server/panel'
os.chdir(panelPath)
sys.path.append("class/")
import json, os, time, re, public


class disk_analysis_main:
    _exe_cmd = 'ncdu'
    #扫描历史
    log_path = '{}/disk_analysis/scan/'.format(public.get_setup_path())

    conf_file = '{}/plugin/disk_analysis/config.json'.format(public.get_panel_path())

    remove_task_set = set()

    def __init__(self):
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

        if not os.path.isfile(self.conf_file):
            public.writeFile(self.conf_file, json.dumps({}))

        if os.getenv('BT_PANEL'):
            self._exe_cmd = '{}/plugin/disk_analysis/ncdu'.format(panelPath)

    def start_scan(self, get):
        """
        @name 扫描磁盘
        @param path 扫描目录
        """
        path_id = get.id
        path = get.path
        if not os.path.isdir(path):
            return public.returnMsg(False, '目录不存在.')

        if path != "/": path = str(path).rstrip("/")
        exclude_list = ["--exclude /proc/kcore"]
        if 'exclude' in get:
            exclude = get.exclude
            exclude_list = str(exclude).split(",")
            exclude_list = [f'--exclude {path}{url}' for url in exclude_list]

        result_file = '{}{}'.format(self.log_path, path_id)
        exec_shell = "{} {} -o {} {} ".format(self._exe_cmd, path, result_file, " ".join(exclude_list)).replace('\\','/').replace('//','/')
        import panelTask
        task_obj = panelTask.bt_task()
        task_id = task_obj.create_task('扫描目录文件大小', 0, exec_shell)

        self.set_scan_config(path_id, path)
        return {"status": True, "msg":'扫描任务已创建.', "task_id": task_id}

    # 删除任务
    def remove_task(self, get):
        """
        @name 删除扫描任务
        """
        task_info = public.M("task_list").where('id=? AND status=?', (get.id,"-1")).field('id,name,type,shell,other,status,exectime,endtime,addtime').find()
        public.M("task_list").where('id=?', (get.id,)).delete()
        if task_info:
            self.remove_task_set.add(get.id)
            public.ExecShell("kill -9 $(ps aux|grep 'task.py'|grep -v grep|awk '{print $2}')")
            public.ExecShell("kill -9 $(ps aux|grep '" + task_info['shell'] + "'|grep -v grep|awk '{print $2}')")

            public.ExecShell("/etc/init.d/bt start")
            return public.returnMsg(True, '任务已取消!')
        return public.returnMsg(True, '任务已完成!')

    def get_task_lists(self, get):
        """
        @name 获取任务状态
        """
        sql = public.M("task_list")
        data = sql.field('id,name,type,shell,other,status,exectime,endtime,addtime').where("(status=-1 OR status=0) AND id=?", get.task_id).find()

        task_status = not data
        is_remove = get.task_id in self.remove_task_set
        self.remove_task_set.discard(get.task_id)
        return {"is_remove": is_remove, "task_status": task_status}

    @classmethod
    def set_scan_config(cls, path_id, path):
        """
        @name 设置扫描配置
        """
        try:
            data = json.loads(public.readFile(cls.conf_file))
        except:
            data = {}

        data[path_id] = path
        public.writeFile(cls.conf_file, json.dumps(data))

    def get_scan_files(self, get):
        """
        @name 获取扫描结果
        @param id str 扫描id
        """
        result = []
        try:
            data = json.loads(public.readFile(self.conf_file))
        except:
            data = {}

        temp = []
        for s_file, path in data.items():
            filename = '{}/{}'.format(self.log_path, s_file)
            if not os.path.isfile(filename):
                temp.append(s_file)
                continue
            f_stat = os.stat(filename)
            f_info = {
                'id': s_file,
                'size': f_stat.st_size,
                'mtime': f_stat.st_mtime,
                'path': path
            }
            result.append(f_info)
        result.reverse()

        # 删除不存在的
        for s_file in temp:
            del data[s_file]
        public.writeFile(self.conf_file, json.dumps(data))
        return result

    def del_scan_files(self, get):
        """
        @name 删除指定扫描结果
        """
        try:
            data = json.loads(public.readFile(self.conf_file))
        except:
            data = {}
        ids = get.ids.split(',')
        for id in ids:
            filename = '{}/{}'.format(self.log_path, id)
            del data[id]
            if os.path.exists(filename):
                os.remove(filename)
        public.writeFile(self.conf_file, json.dumps(data))
        return public.returnMsg(True, '删除成功.')

    def get_scan_log(self, get):
        """
        @name 获取扫描日志
        @param id 扫描id
        """
        path = None
        id = get.id
        if 'path' in get:
            path = get.path.replace('\\', '/').replace('//', '/')
            if path != "/": path = str(path).rstrip("/")

        result_file = '{}/{}'.format(self.log_path, id)
        if not os.path.exists(result_file):
            return public.returnMsg(False, '扫描结果不存在.')

        if path and not os.path.isdir(path):
            return public.returnMsg(False, '{}不是一个有效目录.'.format(path))

        result = self.__get_log_data(result_file, path)
        if len(result) > 0:
            result = result[0]
        else:
            result = {}
        return result

    @classmethod
    def __get_log_data(cls, log_file, path):
        """
        @name 获取扫描日志
        @param log_file 日志文件
        """
        result = []
        data = public.readFile(log_file)
        data = json.loads(data)
        for info in data:
            if isinstance(info, list):
                root_path = info[0]["name"]
                if path is not None:
                    info = cls.__get_sub_data(info[1:], root_path, path)
                    if info is None: continue
                    info[0]["fullpath"] = path
                else:
                    info[0]["fullpath"] = root_path
                dir_info = cls.__get_dirs_info(info)
                result.append(dir_info)

        return result

    @classmethod
    def __get_sub_data(cls, data, root_path, sub_path):
        """
        @name 获取子目录数据
        @param id int 记录id
        @param path string 目录
        """
        for val in data:
            if isinstance(val, list):
                sfile = f"{root_path}/{val[0]['name']}".replace('\\', '/').replace('//', '/')
                if sfile.lower() == sub_path.lower():
                    return val
                elif len(val) > 1:
                    val =  cls.__get_sub_data(val[1:], sfile, sub_path)
                    if val is not None:
                        return val
        else:
            return None

    @classmethod
    def __get_dirs_info(cls, data):
        """
        @name 获取目录详细信息
        @param data 目录信息
        @param result 结果
        """
        dir_info = data[0]
        dir_info["type"] = 1
        dir_info["asize"] = 0
        dir_info["dsize"] = 0
        dir_info["dirs"] = 0
        dir_info["files"] = 0
        dir_info["dir_num"] = 0
        dir_info["file_num"] = 0
        dir_info["total_asize"] = 0
        dir_info["total_dsize"] = 0
        dir_info['list'] = []
        cls.__get_stat(dir_info["fullpath"], dir_info)

        for info in data[1:]:
            if isinstance(info, list): # 目录
                dir_info["dirs"] += 1
                dir_info["dir_num"] += 1
                cls.__get_dirs_size(info)
                info = info[0]
                dir_info["dir_num"] += info["dir_num"]
                dir_info["file_num"] += info["file_num"]
                dir_info["total_asize"] += info["total_asize"]
                dir_info["total_dsize"] += info["total_dsize"]
            else:
                if info.get("excluded") == "pattern":
                    continue
                dir_info["files"] += 1
                dir_info["file_num"] += 1
                if info.get("asize") is None: info["asize"] = 0
                if info.get("dsize") is None: info["dsize"] = 0
                info["type"] = 0
                info["total_asize"] = info["asize"]
                info["total_dsize"] = info["dsize"]
                dir_info["total_asize"] += info["asize"]
                dir_info["total_dsize"] += info["dsize"]

            path = os.path.join(dir_info["fullpath"], info["name"])
            cls.__get_stat(path, info)
            dir_info['list'].append(info)
        dir_info['list'] = sorted(dir_info['list'],
                                  key=lambda x: x['total_asize'],
                                  reverse=True)
        total_max = dir_info["total_asize"]
        for info in dir_info["list"]:
            if total_max == 0:
                info["percent"] = 0
            else:
                info["percent"] = round(info['total_asize'] / total_max * 100, 2)
        return dir_info

    @classmethod
    def __get_dirs_size(cls, dirs_list):
        """
        @param info 目录信息
        @param result 结果
        """
        dir_info = dirs_list[0]
        dir_info["type"] = 1
        dir_info["asize"] = dir_info.get("asize",0)
        dir_info["dsize"] = dir_info.get("dsize",0)
        dir_info["dirs"] = 0
        dir_info["files"] = 0
        dir_info["dir_num"] = 0
        dir_info["file_num"] = 0
        dir_info["total_asize"] = dir_info.get("asize",0)
        dir_info["total_dsize"] = dir_info.get("dsize",0)
        for info in dirs_list[1:]:
            if isinstance(info, list):  # 目录
                dir_info["dirs"] += 1
                dir_info["dir_num"] += 1
                cls.__get_dirs_size(info)
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

    @classmethod
    def __get_stat(cls, path, info):
        if not os.path.exists(path):
            info["accept"] = None
            info["user"] = None
            info["mtime"] = "--"
            info["ps"] = None
            return
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
        info["ps"] = cls.get_file_ps(path)

    @classmethod
    def get_file_ps(cls, filename):
        '''
            @name 获取文件或目录备注
            @author hwliang<2020-10-22>
            @param filename<string> 文件或目录全路径
            @return string
        '''

        ps_path = public.get_panel_path() + '/data/files_ps'
        f_key1 = '/'.join((ps_path, public.md5(filename)))
        if os.path.exists(f_key1):
            return public.readFile(f_key1)

        f_key2 = '/'.join((ps_path, public.md5(os.path.basename(filename))))
        if os.path.exists(f_key2):
            return public.readFile(f_key2)

        pss = {
            '/www/server/data': '此为MySQL数据库默认数据目录，请勿删除!',
            '/www/server/mysql': 'MySQL程序目录',
            '/www/server/redis': 'Redis程序目录',
            '/www/server/mongodb': 'MongoDB程序目录',
            '/www/server/nvm': 'PM2/NVM/NPM程序目录',
            '/www/server/pass': '网站BasicAuth认证密码存储目录',
            '/www/server/speed': '网站加速数据目录',
            '/www/server/docker': 'Docker插件程序与数据目录',
            '/www/server/total': '网站监控报表数据目录',
            '/www/server/btwaf': 'WAF防火墙数据目录',
            '/www/server/pure-ftpd': 'ftp程序目录',
            '/www/server/phpmyadmin': 'phpMyAdmin程序目录',
            '/www/server/rar': 'rar扩展库目录，删除后将失去对RAR压缩文件的支持',
            '/www/server/stop': '网站停用页面目录,请勿删除!',
            '/www/server/nginx': 'Nginx程序目录',
            '/www/server/apache': 'Apache程序目录',
            '/www/server/cron': '计划任务脚本与日志目录',
            '/www/server/php': 'PHP目录，所有PHP版本的解释器都在此目录下',
            '/www/server/tomcat': 'Tomcat程序目录',
            '/www/php_session': 'PHP-SESSION隔离目录',
            '/proc': '系统进程目录',
            '/dev': '系统设备目录',
            '/sys': '系统调用目录',
            '/tmp': '系统临时文件目录',
            '/var/log': '系统日志目录',
            '/var/run': '系统运行日志目录',
            '/var/spool': '系统队列目录',
            '/var/lock': '系统锁定目录',
            '/var/mail': '系统邮件目录',
            '/mnt': '系统挂载目录',
            '/media': '系统多媒体目录',
            '/dev/shm': '系统共享内存目录',
            '/lib': '系统动态库目录',
            '/lib64': '系统动态库目录',
            '/lib32': '系统动态库目录',
            '/usr/lib': '系统动态库目录',
            '/usr/lib64': '系统动态库目录',
            '/usr/local/lib': '系统动态库目录',
            '/usr/local/lib64': '系统动态库目录',
            '/usr/local/libexec': '系统动态库目录',
            '/usr/local/sbin': '系统脚本目录',
            '/usr/local/bin': '系统脚本目录'

        }
        if filename in pss:  return "PS：" + pss[filename]
        return None