#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwliang@bt.cn>
# +-------------------------------------------------------------------
#+--------------------------------------------------------------------
#|   宝塔防篡改程序
#+--------------------------------------------------------------------
import os,sys,public,json,time

class tamper_proof_main:
    __plugin_path = '/www/server/panel/plugin/tamper_proof'
    __sites = None
    __session_name = 'tamper_proof' + time.strftime('%Y-%m-%d')



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
        if len(data)>0:
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
        time.sleep(0.5)
        if os.path.exists(php_name):
            if os.path.exists(php_name):
                public.ExecShell("rm -rf %s" % php_name)
            return public.returnMsg(False,"拦截失败,可能未开启防篡改")
        return public.returnMsg(True, "拦截成功")



    def get_speed(self,get):
        speed_file = self.__plugin_path + '/speed.pl'
        log_file = self.__plugin_path + '/service.log'
        result = {'speed':'','log':'','status':True,'msg':'获取成功'}
        if os.path.exists(speed_file):
            result['speed'] = public.readFile(speed_file)
        if os.path.exists(log_file):
            result['log'] = public.GetNumLines(log_file,11)
        return result

    def get_run_logs(self,get):
        log_file = self.__plugin_path + '/service.log'
        return public.returnMsg(True,public.GetNumLines(log_file,200))
    
    def get_index(self,get):
        ret=self.get_tamper_proof()
        if ret==0:
            return  False
        self.sync_sites(get)
        day = None
        if hasattr(get,'day'): day = get.day
        data = {}
        data['open'] = self.get_service_status(None)
        data['sites'] = self.get_sites(None)
        data['total'] = self.get_total()
        for i in range(len(data['sites'])):
            data['sites'][i]['total'] = self.get_total(data['sites'][i]['siteName'],day)
        return data

    def get_sites(self,get = None):
        if self.__sites: return self.__sites
        siteconf = self.__plugin_path + '/sites.json'
        d = public.readFile(siteconf)
        if not os.path.exists(siteconf) or not d:
            public.writeFile(siteconf,"[]")
        data = json.loads(public.readFile(siteconf))

        # 处理多余字段开始 >>>>>>>>>>
        is_write = False
        rm_keys = ['lock','bak_open']
        for i in data:
            i_keys = i.keys()
            if not 'open' in i_keys: i['open'] = False
            for o in rm_keys:
                if o in i_keys:
                    if i[o]: i['open'] = True
                    i.pop(o)
                    is_write = True
        if is_write: public.writeFile(siteconf,json.dumps(data))
        # 处理多余字段结束 <<<<<<<<<<<<<
        
        self.__sites = data
        return data

    def get_site_find(self,get):
        return self.__get_find(get.siteName)

    def __get_find(self,siteName):
        data = self.get_sites(None)
        for siteInfo in data:
            if siteName == siteInfo['siteName']: return siteInfo
        return None

    def save_site_config(self,siteInfo):
        data = self.get_sites(None)
        for i in range(len(data)):
            if data[i]['siteName'] != siteInfo['siteName']: continue
            data[i] = siteInfo
            break
        self.write_sites(data)

    def write_sites(self,data):
        public.writeFile(self.__plugin_path + '/sites.json',json.dumps(data))
        public.ExecShell('/etc/init.d/bt_tamper_proof reload')

    def service_admin(self,get):
        m_logs = {'start':'启动','stop':'停止','restart':'重启'}
        public.ExecShell('/etc/init.d/bt_tamper_proof %s' % get.serviceStatus)
        self.write_log('%s防篡改服务' % m_logs[get.serviceStatus])
        return public.returnMsg(True,u'操作成功!')

    def get_service_status(self,get):
        result = public.ExecShell("/etc/init.d/bt_tamper_proof status|grep already")
        return (len(result[0]) > 3)

    def set_site_status(self,get):
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        try:
            siteInfo['open'] =  not siteInfo['open']
        except:
            siteInfo['open'] = not siteInfo['open']
        # if siteInfo['open']:
        #     if not self.check_site_type(siteInfo): return public.returnMsg(False,u'不支持指定项目!')
        self.save_site_config(siteInfo)
        m_logs = {True:'开启',False:'关闭'}
        self.write_log('%s站点[%s]防篡改保护' % (m_logs[siteInfo['open']],siteInfo['siteName']))
        return public.returnMsg(True,u'设置成功!')


    def set_site_status_all(self,get):
        '''
            @name 批量设置网站状态
            @author hwliang<2021-05-13>
            @param get<dict_obj{
                siteNames: JSON<网站名称> JSON列表字符串, 例：["bt.cn","abc.cn"]
                siteState: int<防篡改状态> 0.关闭 1.开启
            }>
            @return dict
        '''
        sites = self.get_sites(None)
        siteState = True if get.siteState == '1' else False
        siteNames = json.loads(get.siteNames)
        m_logs = {True:'开启',False:'关闭'}
        for i in range(len(sites)):
            if sites[i]['siteName'] in siteNames: 
                sites[i]['open'] =  siteState
                self.write_log('%s站点[%s]防篡改保护' % (m_logs[siteState],sites[i]['siteName']))
        self.write_sites(sites)
        return public.returnMsg(True,'批量设置成功')



    def CheckSyssafe(self):
        if os.path.exists("/www/server/panel/plugin/syssafe"):
            confile = "/www/server/panel/plugin/syssafe/config.json"
            conf = json.loads(public.readFile(confile))
            if "xargs" not in conf["process"]["process_white"]:
                return False
            return True
        else:
            return True


    def check_site_type(self,siteInfo):
        n = 0
        if os.path.exists(siteInfo['path'] + '/addons'): n += 1
        if os.path.exists(siteInfo['path'] + '/attachment'): n += 1
        if os.path.exists(siteInfo['path'] + '/data'): n += 1
        if os.path.exists(siteInfo['path'] + '/payment'): n += 1
        if n > 3: return False
        return True


    def site_reload(self,siteInfo):
        public.ExecShell("{} {} {}".format(public.get_python_bin(),self.__plugin_path + '/tamper_proof_service.py unlock',siteInfo['path']))
        tip_file = self.__plugin_path + '/tips/' + siteInfo['siteName'] + '.pl'
        if os.path.exists(tip_file): os.remove(tip_file)

    def add_excloud(self,get):
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        get.excludePath = get.excludePath.strip()
        if not get.excludePath: return public.returnMsg(False,'排除内容不能为空')

        errors=[]
        for excludePath in get.excludePath.split('\n'):
            if not excludePath: continue
            if excludePath.find('/') != -1:
                if not os.path.exists(excludePath):
                    errors.append(excludePath)
                    continue
            excludePath = excludePath.lower()
            if excludePath[-1] == '/': excludePath = get.excludePath[:-1]
            # return excludePath
            if excludePath in siteInfo['excludePath']: continue
            siteInfo['excludePath'].insert(0,excludePath)
            self.write_log('站点[%s]添加排除目录名[%s]到排除列表' % (siteInfo['siteName'],excludePath))
        if errors:
            return public.returnMsg(False, u'添加失败请文件夹不存在%s'%' , '.join(errors))
        self.site_reload(siteInfo)
        self.save_site_config(siteInfo)

        return public.returnMsg(True,u'添加成功!')

    def remove_excloud(self,get):
        siteInfo = self.get_site_find(get)
        get.excludePath = get.excludePath.strip()
        if not get.excludePath: return public.returnMsg(False,'排除文件或目录不能为空')
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        for excludePath in get.excludePath.split(','):
            if not excludePath: continue
            if not excludePath in siteInfo['excludePath']: continue
            siteInfo['excludePath'].remove(excludePath)
            self.write_log('站点[%s]从排除列表中删除目录名[%s]' % (siteInfo['siteName'],excludePath))
        self.site_reload(siteInfo)
        self.save_site_config(siteInfo)
        return public.returnMsg(True,u'删除成功!')

    def add_protect_ext(self,get):
        # if get.protectExt.find('.') != -1: return public.returnMsg(False,u'扩展名称不能包含[.]')
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        get.protectExt = get.protectExt.strip().lower()
        if not get.protectExt: return public.returnMsg(False,u'添加失败!')
        for protectExt in get.protectExt.split("\n"):
            if protectExt[0] == '/':
                if os.path.isdir(protectExt): continue
            if protectExt in siteInfo['protectExt']: continue
            siteInfo['protectExt'].insert(0,protectExt)
            self.write_log('站点[%s]添加文件类型或文件名[.%s]到受保护列表' % (siteInfo['siteName'],protectExt))
        self.site_reload(siteInfo)
        self.save_site_config(siteInfo)
        return public.returnMsg(True,u'添加成功!')

    def remove_protect_ext(self,get):
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        get.protectExt = get.protectExt.strip()
        if not get.protectExt: return public.returnMsg(False,'被删除的保护列表不能为空')
        for protectExt in get.protectExt.split(','):
            if not protectExt in siteInfo['protectExt']: continue
            siteInfo['protectExt'].remove(protectExt)
            self.write_log('站点[%s]从受保护列表中删除[.%s]' % (siteInfo['siteName'],protectExt))
        self.site_reload(siteInfo)
        self.save_site_config(siteInfo)
        return public.returnMsg(True,u'删除成功!')

    def sync_sites(self,get):
        data = self.get_sites(None)
        sites = public.M('sites').field('name,path').where("project_type=?",("PHP")).select()
        config = json.loads(public.readFile(self.__plugin_path + '/config.json'))
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
            data.append(siteInfo)
            n +=1

        newData = []
        for siteInfoTmp in data:
            if siteInfoTmp['siteName'] in names:
                newData.append(siteInfoTmp)
            else:
                public.ExecShell("rm -rf " + self.__plugin_path + '/sites/' + siteInfoTmp['siteName'])
                n+=1
        if n > 0: self.write_sites(newData)
        self.__sites = None

    def get_total(self,siteName = None,day=None):
        defaultTotal = {"total":0,"delete":0,"create":0,"modify":0,"move":0}
        if siteName:
            total = {}
            total['site'] = public.readFile(self.__plugin_path + '/sites/'+siteName+'/bt_tamper_proof_total/total.json')
            if total['site']: 
                total['site'] = json.loads(total['site'])
            else:
                total['site'] = defaultTotal
            if not day: day = time.strftime("%Y-%m-%d",time.localtime())
            total['day'] = public.readFile(self.__plugin_path + '/sites/'+siteName + '/bt_tamper_proof_total/' + day + '/total.json')
            if total['day']: 
                total['day'] = json.loads(total['day'])
            else:
                total['day'] = defaultTotal
        else:
            filename = self.__plugin_path + '/sites/total.json'
            if os.path.exists(filename):
                total = json.loads(public.readFile(filename))
            else:
                total = defaultTotal
        return total

    def get_days(self,path):
        days = []
        if not os.path.exists(path): os.makedirs(path)
        for dirname in os.listdir(path):
            if dirname == '..' or dirname == '.' or dirname == 'total.json': continue
            if not os.path.isdir(path + '/' + dirname): continue
            days.append(dirname)
        days = sorted(days,reverse=True)
        return days

    #取文件指定尾行数
    def GetNumLines(self,path,num,p=1):
        pyVersion = sys.version_info[0]
        try:
            import cgi
            if not os.path.exists(path): return ""
            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path,'rb')
            buf = ""
            fp.seek(-1, 2)
            if fp.read(1) == "\n": fp.seek(-1, 2)
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
                            except: pass
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
                            if type(t_buf) == bytes: t_buf = t_buf.decode('utf-8')
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break
            fp.close()
        except: return []
        if len(data) >= 2000:
            arr = []
            for d in data:
                arr.insert(0,json.dumps(d))
            public.writeFile(path,"\n".join(arr))
        return data


    def check_site_logs(self,get):
        ret=[]
        import datetime
        cur_month = datetime.datetime.now().month
        cur_day = datetime.datetime.now().day
        cur_year=datetime.datetime.now().year
        cur_hour = datetime.datetime.now().hour
        cur_minute= datetime.datetime.now().minute
        cur_second = datetime.datetime.now().second
        months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07',
                  'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
        logs_data=self.get_site_logs(get)
        if not logs_data:return False
        for i2 in logs_data:
            try:
                i = i2.split()
                # 判断状态码是否为200
                if int(i[8]) not in [200, 500]: continue
                # 判断是否为POST
                day_time = i[3].split('/')[0].split('[')[1]
                if int(cur_day) != int(day_time): continue
                month_time = i[3].split('/')[1]
                if int(months[month_time]) != int(cur_month): continue
                year_time = i[3].split('/')[2].split(':')[0]
                if int(year_time) != int(cur_year): continue
                hour_time = i[3].split('/')[2].split(':')[1]
                if int(hour_time) != int(cur_hour): continue
                minute_time = i[3].split('/')[2].split(':')[2]
                if int(minute_time) != int(cur_minute): continue
                second_time = int(i[3].split('/')[2].split(':')[3])
                if cur_second - second_time > 10: continue
                ret.append(i2)
            except:
                continue
        ret2=[]
        if len(ret) > 20:
            for i2 in logs_data:
                try:
                    i = i2.split()
                    if i[6] != 'POST': continue
                    if int(i[8]) not in [200, 500]: continue
                    # 判断是否为POST
                    day_time = i[3].split('/')[0].split('[')[1]
                    if int(cur_day) != int(day_time): continue
                    month_time = i[3].split('/')[1]
                    if int(months[month_time]) != int(cur_month): continue
                    year_time = i[3].split('/')[2].split(':')[0]
                    if int(year_time) != int(cur_year): continue
                    hour_time = i[3].split('/')[2].split(':')[1]
                    if int(hour_time) != int(cur_hour): continue
                    minute_time = i[3].split('/')[2].split(':')[2]
                    if int(minute_time) != int(cur_minute): continue
                    ret2.append(i2)
                except:
                    continue
        if ret2:
            ret=ret2
        if len(ret)>20:
            return ret[0:20]
        return ret

    def get_site_logs(self, get):
        try:
            import cgi
            pythonV = sys.version_info[0]
            path = '/www/wwwlogs/'+ get.siteName+'.log'
            num = 500
            if not os.path.exists(path): return []
            p = 1
            if 'p' in get:
                p = int(get.p)
            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path, 'rb')
            buf = ""
            try:
                fp.seek(-1, 2)
            except:
                return []
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            b = True
            n = 0
            c = 0
            while c < count:
                while True:
                    newline_pos = str.rfind(buf, "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            if line:
                                try:
                                    data.append(line)
                                except:
                                    c -= 1
                                    n -= 1
                                    pass
                            else:
                                c -= 1
                                n -= 1
                        buf = buf[:newline_pos]
                        n += 1
                        c += 1
                        break
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pythonV == 3: t_buf = t_buf.decode('utf-8', errors="ignore")
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break
            fp.close()
        except:
            data = []
        return data

    def get_safe_logs(self,get):
        data = {}
        path = self.__plugin_path + '/sites/'+get.siteName + '/bt_tamper_proof_total'
        data['days'] = self.get_days(path)
        if not data['days']:
            data['logs'] = []
        else:
            if not 'p' in get: get.p = 1
            day =  data['days'][0]
            if hasattr(get,'day'): day = get.day
            data['get_day'] = day
            data['logs'] = self.GetNumLines(path + '/' + day + '/logs.json',2000,int(get.p))
        return data

    def ClearDayLog(self,get):
        data = {}
        path = self.__plugin_path + '/sites/' + get.siteName + '/bt_tamper_proof_total'
        data['days'] = self.get_days(path)
        if get.day in data['days']:
            logpath = path+"/"+get.day+"/logs.json"
            if os.path.exists(logpath):
                public.ExecShell("echo ''> %s" % logpath)
                public.WriteLog('防篡改程序', logpath+" 防篡改日志清理成功")
                return public.returnMsg(True, u'清理成功!')
            else:
                return public.returnMsg(False, u'没有该日志文件!')


    def get_logs(self,get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?',(u'防篡改程序',)).count()
        limit = 12
        info = {}
        info['count'] = count
        info['row']   = limit
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']    = int(get['p'])
        info['uri']      = {}
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        data = {}
        data['page'] = page.GetPage(info,'1,2,3,4,5')
        data['data'] = public.M('logs').where('type=?',(u'防篡改程序',)).order('id desc').limit(str(page.SHIFT)+','+str(page.ROW)).field('log,addtime').select()
        return data

    def write_log(self,log):
        public.WriteLog('防篡改程序',log)


    def get_tamper_proof(self):
        from BTPanel import session, cache
        import panelAuth
        if self.__session_name in session: return session[self.__session_name]
        cloudUrl = public.GetConfigValue('home')+'/api/panel/get_soft_list'
        pdata = panelAuth.panelAuth().create_serverid(None)
        ret = public.httpPost(cloudUrl, pdata)
        if not ret:
            if not self.__session_name in session: session[self.__session_name] = 1
            return 1
        try:
            ret = json.loads(ret)
            for i in ret["list"]:
                if i['name'] == 'tamper_proof':
                    if i['endtime'] >= 0:
                        if not self.__session_name in session: session[self.__session_name] = 2
                        return 2
            if not self.__session_name in session: session[self.__session_name] = 0
            return 0
        except:
            if not self.__session_name in session: session[self.__session_name] = 1
            return 1
        # stop config

    def stop(self):
        public.ExecShell('/etc/init.d/bt_tamper_proof stop')
        try:
            version = public.version()
            rcnlist = public.httpGet(public.GetConfigValue('home')+'/api/panel/notpro?version=%s' % version)
        except:
            pass
        return True
    def stop_nps(self, get):
        public.WriteFile("data/tamper_proof_nps.pl", "")
        return public.returnMsg(True, '关闭成功')

    def get_nps_questions(self):
        try:
            import requests
            api_url = public.GetConfigValue('home')+'/panel/notpro'
            user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
            data = {
                "uid": user_info['uid'],
                "access_key": user_info['access_key'],
                "serverid": user_info['serverid'],
                "product_type": 3
            }

            result = requests.post(api_url, data=data, timeout=10).json()
            if result['res']:
                public.WriteFile('data/get_nps_questions.json', json.dumps(result['res']))
        except:
            public.WriteFile('data/get_nps_questions.json', json.dumps([{
                "id": "NKORxSVqUMjc0YjczNTUyMDFioPLiIoT",
                "question": "当初购买防火墙是解决什么问题？什么事件触发的？",
                "hint": "如：购买时是想预防网站以后被攻击。",
                "required": 1
            }, {
                "id": "dFMoTKffBMmM0YjczNTUyMDM0HugtbUY",
                "question": "您在使用防火墙过程中出现最多的问题是什么？",
                "hint": "如：开启后还是被入侵，然后后续怎么去处理？",
                "required": 1
            }, {
                "id": "dnWeQbiHJMmI4YjczNTUyMDJhurmpsfs",
                "question": "谈谈您对防火墙的建议。",
                "hint": "如：我希望防火墙能防御多台服务器。天马行空，说说您的想法。",
                "required": 1
            }]))


    def get_nps(self, get):
        data = {}
        data['safe_day'] = 0
        time_path="/www/server/panel/plugin/tamper_proof/install_time.pl"
        insta_time=0
        if not  os.path.exists(time_path):
            public.writeFile(time_path,str(int(time.time())))
            
        else:
            try:
                insta_time=int(public.ReadFile(time_path))
            except:
                public.writeFile(time_path,str(int(time.time())))
                insta_time=0
        if insta_time != 0: data['safe_day'] = int((time.time() - insta_time) / 86400)
        if not os.path.exists("data/tamper_proof_nps.pl"):
            # 如果安全运行天数大于5天 并且没有没有填写过nps的信息
            data['nps'] = False
            public.run_thread(self.get_nps_questions, ())
            if os.path.exists("data/tamper_proof_nps_count.pl"):
                # 读取一下次数
                count = public.ReadFile("data/tamper_proof_nps_count.pl")
                if count:
                    count = int(count)
                    public.WriteFile("data/tamper_proof_nps_count.pl", str(count + 1))
                    data['nps_count'] = count + 1
            else:
                public.WriteFile("data/tamper_proof_nps_count.pl", "1")
                data['nps_count'] = 1
        else:
            data['nps'] = True
        return data

    def write_nps(self, get):
        '''
            @name nps 提交
            @param rate 评分
            @param feedback 反馈内容

        '''
        import json, requests
        api_url = public.GetConfigValue('home')+'/panel/notpro'
        user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
        if 'rate' not in get:
            return public.returnMsg(False, "参数错误")
        if 'feedback' not in get:
            get.feedback = ""
        if 'phone_back' not in get:
            get.phone_back = 0
        else:
            if get.phone_back == 1:
                get.phone_back = 1
            else:
                get.phone_back = 0

        if 'questions' not in get:
            return public.returnMsg(False, "参数错误")

        try:
            get.questions = json.loads(get.questions)
        except:
            return public.returnMsg(False, "参数错误")

        data = {
            "uid": user_info['uid'],
            "access_key": user_info['access_key'],
            "serverid": user_info['serverid'],
            "product_type": 3,
            "rate": get.rate,
            "feedback": get.feedback,
            "phone_back": get.phone_back,
            "questions": json.dumps(get.questions)
        }
        try:
            requests.post(api_url, data=data, timeout=10).json()
            public.WriteFile("data/tamper_proof_nps.pl", "1")
        except:
            pass
        return public.returnMsg(True, "提交成功")
