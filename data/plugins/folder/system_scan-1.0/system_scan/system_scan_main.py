import os, sys
import subprocess
import time

BASE_PATH = "/www/server/panel"
os.chdir(BASE_PATH)
sys.path.insert(0, "class/")
import public, json


class system_scan_main:
    __vul_list = '/www/server/panel/plugin/system_scan/high_risk_vul-9.json'
    __path = '/www/server/panel/data/system_cve'
    __ignore = __path + '/ignore.json'
    __result = __path + '/result.json'
    __repair_count = __path + '/repair_count.json'
    __plugin_path = '/www/server/panel/plugin/system_scan'

    def __init__(self):
        if not os.path.exists(self.__path):
            os.makedirs(self.__path, 384)
        if not os.path.exists(self.__ignore):
            result = []
            public.WriteFile(self.__ignore, json.dumps(result))
        if not os.path.exists(self.__result):
            result = []
            public.WriteFile(self.__result, json.dumps(result))
        self.compare_md5()

    def system_scan(self, get):
        '''
        一键扫描系统
        :param get:
        :return: dict
        '''
        self.compare_md5()
        sys_version = self.get_sys_version()
        sys_product = self.get_sys_product()
        vul_list = self.get_vul_list()
        new_risk_list = []
        new_ignore_list = []
        # error_list = []
        result_dict = {}
        # cp_list = []
        vul_count = 0
        ignore_list = self.get_ignore_list()

        for vul in vul_list:
            vul_count += 1
            for v in vul["affected_list"]:
                if v["manufacturer"] == sys_version:
                    tmp = 1  # 默认命中
                    vul_version = v['affected'].split(
                        "Up to (excluding)\n                                                ")[1]
                    try:
                        for soft in v["softname"]:
                            compare_result = self.version_compare(sys_product[soft], vul_version)
                            if compare_result >= 0:
                                tmp = 0  # 当有一个软件包版本不在漏洞范围内，则不命中
                                break
                        if tmp == 1:
                            # softname_list = [soft+'-'+sys_product[soft] for soft in v["softname"]]
                            # softname_list = [{soft: sys_product[soft]} for soft in v["softname"]]
                            softname_dict = {}
                            for soft in v["softname"]:
                                softname_dict[soft] = sys_product[soft]
                            risk = self.get_score_risk(vul["score"])
                            vul_dict = {key: vul[key] for key in ["cve_id", "vuln_name", "vuln_time", "vuln_solution"]}
                            vul_dict["vuln_risk"] = risk
                            vul_dict["soft_name"] = softname_dict
                            vul_dict["vuln_version"] = vul_version
                            vul_dict["check_time"] = self.get_time()
                            vul_dict["reboot"] = ""
                            if "kernel" in [k for k in v["softname"]]:
                                vul_dict["reboot"] = "该漏洞属于内核漏洞，需要自行升级内核版本，建议升级之前做好快照以及备份\n可联系客服人工处理"
                            if vul["cve_id"] in ignore_list:
                                new_ignore_list.append(vul_dict)
                                break
                            new_risk_list.append(vul_dict)
                            break
                        # cp_list.append(vul["cve_id"]+':    '+str([soft+'-'+sys_product[soft] for soft in v["softname"]])+'  >=  '+vul_version)
                    except Exception as e:
                        # error_list.append(vul["cve_id"]+':    '+str(e))
                        break
            result_dict["vul_count"] = vul_count
        result_dict["risk"] = new_risk_list
        result_dict["ignore"] = new_ignore_list
        # result_dict["reboot"] = self.__need_reboot
        # result_dict["error"] = error_list
        # result_dict["compare"] = cp_list
        public.WriteFile(self.__path+'/system_scan_time', self.get_time())
        try:
            public.WriteFile(self.__result, json.dumps(result_dict))
            return public.returnMsg(True, "扫描完成")
        except:
            return public.returnMsg(False, "扫描失败")

    # 取系统版本
    def get_sys_version(self):
        '''
        获取当前系统版本
        :return: string
        '''
        sys_version = "None"
        if os.path.exists("/etc/redhat-release"):
            result = public.ReadFile("/etc/redhat-release")
            if "CentOS Linux release 7" in result:
                sys_version = "centos_7"
            elif "CentOS Linux release 8" in result or "CentOS Stream release 8" in result:
                sys_version = "centos_8"
        elif os.path.exists("/etc/issue"):
            if "Ubuntu 20.04" in public.ReadFile("/etc/issue"):
                sys_version = "ubuntu_20.04"
            elif "Ubuntu 22.04" in public.ReadFile("/etc/issue"):
                sys_version = "ubuntu_22.04"
            elif "Ubuntu 18.04" in public.ReadFile("/etc/issue"):
                sys_version = "ubuntu_18.04"
        return sys_version

    # 取软件包版本
    def get_sys_product(self):
        """
        :return dict 如果系统不支持则返回str None
        """
        product_version = {}
        sys_version = self.get_sys_version()
        if sys_version == 'None':return public.returnMsg(False,'当前系统暂不支持')
        if "centos" in sys_version:
            result = public.ExecShell('rpm -qa --qf \'%{NAME};%{VERSION}-%{RELEASE}\\n\'')[0].strip().split('\n')
        elif "ubuntu" in sys_version:
            # result1 = subprocess.check_output(['dpkg-query', '-W', '-f=${Package};${Version}\n']).decode('utf-8').strip().split('\n')
            result = public.ExecShell('dpkg-query -W -f=\'${Package};${Version}\n\'')[0].strip().split('\n')
        elif sys_version == "None":
            return None
        else:
            return None
        for pkg in result:
            product_version[pkg.split(";")[0]] = pkg.split(";")[1]
        # product_version["kernel"] = subprocess.check_output(['uname', '-r']).decode('utf-8').strip().replace(".x86_64", "")
        product_version["kernel"] = public.ExecShell('uname -r')[0].strip()
        return product_version

    # 取漏洞信息
    def get_vul_list(self):
        return json.loads(public.ReadFile(self.__vul_list))

    # 按分数评等级
    def get_score_risk(self, score):
        '''
        拿到分数，返回危险等级
        :param score:
        :return: int 若没有符合的分数就报错，需要捕获异常
        '''
        if float(score) >= 9.0:
            risk = '严重'
        elif float(score) >= 7.0:
            risk = '高危'
        elif float(score) >= 6.0:
            risk = '中危'
        return risk

    # 版本比较
    def version_compare(self, ver_a, ver_b):
        '''
        比较版本大小
        :param ver_a: 软件版本
        :param ver_b: 漏洞版本
        :return: int 大于等于返回1或0，小于返回-1
        '''
        if "ubuntu" in self.get_sys_version():
            if ver_b.startswith("1:"):
                ver_b = ver_b[2:]
            # if ver_a.startswith("1:"):
            #     ver_a = ver_a[2:]
            result = public.ExecShell("dpkg --compare-versions "+ver_a+" ge "+ver_b+" && echo true")
            if 'warning' in result[1].strip():return None
            if 'true' in result[0].strip():return 1
            else:return -1
        from vercmp import vercmp
        return vercmp(ver_a, ver_b)
        # return compare_versions(ver_a, ver_b)

    def get_ignore_list(self):
        return json.loads(public.ReadFile(self.__ignore))

    def set_ignore(self, args):
        '''
        设置忽略指定cve，若已在列表里，则删除，不在列表里则添加
        :param args:
        :return: dict {status:true,msg:'设置成功/失败'}
        '''
        cve_list = json.loads(args.cve_list.strip())
        ignore_list = self.get_ignore_list()
        for cl in cve_list:
            if cl in ignore_list:
                ignore_list.remove(cl)
            else:
                ignore_list.append(cl)

        public.WriteFile(self.__ignore, json.dumps(ignore_list))
        # public.WriteFile(self.__result, json.dumps(result_dict))
        return public.returnMsg(True, '{}设置成功!'.format(cve_list))
        # except:
        #     return public.returnMsg(False, '{}设置失败!'.format(cve_list))

    def get_list(self, get):
        '''
        获取上一次扫描结果
        :param get:
        :return: dict
        '''
        d_risk = 0
        h_risk = 0
        m_risk = 0
        vul_list = []
        if not os.path.exists(self.__result):
            tmp_dict = {"vul_count": len(self.get_vul_list()), "risk": [], "ignore": [],
                        "count": {"serious": 0, "high_risk": 0, "moderate_risk": 0}, "msg": "",
                        "repair_count": {"all_count": 0, "today_count": 0}, "all_check_time": "", "ignore_count": 0}
            if os.path.exists("/etc/redhat-release"):
                result = public.ReadFile("/etc/redhat-release")
                if "CentOS Linux release 8" in result:
                    tmp_dict["msg"] = "当前系统【centos_8】官方已停止维护，为了安全起见，建议升级至centos 8 stream\n详情参考教程：https://www.bt.cn/bbs/thread-82931-1-1.html"
            return tmp_dict
        if public.ReadFile(self.__result) == '[]':
            tmp_dict = {"vul_count": len(self.get_vul_list()), "risk": [], "ignore": [],
                        "count": {"serious": 0, "high_risk": 0, "moderate_risk": 0}, "msg": "",
                        "repair_count": {"all_count": 0, "today_count": 0}, "all_check_time": "", "ignore_count": 0}
            if os.path.exists("/etc/redhat-release"):
                result = public.ReadFile("/etc/redhat-release")
                if "CentOS Linux release 8" in result:
                    tmp_dict["msg"] = "当前系统【centos_8】官方已停止维护，为了安全起见，建议升级至centos 8 stream\n详情参考教程：https://www.bt.cn/bbs/thread-82931-1-1.html"
            return tmp_dict
        result_dict = json.loads(public.ReadFile(self.__result))
        old_risk_list = result_dict["risk"]
        old_ignore_list = result_dict["ignore"]
        new_risk_list = old_risk_list.copy()
        new_ignore_list = old_ignore_list.copy()
        tmp_ignore_list = self.get_ignore_list()
        for cve in old_risk_list:
            public.print_log(len(old_risk_list))
            if cve["cve_id"] in tmp_ignore_list:
                new_ignore_list.append(cve)
                new_risk_list.remove(cve)
        for cve_ig in old_ignore_list:
            if cve_ig["cve_id"] not in tmp_ignore_list:
                new_risk_list.append(cve_ig)
                new_ignore_list.remove(cve_ig)
        for vul in new_ignore_list+new_risk_list:
            vul_list.append(vul["cve_id"])
            if vul["cve_id"] in tmp_ignore_list:
                continue
            if vul["vuln_risk"] == "严重":
                d_risk += 1
            elif vul["vuln_risk"] == '高危':
                h_risk += 1
            elif vul["vuln_risk"] == '中危':
                m_risk += 1
        list_sort = ['严重','高危','中危']  # 排序列表
        # result_dict["risk"] = old_risk_list
        result_dict["risk"] = sorted(new_risk_list, key=lambda x: list_sort.index(x.get("vuln_risk")))
        # result_dict["ignore"] = old_ignore_list
        result_dict["ignore"] = sorted(new_ignore_list, key=lambda x: list_sort.index(x.get("vuln_risk")))
        # result_dict["reboot"] = self.__need_reboot
        result_dict["count"] = {"serious":d_risk,"high_risk":h_risk,"moderate_risk":m_risk}
        result_dict["msg"] = ""
        result_dict["repair_count"] = self.count_repair(vul_list)
        result_dict["all_check_time"] = public.ReadFile(self.__path+'/system_scan_time')
        result_dict["ignore_count"] = len(tmp_ignore_list)
        if os.path.exists("/etc/redhat-release"):
            result = public.ReadFile("/etc/redhat-release")
            if "CentOS Linux release 8" in result:
                result_dict["msg"] = "当前系统【centos_8】官方已停止维护，为了安全起见，建议升级至centos 8 stream\n详情参考教程：https://www.bt.cn/bbs/thread-82931-1-1.html"
        public.WriteFile(self.__result, json.dumps(result_dict))
        return result_dict

    def check_cve(self, args):
        '''
        检测单个漏洞
        :param args:
        :return: dict
        '''
        sys_product = self.get_sys_product()
        cve_id = args.cve_id.strip()
        result_dict = json.loads(public.ReadFile(self.__result))
        risk_list = result_dict["risk"]
        ignore_list = result_dict["ignore"]
        tmptmp = 1
        for cve in risk_list:
            if cve["cve_id"] == cve_id:
                tmp = 1  # 默认命中漏洞
                cve["check_time"] = self.get_time()
                for soft in list(cve["soft_name"].keys()):
                    if self.version_compare(sys_product[soft], cve["vuln_version"]) >= 0:
                        tmp = 0  # 当有一个软件包不命中，则为已修复
                        tmptmp = 0
                        break
                if tmp == 0:
                    risk_list.remove(cve)
        for cve in ignore_list:
            if cve["cve_id"] == cve_id:
                tmp = 1  # 默认命中漏洞
                cve["check_time"] = self.get_time()
                for soft in list(cve["soft_name"].keys()):
                    if self.version_compare(sys_product[soft], cve["vuln_version"]) >= 0:
                        tmp = 0  # 当有一个软件包不命中，则为已修复
                        tmptmp = 0
                        break
                if tmp == 0:
                    ignore_list.remove(cve)
        result_dict["risk"] = risk_list
        result_dict["ignore"] = ignore_list
        public.WriteFile(self.__result, json.dumps(result_dict))
        if tmptmp == 0:
            return public.returnMsg(True, cve_id+'已修复')
        else:
            return public.returnMsg(True, cve_id+'未修复')

    def repair_cve(self,args):
        '''
        修复单个漏洞
        :param args:
        :return: dict
        '''
        cve_id = args.cve_id.strip()
        result_dict = json.loads(public.ReadFile(self.__result))
        result_list = result_dict["risk"] + result_dict["ignore"]
        for cve in result_list:
            if cve["cve_id"] == cve_id:
                for soft in list(cve["soft_name"].keys()):
                    result = self.upgrade_soft(soft)
                    if result == 2:
                        return public.returnMsg(False, '修复失败，软件包{}更新失败，请更新下载源或自行比对版本信息是否存在误判'.format(soft))
        self.check_cve(args)
        return public.returnMsg(True, cve_id+'修复成功')

    def repare_all_cve(self, get):
        '''
        批量修复未忽略漏洞
        :param get:
        :return: dict
        '''
        result_list = json.loads(public.ReadFile(self.__result))["risk"]
        error_list = []
        already_repair = []
        tmp_list = []
        public.ExecShell('yum')
        for cve in result_list:
            for soft in list(cve["soft_name"].keys()):
                if soft == 'kernel':
                    continue
                if soft in already_repair:
                    continue
                result = self.upgrade_soft(soft)
                if result == 2:
                    error_list.append(soft)
                already_repair.append(soft)
            tmp_list.append(cve["soft_name"])
        self.system_scan(get)
        if error_list:
            return {"status": True, "msg": tmp_list}
        return {"status": True, "msg": []}

    def upgrade_soft(self, soft):
        '''
        升级软件包
        :param soft: 软件包名
        :return: int 2为升级失败，1为成功
        '''
        error_message = ['Couldn\'t find', 'Error', 'Nothing to do', 'already the newest']
        sys_version = self.get_sys_version()
        if "centos" in sys_version:
            # public.ExecShell('yum update -y '+soft+' > '+self.__path+'/log.txt 2>&1')
            public.ExecShell('yum update -y {} 2>&1 |tee -a {}/log.txt'.format(soft, self.__path))
            # subprocess.check_output(['yum', 'update', '-y', soft])
        elif "ubuntu" in sys_version:
            # public.ExecShell('apt install -y '+soft+' > '+self.__path+'/log.txt 2>&1')
            public.ExecShell('apt install -y {} 2>&1 |tee -a {}/log.txt'.format(soft, self.__path))
        result = public.ReadFile(self.__path+'/log.txt')
        for error in error_message:
            if error in result:
                return 2
        return 1

    def get_time(self):
        return public.format_date()

    def count_repair(self, now_list):
        '''
        获取总共修复漏洞的数量以及今日修复漏洞数量
        :param now_list:
        :return: dict
        '''
        cve_dict = {}
        if not os.path.exists(self.__repair_count):
            cve_dict["all_cve"] = now_list
            cve_dict["today_cve"] = now_list
            cve_dict["time"] = self.get_time()
            public.WriteFile(self.__repair_count, json.dumps(cve_dict))
        cve_dict = json.loads(public.ReadFile(self.__repair_count))
        cve_dict["all_cve"].extend(set(now_list) - set(cve_dict["all_cve"]))
        all_count = len(cve_dict["all_cve"]) - len(now_list)
        cve_dict["today_cve"].extend(set(now_list)-set(cve_dict["today_cve"]))
        today_count = len(cve_dict["today_cve"]) - len(now_list)
        if cve_dict["time"].split(" ")[0] != self.get_time().split(" ")[0]:
            cve_dict["today_cve"] = now_list
        cve_dict["time"] = self.get_time()
        public.WriteFile(self.__repair_count, json.dumps(cve_dict))
        return {"all_count":all_count,"today_count":today_count}

    def compare_md5(self):
        '''
        对比md5，更新漏洞库
        :return:
        '''
        import requests
        try:
            new_md5 = requests.get("https://www.bt.cn/vulscan_d11ad1fe99a5f078548b0ea355db42dc.txt").text
        except:
            return 0
        old_md5 = public.FileMd5(self.__vul_list)
        if old_md5 != new_md5:
            try:
                public.downloadFile("https://download.bt.cn/install/src/high_risk_vul.zip", "/www/server/panel/plugin/system_scan/high_risk_vul.zip")
                public.ExecShell("unzip -o /www/server/panel/plugin/system_scan/high_risk_vul.zip -d /www/server/panel/plugin/system_scan/")
            except:
                return 0
        return 1

    def get_logs(self, get):
        '''
        获取升级日志
        :param get:
        :return: dict
        '''
        import files
        return public.returnMsg(True, files.files().GetLastLine(self.__path+'/log.txt', 20))


if __name__ == "__main__":
    get = '0'
    sys_scan = system_scan_main()
    print(sys_scan.compare_md5())
