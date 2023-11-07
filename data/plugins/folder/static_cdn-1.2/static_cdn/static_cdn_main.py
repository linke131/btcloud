#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 黄文良 <287962566@qq.com>
#-------------------------------------------------------------------

#------------------------------
# 面板静态文件加速
#------------------------------
import os,sys,json
import time
import public
from BTPanel import cache
class static_cdn_main:
    plugin_path='plugin/static_cdn'
    hosts_file = plugin_path + '/hosts.json'
    url_file = plugin_path + '/url_file.pl'
    url_open = plugin_path + '/not_open.pl'

    def __init__(self):
        pass
    
    def get_hosts(self,get):
        if not hasattr(public,'get_cdn_url'):
            return public.returnMsg(False,'不支持的版本，请将面板更新到最新，如果已经是最新版，请在首页修复面板!')
        if not self.get_state(get):
            return public.returnMsg(False,'请先开启静态加速功能!')
        hosts = json.loads(public.readFile(self.hosts_file))
        cdn_url = self.get_url(None)
        for i in range(len(hosts)):
            if hosts[i]['url'] == cdn_url:
                hosts[i]['state'] = 1
        return hosts

    def get_host(self,cdn_url):
        hosts = self.get_hosts(None)
        for host in hosts:
            if cdn_url == host['url']:
                return host
        return False

    def get_url(self,get):
        if not self.get_state(get): return False
        if not os.path.exists(self.url_file):
            return False
        return public.readFile(self.url_file).strip()

    def set_state(self,get):
        key = 'static_cdn_state'
        if cache.get(key): return public.returnMsg(False,'请隔3秒钟后再设置!')
        if os.path.exists(self.url_open):
            os.remove(self.url_open)
            public.WriteLog('面板设置','开启面板静态加速功能!')
        else:
            public.writeFile(self.url_open,'')
            public.WriteLog('面板设置','关闭面板静态加速功能!')
        cache.set(key,1,3)
        return public.returnMsg(True,'设置成功!')

    def get_state(self,get):
        return not os.path.exists(self.url_open)
        
    def set_url(self,get):
        if not self.get_state(get):
            return public.returnMsg(False,'请先开启静态加速功能!')
        get.cdn_url = get.cdn_url.strip()
        cdn_url = self.get_url(get)
        if cdn_url == get.cdn_url:
            return public.returnMsg(True,'设置成功!')
        host = self.get_host(get.cdn_url)
        if not host:
            return public.returnMsg(False,'指定CDN节点不存在!')
        public.writeFile(self.url_file,get.cdn_url)
        public.WriteLog('面板设置','设置面板静态加速节点为：{}'.format(host['name']))
        return public.returnMsg(True,'设置成功!')