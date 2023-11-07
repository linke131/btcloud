# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzz <wzz@bt.cn>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# | 堡塔Docker模型引导程序
# +--------------------------------------------------------------------
import sys, os

os.chdir("/www/server/panel")
sys.path.append("class/")
import config, public


class docker_project_m_main:
    __plugin_path = "/www/server/panel/plugin/docker_project_m/"
    __config = None

    def __init__(self):
        self.configs = config.config()

    def get_config(self, get):
        public.set_module_logs('docker_project_m', 'get_config', 1)
        menu_list = self.configs.get_menu_list(get)
        for list in menu_list:
            if list["id"] == "memuDocker":
                return list
        return {}

    def set_config(self, get):
        public.set_module_logs('docker_project_m', 'set_config', 1)
        return self.configs.set_hide_menu_list(get)
