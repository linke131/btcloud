#!/usr/bin/python
# coding: utf-8
"""

author: linxiao
date: 2020/9/14 16:32
"""
import json

# ip_entry = "192.169.42.0/15"
import IPy
import socket


def get_host_ip():
    """
    查询本机ip地址
    :return:
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


ip_file = "ips.txt"
ip_list = []
country = "US"
with open(ip_file, "r") as fp:
    content = json.load(fp)
    for obj in content:
        if obj["brief"] == country:
            ip_list = obj["ips"]
# print("Local host IP: {}".format(get_host_ip()))

# ip_list = [ip_entry]
for ip_entry in ip_list:
    release_ips = ["127.0.0.1", "172.16.1.1", "10.0.0.1", "192.168.0.0",
                   get_host_ip()]
    ip = IPy.IP(ip_entry, make_net=True)
    for rip in release_ips:
        rip_obj = IPy.IP(rip)
        overlap = ip.overlaps(rip_obj)
        if overlap != 0:
            print("Overlop: {}".format(ip_entry))
        # overlap = ip.overlaps(rip_obj.broadcast())
        # if overlap > 0:
        #     print("Overlop2: {}".format(ip_entry))


# print(IPy.IP('192.168.1.0/24').overlaps('192.168.0.0/23'))

