#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

public_file=/www/server/panel/install/public.sh
publicFileMd5=$(md5sum ${public_file} 2>/dev/null | awk '{print $1}')
md5check="8e49712d1fd332801443f8b6fd7f9208"
if [ "${publicFileMd5}" != "${md5check}" ]; then
    wget -O Tpublic.sh http://download.bt.cn/install/public.sh -T 20
    publicFileMd5=$(md5sum Tpublic.sh 2>/dev/null | awk '{print $1}')
    if [ "${publicFileMd5}" == "${md5check}" ]; then
        \cp -rpa Tpublic.sh $public_file
    fi
    rm -f Tpublic.sh
fi
. $public_file
download_Url=$NODE_URL
pluginPath=/www/server/panel/plugin/rsync
centos=1
if [ ! -f /usr/bin/yum ]; then
    centos=0
fi

install_main() {
    check_fs
    get_lsyncd_version
    get_rsync_version
    if [[ "${1}" == "install" ]]; then
        if [ -f "${pluginPath}/repair.pl" ] || [ -f "${pluginPath}/upgrade.pl" ]; then
            check_package "reinstall"
        else
            if [[ -z "$lsyncd_version" ]] || [ "$lsyncd_version" != "2.3.1" ] ||
                [[ -z "$rsync_version" ]] || [[ "$rsync_version" != "3.2.6" ]]; then
                check_package
            fi
        fi
    else
        check_package "$@"
    fi
    \cp -f $pluginPath/rsynd.init /etc/init.d/rsynd
    chmod +x /etc/init.d/rsynd
    if [ $centos == 1 ]; then
        chkconfig --add rsynd
        chkconfig --level 2345 rsynd on
    else
        update-rc.d rsynd defaults
    fi

    \cp -f $pluginPath/lsyncd.init /etc/init.d/lsyncd
    chmod +x /etc/init.d/lsyncd
    if [ $centos == 1 ]; then
        chkconfig --add lsyncd
        chkconfig --level 2345 lsyncd on
    else
        update-rc.d lsyncd defaults
    fi

    mkdir -p $pluginPath
    cd $pluginPath && rm -f rsync_*.so
    rm -rf "${pluginPath}/repair.pl"
    rm -rf "${pluginPath}/upgrade.pl"
    echo >/www/server/panel/data/reload.pl
    echo 'Successify'
}

rsync_install() {
    if [[ "$rsync_version" != "3.2.6" ]]; then
        wget -O rsync-3.2.6.tar.gz $download_Url/install/src/rsync-3.2.6.tar.gz -T 20
        tar xvf rsync-3.2.6.tar.gz
        cd rsync-3.2.6
        ./configure --prefix=/usr $parm
        make -j $cpuCore
        make install
        cd ..
        rm -rf rsync-3.2.6*
        rsync_version=$(/usr/bin/rsync --version | grep version | awk '{print $3}')
        if [ "$rsync_version" != "3.2.6" ]; then
            rm -f /usr/bin/rsync
            ln -sf /usr/local/bin/rsync /usr/bin/rsync
        fi
    fi
}

get_rsync_version() {
    rsync_version=$(/usr/bin/rsync --version | grep version | awk '{print $3}')
}

get_lsyncd_version() {
    lsyncd_version=$(lsyncd --version | grep Version | awk '{print $2}')
}

check_package() {
    if [ $centos == 1 ]; then
        install_packages="cmake3 expect lsyncd tcl gcc g++ gawk autoconf automake python3-pip acl libacl-devel attr libattr-devel xxhash-devel libzstd-devel lz4-devel openssl-devel"
        for i_name in $install_packages; do
            yum -y install $i_name
        done
        isInstall=$(rpm -qa | grep lua-devel)
        if [ "$isInstall" == "" ]; then
            yum install lua5.3 lua-devel asciidoc cmake -y
        fi
    else
        install_packages="expect tcl gcc g++ gawk autoconf automake python3-cmarkgfm acl libacl1-dev attr libattr1-dev libxxhash-dev libzstd-dev liblz4-dev libssl-dev"
        for i_name in $install_packages; do
            apt-get install $i_name -y
        done

        isInstall=$(dpkg -l | grep liblua5.3-dev)
        if [ "$isInstall" == "" ]; then
            rm -rf /usr/lib/x86_64-linux-gnu/liblua*
            apt-get install lua5.3 liblua5.3 liblua5.3-dev cmake -y
        fi
    fi

    if [ -f /usr/local/lib/lua/5.1/cjson.so ]; then
        if [ ! -d "/usr/lib64/lua/5.1" ]; then
            mkdir -p /usr/lib64/lua/5.1
        fi
        rm -rf /usr/lib64/lua/5.1/cjson.so
        ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so

        if [ ! -d "/usr/lib/lua/5.1" ]; then
            mkdir -p /usr/lib/lua/5.1
        fi
        rm -rf /usr/lib/lua/5.1/cjson.so
        ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
    fi
    rconf=$(cat /etc/rsyncd.conf | grep 'rsyncd.pid')
    if [ "$rconf" == "" ]; then
        cat >/etc/rsyncd.conf <<EOF
uid = root
use chroot = no
dont compress = *.gz *.tgz *.zip *.z *.Z *.rpm *.deb *.bz2 *.mp4 *.avi *.swf *.rar
hosts allow =
max connections = 200
gid = root
timeout = 600
lock file = /var/run/rsync.lock
pid file = /var/run/rsyncd.pid
log file = /var/log/rsyncd.log
port = 873
EOF
    fi

    if [[ "${1}" = "reinstall" ]] || [[ -z "$rsync_version" ]] || [[ "$rsync_version" != "3.2.6" ]]; then
        if [ $centos == 1 ]; then
            xxhash_result=$(rpm -qa | grep xxHash-devel)
            zstd_result=$(rpm -qa | grep libzstd-devel)
            lz4_result=$(rpm -qa | grep liblz4-devel)
        else
            xxhash_result=$(dpkg -l | grep libxxhash-dev)
            zstd_result=$(dpkg -l | grep libzstd-dev)
            lz4_result=$(dpkg -l | grep liblz4-dev)
        fi

        if [[ -z $xxhash_result ]]; then
            wget -O xxHash-0.8.0.tar.gz $download_Url/install/src/xxHash-0.8.0.tar.gz
            tar xvf xxHash-0.8.0.tar.gz
            cd xxHash-0.8.0
            make -j $cpuCore
            make install
        fi

        if [[ -z $zstd_result ]]; then
            wget -O zstd-1.5.0.tar.gz $download_Url/install/src/zstd-1.5.0.tar.gz
            tar xvf zstd-1.5.0.tar.gz
            cd zstd-1.5.0
            make -j $cpuCore
            make install
        fi

        if [[ -z $lz4_result ]]; then
            wget -O lz4-v1.9.3.tar.gz $download_Url/install/src/lz4-v1.9.3.tar.gz
            tar xvf lz4-v1.9.3.tar.gz
            cd lz4-v1.9.3
            make -j $cpuCore
            make install
        fi
    fi
    rsync_install
    get_rsync_version
    parm="--disable-xxhash --disable-zstd --disable-lz4"
    rsync_install

    # if [ ! -f /usr/bin/rsync ];then
    # 	yum install rsync -y
    # fi

    if [[ "${1}" = "reinstall" ]] || [[ -z "$lsyncd_version" ]] || [ "$lsyncd_version" != "2.3.1" ]; then
        wget -O lsyncd-v2.3.1.tar.gz $download_Url/install/src/lsyncd-v2.3.1.tar.gz -T 20
        tar xvf lsyncd-v2.3.1.tar.gz
        cd lsyncd-2.3.1
        if [ $centos == 1 ]; then
            cmake3 -DCMAKE_INSTALL_PREFIX=/usr
        else
            cmake -DCMAKE_INSTALL_PREFIX=/usr
        fi
        check_lua_path
        make
        make install
        cd ..
        rm -rf lsyncd-2.3.1
        if [ ! -f /etc/lsyncd.conf ]; then
            echo >/etc/lsyncd.conf
        fi
        systemctl daemon-reload
        systemctl enable lsyncd
    fi

    if [ ! -f /usr/bin/lsyncd ]; then
        yum install lua5.1 -y
        yum install lua5.1-devel -y
        wget -O lsyncd-2.2.2-1.el7.x86_64.rpm $download_Url/rpm/centos7/64/lsyncd-2.2.2-1.el7.x86_64.rpm -T 20
        rpm -ivh lsyncd-2.2.2-1.el7.x86_64.rpm --nodeps --force
        systemctl enable lsyncd
        systemctl start lsyncd
    fi
}

check_lua_path(){
    if [ ! -f /usr/bin/lua ]; then
      ln -sf /usr/bin/lua5.3 /usr/local/lua5.3
    fi
    if [ ! -f /usr/bin/luac ]; then
      ln -sf /usr/bin/luac5.3 /usr/local/luac5.3
    fi
}

check_fs() {
    is_max_user_instances=$(cat /etc/sysctl.conf | grep max_user_instances)
    if [ "$is_max_user_instances" == "" ]; then
        echo "fs.inotify.max_user_instances = 1024" >>/etc/sysctl.conf
        echo "1024" >/proc/sys/fs/inotify/max_user_instances
    fi

    is_max_user_watches=$(cat /etc/sysctl.conf | grep max_user_watches)
    if [ "$is_max_user_watches" == "" ]; then
        echo "fs.inotify.max_user_watches = 819200" >>/etc/sysctl.conf
        echo "819200" >/proc/sys/fs/inotify/max_user_watches
    fi
}

uninstall_main() {
    /etc/init.d/rsynd stop
    if [ $centos == 1 ]; then
        chkconfig --del rsynd
    else
        update-rc.d -f rsynd remove
    fi
    rm -f /etc/init.d/rsynd

    if [ -f /etc/init.d/rsync_inotify ]; then
        /etc/init.d/rsync_inotify stopall
        chkconfig --del rsync_inotify
        rm -f /etc/init.d/rsync_inotify
    fi

    if [ -f /etc/init.d/lsyncd ]; then
        /etc/init.d/lsyncd stop
        if [ $centos == 1 ]; then
            chkconfig --level 2345 lsyncd off
            chkconfig --del rsynd
        else
            update-rc.d -f rsynd remove
        fi
    else
        systemctl disable lsyncd
        systemctl stop lsyncd
    fi

    rm -f /etc/lsyncd.conf
    rm -f /etc/rsyncd.conf
    rm -rf $pluginPath
}

if [ "${1}" == 'install' ] || [ "${1}" == "repair" ] || [ "${1}" == "upgrade" ]; then
    install_main "$@"
elif [ "${1}" == 'uninstall' ]; then
    uninstall_main
fi
