#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: cjxin <cjxin@bt.cn>
# +-------------------------------------------------------------------

import os, sys,datetime,shutil,re
from unittest import result
panelPath = os.getenv('BT_PANEL')
if not panelPath: panelPath = '/www/server/panel'
os.chdir(panelPath)
sys.path.insert(0,panelPath + "/class/")
import public,json,time,random,base64

class oneav_main:


    log_file = '/var/log/oneav/oneav.warn'
    service_file = '/opt/threatbook/OneAV/oneav/oneavd'
    conf_file = '/opt/threatbook/OneAV/OneAV/conf/scan_strategy.json'

    soft_path = '/opt/threatbook/OneAV/oneav'
    plugin_path = '{}/plugin/oneav'.format(panelPath)
    scan_file = '{}/data/config.json'.format(plugin_path)

    def __init__(self):

        log_file = '{}/data/logs'.format(self.plugin_path)
        if not os.path.exists(log_file):  os.makedirs(log_file,384)


    def get_config(self,get):
        '''
        @name 获取配置信息
        '''
        if os.path.exists(self.conf_file):
            conf = json.loads(public.readFile(self.conf_file))


            conf['oneav']['detect_dir'].reverse()
            return conf
        return public.returnMsg(False,'配置文件不存在')

    def set_config(self,get):
        """
        @name 修改配置文件
        """
        if not os.path.exists(self.conf_file):
            return public.returnMsg(False,'配置文件不存在')
        conf = json.loads(public.readFile(self.conf_file))

        layer = int(get.layer)
        hours = int(get.hours)
        minute = int(get.minute)

        conf['oneav']['layer'] = layer
        conf['oneav']['cycle'] = '{} {} * * *'.format(minute,hours)

        public.writeFile(self.conf_file,json.dumps(conf))

        self.restart_services(get)
        return public.returnMsg(True,'设置成功')

    def add_scan_path(self,get):
        """
        @name 添加扫描路径
        @param path 路径
        """
        paths = json.loads(get.paths)

        if not os.path.exists(self.conf_file):
            return public.returnMsg(False,'配置文件不存在')

        conf = json.loads(public.readFile(self.conf_file))
        res = {'errs':{},'sucs':{}} # 记录成功和失败的路径

        dirs = conf['oneav']['detect_dir']
        for path in paths:

            if not os.path.exists(path):
                res['errs'][path] = '路径不存在'
                continue

            if path in dirs:
                res['errs'][path] = '路径已添加至扫描列表'
            else:
                res['sucs']['path'] = '添加成功'
                dirs.append(path)
        conf['oneav']['detect_dir'] = dirs
        public.writeFile(self.conf_file,json.dumps(conf))

        self.restart_services(get)
        return res


    def del_scan_path(self,get):
        """
        @name 删除扫描路径
        @param paths 路径
        """
        paths = json.loads(get.paths)

        if not os.path.exists(self.conf_file):
            return public.returnMsg(False,'配置文件不存在')

        conf = json.loads(public.readFile(self.conf_file))
        res = {'errs':{},'sucs':{}} # 记录成功和失败的路径

        dirs = conf['oneav']['detect_dir']
        for path in paths:
            if path in dirs:
                dirs.remove(path)
                res['sucs'][path] = '删除成功.'
            else:
                res['errs'][path] = '路径不存在'

        conf['oneav']['detect_dir'] = dirs
        public.writeFile(self.conf_file,json.dumps(conf))

        self.restart_services(get)
        return res


    def get_status(self,get):
        '''
        @name 获取扫描状态
        '''
        if os.path.exists(self.conf_file):
            conf = json.loads(public.readFile(self.conf_file))
            return conf['scan_strategy']['scan_status']
        return public.returnMsg(False,'配置文件不存在')


    def get_service_status(self,get):
        """
        @name 获取服务状态
        """
        if public.is_process_exists_by_cmdline(self.service_file):
            return public.returnMsg(True,'服务已启动')
        return public.returnMsg(False,'服务未启动')

    def set_service_status(self,get):
        """
        @name 设置服务状态
        @param status 服务状态 enable，disable，start，stop
        """
        status = get.status
        if status in ['disable','stop']:

            public.ExecShell('oneav_{}'.format(status))
            if self.get_service_status(get)['status']:
                return public.returnMsg(False,'操作失败，请稍后重试.')
            return public.returnMsg(True,'设置成功')
        else:

            if status in ['restart','reload']:
                self.restart_services(get)
            else:
                public.ExecShell('oneav_{}'.format(status))
            if not self.get_service_status(get)['status']:
                return public.returnMsg(False,'操作失败，请稍后重试.')
            return public.returnMsg(True,'设置成功')


    def restart_services(self,get):
        """
        @name 重启服务
        """
        public.ExecShell('oneav_stop')
        public.ExecShell('oneav_start')
        return public.returnMsg(True,'重启成功')

    def start_scan(self,get):
        """
        @name 开始手动扫描
        @param paths 扫描路径 [path1,path2]
        """
        paths = []
        try:
            paths = json.loads(get.paths)
        except:pass

        if len(paths) == 0:
            return public.returnMsg(False,'请选择扫描路径')

        scan_id = int(time.time())
        log_file = '{}/data/logs/{}.log'.format(self.plugin_path,scan_id)

        info = {
            'scan_id':scan_id,
            'time':scan_id,
            'paths':paths,
            'logs' : log_file
        }

        shell = 'cd {} && ./oneav --scan {} --log {}'.format(self.soft_path,' '.join(paths),log_file)

        public.print_log('开始手动扫描:{}'.format(shell))

        import panelTask
        task_obj = panelTask.bt_task()

        task_obj.create_task('微步木马扫描', 0, shell)
        public.set_module_logs('oneav', 'start_scan', 1)
        public.WriteLog('微步木马扫描', '手动扫描：{}'.format(' '.join(paths)))

        self.__set_scan_history(info)
        res = public.returnMsg(True, '添加扫描任务成功')
        res['path'] = log_file
        return res

    def get_scan_history(self,get):
        """
        @name 获取扫描历史
        """
        result = []
        data = self.__get_scan_history()
        for key in data:
            data[key]['size'] = 0
            try:
                data[key]['size'] = os.path.getsize(data[key]['logs'])
            except:pass
            result.append(data[key])

        result = sorted(result,key=lambda x:x['time'],reverse=True)
        return result

    def del_scan_history(self,get):
        """
        @name 删除扫描历史
        """
        scan_id = get.scan_id

        if not os.path.exists(self.conf_file):
            return public.returnMsg(False,'配置文件不存在')
        data = self.__get_scan_history()
        if scan_id in data:
            del data[scan_id]
            public.writeFile(self.scan_file,json.dumps(data))
        return public.returnMsg(True,'删除成功')


    def __get_scan_history(self):
        """
        @name 获取扫描历史
        """
        result = {}
        try:
            result = json.loads(public.readFile(self.scan_file))
        except:pass
        return result

    def __set_scan_history(self,data):
        """
        @name 设置扫描历史
        """
        result = self.__get_scan_history()
        result[data['scan_id']] = data

        public.writeFile(self.scan_file,json.dumps(result))
        return public.returnMsg(True,'设置成功')



    def get_scan_log(self,get):
        """
        @name 获取手动扫描日志
        """

        p = 1
        count = 15
        if 'count' in get: count = int(get.count)
        if 'p' in get: p = int(get.p)

        res = []
        scan_id = get.scan_id
        log_file = '{}/data/logs/{}.log'.format(self.plugin_path,scan_id)

        if os.path.exists(log_file):
            res = self.__get_num_logs(log_file,count,p)
        res = sorted(res,key=lambda x:x['time'],reverse=True)
        return res


    def get_logs(self,get):
        '''
        @name 获取日志
        '''

        p = 1
        count = 15
        if 'count' in get: count = int(get.count)
        if 'p' in get: p = int(get.p)

        res = []
        if os.path.exists(self.log_file):
            res = self.__get_num_logs(self.log_file,count,p)

        res = sorted(res,key=lambda x:x['time'],reverse=True)
        return res



    def __get_num_logs(self,path,count,p):
        """
        @name 获取日志
        """
        data = []
        limit = 1000
        min_line = (p - 1) * count
        s_page = int(str((count * p) / limit ).split('.')[0]) + 1
        start_line = (s_page - 1) * limit

        res = public.GetNumLines(path,1000,s_page).split('\n')
        res.reverse()

        for _line in res:
            if len(data) >= count:
                break

            if start_line >= min_line:
                try:
                    info = json.loads(_line)
                    data.append(info)
                except:pass
            start_line += 1
        return data




