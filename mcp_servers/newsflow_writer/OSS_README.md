# OSS文件上传功能

## 功能说明

该模块提供将文件上传到各种对象存储服务（OSS）的功能，支持：

- **阿里云OSS**
- **腾讯云COS**
- **AWS S3**
- **MinIO**

## 配置说明

在 `config.yaml` 中添加 `oss` 配置部分：

```yaml
oss:
  provider: "aliyun"  # OSS提供商: aliyun/alibaba, tencent/qcloud, aws/s3, minio
  bucket_name: "your-bucket-name"  # 存储桶名称
  key_prefix: "newsflow/"  # 对象键前缀（可选）
  use_cname: false  # 是否使用自定义域名
  custom_domain: ""  # 自定义域名（可选）
  
  # 根据provider选择以下配置之一：
  
  # 阿里云OSS
  access_key_id: "your_access_key_id"
  access_key_secret: "your_access_key_secret"
  endpoint: "oss-cn-hangzhou.aliyuncs.com"
  
  # 或腾讯云COS
  # secret_id: "your_secret_id"
  # secret_key: "your_secret_key"
  # region: "ap-beijing"
  
  # 或AWS S3
  # aws_access_key_id: "your_aws_access_key_id"
  # aws_secret_access_key: "your_aws_secret_access_key"
  # region: "us-east-1"
  
  # 或MinIO
  # endpoint: "localhost:9000"
  # access_key: "your_minio_access_key"
  # secret_key: "your_minio_secret_key"
  # secure: true
```

## 依赖安装

根据使用的OSS提供商，安装对应的SDK：

### 阿里云OSS
```bash
pip install oss2
```

### 腾讯云COS
```bash
pip install cos-python-sdk-v5
```

### AWS S3
```bash
pip install boto3
```

### MinIO
```bash
pip install minio
```

## 使用方法

### 通过MCP工具调用

```python
# 上传文件到OSS
upload_file_to_oss(
    file_path="/path/to/local/file.html",
    oss_key="2025-11-02/newsflow.html"  # 可选，如果不提供则使用文件名
)
```

### 配置示例

#### 阿里云OSS示例

```yaml
oss:
  provider: "aliyun"
  bucket_name: "my-newsflow-bucket"
  key_prefix: "newsflow/"
  access_key_id: "LTAI5t..."
  access_key_secret: "your_secret_key"
  endpoint: "oss-cn-hangzhou.aliyuncs.com"
```

#### 腾讯云COS示例

```yaml
oss:
  provider: "tencent"
  bucket_name: "my-newsflow-bucket"
  key_prefix: "newsflow/"
  secret_id: "your_secret_id"
  secret_key: "your_secret_key"
  region: "ap-beijing"
```

#### AWS S3示例

```yaml
oss:
  provider: "aws"
  bucket_name: "my-newsflow-bucket"
  key_prefix: "newsflow/"
  aws_access_key_id: "your_access_key"
  aws_secret_access_key: "your_secret_key"
  region: "us-east-1"
```

#### MinIO示例

```yaml
oss:
  provider: "minio"
  bucket_name: "my-newsflow-bucket"
  key_prefix: "newsflow/"
  endpoint: "localhost:9000"
  access_key: "minioadmin"
  secret_key: "minioadmin"
  secure: false  # 本地开发可以使用false
```

## 返回结果

上传成功后返回：

```json
{
  "success": true,
  "file_path": "/path/to/local/file.html",
  "oss_url": "https://bucket.oss-cn-hangzhou.aliyuncs.com/newsflow/2025-11-02/newsflow.html",
  "oss_key": "newsflow/2025-11-02/newsflow.html",
  "message": "文件已成功上传到阿里云OSS: https://...",
  "error": null
}
```

上传失败返回：

```json
{
  "success": false,
  "file_path": "/path/to/local/file.html",
  "oss_url": "",
  "oss_key": "",
  "message": "错误信息",
  "error": "错误详情"
}
```

## 使用场景

1. **上传生成的HTML文件**：将生成的新闻摘要HTML文件上传到OSS，方便分享
2. **备份Markdown文件**：定期备份生成的Markdown文件到OSS
3. **CDN分发**：通过OSS的CDN功能，让邮件中的链接指向OSS上的文件

