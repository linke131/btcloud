#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath=/www/server/panel/plugin/btwaf
remote_dir="total2"
pyVersion=$(python -c 'import sys;print(sys.version_info[0]);')
py_zi=$(python -c 'import sys;print(sys.version_info[1]);')
pluginPath2=/www/server/panel/plugin/webshell_san
aacher=$(uname -a |grep -Po aarch64|awk 'NR==1')
Centos6Check=$(cat /etc/redhat-release|grep ' 6.'|grep -i centos)


Get_platform()
{
    case $(uname -s 2>/dev/null) in
        Linux )                    echo "linux" ;;
        FreeBSD )                  echo "freebsd" ;;
        *BSD* )                    echo "bsd" ;;
        Darwin )                   echo "macosx" ;;
        CYGWIN* | MINGW* | MSYS* ) echo "mingw" ;;
        AIX )                      echo "aix" ;;
        SunOS )                    echo "solaris" ;;
        * )                        echo "unknown"
    esac
}
Remove_path()
{
    local prefix=$1
    local new_path
    new_path=$(echo "${PATH}" | sed \
        -e "s#${prefix}/[^/]*/bin[^:]*:##g" \
        -e "s#:${prefix}/[^/]*/bin[^:]*##g" \
        -e "s#${prefix}/[^/]*/bin[^:]*##g")
    export PATH="${new_path}"
}
Add_path()
{
    local prefix=$1
    local new_path
    new_path=$(echo "${PATH}" | sed \
        -e "s#${prefix}/[^/]*/bin[^:]*:##g" \
        -e "s#:${prefix}/[^/]*/bin[^:]*##g" \
        -e "s#${prefix}/[^/]*/bin[^:]*##g")
    export PATH="${prefix}:${new_path}"
}

Get_lua_version(){
    echo `lua -e 'print(_VERSION:sub(5))'`
}


Install_LuaJIT()
{	
	LUAJIT_VER="2.1.0-beta3"
	LUAJIT_INC_PATH="luajit-2.1"
	if [ ! -f '/usr/local/lib/libluajit-5.1.so' ] || [ ! -f "/usr/local/include/${LUAJIT_INC_PATH}/luajit.h" ];then
		#wget -c -O LuaJIT-${LUAJIT_VER}.tar.gz ${download_Url}/install/src/LuaJIT-${LUAJIT_VER}.tar.gz -T 10
		cd $pluginPath && tar xvf $pluginPath/LuaJIT-${LUAJIT_VER}.tar.gz
		cd $pluginPath/LuaJIT-${LUAJIT_VER}
		make linux
		make install
		cd ..
		rm -rf LuaJIT-*
		export LUAJIT_LIB=/usr/local/lib
		export LUAJIT_INC=/usr/local/include/${LUAJIT_INC_PATH}/
		ln -sf /usr/local/lib/libluajit-5.1.so.2 /usr/local/lib64/libluajit-5.1.so.2
		echo "/usr/local/lib" >> /etc/ld.so.conf
		ldconfig
	fi
}


Install_lua515(){
    local install_path="/www/server/btwaf/lua515"
    
    local version
    version=$(Get_lua_version)

    echo "Current lua version: "$version
    if  [ -d "${install_path}/bin" ]
    then
        Add_path "${install_path}/bin"
        echo "Lua 5.1.5 has installed."
		return 1
    fi
    
    local lua_version="lua-5.1.5"
    local package_name="${lua_version}.tar.gz"
    mkdir -p $install_path
	cd $pluginPath
    tar xvzf $pluginPath/$package_name
    cd $lua_version
    platform=$(Get_platform)
    if [ "${platform}" = "unknown" ] 
    then
        platform="linux"
    fi
    make "${platform}" install INSTALL_TOP=$install_path
    Add_path "${install_path}/bin"
    #rm -rf "${pluginPath}/${lua_version}*"

    version=$(Get_lua_version)
    if [ ${version} == "5.1" ]
    then
        echo "Lua 5.1.5 has installed."
        return 1
    fi
    return 0
}


Install_sqlite3_for_nginx()
{

    if [ true ];then
	   cd $pluginPath
        tar xf $pluginPath/luarocks-3.5.0.tar.gz
	    cd $pluginPath/luarocks-3.5.0
	    ./configure --with-lua-include=/www/server/btwaf/lua515/include --with-lua-bin=/www/server/btwaf/lua515/bin
	    make -I/www/server/btwaf/lua515/bin
	    make install 
    fi

    if [ true ];then
        yum install -y sqlite-devel 

        apt install -y libsqlite3-dev
        cd $pluginPath && unzip $pluginPath/lsqlite3_fsl09y.zip && cd lsqlite3_fsl09y && make
        if [ -f '/www/server/panel/plugin/btwaf/lsqlite3_fsl09y/lsqlite3.so' ];then
		    echo "sqlite3安装成功"
            \cp -a -r $pluginPath/lsqlite3_fsl09y/lsqlite3.so /www/server/btwaf/lsqlite3.so
			chmod 755 /usr/local/lib/lua/5.1/lsqlite3.so
        else
			echo "sqlite3解压失败"
        fi
    fi
    if [ -f /usr/local/lib/lua/5.1/cjson.so ];then
        is_jit_cjson=$(luajit -e "require 'cjson'" 2>&1|grep 'undefined symbol: luaL_setfuncs')
        if [ "$is_jit_cjson" != "" ];then
            cd /tmp
            luarocks install lua-cjson
        fi
    fi
	chmod 755 /www/server/btwaf/lsqlite3.so
}


install_mbd(){
	#如果没有文件
	echo ""
}


Install_white_ip()
{
cat >$pluginPath/white.py<< EOF
# coding: utf-8
import sys,os
sys.path.append('/www/server/panel/class')
os.chdir('/www/server/panel')
import json

def ReadFile(filename,mode = 'r'):
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    import os
    if not os.path.exists(filename): return False
    fp = None
    try:
        fp = open(filename, mode)
        f_body = fp.read()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode,encoding="utf-8",errors='ignore')
                f_body = fp.read()
            except:
                fp = open(filename, mode,encoding="GBK",errors='ignore')
                f_body = fp.read()
        else:
            return False
    finally:
        if fp and not fp.closed:
            fp.close()
    return f_body

def WriteFile(filename,s_body,mode='w+'):
    """
    写入文件内容
    @filename 文件名
    @s_body 欲写入的内容
    return bool 若文件不存在则尝试自动创建
    """
    try:
        fp = open(filename, mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode,encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False 
def ip2long(ip):
    ips = ip.split('.')
    if len(ips) != 4: return 0
    iplong = 2 ** 24 * int(ips[0]) + 2 ** 16 * int(ips[1]) + 2 ** 8 * int(ips[2]) + int(ips[3])
    return iplong
def zhuanhuang(aaa):
    ac = []
    cccc = 0
    list = []
    list2 = []
    for i in range(len(aaa)):
        for i2 in aaa[i]:
            dd = ''
            coun = 0
            for i3 in i2:
                if coun == 3:
                    dd += str(i3)
                else:
                    dd += str(i3) + '.'
                coun += 1
            list.append(ip2long(dd))
            cccc += 1
            if cccc % 2 == 0:
                aa = []
                bb = []
                aa.append(list[0])
                bb.append(list[1])
                cc = []
                cc.append(aa)
                cc.append(bb)
                ac.append(list)
                list = []
                list2 = []
    return ac
def main():
    try:
        aaa = json.loads(ReadFile("/www/server/btwaf/rule/ip_white.json"))
        if not aaa:return  False
        if type(aaa[0][0])==list:
            f = open('/www/server/btwaf/rule/ip_white.json', 'w')
            f.write(json.dumps(zhuanhuang(aaa)))
            f.close()
    except:
        WriteFile("/www/server/btwaf/rule/ip_white.json", json.dumps([]))

    try:
        aaa = json.loads(ReadFile("/www/server/btwaf/rule/ip_black.json"))
        if not aaa: return False
        if type(aaa[0][0]) == list:
            f = open('/www/server/btwaf/rule/ip_black.json', 'w')
            f.write(json.dumps(zhuanhuang(aaa)))
            f.close()
    except:
        WriteFile("/www/server/btwaf/rule/ip_black.json", json.dumps([]))
main()

def to_info():
    try:
        import PluginLoader,public
        get = public.dict_obj()
        get.plugin_get_object = 1
        fun_obj = PluginLoader.plugin_run("btwaf", "get_total_all", get)
        gets = public.dict_obj()
        fun_obj(gets)
        fun_obj = PluginLoader.plugin_run("btwaf", "get_site_config", get)
        fun_obj(gets)
    except:
        pass
to_info()
print("转换ip格式")
EOF
}


Install_btwaf()
{ 
	mkdir $pluginPath2
	mkdir -p $pluginPath
	if [ -d '/www/server/btwaf/' ];then
		echo ""
	else 
		mkdir -p /www/server/btwaf/
	fi 
	wget -O $pluginPath/btwaf_static.zip  http://download.bt.cn/btwaf_rule/btwaf_static.zip
	count=`ls -l /www/server/panel/plugin/btwaf/btwaf_static.zip | awk '{print $5}'`

	if [ "$count" -lt 32564250 ];then
		echo '下载失败' > $install_tmp
		echo 'ERROR:安装失败' > $install_tmp
	fi 
	if [ -d $pluginPath/btwaf_static ];then
		rm -rf $pluginPath/btwaf_static
	fi
	
	cd $pluginPath  && unzip $pluginPath/btwaf_static.zip
	
	if [ -d $pluginPath/btwaf_static ];then
		echo "解压成功"
	else
		echo '解压失败' > $install_tmp
		echo 'ERROR:安装失败' > $install_tmp
	fi
	
	#覆盖静态文件
	rm -rf $pluginPath/static/src $pluginPath/static/fonts  $pluginPath/static/moment $pluginPath/static/img $pluginPath/static/esri $pluginPath/static/dojo
	mv $pluginPath/btwaf_static/static/src $pluginPath/static/
	mv $pluginPath/btwaf_static/static/moment $pluginPath/static/
	#mv $pluginPath/btwaf_static/static/esri $pluginPath/static/
	#mv $pluginPath/btwaf_static/static/dojo $pluginPath/static/
	mv $pluginPath/btwaf_static/static/img $pluginPath/static/
	mv $pluginPath/btwaf_static/static/fonts $pluginPath/static/

	rm -rf $pluginPath/btwaf_static/static
	mv -f $pluginPath/btwaf_static/* $pluginPath/
	rm -rf $pluginPath/btwaf_static/
	
	#覆盖
	rm -rf $pluginPath/btwaf_static.zip
	
	mv -f $pluginPath/GeoLite2-Country.mmdb  /www/server/btwaf/GeoLite2-Country.mmdb
	mv -f  $pluginPath/GeoLite2-City.mmdb /www/server/btwaf/GeoLite2-City.mmdb
	
	
	if [ -f /www/server/btwaf/httpd.lua ];then
		rm -rf /www/server/btwaf
	fi
	
	
	
	en=''
	grep "English" /www/server/panel/config/config.json >> /dev/null
	if [ "$?" -eq 0 ];then
		en='_en'
	fi
	usranso2=`ls -l /usr/local/lib/lua/5.1/cjson.so | awk '{print $5}'`
	if [ $usranso2 -eq 0 ];then
		rm -rf /usr/local/lib/lua/5.1/cjson.so
	fi
	rm -rf /www/server/panel/vhost/nginx/free_waf.conf
	rm -rf /www/server/free_waf
	rm -rf /www/server/panel/plugin/free_waf
	yum install sqlite-devel -y
	apt install sqlite-devel libreadline-dev -y 
	#Install_socket


	yum install lua-socket readline-devel -y
	yum install lua-json  -y 
	apt-get install lua-socket -y
	apt-get install lua-cjson -y
	Install_cjson
	#Install_luarocks
	Install_lua515
	Install_sqlite3_for_nginx
	echo '正在安装脚本文件...' > $install_tmp
	Install_white_ip
	python $pluginPath/send_vilidate.py
	python $pluginPath/black.py
	if [ ! -f /www/server/btwaf/captcha/num2.json ];then
		unzip -o $pluginPath/captcha.zip  -d /www/server/btwaf/ > /dev/null
		rm -rf $pluginPath/captcha.zip
	fi
	if [ ! -f /www/server/panel/vhost/nginx/speed.conf ];then
		\cp -a -r $pluginPath/btwaf.conf  /www/server/panel/vhost/nginx/btwaf.conf
	else
		\cp -a -r $pluginPath/btwaf2.conf  /www/server/panel/vhost/nginx/btwaf.conf
	fi
	rm -rf $pluginPath2/webshell_san_main.py
	#cp -a -r  $pluginPath/webshell_san_main.py $pluginPath2/webshell_san_main.py
	\cp -a -r /www/server/panel/plugin/btwaf/icon.png /www/server/panel/static/img/soft_ico/ico-btwaf.png
	btwaf_path=/www/server/btwaf
	mkdir -p $btwaf_path/html
	rm -rf /www/server/btwaf/cms
	mv $pluginPath/btwaf_lua/cms/  $btwaf_path
	
	rm -rf $btwaf_path/xss_parser
	#mv $pluginPath/btwaf_lua/xss_parser $btwaf_path
	
	if [ ! -f $btwaf_path/html/url.html ];then
		\cp -a -r $pluginPath/btwaf_lua/html/url.html $btwaf_path/html/url.html
		\cp -a -r $pluginPath/btwaf_lua/html/ip.html $btwaf_path/html/ip.html
	fi
	
	if [ ! -f $btwaf_path/html/get.html ];then
		\cp -a -r $pluginPath/btwaf_lua/html/get.html $btwaf_path/html/get.html
		\cp -a -r $pluginPath/btwaf_lua/html/get.html $btwaf_path/html/post.html
		\cp -a -r $pluginPath/btwaf_lua/html/get.html $btwaf_path/html/cookie.html
		\cp -a -r $pluginPath/btwaf_lua/html/get.html $btwaf_path/html/user_agent.html
		\cp -a -r $pluginPath/btwaf_lua/html/get.html $btwaf_path/html/other.html
	fi
	mkdir -p $btwaf_path/rule
	\cp -a -r $pluginPath/btwaf_lua/rule/cn.json $btwaf_path/rule/cn.json
	\cp -a -r $pluginPath/btwaf_lua/rule/lan.json $btwaf_path/rule/lan.json

	mkdir  /www/server/btwaf/js
	chown www:www /www/server/btwaf/js
	\cp -a -r $pluginPath/btwaf_lua/js/fingerprint2.js $btwaf_path/js/fingerprint2.js



	if [ ! -f $btwaf_path/rule/post.json ];then
		\cp -a -r $pluginPath/btwaf_lua/rule/url.json $btwaf_path/rule/url.json
		\cp -a -r $pluginPath/btwaf_lua/rule/args.json $btwaf_path/rule/args.json
		\cp -a -r $pluginPath/btwaf_lua/rule/post.json $btwaf_path/rule/post.json
		\cp -a -r $pluginPath/btwaf_lua/rule/cookie.json $btwaf_path/rule/cookie.json
		\cp -a -r $pluginPath/btwaf_lua/rule/head_white.json $btwaf_path/rule/head_white.json
		\cp -a -r $pluginPath/btwaf_lua/rule/user_agent.json $btwaf_path/rule/user_agent.json
		\cp -a -r $pluginPath/btwaf_lua/rule/cn.json $btwaf_path/rule/cn.json
		\cp -a -r $pluginPath/btwaf_lua/rule/ip_white.json $btwaf_path/rule/ip_white.json
		\cp -a -r $pluginPath/btwaf_lua/rule/scan_black.json $btwaf_path/rule/scan_black.json
		\cp -a -r $pluginPath/btwaf_lua/rule/url_black.json $btwaf_path/rule/url_black.json
		\cp -a -r $pluginPath/btwaf_lua/rule/ip_black.json $btwaf_path/rule/ip_black.json
		\cp -a -r $pluginPath/btwaf_lua/rule/url_white.json $btwaf_path/rule/url_white.json
		\cp -a -r $pluginPath/btwaf_lua/1.json $btwaf_path/1.json
		\cp -a -r $pluginPath/btwaf_lua/2.json $btwaf_path/2.json
		\cp -a -r $pluginPath/btwaf_lua/3.json $btwaf_path/3.json
		\cp -a -r $pluginPath/btwaf_lua/4.json $btwaf_path/4.json
		\cp -a -r $pluginPath/btwaf_lua/5.json $btwaf_path/5.json
		\cp -a -r $pluginPath/btwaf_lua/6.json $btwaf_path/6.json
		\cp -a -r $pluginPath/btwaf_lua/zhi.json $btwaf_path/zhi.json
	fi
	if [ ! -f $btwaf_path/rule/url_white_senior.json ];then
		\cp -a -r $pluginPath/btwaf_lua/rule/url_white_senior.json $btwaf_path/rule/url_white_senior.json
	fi
	\cp -a -r $pluginPath/btwaf_lua/rule/args.json $btwaf_path/rule/args.json
	\cp -a -r $pluginPath/btwaf_lua/rule/post.json $btwaf_path/rule/post.json
	\cp -a -r $pluginPath/btwaf_lua/rule/url.json $btwaf_path/rule/url.json
	\cp -a -r $pluginPath/btwaf_lua/rule/cookie.json $btwaf_path/rule/cookie.json
	\cp -a -r $pluginPath/btwaf_lua/rule/user_agent.json $btwaf_path/rule/user_agent.json
	
	\cp -a -r $pluginPath/btwaf_lua/1.json $btwaf_path/1.json
	\cp -a -r $pluginPath/btwaf_lua/2.json $btwaf_path/2.json
	\cp -a -r $pluginPath/btwaf_lua/3.json $btwaf_path/3.json
	\cp -a -r $pluginPath/btwaf_lua/4.json $btwaf_path/4.json
	\cp -a -r $pluginPath/btwaf_lua/5.json $btwaf_path/5.json
	\cp -a -r $pluginPath/btwaf_lua/6.json $btwaf_path/6.json
	\cp -a -r $pluginPath/btwaf_lua/7.json $btwaf_path/7.json
	\cp -a -r $pluginPath/btwaf_lua/zhi.json $btwaf_path/zhi.json
	if [ ! -f $btwaf_path/webshell.json ];then
		\cp -a -r $pluginPath/btwaf_lua/webshell.json $btwaf_path/webshell.json
	fi
	
	if [ ! -f $btwaf_path/webshell_url.json ];then
		\cp -a -r $pluginPath/btwaf_lua/webshell_url.json $btwaf_path/webshell_url.json
	fi
	
	#\cp -a -r $pluginPath/GeoLite2-Country.mmdb $btwaf_path/GeoLite2-Country.mmdb
	
	if [ ! -f $btwaf_path/shell_check.json ];then
		\cp -a -r $pluginPath/btwaf_lua/shell_check.json $btwaf_path/shell_check.json
	fi
	
	if [ ! -f $btwaf_path/rule/cc_uri_white.json ];then
		\cp -a -r $pluginPath/btwaf_lua/rule/cc_uri_white.json $btwaf_path/rule/cc_uri_white.json
	fi
	
	if [ ! -f $btwaf_path/rule/reg_tions.json ];then
		\cp -a -r $pluginPath/btwaf_lua/rule/reg_tions.json $btwaf_path/rule/reg_tions.json
	fi
	
	if [ ! -f $btwaf_path/rule/url_request_mode.json ];then
		\cp -a -r $pluginPath/btwaf_lua/rule/url_request_mode.json $btwaf_path/rule/url_request_mode.json
	fi
	
	
	
	if [ ! -f /dev/shm/stop_ip.json ];then
		\cp -a -r $pluginPath/btwaf_lua/stop_ip.json /dev/shm/stop_ip.json
	fi
	chmod 777 /dev/shm/stop_ip.json
	chown www:www /dev/shm/stop_ip.json
	
	if [ ! -f $btwaf_path/site.json ];then
		\cp -a -r $pluginPath/btwaf_lua/site.json $btwaf_path/site.json
	fi
	
	if [ ! -f $btwaf_path/zhizhu1.json ];then
		\cp -a -r $pluginPath/btwaf_lua/zhizhu1.json $btwaf_path/zhizhu1.json
	fi
	if [ ! -f $btwaf_path/zhizhu2.json ];then
		\cp -a -r $pluginPath/btwaf_lua/zhizhu2.json $btwaf_path/zhizhu2.json
	fi
	if [ ! -f $btwaf_path/zhizhu4.json ];then
		\cp -a -r $pluginPath/btwaf_lua/zhizhu4.json $btwaf_path/zhizhu4.json
	fi
	if [ ! -f $btwaf_path/zhizhu5.json ];then
		\cp -a -r $pluginPath/btwaf_lua/zhizhu5.json $btwaf_path/zhizhu5.json
	fi
	if [ ! -f $btwaf_path/zhizhu6.json ];then
		\cp -a -r $pluginPath/btwaf_lua/zhizhu6.json $btwaf_path/zhizhu6.json
	fi
	if [ ! -f $btwaf_path/config.json ];then
		\cp -a -r $pluginPath/btwaf_lua/config.json $btwaf_path/config.json
	fi
	
	if [ ! -f $btwaf_path/domains.json ];then
		\cp -a -r $pluginPath/btwaf_lua/domains.json $btwaf_path/domains.json
	fi
	
	if [ ! -f $btwaf_path/total.json ];then
		\cp -a -r $pluginPath/btwaf_lua/total.json $btwaf_path/total.json
	fi
	
	if [ ! -f $btwaf_path/drop_ip.log ];then
		
		\cp -a -r $pluginPath/btwaf_lua/drop_ip.log $btwaf_path/drop_ip.log
	fi
	\cp -a -r $pluginPath/btwaf_lua/zhi.lua $btwaf_path/zhi.lua
	\cp -a -r $pluginPath/btwaf_lua/10.69.lua $btwaf_path/init.lua
	\cp -a -r $pluginPath/btwaf_lua/libinjection.lua $btwaf_path/libinjection.lua
	\cp -a -r $pluginPath/btwaf_lua/xss_engine.lua $btwaf_path/xss_engine.lua
	\cp -a -r $pluginPath/btwaf_lua/ElementNode.lua $btwaf_path/ElementNode.lua
	\cp -a -r $pluginPath/btwaf_lua/multipart.lua $btwaf_path/multipart.lua
	\cp -a -r $pluginPath/btwaf_lua/libbtengine.lua $btwaf_path/libbtengine.lua
	\cp -a -r $pluginPath/btwaf_lua/libphp.so $btwaf_path/libphp.so
	if [ ! -n "$Centos6Check" ]; then
		\cp -a -r $pluginPath/btwaf_lua/libinjection_23_05_06.so $btwaf_path/libinjection.so
	else
		\cp -a -r $pluginPath/btwaf_lua/centos6_libinjection.so $btwaf_path/libinjection.so
	fi
	\cp -a -r $pluginPath/btwaf_lua/header.lua $btwaf_path/header.lua
	\cp -a -r $pluginPath/btwaf_lua/uuid.lua $btwaf_path/uuid.lua
	\cp -a -r $pluginPath/btwaf_lua/dns.lua $btwaf_path/dns.lua
	\cp -a -r $pluginPath/btwaf_lua/body3.lua $btwaf_path/body.lua
	\cp -a -r $pluginPath/btwaf_lua/waf.lua $btwaf_path/waf.lua
	\cp -a -r $pluginPath/btwaf_lua/maxminddb.lua $btwaf_path/maxminddb.lua
	\cp -a -r $pluginPath/btwaf_lua/libmaxminddb.so $btwaf_path/libmaxminddb.so
	\cp -a -r $pluginPath/btwaf_lua/LICENSE $btwaf_path/LICENSE
	chmod +x $btwaf_path/waf.lua
	chmod +x $btwaf_path/init.lua
	mkdir -p /www/wwwlogs/btwaf
	mkdir -p /www/server/btwaf/webshell_total
	rm -rf  $btwaf_path/nday
	mv $pluginPath/btwaf_lua/nday $btwaf_path/nday
	chmod 777 /www/wwwlogs/btwaf
	chmod -R 755 /www/server/btwaf
	chmod -R 644 /www/server/btwaf/rule
	chmod -R 666 /www/server/btwaf/total.json
	chmod -R 666 /www/server/btwaf/drop_ip.log
	echo '' > /www/server/nginx/conf/luawaf.conf
	chown -R root:root /www/server/btwaf/
	chown www:www /www/server/btwaf/*.json
	chown www:www /www/server/btwaf/drop_ip.log
	install_mbd
	#Install_sqlite3_for_nginx
	mkdir /www/server/btwaf/total
	chown www:www /www/server/btwaf/total
	mkdir -p /www/server/btwaf/totla_db/http_log
	if [ ! -f /www/server/btwaf/totla_db/totla_db.db ];then
		\cp -a -r $pluginPath/btwaf_lua/totla_db/totla_db.db $btwaf_path/totla_db/totla_db.db
		chown www:www /www/server/btwaf/totla_db/totla_db.db
		chmod 755 $btwaf_path/totla_db/totla_db.db
	fi
	chown www:www /www/server/btwaf/totla_db/totla_db.db
	/usr/bin/python $pluginPath/white.py
	/www/server/panel/pyenv/bin/python $pluginPath/white.py
	/www/server/panel/pyenv/bin/python $pluginPath/black.py
	python $pluginPath/black.py
	
	if [ ! -f $btwaf_path/resty/memcached.lua ];then
		#做软连
		
		if [ -f /www/server/nginx/lualib/resty/memcached.lua ];then
			#openrestry 兼容
			echo "openresty兼容"
			ln -s /www/server/nginx/lualib/resty  /www/server/btwaf
		fi 
	fi 
	
	if [ "$aacher" == "aarch64" ];then
		rm -rf /www/server/btwaf/libinjection.so
		\cp -a -r $pluginPath/btwaf_lua/libinjection_arm.so /www/server/btwaf/libinjection.so
		#如果是openresty 做一个软连接

		#rm -rf cp  $btwaf_path/init.lua
		#cp -a -r /tmp/btwaf/xiu34.lua $btwaf_path/init.lua
	fi
	#Install_sqlite3_for_nginx
	chown www:www /www/server/btwaf/totla_db/totla_db.db
	
	rm -rf /www/server/btwaf/ngx
	rm -rf /www/server/btwaf/resty
	NGINX_VER=$(/www/server/nginx/sbin/nginx -v 2>&1|grep -oE 1.2[34])
	if [ "${NGINX_VER}" ];then
		sed -i "/lua_package_path/d" /www/server/nginx/conf/nginx.conf
		\cp -rpa /www/server/nginx/lib/lua/* /www/server/btwaf
	fi
	
	
	/etc/init.d/nginx restart
	sleep 2
	para5=$(ps -aux |grep nginx |grep  /www/server/nginx/conf/nginx.conf | awk 'NR==2')
	if [ ! -n "$para5" ]; then 
		/etc/init.d/nginx restart
	fi
	sleep 2
	para1=$(ps -aux |grep nginx |grep  /www/server/nginx/conf/nginx.conf | awk 'NR==2')
	parc2=$(netstat -nltp|grep nginx| grep 80|wc -l)
	if [ ! -n "$para1" ]; then 
		if [ $parc2 -eq 0 ]; then 
			Cjson2
			rm -rf /www/server/btwaf/init.lua
			echo '正在修复中'
			Install_LuaJIT
			Install_sqlite3_for_nginx
			luarocks install lua-cjson
			\cp -a -r $pluginPath/btwaf_lua/10.69.lua $btwaf_path/init.lua
			/etc/init.d/nginx restart
			para1=$(ps -aux |grep nginx |grep  /www/server/nginx/conf/nginx.conf | awk 'NR==2')
			parc2=$(netstat -nltp|grep nginx| grep 80|wc -l)
			if [ ! -n "$para1" ]; then 
				\cp -a -r $pluginPath/btwaf_lua/10.69.lua $btwaf_path/init.lua
				/etc/init.d/nginx restart
				#para1=$(ps -aux |grep nginx |grep  /www/server/nginx/conf/nginx.conf | awk 'NR==2')
				parc2=$(netstat -nltp|grep nginx| grep 80|wc -l)
				if [ $parc2 -eq 0 ]; then 
					cp -a -r $pluginPath/btwaf_lua/10.69.lua $btwaf_path/init.lua
					/etc/init.d/nginx restart
				fi
			fi
		fi
	fi
	
	rm -rf $pluginPath/btwaf_lua
	rm -rf $pluginPath/LuaJIT-2.1.0-beta*
	rm -rf $pluginPath/lua-5.1.5*
	rm -rf $pluginPath/captcha.zip
	rm -rf $pluginPath/luarocks-3.5.0*
	rm -rf $pluginPath/GeoLite2-City.mmdb
	rm -rf $pluginPath/lsqlite3_fsl09y*
	rm -rf $pluginPath/lua-cjson-2.1.0*
	
	#安装bt_ipfter
	#关闭
	/etc/init.d/bt_ipfilter stop
	cd $pluginPath/bt_ipfilter
	bash bt_ipfilter_install.sh
	isStart=$(ps aux |grep -E "(bt-ipfilter)"|grep -v grep|grep -v "/etc/init.d/bt_ipfilter"|awk '{print $2}'|xargs)
	if [ "$isStart" == '' ];then
		bash bt_ipfilter_install.sh
	fi
	/etc/init.d/bt_ipfilter restart
	chmod 755 /www/server/btwaf/rule
	chmod 755 /www/server/btwaf/
	rm -rf /www/server/btwaf/ffijson.lua
	chown www:www -R /www/server/btwaf/totla_db/
	chown www:www -R /www/server/btwaf/total/
	rm -rf /www/server/panel/plugin/btwaf/*.so
	
	chown www:www -R /www/server/btwaf/totla_db/http_log
	chown www:www -R /www/server/btwaf/totla_db/
	chown www:www -R  /www/server/btwaf/webshell_total
	
	chown www:www /www/server/btwaf/totla_db
	chown www:www /www/server/btwaf/http_log
	chmod 755 /www/server/btwaf/totla_db
	chown root:root /www/server/btwaf/config.json
	chown root:root /www/server/btwaf/domains.json
	chown root:root /www/server/btwaf/site.json
	chown root:root /www/server/btwaf/zhi.json
	chown root:root /www/server/btwaf/1.json
	chown root:root /www/server/btwaf/2.json
	chown root:root /www/server/btwaf/3.json
	chown root:root /www/server/btwaf/4.json
	chown root:root /www/server/btwaf/5.json
	chown root:root /www/server/btwaf/6.json
	chown root:root /www/server/btwaf/7.json
	rm -rf $pluginPath/bt_ipfilter
	echo '安装完成' > $install_tmp
}


Cjson2()
{
	cd $pluginPath
	tar xvf $pluginPath/lua-cjson-2.1.0.tar.gz
	cd $pluginPath/lua-cjson-2.1.0
	make clean
	make 
	make install
	cd ..
	#rm -rf lua-cjson-2.1.0
	cp -a -r /usr/local/lib/lua/5.1/cjson.so /www/server/btwaf/cjson.so
}

Install_cjson()
{
	Install_LuaJIT
	if [ -f /usr/bin/yum ];then
		isInstall=`rpm -qa |grep lua-devel`
		if [ "$isInstall" == "" ];then
			yum install lua lua-devel -y
			yum install lua-socket -y
		fi
	else
		isInstall=`dpkg -l|grep liblua5.1-0-dev`
		if [ "$isInstall" == "" ];then
			apt-get install lua5.1 lua5.1-dev -y
		fi
	fi
	
	if [ -f /usr/local/lib/lua/5.1/cjson.so ];then
			is_jit_cjson=$(luajit -e "require 'cjson'" 2>&1|grep 'undefined symbol: luaL_setfuncs')
			if [ "$is_jit_cjson" != "" ];then
				rm -f /usr/local/lib/lua/5.1/cjson.so
			fi
	fi
	
	
	if [ ! -f /www/server/btwaf/cjson.so ];then
		cd $pluginPath
		tar $pluginPath/xvf lua-cjson-2.1.0.tar.gz
		#rm -f lua-cjson-2.1.0.tar.gz
		cd $pluginPath/lua-cjson-2.1.0
		make clean
		make 
		make install
		cd ..
		#rm -rf lua-cjson-2.1.0
		cp -a -r /usr/local/lib/lua/5.1/cjson.so /www/server/btwaf/cjson.so
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
		wget -O luasocket-master.zip $download_Url/install/src/luasocket-master.zip -T 20
		unzip luasocket-master.zip
		rm -f luasocket-master.zip
		cd luasocket-master
		export C_INCLUDE_PATH=/usr/local/include/luajit-2.0:$C_INCLUDE_PATH
		make
		make install
		cd ..
		rm -rf luasocket-master
	fi
	rm -rf /usr/share/lua/5.1/socket

	if [ ! -d /usr/share/lua/5.1/socket ]; then
		if [ -d /usr/lib64/lua/5.1 ];then
			mkdir /usr/lib64/lua/5.1/
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
		mkdir -p /usr/share/lua/5.1/ 
		mkdir -p /www/server/btwaf/
		ln -sf /usr/local/share/lua/5.1/mime.lua /usr/share/lua/5.1/mime.lua
		ln -sf /usr/local/share/lua/5.1/socket.lua /usr/share/lua/5.1/socket.lua
		ln -sf /usr/local/share/lua/5.1/socket /usr/share/lua/5.1/socket
		
		ln -sf /usr/local/share/lua/5.1/mime.lua /www/server/btwaf/mime.lua
		ln -sf /usr/local/share/lua/5.1/socket.lua /www/server/btwaf/socket.lua
		ln -sf /usr/local/share/lua/5.1/socket /www/server/btwaf/socket	
	fi
}

Uninstall_btwaf()
{
	rm -rf /www/server/panel/static/btwaf
	rm -f /www/server/panel/vhost/nginx/btwaf.conf
	rm -rf /www/server/panel/plugin/btwaf/
	#rm -rf /usr/local/lib/lua/5.1/cjson.so
	#rm -rf /www/server/btwaf/lsqlite3.so
	NGINX_VER=$(/www/server/nginx/sbin/nginx -v 2>&1|grep -oE 1.2[34])
	if [ "${NGINX_VER}" ];then
		sed -i '/include proxy\.conf;/a \        lua_package_path "/www/server/nginx/lib/lua/?.lua;;";' /www/server/nginx/conf/nginx.conf
	fi
	/etc/init.d/nginx reload
	echo '-,0.0.0.0' >/dev/shm/.bt_ip_filter
}

Check_install(){
if [ ! -d /www/server/btwaf/socket ]; then
	Install_btwaf
fi

}


if [ "${1}" == 'install' ];then
	Install_btwaf
elif  [ "${1}" == 'update' ];then
	Install_btwaf
elif [ "${1}" == 'uninstall' ];then
	Uninstall_btwaf
fi