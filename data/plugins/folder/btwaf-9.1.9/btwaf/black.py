# coding: utf-8
import sys
sys.path.append('/www/server/panel/class')

import os,public,json

class black:
    __path = '/www/server/btwaf/'

    def __get_rule(self, ruleName):
        path = self.__path + 'rule/' + ruleName + '.json';
        rules = public.readFile(path)
        if not rules: return False
        return json.loads(rules)


    def long2ip(self, long):
        floor_list = []
        yushu = long
        for i in reversed(range(4)):  # 3,2,1,0
            res = divmod(yushu, 256 ** i)
            floor_list.append(str(res[0]))
            yushu = res[1]
        return '.'.join(floor_list)

    def __write_rule(self, ruleName, rule):
        path = self.__path + 'rule/' + ruleName + '.json';
        public.writeFile(path, json.dumps(rule))
        public.serviceReload()


    def bt_ip_filter(self,datas):
        #检查状态
        status=public.ExecShell("/etc/init.d/bt_ipfilter status")
        if 'service not running' in status[0]:
            public.ExecShell("/etc/init.d/bt_ipfilter restart")
        path="/dev/shm/.bt_ip_filter"
        if os.path.exists(path):
            data=public.ReadFile(path)
            data+="\n"+datas
            public.WriteFile(path,data)
        else:
            public.WriteFile(path, datas)

    def get_cn_list(self, type):
        if type == 'ip_white' or type == 'ip_black' or type == 'cn':
            try:
                rule = self.__get_rule(type)
                for i in rule:
                    for i2 in range(len(i)):
                        i[i2] = self.long2ip(i[i2])
                return rule
            except:
                self.__write_rule(type, [])
                os.system('/etc/init.d/nginx restart')
                return []
        else:
            rule = self.__get_rule(type)
            for i in rule:
                for i2 in range(len(i)):
                    i[i2] = self.long2ip(i[i2])
            return rule
datas=black()
for i in datas.get_cn_list('ip_black'):
    datas.bt_ip_filter("+,%s-%s,86400" % (i[0], i[1]))