#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

SPIDER_MEM="10m"
BTWAF_MEM="30m"
DROP_IP_MEM="30m"
DROP_SUM_MEM="30m"
BTWAF_DATA_MEM="100m"

MEM_TOTAL=$(free -m | grep Mem | awk '{print  $2}')
if [[ "${MEM_TOTAL}" -gt 4096 && "${MEM_TOTAL}" -le 8192 ]];then
	SPIDER_MEM="10m"
	BTWAF_MEM="60m"
	DROP_IP_MEM="60m"
	DROP_SUM_MEM="60m"
	BTWAF_DATA_MEM="150m"
elif [[ "${MEM_TOTAL}" -gt 8192 && "${MEM_TOTAL}" -le 16384 ]]; then
	SPIDER_MEM="15m"
	BTWAF_MEM="100m"
	DROP_IP_MEM="100m"
	DROP_SUM_MEM="100m"
	BTWAF_DATA_MEM="200m"
elif [[ "${MEM_TOTAL}" -gt 16384 && "${MEM_TOTAL}" -le 32768 ]]; then
	SPIDER_MEM="20m"
	BTWAF_MEM="200m"
	DROP_IP_MEM="200m"
	DROP_SUM_MEM="200m"
	BTWAF_DATA_MEM="280m"
elif [[ "${MEM_TOTAL}" -gt 32768 && "${MEM_TOTAL}" -le 65536 ]]; then
	SPIDER_MEM="25m"
	BTWAF_MEM="300m"
	DROP_IP_MEM="300m"
	DROP_SUM_MEM="300m"
	BTWAF_DATA_MEM="350m"
elif [[ "${MEM_TOTAL}" -gt 65536 && "${MEM_TOTAL}" -le 131072 ]]; then
	SPIDER_MEM="30m"
	BTWAF_MEM="400m"
	DROP_IP_MEM="400m"
	DROP_SUM_MEM="400m"
	BTWAF_DATA_MEM="500m"
elif [ "${MEM_TOTAL}" -gt 131072 ]; then
	SPIDER_MEM="30m"
	BTWAF_MEM="500m"
	DROP_IP_MEM="500m"
	DROP_SUM_MEM="500m"
	BTWAF_DATA_MEM="600m"
fi

sed -i "s/spider 10m/spider ${SPIDER_MEM}/g" /www/server/panel/vhost/nginx/btwaf.conf
sed -i "s/btwaf 30m/btwaf ${BTWAF_MEM}/g" /www/server/panel/vhost/nginx/btwaf.conf
sed -i "s/drop_ip 30m/drop_ip ${DROP_IP_MEM}/g" /www/server/panel/vhost/nginx/btwaf.conf
sed -i "s/drop_sum 30m/drop_sum ${DROP_SUM_MEM}/g" /www/server/panel/vhost/nginx/btwaf.conf
sed -i "s/btwaf_data 100m/btwaf_data ${BTWAF_DATA_MEM}/g" /www/server/panel/vhost/nginx/btwaf.conf