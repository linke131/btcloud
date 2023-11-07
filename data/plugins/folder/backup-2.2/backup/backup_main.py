#!/usr/bin/python
# coding: utf-8
# ♪(´▽｀)
# 宝塔Linux面板环境备份/还原工具
# Author: 赤井秀一
# email: 1021266737@qq.com
#
import sys, os, importlib

if sys.version_info[0] == 2:
    importlib.reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, time, json, re, zipfile, firewalls, random, db , crontab


def M(table, type='system2'):
    import db
    sql = db.Sql()
    sql.dbfile(type)
    return sql.table(table)


class mobj: port = ps = path = type = ''


class backup_main:
    __path = '/www/server/panel/backup/panelBackup'
    __reduction_path = '/www/server/panel/backup/ReduCtion'
    __Disposable_path = '/www/server/panel/backup/Disposable'
    __backup_path = None

    # 初始化目录
    def __init__(self):
        if not os.path.exists(self.__path):
            os.system('mkdir -p ' + self.__path)
            os.system('chmod -R 600 %s' % self.__path)

        if not os.path.exists(self.__reduction_path):
            os.system('mkdir -p ' + self.__reduction_path)
            os.system('chmod -R 600 %s' % self.__reduction_path)

        if not os.path.exists(self.__Disposable_path):
            os.system('mkdir -p ' + self.__Disposable_path)
            os.system('chmod -R 600 %s' % self.__Disposable_path)

    def BackupDir(self):
        list1 = []
        time_out = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        backup_dir = 'Panel_Bak_' + time_out
        backup_path = '/%s/%s' % (self.__path, backup_dir)
        list1.append(time_out)
        list1.append(backup_dir)
        list1.append(backup_path)
        if backup_path:
            if not os.path.exists(backup_path):
                os.system('mkdir -p %s' % backup_path)
                os.system('chmod -R 600 %s' % backup_path)
        return list1

    # 构造system.db
    def M(table):
        sql = db.Sql()
        sql.dbfile('system2')
        return sql.table(table)

    # 字节单位转换
    def ToSize(self, size):
        ds = ['b', 'KB', 'MB', 'GB', 'TB']
        for d in ds:
            if int(size) < 1024: return "%.2f%s" % (size, d)
            size = size / 1024
        return '0b'

    # 备份日志
    def BackupLog(self, path, isLog=None):
        data = public.M('logs').field('type,log,addtime').select()
        if len(data) >= 1:
            backupLog = path + '/log.json'
            print(backupLog)
            # os.system('mkdir -p  %s' % self.__backup_path)
            os.mknod(backupLog)
            public.writeFile(backupLog, json.dumps(data))
            print('备份完成，共' + str(len(data)) + '条日志!')
            return backupLog

    # 网站信息
    def BackupSite(self, path):
        data = {}
        data['site'] = public.M('sites').field('id,name,path,status,ps,addtime,project_type,project_config').select()
        data['domain'] = public.M('domain').field('pid,name,port,addtime').select()
        if len(data) >= 1:
            backupLog = path + '/site.json'
            print(backupLog)
            # os.system('mkdir -p  %s' % self.__backup_path)
            os.mknod(backupLog)
            public.writeFile(backupLog, json.dumps(data))
            print('备份完成，共' + str(len(data)) + '条日志!')
            return data

    # 计划任务信息
    def BackupCrontab(self, path):
        data = {}
        data['cron'] = public.M('crontab').field('id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sName,sBody,sType,urladdress,save_local,notice,notice_channel').select()
        if len(data) >= 1:
            backupLog = path + '/cron.json'
            print(backupLog)
            # os.system('mkdir -p  %s' % self.__backup_path)
            os.mknod(backupLog)
            public.writeFile(backupLog, json.dumps(data))
            print('备份完成，共' + str(len(data)) + '条日志!')
            return data

    # 备份面板FTP
    def RePanelFtp(self, path):
        data = public.M('ftps').field('name,password,path,status,ps,addtime').select()
        if len(data) >= 1:
            backupLog = path + '/ftp.json'
            print(backupLog)
            # os.system('mkdir -p  %s' % self.__backup_path)
            os.mknod(backupLog)
            public.writeFile(backupLog, json.dumps(data), 'w+')
            print('备份完成，共' + str(len(data)) + '条日志!')
            return backupLog

    # 备份防火墙
    def RePanelFrewall(self, path):
        data = public.M('firewall').field('port,ps,addtime').select()
        if len(data) >= 1:
            backupLog = path + '/firewall.json'
            print(backupLog)
            os.system('touch %s' % backupLog)
            public.writeFile(backupLog, json.dumps(data))
            print('备份完成，共' + str(len(data)) + '条日志!')
            return backupLog

    # 备份配置文件
    def BackupSiteConfig(self, name, path):
        bt_conf = path + '/' + name + '/bt_conf'
        os.system('mkdir -p ' + bt_conf + '/cert')
        print("备份Nginx配置文件")

        # 备份Nginx配置文件
        php_nginxConf = bt_conf + '/php_nginx.conf'
        java_nginxConf = bt_conf + '/java_nginx.conf'
        node_nginxConf = bt_conf + '/node_nginx.conf'
        phpNginxConf = '/www/server/panel/vhost/nginx/' + name + '.conf'
        javaNginxConf = '/www/server/panel/vhost/nginx/java_' + name + '.conf'
        nodeNginxConf = '/www/server/panel/vhost/nginx/node_' + name + '.conf'
        if os.path.exists(phpNginxConf):
            conf = public.readFile(phpNginxConf).replace(' default_server', '')
            public.writeFile(php_nginxConf, conf)

        if os.path.exists(javaNginxConf):
            conf = public.readFile(javaNginxConf).replace(' default_server', '')
            public.writeFile(java_nginxConf, conf)

        if os.path.exists(nodeNginxConf):
            conf = public.readFile(nodeNginxConf).replace(' default_server', '')
            public.writeFile(node_nginxConf, conf)

        # 备份java项目tomcat配置文件
        tomcatPath = bt_conf + '/server.xml'
        siteSerPath = '/www/server/bt_tomcat_web/' + name + '/conf/server.xml'
        if os.path.exists(siteSerPath):
            conf = public.readFile(siteSerPath)
            public.writeFile(tomcatPath, conf)

        # 备份Nginx伪静态文件
        php_nginxRewrite = bt_conf + '/php_rewrite.conf'
        java_nginxRewrite = bt_conf + '/java_rewrite.conf'
        node_nginxRewrite = bt_conf + '/node_rewrite.conf'
        phpNginxRewrite = '/www/server/panel/vhost/rewrite/' + name + '.conf'
        javaNginxRewrite = '/www/server/panel/vhost/rewrite/java_' + name + '.conf'
        nodeNginxRewrite = '/www/server/panel/vhost/rewrite/node_' + name + '.conf'

        if os.path.exists(phpNginxRewrite):
            conf = public.readFile(phpNginxRewrite)
            public.writeFile(php_nginxRewrite, conf)
        if os.path.exists(javaNginxRewrite):
            conf = public.readFile(javaNginxRewrite)
            public.writeFile(java_nginxRewrite, conf)
        if os.path.exists(nodeNginxRewrite):
            conf = public.readFile(nodeNginxRewrite)
            public.writeFile(node_nginxRewrite, conf)

        # 备份子目录伪静态规则
        try:
            panelRewritePath = '/www/server/panel/vhost/rewrite'
            rs = os.listdir(panelRewritePath)
            for r in rs:
                if r.find(name + '_') == -1: continue
                nginxRewrite = bt_conf + '/rewrite_' + r.split('_')[1]
                conf = public.readFile(panelRewritePath + '/' + r)
                public.writeFile(nginxRewrite, conf)
        except:
            pass

        # 备份apache配置文件
        php_httpdConf = bt_conf + '/php_apache.conf'
        java_httpdConf = bt_conf + '/java_apache.conf'
        node_httpdConf = bt_conf + '/node_apache.conf'
        phpHttpdConf = '/www/server/panel/vhost/apache/' + name + '.conf'
        javaHttpdConf = '/www/server/panel/vhost/apache/java_' + name + '.conf'
        nodeHttpdConf = '/www/server/panel/vhost/apache/node_' + name + '.conf'

        if os.path.exists(phpHttpdConf):
            conf = public.readFile(phpHttpdConf)
            public.writeFile(php_httpdConf, conf)
        if os.path.exists(javaHttpdConf):
            conf = public.readFile(javaHttpdConf)
            public.writeFile(java_httpdConf, conf)
        if os.path.exists(nodeHttpdConf):
            conf = public.readFile(nodeHttpdConf)
            public.writeFile(node_httpdConf, conf)

        # 备份apache伪静态
        httpdRewrite = bt_conf + '/.htaccess'
        rewriteConf = '/www/wwwroot/' + name + '/.htaccess'

        if os.path.exists(rewriteConf):
            conf = public.readFile(rewriteConf)
            public.writeFile(httpdRewrite, conf)

        # 备份已部署的证书文件
        sslSrcPath = bt_conf + '/cert/'
        sslDstPath = '/www/server/panel/vhost/cert/' + name + '/'
        sslFiles = ['privkey.pem', 'fullchain.pem']
        for sslFile in sslFiles:
            if os.path.exists(sslDstPath + sslFile):
                conf = public.readFile(sslDstPath + sslFile)
                public.writeFile(sslSrcPath + sslFile, conf)
        return True

    # 备份证书夹
    def BackupSsls(self, path):
        sslsSrcPath = path + '/ssl/'
        os.system('mkdir -p ' + sslsSrcPath)
        path = '/www/server/panel/vhost/ssl'
        dirs = os.listdir(path)
        for dire in dirs:
            apath = path + '/' + dire
            if os.path.isdir(apath):
                listapath = os.listdir(apath)
                for i in listapath:
                    if i.find('json'):
                        public.ExecShell('\cp -r %s %s' % (apath, sslsSrcPath))

    # 备份监控日志功能
    def BackupSystem(self, path):
        db_path = '/www/server/panel/data/'
        db_name = db_path + 'system.db'
        if os.path.exists(db_name):
            public.ExecShell('cp -p %s %s' % (db_name, path))
            if os.path.exists(path + '/system.db'):
                return True

    # 备份环境入口
    def Backup_all(self, get):
        backup_path = self.BackupDir()
        backup_dir = backup_path[1]
        print("#########当前__backup_dir时间：" + backup_dir)
        self.BackupLog(backup_path[2])
        self.RePanelFtp(backup_path[2])
        self.RePanelFrewall(backup_path[2])
        self.BackupSystem(backup_path[2])
        data = self.BackupSite(backup_path[2])
        self.BackupSsls(backup_path[2])
        data1 = self.BackupCrontab(backup_path[2])
        if data['site']:
            if len(data['site']) >= 1:
                for i in data['site']:
                    print(i['name'])
                    self.BackupSiteConfig(i['name'], backup_path[2])
        os.system('cd ' + self.__path + ' &&  zip -r %s.zip %s' % (backup_dir, backup_path[2]))
        print("路劲是：" + backup_dir)
        zip_path = backup_path[2] + '.zip'
        os.system('rm -rf %s' % backup_path[2])
        print("压缩包是：" + zip_path)
        return zip_path

    # 查看已经备份的文件
    def GetBuckup(self, get):
        get={}
        get.items()
        clearPath = [{'path': '/www/server/panel/backup/panelBackup', 'find': 'zip'}]
        total = count = 0
        ret = []
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                    if d.find('zip') == -1: continue
                    filename = c['path'] + '/' + d
                    # print(filename)
                    fsize = os.path.getsize(filename)
                    ret_size = {}
                    ret_size['name'] = filename
                    time1 = os.path.getmtime(filename)
                    # c2 = time.localtime(time1)
                    ret_size['time'] = int(time1)
                    ret_size['filename'] = os.path.basename(filename)
                    ret_size['download'] = '/download?filename=' + filename
                    ret_size['size'] = self.ToSize(int(fsize))
                    ret.append(ret_size)

        ret = sorted(ret, key=lambda x: x['time'], reverse=True)
        return ret

    # 上传接口
    def UploadFile(self, get):
        return '/files?action=UploadFile&path=' + self.__Disposable_path + '&codeing=byte'

    # 解压文件
    def Decompression(self, get):
        clearPath = [{'path': self.__Disposable_path, 'find': 'zip'}]
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                    if d.find(c['find']) == -1: continue
                    filename = c['path'] + '/' + d
                    path = d.replace('.zip', '')
                    print(filename)
                    if os.path.exists(self.__reduction_path + '/panel/backup/panelBackup/' + path):
                        public.ExecShell('rm -rf %s' % filename)
                        print(self.__reduction_path + '/panel/backup/panelBackup/' + path)
                    else:
                        # return public.returnMsg(True, "已经存在")
                        f = zipfile.ZipFile(filename, 'r')
                        for file in f.namelist():
                            f.extract(file, self.__reduction_path)
                    backup_path = self.__reduction_path + '/panel/backup/panelBackup/' + path
                    if os.path.exists(backup_path):
                        os.system('rm -rf %s/*' % self.__Disposable_path)
                        get = mobj()
                        get.path = str(path)
                        get.type = get.type
                        ret = self.ImportData(get)
                        return ret
                    else:
                        os.system('rm -rf %s/*' % self.__Disposable_path)
                        return public.returnMsg(False, "解压失败")
        os.system('rm -rf %s/*' % self.__Disposable_path)
        return public.returnMsg(False, "解压失败")

    def GetBackupSite(self, get):
        clearPath = [{'path': '/www/server/panel/backup/ReduCtion/backup/panelBackup', 'find': 'zip'}]
        total = count = 0
        ret = []
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                    filename = c['path'] + '/' + d
                    print(filename)
                    fsize = os.path.getsize(filename)
                    ret_size = {}
                    ret_size['name'] = filename
                    time1 = os.path.getmtime(filename)
                    c2 = time.localtime(time1)
                    ret_size['time'] = int(time1)
                    ret_size['filename'] = os.path.basename(filename)
                    ret_size['download'] = '/download?filename=' + filename
                    ret_size['size'] = public.ExecShell('du -sh  %s' % filename)[0].split()[0]
                    ret.append(ret_size)
        ret = sorted(ret, key=lambda x: x['time'], reverse=True)
        return ret

    # 删除文件
    def DelFile(self, get):
        path = get.filename
        name_path = '/www/server/panel/backup/panelBackup/' + path
        if os.path.exists(name_path):
            os.system('rm -rf %s' % name_path)
        return public.returnMsg(True, "删除成功")

    # 删除文件
    def DelFile2(self, get):
        path = get.filename
        name_path = '/www/server/panel/backup/ReduCtion/panel/backup/panelBackup/' + path
        if os.path.exists(name_path):
            os.system('rm -rf %s' % name_path)
        return public.returnMsg(True, "删除成功")

    # 从本地导入文件
    def LocalImport(self, get):
        # 本地参数加一个type=local
        path = get.path
        type = get.type
        path = self.__path + '/' + path
        if os.path.exists(path):
            os.system('cp -p %s %s' % (path, self.__Disposable_path))
            ret2 = self.Decompression(get)
            if ret2:
                return ret2
        else:
            return public.returnMsg(False, '参数错误')

    # 导入入口
    def ImportData(self, get):
        path = get.path
        type = get.type
        path = '/www/server/panel/backup/ReduCtion/panel/backup/panelBackup/' + path
        if os.path.exists(path):
            log = self.RecoveryPanelLog(path)
            fire = self.RecoveryFirewalld(path)
            ftp = self.RecoveryFtp(path)
            ssls = self.RecoverySSls(path)
            site = self.RecoverySite(path)
            cron = self.RecoveryCron(path)
            system = self.Recoverysystem(path)
            os.system('rm -rf %s' % path)
            ret = {'log': log, 'firewalld': fire, 'ftp': ftp, 'ssls': ssls, 'site': site, 'cron': cron, 'plugin': True, 'system': system}
            if ret:
                if type != 'local':
                    path = '/www/server/panel/backup/ReduCtion/panel/backup/panelBackup/'
                    os.system('rm -rf %s' % path)
            return public.returnMsg(True, ret)
        else:
            return public.returnMsg(False, "导入失败")

    # 恢复系统监控日志
    def Recoverysystem(self, path):
        log_path = path + '/system.db'
        # 零时的system.db
        temporary_log = '/www/server/panel/data/system2.db'
        system_path = '/www/server/panel/data/system.db'
        if os.path.exists(temporary_log):
            public.ExecShell('rm -rf %s' % temporary_log)
        public.ExecShell('cp -p %s %s' % (log_path, temporary_log))
        if os.path.exists(system_path):
            if os.path.getsize(temporary_log) <= 10000: return False
            if os.path.getsize(system_path) <= 10000 and os.path.getsize(temporary_log) > 10000:
                public.ExecShell('rm -rf %s && mv %s %s ' % (system_path, temporary_log, system_path))
                return True
            else:
                if os.path.exists(temporary_log):
                    sql = "select * from cpuio order by id DESC limit 1;"
                    # 判断是是否是同机器
                    try:
                        ret = M('cpuio').query(sql, ())
                        ret2 = M('cpuio', type='system').where('id=?', (ret,)).select()
                        if ret[0][0][-1] == ret2[0][-1]:
                            return True
                        # 不是同机器
                        else:
                            # 当机器的时间点小于备份时
                            ret2 = M('cpuio', type='system').query(sql, ())
                            if ret[0][0][-1] > ret2[0][-1]:
                                public.ExecShell('rm -rf %s && mv %s %s ' % (system_path, temporary_log, system_path))
                            else:
                                return True
                    except:
                        return True

    # 恢复日志
    def RecoveryPanelLog(self, path):
        log_path = path + '/log.json'
        if os.path.exists(log_path):
            print(log_path)
            log_data = json.loads(public.ReadFile(log_path))
            dbsql = public.M('logs')
            if len(log_data) >= 1:
                for i in log_data:
                    dbsql.addAll('type,log,addtime', (i['type'], i['log'], i['addtime']))
                dbsql.commit()
                return True

    # 恢复防火墙配置
    def RecoveryFirewalld(self, path):
        log_path = path + '/firewall.json'
        ret = []
        if os.path.exists(log_path):
            log_data = json.loads(public.ReadFile(log_path))
            if len(log_data) >= 1:
                for i in log_data:
                    ftpinfo = {}
                    if public.M('firewall').where('port=?', (i['port'],)).count():
                        ftpinfo['port'] = i['port']
                        ftpinfo['status'] = False
                        ret.append(ftpinfo)
                        continue
                    print('插入防火墙')
                    ftpinfo['port'] = i['port']
                    ftpinfo['status'] = True
                    ret.append(ftpinfo)
                    fs = firewalls.firewalls()
                    get = mobj()
                    get.port = str(i['port'])
                    get.ps = str(i['ps'])
                    fs.AddAcceptPort(get)
                    print(ret)
                return ret
        else:
            return False

    # 恢复FTP数据
    def RecoveryFtp(self, path):
        ret = []
        log_path = path + '/ftp.json'
        print('恢复FTP')
        if os.path.exists(log_path):
            log_data = json.loads(public.ReadFile(log_path))
            if len(log_data) >= 1:
                for i in log_data:
                    ftpinfo = {}
                    if public.M('ftps').where('name=?', (i['name'],)).count():
                        ftpinfo['ftp_name'] = i['name']
                        ftpinfo['status'] = False
                        ret.append(ftpinfo)
                        continue
                    ftpinfo['ftp_name'] = i['name']
                    ftpinfo['status'] = True
                    ret.append(ftpinfo)
                    public.M('ftps').add('status,ps,name,addtime,path,password', (i['status'], i['ps'], i['name'], i['addtime'], i['path'], i['password']))
                    public.ExecShell('/www/server/pure-ftpd/bin/pure-pw useradd ' \
                                     + i['name'] + ' -u www -d ' + i['path'] + \
                                     '<<EOF \n' + i['password'] + '\n' + i['password'] + '\nEOF')
                    public.ExecShell('/www/server/pure-ftpd/bin/pure-pw mkdb /www/server/pure-ftpd/etc/pureftpd.pdb')
                return ret
            else:
                return ret
        else:
            return False

    # 恢复网站和配置文件信息
    def RecoverySite(self, path):
        ret = []
        site_path = path + '/site.json'
        if os.path.exists(site_path):
            site_data = json.loads(public.ReadFile(site_path))

            if len(site_data['site']) >= 1:
                for i in site_data['site']:
                    ftpinfo = {}
                    if public.M('sites').where('name=?', (i['name'],)).count():
                        ftpinfo['site_name'] = i['name']
                        ftpinfo['status'] = False
                        ret.append(ftpinfo)
                        continue
                    ftpinfo['site_name'] = i['name']
                    ftpinfo['status'] = True
                    ret.append(ftpinfo)
                    data = public.M('sites').add('name,path,status,ps,addtime,project_type,project_config', (i['name'], i['path'], i['status'], i['ps'], i['addtime'], i['project_type'], i['project_config']))
                    pid_data = public.M('sites').where('name=?', (i['name'],)).field('id').select()[0]['id']
                    for i2 in site_data['domain']:
                        if i['id'] == i2['pid']:
                            public.M('domain').add('pid,name,port,addtime', (pid_data, i2['name'], i2['port'], i2['addtime']))
                            self.RecoverySSl(path, i['name'])
                return ret
            else:
                return ret
        else:
            return False

    # 恢复cron配置文件信息
    def RecoveryCron(self, path):
        ret = []
        cron_path = path + '/cron.json'
        if os.path.exists(cron_path):
            cron_data = json.loads(public.ReadFile(cron_path))
            if len(cron_data['cron']) >= 1:
                for i in cron_data['cron']:
                    croninfo = {}
                    i['hour'] = i['where_hour']
                    i['minute'] = i['where_minute']
                    i['week'] = i['where1']
                    if public.M('crontab').where('echo=?', (i['echo'],)).count():
                        croninfo['name'] = i['name']
                        croninfo['echo'] = i['echo']
                        croninfo['status'] = False
                        ret.append(croninfo)
                        continue
                    croninfo['name'] = i['name']
                    croninfo['echo'] = i['echo']
                    croninfo['status'] = True
                    ret.append(croninfo)
                    crontab.crontab().AddCrontab(i)
                if os.path.exists('/etc/init.d/crond'): 
                    if not public.process_exists('crond'): public.ExecShell('/etc/init.d/crond start')
                elif os.path.exists('/etc/init.d/cron'):
                    if not public.process_exists('cron'): public.ExecShell('/etc/init.d/cron start')
                elif os.path.exists('/usr/lib/systemd/system/crond.service'):
                    if not public.process_exists('crond'): public.ExecShell('systemctl start crond')
                elif os.path.exists('/lib/systemd/system/cron.service'):
                    if not public.process_exists('cron'): public.ExecShell('systemctl start cron')
                return ret
            else:
                return ret
        else:
            return False

    # 恢复站点伪静态SSl
    def RecoverySSl(self, path, site):
        print("恢复站点伪静态SSl")
        ssl_path = path + '/' + site
        php_nginxConf = ssl_path + '/bt_conf/php_nginx.conf'
        java_nginxConf = ssl_path + '/bt_conf/java_nginx.conf'
        node_nginxConf = ssl_path + '/bt_conf/node_nginx.conf'
        phpNginxConf = '/www/server/panel/vhost/nginx/' + site + '.conf'
        javaNginxConf = '/www/server/panel/vhost/nginx/java_' + site + '.conf'
        nodeNginxConf = '/www/server/panel/vhost/nginx/node_' + site + '.conf'
        if os.path.exists(php_nginxConf):
            conf = public.readFile(php_nginxConf)
            public.writeFile(phpNginxConf, conf)

        if os.path.exists(java_nginxConf):
            conf = public.readFile(java_nginxConf)
            public.writeFile(javaNginxConf, conf)

        if os.path.exists(node_nginxConf):
            conf = public.readFile(node_nginxConf)
            public.writeFile(nodeNginxConf, conf)

        # 恢复nginx伪静态文件
        php_nginxRewrite = ssl_path + '/bt_conf/php_rewrite.conf'
        java_nginxRewrite = ssl_path + '/bt_conf/java_rewrite.conf'
        node_nginxRewrite = ssl_path + '/bt_conf/node_rewrite.conf'
        phpNginxRewrite = '/www/server/panel/vhost/rewrite/' + site + '.conf'
        javaNginxRewrite = '/www/server/panel/vhost/rewrite/java_' + site + '.conf'
        nodeNginxRewrite = '/www/server/panel/vhost/rewrite/node_' + site + '.conf'
        if os.path.exists(php_nginxRewrite):
            conf = public.readFile(php_nginxRewrite)
            public.writeFile(phpNginxRewrite, conf)

        if os.path.exists(java_nginxRewrite):
            conf = public.readFile(java_nginxRewrite)
            public.writeFile(javaNginxRewrite, conf)

        if os.path.exists(node_nginxRewrite):
            conf = public.readFile(node_nginxRewrite)
            public.writeFile(nodeNginxRewrite, conf)


        # 恢复子目录伪静态规则
        try:
            backupRewrite = ssl_path + '/bt_conf'
            rs = os.listdir(backupRewrite)
            for r in rs:
                if r.find('rewrite_') == -1: continue
                nginxRewrite = '/www/server/panel/vhost/rewrite/' + site + '_' + r.split('_')[1]
                conf = public.readFile(backupRewrite + '/' + r)
                public.writeFile(nginxRewrite, conf)
        except:
            pass

        # 恢复apache配置文件
        php_httpdConf = ssl_path + '/bt_conf/php_apache.conf'
        java_httpdConf = ssl_path + '/bt_conf/java_apache.conf'
        node_httpdConf = ssl_path + '/bt_conf/node_apache.conf'
        phpHttpdConf = '/www/server/panel/vhost/apache/' + site + '.conf'
        javaHttpdConf = '/www/server/panel/vhost/apache/java_' + site + '.conf'
        nodeHttpdConf = '/www/server/panel/vhost/apache/node_' + site + '.conf'
        if os.path.exists(php_httpdConf):
            conf = public.readFile(php_httpdConf)
            public.writeFile(phpHttpdConf, conf)

        if os.path.exists(java_httpdConf):
            conf = public.readFile(java_httpdConf)
            public.writeFile(javaHttpdConf, conf)

        if os.path.exists(node_httpdConf):
            conf = public.readFile(node_httpdConf)
            public.writeFile(nodeHttpdConf, conf)

        # 恢复证书文件
        sslSrcPath = ssl_path + '/bt_conf/cert/'
        sslDstPathone = '/www/server/panel/vhost/cert/' + site + '/'
        if not os.path.exists(sslDstPathone):
            os.system('mkdir -p ' + sslDstPathone)
        sslFilesone = ['privkey.pem', 'fullchain.pem']
        for sslFileson in sslFilesone:
            if os.path.exists(sslSrcPath + sslFileson):
                conf = public.readFile(sslSrcPath + sslFileson)
                public.writeFile(sslDstPathone + sslFileson, conf)
        public.serviceReload()
        return True

    # 还原证书夹
    def RecoverySSls(self,path):
        sslsSrcPath = path + '/ssl/'
        path = '/www/server/panel/vhost/ssl'
        dirs = os.listdir(sslsSrcPath)
        for i in dirs:
            ssls = sslsSrcPath + i
            if os.path.isdir(ssls):
                public.ExecShell('\cp -r %s %s' % (ssls, path))
        return True
        
