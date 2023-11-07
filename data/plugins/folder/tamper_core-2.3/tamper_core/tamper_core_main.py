#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang<hwl@bt.cn>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   宝塔防篡改程序(驱动层) - 重构版
# +--------------------------------------------------------------------


import os,sys,json,time, public, datetime, glob, shutil, copy


class tamper_core_main:

    __plugin_path = public.get_plugin_path('tamper_core')
    __tamper_path = "{}/tamper".format(public.get_setup_path())
    __tamper_user_bin = "{}/tamperuser".format(__tamper_path)
    __tamper_cli_bin = "{}/tamper-cli".format(__tamper_path)
    __tamper_cli_bash = "{}/cli.sh".format(__tamper_path)
    __init_file = "{}/init.sh".format(__plugin_path)
    __config_file = "{}/tamper.conf".format(__tamper_path)
    __config_ps_file = "{}/config_ps.json".format(__tamper_path)
    __tips_file = "{}/tips.pl".format(__tamper_path)
    __logs_path = "{}/logs".format(__tamper_path)
    __total_path = "{}/total".format(__tamper_path)

    def __init__(self):
        spush_file = "{}/plugin/tamper_core/tamper_push.py".format(public.get_panel_path())
        dpush_file = "{}/class/push/tamper_push.py".format(public.get_panel_path())
        if not os.path.exists(dpush_file):
            shutil.copyfile(spush_file, dpush_file)
            os.chmod(dpush_file, mode=0o777)

        
    def rep_config(self):
        '''
            @name 修复配置文件
            @author hwliang
            @return void
        '''

        default_config = {
            "status":1,
            "ltd":1,
            "min_pid":10,
            "is_create":1,
            "is_modify":1,
            "is_unlink":1,
            "is_mkdir":1,
            "is_rmdir":1,
            "is_rename":1,
            "is_chmod":1,
            "is_chown":1,
            "is_link":1,
            "process_names":["mysqld","systemctl"],
            "uids":[],
            "gids":[],
            "default_black_exts":[".java",".php",".html",".tpl",".js",".css",".jsp",".do",".shtml",".htm",".go",".json",".conf"],
            "default_white_files":[],
            "default_white_dirs":["runtime/","cache/","temp/","tmp/","threadcache/","log/","logs/","caches/","tmps/"],
            "paths":[]
        }

        public.writeFile(self.__config_file,json.dumps(default_config,ensure_ascii=False,indent=4))

    def rep_config_ps(self, config):
        '''
            @name 修复配置文件
            @author hwliang
            @return void
        '''
        default_config = {
            "frequent_process" : [
                {"name": "BT-Panel","zh-cn": "宝塔面板进程","ps": "启用此选项后，您可以使用宝塔面板编辑和保存文件"},
                {"name": "pure-ftpd","zh-cn": "FTP服务进程","ps": "启用此选项后，您可以通过FTP技术上传文件更新网站文件和内容"},
                {"name": "sftp-server","zh-cn": "SFTP服务进程","ps": "启用此选项后，您可以通过SFTP技术上传文件更新网站文件和内容"},
                # {"name": "systemctl","ps":"开启后，将允许systemctl命令修改系统服务的配置文件及日志"},
                #{"name": "cp","ps": "开启后，将允许cp命令复制文件到您的保护目录下"},
                #{"name": "vi","ps": "开启后，您可以通过vi命令修改文件(linux系统下的文本编辑器)"},
                #{"name": "vim","ps": "开启后，您可以通过vim命令修改文件(linux系统下的文本编辑器)"},
                #{"name": "mysqld","ps":"如果您的数据库文件在保护目录之内，请确保开启该项从而使数据库服务正常"},
                #{"name": "php-fpm","ps": "如果您的项目依赖PHP运行，您可以开启该项以保证PHP进程管理器正常工作"},
            ],
            "default_dir_ps": {
                "runtime/":{"ps":"ThinkPHP框架下的缓存和日志文件夹","tip_msg":"删除该白名单后，该目录下文件将受到保护，这也可能影响网站的缓存和日志文件正常写入，是否继续操作？"},
                "cache/":{"ps":"用于保存网站程序运行过程中的缓存信息","tip_msg":"删除该白名单后，该目录下文件将受到保护，这也可能影响网站对缓存信息的正常操作，是否继续操作？"},
                "temp/":{"ps":"用于保存网站程序运行过程中产生的临时文件","tip_msg":"删除该白名单后，该目录下文件将受到保护，这也可能影响网站对临时文件的操作，是否继续操作？"},
                "tmp/":{"ps":"通常是保存网站运行过程中的临时文件的文件夹","tip_msg":"删除该白名单后，该目录下文件将受到保护，这也可能影响网站对临时文件的操作，是否继续操作？"},
                "threadcache/":{"ps":"用于保存网站多线程程序运行过程中的缓存信息","tip_msg":"删除该白名单后，该目录下文件将受到保护，这也可能影响网站对缓存信息的正常操作，是否继续操作？"},
                "log/":{"ps":"网站程序运行的日志文件夹","tip_msg":"删除该白名单后，该目录下文件将受到保护，这也可能影响网站日志文件的正常写入，是否继续操作？"},
                "logs/":{"ps":"网站程序运行的日志文件夹","tip_msg":"删除该白名单后，该目录下文件将受到保护，这也可能影响网站日志文件的正常写入，是否继续操作？"},
                "caches/":{"ps":"保存网站程序运行过程中的缓存信息","tip_msg":"删除该白名单后，该目录下文件将受到保护，这也可能影响网站对缓存信息的正常操作，是否继续操作？"},
                "tmps/":{"ps":"用于保存网站程序运行过程中产生的临时文件","tip_msg":"删除该白名单后，该目录下文件将受到保护，这也可能影响网站对临时文件的操作，是否继续操作？"},
            }
        }
        default_frequent_process= ('BT-Panel','systemctl','pure-ftpd','sftp-server','cp','vi','vim','bash','mysqld','php-fpm')
        for i in config["process_names"]:
            if i not in default_frequent_process:
              default_config["frequent_process"].append({"name": i,"ps": i})
        for i in config["paths"]:
            default_config["dir_ps_" + str(i["pid"])] = {}
        
        public.writeFile(self.__config_ps_file, json.dumps(default_config,ensure_ascii=False,indent=4))

    def read_config_ps(self, config_dict):
        if not os.path.exists(self.__config_ps_file):
            self.rep_config_ps(config_dict)

        config_ps = public.readFile(self.__config_ps_file)
        if not config_ps: # 配置文件为空？
            self.rep_config_ps(config_dict)
            config_ps = public.readFile(self.__config_file)

        try:
            config_ps_dict = json.loads(config_ps)
        except:
            # 配置文件损坏？
            self.rep_config_ps()
            config_ps_dict = json.loads(public.readFile(self.__config_file))

        return config_ps_dict

    def read_config(self):
        '''
            @name 获取配置信息
            @author hwliang
            @return dict
        '''
        # 配置文件不存在？
        if not os.path.exists(self.__config_file):
            self.rep_config()

        config = public.readFile(self.__config_file)
        if not config: # 配置文件为空？
            self.rep_config()
            config = public.readFile(self.__config_file)

        try:
            config_dict = json.loads(config)
        except:
            # 配置文件损坏？
            self.rep_config()
            config_dict = json.loads(public.readFile(self.__config_file))
        
        config_dict.update(**self.read_config_ps(config_dict))
        
        return config_dict

    def save_config(self,config):
        '''
            @name 保存配置信息
            @author hwliang
            @param dict config
            @return void
        '''
        config = copy.deepcopy(config)
        config_ps_file = {}
        if "frequent_process" in config:
            config_ps_file["frequent_process"] = config.pop("frequent_process")
        if "default_dir_ps"in config:
            config_ps_file["default_dir_ps"] = config.pop("default_dir_ps")
        for i in config["paths"]:
            name = "dir_ps_" + str(i["pid"])
            if name in config:
                config_ps_file[name] = config.pop(name)
        public.writeFile(self.__config_file,json.dumps(config,ensure_ascii=False,indent=4))
        public.writeFile(self.__config_ps_file,json.dumps(config_ps_file,ensure_ascii=False,indent=4))
        public.writeFile(self.__tips_file,'1')

    def get_tamper_paths(self,args = None):
        '''
            @name 获取受保护的目录列表
            @author hwliang
            @return list
        '''
        config = self.read_config()
        if not config.get("paths"):
            return []

        result = []
        for path_info in config["paths"]:
            path_info['total'] = self.get_path_total(path_id=path_info['pid'])
            result.append(path_info)
        for i in config["paths"]:
            dir_ps = "dir_ps_" + str(i["pid"])
            for j in range(len(i["white_dirs"])):
                if i["white_dirs"][j] in config[dir_ps]:
                    i["white_dirs"][j] = {
                        "dir": i["white_dirs"][j],
                        "ps": config[dir_ps][i["white_dirs"][j]],
                    }
                elif i["white_dirs"][j] in config["default_dir_ps"]:
                    i["white_dirs"][j] = {
                        "dir": i["white_dirs"][j],
                        "ps": config["default_dir_ps"][i["white_dirs"][j]].get("ps"),
                        "tip_msg": config["default_dir_ps"][i["white_dirs"][j]].get("tip_msg", None)
                    }
                else:
                    i["white_dirs"][j] = {
                        "dir": i["white_dirs"][j]
                    }

        return config["paths"]


    def get_tamper_global_config(self,args = None):
        '''
            @name 获取全局配置
            @author hwliang
            @return dict
        '''
        config = self.read_config()
        return config


    def get_tamper_path_find(self,args=None,path_id=None,path=None):
        '''
            @name 获取指定目录配置
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path_id<int> 目录ID [选填]
            @param path<string> 目录路径 [选填]
            @return dict or None
        '''
        if args: # 参数传递
            if 'path_id' in args:
                path_id = int(args.get("path_id"))
            if 'path' in args:
                path = args.get("path")

        # 参数错误
        if not path_id and not path:
            return None

        # 获取目录配置列表
        path_list = self.get_tamper_paths()

        # 查找目录配置
        for path_info in path_list:
            if path_id and path_info["pid"] == path_id:
                return path_info
            if path and path_info["path"] == path:
                return path_info

        # 没找到？
        return None


    def get_path_id(self,path_list):
        '''
            @name 获取目标ID
            @author hwliang
            @param path_list<list> 目录列表
            @return int
        '''
        if not path_list:
            return 1

        # 获取最大ID
        max_id = 0
        for path_info in path_list:
            if max_id < path_info["pid"]:
                max_id = path_info["pid"]

        # 返回ID
        return max_id + 1


    def create_path_config(self,args=None,path=None,ps=None):
        '''
            @name 创建目录配置
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path<string> 目录路径
            @param ps<dict_obj> 备注
            @return dict
        '''
        if args: # 参数传递
            if 'path' in args:
                path = args.get("path")
            if 'ps' in args:
                ps = args.get("ps")

        # 路径标准化处理
        if path[-1] != "/": path += "/"
        path = path.replace('//','/')

        # 参数过滤
        if not path: return public.returnMsg(False,"目录路径不能为空")
        if not os.path.exists(path) or os.path.isfile(path): return public.returnMsg(False,"无效的目录: {}".format(path))
        if self.get_tamper_path_find(path=path): return public.returnMsg(False,"指定目录已经添加过了: {}".format(path))

        # 关键路径过滤
        if path in ['/','/root/','/boot/','/www/','/www/server/','/www/server/panel/','/www/server/panel/class/','/usr/','/etc/','/usr/bin/','/usr/sbin/']:
            return public.returnMsg(False,"不能添加系统关键目录: {}".format(path))

        config = self.read_config()
        path_info = {
            "pid":self.get_path_id(config["paths"]),
            "path":path,
            "status":1,
            "mode":0,
            "is_create":1,
            "is_modify":1,
            "is_unlink":1,
            "is_mkdir":1,
            "is_rmdir":1,
            "is_rename":1,
            "is_chmod":1,
            "is_chown":1,
            "is_link":1,
            "black_exts": config["default_black_exts"],
            "white_files": config["default_white_files"],
            "white_dirs": config["default_white_dirs"],
            "ps":ps
        }

        # 添加到配置列表
        config["paths"].append(path_info)
        config["dir_ps_" + str(path_info["pid"])] = {}
        self.save_config(config)
        public.WriteLog("防篡改","添加目录配置: {}".format(path))
        return public.returnMsg(True,"添加成功")

    def modify_path_config(self,args=None,path_id=None,path=None,key=None,value=None):
        '''
            @name 修改目录配置
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path_id<int> 目录ID
            @param path<string> 目录路径
            @param key<string> 配置项
            @param value<string> 配置值
            @return dict
        '''

        if args:
            if 'path_id' in args:
                path_id = int(args.get("path_id"))
            if 'path' in args:
                path = args.get("path")
            if 'key' in args:
                key = args.get("key")
            if 'value' in args:
                value = args.get("value")
                if not key in ['ps']: value = int(value)
        if not path_id and not path: return public.returnMsg(False,"参数错误")
        if not key: return public.returnMsg(False,"参数错误")
        keys = ["status","mode","is_create","is_modify","is_unlink","is_mkdir","is_rmdir","is_rename","is_chmod","is_chown","is_link","ps"]
        if key not in keys: return public.returnMsg(False,"指定配置项不存在")
        if not self.get_tamper_path_find(path_id=path_id,path=path): return public.returnMsg(False,"指定目标配置不存在")

        # 获取目录配置
        config = self.read_config()
        for path_info in config["paths"]:
            if path_id and path_info["pid"] == path_id:
                path = path_info["path"]
                path_info[key] = value
                break
            if path and path_info["path"] == path:
                path_info[key] = value
                break
        self.save_config(config)

        key_status = {
            "is_modify":"修改",
            "is_unlink":"删除文件",
            "is_rename":"重命名",
            "is_create":"创建文件",
            "is_mkdir":"创建目录",
            "is_chmod":"修改权限",
            "is_chown":"修改所有者",
            "is_rmdir":"删除目录",
            "is_link":"创建软链接",
        }
        value_status = ["允许","禁止"]
        open_status = ['关闭','开启']
        if key in ['status','ps']:
            if key == 'status':
                public.WriteLog("防篡改","修改目录[{}]配置: [{}]防篡改".format(path,open_status[value]))
            else:
                public.WriteLog("防篡改","修改目录[{}]配置: 备注={}".format(path,value))
        else:
            public.WriteLog("防篡改","修改目录[{}]配置:[{}]{}".format(path,value_status[value],key_status[key]))
        return public.returnMsg(True,"修改成功")

    def remove_path_config(self,args=None,path_id=None,path=None):
        '''
            @name 删除目录配置
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path_id<int> 目录ID
            @param path<string> 目录路径
            @return dict
        '''
        if args:
            if 'path_id' in args:
                path_id = int(args.get("path_id"))
            if 'path' in args:
                path = args.get("path")
        if not path_id and not path: return public.returnMsg(False,"参数错误")
        if not self.get_tamper_path_find(path_id=path_id,path=path): return public.returnMsg(False,"指定目标配置不存在")

        # 获取目录配置
        config = self.read_config()
        for path_info in config["paths"]:
            if path_id and path_info["pid"] == path_id:
                path = path_info["path"]
                config["paths"].remove(path_info)
                break
            if path and path_info["path"] == path:
                path_id = path_info["pid"]
                config["paths"].remove(path_info)
                break
        self.save_config(config)
        # 清理日志和统计文件
        log_file = "{}/{}.log".format(self.__logs_path,path_id)
        if os.path.exists(log_file): os.remove(log_file)
        total_path = "{}/{}".format(self.__total_path,path_id)
        if os.path.exists(total_path): public.ExecShell("rm -rf {}".format(total_path))

        push_conf =  "{}/class/push/push.json".format(public.get_panel_path())
        if os.path.exists(push_conf):
            data = json.loads(public.readFile(push_conf))
            if "tamper_push" in data:
                if str(path_id) in data["tamper_push"] : del data["tamper_push"][str(path_id)]
                if path_id in data["tamper_push"]: del data["tamper_push"][path_id]
                public.writeFile(push_conf,json.dumps(data))

        public.WriteLog("防篡改","删除目录配置: {}".format(path))
        return public.returnMsg(True,"删除成功")


    def add_black_exts(self,args=None,path_id=None,path=None,exts=None):
        '''
            @name 添加黑名单扩展名
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path_id<int> 目录ID
            @param path<string> 目录路径
            @param exts<string> 扩展名
            @return dict
        '''
        if args:
            if 'path_id' in args:
                path_id = int(args.get("path_id"))
            if 'path' in args:
                path = args.get("path")
            if 'exts' in args:
                exts = args.get("exts")
        if not path_id and not path: return public.returnMsg(False,"参数错误")
        if not exts: return public.returnMsg(False,"保护内容不能是空白")
        if not self.get_tamper_path_find(path_id=path_id,path=path): return public.returnMsg(False,"指定目标配置不存在")

        # 获取目录配置
        config = self.read_config()
        for path_info in config["paths"]:
            if path_id and path_info["pid"] == path_id:
                if exts in path_info["black_exts"]: return public.returnMsg(False,"指定后缀名已存在")
                path_info["black_exts"].append(exts)
                path = path_info["path"]
                break
            if path and path_info["path"] == path:
                if exts in path_info["black_exts"]: return public.returnMsg(False,"指定后缀名已存在")
                path_info["black_exts"].append(exts)
                break

        self.save_config(config)
        public.WriteLog("防篡改","添加指定目录:{},的受保护的后缀名: {}".format(path,exts))
        return public.returnMsg(True,"添加成功")


    def remove_black_exts(self,args=None,path_id=None,path=None,exts=None):
        '''
            @name 删除黑名单扩展名
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path_id<int> 目录ID
            @param path<string> 目录路径
            @param exts<string> 扩展名
            @return dict
        '''
        if args:
            if 'path_id' in args:
                path_id = int(args.get("path_id"))
            if 'path' in args:
                path = args.get("path")
            if 'exts' in args:
                exts = args.get("exts")
        if not path_id and not path: return public.returnMsg(False,"参数错误")
        if not exts: return public.returnMsg(False,"排除的内容不能是空白")
        if not self.get_tamper_path_find(path_id=path_id,path=path): return public.returnMsg(False,"指定目标配置不存在")


        # 获取目录配置
        config = self.read_config()
        for path_info in config["paths"]:
            if path_id and path_info["pid"] == path_id:
                if exts not in path_info["black_exts"]: return public.returnMsg(False,"指定后缀名不存在")
                path_info["black_exts"].remove(exts)
                path = path_info["path"]
                break
            if path and path_info["path"] == path:
                if exts not in path_info["black_exts"]: return public.returnMsg(False,"指定后缀名不存在")
                path_info["black_exts"].remove(exts)
                break

        self.save_config(config)
        public.WriteLog("防篡改","删除目录配置：{},的受保护的后缀名: {}".format(path,exts))
        return public.returnMsg(True,"删除成功")


    def add_white_files(self,args=None,path_id=None,path=None,filename=None):
        '''
            @name 添加文件白名单
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path_id<int> 目录ID
            @param path<string> 目录路径
            @param filename<string> 文件名
            @return dict
        '''

        if args:
            if 'path_id' in args:
                path_id = int(args.get("path_id"))
            if 'path' in args:
                path = args.get("path")
            if 'filename' in args:
                filename = args.get("filename")
        if not path_id and not path: return public.returnMsg(False,"参数错误")
        if not filename: return public.returnMsg(False,"添加白名单的内容不能是空白")
        if not self.get_tamper_path_find(path_id=path_id,path=path): return public.returnMsg(False,"指定目标配置不存在")

        # 获取目录配置
        config = self.read_config()
        for path_info in config["paths"]:
            if path_id and path_info["pid"] == path_id:
                if filename in path_info["white_files"]: return public.returnMsg(False,"指定文件已经添加过了")
                path_info["white_files"].append(filename)
                path = path_info["path"]
                break
            if path and path_info["path"] == path:
                if filename in path_info["white_files"]: return public.returnMsg(False,"指定文件已经添加过了")
                path_info["white_files"].append(filename)
                break

        self.save_config(config)
        public.WriteLog("防篡改","添加指定目录:{},的文件白名单: {}".format(path,filename))
        return public.returnMsg(True,"添加成功")


    def remove_white_files(self,args=None,path_id=None,path=None,filename=None):
        '''
            @name 删除文件白名单
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path_id<int> 目录ID
            @param path<string> 目录路径
            @param filename<string> 文件名
            @return dict
        '''
        if args:
            if 'path_id' in args:
                path_id = int(args.get("path_id"))
            if 'path' in args:
                path = args.get("path")
            if 'filename' in args:
                filename = args.get("filename")
        if not path_id and not path: return public.returnMsg(False,"参数错误")
        if not filename: return public.returnMsg(False,"移除白名单的内容不能是空白")
        if not self.get_tamper_path_find(path_id=path_id,path=path): return public.returnMsg(False,"指定目标配置不存在")

        # 获取目录配置
        config = self.read_config()
        for path_info in config["paths"]:
            if path_id and path_info["pid"] == path_id:
                if filename not in path_info["white_files"]: return public.returnMsg(False,"指定文件不存在")
                path_info["white_files"].remove(filename)
                path = path_info["path"]
                break
            if path and path_info["path"] == path:
                if filename not in path_info["white_files"]: return public.returnMsg(False,"指定文件不存在")
                path_info["white_files"].remove(filename)
                break

        self.save_config(config)
        public.WriteLog("防篡改","删除指定目录:{},的文件白名单: {}".format(path,filename))
        return public.returnMsg(True,"删除成功")


    def add_white_dirs(self,args=None,path_id=None,path=None,dirname=None):
        '''
            @name 添加目录白名单
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path_id<int> 目录ID
            @param path<string> 目录路径
            @param dirname<string> 目录名
            @return dict
        '''
        if args:
            if 'path_id' in args:
                path_id = int(args.get("path_id"))
            if 'path' in args:
                path = args.get("path")
            if 'dirname' in args:
                dirname = args.get("dirname")
        if not path_id and not path: return public.returnMsg(False,"参数错误")
        if not dirname: return public.returnMsg(False,"添加白名单的内容不能是空白")
        if not self.get_tamper_path_find(path_id=path_id,path=path): return public.returnMsg(False,"指定目标配置不存在")

        # 获取目录配置
        config = self.read_config()
        for path_info in config["paths"]:
            if path_id and path_info["pid"] == path_id:
                if dirname in path_info["white_dirs"]: return public.returnMsg(False,"指定目录已经添加过了")
                path_info["white_dirs"].append(dirname)
                path = path_info["path"]
                break
            if path and path_info["path"] == path:
                if dirname in path_info["white_dirs"]: return public.returnMsg(False,"指定目录已经添加过了")
                path_info["white_dirs"].append(dirname)
                break

        self.save_config(config)
        public.WriteLog("防篡改","添加指定目录:{},的目录白名单: {}".format(path,dirname))
        return public.returnMsg(True,"添加成功")

    def remove_white_dirs(self,args=None,path_id=None,path=None,dirname=None):
        '''
            @name 删除目录白名单
            @author hwliang
            @param args<dict_obj> 外部参数，可以为空
            @param path_id<int> 目录ID
            @param path<string> 目录路径
            @param dirname<string> 目录名
            @return dict
        '''
        if args:
            if 'path_id' in args:
                path_id = int(args.get("path_id"))
            if 'path' in args:
                path = args.get("path")
            if 'dirname' in args:
                dirname = args.get("dirname")
        if not path_id and not path: return public.returnMsg(False,"参数错误")
        if not dirname: return public.returnMsg(False,"移除白名单的内容不能是空白")
        if not self.get_tamper_path_find(path_id=path_id,path=path): return public.returnMsg(False,"指定目标配置不存在")

        # 获取目录配置
        config = self.read_config()
        for path_info in config["paths"]:
            if path_id and path_info["pid"] == path_id:
                if dirname not in path_info["white_dirs"]: return public.returnMsg(False,"指定目录不存在")
                path_info["white_dirs"].remove(dirname)
                if dirname in config["dir_ps_" + str(path_info["pid"])]: config["dir_ps_" + str(path_info["pid"])].pop(dirname)
                path = path_info["path"]
                break
            if path and path_info["path"] == path:
                if dirname not in path_info["white_dirs"]: return public.returnMsg(False,"指定目录不存在")
                path_info["white_dirs"].remove(dirname)
                if dirname in config["dir_ps_" + str(path_info["pid"])]: config["dir_ps_" + str(path_info["pid"])].pop(dirname)
                break

        self.save_config(config)
        public.WriteLog("防篡改","删除指定目录:{},的目录白名单: {}".format(path,dirname))
        return public.returnMsg(True,"删除成功")


    def modify_global_config(self,args=None,key=None,value=None):
        '''
            @name 修改全局配置
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @param key<string> 全局配置键名
            @param value<string> 全局配置键值
            @return dict
        '''
        if args:
            if 'key' in args: key = args.get("key")
            if 'value' in args: value = int(args.get("value"))

        if not key: return public.returnMsg(False,"参数错误")
        if key in ['process_names','uids','gids','paths']: return public.returnMsg(False,'不允许修改的配置项')
        config = self.read_config()

        if key not in config: return public.returnMsg(False,"指定全局配置不存在")
        config[key] = value
        self.save_config(config)

        key_status = {
            "is_modify":"修改",
            "is_unlink":"删除文件",
            "is_rename":"重命名",
            "is_create":"创建文件",
            "is_mkdir":"创建目录",
            "is_chmod":"修改权限",
            "is_chown":"修改所有者",
            "is_rmdir":"删除目录",
            "is_link":"创建软链接",
        }
        value_status = ["允许","禁止"]
        open_status = ['关闭','开启']
        if key in ['status','min_pid']:
            if key == 'status':
                public.WriteLog("防篡改","修改全局配置: [{}]防篡改".format(open_status[value]))
            else:
                public.WriteLog("防篡改","修改全局配置: 最小受保护PID={}".format(value))
        else:
            public.WriteLog("防篡改","修改全局配置:[{}]{}".format(value_status[value],key_status[key]))
        return public.returnMsg(True,"修改成功")

    def add_process_names(self,args=None,pname=None):
        '''
            @name 添加进程名
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @param name<string> 进程名
            @return dict
        '''
        if args:
            if 'pname' in args: pname = args.get("pname")
        if not pname: return public.returnMsg(False,"参数错误")
        config = self.read_config()
        if pname in config["process_names"]: return public.returnMsg(False,"指定进程名已经添加过了")
        config["process_names"].append(pname)
        self.save_config(config)
        public.WriteLog("防篡改","添加到进程名白名单: {}".format(pname))
        return public.returnMsg(True,"添加成功")


    def remove_process_names(self,args=None,pname=None):
        '''
            @name 删除进程名
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @param pname<string> 进程名
            @return dict
        '''
        if args:
            if 'pname' in args: pname = args.get("pname")
        if not pname: return public.returnMsg(False,"参数错误")
        config = self.read_config()
        if pname not in config["process_names"]: return public.returnMsg(False,"指定进程名不存在")
        config["process_names"].remove(pname)
        self.save_config(config)
        public.WriteLog("防篡改","删除进程名白名单: {}".format(pname))
        return public.returnMsg(True,"删除成功")


    def add_uids(self,args=None,uid=None):
        '''
            @name 添加UID
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @param uid<int> UID
            @return dict
        '''
        if args:
            if 'uid' in args: uid = int(args.get("uid"))
        if uid == None: return public.returnMsg(False,"参数错误")
        config = self.read_config()
        if uid in config["uids"]: return public.returnMsg(False,"指定UID已经添加过了")
        config["uids"].append(uid)
        self.save_config(config)
        public.WriteLog("防篡改","添加到用户白名单: {}".format(self.get_user_byuid(uid)))
        return public.returnMsg(True,"添加成功")

    def remove_uids(self,args=None,uid=None):
        '''
            @name 删除UID
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @param uid<int> UID
            @return dict
        '''
        if args:
            if 'uid' in args: uid = int(args.get("uid"))
        if uid == None: return public.returnMsg(False,"参数错误")
        config = self.read_config()
        if uid not in config["uids"]: return public.returnMsg(False,"指定UID不存在")
        config["uids"].remove(uid)
        self.save_config(config)
        public.WriteLog("防篡改","删除用户白名单: {}".format(self.get_user_byuid(uid)))
        return public.returnMsg(True,"删除成功")

    def get_group_bygid(self,gid):
        '''
            @name 获取组名
            @author hwliang
            @param gid<int> 组ID
            @return string
        '''
        gid = int(gid)
        gids = self.get_linux_gids()
        for g in gids:
            if gid == g['gid']:
                return g['group']
        return gid

    def get_user_byuid(self,uid):
        '''
            @name 获取用户名
            @author hwliang
            @param uid<int> 用户ID
            @return string
        '''
        uid = int(uid)
        uids = self.get_linux_uids()
        for u in uids:
            if uid == u['uid']:
                return u['user']
        return uid

    def add_gids(self,args=None,gid=None):
        '''
            @name 添加GID
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @param gid<int> GID
            @return dict
        '''
        if args:
            if 'gid' in args: gid = int(args.get("gid"))
        if gid == None: return public.returnMsg(False,"参数错误")
        config = self.read_config()
        if gid in config["gids"]: return public.returnMsg(False,"指定用户组已经添加过了")
        config["gids"].append(gid)
        self.save_config(config)


        public.WriteLog("防篡改","添加到用户组白名单: {}".format(self.get_group_bygid(gid)))
        return public.returnMsg(True,"添加成功")

    def remove_gids(self,args=None,gid=None):
        '''
            @name 删除GID
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @param gid<int> GID
            @return dict
        '''
        if args:
            if 'gid' in args: gid = int(args.get("gid"))
        if gid == None: return public.returnMsg(False,"参数错误")
        config = self.read_config()
        if gid not in config["gids"]: return public.returnMsg(False,"指定用户组不存在")
        config["gids"].remove(gid)
        self.save_config(config)
        public.WriteLog("防篡改","删除用户组白名单: {}".format(self.get_group_bygid(gid)))
        return public.returnMsg(True,"删除成功")


    def get_user_ps(self,user):
        '''
            @name 获取用户描述
            @author hwliang
            @param user<string> 用户名
            @return string
        '''
        user = str(user)
        user_ps = {
            "root": "超级管理员用户",
            "www": "用于运行网站的用户，包括php-fpm、nginx、apache、pure-ftpd等网站相关进程都使用此用户",
            "mysql": "用于运行MySQL数据库的用户",
            "mongo": "用于运行MongoDB数据库的用户",
            "memcached": "用于运行Memcached的用户",
            "redis": "用于运行Redis的用户",
            "ftp": "用于运行FTP的用户",
            "postfix": "用于运行Postfix(邮件)的用户",
            "sshd": "用于运行SSH的用户",
            "springboot": "用于运行Java-SpringBoot的用户",
            "tomcat": "用于运行Tomcat的用户",
            "postgres": "用于运行PostgreSQL数据库的用户",
            "named": "用于运行DNS的用户",
            "httpd": "用于运行Apache的用户",
            "nginx": "用于运行Nginx的用户",
            "php-fpm": "用于运行PHP-FPM的用户",
            "pure-ftpd": "用于运行Pure-FTP的用户",
            "nobody": "低权限用户",
        }
        if user in user_ps:
            return user_ps[user]
        return user


    def get_linux_uids(self,args=None):
        '''
            @name 获取系统UID
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @return list
        '''
        passwd_file = "/etc/passwd"
        if not os.path.exists(passwd_file): return []
        uids = []
        passwd_body = public.readFile(passwd_file)
        for line in passwd_body.split("\n"):
            if not line: continue
            _tmp = line.split(":")
            uid = int(_tmp[2])
            if uid < 1000 and uid > 0: continue
            uid_info = {
                "uid":uid,
                "ps": self.get_user_ps(_tmp[0]),
                "user":_tmp[0]
            }
            uids.append(uid_info)
        return sorted(uids,key=lambda x:x['uid'])

    def get_linux_gids(self,args=None):
        '''
            @name 获取系统GID
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @return list
        '''
        group_file = "/etc/group"
        if not os.path.exists(group_file): return []
        gids = []
        group_body = public.readFile(group_file)
        for line in group_body.split("\n"):
            if not line: continue
            _tmp = line.split(":")
            gid = int(_tmp[2])
            if gid < 1000 and gid > 0: continue
            gid_info = {
                "gid":gid,
                "ps": self.get_user_ps(_tmp[0]),
                "group":_tmp[0]
            }
            gids.append(gid_info)
        return sorted(gids,key=lambda x:x['gid'])

    def get_linux_users_or_groups(self,args=None):
        '''
            @name 获取系统用户和组
            @author hwliang<2020-07-01>
            @param args<dict_obj> 外部参数，可以为空
            @return list
        '''

        result = {
            "users":self.get_linux_uids(args),
            "groups":self.get_linux_gids(args)
        }
        return result

    def old_get_logs(self,args = None,path_id = None):
        '''
            @name 获取日志
            @author hwliang<2020-07-01>
            @param path_id<int> 日志路径ID
            @return list
        '''
        rows = 10
        p = 1
        if args:
            if 'path_id' in args: path_id = int(args.get("path_id"))
            if 'p' in args: p = int(args.get("p"))
            if 'rows' in args: rows = int(args.get("rows"))
        if path_id == None: return public.returnMsg(False,"参数错误")

        path_info = self.get_tamper_path_find(path_id=path_id)
        if not path_info: return public.returnMsg(False,"指定目录配置不存在")

        log_file = "{}/{}.log".format(self.__logs_path,path_id)
        if not os.path.exists(log_file):
            return []

        result = []

        f_size = os.path.getsize(log_file)

        if f_size > 1024 * 1024 * 30:
            page = public.get_page(10000,p,rows)
            tmp_lines = public.GetNumLines(log_file,rows,p)
            if tmp_lines:
                tmp_lines = tmp_lines.split("\n")
            else:
                tmp_lines = []

        else:
            fp = open(log_file,"r",errors="ignore")
            all_lines = fp.readlines()
            fp.close()
            page = public.get_page(len(all_lines),p,rows)
            start = int(page['shift'])
            tmp_lines = []
            all_sort_lines = []
            for line in all_lines:
                all_sort_lines.insert(0,line)
            tmp_lines = all_sort_lines[start:start+rows]

        for _line in tmp_lines:
            _tmp = _line.split("] [")
            if len(_tmp) < 2: continue
            _info = {
                "date": _tmp[0].strip().strip("["),
                "type": _tmp[1],
                "content": _tmp[2].replace(path_info['path'],"./"),
                "user": _tmp[3],
                "process": _tmp[4].strip().strip("]")
            }
            result.append(_info)
        page['data'] = sorted(result,key=lambda x:x['date'],reverse=True)

        return page


    def get_action_logs(self,args=None):
        '''
            @name 获取操作日志
            @author hwliang
            @param p<int> 分页
            @param rows<int> 每页行数
        '''

        num = public.M("logs").where("type=?","防篡改").count()
        p = 1
        rows = 10
        if args:
            if 'p' in args: p = int(args.get("p"))
            if 'rows' in args: rows = int(args.get("rows"))

        page = public.get_page(num,p,rows)
        limit = "{},{}".format(page["shift"],page['row'])
        page['data'] = public.M("logs").where("type=?","防篡改").order("id desc").limit(limit).field("addtime,type,log").select()
        return page

    def get_path_total(self,args=None,path_id=None):
        '''
            @name 获取目录统计
            @author hwliang
            @param path_id<int> 目录ID
            @return dict
        '''
        if args:
            if 'path_id' in args: path_id = int(args.get("path_id"))

        if path_id == None: return public.returnMsg(False,"参数错误")
        total_all_file = "{}/{}/total.json".format(self.__total_path,path_id)
        total = {}
        default_total = {
            "create": 0, "modify": 0,
            "unlink": 0, "rename": 0,
            "mkdir":  0, "rmdir":  0,
            "chmod":  0, "chown":  0,
            "link":   0
        }

        total['all'] = default_total

        _all = public.readFile(total_all_file)
        if _all: total['all'] = json.loads(_all)
        total['today'] = default_total
        total_today_file = "{}/{}/{}.json".format(self.__total_path,path_id,public.format_date("%Y-%m-%d"))
        _today = public.readFile(total_today_file)
        if _today:
            _today = json.loads(_today)
            for k in _today.keys():
                total['today']['create'] += _today[k]['create']
                total['today']['modify'] += _today[k]['modify']
                total['today']['unlink'] += _today[k]['unlink']
                total['today']['rename'] += _today[k]['rename']
                total['today']['mkdir'] += _today[k]['mkdir']
                total['today']['rmdir'] += _today[k]['rmdir']
                total['today']['chmod'] += _today[k]['chmod']
                total['today']['chown'] += _today[k]['chown']
                total['today']['link'] += _today[k]['link']
        return total


    def get_path_total_list(self,args=None,path_id=None):
        '''
            @name 获取所有目录统计
            @author hwliang
            @param path_id<int> 目录ID
            @return list
        '''
        if args:
            if 'path_id' in args: path_id = int(args.get("path_id"))
        total_path = "{}/{}".format(self.__total_path,path_id)
        if not os.path.exists(total_path): return []
        total_all = []
        day_files = []
        for day_name in os.listdir(total_path):
            if day_name in ['total.json']: continue
            day_file = "{}/{}".format(total_path,day_name)
            if not os.path.exists(day_file): continue
            day_files.append(day_name.strip('.json'))

        for day_name in sorted(day_files,reverse=False):
            day_file = "{}/{}.json".format(total_path,day_name)
            _day = json.loads(public.readFile(day_file))
            for k in sorted(_day.keys()):
                _tmp = _day[k]
                _tmp['date_hour'] = "{}_{}".format(day_name,k)
                total_all.append(_tmp)

        return total_all

    def get_glabal_total(self,args=None):
        '''
            @name 获取全局统计
            @author hwliang
            @return dict
        '''
        result = {}
        total_all_file = "{}/total.json".format(self.__total_path)
        total = {
            "create": 0, "modify": 0, "unlink":0,"rename": 0, "mkdir": 0,
            "rmdir": 0,"chmod": 0,"chown": 0,"link": 0,"warning_msg":  0
        }
        _all = public.readFile(total_all_file)
        if _all: total = json.loads(_all)
        if "warning_msg" not in total:
            total["warning_msg"] = 0
        result["glabal"] = total
        details = []
        config = self.read_config()
        for i in config["paths"]:
            _tmp = self.get_path_total(path_id = i["pid"])
            _tmp.update(pid=i["pid"], path=i["path"])
            details.append(_tmp)
        result["details"] = details
        glabal_today = {}
        for i in details:
            for k, v in i["today"].items():
                if k not in glabal_today:
                    glabal_today[k] = v
                else:
                    glabal_today[k] += v
        result["glabal_today"] = glabal_today    
        glabal_status = self.get_service_status()
        glabal_status.update(settings_status = bool(config["status"]))
        result["glabal_status"] = glabal_status
        result["days"] = self._get_use_day()

        return result

    def get_service_status(self,args=None):
        '''
            @name 获取服务状态
            @author hwliang
            @return dict  kernel_module_status=内核驱动加载状态，controller_status=控制器状态
        '''
        result = {}
        result['kernel_module_status'] = not public.ExecShell("lsmod|grep tampercore")[0].strip() == ""
        result['controller_status'] = not public.ExecShell("pidof tamperuser")[0].strip() == ""
        return result

    def service_admin(self,args = None,action = None):
        '''
            @name 服务管理
            @author hwliang
            @param action<str> 动作 start|stop|restart|reload
        '''

        if args:
            if 'action' in args: action = args.get("action")
        if not action in ['stop','reload','start','restart']:
            return public.returnMsg(False,'不支持的操作参数')

        res = public.ExecShell("/etc/init.d/bt-tamper {}".format(action))[0]

        _tip = """当前内核版本不一致，请尝试更新系统，获取内核版本,具体操作如下:<br><b>1</b>.&nbsp为您的服务器做好<b>快照或备份</b>，以防止更新系统过程中出错，导致不可挽回的损失。<br>
<b>2</b>.&nbsp执命令更新服务器<br>&nbsp&nbsp&nbsp&nbsp如果您的服务器系统类型为Redhat系，如Redhat、Centos、Fedora等，您可以执行<br> <code>yum update</code> 进行更新.<br>
&nbsp&nbsp&nbsp&nbsp如果您的服务器系统类型为Debian系，主要有Debian、Ubuntu、Mint等，您可以先执行<code>apt-get update -y</code>更新管理工具，再执行<code>apt-get upgrade -y</code>更新系统<br>
<b>3</b>.&nbsp<b>重启服务器</b>，重新安装下防篡改插件"""

        msg_status = {"stop":"停止","reload":"重载","start":"启动","restart":"重启"}
        if action != 'stop':
            status_msg = self.get_service_status()
            if not status_msg['kernel_module_status']:
                if res.find("内核版本不一致") != -1:
                    return {"status": False, "tip": _tip}
                return public.returnMsg(False,'内核模块加载失败')
            if not status_msg['controller_status']:
                return public.returnMsg(False,'控制器启动失败')
        public.WriteLog('防篡改','防篡改服务已{}'.format(msg_status[action]))
        return public.returnMsg(True,'防篡改服务已{}'.format(msg_status[action]))


#—————————————————————
#  融合到文件目录系统  |
#—————————————————————

    def check_dir_safe(self, args=None, file_data= None):
        """ 融合到文件目录系统， 查看文件是否安全
        @author baozi <202-03-1>
        @param:
            file_data ( dict ) : 包含 1.base_path 查询目录的父级目录的绝对路径, 2.dirs 文件夹的名称列表, 3.files 文件的名称列表
        @return ( dict )  是否被保护 (1.dirs 文件夹的名称列表, 2. files 文件的名称列表， 3. rules保护规则
        """
        res = {"this":"", "dirs": [], "files": [], "rules":[], "status":True, "tip":"ok"}
        status = self.get_service_status()
        if not (status["kernel_module_status"] and  status["controller_status"]):
            res["status"], res["tip"] = False, "内核模块加载失败"
            return res
        if args:
            if 'file_data' in args: file_data = args.get("file_data")
        if not file_data:
            res["status"], res["tip"] = False, "没有文件信息"
            return res
        config = self.read_config()
        if config["status"] != 1:
            res["status"], res["tip"] = False, "全局设置已关闭，开启后才可检测"
            return res

        # 构建查询tree
        root, rules = self._build_dict_tree(config)

        # 路径查询
        node = root
        use_rule = set()
        target_pid = 0
        target_status = False
        base_path_list = file_data["base_path"].split("/")[1:]
        for i, p in enumerate(base_path_list):
            if not node["children"]:
                break
            if p not in node["children"]:
                break
            node = node["children"][p]
            if node["pid"] != target_pid:
                target_pid = node["pid"]
                target_status = bool(node["status"])

        # 本层是否已被排除
        this_is_white = False
        if target_pid != 0:
            rule = rules[target_pid]
            if self._check_white_dirs(file_data["base_path"] + "/", rule["white_dirs"]):
                this_is_white = True
                res["this"] = "0;" + str(target_pid)
            else:
                res["this"] = "1;" + str(target_pid)
        else:
            res["this"] = "0;0"

        for i in file_data["dirs"]:
            _path = file_data["base_path"] + "/" + i + "/"
            # 本层的下级文件夹是否运用其他规则
            if node["children"] and i in node["children"] and node["children"][i]["pid"] != node["pid"]:
                _rule = rules[node["children"][i]["pid"]]
                safe = not self._check_white_dirs(_path, _rule["white_dirs"]) and bool(_rule["status"])
                res["dirs"].append("{};{}".format(int(safe),  node["children"][i]["pid"]))
                use_rule.add(node["children"][i]["pid"])
                continue
            if this_is_white:
                res["dirs"].append("0;{}".format(target_pid))
            else:
                safe = not self._check_white_dirs(_path, rules[target_pid]["white_dirs"]) if target_pid != 0 else False
                safe = safe and target_status
                res["dirs"].append("{};{}".format(int(safe), target_pid))

        for i in file_data["files"]:
            file_path = file_data["base_path"] + "/" + i
            if target_pid == 0 or this_is_white:
                res["files"].append("0;{}".format(target_pid))
                continue
            if target_pid != 0:
                safe = False
                if self._check_ext(file_path, rules[target_pid]["black_exts"]):
                    safe = not self._check_white_files(file_path, rules[target_pid]["white_files"])

                safe = safe and bool(target_status)
                res["files"].append("{};{}".format(int(safe), target_pid))

        if target_pid != 0:
            use_rule.add(target_pid)

        for i in use_rule:
            res["rules"].append(rules[i])

        return res

    # 构建查询tree
    def _build_dict_tree(self, config):
        rules = {}
        root = {"pid": 0, "status": 0, "children":{}}
        for i in config["paths"]:
            rules[i["pid"]] = i
            path_list = i["path"].split("/")[1:-1]
            node = root
            for j in path_list:
                if j not in node["children"]:
                    node["children"][j] = {"pid": node["pid"], "status": node["status"],  "children":{}}
                node = node["children"][j]
            node["pid"] = i["pid"]
            node["status"] = i["status"]

        return root, rules

    def _check_white_dirs(self, dir_path, white_dirs):
        res = []
        for i in white_dirs:
            if i[0] != "/" and i[-1] == "/":
                if dir_path.find("/" + i) != -1:
                    res.append(i)
            else:
                if dir_path.find(i) != -1:
                    res.append(i)
        return res


    def _check_ext(self, file_path, black_exts):
        res = []
        for i in black_exts:
            if i[0] == ".":
                if file_path.endswith(i):
                    res.append(i)
            else:
                _black = "/" + i if i[0] != "/" else i
                if file_path.endswith(_black):
                    res.append(i)

        return res

    def _check_white_files(self, file_path, white_files):
        res = []
        for i in white_files:
            if i[0] == "/":
                if file_path.startswith(i):
                    res.append(i)
            else:
                if file_path.endswith("/" + i):
                    res.append(i)

        return res

    def _check_tamper_system(self, res):
        status = self.get_service_status()
        if not status["kernel_module_status"] or not status["controller_status"]:
            res["status"], res["msg"]= False, "服务未开启或内核出现了问题"
            res["kernel_module_status"]  = status["kernel_module_status"]
            res["controller_status"] = status["controller_status"]
            return False, res
        config = self.read_config()
        if config["status"] != 1:
            res["status"], res["msg"] = False, "全局设置已关闭，开启后才可检测"
            return False, res

        return True, config

    def _test_bool_parameter(self, pm, default):
        if pm in ("False", "false", 0, "0", None, "null", "FALSE", False):
            return False
        if pm in ("True", "true", 1, "1", "TRUE", True):
            return True
        return default

    def _create_path_config(self, path, **kwargs):
        # 路径标准化处理
        if path[-1] != "/": path += "/"
        path = path.replace('//','/')

        # 参数过滤
        if not path: return public.returnMsg(False,"目录路径不能为空")
        if not os.path.exists(path) or os.path.isfile(path): return public.returnMsg(False,"无效的目录: {}".format(path))
        if self.get_tamper_path_find(path=path): return public.returnMsg(False,"指定目录已经添加过了: {}".format(path))

        # 关键路径过滤
        if path in ['/','/root/','/boot/','/www/','/www/server/','/www/server/panel/','/www/server/panel/class/','/usr/','/etc/','/usr/bin/','/usr/sbin/']:
            return public.returnMsg(False,"不能添加系统关键目录: {}".format(path))

        config = self.read_config()
        path_info = {
            "pid":self.get_path_id(config["paths"]),
            "path":path,
            "status":1,
            "mode":0,
            "is_create":1,
            "is_modify":1,
            "is_unlink":1,
            "is_mkdir":1,
            "is_rmdir":1,
            "is_rename":1,
            "is_chmod":1,
            "is_chown":1,
            "is_link":1,
            "black_exts": kwargs["black_exts"] if "black_exts" in kwargs else config["default_black_exts"],
            "white_files": kwargs["white_files"] if "white_files" in kwargs else config["default_white_files"],
            "white_dirs": kwargs["white_dirs"] if "white_dirs" in kwargs else config["default_white_dirs"],
            "ps": ""
        }

        # 添加到配置列表
        config["paths"].append(path_info)
        config["dir_ps_" + str(path_info["pid"])] = {}
        self.save_config(config)
        public.WriteLog("防篡改","添加目录配置: {}".format(path))
        return {"status":True, "msg":"添加目录成功", "rule": path_info }
    
    def quick_lock_file(self, args = None, file_path = None, same_type=False, forcible=False):
        """ 融合到文件目录系统， 快速锁定文件
        @author baozi <202-03-6>
        @param:
            file_path ( dict ) : 文件所在位置
        @return ( dict )

        √ : 遇到多重白名单？ 最多两层， 可以同时移除
        """
        res = {"status":True, "tip":"ok"}
        flag, config = self._check_tamper_system(res)
        if not flag:
            return config
        if args:
            if 'file_path' in args: file_path = args.get("file_path")
            if 'forcible' in args: forcible = self._test_bool_parameter(args.get("forcible"), forcible)
            if 'same_type' in args: same_type = self._test_bool_parameter(args.get("same_type"), same_type)

        if not file_path or not os.path.isfile(file_path):
            res["status"], res["tip"] = False, "没有文件信息"
            return res

        # 构建查询tree
        root, rules = self._build_dict_tree(config)

        node = root
        target_pid = 0
        target_status = False
        path_list = file_path.split("/")[1:-1]
        for p in path_list:
            if not node["children"]:
                break
            if p not in node["children"]:
                break
            node = node["children"][p]
            if node["pid"] != target_pid:
                target_pid = node["pid"]
                target_status = bool(node["status"])

        if target_pid == 0:
            # 自身没有规则，创建一个快锁规则
            # 路径标准化处理
            path, file_name = file_path.rsplit("/", 1)
            _ext = "." + file_name.rsplit(".")[1] if "." in file_name else file_name
            black_exts = [file_path,] if not same_type else [_ext,]

            return self._create_path_config(path, black_exts=black_exts, white_files=[], white_dirs=[])

        # 规则未开启
        if not target_status:
            return public.returnMsg(False,"该路径下已存在防篡改规则，但未开启是使用，请打开该规则之后再次尝试修改")
        # 检查这个文件已经被锁定 则无法操作，返回错误
        # 未被锁定
        # 1. 规则已开启，不在保护对象中              ————>     定点添加保护 或 批量添加保护
        # 2. 规则已开启，在保护对象中，但被文件白名单排除 ————>     1.白名单中定点移除，则取消移除   2.白名单规则批量移除的，且用户未选择作用于所有同类文件，则不支持快锁
        # 2. 规则已开启，在保护对象中，但被文件夹白名单排除 ————>     1.规则根目录不在本层，新建一个规则保护， 2.规则根目录在本层，需改这个规则，使之符合要求（这种情况说明原规则未起到任何作用），
        # 3. 规则未开启                            ————>     不支持快锁，请用户手动修改状态

        rule = rules[target_pid]
        path, file_name = file_path.rsplit("/", 1)
        if self._check_white_dirs(path + "/", rule["white_dirs"]):
            _ext = "." + file_name.rsplit(".")[1] if "." in file_name else file_name
            black_exts = [file_path,] if not same_type else [_ext,]
            if path + "/" == rule["path"]:
                rule["black_exts"] = black_exts
                rule["white_files"] = []
                rule["white_dirs"] = []
                public.WriteLog("防篡改","快锁功能修改目录:{},的受保护的后缀名为: {},并清空了白名单文件和白名单文件夹。".format(rule["path"], black_exts))

                for i, p in enumerate(config["paths"]):
                    if p["pid"] == target_pid:
                        config["paths"][i] = rule

                self.save_config(config)
                return public.returnMsg(True,"修改成功")
            else:
                return self._create_path_config(path, black_exts=black_exts, white_files=[], white_dirs=[])

        if self._check_ext(file_path, rule["black_exts"]) and not self._check_white_files(file_path, rule["white_files"]):
                return public.returnMsg(False, "该文件已被保护，无需修改")

        if not self._check_ext(file_path, rule["black_exts"]):
            _ext = "." + file_name.rsplit(".")[1] if "." in file_name else file_name
            black_ext = file_path if not same_type else _ext
            rule["black_exts"].append(black_ext)
            public.WriteLog("防篡改","快锁功能添加目录:{},的受保护的后缀名: {}".format(rule["path"], black_ext))

        if self._check_white_files(file_path, rule["white_files"]):
            if not forcible :
                if not file_path in rule["white_files"]:
                    return {"status":False,"msg": "该文件为白名单规则批量解锁的文件，强制执行将移除这些白名单规则，但可能同时影响其他文件状态。" ,"white_files": self._check_white_files(file_path, rule["white_files"])}
            if forcible:
                if file_name in rule["white_files"]:
                    rule["white_files"].remove(file_name)
                    public.WriteLog("防篡改","快锁功能强制移除目录:{},的文件白名单: {}".format(rule["path"], file_name))

            if file_path in rule["white_files"]:
                rule["white_files"].remove(file_path)
                public.WriteLog("防篡改","快锁功能移除目录:{},的文件白名单: {}".format(rule["path"], file_path))

        for i, p in enumerate(config["paths"]):
            if p["pid"] == target_pid:
                config["paths"][i] = rule

        self.save_config(config)

        return public.returnMsg(True,"修改成功")


    def quick_unlock_file(self, args = None, file_path = None, same_type=False, forcible=False):
        """ 融合到文件目录系统， 快速解锁文件
        @author baozi <202-03-6>
        @param:
            file_path ( dict ) : 文件所在位置
        @return ( dict )
        ? : 遇到多重锁定
        """
        # 检查这个文件未被锁定 则无法操作，返回错误
        # 已被锁定，规则已开启，在保护对象中
        # 1. 属于定点添加保护                       ————>     移除添加的保护
        # 2. 属于规则范围内的保护对象                ————>     通过白名单中定点移除，取消保护
        res = {"status":True, "msg":"ok"}
        flag, config = self._check_tamper_system(res)
        if not flag:
            return config
        if args:
            if 'file_path' in args: file_path = args.get("file_path")
            if 'same_type' in args: same_type = self._test_bool_parameter(args.get("same_type"), same_type)
        if not file_path or not os.path.isfile(file_path):
            res["status"], res["msg"] = False, "没有文件信息"
            return res

        # 构建查询tree
        root, rules = self._build_dict_tree(config)

        node = root
        target_pid = 0
        target_status = False
        path_list = file_path.split("/")[1:-1]
        for p in path_list:
            if not node["children"]:
                break
            if p not in node["children"]:
                break
            node = node["children"][p]
            if node["pid"] != target_pid:
                target_pid = node["pid"]
                target_status = bool(node["status"])

        if target_pid == 0 or not target_status:
            return public.returnMsg(False, "文件未被保护，无法解除保护")

        rule = rules[target_pid]
        path, file_name = file_path.rsplit("/", 1)
        if self._check_white_dirs(path + "/", rule["white_dirs"]):
            return public.returnMsg(False, "文件未被保护，无法解除保护")

        if self._check_ext(file_path, rule["black_exts"]) and not self._check_white_files(file_path, rule["white_files"]):
            if file_path in rule["black_exts"]:
                rule["black_exts"].remove(file_path)
                public.WriteLog("防篡改","快锁功能移除目录:{},的受保护的后缀名: {}".format(rule["path"], file_path))
            else:
                rule["white_files"].append(file_path)
                public.WriteLog("防篡改","快锁功能添加目录:{},的文件白名单: {}".format(rule["path"], file_path))
            if same_type:
                file_name = file_path.rsplit("/", 1)[1]
                _ext = "." + file_name.rsplit(".")[1] if "." in file_name else file_name
                if _ext in rule["black_exts"]:
                    rule["black_exts"].remove(_ext)
                    public.WriteLog("防篡改","快锁功能移除目录:{},的受保护的后缀名: {}".format(rule["path"], _ext))
        else:
            return public.returnMsg(False, "文件未被保护，无法解除保护")

        for i, p in enumerate(config["paths"]):
            if p["pid"] == target_pid:
                config["paths"][i] = rule

        self.save_config(config)

        return public.returnMsg(True,"修改成功")


    def quick_lock_dir(self, args= None, dir_path=None, forcible=False):
        """ 融合到文件目录系统， 快速锁定文件夹（目录）
        @author baozi <202-03-6>
        @param:
            file_path ( dict ) : 文件所在位置
        @return ( dict )
        """
        res = {"status":True, "tip":"ok"}
        flag, config = self._check_tamper_system(res)
        if not flag:
            return config
        if args:
            if 'dir_path' in args: dir_path = args.get("dir_path")
            if 'forcible' in args: forcible = self._test_bool_parameter(args.get("forcible"), forcible)


        if not dir_path or not os.path.exists(dir_path):
            res["status"], res["tip"] = False, "没有文件信息"
            return res
        if dir_path[-1] != "/": dir_path += "/"

        # 构建查询tree
        root, rules = self._build_dict_tree(config)
        node = root
        target_pid = 0
        target_status = False
        path_list = dir_path.split("/")[1:-1]
        for p in path_list:
            if not node["children"]:
                break
            if p not in node["children"]:
                break
            node = node["children"][p]
            if node["pid"] != target_pid:
                target_pid = node["pid"]
                target_status = bool(node["status"])

        # 自身没有规则 -> 创建一个快锁规则
        # 如果有规则, 规则未开启,且规则根路径为本文件夹路径-> 开启该文件目录锁对应的规则

        # 如果有规则, 规则未开启,但规则根路径不是本文件夹路径-> 创建一个快锁规则

        # 如路径被白名单定点排除，则移除该白名单项
        # 如果路径属于被白名单规则批量移除，则需要用户选择强制执行，移除受限白名单
        if target_pid == 0:
            return self._create_path_config(dir_path)
        rule = rules[target_pid]
        if not target_status:
            if dir_path == rule["path"]:
                rule["status"] = 1
            else:
                return self._create_path_config(dir_path)

        if self._check_white_dirs(dir_path, rule["white_dirs"]):
            if dir_path in rule["white_dirs"]:
                rule["white_dirs"].remove(dir_path)
                public.WriteLog("防篡改","快锁功能删除目录:{},的目录白名单: {}".format(rule["path"],dir_path))

        else:
            return public.returnMsg(False, "文件路径已被保护，无法操作")

        res = self._check_white_dirs(dir_path, rule["white_dirs"])
        if res:
            if not forcible:
                return {"status":False, "msg": "该文件路径为白名单批量规则批量解锁，强制执行会移除这些白名单表，这可能影响其他文件的状态!", "white_dirs": res}
            for i in res:
                rule["white_dirs"].remove(i)
                public.WriteLog("防篡改","快锁功能强制删除目录:{},的目录白名单: {}".format(rule["path"],i))


        for i, p in enumerate(config["paths"]):
            if p["pid"] == target_pid:
                config["paths"][i] = rule

        self.save_config(config)

        return public.returnMsg(True,"修改成功")


    def quick_unlock_dir(self, args= None, dir_path=None):
        """ 融合到文件目录系统， 快速解锁定文件夹（目录）
        @author baozi <202-03-6>
        @param:
            file_path ( dict ) : 文件所在位置
        @return ( dict )
        """
        res = {"status":True, "tip":"ok"}
        flag, config = self._check_tamper_system(res)
        if not flag:
            return config
        if args:
            if 'dir_path' in args: dir_path = args.get("dir_path")

        if not dir_path or not os.path.exists(dir_path):
            res["status"], res["tip"] = False, "没有文件信息"
            return res
        if dir_path[-1] != "/": dir_path += "/"

        # 构建查询tree
        root, rules = self._build_dict_tree(config)
        node = root
        target_pid = 0
        target_status = False
        path_list = dir_path.split("/")[1:-1]
        for p in path_list:
            if not node["children"]:
                break
            if p not in node["children"]:
                break
            node = node["children"][p]
            if node["pid"] != target_pid:
                target_pid = node["pid"]
                target_status = bool(node["status"])

        # 自身没有规则 或未开启 -> 返回错误
        # 如果有规则, 规则已开启,且规则根路径为本文件夹路径-> 关闭该文件目录锁对应的规则
        # 白名单添加定点排除
        if target_pid == 0:
            return public.returnMsg(False, "文件路径未被保护，无法操作")
        rule = rules[target_pid]
        if  target_status:
            if dir_path == rule["path"]:
                rule["status"] = 0
        else:
            return public.returnMsg(False, "文件路径未被保护，无法操作")

        if  not self._check_white_dirs(dir_path, rule["white_dirs"]):
            rule["white_dirs"].append(dir_path)
            public.WriteLog("防篡改","快锁功能添加目录:{},的目录白名单: {}".format(rule["path"],dir_path))
        else:
            return public.returnMsg(False, "文件路径未被保护，无法操作")

        for i, p in enumerate(config["paths"]):
            if p["pid"] == target_pid:
                config["paths"][i] = rule

        self.save_config(config)

        return public.returnMsg(True,"修改成功")

    def get_backtrack_image(self, args=None):
        """获取防篡改任务
        @author baozi <202-03-11>
        @param:
        @return
        """
        backtrack_path = public.get_panel_path() + "/data/crontab"
        file_path =  backtrack_path + "/tamper_image.json"
        if os.path.exists(file_path) and os.path.isfile(file_path) :
            tasks = json.loads(public.readFile(file_path))
            task_file = tasks["task"]
            if os.path.exists(task_file):
                return {"status": True,"time": tasks["time"]}
        
        return  {"status": False, "tip": "没有回溯任务"}
                

    def make_backtrack_image(self, args=None, time_congfig=None, forcible=False):
        """ 设置防篡改任务
        @author baozi <202-03-6>
        @param:
            file_path ( dict ) : 文件所在位置
        @return ( dict )
        """
        backtrack_path = public.get_panel_path() + "/data/crontab"
        file_path =  backtrack_path + "/tamper_image.json"
        if args:
            if 'time_congfig' in args: time_congfig = args.get("time_congfig")
            if 'forcible' in args: forcible = self._test_bool_parameter(args.get("forcible"), False)
        if isinstance(time_congfig,str):
            time_congfig = json.loads(time_congfig)
        if not os.path.exists(backtrack_path):
            os.makedirs(backtrack_path, mode=0o600)
        if os.path.exists(file_path) and os.path.isfile(file_path) :
            task_file = json.loads(public.readFile(file_path))["task"]
            if os.path.exists(task_file):
                if not forcible:
                    return public.returnMsg(False, "只能存在一个范篡改回溯设置，是否强制替换之前的设置？")
                else:
                    public.WriteLog("防篡改", "防篡改回溯任务移除成功")
                    os.remove(task_file)

        set_type = "delay" if  "type" in time_congfig and time_congfig["type"] in ("delay", "date") else time_congfig["type"]
        if set_type == "delay":
            try:
                h = int(time_congfig.get("hour"))
                m = int(time_congfig.get("minute"))
                if not 0 <= m <= 60: raise ValueError
            except ValueError:
                return public.returnMsg(False, "时间设置错误")
            _time = (datetime.datetime.now() + datetime.timedelta(hours=h, minutes=m)).timestamp()
        else:
            try:

                _time = datetime.datetime.fromtimestamp(float(time_congfig.get("time"))).timestamp()
            except ValueError:
                return public.returnMsg(False, "时间设置错误")
            except OSError:
                try:
                    _time = datetime.datetime.fromtimestamp(float(time_congfig.get("time"))/1000).timestamp()
                except:
                    return public.returnMsg(False, "时间设置错误")

        config_data = {
            "time": int(_time),
            "type": 2,
            "name":"tamper_core",
            "fun":"task_callback",
            "args": {}
        }

        res = public.set_tasks_run(config_data)
        if not res["status"]:
            return public.returnMsg(False, "回溯任务设置失败")

        task = res["msg"]
        task_run_data = json.dumps({
            "task": task,
            "config": self.read_config(),
            "time": int(_time)
        })
        public.writeFile(file_path, task_run_data)
        public.WriteLog("防篡改","防篡改回溯任务设置成功，预计回溯时间：{}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(_time)))))

        return public.returnMsg(False, "设置成功")

    def  remove_backtrack_image(self, args=None):
        """移除防篡改回溯任务
        @author baozi <202-03-11>
        @param:
        @return
        """
        backtrack_path = public.get_panel_path() + "/data/crontab"
        file_path =  backtrack_path + "/tamper_image.json"
        if os.path.exists(file_path) and os.path.isfile(file_path) :
            tasks = json.loads(public.readFile(file_path))
            task_file = tasks["task"]
            if os.path.exists(task_file):
                os.remove(task_file)
                public.WriteLog("防篡改", "防篡改回溯任务移除成功")
                return  {"status": True, "tip": "回溯任务移除成功"}
                
        return  {"status": False, "tip": "没有回溯任务"}
    
    def task_callback(self, args):
        """ 用于回调，修改防篡改中的设置
        @author baozi <202-03-6>
        @param:
            file_path ( dict ) : 文件所在位置
        @return ( dict )
        """
        run_time = public.format_date()
        log_msg = f"防篡改回调操作(执行时间:{run_time}):\n"
        status = self.get_service_status()
        if not (status["kernel_module_status"] and  status["controller_status"]):
            log_msg += "\t内核模块加载失败\n"
        config = self.read_config()
        if config["status"] != 1:
            log_msg += "\t全局设置已关闭，开启后设置才能生效\n"

        backtrack_path = public.get_panel_path() + "/data/crontab"
        file_path =  backtrack_path + "/tamper_image.json"
        if not os.path.exists(backtrack_path):
            os.makedirs(backtrack_path, mode=0o600)
            log_msg += "\t快照文件丢失，未能回溯成功"
            public.WriteLog("防篡改",log_msg)
            return public.returnMsg(False, "防篡改回溯: 快照文件丢失，未能回溯成功!")

        if not (os.path.exists(file_path) and os.path.isfile(file_path)):
            log_msg += "\t快照文件丢失，未能回溯成功"
            public.WriteLog("防篡改",log_msg)
            return public.returnMsg(False, "防篡改回溯: 快照文件丢失，未能回溯成功!")

        try:
            task_run_data = json.loads(public.readFile(file_path))
            conf = task_run_data["config"]
        except:
            log_msg += "\t快照文件疑似被修改，无法读取，未能回溯成功"
            public.WriteLog("防篡改",log_msg)
            return public.returnMsg(False, "防篡改回溯: 快照文件疑似被修改，无法读取，未能回溯成功")
        self.save_config(conf)
        log_msg += "\t防篡改配置文件恢复成功"
        os.remove(file_path)
        public.WriteLog("防篡改",log_msg)
        return public.returnMsg(True, "防篡改回溯: 防篡改配置文件恢复成功")

    def get_effective_path(self, args=None, path=None):
        """查询路径生效的方式
        @author baozi <202-03-11>
        @param:
        @return  dict :  状态和生效条件
        """
        res = {"status":True, "tip":"ok"}
        flag, config = self._check_tamper_system(res)
        if not flag:
            config["tip"] = config.pop("msg")
            return config
        if args:
            if 'path' in args: path = args.get("path")
            # if 'next_state' in args: next_state = self._test_bool_parameter(args.get("next_state"))
        public.set_module_logs('tamper_core','get_effective_path')    
        if not path or not os.path.exists(path):
            res["status"], res["tip"] = False, "没有文件信息"
            return res

        if path[-1] == "/": path = path[:-1]
        file, dir_path= None, path
        if os.path.isfile(dir_path):
            dir_path, file= path.rsplit("/", 1)

        # 构建查询tree
        root, rules = self._build_dict_tree(config)

        # 路径查询
        node = root
        target_pid = 0
        target_status = False
        base_path_list = dir_path.split("/")[1:]
        for i, p in enumerate(base_path_list):
            if not node["children"]:
                break
            if p not in node["children"]:
                break
            node = node["children"][p]
            if node["pid"] != target_pid:
                target_pid = node["pid"]
                target_status = bool(node["status"])

        if target_pid == 0:
            res.update(data={
                "lock": False,
                "pid":0,
                "action": ["create",]
            })
            return res

        rule = rules[target_pid]
        _white_dir = self._check_white_dirs(dir_path + "/", rule["white_dirs"])
        _black_exts = []
        _white_files = []
        if file:
            _black_exts = self._check_ext(os.path.join(dir_path, file), rule["black_exts"])
            _white_files = self._check_white_files(os.path.join(dir_path, file), rule["white_files"])

        state =  not bool(_white_dir) and target_status
        act = []
        # if not target_status and dir_path + "/" == rule["path"]:
        if not target_status:
            act.append("open")
        if not state:
            # 当前未锁定状态， 目标：锁定
            # 若不在本层：则添加新的规则
            # 若有白名单保护: 可以移除白名单
            # if dir_path + "/" != rule["path"]:  # 暂时放弃create （不在本层：则添加新的规则）
            #     act.append("create")
            if _white_dir:
                act.append("remove_wd")
        if state and not file:
            # 当前锁定状态， 目标：解除锁定 （选择的不是文件）
            # 若在本层: 可以选择关闭，不在本层则： 添加白名单（决定路径）
            if dir_path + "/" == rule["path"]:
                act.append("close")
            else:
                act.append("add_wd")

        if file:
            state = state and bool(_black_exts) and not bool(_white_files)
            # 当前未锁定状态， 目标：解除文件锁定
            # 若不在本层则：添加新的规则
            # 若有白名单保护：可以移除白名单
            if  not state:
                if not _black_exts:
                    act.append("add_bf")
                if _white_files:
                    act.append("remove_wf")
            else:
            # 当前锁定状态， 目标：解除文件锁定
            # 移除黑名单后缀， 添加白名单
                act.append("remove_bf")
                act.append("add_wf")

        res.update(data={
            "lock": state,
            "pid":target_pid,
            "action": act,
            "white_dir": _white_dir,
            "black_exts": _black_exts,
            "white_files": _white_files,
            "rule":rule,
        })
        return res

    def create_path(self, args=None, path=None, exts=[]):
        """创建一个规则，可以指定要保护的内容
        @author baozi <202-03-13>
        @param:
            args ( dict )  (default: None )
                : 请求信息
            path ( str )  (default: None )
                : 添加的路径
            exts ( list )  (default: [] )
                : 待添加的黑名单，为空时则使用默认黑名单
        @return
        """
        if args:
            if 'path' in args:
                path = args.get("path")
            if 'exts' in args:
                exts = args.get("exts")

        if not exts:
            black_exts = None
        else:
            black_exts = exts
            if black_exts[0] == "[":
                black_exts = json.loads(black_exts)
            if isinstance(black_exts, str):
                black_exts = [black_exts,]

        if not os.path.exists(path): return public.returnMsg(False, "指定配置目标文件路径不存在")
        if os.path.isfile(path): return public.returnMsg(False, "指定配置目标文件路径不应当是具体文件")

        if black_exts:
            return self._create_path_config(path, black_exts=black_exts)
        else:
            return self._create_path_config(path)


    def batch_setting(self, args=None, pid=None, settings=None):
        """对某一个已存在的规则进行批量设置
        @author baozi <202-03-13>
        @param:
            args ( dict )  (default: None )
                : 请求信息
            pid ( int )  (default: None )
                : 目标规则的ID
            settings ( list )  (default: None )
                : 修改内容
        @return  dict : 操作结果
        """
        try:
            if args:
                if 'pid' in args:
                    pid = int(args.get("pid"))
                if 'settings' in args:
                    settings = args.get("settings")
            if isinstance(pid, str):
                pid = int(pid)
            if isinstance(settings, str):
                settings = json.loads(settings)
        except ValueError:
            return {"status": False, "msg": "参数错误"}
        if not settings:
            return {"status": False, "msg": "参数缺失"}

        if not self.get_tamper_path_find(path_id=pid): return public.returnMsg(False,"指定目标配置不存在")

        # 获取目录配置
        config = self.read_config()
        for path_info in config["paths"]:
            if  path_info["pid"] == pid:
                rule = path_info
                break

        log_msg = "对目录：{}的规则进行批量更改".format(rule["path"])
        for i in settings:
            key = i.get("key")
            if key not in ("open","close","remove_wd","add_wd","add_bf","remove_bf","add_wf","remove_wf"):
                return {"status": False, "msg": "未识别的操作项:{}".format(key)}
            if key == "open":
                rule["status"] = 1
                log_msg += "\n开启规则"
                continue
            elif key == "close":
                rule["status"] = 0
                log_msg += "\n关闭规则"
                continue

            values = i.get("values")
            values = [values, ] if isinstance(values, str) else values
            if not values:
                return {"status": False, "msg": "项:{}没有操作内容:".format(key)}
            if key == "remove_wd":
               for i in values:
                    if i in rule["white_dirs"]:
                        rule["white_dirs"].remove(i)
                        log_msg += "\n移除白名单路径:{}".format(i)
            elif key == "add_wd":
                for i in values:
                    if i not in rule["white_dirs"]:
                        rule["white_dirs"].append(i)
                        log_msg += "\n追加白名单路径: {}".format(i)
            elif key == "add_bf":
                for i in values:
                    if i not in rule["black_exts"]:
                        rule["black_exts"].append(i)
                        log_msg += "\n追加受保护的后缀: {}".format(i)
            elif key == "remove_bf":
                for i in values:
                    if i in rule["black_exts"]:
                        rule["black_exts"].remove(i)
                        log_msg += "\n移除受保护的后缀: {}".format(i)
            elif key == "add_wf":
                for i in values:
                    if i not in rule["white_files"]:
                        rule["white_files"].append(i)
                        log_msg += "\n追加白名单文件: {}".format(i)
            elif key == "remove_wf":
                for i in values:
                    if i in rule["white_files"]:
                        rule["white_files"].remove(i)
                        log_msg += "\n移除白名单文件: {}".format(i)
            if key not in ("open","close","remove_wd","add_wd","add_bf","remove_bf","add_wf","remove_wf"):
                return {"status": False, "msg": "未识别的操作项:{}".format(key)}


        self.save_config(config)
        public.WriteLog("防篡改",log_msg)
        return public.returnMsg(True,"修改成功")


#——————————————————————————————
#        日志切割与查询         |
#——————————————————————————————

    def _get_log_content(self, p, row, log_file_paths):
        """创建一个内，用于排序并获取日志内容
        @author baozi <202-03-23>
        @param: 
            log_file_paths  ( list ):  日志文件的列表
        @return 
        """
        def the_generator(self):
            _buf = b""
            for fp in self._get_fp():
                is_start = True
                while is_start:
                    buf = b''
                    while True:
                        pos = fp.tell()
                        read_size = pos if pos <= 38 else 38
                        fp.seek(-read_size, 1)
                        _buf = fp.read(read_size) + _buf
                        fp.seek(-read_size, 1)
                        nl_idx = _buf.rfind(ord('\n'))
                        if nl_idx == -1:
                            if pos <= 38: 
                                buf,  _buf = _buf, b''
                                is_start = False
                                break
                        else:
                            buf = _buf[nl_idx+1:]
                            _buf = _buf[:nl_idx]
                            break
                    res = self._is_use(buf.decode("utf-8"))
                    if self.count > 10000:
                        self.count -= 1
                        return 
                    if not (res is False):
                        yield res
        
        def the_init(self, p, size, log_files):
            self.log_files = log_files
            self.count = 0
            self.t_range = [(p-1)*size, p*size]
            self.test = [None for _ in range(4)]

        def the__get_fp(self):
            for i in self.log_files:
                if not os.path.exists(i): continue
                with open(i, 'rb') as fp:
                    fp.seek(-1, 2)
                    yield fp
        
        def the__is_use(self, log: str):
            _test = [i for i in log.split("] [")]
            _test[0] = _test[0].strip().strip("[")
            _test[4] = _test[4].strip().strip("]")
            for i in range(4):
                if self.test[i] is None: continue
                if not self.test[i](_test[i+1]):
                    return False
            self.count += 1
            if self.t_range[0] <= self.count - 1 < self.t_range[1]:
                return _test
            return False
        
        def the_set_args(self, target=None, t_type=None, user=None, proc=None):
            if target:
                self.test[1] = lambda x: x.find(target) != -1
            if t_type:
                self.test[0] = lambda x: x == t_type
            if user:
                self.test[2] = lambda x: x == user
            if proc:
                self.test[3] = lambda x: x.find(proc) != -1
            if bool(self.test[0]) or bool(self.test[1]) or bool(self.test[2]) or bool(self.test[3]):
                self._need = True
            else:
                self._need = False
            
        attr = {
            "__init__": the_init, 
            "_get_fp": the__get_fp, 
            "__iter__": the_generator,
            "_is_use": the__is_use,
            "set_args": the_set_args
        }
        return type("LogContent", (object, ), attr)(p, row, log_file_paths)
    
    # 获取日志文，并按关系排序
    def _get_log_files(self, log_path, before=None):
        files = glob.glob(log_path + "/*.log")
        files.sort(reverse=True)
        if before:
            try:
                idx = files.index("{}/{}.log".format(log_path, before))
            except:
                return []
            return files[idx:]
        return files
    
    def _check_query(self, query):
        err , res = "", {}
        if "target" in query and isinstance(query["target"], str):
            tmp = query["target"].strip()
            res["target"] = tmp if bool(tmp) else None

        if "t_type" in query and isinstance(query["t_type"], str):
            if query["t_type"] in ("create","modify","unlink","rename","mkdir","rmdir","chmod","chown","link"):
                res["t_type"] = query["t_type"]
            else:
                err += "查询项：触发方式，设置错误\n"
        if not "user" in query: pass
        elif query["user"] not in self._get_sys_user():
            err += "查询项：用户，设置错误\n"
        else:
            res["user"] = query["user"]

        if "proc" in query and query["proc"]:
            tmp = query["proc"].strip()
            res["proc"] = tmp if bool(tmp) else None
        
        query = res
        return err 

    def get_logs(self,args=None, path_id=None):
        '''
            @name 获取日志
            @author baozi<2023-03-22>
            @param path_id<int> 日志路径ID
            @return list
        '''
        rows = 10
        p = 1
        query = None
        date = None
        if args:
            if 'path_id' in args: path_id = int(args.get("path_id"))
            if 'p' in args: p = int(args.get("p"))
            if 'rows' in args: rows = int(args.get("rows"))
            if 'date' in args: date = args.get("date")
            if 'query' in args: query = args.get("query")
        if query and isinstance(query, str):
            query = json.loads(query)
        if not query or not isinstance(query, dict):
            query = {}
        err = self._check_query(query)
        if err:
            return public.returnMsg(False, err)
        if path_id == None: return public.returnMsg(False,"参数错误")
        path_info = self.get_tamper_path_find(path_id=path_id)
        if not path_info: return public.returnMsg(False,"指定目录配置不存在")

        log_path = "{}/{}".format(self.__logs_path, path_id)
        if not os.path.exists(log_path) or not os.path.isdir(log_path):
            return []
        today= time.strftime('%Y-%m-%d', time.localtime())
        if date == "query":
            log_files = self._get_log_files(log_path)
        elif  not date:
            log_files = ["{}/{}.log".format(log_path, today),]
        else:
            log_files = ["{}/{}.log".format(log_path, date),]

        result = []
        logcontent = self._get_log_content(p, rows, log_files)
        logcontent.set_args(**query)
        for i in logcontent:
            result.append(i)
        
        page = public.get_page(logcontent.count, p=p,rows=rows)
        for i in range(len(result)):
            _info = {
                "date": result[i][0],
                "type": result[i][1],
                "content":result[i][2],
                "user": result[i][3],
                "process": result[i][4]
            }
            result[i] = _info
        page["data"] = result
        page["size"] = self._get_log_size(log_path)
        page["dates"] = [i.strip(".log") for i in os.listdir(log_path)]
        page["dates"].sort(reverse=True)
        if  today != page["dates"][0]:
            page["dates"].insert(0, today)
        return page

    def _get_sys_user(self):
        """获取所有用户名
        @author baozi <202-03-23>
        @param: 
        @return 
        """
        user_set = set()
        with open('/etc/passwd') as fp:
            for line in fp.readlines():
                user_set.add(line.split(':', 1)[0])
        
        return user_set
    
    def _get_log_size(self, log_path):
        size=0
        for i in glob.glob(log_path + "/*.log"):
            size+=os.path.getsize(i)
        return public.to_size(size)


    # 获取使用天数记录
    def _get_use_day(self):
        day_file = "{}/date.pl".format(self.__tamper_path)
        if not os.path.exists(day_file):
            public.writeFile(day_file, f'{int(time.time())}\n0\n')
            return 1
        last, sum = public.readFile(day_file).split("\n")[:2]
        try:
            if last.isdecimal():
                sum = int(time.time()) - int(last) + int(sum)
            else:
                sum = int(sum)
            day = int(sum/(60*60*24)) + 1
            return day
        except:
            return day
        
    def del_logs(self, args=None, path_id=None, date=None, before=False):
        '''
            @name 删除日志
            @author baozi<2023-03-22>
            @param path_id<int> 日志路径ID
            @return list
        '''
        date = None
        if args:
            if 'path_id' in args: path_id = int(args.get("path_id"))
            if 'date' in args: date = args.get("date")
            if 'before' in args: before = args.get("before")
        if path_id == None: return public.returnMsg(False,"参数错误")
        path_info = self.get_tamper_path_find(path_id=path_id)
        if not path_info: return public.returnMsg(False,"指定目录配置不存在")
        try:
            date = date.strip()
            time.strptime(date, '%Y-%m-%d')
        except:
            return public.returnMsg(False,"指定目录配置不存在")

        if bool(before):
            files = self._get_log_files(self.__logs_path + '/' + str(path_id), date)
            del_msg = ''
            for i in files:
                os.remove(i)
            if len(files) >= 2:
                del_msg = files[-1][-14:-4] + '至' + files[0][-14:-4]
            elif len(files) == 1:
                del_msg = files[0][-14:-4]
            else:
                return {"status":True, "msg":"没有指定日期的日志"}
        else:
            files = "{}/{}/{}.log".format(self.__logs_path, path_id, date)
            if os.path.exists(files):
                del_msg = date
                os.remove(files)
            else:
                return {"status":True, "msg":"没有指定日期的日志"}
            
        public.WriteLog("防篡改","保护目录: {}删除了{}的日志".format(path_info["path"], del_msg))
        return {"status":True, "msg":"删除成功"}


    def set_frequent_process(self, args=None, proc_name=None, ps=""):
        '''
         @proc_name 进程名
        '''
        if args:
            if 'proc_name' in args: proc_name = args.get("proc_name")
            if 'ps' in args: ps = args.get("ps")
        config = self.read_config()
        if not proc_name:
            return {"status": False, "msg":"进程名不能为空"}
        if not ps:
            ps = ""
        for i in config["frequent_process"]:
            if i["name"] == proc_name:
                i["ps"] = ps
                break
        else:
            if proc_name not in config["process_names"]:config["process_names"].append(proc_name)
            config["frequent_process"].append({"name": proc_name, "ps":ps})
        
        self.save_config(config)

        return {"status": True, "msg":"设置成功"}

    def del_frequent_process(self, args=None, proc_name=None, ps=""):
        '''
         @proc_name 进程名
        '''
        if args:
            if 'path_id' in args: path_id = int(args.get("path_id"))
            if 'proc_name' in args: proc_name = args.get("proc_name")
            if 'ps' in args: ps = args.get("ps")
        if path_id == None: return public.returnMsg(False,"参数错误")
        config = self.read_config()
        rule = None
        for i in config["paths"]:
            if i["pid"] == path_id:
                rule = i
        if not rule:
            return public.returnMsg(False,"指定目录配置不存在")
        if not proc_name:
            return {"status": False, "msg":"进程名不能为空"}
        if not ps:
            ps = ""
        for i in range(len(config["frequent_process"])-1, -1, -1):
            if config["frequent_process"][i]["name"] == proc_name:
                del config["frequent_process"][i]
                if proc_name in config["process_names"]:
                    config["process_names"].remove(proc_name)

        self.save_config(config)

        return {"status": True, "msg":"设置成功"}
    
    def attack(self, args=None, path_id=None):
        if args:
            if 'path_id' in args: path_id = int(args.get("path_id"))
        if path_id == None: return public.returnMsg(False,"参数错误")
        config = self.read_config()

        rule = None
        for i in config["paths"]:
            if i["pid"] == path_id:
                rule = i
        if not rule:
            return public.returnMsg(False,"指定目录配置不存在")
        if not (bool(rule["status"]) and bool(config["status"])): return public.returnMsg(False,"没有打开防篡改，无法测试。")
        res = self._check_white_dirs(rule["path"], rule["white_dirs"])
        if res:
            return {"status": False, "msg":"白名单文件夹中存在匹配当前保护目录的项目，这导致该目录下所有文件均未加入保护，无法测试。", "white_dirs": res}
        acts = [
            "is_mkdir",   # ---> 所有情况都可以测试
            "is_create",  # ----> 需要有保护的黑名单
            "is_link",    # ----> 需要有保护的黑名单 并且需要启用一个白名单进程生成有个被保护的文件供模拟的攻击者操作
            "is_chmod",
            "is_chown",
            "is_rename",
            "is_modify",
            "is_unlink",
            "is_rmdir"
        ]
        random_name = self._random_name()
        attack_config = {"attack_process": random_name, "base_path": rule["path"]}
        for i, act in enumerate(acts):
            if rule[act] == 1:
                attack_config["type"] = act
                if i == 0:
                    attack_config["dir"] = "{}{}".format(rule["path"], random_name)
                    return self._do_attack(attack_config, config)
                else:
                    break
        else:
            return {"status": False, "msg":"基础设置中未开启任何保护规则，无法测试。"}
        
        ext, file_path = None, []
        for i in rule["black_exts"]:
            if i[0] == "." and i.find("/") == -1:
                ext = i
            else:
                file_path.append(i)
        
        attack_config["dir"] = "{}{}".format(rule["path"], random_name)
        if ext:
            attack_config["file"] = "{}{}{}".format(rule["path"], random_name, ext)
            return self._do_attack(attack_config, config)
        
        if not file_path:
            return {"status": False, "msg":"没有设置任何受保护的后缀，无法测试。"}
        
        file_path.sort(key=lambda x :len(x))
        ext = file_path[0]
        if ext[0] != "/":
            random_name += "/"
        attack_config["file"] = "{}{}{}".format(rule["path"], random_name, ext)
        return self._do_attack(attack_config, config)
    
    def _random_name(self):
        from uuid import uuid4
        return uuid4().hex[::4]


    def _do_attack(self, attack_config, config):
        prep_process = self._random_name()
        atk_user = "tmaper" + self._random_name()
        attack_config.update(prep_process=prep_process)    
        self._change_permission(attack_config["base_path"], atk_user, True)

        from tamper_attack import Attack, PrepareAttack, clean
        config["process_names"].append(prep_process)
        self.save_config(config)
        if os.path.exists(self.__tips_file):
            while True:
                time.sleep(0.01)
                if not os.path.exists(self.__tips_file):
                    time.sleep(0.1)
                    break
        
        atk_file_path = "{}/plugin/tamper_core/tamper_attack.py".format(public.get_panel_path())
        public.ExecShell(PrepareAttack.set_prep_sh(attack_config, atk_file_path), user=atk_user)
        public.ExecShell(Attack.do_attack_sh(attack_config, atk_file_path), user=atk_user)
        res = public.readFile("/tmp/{}.log".format(attack_config["attack_process"]))
        if res == "ok\n":
            flag = True
        else:
            flag = False
        public.ExecShell(PrepareAttack.remove_prep_sh(attack_config, atk_file_path), user=atk_user)
        clean(attack_config)

        self._change_permission(attack_config["base_path"], atk_user, False)
        config["process_names"].remove(prep_process)
        self.save_config(config)

        return {"status": flag, "msg":"已进行模拟攻击", "attack_msg": self._show_attack(attack_config, atk_user, flag)}
    
    def _show_attack(self, attack_config, atk_user, flag):
        acts = {
            "is_mkdir":'创建文件夹',   
            "is_create":'创建文件',  
            "is_link":'创建软链接',   
            "is_chmod":'修改文件权限',
            "is_chown":'修改所有者',
            "is_rename":'重命名',
            "is_modify":'修改文件内容',
            "is_unlink":'删除文件',
            "is_rmdir":'删除文件'
        }
        act_type = "尝试攻击方式：{}".format(acts[attack_config["type"]])
        prep = "准备阶段：创建测试用户[{}]".format(atk_user)
        if attack_config["type"] not in ("is_mkdir", "is_create"):
            prep += "，创建测试文件夹[{}]和测试文件[{}]".format(attack_config["dir"], attack_config["file"])
        attack = "攻击内容：使用测试用户运行测试程序[{}]执行{}操作".format(attack_config["attack_process"], acts[attack_config["type"]])
        end = "攻击结果：" + ("该次攻击已被拦截，防御成功" if flag else "该次攻击未拦截成功，请尽快联系官方解决问题" )

        return act_type, prep, attack, end, "结束阶段：清除本次测试中的所有临时文件"
    
    def _change_permission(self, base_path, user, add_perm=True):
        python_path = "{}/pyenv/bin".format(public.get_panel_path())
        if add_perm:
            public.ExecShell('useradd -s /sbin/nologin {}'.format(user))
            public.ExecShell('setfacl -m u:{}:--x {}'.format(user, python_path))
            public.ExecShell('setfacl -m u:{}:--x {}'.format(user, python_path + "/python3.7"))
            tmp_path = ''
            for i in base_path.split("/")[1:-1]:
                tmp_path += f"/{i}"
                public.ExecShell('setfacl -m u:{}:rwx {}'.format(user, tmp_path))
        else:
            tmp_path = ''
            for i in base_path.split("/")[1:-1]:
                tmp_path += f"/{i}"
                public.ExecShell('setfacl -b {}'.format(tmp_path))
            public.ExecShell('setfacl -b {}'.format(python_path))
            public.ExecShell('setfacl -b {}'.format(python_path + "/python3.7"))
            public.ExecShell('userdel -r {}'.format(user))

    def set_white_dir_with_ps(self, args=None, path_id=None, dir_name=None, ps=""):
        '''
         @dir_name 白名单文件夹
        '''
        if args:
            if 'dir_name' in args: dir_name = args.get("dir_name")
            if 'ps' in args: ps = args.get("ps")
            if 'path_id' in args: path_id = int(args.get("path_id"))
        if path_id == None: return public.returnMsg(False,"参数错误")
        config = self.read_config()

        rule = None
        for i in config["paths"]:
            if i["pid"] == path_id:
                rule = i
        if not rule:
            return public.returnMsg(False,"指定目录配置不存在")
        if not dir_name:
            return {"status": False, "msg":"白名单目录不能为空"}
        if not ps:
            ps = ""
        dis_ps_name = "dir_ps_" + str(rule["pid"])
        if dir_name in config[dis_ps_name]:
            config[dis_ps_name][dir_name] = ps
        else:
            if dir_name not in rule["white_dirs"]: rule["white_dirs"].append(dir_name)
            config[dis_ps_name][dir_name] = ps
        
        self.save_config(config)

        return {"status": True, "msg":"设置成功"}

    def del_white_dir_with_ps(self, args=None, path_id=None, dir_name=None):
        '''
         @dir_name 白名单文件夹
        '''
        if args:
            if 'dir_name' in args: dir_name = args.get("dir_name")
            if 'path_id' in args: path_id = int(args.get("path_id"))
        if path_id == None: return public.returnMsg(False,"参数错误")
        config = self.read_config()
        rule = None
        for i in config["paths"]:
            if i["pid"] == path_id:
                rule = i
        if not rule:
            return public.returnMsg(False,"指定目录配置不存在")
        if not dir_name:
            return {"status": False, "msg":"白名单目录不能为空"}

        dis_ps_name = "dir_ps_" + str(rule["pid"])
        if dir_name in config[dis_ps_name]:
            config[dis_ps_name].pop(dir_name)
            if dir_name in rule["white_dirs"]:
                rule["white_dirs"].remove(dir_name)
        
        self.save_config(config)

        return {"status": True, "msg":"设置成功"}
    
    def get_sites_path(self, args=None):
        """获取站点的路径
        @author baozi <202-03-23>
        @return 
        """

        sites_data = public.M("sites").field("name,path,project_type").select()
        config = self.read_config()
        res = []
        use_path = {i["path"] for i in config["paths"]}
        for i in sites_data:
            if i["project_type"] in ("Go", "Other"):
                i["path"] = i['path'].rsplit("/", 1)[0]  # Go 和 Other 项目的路径是运行文件的路径
            if i["project_type"] == "Java" and os.path.isfile(i["path"]):
                i["path"] = i['path'].rsplit("/", 1)[0]  # springboot 项目的路径是运行文件的路径
            
            # 规范路径
            if i["path"][-1] != "/":
                i["path"] += "/"

            if i["path"] not in use_path:
                i["can_create"] = True
            else:
                i["can_create"] = False
            res.append(i)
        res.sort(key=lambda x: int(x["can_create"]), reverse=True)
        return res
    
    def multi_create(self, args=None, paths=[]):
        """一次性添加多个目录的防篡改
        @author baozi <202-03-23>
        @param: 
            args ( _type_ )  (default: None )
                : _description_ 
            path ( list )  (default: [] )
                : 要添加的目录 
        @return 
        """

        if args:
            if 'paths' in args:
                paths = args.get("paths")

        if not paths:
            return public.returnMsg(False, "没有文件路径")
        else:
            if isinstance(paths, str) and paths[0] == "[":
                paths = json.loads(paths)
            elif not isinstance(paths, list):
                return public.returnMsg(False, "文件路径错误")
        
        res = [{
                "pid": None,
                "path": i["path"] if i["path"][-1] == "/" else i["path"] + "/" ,
                "ps": i["ps"],
                "msg": "目录添加成功",
                "status": True
            } for i in paths]
        
        config = self.read_config()
        use_path = {i["path"] for i in config["paths"]}
        start_pid = self.get_path_id(config["paths"])
        for i in res:
            i["path"] = i["path"].replace('//','/')
            if i["path"] in use_path:
                i["status"] = False
                i["msg"] = "已存在的目录，无法重复添加"
                continue
            flag, msg = self._create_path_for_multi(start_pid + 1, i["path"], config, i["ps"])
            if flag:
                start_pid += 1
                i["pid"] = start_pid
                i["rule"] = msg
            else:
                i["status"] = False
                i["msg"] = msg
        
        self.save_config(config)

        return res
    
    def _create_path_for_multi(self, pid, path, config, ps = ""):
        # 路径标准化处理
        if path[-1] != "/": path += "/"
        path = path.replace('//','/')

        # 参数过滤
        if not path: return False, "目录路径不能为空"
        if not os.path.exists(path) or os.path.isfile(path): return False, "无效的目录: {}".format(path)

        # 关键路径过滤
        if path in ['/','/root/','/boot/','/www/','/www/server/','/www/server/panel/','/www/server/panel/class/','/usr/','/etc/','/usr/bin/','/usr/sbin/']:
            return public.returnMsg(False,"不能添加系统关键目录: {}".format(path))

        path_info = {
            "pid":pid,
            "path":path,
            "status":1,
            "mode":0,
            "is_create":1,
            "is_modify":1,
            "is_unlink":1,
            "is_mkdir":1,
            "is_rmdir":1,
            "is_rename":1,
            "is_chmod":1,
            "is_chown":1,
            "is_link":1,
            "black_exts": config["default_black_exts"],
            "white_files": config["default_white_files"],
            "white_dirs": config["default_white_dirs"],
            "ps": ps
        }

        # 添加到配置列表
        config["paths"].append(path_info)
        config["dir_ps_" + str(path_info["pid"])] = {}
        public.WriteLog("防篡改","添加目录配置: {}".format(path))
        return True, path_info
    
    def get_frequent_process(self, args=None):
        config = self.read_config()
        res = config["frequent_process"]

        for i in res:
            if i["name"] in config["process_names"]:
                i["status"] =True
            else:
                i["status"] =False
            
        return res
