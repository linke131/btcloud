#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: cjxin <cjxin@bt.cn>
# +-------------------------------------------------------------------

import os, sys,datetime,shutil,re
panelPath = os.getenv('BT_PANEL')
if not panelPath: panelPath = '/www/server/panel'
os.chdir(panelPath)
sys.path.insert(0,panelPath + "/class/")
import public,json,time,random,base64,db

class ssl_verify_main:
    
    _API_URL = 'https://api.bt.cn/bt_cert'
    _sql = None
    _os = "Linux"
    _b_gd = None
    def __init__(self):
        self._sql = db.Sql().dbfile('ssl_verify')
        if os.getenv('BT_PANEL'): self._os = 'Windows'


    def create_database(self):
        
        csql = '''CREATE TABLE IF NOT EXISTS `config` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `company` REAL,
    `domain`  REAL,
    `crl`   REAL,
    `key`   REAL,
    `pfx`   REAL,
    `cert`  REAL,
    `ca_cert`  REAL,
    `password`  REAL,
    `last_modify` INTEGER,
    `day` INTEGER,
    `addtime` INTEGER
)'''
        self._sql .execute(csql,())

        csql = '''CREATE TABLE IF NOT EXISTS `logs` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `log` REAL,
  `addtime` INTEGER
)'''
        self._sql.execute(csql,())

        csql = '''CREATE TABLE IF NOT EXISTS `ssl` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `company` REAL,
  `client`  REAL,
  `pfx`     REAL,
  `password`    REAL,
  `status` INTEGER,
  `last_modify` INTEGER,
  `day` INTEGER,
  `addtime` INTEGER
)'''
        self._sql.execute(csql,())

    def get_file_list(self,path, flist):     
        """
        递归获取目录所有文件列表
        @path 目录路径
        @flist 返回文件列表
        """
        if os.path.exists(path):        
            files = os.listdir(path)
            flist.append(path)
            for file in files:
                if os.path.isdir(path + '/' + file):
                    self.get_file_list(path + '/' + file, flist)
                else:
                    flist.append(path + '/' + file)

    def get_config(self,get):
        """
        @获取配置
        """
        self.create_database()
        data = self._sql.table('config').select()

        spath = '{}/plugin/ssl_verify/domain'.format(panelPath)
        if not os.path.exists(spath): os.makedirs(spath)
        
        if len(data):
            data[0]['info'] = ''

            if data[0]['key']:                
                public.writeFile(spath + '/key.pem',data[0]['key'].strip())
                public.writeFile(spath + '/cert.pem',data[0]['cert'].strip())

                try:
                    data[0]['info'] = public.get_cert_data(spath + '/cert.pem')  
                except :pass

            cpath = '{}/plugin/ssl_verify/client'.format(panelPath)
            if not os.path.exists(cpath): os.makedirs(cpath)

            if data[0]['ca_cert']:                
                public.writeFile(cpath + '/ca.pem',data[0]['ca_cert'].strip())
                public.writeFile(cpath + '/crl.pem',data[0]['crl'].strip())

        ret = self.get_post_argv(get)
        return data

    def set_config(self,get):
        """
            @保存配置
        """
        pdata = {}
        if not 'company' in get or not re.search('^[\u4e00-\u9fa5_a-zA-Z0-9]+$',get['company']):
            return public.returnMsg(False,'company不合法，只允许中文、英文或数字.'); 
        
        pdata['domain'] = ''        
        pdata['company'] = get['company']
        if 'domain' in get:
            reg = "^([\w\-\*]{1,100}\.){1,10}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$";
            for x in get['domain'].split(','):                
                if not re.match(reg, x): 
                    return public.returnMsg(False,'域名不合法.');
            pdata['domain'] = get['domain']
          
        data = self._sql.table('config').select()
        if len(data) > 0:            
            self._sql.table('config').where("id=?",(data[0]['id'],)).update(pdata);
        else:
            self._sql.table('config').add('company,domain,addtime',(pdata['company'],pdata['domain'],int(time.time())))     

        self.get_bundle_crl(get)

        return public.returnMsg(True,'修改成功.'); 

    def get_post_argv(self,get):
        """
        @构造请求参数
        """
        data = self._sql.table('config').select()
        if len(data) <= 0: 
            return public.returnMsg(False,'请先填写配置.');

        find = data[0]
        if not find['domain']: 
            return public.returnMsg(False,'域名为空，请先完善域名信息.');

        if not find['company']: 
            return public.returnMsg(False,'公司名称或姓名为空.'); 

        uInfo = public.get_user_info()
        if not uInfo: 
            return public.returnMsg(False,'未绑定宝塔帐号，请先绑定.');

        pdata = {}        
        pdata['uid'] = uInfo['uid']
        try:
            user_file = '{}/data/userInfo.json'.format(panelPath)
            userTmp = json.loads(public.readFile(user_file))

            pdata['access_key'] = userTmp['access_key']
        except :
            pdata['access_key'] = ''

        pdata['company'] = find['company']
        pdata['domain'] = find['domain']
        pdata['config_id'] = find['id'] 
        pdata['status'] = True
        return pdata

    def write_logs(self,log):
        """
        @保存日志
        """
        self._sql.table('logs').add('log,addtime',(log,int(time.time())))

    def get_ssl_list(self,get):
        """
        获取所有证书列表
        """
        self.create_database()

        _sql = self._sql.table('ssl')
        where = '1=1'
        if 'status' in get:
            if int(get['status']): where = "status={}".format(get['status'])

        if 'search' in get: 
            where += " and client like '%" + get['search'] + "%'"

        data = _sql.where(where,()).field('id,company,pfx,password,client,status,day,last_modify,addtime').select()
        return data


    def _get_conf_path(self,siteName):
        """
        获取网站配置
        """
        serverType = public.get_webserver()
        if os.getenv('BT_PANEL'):            
            if serverType == 'iis': return None               
            path = "{}/{}/conf/bt_ca/{}".format(public.get_soft_path(),serverType,siteName)            
        else:
            path = '{}/vhost/{}/bt_ca/{}'.format(panelPath,serverType,siteName)
        if not os.path.exists(path): os.makedirs(path)            
        return path

    def _get_site_path(self,siteName):
        """
        @获取网站主配置文件路径
        """
        serverType = public.get_webserver()
        if os.getenv('BT_PANEL'):            
            if serverType == 'iis': return None               
            path = "{}/{}/conf/vhost/{}.conf".format(public.get_soft_path(),serverType,siteName)   
            return path
        else:
            spath =  '{}/vhost/{}'.format(panelPath,serverType)
            path = '{}/{}.conf'.format(spath,siteName)
            if os.path.exists(path): return path

            flist = []
            self.get_file_list(spath,flist)
            for x in flist:
                if x.find('_'+siteName+'.conf') >=0: 
                    if os.path.exists(x) and os.path.isfile(x): return x                        
            return False                                    
        

    def update_crl_conf(self,get):
        """
        @更新注销列表到nginx/apache
        """
        serverType = public.get_webserver()
        config = self.get_config(None)[0]

        if serverType != 'iis':
            if os.getenv('BT_PANEL'):            
            
                root_path = "{}/{}/conf/bt_ca".format(public.get_soft_path(),serverType)            
            else:
                root_path = '{}/vhost/{}/bt_ca'.format(panelPath,serverType)
            if not os.path.exists(root_path): os.makedirs(root_path)
   
            for siteName in os.listdir(root_path):
                path = os.path.join(root_path, siteName)
                if not os.path.isdir(path): continue

                crl = path + '/ca.crl'            
                if os.path.exists(crl):public.writeFile(crl,config['crl'].strip())

                cert = path + '/ca.cert'
                if os.path.exists(cert):public.writeFile(cert,config['ca_cert'].strip())
        
        ssl_path = '{}/ssl'.format(panelPath)
        if not os.path.exists(ssl_path): os.makedirs(ssl_path)
        
        ca_file = '{}/ssl/ca.pem'.format(panelPath)
        crl_file = '{}/ssl/crl.pem'.format(panelPath)
      
        public.writeFile(crl_file,config['crl'].strip())
        public.writeFile(ca_file,config['ca_cert'].strip())

        public.serviceReload();
        return True

    def get_site_list(self,get):
        """
        获取网站列表
        """
        where = '1=1'
        if 'search' in get: where =  "id='"+get['search']+"' or name like '%"+get['search']+"%' or status like '%"+get['search']+"%' or ps like '%"+get['search']+"%'"
        data = public.M('sites').where(where,()).select()

        result = []                             
        for v in data:
            v['ssl_verify'] = False
            
            try:
                file = self._get_site_path(v['name'])               
                if file:                          
                    conf = public.readFile(file)                        
                    slist = ['\s+include.+bt_ca/{}/{}.conf;\s+'.format(v['name'],v['name']),'\s+IncludeOptional.+conf/bt_ca/{}/{}.conf\s+'.format(v['name'],v['name'])]
                    for x in slist:
                        if re.search(x,conf):                
                            v['ssl_verify'] = True   
                            break;
                result.append(v)
            except :
                return public.returnMsg(False,conf);

        result = sorted(result,key= lambda  x:x['ssl_verify'],reverse=True)
        return result;

    def _write_pfx(self,path,data):
        """
        @保存二进制文件
        """
        if self._os == 'Windows':
            public.writeFile2(path,data,'wb+')        
        else:
            public.writeFile(path,data,'wb+')
        
    def set_ssl_verify(self,get):
        """
        @设置网站开关
        """
        siteName = get['siteName']
        status = int(get['status'])
        web =  public.get_webserver()
        if web == 'iis':  return public.returnMsg(False,'双向认证暂时不支持IIS.');

        import panelSite
        site_obj = panelSite.panelSite()
        ret = site_obj.GetSSL(get)
        if not ret['status']: return public.returnMsg(False,'该网站未开启SSL，不支持双向认证.');
               
        root_path = self._get_conf_path(siteName)

        conf_path = '{}/{}.conf'.format(root_path,siteName)
        file = self._get_site_path(siteName)
        if not os.path.exists(file): 
            return public.returnMsg(False,'网站配置文件不存在.');   

        conf = public.readFile(file)

        rep_conf = 'include bt_ca/{}/{}.conf;'.format(siteName,siteName)

        if status:
            config = self.get_config(None)[0]
            if not config['ca_cert']:
                ret = self.get_bundle_crl(None)
                if not ret['status']: 
                    return public.returnMsg(False,ret['msg']);
                config = self.get_config(None)[0]

            if self._os == 'Windows':
                #nginx
                if web == 'nginx':                    
                    ssl_conf = """ssl_verify_client on;
ssl_verify_depth 5;
ssl_crl bt_ca/{}/ca.crl;
ssl_client_certificate bt_ca/{}/ca.cert;""".format(siteName,siteName)
                    
                    key = 'include bt_ca/{}/{}.conf;'.format(siteName,siteName)
                    if conf.find(key) == -1:                        
                        conf = conf.replace("#SSL-INFO-END","\n\t{}\n\t#SSL-INFO-END".format(key))
                #apache
                else: 
                    ssl_conf= '''SSLVerifyClient on  
SSLVerifyDepth  5
SSLCARevocationPath "conf/bt_ca/{}/"
SSLCACertificateFile "conf/bt_ca/{}/ca.cert"'''.format(siteName,siteName)

                    key = 'IncludeOptional conf/bt_ca/{}/{}.conf'.format(siteName,siteName)
                    if conf.find(key) == -1:  
                        conf = conf.replace("SSLHonorCipherOrder On","SSLHonorCipherOrder On\n\t{}".format(key))
            else:
                #linux nginx
                if web == 'nginx':
                    ssl_conf = """ssl_verify_client on;
ssl_verify_depth 5;
ssl_crl /www/server/panel/vhost/nginx/bt_ca/{}/ca.crl;
ssl_client_certificate /www/server/panel/vhost/nginx/bt_ca/{}/ca.cert;""".format(siteName,siteName)
                    
                    key = 'include /www/server/panel/vhost/nginx/bt_ca/{}/{}.conf;'.format(siteName,siteName)
                    if conf.find(key) == -1:                        
                        conf = conf.replace("#SSL-END","\n\t{}\n\t#SSL-END".format(key))
                #linux apache
                elif web == 'apache':
                    ssl_conf= '''SSLVerifyClient on  
SSLVerifyDepth  5
SSLCARevocationPath "/www/server/panel/vhost/apache/bt_ca/{}/"
SSLCACertificateFile "/www/server/panel/vhost/apache/bt_ca/{}/ca.cert"'''.format(siteName,siteName)

                    key = 'IncludeOptional /www/server/panel/vhost/apache/bt_ca/{}/{}.conf'.format(siteName,siteName)
                    if conf.find(key) == -1:  
                        conf = conf.replace("SSLHonorCipherOrder On","SSLHonorCipherOrder On\n\t{}".format(key))
                            
            public.writeFile(conf_path,ssl_conf)
            public.writeFile(root_path+'/ca.crl',config['crl'].strip()) #注销列表
            public.writeFile(root_path+'/ca.cert',config['ca_cert'].strip()) # ca证书
            
            public.writeFile(file,conf) #更新网站配置
            public.serviceReload()
            return public.returnMsg(True,'开启双向认证成功.'); 
                
        else:
            if os.path.exists(conf_path): os.remove(conf_path)

            slist = ['\s+include.+bt_ca/{}/{}.conf;\s+'.format(siteName,siteName),'\s+IncludeOptional.+conf/bt_ca/{}/{}.conf\s+'.format(siteName,siteName)]
            for key in slist:
                if re.search(key,conf):
                    conf = re.sub(key,'\n\t',conf) 
                    public.writeFile(file,conf)
                    public.serviceReload()

            return public.returnMsg(True,'关闭双向认证成功.'); 


    def pkcs12_to_pem(self,pfx_buff,password = None):
        """
        pfx转pem
        """
        from OpenSSL import crypto   
        try:        
            p12 = crypto.load_pkcs12(pfx_buff,password)
        except :
            p12 = crypto.load_pkcs12(pfx_buff)

        data = {}
        data['key'] = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey()).decode().strip()    
        data['cert'] = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate()).decode().strip()

        ca_list = []
        for x in p12.get_ca_certificates():
            ca_list.insert(0,crypto.dump_certificate(crypto.FILETYPE_PEM, x).decode().strip())
        data['ca']  = '\n'.join(ca_list)

        return data

    #清除pfx证书密码
    def clear_pkcs12_pwd(self,pfx_buff,password):

        ret = self.pkcs12_to_pem(pfx_buff,password)

        new_buffer = self.dump_pkcs12(ret['key'],'{}\n{}'.format(ret['cert'],ret['ca']),ret['cert'])
   
        return new_buffer

    # 证书转为pkcs12
    def dump_pkcs12(self,key_pem=None, cert_pem=None, ca_pem=None, friendly_name=None):
        import OpenSSL

        p12 = OpenSSL.crypto.PKCS12()

        if cert_pem:
        
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem.encode())
   
            p12.set_certificate(x509)
        if key_pem:
            p12.set_privatekey(OpenSSL.crypto.load_privatekey(
                OpenSSL.crypto.FILETYPE_PEM, key_pem.encode()))
        if ca_pem:
            p12.set_ca_certificates((OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, ca_pem.encode()),))
        if friendly_name:
            p12.set_friendlyname(friendly_name.encode())
        return p12.export()

    def down_domain_pfx(self,get):
        """
        @下载域名证书
        """
        sdata = self._sql.table('config').where("id>?",(0,)).select()
        if len(sdata) <= 0 or not sdata[0]['pfx']: 
            return public.returnMsg(False,'未生成域名证书.');
        find = sdata[0];

        spath = '{}/plugin/ssl_verify/domain'.format(panelPath)
        if os.path.exists(spath): shutil.rmtree(spath,True)        
        os.makedirs(spath)

        pfx_buffer = base64.b64decode(find['pfx'])
        self._write_pfx("{}/domain.pfx".format(spath),pfx_buffer)
        public.writeFile("{}/password.txt".format(spath),find['password'])
        public.writeFile("{}/使用说明.txt".format(spath),"""Windows用户使用说明：
1、双击当前目录的pfx文件
2、选择下一页直至输入密码页面
3、打开password.txt文件，将密码粘贴进输入框
4、完成导入

MAC用户使用说明：
1、cmmand+空格   搜索"Keychain Access"
2、将pfx文件拖入到系统的证书列表
3、打开password.txt文件，将密码粘贴进输入框
4、完成导入

其他系统用户使用说明（Google Chrome为例）：
1、右上角打开浏览器设置
2、打开隐私设置和安全性
3、选择安全
4、管理证书
5、导入证书
6、打开password.txt文件，将密码粘贴进输入框
7、完成导入

如默认浏览器无法正常使用，请使用谷歌浏览器进行配置""")

        cert_data = self.pkcs12_to_pem(pfx_buffer,find['password'])
        public.writeFile("{}/key.pem".format(spath),cert_data['key'])
        public.writeFile("{}/cert.crt".format(spath),cert_data['cert'] + cert_data['ca'])


        flist = []
        self.get_file_list(spath,flist)

        zfile = '{}/domain.zip'.format(spath).replace("\\","/")
        import zipfile  
        f = zipfile.ZipFile(zfile,'w',zipfile.ZIP_DEFLATED)
        for item in flist:
            s_path = item.replace(spath,'')
            if s_path: f.write(item,s_path)     
        f.close()

        return public.returnMsg(True,zfile); 

    def down_client_pfx(self,get):
        """
        @下载客户端证书
        """
        id = get['id']
        find = self._sql.table('ssl').where("id=?",(id,)).find()
        if not find: return public.returnMsg(False,'未找到指定使用者信息.');

        spath = '{}/plugin/ssl_verify/client/{}'.format(panelPath,find['client'])
        if os.path.exists(spath): shutil.rmtree(spath,True)        
        os.makedirs(spath)
        
        pfx_buffer = base64.b64decode(find['pfx'])
        self._write_pfx("{}/{}.pfx".format(spath,find['client']),pfx_buffer)
        public.writeFile("{}/password.txt".format(spath),find['password'])
        public.writeFile("{}/使用说明.txt".format(spath),"""Windows用户使用说明：
1、双击当前目录的pfx文件
2、选择下一页直至输入密码页面
3、打开password.txt文件，将密码粘贴进输入框
4、完成导入

MAC用户使用说明：
1、cmmand+空格   搜索"Keychain Access"
2、将pfx文件拖入到系统的证书列表
3、打开password.txt文件，将密码粘贴进输入框
4、完成导入

如默认浏览器无法正常使用，请使用谷歌浏览器进行配置""")
        
        cert_data = self.pkcs12_to_pem(pfx_buffer,find['password'])
        public.writeFile("{}/key.pem".format(spath),cert_data['key'])
        public.writeFile("{}/cert.crt".format(spath),cert_data['cert'] + cert_data['ca'])


        flist = []
        self.get_file_list(spath,flist)

        zfile = '{}/{}.zip'.format(spath,find['client']).replace("\\","/")
        import zipfile  
        f = zipfile.ZipFile(zfile,'w',zipfile.ZIP_DEFLATED)
        for item in flist:
            s_path = item.replace(spath,'')
            if s_path: f.write(item,s_path)        
        f.close()

        return public.returnMsg(True,zfile); 

    def get_domain_cert(self,get):
        """
        @申请域名证书
        """
        rdata = self.get_post_argv(get)
        if not rdata['status']: return rdata

        rdata['action'] = 'get_domain_cert'
        try:
            print(self._API_URL,json.dumps(rdata))
            result = public.httpPost(self._API_URL,{'data':json.dumps(rdata)},30)
            print(result)
            result = json.loads(result)

            if not result['status']: 
                return result
            
            pdata = {}
            pdata['key'] = result['key']
            pdata['pfx'] = result['pfx']
            pdata['cert'] = result['cert']
            pdata['password'] = result['password']
            pdata['day'] = 365
            pdata['last_modify'] = int(time.time())

            self._sql.table('config').where("id=?",(rdata['config_id'],)).update(pdata);
            
            self.write_logs("域名证书生成成功")
            return result
        except :         
            #print(result)
            self.write_logs("域名证书生成失败->" + str(result))
            return public.returnMsg(False,'连接宝塔官网失败，请检查网络原因.'+result);

    def update_panel_ssl(self,get):
        """
        @申请域名证书,并且更新到面板SSL
        """
        result = self.get_domain_cert(get)
        if 'status' in result and not result['status']: 
            return result
        
        ssl_path = '{}/ssl'.format(panelPath)
        if not os.path.exists(ssl_path): os.makedirs(ssl_path)

        keyfile = 'ssl/privateKey.pem'
        certfile = 'ssl/certificate.pem'

        public.writeFile(keyfile,result['key'].strip())
        public.writeFile(certfile,result['cert'].strip())

        return public.returnMsg(True,"更新到面板SSL成功.");


    def get_bundle_crl(self,get):
        """
        @更新ca证书和crl撤销列表
        """
        rdata = self.get_post_argv(get)
        if not rdata['status']: return rdata

        rdata['action'] = 'get_bundle_crl'     
        result = public.httpPost(self._API_URL,{'data':json.dumps(rdata)},30)
        result = json.loads(result)

        if not result['status']:  
            return result

        cData = {}
        cData['crl'] = result['crl']
        cData['ca_cert'] = result['ca_cert']
        self._sql.table('ssl').table('config').where("id>?",(0,)).update(cData)

        self.update_crl_conf(None)
        self.write_logs("更新CA证书和撤销列表成功")
        return result

    def revoke_client_cert(self,get):
        """
        @注销证书
        """
        find = self._sql.table('ssl').where("id=?",(get.id,)).find()
        if not find: return public.returnMsg(False,'未找到指定使用者信息.');
           
        rdata = self.get_post_argv(get)
        if not rdata['status']: return rdata
        rdata['action'] = 'revoke_client_cert'         
        rdata['client'] = find['client']

        result = public.httpPost(self._API_URL,{'data':json.dumps(rdata)},30)
        result = json.loads(result)

        if not result['status']:
            return result

        cData = {}
        cData['crl'] = result['crl']
        cData['ca_cert'] = result['ca_cert']
        self._sql.table('config').where("id>?",(0,)).update(cData)

        self._sql.table('ssl').where("id=?",(get.id,)).setField('status',-1)
        self.update_crl_conf(None)
        self.write_logs("撤销证书[{}]成功".format(find['client']))
        return result


    def get_user_cert(self,get):
        """
            @申请客户端证书
        """
        rdata = self.get_post_argv(get)
        if not rdata['status']: return rdata

        client = get['client']
        rdata['action'] = 'get_user_cert'           
        rdata['client'] = client
        try:
            if not client or not re.search('^[\u4e00-\u9fa5_a-zA-Z0-9-_]+$',client): 
                return public.returnMsg(False,'使用者信息不能为空.');

            find = self._sql.table('ssl').where("client=?",(client,)).find()
            if not find: self._sql.table('ssl').add('company,client,status,addtime',(rdata['company'],client,0,int(time.time())))

            result = public.httpPost(self._API_URL,{'data':json.dumps(rdata)},30)
            result = json.loads(result)

            if not result['status']: 
                return result
            
            #更新ca证书
            cData = {}
            cData['crl'] = result['crl']
            cData['ca_cert'] = result['ca_cert']
            self._sql.table('config').where("id>?",(0,)).update(cData)

            pdata = {}
            pdata['status'] = 1
            pdata['pfx'] = result['pfx']
            pdata['password'] = result['password']  
            pdata['day'] = 365
            pdata['last_modify'] = int(time.time())

            self._sql.table('ssl').where("client=?",(client,)).update(pdata);
            
            self.write_logs("生成客户端证书[{}]成功".format(client))
            return result
        except :
            self.write_logs("生成客户端证书[{}]失败->{}".format(client,result))
            return public.returnMsg(False,'连接宝塔官网失败，请检查网络原因.');
        


if __name__ == '__main__':

    pass
   