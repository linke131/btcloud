#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# | Date: 2022/6/7
# +--------------------------------------------------------------------
# | 宝塔网站监控报表 - 日志接收服务
# +--------------------------------------------------------------------
# | TODO: 全局开关处理
# | TODO: 服务一直运行，配置只在第一次时读取，如何及时更新到最新的配置文件
# | TODO: 异常处理，一个地方报错，整个服务崩溃
# | TODO: 运行时间长了后的内存占用测试
# | TODO: python2测试
# | TODO: 其他版本的ngx_lua测试
# | TODO: 转换成后台服务方式运行, 添加宝塔加固白名单
# +--------------------------------------------------------------------

import sys
import os
import socket
import selectors
from threading import Thread
import time
import json
import re
import sqlite3
from multiprocessing import JoinableQueue
import logging


os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")
os.environ["UA_PARSER_YAML"] = "/www/server/panel/plugin/total/regexes.yaml"

import public
debug = os.path.exists("/www/server/panel/plugin/total/debug.pl")

from user_agents import parse

class TotalServer:
    connections = {}
    addresses = {}
    timeouts = {}
    passwords = {}
    config = {}
    backend_conf = "/www/server/total/config.json"
    domains = {}
    domain_conf = "/www/server/total/domains.json"
    no_binding_server_name = "btunknownbt"
    data_queue = JoinableQueue()
    __frontend_path = '/www/server/panel/plugin/total'
    sqlite_interrupt_delay = 60*2

    def __init__(self):
        self.re_header = re.compile("^([\w-]+):\s+(.+)$")
        self.re_ipv4 = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        self.re_ipv6 = re.compile("^[\w:]+$")
        # self.re_spider = re.compile("(Baiduspider|Bytespider|360Spider|Sogou web spider|Sosospider|Googlebot|bingbot|AdsBot-Google|Google-Adwords|YoudaoBot|Yandex|DNSPod-Monitor|YisouSpider|mpcrawler|Yahoo|Slurp|DuckDuckGo)", re.I|re.M)
        # self.re_mobile = re.compile("(Mobile|Android|iPhone|iPod|iPad)", re.I|re.M)
        # self.re_pc = re.compile("(TheWorld|TencentTraveler|UCWEB|UBrowser|2345Explorer)", re.I|re.M)

        # self.re_firefox = re.compile("firefox", re.I|re.M)
        # self.re_msie = re.compile("(MSIE|Trident)", re.I|re.M)
        # self.re_chrome = re.compile("Chrome", re.I|re.M)
        # self.re_safari = re.compile("Safari", re.I|re.M)
        # self.re_machine = re.compile("([Cc]url|HeadlessChrome|[a-zA-Z]+[Bb]ot|[Ww]get|[Ss]pider|[Cc]rawler|[Ss]crapy|zgrab|[Pp]ython|java)", re.I|re.M)
        # self.re_os = re.compile("(Windows|Linux|Macintosh)", re.I|re.M)
        # self.re_weixin = re.compile("MicroMessenger", re.I|re.M)

        self.sqlite_pool = {}
        self.update_stat_keys = {}
        self.update_uri_keys = {}
        self.update_ip_keys = {}
        self.spider_table = {
            "baidu":1,  # check
            "bing":2,  # check 
            "qh360":3, # check
            "google":4,
            "bytes":5,  # check
            "sogou":6,  # check
            "youdao":7,
            "soso":8,
            "dnspod":9,
            "yandex":10,
            "yisou":11,
            "other":12,
            "mpcrawler":13,
            "yahoo":14, # check
            "duckduckgo":15
        }
        self.spiders_ip_lib = {}
        self.fake_spider = 77
        self.clients_map = {
            "android":"android",
            "iphone":"iphone",
            "ipod":"iphone",
            "ipad":"iphone",
            "firefox":"firefox",
            "ie": "msie",
            "msie":"msie",
            "trident":"msie",
            "360se":"qh360",
            "360ee":"qh360",
            "360browser":"qh360",
            "qihoobrowser": "qh360",
            "qihoo":"qh360",
            "the world":"theworld",
            "theworld":"theworld",
            "tencenttraveler":"tt",
            "maxthon":"maxthon",
            "opera":"opera",
            "qqbrowser":"qq",
            "ucweb":"uc",
            "ubrowser":"uc",
            "safari":"safari",
            "chrome":"chrome",
            "metasr":"metasr",
            "2345explorer":"pc2345",
            "edge":"edeg",
            "edg":"edeg",
            "windows":"windows",
            "linux":"linux",
            "macintosh":"mac",
            "mac os x": "mac",
            "mobile":"mobile"
        }
        self.cache = {}
        self.cache_file = self.__frontend_path + "/cache.data"
        if not os.path.exists(self.cache_file):
            open(self.cache_file, "a+")
        self.load_cache()

    def save_cache(self):
        """保存缓存"""
        with open(self.cache_file, "w", encoding="utf-8") as fp:
            for k,v in self.cache.items():
                exp_time = v["exp"]
                val = v["val"]
                fp.write(str(k)+","+str(val)+","+str(exp_time)+ "\n")

    def load_cache(self):
        """加载缓存"""
        with open(self.cache_file, "r", encoding="utf-8") as fp:
            line = fp.readline().strip()
            while line:
                k, v, exp_time = line.split(",")
                self.cache[k] = {
                    "val": v,
                    "exp": float(exp_time)
                }
                line = fp.readline().strip()

    def set_cache(self, key, value, end_of_day=False, exp=0):
        """设置缓存

        Args:
            key (str): key
            value (str/num): 值
            end of day (bool): 是否只在当天有效
            exp (int): 过期时间,秒; 0为不过期
        """
        if end_of_day:
            exp_time = self.get_end_time()
        else:
            now = time.time()
            if exp > 0:
                exp_time = now+exp*60
            else:
                exp_time = 0
        self.cache[key] = {} 
        self.cache[key]["val"] = value
        self.cache[key]["exp"] = exp_time
    
    def get_cache(self, key):
        """获取缓存

        Args:
            key (str): 缓存键值

        Returns:
            str: 缓存值
        """
        if key in self.cache.keys():
            res = self.cache[key]
            exp_time = res["exp"]
            if exp_time == 0:
                return res["val"]

            now = time.time()
            if now >= exp_time:
                return None
            return res["val"]
        return None


    def run(self, host="127.0.0.1", port=9876):
        #初始化Socket
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
        #self.s.setblocking(False)
        self.s.bind((host, port))
        self.s.listen(0)

        #注册epool模型
        self.epoll=selectors.DefaultSelector()
        self.epoll.register(self.s,selectors.EVENT_READ,self.on_accept)

        logging.debug("正在开启数据解析进程...")
        consume_thread = Thread(target=self.consume_data)
        consume_thread.setDaemon(True)
        consume_thread.start()

        logging.debug("正在开启数据后台任务进程...")
        task_thread = Thread(target=self.server_task)
        task_thread.setDaemon(True)
        task_thread.start()


        self.listen_event()

    def listen_event(self):
        try:
            while True:
                events = self.epoll.select()
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)
        except:
            pass
            #print(public.get_error_info())
        finally:
            self.connections = {}
            self.addresses = {}
            self.passwords = {}
            self.timeouts = {}
            
            for k in list(self.sqlite_pool.keys()):
                try:
                    sqlite_obj = self.sqlite_pool[k]
                    sqlite_obj and sqlite_obj["cursor"] and sqlite_obj["cursor"].close()
                    sqlite_obj and sqlite_obj["connect"] and sqlite_obj["connect"].close()
                    del self.sqlite_pool[k]
                except Exception as e:
                    print("关闭连接出现错误: {}".format(e))
            # print("exit service")
            #self.listen_event()
            logging.debug("服务进程退出。")

    def on_accept(self,sock,mask):
        try:
            conn,addr=sock.accept()
            logging.debug("Connect: %s >> %s" % (str(addr),conn.fileno()))
            self.connections[conn.fileno()] = conn
            self.addresses[conn.fileno()] = addr
            self.timeouts[conn.fileno()] = time.time()
            self.epoll.register(conn,selectors.EVENT_READ,self.on_read)
            self.clean_fd()
        except Exception as e:
            logging.error("On accept err:")
            logging.error(e)
            # print(public.get_error_info())

    def on_read(self,conn,fd):
        try:
            fd = conn.fileno()
            start = time.time()
            self.timeouts[fd] = start

            packed_data = self.connections[fd].recv(5)
            if len(packed_data) != 5:
                return self.on_close(fd)
            try:
                # hex, token, client_id, fun, data_len, s1, s2 = struct.unpack(
                #     '!2s32shBHBH',packed_data)
                # print(hex, token, client_id, fun, data_len, s1, s2)

                header_data = packed_data.decode("utf-8")
                # print("Header data:")
                data_len = int(header_data)
                # print(data_len)
                # if  != "BT":
                #     print("无效连接。")
                #     return self.on_close(fd)
                
            except Exception as e:
                logging.error("无效连接err:")
                logging.error(e)
                return self.on_close(fd)

            data = bytes()
            buff = 1024
            i = 0

            while True:
                e_len =  data_len - i
                if e_len >= buff:
                    data += self.connections[fd].recv(buff)
                    i+=buff
                else:
                    if e_len > 0:
                        data += self.connections[fd].recv(e_len)
                    break

            # print("data:")
            # print(data.decode("utf-8").split("#\n#"))
            self.data_queue.put(data)
        except Exception as e:
            logging.error("on read exp:")
            logging.error(e)

    def server_task(self):
        """后台服务定时任务
        
        任务1：定时检查数据库连接是否需要关闭
        任务2：定时清理已过期的缓存
        """
        while True:
            now = time.time()
            need_close = []
            for s_name, sqlite_obj in self.sqlite_pool.items():
                # print("check db connect: {}".format(s_name))
                # 超过一定时间未写入数据，及时关闭连接
                if "last_commit" in sqlite_obj.keys():
                    if (now - sqlite_obj["last_commit"]) > self.sqlite_interrupt_delay:
                        need_close.append(s_name)
                else:
                    sqlite_obj["last_commit"] = self.sqlite_interrupt_delay

            for s_name in need_close:
                sqlite_obj = self.sqlite_pool[s_name]
                logging.debug("关闭网站: {} 的数据库连接...".format(s_name))
                sqlite_obj["cursor"] and sqlite_obj["cursor"].close()
                sqlite_obj["connect"] and sqlite_obj["connect"].close()

                del self.sqlite_pool[s_name]

            # 清理过期缓存
            for k in list(self.cache.keys()):
                v = self.cache[k]
                exp_time = v["exp"]
                if exp_time > 0 and now > exp_time:
                    del self.cache[k]

            time.sleep(60)

    def consume_data(self):
        """解析数据，并存储"""
        while True:
            data = self.data_queue.get()
            logging.debug("[当前Data queue size: {}，开始解析数据.".format(self.data_queue.qsize()))
            self.parse_data(data)

    def get_config(self, site):
        """获取站点的配置文件

        Args:
            site (string): 站点名或者global, global代表全局配置

        Returns:
            dict: 站点配置
        """
        if not self.config:
            c_str_data = public.readFile(self.backend_conf)
            if c_str_data:
                self.config = json.loads(c_str_data)
        if site == "global":
            return self.config[site]
        if site not in self.config or not self.config[site]:
            return self.config["global"]
        global_config = self.config["global"]
        con = self.config[site]
        # inherited: 标记单个子站点的配置文件是否已继承过全局配置，避免重复去取缺失值。
        if "inherited" in con:
            return con
        for k,v in global_config.items():
            if k not in con.keys():
                con[k] = v
        con["inherited"] = True
        self.config[site] = con
        return con

    def get_domains(self):
        if not self.domains:
            c_str_data = public.readFile(self.domain_conf)
            if c_str_data:
                self.domains = json.loads(c_str_data)
        return self.domains

    def get_server_name(self, c_name):
        """获取server anme

        Args:
            c_name (str): 用户访问的域名

        Returns:
            str: 真实的域名
        TODO: 缓存已查找的结果
        """
        determined_name = ""
        domains = self.get_domains()
        for dm_obj in domains:
            main_site = dm_obj["name"]
            bind_list = dm_obj["domains"]

            if main_site == c_name:
                return main_site 
            for dm in bind_list:
                if c_name == dm:
                    return main_site
                if dm.find("*") != -1:
                    _dm = dm.replace("*", ".*")
                    if re.search(_dm, c_name):
                        determined_name = main_site
        if determined_name:
            return determined_name
        return self.no_binding_server_name

    def get_client_real_ip(self, config, headers, remote_addr):
        """根据CDN配置，从请求头中获取客户端真实IP地址

        Args:
            config (dict): 站点配置
            headers (dict): 请求头
            remote_addr (str): ngx请求中的客户端IP
        
        Return:
            client_ip: 客户端请求真实IP
            ip_list: 客户端请求到达服务器所经过的转发IP列表
        """
        default_client_ip = "unknown"
        client_ip = default_client_ip
        ip_list = default_client_ip 
        cdn = config["cdn"]
        if cdn and "cdn_headers" in config:
            for key in config["cdn_headers"]:
                if key in headers.keys():
                    ip_list = headers[key]
                    client_ip = ip_list.split(",")[0]
                    break
        if client_ip == default_client_ip:
            client_ip = remote_addr
            ip_list = remote_addr
            return client_ip, ip_list
        
        #IPV6
        if self.re_ipv6.match(client_ip):
            ip_list = client_ip
            return client_ip, ip_list
        #IPV4
        if not self.re_ipv4.match(client_ip):
            if not remote_addr:
                client_ip = default_client_ip
                ip_list = default_client_ip
            else:
                ip_list = client_ip + "," + remote_addr
                client_ip = remote_addr
        else:
            if client_ip not in ip_list:
                ip_list = client_ip + "," + ip_list
        return client_ip, ip_list

    def parse_request_header(self, header_str):
        # print("请求头原文本：")
        # print(header_str)
        slist = header_str.split("\r\n")
        headers = {}
        headers["method"], headers["uri"], headers["protocol"] = slist[0].split()
        for i in range(1, len(slist)):
            item = slist[i]
            mres = self.re_header.match(item)
            if mres:
                headers[mres.group(1)] = mres.group(2)
        return headers

    def exclude_status_code(self, exclude_list, status_code):
        # 排除状态码
        return status_code in exclude_list

    def exclude_extension(self, exclude_list, uri):
        # 排除后缀
        for ext in exclude_list:
            if uri.endswith(ext):
                return True
        return False

    def exclude_url(self, exclude_list, url):
        # 排除URL
        for ex_obj in exclude_list:
            if ex_obj["mode"] == "regular":
                if re.search(ex_obj["url"], url):
                    return True
            else:
                if ex_obj["url"] == url:
                    return True
        return False

    def exclude_ip(self, exclude_list, ip):
        return ip in exclude_list

    def stat_ip(self, cur, ip, body_length, is_spider):
        if ip not in self.update_ip_keys.keys():
            insert_sql = "INSERT INTO ip_stat(ip) SELECT ? WHERE " \
            "NOT EXISTS(SELECT ip FROM ip_stat WHERE ip=?)"
            cur.execute(insert_sql, [ip, ip])
            self.update_ip_keys[ip] = True
        number_day = str(time.localtime().tm_mday)
        day_column = "day"+ number_day
        flow_column = "flow"+number_day
        spider_column = "spider_flow"+number_day
        if not is_spider:
            update_sql = "UPDATE ip_stat SET "+ self.get_update_field(day_column) \
            + "," + self.get_update_field(flow_column, body_length) + " WHERE ip=?"
        else:
            update_sql = "UPDATE ip_stat SET "+ self.get_update_field(day_column) \
            + "," + self.get_update_field(spider_column, body_length) + " WHERE ip=?"
        # print("stat ip sql:")
        # print(update_sql)
        cur.execute(update_sql, [ip])

    def stat_uri(self, cur, uri, body_length, is_spider):
        uri_md5 = public.md5(uri)
        if uri_md5 not in self.update_uri_keys.keys():
            insert_sql = "INSERT INTO uri_stat(uri_md5, uri) SELECT ?,? WHERE " \
            "NOT EXISTS(SELECT uri_md5 FROM uri_stat WHERE uri_md5=?)"
            cur.execute(insert_sql, [uri_md5, uri, uri_md5])
            self.update_uri_keys[uri_md5] = True
        number_day = str(time.localtime().tm_mday)
        day_column = "day"+ number_day
        flow_column = "flow"+number_day
        spider_column = "spider_flow"+number_day
        if not is_spider:
            update_sql = "UPDATE uri_stat SET "+ self.get_update_field(day_column) \
            + "," + self.get_update_field(flow_column, body_length) + " WHERE uri_md5=?"
        else:
            update_sql = "UPDATE uri_stat SET "+ self.get_update_field(day_column) \
            + "," + self.get_update_field(spider_column, body_length) + " WHERE uri_md5=?"
        # print("stat uri sql:")
        # print(update_sql)
        cur.execute(update_sql, [uri_md5])
        
    def update_stat(self, update_server_name, cur, stat_table, time_key, columns):
        if not columns: return
        check_key = update_server_name+stat_table
        if check_key not in self.update_stat_keys.keys():
            self.update_stat_keys[check_key] = []

        if time_key not in self.update_stat_keys[check_key]:
            self.update_stat_keys[check_key] = []
            check_sql = "INSERT INTO {table}(time) SELECT ? WHERE NOT " \
            "EXISTS(SELECT time FROM {table} WHERE time=?)".format(
                table=stat_table
            )
            rows = cur.execute(check_sql, [time_key, time_key])
            self.update_stat_keys[check_key].append(time_key)
            # print("{}/{}/time key: {} 已初始化，rows: {}。".format(update_server_name, stat_table, time_key, rows))
        
        update_sql = "UPDATE {table} SET {columns} WHERE time=?".format(
            table=stat_table, columns=columns)
        res = cur.execute(update_sql, [time_key])
        # update_rows = 0
        # res = cur.fetchone()
        # if res:
        #     update_rows = res[0]

        # print("更新{} {}行数：{}".format(update_server_name, stat_table, update_rows))

    def get_spider_json(self, spider_num_name):
        spider_ips_path = "/www/server/total/xspiders/{}.json".format(spider_num_name)
        if spider_num_name in self.spiders_ip_lib.keys():
            return self.spiders_ip_lib[spider_num_name]

        if os.path.exists(spider_ips_path):
            spiders = json.loads(public.readFile(spider_ips_path))
            self.spiders_ip_lib[spider_num_name] = spiders
            return spiders
        return []

    def get_spiders_ip_dict(self, spider_num_name):
        spider_ips_path = "/www/server/total/xspiders/{}.json".format(spider_num_name)
        if spider_num_name in self.spiders_ip_lib.keys():
            return self.spiders_ip_lib[spider_num_name]

        if os.path.exists(spider_ips_path):
            spiders = json.loads(public.readFile(spider_ips_path))
            dict_sta = {}
            for ip in spiders:
                dict_sta[ip] = True
            self.spiders_ip_lib[spider_num_name] = dict_sta
            return dict_sta
        return {}

    def check_spider(self, spider_num_name, client_ip):
        spiders = self.get_spiders_ip_dict(spider_num_name)
        if debug:
            logging.debug("蜘蛛: {} IP数量：".format(spider_num_name))
            logging.debug(len(spiders))
            logging.debug("check ip: {}".format(client_ip))
        if not spiders:
            return True
        return spiders.get(client_ip, False)

    def match_spider2(self, user_agent_family, client_ip):
        spider_name = ""
        spider_index = 0
        check_res = True

        if True:
            # if debug:
            #     print("match spider: {}".format(user_agent_family))
            spider_match = user_agent_family
            if spider_match.find("baidu") != -1:
                spider_name = "baidu"
                check_res = self.check_spider("1", client_ip)
            elif spider_match.find("bytes") != -1:
                spider_name = "bytes"
                check_res = self.check_spider("7", client_ip)
                # if debug:
                #     print("check fake spider: {}".format(check_res))
            elif spider_match.find("360") != -1:
                spider_name = "qh360"
                check_res = self.check_spider("3", client_ip)
            elif spider_match.find("sogou") != -1:
                spider_name = "sogou"
                check_res = self.check_spider("4", client_ip)
            elif spider_match.find("soso") != -1:
                spider_name = "soso"
            elif spider_match.find("google") != -1:
                spider_name = "google"
                check_res = self.check_spider("2", client_ip)
            elif spider_match.find("bingbot") != -1:
                spider_name = "bing"
                check_res = self.check_spider("6", client_ip)
            elif spider_match.find("youdao") != -1:
                spider_name = "youdao"
            elif spider_match.find("dnspod") != -1:
                spider_name = "dnspod"
            elif spider_match.find("yandex") != -1:
                spider_name = "yandex"
            elif spider_match.find("yisou") != -1:
                spider_name = "yisou"
            elif spider_match.find("mpcrawler") != -1:
                spider_name = "mpcrawler"
            elif spider_match.find("yahoo") != -1:
                spider_name = "yahoo"
                check_res = self.check_spider("5", client_ip)
            elif spider_match.find("slurp") != -1:
                spider_name = "yahoo"
                check_res = self.check_spider("5", client_ip)
            elif spider_match.find("duckduckgo") != -1:
                spider_name = "duckduckgo"
            else:
                spider_name = "other"
            if not check_res:
                spider_index = self.fake_spider
            else:
                spider_index = self.spider_table[spider_name]
            
            if debug:
                print("spider name: {}".format(spider_name))
                print("spider index: {}".format(spider_index))
        return spider_name, spider_index

    def match_spider(self, user_agent, client_ip):
        """匹配蜘蛛

        Args:
            client_ip (_type_): _description_
        """
        is_spider = False
        spider_name = ""
        spider_index = 0
        check_res = True

        if not user_agent:
            return is_spider, spider_name, spider_index

        search_res = self.re_spider.search(user_agent)
        print("spider agent:")
        print("<"+user_agent+">")
        print("spdier search:")
        print(search_res)
        if search_res:
            is_spider = True
            spider_match = search_res[1].lower()
            if spider_match.find("baidu") != -1:
                spider_name = "baidu"
                check_res = self.check_spider("1", client_ip)
            elif spider_match.find("bytes") != -1:
                spider_name = "bytes"
                check_res = self.check_spider("7", client_ip)
            elif spider_match.find("360") != -1:
                spider_name = "qh360"
                check_res = self.check_spider("3", client_ip)
            elif spider_match.find("sogou") != -1:
                spider_name = "sogou"
                check_res = self.check_spider("4", client_ip)
            elif spider_match.find("soso") != -1:
                spider_name = "soso"
            elif spider_match.find("google") != -1:
                spider_name = "google"
                check_res = self.check_spider("2", client_ip)
            elif spider_match.find("bingbot") != -1:
                spider_name = "bing"
                check_res = self.check_spider("6", client_ip)
            elif spider_match.find("youdao") != -1:
                spider_name = "youdao"
            elif spider_match.find("dnspod") != -1:
                spider_name = "dnspod"
            elif spider_match.find("yandex") != -1:
                spider_name = "yandex"
            elif spider_match.find("yisou") != -1:
                spider_name = "yisou"
            elif spider_match.find("mpcrawler") != -1:
                spider_name = "mpcrawler"
            elif spider_match.find("yahoo") != -1:
                spider_name = "yahoo"
                check_res = self.check_spider("5", client_ip)
            elif spider_match.find("slurp") != -1:
                spider_name = "yahoo"
                check_res = self.check_spider("5", client_ip)
            elif spider_match.find("duckduckgo") != -1:
                spider_name = "duckduckgo"
            else:
                spider_name = "other"
            if not check_res:
                return is_spider, spider_name, self.fake_spider
            spider_index = self.spider_table[spider_name]
        return is_spider, spider_name, spider_index

    def get_update_field(self, field, val=1):
        return field + "=" + field + "+" + str(val)

    def match_client2(self, user_agent, client_ip):
        clients = {}
        match_res = {
            "is_spider": False,
            "spider_name": "",
            "spider_index": "",
            "fields": {}
        }
        if not user_agent:
            return match_res
        
        p = parse(user_agent)
        ua = p.browser.family.lower()
        device_name = p.device.family.lower()
        os_name = p.os.family.lower()
        is_mobile = p.is_mobile
        is_tablet = p.is_tablet
        is_bot = p.is_bot
        is_pc = p.is_pc

        if debug:
            print("User agent: {}".format(ua))
            print("device name: {}".format(device_name))
        # 蜘蛛匹配
        if is_bot and device_name == "spider":
            spider_name, spider_index = self.match_spider2(ua, client_ip)
            match_res["is_spider"] = True
            match_res["spider_name"] = spider_name
            match_res["spider_index"] = spider_index 
            match_res["fields"] = clients
            return match_res

        # 移动端匹配
        if is_mobile or is_tablet:
            clients["mobile"] = 1
            if os_name in ["ios"]:
                clients["iphone"] = 1
            elif os_name in ["android"]:
                clients["android"] = 1
            else:
                if debug:
                    print("其他移动操作系统类型: {}".format(os_name))
        else:
            # pc
            if ua in self.clients_map.keys():
                clients[self.clients_map[ua]] = 1
            elif ua == "machine":
                clients["machine"] = 1
            else:
                # 移动端+PC端+机器以外 归类到其他
                if debug:
                    print("other user agent: {}".format(ua))
                clients["other"] = 1
            # OS
            if os_name != "other":
                if os_name in self.clients_map.keys():
                    clients[self.clients_map[os_name]] = 1
                else:
                    if debug:
                        print("其他系统类型: {}".format(user_agent))
                    other_os_res = re.search("(linux|ubuntu)", "linux", re.I|re.M)
                    if other_os_res:
                        res = other_os_res[1].lower()
                        if res in ["linux", "ubuntu"]:
                            clients["linux"] = 1

        if ua == "micromessenger":
            clients["weixin"] = 1
        match_res["fields"] = clients
        return match_res

    def match_client(self, user_agent):
        client_stat_fields = ""
        if not user_agent:
            return ""
        mobile_res = self.re_mobile.search(user_agent)
        if mobile_res:
            client_stat_fields += "," + self.get_update_field("mobile")
            m_client = mobile_res[1].lower()
            if m_client != "mobile":
                client_stat_fields += "," + self.get_update_field(
                    self.clients_map[m_client])
        else:
            # pc
            pc_res = self.re_pc.search(user_agent)
            cls_pc = ""
            if not pc_res:
                if self.re_firefox.search(user_agent):
                    cls_pc = "firefox"
                elif self.re_msie.search(user_agent):
                    cls_pc = "msie"
                elif self.re_chrome.search(user_agent):
                    cls_pc = "chrome"
                elif self.re_safari.search(user_agent):
                    cls_pc = "safari"
            else:
                cls_pc = pc_res[1].lower()

            if cls_pc:
                client_stat_fields += "," + self.get_update_field(self.clients_map[cls_pc])
            else:
                machine_res = self.re_machine.search(user_agent)
                if machine_res:
                    client_stat_fields += "," + self.get_update_field("machine")
                else:
                    # 移动端+PC端+机器以外 归类到其他
                    client_stat_fields += "," + self.get_update_field("other")
            # OS
            os_res = self.re_os.search(user_agent)
            if os_res:
                os_name = os_res[1].lower()
                client_stat_fields += "," + self.get_update_field(self.clients_map[os_name])

        other_res = self.re_weixin.search(user_agent)
        if other_res:
            client_stat_fields += "," + self.get_update_field("weixin")
        if client_stat_fields:
            client_stat_fields = client_stat_fields[1:]
        return client_stat_fields

    def get_end_time(self):
        now = time.localtime()
        return time.mktime((now.tm_year, now.tm_mon, now.tm_mday, 
            23, 59, 59, 0, 0, 0))

    def statistics_request(self, params):
        method = params["method"]
        status_code = params["status_code"]
        body_length = params["body_length"]
        user_agent = params["user_agent"].lower()
        content_type = params["content_type"]
        client_ip = params["client_ip"]
        pvc = 0
        uvc = 0
        if method == "GET" and status_code == 200 and body_length > 512 and user_agent:
            if content_type.find("text/html") != -1:
                pvc = 1
                if user_agent.find("mozilla") != -1:
                    today = time.strftime("%Y-%m-%d", time.localtime())
                    md5_key = public.md5(client_ip+user_agent+today)
                    if not self.get_cache(md5_key):
                        uvc = 1
                        self.set_cache(md5_key, 1, end_of_day=True)
        return pvc,uvc

    def statistics_ipc(self, server_name, client_ip):
        ipc = 0
        ip_key = server_name+"_"+client_ip
        ip_cache = self.get_cache(ip_key)
        if not ip_cache:
            ipc = 1
            self.set_cache(ip_key,1,end_of_day=True)
        return ipc


    def parse_data(self, source_data):
        """解析日志数据

        Args:
            source_data (str): 从ngx_lua端发送过来的数据
        """
        try:
            no_total_server_names = ['default', '_', 'phpinfo']
            data_list = source_data.decode('utf-8').split('#\n#')
            server_keys = []
            for req_str_data in data_list:
                req_data = req_str_data.split('@\n@')
                remote_addr = req_data[0]
                server_name = req_data[1]
                if server_name:
                    server_name = self.get_server_name(server_name)
                    server_name = server_name.replace('_', '.')
                if server_name in no_total_server_names:
                    continue
                if server_name not in server_keys:
                    server_keys.append(server_name)

                status_code = int(req_data[2])
                if not status_code or status_code == 0 or status_code == 444:
                    continue
                body_length = float(req_data[3])
                referer = req_data[4]
                request_time = float(req_data[5])
                request_header = self.parse_request_header(req_data[6])
                if not request_header:
                    request_header = {}
                client_port = int(req_data[7])
                log_time = req_data[8]
                time_key = time.strftime("%Y%m%d%H", time.localtime(float(log_time)))
                payload = req_data[9]
                content_type = req_data[10]
                if payload:
                    request_header["payload"] = payload
                
                domain = request_header.get('Host', '')
                if domain:
                    domain = domain.replace('_', '.')
                method = request_header.get('method', '')
                if not method:
                    continue
                uri = request_header.get('uri', '')
                param_inx = uri.find('?')
                if param_inx == -1:
                    request_uri = uri
                else:
                    request_uri = uri[0:param_inx]
                if request_uri == "/favicon.ico":
                    continue
                protocol = request_header.get('protocol', '')
                config = self.get_config(server_name)
                user_agent = request_header.get("User-Agent", "")
                client_ip, ip_list = self.get_client_real_ip(config, request_header, remote_addr)

                # print("server name: {}".format(server_name))
                # print('client ip: {}'.format(client_ip))
                # print('ip list: {}'.format(ip_list))
                # print('uri: {}'.format(uri))
                # print('request uri: {}'.format(request_uri))
                # print('request method: {}'.format(method))
                # print('body length: {}'.format(body_length))
                # print('request time: {}'.format(request_time))
                # print('status code: {}'.format(status_code))
                # print('protocol: {}'.format(protocol))
                # print('client port: {}'.format(client_port))
                # print('referer: {}'.format(referer))
                # print("payload: {}".format(payload))
                # print("user agent: {}".format(user_agent))
                # print("content type: {}".format(content_type))

                conn = None
                cur = None

                if server_name not in self.sqlite_pool:
                    self.sqlite_pool[server_name] = {}
                    db_path = "{}/{}/logs.db".format(config["data_dir"], server_name)
                    if not os.path.exists(db_path):
                        from total_migrate import total_migrate
                        tm = total_migrate()
                        res = tm.init_site_db(server_name)
                        if debug:
                            print("数据库: {} 初始化结果：{}。".format(server_name, res))
                    conn = sqlite3.connect(db_path, check_same_thread=False)
                    cur = conn.cursor()

                    self.sqlite_pool[server_name]["connect"] = conn
                    self.sqlite_pool[server_name]["cursor"] = cur
                else:
                    conn = self.sqlite_pool[server_name]["connect"]
                    cur = self.sqlite_pool[server_name]["cursor"]
                    
                exclude = self.exclude_extension(
                    config["exclude_extension"], request_uri) or \
                        self.exclude_url(config["exclude_url"], uri) or \
                        self.exclude_status_code(config["exclude_status"], 
                            status_code) or \
                        self.exclude_ip(config["exclude_ip"], client_ip)

                request_stat_fields = "req=req+1,length=length+"+str(float(body_length))
                client_stat_fields = ""
                spider_stat_fields = ""

                if exclude:
                    logging.debug("排除URL: {}".format(uri))
                    self.update_stat(server_name, cur, "request_stat", time_key, request_stat_fields)
                    continue

                # 统计方法请求数
                method_field = "http_"+method.lower()
                request_stat_fields += "," + self.get_update_field(method_field, 1)

                client_info = self.match_client2(user_agent, client_ip)
                is_spider = client_info["is_spider"]
                spider_name = client_info["spider_name"]
                spider_index = client_info["spider_index"]
                fields = client_info["fields"]
                for k,v in fields.items():
                    if is_spider:
                        if spider_stat_fields:
                            spider_stat_fields += "," 
                        spider_stat_fields += self.get_update_field(k, v)
                    else:
                        if client_stat_fields:
                            client_stat_fields += "," 
                        client_stat_fields += self.get_update_field(k, v)
                        
                # print("is spider: {}".format(is_spider))
                # print("spider name: {}".format(spider_name))
                # print("spider index: {}".format(spider_index))
                # print("spider stat:")
                # print(spider_stat_fields)
                # print("client stat:")
                # print(client_stat_fields)
                pvc = 0
                uvc = 0
                ipc = 0
                if not is_spider:
                    # client_stat_fields = self.match_client(user_agent)
                    # if not client_stat_fields:
                    #     request_stat_fields += "," + self.get_update_field("other", 1)
                    # print("request headers:")
                    # print(request_header.keys())
                    # content_type = request_header.get("Content-Type", "")
                    # print("Content type:")
                    # print(content_type)
                    params = {
                        "method": method,
                        "status_code": status_code,
                        "body_length": body_length,
                        "user_agent": user_agent,
                        "content_type": content_type,
                        "client_ip": client_ip
                    }
                    if client_stat_fields.find("machine") != -1:
                        if config["statistics_machine_access"]:
                            pvc,uvc = self.statistics_request(params)
                    else:
                        pvc,uvc = self.statistics_request(params)
                    ipc = self.statistics_ipc(server_name, client_ip)
                else:
                    if spider_index != self.fake_spider:
                        spider_stat_fields += self.get_update_field(spider_name)
                        request_stat_fields += "," + self.get_update_field(spider_name)
                    else:
                        request_stat_fields += "," + self.get_update_field("fake_spider")

                if ipc>0:
                    request_stat_fields += "," + self.get_update_field("ip")
                if pvc>0:
                    request_stat_fields += "," + self.get_update_field("pv")
                if uvc>0:
                    request_stat_fields += "," + self.get_update_field("uv")

                self.update_stat(server_name, cur, "client_stat", time_key, client_stat_fields)
                # logging.debug("已更新客户端统计。")
                self.update_stat(server_name, cur, "spider_stat", time_key, spider_stat_fields)
                # logging.debug("已更新蜘蛛统计。")
                self.update_stat(server_name, cur, "request_stat", time_key, request_stat_fields)
                # logging.debug("已更新请求统计。")

                if config["statistics_uri"]:
                    self.stat_uri(cur, request_uri, body_length, is_spider)
                if config["statistics_ip"]:
                    self.stat_ip(cur, client_ip, body_length, is_spider)

                if status_code == 500 or \
                    (method == "POST" and config["record_post_args"] ) or \
                        (status_code == 403 and config["record_403_args"]):
                        logging.debug("记录请求原文: method={}, status_code={}".format(method, 
                            status_code))
                        req_header = json.dumps(request_header)
                else:
                    req_header = ""

                args = [log_time, client_ip, domain, server_name, method, 
                status_code, uri, body_length, referer, user_agent, spider_index,
                protocol, request_time, req_header, ip_list, 
                client_port]
                cur.execute("INSERT INTO site_logs(" \
                    "time,ip,domain,server_name,method,status_code," \
                    "uri,body_length,referer,user_agent,is_spider," \
                    "protocol,request_time,request_headers,ip_list,client_port) " \
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", args)

                logging.debug("日志数据已存储。")

            for key, sqlite_obj in self.sqlite_pool.items():
                if key in server_keys:
                    sqlite_obj["connect"].commit()
                    sqlite_obj["last_commit"] = time.time()

        except Exception as e:
            import traceback
            traceback.print_exc()
        finally:
            pass
            # print(".", end="")
    
    def on_close(self,fd):
        if not fd in self.connections: return
        try:
            self.epoll.unregister(self.connections[fd])
            #print("close: %s" % str(self.addresses[fd]))
        except:
            pass
        try:
            self.connections[fd].close()
        except:
            pass
        try:
            del(self.connections[fd])
            del(self.addresses[fd])
            del(self.passwords[fd])
            del(self.timeouts[fd])
            del(self.tags[fd])
        except:pass

    def clean_fd(self):
        t = time.time()
        for i in self.timeouts.keys():
            if t - self.timeouts[i] < 3600: continue
            if i in self.addresses: del(self.addresses[i])
            if i in self.connections: 
                self.epoll.unregister(self.connections[i])
                self.connections[i].close()
                del(self.connections[i])
            if i in self.timeouts: del(self.timeouts[i])