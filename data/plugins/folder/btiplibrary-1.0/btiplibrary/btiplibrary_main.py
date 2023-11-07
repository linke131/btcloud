# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   IP精准数据包 测试版
# +--------------------------------------------------------------------
import os, sys

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")

import public

class btiplibrary_main:

	access_defs = ["get_request_address"]

	def get_request_address(self):
		return public.returnMsg(True, "https://www.bt.cn/api/panel/get_ip_info")