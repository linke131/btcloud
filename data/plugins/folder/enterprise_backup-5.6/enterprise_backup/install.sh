#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

install_tmp='/tmp/bt_install.pl'

pluginPath=/www/server/panel/plugin/enterprise_backup

pyVersion=$(python -c 'import sys;print(sys.version_info[0]);')

cpu_arch=`arch`

# Install_Xtrabackup()
# {
#   if [ -f "/etc/redhat-release" ];then
#     CENTOS_OS=$(cat /etc/redhat-release|grep  -oEi centos)
#     if [ "${CENTOS_OS}" ];then
#       el=$(cat /etc/redhat-release|grep -oE "([6-8]\.)+[0-9]+"|cut -f1 -d ".")
#       if [ "${el}" == "7" ] || [ "${el}" == "8" ];then
#           OS_SYS="centos"
#           OS_VER="${el}"
#       fi 
#     fi
#   else
#     UBUNTU_VER=$(cat /etc/issue|grep -i ubuntu|awk '{print $2}'|cut -d. -f1)
#     DEBIAN_VER=$(cat /etc/issue|grep -i debian|awk '{print $3}')
#     if [ "${UBUNTU_VER}" == "18" ] || [ "${UBUNTU_VER}" == "20" ] || [ "${UBUNTU_VER}" == "22" ];then
#       OS_SYS="ubuntu"
#       OS_VER="${UBUNTU_VER}"
#     elif [ "${DEBIAN_VER}" == "10" ] || [ "${DEBIAN_VER}" == "11" ]; then
#       OS_SYS="debian"
#       OS_VER="${DEBIAN_VER}"
#     fi
#   fi

#   if [ "${OS_VER}" ];then
#     #下载安装代码
#   fi
# }

Install()
{
  if [[ $cpu_arch != "x86_64" ]];then
    echo '不支持非x86架构的系统安装'
    exit 0
  fi
  if [ -f "/usr/bin/apt-get" ];then
    apt install pigz -y
    apt install openssl -y
  elif [ -f "/usr/bin/yum" ];then
    yum install pigz -y
    yum install openssl -y
  fi
  mkdir -p $pluginPath
  mkdir -p $pluginPath/crontab_tasks
  mkdir -p $pluginPath/config
  \mv -f /www/server/panel/data/enterprise_backup_config/* $pluginPath/config

  echo > $pluginPath/enterprise_backup_main.py
  echo '正在安装脚本文件...' > $install_tmp
  if [  -f /www/server/panel/pyenv/bin/python ];then
    btpip install oss2
    btpip install qiniu==7.4.1 -I
    btpip install cos-python-sdk-v5
    btpip install boto3
  else
    if [ "$pyVersion" == 2 ];then
      /usr/bin/pip install oss2
      /usr/bin/pip install qiniu==7.4.1 -I
      /usr/bin/pip install cos-python-sdk-v5
      /usr/bin/pip install boto3
    else
      /usr/bin/pip3 install oss2
      /usr/bin/pip3 install qiniu==7.4.1 -I
      /usr/bin/pip3 install cos-python-sdk-v5
      /usr/bin/pip3 install boto3
    fi
  fi

  find $pluginPath -name "*.so" | xargs rm -f 
  \cp -a -r $pluginPath/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-enterprise_backup.png
  echo '安装完成' > $install_tmp
}

Uninstall()
{
  mkdir -p /www/server/panel/data/enterprise_backup_config
  \mv -f $pluginPath/config/* /www/server/panel/data/enterprise_backup_config
  rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
  Install
elif  [ "${1}" == 'update' ];then
  Install
elif [ "${1}" == 'uninstall' ];then
  Uninstall
fi
