"""
OSS文件上传模块
支持多种对象存储服务：阿里云OSS、腾讯云COS、AWS S3等
"""
import os
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def upload_file_to_oss(
    file_path: str,
    oss_key: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    上传文件到OSS
    
    参数:
        file_path: 本地文件路径
        oss_key: OSS中的对象键（可选，如果不提供则使用文件名）
        config: 配置字典（可选，如果为None则自动加载）
    
    返回:
        {
            "success": True/False,
            "file_path": "本地文件路径",
            "oss_url": "OSS访问URL",
            "oss_key": "OSS对象键",
            "message": "成功/错误消息",
            "error": "错误信息（如果失败）"
        }
    """
    try:
        # 加载配置
        if config is None:
            from shared.config import load_config
            config = load_config()
        
        oss_config = config.get("oss", {})
        if not oss_config:
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": "",
                "message": "OSS配置不存在，请在config.yaml中配置oss部分",
                "error": "配置缺失"
            }
        
        provider = oss_config.get("provider", "").lower()
        if not provider:
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": "",
                "message": "OSS提供商未配置，请在config.yaml中配置oss.provider",
                "error": "提供商未配置"
            }
        
        # 检查文件是否存在
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": "",
                "message": f"文件不存在: {file_path}",
                "error": "文件不存在"
            }
        
        # 确定OSS中的对象键
        if oss_key is None:
            # 如果没有指定oss_key，使用文件名
            oss_key = file_path_obj.name
        else:
            # 如果指定了oss_key，确保不以/开头（除非是根目录）
            oss_key = oss_key.lstrip('/')
        
        # 添加前缀（如果配置了）
        prefix = oss_config.get("key_prefix", "").strip()
        if prefix:
            prefix = prefix.rstrip('/') + '/'
            oss_key = prefix + oss_key
        
        # 根据提供商上传文件
        if provider == "aliyun" or provider == "alibaba":
            return _upload_to_aliyun_oss(file_path, oss_key, oss_config)
        elif provider == "tencent" or provider == "qcloud":
            return _upload_to_tencent_cos(file_path, oss_key, oss_config)
        elif provider == "aws" or provider == "s3":
            return _upload_to_aws_s3(file_path, oss_key, oss_config)
        elif provider == "minio":
            return _upload_to_minio(file_path, oss_key, oss_config)
        else:
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": oss_key,
                "message": f"不支持的OSS提供商: {provider}，支持: aliyun, tencent, aws, minio",
                "error": "不支持的提供商"
            }
    
    except Exception as e:
        logger.error(f"上传文件到OSS失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "file_path": file_path,
            "oss_url": "",
            "oss_key": "",
            "message": f"上传失败: {str(e)}",
            "error": str(e)
        }


def _upload_to_aliyun_oss(file_path: str, oss_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """上传到阿里云OSS"""
    try:
        import oss2
        
        access_key_id = config.get("access_key_id")
        access_key_secret = config.get("access_key_secret")
        endpoint = config.get("endpoint")
        bucket_name = config.get("bucket_name")
        
        if not all([access_key_id, access_key_secret, endpoint, bucket_name]):
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": oss_key,
                "message": "阿里云OSS配置不完整，需要: access_key_id, access_key_secret, endpoint, bucket_name",
                "error": "配置不完整"
            }
        
        # 创建认证对象
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        
        # 检查bucket是否存在（使用Service对象）
        try:
            import oss2
            service = oss2.Service(auth, endpoint)
            buckets = [b.name for b in oss2.BucketIterator(service)]
            if bucket_name not in buckets:
                return {
                    "success": False,
                    "file_path": file_path,
                    "oss_url": "",
                    "oss_key": oss_key,
                    "message": f"存储桶不存在: {bucket_name}，请检查bucket_name配置是否正确",
                    "error": "存储桶不存在"
                }
        except Exception as check_error:
            logger.warning(f"检查存储桶时出错（可能权限不足）: {str(check_error)}")
            # 继续尝试上传，可能是权限问题但bucket存在
        
        # 上传文件
        logger.info(f"正在上传文件到阿里云OSS: {file_path} -> {oss_key}")
        try:
            result = bucket.put_object_from_file(oss_key, file_path)
        except oss2.exceptions.AccessDenied as e:
            error_details = str(e)
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": oss_key,
                "message": "访问被拒绝。请检查：1) AccessKey是否有写入权限 2) 存储桶ACL设置 3) AccessKey配置是否正确",
                "error": f"AccessDenied: {error_details}"
            }
        except oss2.exceptions.NoSuchBucket:
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": oss_key,
                "message": f"存储桶不存在: {bucket_name}",
                "error": "存储桶不存在"
            }
        
        # 构建访问URL
        if config.get("use_cname", False) and config.get("custom_domain"):
            # 使用自定义域名
            base_url = config["custom_domain"].rstrip('/')
            oss_url = f"{base_url}/{oss_key}"
        else:
            # 使用默认域名
            base_url = f"https://{bucket_name}.{endpoint.replace('http://', '').replace('https://', '')}"
            oss_url = f"{base_url}/{oss_key}"
        
        return {
            "success": True,
            "file_path": file_path,
            "oss_url": oss_url,
            "oss_key": oss_key,
            "message": f"文件已成功上传到阿里云OSS: {oss_url}",
            "error": None
        }
    
    except ImportError:
        return {
            "success": False,
            "file_path": file_path,
            "oss_url": "",
            "oss_key": oss_key,
            "message": "oss2库未安装，请运行: pip install oss2",
            "error": "依赖缺失"
        }
    except Exception as e:
        logger.error(f"阿里云OSS上传失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "file_path": file_path,
            "oss_url": "",
            "oss_key": oss_key,
            "message": f"上传失败: {str(e)}",
            "error": str(e)
        }


def _upload_to_tencent_cos(file_path: str, cos_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """上传到腾讯云COS"""
    try:
        from qcloud_cos import CosConfig
        from qcloud_cos import CosS3Client
        
        secret_id = config.get("secret_id")
        secret_key = config.get("secret_key")
        region = config.get("region")
        bucket_name = config.get("bucket_name")
        
        if not all([secret_id, secret_key, region, bucket_name]):
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": cos_key,
                "message": "腾讯云COS配置不完整，需要: secret_id, secret_key, region, bucket_name",
                "error": "配置不完整"
            }
        
        # 创建配置和客户端
        cos_config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        client = CosS3Client(cos_config)
        
        # 上传文件
        logger.info(f"正在上传文件到腾讯云COS: {file_path} -> {cos_key}")
        with open(file_path, 'rb') as fp:
            response = client.put_object(
                Bucket=bucket_name,
                Body=fp,
                Key=cos_key
            )
        
        # 构建访问URL
        if config.get("use_cname", False) and config.get("custom_domain"):
            base_url = config["custom_domain"].rstrip('/')
            cos_url = f"{base_url}/{cos_key}"
        else:
            base_url = f"https://{bucket_name}.cos.{region}.myqcloud.com"
            cos_url = f"{base_url}/{cos_key}"
        
        return {
            "success": True,
            "file_path": file_path,
            "oss_url": cos_url,
            "oss_key": cos_key,
            "message": f"文件已成功上传到腾讯云COS: {cos_url}",
            "error": None
        }
    
    except ImportError:
        return {
            "success": False,
            "file_path": file_path,
            "oss_url": "",
            "oss_key": cos_key,
            "message": "cos-python-sdk-v5库未安装，请运行: pip install cos-python-sdk-v5",
            "error": "依赖缺失"
        }
    except Exception as e:
        logger.error(f"腾讯云COS上传失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "file_path": file_path,
            "oss_url": "",
            "oss_key": cos_key,
            "message": f"上传失败: {str(e)}",
            "error": str(e)
        }


def _upload_to_aws_s3(file_path: str, s3_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """上传到AWS S3"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        aws_access_key_id = config.get("aws_access_key_id")
        aws_secret_access_key = config.get("aws_secret_access_key")
        region_name = config.get("region", "us-east-1")
        bucket_name = config.get("bucket_name")
        
        if not all([aws_access_key_id, aws_secret_access_key, bucket_name]):
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": s3_key,
                "message": "AWS S3配置不完整，需要: aws_access_key_id, aws_secret_access_key, bucket_name",
                "error": "配置不完整"
            }
        
        # 创建S3客户端
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # 上传文件
        logger.info(f"正在上传文件到AWS S3: {file_path} -> {s3_key}")
        s3_client.upload_file(file_path, bucket_name, s3_key)
        
        # 构建访问URL
        if config.get("use_cname", False) and config.get("custom_domain"):
            base_url = config["custom_domain"].rstrip('/')
            s3_url = f"{base_url}/{s3_key}"
        else:
            base_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com"
            s3_url = f"{base_url}/{s3_key}"
        
        return {
            "success": True,
            "file_path": file_path,
            "oss_url": s3_url,
            "oss_key": s3_key,
            "message": f"文件已成功上传到AWS S3: {s3_url}",
            "error": None
        }
    
    except ImportError:
        return {
            "success": False,
            "file_path": file_path,
            "oss_url": "",
            "oss_key": s3_key,
            "message": "boto3库未安装，请运行: pip install boto3",
            "error": "依赖缺失"
        }
    except Exception as e:
        logger.error(f"AWS S3上传失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "file_path": file_path,
            "oss_url": "",
            "oss_key": s3_key,
            "message": f"上传失败: {str(e)}",
            "error": str(e)
        }


def _upload_to_minio(file_path: str, minio_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """上传到MinIO"""
    try:
        from minio import Minio
        from minio.error import S3Error
        
        endpoint = config.get("endpoint")
        access_key = config.get("access_key")
        secret_key = config.get("secret_key")
        bucket_name = config.get("bucket_name")
        secure = config.get("secure", True)
        
        if not all([endpoint, access_key, secret_key, bucket_name]):
            return {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": minio_key,
                "message": "MinIO配置不完整，需要: endpoint, access_key, secret_key, bucket_name",
                "error": "配置不完整"
            }
        
        # 创建MinIO客户端
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        # 确保bucket存在
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"已创建bucket: {bucket_name}")
        
        # 上传文件
        logger.info(f"正在上传文件到MinIO: {file_path} -> {minio_key}")
        client.fput_object(bucket_name, minio_key, file_path)
        
        # 构建访问URL
        protocol = "https" if secure else "http"
        if config.get("use_cname", False) and config.get("custom_domain"):
            base_url = config["custom_domain"].rstrip('/')
            minio_url = f"{base_url}/{minio_key}"
        else:
            base_url = f"{protocol}://{endpoint}/{bucket_name}"
            minio_url = f"{base_url}/{minio_key}"
        
        return {
            "success": True,
            "file_path": file_path,
            "oss_url": minio_url,
            "oss_key": minio_key,
            "message": f"文件已成功上传到MinIO: {minio_url}",
            "error": None
        }
    
    except ImportError:
        return {
            "success": False,
            "file_path": file_path,
            "oss_url": "",
            "oss_key": minio_key,
            "message": "minio库未安装，请运行: pip install minio",
            "error": "依赖缺失"
        }
    except Exception as e:
        logger.error(f"MinIO上传失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "file_path": file_path,
            "oss_url": "",
            "oss_key": minio_key,
            "message": f"上传失败: {str(e)}",
            "error": str(e)
        }

