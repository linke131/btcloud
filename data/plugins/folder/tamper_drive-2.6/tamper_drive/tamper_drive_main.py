#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔防篡改程序
# +--------------------------------------------------------------------
import os
import sys
import public
import json
import time

if __name__ != '__main__':
    from BTPanel import session, cache


class tamper_drive_main:
    __plugin_path = '/www/server/panel/plugin/tamper_drive'
    __data_path = '/www/server/tamper'
    __sites = None
    __session_name = 'tamper_drive_' + time.strftime('%Y-%m-%d')
    __rc4_key = "FMWfFY2B7sGZJaaT"
    __sync_file = __data_path + '/specially'
    __tamper_file = __data_path + '/logs/'
    __tamper_total = __data_path + '/total/'
    __service_config = None
    __tamper_conf = __data_path + "/tamper_drive.conf"
    __global_config = __plugin_path + '/config.json'
    __index = 0
    __max_site = 384

    def __init__(self):
            if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'send_settings')).count():
                public.M('').execute('''CREATE TABLE "send_settings" (
                    "id" INTEGER PRIMARY KEY AUTOINCREMENT,"name" TEXT,"type" TEXT,"path" TEXT,"send_type" TEXT,"last_time" TEXT ,"time_frame" TEXT,"inser_time" TEXT DEFAULT'');''')
            if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'send_msg')).count():
                public.M('').execute(
                    '''CREATE TABLE "send_msg" ("id" INTEGER PRIMARY KEY AUTOINCREMENT,"name" TEXT,"send_type" TEXT,"msg" TEXT,"is_send" TEXT,"type" TEXT,"inser_time" TEXT DEFAULT '');''')

    '''设置表插入数据'''
    def insert_settings(self,name,type,path,send_type,time_frame=180):
        inser_time = self.dtchg(int(time.time()))
        last_time=int(time.time())
        if public.M('send_settings').where('name=?',(name,)).count(): return False
        data={"name":name,"type":type,"path":path,"send_type":send_type,"time_frame":time_frame,"inser_time":inser_time,"last_time":last_time}
        return public.M('send_settings').insert(data)

    # 取当前可用PHP版本
    def GetPHPVersion(self):
        phpVersions = public.get_php_versions()
        httpdVersion = ""
        data = []
        for val in phpVersions:
            tmp = {}
            checkPath = '/www/server/php/' + val + '/bin/php'
            if val in ['00', 'other']: checkPath = '/etc/init.d/bt'
            if httpdVersion == '2.2': checkPath =  '/www/server/php/' + val + '/libphp5.so'
            if os.path.exists(checkPath):
                tmp['version'] = val
                tmp['name'] = 'PHP-' + val
                if val == '00':
                    continue

                if val == 'other':
                    continue
                data.append(tmp)
        if len(data)>=0:
            return data[0]
        return False

    def sim_test(self,get):
        '''
        @name 模拟测试是否成功
        @author 梁凯强<2022-1-11>
        @param path 目录
        @return int
        '''
        path=get.path.strip()
        if not os.path.exists(path):return public.returnMsg(False,"此目录不存在")
        #判断是否安装php
        php_version =self.GetPHPVersion()
        if not php_version:return public.returnMsg(False,"未安装PHP测试失败")
        php_path='/www/server/php/' + php_version['version'] + '/bin/php'
        php_name= path+"/"+str(int(time.time()))+".php"
        if os.path.exists(php_name):
            public.ExecShell("rm -rf %s"%php_name)
        ###写入
        cmdString=php_path+" -r \"file_put_contents('{}','{}');\"".format(php_name,php_name)
        public.ExecShell(cmdString,user='www')
        if os.path.exists(php_name):
            if os.path.exists(php_name):
                public.ExecShell("rm -rf %s" % php_name)
            return public.returnMsg(False,"写入文件成功,可能未开启防篡改")
        return public.returnMsg(True, "拦截成功")

    def dtchg(self,x):
        try:
            time_local = time.localtime(float(x))
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
            return dt
        except:
            return False


    def get_index(self, get):
        #ret = self.get_tamper_drive()
        #if ret == 0:
        #  return False

        day = None
        if hasattr(get, 'day'):
            day = get.day
            day = day.replace('-0','-')
        data = {}
        self.sync_sites(None)
        data['open'] = self.get_service_status(None)
        data['sites'] = self.get_sites(None)
        data['total'] = self.get_total()
        data['mod_status'] = self.check_mod_status()
        for i in range(len(data['sites'])):
            data['sites'][i]['total'] = self.get_total(
                data['sites'][i]['siteName'], day)
        return data

    def check_os(self):
        os_v = public.ExecShell(r'cat /etc/redhat-release |grep "CentOS"|grep -Eo "[0-9]+\.[0-9]+\.[0-9]+"')[0].strip()
        if not os_v:
            return public.returnMsg(False,'不支持的操作系统类型，需要Centos7.x Centos8.x')
        if os_v[0] != '7' and os_v[0] != '8':
            return public.returnMsg(False,'不支持的操作系统版本，需要Centos7.x,centos8.x')
        
        core_v = int(public.ExecShell("uname -r|awk -F. '{print $1$2}'")[0])
        if core_v > 418 or core_v < 310:
            return public.returnMsg(False,'不支持的Linux内核版本，仅支持：kernel-3.10 - 4.18')

        return False


    def reload_mod(self,args=None):
        '''
            @name 尝试重新加载内核模块
            @author 黄文良<2020-05-12>
            @return int
        '''

        res = self.check_os()
        if res:
            return res
        kos_path = self.__plugin_path + '/kos'
        if not os.path.exists(kos_path):
            os.makedirs(kos_path,384)
        cfg_file = kos_path + '/tampercfg.ko'
        core_file = kos_path + '/tampercore.ko'
        if not os.path.exists(cfg_file):
            public.ExecShell("wget -O {} {} -T 5".format(cfg_file,public.get_url() + '/install/plugin/tamper_drive/kos/tampercfg.ko'))
            public.ExecShell("wget -O {} {} -T 5".format(core_file,public.get_url() + '/install/plugin/tamper_drive/kos/tampercore.ko'))
        
        init_file = '/etc/init.d/bt_tamper_drive'
        if not os.path.exists(init_file):
            service_file = self.__plugin_path + '/bt_tamper_drive'
            if not os.path.exists(service_file):
                public.ExecShell("wget -O {} {} -T 5".format(service_file,public.get_url() + '/install/plugin/tamper_drive/bt_tamper_drive'))
            
            public.ExecShell("\cp -arf {} {}".format(service_file,init_file))
            public.ExecShell("chmod +x {}".format(init_file))
            public.ExecShell("chkconfig --add bt_tamper_drive")
            public.ExecShell("chkconfig --level 2345 bt_tamper_drive on")

        public.ExecShell("{} start".format(init_file))
        if self.check_mod_status():
            return public.returnMsg(True,'模块加载成功!')
        return public.returnMsg(False,'模块加载失败!')


    def check_mod_status(self):
        '''
            @name 检测内核模块是否加载
            @author 黄文良<2020-05-12>
            @return int
        '''
        is_mod = public.ExecShell("lsmod|grep tampercore")[0].strip()
        if not is_mod:
            return 0
        return 1
        
    def get_safe_count(self):
        '''
            @name 获取当前受保护的网站数量
            @author 黄文良<2020-04-24>
            @return int
        '''
        data = self.get_sites(None)
        n = 0
        for i in data:
            if i['open'] in ['1',1,True]:
                n+=1
        return n

    def get_sites(self, get=None):
        if self.__sites:
            return self.__sites
        siteconf = self.__plugin_path + '/sites.json'
        d = public.readFile(siteconf)
        if not os.path.exists(siteconf) or not d:
            public.writeFile(siteconf, "[]")
        data = json.loads(public.readFile(siteconf))
        is_write = False
        for i in range(len(data)):
            if not 'open' in data[i]:
                data[i]['open'] = False
                if 'bak_open' in data[i]:
                    data[i]['open'] = data[i]['bak_open']
                    data[i].pop('bak_open')
                    is_write = True
                if 'lock' in data[i]:
                    data[i].pop('lock')
                    is_write = True
            if not 'protect_whiteprocess' in data[i]:
                data[i]['protect_whiteprocess'] = []
            if not 'protect_whitepathfile' in data[i]:
                data[i]['protect_whitepathfile'] = []
            if not 'uid' in data[i]:
                data[i]['uid'] = ['0']
                
        if is_write:
            public.writeFile(siteconf, json.dumps(data))
        self.__sites = data
        return data

    def get_site_find(self, get):
        return self.__get_find(get.siteName)

    def __get_find(self, siteName):
        data = self.get_sites(None)
        for siteInfo in data:
            if siteName == siteInfo['siteName']:
                return siteInfo
        return None

    def save_site_config(self, siteInfo):
        data = self.get_sites(None)
        for i in range(len(data)):
            if data[i]['siteName'] != siteInfo['siteName']:
                continue
            data[i] = siteInfo
            break
        self.write_sites(data)

    def write_sites(self, data):
        public.writeFile(self.__plugin_path + '/sites.json', json.dumps(data))
        self.__write_service_config()
        self.__write_sync()

    def set_site_status(self, get):
        '''
            @name 设置网站防篡改状态
            @author 黄文良<2020-04-24>
            @param get dict_obj{
                siteName: string(网站名称)
            }
            @return dict{
                status: bool(状态),
                msg: string(详情)
            }
        '''
        siteInfo = self.get_site_find(get)
        if not siteInfo:
            return public.returnMsg(False, u'指定站点不存在!')
        if len(siteInfo['path']) > 128:
            return public.returnMsg(False,'受保护的目录长度不能大于128个字符')
        if len(siteInfo['siteName']) > 64:
            return public.returnMsg(False,'受保护的网站名称长度不能大于64个字符')
            
        if not siteInfo['open']:
            if self.get_safe_count() >= self.__max_site:
                return public.returnMsg(False,'开启失败最多只能保护{}个网站'.format(self.__max_site))
        siteInfo['open'] = not siteInfo['open']
        
        self.save_site_config(siteInfo)
        m_logs = {True: '开启', False: '关闭'}
        self.write_log('%s站点[%s]防篡改保护' %
                       (m_logs[siteInfo['open']], siteInfo['siteName']))
        return public.returnMsg(True, u'设置成功!')

    def add_excloud(self, get):
        siteInfo = self.get_site_find(get)
        if not siteInfo:
            return public.returnMsg(False, u'指定站点不存在!')
        get.excludePath = get.excludePath.strip()
        if len(get.excludePath) > 64:
            return public.returnMsg(False,'排除的目录路径长度不能超过64个字符')
        if not get.excludePath: return public.returnMsg(False,'不能排除空值!')
        if len(siteInfo['excludePath']) >= 64:
            return public.returnMsg(False,'最多只能添加24条排除规则!')
        if get.excludePath in siteInfo['excludePath']:
            return public.returnMsg(False, u'指定目录已在排除列表!')
        siteInfo['excludePath'].insert(0, get.excludePath)
        self.save_site_config(siteInfo)
        self.write_log('站点[%s]添加排除目录名[%s]到排除列表' %
                       (siteInfo['siteName'], get.excludePath))
        return public.returnMsg(True, u'添加成功!')

    def remove_excloud(self, get):
        siteInfo = self.get_site_find(get)
        if not siteInfo:
            return public.returnMsg(False, u'指定站点不存在!')
        if not get.excludePath in siteInfo['excludePath']:
            return public.returnMsg(False, u'指定目录不在排除列表!')
        siteInfo['excludePath'].remove(get.excludePath)
        self.save_site_config(siteInfo)
        self.write_log('站点[%s]从排除列表中删除目录名[%s]' %
                       (siteInfo['siteName'], get.excludePath))
        return public.returnMsg(True, u'删除成功!')

    def add_protect_ext(self, get):
        if get.protectExt.find('.') != -1:
            return public.returnMsg(False, u'扩展名称不能包含[.]')
        siteInfo = self.get_site_find(get)
        if not siteInfo:
            return public.returnMsg(False, u'指定站点不存在!')
        get.protectExt = get.protectExt.strip()
        if len(get.protectExt) > 12:
            return public.returnMsg(False,'扩展名最大长度不能超过12个字符!')
        if not get.protectExt:
            return public.returnMsg(False,'扩展名不能为空!')
        if len(siteInfo['protectExt']) >= 64:
            return public.returnMsg(False,'最多只能添加64个受保护的扩展名!')
        if get.protectExt in siteInfo['protectExt']:
            return public.returnMsg(False, u'指定文件类型已在受保护列表!')
        siteInfo['protectExt'].insert(0, get.protectExt)
        self.save_site_config(siteInfo)
        self.write_log('站点[%s]添加文件类型[.%s]到受保护的文件类型列表' %
                       (siteInfo['siteName'], get.protectExt))
        return public.returnMsg(True, u'添加成功!')

    def remove_protect_ext(self, get):
        siteInfo = self.get_site_find(get)
        if not siteInfo:
            return public.returnMsg(False, u'指定站点不存在!')
        if not get.protectExt in siteInfo['protectExt']:
            return public.returnMsg(False, u'指定文件类型不在受保护列表!')
        siteInfo['protectExt'].remove(get.protectExt)
        self.save_site_config(siteInfo)
        self.write_log('站点[%s]从受保护的文件类型列表中删除文件类型[.%s]' %
                       (siteInfo['siteName'], get.protectExt))
        return public.returnMsg(True, u'删除成功!')
        
        
    def get_users(self,get):
        '''
            @name 获取系统用户列表
            @author 黄文良<2020-04-24>
            @param get dict_obj{
                siteName: string(网站名称)
            }
            
            @return list[
                {
                    username: string(用户名),
                    uid: int(uid),
                    gid: int(gid),
                    state: int(1.受保护 0.不受保护),
                    ps: string(用户描述)
                }
            ]
        '''
        
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,'指定网站不存在!')
        pwd_conf = public.readFile('/etc/passwd')
        pwd_line = pwd_conf.split('\n')
        sys_users = []
        u_ps = {
            "root":"超级管理员",
            "www":"宝塔管理的网站、FTP服务使用的用户",
            "redis":"redis数据库用户",
            "mysql":"mysql数据库用户",
            "ftp":"系统中其它FTP",
            "mail":"邮件帐户",
            "postfix":"postfix邮局服务",
            "sync": "rsync数据同步服务"
        }
        
        for pwd_info in pwd_line:
            u_info = pwd_info.split(':')
            if not u_info: continue
            if len(u_info) < 4: continue
            ###if u_info[0] in ['root','www']: continue
            tmp = {
                'username': u_info[0],
                'uid': u_info[2],
                'gid': u_info[3],
                'state': '0',
                'ps': u_info[0] 
            }
            if u_info[0] in u_ps.keys():
                tmp['ps'] = u_ps[u_info[0]]
            if not u_info[2] in siteInfo['uid']:
                tmp['state'] = '1'
            sys_users.append(tmp)
        return sys_users
    
    def set_user_status(self, get):
        '''
            @name 设置系统用户的防篡改状态
            @author 黄文良<2020-04-24>
            @param get dict_obj {
                uid: int(系统用户的uid),
                username: string(系统用户名),
                siteName: string(网站名称),
                state: int(0.关闭 / 1.开启)
            }
            @return dict{
                status: bool,
                msg: string
            }
        '''
        if not 'uid' in get:
            return public.returnMsg(False,'uid不能为空!')
        if not 'username' in get:
            return public.returnMsg(False,'username不能为空!')
        if not 'siteName' in get:
            return public.returnMsg(False,'siteName不能为空!')
        if not 'state' in get:
            return public.returnMsg(False,'state不能为空!')
        if len(get.uid) < 1:
            return public.returnMsg(False,'uid不能为空!')
        if len(get.username) < 1:
            return public.returnMsg(False,'username不能为空!')
        if len(get.siteName) < 1:
            return public.returnMsg(False,'siteName不能为空!')
        if len(get.state) < 1:
            return public.returnMsg(False,'state不能为空!')
        if len(get.uid) > 6:
            return public.returnMsg(False,'UID长度不能超过6位数!')
        
        siteInfo = self.get_site_find(get)
        if not siteInfo:
            return public.returnMsg(False, u'指定站点不存在!')
        
        if not 'uid' in siteInfo:
            siteInfo['uid'] = ['0']
            
        if len(siteInfo['uid']) >= 64:
            return public.returnMsg(False,'不受保护的用户数量不能超过64个!')
        
        if get.state == '1':
            if not get.uid in siteInfo['uid']:
                siteInfo['uid'].append(get.uid)
        else:
            if get.uid in siteInfo['uid']:
                siteInfo['uid'].remove(get.uid)
        
        self.save_site_config(siteInfo)
        stats = {'0':"关闭",'1':"开启"}
        self.write_log('站点[{}]设置用户[{}]的防篡改状态为[{}]'.format(siteInfo['siteName'], get.username,stats[get.state]))
        return public.returnMsg(True, u'设置成功!')

    # 同步网站列表
    def sync_sites(self, get):
        data = self.get_sites(None)
        sites = public.M('sites').field('name,path').select()
        config = self.get_global_config()
        names = []
        n = 0
        for siteTmp in sites:
            names.append(siteTmp['name'])
            siteInfo = self.__get_find(siteTmp['name'])
            if siteInfo:
                if siteInfo['path'] != siteTmp['path']:
                    siteInfo['path'] = siteTmp['path']
                    self.save_site_config(siteInfo)
                    data = self.get_sites()
                continue
            siteInfo = {}
            siteInfo['siteName'] = siteTmp['name']
            siteInfo['path'] = siteTmp['path']
            siteInfo['open'] = False
            siteInfo['excludePath'] = config['excludePath']
            siteInfo['protectExt'] = config['protectExt']
            siteInfo['uid'] = []
            siteInfo['protect_whiteprocess'] = []
            siteInfo['protect_whitepathfile'] = []
            data.append(siteInfo)
            n += 1

        newData = []
        for siteInfoTmp in data:
            if siteInfoTmp['siteName'] in names:
                newData.append(siteInfoTmp)
            else:
                public.ExecShell("rm -rf " + self.__plugin_path +
                                 '/sites/' + siteInfoTmp['siteName'])
                n += 1
        if n > 0:
            self.write_sites(newData)
        self.__sites = None

    def get_total(self, siteName=None, day=None):
        if siteName:
            total = {}
            total['site'] = self.format_total(public.readFile(
                self.__tamper_total + '/'+siteName+'/total.txt'))
            if not day:
                day = time.strftime("%Y-%m-%d", time.localtime())
            day = day.replace('-0','-')
            total['day'] = self.format_total(public.readFile(
                self.__tamper_total + '/' + siteName + '/' + day + '.txt'))
        else:
            total = self.format_total(public.readFile(
                self.__tamper_total + '/total.txt'))
        return total

    def Reverse(self,lst):
        return [ele for ele in reversed(lst)]

    def get_days(self, path):
        days = []
        if not os.path.exists(path):
            os.makedirs(path)
        for dirname in os.listdir(path):
            if dirname == '..' or dirname == '.' or dirname == 'total.json':
                continue
            if os.path.isdir(path + '/' + dirname):
                continue
            days.append(dirname.split('.')[0])
        days = sorted(days, reverse=True)
        return days
        #return self.Reverse(days)



    def format_total(self, data):
        defaultTotal = {"total": 0, "delete": 0,
                        "create": 0, "modify": 0, "move": 0}
        if not data:
            return defaultTotal
        t_tmp = data.split()
        try:
            defaultTotal['total'] = int(t_tmp[0].split('=')[1])
            defaultTotal['create'] = int(t_tmp[1].split('=')[1])
            defaultTotal['delete'] = int(t_tmp[2].split('=')[1])
            defaultTotal['modify'] = int(t_tmp[3].split('=')[1])
            defaultTotal['move'] = int(t_tmp[4].split('=')[1])
            return defaultTotal
        except:
            return data

    # 取文件指定尾行数
    def GetNumLines(self, path, num, p=1):
        pyVersion = sys.version_info[0]
        try:
            import cgi
            if not os.path.exists(path):
                return ""
            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path, 'rb')
            buf = ""
            fp.seek(-1, 2)
            if fp.read(1) == "\n":
                fp.seek(-1, 2)
            data = []
            b = True
            n = 0
            for i in range(count):
                while True:
                    newline_pos = str.rfind(str(buf), "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            try:
                                data.append(json.loads(cgi.escape(line)))
                            except:
                                pass
                        buf = buf[:newline_pos]
                        n += 1
                        break
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pyVersion == 3:
                            if type(t_buf) == bytes:
                                t_buf = t_buf.decode('utf-8')
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b:
                    break
            fp.close()
        except:
            return []
        if len(data) >= 2000:
            arr = []
            for d in data:
                arr.insert(0, json.dumps(d))
            public.writeFile(path, "\n".join(arr))
        return data

    def get_safe_logs(self, get):
        data = {}
        path = self.__tamper_file + '/'+get.siteName
        data['days'] = self.get_days(path)
        
        if not data['days']:
            data['logs'] = []
        else:
            if not 'p' in get:
                get.p = 1
                
            day = data['days'][0]
            if hasattr(get, 'day'):
                day = get.day
            day = day.replace('-0','-')
            data['get_day'] = day
            data['logs'] = self.GetNumLines(
                path + '/' + day + '.log', 2000, int(get.p))
        return data

    def ClearDayLog(self, get):
        data = {}
        path = self.__tamper_file+ '/' + get.siteName + '/'
        data['days'] = self.get_days(path)
        get.day = get.day.replace('-0','-')
        if get.day in data['days']:
            logpath = (path+get.day + '.log').replace('//','/')
            if os.path.exists(logpath):
                public.ExecShell("echo ''> %s" % logpath)
                public.WriteLog('防篡改程序', logpath+" 防篡改日志清理成功")
                return public.returnMsg(True, u'清理成功!')
            else:
                return public.returnMsg(False, u'没有该日志文件!' +  path+get.day + '.log')
                
                
    def get_logs(self, get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (u'防篡改程序',)).count()
        limit = 12
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = {}
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        data['page'] = page.GetPage(info, '1,2,3,4,5')
        data['data'] = public.M('logs').where('type=?', (u'防篡改程序',)).order(
            'id desc').limit(str(page.SHIFT)+','+str(page.ROW)).field('log,addtime').select()
        return data

    def write_log(self, log):
        public.WriteLog('防篡改程序', log)

    def get_tamper_drive(self):
        import panelAuth
        from BTPanel import session
        if self.__session_name in session:
            if session[self.__session_name] != 0:
                return session[self.__session_name]

        cloudUrl = public.GetConfigValue('home')+'/api/panel/get_soft_list_test'
        pdata = panelAuth.panelAuth().create_serverid(None)
        ret = public.httpPost(cloudUrl, pdata)
        if not ret:
            if not self.__session_name in session:
                session[self.__session_name] = 1
            return 1
        try:
            ret = json.loads(ret)
            for i in ret["list"]:
                if i['name'] == 'tamper_drive':
                    if i['endtime'] >= 0:
                        session[self.__session_name] = 2
                        return 2
            return 0
        except:
            session[self.__session_name] = 1
            return 1

    # 添加保护目录
    def AddProtect_Path(self, get):
        # 保存之后重载配置
        protect_path = get['protect_path'].strip()
        name = os.path.basename(protect_path)
        if not os.path.exists(protect_path):
            os.makedirs(protect_path)

        # 添加网站记录
        data = self.get_site_conf(None)
        protect_list = {
            "siteName": name,
            "path": protect_path,
            "service_status": 1,
            "protectExt": [],
            "excludePath": [],
            "protect_whiteprocess": [],
            "protect_whitepathfile": []
        }
        data.append(protect_list)
        self.write_sites(data)
        # 添加内核模块的配置数据
        self.__write_service_config()
        self.write_log('添加保护目录[' + protect_path + ']')
        self.__write_sync()
        return public.returnMsg(True, '添加成功!')

    def rc4(self, data, key):
        S, j, out = list(range(256)), 0, []
        for i in range(256):
            j = (j + S[i] + ord(key[i % len(key)])) % 256
            S[i], S[j] = S[j], S[i]
        i = j = 0
        for ch in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            out.append(chr(ord(ch) ^ S[(S[i] + S[j]) % 256]))
        return "".join(out)

    # 获取全局配置
    def get_global_config(self, get=None):
        data = json.loads(public.readFile(self.__global_config))
        if not 'open' in data:
            data['open'] = False
            if 'bak_open' in data:
                data['open'] = data['bak_open']
                del(data['bak_open'])
            if 'lock' in data:
                del(data['lock'])
            self.save_global_config(data)
        return data

    # 保存全局配置
    def save_global_config(self, config):
        public.writeFile(self.__global_config, json.dumps(config))
        self.__write_service_config()
        self.__write_sync()
        return True

    # 设置全局状态
    def set_global_status(self, get=None):
        data = self.get_global_config()
        data['open'] = not data['open']
        self.save_global_config(data)
        m_logs = {True: '开启', False: '关闭'}
        self.write_log('全局[%s]防篡改' % (m_logs[data['open']]))
        return public.returnMsg(True, '操作成功!')

    # 获取全局状态
    def get_service_status(self, get=None):
        return self.get_global_config()['open']

    def __write_service_config(self):
        self.__service_config = ""
        status = self.get_service_status(None)
        if status:
            status = 1
        else:
            status = 0
        self.__service_config += '''[service_begin]
service_on={}

[path_group]
'''.format(status)
        data = self.get_site_conf(None)
        for i in range(len(data)):
            self.__write_config_to(data[i])
        public.writeFile(self.__tamper_conf + '.show', self.__service_config)
        public.writeFile(self.__tamper_conf, self.rc4(self.__service_config, self.__rc4_key))
        public.ExecShell("chmod -R 777 {}".format(self.__data_path))
        public.ExecShell("chown -R root:root {}".format(self.__data_path))
        self.__service_config = ""
        self.__index = 0

    def __write_config_to(self, data):
        if not data['open']:
            return
        #if self.__index >= self.__max_site:
        #    return

        if data['open']:
            data['open'] = 1
        else:
            data['open'] = 0
        if not 'protect_whiteprocess' in data:
            data['protect_whiteprocess'] = []
        if not 'protect_whitepathfile' in data:
            data['protect_whitepathfile'] = []
        if not 'uid' in data:
            data['uid'] = ['0']
        
        self.__service_config += """name{index}={name}
path{index}={path}
open_status{index}={service_status}
uid{index}={uid},
process{index}={protect_whiteprocess},
rule_one{index}={protectExt},
rule_two{index}={excludePath},
rule_three{index}={protect_whitepathfile},

""".format(index=self.__index,
           name=data['siteName'],
            path=data['path'],
            uid=','.join(data['uid']),
            service_status=data['open'],
            protect_whiteprocess=','.join(data['protect_whiteprocess']),
            protectExt=','.join(data['protectExt']),
            excludePath=','.join(data['excludePath']),
            protect_whitepathfile=','.join(data['protect_whitepathfile'])).replace('=,', '=')

        self.__index = self.__index + 1

        log_path = self.__tamper_file + '/{}'.format(data['siteName'])
        if not os.path.exists(log_path):
            os.makedirs(log_path, mode=384)

        total_path = self.__tamper_total + '/{}'.format(data['siteName'])
        if not os.path.exists(total_path):
            os.makedirs(total_path, mode=384)
        
        
    def __write_sync(self):
        public.ExecShell("sync")

        if os.path.exists(self.__sync_file):
            os.removedirs(self.__sync_file)
        os.makedirs(self.__sync_file,mode=493)
        # time.sleep(0.1)
        # if os.path.exists(self.__sync_file):
        #    os.removedirs(self.__sync_file)
        
    def get_site_conf(self, get):
        data = json.loads(public.readFile(self.__plugin_path + '/sites.json'))
        return data


    #报警日志
    def get_log_send(self,get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (u'堡塔防篡改告警',)).count()
        limit = 12
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
        data = {}
        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('logs').where('type=?', (u'堡塔防篡改告警',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data


    '''报警开关'''
    def get_send_status(self,get):
        if not public.M('send_settings').where('name=?', ('堡塔防篡改',)).count():return public.returnMsg(False,{"open":False,'to_mail':False})
        data=public.M('send_settings').where('name=?', ('堡塔防篡改',)).field('id,name,type,path,send_type,inser_time,last_time,time_frame').select()
        data=data[0]
        if data['send_type']=='mail':return public.returnMsg(True,{"open": True, "to_mail": "mail"})
        if data['send_type'] == 'mail': return public.returnMsg(True,{"open": True, "to_mail": "dingding"})
        else:return public.returnMsg(False,{"open":False,'to_mail':False})

    '''报警设置'''
    def set_mail_to(self,get):
        if not public.M('send_settings').where('name=?', ('堡塔防篡改',)).count():
            self.insert_settings('堡塔防篡改', 'file', '/www/server/tamper/notice.txt', 'mail',900)
            self.write_log('开启成功邮件告警成功')
            return public.returnMsg(True, '开启成功')
        else:
            data = public.M('send_settings').where('name=?', ('堡塔防篡改',)).field(
                'id,name,type,path,send_type,inser_time,last_time,time_frame').select()
            data=data[0]
            public.M('send_settings').where("id=?",(data['id'])).update({"send_type":"mail"})
            self.write_log('开启成功邮件告警成功')
            return public.returnMsg(True, '开启成功')

    '''钉钉'''
    def set_dingding(self,get):
        if not public.M('send_settings').where('name=?', ('堡塔防篡改',)).count():
            self.insert_settings('堡塔防提权', 'file', '/www/server/tamper/notice.txt', 'dingding',900)
            self.write_log('开启成功dingding告警成功')
            return public.returnMsg(True, '开启成功')
        else:
            data = public.M('send_settings').where('name=?', ('堡塔防篡改',)).field(
                'id,name,type,path,send_type,inser_time,last_time,time_frame').select()
            data=data[0]
            public.M('send_settings').where("id=?",(data['id'])).update({"send_type":"dingding"})
            self.write_log('开启成功dingding告警成功')
            return public.returnMsg(True, '开启成功')