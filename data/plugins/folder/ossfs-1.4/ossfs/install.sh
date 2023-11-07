#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'

public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file
download_Url=$NODE_URL
System_Lib(){
	if [ "${PM}" == "yum" ] || [ "${PM}" == "dnf" ] ; then
		Pack="fuse-devel gcc-c++ autoconf automake libuuid-devel openssl-devel libcurl-devel fuse libxml2-devel automake make"
	elif [ "${PM}" == "apt-get" ]; then
		Pack="libfuse-dev fuse autoconf uuid-dev libssl-dev libcurl4-openssl-dev automake autotools-dev fuse g++ libcurl4-openssl-dev libxml2-dev make pkg-config"
	fi
	${PM} install ${Pack} -y
}
##  cosfs  s3fs  bosfs
# py libs

Install_s3fs(){
	#安装s3fs
	if [ -x "$(command -v s3fs)" ] && [ "repair" != "$1" ]; then
		echo "s3fs exist, skip..."
		return
	fi

	wget -O s3fs-fuse-1.92.tar.gz ${download_Url}/install/plugin/ossfs/s3fs-fuse-1.92.tar.gz
	tar xf s3fs-fuse-1.92.tar.gz
	cd s3fs-fuse-1.92
	./autogen.sh
	./configure
	make && make install
	cd ..
}

Install_cosfs(){
	if [ -x "$(command -v cosfs)" ] && [ "repair" != "$1" ]; then
		echo "cosfs exist, skip..."
		return
	fi
	wget -O cosfs-1.0.20.tar.gz ${download_Url}/install/plugin/ossfs/cosfs-1.0.20.tar.gz
	tar xf cosfs-1.0.20.tar.gz
	cd cosfs-1.0.20
	./autogen.sh
	./configure
	make && make install
	cd ..
}

Install_bosfs(){
	if [ -x "$(command -v bosfs)" ] && [ "repair" != "$1" ]; then
		echo "bosfs exist, skip..."
		return
	fi
	wget -O bosfs-1.0.0.13.2.tar.gz ${download_Url}/install/plugin/ossfs/bosfs-1.0.0.13.2.tar.gz
	tar xf bosfs-1.0.0.13.2.tar.gz
	cd bosfs-1.0.0.13.2
	sh build.sh
	cd ..
}


Install_Ossfs(){

	#安装cosfs
	mkdir -p /www/ossfs
	mkdir -p /www/server/panel/plugin/ossfs

	Install_s3fs $1

	Install_bosfs $1

	Install_cosfs $1

	btpip install bce-python-sdk cos-python-sdk-v5 oss2 boto3 ks3sdk esdk-obs-python
	# clear
	rm -rf bosfs-* cosfs-* s3fs-*

	echo '安装完成'
}

Uninstall_Ossfs()
{
	rm -rf /www/server/panel/plugin/ossfs
}


actionType=$1
if [ "${actionType}" == "install" ];then
	System_Lib
	Install_Ossfs
elif [ "${actionType}" == "repair" ];then
	System_Lib
	Install_Ossfs $1
else
	Uninstall_Ossfs
fi