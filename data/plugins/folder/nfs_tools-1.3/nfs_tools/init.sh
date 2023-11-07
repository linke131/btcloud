#!/bin/bash
# chkconfig: 2345 55 25
# description: bt.cn BT-NFS-MOUNT

### BEGIN INIT INFO
# Provides:          BT-NFS-MOUNT
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts BT-NFS-MOUNT
# Description:       starts the BT-NFS-MOUNT
### END INIT INFO

panel_path=/www/server/panel

bin_file=$panel_path/plugin/nfs_tools/BT-NFS-MOUNT
cd $panel_path

env_path=$panel_path/pyenv/bin/activate
if [ -f $env_path ];then
        source $env_path
        pythonV=$panel_path/pyenv/bin/python
        chmod -R 700 $panel_path/pyenv/bin
else
        pythonV=/usr/bin/python
fi

panel_start()
{       
    echo -e "Starting BT-NFS-MOUNT service.... \c"
    nohup $pythonV $bin_file &> /dev/null
    echo -e "\033[32mdone\033[0m"
}



case "$1" in
        'start')
                panel_start
                ;;
        'stop')
                echo 'error'
                ;;
        'restart')
                panel_start
                ;;
        'reload')
                panel_start
                ;;
        'status')
                echo 'error'
                ;;
        *)
                echo "Usage: /etc/init.d/bt-nfs-mount {start|restart|reload}"
        ;;
esac