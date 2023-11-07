#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Install() {
  if [ ! -d /www/server/panel/plugin/bt_bbr ]; then
    mkdir -p /www/server/panel/plugin/bt_bbr
  fi
  kernel_version=$(uname -r | cut -d '.' -f 1,2)
  if [ $(echo "$kernel_version < 4.9" | bc) -ne 0 ]; then
    echo '内核版本小于4.9，安装失败！'
    rm -rf /www/server/panel/plugin/bt_bbr
    exit 1
  fi
  # 检查curl是否已安装
  if ! command -v curl &>/dev/null; then
    # 根据操作系统类型执行不同的安装命令
    if [[ -f /etc/debian_version ]]; then
      sudo apt-get update
      sudo apt-get install -y curl
    elif [[ -f /etc/redhat-release ]]; then
      sudo yum update
      sudo yum install -y curl
    fi
  fi

  ln -s /usr/lib64/tc /usr/lib/tc
  dd if=/dev/zero of=/www/server/panel/plugin/bt_bbr/40M bs=1 count=0 seek=40M
  dd if=/dev/zero of=/www/server/panel/plugin/bt_bbr/1G bs=1 count=0 seek=1G
  cd /www/server/panel/plugin/bt_bbr
  echo 'Successify'
}
Uninstall() {
  rm -rf /www/server/panel/plugin/bt_bbr
  echo 'Successify'
}

action=$1
if [ "${1}" == 'install' ]; then
  Install
else
  Uninstall
fi
