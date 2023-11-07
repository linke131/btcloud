#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 邹浩文 <627622230@qq.com>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   微擎优化脚本v1
# +--------------------------------------------------------------------
import json,sys,re,os,time
sys.path.append('/www/server/panel/class')
import public

class OPTCancel:

    # def _read_conf(self):
    #     conf = public.readFile("/www/server/panel/plugin/site_optimization/config.json")
    #     if not conf:
    #         return False
    #     return json.loads(conf)

    def opt_cancel(self,get):
        version = OPTCheck().get_php_v(get.sitename)
        opt_fun = get.opt_fun
        for o in opt_fun:
            if o == "php_concurrency":
                # 还原php-fpm配置
                self.restore_conf('/www/server/php/{}/etc/php-fpm.conf'.format(version))
            if o == "self_db_cache":
                # 还原mysql配置
                self.restore_conf('/etc/my.cnf')
            if o == "db_cache":
                # 卸载插件
                self._uninstall_ext(get,"redis",version)
                # 还原微擎配置
                self.restore_conf(get.sitepath + "/data/config.php")
            if o == "php_cache":
                self._uninstall_ext(get,"opcache",version)
            # 还原php主配置
            # self.restore_conf('/www/server/php/{}/etc/php.ini'.format(version))
        public.ExecShell("/etc/init.d/php-fpm-{} reload".format(version))
        return public.returnMsg(True,"取消成功")

    def _uninstall_ext(self,get,name,version):
        import files
        get.name = name
        get.version = version
        files.files().UninstallSoft(get)

    def restore_conf(self,filename):
        bak_file = filename+"_opt_bak"
        shell = "/usr/bin/cp {} {}".format(bak_file,filename)
        public.ExecShell(shell)

class OPTStart:

    def __init__(self,sitanme):
        self.version = OPTCheck().get_php_v(sitanme)
        self.backexist = None
        self._writelog(empty=True)

    def _writelog(self,content=None,empty=None):
        if empty:
            public.writeFile("/tmp/opt.log", "")
        else:
            public.writeFile("/tmp/opt.log",content+"\n","a+")

    # def _write_records(self,content):
    #     conf = public.readFile(self.opt_records_file)

    def _check_install_finish(self,sname,optname,ext=None):
        n = 0
        while True:
            if self._check_soft_status(sname,ext=ext):
                return True
            time.sleep(1)
            n += 1
            if n > 6000:
                break
        if n > 6000:
            self._writelog("安装{}超过10分钟取消{}优化...".format(sname,optname))
            return False
        return True

    def _install_redis(self,get):
        import panelPlugin
        get.sName = "redis"
        get.version = "5.0"
        get.type = "0"
        panelPlugin.panelPlugin().install_plugin(get)
        if self._check_install_finish("redis","微擎缓存优化"):
            return True

    def _check_soft_status(self,sname,ext=None):
        if ext:
            filename = "/www/server/php/{}/etc/php.ini".format(self.version)
            conf = public.readFile(filename)
            if sname in conf:
                return True
        else:
            pid = "/www/server/{0}/{0}.pid".format(sname)
            if os.path.exists(pid):
                return True

    def _install_ext(self,get,name,so):
        import files
        filename = "/www/server/php/{}/etc/php.ini".format(self.version)
        if not self.backexist:
            self.backup_conf(filename)
            self.backexist = True
        conf = public.readFile(filename)
        if not conf:
            return False
        if so in conf:
            return True
        get.name = name
        get.version = self.version
        get.type = "1"
        files.files().InstallSoft(get)
        if self._check_install_finish(name,"微擎缓存优化",ext=1):
            return True

    def backup_conf(self,file):
        bak_file = file + '_opt_bak'
        def_file = file + '_opt_def'
        if not os.path.exists(def_file):
            shell = "/usr/bin/cp {} {}".format(file, def_file)
            public.ExecShell(shell)
        shell = "/usr/bin/cp {} {}".format(file,bak_file)
        public.ExecShell(shell)

    # 优化数据库外部缓存
    def db_cache(self,get):
        sitepath = get.sitepath
        if not os.path.exists("/www/server/redis/version.pl"):
            if not self._install_redis(get):
                return public.returnMsg(False,"redis 安装超时，请稍后重试")
            self._writelog("安装redis成功")
        if not self._install_ext(get,"redis","redis.so"):
            return public.returnMsg(False, "redis php扩展 安装超时，请稍后重试")
        self._writelog("安装php redis扩展成功")
        reg = "\$config\['setting'\]\['cache'\]\s*=\s*[\'\"]\s*mysql\s*[\'\"];"
        set_redis = "$config['setting']['cache'] = 'redis';"
        filename = sitepath + "/data/config.php"
        #备份配置
        self.backup_conf(filename)
        conf = public.readFile(filename)
        conf = re.sub(reg,set_redis,conf)
        # 获取redis密码
        pwd = ""
        if "requirepass" in conf:
            pwd_reg = "requirepass\s*(.*)"
            pwd = re.search(pwd_reg,conf).groups()[0]
        # 获取绑定ip
        bindip_reg = "bind\s*(.*)"
        bindip = re.search(bindip_reg,conf)
        if bindip:
            bindip = bindip.groups()[0]
        else:
            bindip = "127.0.0.1"
        # 检查是否有redis配置
        if "CONFIG REDIS" not in conf:
            redis_cache_conf = """
    // --------------------------  CONFIG REDIS  --------------------------- //
    $config['setting']['redis']['server'] = '{}';//如果redis服务器在别的机器，请填写机器的IP地址。
    $config['setting']['redis']['port'] = 6379;
    $config['setting']['redis']['pconnect'] = 0;
    $config['setting']['redis']['timeout'] = 1;
    $config['setting']['redis']['requirepass'] = '{}';
    $config['setting']['redis']['session'] = 1; //session存储方式redis
    """.format(bindip,pwd)
            public.writeFile(filename,conf+redis_cache_conf)
        else:
            public.writeFile(filename, conf)
        public.ExecShell("/etc/init.d/php-fpm-{} restart".format(self.version))
        self._writelog("微擎缓存优化成功")
        return public.returnMsg(True,"微擎缓存优化成功")

    # 优化php缓存
    def php_cache(self,get):
        if not self._install_ext(get,"opcache","opcache.so"):
            return public.returnMsg(False,"php 扩展 opcache安装超时")
        public.ExecShell("/etc/init.d/php-fpm-{} restart".format(self.version))
        return public.returnMsg(True, "php 扩展 opcache安装成功")

    # 优化php并发
    def php_concurrency(self,get):
        mem_total = int(OPTCheck().get_mem())
        if mem_total <= 1024:
            get.max_children = '30'
            get.start_servers = '5'
            get.min_spare_servers = '5'
            get.max_spare_servers = '20'
        elif 1024 < mem_total <= 2048:
            get.max_children = '50'
            get.start_servers = '5'
            get.min_spare_servers = '5'
            get.max_spare_servers = '30'
        elif 2048 < mem_total <= 4098:
            get.max_children = '80'
            get.start_servers = '10'
            get.min_spare_servers = '10'
            get.max_spare_servers = '30'
        elif 4098 < mem_total <= 8096:
            get.max_children = '120'
            get.start_servers = '10'
            get.min_spare_servers = '10'
            get.max_spare_servers = '30'
        elif 8096 < mem_total <= 16192:
            get.max_children = '200'
            get.start_servers = '15'
            get.min_spare_servers = '15'
            get.max_spare_servers = '50'
        elif 16192 < mem_total <= 32384:
            get.max_children = '300'
            get.start_servers = '20'
            get.min_spare_servers = '20'
            get.max_spare_servers = '50'
        elif 32384 < mem_total:
            get.max_children = '500'
            get.start_servers = '20'
            get.min_spare_servers = '20'
            get.max_spare_servers = '50'
        get.version = self.version
        get.pm = "dynamic"
        import config
        self.backup_conf('/www/server/php/{}/etc/php-fpm.conf'.format(self.version))
        result = config.config().setFpmConfig(get)
        if not result['status']:
            self._writelog("php 并发优化失败 {}".format(result))
            return result
        self._writelog("php 并发优化成功")
        return public.returnMsg(True, "php 并发优化成功")

    # 优化数据库自身缓存
    def self_db_cache(self,get):
        mem_total = int(OPTCheck().get_mem())
        if mem_total <= 2048:
            get.key_buffer_size = '128'
            get.query_cache_size = '64'
            get.tmp_table_size = '64'
            get.innodb_buffer_pool_size = '256'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '768'
            get.read_buffer_size = '768'
            get.read_rnd_buffer_size = '512'
            get.join_buffer_size = '1024'
            get.thread_stack = '256'
            get.binlog_cache_size = '64'
            get.thread_cache_size = '64'
            get.table_open_cache = '128'
            get.max_connections = '100'
            get.query_cache_type = '1'
            get.max_heap_table_size = '64'
        elif 2048 < mem_total <= 4096:
            get.key_buffer_size = '256'
            get.query_cache_size = '128'
            get.tmp_table_size = '384'
            get.innodb_buffer_pool_size = '384'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '768'
            get.read_buffer_size = '768'
            get.read_rnd_buffer_size = '512'
            get.join_buffer_size = '2048'
            get.thread_stack = '256'
            get.binlog_cache_size = '64'
            get.thread_cache_size = '96'
            get.table_open_cache = '192'
            get.max_connections = '200'
            get.query_cache_type = '1'
            get.max_heap_table_size = '384'
        elif 4096 < mem_total <= 8192:
            get.key_buffer_size = '384'
            get.query_cache_size = '192'
            get.tmp_table_size = '512'
            get.innodb_buffer_pool_size = '512'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '1024'
            get.read_buffer_size = '1024'
            get.read_rnd_buffer_size = '768'
            get.join_buffer_size = '2048'
            get.thread_stack = '256'
            get.binlog_cache_size = '128'
            get.thread_cache_size = '128'
            get.table_open_cache = '384'
            get.max_connections = '300'
            get.query_cache_type = '1'
            get.max_heap_table_size = '512'
        elif 8192 < mem_total <= 16384:
            get.key_buffer_size = '512'
            get.query_cache_size = '256'
            get.tmp_table_size = '1024'
            get.innodb_buffer_pool_size = '1024'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '2048'
            get.read_buffer_size = '2048'
            get.read_rnd_buffer_size = '1024'
            get.join_buffer_size = '4096'
            get.thread_stack = '384'
            get.binlog_cache_size = '192'
            get.thread_cache_size = '192'
            get.table_open_cache = '1024'
            get.max_connections = '400'
            get.query_cache_type = '1'
            get.max_heap_table_size = '1024'
        elif 16384 < mem_total <= 32768:
            get.key_buffer_size = '1024'
            get.query_cache_size = '384'
            get.tmp_table_size = '2048'
            get.innodb_buffer_pool_size = '4096'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '4096'
            get.read_buffer_size = '4096'
            get.read_rnd_buffer_size = '2048'
            get.join_buffer_size = '8192'
            get.thread_stack = '512'
            get.binlog_cache_size = '256'
            get.thread_cache_size = '256'
            get.table_open_cache = '2048'
            get.max_connections = '500'
            get.query_cache_type = '1'
            get.max_heap_table_size = '2048'
        elif 32768 < mem_total:
            get.key_buffer_size = '2048'
            get.query_cache_size = '500'
            get.tmp_table_size = '4096'
            get.innodb_buffer_pool_size = '8192'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '8192'
            get.read_buffer_size = '8192'
            get.read_rnd_buffer_size = '4096'
            get.join_buffer_size = '16384'
            get.thread_stack = '1024'
            get.binlog_cache_size = '512'
            get.thread_cache_size = '512'
            get.table_open_cache = '2048'
            get.max_connections = '1000'
            get.query_cache_type = '1'
            get.max_heap_table_size = '4096'
        import database
        self.backup_conf('/etc/my.cnf')
        result = database.database().SetDbConf(get)
        if not result['status']:
            self._writelog("Mysql 优化失败 {}".format(result))
            return result
        public.ExecShell("/etc/init.d/mysqld restart")
        self._writelog("Mysql 优化成功")
        return public.returnMsg(True, "Mysql 优化成功")


    def main(self,sitename,sitepath,opt_list):
        self.version = OPTCheck().get_php_v(sitename)
        for i in opt_list:
            if i == "db_cache":
                exec("self.{}({})".format(i,sitepath))
            exec("self.{}()".format(i))

class OPTCheck:
    # f = "/www/server/panel/plugin/site_optimization/opt_site_script/tmp.json"
    def __init__(self):
        self.data = []

    def get_php_v(self,sitename):
        filename = '/www/server/panel/vhost/nginx/{}.conf'.format(sitename)
        conf = public.readFile(filename)
        if not conf:
            return False
        reg = "include\s+enable-php-(\d+)\.conf;"
        tmp = re.search(reg,conf)
        if not tmp:
            return
        tmp = tmp.groups(1)[0]
        return tmp

    def db_cache(self,sitepath):
        result = {}
        reg = "\$config\['setting'\]\['cache'\]\s*=\s*[\'\"]\s*mysql\s*[\'\"];"
        conffile = sitepath+"/data/config.php"
        conf = public.readFile(conffile)
        # if not self.data:
        #     result['id'] = 1
        # else:
        #     pass
        result["opt_name"] = "微擎缓存优化"
        result["fun"] = "db_cache"
        result["tips"] = "优化微擎的缓存方式，将其设置为redis"
        result["opt"] = 1
        if re.search(reg,conf):
            result["opt"] = 0
        print(result)
        self.data.append(result)

    def get_mem(self):
        import psutil
        mem = psutil.virtual_memory()
        memInfo = {'memTotal':int(mem.total/1024/1024),'memFree':int(mem.free/1024/1024),'memBuffers':int(mem.buffers/1024/1024),'memCached':int(mem.cached/1024/1024)}
        return memInfo['memTotal']

    # 优化php缓存
    def php_cache(self,sitename):
        result = {}
        version = self.get_php_v(sitename)
        reg = "opcache\.enable\s*=\s*1"
        filename = "/www/server/php/{}/etc/php.ini".format(version)
        conf = public.readFile(filename)
        if not conf:
            return False
        result["opt_name"] = "PHP缓存优化"
        result["fun"] = "php_cache"
        result["tips"] = "优化PHP的缓存"
        result["opt"] = 1
        if not re.search(reg,conf):
            result["opt"] = 0
        print(result)
        self.data.append(result)

    # 优化php并发
    def php_concurrency(self,get):
        result = {}
        version = self.get_php_v(get.sitename)
        filename = "/www/server/php/{}/etc/php-fpm.conf".format(version)
        conf = public.readFile(filename)
        reg = "pm\.max_children\s*=\s*(\d+)"
        if not conf:
            return False
        max_children = re.search(reg,conf)
        if not max_children:
            return False
        max_children = max_children.groups(1)[0]
        mem_total = int(self.get_mem())
        result["opt_name"] = "PHP并发优化"
        result["fun"] = "php_concurrency"
        result["tips"] = "根据服务器内存优化PHP的并发数"
        result["opt"] = 1
        if mem_total <= 1024:
            max_children_tmp = 30
        elif 1024 < mem_total <= 2048:
            max_children_tmp = 50
        elif 2048 < mem_total <= 4098:
            max_children_tmp = 80
        elif 4098 < mem_total <= 8096:
            max_children_tmp = 120
        elif 8096 < mem_total <= 16192:
            max_children_tmp = 200
        elif 16192 < mem_total <= 32384:
            max_children_tmp = 300
        elif 32384 < mem_total:
            max_children_tmp = 500
        if str(max_children) != str(max_children_tmp):
            result["opt"] = 0
        self.data.append(result)

    # 优化数据库自身缓存
    def self_db_cache(self,get):
        mem_total = int(self.get_mem())
        if mem_total <= 2048:
            key_buffer_size_tmp = 128
        elif 2048 < mem_total <= 4096:
            key_buffer_size_tmp = 256
        elif 4096 < mem_total <= 8192:
            key_buffer_size_tmp = 384
        elif 8192 < mem_total <= 16384:
            key_buffer_size_tmp = 512
        elif 16384 < mem_total <= 32768:
            key_buffer_size_tmp = 1024
        elif 32768 < mem_total:
            key_buffer_size_tmp = 2048
        filename = "/etc/my.cnf"
        conf = public.readFile(filename)
        if not conf:
            return False
        result = {}
        result["opt_name"] = "Mysql优化"
        result["fun"] = "self_db_cache"
        result["tips"] = "根据服务器内存优化Mysql"
        result["opt"] = 1
        reg = "key_buffer_size\s*=\s*(\d+)M"
        key_buffer_size = re.search(reg,conf)
        if not conf:
            result["opt"] = 0
            print(result)
            self.data.append(result)
            return
        key_buffer_size = key_buffer_size.groups(1)[0]
        if str(key_buffer_size) != str(key_buffer_size_tmp):
            result["opt"] = 0
        print(result)
        self.data.append(result)

    # 获取mysql数据目录
    def get_mysql_storage_dir(self):
        try:
            public.CheckMyCnf()
            myfile = '/etc/my.cnf'
            mycnf = public.readFile(myfile)
            rep = "datadir\s*=\s*(.+)\n"
            datadir = re.search(rep, mycnf).groups()[0]
        except:
            datadir = '/www/server/data'
        return datadir

    # 优化数据库
    def db_index(self):
        import time
        storage_dir = self.get_mysql_storage_dir()
        slow_log_file = storage_dir + "/mysql-slow.log"
        d = public.ExecShell("tail -n 50 {}|grep 'SET timestamp='".format(slow_log_file))
        result = {}
        result["opt_name"] = "Mysql 慢sql优化"
        result["fun"] = "db_index"
        result["tips"] = "目前数据库运行速度良好"
        result["opt"] = 1
        if d:
            d = d[0]
            d = d.split("\n")
            l = [re.search(".*?(\d+)", x).groups(1)[0] for x in d if x]
            now = int(time.time())
            s = [ i for i in l if now - int(i) < 86400]
            if s:
                result["opt"] = 0
                result["tips"] = "请尝试使用【数据库运维工具】 优化数据库"
        print(result)
        self.data.append(result)

    # php版本优化
    def php_version(self,sitename):
        result = {}
        version = self.get_php_v(sitename)
        result["fun"] = "php_version"
        result["tips"] = "建议将php版本升级到7或以上以获取更高性能"
        result["opt_name"] = "PHP版本建议"
        result["opt"] = 1
        if version != "00" and int(version) < 70:
            result["opt"] = 0
        print(result)
        self.data.append(result)

    def main(self,get):
        self.php_version(get.sitename)
        self.db_cache(get.sitepath)
        self.php_cache(get.sitename)
        self.php_concurrency(get)
        self.self_db_cache(get)
        self.db_index()
        return self.data
        # public.writeFile(self.f,json.dumps(self.data))




# class get:
#     pass
#
#
# if __name__ == "__main__":
#     sitepath = sys.argv[1]
#     sitename = sys.argv[2]
#     act = sys.argv[3]
#     if act == "check":
#         OPTCheck().main(get)
#     else:
#         OPTStart().main()


