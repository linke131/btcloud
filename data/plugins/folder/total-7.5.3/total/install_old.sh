#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
public_file=/www/server/panel/install/public.sh
#安装脚本概述
#经过不同的用户安装环境测试，整理安装脚本安装逻辑如下：
#Web Server: nginx, apache
#lua版本: 5.1.4 5.1.5 5.3.1
#OS: CentOS7 CentOS8
#
#nginx和apache单独分开安装逻辑:
#
#因为面板的nginx是固定编译了lua5.1.5，所以nginx的安装统一会安装一个独立的lua5.1.5版本到/www/server/total/lu515,
#用来编译安装luarocks和lsqlite3。
#
#apache的编译跟随OS自带的Lua版本，所以apache默认不安装lua515环境。
#
#所有版本共用一个的lua脚本，已经从lua代码层面解决5.1~5.3的语法不同之处。

# if [ ! -f $public_file ];then
wget -O $public_file http://download.bt.cn/install/public.sh -T 5
# fi

download_Url=""
if [ ! "${1}" == 'uninstall' ]; then
    . $public_file
    download_Url=$NODE_URL
fi
pluginPath=/www/server/panel/plugin/total
libraryPath=/www/server/panel/plugin/total/library
total_path=/www/server/total
remote_dir="total2"

wrong_actions=()
# Retry Download file
download_file() {
    local_file=$1
    source=$2
    timeout=$3
    retry=$4
    if [ -n "$5" ]; then
        ori_retry=$5
    else
        ori_retry=$retry
    fi
    #echo "source:$source/local:$local_file/retry:$retry/ori_retry:$ori_retry"
    wget --no-check-certificate -O $local_file $source -T $timeout -t $ori_retry
    if [ -s $local_file ]; then
        echo $local_file" download successful."
    else
        if [ $retry -gt 1 ]; then
            let retry=retry-1
            download_file $local_file $source $timeout $retry $ori_retry
        else
            echo "* "$local_file" download failed!"
            wrong_actions[${#wrong_actions[*]}]=$local_file
        fi
    fi
}

# Returns the platform
Get_platform() {
    case $(uname -s 2>/dev/null) in
    Linux) echo "linux" ;;
    FreeBSD) echo "freebsd" ;;
    *BSD*) echo "bsd" ;;
    Darwin) echo "macosx" ;;
    CYGWIN* | MINGW* | MSYS*) echo "mingw" ;;
    AIX) echo "aix" ;;
    SunOS) echo "solaris" ;;
    *) echo "unknown" ;;
    esac
}
Remove_path() {
    local prefix=$1
    local new_path
    new_path=$(
        echo "${PATH}" | sed \
            -e "s#${prefix}/[^/]*/bin[^:]*:##g" \
            -e "s#:${prefix}/[^/]*/bin[^:]*##g" \
            -e "s#${prefix}/[^/]*/bin[^:]*##g"
    )
    export PATH="${new_path}"
}
Add_path() {
    local prefix=$1
    local new_path
    new_path=$(
        echo "${PATH}" | sed \
            -e "s#${prefix}/[^/]*/bin[^:]*:##g" \
            -e "s#:${prefix}/[^/]*/bin[^:]*##g" \
            -e "s#${prefix}/[^/]*/bin[^:]*##g"
    )
    export PATH="${prefix}:${new_path}"
}

Get_lua_version() {
    echo $(lua -e 'print(_VERSION:sub(5))')
}

Install_lua515() {
    local install_path="/www/server/total/lua515"

    local version
    version=$(Get_lua_version)

    echo "Current lua version: "$version
    if [ -d "${install_path}/bin" ]; then
        Add_path "${install_path}/bin"
        echo "Lua 5.1.5 has installed."
        return 1
    fi

    local lua_version="lua-5.1.5"
    local package_name="${lua_version}.tar.gz"
    local url=http://download.bt.cn/install/plugin/${remote_dir}/library/$package_name
    echo "lua515下载链接:"$url
    mkdir -p $install_path
    local tmp_dir=/tmp/$lua_version
    mkdir -p $tmp_dir && cd $tmp_dir

    if [ ! -f $libraryPath/$package_name ]; then
        download_file $libraryPath/$package_name $url 10 3
    fi
    tar xvzf $libraryPath/$package_name
    cd $lua_version
    platform=$(Get_platform)
    if [ "${platform}" = "unknown" ]; then
        platform="linux"
    fi
    make "${platform}" install INSTALL_TOP=$install_path
    Add_path "${install_path}/bin"
    rm -rf "${lua_version}*"

    version=$(Get_lua_version)
    if [ ${version} == "5.1" ]; then
        echo "Lua 5.1.5 has installed."
        return 1
    fi
    return 0
}
Install_sqlite3_for_nginx() {

    if ! hash luarocks 2>/dev/null; then
        # if [ true ];then
        rm -rf /tmp/luarocks-3.5.0
        # wget -c -O /tmp/luarocks-3.5.0.tar.gz http://download.bt.cn/btwaf_rule/test/btwaf/luarocks-3.5.0.tar.gz  -T 10
        if [ ! -f $libraryPath/luarocks-3.5.0.tar.gz ]; then
            download_file $libraryPath/luarocks-3.5.0.tar.gz http://download.bt.cn/install/plugin/$remote_dir/library/luarocks-3.5.0.tar.gz 10 3
        fi

        cd /tmp && tar xf $libraryPath/luarocks-3.5.0.tar.gz
        cd /tmp/luarocks-3.5.0
        ./configure --with-lua-include=/www/server/total/lua515/include --with-lua-bin=/www/server/total/lua515/bin
        make -I/www/server/total/lua515/bin
        make install
        cd /tmp && rm -rf /tmp/luarocks-3.5.0
    fi
    # find_lsqlite=$(luarocks list | grep lsqlite3)
    # if [ "$find_lsqlite" != "lsqlite3" ]; then
    if [ true ]; then
        yum install -y sqlite-devel
        apt install -y libsqlite3-dev
        rm -rf /tmp/lsqlite3_fsl09y
        if [ ! -f $libraryPath/lsqlite3_fsl09y.zip ]; then
            download_file $libraryPath/lsqlite3_fsl09y.zip http://download.bt.cn/install/plugin/$remote_dir/library/lsqlite3_fsl09y.zip 10 3
        fi
        cd /tmp && unzip $libraryPath/lsqlite3_fsl09y.zip && cd lsqlite3_fsl09y && make
        if [ ! -f '/tmp/lsqlite3_fsl09y/lsqlite3.so' ]; then
            echo $tip9
            wrong_actions[${#wrong_actions[*]}]="lsqlite3 install failed."
            # wget -c -o /www/server/total/lsqlite3.so http://download.bt.cn/btwaf_rule/test/btwaf/lsqlite3.so -T 10
            if [ ! -f $libraryPath/lsqlite3.so ]; then
                download_file $libraryPath/lsqlite3.so http://download.bt.cn/install/plugin/$remote_dir/library/lsqlite3.so 10 3
            fi
            \cp -a -r $libraryPath/lsqlite3.so $total_path/lsqlite3.so
        else
            echo $tip10
            \cp -a -r /tmp/lsqlite3_fsl09y/lsqlite3.so $total_path/lsqlite3.so
        fi
        rm -rf /tmp/lsqlite3_fsl09y/*
        rm -rf /tmp/lsqlite3_fsl09y.zip
    fi
    if [ -f /usr/local/lib/lua/5.1/cjson.so ]; then
        is_jit_cjson=$(luajit -e "require 'cjson'" 2>&1 | grep 'undefined symbol: luaL_setfuncs')
        if [ "$is_jit_cjson" != "" ]; then
            cd /tmp
            luarocks install lua-cjson
        fi
    fi
}

Install_sqlite3_for_apache() {
    if [ -f '/usr/include/lua.h' ]; then
        include_path='/usr/include/'
    elif [ -f '/usr/include/lua5.1/lua.h' ]; then
        include_path='/usr/include/lua5.1'
    elif [ -f '/usr/include/lua5.3/lua.h' ]; then
        include_path='/usr/include/lua5.3'
    elif [ -f '/usr/local/include/luajit-2.0/lua.h' ]; then
        include_path='/usr/local/include/luajit-2.0/'
    elif [ -f '/usr/include/lua5.1/' ]; then
        include_path='/usr/include/lua5.1/'
    elif [ -f '/usr/local/include/luajit-2.1/' ]; then
        include_path='/usr/local/include/luajit-2.1/'
    else
        include_path=''
    fi

    is_lua53=""
    if [ $(Get_lua_version) == "5.3" ] && [ -d '/usr/lib64/lua' ]; then
        lua_bin='/usr/bin/'
        is_lua53="yes"
    elif [ $(Get_lua_version) == "5.3" ] && [ -f '/usr/lib64/lua' ]; then
        lua_bin='/usr/lib64'
        is_lua53="yes"
    elif [ -f '/usr/bin/lua' ]; then
        lua_bin='/usr/bin/'
    elif [ -f '/usr/lib/lua' ]; then
        lua_bin='/usr/lib/'
    else
        lua_bin=$(which lua | xargs dirname)
    fi
    # if ! hash luarocks 2>/dev/null; then
    if [ true ]; then
        rm -rf /tmp/luarocks-3.5.0
        # wget -c -O /tmp/luarocks-3.5.0.tar.gz http://download.bt.cn/btwaf_rule/test/btwaf/luarocks-3.5.0.tar.gz  -T 10
        if [ ! -f $libraryPath/luarocks-3.5.0.tar.gz ]; then
            download_file $libraryPath/luarocks-3.5.0.tar.gz http://download.bt.cn/install/plugin/$remote_dir/library/luarocks-3.5.0.tar.gz 10 3
        fi

        cd /tmp && tar xvf $libraryPath/luarocks-3.5.0.tar.gz >/dev/null
        cd /tmp/luarocks-3.5.0
        if [ $is_lua53 == "yes" ]; then
            # echo "---------------is lua 5.3"
            ./configure --with-lua-include=$include_path --with-lua-bin=$lua_bin
            make
        else
            ./configure --with-lua-include=$include_path --with-lua-bin=$lua_bin
            make -I$include_path
        fi
        make install
        cd /tmp && rm -rf /tmp/luarocks-3.5.0
    fi
    # find_lsqlite=$(luarocks list | grep lsqlite3)
    # if [ "$find_lsqlite" != "lsqlite3" ]; then
    if [ true ]; then
        if hash yum 2>/dev/null; then
            yum install -y sqlite-devel
        fi
        if hash apt 2>/dev/null; then
            apt install -y libsqlite3-dev
        fi
        rm -rf /tmp/lsqlite3_fsl09y
        if [ ! -f $libraryPath/lsqlite3_fsl09y.zip ]; then
            download_file $libraryPath/lsqlite3_fsl09y.zip http://download.bt.cn/install/plugin/$remote_dir/library/lsqlite3_fsl09y.zip 10 3
        fi
        cd /tmp && unzip $libraryPath/lsqlite3_fsl09y.zip && cd lsqlite3_fsl09y && make
        if [ ! -f /tmp/lsqlite3_fsl09y/lsqlite3.so ]; then
            echo $tip9
            wrong_actions[${#wrong_actions[*]}]="lsqlite3 install failed."
            # wget -c -o /www/server/total/lsqlite3.so http://download.bt.cn/btwaf_rule/test/btwaf/lsqlite3.so -T 10
            if [ ! -f $libraryPath/lsqlite3.so ]; then
                download_file $libraryPath/lsqlite3.so http://download.bt.cn/install/plugin/$remote_dir/library/lsqlite3.so 10 3
            fi
            \cp -a -r $libraryPath/lsqlite3.so $total_path/lsqlite3.so
        else
            echo $tip10
            \cp -a -r /tmp/lsqlite3_fsl09y/lsqlite3.so $total_path/lsqlite3.so
        fi
        rm -rf /tmp/lsqlite3_fsl09y
    fi

    if [ -f /usr/local/lib/lua/5.1/cjson.so ]; then
        is_jit_cjson=$(luajit -e "require 'cjson'" 2>&1 | grep 'undefined symbol: luaL_setfuncs')
        if [ "$is_jit_cjson" != "" ]; then
            cd /tmp
            luarocks install lua-cjson
        fi
    fi
}

Install_cjson() {
    if [ -f /usr/local/lib/lua/5.1/cjson.so ]; then
        is_jit_cjson=$(luajit -e "require 'cjson'" 2>&1 | grep 'undefined symbol:luaL_setfuncs')
        if [ "$is_jit_cjson" != "" ]; then
            rm -f /usr/local/lib/lua/5.1/cjson.so
        fi
    fi
    if [ -f /usr/bin/yum ]; then
        isInstall=$(rpm -qa | grep lua-devel)
        if [ "$isInstall" == "" ]; then
            yum install lua lua-devel -y
        fi
    else
        isInstall=$(dpkg -l | grep liblua5.1-0-dev)
        if [ "$isInstall" == "" ]; then
            apt-get install lua5.1 lua5.1-dev lua5.1-cjson lua5.1-socket -y
        fi
    fi
    Centos8Check=$(cat /etc/redhat-release | grep -iE ' 8(\.\d)*' | grep -iE 'centos|Red Hat|Alibaba|Anolis')
    AlibabaCheck=$(cat /etc/redhat-release | grep 'Alibaba')
    Install_lua53=""
    if [ "${AlibabaCheck}" ]; then
        version=$(Get_lua_version)
        if [ $version == "5.3" ]; then
            Install_lua53="true"
        fi
    fi
    if [ "${Centos8Check}" ] || [ "${Install_lua53}" ]; then
        yum install lua-socket -y
        if [ ! -f /usr/lib/lua/5.3/cjson.so ]; then
            # wget -O lua-5.3-cjson.tar.gz $download_Url/src/lua-5.3-cjson.tar.gz -T 20
            cd /tmp
            if [ ! -f $libraryPath/lua-5.3-cjson.tar.gz ]; then
                download_file $libraryPath/lua-5.3-cjson.tar.gz $download_Url/src/lua-5.3-cjson.tar.gz 20 3
            fi
            tar -xvf $libraryPath/lua-5.3-cjson.tar.gz
            cd lua-5.3-cjson
            make
            make install
            ln -sf /usr/lib/lua/5.3/cjson.so /usr/lib64/lua/5.3/cjson.so
            cd /tmp
            rm -rf lua-5.3-cjson
        fi
        return
    fi

    if [ ! -f /usr/local/lib/lua/5.1/cjson.so ]; then
        # wget -O lua-cjson-2.1.0.tar.gz $download_Url/install/src/lua-cjson-2.1.0.tar.gz -T 20
        cd /tmp
        if [ ! -f $libraryPath/lua-cjson-2.1.0.tar.gz ]; then
            download_file $libraryPath/lua-cjson-2.1.0.tar.gz $download_Url/install/src/lua-cjson-2.1.0.tar.gz 20 3
        fi
        tar xvf $libraryPath/lua-cjson-2.1.0.tar.gz
        cd lua-cjson-2.1.0
        make clean
        make
        make install
        cd /tmp
        rm -rf lua-cjson-2.1.0
        ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so
        ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
    else
        if [ -d "/usr/lib64/lua/5.1" ]; then
            ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so
        fi

        if [ -d "/usr/lib/lua/5.1" ]; then
            ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
        fi
    fi
    cd /tmp
    luarocks install lua-cjson
}

Install_socket() {
    if [ ! -f /usr/local/lib/lua/5.1/socket/core.so ]; then
        # wget -O luasocket-master.zip $download_Url/install/src/luasocket-master.zip -T 20
        cd /tmp
        if [ ! -f $libraryPath/luasocket-master.zip ]; then
            download_file $libraryPath/luasocket-master.zip $download_Url/install/src/luasocket-master.zip 20 3
        fi
        unzip $libraryPath/luasocket-master.zip
        cd luasocket-master
        make
        make install
        cd /tmp
        rm -rf luasocket-master
    fi

    if [ ! -d /usr/share/lua/5.1/socket ]; then
        if [ -d /usr/lib64/lua/5.1 ]; then
            rm -rf /usr/lib64/lua/5.1/socket /usr/lib64/lua/5.1/mime
            ln -sf /usr/local/lib/lua/5.1/socket /usr/lib64/lua/5.1/socket
            ln -sf /usr/local/lib/lua/5.1/mime /usr/lib64/lua/5.1/mime
        else
            rm -rf /usr/lib/lua/5.1/socket /usr/lib/lua/5.1/mime
            ln -sf /usr/local/lib/lua/5.1/socket /usr/lib/lua/5.1/socket
            ln -sf /usr/local/lib/lua/5.1/mime /usr/lib/lua/5.1/mime
        fi
        rm -rf /usr/share/lua/5.1/mime.lua /usr/share/lua/5.1/socket.lua /usr/share/lua/5.1/socket
        ln -sf /usr/local/share/lua/5.1/mime.lua /usr/share/lua/5.1/mime.lua
        ln -sf /usr/local/share/lua/5.1/socket.lua /usr/share/lua/5.1/socket.lua
        ln -sf /usr/local/share/lua/5.1/socket /usr/share/lua/5.1/socket
    fi
    cd /tmp
    luarocks install luasocket
}

Install_mod_lua_for_apache() {
    if [ ! -f /www/server/apache/bin/httpd ]; then
        return 0
    fi

    if [ -f /www/server/apache/modules/mod_lua.so ]; then
        return 0
    fi
    cd /www/server/apache
    if [ ! -d /www/server/apache/src ]; then
        # wget -O httpd-2.4.33.tar.gz $download_Url/src/httpd-2.4.33.tar.gz -T 20
        if [ ! -f $libraryPath/httpd-2.4.33.tar.gz ]; then
            download_file $libraryPath/httpd-2.4.33.tar.gz $download_Url/src/httpd-2.4.33.tar.gz 20 3
        fi
        tar xvf $libraryPath/httpd-2.4.33.tar.gz
        mv httpd-2.4.33 src
        cd /www/server/apache/src/srclib
        if [ ! -f $libraryPath/apr-1.6.3.tar.gz ]; then
            download_file $libraryPath/apr-1.6.3.tar.gz $download_Url/src/apr-1.6.3.tar.gz 10 3
        fi
        if [ ! -f $libraryPath/apr-util-1.6.1.tar.gz ]; then
            download_file $libraryPath/apr-util-1.6.1.tar.gz $download_Url/src/apr-util-1.6.1.tar.gz 10 3
        fi
        tar zxf $libraryPath/apr-1.6.3.tar.gz
        tar zxf $libraryPath/apr-util-1.6.1.tar.gz
        mv apr-1.6.3 apr
        mv apr-util-1.6.1 apr-util
    fi
    cd /www/server/apache/src
    ./configure --prefix=/www/server/apache --enable-lua
    cd modules/lua
    make
    make install

    if [ ! -f /www/server/apache/modules/mod_lua.so ]; then
        echo $tip8
        exit 0
    fi
}

Install_pdf_library() {

    if [ ! -f /usr/share/fonts/msyh.ttf ]; then
        download_file $libraryPath/msyh.ttf $download_Url/install/plugin/${remote_dir}/library/msyh.ttf 10 3
        \cp $libraryPath/msyh.ttf /usr/share/fonts/msyh.ttf
        rm -f $libraryPath/msyh.ttf
    fi
    rm -f $libraryPath/msyh.ttf

    if hash btpip 2>/dev/null; then
        btpip install pdfkit
    else
        pip install pdfkit
    fi

    if hash wkhtmltopdf 2>/dev/null; then
        echo "PDF module is installed."
        return 0
    fi

    v=$(cat /etc/redhat-release | sed -r 's/.* ([0-9]+)\..*/\1/')
    if [ $v -eq 6 ]; then
        # wget -O $pluginPath/library/wkhtmltox-0.12.6-1.centos6.x86_64.rpm  $download_Url/install/plugin/$remote_dir/wkhtmltox-0.12.6-1.centos6.x86_64.rpm -T 10
        if [ ! -f $libraryPath/wkhtmltox-0.12.6-1.centos6.x86_64.rpm ]; then
            download_file $libraryPath/wkhtmltox-0.12.6-1.centos6.x86_64.rpm $download_Url/install/plugin/$remote_dir/library/wkhtmltox-0.12.6-1.centos6.x86_64.rpm 10 3
        fi
        yum install -y $libraryPath/wkhtmltox-0.12.6-1.centos6.x86_64.rpm
    fi
    if [ $v -eq 7 ]; then
        # wget -O $pluginPath/library/wkhtmltox-0.12.6-1.centos7.x86_64.rpm $download_Url/install/plugin/$remote_dir/wkhtmltox-0.12.6-1.centos7.x86_64.rpm -T 10
        if [ ! -f $libraryPath/wkhtmltox-0.12.6-1.centos7.x86_64.rpm ]; then
            download_file $libraryPath/wkhtmltox-0.12.6-1.centos7.x86_64.rpm $download_Url/install/plugin/$remote_dir/library/wkhtmltox-0.12.6-1.centos7.x86_64.rpm 10 3
        fi
        yum install -y $libraryPath/wkhtmltox-0.12.6-1.centos7.x86_64.rpm
    fi
    Centos8Check=$(cat /etc/redhat-release | grep ' 8.' | grep -iE 'centos|Red Hat')
    if [ "${Centos8Check}" ]; then
        # wget -O $pluginPath/library/wkhtmltox-0.12.6-1.centos8.x86_64.rpm $download_Url/install/plugin/$remote_dir/wkhtmltox-0.12.6-1.centos8.x86_64.rpm -T 10
        if [ ! -f $libraryPath/wkhtmltox-0.12.6-1.centos8.x86_64.rpm ]; then
            download_file $libraryPath/wkhtmltox-0.12.6-1.centos8.x86_64.rpm $download_Url/install/plugin/$remote_dir/library/wkhtmltox-0.12.6-1.centos8.x86_64.rpm 10 3
        fi
        yum install -y $libraryPath/wkhtmltox-0.12.6-1.centos8.x86_64.rpm
    fi

    os_release=$(. /etc/os-release && echo $ID_LIKE)
    sys_version=$(. /etc/os-release && echo $VERSION)
    if [[ $os_release =~ "centos" ]] && [[ $sys_version =~ "8." ]]; then
        yum install -y xorg-x11-fonts-75dpi xorg-x11-fonts-Type1 libXext openssl-devel
        if [ ! -f $libraryPath/wkhtmltox-0.12.6.1-2.almalinux8.x86_64.rpm ]; then
            download_file $libraryPath/wkhtmltox-0.12.6.1-2.almalinux8.x86_64.rpm $download_Url/install/plugin/$remote_dir/library/wkhtmltox-0.12.6.1-2.almalinux8.x86_64.rpm 10 3
        fi
        yum install -y $libraryPath/wkhtmltox-0.12.6.1-2.almalinux8.x86_64.rpm
    fi

    deb_version_file="/etc/issue"
    os_type='ubuntu'
    os_version=$(cat $deb_version_file | grep Ubuntu | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]+')
    if [ -z "${os_version}" ]; then
        os_type='debian'
        os_version=$(cat $deb_version_file | grep Debian | awk '{print $3}')
        deb_install_file=''
        if [ "${os_version}" -eq 9 ]; then
            deb_install_file='wkhtmltox_0.12.6-1.stretch_amd64.deb'
        elif [ "${os_version}" -eq 10 ]; then
            deb_install_file='wkhtmltox_0.12.6-1.buster_amd64.deb'
        elif [ "${os_version}" -eq 11 ]; then
            deb_install_file='wkhtmltox_0.12.6.1-2.bullseye_amd64.deb'
        fi
        download_file $libraryPath/$deb_install_file $download_Url/install/plugin/$remote_dir/library/$deb_install_file 10 3
        apt install -y $libraryPath/$deb_install_file
    else
        if [ "${os_version}" -eq 20 ]; then
            if [ ! -f $libraryPath/wkhtmltox_0.12.6-1.focal_amd64.deb ]; then
                download_file $libraryPath/wkhtmltox_0.12.6-1.focal_amd64.deb $download_Url/install/plugin/$remote_dir/library/wkhtmltox_0.12.6-1.focal_amd64.deb 10 3
            fi
            apt install -y $libraryPath/wkhtmltox_0.12.6-1.focal_amd64.deb
        elif [ "${os_version}" -eq 18 ]; then
            if [ ! -f $libraryPath/wkhtmltox_0.12.6-1.bionic_amd64.deb ]; then
                download_file $libraryPath/wkhtmltox_0.12.6-1.bionic_amd64.deb $download_Url/install/plugin/$remote_dir/library/wkhtmltox_0.12.6-1.bionic_amd64.deb 10 3
            fi
            apt install -y $libraryPath/wkhtmltox_0.12.6-1.bionic_amd64.deb
        elif [ "${os_version}" -eq 16 ]; then
            if [ ! -f $libraryPath/wkhtmltox_0.12.6-1.xenial_amd64.deb ]; then
                download_file $libraryPath/wkhtmltox_0.12.6-1.xenial_amd64.deb $download_Url/install/plugin/$remote_dir/library/wkhtmltox_0.12.6-1.xenial_amd64.deb 10 3
            fi
            apt install -y $libraryPath/wkhtmltox_0.12.6-1.xenial_amd64.deb
        fi
    fi
}

Install_ip_library() {
    if [ ! -f $libraryPath/ip.db ]; then
        download_file $libraryPath/ip.db $download_Url/install/plugin/$remote_dir/library/ip.db 10 3
    fi
}

Install_nginx_environment() {
    echo "Installing nginx environment..."
    Install_lua515
    Install_sqlite3_for_nginx
    Install_cjson
    Install_pdf_library
    Install_ip_library
}

Install_apache_environment() {
    echo "Installing apache environment..."
    Install_mod_lua_for_apache
    Install_sqlite3_for_apache
    Install_cjson
    Install_socket
    Install_pdf_library
    Install_ip_library
}

Install_environment() {
    if [ ! -f /usr/include/linux/limits.h ]; then
        yum install kernel-headers -y
    fi
    if [ -f /www/server/apache/bin/httpd ]; then
        Install_apache_environment
    elif [ -f /www/server/nginx/sbin/nginx ]; then
        Install_nginx_environment
    else
        echo "Please install nginx or apache first."
    fi
}

tip1="检测到当前面板安装了云控，请暂时使用旧版本监控报表。"
tip2="开始安装旧版本监控报表v3.7..."
tip3="正在安装插件脚本文件..."
tip4="正在初始化数据..."
tip5="开始执行插件补丁..."
tip6="数据初始化完成。"
tip7="安装完成。"
tip8='mod_lua安装失败!'
tip9='解压不成功'
tip10='解压成功'
tip11="安装失败！"

Install_total() {
    mkdir -p $total_path
    mkdir -p $libraryPath
    if ! hash gcc 2>/dev/null; then
        yum install -y gcc
    fi

    if ! hash g++ 2>/dev/null; then
        yum install -y gcc+ gcc-c++
    fi

    Install_environment

    btpip install user-agents==2.2.0

    cd /tmp
    echo $tip3 >$install_tmp

    mv -f $pluginPath/panelMonitor.py /www/server/panel/class/monitor.py

    if [ ! -f $total_path/debug.log ]; then
        touch $total_path/debug.log
        chown www:www $total_path/debug.log
    fi

    if [ -f $pluginPath/total_main.cpython-37m-x86_64-linux-gnu.so ]; then
        rm -f $pluginPath/total_main.cpython-37m-x86_64-linux-gnu.so
    fi

    # js fix
    if [ ! -f /www/server/panel/BTPanel/static/js/tools.min.js ]; then
        \cp $pluginPath/tools.min.js /www/server/panel/BTPanel/static/js/tools.min.js
    fi
    rm -f $pluginPath/tools.min.js

    if [ ! -f /www/server/panel/BTPanel/static/js/china.js ]; then
        \cp $pluginPath/china.js /www/server/panel/BTPanel/static/js/china.js
    fi
    rm -f $pluginPath/china.js

    # total path install
    if [ ! -f $total_path/config.json ]; then
        \cp $pluginPath/total_config.json $total_path/config.json
    fi
    rm -f $pluginPath/total_config.json

    if [ -f /www/server/apache/bin/httpd ]; then
        if [ ! -f $total_path/closing ]; then
            if [ ! -f /www/server/panel/vhost/apache/total.conf ]; then
                \cp $pluginPath/total_httpd.conf /www/server/panel/vhost/apache/total.conf
            fi
        fi
    elif [ -f /www/server/nginx/sbin/nginx ]; then
        if [ ! -f $total_path/closing ]; then
            if [ ! -f /www/server/panel/vhost/nginx/total.conf ]; then
                \cp $pluginPath/total_nginx.conf /www/server/panel/vhost/nginx/total.conf
            fi
        fi
    fi

    /bin/cp -rf $pluginPath/total2/* $total_path
    rm -rf $pluginPath/total2

    if [ ! -f $pluginPath/server_port.pl ]; then
        echo 9876 >$pluginPath/server_port.pl
    fi

    if [ ! -f $pluginPath/server.log ]; then
        touch $pluginPath/server.log
    fi

    # execute patch
    echo $tip4
    if hash btpip 2>/dev/null; then
        btpython $pluginPath/total_migrate.py
        echo $tip5
        btpython $pluginPath/total_patch.py
    else
        python $pluginPath/total_migrate.py
        echo $tip5
        python $pluginPath/total_patch.py
    fi
    echo $tip6

    # authority
    chown -R www:www $total_path
    chmod -R 755 $total_path

    chmod +x $total_path/httpd_log.lua && chown -R root:root $total_path/httpd_log.lua
    chmod +x $total_path/nginx_log.lua && chown -R root:root $total_path/nginx_log.lua
    chmod +x $total_path/memcached.lua && chown -R root:root $total_path/memcached.lua
    if [ -f $total_path/lsqlite3.so ]; then
        chmod +x $total_path/lsqlite3.so && chown -R root:root $total_path/lsqlite3.so
    fi
    chmod +x $total_path/CRC32.lua && chown -R root:root $total_path/CRC32.lua

    # load module
    waf=/www/server/panel/vhost/apache/btwaf.conf
    if [ ! -f $waf ]; then
        echo "LoadModule lua_module modules/mod_lua.so" >$waf
    fi

    # del .so
    if [ -f $pluginPath/total_main.so ]; then
        rm -rf $pluginPath/total_main.so
    fi

    # 兼容负载均衡插件，lua引用路劲
    chmod +x $total_path/load_total.lua && chown -R root:root $total_path/load_total.lua
    dir_list=$(ls -d /www/server/panel/vhost/nginx/proxy/*/)
    for dir in $dir_list; do
        conf_file=${dir}load_balance.conf
        if [ -f "$conf_file" ]; then
            if [ -d /www/server/panel/plugin/load_balance ]; then
                \cp -r /www/server/total/load_total.lua /www/server/panel/plugin/load_balance/load_total.lua
                \cp -r /www/server/total/load_total.lua /www/server/panel/vhost/nginx/load_total.lua
            fi
        fi
    done

    # reload
    if [ -f /etc/init.d/httpd ]; then
        /etc/init.d/httpd reload
    else
        /etc/init.d/nginx reload
        cat /www/server/nginx/logs/nginx.pid | xargs kill -HUP
    fi

    # echo errors
    if [ ${#wrong_actions[*]} -gt 0 ]; then
        echo $tip11
        for ((i = 0; i < ${#wrong_actions[@]}; i++)); do
            echo ${wrong_actions[i]}
        done
        echo Error:安装失败
    else
        # success
        if [ ! -f $pluginPath/info.json ]; then
            download_file $pluginPath/info.json $download_Url/install/plugin/$remote_dir/info.json 5 3
        fi
        echo $tip7
        echo $tip7 >$install_tmp
        echo >/www/server/panel/data/reload.pl
        echo "Successify"
    fi
}

Uninstall_total() {
    if [ -f /etc/init.d/httpd ]; then
        if [ -f $total_path/uninstall.lua ]; then
            lua $total_path/uninstall.lua
        fi
    fi

    if hash btpython 2>/dev/null; then
        btpython $pluginPath/total_task.py remove
    else
        python $pluginPath/total_task.py remove
    fi

    chkconfig --level 2345 bt_total_init off

    cd /tmp
    rm -rf $total_path
    rm -f /www/server/panel/vhost/apache/total.conf
    rm -f /www/server/panel/vhost/nginx/total.conf
    rm -rf $pluginPath

    rm -f /etc/init.d/bt_total_init
    rm -f /usr/bin/bt_total_init

    if [ -f /etc/init.d/httpd ]; then
        if [ ! -d /www/server/panel/plugin/btwaf_httpd ]; then
            rm -f /www/server/panel/vhost/apache/btwaf.conf
        fi
        /etc/init.d/httpd reload
    else
        /etc/init.d/nginx reload
    fi
}

if [ "${1}" == 'install' ]; then
    Install_total
elif [ "${1}" == 'update' ]; then
    Install_total
elif [ "${1}" == 'uninstall' ]; then
    Uninstall_total
fi
