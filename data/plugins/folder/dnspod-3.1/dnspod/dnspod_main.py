import sys,os,time,json
panelPath = os.getenv('BT_PANEL')
if not panelPath: panelPath = '/www/server/panel'

os.chdir(panelPath)
sys.path.append("class/")
import public,random
try:
    from BTPanel import session,cache
except:pass

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dnspod.v20210323 import dnspod_client, models
import ssl
ssl._create_default_https_context=ssl._create_unverified_context

class dnspod_main:


    appid = None
    secretId = None
    secretKey = None
    aes_key = None
    endpoint = "dnspod.tencentcloudapi.com"
    conf_path = 'plugin/cosfs/mount.conf'
    tx_path = '{}/data/tencent.conf'.format(panelPath)


    def __init__(self):
        self.aes_key = public.readFile('{}/data/a_pass.pl'.format(panelPath))
        if not self.aes_key:
            self.aes_key = public.GetRandomString(16)
            public.writeFile('{}/data/a_pass.pl'.format(panelPath),self.aes_key)

        if os.path.exists(self.tx_path):
            conf = public.readFile(self.tx_path)
            if conf:
                data = json.loads(public.aes_decrypt(conf,self.aes_key))
                self.appid = data['appid']
                self.secretId = data['secretId']
                self.secretKey = data['secretKey']

    """
    @设置密钥
    @secretId 必填
    @secretKey 必填
    @appid 非必填 cos需要使用
    """
    def set_config(self,get):
        try:
            data = {}
            data['appid'] = ''
            data['secretId'] = get.secretId
            data['secretKey'] = get.secretKey
            if 'appid' in get: data['appid'] = get.appid

            self.appid = data['appid']
            self.secretId = data['secretId']
            self.secretKey = data['secretKey']

            client = self.__client()
            req = models.DescribeDomainListRequest()
            resp = client.DescribeDomainList(req)

            sdata = public.aes_encrypt(json.dumps(data),self.aes_key)
            public.writeFile(self.tx_path,sdata)
            return public.returnMsg(True,"设置成功!")
        except TencentCloudSDKException as err:
            return public.returnMsg(False,self.__get_error(err))


    def unbind_config(self,get):
        """
        @name 解绑密钥
        """
        if os.path.exists(self.tx_path):
            os.remove(self.tx_path)
        return public.returnMsg(True,'解绑成功')

    """
    @获取密钥
    """
    def get_config(self,get):
        conf = public.readFile(self.tx_path)
        if conf:
            try:
                data = json.loads(public.aes_decrypt(conf,self.aes_key))
                return data
            except:pass
        return False

    """
    @获取dnspod客户端对象
    """
    def __client(self):

        cred = credential.Credential(self.secretId,self.secretKey)
        httpProfile = HttpProfile()
        httpProfile.endpoint = self.endpoint
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = dnspod_client.DnspodClient(cred, "", clientProfile)

        return client

    """
    @获取DNS_NS记录
    """
    def get_dnspod_ns(self,get):

        try:
            key = '{}_dns_ns'.format(get['domain'])

            if not 'force' in get:
                ret = cache.get(key)
                if ret: return ret

            client = self.__client()
            req = models.DescribeRecordListRequest()
            params = {
                "Domain": get['domain'],
                "Limit": 3000,
                "RecordType": "NS"
            }
            req.from_json_string(json.dumps(params))
            resp = client.DescribeRecordList(req)
            resp = self.__get_json(resp)

            cache.set(key,resp,3600)
            return resp
        except TencentCloudSDKException as err:
            return public.returnMsg(False,self.__get_error(err))

    def query_dns(self,get):
        """
        @name 查询dns记录名称
        @type 查询dns记录类型
        @domain 查询dns记录域名(根域名，如bt.cn)
        """
        domain = get.domain
        dns_type = get.dns_type

        res = public.query_dns(domain,dns_type)
        if not res:


            return public.returnMsg(False,'查询失败')

        return res


    """
    @获取解析记录列表
    @domain String	要操作的域名（主域名，不包括 www，例如：qcloud.com）
    @subDomain	String	（过滤条件）根据子域名进行过滤
    @recordType	String	（过滤条件）根据记录类型进行过滤
    """
    def get_record_list(self,get):

        search = ''
        if 'search' in get:
            search =  get['search'].lower()

        try:
            client = self.__client()
            req = models.DescribeRecordListRequest()
            params = {
                "Domain": get['domain'],
                # "Limit": 3000
            }
            req.from_json_string(json.dumps(params))
            resp = client.DescribeRecordList(req)
            resp = self.__get_json(resp)
            del resp["RecordCountInfo"]

            ips = []
            n_list = []
            for val in resp['RecordList']:
                if public.check_ip(val['Value']) and not val['Value'] in ips: ips.append(val['Value'])

                if search:
                    for key in ['TTL','Value','Name','Type']:
                        if str(val[key]).lower().find(search) >= 0:
                            n_list.append(val)
                            break
                else:
                    n_list.append(val)
            import page
            page, data_list = page.page_data(get, n_list)
            resp['page'] = page
            resp['RecordList'] = data_list

            local_ip = public.GetLocalIp()
            if public.check_ip(local_ip) and not local_ip in ips:
                ips.append(local_ip)
            resp['ips'] = ips

            return resp
        except TencentCloudSDKException as err:
            return public.returnMsg(False,self.__get_error(err))



    """
    网站创建解析
    """
    def create_record_bysite(self,get):

        domains = json.loads(get['domains'])
        if len(domains) <= 0:
            return public.returnMsg(False,'域名列表不能为空!');

        result = {
            "status":True,
            "success":[],
            "error":{}
        }
        client = self.__client()
        local_ip = public.GetLocalIp()
        for domain in domains:
            if not domain: continue
            if public.check_ip(domain): continue

            root,sub_domain = public.get_root_domain(domain)
            if not sub_domain: sub_domain = '@'

            try:
                req = models.CreateRecordRequest()
                params = {
                    "Domain": root,
                    "SubDomain": sub_domain,
                    "RecordType": 'A',
                    "RecordLine": '默认',
                    "Value": local_ip
                }
                req.from_json_string(json.dumps(params))
                resp = client.CreateRecord(req)
                resp = self.__get_json(resp)
                if 'RequestId' in resp:
                    result['success'].append(sub_domain)
            except TencentCloudSDKException as err:
                result['error'][sub_domain] = err.message

        return result


    def create_record(self,get):
        """
        @创建解析记录
        @domain String 要添加解析记录的域名（主域名，不包括 www，例如：qcloud.com）
        @subDomain	String	子域名，例如：www
        @recordType	String	记录类型，可选的记录类型为："A", "CNAME", "MX", "TXT", "NS", "AAAA", "SRV"
        @recordLine	String	记录的线路名称，例如："默认"
        @value	String	记录值，例如 IP：192.168.10.2，CNAME：cname.dnspod.com.，MX：mail.dnspod.com.
        @ttl Int	TTL 值，范围1 - 604800，不同等级域名最小值不同，默认为 600
        @mx	Int	MX 优先级，范围为0 - 50，当 recordType 选择 MX 时，mx 参数必选
        """
        try:
            sub_domains = get['subDomain'].split(',')
            if len(sub_domains) <= 0:
                return public.returnMsg(False,'记录值列表不能为空!');

            result = {
                "status":True,
                "success":[],
                "error":{}
            }

            client = self.__client()
            for sub_domain in sub_domains:
                if not sub_domain: continue

                try:
                    req = models.CreateRecordRequest()
                    params = {
                        "Domain": get['domain'],
                        "SubDomain": sub_domain,
                        "RecordType": get['recordType'],
                        "RecordLine": get['recordLine'],
                        "Value": get['value'],
                        "MX": int(get['mx']),
                        "TTL": int(get['ttl'])
                    }

                    req.from_json_string(json.dumps(params))
                    resp = client.CreateRecord(req)
                    resp = self.__get_json(resp)
                    if 'RequestId' in resp:
                        result['success'].append(sub_domain)
                except TencentCloudSDKException as err:
                    result['error'][sub_domain] = err.message


            return result
        except :
            return public.returnMsg(False,public.get_error_info());


    def delete_record(self,get):
        """
        @删除解析记录
        @domain	String	解析记录所在的域名
        @recordId   Int	解析记录 ID
        """
        try:
            client = self.__client()
            req = models.DeleteRecordRequest()
            params = {
                "Domain": get['domain'],
                "RecordId": int(get['recordId'])
            }
            req.from_json_string(json.dumps(params))
            resp = client.DeleteRecord(req)
            resp = self.__get_json(resp)
            if 'RequestId' in resp:
                return public.returnMsg(True,'删除成功!')
            return public.returnMsg(False,'删除失败!')
        except TencentCloudSDKException as err:
            return public.returnMsg(False,err.message)


    def set_record_status(self,get):
        """
        @设置解析记录状态
        @domain	String	解析记录所在的域名
        @recordId   Int	解析记录 ID
        @status 状态 可选值为：“disable” 和 “enable”，分别代表 “暂停” 和 “启用”
        """
        try:
            client = self.__client()
            req = models.ModifyRecordStatusRequest()
            params = {
                "Domain": get['domain'],
                "RecordId": int(get['recordId']),
                "Status": get['status']
            }
            req.from_json_string(json.dumps(params))

            resp = client.ModifyRecordStatus(req)
            resp = self.__get_json(resp)
            if 'RequestId' in resp:
                return public.returnMsg(True,'修改成功!')
            return public.returnMsg(False,'修改失败!')

        except TencentCloudSDKException as err:
            return public.returnMsg(False,err.message)


    def modify_record(self,get):
        """
        @修改解析记录
        @domain	是	String	要操作的域名（主域名，不包括 www，例如：qcloud.com）
        @recordId	是	Int	解析记录的 ID，可通过 RecordList 接口返回值中的 ID 获取
        @subDomain	是	String	子域名，例如：www
        @recordType	是	String	记录类型，可选的记录类型为："A"，"CNAME"，"MX"，"TXT"，"NS"，"AAAA"，"SRV"
        @recordLine	是	String	记录的线路名称，例如："默认"
        @value	是	String	记录值，例如 IP：192.168.10.2，CNAME：cname.dnspod.com.，MX：mail.dnspod.com.
        @ttl	否	Int	TTL 值，范围1 - 604800，不同等级域名最小值不同，默认为 600
        @mx	否	Int	MX 优先级，范围为0 ~ 50，当 recordType 选择 MX 时，mx 参数必选
        """

        try:
            client = self.__client()
            req = models.ModifyRecordRequest()
            params = {
                "Domain": get['domain'],
                "RecordId": int(get['recordId']),
                "SubDomain":get['subDomain'],
                "RecordType": get['recordType'],
                "RecordLine": get['recordLine'],
                "Value": get['value'],
                "MX": int(get['mx']),
                "TTL": int(get['ttl'])
            }

            req.from_json_string(json.dumps(params))
            resp = client.ModifyRecord(req)
            resp = self.__get_json(resp)
            if 'RequestId' in resp:
                return public.returnMsg(True,'修改成功!')
            return public.returnMsg(False,'修改失败!')

        except TencentCloudSDKException as err:
            return public.returnMsg(False,err.message)

    """
    @添加DNSpod域名
    @domain	是	String	要添加的域名（主域名，不包括 www，例如：qcloud.com）
    @projectId	否	Int	项目 ID，如果不填写，则为 “默认项目”
    """
    def add_domain(self,get):
        try:
            domains = json.loads(get['domain'])
            if len(domains) <= 0:
                return public.returnMsg(False,'域名列表不能为空!');

            result = {
                "success":[],
                "error":{}
            }
            client = self.__client()
            for domain in domains:
                try:
                    req = models.CreateDomainRequest()
                    params = {
                        "Domain": domain
                    }
                    req.from_json_string(json.dumps(params))
                    resp = client.CreateDomain(req)
                    resp = self.__get_json(resp)
                    if 'RequestId' in resp:
                        result['success'].append(domain)
                except TencentCloudSDKException as err:
                    result['error'][domain] = err.message

            return result
        except :
            return public.returnMsg(False,public.get_error_info())


    """
    @删除DNSpod域名
    @domain 域名列表
    """
    def del_domain(self,get):
        try:
            domains = json.loads(get['domain'])
            if len(domains) <= 0: return public.returnMsg(False,'域名列表不能为空!');
            result = {
                "success":[],
                "error":{}
            }
            client = self.__client()
            for domain in domains:
                try:
                    req = models.DeleteDomainRequest()
                    params = {
                        "Domain": domain
                    }
                    req.from_json_string(json.dumps(params))
                    resp = client.DeleteDomain(req)
                    resp = self.__get_json(resp)
                    if 'RequestId' in resp:
                        result['success'].append(domain)
                except TencentCloudSDKException as err:
                    result['error'][domain] = err.message

            return result
        except :
            return public.returnMsg(False,public.get_error_info());



    def set_domain_status(self,get):
        """
        @设置DNSpod域名状态
        @domain 域名列表
        @status	是	String	可选值为：“disable” 和 “enable”，分别代表 “暂停” 和 “启用”
        """
        try:
            domains = json.loads(get['domain'])
            if len(domains) <= 0:
                return public.returnMsg(False,'域名列表不能为空!');

            result = {
                "status":True,
                "success":[],
                "error":{}
            }

            client = self.__client()
            for domain in domains:
                try:
                    req = models.ModifyDomainStatusRequest()
                    params = {
                        "Domain": domain,
                        "Status": get.status
                    }
                    req.from_json_string(json.dumps(params))
                    resp = client.ModifyDomainStatus(req)
                    resp = self.__get_json(resp)
                    if 'RequestId' in resp:
                        result['success'].append(domain)
                except TencentCloudSDKException as err:
                    result['error'][domain] = err.message
            return result
        except :
            return public.returnMsg(False,public.get_error_info());


    def get_domain_list(self,get = None):
        """
        @name 获取域名列表
        @param search 搜索关键字
        """
        try:
            client = self.__client()
            req = models.DescribeDomainListRequest()
            params = {}
            if 'search' in get:
                params['Keyword'] = get.search
            req.from_json_string(json.dumps(params))
            resp = client.DescribeDomainList(req)
            data = self.__get_json(resp)

            del data["DomainCountInfo"]
            DomainList = data["DomainList"]

            import page
            page, data_list = page.page_data(get, DomainList)
            data['page'] = page
            data['DomainList'] = data_list

            return data

        except TencentCloudSDKException as err:
            return public.returnMsg(False,self.__get_error(err))

    def __get_error(self,error):
        """
        @name 获取错误信息
        @param error 错误信息
        """
        return error.message

    def __get_json(self,resp):
        """
        @name 获取返回信息
        @param resp 返回信息
        """
        return json.loads(resp.to_json_string())


if __name__ == '__main__':
    dns_obj = dnspod_main()
    get = {}
    get['domain'] = 'muluo.org'
    get['recordId'] = '934626056'
    res = dns_obj.delete_record(get)
    print(res)