#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
Install_GDrive()
{

tmp_ping=`ping -c 1 -w 1 google.com 2>&1`
if [ $? -eq 0 ];then
    tmp=`python -V 2>&1|awk '{print $2}'`
    pVersion=${tmp:0:3}
    if [ -f "/usr/bin/btpip" ];then
      tmp=$(btpip list|grep google-api-python-client|awk '{print $2}')
      if [ $tmp != '2.39.0' ];then
        btpip install --upgrade google-api-python-client
        btpip uninstall google-api-python-client -y
        btpip install -I google-api-python-client==2.39.0 -i https://pypi.Python.org/simple
      fi
      tmp=$(btpip list|grep google-auth-httplib2|awk '{print $2}')
      if [ $tmp != '0.1.0' ];then
        btpip uninstall google-auth-httplib2 -y
        btpip install -I google-auth-httplib2==0.1.0 -i https://pypi.Python.org/simple
      fi
      tmp=$(btpip list|grep google-auth-oauthlib|awk '{print $2}')
      if [ $tmp != '0.5.0' ];then
        btpip uninstall google-auth-oauthlib -y
        btpip install -I google-auth-oauthlib==0.5.0 -i https://pypi.Python.org/simple
      fi
      tmp=$(btpip list|grep -E '^httplib2'|awk '{print $2}')
      if [ $tmp != '0.18.1' ];then
        btpip uninstall httplib2 -y
        btpip install -I httplib2==0.18.1 -i https://pypi.Python.org/simple
      fi
    else
      pip install -I pyOpenSSL
      pip install -I google-api-python-client==2.39.0 google-auth-httplib2==0.1.0 google-auth-oauthlib==0.5.0 -i https://pypi.Python.org/simple
      pip install -I httplib2==0.18.1 -i https://pypi.Python.org/simple
    fi
    echo '正在安装脚本文件...' > $install_tmp
    \cp -rp /www/server/panel/plugin/gdrive/credentials.json /root/credentials.json
    \cp -rp /www/server/panel/plugin/gdrive/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-gdrive.png
    ln -sf /www/server/panel/plugin/gdrive/credentials.json /root/credentials.json
    echo '安装完成' > $install_tmp
else
    echo '服务器连接不上谷歌云！安装失败！' > $install_tmp
    exit 1
}

Uninstall_GDrive()
{
	rm -rf /www/server/panel/plugin/gdrive
	rm -f /www/server/panel/script/backup_gdrive.py
	echo '卸载完成' > $install_tmp
}


action=$1
if [ "${1}" == 'install' ];then
	Install_GDrive
	echo '1' > /www/server/panel/data/reload.pl
else
	Uninstall_GDrive
fi
