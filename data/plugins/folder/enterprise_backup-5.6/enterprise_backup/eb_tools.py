# coding: utf-8
import os
import sys

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public
from pluginAuth import Plugin

def request_plugin(fun_name, args, kwargs={}, retry=2):
    plugin_name = "enterprise_backup"
    # print("request plugin:", plugin_name)
    plu = Plugin(plugin_name)
    msg = ""
    try:
        result = plu.get_fun(fun_name)(*args, **kwargs)
        if result:
            from collections.abc import Iterable
            if isinstance(result, Iterable) and "status" in result:
                msg = result["msg"]
    except Exception as e:
        msg = str(e)
        result = public.returnMsg(False, msg)
    
    if msg.find("授权验证失败")!=-1:
        if retry>0:
            return request_plugin(fun_name, args, kwargs, retry=retry-1)
        raise RuntimeError(msg)
    return result