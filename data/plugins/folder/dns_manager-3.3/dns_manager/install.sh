#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

pluginPath=/www/server/panel/plugin/dns_manager

Install_Bind9()
{
    yum install bind bind-chroot bind-devel* -y
    if [ ! -f /var/named/chroot/etc/named.rfc1912.zones ];then
        if [ -d '/usr/share/doc/bind/' ];then
          cp -R /usr/share/doc/bind/sample/var/named/* /var/named/chroot/var/named/
        else
          cp -R /usr/share/doc/bind-*/sample/var/named/* /var/named/chroot/var/named/
        fi
        touch /var/named/chroot/var/named/data/cache_dump.db
        touch /var/named/chroot/var/named/data/named_stats.txt
        touch /var/named/chroot/var/named/data/named_mem_stats.txt
        touch /var/named/chroot/var/named/data/named.run
        mkdir /var/named/chroot/var/named/dynamic
        touch /var/named/chroot/var/named/dynamic/managed-keys.bind
        chown -R named.named /var/named/chroot/var/named/data/*
        chmod 744 /var/named/chroot/var/named/data/named.run
        chown -R named.named /var/named/chroot/var/named/dynamic/*
        cp -p /etc/named.* /var/named/chroot/etc/
        sed -i 's/127.0.0.1;/any;/g' /var/named/chroot/etc/named.conf
        sed -i 's/localhost;/any;/g' /var/named/chroot/etc/named.conf
        sed -i 's/recursion yes;/recursion no;/g' /var/named/chroot/etc/named.conf
    fi
  systemctl start named-chroot
	systemctl enable named-chroot
}

Install_Powerdns_Redhat()
{
  yum install pdns -y
  groupadd named
  useradd -g named -s /sbin/nologin named
  mv /etc/pdns/pdns.conf /etc/pdns/pdns.conf_bt
  cp $pluginPath/pdns.conf /etc/pdns/pdns.conf
  chmod 644 /etc/pdns/pdns.conf
  mkdir -p /var/named/chroot/etc
  mkdir -p /var/named/chroot/var/named
  chmod  755 /var/named
  chmod  755 /var/named/chroot
  chmod  755 /var/named/chroot/etc
  chmod  755 /var/named/chroot/var
  chmod  755 /var/named/chroot/var/named
  chmod -R 644 /var/named/chroot/etc/*
  chmod -R 644 /var/named/chroot/var/named/*
  if [ ! -f "/var/named/chroot/etc/named.rfc1912.zones" ];then
    touch /var/named/chroot/etc/named.rfc1912.zones
  fi
  bind_conf=$(grep 'file "/var/' /var/named/chroot/etc/named.rfc1912.zones)
  if [ "$bind_conf" == "" ];then
    sed -i 's/file\s*\"/file \"\/var\/named\/chroot\/var\/named\//g' /var/named/chroot/etc/named.rfc1912.zones
  fi
  systemctl stop systemd-resolved
  systemctl disable systemd-resolved
	systemctl stop named-chroot
	systemctl disable named-chroot
  systemctl enable pdns
  systemctl restart pdns
}

Install_Powerdns_Ubuntu()
{
  ubuntu=$(cat /etc/issue)
  if [[ "$ubuntu" =~ "Ubuntu" ]];then
    systemctl disable systemd-resolved
    systemctl stop systemd-resolved
    rm /etc/resolv.conf
    echo "nameserver 8.8.8.8" > /etc/resolv.conf
  fi
  curl https://repo.powerdns.com/FD380FBB-pub.asc | sudo apt-key add -
  apt-get update
  apt-get install pdns-server -y
  groupadd named
  useradd -g named -s /sbin/nologin named
  mv /etc/powerdns/pdns.conf /etc/powerdns/pdns.conf_bt
  cp $pluginPath/pdns.conf /etc/powerdns/pdns.conf
  chmod 600 /etc/powerdns/pdns.conf
  mkdir -p /var/named/chroot/etc
  mkdir -p /var/named/chroot/var/named
  if [ ! -f "/var/named/chroot/etc/named.rfc1912.zones" ];then
    touch /var/named/chroot/etc/named.rfc1912.zones
  fi
  systemctl enable pdns
  systemctl restart pdns
}

Install_Powerdns()
{
  if [ -f '/etc/redhat-release' ];then
    Install_Powerdns_Redhat
  else
    Install_Powerdns_Ubuntu
  fi
}

Install_DnsManager()
{
	mkdir -p $pluginPath
	Install_Powerdns
	if [ -f "/www/server/panel/pyenv/bin/pip" ];then
	/www/server/panel/pyenv/bin/pip install dnspython
	else
	/usr/bin/pip install dnspython
	fi
    \cp -a -r /www/server/panel/plugin/dns_manager/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-dns_manager.png
	echo 'Successify'
}


Uninstall_DnsManager()
{
	rm -rf $pluginPath
	rm -f /var/named/chroot/etc/named.rfc1912.zones_bak
	mv /var/named/chroot/etc/named.rfc1912.zones /var/named/chroot/etc/named.rfc1912.zones_bak
  mv /var/named/chroot/var/named /var/named/chroot/var/named_bak
  rm -rf /var/named/chroot/var/named
	/usr/bin/systemctl stop named-chroot
	systemctl disable named-chroot
	systemctl stop pdns
	systemctl disable pdns
	echo 'Successify'
}

if [ "${1}" == 'install' ];then
	Install_DnsManager
elif  [ "${1}" == 'update' ];then
	update_DnsManager
elif [ "${1}" == 'uninstall' ];then
	Uninstall_DnsManager
fi
