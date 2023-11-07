#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'


pluginPath=/www/server/panel/plugin/bt_ssh_auth
pamPath=/usr/pam_python_so
check_md5="adece195456b8765477e18b685b71268"
so_file="/usr/pam_python_so/pam_btssh_authentication.so"
restart_ssh()
{
    # 删除指定字段
        sed -i '/auth  requisite  \/usr\/pam_python_so\/pam_btssh_authentication.so/d' /etc/pam.d/sshd    
    # 判断Linux发行版并执行相应的命令
        if command -v systemctl >/dev/null 2>&1; then
            systemctl restart sshd
        elif command -v service >/dev/null 2>&1; then
            service sshd restart
        fi
}

Install_clear()
{
    mkdir -p $pamPath
    chmod 600 $pamPath
    if [ -e $so_file ]; then
        actual_md5sum=$(md5sum "$so_file" | awk '{print $1}')
            if [ "$actual_md5sum" != "check_md5" ]; then
                \cp -a -r pam_btssh_authentication.so $pamPath
            fi
    else
        \cp -a -r pam_btssh_authentication.so $pamPath
    fi
    if command -v setenforce >/dev/null 2>&1; then
    setenforce 0
    fi
    echo '安装完成' > $install_tmp
}


Uninstall_clear()
{
    restart_ssh
    rm -rf $pluginPath
    rm -rf $pamPath
}

action=$1
if [ "${1}" == 'install' ];then
    Install_clear
else
    Uninstall_clear
fi
