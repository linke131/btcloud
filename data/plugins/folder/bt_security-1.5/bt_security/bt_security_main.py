# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkq <lkq@bt.com>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔防提权
# +--------------------------------------------------------------------
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, json,time,re
if __name__ != '__main__':
    from panelAuth import panelAuth

class bt_security_main:
    __session_name = None
    __etc='/usr/local/usranalyse/etc/usranalyse.ini'
    __lib='/usr/local/usranalyse/lib/libusranalyse.so'
    __disable='/usr/local/usranalyse/sbin/usranalyse-disable'
    __ensable='/usr/local/usranalyse/sbin/usranalyse-enable'
    __log='/usr/local/usranalyse/logs/'
    __security_path='/www/server/panel/plugin/bt_security'
    __user_data=None
    __bt_security='/etc/ld.so.preload'
    __to_msg='/www/server/panel/plugin/bt_security/msg.conf'

    def __init__(self):
        pass

    '''判断是否存在日志目录'''
    def check_log_file(self,get):
        if not os.path.exists(self.__log+'log/root'):
            os.system('mkdir -p %s && chmod 777 %s'%(self.__log+'log/root',self.__log+'log'))
            os.system('chmod 700 %s' % (self.__log + 'log/root'))
        data=self.system_user(get)
        for i in data:
            if i[0]=='mysql' or i[0]=='www' or i[0]=='redis':
                if not os.path.exists(self.__log+'log/'+i[0]):
                    os.system('mkdir -p %s && chmod 777 %s ' % (self.__log+'log/'+i[0], self.__log+'log/'+i[0]))
        if not os.path.exists(self.__log + 'total/root'):
            os.system('mkdir -p %s && chmod 777 %s' % (self.__log + 'total/root', self.__log + 'total'))
            os.system('chmod 700 %s' % (self.__log + 'total/root'))
        data = self.system_user(get)
        for i in data:
            if i[0] == 'mysql' or i[0] == 'www' or i[0] == 'redis':
                if not os.path.exists(self.__log + 'total/' + i[0]):
                    os.system('mkdir -p %s && chmod 777 %s ' % (self.__log + 'total/' + i[0], self.__log + 'total/' + i[0]))
        for i in self.system_user(get):
            self.mkdir_user_path(i[0])
        return True

    '''建立用户的统计目录和日志记录'''
    def mkdir_user_path(self,user):
        if not os.path.exists(self.__log+'/log/'+user):
            os.system('mkdir -p %s && chmod 777 %s'%(self.__log+'/log/'+user,self.__log+'/log/'+user))
        if not os.path.exists(self.__log+'/total/'+user):
            os.system('mkdir -p %s && chmod 777 %s' % (self.__log + '/total/' + user, self.__log + '/total/' + user))

    #验证文件的完整性
    def check_file(self):
        if os.path.exists(self.__etc) and os.path.exists(self.__lib) and os.path.exists(self.__disable) and os.path.exists(self.__ensable):
            return True
        return False

    '''
    验证是否购买, 2为购买 1 为需要再次确认 0 未购买 
    '''
    def get_bt_security_drive(self):
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
                if i['name'] == 'bt_security':
                    if i['endtime'] >= 0:
                        session[self.__session_name] = 2
                        return 2
            return 0
        except:
            session[self.__session_name] = 1
            return 1

    '''读取用户信息'''
    def system_user(self,get):
        if not os.path.exists('/etc/passwd'):return  []
        user_data=open('/etc/passwd','r')
        ret=[]
        for i in user_data:
            if i:
                i=i.strip().split(':')
                if len(i)<4:continue
                ret2=[]
                ret2.append(i[0])
                ret2.append(i[2])
                ret2.append(i[-1])
                ret.append(ret2)
        return  ret

    '''查看天数跟总的次数'''
    def get_day(self,get):
        try:
            if not  os.path.exists(self.__security_path+'/day.json'):
                public.writeFile(self.__security_path + '/day.json', {"day": int(time.time())})
                day=0
            else:
                day=json.loads(public.ReadFile(self.__security_path+'/day.json'))['day']
                day=int((int(time.time())-day)/86400)
        except:
            public.writeFile(self.__security_path+'/day.json',{"day":int(time.time())})
            day=0
        #获取总的次数
        if os.path.exists(self.__log+'total/total.txt'):
            ret=public.ReadFile(self.__log+'total/total.txt')
            data=re.findall('total=(\d+)',ret)
            if not data:totla=0
            try:
                totla=int(data[0])
            except:
                totla = 0
        else:
            totla=0
        return {'day':day,'totla':totla}

    '''判断这个用户是否开启'''
    def check_open_user(self,uid):
        if not os.path.exists(self.__etc):return False
        user_etc=public.ReadFile(self.__etc)
        if re.search('\nuserstop_chain = "stop_uid:(.+)"', user_etc):
            user_data=re.search('\nuserstop_chain = "stop_uid:(.+)"', user_etc).group(1).split(',')

            if uid in user_data:return True
        else:
            if  re.search('\nuserstop_chain = "stop_uid:"', user_etc):return False
            #获取不到。说明配置文件有问题
            user_etc=re.sub('\noutput = file:/usr/local/usranalyse/logs','\noutput = file:/usr/local/usranalyse/logs\nuserstop_chain = "stop_uid:www,redis,mysql"\n',user_etc)
            public.ReadFile(self.__etc,user_etc)
            if uid in ['www','mysql','redis']: return True
        return False

    '''统计用户'''
    def get_user_totla(self,uid,day):
        ret={'totla':0,"day_totla":0}
        if not os.path.exists(self.__log+'total/'+uid):return ret
        if not os.path.exists(self.__log+'total/'+uid+'/total.txt'):
            return ret
        else:
            ret3 = public.ReadFile(self.__log+'total/'+uid+'/total.txt')
            data = re.findall('total=(\d+)', ret3)
            if not data: totla = 0
            try:
                totla = int(data[0])
            except:
                totla = 0
        if not os.path.exists(self.__log + 'total/' + uid + '/'+day+'.txt'):
            day_totla=0
        else:
            ret2 = public.ReadFile(self.__log + 'total/' + uid + '/'+day+'.txt')
            data = re.findall('total=(\d+)', ret2)
            if not data: day_totla = 0
            try:
                day_totla = int(data[0])
            except:
                day_totla = 0
        ret = {'totla': totla, "day_totla": day_totla}
        return ret

    '''处理时间'''
    def check_day(self,day):
        day=day.split('-')
        if day[1][0]=='0':
            day[1]=day[1][1]
        if day[2][0]=='0':
            day[2]=day[2][1]
        return '-'.join(day)

    '''查看用户是否开启日志'''
    def _check_user_log(self,uid):
        if not os.path.exists(self.__etc): return True
        user_etc = public.ReadFile(self.__etc)
        if re.search('\nfilter_chain = ".+;exclude_uid:(.+)"', user_etc):
            user_data = re.search('\nfilter_chain = ".+;exclude_uid:(.+)"', user_etc).group(1).split(',')
            if uid in user_data: return False
        else:
            if re.search('\nfilter_chain = ".+;exclude_uid:"', user_etc):
                return True
        return True

    '''判断是否存在这个uid'''
    def _check_uid(self,uid):
        for i in self.system_user(None):
            if i[1]==uid:return True
        return False

    '''获取日志列表 and  获取禁止的列表'''
    def get_exid_expr(self,user_etc):
        ex_pr = []
        ex_id=[]
        if not re.search('\nfilter_chain = "exclude_spawns_of:.+',user_etc):
            user_etc2 = re.sub('\noutput = file:/usr/local/usranalyse/logs',
                              '\noutput = file:/usr/local/usranalyse/logs\nfilter_chain = "exclude_spawns_of:crond;exclude_uid:"\n',
                              user_etc)
            public.writeFile(self.__etc, user_etc2)
            return {"ex_id":ex_id,"ex_pr":ex_pr,"user_etc":user_etc2}
        if re.search('\nfilter_chain = "exclude_spawns_of:(.+);exclude_uid:',user_etc):
            ex_pr=re.search('\nfilter_chain = "exclude_spawns_of:(.+);exclude_uid:', user_etc).group(1).split(',')
        else:
            if re.search('\nfilter_chain = "exclude_spawns_of:;exclude_uid:', user_etc):
                ex_pr=[]
        if re.search('\nfilter_chain = "exclude_spawns_of:.+;exclude_uid:(.+)"',user_etc):
            ex_id=re.search('\nfilter_chain = "exclude_spawns_of:.+;exclude_uid:(.+)"', user_etc).group(1).split(',')

        if re.search('\nfilter_chain = "exclude_spawns_of:;exclude_uid:(.+)"', user_etc):
            ex_id = re.search('\nfilter_chain = "exclude_spawns_of:;exclude_uid:(.+)"', user_etc).group(1).split(',')

        if re.search('\nfilter_chain = "exclude_spawns_of:.+;exclude_uid:"', user_etc):
            ex_id = []
        if re.search('\nfilter_chain = "exclude_spawns_of:;exclude_uid:"', user_etc):
            ex_id = []
        return {"ex_id":ex_id,"ex_pr":ex_pr,"user_etc":user_etc}

    '''关闭用户日志'''
    def stop_user_log(self,get):
        '''参数一个 uid'''
        if not 'uid' in get:return public.returnMsg(False,'请传递uid')
        uid=get.uid.strip()
        if not self._check_uid(uid):return public.returnMsg(False,'请传递正确的uid')
        if not os.path.exists(self.__etc): return public.returnMsg(False,'配置文件错误')
        user_etc = public.ReadFile(self.__etc)
        user_data=self.get_exid_expr(user_etc)
        user_data2=[]
        if uid in user_data['ex_id']:return public.returnMsg(False,'已经存在,请勿重复提交')
        [user_data2.append(x) for x in user_data['ex_id']]
        user_data2.append(uid)
        user_data['user_etc'] = re.sub('\nfilter_chain = "exclude_spawns_of:%s;exclude_uid:%s"' %(','.join(user_data['ex_pr']),','.join(user_data['ex_id'])),
                          '\nfilter_chain = "exclude_spawns_of:%s;exclude_uid:%s"' %(','.join(user_data['ex_pr']),','.join(user_data2)), user_data['user_etc'])
        public.writeFile(self.__etc, user_data['user_etc'])
        return public.returnMsg(True, '关闭成功')

    '''开启用户日志'''
    def start_user_log(self,get):
        '''uid'''
        if not 'uid' in get:return public.returnMsg(False,'请传递uid')
        uid=get.uid.strip()
        if not self._check_uid(uid):return public.returnMsg(False,'请传递正确的uid')
        if not os.path.exists(self.__etc): return public.returnMsg(False,'配置文件错误')
        user_etc = public.ReadFile(self.__etc)
        user_data=self.get_exid_expr(user_etc)
        user_data2=[]
        if not uid in user_data['ex_id']: return public.returnMsg(False, '当前用户已开启,请勿重复提交')
        for i in user_data['ex_id']:
            if i == uid: continue
            user_data2.append(i)
        user_data['user_etc'] = re.sub('\nfilter_chain = "exclude_spawns_of:%s;exclude_uid:%s"' %(','.join(user_data['ex_pr']),','.join(user_data['ex_id'])),
                          '\nfilter_chain = "exclude_spawns_of:%s;exclude_uid:%s"' %(','.join(user_data['ex_pr']),','.join(user_data2)), user_data['user_etc'])
        public.writeFile(self.__etc, user_data['user_etc'])
        return public.returnMsg(True, '开启成功')

    def ps(self,uid):
        if uid[0]=='root':return '系统管理员用户(可登陆)'
        if uid[1]=='0':return '系统管理员用户(可登陆)'
        if uid[0]=='www':return 'web启动用户(不可登陆)'
        if uid[0] == 'mysql': return 'Mysql用户(不可登陆)'
        if uid[0] == 'redis': return 'Redis用户(不可登陆)'
        if uid[2] =='/bin/bash':return '%s用户(可登陆)'%uid[0]
        else:
            return '%s用户(不可登陆)' % uid[0]

    '''每个用户的总次数/每日次数'''
    def user_totla(self,get):
        if not 'day' in get: get.day = time.strftime("%Y-%m-%d", time.localtime())
        system_user=self.system_user(get)
        for i in system_user:
            data=self.get_user_totla(i[0],self.check_day(get.day))
            i.append(self.check_open_user(i[0]))
            i.append(data)
            i.append(self._check_user_log(i[1]))
            i.append(self.ps(i))

        return sorted(system_user, key=lambda x: x[4]['totla'], reverse=True)

    '''查看是否开启防提权'''
    def get_bt_security(self,get):
        data=public.ReadFile(self.__bt_security)
        if re.search(self.__lib,data):
            return True
        return False

    '''关闭防提权'''
    def stop_bt_security(self,get):
        if not os.path.exists(self.__lib):return public.returnMsg(False, '防提权文件丢失,请卸载重新安装后尝试')
        data = public.ReadFile(self.__bt_security)
        if not re.search(self.__lib, data):
            self.__write_log('关闭防提权总开关成功')
            return public.returnMsg(True, '关闭成功')
        if os.path.exists(self.__disable):
            os.system(self.__disable)
            if not re.search(self.__lib, data):
                self.__write_log('关闭防提权总开关成功')
                return public.returnMsg(True, '关闭成功')
            else:
                data=re.sub(self.__lib,'',data)
                public.writeFile(self.__bt_security,data)
                self.__write_log('关闭防提权总开关成功')
                return public.returnMsg(True, '关闭成功')
        else:
            data=re.sub(self.__lib, '', data)
            public.writeFile(self.__bt_security, data)
            self.__write_log('关闭防提权总开关成功')
            return public.returnMsg(True, '关闭成功')

    '''开启防提权'''
    def start_bt_security(self,get):
        if not os.path.exists(self.__lib):return public.returnMsg(False, '防提权文件丢失,请卸载重新安装后尝试')
        data2 = public.ReadFile(self.__bt_security)
        if re.search(self.__lib, data2):
            self.__write_log('开启防提权总开关成功')
            return public.returnMsg(True, '开启成功')
        if os.path.exists(self.__ensable):
            os.system(self.__ensable)
            data = public.ReadFile(self.__bt_security)
            if re.search(self.__lib, data):
                self.__write_log('开启防提权总开关成功')
                return public.returnMsg(True, '开启成功')
            else:
                public.writeFile(self.__bt_security,self.__lib)
                self.__write_log('开启防提权总开关成功')
                return public.returnMsg(True, '开启成功')
        else:
            public.writeFile(self.__bt_security, self.__lib)
            self.__write_log('开启防提权总开关成功')
            return public.returnMsg(True, '开启成功')
    '''
    显示统计/每天/总/日志
    '''
    def get_total_all(self,get):
        if not self.check_file():return  {"status":False,"msg":"本插件未安装成功,建议卸载重新安装"}
        self.check_log_file(get)
        if not 'day' in get:get.day=time.strftime("%Y-%m-%d", time.localtime())
        ret={}
        ret['totla_days']=self.get_day(get)['day']
        ret['totla_times'] = self.get_day(get)['totla']
        ret['system_user']=self.user_totla(get)
        ret['open']=self.get_bt_security(get)
        ret['status']=True
        return ret

    '''获取当前用户的日志日期'''
    def get_logs_list(self, get):
        path = '/usr/local/usranalyse/logs/log/'+get.user
        if not os.path.exists(path):return []
        data = []
        for fname in os.listdir(path):
            if re.search('(\d+-\d+-\d+).txt$',fname):
                tmp = fname.replace('.txt', '')
                data.append(tmp)
        return sorted(data, reverse=True)

    '''获取用户的日志'''
    def get_safe_logs(self, path,p=1,num=11):
        try:
            import cgi
            pythonV = sys.version_info[0]
            if not os.path.exists(path): return '111';
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
            for i in range(count):
                while True:
                    newline_pos = str.rfind(buf, "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            try:
                                tmp_data = json.loads(cgi.escape(line))
                                data.append(tmp_data)
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
                        if pythonV == 3: t_buf = t_buf.decode('utf-8')
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break;
            fp.close()
        except:
            data = []
        return data

    def get_user_log(self,get):
        '''
        四个参数 user  day
        user --> 用户
        day---> 时间  2020-06-01
        p ---> 页数
        num -->数量
        '''
        if not 'day' in get: get.day = time.strftime("%Y-%m-%d", time.localtime())
        user=get.user.strip()
        path=self.__log+'log/'+user+'/'+self.check_day(get.day)+'.txt'
        if not os.path.exists(path):
            return []
        if not 'p' in get:get.p=1
        if not 'num'in get:get.num=10
        return self.get_safe_logs(path=path,p=int(get.p),num=int(get.num))



    '''验证用户是否是root'''
    def _check_user(self,user):
        system_user = self.system_user(None)
        for i in system_user:
            if i[0] == user:
                if i[1]=='0':return True
        return False

    '''用户开启防提权'''
    def start_user_security(self,get):
        '''
        参数一个
        用户名-->user
        '''
        user_data2=[]
        if not 'user' in get:return  public.returnMsg(False,'请选择用户')
        if get.user.strip()=='root':return  public.returnMsg(False,'root用户不需要开启防提权,默认记录了日志')
        if self._check_user(get.user.strip()):return  public.returnMsg(False,'root用户不需要开启防提权,默认记录了日志')
        user_etc = public.ReadFile(self.__etc)
        if re.search('\nuserstop_chain = "stop_uid:(.+)"', user_etc):
            user_data = re.search('\nuserstop_chain = "stop_uid:(.+)"', user_etc).group(1).split(',')
            if get.user.strip() in user_data:return  public.returnMsg(False,'当前用户已经开启了防提权')
            [user_data2.append(x) for x in user_data]
            user_data2.append(get.user.strip())
            user_etc=re.sub('\nuserstop_chain = "stop_uid:%s"'%','.join(user_data),'\nuserstop_chain = "stop_uid:%s"'%','.join(user_data2),user_etc)
            public.writeFile(self.__etc,user_etc)

            return public.returnMsg(True, '开启成功')
        else:
            if not re.search('\noutput = file:/usr/local/usranalyse/logs',user_etc):return  public.returnMsg(False,'配置文件错误,请卸载重新安装防提权')
            if re.search('\nuserstop_chain = "stop_uid:"', user_etc):
                user_etc = re.sub('\nuserstop_chain = "stop_uid:"',
                                  '\nuserstop_chain = "stop_uid:%s"' %get.user.strip(), user_etc)
                public.writeFile(self.__etc, user_etc)
                return public.returnMsg(True, '开启成功')
            else:
                user_etc = re.sub('\noutput = file:/usr/local/usranalyse/logs',
                                  '\noutput = file:/usr/local/usranalyse/logs\nuserstop_chain = "stop_uid:www,redis,mysql%s"\n'%get.user.strip(),
                                  user_etc)
                public.writeFile(self.__etc, user_etc)
                self.__write_log('开启防提权成功')
                return public.returnMsg(True, '开启成功')

    '''关闭防提权'''
    def stop_user_security(self,get):
        '''
        用户名-->user
        '''
        user_data2 = []
        if not 'user' in get: return public.returnMsg(False, '请选择用户')
        if get.user.strip() == 'root': return public.returnMsg(False, 'root用户不需要关闭防提权,默认记录了日志')
        if self._check_user(get.user.strip()): return public.returnMsg(False, 'root用户不需要关闭防提权,默认记录了日志')
        user_etc = public.ReadFile(self.__etc)
        if re.search('\nuserstop_chain = "stop_uid:(.+)"', user_etc):
            user_data = re.search('\nuserstop_chain = "stop_uid:(.+)"', user_etc).group(1).split(',')
            if not get.user.strip() in user_data:return  public.returnMsg(False,'当前用户未开启防提权')
            for i in user_data:
                if i==get.user.strip():continue
                user_data2.append(i)
            user_etc=re.sub('\nuserstop_chain = "stop_uid:%s"'%','.join(user_data),'\nuserstop_chain = "stop_uid:%s"'%','.join(user_data2),user_etc)
            public.writeFile(self.__etc,user_etc)
            return public.returnMsg(True, '关闭成功')
        else:
            if not re.search('\noutput = file:/usr/local/usranalyse/logs',user_etc):return  public.returnMsg(False,'配置文件错误,请卸载重新安装防提权')
            if re.search('\nuserstop_chain = "stop_uid:"', user_etc):
                return public.returnMsg(True, '关闭成功')
            else:
                user_etc = re.sub('\noutput = file:/usr/local/usranalyse/logs',
                                  '\noutput = file:/usr/local/usranalyse/logs\nuserstop_chain = "stop_uid:www,redis,mysql%s"\n'%get.user.strip(),
                                  user_etc)
                public.writeFile(self.__etc, user_etc)
                self.__write_log('关闭防提权成功')
                return public.returnMsg(True, '关闭成功')

    '''过滤进程记录'''
    def porcess_set_up_log(self,get):
        user_etc = public.ReadFile(self.__etc)
        user_data = self.get_exid_expr(user_etc)
        return user_data['ex_pr']

    '''添加进程'''
    def add_porcess_log(self,get):
        if not 'cmd' in get: return public.returnMsg(False, '请输入你需要添加的进程名')
        cmd = get.cmd.strip()
        user_data2 = []
        user_etc = public.ReadFile(self.__etc)
        user_data=self.get_exid_expr(user_etc)
        if cmd in user_data['ex_pr']:return public.returnMsg(False,'已经存在,请勿重复提交')
        [user_data2.append(x) for x in user_data['ex_pr']]
        user_data2.append(cmd)
        user_data['user_etc'] = re.sub('\nfilter_chain = "exclude_spawns_of:%s;exclude_uid:%s"' %(','.join(user_data['ex_pr']),','.join(user_data['ex_id'])),
                          '\nfilter_chain = "exclude_spawns_of:%s;exclude_uid:%s"' %(','.join(user_data2),','.join(user_data['ex_id'])), user_data['user_etc'])
        public.writeFile(self.__etc, user_data['user_etc'])
        self.__write_log('添加进程%s成功' % cmd)
        return public.returnMsg(True, '添加成功')


    '''删除进程'''
    def del_porcess_log(self,get):
        if not 'cmd' in get: return public.returnMsg(False, '请输入你需要添加的进程名')
        cmd=get.cmd.strip()
        user_data2 = []
        user_etc = public.ReadFile(self.__etc)
        user_data=self.get_exid_expr(user_etc)
        if not  cmd in user_data['ex_pr']:return public.returnMsg(False,'不存在')
        for i in user_data['ex_pr']:
            if i == cmd: continue
            user_data2.append(i)
        user_data['user_etc'] = re.sub('\nfilter_chain = "exclude_spawns_of:%s;exclude_uid:%s"' %(','.join(user_data['ex_pr']),','.join(user_data['ex_id'])),
                          '\nfilter_chain = "exclude_spawns_of:%s;exclude_uid:%s"' %(','.join(user_data2),','.join(user_data['ex_id'])), user_data['user_etc'])
        public.writeFile(self.__etc, user_data['user_etc'])
        self.__write_log('删除进程%s成功'%cmd)
        return public.returnMsg(True, '删除成功')

    '''报警开关'''
    def get_send_status(self,get):
        if not os.path.exists(self.__to_msg):
            public.writeFile(self.__to_msg, json.dumps({"open":False,'to_mail':False}))
            return {"open":False,'to_mail':False}
        try:
            msg_conf=json.loads(public.ReadFile(self.__to_msg))
            return public.returnMsg(True,msg_conf)
        except:
            public.writeFile(self.__to_msg,json.dumps({"open":False,'to_mail':False}))
            return {"open":False,'to_mail':False}

    '''报警设置'''
    def set_mail_to(self,get):
        public.writeFile(self.__to_msg, json.dumps({"open": True, 'to_mail': 'mail'}))
        self.__write_log('开启成功邮件告警成功')
        return public.returnMsg(True, '开启成功')

    '''钉钉'''
    def set_dingding(self,get):
        public.writeFile(self.__to_msg, json.dumps({"open": True, 'to_mail': 'dingding'}))
        self.__write_log('开启成功钉钉告警成功')
        return public.returnMsg(True, '开启成功')

    def check_status(self,get):
        '验证是否拦截'
        www_path='/usr/local/usranalyse/logs/total/www/total.txt'
        if not os.path.exists(www_path):
            www_coun=0
        else:
            ret2 = public.ReadFile('/usr/local/usranalyse/logs/total/www/total.txt')
            if not re.search('total=(\d+)', ret2):www_coun = 0
            data = re.findall('total=(\d+)', ret2)
            if not data:
                www_coun = 0
            try:
                www_coun = int(data[0])
            except:
                www_coun = 0
        public.ExecShell('cd /tmp && whoami',user='www')
        if os.path.exists('/usr/local/usranalyse/logs/total/www/total.txt'):
            www_coun2=0
        ret = public.ReadFile('/usr/local/usranalyse/logs/total/www/total.txt')
        if not ret:return public.returnMsg(False,'防提权测试失败,可能是未开启防提权,或者www用户未开启防提权')
        if not re.search('total=(\d+)', ret): www_coun = 0
        data = re.findall('total=(\d+)', ret)
        if not data: www_coun2 = 0
        try:
            www_coun2 = int(data[0])
        except:
            www_coun2 = 0
        if www_coun2==www_coun:
            self.__write_log('防提权测试失败,可能是未开启防提权,或者www用户未开启防提权')
            return public.returnMsg(False,'防提权测试失败,可能是未开启防提权,或者www用户未开启防提权')
        self.__write_log('防提权测试防护成功,www用户执行命令了nologin命令,记录并增加一条')
        return public.returnMsg(True,'防提权测试防护成功,www用户执行命令了nologin命令,记录并增加一条')

    def __write_log(self, msg):
        public.WriteLog('防提权', msg)

    #报警日志
    def get_log_send(self,get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (u'防提权告警',)).count()
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
        data['data'] = public.M('logs').where('type=?', (u'防提权告警',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select();
        return data

    #报警日志
    def get_log(self,get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (u'防提权',)).count()
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
        data['data'] = public.M('logs').where('type=?', (u'防提权',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data