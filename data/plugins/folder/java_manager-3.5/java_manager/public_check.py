# coding: utf-8
# -----------------------------
# 宝塔Linux面板 java项目管理器
# Author: HUB

import sys, os, time, re

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, files, firewalls


class file:
    path = encoding = ''


class mobj:
    port = ps = ''


class liang:
    version = ''


class public_check(object):

    # 检查端口是否被占用
    def check_port(self, port):
        a = public.ExecShell("netstat -nltp|awk '{print $4}'")
        if a[0]:
            if re.search(':' + port + '\n', a[0]):
                return True
            else:
                return False
        else:
            return False

    # 检查域名合法性
    def is_domain(self, domain):
        import re
        domain_regex = re.compile(r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z', re.IGNORECASE)
        return True if domain_regex.match(domain) else False

    # 本地hosts
    def SetHosts(self, domain):
        ret = public.ReadFile('/etc/hosts')
        import re
        rec = '%s' % domain
        if re.search(rec, ret):
            pass
        else:
            public.ExecShell('echo "127.0.0.1 ' + domain + '" >> /etc/hosts')

    # 随机生成端口
    def generate_random_port(self):
        import random

        port = str(random.randint(5000, 10000))
        while True:
            if not self.check_port(port): break
            port = str(random.randint(5000, 10000))
        return port
    
    # 判断端口是否被占用
    def IsOpen(self, port):
        ip = '0.0.0.0'
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    def create_site(self, get):
        import panelSite
        s = panelSite.panelSite()
        result = s.AddSite(get)
        if 'status' in result: return result;
        result['id'] = public.M('sites').where('name=?', (get.domain,)).getField('id')
        self.set_ssl_check(get.domain)
        return result

    # 设置SSL验证目录过滤
    def set_ssl_check(self, siteName):
        rewriteConf = '''#一键申请SSL证书验证目录相关设置
    location ~ \.well-known{
        allow all;
    }'''
        public.writeFile('vhost/rewrite/' + siteName + '.conf', rewriteConf)
