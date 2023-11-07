#coding: utf-8
import sys,os,time,json
panelPath = os.getenv('BT_PANEL')
if not panelPath: panelPath = '/www/server/panel'

sys.path.append("class/")
import public,random,requests,hmac,base64,datetime
from BTPanel import session,cache
from qcloud_cos import CosConfig,CosS3Client
import ssl
ssl._create_default_https_context=ssl._create_unverified_context

class cosfs_main:
    
    appid = None
    secretId = None
    secretKey = None
    aes_key = None
    conf_path = 'plugin/cosfs/mount.conf'
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
            buckets  = client.list_buckets()

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
    @获取所有存储桶列表
    @return list
    """
    def get_buckets(self,get = None):  
        
        try:
            data = {}        
            data['list'] = []
            data['total'] = 0
            client = self.__client()    
            buckets  = client.list_buckets()
            if not 'Buckets' in buckets or not buckets['Buckets']: return data
                
            search = ''
            if 'search' in get: search =  get['search'].lower()
    
            offset = 0; length = 10
            if 'length' in get: length = int(get['length'])
            if 'offset' in get :
                offset = (int(get['offset']) - 1) * length  
    
            mdata = self.get_mount_config()
            arr_list = buckets['Buckets']['Bucket']         
            
            regions = {}
            for region_list in self.get_regions(None):     
                for region in region_list['data']:        
                    regions[region['value']] = region['title']
                        
                
            slist = []
            total = 0
            for idx, obj in enumerate(arr_list):
                if not obj['Location'] in regions: continue
                
                obj['mounted'] = False
                obj['region_name'] = regions[obj['Location']]
                if obj['Name'] in mdata:  obj['mounted'] = mdata[obj['Name']]
                
                if obj['Name'].lower().find(search) >= 0 or  obj['Location'].lower().find(search) >= 0: 
                    total += 1                                       
                    slist.append(obj)
            
            slist.sort(key = lambda x:x["CreationDate"],reverse = True)
            for idx,obj in enumerate(slist):
                if idx >= offset and len(data['list']) < length:  data['list'].append(obj) 

            if len(data['list']) == 0: data['list'] = slist

            data['total'] = total
            return data
        except :
            return public.returnMsg(False,public.get_error_info());

    """
    获取未挂载的存储桶列表
    """
    def get_unmounted_buckets(self,get):
         
        try:
            data = {}        
            data['list'] = []
            data['total'] = 0
            client = self.__client()    
            buckets  = client.list_buckets()
            if not 'Buckets' in buckets or not buckets['Buckets']: return data

            offset = 0; length = 100

            mdata = self.get_mount_config()
            arr_list = buckets['Buckets']['Bucket']         
            
            regions = {}
            for region_list in self.get_regions(None):     
                for region in region_list['data']:        
                    regions[region['value']] = region['title']
                        
                
            slist = []
            total = 0
            for idx, obj in enumerate(arr_list):
                if not obj['Location'] in regions: continue               
                if obj['Name'] in mdata: continue
                            
                total += 1                                       
                slist.append(obj)
            
            slist.sort(key = lambda x:x["CreationDate"],reverse = True)
            for idx,obj in enumerate(slist):
                if idx >= offset and len(data['list']) < length:  data['list'].append(obj) 

            if len(data['list']) == 0: data['list'] = slist

            data['total'] = total
            return data
        except :
            return public.returnMsg(False,public.get_error_info());

    """
    @获取所有大区列表
    @return list
    """
    def get_regions(self,get):
        return [{"value":"中国大陆","data":[{"value":"ap-beijing-1","title":"北京一区"},{"value":"ap-beijing","title":"北京"},{"value":"ap-nanjing","title":"南京"},{"value":"ap-shanghai","title":"上海"},{"value":"ap-guangzhou","title":"广州"},{"value":"ap-chengdu","title":"成都"},{"value":"ap-chongqing","title":"重庆"}]},{"value":"亚太地区","data":[{"value":"ap-hongkong","title":"中国香港"},{"value":"ap-singapore","title":"新加坡"},{"value":"ap-mumbai","title":"孟买"},{"value":"ap-seoul","title":"首尔"},{"value":"ap-bangkok","title":"曼谷"},{"value":"ap-tokyo","title":"东京"}]},{"value":"北美地区","data":[{"value":"na-siliconvalley","title":"硅谷（美西）"},{"value":"na-ashburn","title":"弗吉尼亚（美东）"},{"value":"na-toronto","title":"多伦多"}]},{"value":"欧洲地区","data":[{"value":"eu-frankfurt","title":"法兰克福"},{"value":"eu-moscow","title":"莫斯科"}]}]

    """
    @创建存储桶
    @region 所属大区
    @bucket_name	待创建的存储桶名称，由 BucketName-APPID 构成
    """
    def create_bucket(self,get):        
        try:
            region = get['region']
            bucket_name = get['bucket_name']

            client = self.__client(region)
            response = client.create_bucket(
                Bucket = '{}-{}'.format(bucket_name,self.appid),
                ACL = 'private'
            )
            return public.returnMsg(True,'创建成功!'); 
        except :
            error = public.get_error_info()
            if error.find('BucketAlreadyOwnedByYou') >=0 or error.find('BucketAlreadyExists') >= 0 :
                return public.returnMsg(False,'创建失败，存储桶名称重复.'); 
            else:
                return public.returnMsg(False,public.get_error_info()); 

    """
    @删除存储桶
    @region 所属大区
    @bucket_name	待删除的存储桶名称
    """
    def delete_bucket(self,get):        
        try:
            region = get['region']
            bucket_name = get['bucket_name']

            client = self.__client(region)
            response = client.delete_bucket(
                Bucket = bucket_name
            )
            return public.returnMsg(True,'删除存储桶{}成功!'.format(bucket_name)); 
        except :
            error = public.get_error_info()
            if error.find('The bucket you tried to delete is not empty') >=0 :
                return public.returnMsg(False,'删除失败，请先手动删除所有文件.'); 
            return public.returnMsg(False,public.get_error_info()); 


    """
    @获取所有文件列表
    @region 所属大区
    @bucket_name 对象存储名称
    @path 指定路径
    @return list 
    """
    def get_list(self,get):
            
        region = get['region']
        bucket = get['bucket_name']
        path = self.get_path(get['path'])

        data = []
        client = self.__client(region)        
        objects = client.list_objects(Bucket=bucket,Prefix=path, MaxKeys=1000,Delimiter = '/')
        print(objects)
        if 'Contents' in objects:
            for b in objects['Contents']:
                tmp = {}
                b['Key'] = b['Key'].replace(path, '')
                if not b['Key']: continue
                tmp['name'] = b['Key']
                tmp['size'] = b['Size']
                tmp['type'] = b['StorageClass']
                tmp['download'] = self.generate_download_url(client,bucket,path + b['Key'])
                tstr = b['LastModified']
                t = datetime.datetime.strptime(tstr, "%Y-%m-%dT%H:%M:%S.%fZ")
                t += datetime.timedelta(hours=8)
                ts = int((time.mktime(t.timetuple()) + t.microsecond / 1000000.0))
                tmp['time'] = ts
                data.append(tmp)


        if 'CommonPrefixes' in objects:
            for i in objects['CommonPrefixes']:
                if not i['Prefix']: continue
                dir_dir = i['Prefix'].split('/')[-2] + '/'
                tmp = {}
                tmp["name"] = dir_dir
                tmp["type"] = None
                data.append(tmp)

        mlist = {}

        mlist['path'] = path
        mlist['list'] = data
        return mlist

    """
    @创建目录
    @region 所属大区
    @bucket_name 存储桶名称	
    @dir_name 目录名称
    """
    def create_dir(self,get):

        try:
            region = get['region']
            bucket_name = get['bucket_name']
            dir_name = self.get_path(get['dir_name'])
            client = self.__client(region)

            response = client.put_object(
                Bucket = bucket_name,
                Body = '',
                Key= dir_name
            )
            return public.returnMsg(True,'创建目录{}成功!'.format(dir_name)); 
        except :
            return public.returnMsg(False,public.get_error_info()); 

    """
    @批量删除
    @region 所属大区
    @bucket_name 存储桶名称	
    @filenames 文件名称列表，如：111/abc.txt,222/def.txt
    """
    def delete_object(self,get):
        try:
            region = get['region']
            bucket_name = get['bucket_name']

            client = self.__client(region)    
            for x in get['filenames'].split(','):     
                print(x)                                      
                response = client.delete_object(
                    Bucket = bucket_name,   
                    Key =  x
                )
            print(response)
            return public.returnMsg(True,'批量删除对象{}成功!'.format(get['filenames'])); 
        except :
            return public.returnMsg(False,public.get_error_info());


    """
    @上传文件 小于等于20M的文件调用简单上传，对于大于20MB的文件调用分块上传，对于分块上传未完成的文件会自动进行断点续传
    @region 所属大区
    @bucket_name 存储桶名称	
    @filename 文件名称
    @local_path 本地文件路径
    """
    def upload_file(self,get):
        try:
            region = get['region']
            bucket_name = get['bucket_name']
            filename =  get['filename']
            localPath = get['local_path']

            client = self.__client(region)          
            response = client.upload_file(
                Bucket = bucket_name,            
                Key = filename,
                LocalFilePath = localPath
            )
            return public.returnMsg(True,'上传文件{}成功!'.format(filename));  
        except :
            return public.returnMsg(False,public.get_error_info());
     
    """
    @ 对象移动
    @region 所属大区
    @bucket_name 存储桶名称	   
    @src 源文件
    @filename 文件名称
    """
    def move(self,get):
        try:
            ret = self.copy(get)
            if ret['status']:
                get['filenames'] = get['src']
                ret = self.delete_object(get)
                if ret['status']:
                    return public.returnMsg(True,'移动对象{}成功!'.format(get['filename']));  
            return ret
        except :
            return public.returnMsg(False,public.get_error_info());
        

    """
    @ 文件拷贝，小于5G的文件调用 copy_object，大于等于5G的文件调用分块上传的 upload_part_copy
    @region 所属大区
    @bucket_name 存储桶名称	   
    @src 源文件
    @filename 文件名称
    """
    def copy(self,get):
        try:
            region = get['region']
            bucket_name = get['bucket_name']            
            src = get['src']
            filename =  get['filename']
            
            client = self.__client(region)
            response = client.copy(
                Bucket = bucket_name,            
                Key = filename,
                CopySource = {
                    "Bucket": bucket_name,
                    "Key" : src,
                    "Region": region
                }
            )      
            return public.returnMsg(True,'拷贝文件{}成功!'.format(filename));  
        except :
            return public.returnMsg(False,public.get_error_info());

    def get_cosfs_bin(self):

        sbin = ['/usr/local/bin/cosfs','/usr/bin/cosfs','/usr/local/sbin/cosfs','/usr/sbin/cosfs']
        for bin_file in sbin:
            if os.path.exists(bin_file): return bin_file
        return 'cosfs'


    """
    @挂载目录
    @region 所属大区
    @bucket_name 存储名称
    @path 挂载的目录
    """
    def mount_cosfs(self,get):
        
        try:
            path = get['path']
            region = get['region']
            bucket_name = get['bucket_name']
            conf = '{}:{}:{}'.format(bucket_name,self.secretId,self.secretKey)
        
            #写入配置文件
            local_path = '/etc/passwd-cosfs'
            if os.path.exists(local_path): 
                re_conf = public.readFile(local_path)
                if re_conf:                    
                    if re_conf.find(conf) < 0:  conf = '{}\n{}'.format(re_conf,conf)  

            public.writeFile(local_path,conf)
            public.ExecShell("chmod 640 " + local_path)
        
            if not os.path.exists(path):
                public.ExecShell('mkdir -p {}'.format(path))

            if self.check_mount(path):  
                return public.returnMsg(False,'目录已经被挂载，请更换到其他目录.');        

            shell = '{} {} {} -ourl=http://cos.{}.myqcloud.com -odbglevel=info -onoxattr -oallow_other'.format(self.get_cosfs_bin(),bucket_name,path,region)
            ret = public.ExecShell(shell)  
            if ret[1]: return public.returnMsg(False,ret[1]); 

            sh_path = '/www/server/panel/script/cosfs.sh'
            public.ExecShell('echo "{}">> {} '.format(shell,sh_path))   

            cosfs_path = '/etc/init.d/bt-cosfs'
            if not os.path.exists(cosfs_path):
                public.writeFile(cosfs_path,'''#! /bin/bash
#
# cosfs Automount Tencentyun COS Bucket in the specified direcotry.
# chkconfig: 2345 90 10
# description: Activates/Deactivates cosfs configured to start at boot time.

bash {}'''.format(sh_path))
                public.ExecShell('chmod +x /etc/init.d/bt-cosfs')

                public.ExecShell('sudo update-rc.d bt-cosfs defaults')
                public.ExecShell('chkconfig --add bt-cosfs')
                public.ExecShell('chkconfig --level 2345 bt-cosfs on')
	

            if self.check_mount(path):  
                data = self.get_mount_config()
                data[bucket_name] = path
                self.set_mount_config(data)
                cache.delete('sys_disk')
                return public.returnMsg(True,'存储对象{}已成功挂载到{}目录'.format(bucket_name,path));
            return public.returnMsg(False,ret[0]);
        except :
            return public.returnMsg(False,public.get_error_info());

    """
    @卸载挂载目录
    @bucket_name 存储对象名称
    @path 挂载的目录
    """
    def umount_cosfs(self,get):
        try:
            path = get['path']
            bucket_name = get['bucket_name']

            ret = public.ExecShell('umount {}'.format(path))
            if ret[1]: return public.returnMsg(False,ret[1]);

            reg = 'cosfs#{} {}.+'.format(bucket_name,path)

            data = self.get_mount_config()
            del data[bucket_name]
            self.set_mount_config(data)

            cache.delete('sys_disk')
            return public.returnMsg(True,'卸载成功.');
        except :
            return public.returnMsg(False,public.get_error_info());

    """
    @获取下载地址
    @client 客户端对象
    @bucket_name 存储名称
    @object_name 文件名
    @return url
    """
    def generate_download_url(self,client,bucket_name,object_name):              
        expires = 60 * 60
        url = client.get_presigned_download_url(Bucket = bucket_name,Key=object_name, Expired=expires,)
        return url

    # 取目录路径
    def get_path(self, path):
        if path == '/': path = '';
        if path[:1] == '/':
            path = path[1:];
        if path[-1:] != '/': path += '/';
        if path == '/': path = '';
        return path.replace('//', '/');

    def check_mount(self,path):        
        ret = public.ExecShell('ls /www -al')
        link_path = False
        
        if ret[0][:1] == 'l': link_path = ret[0].split(' ')[-1].strip()
        if link_path: path = path.replace('/www',link_path)

        ret = public.ExecShell("df -h|grep {}".format(path))
        arrs = ret[0].split() 

        if path in arrs: return ret[0]
        return False

    #获取配置
    def get_mount_config(self):
        try:            
            data = public.readFile(self.conf_path)
            if not data:  data= "{}"
            return json.loads(data)
        except :
            return {}

    #保存配置
    def set_mount_config(self,data):
        public.writeFile(self.conf_path,json.dumps(data))


    """
    @获取cos连接
    @region 连接指定大区
    """
    def __client(self,region = 'cos'):                           
        config = CosConfig(Region=region, SecretId = self.secretId, SecretKey = self.secretKey)
        client = CosS3Client(config)
        return client 

if __name__ == "__main__":
    cos = cosfs_main()