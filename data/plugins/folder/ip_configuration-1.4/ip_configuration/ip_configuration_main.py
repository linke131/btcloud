#!/usr/bin/python
# coding: utf-8
# +------------------------------------------------------------------
# | ip配置工具平台客户端
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hezhihong <272267659@qq.com>
# +-------------------------------------------------------------------
from __future__ import absolute_import, print_function, division

import os
import yaml
import re
import sys
import time
import sqlite3



BASE_PATH = "/www/server/panel"

os.chdir(BASE_PATH)
sys.path.insert(0, "class/")

import public


_ver = sys.version_info
#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)

if is_py2:
    reload(sys)
    sys.setdefaultencoding('utf-8')


class ip_configuration_main:
    
    def get_system(self):
        system_type_file_path = '/etc/os-release'
        system_type_list = []
        system_version_list = []
        linux_sys_type = ''
        system_type = ''
        if not os.path.exists(system_type_file_path):
            return public.returnMsg(True, '配置文件不存在')
        with open(system_type_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(system_type_file_path, "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value = 'VERSION='
                if tmp_value in line:
                    system_version_list.append(line)
                tmp_value = 'PRETTY_NAME='
                if tmp_value in line:
                    system_type_list.append(line)
                f_w.write(line)
        #以下代码暂时弃用
        # if system_type_list = []:
        #     with open(system_type_file_path, "r", encoding="utf-8") as f:
        #         lines = f.readlines()
        #     with open(system_type_file_path, "w", encoding="utf-8") as f_w:
        #         for line in lines:
        #             tmp_value = 'NAME='
        #             if tmp_value in line:
        #                 system_type_list.append(line)
        #             f_w.write(line)
            
        if 'Ubuntu' in system_type_list[0]:
            linux_sys_type = 'ubuntu'
        elif 'ubuntu' in system_type_list[0]:
            linux_sys_type = 'ubuntu'
        elif 'CentOS' in system_type_list[0]:
            linux_sys_type = 'centos'
        elif 'centos' in system_type_list[0]:
            linux_sys_type = 'centos'
        elif 'Debian' in system_type_list[0]:
            linux_sys_type = 'debian'
        elif 'debian' in system_type_list[0]:
            linux_sys_type = 'debian'
        else:
            linux_sys_type = ''

        if linux_sys_type == 'ubuntu':     
            if '18' in  system_version_list[0]:
                system_type = 'ubuntu'
            elif '20' in  system_version_list[0]:
                system_type = 'ubuntu'
                print(system_type)
            else:
                system_type = ''
        elif linux_sys_type == 'centos':
            if '7' in  system_version_list[0]:
                system_type = 'centos'
            else:
                system_type = ''
        elif linux_sys_type == 'debian':
            if '10' in system_version_list[0]:
                system_type = 'debian'
            else:
                system_type = ''
        elif linux_sys_type == '':
            system_type = ''
        else:
            system_type = ''
        return system_type

    def get_default_netmask_value(self,dev_name):
        """
        取子网掩码值并自动计算子网掩码,IP值,网络位
        netmask_value为子网掩码值，如255.255.255.0
        netmask_num为网络位，如127.16.0.16/24中的24
        ip_value为IP值，如172.16.0.16
        dev_name为网卡名称，如eth0
        """
        if dev_name == '':
            dev_name = public.ExecShell("ip add |grep LOWER_UP|grep -v lo|sed 's/://g'|awk '{print $2}'")[0].split()[0].strip()
        tmp_exec = 'ip add | grep ' + dev_name + ' |grep inet'
        try:
            tmp_exec = str(public.ExecShell(tmp_exec)).split()[2].strip()
            netmask_num = tmp_exec.split('/')[1].strip()
            ip_value = tmp_exec.split('/')[0].strip()
        except:
            tmp_exec = ''
            netmask_num = ''
            ip_value = ''
        netmask_value = ''
        if netmask_num != '':
            netmask_value=self.netmask_num_to_netmask_value(netmask_num=netmask_num)
        else:
            netmask_value = ''
        return netmask_value, netmask_num, ip_value, dev_name
        
        
    def netmask_num_to_netmask_value(self,netmask_num):
        if netmask_num:
            tmp_valuelist = {}
            tmp_value = 'tmp_value'
            tmp_valuelist['tmp_value1'] = '128'
            tmp_valuelist['tmp_value2'] = '192'
            tmp_valuelist['tmp_value3'] = '224'
            tmp_valuelist['tmp_value4'] = '240'
            tmp_valuelist['tmp_value5'] = '248'
            tmp_valuelist['tmp_value6'] = '252'
            tmp_valuelist['tmp_value7'] = '254'
            tmp_valuelist['tmp_value8'] = '255'
            if int(netmask_num) <= 8:
                tmp_value = tmp_value + netmask_num
                netmask_value = tmp_valuelist[tmp_value] + '.0.0.0'
            elif int(netmask_num) > 9 and int(netmask_num) <= 16:
                tmp_value = tmp_value + str(int(netmask_num) - 8)
                netmask_value = '255.' + tmp_valuelist[tmp_value] + '.0.0'
            elif int(netmask_num) > 16 and int(netmask_num) <= 24:
                tmp_value = tmp_value + str(int(netmask_num) - 16)
                netmask_value = '255.255.' + tmp_valuelist[tmp_value] + '.0'
            elif int(netmask_num) > 24 and int(netmask_num) <= 32:
                tmp_value = tmp_value + str(int(netmask_num) - 24)
                netmask_value = '255.255.255.' + tmp_valuelist[tmp_value]
        return netmask_value

    def intranet_or_extranet(self, ip_address):
        """
        服务器本机内外网IP映射绑定区分
        ip_address:
        传入的IP地址，如172.16.0.1

        net_type:
        内网绑定方式返回Intranet
        外网绑定方式返回Extranet
        """
        tmp_c = ip_address.split('.')[0]
        tmp_d = ip_address.split('.')[1]
        if int(tmp_c) == 10:
            net_type = 'intranet'
        elif int(tmp_c) == 172:
            if int(tmp_d) >= 16 and int(tmp_d) <= 31:
                net_type = 'intranet'
            else:
                net_type = 'extranet'
        elif int(tmp_c) == 192:
            if int(tmp_d) == 168:
                net_type = 'intranet'
            else:
                net_type = 'extranet'
        else:
            net_type = 'extranet'
        return net_type
        
    def get_ubuntu_conf_file(self):
        """
        ubuntu取网卡配置文件路径
        返回值：
        confpath  ubuntu配置文件绝对路径
        """
        netmask_value, netmask_num, ip_value, dev_name = self.get_default_netmask_value(dev_name='')
        c_dir = '/etc/netplan/'
        a = public.ExecShell('ls /etc/netplan/')
        b = a[0].strip().split('\n')
        confpath = ''
        tmp_name = ''
        if len(b) > 1:
            for i in range(0, len(b) - 1):
                if b[i][-4:] != 'yaml': continue
                tmp_name = b[i]
                confpath = c_dir + b[i]
                rep = dev_name + ':\s*\\n'
                conf = public.readFile(confpath)
                result = re.search(rep, conf)
                if result:
                    break
        else:
            confpath = c_dir + b[0]
        return confpath

    def check_ip(self, address):
        """
        验证IP合法性

        """
        try:
            if address.find('.') == -1: return False
            iptmp = address.split('.')
            if len(iptmp) != 4: return False
            for ip in iptmp:
                if int(ip) > 255: return False
            return True
        except:
            return False
            
    def check_netmask(self,netmask):
        """
        验证子网掩码是否有效
        有效返回new_net_num，即网络ID位
        无效返回False

        """
        tmp_list_one=['128','192','224','240','248','252','254','255']
        tmp_list_two=['0','128','192','224','240','248','252','254','255']
        check_list = []
        if netmask.split('.')[0] in tmp_list_one:
            check_list.append('True')
        if netmask.split('.')[1] in tmp_list_two:
            check_list.append('True')
        if netmask.split('.')[2] in tmp_list_two:
            check_list.append('True')
        if netmask.split('.')[3] in tmp_list_two:
            check_list.append('True')
        if len(check_list) != 4:
            return False
        if netmask.split('.')[0] != '255':
            if netmask.split('.')[1] != '0':
                return False
        if netmask.split('.')[1] != '255':
            if netmask.split('.')[2] != '0':
                return False  
        if netmask.split('.')[2] != '255':
            if netmask.split('.')[3] != '0':
                return False   
        tmp_dict = {}
        tmp_dict['0'] = '0'
        tmp_dict['128'] = '1'    
        tmp_dict['192'] = '2'
        tmp_dict['224'] = '3'
        tmp_dict['240'] = '4'
        tmp_dict['248'] = '5'
        tmp_dict['252'] = '6'
        tmp_dict['254'] = '7'
        tmp_dict['255'] = '8'
        add_one = int(tmp_dict[netmask.split('.')[0].strip()])
        add_two = int(tmp_dict[netmask.split('.')[1].strip()])
        add_three = int(tmp_dict[netmask.split('.')[2].strip()])
        add_four = int(tmp_dict[netmask.split('.')[3].strip()])
        new_net_num = add_one+add_two+add_three+add_four
        return new_net_num
    
    def get_str_cursor(self,conf_file,str_check):
        """
        获取指定字符串在指定文件的游标
        conf_file    获取游标的文件
        str_check    获取游标的字符串
        """
        conf = public.readFile(conf_file)
        if conf.find(str_check) != -1:
            str_cursor = conf.find(str_check)
        else:
            str_cursor = ''
        return str_cursor
        
        
    def get_check_else(self,dev_name):
        """
        取间隔最近的且大于自身网卡名的字符游标
        如果没有大于自身的网卡名游标，返回空
        返回值
        check_self  自身所在的游标
        check_else  比较字符所在的游标
        """
        confpath = '/etc/network/interfaces'
        str_check = 'auto '+ dev_name
        check_self = self.get_str_cursor(conf_file = confpath,str_check = str_check)
        dev_name_list = self.get_network_card_name_list()
        check_else = ''
        if len(dev_name_list) < 2:
            if dev_name_list[0] == dev_name:
                return check_self,check_else
        conf = public.readFile(confpath)
        tmp_check = []
        for i in range(0,len(dev_name_list)):
            if dev_name == dev_name_list[i]: continue
            if conf.find('auto '+dev_name_list[i]) != -1:
                tmp_check.append(conf.find('auto '+dev_name_list[i]))
        if tmp_check != []:
            if len(tmp_check) < 2:
                if conf.find('auto '+dev_name) < int(tmp_check[0]):
                    check_else = tmp_check[0]
            else:
                tmp_check.append(check_self)
                tmp_check.sort(reverse = True)
                if tmp_check.index(check_self) != 0:
                    check_else = (tmp_check[tmp_check.index(check_self)-1])
        return check_self,check_else
        
        
    def get_new_dev_name(self,dev_name,data):
        """
        取新的配置设备名
        """
        # lines = data.readlines()
        new_dev_name = ''
        conf_file = '/etc/network/interfaces'
        with open(conf_file+'.bak', "w", encoding="utf-8") as f_w:
            f_w.write(data)
        conf = public.readFile(conf_file+'.bak')
        for i in range(0,1000):
            rep = '\n*\s*iface '+dev_name+':'+str(i)+' inet static\s*\n*'
            result = re.search(rep,conf)
            if not result:
                new_dev_name = dev_name+':'+str(i)
                break
        return new_dev_name
        
        
    def debian_check_ip(self,dev_name,check_str,exclude_value):
        """
        debian检测IP是否已添加 
        """
        network_card_bind_ip_list,network_all_list = self.get_network_card_ip_list(network_name = dev_name)
        if exclude_value == '':
            network_all_list = network_all_list 
        else:
            tmp_check = []
            for i in range(0,len(network_all_list)):
                if exclude_value != network_all_list[i]:
                    tmp_check.append(network_all_list[i])
            network_all_list = tmp_check 
        check_value = []
        for i in range(0,len(network_all_list)):
            if check_str == network_all_list[i]:
                check_value.append('True')
        if check_value != []:
            return False
        else:
            return True
        
    def set_ip_address(self, get):
        """
        设置IP主函数

        """
        if get.netmask_add  == '':
            return public.returnMsg(False, '子网掩码不能为空！')
        system_type = self.get_system()
        if system_type == '':
            return public.returnMsg(False, '不支持的操作系统类型！')
        dev_name_list = self.get_network_card_name_list()
        if not self.check_ip(address=get.ip_address_add): return public.returnMsg(False,'IP地址不合法!')
        if get.netmask_add != '':
            if not self.check_ip(address=get.netmask_add): return public.returnMsg(False,'子网掩码不合法!')
        if self.check_netmask(netmask=get.netmask_add) == False: return public.returnMsg(False,'子网掩码无效！')
        if system_type == "centos":
            if self.centos_ip_set(dev_name = get.dev_name,ip_address_add=get.ip_address_add,netmask_add=get.netmask_add) == False:
                return public.returnMsg(False, '指定IP已经添加过！')
        elif system_type == "debian":
            new_net_num = self.check_netmask(netmask=get.netmask_add)
            if self.debian_ip_set(dev_name=get.dev_name,ip_address_add=get.ip_address_add,netmask_add=new_net_num) == False:
                return public.returnMsg(False, '指定IP已经添加过！')
        elif system_type == "ubuntu":
            new_net_num = self.check_netmask(netmask=get.netmask_add)
            if self.ubuntu_ip_set(dev_name=get.dev_name,ip_address_add=get.ip_address_add,netmask_add=new_net_num) == False:
                return public.returnMsg(False, '指定IP已经添加过！')
        self.reload_network()
        return public.returnMsg(True, '添加成功!')
        
    def modify_ip_netmask(self,get):
        """
        编辑IP、子网掩码主函数
        需要前端返回:
        网卡设备名          dev_name 
        修改前ip地址        old_ip
        修改后ip地址        new_ip
        修改前子网掩码      old_netmask
        修改后子网掩码      new_netmask
        
        """
        if get.new_netmask  == '':
            return public.returnMsg(False, '子网掩码不能为空！')
        dev_name_list = self.get_network_card_name_list()
        if not self.check_ip(address=get.new_ip): return public.returnMsg(False,'IP地址不合法!')
        if not self.check_ip(address=get.new_netmask): return public.returnMsg(False,'子网掩码不合法!')
        if self.check_netmask(netmask=get.new_netmask) == False: return public.returnMsg(False,'子网掩码无效！')
        system_type = self.get_system()
        if system_type == '':
            return public.returnMsg(False, '不支持的操作系统类型！')
        if system_type == "centos":
            if self.centos_modify_ip_netmask(dev_name=get.dev_name,old_ip=get.old_ip,old_netmask=get.old_netmask,new_ip=get.new_ip,new_netmask=get.new_netmask) == False:
                return public.returnMsg(False, '提交的信息已存在！')
            self.reload_network()
        elif system_type == "debian":
            if self.debian_modify_ip_netmask(dev_name=get.dev_name,old_ip=get.old_ip,old_netmask=get.old_netmask,new_ip=get.new_ip,new_netmask=get.new_netmask) == False:
                return public.returnMsg(False, '提交的信息已存在！')
            self.reload_network()
        elif system_type == "ubuntu":
            if self.ubuntu_modify_ip_netmask(dev_name=get.dev_name,old_ip=get.old_ip,old_netmask=get.old_netmask,new_ip=get.new_ip,new_netmask=get.new_netmask) == False:
                return public.returnMsg(False, '提交的信息已存在！')
            self.reload_network()
            time.sleep(1)
        return public.returnMsg(True, '编辑成功!')
        
        
    def del_ip_netmask(self, get):
        """
        删除IP、子网掩码主函数
        需要前端返回:
        网卡设备名          dev_name 
        ip地址              ip_value
        子网掩码            netmask_value
        """
        dev_name_list = self.get_network_card_name_list()
        system_type = self.get_system()
        if system_type == '':
            return public.returnMsg(False, '不支持的操作系统类型！')
        if system_type == "centos":
            index_num = self.get_centos_index(dev_name = get.dev_name,old_ip = get.ip_value)
            if self.centos_ip_netmask_del(dev_name = get.dev_name,index_num=index_num,ip_value =get.ip_value,netmask_value = get.netmask_value) == False:
                return public.returnMsg(False, '删除IP、子网掩码失败！')
            self.reload_network()
        elif system_type == "debian":
            if self.debian_ip_netmask_del(dev_name=get.dev_name,ip_value=get.ip_value,netmask_value=get.netmask_value) == False:
                return public.returnMsg(False, '删除IP、子网掩码失败！')
            self.reload_network()
        elif system_type == "ubuntu":
            if self.ubuntu_ip_netmask_del(dev_name=get.dev_name,ip_value=get.ip_value,netmask_value=get.netmask_value) == False:
                return public.returnMsg(False, '删除IP、子网掩码失败！')
            self.reload_network()
        return public.returnMsg(True, '删除IP、子网掩码成功!')
    
    def linux_modify_gateway(self,get):
        """
        修改网关主函数
        """
        if get.new_gateway  == '':
            return public.returnMsg(False, '网关不能为空！')
        if not self.check_ip(address=get.new_gateway): return public.returnMsg(False,'网关不合法!')
        system_type = self.get_system()
        if system_type == '':
            return public.returnMsg(False, '不支持的操作系统类型！')
        if system_type == "centos":
            if self.centos_modify_gateway(dev_name=get.dev_name,new_gateway=get.new_gateway) == False:
                return public.returnMsg(False, '请配置IP后再修改!')
            self.centos_modify_gateway(dev_name=get.dev_name,new_gateway=get.new_gateway)
        elif system_type == "debian":
            self.debian_modify_gateway(dev_name=get.dev_name,new_gateway=get.new_gateway)
        elif system_type == "ubuntu":
            if self.ubuntu_modify_gateway(dev_name=get.dev_name,new_gateway=get.new_gateway) == False:
                return public.returnMsg(False, '请配置IP后再修改!')
            self.ubuntu_modify_gateway(dev_name=get.dev_name,new_gateway=get.new_gateway)
        self.reload_network()
        return public.returnMsg(True, '网关修改成功!')
        
    def get_centos_index(self,dev_name,old_ip):
        """
        centos 取配置索引值
        """
        conf_file = '/etc/sysconfig/network-scripts/ifcfg-'+dev_name
        with open(conf_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(conf_file, "w", encoding="utf-8") as f_w:
            get_index_str = []
            index_num = ''
            get_index_list = []
            for line in lines:
                tmp_value = old_ip
                if tmp_value in line:
                    rep = old_ip+'\d+'
                    result = re.search(rep,line)
                    if not result:
                        rep = '\d+'+old_ip
                        result = re.search(rep,line)
                        if not result:
                            tmp_value = 'IPADDR'
                            if tmp_value in line:
                                get_index_list.append(line)
                f_w.write(line)
            if  get_index_list != []:
                if len(get_index_list) > 1:
                    tmp_index = ''
                    for i in range(0,len(get_index_list)):
                        tmp_a = get_index_list[i].split('\n')[0].split('.')[3]
                        if tmp_a == old_ip.split('.')[3]:
                            get_index_str.append(get_index_list[i])
                else:
                    get_index_str.append(get_index_list[0])
            if get_index_str == []:
                return False
            else:
                index_num = get_index_str[0].split('=')[0].split('ADDR')[1]
        return index_num
        
    def get_modify_index(self,dev_name):
        conf_file = '/etc/sysconfig/network-scripts/ifcfg-'+dev_name
        modify_index_list = []
        with open(conf_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            get_index_list = []
            for line in lines:
                tmp_check_value = 'IPADDR'
                for i in range(0,1000):
                    tmp_value_add = tmp_check_value+str(i)
                    tmp_value = tmp_check_value+str(i)+'='
                    if tmp_value in line:
                        get_index_list.append(tmp_value_add)
            if get_index_list != []:
                if len(get_index_list) > 1:
                    get_index_list = sorted(get_index_list,key = lambda x: ( int(x.split('ADDR')[1]) ))
                    for i in range(0,len(get_index_list)):
                        tmp_dict = {}
                        ii = i
                        if get_index_list[i].split('ADDR')[1] != ii:
                            tmp_dict['old_ipaddr_index'] = get_index_list[i]
                            tmp_dict['new_ipaddr_index'] = 'IPADDR'+str(i)
                            if tmp_dict['old_ipaddr_index'] != tmp_dict['new_ipaddr_index']:
                                modify_index_list.append(tmp_dict)
        return get_index_list
        
    def centos_network_completion(self,dev_name,ip_address_add,netmask_add,gateway_add):
        """
        centos网卡配置文件检查、补全
        """
        #检查配置文件是否存在，不存在则自动创建
        netmask_value, netmask_num, ip_value, dev_namen = self.get_default_netmask_value(dev_name=dev_name)
        default_gateway = str(public.ExecShell('ip route | grep default')).split()[2]
        cfile = '/etc/sysconfig/network-scripts/ifcfg-' + dev_name
        if not os.path.exists(cfile):
            f = open(cfile,'w')
            f.close
        # 网卡配置文件补全
        tmp_check = []
        with open(cfile, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                tmp_value = '# Created by bt on instance boot automatically,do not edit'
                if tmp_value in line:
                    tmp_check.append('True')
                tmp_value = 'IPADDR='
                if tmp_value in line:
                    tmp_check.append('True')
        if len(tmp_check)<2:
            tmp_value = '# Created by bt on instance boot automatically,do not edit'+'\n'
            conf = tmp_value
            tmp_value = 'BOOTPROTO=static'+'\n'
            conf += tmp_value
            tmp_value = 'DEVICE='+dev_name+'\n'
            conf += tmp_value
            tmp_value = 'ONBOOT=yes'+'\n'
            conf += tmp_value
            tmp_value = 'PERSISTENT_DHCLIENT=yes'+'\n'
            conf += tmp_value
            tmp_value = 'TYPE=Ethernet'+'\n'
            conf += tmp_value
            tmp_value = 'USERCTL=no'+'\n'
            conf += tmp_value
            if ip_address_add == '':
                tmp_value = 'IPADDR='+ip_value+'\n'
            else:
                tmp_value = 'IPADDR='+ip_address_add+'\n'
            conf += tmp_value
            if netmask_add == '':
                tmp_value = 'NETMASK='+netmask_value+'\n'
            else:
                tmp_value = 'NETMASK='+netmask_add+'\n'
            conf += tmp_value
            if gateway_add == '':
                tmp_value = 'GATEWAY='+default_gateway+'\n'
                conf += tmp_value
            else:
                pass
            with open(cfile, "w", encoding="utf-8") as f_w:
                f_w.write(conf)
        else:
            pass
        return True
        

    def centos_ip_set(self, dev_name,ip_address_add,netmask_add):
        """
        centos网卡添加IP(兼容多网卡)

        """
        cfile = '/etc/sysconfig/network-scripts/ifcfg-' + dev_name
        dev_name_list = self.get_network_card_name_list()
        netmask_value, netmask_num, ip_value, dev_namen = self.get_default_netmask_value(dev_name=dev_name)
        if dev_name == dev_name_list[0]:
            self.centos_network_completion(dev_name=dev_name,ip_address_add='',netmask_add='',gateway_add = '')
        else:
            net_type = self.intranet_or_extranet(ip_address = ip_address_add)
            if net_type == 'extranet':
                if self.check_extranet_ip(extranet_ip=ip_address_add) == False:
                    return False
            if not os.path.exists(cfile):
                self.centos_network_completion(dev_name=dev_name,ip_address_add=ip_address_add,netmask_add=netmask_add,gateway_add = '1')
                return True
            else:
                tmp_check = []
                with open(cfile, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        tmp_value = '# Created by bt on instance boot automatically,do not edit'
                        if tmp_value in line:
                            tmp_check.append('True')
                        tmp_value = 'IPADDR='
                        if tmp_value in line:
                            tmp_check.append('True')
                if len(tmp_check)<2:
                    self.centos_network_completion(dev_name=dev_name,ip_address_add=ip_address_add,netmask_add=netmask_add,gateway_add = '1')
                    return True
        #IP检测
        net_type = self.intranet_or_extranet(ip_address = ip_address_add)
        if net_type == 'extranet':
            if self.check_extranet_ip(extranet_ip=ip_address_add) == False:
                return False
        if self.get_centos_index(dev_name=dev_name,old_ip=ip_address_add) != False:
            return False
        # 增加IP配置
        conf = public.readFile(cfile)
        tmp_list = []
        tmp_ip_value = ''
        tmp_netmask_value = ''
        for i in range(0,1000):
            tmp_ip_value = 'IPADDR'+str(i)
            tmp_netmask_value = 'NETMASK'+str(i)
            result = re.search(tmp_ip_value, conf)
            if not result:
                ii = str(i)
                tmp_list.append(ii)
                break
        tmp_add_value = '\n'
        if netmask_add == '':
            netmask_add = netmask_value
        tmp_add_value = '\n'
        tmp_add_value += 'IPADDR'+tmp_list[0]+'='+ip_address_add+'\n'
        tmp_add_value += 'NETMASK'+tmp_list[0]+'='+netmask_add+'\n'
        conf += tmp_add_value
        public.writeFile(cfile, conf)
        self.remove_blank_lines(conf_file=cfile)
        return True
        
    
    def centos_modify_ip_netmask(self,dev_name,old_ip,old_netmask,new_ip,new_netmask):
        """
        centos 编辑IP、子网掩码
        """
        if old_ip == new_ip:
            if old_netmask == new_netmask:
                return False
            else:
                pass
        else:
            if self.get_centos_index(dev_name=dev_name,old_ip=new_ip) != False:
                return False
        net_type = self.intranet_or_extranet(ip_address = new_ip)
        if net_type == 'extranet':
            if self.check_extranet_ip(extranet_ip=new_ip) == False:
                return False
        index_num = self.get_centos_index(dev_name=dev_name,old_ip=old_ip)
        conf_file = '/etc/sysconfig/network-scripts/ifcfg-'+dev_name
        with open(conf_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(conf_file, "w", encoding="utf-8") as f_w:
            tmp_ip_index = 'IPADDR'+str(index_num)+'='
            tmp_netmask_index = 'NETMASK'+str(index_num)+'='
            tmp_gateway_index = 'GATEWAY'+str(index_num)+'='
            for line in lines:
                if tmp_ip_index in line:
                    line = line.replace(old_ip,new_ip)
                if tmp_netmask_index in line:
                    line = line.replace(old_netmask,new_netmask)
                # if tmp_gateway_index in line:
                #     continue
                f_w.write(line)
        self.remove_blank_lines(conf_file=conf_file)
        return True
        

    def centos_ip_netmask_del(self,dev_name,index_num,ip_value,netmask_value):
        """
        centos 删除IP、子网掩码
        """
        network_card_lists = self.get_network_card_name_list()
        network_card_bind_ip_list,network_all_list = self.get_network_card_ip_list(network_name = dev_name)
        conf_file = '/etc/sysconfig/network-scripts/ifcfg-'+dev_name
        tmp_ip_index = 'IPADDR'+index_num+'='
        tmp_netmask_index = 'NETMASK'+index_num+'='
        tmp_gateway_index = 'GATEWAY'+index_num+'='
        if dev_name != network_card_lists[0]:
            if len(network_all_list) < 2:
                with open(conf_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open(conf_file, "w", encoding="utf-8") as f_w:
                    for line in lines:
                        if tmp_ip_index in line:
                            continue
                        if tmp_netmask_index in line:
                            continue
                        if tmp_gateway_index in line:
                            continue
                        f_w.write(line)
                self.remove_blank_lines(conf_file=conf_file)
                return True
        elif dev_name == network_card_lists[0]:
            if len(network_all_list) < 3:
                with open(conf_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open(conf_file, "w", encoding="utf-8") as f_w:
                    for line in lines:
                        if tmp_ip_index in line:
                            continue
                        if tmp_netmask_index in line:
                            continue
                        if tmp_gateway_index in line:
                            continue
                        f_w.write(line)
                self.remove_blank_lines(conf_file=conf_file)
                return True
        get_index_list = self.get_modify_index(dev_name=dev_name)
        get_index_max = get_index_list[(len(get_index_list)-1)].split('ADDR')[1]
        tmp_del_value = []
        tmp_dict = {}
        with open(conf_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(conf_file, "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value_one = 'IPADDR'+get_index_max+'='
                tmp_value_two = 'NETMASK'+get_index_max+'='
                tmp_value_three = 'GATEWAY'+get_index_max+'='
                if tmp_value_one in line:
                    tmp_dict['IPADDR'] = line.split('=')[1].strip()
                    continue
                if tmp_value_two in line:
                    tmp_dict['NETMASK'] = line.split('=')[1].strip()
                    continue
                f_w.write(line)
        tmp_del_value.append(tmp_dict)
        if tmp_del_value != []:
            with open(conf_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(conf_file, "w", encoding="utf-8") as f_w:
                for line in lines:
                    if tmp_ip_index in line:
                        line = line.replace(str(ip_value),str(tmp_del_value[0]['IPADDR']))
                    if tmp_netmask_index in line:
                        line = line.replace(str(netmask_value),str(tmp_del_value[0]['NETMASK']))
                    f_w.write(line)
        
        self.remove_blank_lines(conf_file=conf_file)
        return True

    def centos_modify_gateway(self,dev_name,new_gateway):
        """
        centos修改网关
        """
        conf_file = '/etc/sysconfig/network-scripts/ifcfg-'+dev_name
        tmp_check = []
        with open(conf_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                tmp_value = '# Created by bt on instance boot automatically,do not edit'
                if tmp_value in line:
                    tmp_check.append('True')
                tmp_value = 'IPADDR='
                if tmp_value in line:
                    tmp_check.append('True')
        if len(tmp_check)<2:
            return False
        tmp_gateway = 'GATEWAY='
        default_route = self.get_default_route(dev_name=dev_name)
        with open(conf_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        check_value = []
        # with open(conf_file, "w", encoding="utf-8") as f_w:
        #     for line in lines:
        #         rep = '\n*\s*GATEWAY\s*=.*\s*\n*'
        #         result = re.search(rep,line)
        #         if result:
        #             line = line.replace(default_route,new_gateway)
        #             check_value.append('True')
        #         else:
        #             pass
        #         f_w.write(line)
        if check_value == []:
            conf = public.readFile(conf_file)
            conf += '\n'+'GATEWAY='+new_gateway+'\n'
            public.writeFile(conf_file, conf)
        # self.remove_blank_lines(conf_file=conf_file)
        return True
        

    def ubuntu_ip_set(self, dev_name,ip_address_add,netmask_add):
        """
        ubuntu添加IP
        前端需要获取IP，网关使用默认网关
        """
        confpath = self.get_ubuntu_conf_file()
        dev_name_list = self.get_network_card_name_list()
        netmask_value, netmask_num, ip_value, dev_namen = self.get_default_netmask_value(dev_name=dev_name_list[0])
        tmp_a = public.ExecShell('ip route | grep default')[0].split()[2]
        ip_value = ip_value.split('/')[0]
        #网卡配置文件补全
        tmp_conf = public.readFile(confpath)        
        rep = '\n*\s*'+'gateway4'+':\s*.*\s*\n*'#':\s*\d+'+'.'+'\d+'+'.'+'\d+'+'.'+'\d+'+'\s*\n*'
        result = re.search(rep,str(tmp_conf))
        if not result:
            tmp_data = {'network': {'ethernets': {dev_name_list[0]: {'addresses': [ip_value+'/'+str(netmask_num)], 'gateway4': tmp_a}}, 'version': 2}}
            with open(confpath,"w") as f:
                yaml.dump(tmp_data,f,encoding='utf-8')
                f.close()
        if dev_name != dev_name_list[0]:
            rep = '\n*\s*'+dev_name+':\s*\n*'
            result = re.search(rep,str(tmp_conf))
            if not result:
                conf = public.readFile(confpath)
                data = yaml.load(conf,Loader=yaml.FullLoader)
                tmp_value_add = ip_address_add+'/'+str(netmask_add)
                data['network']['ethernets'][dev_name] = {'addresses': [tmp_value_add]}
                # data['network']['ethernets'][dev_name] = {'addresses': [tmp_value_add], 'gateway4': tmp_a}
                with open(confpath,"w") as f:
                    yaml.dump(data,f,encoding='utf-8')
                    f.close()
                return True
        #ip检测
        net_type = self.intranet_or_extranet(ip_address = ip_address_add)
        if net_type == 'extranet':
            if self.check_extranet_ip(extranet_ip=ip_address_add) == False:
                return False
        conf = public.readFile(confpath)
        data = yaml.load(conf,Loader=yaml.FullLoader)
        tmp_data = data['network']['ethernets'][dev_name]['addresses']
        network_card_bind_ip_list,network_all_list = self.get_network_card_ip_list(network_name = dev_name)
        check_tmp_value = []
        if network_all_list == []:
            pass
        else:
            if tmp_data != []:
                for i in range(0,len(tmp_data)):
                    if ip_address_add ==  str(tmp_data[i]).split()[0].split('/')[0]:
                        check_tmp_value.append('True')
            else:
                pass
        if check_tmp_value != []:
            return False
        else:
            #增加IP
            tmp_value_add = ip_address_add+'/'+str(netmask_add)
            tmp_data.append(tmp_value_add)
            data['network']['ethernets'][dev_name]['addresses'] = tmp_data
            with open(confpath,"w") as f:
                yaml.dump(data,f,encoding='utf-8')
                f.close()
        tmp_exec = 'ip addr flush dev '+dev_name
        public.ExecShell(tmp_exec)
        self.remove_blank_lines(conf_file=confpath)
        return True
        
    def ubuntu_modify_ip_netmask(self,dev_name,old_ip,old_netmask,new_ip,new_netmask):
        """
        ubuntu编辑ip、子网掩码

        """
        if old_ip == new_ip:
            if old_netmask == new_netmask:
                return False
            else:
                pass
        net_type = self.intranet_or_extranet(ip_address = new_ip)
        if net_type == 'extranet':
            if self.check_extranet_ip(extranet_ip=new_ip) == False:
                return False
        old_netmask_num = self.check_netmask(netmask=old_netmask)
        new_netmask_num = self.check_netmask(netmask=new_netmask)
        confpath = self.get_ubuntu_conf_file()
        conf = public.readFile(confpath)
        data=yaml.load(conf,Loader=yaml.FullLoader)
        tmp_data = data['network']['ethernets'][dev_name]['addresses']
        tmp_data_one = []
        check_tmp_value = []
        for i in range(0,len(tmp_data)):
            tmp_value = str(tmp_data[i]).split()[0].split('/')[0]
            if old_ip !=  tmp_value:
                tmp_data_one.append(tmp_value)
        for i in range(0,len(tmp_data_one)):
            if new_ip ==  str(tmp_data_one[i]).split()[0].split('/')[0]:
                check_tmp_value.append('True')
        if check_tmp_value != []:
            return False
        old_ip_netmask = old_ip+'/'+str(old_netmask_num)
        new_ip_netmask = new_ip+'/'+str(new_netmask_num)
        tmp_data.remove(old_ip_netmask)
        tmp_data.append(new_ip_netmask)
        data['network']['ethernets'][dev_name]['addresses'] = tmp_data
        with open(confpath,"w") as f:
            yaml.dump(data,f,encoding='utf-8')
            f.close()
        tmp_exec = 'ip addr flush dev '+dev_name
        public.ExecShell(tmp_exec)
        self.remove_blank_lines(conf_file=confpath)
        return True
    
    def ubuntu_ip_netmask_del(self,dev_name,ip_value,netmask_value):
        """
        ubuntu删除Ip、子网掩码
        
        """
        network_card_bind_ip_list,network_all_list = self.get_network_card_ip_list(network_name = dev_name)
        new_net_num = self.check_netmask(netmask=netmask_value)
        confpath = self.get_ubuntu_conf_file()
        conf = public.readFile(confpath)
        data=yaml.load(conf,Loader=yaml.FullLoader)
        tmp_data = data['network']['ethernets'][dev_name]['addresses']
        del_ip_netmask = str(ip_value)+'/'+str(new_net_num)
        dev_name_list = self.get_network_card_name_list()
        if len(network_all_list)<2:
            if dev_name != dev_name_list[0]:
               data['network']['ethernets'].pop(dev_name) 
        else:
            if del_ip_netmask in tmp_data:
                tmp_data.remove(del_ip_netmask)
            data['network']['ethernets'][dev_name]['addresses'] = tmp_data
        with open(confpath,"w") as f:
            yaml.dump(data,f,encoding='utf-8')
            f.close()
        tmp_exec = 'ip addr flush dev '+dev_name
        public.ExecShell(tmp_exec)
        self.remove_blank_lines(conf_file=confpath)
        return True
        
    def ubuntu_modify_gateway(self,dev_name,new_gateway):
        """
        ubuntu修改网关
        """
        confpath = self.get_ubuntu_conf_file()
        tmp_conf = public.readFile(confpath)
        rep = '\n*\s*'+dev_name+':\s*\n*'
        result = re.search(rep,str(tmp_conf))
        if not result:
            return False
        rep = '\n*\s*'+'gateway4'+':\s*\d+\.\d+\.\d+\.\d+\s*\n*'
        result = re.search(rep,str(tmp_conf))
        if not result:
            return False
        conf = public.readFile(confpath)
        data=yaml.load(conf,Loader=yaml.FullLoader)
        data['network']['ethernets'][dev_name]['gateway4'] = new_gateway
        with open(confpath,"w") as f:
            yaml.dump(data,f,encoding='utf-8')
            f.close()
        tmp_exec = 'ip addr flush dev '+dev_name
        public.ExecShell(tmp_exec)
        return True

    def check_extranet_ip(self,extranet_ip):
        """
        公网IP是否已添加判断
        """
        network_card_lists = self.get_network_card_name_list()
        extranet_ip_value = []
        for i in range(0,len(network_card_lists)):
            network_card_bind_ip_list,network_all_list = self.get_network_card_ip_list(network_name = network_card_lists[i])
            if len(network_all_list) < 1:
                continue
            if extranet_ip in network_all_list:
                extranet_ip_value.append('True')
        if extranet_ip_value != []:
            return False
        return True
        

    def debian_ip_set(self,dev_name,ip_address_add,netmask_add):
        """
        debian文件切片配置方法(兼容多网卡)
        """
        #网卡配置文件补全
        dev_name_list = self.get_network_card_name_list()
        netmask_value, netmask_num, ip_value, dev_namen = self.get_default_netmask_value(dev_name=dev_name_list[0])
        conf_file = '/etc/network/interfaces'
        net_type = self.intranet_or_extranet(ip_address = ip_address_add)
        extranet_check = []
        if net_type == 'extranet':
            with open(conf_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    tmp_value = str(ip_address_add)
                    if tmp_value in line:
                        rep = str(ip_address_add)+'\d+'
                        result = re.search(rep,line)
                        if not result:
                            rep = '\d+'+str(ip_address_add)
                            result = re.search(rep,line)
                            if not result:
                                tmp_value = 'address'
                                if tmp_value in line:
                                    extranet_check.append('True')
        if extranet_check != []:
            return False
        tmp_check = []
        tmp_gateway = public.ExecShell('ip route | grep default')[0].split()[2]
        with open(conf_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                tmp_value = '# Created by bt on instance boot automatically,do not edit'
                if tmp_value in line:
                    tmp_check.append('True')
                tmp_value = 'address'
                if tmp_value in line:
                    tmp_check.append('True')
                tmp_value = 'gateway'
                if tmp_value in line:
                    tmp_check.append('True')
        if len(tmp_check)<3:
            tmp_aa = '# Created by bt on instance boot automatically,do not edit'+'\n'
            conf = tmp_aa
            tmp_aa = 'auto lo'+'\n'
            conf += tmp_aa
            tmp_aa = 'iface lo inet loopback'+'\n'
            conf += tmp_aa
            tmp_aa = 'auto ' + dev_name_list[0]+'\n'
            conf += tmp_aa
            tmp_bb = 'iface ' + dev_name_list[0] + " inet static"+'\n'
            conf += tmp_bb
            tmp_cc = "        address " + ip_value+'/'+netmask_num+'\n'
            conf += tmp_cc
            tmp_dd = "        gateway " + tmp_gateway+'\n'
            conf += tmp_dd
            public.writeFile(conf_file, conf)
        if dev_name != dev_name_list[0]:
            conf = public.readFile(conf_file)
            rep = '\n*\s*iface '+dev_name+' inet static\s*\n*'
            result = re.search(rep,conf)
            if not result:
                tmp_aa = '\n'+'auto ' + dev_name+'\n'
                conf += tmp_aa
                tmp_bb = 'iface ' + dev_name + " inet static"+'\n'
                conf += tmp_bb
                tmp_cc = "        address " + ip_address_add+'/'+str(netmask_add)+'\n'
                conf += tmp_cc
                # tmp_dd = "        gateway " + tmp_gateway+'\n'
                # conf += tmp_dd
                public.writeFile(conf_file, conf)
                tmp_exec = 'ip addr flush dev '+dev_name
                public.ExecShell(tmp_exec)
                self.remove_blank_lines(conf_file=conf_file)
                return True
        else:
            pass
        #IP检测
        if self.debian_check_ip(dev_name=dev_name ,check_str=ip_address_add,exclude_value='') == False:
            return False
        #增加IP
        conf = public.readFile(conf_file)
        check_self,check_else = self.get_check_else(dev_name=dev_name)
        if check_self != '':
            tmp_conf_one = conf[:check_self]
            if check_else == '':
                tmp_conf_two = conf[check_self:]
            else:
                tmp_conf_two = conf[check_self:check_else]
                tmp_conf_three = conf[check_else:]
        else:
            pass    
        new_dev_name = self.get_new_dev_name(dev_name=dev_name,data=tmp_conf_two)
        tmp_add = '\n'+'auto '+new_dev_name+'\n'
        tmp_add += 'iface '+new_dev_name+' inet static'+'\n'
        tmp_add += "        address "+ip_address_add+'/'+str(netmask_add)+'\n'
        tmp_conf_two += tmp_add
        if check_else == '':
            conf = tmp_conf_one+tmp_conf_two
        else:
            conf = tmp_conf_one+tmp_conf_two+tmp_conf_three
        with open(conf_file, "w", encoding="utf-8") as f_w:
            f_w.write(conf)
        self.remove_blank_lines(conf_file=conf_file)
        return True

    
    def debian_modify_ip_netmask(self,dev_name,old_ip,old_netmask,new_ip,new_netmask):
        """
        debian 编辑IP、子网掩码(兼容多网卡)
        """
        #IP检测
        conf_file = '/etc/network/interfaces'
        if new_ip == old_ip:
            if new_netmask == old_netmask:
                return False
        else:
            if self.debian_check_ip(dev_name=dev_name ,check_str=new_ip,exclude_value=old_ip) == False:
                return False
            net_type = self.intranet_or_extranet(ip_address = new_ip)
            extranet_check = []
            if net_type == 'extranet':
                with open(conf_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        tmp_value = str(new_ip)
                        if tmp_value in line:
                            rep = str(new_ip)+'\d+'
                            result = re.search(rep,line)
                            if not result:
                                rep = '\d+'+str(new_ip)
                                result = re.search(rep,line)
                                if not result:
                                    tmp_value = 'address'
                                    if tmp_value in line:
                                        extranet_check.append('True')
            if extranet_check != []:
                return False

        #编辑修改
        old_netmask_num = self.check_netmask(netmask=old_netmask)
        new_netmask_num = self.check_netmask(netmask=new_netmask)
        conf = public.readFile(conf_file)
        check_self,check_else = self.get_check_else(dev_name=dev_name)
        tmp_conf_one = conf[:check_self]
        if check_else == '':
            tmp_conf_two = conf[check_self:]
        else:
            tmp_conf_two = conf[check_self:check_else]
            tmp_conf_three = conf[check_else:]
        old_value = old_ip+'/'+str(old_netmask_num)
        new_value = new_ip+'/'+str(new_netmask_num)
        with open(conf_file+'.bak', "w", encoding="utf-8") as f_w:
            f_w.write(tmp_conf_two)
        with open(conf_file+'.bak', "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(conf_file+'.bak', "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value = old_ip+'/'+str(old_netmask_num)
                if tmp_value in line:
                    tmp_value = 'address'
                    if tmp_value in line:
                        rep = old_ip+'/'+str(old_netmask_num)+'\d+'
                        result = re.search(rep,line)
                        if not result:
                            rep = '\d+'+old_ip+'/'+str(old_netmask_num)
                            result = re.search(rep,line)
                            if not result:
                                line = line.replace(old_value,new_value)
                f_w.write(line)
        tmp_conf_two = public.readFile(conf_file+'.bak')
        if check_else == '':
            conf = tmp_conf_one+tmp_conf_two
        else:
            conf = tmp_conf_one+tmp_conf_two+tmp_conf_three
        with open(conf_file, "w", encoding="utf-8") as f_w:
            f_w.write(conf)
        self.remove_blank_lines(conf_file=conf_file)
        return True
        
    def get_debian_else_gateway(self,dev_name):
        """
        debian除默认网关外的网关获取方法
        """
        conf_file = '/etc/network/interfaces'
        conf = public.readFile(conf_file)
        check_self,check_else = self.get_check_else(dev_name=dev_name)
        tmp_conf_one = conf[:check_self]
        if check_else == '':
            tmp_conf_two = conf[check_self:]
        else:
            tmp_conf_two = conf[check_self:check_else]
            tmp_conf_three = conf[check_else:]
        with open(conf_file+'.tmp', "w", encoding="utf-8") as f_w:
            f_w.write(tmp_conf_two)
        tmp_gateway = []
        with open(conf_file+'.tmp', "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if 'gateway' in line:
                    tmp_gateway.append(line)
        if check_else == '':
            conf = tmp_conf_one+tmp_conf_two
        else:
            conf = tmp_conf_one+tmp_conf_two+tmp_conf_three
        with open(conf_file, "w", encoding="utf-8") as f_w:
            f_w.write(conf)
        debian_else_gateway = ''
        if tmp_gateway != []:
            debian_else_gateway = tmp_gateway[0].split()
        return debian_else_gateway
            
        
    def debian_modify_gateway(self,dev_name,new_gateway):
        """
        debian修改网关
        """
        conf_file = '/etc/network/interfaces'
        conf = public.readFile(conf_file)
        old_gateway = self.get_debian_else_gateway(dev_name=dev_name)
        check_self,check_else = self.get_check_else(dev_name=dev_name)
        tmp_conf_one = conf[:check_self]
        if check_else == '':
            tmp_conf_two = conf[check_self:]
        else:
            tmp_conf_two = conf[check_self:check_else]
            tmp_conf_three = conf[check_else:]
        with open(conf_file+'.tmp', "w", encoding="utf-8") as f_w:
            f_w.write(tmp_conf_two)
        with open(conf_file+'.tmp', "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(conf_file+'.tmp', "w", encoding="utf-8") as f_w:
            for line in lines:
                if 'gateway' in line:
                    line = line.replace(str(old_gateway),str(new_gateway))
                f_w.write(line)
        tmp_conf_two = public.readFile(conf_file+'.tmp')
        if check_else == '':
            conf = tmp_conf_one+tmp_conf_two
        else:
            conf = tmp_conf_one+tmp_conf_two+tmp_conf_three
        with open(conf_file, "w", encoding="utf-8") as f_w:
            f_w.write(conf)
        if os.path.exists(conf_file+'.tmp'):
            tmp_exec = 'sudo rm -f '+conf_file+'.tmp'
            public.ExecShell(tmp_exec)
        return True
        
        
    def get_debian_del_network(self,dev_name,del_value):
        """
        取debian删除的网卡名
        """
        tmp_exec = 'ip add | grep '+dev_name+'| grep inet| grep '+del_value
        public.ExecShell(tmp_exec)
        tmp_a = public.ExecShell(tmp_exec)
        tmp_b = tmp_a[0].split()
        del_network = tmp_b[len(tmp_b)-1]
        return del_network
        
        
    def remove_blank_lines(self,conf_file):
        """
        去除文本的空行
        """
        file_one = open(conf_file, 'r', encoding='utf-8')
        lines = file_one.readlines()
        file_two = open(conf_file, 'w', encoding='utf-8') 
        for line in lines:
            if line.split():
                file_two.writelines(line)
            else:
                file_two.writelines("")
        file_one.close()
        file_two.close()
        return True
        
        
    def multiple_ip_del(self,conf_file,dev_name,del_ip_netmask):
        """
        debian第一张网卡绑定IP超过3个以及非第一张网卡绑定IP超过2个的删除IP方法
        """
        net_name_list,tmp_ip = self.get_debian_index(dev_name=dev_name)
        del_one = '    address '+tmp_ip
        del_two = 'auto '+net_name_list[0]
        del_three = 'iface '+net_name_list[0]+' inet static'
        tmp_conf = public.readFile(conf_file+'.tmp')
        with open(conf_file+'.tmp', "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(conf_file+'.tmp', "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value = del_one
                if tmp_value in line:
                    rep = del_one+'\d+'
                    result = re.search(rep,tmp_conf)
                    if not result:
                        continue
                tmp_value = del_two
                if tmp_value in line:
                    rep = del_two+'\d+'
                    result = re.search(rep,tmp_conf)
                    if not result:
                        continue
                tmp_value = del_three
                if tmp_value in line:
                    continue
                f_w.write(line)
        tmp_conf = public.readFile(conf_file+'.tmp')
        with open(conf_file+'.tmp', "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(conf_file+'.tmp', "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value = del_ip_netmask
                if tmp_value in line:
                    rep = tmp_value+'\d+'
                    result = re.search(rep,tmp_conf)
                    if not result:
                        line = line.replace(del_ip_netmask,del_one)
                f_w.write(line)
        return True
        
    def single_ip_del(self,dev_name,conf_file,del_one,del_two,del_three):
        """
        debian第一张网卡绑定IP2个以下（包含2个）以及非第一张网卡绑定IP只有1个的删除IP方法
        """
        dev_name_list = self.get_network_card_name_list()
        tmp_conf = public.readFile(conf_file+'.tmp')
        with open(conf_file+'.tmp', "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(conf_file+'.tmp', "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value = del_one
                if tmp_value in line:
                    rep = del_one+'\d+'
                    result = re.search(rep,tmp_conf)
                    if not result:
                        rep = '\d+'+del_one
                        result = re.search(rep,tmp_conf)
                        if not result:
                            continue
                tmp_value = del_two
                if tmp_value in line:
                    rep = del_two+'\d+'
                    result = re.search(rep,tmp_conf)
                    if not result:
                        rep = '\d+'+del_two
                        result = re.search(rep,tmp_conf)
                        if not result:
                            continue
                tmp_value = del_three
                if tmp_value in line:
                    continue
                if dev_name != dev_name_list[0]:
                    tmp_value = 'gateway'
                    if tmp_value in line:
                        continue
                f_w.write(line)
        
            
        return True
        
    def debian_ip_netmask_del(self,dev_name,ip_value,netmask_value):
        """
        debian删除ip、子网掩码(兼容多网卡)
        
        """
        dev_name_list = self.get_network_card_name_list()
        network_card_bind_ip_list,network_all_list = self.get_network_card_ip_list(network_name = dev_name)
        conf_file = '/etc/network/interfaces'
        conf = public.readFile(conf_file)
        check_self,check_else = self.get_check_else(dev_name=dev_name)
        new_net_num = self.check_netmask(netmask=netmask_value)
        tmp_conf_one = conf[:check_self]
        if check_else == '':
            tmp_conf_two = conf[check_self:]
        else:
            tmp_conf_two = conf[check_self:check_else]
            tmp_conf_three = conf[check_else:]
        del_one = ip_value+'/'+str(new_net_num)
        del_network = self.get_debian_del_network(dev_name=dev_name,del_value=del_one)
        del_one = '    address '+del_one
        del_two = 'auto '+del_network
        del_three = 'iface '+del_network+' inet static'
        with open(conf_file+'.tmp', "w", encoding="utf-8") as f_w:
            f_w.write(tmp_conf_two)
        if dev_name != dev_name_list[0]:
            if len(network_all_list) > 1:
                self.multiple_ip_del(conf_file=conf_file,dev_name=dev_name,del_ip_netmask=del_one)
            else:
                if self.single_ip_del(dev_name=dev_name,conf_file=conf_file,del_one=del_one,del_two=del_two,del_three=del_three) == False:
                    return False
                self.single_ip_del(dev_name=dev_name,conf_file=conf_file,del_one=del_one,del_two=del_two,del_three=del_three)
                    
        elif dev_name == dev_name_list[0]:
            if len(network_all_list) > 2:
                self.multiple_ip_del(conf_file=conf_file,dev_name=dev_name,del_ip_netmask=del_one)
            else:
                self.single_ip_del(dev_name=dev_name,conf_file=conf_file,del_one=del_one,del_two=del_two,del_three=del_three)
        tmp_conf_two = public.readFile(conf_file+'.tmp')
        if check_else == '':
            conf = tmp_conf_one+tmp_conf_two
        else:
            conf = tmp_conf_one+tmp_conf_two+tmp_conf_three
        with open(conf_file, "w", encoding="utf-8") as f_w:
            f_w.write(conf)
        self.remove_blank_lines(conf_file=conf_file)
        tmp_exec = 'ip addr flush dev '+dev_name
        public.ExecShell(tmp_exec)
        return True
        
    def get_debian_index(self,dev_name):
        """
        取debian网卡下对应配置名最大索引 
        """
        tmp_exec = 'ip add | grep '+dev_name+' | grep inet'
        tmp_value = public.ExecShell(tmp_exec)
        tmp_a = tmp_value[0].split('\n')
        net_name_list = []
        for i in range(0,len(tmp_a)):
            rep = 'inet'
            result = re.search(rep,tmp_a[i])
            if result:
                tmp_b = tmp_a[i].strip().split()
                tmp_c = tmp_b[len(tmp_b)-1]
                if tmp_c == dev_name:
                    continue
                else:
                    net_name_list.append(tmp_c)
        net_name_list = sorted(net_name_list,key = lambda x:(x.split(':')[1]),reverse=True)
        tmp_exec = 'ip add | grep '+dev_name+' | grep inet| grep '+net_name_list[0]
        tmp_value = public.ExecShell(tmp_exec)
        tmp_ip = tmp_value[0].strip().split()[1]
        return net_name_list,tmp_ip

    def reload_network(self):
        """
        重启网络服务

        """
        system_type = self.get_system()
        if system_type == "centos":
            public.ExecShell("systemctl restart network")
        elif system_type == "debian":
            public.ExecShell("sudo /etc/init.d/networking restart")
        elif system_type == "ubuntu":
            public.ExecShell('sudo netplan apply')
        return True

    def ftp_ip_set(self, get):
        """
        ftp IP配置，解决用户无法使用ftp存储空间连接时的配置
        配置不支持自定义IP配置，也是防止用户误配置导致连接不上
        会自动获取本地服务器出口IP，并将获取到的出口公网IP设置为FTP IP。

        """
        ftp_conf_file = '/www/server/pure-ftpd/etc/pure-ftpd.conf'
        ftp_dir = '/www/server/pure-ftpd/'
        if not os.path.exists(ftp_dir):
            return public.returnMsg(False, '未安装ftp或者非面板安装的ftp')
        if not os.path.exists(ftp_conf_file):
            return public.returnMsg(False, '未检测到配置文件')
        # if os.stat(ftp_conf_file).st_size == 0:
        #     return public.returnMsg(False, '配置文件为空，请检查ftp配置文件是否正常！')
        ip_value = public.ExecShell('curl http://www.bt.cn/api/getipaddress')[0]
        rep = r"\n*#*\s*ForcePassiveIP\s*.*\n*"
        conf = public.ReadFile(ftp_conf_file)
        result = re.search(rep, conf)
        if result:
            conf = re.sub(rep, '\n'+'ForcePassiveIP                ' + ip_value + '\n', conf)
            public.writeFile(ftp_conf_file, conf)
        else:
            conf_value = '\n'
            conf += conf_value
            conf_value = '\n' + '# BT created IP configuration code segment, please do not edit'
            conf += conf_value
            conf_value = '\n' + 'ForcePassiveIP                ' + ip_value
            conf += conf_value
            public.writeFile(ftp_conf_file, conf)
        public.ExecShell('/etc/init.d/pure-ftpd restart')
        return public.returnMsg(True, '设置成功')

    def ftp_ip_unset(self, get):
        """
        ftp 取消ip设置
        返回值：
        True：
            取消设置成功
        False:
            取消设置失败
        """
        ip_value = public.ExecShell('curl http://www.bt.cn/api/getipaddress')[0]
        print(type(ip_value))
        ftp_conf_file = '/www/server/pure-ftpd/etc/pure-ftpd.conf'
        if not os.path.exists(ftp_conf_file):
            return public.returnMsg(False, 'FTP配置文件不存在！')
        if os.stat(ftp_conf_file).st_size == 0:
            return public.returnMsg(False, 'FTP配置文件为空文件，请检查ftp配置文件是否正常！')
        rep = r"\n*#*\s*ForcePassiveIP\s*.*\n*"
        conf = public.ReadFile(ftp_conf_file)
        result = re.search(rep, conf)
        if not result:
            return public.returnMsg(False, '无需设置')
        if result[0].strip()[0] == '#':
            return public.returnMsg(False, '无需设置')
        with open(ftp_conf_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(ftp_conf_file, "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value = 'ForcePassiveIP'
                if tmp_value in line:
                    line = '\n# ' + line
                f_w.write(line)
        return public.returnMsg(True, '设置成功')
        
    def dns_conf_completion(self):
        """
        检测dns配置文件
        """
        dns_conf_file = '/etc/resolv.conf'
        conf = public.ReadFile(dns_conf_file)
        rep = '\n*#*\s*nameserver 114.114.114.114\s*\n*'
        result = re.search(rep,conf)
        if not result:
            public.ExecShell('sudo echo "nameserver 114.114.114.114">>/etc/resolv.conf')
        rep = '\n*#*\s*nameserver 8.8.8.8\s*\n*'
        result = re.search(rep,conf)
        if not result:
            public.ExecShell('sudo echo "nameserver 8.8.8.8">>/etc/resolv.conf')
    
        
    def check_ping(self):
        """
        测试是否能连通www.bt.cn
        返回值：
        is_ping      True表示能正常连通，False表示无法连通
        """
        self.dns_conf_completion()
        tmp = public.ExecShell('ping -c 1 -w 1 www.bt.cn')
        is_ping = False
        try:
            if tmp[0].split('time=')[1].split()[0]: is_ping = True
        except:
            pass
        return is_ping
        
        
    def get_ftp_ip_list(self, get):
        """
        获取ftp ip设置列表，如未设置，返回未设置
        返回值：
        True：
            IP已设置
        False:
            IP未设置


        """
        system_type = self.get_system()
        is_ping = self.check_ping()
        if is_ping:
            ip_value = public.ExecShell('curl http://www.bt.cn/api/getipaddress')[0]
        else:
            ip_value = ''
        if not ip_value:ip_value=public.GetLocalIp()
        if not self.check_ip(address=ip_value):
            return public.returnMsg(False,'获取服务器出口IP失败，请检查服务器DNS!    国内的机器执行以下命令：echo "nameserver 114.114.114.114">>/etc/resolv.conf        国外的机器执行命令：echo "nameserver 8.8.8.8">>/etc/resolv.conf')
        ftp_conf_file='/www/server/pure-ftpd/etc/pure-ftpd.conf'
        tmp_dict = {}
        ftp_list = []
        tmp_dict["ip"] = ip_value
        if not os.path.exists(ftp_conf_file):
            tmp_dict["status"] = False
            ftp_list.append(tmp_dict)
            return ftp_list
        if os.stat(ftp_conf_file).st_size == 0:
            tmp_dict["status"] = False
            ftp_list.append(tmp_dict)
            return ftp_list
        if os.path.exists(ftp_conf_file):
            if os.stat(ftp_conf_file).st_size > 0:
                rep = r"\n*#*\s*ForcePassiveIP\s*.*\n*"
                conf = public.ReadFile(ftp_conf_file)
                result = re.search(rep, conf)
                if result:
                    # tmp_value = result[0].split('IP')[0][0]
                    if result[0].strip()[0] == '#':
                        tmp_dict["status"] = False
                    else:
                        tmp_value = result[0].strip().split('IP')[1].strip()
                        if tmp_value == ip_value:
                            tmp_dict["status"] = True
                        elif tmp_value != ip_value:
                            tmp_dict["status"] = False
                else:
                    tmp_dict["status"] = False
            else:
                tmp_dict["status"] = False
        ftp_list.append(tmp_dict)
        return ftp_list

    def ssh_allow_ip_add(self, get):
        """
        ssh允许策略ip设置
        需要前端获取到用户设置的IP，暂时变量为ip.
        """
        if not self.check_database(): return public.returnMsg(False,'数据库创建失败！!')
        self.check_tables()
        # if not self.check_tables(): return public.returnMsg(False,'数据库相关表创建失败！!')
        tmp_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        if not self.check_ip(get.ssh_adresss): return public.returnMsg(False, 'IP地址不合法!')
        one_line_ip_value,ssh_allow_ip,ssh_remask,ssh_add_time = self.ip_configuration_db_query(get.ssh_adresss)
        if one_line_ip_value :
            pass
            # self.ip_configuration_db_update(self,ssh_ip=get.ssh_adresss,modify_remark =ssh_remask,modify_time=tmp_time)
        else:
            tmp_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            self.ip_configuration_db_add(set_ssh_ip=get.ssh_adresss, remark=get.remarks, add_time=tmp_time)
            # self.ip_configuration_db_add(self,ssh_ip=get.ssh_adresss,remark =get.remarks,add_time=tmp_time)
        if get.remarks != "":
            pass
        hosts_allow = '/etc/hosts.allow'
        hosts_deny = '/etc/hosts.deny'
        if not os.path.exists(hosts_allow):
            return public.returnMsg(False, '配置文件不存在！')
        if not os.path.exists(hosts_deny):
            return public.returnMsg(False, '配置文件不存在！')
        tmp_value = 'sshd:' + get.ssh_adresss + ':allow\n'
        conf = public.ReadFile(hosts_allow)
        rep = tmp_value
        result = re.search(rep, conf)
        if result:
            conf = public.ReadFile(hosts_deny)
            rep = 'sshd:ALL' + '\n'
            result = re.search(rep, conf)
            if not result:
                conf += rep
                public.writeFile(hosts_deny, conf)
            else:
                with open(hosts_deny, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open(hosts_deny, "w", encoding="utf-8") as f_w:
                    for line in lines:
                        tmp_value = 'sshd:ALL'
                        if tmp_value in line:
                            line =  tmp_value+'\n'
                        f_w.write(line)
            return public.returnMsg(False, '指定IP已经添加过！')
        else:
            conf += tmp_value
            public.writeFile(hosts_allow, conf)
            conf = public.ReadFile(hosts_deny)
            rep = 'sshd:ALL' + '\n'
            result = re.search(rep, conf)
            if result:
                with open(hosts_deny, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open(hosts_deny, "w", encoding="utf-8") as f_w:
                    for line in lines:
                        tmp_value = 'sshd:ALL'
                        if tmp_value in line:
                            line =  tmp_value+'\n'
                        f_w.write(line)
            else:
                conf += rep
                public.writeFile(hosts_deny, conf)
        public.ExecShell('systemctl restart sshd.service')
        return public.returnMsg(True, '成功设置')

    def ssh_allow_ip_del(self, get):
        """
        ssh解除允许的sshIP限制，删除操作接口
        需要前端获取到用户设置的IP，暂时变量为ip.

        """
        hosts_allow = '/etc/hosts.allow'
        hosts_deny = '/etc/hosts.deny'
        if not os.path.exists(hosts_allow):
            return public.returnMsg(False, '配置文件不存在！')
        if not os.path.exists(hosts_deny):
            return public.returnMsg(False, '配置文件不存在！')
        tmp_value = 'sshd:' + get.ssh_relieve_adresss + ':allow'
        conf = public.ReadFile(hosts_allow)
        rep = tmp_value + '\n'
        result = re.search(rep, conf)
        if result:
            with open(hosts_allow, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(hosts_allow, "w", encoding="utf-8") as f_w:
                for line in lines:
                    if tmp_value in line:
                        continue
                    f_w.write(line)
        else:
            pass
        public.ExecShell('systemctl restart sshd.service')
        self.ip_configuration_db_del(ssh_ip=get.ssh_relieve_adresss)
        args=public.dict_obj()
        ssh_allow_ip_list = self.get_ssh_ip_list(args)
        if ssh_allow_ip_list == []:
            self.ssh_ip_iniT(args)
        return public.returnMsg(True, '删除成功！')
        
    def ssh_ip_init(self,get):
        if not self.ssh_ip_iniT(get):
            return public.returnMsg(False, '配置文件不存在!')
        return public.returnMsg(True, '初始化成功！')
    

    def ssh_ip_iniT(self, get):
        """
        ssh解除全部允许的sshIP限制
        一键恢复初始不限制的状态

        """
        hosts_allow = '/etc/hosts.allow'
        hosts_deny = '/etc/hosts.deny'
        if not os.path.exists(hosts_allow):
            return False
        if not os.path.exists(hosts_deny):
            return False
        # tmp_value = 'sshd:'+'.*:allow'
        # conf = public.ReadFile(hosts_allow)
        # rep = tmp_value+'\n'
        # result = re.search(rep,conf)
        # 一键恢复初始不限制的状态
        # if result:
        with open(hosts_allow, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(hosts_allow, "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value = 'sshd:'
                if tmp_value in line:
                    continue
                f_w.write(line)
        with open(hosts_deny, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(hosts_deny, "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value = 'sshd:ALL'
                if tmp_value in line:
                    continue
                f_w.write(line)
        # else:
        #     pass
        self.ip_configuration_db_table_del()
        public.ExecShell('systemctl restart sshd.service')
        return True

    def get_ssh_ip_list(self, get):
        """
        获取ssh ip设置列表，如未设置，返回未设置
        返回值：
        ssh_allow_ip_list：
            返回一个授权IP列表数组
        """
        hosts_allow = '/etc/hosts.allow'
        hosts_deny = '/etc/hosts.deny'
        tmp_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        if not os.path.exists(hosts_allow):
            return public.returnMsg(False, '配置文件不存在！')
        if not os.path.exists(hosts_deny):
            return public.returnMsg(False, '配置文件不存在！')
        tmp_list = []
        ssh_allow_ip_list = []
        with open(hosts_deny, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(hosts_deny, "w", encoding="utf-8") as f_w:
            for line in lines:
                tmp_value = 'sshd:ALL'
                if tmp_value in line:
                    tmp_list.append('Ture')
                f_w.write(line)
        if tmp_list != []:
            tmp_ip_list = []
            with open(hosts_allow, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(hosts_allow, "w", encoding="utf-8") as f_w:
                for line in lines:
                    tmp_value = 'sshd:'            
                    if tmp_value in line:
                        tmp_a = line.split(':')[1]
                        if tmp_a == "": continue
                        tmp_ip_list.append(tmp_a)
                        one_line_ip_value,ssh_allow_ip,ssh_remask,ssh_add_time = self.ip_configuration_db_query(ssh_ip=tmp_a)
                        # tmp_dict["ip"] = ssh_allow_ip
                        # tmp_dict["status"] = True
                        # tmp_dict["remarks"] = ssh_remask
                        # tmp_dict["add_time"] = ssh_add_time
                        # ssh_allow_ip_list.append(tmp_dict)
                        if one_line_ip_value != "":
                            tmp_dict = {}
                            tmp_dict["ip"] = tmp_a
                            tmp_dict["status"] = True
                            tmp_dict["remarks"] = ssh_remask
                            tmp_dict["add_time"] = ssh_add_time
                            ssh_allow_ip_list.append(tmp_dict)
                        else:
                            tmp_dict = {}
                            tmp_dict["remarks"] = ''
                            self.ip_configuration_db_add(set_ssh_ip=tmp_a, remark=str(tmp_dict["remarks"]), add_time=tmp_time)
                            one_line_ip_value,ssh_allow_ip,ssh_remask,ssh_add_time = self.ip_configuration_db_query(ssh_ip=tmp_a)
                            tmp_dict["ip"] = tmp_a
                            tmp_dict["status"] = True
                            tmp_dict["remarks"] = ssh_remask
                            tmp_dict["add_time"] = ssh_add_time
                            ssh_allow_ip_list.append(tmp_dict)
                    f_w.write(line)
        else:
            pass
        return ssh_allow_ip_list

    def ssh_allow_ip_modify(self, get):
        """
        获取ssh 编辑ip设置列表，如未设置，返回未设置
        返回值：
        True:
            编辑/修改成功
        False：
            编辑/修改失败
        """
        
        if not self.check_ip(get.new_ssh_allow_ip): return public.returnMsg(False, 'IP地址不合法!')
        hosts_allow = '/etc/hosts.allow'
        hosts_deny = '/etc/hosts.deny'
        tmp_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        if not os.path.exists(hosts_allow):
            return public.returnMsg(False, '配置文件不存在！')
        if not os.path.exists(hosts_deny):
            return public.returnMsg(False, '配置文件不存在！')
        tmp_value = 'sshd:' + get.old_ssh_allow_ip + ':allow'
        conf = public.ReadFile(hosts_allow)
        rep = tmp_value + '\n'
        result_one = re.search(rep, conf)
        old_ssh_allow_ip_value = 'sshd:' + get.new_ssh_allow_ip + ':allow\n'
        result_two = re.search(old_ssh_allow_ip_value, conf)
        if result_two:
            return public.returnMsg(False, '修改的ip已存在授权IP中，无法修改！')
        if result_one:
            with open(hosts_allow, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(hosts_allow, "w", encoding="utf-8") as f_w:
                for line in lines:
                    if tmp_value in line:
                        tmp_value = 'sshd:' + get.new_ssh_allow_ip + ':allow\n'
                        line = tmp_value
                        modify_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                    f_w.write(line)
            one_line_ip_value,ssh_allow_ip,ssh_remask,ssh_add_time = self.ip_configuration_db_query(get.old_ssh_allow_ip)
            tmp_remark = ssh_remask
            if one_line_ip_value != "":
                self.ip_configuration_db_del(ssh_ip=get.old_ssh_allow_ip)
            one_line_ip_value,ssh_allow_ip,ssh_remask,ssh_add_time = self.ip_configuration_db_query(get.new_ssh_allow_ip)
            if one_line_ip_value == "":
                self.ip_configuration_db_add(set_ssh_ip=get.new_ssh_allow_ip, remark=tmp_remark, add_time=tmp_time)
        else:
            pass

        public.ExecShell('systemctl restart sshd.service')
        return public.returnMsg(True, '修改成功')

    def check_database(self):
        """
        检测数据库文件是否存在，不存在则自动创建

        """
        plugin_dir = "/www/server/panel/plugin/ip_configuration"
        ip_configuration_db_path = os.path.join(plugin_dir, "ip_configuration.db")
        # 判断ip_configuration_db_path是否存在，不存在则创建
        if not os.path.exists(ip_configuration_db_path):
            f = open(ip_configuration_db_path,'w')
        return True

    def check_tables(self):
        """
        检测数据库相关表是否存在，不存在则自动创建

        """
        plugin_dir = "/www/server/panel/plugin/ip_configuration"
        ip_configuration_db_path = os.path.join(plugin_dir, "ip_configuration.db")
        isolation_level = "EXCLUSIVE"
        try:
            import sqlite3
            conn = None
            cur = None
            conn = sqlite3.connect(ip_configuration_db_path, isolation_level=isolation_level)
            cur = conn.cursor()
            results = cur.execute("SELECT name FROM sqlite_master where type='table'").fetchall()
            tables = [r[0] for r in results]
            if "ssh_ip_log" in tables:
                return True
            else:
                cur.execute("""
                create table ssh_ip_log(
                    ssh_ip text,
                    remark integer,
                    add_time timestamp default CURRENT_TIMESTAMP
                )
                """)
                """ssh_ip_log 表说明
                记录ssh授权IP操作时间、备注
                @ssh_ip     ssh授权IP
                @remark     备注
                @add_time   添加时间
                """
        except Exception as e:
            return False
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        return True

    def ip_configuration_db_add(self, set_ssh_ip, remark, add_time):
        """
        将记录的ssh授权IP操作时间、备注、操作时间存储到数据库

        """
        plugin_dir = "/www/server/panel/plugin/ip_configuration"
        ip_configuration_db_path = os.path.join(plugin_dir, "ip_configuration.db")
        conn = None
        cur = None
        conn = sqlite3.connect(ip_configuration_db_path)
        cur = conn.cursor()
        add_exec = "INSERT INTO ssh_ip_log(ssh_ip,remark,add_time) Values('" + set_ssh_ip + "','" + remark + "','" + add_time + "')"
        if (cur.execute(add_exec)):
            conn.commit()
            return public.returnMsg(True,'备注信息{}添加成功!'.format(set_ssh_ip))
        return True

    def ip_configuration_db_update(self, get):
        """
        更新数据库数据
        当修改备注时，需要调用
        ssh_ip           需要修改的IP
        modify_remark    修改后的备注信息
        modify_time      修改备注的操作时间
        """
        plugin_dir = "/www/server/panel/plugin/ip_configuration"
        ip_configuration_db_path = os.path.join(plugin_dir, "ip_configuration.db")
        conn = None
        cur = None
        conn = sqlite3.connect(ip_configuration_db_path)
        cur = conn.cursor()
        tmp_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        one_line_ip_value,ssh_allow_ip,ssh_remask,ssh_add_time = self.ip_configuration_db_query(get.remark_ip)
        tmp_remark = ssh_remask
        update_exec_one = "UPDATE ssh_ip_log SET remark='" + get.modify_remark + "' WHERE ssh_ip='" + get.remark_ip + "'"
        update_exec_two = "UPDATE ssh_ip_log SET add_time='" + tmp_time + "' WHERE ssh_ip='" + get.remark_ip + "'"
        cur.execute(update_exec_one)
        cur.execute(update_exec_two)
        conn.commit()
        return public.returnMsg(True, '更新{}备注数据成功!'.format(get.modify_remark))

    def ip_configuration_db_del(self, ssh_ip):
        """
        删除IP数据
        当操作删除IP时，需要调用
        需要从前端获取IP
        """

        plugin_dir = "/www/server/panel/plugin/ip_configuration"
        ip_configuration_db_path = os.path.join(plugin_dir, "ip_configuration.db")
        conn = None
        cur = None
        conn = sqlite3.connect(ip_configuration_db_path)
        cur = conn.cursor()
        del_exec = "DELETE FROM ssh_ip_log WHERE ssh_ip='" + ssh_ip + "'"
        cur.execute(del_exec)
        conn.commit()
        return public.returnMsg(True, '删除{}数据库信息成功!'.format(ssh_ip))

    def ip_configuration_db_table_del(self):
        self.check_database()
        self.check_tables()
        plugin_dir = "/www/server/panel/plugin/ip_configuration"
        ip_configuration_db_path = os.path.join(plugin_dir, "ip_configuration.db")
        conn = None
        cur = None
        conn = sqlite3.connect(ip_configuration_db_path)
        cur = conn.cursor()
        del_exec = "DELETE FROM ssh_ip_log"
        cur.execute(del_exec)
        conn.commit()
        return public.returnMsg(True, '删除ssh_ip_log数据库表内信息成功!')
        

    def ip_configuration_db_query(self, ssh_ip):
        """
        查询数据库信息

        返回值说明：
        one_line_ip_value     IP储存整行数据，包括IP值、备注信息、操作时间
        ssh_allow_ip          IP值
        ssh_remask            备注信息
        ssh_add_time          操作时间
        """
        plugin_dir = "/www/server/panel/plugin/ip_configuration"
        ip_configuration_db_path = os.path.join(plugin_dir, "ip_configuration.db")
        if not self.check_database(): return public.returnMsg(False,'数据库创建失败！!')
        self.check_tables() 
        conn = None
        cur = None
        conn = sqlite3.connect(ip_configuration_db_path)
        cur = conn.cursor()
        query_exec = "select * from ssh_ip_log"
        results = cur.execute(query_exec).fetchall()
        one_line_ip_value = ""
        ssh_allow_ip = ""
        ssh_remask = ""
        ssh_add_time = ""
        result = cur.execute(query_exec).fetchall()
        for tmp_ip in result:
            if ssh_ip in tmp_ip:
                one_line_ip_value = tmp_ip
                ssh_allow_ip = tmp_ip[0]
                ssh_remask = tmp_ip[1]
                ssh_add_time = tmp_ip[2]
            if ssh_allow_ip:
                break
        return one_line_ip_value, ssh_allow_ip, ssh_remask, ssh_add_time
  
        
    def get_docker_network_list(self):
        """
        取docker网卡名列表
        """
        try:
            public.ExecShell('brctl show')
        except:
            return False
        try:
            docker_network_list = public.ExecShell("brctl show |grep -v bridge|awk '{print $1}'")[0].strip().split('\n')
        except:
            docker_network_list = []
        return docker_network_list
  
        
    def get_network_card_name_list(self):
        """
        取网卡设备名列表
        不统计在网卡列表内的字符如下：
        lo
        docker
        """
        if self.get_docker_network_list() != False:
            docker_network_list = self.get_docker_network_list()
        dev_name = public.ExecShell("ip add |grep BROADCAST|grep -v lo|grep -v docker |sed 's/://g'|awk '{print $2}'")[0].split()
        tmp_list = []
        for i in range(0,len(dev_name)):
            rep = 'docker'
            result = re.search(rep,dev_name[i])
            if not result:
                if docker_network_list != []: 
                    if dev_name[i] not in docker_network_list:
                        tmp_list.append(dev_name[i])
                else:
                    tmp_list.append(dev_name[i])
        return tmp_list            
        
    def get_ip_set_list(self,get):
        """
        ip设置接口返回信息
        """
        ip_set_list = {}
        network_card_lists = self.get_network_card_name_list()
        ip_set_list['net_card_list'] = network_card_lists
        if get.network_name == '':
            network_card_bind_ip_list,network_all_list = self.get_network_card_ip_list(network_name = network_card_lists[0])
        else:
            network_card_bind_ip_list,network_all_list = self.get_network_card_ip_list(network_name = get.network_name)
        if network_card_bind_ip_list == []:
            ip_set_list['ip_list'] = []
        else:
            ip_set_list['ip_list'] = network_card_bind_ip_list
        if get.network_name == '':
            default_network_card_data = self. get_default_network_card_list(network_name = network_card_lists[0])
        else:
            default_network_card_data = self. get_default_network_card_list(network_name = get.network_name)
        ip_set_list['net_card_data'] = default_network_card_data
        system_type = self.get_system()
        if system_type == 'centos':
            ip_set_list['system_type'] = True
        elif system_type == 'ubuntu':
            ip_set_list['system_type'] = True
        elif system_type == 'debian':
            ip_set_list['system_type'] = False
        return ip_set_list
    
    def get_network_card_ip_list(self,network_name):
        """
        取指定网卡设备绑定IP列表
        需要从前端获取网卡设备名，参数为network_name
        返回值，如
        {'network_card_name': 'eth0', 'data': ['172.16.0.5/20', '172.16.0.11/16']}
        """
        try:
            tmp_exec = 'ip add |grep '+network_name+'| grep inet'
            tmp_value = public.ExecShell(tmp_exec)
        except:
            tmp_list = []
            network_card_list = {}
            network_card_list['network_card_name'] = network_name
            network_card_list['data'] = tmp_list
            network_card_list = {'network_card_name':network_name,'data':tmp_list}
            network_card_list = []
            network_all_list = []
            return network_card_list,network_all_list
        tmp_value = str(tmp_value).split('\\n')
        tmp_list = []
        network_all_list = []
        network_card_list = []
        if len(tmp_value)>1:
            tmp_check_list = []
            for i in range(0,len(tmp_value)):
                tmp_dict = {}
                rep = r'inet'
                result = re.search(rep,tmp_value[i])
                if not result: continue
                tmp_index = tmp_value[i].split().index('inet')
                tmp_index = tmp_index+1
                tmp_value_c = tmp_value[i].split()[tmp_index]
                tmp_value_check = tmp_value_c.split('/')[0]
                net_netmask_num = tmp_value_c.split('/')[1]
                network_card_lists = self.get_network_card_name_list()
                netmask_value, netmask_num, ip_value, dev_name = self.get_default_netmask_value(dev_name=network_card_lists[0])
                if not tmp_value_check: continue
                network_all_list.append(tmp_value_check)
                if network_name == network_card_lists[0]:
                    if tmp_value_check == ip_value: continue
                tmp_check_list.append(tmp_value_check)
                tmp_dict['ip'] = tmp_value_check
                netmask_value=self.netmask_num_to_netmask_value(netmask_num=net_netmask_num)
                tmp_dict['netmask'] = netmask_value
                tmp_list.append(tmp_dict)
            if tmp_list == []:
                network_card_list = []
            else:
                network_card_list = tmp_list
        return network_card_list,network_all_list
        
    def get_dev_name_num(self):
        dev_name_list = self.get_network_card_name_list()
        if len(dev_name_list)>1:
            return False
        else:
            return True 
            
    def get_default_route(self,dev_name):
        """
        取网卡默认网关
        """
        tmp_exec = 'ip route | grep default | grep '+dev_name
        try:
            tmp_value = public.ExecShell(tmp_exec)[0].split('\n')
            if len(tmp_value)>1:
                default_route = str(tmp_value[1]).split()[2]
            else:
                default_route = public.ExecShell(tmp_exec)[0].split()[2]
        except:
            try:
                default_route = public.ExecShell(tmp_exec)[0].split()[2]
            except:
                default_route = ''
        system_type = self.get_system()
        if system_type == 'ubuntu':
            if default_route == '':
                try:
                    confpath = self.get_ubuntu_conf_file()
                    conf = public.readFile(confpath)
                    data=yaml.load(conf,Loader=yaml.FullLoader)
                    default_route = data['network']['ethernets'][dev_name]['gateway4']
                except:
                    default_route = ''
        return default_route

    def get_default_network_card_list(self,network_name):
        """
        out_ip 本机出口IP
        default_bind_ip 默认绑定IP
        network_id_num 网络ID的位数
        default_route 默认网关
        default_netmask 默认子网掩码
        """
        dev_name_list = self.get_network_card_name_list()
        tmp_dict = {}
        default_network_card_data = []
        netmask_value, netmask_num, ip_value, dev_namen = self.get_default_netmask_value(dev_name=network_name)
        dev_name = network_name
        default_netmask = netmask_value
        default_route = self.get_default_route(dev_name=network_name)
        is_ping = self.check_ping()
        if is_ping:
            tmp_value = public.ExecShell("curl http://www.bt.cn/api/getipaddress")
        else:
            tmp_value = ''
        if tmp_value == '':
            out_ip = ''
        else:
            out_ip = list(tmp_value)[0]
        default_bind_ip = ip_value
        network_id_num = netmask_num
        out_ip = public.GetLocalIp() if not out_ip else out_ip
        tmp_dict['out_ip'] = out_ip
        tmp_dict['default_bind_ip'] = default_bind_ip
        tmp_dict['network_id_num'] = network_id_num
        tmp_dict['default_route'] = default_route
        tmp_dict['default_netmask'] = default_netmask
        default_network_card_data.append(tmp_dict)
        return tmp_dict