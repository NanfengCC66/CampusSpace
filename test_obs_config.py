"""
华为云 OBS 配置测试脚本
"""
import os
import sys

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings

def test_obs_config():
    """测试华为云OBS配置"""
    
    print("=" * 60)
    print("华为云 OBS 配置测试")
    print("=" * 60)
    print()
    
    # 检查环境变量
    print("【1】检查环境变量...")
    access_key = os.environ.get('HUAWEI_ACCESS_KEY')
    secret_key = os.environ.get('HUAWEI_SECRET_KEY')
    
    if access_key:
        print(f"  ✅ HUAWEI_ACCESS_KEY: {access_key[:10]}***")
    else:
        print("  ❌ HUAWEI_ACCESS_KEY 未设置")
        print("     请运行: set HUAWEI_ACCESS_KEY=你的AK")
    
    if secret_key:
        print(f"  ✅ HUAWEI_SECRET_KEY: {secret_key[:10]}***")
    else:
        print("  ❌ HUAWEI_SECRET_KEY 未设置")
        print("     请运行: set HUAWEI_SECRET_KEY=你的SK")
    
    print()
    
    # 检查配置
    print("【2】检查Django配置...")
    try:
        config = settings.HUAWEI_OBS_CONFIG
        print(f"  ✅ OBS Server: {config.get('server')}")
        print(f"  ✅ Bucket Name: {config.get('bucket_name')}")
    except AttributeError:
        print("  ❌ HUAWEI_OBS_CONFIG 未配置")
        print("     请在 settings.py 中添加配置")
    
    print()
    
    # 测试连接
    if access_key and secret_key:
        print("【3】测试OBS连接...")
        try:
            from obs import ObsClient
            
            obs_client = ObsClient(
                access_key_id=access_key,
                secret_access_key=secret_key,
                server=config.get('server')
            )
            
            # 列出桶
            resp = obs_client.listBuckets()
            
            if resp.status < 300:
                print(f"  ✅ 连接成功")
                print(f"  ✅ 找到 {len(resp.body.buckets)} 个桶")
                
                for bucket in resp.body.buckets:
                    marker = "→ " if bucket.name == config.get('bucket_name') else "  "
                    print(f"     {marker}{bucket.name}")
            else:
                print(f"  ❌ 连接失败: {resp.errorMessage}")
            
            obs_client.close()
            
        except ImportError:
            print("  ❌ esdk-obs-python 未安装")
            print("     请运行: pip install esdk-obs-python")
        except Exception as e:
            print(f"  ❌ 连接错误: {str(e)}")
    else:
        print("【3】跳过连接测试（环境变量未设置）")
    
    print()
    print("=" * 60)
    
    # 总结
    if access_key and secret_key:
        print("✅ 配置完成！可以开始使用华为云OBS")
    else:
        print("⚠️  请先设置环境变量：")
        print()
        print("    Windows (CMD):")
        print("      set HUAWEI_ACCESS_KEY=你的AK")
        print("      set HUAWEI_SECRET_KEY=你的SK")
        print()
        print("    Windows (PowerShell):")
        print("      $env:HUAWEI_ACCESS_KEY=\"你的AK\"")
        print("      $env:HUAWEI_SECRET_KEY=\"你的SK\"")
        print()
        print("    Linux/Mac:")
        print("      export HUAWEI_ACCESS_KEY=\"你的AK\"")
        print("      export HUAWEI_SECRET_KEY=\"你的SK\"")
    
    print("=" * 60)

if __name__ == '__main__':
    test_obs_config()