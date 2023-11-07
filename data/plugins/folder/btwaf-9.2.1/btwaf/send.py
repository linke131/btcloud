#coding: utf-8
import os,sys
sys.path.insert(0,"/www/server/panel/class/")
os.chdir('/www/server/panel')
import json,time
import public,PluginLoader
import totle_db2
class send:
    __PATH = '/www/server/panel/plugin/btwaf/'


    def start(self):

        self.Start_Alarm()
        return False

    def M2(self, table):
        with totle_db2.Sql() as sql:
            return sql.table(table)

    def Get_Alarm(self,get):
        '''
            @name 获取告警设置
        '''
        try:
            if not os.path.exists("data/btwaf_alarm.json"):
                self.Set_Alarm(None)
            info=json.loads(public.readFile("data/btwaf_alarm.json"))
            return info
        except:
            self.Set_Alarm(None)
            return json.loads(public.readFile("data/btwaf_alarm.json"))


    #设置告警
    def Set_Alarm(self,get):
        pdata={}
        if 'cc' not in get:
            pdata['cc']={"cycle":120,"limit":30,"status":False}
        else:
            pdata['cc'] = json.loads(get.cc)
        if 'file' not in get:
            pdata['file']={"cycle":120,"limit":60,"status":False}
        else:
            pdata['file'] = json.loads(get.file)
        #新版本
        if 'version' not in get:
            pdata['version']={"status":False}
        else:
            pdata['version'] = json.loads(get.version)

        if 'webshell' not in get:
            pdata['webshell']={"status":False}
        else:
            pdata['webshell'] = json.loads(get.vul)

        if 'vul' not in get:
            pdata['vul']={"status":False}
        else:
            pdata['vul'] = json.loads(get.vul)

        if 'send' not in get:
            pdata['send']={"status":False,"send_type":"error"}
        else:
            pdata['send'] = json.loads(get.send)

        public.WriteFile("data/btwaf_alarm.json",json.dumps(pdata))
        return public.returnMsg(True, '设置成功')


    def send_mail_data(self,title,body,login_type):
        try:
            object = public.init_msg(login_type.strip())
            if not object:
                return False
            if login_type=="mail":
                data={}
                data['title'] = title
                data['msg'] = body
                object.push_data(data)
            elif login_type=="wx_account":
                object.send_msg(body)
            else:
                msg = public.get_push_info(title,['>发送内容：' + body])
                public.WriteLog("WAF防火墙消息通知", msg)
                object.push_data(msg)
        except:
            pass

    #开启告警
    def Start_Alarm(self):
        try:
            info = json.loads(public.readFile("data/btwaf_alarm.json"))
        except:
            info = self.Get_Alarm(None)
        #告警类型是否开启
        if info['send']['send_type']=='error':return False
        if info['send']['status']:
            #获取CC攻击告警
            cc_status,cc_info=self.Get_CC_Alarm(info['cc'])
            if cc_status:
                title="宝塔防火墙-CC攻击告警"
                body=cc_info
                self.send_mail_data(title,body,info['send']['send_type'])
            #获取封锁IP总数告警
            file_status,file_info=self.Get_File_Alarm(info['file'])
            if file_status:
                title="宝塔防火墙-封锁IP数量"
                body=file_info
                self.send_mail_data(title,body,info['send']['send_type'])
            #获取版本更新告警
            version_status,version_info=self.Get_Version_Alarm(info['version'])
            if version_status:
                title="宝塔防火墙版本更新"
                self.send_mail_data(title,version_info,info['send']['send_type'])
            #获取发现木马告警
            webshell_status,webshell_info=self.Get_Webshell_Alarm(info['webshell'])
            if webshell_status:
                title="宝塔防火墙木马文件告警"
                body=webshell_info
                self.send_mail_data(title,body,info['send']['send_type'])
            #获取安全漏洞通知告警
            vul_status,vul_info=self.Get_Vul_Alarm(info['vul'])
            if vul_status:
                title="漏洞情报预警"
                body=vul_info
                print(vul_info)
                self.send_mail_data(title,body,info['send']['send_type'])
        return True

    #获取CC攻击告警
    def Get_CC_Alarm(self,info):
        if info['status']==False:return False,""
        if os.path.exists("data/btwaf_cc_send.time"):
            last_time=float(public.readFile("data/btwaf_cc_send.time"))
            if info['cycle']<60:info['cycle']=60
            if time.time()-last_time<info['cycle']:
                return False,""
        public.writeFile("data/btwaf_cc_send.time",str(time.time()))
        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
            try:
                if self.M2('blocking_ip').order('id desc').count() == 0: return False,""
            except:
                return False,""
            count=self.M2('blocking_ip').order('id desc').where('time>? and filter_rule=?',(time.time()-info['cycle'],"cc")).count()
            if count>info['limit']:
                #获取排行top10
                ip_list=[]
                infos = self.M2('blocking_ip').order('id desc').where('time>? and filter_rule=?',(time.time() - info['cycle'],"cc")).select()
                for info2 in infos:
                    ip_list.append(info2['ip'])
                ip_list=list(set(ip_list))
                #top10
                if len(ip_list)>10:
                    ip_list=ip_list[:10]
                resutl_info="宝塔防火墙提醒您，已拦截到CC攻击\r\n %s秒内 拦截%s次，\r\n攻击IP排行TOP10：\r\n"%(info['cycle'],count)
                ip='\r\n'.join(ip_list)
                resutl_info+=ip+"\r\n 如打开网站比较慢建议开启CC增强模式、如果已开启则忽略此告警。\r\n当前告警行为10分钟内不再发送。"
                #+10分钟
                public.writeFile("data/btwaf_cc_send.time", str(time.time()+600))
                return True,resutl_info
        return False,""

    #封锁次数告警
    def Get_File_Alarm(self,info):
        if info['cycle'] < 60: info['cycle'] = 60
        if info['status']==False:return False,""
        if os.path.exists("data/btwaf_file_send.time"):
            last_time=float(public.readFile("data/btwaf_file_send.time"))
            if info['cycle']<60:info['cycle']=60
            if time.time()-last_time<info['cycle']:
                return False,""
        public.writeFile("data/btwaf_file_send.time",str(time.time()))
        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
            try:
                if self.M2('blocking_ip').order('id desc').count() == 0: return False,""
            except:
                return False,""
            count = self.M2('blocking_ip').order('id desc').where('time>?',(time.time() - info['cycle'])).count()
            if count > info['limit']:
                infos=self.M2('blocking_ip').order('id desc').where('time>?',(time.time() - info['cycle'])).select()
                #获取排行top10
                ip_list=[]
                for info2 in infos:
                    ip_list.append(info2['ip'])
                    if len(ip_list)>10:
                        break
                resutl_info="\r\n宝塔防火墙提醒您，封锁次数告警\r\n %s秒 拦截数量为%s，\r\n攻击IP排行TOP10：\r\n"%(info['cycle'],len(infos))
                ip='\r\n'.join(ip_list)
                resutl_info+=ip+"\r\n当前这些IP已经被防火墙拦截、如攻击的IP较多、建议可以把某些IP段加入到系统防火墙中、\r\n10分钟内不再发送封锁总数告警信息"
                public.writeFile("data/btwaf_cc_send.time", str(time.time() + 600))
                return True,resutl_info
        return False,""

    #获取版本更新告警
    def Get_Version_Alarm(self,info):
        # {"status":True}
        if info['status']==False:return False,""
        import panelPlugin
        #上一次检测的时间。要隔一天检测一次
        if os.path.exists("data/btwaf_version.time"):
            last_time=float(public.readFile("data/btwaf_version.time"))
            if time.time()-last_time<86400:
                return False,""
        public.writeFile("data/btwaf_version.time",str(time.time()))
        p = panelPlugin.panelPlugin()
        get=public.dict_obj()
        get.show=1
        get.plugin_name="btwaf"
        infos=p.get_plugin_upgrades(get)
        p_version=infos[0]
        version=p_version['m_version']+"."+p_version['version']
        #本地版本
        local_version=json.loads(public.readFile("/www/server/panel/plugin/btwaf/info.json"))['versions']
        if version!=local_version:
            #版本有更新
            return True,"\r\n防火墙版本有更新，\r\n当前版本："+local_version+"，\r\n最新版本："+version+" \r\n更新内容如下: "+p_version['update_msg']
        return False,""

    #获取发现木马告警
    def Get_Webshell_Alarm(self,info):
        #十分钟一次
        if os.path.exists("data/btwaf_shell_send.time"):
            last_time=float(public.readFile("data/btwaf_shell_send.time"))
            if time.time()-last_time<600:
                return False,""
        if info['status']==False:return False,""
        Webshell_Alarm = self.__PATH + 'Webshell_Alarm.json'
        try:
            webshell_list=json.loads(public.ReadFile(Webshell_Alarm))
            if len(webshell_list)>0:
                public.WriteFile(Webshell_Alarm,"[]")
                return True,"\r\n宝塔防火墙提醒您，发现木马文件，\r\n木马文件列表如下：\r\n"+'\r\n'.join(webshell_list)+" \r\n所有文件已拉入隔离区，如有误报请手动恢复。10分钟内不再发送木马告警信息"
            return False,""
        except:
            return False,""

    #获取安全漏洞通知告警
    def Get_Vul_Alarm(self,info):
        if info['status']==False:return False,""
        #上一次检测的时间。要隔一天检测一次
        if os.path.exists("data/btwaf_vul.time"):
            last_time=float(public.readFile("data/btwaf_vul.time"))
            if time.time()-last_time<86400:
                return False,""
        public.writeFile("data/btwaf_vul.time",str(time.time()))

        #从云端获取数据
        try:
            url="https://www.bt.cn/api/bt_waf/getVulScanInfoList"
            user_info=public.get_user_info()
            data=public.httpPost(url,data={"uid":user_info["uid"],"serverid":user_info["serverid"],"access_key":user_info["access_key"]})
            data=json.loads(data)
            into=""
            nonce=data['nonce']
            for i in data['res']:
                #如果是一天内的数据
                if nonce-i['addtime']<86400:
                    #如果是未修复的
                    into+="\r\n"+"CVE编号："+i['cve_id']+"\r\n漏洞名称:"+i['name']+" \r\n漏洞介绍：\r\n"+i['info']+" \r\n漏洞详情：\r\n"+i['msg']
            if into!="":
                return True,"宝塔安全漏洞预警  漏洞列表如下："+into
            return False,""
        except:
            return False,""