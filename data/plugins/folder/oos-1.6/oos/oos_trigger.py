#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys
import os
import json
import time
import pwd
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
import public

class trigger:
    plugin_path = 'plugin/oos/'
    trigger_path = plugin_path + 'triggers/'

    #获取触发器列表
    def get_trigger_list(self):
        trigger_list = []
        for name in os.listdir(self.trigger_path):
            info_file = self.trigger_path + name + '/info.json'
            if not os.path.exists(info_file): continue
            info = json.loads(public.readFile(info_file))
            trigger_list.append(info)

        trigger_list = sorted(trigger_list,key=lambda x: x['sort'])
        return trigger_list

    #获取指定触发器
    def get_trigger_find(self,name):
        info_file = self.trigger_path + name + '/info.json' 
        script_file = self.trigger_path + name + '/script.py' 
        if not os.path.exists(info_file) or not os.path.exists(script_file):
            return False
        info = json.loads(public.readFile(info_file))
        info['script'] = public.readFile(script_file)
        return info
    
    #删除指定触发器
    def remove_trigger(self,name):
        _path = self.trigger_path + name
        if os.path.exists(_path):
            public.ExecShell("rm -rf {}".format(_path))
        
        return True

    #添加触发器
    def add_trigger(self,info,script):
        _path = self.trigger_path + info['name']
        if not os.path.exists(_path):
            os.makedirs(_path,384)
        public.writeFile(_path + '/info.json',json.dumps(info))
        public.writeFile(_path + '/script.py',script)
        return True

    #修改改定触发器
    def modify_trigger(self,info,script):
        _path = self.trigger_path + info['name']
        if not os.path.exists(_path):
            return False

        public.writeFile(_path + '/info.json',json.dumps(info))
        public.writeFile(_path + '/script.py',script)
        return True
    
        
