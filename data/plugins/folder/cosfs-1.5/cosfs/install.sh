#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'

System_Lib(){
	if [ "${PM}" == "yum" ] || [ "${PM}" == "dnf" ] ; then
		Pack="automake gcc-c++ git libcurl-devel libxml2-devel fuse-devel make openssl-devel fuse"
	elif [ "${PM}" == "apt-get" ]; then
		Pack="automake autotools-dev g++ git libcurl4-gnutls-dev libfuse-dev libssl-dev libxml2-dev make pkg-config fuse"
	fi
	${PM} install ${Pack} -y
}
Cosfs_Install(){
	cd /www/server/panel/plugin/cosfs/
	unzip /www/server/panel/plugin/cosfs/cosfs-master.zip
	cd /www/server/panel/plugin/cosfs/cosfs-master
	./autogen.sh
	./configure
	make
	make install
	cd ..
	rm -rf cosfs-master*
	pip install cos-python-sdk-v5
	btpip install cos-python-sdk-v5
	mkdir -p /www/cosfs
	echo '安装完成' > $install_tmp
}

Uninstall_cosfs()
{
	rm -rf /www/server/panel/plugin/cosfs
}


actionType=$1
if [ "${actionType}" == "install" ];then
	System_Lib
	Cosfs_Install
else
	Uninstall_cosfs
fi