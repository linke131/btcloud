#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhwen <zhw@bt.cn>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   堡塔站点优化
# +--------------------------------------------------------------------

import public,os,json,re,sys

class site_optimization_main:
    plugin_path = '/www/server/panel/plugin/site_optimization'
    check_script_path = plugin_path + '/check_site_type_script/'
    opt_script_path = plugin_path + '/opt_site_script/'
    opt_conf_file = plugin_path + '/opt_scripts.json'
    confile = plugin_path + '/config.json'
    opt_records_file = opt_script_path+ '/tmp.json'


    # 获取所有站点信息
    def get_all_site_info(self,get):
        site_infos = public.M('sites').field('name,path').select()
        for s in site_infos:
            info = self._get_opt_info(s['name'])
            if info:
                s['opt'] = 1
                s['script'] = info['script']
            else:
                s['opt'] = 0
                s['script'] = ""
        return site_infos

    def _get_all_check_script_result(self,script_list,script_path,site_path):
        sys.path.append(self.check_script_path)
        site_infos = []
        for s in script_list:
            if s[-2:] != "py":
                continue
            m = s[:-3]
            result = eval("__import__('{module}').check('{path}')".format(module=m,path=site_path))
            if result:
                site_infos.append(result)
        return site_infos

    def _merge_result(self,site_infos):
        data = {}
        for site_info in site_infos:
            if not data:
                data[site_info['type']] = {site_info['version']: 1}
                continue
            if site_info['type'] in data.keys():
                if site_info['version'] not in data[site_info['type']]:
                    data[site_info['type']][site_info['version']] = 1
                    continue
                for v in data[site_info['type']].keys():
                    if site_info['version'] == v:
                        data[site_info['type']][v] += 1
                        break
            else:
                data[site_info['type']] = {site_info['version']: 1}
        return data

    def _take_max(self,data):
        if len(data) == 1 and len(data.values()) == 1:
            return {"type":list(data.keys())[0],"version":list(data[list(data.keys())[0]].keys())[0],"opt":0}
        else:
            tmp = {}
            for i in data:
                for x in data[i]:
                    if not tmp or i not in tmp:
                        tmp[i] = {x: data[i][x]}
                        continue
                    if tmp[i].values()[0] < data[i][x]:
                        tmp[i] = {x: data[i][x]}
            tmp1 = {}
            for i in tmp:
                if not tmp1:
                    tmp1[i] = tmp[i]
                    continue
                # 获取字典自己的第一个key带入自己查询并发挥value
                if tmp[i][list(tmp[i].keys())[0]] > tmp1[list(tmp1.keys())[0]][list(tmp1[list(tmp1.keys())[0]].keys())[0]]:
                    del (tmp1[tmp1.keys()[0]])
                    tmp1[i] = tmp[i]
        return {"type":list(tmp1.keys())[0],"version":list(tmp1[list(tmp1.keys())[0]].keys())[0],"opt":0}

    def _get_site_run_dir(self,sitename):
        filename = "/www/server/panel/vhost/nginx/{}.conf".format(sitename)
        conf = public.readFile(filename)
        if not conf:
            return False
        run_dir = re.search('root\s*(.*);',conf)
        if not run_dir:
            return False
        return run_dir.groups(1)[0]

    def _read_conf(self,filename):
        conf = public.readFile(filename)
        if not conf:
            conf = {}
        else:
            conf = json.loads(conf)
        return conf

    # 检查站点类型
    def check_site_type(self,get):
        """
        sitepath
        sitename
        path
        """
        sitename = get.sitename
        site_path = get.sitepath
        # 获取站点运行目录
        run_dir = self._get_site_run_dir(sitename)
        if run_dir:
            site_path = run_dir
        # 从脚本目录获取检查脚本
        script_list = os.listdir(self.check_script_path)
        # 检查本地脚本，如果没有，尝试从云端获取
        # 获取所有脚本返回值
        site_infos = self._get_all_check_script_result(script_list,self.check_script_path,site_path)
        # return site_infos
        if not site_infos:
            return public.returnMsg(False,"没找到匹配的站点,请等待脚本更新或到论坛提交优化需求")
        # 将返回值合并处理
        data = self._merge_result(site_infos)
        # 计算最匹配的站点类型和版本
        result = self._take_max(data)
        conf = self._read_conf(self.confile)
        if sitename not in conf:
            conf = {sitename: result}
        public.writeFile(self.confile,json.dumps(conf))
        return result

    # 导入数据
    def import_data(self,get):
        import files
        f = files.files()
        get.f_path = "/tmp"
        result = f.upload(get)
        return result

    # 上传脚本
    def upload_script(self,get):
        """script_type:check/opt
        tips:script description
        f_name:"aaa.py"
        site_type:"微擎"
        """
        tips = get.tips
        f_name = get.f_name
        site_type = ''
        if hasattr(get,'site_type'):
            site_type = get.site_type
        script_type = ''
        if hasattr(get,'script_type'):
            script_type = get.script_type
        conf = self._read_conf(self.opt_conf_file)
        upload_file = "/tmp/" + f_name
        if not os.path.exists(upload_file):
            return public.returnMsg(False, "没找到上传文件，请尝试重新上传")
        if script_type == "check":
            public.ExecShell("mv {} {}".format(upload_file,self.check_script_path))
        else:
            public.ExecShell("mv {} {}".format(upload_file, self.opt_script_path))
        data = {"type":site_type,"tips":tips,"script":f_name}
        conf[script_type].append(data)
        public.writeFile(self.opt_conf_file,json.dumps(conf))
        return public.returnMsg(True,"上传成功")

    # 获取脚本列表
    def get_script_list(self,get):
        conf = self._read_conf(self.opt_conf_file)
        if get.stype == "check":
            return conf["check"]
        else:
            return conf["opt"]

    # 从云端更新脚本按钮
    def get_cloud_script(self,get):
        # 获取云端脚本
        cloud_file= 'http://download.bt.cn/install/plugin/site_optimization/opt_scripts.json'
        cloud_json = public.httpGet(cloud_file,timeout=10)
        try:
            cloud_json = json.loads(cloud_json)
        except:
            cloud_json = {}
        local_json = self._read_conf(self.opt_conf_file)
        if not local_json:
            local_json = cloud_json

        # 检查是否有更新
        n=0
        scripturl = "http://download.bt.cn/install/plugin/site_optimization/{}/{}"
        for c in cloud_json:
            for i in cloud_json[c]:
                if i not in local_json[c]:
                    dir = "check_site_type_script"
                    if c == "opt":
                        dir = "opt_site_script"
                    script_content = public.httpGet(scripturl.format(dir,i['script']))
                    public.writeFile(self.plugin_path+"/{}/{}".format(dir,i['script']),script_content)
                    local_json[c].append(i)
                    n+=1
        public.writeFile(self.opt_conf_file,json.dumps(local_json))
        return public.returnMsg(True,"已经更新 {} 个脚本".format(n))

    # 获取优化脚本列表
    def get_optimization_script_list(self,get):
        """
        sitetype:{"type":"微擎","version":"v2.0"}
        :param get:
        :return:
        """
        sitetype = json.loads(get.sitetype)
        # 从脚本目录获取检查脚本
        conf = json.loads(public.readFile(self.opt_conf_file))
        tmp = []
        for i in conf['opt']:
            if i['type'] == sitetype['type']:
                tmp.append(i)
        return tmp

    # 检查可优化项目
    def check_site_opt(self,get):
        """
        sitepath
        script
        sitename
        :param get:
        :return:
        """
        sys.path.append(self.opt_script_path)
        sitename = get.sitename
        script = get.script
        run_dir = self._get_site_run_dir(sitename)
        if run_dir:
            get.sitepath = run_dir
        m = script[:-3]
        result = eval("__import__('{}').OPTCheck().main(get)".format(m))
        conf = self._read_conf(self.confile)
        try:
            conf[sitename]["script"] = script
            conf[sitename]['sitepath'] = get.sitepath
        except:
            return public.returnMsg(False,"请先检查站点类型")
        public.writeFile(self.confile,json.dumps(conf))
        return result

    def _get_opt_info(self,sitename):
        conf = self._read_conf(self.confile)
        if sitename in conf and str(conf[sitename]['opt']) == "1":
            return {"script":conf[sitename]['script']}
        return False

    # 优化站点
    def opt_site(self,get):
        scrpit_name = get.script
        sitename = get.sitename
        conf = self._read_conf(self.confile)
        conf_sitepath = conf[sitename]['sitepath']
        if get.sitepath != conf_sitepath:
            get.sitepath = conf_sitepath
        sys.path.append(self.opt_script_path)
        try:
            opt_act = json.loads(get.opt_act)
        except:
            return public.returnMsg(False,"参数错误")
        m = scrpit_name[:-3]
        er = ""
        pass_opt = ['php_version','db_index']
        opt_fun = self._read_conf(self.opt_records_file)
        opt_fun[sitename] = []
        for i in opt_act:
            if str(i['opt']) != '0' and i['fun'] not in pass_opt:
                continue
            try:
                result = eval("__import__('{}').OPTStart('{}').{}(get)".format(m,sitename,i['fun']))
                if not result['status']:
                    return result
                opt_fun[sitename].append(i['fun'])
            except Exception as e:
                er=public.get_error_info()
                # public.WriteLog('站点优化', ' 优化项目【{}】失败，详情请查看 /tmp/opt.log'.format(i['fun']))
        # 写入优化配置
        conf[sitename]['opt'] = 1
        public.writeFile(self.confile,json.dumps(conf))
        # 写入优化项目用与取消优化
        public.writeFile(self.opt_records_file,json.dumps(opt_fun))
        public.WriteLog('站点优化', ' 优化站点【{}】成功'.format(get.sitename))
        return public.returnMsg(True,"优化成功")

    # 取消优化
    def cancel_opt(self,get):
        """sitename"""
        sys.path.append(self.opt_script_path)
        tmp = self._read_conf(self.confile)
        if not tmp:
            return public.returnMsg(False,"没有已经优化的站点")
        opt_fun = self._read_conf(self.opt_records_file)
        if not opt_fun:
            return public.returnMsg(False, "没有检查到有已经优化的项目")
        opt_fun = opt_fun[get.sitename]
        conf = tmp[get.sitename]
        m = conf['script'][:-3]
        get.sitepath = conf['sitepath']
        get.opt_fun = opt_fun
        result = eval("__import__('{}').OPTCancel().opt_cancel(get)".format(m))
        del(tmp[get.sitename])
        public.writeFile(self.confile,json.dumps(tmp))
        public.WriteLog('站点优化', ' 取消优化站点【{}】成功'.format(get.sitename))

        return result

    # 获取优化日志
    def get_logs(self,get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', ('站点优化',)).count()
        limit = 12
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
        data['data'] = public.M('logs').where('type=?', ('站点优化',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data