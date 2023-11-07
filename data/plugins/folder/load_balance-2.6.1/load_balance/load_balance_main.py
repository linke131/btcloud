# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzj and hwliang<2021>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔负载均衡
# +--------------------------------------------------------------------
import sys
import os
import re
import json
import time
import shutil
import types
from typing import Union, Callable, Optional, List, Iterator, Tuple, BinaryIO
from importlib import import_module
os.chdir("/www/server/panel")
sys.path.append("/www/server/panel/class/")
import public, send_mail
try:
    from BTPanel import cache
except:
    pass


def sql_decoration(sql_obj, cls):
    def _all(table_conn):
        res = []
        for data in table_conn.order('id desc').select():
            res.append(cls.new(data))
        return res

    def get_by_id(table_conn, cls_id):
        data = table_conn.where("id=?", (cls_id,)).find()
        if data:
            return cls.new(data)
        return None

    def get_by_name(table_conn, cls_name):
        data = table_conn.where("name=?", (cls_name,)).find()
        if data:
            return cls.new(data)
        return None

    setattr(sql_obj, "all", types.MethodType(_all, sql_obj))
    setattr(sql_obj, "get_by_id", types.MethodType(get_by_id, sql_obj))
    setattr(sql_obj, "get_by_name", types.MethodType(get_by_name, sql_obj))

    return sql_obj


class SqlUtil:
    def __init__(self, db_name: str, cls):
        self._db_name = db_name
        self._obj_class = cls
        self._db_conn = None

    def __call__(self):
        if self._db_conn is not None:
            del self._db_conn
        self._db_conn = sql_decoration(public.M(self._db_name), self._obj_class)
        return self

    def __getattr__(self, item):
        if self._db_conn is not None:
            res = getattr(self._db_conn, item, None)
            if res is not None:
                return res
        raise AttributeError("not found {}".format(item))


class Config:
    log_type = '负载均衡'
    plugin_path = '/www/server/panel/plugin/load_balance'
    nginx_conf_path = '/www/server/panel/vhost/nginx'
    heartbeat = plugin_path + '/heartbeat.json'
    mail_config = '/www/server/panel/data/stmp_mail.json'
    mail_list_data = '/www/server/panel/data/mail_list.json'
    dingding_config = '/www/server/panel/data/dingding.json'
    tcp_load_path = plugin_path + '/tcp_config'
    tcp_load_conf_path = '/www/server/panel/vhost/nginx/tcp'


cfg = Config()


def write_log(log_content):
    public.WriteLog(cfg.log_type, log_content)


################################################################
#  HTTP/HTTPS 负载均衡
################################################################


class KeyObject(object):
    _data_keys_ = tuple()

    def __init__(self, **kwargs):
        self._data = dict()
        for k, v in kwargs.items():
            if k in self._data_keys_:
                self._data[k] = v

    def __setattr__(self, k, v):
        if k in self._data_keys_:
            self._data[k] = v
        else:
            self.__dict__[k] = v

    def __getattr__(self, item):
        if item in self._data_keys_:
            return self._data.get(item, None)
        raise AttributeError("not found {}".format(item))


class UpStream(KeyObject):
    SQL: SqlUtil = None
    _data_keys_ = ("id", "name", "session_type", "expires", "cookie_name", "httponly", "secure", "nodes", "addtime")

    # 调用get_data 后数据结构会变化
    def get_data(self):
        self._data["nodes"] = [i.get_data() for i in self._data["nodes"]]
        return self._data

    @classmethod
    def new(cls, data):
        upstream = cls(**data)
        if "nodes" in data:
            upstream.nodes = [Node(upstream, **n) for n in json.loads(data['nodes'])]
        return upstream

    @staticmethod
    def init_table():
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'upstream')).count():
            sql = '''CREATE TABLE "upstream" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT,
    "session_type" TEXT,
    "expires" INTEGER DEFAULT 12,
    "cookie_name" TEXT DEFAULT "bt_route",
    "httponly" INTEGER DEFAULT 0,
    "secure" INTEGER DEFAULT 0,
    "nodes" TEXT,
    "addtime" INTEGER);'''
            public.M('').execute(sql)

    # 保存到数据库
    def save(self):
        data = {
            "name": self.name,
            "session_type": self.session_type,
            "expires": self.expires if self.expires else 12,
            "cookie_name": self.cookie_name if self.cookie_name else "bt_route",
            "httponly": self.httponly if self.httponly else 1,
            "secure": self.secure if self.secure else 0,
            "nodes": json.dumps([i.get_data() for i in self.nodes]),
        }
        if self.id is None:
            data["addtime"] = int(time.time())
            res = self.SQL().insert(data)
            create = True
        else:
            res = self.SQL().where("id=?", self.id).update(data)
            create = False
        if isinstance(res, str) and res.startswith("error"):
            return False, "数据存储失败"
        if create:
            return True, res
        return True, self.id

    # 从数据库删除
    def delete(self):
        self.SQL().where('id=?', int(self.id)).delete()

    def save_to_config(self) -> Tuple[bool, str]:
        up_file = "{}/upstream_{}.conf".format(cfg.nginx_conf_path, self.name)
        bk_file = '/tmp/ng_file_bk_{}.conf'.format(str(int(time.time())))
        has_bk_file = False
        if os.path.exists(up_file):
            has_bk_file = True
            shutil.copyfile(up_file, bk_file)

        alg = ""
        if self.session_type == "ip_hash":
            alg = "    ip_hash;\n"
        elif self.session_type == "sticky":
            tmp = []
            if int(self.httponly) == 1:
                tmp.append("httponly")
            if int(self.secure) == 1:
                tmp.append("secure")
            other = " " + " ".join(tmp)
            alg = "    sticky name={name} expires={expires}h{other};\n".format(
                name=self.cookie_name, expires=self.expires, other=other
            )
        nodes = "\n".join([node.to_config_str() for node in self.nodes])
        up_body = ('upstream %s {\n' % self.name) + alg + nodes + '\n}'
        public.writeFile(up_file, up_body)
        # 检查nginx配置
        conf_status = public.checkWebConfig()
        if conf_status is not True and has_bk_file:
            shutil.copyfile(bk_file, up_file)
            os.remove(bk_file)
            return False, 'ERROR: 配置出错<br><a style="color:red;">' + conf_status.replace("\n", '<br>') + '</a>'
        if has_bk_file:
            os.remove(bk_file)
        public.serviceReload()
        return True, '配置成功'

    def delete_from_config(self) -> Tuple[bool, str]:
        up_file = "{}/upstream_{}.conf".format(cfg.nginx_conf_path, self.name)
        bk_file = '/tmp/ng_file_bk_{}.conf'.format(str(int(time.time())))
        has_bk_file = False
        if os.path.exists(up_file):
            shutil.copyfile(up_file, bk_file)
            has_bk_file = True
            os.remove(up_file)
        conf_status = public.checkWebConfig()
        if conf_status is not True:
            shutil.copyfile('/tmp/ng_file_bk.conf', up_file)
            os.remove(bk_file)
            return False, 'ERROR: 配置出错<br><a style="color:red;">' + conf_status.replace("\n", '<br>') + '</a>'
        if has_bk_file:
            os.remove(bk_file)
        public.serviceReload()
        self.delete()
        self.delete_push_conf()
        return True, '删除成功!'

    def delete_push_conf(self):
        push_module = import_module(".load_balance_push", package="push")
        push_obj = getattr(push_module, 'load_balance_push')()
        get = public.dict_obj()
        get.upstream_name = self.name
        push_obj.del_push_config(get)

    @property
    def proxy_by_https(self):
        for node in self.nodes:
            if int(node.port) in (443, 8443):
                return True
        return False

    def check_nodes(self, access_codes=tuple(), return_nodes: bool = False) -> Union[str, list, None]:
        res_msg = ''
        res_nodes = []
        for node in self.nodes:
            print(u'正在检测资源[%s]中的节点[%s]...' % (self.name, node.server))
            if not node.ping(access_codes):
                msg = u'负载【%s】中的节点【%s】链接失败！<br/>' % (self.name, node.server)
                print(msg)
                res_msg += msg
                res_nodes.append(node.ping_url)
        if return_nodes:
            return res_nodes
        if res_msg:
            return res_msg

    def get_total(self, day_date=None):
        '''
            @name 获取负载均衡统计信息
            @author hwliang<2021-05-28>
            @param item<dcit> 负载均衡信息
            @return dict
        '''

        result = {
            'day_count': 0,
            'day_error': 0,
            'day_speed': 0,
            'request_timeout': 0,
            'last_request_time': 0,
            'nodes': []
        }
        if not self.nodes:
            return result
        if not day_date:
            day_date = public.format_date('%Y-%m-%d')
        day_time = int(time.time())

        for node in self.nodes:
            tmp = node.get_total(day_date)
            if day_time - tmp['last_request_time'] > 10:
                tmp['day_speed'] = 0
            result['day_count'] += tmp['day_count']
            result['day_error'] += tmp['day_error']
            result['day_speed'] += tmp['day_speed']
            if result['request_timeout'] < tmp['request_timeout']:
                result['request_timeout'] = tmp['request_timeout']
            if result['last_request_time'] < tmp['last_request_time']:
                result['last_request_time'] = tmp['last_request_time']
            result['nodes'].append(tmp)
        return result


UpStream.SQL = SqlUtil("upstream", UpStream)


class Server(KeyObject):
    SQL: SqlUtil = None
    _data_keys_ = ("id", "site_id", "main_domain", "default_upstream", "domains", "locations", "addtime")

    def __init__(self, **kwargs):
        super(Server, self).__init__(**kwargs)
        self._error_code: Optional[List[str]] = None

    def __setattr__(self, k, v):
        if k in self._data_keys_:
            self._data[k] = v
        elif k == "error_code":
            self.set_error_code(v)
        else:
            self.__dict__[k] = v

    # 调用get_data 后数据结构会变化，只能调用一次
    def get_data(self):
        default_upstream_data = self._data["default_upstream"].get_data()
        self._data["nodes"] = default_upstream_data.pop("nodes", [])
        self._data["default_upstream"] = default_upstream_data["name"]
        self._data["upstream_info"] = default_upstream_data
        return self._data

    @classmethod
    def new(cls, data):
        if "domains" in data:
            data["domains"] = json.loads(data["domains"])
        if "domains" in data:
            data["locations"] = json.loads(data["locations"])
            for loc in data["locations"]:
                loc["proxy_pass"] = UpStream.SQL().get_by_name(loc["proxy_pass"])
        if "default_upstream" in data:
            data["default_upstream"] = UpStream.SQL().get_by_name(data["default_upstream"])
        return cls(**data)

    @staticmethod
    def init_table():
        server_table = public.M('sqlite_master').where('type=? AND name=?', ('table', 'server')).find()
        if not server_table:
            sql = '''CREATE TABLE "server" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "site_id" INTEGER,
    "main_domain" TEXT,
    "default_upstream" TEXT,
    "domains" TEXT,
    "locations" TEXT,
    "addtime" INTEGER);'''
            public.M('').execute(sql)
        if server_table and server_table["sql"].find("site_id") == -1:
            alter_sql = 'ALTER TABLE "server" ADD COLUMN "site_id" INTEGER;'
            public.M('').execute(alter_sql)
            servers = public.M("server").select()
            for server in servers:
                site_id = public.M('sites').where('name=?', (server["main_domain"],)).getField('id')
                public.M("server").where("id=?", (server["id"],)).setField("site_id", int(site_id))

    # 保存到数据库
    def save(self):
        data = {
            "main_domain": self.main_domain,
            "default_upstream": self.default_upstream.name,
            "domains": self.domains if isinstance(self.domains, str) else json.dumps(self.domains),
            "locations": json.dumps(self.locations) if self.locations else '[]',
        }
        if self.id is not None:
            res = self.SQL().where("id = ?", self.id).update(data)
        else:
            data["addtime"] = int(time.time())
            res = self.SQL().insert(data)

        if isinstance(res, str) and res.startswith("error"):
            return False, "数据存储失败"
        return True, res

    # 从数据库删除
    def delete(self):
        self.SQL().where('id=?', int(self.id)).delete()

    # 格式化所有location配置
    @staticmethod
    def _format_locations(data) -> str:
        if data['proxy_pass'].proxy_by_https:  # type: data['proxy_pass']: UpStream
            proxy_pass = 'https://' + data['proxy_pass'].name
        else:
            proxy_pass = 'http://' + data['proxy_pass'].name
        return '''
location %s %s {
    proxy_pass %s;
    proxy_set_header Host %s;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header REMOTE-HOST $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
    proxy_cache off;
}\n''' % (data['type'], data['rule'], proxy_pass, data['host'])

    def _format_main_locations(self) -> str:
        return self._format_locations({"type": '', "rule": "/", "proxy_pass": self.default_upstream, "host": "$host"})

    # 将反向代理配置写入配置文件
    def save_proxy_file(self) -> Tuple[bool, str]:
        proxy_dir = "{}/proxy/{}".format(cfg.nginx_conf_path, self.main_domain)
        if not os.path.exists(proxy_dir):
            os.makedirs(proxy_dir)
        locations = "".join([self._format_locations(data) for data in self.locations])
        mian_location = self._format_main_locations()

        conf_body = '''#PROXY-START
%s%s 
set $site_name %s;
include /www/server/panel/vhost/nginx/load_total.lua;
#PROXY-END''' % (locations, mian_location, self.main_domain)
        proxy_conf_file = proxy_dir + '/load_balance.conf'
        bk_file = '/tmp/ng_file_bk_{}.conf'.format(str(int(time.time())))
        has_bk_file = False
        if os.path.exists(proxy_conf_file):
            has_bk_file = True
            shutil.copyfile(proxy_conf_file, bk_file)
        public.writeFile(proxy_conf_file, conf_body)
        # 网站配置文件增加反向代理配置
        site_ng_file = "/www/server/panel/vhost/nginx/{}.conf".format(self.main_domain)
        ng_conf = public.readFile(site_ng_file)
        rep = r"include.*\/proxy\/.*\*.conf;"
        if not re.search(rep, ng_conf):
            ng_proxy_file_str = "/www/server/panel/vhost/nginx/proxy/{}/*.conf;".format(self.main_domain)
            replace_str = "\n\t#引用反向代理规则，注释后配置的反向代理将无效\n\tinclude {}\n\n\tinclude enable-php-".format(
                ng_proxy_file_str)
            ng_conf = ng_conf.replace("include enable-php-", replace_str)
        # static_conf = r'''location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
        #     {
        #         expires      30d;
        #         error_log /dev/null;
        #         access_log /dev/null;
        #     }
        #
        #     location ~ .*\.(js|css)?$
        #     {
        #         expires      12h;
        #         error_log /dev/null;
        #         access_log /dev/null;
        #     }'''
        # # location ~ \.\*\\\.\(([^\s]*\|)*[^\s]*\)\$(.*\n)* *access_log\s*/dev/null;\n *\} # 正则平替方案
        # if static_conf in ng_conf:
        #     ng_conf = ng_conf.replace(static_conf, '')
        ng_conf = re.sub(r"location .{3,10}\((gif|js)[^{]*[^}]*}\n", "", ng_conf)
        public.writeFile(site_ng_file, ng_conf)
        # 检查nginx配置
        conf_status = public.checkWebConfig()
        if has_bk_file and conf_status is not True:
            shutil.copyfile(bk_file, proxy_conf_file)
            os.remove(proxy_conf_file)
            return False, 'ERROR: 配置出错<br><a style="color:red;">' + conf_status.replace("\n", '<br>') + '</a>'
        if has_bk_file:
            os.remove(bk_file)
        public.serviceReload()
        return True, '配置成功'

    # 建立一个空白站点在PHP项目中，方便部署ssl
    def create_relevance_site(self) -> Union[int, dict]:
        port_index = self.domains[0].find(':')
        port = "80" if port_index == -1 else self.domains[port_index + 1:]
        get = public.dict_obj()
        get.webname = json.dumps({'domain': self.main_domain, 'domainlist': self.domains[1:], 'count': len(self.domains)})
        get.port = port
        get.ftp = 'false'
        get.sql = 'false'
        get.version = '00'
        get.ps = '负载均衡[' + self.main_domain + ']的绑定站点'
        get.path = public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + self.main_domain
        import panelSite
        s = panelSite.panelSite()
        result = s.AddSite(get)
        if 'status' in result:
            return result
        site_id = public.M('sites').where('name=?', (self.main_domain,)).getField('id')
        return site_id

    # 删除关联站点
    def delete_relevance_site(self):
        import panelSite
        get = public.dict_obj()
        get.id = self.site_id if self.site_id else public.M('sites').where('name=?', self.main_domain).getField('id')
        get.webname = self.main_domain
        panelSite.panelSite().DeleteSite(get)

    def delete_proxy_file(self):
        conf_file = cfg.nginx_conf_path + '/' + self.main_domain + '.conf'
        if os.path.exists(conf_file):
            os.remove(conf_file)
        public.serviceReload()

    def _get_error_code(self):
        proxy_conf = "{}/proxy/{}/load_balance.conf".format(cfg.nginx_conf_path, self.main_domain)
        conf_data = public.readFile(proxy_conf)
        rep = "proxy_next_upstream(?P<target>[^;]*);"
        res = re.search(rep, conf_data)
        if not res:
            return []
        codes = res.group("target").split(" ")
        err_code = []
        for i in codes:
            if i.startswith("http_"):
                err_code.append(int(i[5:]))
        return err_code

    def get_error_code(self):
        if self._error_code is None:
            self._error_code = self._get_error_code()
        return self._error_code

    def set_error_code(self, values: List[Union[str, int]]):
        if self._error_code is None:
            self._error_code = self._get_error_code()
        new_code = []
        for code in values:
            if isinstance(code, str) and code.isdecimal():
                code = int(code)
            if isinstance(code, int) and 100 <= code < 600:
                new_code.append(code)
        if not new_code:
            return
        conf_str = "proxy_next_upstream error timeout invalid_header %s;" % (
            " ".join(["http_" + str(i) for i in new_code])
        )
        proxy_conf = "{}/proxy/{}/load_balance.conf".format(cfg.nginx_conf_path, self.main_domain)
        conf_data: str = public.readFile(proxy_conf)
        rep = "proxy_next_upstream[^;]*;"
        conf_data = re.sub(rep, conf_str, conf_data, 1)
        public.writeFile(proxy_conf, conf_data)
        public.serviceReload()
        self._error_code = new_code

    error_code = property(get_error_code, set_error_code)


Server.SQL = SqlUtil("server", Server)


class Node(KeyObject):
    _data_keys_ = ("server", "path", "port", "state", "weight", "max_fails", "fail_timeout", "ps")

    def __init__(self, upstream, **kwargs):
        self.upstream: UpStream = upstream
        self.ping_url = None
        super(Node, self).__init__(**kwargs)

    def get_data(self):
        return self._data

    def ping(self, access_codes=tuple()) -> bool:
        if self.port == '443':
            return self._ping_by_https(access_codes)
        return self._ping_by_http(access_codes)

    def get_node_status(self, access_codes=tuple()) -> bool:
        cache_name = "node_{}_{}".format(self.server, self.path)
        res = cache.get(cache_name)
        if res is None:
            status = self.ping(access_codes)
            cache.set(cache_name, status, 60)
            return status
        return res

    def _ping_by_https(self, access_codes) -> bool:
        self.ping_url = "https://{}{}".format(self.server, self.path)
        try:
            from gevent import monkey
            monkey.patch_ssl()
            import requests
            ret = requests.get(url=str(self.ping_url), verify=False, timeout=10)
            if bool(access_codes):
                ac_code = access_codes
            else:
                ac_code = (200, 301, 302, 404, 403)
            if ret.status_code in ac_code:
                return False
            else:
                return True
        except IOError:
            return False

    def _ping_by_http(self, access_codes) -> bool:
        if bool(access_codes):
            ac_code = access_codes
        else:
            ac_code = (200, 301, 302, 404, 403)
        self.ping_url = "http://{}:{}{}".format(self.server, self.port, self.path)
        try:
            if sys.version_info[0] == 2:
                import urllib2
                rec = urllib2.urlopen(self.ping_url, timeout=3)
            else:
                import urllib.request
                rec = urllib.request.urlopen(self.ping_url, timeout=3)
            if rec.getcode() in ac_code:
                return True
            return False
        except Exception as e:
            if hasattr(e, "code"):
                if e.code in ac_code:
                    return False
                else:
                    return True
            return False

    def to_config_str(self) -> str:
        weight_str = "weight=%s" % self.weight
        if int(self.state) == 0:
            weight_str = "down"
        elif int(self.state) == 2:
            weight_str = "backup"
        return '    server {s}:{p} max_fails={mf} fail_timeout={ft}s {w};'.format(
            s=self.server, p=self.port, mf=self.max_fails, ft=self.fail_timeout, w=weight_str)

    # 获取节点的统计信息
    def get_total(self, day_date=None):
        '''
            @name 获取指定节点统计信息
            @author hwliang<2021-05-28>
            @param day_date<string> 日期
            @return dict
        '''
        total_path = '/www/wwwlogs/load_balancing/total/{}/{}.pl'
        if not day_date:
            day_date = public.format_date('%Y-%m-%d')

        load_tmp = {
            "day_count": 0,
            "day_error": 0,
            "day_speed": 0,
            "request_timeout": 0,
            "last_request_time": 0
        }

        load_total_day_file = total_path.format(self.upstream.name, day_date)
        if os.path.exists(load_total_day_file):
            day_tmp = public.readFile(load_total_day_file).split(' ')
            load_tmp['day_count'] = int(day_tmp[0])
            load_tmp['day_error'] = int(day_tmp[1])
            load_tmp['day_speed'] = int(day_tmp[2])
            load_tmp['request_timeout'] = int(day_tmp[3])
            load_tmp['last_request_time'] = int(day_tmp[4])

        tmp = {
            "node": "{}:{}".format(self.server, self.port),
            "day_count": 0,
            "day_error": 0,
            "day_speed": 0,
            "request_timeout": 0,
            "last_request_time": 0,
            "ps": self.ps if self.ps else ""
        }

        total_day_file = total_path.format(tmp['node'].replace(':', '_'), day_date)
        tmp['file'] = total_day_file
        if os.path.exists(total_day_file):
            day_tmp = public.readFile(total_day_file).split(' ')
            tmp['day_count'] = int(day_tmp[0]) + load_tmp['day_count']
            tmp['day_error'] = int(day_tmp[1]) + load_tmp['day_error']
            if load_tmp['last_request_time'] > tmp['last_request_time']:
                tmp['day_speed'] = load_tmp['day_speed']
                tmp['request_timeout'] = load_tmp['request_timeout']
                tmp['last_request_time'] = load_tmp['last_request_time']
            else:
                tmp['day_speed'] = int(day_tmp[2])
                tmp['request_timeout'] = int(day_tmp[3])
                tmp['last_request_time'] = int(day_tmp[4])

        return tmp


class LogCollect:
    """
    排序查询并获取日志内容
    """

    def __init__(self, page, size, log_files):
        self.log_files = log_files
        self.count = 0
        self.t_range = [(page - 1) * size, page * size]
        self.test: List[Optional[Callable]] = [None for _ in range(4)]
        self.all_file_have_been_read = False

    # 返回日志内容
    def __iter__(self):
        _buf = b""
        for file_size, fp in self._get_fp():
            while file_size:
                read_size = min(1024, file_size)
                fp.seek(-read_size, 1)
                buf: bytes = fp.read(read_size) + _buf
                fp.seek(-read_size, 1)
                if file_size > 1024:
                    idx = buf.find(ord("\n"))
                    _buf, buf = buf[:idx], buf[idx + 1:]
                for i in self._get_log_line_from_buf(buf):
                    yield i
                if self.count > self.t_range[1]:
                    return
                file_size -= read_size
        self.all_file_have_been_read = True

    # 从缓冲中读取日志
    def _get_log_line_from_buf(self, buf: bytes) -> Iterator[Optional[List[str]]]:
        n, m = 0, 0
        buf_len = len(buf) - 1
        log_line = []
        for i in range(buf_len, -1, -1):
            if buf[i] == ord("|"):
                log_line.append(buf[buf_len + 1 - m: buf_len - n + 1].decode("utf-8"))
                n = m = m + 1
            elif buf[i] == ord("\n"):
                log_line.append(buf[buf_len + 1 - m: buf_len - n + 1].decode("utf-8"))
                res = self._check_use(log_line)
                if res is not None:
                    yield res
                log_line = list()
                n = m = m + 1
            else:
                m += 1
        log_line.append(buf[0: buf_len - n + 1].decode("utf-8"))
        res = self._check_use(log_line)
        if res is not None:
            yield res

    # 获取所有文件和文件大小
    def _get_fp(self) -> Iterator[Tuple[int, BinaryIO]]:
        for i in self.log_files:
            if not os.path.exists(i):
                continue
            with open(i, 'rb') as fp:
                fp.seek(-1, 2)
                yield os.stat(i).st_size - 1, fp

    # 格式化并筛选查询条件
    def _check_use(self, log_line: List[str]) -> Optional[List[str]]:
        # 重组日志
        uri = "|".join(log_line[-5:5:-1])
        log_line = log_line[-1:-5:-1] + log_line[5::-1] + [uri]
        # 筛选查询条件，暂未使用
        # for i in range(4):
        #     if self.test[i] is None:
        #         continue
        #     if not self.test[i]():
        #         return False
        self.count += 1
        if self.t_range[0] <= self.count - 1 < self.t_range[1]:
            return log_line

    # 设置查询条件，暂未使用
    def set_args(self, target=None, t_type=None, user=None, proc=None):
        pass
        # if target:
        #     self.test[1] = lambda x: x.find(target) != -1
        # if t_type:
        #     self.test[0] = lambda x: x == t_type
        # if user:
        #     self.test[2] = lambda x: x == user
        # if proc:
        #     self.test[3] = lambda x: x.find(proc) != -1
        # if bool(self.test[0]) or bool(self.test[1]) or bool(self.test[2]) or bool(self.test[3]):
        #     self._need = True
        # else:
        #     self._need = False


class WarningMsg:
    def __init__(self, send_type="mail"):
        self._mail = send_mail.send_mail()
        self.send_type = send_type
        self._mail_list = []
        self.title = "负载均衡节点异常"
        self._warp = "</tbody></table><hr><p>此为堡塔面板通知邮件，请勿回复</p>"
        if not os.path.exists(cfg.mail_list_data):
            ret = []
            public.writeFile(cfg.mail_list_data, json.dumps(ret))
        else:
            try:
                mail_data = json.loads(public.ReadFile(cfg.mail_list_data))
                self._mail_list = mail_data
            except json.JSONDecodeError:
                ret = []
                public.writeFile(cfg.mail_list_data, json.dumps(ret))

    # 查看能使用的告警通道
    def get_settings(self, get=None):
        qq_mail_info = json.loads(public.ReadFile(cfg.mail_config))
        user_mail = len(qq_mail_info) != 0
        dingding_info = json.loads(public.ReadFile(cfg.dingding_config))
        dingding = len(dingding_info) != 0
        ret = dict()
        ret['user_mail'] = {
            "user_name": user_mail,
            "mail_list": self._mail_list,
            "info": qq_mail_info if user_mail else False
        }
        ret['dingding'] = {
            "dingding": dingding,
            "info": dingding_info if dingding else False
        }
        return ret

    def __call__(self, check_func: Callable[[], Optional[str]]) -> None:
        msg = check_func()
        if not msg:
            return
        mail_body = msg + self._warp
        msg_pipe = self.get_settings()

        if self.send_type == 'dingding' and msg_pipe['dingding']['dingding']:
            msg = mail_body
            self._mail.dingding_send(msg)
        elif self.send_type == 'mail' and msg_pipe['user_mail']['user_name']:
            if len(self._mail_list) == 0:
                self._mail.qq_smtp_send(
                    str(msg_pipe['user_mail']['info']['qq_mail']),
                    title=self.title, body=mail_body
                )
            else:
                for i in self._mail_list:
                    self._mail.qq_smtp_send(str(i), title=self.title, body=mail_body)


################################################################
#  TCP/UDP 负载均衡
################################################################

class TcpNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def ping(self) -> Tuple[bool, str]:
        import socket
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect((self.ip, self.port))
            s.close()
        except socket.error:
            return False, '无法连接{}:{}，请检查目标机器是否放行端口'.format(self.ip, self.port)
        return True, '访问节点[{}:{}]成功!'.format(self.ip, self.port)


class TcpServer:
    pass


################################################################
#   负载均衡对外接口
################################################################


# 管理对外接口
# 处理请求逻辑
class load_balance_main(object):

    def __init__(self):
        UpStream.init_table()
        Server.init_table()
        s_push_file = "{}/load_balance_push.py".format(cfg.plugin_path)
        d_push_file = "{}/class/push/load_balance_push.py".format(public.get_panel_path())
        tip_file = "{}/push_tip".format(cfg.plugin_path)
        if not os.path.exists(d_push_file):
            shutil.copy(s_push_file, d_push_file)
        elif not os.path.exists(tip_file):
            data = public.readFile(d_push_file)
            if data.find("| version: 2.6.1") == -1:
                shutil.copy(s_push_file, d_push_file)
                public.writeFile(tip_file, "")

    def import_old_data(self, get=None):
        '''
        导入旧的负载均衡的数据
        :param get:
        :return:
        '''
        old_conf_path = '/www/server/panel/plugin/load_leveling/config.json'
        if not os.path.exists(old_conf_path):
            return None
        old_conf = json.loads(public.readFile(old_conf_path))
        for item in old_conf:
            upstream = UpStream()
            upstream.name = item['name']
            if public.M('upstream').where('name=?', upstream.name).count():
                continue
            upstream.session_type = item['session_type']
            upstream.expires = int(item['expires']) if 'expires' in item else 12
            upstream.cookie_name = item['cookie_name'] if 'cookie_name' in item else 'bt_route'
            upstream.httponly = int(item['httponly']) if 'httponly' in item else 1
            upstream.secure = int(item['secure']) if 'secure' in item else 0
            upstream.nodes = [Node(upstream, **i) for i in item['nodes']]
            # 旧的配置文件复制到新的配置文件
            old_up_file = cfg.nginx_conf_path + '/leveling_' + upstream.name + '.conf'
            up_file = cfg.nginx_conf_path + '/upstream_' + upstream.name + '.conf'
            if os.path.exists(old_up_file):
                shutil.copyfile(old_up_file, up_file)
                os.remove(old_up_file)
            # 插入数据到upstream表
            upstream.save()
            write_log("创建负载均衡配置[{}]".format(upstream.name))

    def get_upstream_list(self, get):
        '''
        获取upstream列表
        :param get:
        :return:
        '''
        if public.ExecShell('nginx -V 2>&1|grep nginx-sticky-module')[0] == '':
            return public.returnMsg(False, '当前nginx不支持sticky模块, 请重装nginx!')
        if not os.path.exists('/www/server/nginx/sbin/nginx'):
            return public.returnMsg(False, '本插件基于nginx, 请先安装!')
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 8
        callback = get.callback if 'callback' in get else ''

        all_upstream = UpStream.SQL().all()
        count = len(all_upstream)
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = all_upstream[(p - 1) * rows: p * rows]
        for i in range(len(data_list)):
            total = data_list[i].get_total()
            data_list[i] = data_list[i].get_data()
            data_list[i]['total'] = total

        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    def get_all_upstream(self, get):
        '''
        获取所有的upstream
        :param get:
        :return:
        '''
        all_upstream = UpStream.SQL().all()
        if 'search' in get:
            search_data = []
            for upstream in all_upstream:
                if get['search'] in upstream.name:
                    search_data.append(upstream)
            all_upstream = search_data
        return [i.get_data() for i in all_upstream]

    def get_upstream_find(self, get):
        '''
        获取指定upstream的详情
        :param get:
        :return:
        '''
        upstream = UpStream.SQL().get_by_id(get.id)
        if upstream:
            return upstream.get_data()
        return {}

    @staticmethod
    def _check_upstream(upstream: UpStream, get):
        upstream.session_type = get.session_type
        upstream.expires = int(get.expires) if 'expires' in get else 12
        upstream.cookie_name = get.cookie_name if 'cookie_name' in get else 'bt_route'
        upstream.httponly = int(get.httponly) if 'httponly' in get else 1
        upstream.secure = int(get.secure) if 'secure' in get else 0
        upstream.nodes = [Node(upstream, **i) for i in json.loads(get.nodes)]
        if upstream.session_type == 'ip_hash':
            for node in upstream.nodes:
                if node.state == 2:
                    return public.returnMsg(False, 'IP会话跟随中不能存在备份节点')

    def add_upstream(self, get):
        '''
        新增upstream
        :param get:
        :return:
        '''
        upstream = UpStream()
        upstream.name = get.up_name.strip()
        if not upstream.name:
            return public.returnMsg(False, '资源名称不能为空')
        if os.path.exists(cfg.nginx_conf_path + '/leveling_' + upstream.name + '.conf'):
            return public.returnMsg(False, '旧的负载均衡已经添加名为[%s]的负载均衡，请先删除' % upstream.name)
        if UpStream.SQL().get_by_name(upstream.name):
            return public.returnMsg(False, '资源[%s]已经存在，不能重复添加' % upstream.name)

        self.get_node_list(None)
        res = self._check_upstream(upstream, get)
        if res is not None:
            return res
        # 更新配置文件
        flag, msg = upstream.save_to_config()
        if not flag:
            return public.returnMsg(False, msg)
        flag, up_id = upstream.save()
        if not flag:
            return public.returnMsg(False, up_id)
        write_log("创建负载均衡配置[{}]".format(upstream.name))
        return public.returnMsg(True, up_id)

    def modify_upstream(self, get):
        '''
        编辑upstream
        :param get:
        :return:
        '''
        if 'id' not in get:
            return public.returnMsg(False, '缺少id参数!')
        upstream = UpStream.SQL().get_by_id(get.id)
        if not upstream:
            return public.returnMsg(False, '没有该负载均衡配置!')
        upstream.name = get.up_name.strip()
        if "status_code" in get:
            err_codes = get.status_code.strip()
            try:
                codes = json.loads(err_codes)
                codes = [int(code) for code in codes]
            except json.JSONDecodeError:
                return public.returnMsg(False, 'codes参数错误')
            server_data = Server.SQL().where("default_upstream=?", (upstream.name,)).find()
            Server.new(server_data).error_code = codes
        res = self._check_upstream(upstream, get)
        if res is not None:
            return res
        # 更新配置文件
        flag, msg = upstream.save_to_config()
        if not flag:
            return public.returnMsg(False, msg)
        flag, up_id = upstream.save()
        if not flag:
            return public.returnMsg(False, up_id)
        write_log("修改负载均衡配置[{}]".format(upstream.name))
        return public.returnMsg(True, "修改成功!")

    def delete_upstream(self, get):
        '''
        删除upstream
        :param get: id
        :return:
        '''
        if 'id' not in get:
            return public.returnMsg(False, '缺少id参数!')
        upstream = UpStream.SQL().get_by_id(get.id)
        if not upstream:
            return public.returnMsg(False, '没有该负载均衡配置!')
        # 删除告警任务
        push_module = import_module(".load_balance_push", package="push")
        push_obj = getattr(push_module, 'load_balance_push')()
        get.upstream_name = upstream.name
        push_obj.del_push_config(get)
        # 出错未处理
        upstream.delete_from_config()
        write_log("删除负载均衡配置[{}]".format(upstream.name))
        return public.returnMsg(True, '删除成功!')

    def check_url(self, get):
        '''
        检测节点
        :param get:
        :return:
        '''
        if not get.path:
            return public.returnMsg(False, '不能为空')
        if str(get.path[0]) != '/':
            return public.returnMsg(False, '例如/aa.txt')
        node = Node(None)
        node.server = get.ip.strip()
        node.port = get.port.strip()
        node.path = get.path.strip()
        if not node.ping():
            return public.returnMsg(False, '访问节点[%s]失败' % node.ping_url)
        return public.returnMsg(True, '访问节点[%s]成功' % node.ping_url)

    def check_tcp(self, get):
        import socket
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect((get.ip.strip(), int(get.port)))
            s.close()
        except:
            return public.returnMsg(False, '无法连接{}:{}，请检查目标机器是否放行端口'.format(get.ip, get.port))
        return public.returnMsg(True, '访问节点[{}:{}]成功!'.format(get.ip, get.port))

    # todo:
    @staticmethod
    def _get_mod() -> dict:
        from BTPanel import session
        from panelAuth import panelAuth
        skey = 'bt_load_balcnce_res'
        if skey in session:
            return public.returnMsg(True, 'OK!')
        params = {'pid': '100000009'}
        result = panelAuth().send_cloud('check_plugin_status', params)
        try:
            if not result['status']:
                if skey in session:
                    del (session[skey])
                return result
        except:
            pass
        session[skey] = True
        return result

    @staticmethod
    def _sqlite_like_replace(data_str: str) -> str:
        key_list = ('/', '%', '(', ')', '[', ']', '&', '_')
        res = ''
        for c in data_str:
            if c in key_list:
                res += "/" + c
            elif c == "'":
                res += "''"
            else:
                res += c
        return res

    def get_server_list(self, get):
        '''
        获取server列表
        :param get: p：页码  size：分页大小
        :return:
        '''
        if public.ExecShell('nginx -V 2>&1|grep nginx-sticky-module')[0] == '':
            return public.returnMsg(False, '当前nginx不支持sticky模块, 请重装nginx!')
        if not os.path.exists('/www/server/nginx/sbin/nginx'):
            return public.returnMsg(False, '本插件基于nginx, 请先安装!')
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 8
        callback = get.callback if 'callback' in get else ''
        search = get.search if 'search' in get else None
        result = self._get_mod()
        if not result['status']:
            return result
        count = Server.SQL().count()
        limit_str = "{},{}".format((p - 1) * rows, rows)
        if search is not None and bool(search):
            like_name = self._sqlite_like_replace(search)
            like_str1 = "default_upstream LIKE '%{}%' ESCAPE '/'".format(like_name)
            like_str2 = "main_domain LIKE '%{}%' ESCAPE '/'".format(like_name)
            count = Server.SQL().where("{} OR {}".format(like_str1, like_str2), ()).count()
            data_list = Server.SQL().where("{} OR {}".format(like_str1, like_str2), ()).limit(limit_str).all()
        else:
            data_list = Server.SQL().limit(limit_str).all()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        for i in range(len(data_list)):
            # if data_list[i].default_upstream is None:
            #     continue
            total = data_list[i].default_upstream.get_total()
            if 'status' in total:
                total = {}
            data_list[i] = data_list[i].get_data()
            data_list[i]["total"] = total
        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    def get_node_list(self, get):
        '''
            @name 获取节点列表
            @author hwliang<2021-05-28>
            @param get
            @return list
        '''
        all_upstreams = UpStream.SQL().all()
        nodes = []
        revs = []
        for upstream in all_upstreams:
            main_domain = Server.SQL().where('default_upstream=?', upstream.name).getField('main_domain')
            if not main_domain:
                up_file = cfg.nginx_conf_path + '/upstream_' + upstream.name + '.conf'
                if os.path.exists(up_file):
                    os.remove(up_file)
                upstream.delete()
                continue
            for node in upstream.nodes:
                if "{}:{}".format(node.server, node.port) in revs:
                    continue
                total_arr = node.get_total()
                status = node.get_node_status()
                node_data = node.get_data()
                node_data['node'] = total_arr['node']
                node_data['day_count'] = total_arr['day_count']
                node_data['day_error'] = total_arr['day_error']
                node_data['day_speed'] = total_arr['day_speed']
                node_data['last_request_time'] = total_arr['last_request_time']
                node_data['request_timeout'] = total_arr['request_timeout']
                node_data['main_domain'] = main_domain
                node_data['status'] = status
                node_data['id'] = upstream.id
                revs.append(node_data['node'])
                nodes.append(node_data)

        del revs
        return sorted(nodes, key=lambda x: x['day_count'], reverse=True)

    def get_push_project(self, get=None):
        all_upstream = UpStream.SQL().all()
        res = []
        if not all_upstream:
            return res
        res.append({
            "title": "所有已配置的负载",
            "value": "all"
        })
        for upstream in all_upstream:
            res.append({
                "title": upstream.name,
                "value": upstream.name
            })
        return res

    @staticmethod
    def get_check_upstream(get):
        if get.upstream_name == "all":
            _upstreams = UpStream.SQL().all()
        else:
            upstream = UpStream.SQL().get_by_name(get.upstream_name)
            _upstreams = []
            if upstream is not None:
                _upstreams.append(upstream)
        if not _upstreams:
            return []
        return _upstreams

    def set_push_config(self, get):
        conf_path = "{}/class/push/push.json".format(public.get_panel_path())
        pdata: dict = json.loads(get.data)
        if 'cycle' not in pdata:
            pdata['cycle'] = "200|301|302|404|403"
        if 'interval' not in pdata:
            pdata['interval'] = 60
        if 'push_count' not in pdata:
            pdata['push_count'] = 2
        if 'key' not in pdata:
            pdata['key'] = ""
        if 'count' not in pdata:
            pdata['count'] = 1
        get.name = 'load_balance_push'
        push_module = import_module(".load_balance_push", package="push")
        push_obj = getattr(push_module, 'load_balance_push')()
        get['data'] = json.dumps(pdata)
        result = push_obj.set_push_config(get)
        if 'status' in result:
            return result
        data = result
        public.writeFile(conf_path, json.dumps(data))
        return public.returnMsg(True, '保存成功.')

    def set_node_ps(self, get):
        if 'id' not in get:
            return public.returnMsg(False, '缺少id参数!')
        node_ip = getattr(get, 'server', "").strip()
        node_port = getattr(get, 'port', 0)
        node_ps = getattr(get, 'ps', "").strip()
        upstream = UpStream.SQL().get_by_id(get.id)
        if not upstream:
            return public.returnMsg(False, '没有指定的负载均衡配置!')
        for node in upstream.nodes:
            if node.server == node_ip and int(node.port) == int(node_port):
                node.ps = node_ps
                break
        else:
            return public.returnMsg(False, '未找到该节点')
        flag, msg = upstream.save()
        if not flag:
            return public.returnMsg(False, '备注保存失败')
        return public.returnMsg(True, '保存成功')

    def get_total_today(self, get):
        '''
            @name 获取指定日期的负载均衡统计信息
            @author hwliang<2021-05-28>
            @param get<dict_obj>{
                upstream_name 资源名称
                day_date 日期
            }
        '''
        if 'upstream_name' not in get:
            return public.returnMsg(False, '资源名称不能为空')
        upstream = UpStream.SQL().get_by_name(get.upstream_name)
        if not upstream:
            return public.returnMsg(False, '没有该负载均衡配置')

        if 'day_date' not in get:
            get.day_date = public.format_date('%Y-%m-%d')

        return upstream.get_total(get.day_date)

    def get_load_logs(self, get):
        '''
            @name 获取指定日期的负载均衡访问日志
            @author hwliang<2021-05-28>
            @param get<dict_obj>{
                main_domain 负载均衡主域名
                day_date 日期
                p 分页
            }
        '''
        public.print_log(get.__dict__)

        if 'main_domain' not in get:
            return public.returnMsg(False, '主域名不能为空')

        if 'day_date' not in get:
            get.day_date = public.format_date('%Y-%m-%d')

        logs_path = '/www/wwwlogs/load_balancing/logs/{}'.format(get.main_domain)
        load_log_file = '{}/{}.log'.format(logs_path, get.day_date)
        result = {'total_size': 0, 'size': 0, 'data': [], 'end': False}
        if not os.path.exists(logs_path):
            return result
        for logs_name in os.listdir(logs_path):
            filename = logs_path + '/' + logs_name
            if os.path.isdir(filename):
                continue
            result['total_size'] += os.path.getsize(filename)
        if os.path.exists(load_log_file):
            result['size'] = os.path.getsize(load_log_file)
        else:
            return result

        page, size = 1, 10
        if 'p' in get:
            page = int(get.p)
        logs = LogCollect(page, size, [load_log_file, ])
        result['data'] = [i for i in logs]
        result['end'] = logs.all_file_have_been_read
        result['continue_page'] = page + 1
        return result

    def add_server(self, get):
        '''
        新增server
        :param get:
        :return:
        '''
        if 'domains' not in get:
            return public.returnMsg(False, '缺少域名参数')
        if 'default_upstream' not in get:
            return public.returnMsg(False, '缺少默认节点资源参数')
        server = Server()
        domain_list = json.loads(get.domains)
        server.main_domain = domain_list[0].split(':')[0]

        if public.M('domain').where('name=?', server.main_domain).count():
            return public.returnMsg(False, '指定域名已经在网站列表中添加过了，不能重复添加!')

        for domain in domain_list:
            if public.M('domain').where('name=?', domain.split(':')[0]).count():
                return public.returnMsg(False, '指定域名已经在网站列表中添加过了，不能重复添加!')

        if public.M('server').where('main_domain=?', server.main_domain).count():
            return public.returnMsg(False, '指定的负载均衡已经存在，不能重复添加')
        default_upstream = UpStream.SQL().get_by_name(get.default_upstream.strip())
        if not default_upstream:
            return public.returnMsg(False, '负载均衡节点未保存成功，请重试。')
        server.domains = domain_list
        server.default_upstream = default_upstream
        server.locations = json.loads(get.locations) if 'locations' in get else []
        # 创建网站
        result = server.create_relevance_site()
        if isinstance(result, dict):
            return result
        else:
            server.site_id = result
        # 创建proxy配置文件
        flag, msg = server.save_proxy_file()
        if not flag:
            server.delete_relevance_site()
            return public.returnMsg(False, msg)
        server.save()
        write_log("创建网站负载均衡[{}]".format(server.main_domain))
        return public.returnMsg(True, '添加成功!')

    def modify_server(self, get):
        '''
        编辑server
        :param get:
        :return:
        '''
        if 'id' not in get:
            return public.returnMsg(False, '缺少id参数!')
        server = Server.SQL().get_by_id(get.id)
        if not server:
            return public.returnMsg(False, '没有指定的负载均衡配置')

        server.default_upstream = get.default_upstream
        server.locations = get.locations
        flag, msg = server.save_proxy_file()
        if not flag:
            return public.returnMsg(False, msg)
        server.save()
        write_log("修改网站负载均衡[{}]".format(server.main_domain))
        return public.returnMsg(True, '修改成功!')

    def delete_server(self, get):
        '''
        删除server
        :param get:
        :return:
        '''
        if 'id' not in get:
            return public.returnMsg(False, '缺少id参数!')
        server_id = int(get.id)
        server = Server.SQL().get_by_id(server_id)
        server.delete_proxy_file()
        server.delete_relevance_site()
        server.delete()
        server.default_upstream.delete_from_config()  # 出错未处理
        write_log("删除网站负载均衡[{}]".format(server.main_domain))
        return public.returnMsg(True, '删除成功!')

    def sever_err_code(self, get):
        """获取网站现在已经设置的检测错误的错误码"""
        if 'id' not in get:
            return public.returnMsg(False, '缺少id参数!')
        server_id = int(get.id)
        server = Server.SQL().get_by_id(server_id)
        if not server:
            return public.returnMsg(False, '没有这个负载均衡服务!')
        return {"code": server.error_code, "status": True}

    # def set_sever_err_code(self, get):
    #     """设置网站现在已经设置的检测错误的错误码"""
    #     if 'id' not in get:
    #         return public.returnMsg(False, '缺少id参数!')
    #     if 'codes' not in get:
    #         return public.returnMsg(False, '缺少codes参数!')
    #     try:
    #         codes = json.loads(get.codes)
    #     except json.JSONDecodeError:
    #         return public.returnMsg(False, 'codes参数错误')
    #     server_id = int(get.id)
    #     server: Server = Server.SQL().get_by_id(server_id)
    #     if not server:
    #         return public.returnMsg(False, '没有这个负载均衡服务!')
    #     server.error_code = codes
    #     return public.returnMsg(True, "设置成功")

    def server_set_ssl(self, get):
        '''
        server设置ssl证书
        :param get:
        :return:
        '''
        siteName = get.siteName
        path = '/www/server/panel/vhost/cert/' + siteName
        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"

        if get.key.find('KEY') == -1: return public.returnMsg(False, 'SITE_SSL_ERR_PRIVATE')
        if get.csr.find('CERTIFICATE') == -1: return public.returnMsg(False, 'SITE_SSL_ERR_CERT')
        public.writeFile('/tmp/cert.pl', get.csr)
        if not public.CheckCert('/tmp/cert.pl'): return public.returnMsg(False, '证书错误,请粘贴正确的PEM格式证书!')
        backup_cert = '/tmp/backup_cert_' + siteName

        import shutil
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        if os.path.exists(path): shutil.move(path, backup_cert)
        if os.path.exists(path): shutil.rmtree(path)

        public.ExecShell('mkdir -p ' + path)
        public.writeFile(keypath, get.key)
        public.writeFile(csrpath, get.csr)

        # 写入配置文件
        result = self.set_ssl_conf(get)
        if not result['status']: return result
        isError = public.checkWebConfig()

        if type(isError) == str:
            if os.path.exists(path): shutil.rmtree(backup_cert)
            shutil.move(backup_cert, path)
            return public.returnMsg(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')
        public.serviceReload()

        if os.path.exists(path + '/partnerOrderId'): os.remove(path + '/partnerOrderId')
        if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')
        p_file = '/etc/letsencrypt/live/' + get.siteName
        if os.path.exists(p_file): shutil.rmtree(p_file)

        # 清理备份证书
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        return public.returnMsg(True, 'SITE_SSL_SUCCESS')

    def set_ssl_conf(self, get):
        '''
        添加SSL配置
        :param get:
        :return:
        '''
        siteName = get.siteName
        if 'first_domain' not in get:
            get.first_domain = siteName

        # Nginx配置
        file = '/www/server/panel/vhost/nginx/' + siteName + '.conf'
        ng_file_bk = '/tmp/ng_file_bk_{}.conf'.format(str(int(time.time())))
        has_bk_file = False
        conf = public.readFile(file)

        if conf:
            if conf.find('ssl_certificate') == -1:
                sslStr = """#error_page 404/404.html;
    ssl_certificate    /www/server/panel/vhost/cert/%s/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/%s/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2%s;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";
    error_page 497  https://$host$request_uri;
""" % (get.first_domain, get.first_domain, self.get_tls13())
                if conf.find('ssl_certificate') != -1:
                    public.serviceReload()
                    return public.returnMsg(True, 'SITE_SSL_OPEN_SUCCESS')

                conf = conf.replace('#error_page 404/404.html;', sslStr)
                # 添加端口
                rep = r"listen.*[\s:]+(\d+).*;"
                tmp = re.findall(rep, conf)
                if not public.inArray(tmp, '443'):
                    listen = re.search(rep, conf).group()
                    versionStr = public.readFile('/www/server/nginx/version.pl')
                    http2 = ''
                    if versionStr:
                        if versionStr.find('1.8.1') == -1: http2 = ' http2'
                    default_site = ''
                    if conf.find('default_server') != -1: default_site = ' default_server'

                    listen_ipv6 = ';'
                    if os.path.exists(
                            '/www/server/panel/data/ipv6.pl'): listen_ipv6 = ";\n\tlisten [::]:443 ssl" + http2 + default_site + ";"
                    conf = conf.replace(listen, listen + "\n\tlisten 443 ssl" + http2 + default_site + listen_ipv6)
                shutil.copyfile(file, ng_file_bk)
                has_bk_file = True
                public.writeFile(file, conf)
        isError = public.checkWebConfig()
        if isError is not True:
            if os.path.exists(ng_file_bk):
                shutil.copyfile(ng_file_bk, file)
            public.ExecShell("rm -f /tmp/backup_*.conf")
            return public.returnMsg(False,
                                    '证书错误: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')
        elif has_bk_file:
            os.remove(ng_file_bk)
        # 放行端口
        import firewalls
        get.port = '443'
        get.ps = 'HTTPS'
        firewalls.firewalls().AddAcceptPort(get)
        public.serviceReload()
        result = public.returnMsg(True, 'SITE_SSL_OPEN_SUCCESS')
        result['csr'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem')
        result['key'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem')
        return result

    def get_tls13(self):
        '''
        获取TLS1.3标记
        :return:
        '''
        nginx_bin = '/www/server/nginx/sbin/nginx'
        nginx_v = public.ExecShell(nginx_bin + ' -V 2>&1|grep version:')[0]
        nginx_v = re.search(r'nginx/1\.1(5|6|7|8|9).\d', nginx_v)
        openssl_v = public.ExecShell(nginx_bin + ' -V 2>&1|grep OpenSSL')[0].find('OpenSSL 1.1.') != -1
        if nginx_v and openssl_v:
            return ' TLSv1.3'
        return ''

    def add_lbs_general(self, get):
        '''
        普通模式添加负载均衡
        :param get:
        :return:
        '''
        if not 'nodes' in get: return public.returnMsg(False, '缺少节点参数')
        try:
            nodes = json.loads(get.nodes)
            if nodes in ['false', False, None]: return public.returnMsg(False, '至少需要添加1个节点')
            _ok = False
            for node in nodes:
                if node['state'] in ['1', 1]: _ok = True
            if not _ok:
                return public.returnMsg(False, '至少需要添加一个【参与】负载的的节点')
        except:
            return public.returnMsg(False, '至少需要添加1个节点')

        up_result = self.add_upstream(get)
        if not up_result['status']:
            return up_result
        get.default_upstream = get.up_name
        result = self.add_server(get)
        if not result['status']:
            get_obj = public.dict_obj()
            get_obj.id = up_result["msg"]
            self.delete_upstream(get_obj)
            return result
        return public.returnMsg(True, '添加成功')

    def get_logs(self, get):
        '''
        获取日志
        :param get:
        :return:
        '''
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', cfg.log_type).count()
        limit = 11
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
        data['data'] = public.M('logs').where('type=?', cfg.log_type).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    def del_log(self, get):
        '''
        # 删除日志
        :param get:
        :return:
        '''
        public.M('logs').where('type=?', cfg.log_type).delete()
        return public.returnMsg(True, '清理成功')

    def get_heartbeat_conf(self, get):
        '''
        获取告警邮箱列表和心跳检测设置
        :param get:
        :return:
        '''
        if not os.path.exists(cfg.heartbeat):
            public.writeFile(cfg.heartbeat, json.dumps({'time': 30, 'warning': 3}))
        upBody = public.readFile(cfg.heartbeat)
        data = json.loads(upBody)
        if public.M('crontab').where('name=?', (u'[勿删]负载均衡节点心跳检测任务',)).count():
            data['open'] = True
        else:
            data['open'] = False
        return {'emails': WarningMsg()._mail_list, 'heartbeat': data}

    def modify_heartbeat_conf(self, get):
        '''
        修改心跳包设置
        :param self:
        :param get:
        :return:
        '''
        heartbeat = {}
        heartbeat['time'] = int(get.time)
        heartbeat['warning'] = int(get.warning)
        public.writeFile(cfg.heartbeat, json.dumps(heartbeat))

        id = public.M('crontab').where('name=?', (u'[勿删]负载均衡节点心跳检测任务',)).getField('id')
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        if os.path.exists('/www/server/panel/pyenv'):
            python_path = '/www/server/panel/pyenv/bin/python'
        else:
            python_path = '/usr/bin/python'
        data = {}
        data['name'] = '[勿删]负载均衡节点心跳检测任务'
        data['type'] = 'minute-n'
        data['where1'] = get.time
        data['sBody'] = '{} {}/check_task.py'.format(python_path, cfg.plugin_path)
        data['backupTo'] = 'localhost'
        data['sType'] = 'toShell'
        data['hour'] = ''
        data['minute'] = ''
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''
        crontab.crontab().AddCrontab(data)
        public.WriteLog(cfg.log_type, '修改心跳包检测配置')
        return public.returnMsg(True, '设置成功!')

    def heartbeat_off(self, get):
        '''
        关闭心跳包
        :param get:
        :return:
        '''
        id = public.M('crontab').where('name=?', (u'[勿删]负载均衡节点心跳检测任务',)).getField('id')
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        public.WriteLog(cfg.log_type, '关闭心跳包检测配置')
        return public.returnMsg(True, '已关闭任务')

    def check_port_exists(self, load_port):
        '''
            @name 检查端口是否占用
            @author hwliang<2021-05-29>
            @param port<int> 端口
            @return bool
        '''

        for c_name in os.listdir(cfg.tcp_load_path):
            filename = "{}/{}".format(cfg.tcp_load_path, c_name)
            if not os.path.exists(filename):
                continue
            tcp_info = json.loads(public.readFile(filename))
            if tcp_info['load_port'] == load_port:
                return True

        if public.ExecShell('lsof -i:{}|grep LISTEN'.format(load_port))[0].strip():
            return True
        return False

    def check_tcpname_exists(self, load_name):
        '''
            @name 检查负载名称是否存在
            @author hwliang<2021-05-29>
            @param port<int> 端口
            @return bool
        '''
        if not os.path.exists(cfg.tcp_load_path):
            os.makedirs(cfg.tcp_load_path, 384)

        if load_name + ".json" in os.listdir(cfg.tcp_load_path):
            return True
        return False

    def save_tcpload(self, tcp_info):
        '''
            @name 保存TCP负载均衡配置信息
            @author hwliang<2021-05-29>
            @param tcp_info<dict> TCP配置信息
            @return bool
        '''

        filename = "{}/{}.json".format(cfg.tcp_load_path, tcp_info['load_name'])
        public.writeFile(filename, json.dumps(tcp_info))
        self.write_tcp_conf(tcp_info)

    def write_tcp_conf(self, tcp_info):
        '''
            @name 写入到TCP负载均衡配置文件
            @author hwliang<2021-05-29>
            @param tcp_info<dict> TCP配置信息
            @return bool
        '''
        self.tcp_load_check()
        servers = []
        states = [' down', '', ' backup']
        is_backup = False
        for node in tcp_info['nodes']:
            if node['state'] == 2:
                is_backup = True
            servers.append(
                "\tserver {}:{} weight={} max_fails={} fail_timeout={}{};".format(
                    node['address'],
                    node['port'],
                    node['weight'],
                    node['max_fails'],
                    node['fail_timeout'],
                    states[node['state']]
                )
            )
        ip_hash = '' if tcp_info['load_iphash'] == 0 or is_backup else "\thash $remote_addr consistent;\n"
        tcp_conf = '''upstream tcp_{load_name} {{
{ip_hash}{servers}
}}

server {{
    listen {address}:{port};
    proxy_connect_timeout {connect_timeout}s;
    proxy_timeout {timeout}s;
    proxy_pass tcp_{load_name};
    access_log /www/wwwlogs/load_balancing/tcp/{load_name}.log tcp_format;
}}
'''.format(
            load_name=tcp_info['load_name'],
            ip_hash=ip_hash,
            servers="\n".join(servers),
            address=tcp_info['load_address'],
            port=tcp_info['load_port'],
            connect_timeout=tcp_info['load_connect_timeout'],
            timeout=tcp_info['load_timeout']
        )
        if not os.path.exists(cfg.tcp_load_conf_path):
            os.makedirs(cfg.tcp_load_conf_path)
        conf_file = "{}/{}.conf".format(cfg.tcp_load_conf_path, tcp_info['load_name'])
        public.writeFile(conf_file, tcp_conf)
        public.ServiceReload()
        return True

    def tcp_load_check(self):
        '''
            @name tcp负载均衡环境检测
            @author hwliang<2021-06-09>
            @return void
        '''
        log_path = '/www/wwwlogs/load_balancing/tcp'
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        ngx_conf_file = '/www/server/nginx/conf/nginx.conf'
        ngx_conf = public.readFile(ngx_conf_file)
        if not ngx_conf: return
        if ngx_conf.find('tcp-access.log') != -1: return

        stream_conf = '''
stream {
    log_format tcp_format '$time_local|$remote_addr|$protocol|$status|$bytes_sent|$bytes_received|$session_time|$upstream_addr|$upstream_bytes_sent|$upstream_bytes_received|$upstream_connect_time';

    access_log /www/wwwlogs/tcp-access.log tcp_format;
    error_log /www/wwwlogs/tcp-error.log;
    include /www/server/panel/vhost/nginx/tcp/*.conf;
}'''

        ngx_conf += stream_conf
        public.writeFile(ngx_conf_file, ngx_conf)

    def create_tcp_load(self, get):
        '''
            @name 创建TCP负载均衡
            @author hwliang<2021-05-29>
            @param get<dict_obj>{
                load_name: string<名称>
                load_address: string<监听地址> 127.0.0.1/0.0.0.0
                load_port: int<监听端口>
                load_connect_timeout: int<连接超时时间>
                load_timeout: int<连接保持时间>
                load_ps: string<备注信息>
                load_iphash: int<是否启用IP跟随> 0.不启用 , 1.启用
                nodes: json[]<节点列表>{
                    address: string<节点地址>
                    port: int<节点端口>
                    state: int<节点状态> 0.停用 1.参与 2.备份
                    weight: int<权重>
                    max_fails: int<最大重试次数>
                    fail_timeout: int<故障恢复时间>
                }
            }
        '''
        tcp_info = {
            'load_name': get.load_name.strip(),
            'load_address': get.load_address.strip(),
            'load_port': int(get.load_port),
            'load_connect_timeout': int(get.load_connect_timeout),
            'load_timeout': int(get.load_timeout),
            'load_iphash': int(get.load_iphash),
            'load_ps': get.load_ps.strip(),
            'nodes': json.loads(get.nodes)
        }

        if tcp_info['load_port'] > 65535 or tcp_info['load_port'] < 1:
            return public.returnMsg(False, '监听端口范围不正确，应在1-65535之间')

        if self.check_tcpname_exists(tcp_info['load_name']):
            return public.returnMsg(False, '指定负载均衡名称已存在')

        if self.check_port_exists(tcp_info['load_port']):
            return public.returnMsg(False, '指定监听端口已被占用，请使用其它端口!')

        n = 0
        for node in tcp_info['nodes']:
            if node['state'] == 1: n += 1

        if n < 1: return public.returnMsg(False, '最少需要1个[参与]负载均衡的节点!')

        self.save_tcpload(tcp_info)
        public.WriteLog('负载均衡', "添加TCP负载均衡[{}]配置".format(get.load_name))
        return public.returnMsg(True, '创建成功!')

    def modify_tcp_load(self, get):
        '''
            @name 修改TCP负载均衡
            @author hwliang<2021-05-29>
            @param get<dict_obj>{
                load_name: string<名称>
                load_address: string<监听地址>
                load_port: int<监听端口>
                load_connect_timeout: int<连接超时时间>
                load_timeout: int<连接保持时间>
                load_ps: string<备注信息>
                load_iphash: int<是否启用IP跟随> 0.不启用 , 1.启用
                nodes: json[]<节点列表>{
                    address: string<节点地址>
                    port: int<节点端口>
                    state: int<节点状态> 0.停用 1.参与 2.备份
                    weight: int<权重>
                    max_fails: int<最大重试次数>
                    fail_timeout: int<故障恢复时间>
                }
            }
        '''

        tcp_info = {
            'load_name': get.load_name.strip(),
            'load_address': get.load_address.strip(),
            'load_port': int(get.load_port),
            'load_connect_timeout': int(get.load_connect_timeout),
            'load_timeout': int(get.load_timeout),
            'load_iphash': int(get.load_iphash),
            'load_ps': get.load_ps.strip(),
            'nodes': json.loads(get.nodes)
        }

        if tcp_info['load_port'] > 65535 or tcp_info['load_port'] < 1:
            return public.returnMsg(False, '监听端口范围不正确，应在1-65535之间')

        filename = "{}/{}.json".format(cfg.tcp_load_path, tcp_info['load_name'])
        if not os.path.exists(filename):
            return public.returnMsg(False, '指定负载均衡不存在!')

        n = 0
        for node in tcp_info['nodes']:
            if node['state'] == 1: n += 1

        if n < 1: return public.returnMsg(False, '最少需要1个[参与]负载均衡的节点!')

        old_tcp_info = json.loads(public.readFile(filename))
        if old_tcp_info['load_port'] != tcp_info['load_port']:
            if self.check_port_exists(tcp_info['load_port']):
                return public.returnMsg(False, '指定监听端口已被占用，请使用其它端口!')

        self.save_tcpload(tcp_info)
        public.WriteLog('负载均衡', "修改TCP负载均衡[{}]配置".format(get.load_name))
        return public.returnMsg(True, '修改成功!')

    def remove_tcp_load(self, get):
        '''
            @name 删除指定TCP负载均衡
            @author hwliang<2021-05-29>
            @param get<dict_obj>{
                load_name: string<负载均衡名称>
            }
            @return dict
        '''
        load_name = get['load_name'].strip()
        filename = "{}/{}.json".format(cfg.tcp_load_path, load_name)
        if not os.path.exists(filename):
            return public.returnMsg(False, '指定负载均衡不存在!')

        os.remove(filename)

        conf_file = "{}/{}.conf".format(cfg.tcp_load_conf_path, load_name)
        if os.path.exists(conf_file):
            os.remove(conf_file)
            public.ServiceReload()

        public.WriteLog('负载均衡', "删除TCP负载均衡[{}]配置".format(load_name))
        return public.returnMsg(True, '删除成功!')

    def get_tcp_load_list(self, get):
        '''
            @name 获取TCP负载均衡列表
            @author hwliang<2021-05-29>
            @return list
        '''
        if not os.path.exists(cfg.tcp_load_path):
            os.makedirs(cfg.tcp_load_path, 384)
        result = []
        for c_name in os.listdir(cfg.tcp_load_path):
            filename = "{}/{}".format(cfg.tcp_load_path, c_name)
            if not os.path.exists(filename):
                continue
            tcp_info = json.loads(public.readFile(filename))
            tcp_info['total'] = self.get_tcp_load_total(tcp_info['load_name'])
            result.append(tcp_info)
        return result

    def utc_to_time(self, s_date):
        '''
            @name UTC时间转时间戳
            @author hwliang<2021-06-01>
            @param s_date<string> UTC格式时间
            @return int
        '''
        try:
            return int(time.mktime(time.strptime(s_date, "%d/%b/%Y:%H:%M:%S %z")))
        except:
            return s_date

    def get_tcp_load_total(self, load_name):
        '''
            @name 获取指定TCP负载均衡统计信息
            @author hwliang<2021-06-01>
            @param load_name<string> 负载均衡名称
            @return dict
        '''
        load_log_file = '/www/wwwlogs/load_balancing/tcp/{}.log'.format(load_name)
        num = 5000
        tmp_lines = public.GetNumLines(load_log_file, num)
        line_size = 95
        lines = tmp_lines.strip().split("\n")

        result = {'count': 0, 'error': 0, 'speed': 0, 'request_timeout': 0, 'last_request_time': 0}
        if not lines: return result
        line_len = len(lines)
        size_count = int(os.path.getsize(load_log_file) / line_size)
        if line_len > size_count - num:
            result['count'] = line_len
        else:
            result['count'] = size_count

        last_line = lines[-1].split('|')
        if len(last_line) != 11: return result
        result['last_request_time'] = self.utc_to_time(last_line[0])
        result['request_timeout'] = int(float(last_line[6]) * 1000)

        for line in lines:
            tmp = line.split('|')
            if len(tmp) != 11:
                continue
            if tmp[3] != '200':
                result['error'] += 1
            if last_line[0] == tmp[0]: result['speed'] += 1

        if time.time() - result['last_request_time'] > 5:
            result['speed'] = 0

        return result

    def get_tcp_load_find(self, get):
        '''
            @name 获取指定TCP负载均衡配置信息
            @author hwliang<2021-05-29>
            @param get<dict_obj>{
                load_name: string<负载均衡名称>
            }
            @return dict
        '''
        load_name = get['load_name'].strip()
        filename = "{}/{}.json".format(cfg.tcp_load_path, load_name)
        if not os.path.exists(filename):
            return public.returnMsg(False, '指定负载均衡不存在!')
        tcp_info = json.loads(public.readFile(filename))
        return tcp_info

    def get_tcp_load_logs(self, get):
        '''
            @name 获取指定TCP负载均衡访问日志
            @author hwliang<2021-05-29>
            @param get<dict_obj>{
                load_name: string<负载均衡名称>
            }
            @return dict
        '''
        if not 'load_name' in get:
            return public.returnMsg(False, '负载均衡名称不能为空')

        load_log_file = '/www/wwwlogs/load_balancing/tcp/{}.log'.format(get.load_name)
        result = {}
        result['size'] = 0
        result['data'] = []
        result['end'] = True
        m = 0
        if os.path.exists(load_log_file): result['size'] = os.path.getsize(load_log_file)
        try:
            import cgi
            pyVersion = sys.version_info[0]
            num = 10
            if not os.path.exists(load_log_file): return result
            p = 1
            if 'p' in get:
                p = int(get.p)

            start_line = (p - 1) * num
            count = start_line + num
            fp = open(load_log_file, 'rb')
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
                                tmp_data = line.split('|')
                                if len(tmp_data) == 11:
                                    for i in range(len(tmp_data)): tmp_data[i] = cgi.escape(str(tmp_data[i]), True)
                                    tmp_data[0] = public.format_date(times=self.utc_to_time(tmp_data[0]))
                                    tmp_data[6] = str(int(float(tmp_data[6]) * 1000)) + 'ms'
                                    data.append(tmp_data)
                                else:
                                    m += 1
                            except:
                                m += 1
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
        except:
            data = []
        result['end'] = False
        if len(data) + m < num:
            result['end'] = True
        result['continue_line'] = m
        result['data'] = data
        return result


if __name__ == '__main__':
    upstreams = UpStream.SQL().all()
    warning_msg = WarningMsg(send_type="mail")
    for _upstream in upstreams:
        warning_msg(_upstream.check_nodes())
