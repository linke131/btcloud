#!/usr/bin/python
#coding: utf-8
#-----------------------------
# PM2管理插件
#-----------------------------
import sys,os,psutil,time
os.chdir('/www/server/panel')
sys.path.append("class/")
import public,re,json

class pm2_main:
    __SR = None
    __log_path = '/www/wwwlogs/pm2'
    __path = '/www/server/panel/plugin/pm2/list/'
    
    def __init__(self):
        if not os.path.exists(self.__log_path):
            os.makedirs(self.__log_path)
            public.ExecShell("chown -R www:www {}".format(self.__log_path))
        s_path = '/www'
        if os.path.islink(s_path):
            s_path=os.readlink(s_path) + '/server'
        else:
            s_path += '/server'
            if os.path.islink(s_path):
                s_path = os.readlink(s_path)
        self.__SR = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export HOME=/root
export NVM_NODEJS_ORG_MIRROR=http://npm.taobao.org/mirrors/node
export NVM_DIR="{}/nvm"
source /www/server/nvm/nvm.sh
npm config set registry https://registry.npm.taobao.org
'''.format(s_path)


    def get_show_info(self,args):
        '''
            @name 获取项目详细信息
            @author hwliang<2021-04-08>
            @param args<dict_obj{
                pname: string<项目名称>
            }>
            @return dict
        '''
        if not 'pname' in args: return public.returnMsg(False,'缺少参数!')
        pname = args.pname.strip()
        result = public.ExecShell(self.__SR + "pm2 show {}".format(pname))[0]
        result_line  = result.split("\n")
        pdata = {}
        for r_line in result_line:
            r_line = r_line.strip()
            if not r_line: continue
            if r_line.find('─') != -1: continue
            if r_line[0] != '│': continue
            line_arr = r_line.split("│")
            if len(line_arr) < 3: continue
            key = line_arr[1].strip()
            val = line_arr[2].strip()
            if not key or not val: continue
            pdata[key] = val
        return pdata

    
    def get_object_find(self,args):
        '''
            @name 获取指定项目配置信息
            @author hwliang<2021-04-08>
            @param args<dict_obj{
                pname: string<项目名称>
            }>
            @return dict
        '''

        json_file = self.__path + args.pname + '.json'
        if not os.path.exists(json_file):
            return public.returnMsg(False,'项目配置文件不存在，请尝试刷新项目列表后重试')
        data = json.loads(public.readFile(json_file))
        return data


    def get_modules(self,args):
        '''
            @name 获取指定项目当前已安装的模块信息
            @author hwliang<2021-04-08>
            @param args<dict_obj{
                path: string<项目路径>
            }>
            @return list
        '''
        if not 'path' in args: return public.returnMsg(False,'缺少参数!')
        mod_path = os.path.join(args.path,'node_modules')
        modules = []
        if not os.path.exists(mod_path): return modules
        for mod_name in os.listdir(mod_path):
            try:
                mod_pack_file = os.path.join(mod_path,mod_name,'package.json')
                if not os.path.exists(mod_pack_file): continue
                mod_pack_info = json.loads(public.readFile(mod_pack_file))
                pack_info = {
                    "name": mod_name, 
                    "version": mod_pack_info['version'],
                    "description":mod_pack_info['description'],
                    "license": mod_pack_info['license'] if 'license' in mod_pack_info else 'NULL',
                    "homepage": mod_pack_info['homepage']
                    }
                modules.append(pack_info)
            except:
                continue
        return modules

    def install_module(self,args):
        '''
            @name 安装指定模块
            @author hwliang<2021-04-08>
            @param args<dict_obj{
                path: string<项目路径>
                mod_name: string<模块名称>
            }>
            @return dict
        '''
        filename = '{}/node_modules/{}/package.json'.format(args.path,args.mod_name)
        if os.path.exists(filename): return public.returnMsg(False,'指定模块已经安装过了!')
        public.ExecShell(self.__SR + 'cd {} && npm install {} &> /tmp/pm2_mod.log'.format(args.path,args.mod_name))
        if not os.path.exists(filename):
            return public.returnMsg(False,public.readFile('/tmp/pm2_mod.log'))
        return public.returnMsg(True,'安装成功!')


    def install_package_all(self,args):
        '''
            @name 一键安装packages
            @author hwliang<2021-04-08>
            @param args<dict_obj{
                path: string<项目路径>
                mod_name: string<模块名称>
            }>
            @return dict
        '''
        if not os.path.exists(args.path + '/package.json'):
            return public.returnMsg(False,'在项目根目录没有找到package.json配置文件')
        if not os.path.exists(args.path + '/package-lock.json'):
            os.remove(args.path + '/package-lock.json')
        
        result = public.ExecShell(self.__SR + "cd " + args.path + ' && npm install -s')
        if result[1]:
            return public.returnMsg(False,result[1])
        return public.returnMsg(True,'已完成所有依赖安装!')

    def uninstall_module(self,args):
        '''
            @name 卸载指定模块
            @author hwliang<2021-04-08>
            @param args<dict_obj{
                path: string<项目路径>
                mod_name: string<模块名称>
            }>
            @return dict
        '''
        filename = '{}/node_modules/{}/package.json'.format(args.path,args.mod_name)
        if not os.path.exists(filename): return public.returnMsg(False,'指定模块未安装!')
        public.ExecShell(self.__SR + 'cd {} && npm uninstall {} &> /tmp/pm2_mod.log'.format(args.path,args.mod_name))
        if os.path.exists(filename):
            return public.returnMsg(False,public.readFile('/tmp/pm2_mod.log'))
        return public.returnMsg(True,'卸载成功!')

    def clean_object_logs(self,args):
        '''
            @name 清除项目日志
            @author hwliang<2021-04-08>
            @param args<dict_obj{
                pname: string<项目名称>
                log_type: string<日志类型> out|error 
            }>
            @return string
        '''
        if not 'pname' in args: return public.returnMsg(False,'缺少参数!')
        if not 'log_type' in args: return public.returnMsg(False,'缺少参数!')
        log_file = '{}/{}-{}.log'.format(self.__log_path,args.pname,args.log_type)
        if not os.path.exists(log_file):
            log_file = '/root/.pm2/logs/{}-{}.log'.format(args.pname,args.log_type)
            if not os.path.exists(log_file): return public.returnMsg(False,'指定日志不存在!') 
        public.writeFile(log_file,'')
        return public.returnMsg(True,'日志已清空!')
        


    def get_object_logs(self,args):
        '''
            @name 获取指定项目当前已安装的模块信息
            @author hwliang<2021-04-08>
            @param args<dict_obj{
                pname: string<项目名称>
                log_type: string<日志类型> out|error 
            }>
            @return string
        '''
        if not 'pname' in args: return public.returnMsg(False,'缺少参数!')
        if not 'log_type' in args: return public.returnMsg(False,'缺少参数!')
        log_file = '{}/{}-{}.log'.format(self.__log_path,args.pname,args.log_type)
        if not os.path.exists(log_file):
            log_file = '/root/.pm2/logs/{}-{}.log'.format(args.pname,args.log_type)
            if not os.path.exists(log_file): return ''
        return public.GetNumLines(log_file,200)

    #列表
    def List(self,get):
        try:
            tmp = public.ExecShell(self.__SR + "pm2 list -m|grep -v 'pm2 list'|grep -v 'In memory PM2'|grep -v 'Local PM2'")
            appList = tmp[0].strip().split('+---')
            result = []
            tmp = public.ExecShell('lsof -c node -P|grep LISTEN')
            plist = tmp[0].split('\n')
            cpss = 0
            cpss_names = {}
            for app in appList:
                try:
                    if not app: continue
                    tmp2 = re.findall(r"([\w ]+):(.+)",app)
                    tmp3 = {}
                    for t in tmp2:
                        tmp3[t[0].strip()] = t[1].strip()
                    tmp2 = tmp3
                    appInfo = {}
                    appInfo['name'] = app.split('\n')[0].strip()
                    appInfo['id'] = tmp2['pm2 id']
                    appInfo['mode'] = tmp2['mode']
                    appInfo['pid'] = int(tmp2['pid'])
                    appInfo['status'] = tmp2['status']
                    appInfo['restart'] = tmp2['restarted']
                    appInfo['uptime'] = tmp2['uptime']
                    appInfo['cpu'] = 0
                    if appInfo['pid'] and appInfo['pid'] != 'N/A':
                        try:
                            appInfo['cpu'] = psutil.Process(appInfo['pid']).cpu_percent(0.01)

                        except:  appInfo['cpu'] = 0

                    appInfo['mem'] = tmp2['memory usage']
                    appInfo['user'] = 'root'
                    appInfo['watching'] = tmp2['watching']
                    appInfo['port'] = 'OFF'
                    appInfo['path'] = 'OFF'
                    appInfo['c_ps'] = ''

                    for p in plist:
                        ptmp = p.split()
                        if len(ptmp) < 8: continue
                        if ptmp[1] == str(appInfo['pid']):
                            appInfo['port'] = ptmp[8].split(':')[1].split('->')[0]
                        else:
                            # node程序自己fork子进程监听端口的情况下
                            ppid = psutil.Process(int(ptmp[1])).ppid()
                            if str(ppid) ==  str(appInfo['pid']):
                                appInfo['port'] = ptmp[8].split(':')[1].split('->')[0]
                            else:
                                # 集群模式
                                try:
                                    if appInfo['mode'] == 'cluster':
                                        ppid = psutil.Process(int(appInfo['pid'])).ppid()
                                        if str(ppid) ==  str(ptmp[1]):
                                            appInfo['port'] = ptmp[8].split(':')[1].split('->')[0]
                                except:
                                    pass

                    #集群分组
                    if appInfo['mode'] == 'cluster':
                        if appInfo['name'] in cpss_names.keys():
                            appInfo['c_ps'] = '({}{})'.format('集群',cpss_names[appInfo['name']])
                            
                        else:
                            cpss +=1
                            appInfo['c_ps'] = '({}{})'.format('集群',cpss)
                            cpss_names[appInfo['name']] = cpss

                    path_file = self.__path + appInfo['name']
                    json_file = path_file + '.json'
                    if os.path.exists(path_file) or not os.path.exists(json_file):
                        appInfo['max_memory'] = 1024
                        get.pname = appInfo['name']
                        show_info  = self.get_show_info(get)
                        appInfo['run'] = show_info['script path']
                        appInfo['path'] = show_info['exec cwd']
                        pdata = {
                            'pname': appInfo['name'],
                            'exec_user': 'www',
                            'cluster': 1,
                            'max_memory': 1024,
                            'path': appInfo['path'],
                            'run': appInfo['run']
                        }
                        public.writeFile(json_file , json.dumps(pdata))
                        os.remove(path_file)
                    else:
                        info_tmp = json.loads(public.readFile(json_file))
                        appInfo['path'] = info_tmp['path']
                        appInfo['user'] = info_tmp['exec_user']
                        appInfo['max_memory'] = info_tmp['max_memory']
                        appInfo['run'] = info_tmp['run']
                        if 'port' in info_tmp.keys(): # 自定义端口
                            appInfo['port'] = info_tmp['port']
                    result.append(appInfo)
                except: continue
            return result
        except:
            return public.returnMsg(False,'请检查pm2是否正常!'+public.get_error_info())


    #手动设置端口
    def set_object_port(self,get):
        pname = get.pname.strip()
        path_file = self.__path + pname
        json_file = path_file + '.json'
        info_tmp = json.loads(public.readFile(json_file))
        info_tmp['port'] = int(get.port)
        public.writeFile(json_file , json.dumps(info_tmp))
        return public.returnMsg(True,'设置成功!')


    #获取映射参数
    def get_proxy_args(self,path):
        products = [
            {
                "product_name": "thinkjs",
                "package_key": "thinkjs",
                "exists": ["www/static","www/upload"],
                "run":"/www",
                "location": ["static"]
            }
        ]
        run = ''
        location = []
        for i in products:
            if i['package_key']:
                package_file = path + '/package.json'
                if not os.path.exists(package_file): continue
                pack_body = public.readFile(package_file)
                if not pack_body: continue
                if pack_body.find(i['package_key']) == -1: continue
            is_continue = False
            for f in i['exists']:
                filename = path + '/' + f
                if not os.path.exists(filename):
                    is_continue = True
            if is_continue: continue
            run = i['run']
            location = i['location']
        return run,location

    #处理映射后续
    def set_proxy_end(self,args):
        pname = args.pname.strip()
        site_name = args.siteName.strip()
        json_file = self.__path + pname + '.json'
        app_info = json.loads(public.readFile(json_file))
        run,location = self.get_proxy_args(app_info['path'])
        proxy_path = '/www/server/panel/vhost/nginx/proxy/nodejs.hao.com/'
        if os.path.exists(proxy_path):
            for fname in os.listdir(proxy_path):
                filename = proxy_path + '/' + fname
                conf = public.readFile(filename)
                conf = re.sub(r"location\s+\~\*\s+\\\.\(gif.*\n\{\s*proxy_pass\s+(.|\n){0,400}\}","",conf)
                public.writeFile(filename,conf)
        if not run: 
            public.serviceReload()
            return public.returnMsg(True,'不需要处理后续映射!')
        rewrite_file = '/www/server/panel/vhost/rewrite/{}.conf'.format(site_name)
        run_path = (app_info['path']+run).replace('//','/')
        path_str = "|".join(location)
        rewrite_conf = '''
location ~ ^/({})/ {{
    root {};
}}
'''.format(path_str,run_path)
        public.writeFile(rewrite_file,rewrite_conf)
        public.serviceReload()
        return public.returnMsg(True,'已完成映射后续处理!')

    #获取已安装库
    def GetMod(self,get):
        v, tip = self._get_v()
        if tip:
            return []
        tmp = public.ExecShell(self.__SR + "npm list --depth=0 -global --json|grep -v '/www/server/nvm'")
        if tmp[0]:
            modList = json.loads(tmp[0])
        else:
            modList = None
        if not modList:
            nrc = self.get_npmrc()
            if nrc.rc.find("prefix"): nrc.rm_conf("prefix")
            if nrc.rc.find("cache"): nrc.rm_conf("cache")
            del nrc
            tmp = public.ExecShell(self.__SR + "npm list --depth=0 -global --json|grep -v '/www/server/nvm'")
            if not tmp[0]:
                return []
            modList = json.loads(tmp[0])

        err_list = tmp[1].split("\n")
        result = []
        for m in modList['dependencies'].keys():
            mod = {}
            mod['name'] = m
            if 'version' in modList['dependencies'][m]:
                mod['version'] = modList['dependencies'][m]['version']
            else:
                for err in err_list:
                    if err.find(m + '@') != -1:
                        mod['version'] = err
                        break
            result.append(mod)
        return result

    def get_npmrc(self):
        def the_init(this):
            this.path = "/root/.npmrc"
            if os.path.exists(this.path):
                this.rc = public.readFile(this.path)
            else:
                this.rc = ""

        def the_rm_conf(this, name):
            rep = "\n {0,3}%s[^\n]*\n" % name
            this.rc = re.sub(rep, "\n", this.rc)

        def the__del(this):
            public.writeFile(this.path, this.rc)

        return type("npmrc", (object,), {"__init__": the_init, "__del__": the__del, "rm_conf": the_rm_conf})()
    
    #安装库
    def InstallMod(self,get):
        public.ExecShell(self.__SR + 'npm install ' + get.mname + ' -g')
        return public.returnMsg(True,'安装成功!')
    
    #卸载库
    def UninstallMod(self,get):
        MyNot=['pm2','npm']
        if get.mname in MyNot: return public.returnMsg(False,'不能卸载['+get.mname+']')
        public.ExecShell(self.__SR + 'npm uninstall ' + get.mname + ' -g')
        return public.returnMsg(True,'卸载成功!')
    
    #获取Node版本列表
    def Versions(self,get):
        result = {}
        rep = r'v\d+\.\d+\.\d+'
        tmp = public.ExecShell(self.__SR+'nvm ls-remote --lts|grep -v v0|grep -v iojs')
        result['list'] = re.findall(rep, tmp[0])
        v, tip = self._get_v()
        result["version"] = v
        result["msg"] = tip
        result["status"] = not bool(tip)
        return result
    
    #切换Node版本
    def SetNodeVersion(self,get):
        version = get.version.replace('v','')
        estr = '''
export NVM_NODEJS_ORG_MIRROR=http://npm.taobao.org/mirrors/node && nvm install %s
nvm use --delete-prefix %s
nvm alias default %s
oldreg=`npm get registry`
npm config set registry http://registry.npm.taobao.org/
npm install pm2 -g
npm config set registry $oldreg 
''' % (version,version,version)
        public.ExecShell(self.__SR + estr)
        return public.returnMsg(True,'已切换至['+get.version+']')


    #编辑
    def Edit(self,get):
        result = self.Delete(get)
        if not result['status']: return result
        result = self.Add(get)
        time.sleep(1)
        if not result['status']: return result
        return public.returnMsg(True,'修改成功!')
    
    #添加
    def Add(self,get):
        #get.pname = get.pname.encode('utf-8');
        runFile = get.run.strip()
        if runFile not in ['npm','npm run start','npm run']:
            if not os.path.exists(runFile): return public.returnMsg(False,'指定文件不存在!')
        else:
            node_version = public.ExecShell(self.__SR + "nvm version")[0].strip()
            runFile = '/www/server/nvm/versions/node/{}/bin/npm'.format(node_version)
            if not os.path.exists(runFile): return public.returnMsg(False,'请检查是否安装Node!') 
            runFile += ' -- run start'

        
        Nlist = self.List(get)
        
        for node in Nlist:
            if get.pname == node['name']: return public.returnMsg(False,'指定项目名称已经存在!')
        if os.path.exists(get.path + '/package.json') and not os.path.exists(get.path + '/package-lock.json'): public.ExecShell(self.__SR + "cd " + get.path + ' && npm install -s')
        if get.path in ['/','/www','/var','/usr','/usr/bin','/usr/sbin','/usr/local','/www/server','/www/server/panel','/tmp','/home']:
            return public.returnMsg(False,'不能将关键目录设为运行目录')

        exec_user = 'www'
        if 'exec_user' in get: exec_user = get.exec_user
        cluster = ''
        if 'cluster' in get: 
            if int(get.cluster) > 1:
                cluster = ' -i {}'.format(get.cluster)
        max_memory = ''

        if 'max_memory' in get: max_memory = ' --max-memory-restart {}'.format(int(get.max_memory) * 1024 * 1024)

        public.ExecShell("chown -R {}:{} {}".format(exec_user,exec_user,get.path))
        error_log_file = os.path.join(self.__log_path,get.pname+'-error.log')
        out_log_file = os.path.join(self.__log_path,get.pname+'-out.log')

        exec_str = self.__SR + '''cd {}
pm2 -u {} --name {} --cwd {} --output {} --error {} --time{}{} start {}
'''.format(get.path,exec_user,get.pname,get.path,out_log_file,error_log_file,cluster,max_memory,runFile)
        result =  public.ExecShell(exec_str)
        if(result[1]): return public.returnMsg(False,result[1])
        #public.ExecShell(self.__SR + 'cd '+get.path+' && pm2 -u www start ' + runFile +  ' --name "'+get.pname+'"|grep ' + get.pname)
        public.ExecShell(self.__SR + 'pm2 save && pm2 startup')
        if not os.path.exists(self.__path): public.ExecShell('mkdir -p ' + self.__path)
        pdata = {
            'pname': get.pname,
            'exec_user': get.exec_user,
            'cluster': get.cluster,
            'max_memory': get.max_memory,
            'path': get.path,
            'run': get.run.strip()
        }
        public.writeFile(self.__path + get.pname + '.json' , json.dumps(pdata))
        return public.returnMsg(True,'ADD_SUCCESS')
    
    #启动
    def Start(self,get):
        #get.pname = get.pname.encode('utf-8');
        json_file = self.__path + get.pname + '.json'
        app_info = json.loads(public.readFile(json_file))
        appid = get.appid.strip()
        result = public.ExecShell(self.__SR + 'pm2 -u '+app_info['exec_user']+' start ' + get.pname)
        #result = public.ExecShell(self.__SR + 'pm2 -u '+app_info['exec_user']+' start ' + appid)
        if result[0].find('online') != -1: return public.returnMsg(True,'项目['+get.pname+']已启动!')
        return public.returnMsg(False,'项目['+get.pname+']启动失败!<br><pre>' + result[0]  + result[1] + '</pre>')
    
    #停止
    def Stop(self,get):
        #get.pname = get.pname.encode('utf-8');
        appid = get.appid.strip()
        result = public.ExecShell(self.__SR + 'pm2 stop ' + get.pname )
        #result = public.ExecShell(self.__SR + 'pm2 stop ' + appid )
        if result[0].find('stoped') != -1: return public.returnMsg(True,'项目['+get.pname+']已停止!')
        return public.returnMsg(True,'项目['+get.pname+']停止失败!<br><pre>' + result[0] + result[1] + '</pre>')
    
    #重启
    def Restart(self,get):
        #get.pname = get.pname.encode('utf-8');
        json_file = self.__path + get.pname + '.json'
        app_info = json.loads(public.readFile(json_file))
        appid = get.appid.strip()
        result = public.ExecShell(self.__SR + 'pm2 -u '+app_info['exec_user']+' restart ' + get.pname )
        #result = public.ExecShell(self.__SR + 'pm2 -u '+app_info['exec_user']+' restart ' + appid )
        if result[0].find('✓') != -1: return public.returnMsg(True,'项目['+get.pname+']已重启!')
        return public.returnMsg(False,'项目['+get.pname+']重启失败!<br><pre>' + result[0] + result[1] + '</pre>')
    
    #重载
    def Reload(self,get):
        #get.pname = get.pname.encode('utf-8');
        json_file = self.__path + get.pname + '.json'
        app_info = json.loads(public.readFile(json_file))
        appid = get.appid.strip()
        result = public.ExecShell(self.__SR + 'pm2 -u '+app_info['exec_user']+' reload ' + get.pname)
        #result = public.ExecShell(self.__SR + 'pm2 -u '+app_info['exec_user']+' reload ' + appid)
        if result[0].find('✓') != -1: return public.returnMsg(True,'项目['+get.pname+']已重载!')
        return public.returnMsg(False,'项目['+get.pname+']重载失败!<br><pre>' + result[0] + result[1] + '</pre>')
    
    #删除
    def Delete(self,get):
        appid = get.appid.strip()
        
        result = public.ExecShell(self.__SR + 'pm2 stop '+get.pname+' && pm2 delete ' + get.pname)
        if result[0].find('✓') != -1: 
            public.ExecShell(self.__SR + 'pm2 save && pm2 startup')
            path_file  = self.__path + get.pname
            json_file = path_file + '.json'
            if os.path.exists(path_file): os.remove(path_file)
            if os.path.exists(json_file): os.remove(json_file)
            return public.returnMsg(True,'DEL_SUCCESS')
        return public.returnMsg(False,'删除失败!<br><pre>' + result[0] + result[1] + '</pre>')
    
    #获取日志
    def GetLogs(self,get):
        path = '/root/.pm2/pm2.log'
        if not os.path.exists(path): return '当前没有日志'
        return public.readFile(path)

    # 获取版本信息，包含是否可用
    def _get_v(self):
        tmp = public.ExecShell(self.__SR + "type node \nnode -v")
        public.print_log(self.__SR + "type node \nnode -v")
        rep = r"versions/node/(?P<target>v(\d{1,3}\.){1,3}\d{1,3})/bin/node"
        res = re.search(rep, tmp[0])
        if res:
            version = res.group("target")
        else:
            version = None
        tip = None
        if tmp[1] and tmp[1].find("not found") != -1 and tmp[1].find("required by node") != -1:
            tip = "Nodejs版本过高，系统不支持，建议更换为较低版本。"

        return version, tip

    #获取Node版本列表
    def GetVersion(self, get):
        result = {}
        v, tip = self._get_v()
        result["version"] = v
        result["msg"] = tip
        result["status"] = not bool(tip)
        return result


if __name__ == "__main__":
    p = pm2_main()
    print(p.List(None))