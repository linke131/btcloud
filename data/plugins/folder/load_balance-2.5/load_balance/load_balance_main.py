#coding: utf-8
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

os.chdir("/www/server/panel")
sys.path.append("/www/server/panel/class/")
import public, send_mail


class load_balance_main(object):
    __log_type = '负载均衡'
    __plugin_path = '/www/server/panel/plugin/load_balance'
    __nginx_conf_path = '/www/server/panel/vhost/nginx'
    nginx_conf_bak = '/tmp/backup_nginx.conf'
    __heartbeat = __plugin_path + '/heartbeat.json'
    __mail_config = '/www/server/panel/data/stmp_mail.json'
    __mail_list_data = '/www/server/panel/data/mail_list.json'
    __dingding_config = '/www/server/panel/data/dingding.json'
    __tcp_load_path = __plugin_path + '/tcp_config'
    __tcp_load_conf_path = '/www/server/panel/vhost/nginx/tcp'

    def __init__(self):
        try:
            self.mail = send_mail.send_mail()
            if not os.path.exists(self.__mail_list_data):
                ret = []
                public.writeFile(self.__mail_list_data, json.dumps(ret))
            else:
                try:
                    mail_data = json.loads(public.ReadFile(self.__mail_list_data))
                    self.__mail_list = mail_data
                except:
                    ret = []
                    public.writeFile(self.__mail_list_data, json.dumps(ret))
        except:
            pass
        self.create_table()

    # 创建表
    def create_table(self):
        # 创建upstream表
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'upstream')).count():
            public.M('').execute('''CREATE TABLE "upstream" (
                            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                            "name" TEXT,
                            "session_type" TEXT,
                            "expires" INTEGER DEFAULT 12,
                            "cookie_name" TEXT DEFAULT "bt_route",
                            "httponly" INTEGER DEFAULT 0,
                            "secure" INTEGER DEFAULT 0,
                            "nodes" TEXT,
                            "addtime" INTEGER);''')
        # 创建server表
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'server')).count():
            public.M('').execute('''CREATE TABLE "server" (
                            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                            "main_domain" TEXT,
                            "default_upstream" TEXT,
                            "domains" TEXT,
                            "locations" TEXT,
                            "addtime" INTEGER);''')

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
            pdata = {}
            pdata['name'] = item['name']
            if public.M('upstream').where('name=?', pdata['name']).count():
                continue
            pdata['session_type'] = item['session_type']
            pdata['expires'] = int(item['expires']) if 'expires' in item else 12
            pdata['cookie_name'] = item['cookie_name'] if 'cookie_name' in item else 'bt_route'
            pdata['httponly'] = int(item['httponly']) if 'httponly' in item else 1
            pdata['secure'] = int(item['secure']) if 'secure' in item else 0
            pdata['nodes'] = json.dumps(item['nodes'])
            pdata['addtime'] = item['time']
            # 旧的配置文件复制到新的配置文件
            old_up_file = self.__nginx_conf_path + '/leveling_' + pdata['name'] + '.conf'
            up_file = self.__nginx_conf_path + '/upstream_' + pdata['name'] + '.conf'
            if os.path.exists(old_up_file):
                shutil.copyfile(old_up_file, up_file)
                os.remove(old_up_file)
            # 插入数据到upstream表
            public.M('upstream').insert(pdata)
            public.WriteLog(self.__log_type, "创建负载均衡配置[{}]".format(pdata['name']))

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

        count = public.M('upstream').count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('upstream').order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        for i in range(len(data_list)):
            data_list[i]['nodes'] = json.loads(data_list[i]['nodes'])
            data_list[i]['total'] = self.get_total(data_list[i]['name'])


        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    def get_all_upstream(self, get):
        '''
        获取所有的upstream
        :param get:
        :return:
        '''
        data = public.M('upstream').select()
        if 'search' in get:
            search_data = []
            for item in data:
                if get['search'] in item['name']:
                    search_data.append(item)
            data = search_data
        for item in data:
            item['nodes'] = json.loads(item['nodes'])
        return data

    def get_upstream_find(self, get):
        '''
        获取指定upstream的详情
        :param get:
        :return:
        '''
        data = public.M('upstream').where('id=?', get.id).find()
        data['nodes'] = json.loads(data['nodes'])
        return data

    def add_upstream(self, get):
        '''
        新增upstream
        :param get:
        :return:
        '''
        pdata = {}
        pdata['name'] = get.up_name.strip()
        if pdata['name'].find('.') != -1: return public.returnMsg(False,'负载均衡名称中不能包含`.`')
        if not pdata['name']: return public.returnMsg(False, '资源名称不能为空')
        if os.path.exists(self.__nginx_conf_path + '/leveling_' + pdata['name'] + '.conf'):
            return public.returnMsg(False, '旧的负载均衡已经添加名为[%s]的负载均衡，请先删除' % pdata['name'])

        self.get_node_list(None)
        if public.M('upstream').where('name=?', pdata['name']).count():
            return public.returnMsg(False, '资源[%s]已经存在，不能重复添加' % pdata['name'])
        pdata['session_type'] = get.session_type
        pdata['expires'] = int(get.expires) if 'expires' in get else 12
        pdata['cookie_name'] = get.cookie_name if 'cookie_name' in get else 'bt_route'
        pdata['httponly'] = int(get.httponly) if 'httponly' in get else 1
        pdata['secure'] = int(get.secure) if 'secure' in get else 0
        pdata['nodes'] = get.nodes
        if get.session_type == 'ip_hash':
            for item in json.loads(get.nodes):
                if item['state'] == 2:
                    return public.returnMsg(False, 'IP会话跟随中不能存在备份节点')
        pdata['addtime'] = int(time.time())
        # 更新配置文件
        result = self.__write_upstream(pdata, add=True)
        if not result['status']: return result
        public.M('upstream').insert(pdata)
        public.WriteLog(self.__log_type, "创建负载均衡配置[{}]".format(pdata['name']))
        return public.returnMsg(True, '添加成功!')

    def modify_upstream(self, get):
        '''
        编辑upstream
        :param get:
        :return:
        '''
        if 'id' not in get: return public.returnMsg(False, '缺少id参数!')
        pdata = {}
        pdata['name'] = get.up_name.strip()
        pdata['session_type'] = get.session_type
        pdata['expires'] = int(get.expires) if 'expires' in get else 12
        pdata['cookie_name'] = get.cookie_name if 'cookie_name' in get else 'bt_route'
        pdata['httponly'] = int(get.httponly) if 'httponly' in get else 1
        pdata['secure'] = int(get.secure) if 'secure' in get else 0
        pdata['nodes'] = get.nodes
        if get.session_type == 'ip_hash':
            for item in json.loads(get.nodes):
                if item['state'] == 2:
                    return public.returnMsg(False, 'IP会话跟随中不能存在备份节点')
        # 更新配置文件
        result = self.__write_upstream(pdata, add=False)
        if not result['status']: return result
        public.M('upstream').where('name=?', pdata['name']).update(pdata)
        public.WriteLog(self.__log_type, "修改负载均衡配置[{}]".format(pdata['name']))
        return public.returnMsg(True, '修改成功!')

    def delete_upstream(self, get):
        '''
        删除upstream
        :param get: id
        :return:
        '''
        if 'id' not in get: return public.returnMsg(False, '缺少id参数!')
        pdata = public.M('upstream').where('id=?', int(get.id)).find()
        up_file = self.__nginx_conf_path + '/upstream_' + pdata['name'] + '.conf'
        if os.path.exists(up_file):
            shutil.copyfile(up_file, '/tmp/ng_file_bk.conf')
            os.remove(up_file)
        # 检查nginx配置
        conf_status = public.checkWebConfig()
        if conf_status is not True:
            shutil.copyfile('/tmp/ng_file_bk.conf', up_file)
            return public.returnMsg(False, 'ERROR: 配置出错<br><a style="color:red;">' + conf_status.replace("\n", '<br>') + '</a>')
        public.serviceReload()
        public.M('upstream').where('id=?', int(get.id)).delete()
        public.WriteLog(self.__log_type, "删除负载均衡配置[{}]".format(pdata['name']))
        return public.returnMsg(True, '删除成功!')

    def __write_upstream(self, pdata, add=True):
        '''
        将upstream规则写到配置文件
        :param get:
        :return:
        '''
        name = pdata['name']
        up_file = self.__nginx_conf_path + '/upstream_' + name + '.conf'
        if os.path.exists(up_file):
            shutil.copyfile(up_file, '/tmp/ng_file_bk.conf')
        httponly = ''
        if int(pdata['httponly']) == 1:
            httponly = ' httponly'
        secure = ''
        if int(pdata['secure']) == 1:
            secure = ' secure'

        modes = {'ip_hash': ['ip_hash', '#sticky'], 'sticky': ['#ip_hash', 'sticky'], 'off': ['#ip_hash', '#sticky']}
        ip_hash = modes[pdata['session_type']][0]
        sticky = modes[pdata['session_type']][1]

        nodes = ''
        for node in json.loads(pdata['nodes']):
            states = ['down', 'weight=' + str(node['weight']), 'backup']
            nodes += '    server ' + node['server'].strip() + ':' + str(node['port']) + ' max_fails=' + str(node['max_fails']) + ' fail_timeout=' + str(node['fail_timeout']) + 's ' + states[int(node['state'])] + ";\n"

        upBody = '''upstream %s {
    %s;
%s
    %s name=%s expires=%sh%s%s;
}''' % (name, ip_hash, nodes, sticky, pdata['cookie_name'], pdata['expires'], httponly, secure)
        public.writeFile(up_file, upBody)
        # 检查nginx配置
        conf_status = public.checkWebConfig()
        if conf_status is not True:
            if add:
                os.remove(up_file)
            else:
                shutil.copyfile('/tmp/ng_file_bk.conf', up_file)
            return public.returnMsg(False, 'ERROR: 配置出错<br><a style="color:red;">' + conf_status.replace("\n", '<br>') + '</a>')
        public.serviceReload()
        return public.returnMsg(True, '配置成功')

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
        ip = get.ip
        port = get.port
        path = get.path
        if port == '443':
            url = 'https://' + str(ip) + str(path.strip())
        else:
            url = 'http://' + str(ip) + ':' + str(port) + str(path.strip())
        ret = self.__http_get(url)
        if not ret:
            return public.returnMsg(False, '访问节点[%s]失败' % url)
        return public.returnMsg(True, '访问节点[%s]成功' % url)


    def check_tcp(self,get):
        import socket
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect((get.ip.strip(),int(get.port)))
            s.close()
        except:
            return public.returnMsg(False,'无法连接{}:{}，请检查目标机器是否放行端口'.format(get.ip,get.port))
        return public.returnMsg(True,'访问节点[{}:{}]成功!'.format(get.ip,get.port))


    def __http_get(self, url):
        '''
        发送检测请求
        :param url:
        :return:
        '''
        ret = re.search(r'https://', url)
        if ret:
            try:
                from gevent import monkey
                monkey.patch_ssl()
                import requests
                ret = requests.get(url=str(url), verify=False, timeout=10)
                status = [200, 301, 302, 404, 403]
                if ret.status_code in status:
                    return True
                else:
                    return False
            except:
                return False
        else:
            try:
                if sys.version_info[0] == 2:
                    import urllib2
                    rec = urllib2.urlopen(url, timeout=3)
                else:
                    import urllib.request
                    rec = urllib.request.urlopen(url, timeout=3)
                status = [200, 301, 302, 404, 403]
                if rec.getcode() in status:
                    return True
                return False
            except:
                return False


    def __get_mod(self):
        from BTPanel import session
        from panelAuth import panelAuth
        skey = 'bt_load_balcnce_res'
        if skey in session: return public.returnMsg(True,'OK!')
        params = {}
        params['pid'] = '100000009'
        result = panelAuth().send_cloud('check_plugin_status',params)
        try:
            if not result['status']:
                if skey in session: del(session[skey])
                return result
        except: pass
        session[skey] = True
        return result

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
        # result = self.__get_mod()
        # if result['status'] == False: return result

        count = public.M('server').count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('server').order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        for i in range(len(data_list)):
            try:
                data_list[i]['domains'] = json.loads(data_list[i]['domains'])
                data_list[i]['locations'] = json.loads(data_list[i]['locations'])
                data_list[i]['total'] = self.get_total(data_list[i]['default_upstream'])
                if 'status' in data_list[i]['total']:
                    data_list[i]['total'] = {}
                us = public.M('upstream').where('name=?',data_list[i]['default_upstream']).find()
                try:
                    data_list[i]['nodes'] = json.loads(us['nodes'])
                except:
                    data_list[i]['nodes'] = []
                del(us['nodes'])
                data_list[i]['upstream_info'] = us
            except:
                pass
        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}


    def get_node_list(self,get):
        '''
            @name 获取节点列表
            @author hwliang<2021-05-28>
            @param get
            @return list
        '''
        upstreams = public.M('upstream').select()
        nodes = []
        revs = []
        for upstream in upstreams:
            tmp_nodes = json.loads(upstream['nodes'])
            main_domain = public.M('server').where('default_upstream=?',upstream['name']).getField('main_domain')
            if not main_domain:
                up_file = self.__nginx_conf_path + '/upstream_' + upstream['name'] + '.conf'
                if os.path.exists(up_file): os.remove(up_file)
                public.M('upstream').where('name=?',upstream['name']).delete()
                continue
            for tn in tmp_nodes:
                if "{}:{}".format(tn['server'],tn['port']) in revs: continue
                node = tn
                total_arr = self.get_total_node(tn)
                node['node']  = total_arr['node']
                node['day_count']  = total_arr['day_count']
                node['day_error']  = total_arr['day_error']
                node['day_speed']  = total_arr['day_speed']
                node['last_request_time']  = total_arr['last_request_time']
                node['request_timeout']  = total_arr['request_timeout']
                node['main_domain'] = main_domain
                revs.append(node['node'])
                nodes.append(node)

        del(revs)
        return sorted(nodes,key=lambda x:x['day_count'],reverse=True)


    def get_total_today(self,get):
        '''
            @name 获取指定日期的负载均衡统计信息
            @author hwliang<2021-05-28>
            @param get<dict_obj>{
                upstream_name 资源名称
                day_date 日期
            }
        '''
        if not 'upstream_name' in get:
            return public.returnMsg(False,'资源名称不能为空')

        if not 'day_date' in get:
            get.day_date = public.format_date('%Y-%m-%d')

        return self.get_total(get.upstream_name,get.day_date)


    def get_load_logs(self,get):
        '''
            @name 获取指定日期的负载均衡访问日志
            @author hwliang<2021-05-28>
            @param get<dict_obj>{
                main_domain 负载均衡主域名
                day_date 日期
                p 分页
            }
        '''

        if not 'main_domain' in get:
            return public.returnMsg(False,'主域名不能为空')

        if not 'day_date' in get:
            get.day_date = public.format_date('%Y-%m-%d')

        s_path = '/www/wwwlogs/load_balancing/logs/{}'.format(get.main_domain)
        load_log_file = '{}/{}.log'.format(s_path,get.day_date)
        result = {}
        result['total_size'] = 0
        result['size'] = 0
        result['data'] = []
        result['end'] = True
        if not os.path.exists(s_path): return result
        m = 0
        if os.path.exists(load_log_file): result['size'] = os.path.getsize(load_log_file)
        for uname in os.listdir(s_path):
            filename = s_path + '/' + uname
            if os.path.isdir(filename): continue
            result['total_size'] += os.path.getsize(filename)

        try:
            from cgi import html
            pyVersion = sys.version_info[0]
            num = 10
            if not os.path.exists(load_log_file): return result
            p = 1
            if 'p' in get:
                p = int(get.p)

            start_line = (p - 1) * num
            count = start_line + num
            fp = open(load_log_file,'rb')
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
                                    for i in range(len(tmp_data)): tmp_data[i] = html.escape(str(tmp_data[i]),True)
                                    data.append(tmp_data)
                                else: m+=1
                            except: m+= 1
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
        except: data = []
        result['end'] = False
        if len(data) + m < num:
            result['end'] = True
        result['continue_line'] = m
        result['data'] = data
        return result



    def get_total(self,upstream_name,day_date = None):
        '''
            @name 获取负载均衡统计信息
            @author hwliang<2021-05-28>
            @param item<dcit> 负载均衡信息
            @return dict
        '''
        nodes = public.M('upstream').where('name=?',upstream_name).getField('nodes')
        result = {'day_count':0,'day_error':0,'day_speed':0,'request_timeout':0,'last_request_time':0}
        result['nodes'] = []
        if not nodes: return result
        nodes = json.loads(nodes)
        if not day_date: day_date = public.format_date('%Y-%m-%d')
        day_time = int(time.time())



        for node in nodes:
            tmp = self.get_total_node(node,day_date,upstream_name)
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


    def get_total_node(self,node,day_date = None,upstream_name = None):
        '''
            @name 获取指定节点统计信息
            @author hwliang<2021-05-28>
            @param node<dict> 节点信息
            @param day_date<string> 日期
            @return dict
        '''
        total_path = '/www/wwwlogs/load_balancing/total/{}/{}.pl'
        if not day_date: day_date = public.format_date('%Y-%m-%d')

        load_tmp = {}
        load_tmp['day_count'] = 0
        load_tmp['day_error'] = 0
        load_tmp['day_speed'] = 0
        load_tmp['request_timeout'] = 0
        load_tmp['last_request_time'] = 0

        load_total_day_file = total_path.format(upstream_name,day_date)
        if os.path.exists(load_total_day_file):
            day_tmp = public.readFile(load_total_day_file).split(' ')
            load_tmp['day_count'] = int(day_tmp[0])
            load_tmp['day_error'] = int(day_tmp[1])
            load_tmp['day_speed'] = int(day_tmp[2])
            load_tmp['request_timeout'] = int(day_tmp[3])
            load_tmp['last_request_time'] = int(day_tmp[4])

        tmp = {}
        tmp['node'] = "{}:{}".format(node['server'],node['port'])
        tmp['day_count'] = 0
        tmp['day_error'] = 0
        tmp['day_speed'] = 0
        tmp['request_timeout'] = 0
        tmp['last_request_time'] = 0

        total_day_file = total_path.format(tmp['node'].replace(':','_'),day_date)
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
        pdata = {}
        domain_list = json.loads(get.domains)
        pdata['main_domain'] = domain_list[0].split(':')[0]

        if public.M('domain').where('name=?',pdata['main_domain']).count():
            return public.returnMsg(False, '指定域名已经在网站列表中添加过了，不能重复添加!')

        for domain in domain_list:
            if public.M('domain').where('name=?',domain.split(':')[0]).count():
                return public.returnMsg(False, '指定域名已经在网站列表中添加过了，不能重复添加!')

        if public.M('server').where('main_domain=?', pdata['main_domain']).count():
            return public.returnMsg(False, '指定的负载均衡已经存在，不能重复添加')
        pdata['domains'] = get.domains
        pdata['default_upstream'] = get.default_upstream
        pdata['locations'] = get.locations if 'locations' in get else '[]'
        pdata['addtime'] = int(time.time())
        # 创建网站
        result = self.create_site(get)
        if 'status' in result: return result
        # 创建proxy配置文件
        # result = self.__write_server(pdata)
        result = self.create_proxy(pdata, add=True)
        if not result['status']:
            get.id = public.M('sites').where('name=?', pdata['main_domain']).getField('id')
            get.webname = pdata['main_domain']
            import panelSite
            panelSite.panelSite().DeleteSite(get)
            return result
        public.M('server').insert(pdata)
        public.WriteLog(self.__log_type, "创建网站负载均衡[{}]".format(pdata['main_domain']))
        return public.returnMsg(True, '添加成功!')

    def modify_server(self, get):
        '''
        编辑server
        :param get:
        :return:
        '''
        if 'id' not in get: return public.returnMsg(False, '缺少id参数!')
        pdata = public.M('server').where('id=?', get.id).find()
        # domain_list = json.loads(get.domains)
        # if pdata['main_domain'] != domain_list[0].split(':')[0]:
        #     return public.returnMsg(False, '主域名不能修改!')
        # pdata['domains'] = get.domains
        pdata['default_upstream'] = get.default_upstream
        pdata['locations'] = get.locations
        # 更新proxy配置文件
        # result = self.__write_server(pdata)
        result = self.create_proxy(pdata, add=False)
        if not result['status']: return result
        public.M('server').where('id=?', get.id).update(pdata)
        public.WriteLog(self.__log_type, "修改网站负载均衡[{}]".format(pdata['main_domain']))
        return public.returnMsg(True, '修改成功!')

    def create_site(self, get):
        '''
        创建关联站点
        :param get:
        :return:
        '''
        domains = json.loads(get.domains)
        mainDomain = domains[0].split(':')
        if len(mainDomain) == 1: mainDomain.append('80')
        del (domains[0])
        get.webname = json.dumps({'domain': mainDomain[0], 'domainlist': domains, 'count': len(domains)})
        get.port = mainDomain[1]
        get.ftp = 'false'
        get.sql = 'false'
        get.version = '00'
        get.ps = '负载均衡[' + mainDomain[0] + ']的绑定站点'
        get.path = public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + mainDomain[0]
        import panelSite
        s = panelSite.panelSite()
        result = s.AddSite(get)
        if 'status' in result: return result
        result['id'] = public.M('sites').where('name=?', (mainDomain[0],)).getField('id')
        return result

    def check_upstream_https(self, up_name):
        '''
        获取指定upstream的节点是否使用了https端口443，8443
        :param up_name:
        :return:
        '''
        data = public.M('upstream').where('name=?', up_name).find()
        data['nodes'] = json.loads(data['nodes'])
        for node in data['nodes']:
            if node['port'] in (443, 8443):
                return True
        return False

    def create_proxy(self, pdata, add=True):
        '''
        将locatin规则写到反向代理配置文件
        :param pdata:
        :return:
        '''
        proxy_dir = self.__nginx_conf_path + '/proxy/' + pdata['main_domain']
        if not os.path.exists(proxy_dir):
            os.makedirs(proxy_dir)
        locations = self.__gen_locations(json.loads(pdata['locations']))
        if self.check_upstream_https(pdata['default_upstream']):
            proxy_pass = 'https://' + pdata['default_upstream']
        else:
            proxy_pass = 'http://' + pdata['default_upstream']
        conf_body = '''#PROXY-START
%s

location / {
    proxy_pass %s;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header REMOTE-HOST $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
}

set $site_name %s;
include /www/server/panel/vhost/nginx/load_total.lua;
#PROXY-END''' % (locations, proxy_pass,pdata['main_domain'])
        conf_file = proxy_dir + '/load_balance.conf'
        if os.path.exists(conf_file): shutil.copyfile(conf_file, '/tmp/ng_file_bk.conf')
        public.writeFile(conf_file, conf_body)
        # 网站配置文件增加反向代理配置
        ng_file = "/www/server/panel/vhost/nginx/" + pdata['main_domain'] + ".conf"
        ng_conf = public.readFile(ng_file)
        rep = r"include.*\/proxy\/.*\*.conf;"
        if not re.search(rep, ng_conf):
            ng_proxyfile = "/www/server/panel/vhost/nginx/proxy/%s/*.conf" % pdata['main_domain']
            ng_conf = ng_conf.replace("include enable-php-", "\n\t#引用反向代理规则，注释后配置的反向代理将无效\n\t" + "include " + ng_proxyfile + ";\n\n\tinclude enable-php-")
        static_conf = r'''location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }

    location ~ .*\.(js|css)?$
    {
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }'''
        if static_conf in ng_conf:
            ng_conf = ng_conf.replace(static_conf, '')

        ng_conf = re.sub(r"location .{3,30}\(gif(.|\s){1,350}\}\s+","",ng_conf)
        public.writeFile(ng_file, ng_conf)
        # 检查nginx配置
        conf_status = public.checkWebConfig()
        if conf_status is not True:
            if add:
                os.remove(conf_file)
            else:
                shutil.copyfile('/tmp/ng_file_bk.conf', conf_file)
            return public.returnMsg(False, 'ERROR: 配置出错<br><a style="color:red;">' + conf_status.replace("\n", '<br>') + '</a>')
        public.serviceReload()
        return public.returnMsg(True, '配置成功')

    def __gen_locations(self, location_list):
        '''
        根据locations生成location配置
        :param locations:
        :return:
        '''
        location_conf = ''
        for item in location_list:
            if item['type'] == '' and item['rule'] == '/': continue
            if self.check_upstream_https(item['proxy_pass']):
                proxy_pass = 'https://' + item['proxy_pass']
            else:
                proxy_pass = 'http://' + item['proxy_pass']
            location = '''location %s %s {
    proxy_pass %s;
    proxy_set_header Host %s;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header REMOTE-HOST $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
}\n''' % (item['type'], item['rule'], proxy_pass, item['host'])
            location_conf += location

        return location_conf

    def delete_server(self, get):
        '''
        删除server
        :param get:
        :return:
        '''
        if 'id' not in get: return public.returnMsg(False, '缺少id参数!')
        server_id = int(get.id)
        pdata = public.M('server').where('id=?', server_id).find()
        get.id = public.M('sites').where('name=?', pdata['main_domain']).getField('id')
        get.webname = pdata['main_domain']
        import panelSite
        panelSite.panelSite().DeleteSite(get)
        conf_file = self.__nginx_conf_path + '/' + pdata['main_domain'] + '.conf'
        if os.path.exists(conf_file): os.remove(conf_file)
        public.serviceReload()
        public.M('server').where('id=?', server_id).delete()
        get.id = public.M('upstream').where('name=?', pdata['default_upstream']).getField('id')
        self.delete_upstream(get)
        public.WriteLog(self.__log_type, "删除网站负载均衡[{}]".format(pdata['main_domain']))
        return public.returnMsg(True, '删除成功!')

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
        if 'first_domain' not in get: get.first_domain = siteName

        # Nginx配置
        file = '/www/server/panel/vhost/nginx/' + siteName + '.conf'
        ng_file = file
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
                    listen = re.search(rep,conf).group()
                    versionStr = public.readFile('/www/server/nginx/version.pl')
                    http2 = ''
                    if versionStr:
                        if versionStr.find('1.8.1') == -1: http2 = ' http2'
                    default_site = ''
                    if conf.find('default_server') != -1: default_site = ' default_server'

                    listen_ipv6 = ';'
                    if os.path.exists('/www/server/panel/data/ipv6.pl'): listen_ipv6 = ";\n\tlisten [::]:443 ssl"+http2+default_site+";"
                    conf = conf.replace(listen, listen + "\n\tlisten 443 ssl"+http2 + default_site + listen_ipv6)
                shutil.copyfile(file, self.nginx_conf_bak)
                public.writeFile(file, conf)

        isError = public.checkWebConfig()
        if isError is not True:
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, ng_file)
            public.ExecShell("rm -f /tmp/backup_*.conf")
            return public.returnMsg(False, '证书错误: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')
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
        if not 'nodes' in get: return public.returnMsg(False,'缺少节点参数')
        try:
            nodes = json.loads(get.nodes)
            if nodes in ['false',False,None]: return public.returnMsg(False,'至少需要添加1个节点')
            _ok = False
            for node in nodes:
                if node['state'] in ['1',1]: _ok = True
            if not _ok: return public.returnMsg(False,'至少需要添加一个【参与】负载的的节点')
        except:
            return public.returnMsg(False,'至少需要添加1个节点')

        result = self.add_upstream(get)
        if not result['status']: return result
        get.default_upstream = get.up_name
        if get.up_name.find('.') != -1: return public.returnMsg(False,'负载均衡名称中不能包含`.`')
        result = self.add_server(get)
        if not result['status']: return result
        return public.returnMsg(True, '添加成功')

    def get_logs(self, get):
        '''
        获取日志
        :param get:
        :return:
        '''
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', self.__log_type).count()
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
        data['data'] = public.M('logs').where('type=?', self.__log_type).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    def del_log(self, get):
        '''
        # 删除日志
        :param get:
        :return:
        '''
        public.M('logs').where('type=?', self.__log_type).delete()
        return public.returnMsg(True, '清理成功')

    def get_heartbeat_conf(self, get):
        '''
        获取告警邮箱列表和心跳检测设置
        :param get:
        :return:
        '''
        if not os.path.exists(self.__heartbeat):
            public.writeFile(self.__heartbeat, json.dumps({'time': 30, 'warning': 3}))
        upBody = public.readFile(self.__heartbeat)
        data = json.loads(upBody)
        if public.M('crontab').where('name=?', (u'[勿删]负载均衡节点心跳检测任务',)).count():
            data['open'] = True
        else:
            data['open'] = False
        return {'emails': self.__mail_list, 'heartbeat': data}

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
        public.writeFile(self.__heartbeat, json.dumps(heartbeat))

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
        data['sBody'] = '{} {}/check_task.py'.format(python_path, self.__plugin_path)
        data['backupTo'] = 'localhost'
        data['sType'] = 'toShell'
        data['hour'] = ''
        data['minute'] = ''
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''
        crontab.crontab().AddCrontab(data)
        public.WriteLog(self.__log_type, '修改心跳包检测配置')
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
        public.WriteLog(self.__log_type, '关闭心跳包检测配置')
        return public.returnMsg(True, '已关闭任务')

    def check_node(self):
        '''
        检测节点
        :return:
        '''
        upstream_list = public.M('upstream').select()
        mail_body = ''
        for upstream in upstream_list:
            for node in json.loads(upstream['nodes']):
                # 不检查状态为down的节点
                if int(node['state']) == 0: continue
                if int(node['port']) == 443:
                    urlstr = 'https://' + node['server'].strip() + ':' + str(node['port']) + str(node['path'])
                else:
                    urlstr = 'http://' + node['server'].strip() + ':' + str(node['port']) + str(node['path'])
                print(u'正在检测资源[%s]中的节点[%s], 检测url[%s]' % (upstream['name'], node['server'], urlstr))
                status = self.__http_get(urlstr)
                if not status:
                    msg = u'负载【%s】中节点【%s】检测失败<br />' % (upstream['name'], node['server'].strip())
                    print(msg)
                    mail_body += msg
        if mail_body:
            self.send_mail(mail_body)

    # 发送邮件通知
    def send_mail(self, mail_body, send='mail'):
        title = "负载均衡节点异常"
        mail_body += "</tbody></table><hr><p>此为堡塔面板通知邮件，请勿回复</p>"

        tongdao = self.get_settings()

        if send == 'dingding':
            if tongdao['dingding']:
                msg = mail_body
                self.mail.dingding_send(msg)
        elif send == 'mail':
            if tongdao['user_mail']:
                if len(self.__mail_list) == 0:
                    if tongdao['user_mail']['user_name']:
                        self.mail.qq_smtp_send(str(tongdao['user_mail']['info']['qq_mail']), title=title, body=mail_body)
                else:
                    for i in self.__mail_list:
                        if tongdao['user_mail']['user_name']:
                            self.mail.qq_smtp_send(str(i), title=title, body=mail_body)

    # 查看能使用的告警通道
    def get_settings(self, get=None):
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            user_mail = False
        else:
            user_mail = True
        dingding_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(dingding_info) == 0:
            dingding = False
        else:
            dingding = True
        ret = {}
        ret['user_mail'] = {"user_name": user_mail, "mail_list": self.__mail_list, "info": self.get_user_mail()}
        ret['dingding'] = {"dingding": dingding, "info": self.get_dingding()}
        return ret

    # 查看自定义邮箱配置
    def get_user_mail(self, get=None):
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            return False
        return qq_mail_info

    # 查看钉钉
    def get_dingding(self, get=None):
        qq_mail_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(qq_mail_info) == 0:
            return False
        return qq_mail_info


    def check_port_exists(self,load_port):
        '''
            @name 检查端口是否占用
            @author hwliang<2021-05-29>
            @param port<int> 端口
            @return bool
        '''

        for c_name in os.listdir(self.__tcp_load_path):
            filename = "{}/{}".format(self.__tcp_load_path,c_name)
            if not os.path.exists(filename): continue
            tcp_info = json.loads(public.readFile(filename))
            if tcp_info['load_port'] == load_port:
                return True

        if public.ExecShell('lsof -i:{}|grep LISTEN'.format(load_port))[0].strip():
            return True
        return False


    def check_tcpname_exists(self,load_name):
        '''
            @name 检查负载名称是否存在
            @author hwliang<2021-05-29>
            @param port<int> 端口
            @return bool
        '''
        if not os.path.exists(self.__tcp_load_path):
            os.makedirs(self.__tcp_load_path,384)

        if load_name + ".json" in os.listdir(self.__tcp_load_path):
            return True
        return False


    def save_tcpload(self,tcp_info):
        '''
            @name 保存TCP负载均衡配置信息
            @author hwliang<2021-05-29>
            @param tcp_info<dict> TCP配置信息
            @return bool
        '''

        filename = "{}/{}.json".format(self.__tcp_load_path,tcp_info['load_name'])
        public.writeFile(filename,json.dumps(tcp_info))
        self.write_tcp_conf(tcp_info)


    def write_tcp_conf(self,tcp_info):
        '''
            @name 写入到TCP负载均衡配置文件
            @author hwliang<2021-05-29>
            @param tcp_info<dict> TCP配置信息
            @return bool
        '''
        self.tcp_load_check()
        servers = []
        states = [' down','',' backup']
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
        if not 'load_udp' in tcp_info:
            tcp_info['load_udp'] = 0
        udp_tips = ''
        if tcp_info['load_udp']: udp_tips = " udp reuseport"
        ip_hash = '' if tcp_info['load_iphash'] == 0 or is_backup else "\thash $remote_addr consistent;\n"
        tcp_conf = '''upstream tcp_{load_name} {{
{ip_hash}{servers}
}}

server {{
    listen {address}:{port}{udp_tips};
    proxy_connect_timeout {connect_timeout}s;
    proxy_timeout {timeout}s;
    proxy_pass tcp_{load_name};
    access_log /www/wwwlogs/load_balancing/tcp/{load_name}.log tcp_format;
}}
'''.format(
    load_name=tcp_info['load_name'],
    ip_hash = ip_hash,
    udp_tips = udp_tips,
    servers = "\n".join(servers),
    address = tcp_info['load_address'],
    port = tcp_info['load_port'],
    connect_timeout = tcp_info['load_connect_timeout'],
    timeout = tcp_info['load_timeout']
)
        if not os.path.exists(self.__tcp_load_conf_path):
            os.makedirs(self.__tcp_load_conf_path)
        conf_file = "{}/{}.conf".format(self.__tcp_load_conf_path,tcp_info['load_name'])
        public.writeFile(conf_file,tcp_conf)
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
        public.writeFile(ngx_conf_file,ngx_conf)


    def create_tcp_load(self,get):
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
            'load_udp': int(getattr(get,'load_udp','0')),
            'load_connect_timeout': int(get.load_connect_timeout),
            'load_timeout': int(get.load_timeout),
            'load_iphash': int(get.load_iphash),
            'load_ps': get.load_ps.strip(),
            'nodes': json.loads(get.nodes)
        }

        if tcp_info['load_port'] > 65535 or tcp_info['load_port'] < 1:
            return public.returnMsg(False,'监听端口范围不正确，应在1-65535之间')

        if self.check_tcpname_exists(tcp_info['load_name']):
            return public.returnMsg(False,'指定负载均衡名称已存在')

        if self.check_port_exists(tcp_info['load_port']):
            return public.returnMsg(False,'指定监听端口已被占用，请使用其它端口!')

        n = 0
        for node in tcp_info['nodes']:
            if node['state'] ==1: n+=1

        if n < 1: return public.returnMsg(False,'最少需要1个[参与]负载均衡的节点!')

        self.save_tcpload(tcp_info)
        public.WriteLog('负载均衡',"添加TCP负载均衡[{}]配置".format(get.load_name))
        return public.returnMsg(True,'创建成功!')

    def modify_tcp_load(self,get):
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
            'load_udp': int(getattr(get,'load_udp','0')),
            'load_connect_timeout': int(get.load_connect_timeout),
            'load_timeout': int(get.load_timeout),
            'load_iphash': int(get.load_iphash),
            'load_ps': get.load_ps.strip(),
            'nodes': json.loads(get.nodes)
        }


        if tcp_info['load_port'] > 65535 or tcp_info['load_port'] < 1:
            return public.returnMsg(False,'监听端口范围不正确，应在1-65535之间')


        filename = "{}/{}.json".format(self.__tcp_load_path,tcp_info['load_name'])
        if not os.path.exists(filename):
            return public.returnMsg(False,'指定负载均衡不存在!')

        n = 0
        for node in tcp_info['nodes']:
            if node['state'] ==1: n+=1

        if n < 1: return public.returnMsg(False,'最少需要1个[参与]负载均衡的节点!')

        old_tcp_info = json.loads(public.readFile(filename))
        if old_tcp_info['load_port'] != tcp_info['load_port']:
            if self.check_port_exists(tcp_info['load_port']):
                return public.returnMsg(False,'指定监听端口已被占用，请使用其它端口!')


        self.save_tcpload(tcp_info)
        public.WriteLog('负载均衡',"修改TCP负载均衡[{}]配置".format(get.load_name))
        return public.returnMsg(True,'修改成功!')


    def remove_tcp_load(self,get):
        '''
            @name 删除指定TCP负载均衡
            @author hwliang<2021-05-29>
            @param get<dict_obj>{
                load_name: string<负载均衡名称>
            }
            @return dict
        '''
        load_name = get['load_name'].strip()
        filename = "{}/{}.json".format(self.__tcp_load_path,load_name)
        if not os.path.exists(filename):
            return public.returnMsg(False,'指定负载均衡不存在!')

        os.remove(filename)

        conf_file = "{}/{}.conf".format(self.__tcp_load_conf_path,load_name)
        if os.path.exists(conf_file):
            os.remove(conf_file)
            public.ServiceReload()

        public.WriteLog('负载均衡',"删除TCP负载均衡[{}]配置".format(load_name))
        return public.returnMsg(True,'删除成功!')


    def get_tcp_load_list(self,get):
        '''
            @name 获取TCP负载均衡列表
            @author hwliang<2021-05-29>
            @return list
        '''
        if not os.path.exists(self.__tcp_load_path):
            os.makedirs(self.__tcp_load_path,384)
        result = []
        for c_name in os.listdir(self.__tcp_load_path):
            filename = "{}/{}".format(self.__tcp_load_path,c_name)
            if not os.path.exists(filename): continue
            tcp_info = json.loads(public.readFile(filename))
            tcp_info['total'] = self.get_tcp_load_total(tcp_info['load_name'])
            result.append(tcp_info)
        return result

    def utc_to_time(self,s_date):
        '''
            @name UTC时间转时间戳
            @author hwliang<2021-06-01>
            @param s_date<string> UTC格式时间
            @return int
        '''
        try:
            return int(time.mktime(time.strptime(s_date,"%d/%b/%Y:%H:%M:%S %z")))
        except:
            return s_date


    def get_tcp_load_total(self,load_name):
        '''
            @name 获取指定TCP负载均衡统计信息
            @author hwliang<2021-06-01>
            @param load_name<string> 负载均衡名称
            @return dict
        '''
        load_log_file = '/www/wwwlogs/load_balancing/tcp/{}.log'.format(load_name)
        num = 5000
        tmp_lines = public.GetNumLines(load_log_file,num)
        line_size = 95
        lines = tmp_lines.strip().split("\n")

        result = {'count':0,'error':0,'speed':0,'request_timeout':0,'last_request_time':0}
        if not lines: return result
        line_len = len(lines)
        size_count = int(os.path.getsize(load_log_file) / line_size)
        if line_len > size_count - num:
            result['count'] = line_len
        else:
            result['count'] =  size_count

        last_line = lines[-1].split('|')
        if len(last_line) != 11: return result
        result['last_request_time'] = self.utc_to_time(last_line[0])
        result['request_timeout'] = int(float(last_line[6]) * 1000)

        for line in lines:
            tmp = line.split('|')
            if len(tmp) != 11: continue
            if tmp[3] != '200':
                result['error'] += 1
            if last_line[0] == tmp[0]: result['speed'] += 1

        if time.time() - result['last_request_time'] > 5:
            result['speed'] = 0

        return result





    def get_tcp_load_find(self,get):
        '''
            @name 获取指定TCP负载均衡配置信息
            @author hwliang<2021-05-29>
            @param get<dict_obj>{
                load_name: string<负载均衡名称>
            }
            @return dict
        '''
        load_name = get['load_name'].strip()
        filename = "{}/{}.json".format(self.__tcp_load_path,load_name)
        if not os.path.exists(filename):
            return public.returnMsg(False,'指定负载均衡不存在!')
        tcp_info = json.loads(public.readFile(filename))
        return tcp_info

    def get_tcp_load_logs(self,get):
        '''
            @name 获取指定TCP负载均衡访问日志
            @author hwliang<2021-05-29>
            @param get<dict_obj>{
                load_name: string<负载均衡名称>
            }
            @return dict
        '''
        if not 'load_name' in get:
            return public.returnMsg(False,'负载均衡名称不能为空')

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
            fp = open(load_log_file,'rb')
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
                                    for i in range(len(tmp_data)): tmp_data[i] = cgi.escape(str(tmp_data[i]),True)
                                    tmp_data[0] = public.format_date(times = self.utc_to_time(tmp_data[0]))
                                    tmp_data[6] = str(int(float(tmp_data[6]) * 1000)) + 'ms'
                                    data.append(tmp_data)
                                else:
                                    m+=1
                            except: m+=1
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
        except: data = []
        result['end'] = False
        if len(data)+m < num:
            result['end'] = True
        result['continue_line'] = m
        result['data'] = data
        return result










if __name__ == '__main__':
    p = load_balance_main()
    p.check_node()
