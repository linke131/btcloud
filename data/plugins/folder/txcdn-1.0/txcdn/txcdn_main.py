import sys,os,time,json
panelPath = os.getenv('BT_PANEL')
if not panelPath: panelPath = '/www/server/panel'

os.chdir(panelPath)
sys.path.append("class/")
import public,random

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cdn.v20180606 import cdn_client, models
import ssl
ssl._create_default_https_context=ssl._create_unverified_context

class txcdn_main:

    appid = None
    secretId = None
    secretKey = None
    aes_key = None
    endpoint = "cdn.tencentcloudapi.com"
    tx_path = 'data/tencent.conf'

    def __init__(self):

        self.aes_key = public.readFile('data/a_pass.pl')
        if not self.aes_key:
            self.aes_key = public.GetRandomString(16)
            public.writeFile('data/a_pass.pl',self.aes_key)

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
            req = models.DescribeDomainsConfigRequest()         
            resp = client.DescribeDomainsConfig(req) 

            sdata = public.aes_encrypt(json.dumps(data),self.aes_key)
            public.writeFile(self.tx_path,sdata)
            return public.returnMsg(True,"设置成功!")
        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))

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
    @获取域名详细配置）
    """
    def get_domain_byname(self,get = None):
        try:

            domain = get['domain'].strip()
            client = self.__client()
            req = models.DescribeDomainsConfigRequest()
            if get:
                params = { }
                params['Filters'] = []
                params['Filters'].append({ 
                    "Value":[domain],
                    "Name":"domain", 
                    "Fuzzy":False 
                })    
                req.from_json_string(json.dumps(params))
            
            resp = client.DescribeDomainsConfig(req) 
            data = self.__get_json(resp)
            for x in data['Domains']:
                x['resolver'] = self.check_dns_cname(x['Domain'],x['Cname'])
            return data
        except TencentCloudSDKException as err: 
            if str(err).find('CdnUserNotExist') >=0 :
                return public.returnMsg(False,'未开通CDN服务，请先开通. <a class="btlink" target="_blank" href="https://console.cloud.tencent.com/cdn">立即开通</a>')
            return public.returnMsg(False,self.__get_error(err))

    """
    @获取域名列表
    @p 当前页数
    @page 每页显示条数
    @search 搜索条件（域名）
    """
    def get_domains(self,get = None):

        try:

            client = self.__client()
            req = models.DescribeDomainsConfigRequest()
            if get:
                params = { }

                if 'offset' in get: params['Offset'] = (int(get['offset']) - 1) * int(get['length'])
                if 'length' in get: params['Limit'] = int(get['length'])
                if 'search' in get: 
                    if get['search']:   
                        search= get['search'].strip()                 
                        params['Filters'] = []
                        params['Filters'].append({ 
                            "Value":[search],
                            "Name":"domain", 
                            "Fuzzy":True 
                        })

                        params['Filters'].append({ 
                            "Value":[search],
                            "Name":"domain", 
                            "Fuzzy":True 
                        })       

                req.from_json_string(json.dumps(params))
            
            resp = client.DescribeDomainsConfig(req) 
            data = self.__get_json(resp)
            for x in data['Domains']:
                x['resolver'] = self.check_dns_cname(x['Domain'],x['Cname'])
            return data
        except TencentCloudSDKException as err: 
            if str(err).find('CdnUserNotExist') >=0 :
                return public.returnMsg(False,'未开通CDN服务，请先开通. <a class="btlink" target="_blank" href="https://console.cloud.tencent.com/cdn">立即开通</a>')
            return public.returnMsg(False,self.__get_error(err))


    """
    @比较cname
    """
    def check_dns_cname(self,domain,val):     
        import dns.resolver
        try:
            ret = dns.resolver.query(domain, 'CNAME')           
            data = []
            for i in ret.response.answer:                  
                for j in i.items:
                    d_val = str(j).rstrip('.')
                    if d_val == val: return True
        except:
            pass
        return False
    
    """
    @设置域名SSL
    @domain 域名
    @csr 证书内容(非必填，为空则表示从当前网站列表获取证书)
    @key 证书私钥（非必填，为空则表示从当前网站列表获取证书）
    """
    def set_ssl_config(self,get):
        try:
            client = self.__client()
            req = models.UpdateDomainConfigRequest()

            ret =  self.__get_ssl_args(get)
            if 'status' in ret : return public.returnMsg(False,ret['msg'])
            
            params = {
                 "Domain" : get['domain'],
                 "Https": ret
            }
            req.from_json_string(json.dumps(params))
            resp = client.UpdateDomainConfig(req) 
            result = self.__get_json(resp)
            if 'RequestId' in result:
                return public.returnMsg(True,"设置域名SSL[{}]成功，预计时间5-10分钟，请等待执行完毕.".format(get['domain']));
            return result
        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))

    """
    @设置域名回源操作
    @domain 域名
    @origins 回源地址 ['1.1.1.1']
    @originType 回源类型
    @protocol 回源协议
    """
    def set_origin_config(self,get):
        try:
            client = self.__client()
            req = models.UpdateDomainConfigRequest()
            params = {
                 "Domain" : get['domain'],
                 "Origin": self.__get_origin_args(get)
            }   
            req.from_json_string(json.dumps(params))

            resp = client.UpdateDomainConfig(req) 
            result = self.__get_json(resp)
            if 'RequestId' in result:
                return public.returnMsg(True,"设置域名[{}]回源成功，预计时间5-10分钟，请等待执行完毕.".format(get['domain']));
            return result
        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))


    """
    @设置带宽封顶
    @domain 操作的域名
    @status 状态 on：开启 off：关闭
    @limit 流量限制单位bps
    @opera 操作 RESOLVE_DNS_TO_ORIGIN：直接回源，仅自有源站域名支持 RETURN_404：全部请求返回 404
    """
    def set_band_width(self,get):

        try:
            client = self.__client()
            req = models.UpdateDomainConfigRequest()
            params = {
                 "Domain" : get['domain'],
                 "BandwidthAlert": {
                     "Switch":get['status'],
                     "BpsThreshold": int(get['limit']),
                     "CounterMeasure": get['opera']
                 }
            }   
            req.from_json_string(json.dumps(params))

            resp = client.UpdateDomainConfig(req) 
            result = self.__get_json(resp)
            if 'RequestId' in result:
                return public.returnMsg(True,"设置域名[{}]带宽封顶成功.".format(get['domain']));
            return result
        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))

    """
    @获取报表数据
    @start_time 查询起始日期：yyyy-MM-dd HH:mm:ss
    @end_time 查询结束日期：yyyy-MM-dd HH:mm:ss
    @area 查询区域  mainland：中国大陆  overseas：中国境外
    """
    def get_report_data(self,get):
        try:
            client = self.__client()
            req = models.DescribeReportDataRequest()
            params = {                
                 "StartTime": get['start_time'],
                 "EndTime": get['end_time'],
                 "ReportType" : "daily",
                 "Area": get['area']
            }   
            req.from_json_string(json.dumps(params))

            resp = client.DescribeReportData(req) 
            result = self.__get_json(resp)
            return result
        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))

    """
    @获取top数据
    @start_time 查询起始日期：yyyy-MM-dd HH:mm:ss
    @end_time 查询结束日期：yyyy-MM-dd HH:mm:ss
    @metric top类型 url：访问 URL 排序，带参数统计，支持的 Filter 为 flux、request
                    path：访问 URL 排序，不带参数统计，支持的 Filter 为 flux、request（白名单功能）
                    district：省份、国家/地区排序，支持的 Filter 为 flux、request
                    isp：运营商排序，支持的 Filter 为 flux、request
                    host：域名访问数据排序，支持的 Filter 为：flux、request、bandwidth、fluxHitRate、2XX、3XX、4XX、5XX、statusCode
                    originHost：域名回源数据排序，支持的 Filter 为 flux、request、bandwidth、origin_2XX、origin_3XX、origin_4XX、origin_5XX、

    @Filter 过滤字段flux：Metric 为 host 时指代访问流量，originHost 时指代回源流量
                    bandwidth：Metric 为 host 时指代访问带宽，originHost 时指代回源带宽
                    request：Metric 为 host 时指代访问请求数，originHost 时指代回源请求数
                    fluxHitRate：平均流量命中率
                    200：访问 2XX 状态码
                    301：访问 3XX 状态码
                    302  访问 3XX 状态码                
                    500：访问 5XX 状态码
                    origin_200：回源 2XX 状态码
                    origin_301：回源 3XX 状态码
                    origin_302：回源 4XX 状态码
                    origin_500：回源 5XX 状态码
    @domains 查询指定域名(非必填)
    @area 查询区域  mainland：中国大陆  overseas：中国境外
    """
    def get_top_data(self,get):

        try:
            client = self.__client()
            req = models.ListTopDataRequest()
            params = {
                 "StartTime": get['start_time'],
                 "EndTime": get['end_time'],    
                 "Metric": get['metric']
            }   

            if hasattr(get,'domains'):  params['Domains'] = json.loads(get['domains'])
            if hasattr(get,'area'):  params['Area'] = get['area']

            req.from_json_string(json.dumps(params))

            resp = client.ListTopData(req) 
            result = self.__get_json(resp)
            return result
        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))

    """
    @添加域名
    @domain 域名列表
    @serviceType 网站类型 web：静态加速 download：下载加速 media：流媒体点播加速
    """
    def add_domain(self,get):
        try:
            client = self.__client()
            req = models.AddCdnDomainRequest()
                
            params = {
                "Domain" : get['domain'],
                "Area":"mainland",
                "ServiceType" : get['serviceType'],               
                "Origin": self.__get_origin_args(),
                "Ipv6Access": {
                    "Switch": "on"
                }
            }
           
            params['Origin']['ServerName'] = get['domain']
       
            httpsData =  self.__get_ssl_args(get)
            if not 'status' in httpsData :  params['Https'] = httpsData

            req.from_json_string(json.dumps(params))
            resp = client.AddCdnDomain(req) 

            result = self.__get_json(resp)
            if 'RequestId' in result:
                return public.returnMsg(True,"添加域名[{}]成功.".format(get['domain']))
            return result
        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))
        
    """
    @删除域名
    @domain 域名
    """
    def del_domain(self,get):
        try:
            client = self.__client()
            req = models.DeleteCdnDomainRequest()

            params = {
                "Domain" : get['domain']              
            }        
            req.from_json_string(json.dumps(params))
            resp = client.DeleteCdnDomain(req) 

            result = self.__get_json(resp)
            if 'RequestId' in result:
                return public.returnMsg(True,"删除域名[{}]，预计时间5-10分钟，请等待执行完毕..".format(get['domain']));
            return result

        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))


    """
    @停用域名
    @domain 域名
    """
    def stop_domain(self,get):
        try:
            client = self.__client()
            req = models.StopCdnDomainRequest()

            params = {
                "Domain" : get['domain']              
            }        
            req.from_json_string(json.dumps(params))
            resp = client.StopCdnDomain(req) 

            result = self.__get_json(resp)
            if 'RequestId' in result:
                return public.returnMsg(True,"停用域名[{}]，预计时间5-10分钟，请等待执行完毕..".format(get['domain']));
            return result

        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))

    """
    @启用域名
    @domain 域名
    """
    def start_domain(self,get):
        try:
            client = self.__client()
            req = models.StartCdnDomainRequest()

            params = {
                "Domain" : get['domain']              
            }        
            req.from_json_string(json.dumps(params))
            resp = client.StartCdnDomain(req) 

            result = self.__get_json(resp)
            if 'RequestId' in result:
                return public.returnMsg(True,"启用域名[{}]成功，预计时间5-10分钟，请等待执行完毕.".format(get['domain']));
            return result

        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))


    """
    @域名解析操作
    @value 解析值 当value=source表示回源，更改为当前服务器ip
    """
    def set_domain_record(self,get = None):

        domain = get['domain']    
        value = get['value']
        if get['value'] == 'source': value = public.GetLocalIp()

        root,zone = public.get_root_domain(domain)
        if not zone: zone = '@'

        import dnspod_main
        dns_pod = dnspod_main.dnspod_main()

        dmlist = dns_pod.get_domain_list({'length':100})
        for x in dmlist['domains']:
            if x['name'] == root:                
                args = {}                        
                args['domain'] = root
                args['subDomain'] = zone
                args['recordType'] = 'CNAME'
                args['recordLine'] = '默认'
                args['value'] = value
                args['ttl'] = x['min_ttl']

                ret = dns_pod.create_record(args)
            
                if ret['status']:
                    return public.returnMsg(True,'修改成功!');
        
        return public.returnMsg(False,'域名不在DNSPod，请先添加.');


    """
    @获取刷新历史记录
    @start_time 开始时间
    @end_time 结束时间
    """
    def get_purge_list(self,get):
        try:
            search = ''
            if 'search' in get: search = get['search']

            client = self.__client()
            req = models.DescribePurgeTasksRequest()
            
            params = {        
                "StartTime": get['start_time'],
                "EndTime": get['end_time'],
                "Limit" : 2000
            }        
            req.from_json_string(json.dumps(params))
            resp = client.DescribePurgeTasks(req) 

            slist = self.__get_json(resp)
            if not search: return slist

            data = []
            for x in slist['PurgeLogs']: 
                if x['Url'].find(search) >= 0:  data.append(x)
            slist['PurgeLogs'] = data
            slist['TotalCount'] = len(data)
            return slist

        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))


    """
    获取刷新配额
    """
    def get_purge_count(self,get):
        try:
            client = self.__client()
            req = models.DescribePurgeQuotaRequest()  
            resp = client.DescribePurgeQuota(req) 

            return self.__get_json(resp)

        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))

    """
    @刷新URL
    @urls  ['http://bt.cn/1.html']
    """
    def purge_url(self,get):
        try:
            client = self.__client()
            req = models.PurgeUrlsCacheRequest()

            params = {
                "Urls" : json.loads(get['urls'].strip())              
            }        
            req.from_json_string(json.dumps(params))
            resp = client.PurgeUrlsCache(req) 

            result = self.__get_json(resp)
            if 'RequestId' in result:
                return public.returnMsg(True,"刷新成功，请等待执行完毕.");
            return result            

        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))


    """
    @刷新目录
    @paths  ['http://bt.cn/admin']
    """
    def purge_path(self,get):
        try:
            client = self.__client()
            req = models.PurgePathCacheRequest()

            params = {
                "Paths" : json.loads(get['paths']),
                "FlushType" : "delete"
            }        
            req.from_json_string(json.dumps(params))
            resp = client.PurgePathCache(req) 

            result = self.__get_json(resp)
            if 'RequestId' in result:
                return public.returnMsg(True,"刷新成功，请等待执行完毕.");
            return result 
        except TencentCloudSDKException as err: 
            return public.returnMsg(False,self.__get_error(err))


    def __get_origin_args(self,get = None):
        param = {}
        if get:
            origins = json.loads(get['origins'])
            arrs = origins[0].split(':')

            originType = 'domain'
            if public.check_ip(arrs[0]): originType = 'ip'
            
            param = {
                "Origins": origins,
                "OriginType" : originType,
                "OriginPullProtocol" : get['originPullProtocol']
            }
        else:
            param = {                
                "Origins": [public.GetLocalIp()],
                "OriginType" : "ip",
                "OriginPullProtocol" : 'http'
            }
        return param

    """
    @根据域名查找网站名称的SSL情况
    """
    def __get_domain_ssl_info(self,domain):
        pid = public.M('domain').where("name=?",(domain,)).getField('pid')
        if pid:
            siteName = public.M('sites').where("id=?",(pid,)).getField('name')

            import panelSite
            site_obj = panelSite.panelSite()
          
            args = public.dict_obj()
            args['siteName'] = siteName
            sData = site_obj.GetSSL(args)
            return sData

        return {}
                  
    """
    @解析SSL参数
    """
    def __get_ssl_args(self,get = None):        
        try:
            if 'csr' in get:
                httpData = {
                    "CertInfo": {
                        "Certificate": get['csr'],
                        "PrivateKey":  get['key']
                    },
                    "Switch": "on",
                    "Http2": "on"
                }                    
                return httpData  
            else:                                      
                sdata = self.__get_domain_ssl_info(get['domain'])
                if 'key' in sdata and 'csr' in sdata and sdata['key']:                                       
                    httpData = {
                        "CertInfo": {
                            "Certificate": sdata['csr'],
                            "PrivateKey":  sdata['key']
                        },
                        "Switch": "on",
                        "Http2": "on"
                    }       
                    
                    return httpData  
                
                return public.returnMsg(False,'当前面板不存在此站点或者站点未开启SSL，请手动填写证书.') 
                
        except : 
            #'设置失败，请手动填写证书.'
            return public.returnMsg(False,public.get_error_info()) 
    """
    @class转为json对象
    """
    def __get_json(self,resp):
        return json.loads(resp.to_json_string())
    
    """
    @获取CDN客户端对象
    """
    def __client(self):
        cred = credential.Credential(self.secretId,self.secretKey) 
        httpProfile = HttpProfile()
        httpProfile.endpoint = self.endpoint

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = cdn_client.CdnClient(cred, "", clientProfile) 

        return client

    """
    @格式化错误信息
    """
    def __get_error(self,err):
        e_code = err.get_code()
        
        data = {
            "InternalError.DataSystemError": "数据查询错误，请联系腾讯云工程师进一步排查。",
            "InternalError.ScdnUserNoPackage": "SCDN服务未生效，请购买或续费SCDN套餐后重试。",
            "InternalError.ScdnUserSuspend": "安全加速服务已停服，请重新购买套餐后开启。",
            "InvalidParameter.CDNStatusInvalidDomain": "域名状态不合法。",
            "InvalidParameter.CamResourceBelongToDifferentUser": "同一次请求的资源AppId不一致。",
            "InvalidParameter.CamResourceSixStageError": "资源六段式标记参数错误。",
            "InvalidParameter.CamTagKeyAlreadyAttached": "域名已与该标签关联，请勿重复操作。",
            "InvalidParameter.CamTagKeyIllegal": "标签键字符不合法。",
            "InvalidParameter.CamTagKeyNotExist": "标签键不存在。",
            "InvalidParameter.CamTagValueIllegal": "标签值字符不合法。",
            "InvalidParameter.CdnCertNotPem": "HTTPS证书无效。",
            "InvalidParameter.CdnClsDuplicateTopic": "存在重复主题。",
            "InvalidParameter.CdnClsTopicNameInvalid": "主题名字不合法。",
            "InvalidParameter.CdnClsTopicNotExist": "CLS主题不存在。",
            "InvalidParameter.CdnConfigInvalidHost": "域名不合法。",
            "InvalidParameter.CdnConfigInvalidTag": "标签配置不合法。",
            "InvalidParameter.CdnConfigTagRequired": "域名添加失败，当前域名必须选择标签，请确认后重试。",
            "InvalidParameter.CdnHostHasSpecialConfig": "域名拥有特殊配置，需人工处理。",
            "InvalidParameter.CdnHostInternalHost": "内部域名不允许接入。",
            "InvalidParameter.CdnHostInvalidMiddleConfig": "错误的中间源配置。",
            "InvalidParameter.CdnHostInvalidParam": "域名格式不合法，请确认后重试。",
            "InvalidParameter.CdnHostInvalidStatus": "域名状态不合法。",
            "InvalidParameter.CdnInterfaceError": "内部接口错误，请联系腾讯云工程师进一步排查。",
            "InvalidParameter.CdnParamError": "参数错误，请参考文档中示例参数填充。",
            "InvalidParameter.CdnPurgeWildcardNotAllowed": "刷新不支持泛域名。",
            "InvalidParameter.CdnPushWildcardNotAllowed": "预热不支持泛域名。",
            "InvalidParameter.CdnStatInvalidDate": "日期不合法，请参考文档中日期示例。",
            "InvalidParameter.CdnStatInvalidFilter": "统计维度不合法，请参考文档中统计分析示例。",
            "InvalidParameter.CdnStatInvalidMetric": "统计类型不合法，请参考文档中统计分析示例。",
            "InvalidParameter.CdnStatInvalidProjectId": "项目ID错误，请确认后重试。",
            "InvalidParameter.CdnStatTooManyDomains": "查询的域名数量超过限制。",
            "InvalidParameter.CdnUrlExceedLength": "URL超过限制长度。",
            "InvalidParameter.ClsIndexConflict": "索引冲突。",
            "InvalidParameter.ClsIndexRuleEmpty": "索引规则为空。",
            "InvalidParameter.ClsInvalidContent": "无效内容。",
            "LimitExceeded.CamResourceTooManyTagKey": "单个资源标签键数不能超过50。",
            "LimitExceeded.CamTagKeyTooLong": "标签键长度超过最大值。",
            "LimitExceeded.CamTagKeyTooManyTagValue": "单个标签键对应标签值不能超过1000。",
            "LimitExceeded.CamUserTooManyTagKey": "单个用户最多1000个不同的key。",
            "LimitExceeded.CdnCallingQueryIpTooOften": "查询IP归属操作过于频繁。",
            "LimitExceeded.CdnClsTooManyTopics": "该账号已经创建了太多主题。",
            "LimitExceeded.CdnHostOpTooOften": "域名操作过于频繁。",
            "LimitExceeded.CdnPurgePathExceedBatchLimit": "刷新的目录数量超过限制。",
            "LimitExceeded.CdnPurgePathExceedDayLimit": "刷新的目录数量超过每日限制。",
            "LimitExceeded.CdnPurgeUrlExceedBatchLimit": "刷新的Url数量超过限制。",
            "LimitExceeded.CdnPurgeUrlExceedDayLimit": "刷新的Url数量超过每日限额。",
            "LimitExceeded.CdnPushExceedBatchLimit": "预热的Url数量超过单次限制。",
            "LimitExceeded.CdnPushExceedDayLimit": "预热的Url数量超过每日限制。",
            "LimitExceeded.CdnQueryIpBatchTooMany": "批量查询IP归属个数超过限制。",
            "LimitExceeded.CdnUserTooManyHosts": "接入域名数超出限制。",
            "LimitExceeded.ClsLogSizeExceed": "日志大小超限。",
            "LimitExceeded.ClsLogsetExceed": "日志集数目超出。",
            "LimitExceeded.ClsTopicExceed": "主题超限。",
            "LimitExceeded.ScdnLogTaskExceedDayLimit": "每日任务数量超出最大值。",
            "ResourceInUse.CdnConflictHostExists": "域名与系统中已存在域名存在冲突。",
            "ResourceInUse.CdnHostExists": "域名已存在。",
            "ResourceInUse.CdnOpInProgress": "CDN资源正在被操作中。",
            "ResourceInUse.TcbHostExists": "域名已存在。",
            "ResourceNotFound.CamTagKeyNotExist": "标签键不存在。",
            "ResourceNotFound.CamTagNotExist": "标签不存在。",
            "ResourceNotFound.CdnHostNotExists": "账号下无此域名，请确认后重试。",
            "ResourceNotFound.CdnUserNotExists": "未开通CDN服务，请开通后使用此接口。",
            "ResourceNotFound.CdnUserTooManyHosts": "接入域名数超出限制。",
            "ResourceNotFound.ClsIndexNotExist": "索引不存在。",
            "ResourceNotFound.ClsLogsetNotExist": "日志集不存在。",
            "ResourceNotFound.ClsTopicNotExist": "主题不存在。",
            "ResourceUnavailable.CdnHostBelongsToOthersInMainland": "该域名已在其他处接入中国境内服务地域，如需修改服务地域为全球，需验证取回域名。",
            "ResourceUnavailable.CdnHostBelongsToOthersInOverseas": "该域名已在其他处接入中国境外服务地域，如需修改服务地域为全球，需验证取回域名。",
            "ResourceUnavailable.CdnHostExistsInTcb": "域名已经在TCB控制台接入。",
            "ResourceUnavailable.CdnHostIsLocked": "域名被锁定。",
            "ResourceUnavailable.CdnHostIsNotOffline": "域名已开启CDN加速，请手动停用后重试当前操作。",
            "ResourceUnavailable.CdnHostIsNotOnline": "域名已停用，无法提交预热。",
            "ResourceUnavailable.CdnHostNoIcp": "域名未备案。",
            "UnauthorizedOperation.CdnAccountUnauthorized": "子账号禁止查询整体数据。",
            "UnauthorizedOperation.CdnCamUnauthorized": "子账号未配置cam策略。",
            "UnauthorizedOperation.CdnClsNotRegistered": "该账号未授权开通CLS。",
            "UnauthorizedOperation.CdnDomainRecordNotVerified": "域名解析未进行验证。",
            "UnauthorizedOperation.CdnHostExistsInInternal": "域名在内部系统已存在，请提工单处理。",
            "UnauthorizedOperation.CdnHostIsOwnedByOther": "该域名属于其他账号，您没有权限接入。",
            "UnauthorizedOperation.CdnHostIsToApplyHost": "域名需要提工单申请接入。",
            "UnauthorizedOperation.CdnHostIsUsedByOther": "域名已被其他账号接入，更多详情请提交工单联系我们。",
            "UnauthorizedOperation.CdnHostUnauthorized": "CDN子账号加速域名未授权。",
            "UnauthorizedOperation.CdnInvalidUserStatus": "用户状态不合法，暂时无法使用服务。",
            "UnauthorizedOperation.CdnProjectUnauthorized": "子账号项目未授权。",
            "UnauthorizedOperation.CdnTagUnauthorized": "子账号标签未授权。",
            "UnauthorizedOperation.CdnTxtRecordValueNotMatch": "域名解析记录值验证不通过。",
            "UnauthorizedOperation.CdnUserAuthFail": "CDN用户认证失败。",
            "UnauthorizedOperation.CdnUserAuthWait": "CDN用户待认证。",
            "UnauthorizedOperation.CdnUserIsSuspended": "加速服务已停服，请重启加速服务后重试。",
            "UnauthorizedOperation.CdnUserNoWhitelist": "非内测白名单用户，无该功能使用权限。",
            "UnauthorizedOperation.ClsInvalidAuthorization": "无效的授权。",
            "UnauthorizedOperation.ClsServiceNotActivated": "CLS服务未开通，请先在CLS控制台开通服务。",
            "UnauthorizedOperation.ClsUnauthorized": "授权未通过。",
        }

        if e_code in data:
            return data[e_code]
        return err.__str__()


        

if __name__ == "__main__":
    obj = txcdn_main()
    data = {
        'domain': "bbb.muluo.org",
        'serviceType':"web"
    }
    ret = obj.add_domain(data)
    print(ret)

