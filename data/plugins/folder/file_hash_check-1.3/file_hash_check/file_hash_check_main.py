#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔文件监控
#+--------------------------------------------------------------------
import sys
sys.path.append('/www/server/panel/class')
import os,pyinotify,hashlib,public,json,hashlib,shutil,time,pwd

class file_hash_check_main:
    _PLUGIN_PATH = '/www/server/panel/plugin/file_hash_check/'
    _LIST_FILE = _PLUGIN_PATH + '/check_list.json'
    _history_path = '/www/backup/file_history/'
    access_defs = ['start']

    def __init__(self):
        if not os.path.exists(self._history_path):
            os.makedirs(self._history_path,384)

    def start(self):
        run()

    def save_config(self,data):
        '''
            @name 保存配置
            @author hwliang<2021-10-21>
            @param data<dict_obj>{
                data:<list> 校验列表
            }
            @return void
        '''
        public.writeFile(self._LIST_FILE,json.dumps(data))
        self.restart_service(None)


    def get_check_logs(self,get):
        '''
            @name 获取校验日志
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
            }
            @return list
        '''
        index = get.index
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        log_path = self._PLUGIN_PATH + 'logs/' + index + '/logs.json'
        if not os.path.exists(log_path): return []
        data = public.readFile(log_path)
        result = []
        for i in data.split('\n'):
            if not i: continue
            result.insert(0,json.loads(i))
        return result

    def get_logs(self,args):
        #处理前端传过来的参数
        if not 'p' in args: args.p = 1
        if not 'rows' in args: args.rows = 12
        if not 'callback' in args: args.callback = ''
        args.p = int(args.p)
        args.rows = int(args.rows)
        self._log_name = '文件监控'
        #取日志总行数
        count = public.M('logs').where('type=?',(self._log_name,)).count()

        #获取分页数据
        page_data = public.get_page(count,args.p,args.rows,args.callback)

        #获取当前页的数据列表
        log_list = public.M('logs').where('type=?',(self._log_name,)).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).field('id,type,log,addtime').select()

        #返回数据到前端
        return {'data': log_list,'page':page_data['page'] }

    def resync_data(self,get):
        '''
            @name 重新同步数据
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
            }
            @return dict
        '''
        index = get.index
        check_list = self.get_check_list()
        path = None
        check_info = None
        for i in check_list:
            if i['index'] == index:
                path = i['path']
                check_info = i

        p = MyEventHandler()
        p.list_DIR(path,check_info,force=True)
        return public.returnMsg(True,'同步成功!')

    def get_check_list(self,get = None):
        '''
            @name 获取校验列表
            @author hwliang<2021-10-21>
            @param get
            @return list
        '''
        if not os.path.exists(self._LIST_FILE):
            public.writeFile(self._LIST_FILE,'[]')
            return []
        data = json.loads(public.readFile(self._LIST_FILE))
        if get:
            for i in data:
                i['total'] = self.get_check_total(i['index'])
        return data

    def get_check_total(self,index):
        '''
            @name 获取监控目录统计信息
            @author hwliang<2021-10-21>
            @param index<string> 目录索引
            @return int
        '''
        total_file = self._PLUGIN_PATH + 'logs/' + index + '/total.json'
        if not os.path.exists(total_file): return {"total": 0, "delete": 0, "create": 0, "modify": 0, "move": 0,'anti_virus':0,'backup':0}
        data = public.readFile(total_file)
        result = json.loads(data)
        if not 'anti_virus' in result:
            result['anti_virus'] = 0
        if not 'backup' in result:
            result['backup'] = 0
        return result



    def create_check_path(self,get = None):
        '''
            @name 创建监控目录
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                path:<string> 监控目录
                index:<string> 目录索引
                ps:<string> 备注
            }
            @return dict
        '''
        path = get.path.strip()
        if not os.path.exists(path): return public.returnMsg(False,'指定目录不存在!')
        if self.exists_path(path): return public.returnMsg(False,'指定目录已经添加过!')
        if self.exists_index(get.index): return public.returnMsg(False,'指定目录索引已经存在!')
        check_list = self.get_check_list()
        check_info = {
            "index":get.index,
            "open":True,
            "path":path,
            "dir": os.path.isdir(path),
            "exclude_ext":["log","gz","sql","zip","rar","7z","iso","bak","tmp","swp","backup","back","pid","sock"],
            "exclude_name":["temp","tmp","log","logs","cache","runtime"],
            "auto_recovery":False, # 自动恢复
            "auto_backup":True,    # 自动备份
            "backup_num": 30,       # 备份数量
            "auto_anti_virus":True,  # 是否开启自动木马扫描
            "max_size":1048576,
            "allow_create":True,
            "allow_delete":True,
            "allow_move":True,
            "allow_modify":True,
            "ps":get.ps
        }

        check_list.append(check_info)
        self.save_config(check_list)
        public.WriteLog('文件监控','添加监控目录: {}'.format(path))
        return public.returnMsg(True,'添加成功!')

    def remove_check_path(self,get = None):
        '''
            @name 删除监控目录
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
            }
            @return dict
        '''
        index = get.index
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        path = None
        for i in range(len(check_list)):
            if check_list[i]['index'] == index:
                path = check_list[i]['path']
                check_list.pop(i)
                backup_path = self._PLUGIN_PATH + '/'+index
                if os.path.exists(backup_path):
                    public.ExecShell("rm -rf {}".format(backup_path))
                break
        self.save_config(check_list)
        public.WriteLog('文件监控','删除监控目录: {}'.format(path))
        return public.returnMsg(True,'删除成功!')

    def set_check_status(self,get):
        '''
            @name 设置字段状态
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
                key:<string> 字段名 允许： open/auto_recovery/allow_create/allow_delete/allow_move/allow_modify
            }
            @return dict
        '''
        key = get.key
        index = get.index
        if not key in ['open','auto_recovery','auto_backup','auto_anti_virus','allow_create','allow_delete','allow_move','allow_modify']:
            return public.returnMsg(False,'不支持的字段!')
        path = None
        status = None
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                path = i['path']
                i[key] = not i[key]
                status = i[key]
                break
        self.save_config(check_list)
        if key == 'open':
            if status:
                public.WriteLog('文件监控','开启监控目录: {}'.format(path))
            else:
                public.WriteLog('文件监控','关闭监控目录: {}'.format(path))
        else:
            public.WriteLog('文件监控','设置监控目录[{}]的字段[{}]状态: {}'.format(path,key,status))
        return public.returnMsg(True,'设置成功!')


    def set_backup_num(self,get):
        '''
            @name 设置保留的最大备份数量
            @author hwliang
            @param index<string> 目录索引
            @param num<int> 保留的最大备份数量
            @return dict
        '''
        index = get.index
        num = int(get.num)
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                i['backup_num'] = num
                break
        self.save_config(check_list)
        public.WriteLog('文件监控','设置监控目录[{}]的最大备份数量: {}'.format(index,num))
        return public.returnMsg(True,'设置成功!')


    def set_check_ps(self,get):
        '''
            @name 设置备注
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
                ps:<string> 备注
            }
            @return dict
        '''
        index = get.index
        ps = get.ps
        path = None
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                path = i['path']
                i['ps'] = ps
                break
        self.save_config(check_list)
        public.WriteLog('文件监控','设置监控目录[{}]的备注: {}'.format(path,ps))
        return public.returnMsg(True,'设置成功!')

    def get_exclude_ext(self,get):
        '''
            @name 获取排除的文件类型
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
            }
            @return list
        '''
        index = get.index
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                return i['exclude_ext']
        return []

    def add_exclude_ext(self,get):
        '''
            @name 添加排除的文件类型
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
                ext:<string> 文件类型
            }
            @return dict
        '''
        index = get.index
        ext = get.ext.strip('.')
        path = None
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                path = i['path']
                if ext in i['exclude_ext']:
                    return public.returnMsg(False,'已存在!')
                i['exclude_ext'].append(ext)
                break
        self.save_config(check_list)
        public.WriteLog('文件监控','监控目录[{}],添加排除的文件类型: {}'.format(path,ext))
        return public.returnMsg(True,'添加成功!')


    def del_exclude_ext(self,get):
        '''
            @name 删除排除的文件类型
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
                ext:<string> 文件类型
            }
            @return dict
        '''
        index = get.index
        ext = get.ext
        path = None
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                path = i['path']
                if not ext in i['exclude_ext']:
                    return public.returnMsg(False,'不存在!')
                i['exclude_ext'].remove(ext)
                break
        self.save_config(check_list)
        public.WriteLog('文件监控','监控目录[{}],删除排除的文件类型: {}'.format(path,ext))
        return public.returnMsg(True,'删除成功!')


    def get_exclude_name(self,get):
        '''
            @name 获取排除的文件名
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
            }
            @return list
        '''
        index = get.index
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                return i['exclude_name']
        return []

    def add_exclude_name(self,get):
        '''
            @name 添加排除的文件名
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
                fname:<string> 文件名
            }
            @return dict
        '''
        index = get.index
        name = get.fname.lower().strip()
        path = None
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                path = i['path']
                if name in i['exclude_name']:
                    return public.returnMsg(False,'已存在!')
                i['exclude_name'].append(name)
                break
        self.save_config(check_list)
        public.WriteLog('文件监控','监控目录[{}],添加排除的文件名: {}'.format(path,name))
        return public.returnMsg(True,'添加成功!')

    def del_exclude_name(self,get):
        '''
            @name 删除排除的文件名
            @author hwliang<2021-10-21>
            @param get<dict_obj>{
                index:<string> 目录索引
                fname:<string> 文件名
            }
            @return dict
        '''
        index = get.index
        name = get.fname
        path = None
        if not self.exists_index(index): return public.returnMsg(False,'指定目录索引不存在!')
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                path = i['path']
                if not name in i['exclude_name']:
                    return public.returnMsg(False,'不存在!')
                i['exclude_name'].remove(name)
                break
        self.save_config(check_list)
        public.WriteLog('文件监控','监控目录[{}],删除排除的文件名: {}'.format(path,name))
        return public.returnMsg(True,'删除成功!')


    def get_service_status(self,get = None):
        '''
            @name 获取服务状态
            @author hwliang<2021-10-21>
            @return bool
        '''

        if public.ExecShell("ps aux |grep bt_hashcheck|grep -v grep")[0]:
            return True
        return False

    def start_service(self,get):
        '''
            @name 启动服务
            @author hwliang<2021-10-21>
            @return dict
        '''
        if self.get_service_status(): return public.returnMsg(False,'服务已启动!')
        init_file = '/etc/init.d/bt_hashcheck'
        public.ExecShell("{} start".format(init_file))
        if self.get_service_status():
            public.WriteLog('文件监控','启动服务')
            return public.returnMsg(True,'启动成功!')
        return public.returnMsg(False,'启动失败!')

    def stop_service(self,get):
        '''
            @name 停止服务
            @author hwliang<2021-10-21>
            @return dict
        '''
        if not self.get_service_status(): return public.returnMsg(False,'服务已停止!')
        init_file = '/etc/init.d/bt_hashcheck'
        public.ExecShell("{} stop".format(init_file))
        if not self.get_service_status():
            public.WriteLog('文件监控','停止服务')
            return public.returnMsg(True,'停止成功!')
        return public.returnMsg(False,'停止失败!')

    def restart_service(self,get):
        '''
            @name 重启服务
            @author hwliang<2021-10-21>
            @return dict
        '''
        if not self.get_service_status(): return self.start_service(get)
        init_file = '/etc/init.d/bt_hashcheck'
        public.ExecShell("{} restart".format(init_file))
        if self.get_service_status():
            public.WriteLog('文件监控','重启服务')
            return public.returnMsg(True,'重启成功!')
        return public.returnMsg(False,'重启失败!')


    def exists_path(self,path):
        '''
            @name 判断目录是否已经添加过
            @author hwliang<2021-10-21>
            @param path
            @return bool
        '''
        check_list = self.get_check_list()
        for i in check_list:
            if i['path'] == path:
                return True
        return False

    def exists_index(self,index):
        '''
            @name 判断目录索引是否已经添加过
            @author hwliang<2021-10-21>
            @param path
            @return bool
        '''
        check_list = self.get_check_list()
        for i in check_list:
            if i['index'] == index:
                return True
        return False


        # 取历史副本
    def get_history(self, filename):
        try:
            his_path = self._history_path
            save_path = (his_path + filename).replace('//', '/')
            if not os.path.exists(save_path):
                return []
            return sorted(os.listdir(save_path))
        except:
            return []

    # 读取指定历史副本
    def read_history(self, args):
        save_path = (self._history_path + args.filename).replace('//', '/')
        args.path = save_path + '/' + args.history
        import files
        return files.files().GetFileBody(args)

    # 恢复指定历史副本
    def re_history(self, args):
        save_path = (self._history_path + args.filename).replace('//', '/')
        args.path = save_path + '/' + args.history
        if not os.path.exists(args.path):
            return public.returnMsg(False, '指定历史副本不存在!')
        import shutil
        import files
        shutil.copyfile(args.path, args.filename)
        return files.files().GetFileBody(args)




class MyEventHandler(pyinotify.ProcessEvent):
    _PLUGIN_PATH = "/www/server/panel/plugin/file_hash_check"
    _LIST_FILE = _PLUGIN_PATH + '/check_list.json'
    _LIST_DATA = None
    _DONE_FILE = None
    _history_path = '/www/backup/file_history/'
    _last_time = 0
    _last_files_time = {}
    _is_history_num = 0
    _is_anti_virus_num = 0

    def process_IN_CREATE(self, event):
        _info = self.get_SITE_CONFIG(event.pathname)
        if not _info: return False
        if not _info['allow_create']: return False
        if not self.check_FILE(event,_info,True): return False
        self._DONE_FILE = event.pathname
        if event.dir:
            return False
            #if os.path.exists(event.pathname): os.removedirs(event.pathname)
        else:
            if _info['auto_recovery']:
                if os.path.exists(event.pathname): os.remove(event.pathname)
        self.write_LOG('create',_info['index'],event.pathname,_info)

    def process_IN_DELETE(self, event):
        _info = self.get_SITE_CONFIG(event.pathname)
        if not _info: return False
        if not _info['allow_delete']: return False
        if not self.check_FILE(event,_info): return False
        self.renew_FILE(event.pathname,_info)
        self.write_LOG('delete',_info['index'],event.pathname,_info)

    def process_IN_MODIFY(self, event):
        _info = self.get_SITE_CONFIG(event.pathname)
        if not _info: return False
        if not _info['allow_modify']: return False
        if not self.check_FILE(event,_info): return False
        self.renew_FILE(event.pathname,_info)
        self.write_LOG('modify',_info['index'],event.pathname,_info)

    def process_IN_MOVED_TO(self,event):
        _info = self.get_SITE_CONFIG(event.pathname)
        if not _info: return False
        if not _info['allow_move']: return False
        if not self.check_FILE(event,_info): return False
        if hasattr(event,'src_pathname'):
            self.renew_FILE(event.src_pathname,_info)
        else:
            event.src_pathname = "null"
        if not self.renew_FILE(event.pathname,_info):
            backupPath = self._PLUGIN_PATH + '/backup/' + _info['index'] + '/' + event.pathname
            if os.path.exists(backupPath):
                if _info['auto_recovery']:
                    shutil.copyfile(backupPath,event.pathname)

        self.write_LOG('move',_info['index'],event.src_pathname + ' -> ' + event.pathname,_info)

    def process_IN_MOVED_FROM(self,event):
        self.process_IN_MOVED_TO(event)

    def check_FILE(self,event,_info,create = False):
        if not _info: return False
        if self._DONE_FILE == event.pathname:
            self._DONE_FILE = None
            return False
        if self.access_FILE(event.pathname,_info): return False
        if not _info['open']: return False
        if not _info: return False
        if self.exclude_PATH(event.pathname,_info): return False
        if event.dir and create: return True
        if not self.exclude_EXT(event.pathname,_info): return False
        if event.pathname[-1] == '~': return False
        return True

    def exclude_EXT(self,pathname,_info):
        if pathname.find('.') == -1: return True
        extName = pathname.split('.')[-1].lower()
        if extName in ['swp','swx']: return False # vi/vim编辑器
        if _info:
            if extName in _info['exclude_ext']:
                return False
        return True

    def exclude_PATH(self,pathname,_info):
        if pathname.find('/') == -1: return False
        pathname = pathname.lower()
        f_name = os.path.basename(pathname)
        path = os.path.dirname(pathname)
        s_path = path.replace(_info['path'],'') + '/'

        for e_name in _info['exclude_name']:
            if e_name[-1] == '/':
                e_name = e_name[:-1]
            if e_name == f_name:
                return True
            elif e_name == path:
                return True
            elif e_name == pathname:
                return True
            elif s_path.find('/' +e_name + '/') != -1:
                return True
        return False

    def access_FILE(self,pathname,_info):
        filename = '/www/server/panel/access_file.pl'
        if not os.path.exists(filename): return False
        if pathname != public.readFile(filename): return False
        backupFile = self._PLUGIN_PATH + '/backup/' + _info['index'] + '/' + pathname
        if self.check_MD5(backupFile,pathname): return False
        self._DONE_FILE = pathname
        shutil.copyfile(pathname,backupFile)
        if os.path.exists(filename): os.remove(filename)
        return True

    def set_ACCRSS(self,filename,mode = 755,user = 'www',gid=None,uid=None,src_filename = None):
        if not os.path.exists(filename): return False
        if src_filename:
            m_stat = self.get_ACCESS(src_filename)
            mode = m_stat[0]
            uid = m_stat[1]
            gid = m_stat[2]

        if gid == None:
            u_pwd = pwd.getpwnam(user)
            gid = u_pwd.pw_gid
            uid = u_pwd.pw_uid

        os.chown(filename,uid,gid)
        os.chmod(filename,mode)
        return True

    def get_ACCESS(self,filename):
        stat = os.stat(filename)
        return stat.st_mode,stat.st_uid,stat.st_gid

    def check_MD5(self,file1,file2):
        md51 = self.get_MD5(file1)
        md52 = self.get_MD5(file2)
        return (md51 == md52)

    def renew_FILE(self,pathname,_info):
        if not _info['auto_recovery']: return False
        backupPath = self._PLUGIN_PATH + '/backup/' + _info['index'] + '/' + pathname
        if not os.path.exists(backupPath): return False
        if self.check_MD5(backupPath,pathname): return False
        if not os.path.exists(os.path.dirname(pathname)): os.makedirs(os.path.dirname(pathname))
        self._DONE_FILE = pathname
        shutil.copyfile(backupPath,pathname)
        self.set_ACCRSS(filename=pathname,src_filename=backupPath)
        return True

    def get_SITE_CONFIG(self,pathname):
        if not self._LIST_DATA: self._LIST_DATA = json.loads(public.readFile(self._LIST_FILE))
        for _info in self._LIST_DATA:
            length = len(_info['path'])
            if len(pathname) < length: continue
            if _info['path'] != pathname[:length]: continue
            if not _info['open']:continue
            return _info
        return None

    def get_MD5(self,filename):
        if not os.path.isfile(filename): return False
        my_hash = hashlib.md5()
        f = open(filename,'rb')
        while True:
            b = f.read(8096)
            if not b :
                break
            my_hash.update(b)
        f.close()
        return my_hash.hexdigest()

    def get_S_MD5(self,strings):
        m = hashlib.md5()
        m.update(strings)
        return m.hexdigest()


    def list_DIR(self,path,path_info,force = False):
        backupPath = os.path.join(self._PLUGIN_PATH + '/backup/',path_info['index'])
        if os.path.exists(backupPath) and not force:
            return

        if not os.path.exists(backupPath): os.makedirs(backupPath,600)

        # 记录同步时间
        if path == path_info['path']:
            time_file = os.path.join(backupPath,'time.pl')
            public.writeFile(time_file,str(int(time.time())))

        if os.path.isfile(path):
            fileName = path
            backupFile = backupPath + fileName
            if os.path.exists(backupFile):
                if self.check_MD5(backupFile,fileName):
                    return
            backup_dirname = os.path.dirname(backupFile)
            if not os.path.exists(backup_dirname): os.makedirs(backup_dirname,384)
            shutil.copyfile(fileName,backupFile)
            self.set_ACCRSS(filename=backupFile,src_filename=fileName)
        else:
            for name in os.listdir(path):
                if isinstance(name,bytes): name = name.decode('utf-8')
                lower_name = name.lower()
                if lower_name in path_info['exclude_name']: continue
                fileName = os.path.join(path,name)

                if os.path.isdir(fileName):
                    self.list_DIR(fileName,path_info,True)
                    continue
                if self.get_EXT_NAME(lower_name) in path_info['exclude_ext']: continue

                if os.path.getsize(fileName) > path_info['max_size']: continue

                backupFile = backupPath + fileName

                if os.path.exists(backupFile):
                    if self.check_MD5(backupFile,fileName):
                        continue

                backup_dirname = os.path.dirname(backupFile)
                if not os.path.exists(backup_dirname): os.makedirs(backup_dirname,384)
                shutil.copyfile(fileName,backupFile)
                self.set_ACCRSS(filename=backupFile,src_filename=fileName)

    def get_EXT_NAME(self,lower_name):
        # tar.gz 等二级扩展名未兼容
        return lower_name.split('.')[-1]

    def write_LOG(self,eventType,index,pathname,_info):
        now_time = time.time()
        last_time = now_time - self._last_files_time.get(pathname,0)
        if last_time < 0.2:
            return
        self._last_files_time[pathname] = now_time

        logPath = self._PLUGIN_PATH + '/logs/' + index
        if not os.path.exists(logPath): os.makedirs(logPath)
        logFile = os.path.join(logPath,'logs.json')
        logVar = [int(time.time()),eventType,pathname]
        fp = open(logFile,'a+')
        fp.write(json.dumps(logVar) + "\n")
        fp.close()
        totalLogFile = os.path.join(logPath,'total.json')
        if not os.path.exists(totalLogFile):
            totalData = {"total":0,"delete":0,"create":0,"modify":0,"move":0,"backup":0,"anti_virus":0}
        else:
            totalData = json.loads(public.readFile(totalLogFile))
        totalData['total'] += 1
        totalData[eventType] += 1

        public.writeFile(totalLogFile,json.dumps(totalData))
        event_msg = {'delete':'删除','create':'创建','modify':'修改','move':'移动或重命名'}
        res = '告警'
        if _info['auto_recovery']: res = "自动恢复并告警"
        msg = "监测对像：{}  \n文件：{}  \n时间：{}  \n事件：{}  \n处理结果：{}".format(_info['ps'],pathname,public.format_date(),event_msg[eventType],res)

        public.run_thread(self.send_msg,(msg,))
        # 备份和木马检测
        if eventType in ['modify','create']:
            if _info.get('auto_anti_virus'):
                public.run_thread(self.anti_virus,(pathname,_info,last_time))
            public.run_thread(self.save_history,(pathname,_info))


    # 保存历史副本
    def save_history(self, filename,_info):
        if not _info.get('auto_backup'):
            return True
        try:

            his_path = self._history_path
            if filename.find(his_path) != -1:
                return
            save_path = (his_path + filename).replace('//', '/')
            if not os.path.exists(save_path):
                os.makedirs(save_path, 384)

            his_list = sorted(os.listdir(save_path), reverse=True)
            num = _info.get("backup_num",30)
            num = int(num)
            d_num = len(his_list)
            is_write = True
            new_file_md5 = public.FileMd5(filename)
            for i in range(d_num):
                rm_file = save_path + '/' + his_list[i]
                if i == 0:  # 判断是否和上一份副本相同
                    old_file_md5 = public.FileMd5(rm_file)
                    if old_file_md5 == new_file_md5:
                        is_write = False

                if i+1 >= num:  # 删除多余的副本
                    if os.path.exists(rm_file):
                        os.remove(rm_file)
                    continue
            # 写入新的副本
            if is_write:
                public.writeFile(save_path + '/' + str(int(time.time())), public.readFile(filename, 'rb'), 'wb')
                self._is_history_num = 1
                public.WriteLog('文件监控',"检测到文件修改，已自动备份: [{}]:{} ".format(_info['ps'],filename))

                logPath = self._PLUGIN_PATH + '/logs/' + _info['index']
                totalLogFile = os.path.join(logPath,'total.json')
                if not os.path.exists(totalLogFile):
                    totalData = {"total":0,"delete":0,"create":0,"modify":0,"move":0,"backup":0,"anti_virus":0}
                else:
                    totalData = json.loads(public.readFile(totalLogFile))
                totalData['total'] += 1
                totalData['backup'] += 1
                public.writeFile(totalLogFile,json.dumps(totalData))

        except:
            print(public.get_error_info())


    def anti_virus(self,filename,_info,last_time):
        '''
            @name 木马查杀
            @filename 文件名
            @_info 目录信息
        '''
        if last_time < 0.5:
            return
        if not os.path.exists(filename): return
        if os.path.getsize(filename) < 10:
            return
        import webshell_check
        webshell = webshell_check.webshell_check()
        url = webshell.get_check_url()
        res = webshell.upload_file_url2(filename, url)
        if not res: return


        logPath = self._PLUGIN_PATH + '/logs/' + _info['index']
        totalLogFile = os.path.join(logPath,'total.json')
        if not os.path.exists(totalLogFile):
            totalData = {"total":0,"delete":0,"create":0,"modify":0,"move":0,"backup":0,"anti_virus":0}
        else:
            totalData = json.loads(public.readFile(totalLogFile))
        totalData['total'] += 1
        totalData['anti_virus'] += 1
        public.writeFile(totalLogFile,json.dumps(totalData))


        # 告警
        msg = "监测对像：{}  \n文件：{}  \n时间：{}  \n事件：{}  \n处理结果：告警".format(_info['ps'],filename,public.format_date(),"疑似包含恶意代码，请及时处理")
        public.WriteLog('文件监控',"检测到疑似恶意代码，请及时处理: [{}]:{} ".format(_info['ps'],filename))
        self.send_msg(msg)

    def send_msg(self,msg):
        body = "服务器IP：{}  \n{}".format(public.get_ip(),msg)
        title = '【堡塔文件监控】告警事件 - {}'.format(public.get_ip())
        try:
            import panelPush
            msg_dict = {"msg":body}
            msg_all = {
                "feishu":msg_dict,
                "weixin":msg_dict,
                "dingding":msg_dict,
                "wx_account": msg_dict,
                "mail":{
                    "msg": body.replace('**','').replace("\n", "<br/>"),
                    "title": title
                }
            }
            res =  panelPush.panelPush().push_message_immediately(msg_all)
            return res
        except Exception as ex:
            public.send_dingding(body,False)
            public.send_mail(title,body.replace('**','').replace("\n", "<br/>"),False)
            return public.print_log('告警发送失败: {}'.format(ex))


def run():
    import time
    s = time.time()
    watchManager = pyinotify.WatchManager()
    event = MyEventHandler()
    mode = pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM
    _list = json.loads(public.readFile(event._LIST_FILE))
    logType = u'文件监控'
    os.chdir("/www/server/panel")
    for path_info in _list:
        if not path_info['open']: continue
        event.list_DIR(path_info['path'],path_info)
        watchManager.add_watch(path_info['path'], mode ,auto_add=True, rec=True)

    e = round(time.time() - s,2)
    public.WriteLog(logType,u"文件监控服务已成功启动,耗时[%s]秒" % e)
    notifier = pyinotify.Notifier(watchManager, event)
    notifier.loop()


if __name__ == '__main__':
    run()
