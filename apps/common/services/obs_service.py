"""
华为云 OBS 服务
"""
from obs import ObsClient
from django.conf import settings
from django.utils import timezone
import os


class OBSService:
    """华为云OBS服务"""
    
    def __init__(self):
        config = settings.HUAWEI_OBS_CONFIG
        
        # 检查配置
        if not config['access_key'] or not config['secret_key']:
            raise ValueError("华为云OBS未配置，请设置环境变量 HUAWEI_ACCESS_KEY 和 HUAWEI_SECRET_KEY")
        
        self.obs_client = ObsClient(
            access_key_id=config['access_key'],
            secret_access_key=config['secret_key'],
            server=config['server']
        )
        self.bucket_name = config['bucket_name']
    
    def upload_file(self, file, folder='uploads'):
        """
        上传文件到OBS
        
        Args:
            file: Django文件对象
            folder: 存储文件夹
        
        Returns:
            str: 文件访问URL
        """
        # 生成唯一文件名
        ext = os.path.splitext(file.name)[1]
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        filename = f"{folder}/{timestamp}_{file.name}"
        
        # 上传文件
        try:
            resp = self.obs_client.putObject(
                bucketName=self.bucket_name,
                objectKey=filename,
                content=file.read()
            )
            
            if resp.status < 300:
                # 返回访问URL
                server = settings.HUAWEI_OBS_CONFIG['server']
                url = f"https://{self.bucket_name}.{server}/{filename}"
                return url
            else:
                raise Exception(f"上传失败: {resp.errorMessage}")
        
        except Exception as e:
            raise Exception(f"OBS上传错误: {str(e)}")
    
    def delete_file(self, file_url):
        """
        删除OBS文件
        
        Args:
            file_url: 文件URL
        
        Returns:
            bool: 是否成功
        """
        # 从URL提取objectKey
        try:
            server = settings.HUAWEI_OBS_CONFIG['server']
            object_key = file_url.split(f"{self.bucket_name}.{server}/")[1]
            
            resp = self.obs_client.deleteObject(
                bucketName=self.bucket_name,
                objectKey=object_key
            )
            
            return resp.status < 300
        except Exception as e:
            raise Exception(f"OBS删除错误: {str(e)}")
    
    def close(self):
        """关闭连接"""
        self.obs_client.close()