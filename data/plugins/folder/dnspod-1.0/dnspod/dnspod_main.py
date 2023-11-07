#coding: utf-8
import sys,os,time,json

panelPath = os.getenv('BT_PANEL')
if not panelPath: panelPath = '/www/server/panel'

os.chdir(panelPath);
sys.path.append("class/")
import public,random,requests,hmac,base64,urllib,binascii
from BTPanel import session,cache

from hashlib import sha1
import ssl
ssl._create_default_https_context=ssl._create_unverified_context

class dnspod_main:

    host = 'cns.api.qcloud.com'
    secretId = None
    secretKey = None
    aes_key = None

    tx_path = 'data/tencent.conf'
    def __init__(self):
        self.url = 'https://{}/v2/index.php'.format(self.host)

        self.aes_key = public.readFile('data/a_pass.pl')
        if not self.aes_key:
            self.aes_key = public.GetRandomString(16)
            public.writeFile('data/a_pass.pl',self.aes_key)

        if os.path.exists(self.tx_path):
            conf = public.readFile(self.tx_path)
            if conf:
                try:

                    data = json.loads(public.aes_decrypt(conf,self.aes_key))
                    self.appid = data['appid']
                    self.secretId = data['secretId']
                    self.secretKey = data['secretKey']
                except:pass

    """
    @设置密钥
    @secretId 必填 
    @secretKey 必填
    @appid 非必填 cos需要使用
    """
    def set_config(self,get):
        data = {}
        data['appid'] = ''
        data['secretId'] = get.secretId
        data['secretKey'] = get.secretKey       
        if 'appid' in get: data['appid'] = get.appid

        try:
            args = {
                'Action':'DomainList'        
            }
            self.appid = data['appid']
            self.secretId = data['secretId']        
            self.secretKey = data['secretKey']       

            params = self.get_pub_params(args)    
            req = requests.get(url = self.url, params = params)
            sdata =  req.json()['data']

            sdata = public.aes_encrypt(json.dumps(data),self.aes_key)
            public.writeFile(self.tx_path,sdata)

            return public.returnMsg(True,"设置成功!")
        except :
            return public.returnMsg(False,'密钥设置错误，请重新设置.')
        

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
    @遍历获取所有解析记录值
    @args json 
    @p 当前页数，默认0
    @out_list 列表
    """
    def __get_all_data(self, args, p, out_list = []):
        try:


            args['length'] = 100
            args['offset'] = p * args['length']
            params = self.get_pub_params(args)    

            req = requests.get(url = self.url, params = params)
            
            if req.status_code in [200]:
                ret = req.json()['data']     
                key = False
                if args['Action'] == 'RecordList': 
                    key = 'records'
                elif args['Action'] == 'DomainList': 
                    key = 'domains'

                if key:                          
                    out_list.extend(ret[key])
                    if len(ret[key]) >= args['length']:  
                        self.__get_all_record(args, p + 1, out_list)
        except :pass                
        ret[key] = out_list
        return ret

    """
    @获取DNS_NS记录
    """
    def get_dnspod_ns(self,get):

        try:
            key = '{}_dns_ns'.format(get['domain'])

            if not 'force' in get:
                ret = cache.get(key)
                if ret: return ret            
                
            args = {
                "Action":"RecordList",
                "domain":get['domain']      
            }

            params = self.get_pub_params(args)    
           
            req = requests.get(url = self.url, params = params)
            ret = req.json()['data']['domain']
            cache.set(key,ret,3600)
            return ret
        except :
            return public.returnMsg(False,public.get_error_info());  


    """
    @获取解析记录列表
    @domain String	要操作的域名（主域名，不包括 www，例如：qcloud.com）
    @subDomain	String	（过滤条件）根据子域名进行过滤
    @recordType	String	（过滤条件）根据记录类型进行过滤
    """
    def get_record_list(self,get):
        args = {
            "Action":"RecordList",
            "domain":get['domain']      
        }

        if 'length' in get: args['length'] = int(get['length'])
        offset = 10
        if 'offset' in get :
            offset = (int(get['offset']) - 1) * args['length']     
            args['offset'] = offset

        search = ''
        if 'search' in get: search =  get['search'].lower()

        ips = []
        if search:            
            slist = []
            ret = self.__get_all_data(args,0,slist)

            args['offset']  = offset            
            data = []
            searchs = ['ttl','value','name','type']
            for idx, x in enumerate(ret['records']):
                if public.check_ip(x['value']) and not x['value'] in ips: ips.append(x['value'])

                if idx < args['offset'] : continue;                
                if len(data) >= args['length']: break;

                for key in searchs:
                    if str(x[key]).lower().find(search) >= 0:
                        data.append(x)
                        break

            ret['info']['records_num'] = str(len(data))
            ret['info']['record_total'] = str(len(data))
            ret['records'] = data
            ret['ips'] = ips
            return ret
        else:
            params = self.get_pub_params(args)    
            req = requests.get(url = self.url, params = params)
            ret = req.json()['data']

            for idx, x in enumerate(ret['records']):
                if public.check_ip(x['value']) and not x['value'] in ips: ips.append(x['value'])
            ret['ips'] = ips
            return ret          



    """
    网站创建解析
    """
    def create_record_bysite(self,get):

        domains = json.loads(get['domains'])
        if len(domains) <= 0: return public.returnMsg(False,'域名列表不能为空!');

        result = {
            "status":True,
            "success":[],
            "error":{}
        }

        local_ip = public.GetLocalIp()
        for domain in domains: 
            if not domain: continue
            if public.check_ip(domain): continue

            root,sub_domain = public.get_root_domain(domain)     
            if not sub_domain: sub_domain = '@'
            args = {
                "Action":"RecordCreate",
                "domain": root,
                "subDomain":sub_domain,
                "recordLine":"默认",
                "recordType":'A',
                "value": local_ip,        
                
            }
            params = self.get_pub_params(args)    
            req = requests.get(url= self.url, params=params)
            
            if req.status_code in [200]:
                ret = req.json()           
                if ret['codeDesc'] == 'Success':  
                    result['success'].append(domain)
                else:
                    result['error'][domain] = ret['message']    
            else:
                result['error'][domain] = req.json() 
        return result

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
    def create_record(self,get):                
        try:
            sub_domains = get['subDomain'].split(',')
            if len(sub_domains) <= 0: return public.returnMsg(False,'记录值列表不能为空!');
            
            result = {
                "status":True,
                "success":[],
                "error":{}
            }        

            for sub_domain in sub_domains: 
                if not sub_domain: continue

                args = {
                    "Action":"RecordCreate",
                    "domain":get['domain'],
                    "subDomain":sub_domain,
                    "recordType":get['recordType'],
                    "recordLine":get['recordLine'],
                    "value":get['value'],
                    "ttl": get['ttl'],
                    "mx":get['mx']
                }
                params = self.get_pub_params(args)    
                req = requests.get(url=self.url, params=params)

                if req.status_code in [200]:
                    ret = req.json()           
                    if ret['codeDesc'] == 'Success':  
                        result['success'].append(sub_domain)
                    else:
                        result['error'][sub_domain] = ret['message']    
                else:
                    result['error'][sub_domain] = req.json() 
            return result
        except :
            return public.returnMsg(False,public.get_error_info());

    """
    @删除解析记录
    @domain	String	解析记录所在的域名
    @recordId   Int	解析记录 ID
    """
    def delete_record(self,get):
        args = {
            "Action":"RecordDelete",
            "domain":get['domain'],
            "recordId":get['recordId']
        }
        params = self.get_pub_params(args)    
        req = requests.get(url=self.url, params=params)

        if req.status_code in [200]:
            ret = req.json()
            if ret['codeDesc'] == 'Success':  
                return public.returnMsg(True,'删除成功!');

        return public.returnMsg(False,req.json()['message']);

    
    """
    @设置解析记录状态
    @domain	String	解析记录所在的域名
    @recordId   Int	解析记录 ID
    @status 状态 可选值为：“disable” 和 “enable”，分别代表 “暂停” 和 “启用”
    """
    def set_record_status(self,get):
        args = {
            "Action":"RecordStatus",
            "domain":get['domain'],
            "recordId":get['recordId'],
            "status": get['status']
        }
        params = self.get_pub_params(args)    
        req = requests.get(url=self.url, params=params)

        if req.status_code in [200]:
            ret = req.json()
            print(ret)
            if ret['codeDesc'] == 'Success':  
                return public.returnMsg(True,'修改成功!');

        return public.returnMsg(False,req.json()['message']);

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
    def modify_record(self,get):
        args = {
            "Action":"RecordModify",            
            "domain":get['domain'],
            "recordId": get['recordId'],
            "subDomain":get['subDomain'],
            "recordType":get['recordType'],
            "recordLine":get['recordLine'],
            "value":get['value'],
            "ttl" : get['ttl'],
            "mx": get['mx']
        }
        params = self.get_pub_params(args)    
        req = requests.get(url=self.url, params=params)
        if req.status_code in [200]:
            ret = req.json()
            print(ret)
            if ret['codeDesc'] == 'Success':  
                return public.returnMsg(True,'修改成功!');

        return public.returnMsg(False,req.json()['message']);
     
    """
    @添加DNSpod域名
    @domain	是	String	要添加的域名（主域名，不包括 www，例如：qcloud.com）
    @projectId	否	Int	项目 ID，如果不填写，则为 “默认项目”
    """
    def add_domain(self,get):
        try:
            domains = json.loads(get['domain'])
            if len(domains) <= 0: return public.returnMsg(False,'域名列表不能为空!');
          
            result = {
                "success":[],
                "error":{}
            }        
            for domain in domains:                
                args = {
                    "Action":"DomainCreate",
                    "domain":domain
                }
                params = self.get_pub_params(args) 
                req = requests.get(url=self.url, params=params)
        
                if req.status_code in [200]:
                    ret = req.json()           
                    if ret['codeDesc'] == 'Success':  
                        result['success'].append(domain)

                        if hasattr(get,'value'):
                            args = {}
                            args['domain'] = domain
                            args['subDomain'] = '@,www'
                            args['recordType'] = 'A'
                            args['recordLine'] = '默认'
                            args['value'] = get['value']     
                            args['ttl'] = 600
                            ret = self.create_record(args)
                    else:
                        result['error'][domain] = ret['message']    
                else:
                    result['error'][domain] = req.json()  

            return result
        except :
            return public.returnMsg(False,public.get_error_info());
        

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
            for domain in domains:                
                args = {
                    "Action":"DomainDelete",
                    "domain":domain
                }
                params = self.get_pub_params(args) 
                req = requests.get(url=self.url, params=params)
        
                if req.status_code in [200]:
                    ret = req.json()           
                    if ret['codeDesc'] == 'Success':  
                        result['success'].append(domain)
                    else:
                        result['error'][domain] = ret['message']    
                else:
                    result['error'][domain] = req.json()  

            return result
        except :
            return public.returnMsg(False,public.get_error_info());


    """
    @设置DNSpod域名状态
    @domain 域名列表
    @status	是	String	可选值为：“disable” 和 “enable”，分别代表 “暂停” 和 “启用”
    """
    def set_domain_status(self,get):
        try:
            domains = json.loads(get['domain'])
            if len(domains) <= 0: return public.returnMsg(False,'域名列表不能为空!');
            
            result = {
                "status":True,
                "success":[],
                "error":{}
            }        
            for domain in domains:                
                args = {
                    "Action":"SetDomainStatus",
                    "domain":domain,
                    "status":get['status']
                }
                params = self.get_pub_params(args) 
                req = requests.get(url=self.url, params=params)
        
                if req.status_code in [200]:
                    ret = req.json()           
                    if ret['codeDesc'] == 'Success':  
                        result['success'].append(domain)
                    else:
                        result['error'][domain] = ret['message']    
                else:
                    result['error'][domain] = req.json()  

            return result
        except :
            return public.returnMsg(False,public.get_error_info());

    """
    获取域名列表
    """
    def get_domain_list(self,get = None):
        
      
            args = {
                'Action':'DomainList'        
            }
            if get: 

                if 'length' in get: args['length'] = int(get['length'])
                if 'offset' in get :
                    args['offset'] = (int(get['offset']) - 1) * args['length']     

                search = ''
                if 'search' in get: search =  get['search'].lower()

                if search:            
                    slist = []
                    ret = self.__get_all_data(args,0,slist)

                    data = []
                    searchs = ['name','punycode','ttl','grade_title','remark','owner']

                    for idx, x in enumerate(ret['domains']):
                        if idx < args['offset']: continue;                
                        if len(data) >= args['length']: break;

                        for key in searchs:
                            if str(x[key]).lower().find(search) >= 0:
                                data.append(x)
                                break

                    ret['domains'] = data
                    ret['info']['domain_total'] = len(data)
                    return ret
                else:
                    try:
                        params = self.get_pub_params(args)    
                        req = requests.get(url = self.url, params = params)
                        return req.json()['data']   
                    except :
                        return public.returnMsg(False,req.json()); 
       
    """
    @sha1签名
    """
    def hash_hmac(self, code):
        hmac_code = hmac.new(self.secretKey.encode(), code.encode(), sha1).digest()
        return base64.b64encode(hmac_code).decode()

    """
    @请求签名
    """
    def sign(self, accessKeySecret, parameters):  
        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])

        canonicalizedQueryString = ''
        for (k, v) in sortedParameters:
            canonicalizedQueryString += '&' + k + '=' + str(v)
        stringToSign = 'GET' + self.host + '/v2/index.php?' + canonicalizedQueryString[1:]   
        print(stringToSign)
        signature = self.hash_hmac(stringToSign)
     
        return signature

    """
    @获取公共请求参数
    @args 参数列表
    """
    def get_pub_params(self,args):
        params = {  
           
            "Timestamp" : int(time.time()),
            "Nonce": random.randint(11111111111111, 99999999999999),
            "SecretId": self.secretId,
            "SignatureMethod":"HmacSHA1"
        }
        
        for x in args: params[x] = args[x]
        signStr = self.sign(self.secretKey,params)
        params['Signature'] = signStr
        
        return params


    #加密数据
    def De_Code(self,data):
        if sys.version_info[0] == 2:
            pdata = urllib.urlencode(data);
        else:
            pdata = urllib.parse.urlencode(data);
            if type(pdata) == str: pdata = pdata.encode('utf-8')
        return binascii.hexlify(pdata);
    
    #解密数据
    def En_Code(self,data):
        if sys.version_info[0] == 2:
            result = urllib.unquote(binascii.unhexlify(data));
        else:
            if type(data) == str: data = data.encode('utf-8')
            tmp = binascii.unhexlify(data)
            if type(tmp) != str: tmp = tmp.decode('utf-8')
            result = urllib.parse.unquote(tmp)

        if type(result) != str: result = result.decode('utf-8')
        return json.loads(result);



if __name__ == '__main__':
    dns_obj = dnspod_main()

    

    #dns_obj.add_domain(data)


