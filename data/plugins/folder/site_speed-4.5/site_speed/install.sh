#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
os_bit=$(getconf LONG_BIT)
is_arm=$(uname -a|grep -E 'aarch64|arm|ARM')

if [ "$os_bit" = "32" ] || [ "$is_arm" != "" ];then
	echo "========================================="
	grep "English" /www/server/panel/config/config.json > /dev/null
	if [ "$?" -ne 0 ];then
	  echo "错误: 不支持32位和ARM/AARCH64平台的系统!"
	else
	  echo "Error: 32-bit and ARM/AARCH64 platform systems are not supported!"
	fi
	echo "========================================="
	exit 0;
fi

pluginPath=/www/server/panel/plugin/site_speed
extFile=""
version=""
download_Url=https://download.bt.cn

Install_site_speed()
{
	sp_path=/www/server/speed
	mkdir -p $sp_path/total
	mkdir -p $pluginPath

	Install_cjson
	Install_socket
	Install_mod_lua
	Install_gzip_mod


	speed_conf_file=/www/server/panel/vhost/nginx/speed.conf
	m=$(cat $speed_conf_file|grep lua_shared_dict)
	if [ "$m" == "" ];then
		m="lua_shared_dict site_cache 64m;"
	fi
	\cp -f $pluginPath/speed.conf $speed_conf_file
	sed -i "s/^lua_shared_dict.*/$m/" $speed_conf_file

	\cp -f $pluginPath/speed/cookie.lua $sp_path/cookie.lua 
	\cp -f $pluginPath/speed/ffi-zlib.lua $sp_path/ffi-zlib.lua
	\cp -f $pluginPath/speed/speed.lua $sp_path/speed.lua
	\cp -f $pluginPath/speed/nginx_get.lua $sp_path/nginx_get.lua
	\cp -f $pluginPath/speed/nginx_set.lua $sp_path/nginx_set.lua
	\cp -f $pluginPath/speed/httpd_speed.lua $sp_path/httpd_speed.lua
	\cp -f $pluginPath/speed/memcached.lua $sp_path/memcached.lua
	\cp -f $pluginPath/speed/CRC32.lua $sp_path/CRC32.lua
	speed_conf_file=/www/server/panel/vhost/apache/speed.conf
	\cp -f $pluginPath/speed_httpd.conf $speed_conf_file
	if [ ! -f $sp_path/config.lua ];then
		\cp -f $pluginPath/speed/config.lua $sp_path/config.lua
	fi

	ng_waf_file=/www/server/panel/vhost/nginx/btwaf.conf
	if [ -f $ng_waf_file ];then
		sed -i "s/^body_filter_by_lua_file/#body_filter_by_lua_file/" $ng_waf_file
	fi

	waf_file=/www/server/panel/vhost/apache/btwaf.conf
	if [ ! -f $waf_file ];then
		echo "LoadModule lua_module modules/mod_lua.so" > $waf_file
	fi
	chattr +i $waf_file
	mkdir -p /www/server/panel/plugin/btwaf_httpd

	# 卸载旧版本网站加速
	site_cache_path=/www/server/panel/plugin/site_cache
	if [ -f $site_cache/info.json ];then
		wget -O $site_cache/install.sh https://download.bt.cn/install/plugin/site_cache/install.sh -T 5
		bash $site_cache/install.sh uninstall
	fi

	chown -R www:www $sp_path
	chmod -R 755 $sp_path

	if [ -f /etc/init.d/nginx ];then
		/etc/init.d/nginx reload
	else
		/etc/init.d/httpd reload
	fi
	echo > /www/server/panel/data/reload.pl
	echo 'Successify'
}


Uninstall_site_speed()
{
	rm -rf $pluginPath
	rm -rf /www/server/speed

	ng_waf_file=/www/server/panel/vhost/nginx/btwaf.conf
	if [ -f $ng_waf_file ];then
		sed -i "s/^#body_filter_by_lua_file/body_filter_by_lua_file/" $ng_waf_file 
	fi

	speed_conf_file=/www/server/panel/vhost/nginx/speed.conf
	if [ -f $speed_conf_file ];then
		rm -f $speed_conf_file
	fi

	speed_conf_file=/www/server/panel/vhost/apache/speed.conf
	if [ -f $speed_conf_file ];then
		rm -f $speed_conf_file
	fi
	
	if [ -f /etc/init.d/nginx ];then
		/etc/init.d/nginx reload
	else
		/etc/init.d/httpd reload
	fi
}

Install_gzip_mod()
{
	gzip_so=/www/server/speed/gzip.so
	if [ ! -f $gzip_so ];then
		set_include_path
		wget -O lua-gzip-master.zip $download_Url/src/lua-gzip-master.zip -T 20
		unzip lua-gzip-master.zip
		rm -f lua-gzip-master.zip
		cd lua-gzip-master
		make
		mkdir /www/server/speed
		\cp -arf gzip.so $gzip_so
		cd ..
		rm -rf lua-gzip-master
	fi
}

Install_cjson()
{
	if [ -f /usr/bin/yum ];then
		isInstall=`rpm -qa |grep lua-devel`
		if [ "$isInstall" == "" ];then
			yum install lua lua-devel -y
		fi
	else
		isInstall=`dpkg -l|grep liblua5.1-0-dev`
		if [ "$isInstall" == "" ];then
			apt-get install lua5.1 lua5.1-dev lua5.1-cjson lua5.1-socket -y
		fi
	fi
	
	if [ -f /etc/redhat-release ];then
		Centos8Check=$(cat /etc/redhat-release | grep ' 8.' | grep -iE 'centos|Red Hat')
		if [ "${Centos8Check}" ];then
			yum install lua-socket -y
			if [ ! -f /usr/lib/lua/5.3/cjson.so ];then
				wget -O lua-5.3-cjson.tar.gz $download_Url/src/lua-5.3-cjson.tar.gz -T 20
				tar -xvf lua-5.3-cjson.tar.gz
				cd lua-5.3-cjson
				make
				make install
				ln -sf /usr/lib/lua/5.3/cjson.so /usr/lib64/lua/5.3/cjson.so
				cd ..
				rm -f lua-5.3-cjson.tar.gz
				rm -rf lua-5.3-cjson
				return
			fi
		fi
	fi

	if [ ! -f /usr/local/lib/lua/5.1/cjson.so ];then
		set_include_path
		wget -O lua-cjson-2.1.0.tar.gz $download_Url/install/src/lua-cjson-2.1.0.tar.gz -T 20
		tar xvf lua-cjson-2.1.0.tar.gz
		rm -f lua-cjson-2.1.0.tar.gz
		cd lua-cjson-2.1.0
		make clean
		make
		make install
		cd ..
		rm -rf lua-cjson-2.1.0
		ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so
		ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
	else
		if [ -d "/usr/lib64/lua/5.1" ];then
			ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so
		fi

		if [ -d "/usr/lib/lua/5.1" ];then
			ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
		fi
	fi
}


Install_socket()
{

	if [ ! -f /usr/local/lib/lua/5.1/socket/core.so ];then
		set_include_path
		wget -O luasocket-master.zip $download_Url/install/src/luasocket-master.zip -T 20
		unzip luasocket-master.zip
		rm -f luasocket-master.zip
		cd luasocket-master
		make
		make install
		cd ..
		rm -rf luasocket-master
	fi

	if [ ! -d /usr/share/lua/5.1/socket ]; then
		if [ -d /usr/lib64/lua/5.1 ];then
			rm -rf /usr/lib64/lua/5.1/socket /usr/lib64/lua/5.1/mime
			ln -sf /usr/local/lib/lua/5.1/socket /usr/lib64/lua/5.1/socket
			ln -sf /usr/local/lib/lua/5.1/mime /usr/lib64/lua/5.1/mime
		else
			rm -rf /usr/lib/lua/5.1/socket /usr/lib/lua/5.1/mime
			mkdir -p /usr/lib/lua/5.1/
			ln -sf /usr/local/lib/lua/5.1/socket /usr/lib/lua/5.1/socket
			ln -sf /usr/local/lib/lua/5.1/mime /usr/lib/lua/5.1/mime
		fi
		rm -rf /usr/share/lua/5.1/mime.lua /usr/share/lua/5.1/socket.lua /usr/share/lua/5.1/socket
		mkdir -p /usr/share/lua/5.1
		ln -sf /usr/local/share/lua/5.1/mime.lua /usr/share/lua/5.1/mime.lua
		ln -sf /usr/local/share/lua/5.1/socket.lua /usr/share/lua/5.1/socket.lua
		ln -sf /usr/local/share/lua/5.1/socket /usr/share/lua/5.1/socket
	fi
}

Install_mod_lua()
{
	if [ ! -f /www/server/apache/bin/httpd ];then
		return 0;
	fi

	if [ -f /www/server/apache/modules/mod_lua.so ];then
		return 0;
	fi
	cd /www/server/apache
	if [ ! -d /www/server/apache/src ];then
		wget -O httpd-2.4.33.tar.gz $download_Url/src/httpd-2.4.33.tar.gz -T 20
		tar xvf httpd-2.4.33.tar.gz
		rm -f httpd-2.4.33.tar.gz
		mv httpd-2.4.33 src
		cd /www/server/apache/src/srclib
		wget -O apr-1.6.3.tar.gz $download_Url/src/apr-1.6.3.tar.gz
		wget -O apr-util-1.6.1.tar.gz $download_Url/src/apr-util-1.6.1.tar.gz
		tar zxf apr-1.6.3.tar.gz
		tar zxf apr-util-1.6.1.tar.gz
		mv apr-1.6.3 apr
		mv apr-util-1.6.1 apr-util
	fi
	cd /www/server/apache/src
	./configure --prefix=/www/server/apache --enable-lua
	cd modules/lua
	make
	make install

	if [ ! -f /www/server/apache/modules/mod_lua.so ];then
		echo 'Error: mod_lua安装失败!';
		exit 0;
	fi
}

set_include_path()
{
	if [ -d /usr/include/lua5.1 ];then
		C_INCLUDE_PATH=/usr/include/lua5.1/
		export C_INCLUDE_PATH
	fi
}


action=$1
if [ "${1}" == 'install' ];then
	Install_site_speed
else
	Uninstall_site_speed
fi
