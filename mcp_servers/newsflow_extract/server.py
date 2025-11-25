"""
NewsFlow Extract MCP Server
URL提取服务的MCP服务器入口
"""
import asyncio
import logging
import sys
import json
import concurrent.futures
from typing import Any, Dict, List

# 配置日志（输出到stderr，不影响stdio通信）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # MCP使用stdio通信，日志输出到stderr
)
logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, Resource
except ImportError:
    try:
        # 尝试另一种可能的包名
        from modelcontextprotocol.server import Server
        from modelcontextprotocol.server.stdio import stdio_server
        from modelcontextprotocol.types import Tool, TextContent, Resource
    except ImportError:
        logger.error("MCP SDK未安装，请运行: pip install mcp")
        logger.error("或尝试: pip install @modelcontextprotocol/server-python")
        sys.exit(1)

from .extractor import extract_links_from_url

# 导入writer模块（使用相对导入）
try:
    from ..newsflow_writer.writer import (
        normalize_recipients,
        save_markdown_file, 
        create_date_folder, 
        load_config,
        send_email_from_date_folder
    )
    WRITER_AVAILABLE = True
    logger.info("✅ writer模块导入成功，save_markdown_file、create_date_folder 和 send_email_from_date_folder 工具可用")
except ImportError as e:
    logger.error(f"❌ 无法导入writer模块: {e}")
    logger.error(f"   这将导致 save_markdown_file、create_date_folder 和 send_email_from_date_folder 工具不可用")
    logger.error(f"   请检查 writer.py 文件是否存在，以及所有依赖是否正确安装")
    WRITER_AVAILABLE = False
    normalize_recipients = None
    load_config = None
    send_email_from_date_folder = None
except Exception as e:
    logger.error(f"❌ 导入writer模块时发生错误: {e}", exc_info=True)
    WRITER_AVAILABLE = False
    normalize_recipients = None
    load_config = None
    send_email_from_date_folder = None

# 导入OSS上传模块
try:
    from ..newsflow_writer.oss_uploader import upload_file_to_oss
    OSS_AVAILABLE = True
    logger.info("✅ OSS上传模块导入成功，upload_file_to_oss 工具可用")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入OSS上传模块: {e}")
    logger.warning(f"   OSS上传功能将不可用")
    OSS_AVAILABLE = False
    upload_file_to_oss = None
except Exception as e:
    logger.warning(f"⚠️ 导入OSS上传模块时发生错误: {e}")
    OSS_AVAILABLE = False
    upload_file_to_oss = None

# 创建MCP服务器实例
app = Server("newsflow-extract")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    列出MCP服务提供的所有工具
    """
    logger.info("📋 正在列出可用工具...")
    tools = [
        Tool(
            name="extract_links_from_url",
            description="从指定URL提取所有链接。使用Selenium无头模式访问网站，等待页面完全渲染后提取所有a标签链接，并自动将相对路径转换为绝对路径。",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "网站URL，如 'https://example.com'"
                    }
                },
                "required": ["url"]
            }
        )
    ]
    logger.info(f"✅ 基础工具已添加: extract_links_from_url")
    
    # 如果writer模块可用，添加writer工具
    if WRITER_AVAILABLE:
        logger.info("📝 writer模块可用，正在添加 writer 工具...")
        writer_tools = [
            Tool(
                name="save_markdown_file",
                description="保存Markdown文件到日期文件夹。按照指定格式创建Markdown文件，包含文章原标题、AI总结和原文链接。支持缓存功能，会自动检查文章是否已分析过。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "文件名（文章标题，会进行安全处理）"
                        },
                        "original_title": {
                            "type": "string",
                            "description": "文章原标题（Markdown中的'原名'）"
                        },
                        "summary": {
                            "type": "string",
                            "description": "AI生成的一两百字总结（Markdown中的'ai总结内容'）"
                        },
                        "url": {
                            "type": "string",
                            "description": "文章原始URL（Markdown中的'原文链接'）"
                        },
                        "date": {
                            "type": "string",
                            "description": "日期（YYYY-MM-DD格式），可选，默认为今天"
                        },
                        "chinese_title": {
                            "type": "string",
                            "description": "中文标题（用于缓存），可选，如果不提供则使用title作为默认值"
                        },
                        "skip_if_exists": {
                            "type": "boolean",
                            "description": "如果文章已分析过是否跳过保存（默认false，会覆盖保存）"
                        },
                        "detailed_summary": {
                            "type": "string",
                            "description": "详细的文章概括（可选，500-800字），包含背景信息、核心要点、关键信息、影响分析和结论"
                        }
                    },
                    "required": ["title", "original_title", "summary", "url"]
                }
            ),
            Tool(
                name="create_date_folder",
                description="创建日期文件夹（YYYY-MM-DD格式）。如果文件夹已存在则不重复创建。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期（YYYY-MM-DD格式），可选，默认为今天"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="send_email_from_date_folder",
                description="读取指定日期文件夹中的所有Markdown文件，并发送邮件到指定邮箱（支持多个收件人）。将读取日期文件夹下的所有.md文件，解析文章信息（原名、AI总结、原文链接），生成格式化的HTML邮件并发送到所有指定的收件人。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期（YYYY-MM-DD格式），要读取的日期文件夹"
                        },
                        "recipient_email": {
                            "oneOf": [
                                {
                                    "type": "string",
                                    "description": "单个收件人邮箱地址"
                                },
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "多个收件人邮箱地址列表"
                                }
                            ],
                            "description": "收件人邮箱地址（可选，可以是字符串或字符串列表，如果不提供则从config.yaml中的email.recipient_emails或email.recipient_email读取）"
                        },
                        "subject": {
                            "type": "string",
                            "description": "邮件主题（可选），默认为'NewsFlow - {date} 新闻摘要'"
                        }
                    },
                    "required": ["date"]
                }
            )
        ]
        tools.extend(writer_tools)
        logger.info(f"✅ Writer工具已添加: save_markdown_file, create_date_folder, send_email_from_date_folder")
    else:
        logger.warning("⚠️  writer模块不可用，仅提供基础工具")
    
    # 如果OSS上传模块可用，添加OSS上传工具
    if OSS_AVAILABLE:
        logger.info("☁️ OSS上传模块可用，正在添加 OSS 上传工具...")
        oss_tools = [
            Tool(
                name="upload_file_to_oss",
                description="上传文件到OSS（对象存储服务）。支持阿里云OSS、腾讯云COS、AWS S3、MinIO等多种服务。配置信息从config.yaml的oss部分读取。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要上传的本地文件路径（绝对路径或相对路径）"
                        },
                        "oss_key": {
                            "type": "string",
                            "description": "OSS中的对象键（可选），如果不提供则使用文件名。可以包含路径，如 'folder/subfolder/file.txt'"
                        }
                    },
                    "required": ["file_path"]
                }
            )
        ]
        tools.extend(oss_tools)
        logger.info(f"✅ OSS上传工具已添加: upload_file_to_oss")
    
    logger.info(f"📊 总共 {len(tools)} 个工具可用")
    
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    处理工具调用
    """
    if name == "extract_links_from_url":
        url = arguments.get("url")
        
        if not url:
            error_result = {
                "error": "缺少必需参数: url",
                "links": [],
                "count": 0
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        try:
            logger.info(f"调用工具 extract_links_from_url，URL: {url}")
            
            # 调用提取函数（extractor是同步函数，需要在executor中运行）
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, extract_links_from_url, url)
            
            # 将结果转换为JSON字符串
            result_json = json.dumps(result, ensure_ascii=False)
            
            logger.info(f"提取完成，共 {result.get('count', 0)} 个链接")
            
            return [TextContent(
                type="text",
                text=result_json
            )]
            
        except Exception as e:
            logger.error(f"处理工具调用失败: {str(e)}", exc_info=True)
            error_result = {
                "error": str(e),
                "links": [],
                "count": 0
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
    
    elif name == "save_markdown_file":
        if not WRITER_AVAILABLE:
            error_result = {
                "path": "",
                "filename": "",
                "date_folder": "",
                "success": False,
                "error": "writer模块不可用"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        title = arguments.get("title")
        original_title = arguments.get("original_title")
        summary = arguments.get("summary")
        url = arguments.get("url")
        date = arguments.get("date")
        chinese_title = arguments.get("chinese_title")
        skip_if_exists = arguments.get("skip_if_exists", False)
        detailed_summary = arguments.get("detailed_summary")
        
        # 参数校验
        if not title or not original_title or not summary or not url:
            error_result = {
                "path": "",
                "filename": "",
                "date_folder": "",
                "success": False,
                "error": "缺少必需参数: title, original_title, summary, url"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        try:
            logger.info(f"调用工具 save_markdown_file，标题: {title}")
            if detailed_summary:
                logger.info(f"包含详细概括（{len(detailed_summary)} 字符）")
            
            # 调用写入函数（同步函数，需要在executor中运行）
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                save_markdown_file,
                title,
                original_title,
                summary,
                url,
                date,
                None,  # config参数，使用None让函数自动加载
                chinese_title,
                skip_if_exists,
                detailed_summary  # 传递详细概括参数
            )
            
            # 将结果转换为JSON字符串
            result_json = json.dumps(result, ensure_ascii=False)
            
            if result.get("success"):
                logger.info(f"保存文件成功: {result.get('path')}")
            else:
                logger.error(f"保存文件失败: {result.get('error')}")
            
            return [TextContent(
                type="text",
                text=result_json
            )]
            
        except Exception as e:
            logger.error(f"处理工具调用失败: {str(e)}", exc_info=True)
            error_result = {
                "path": "",
                "filename": "",
                "date_folder": "",
                "success": False,
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
    
    elif name == "create_date_folder":
        if not WRITER_AVAILABLE:
            error_result = {
                "path": "",
                "success": False,
                "error": "writer模块不可用"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        date = arguments.get("date")
        
        try:
            logger.info(f"调用工具 create_date_folder，日期: {date or '今天'}")
            
            # 调用创建文件夹函数（同步函数，需要在executor中运行）
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, create_date_folder, date)
            
            # 将结果转换为JSON字符串
            result_json = json.dumps(result, ensure_ascii=False)
            
            if result.get("success"):
                logger.info(f"创建文件夹成功: {result.get('path')}")
            else:
                logger.error(f"创建文件夹失败: {result.get('error')}")
            
            return [TextContent(
                type="text",
                text=result_json
            )]
            
        except Exception as e:
            logger.error(f"处理工具调用失败: {str(e)}", exc_info=True)
            error_result = {
                "path": "",
                "success": False,
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
    
    elif name == "send_email_from_date_folder":
        if not WRITER_AVAILABLE:
            error_result = {
                "success": False,
                "date": "",
                "email": "",
                "files_count": 0,
                "message": "writer模块不可用",
                "error": "writer模块不可用"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        date = arguments.get("date")
        recipient_email = arguments.get("recipient_email")
        subject = arguments.get("subject")
        
        if not date:
            error_result = {
                "success": False,
                "date": "",
                "email": recipient_email or "",
                "files_count": 0,
                "message": "缺少必需参数: date",
                "error": "缺少必需参数"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        try:
            # 格式化收件人信息用于日志
            recipient_info = "从配置读取"
            if recipient_email:
                if isinstance(recipient_email, list):
                    recipient_info = f"{len(recipient_email)}个收件人: {', '.join(recipient_email)}"
                else:
                    recipient_info = str(recipient_email)
            logger.info(f"调用工具 send_email_from_date_folder，日期: {date}, 收件人: {recipient_info}")
            
            # 调用邮件发送函数（同步函数，需要在executor中运行）
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                send_email_from_date_folder,
                date,
                recipient_email,
                subject,
                None  # config参数，使用None让函数自动加载
            )
            
            # 将结果转换为JSON字符串
            result_json = json.dumps(result, ensure_ascii=False)
            
            if result.get("success"):
                recipients_list = result.get("recipients", [])
                files_count = result.get("files_count", 0)
                if recipients_list:
                    recipients_str = ", ".join(recipients_list)
                    logger.info(f"邮件发送成功: {len(recipients_list)}个收件人 ({recipients_str}), 共 {files_count} 篇文章")
                else:
                    logger.info(f"邮件发送完成，共 {files_count} 篇文章")
                # 检查是否有失败的收件人
                failed_list = result.get("failed", [])
                if failed_list:
                    logger.warning(f"部分邮件发送失败: {len(failed_list)}个收件人")
            else:
                logger.error(f"邮件发送失败: {result.get('error') or result.get('message', '未知错误')}")
            
            return [TextContent(
                type="text",
                text=result_json
            )]
            
        except Exception as e:
            logger.error(f"处理工具调用失败: {str(e)}", exc_info=True)
            # 尝试规范化收件人列表（如果normalize_recipients可用）
            emails_list = []
            if recipient_email:
                if normalize_recipients:
                    emails_list = normalize_recipients(recipient_email)
                elif isinstance(recipient_email, list):
                    emails_list = recipient_email
                else:
                    emails_list = [recipient_email]
            error_result = {
                "success": False,
                "date": date,
                "emails": emails_list,
                "files_count": 0,
                "message": f"发送邮件失败: {str(e)}",
                "recipients": [],
                "failed": [],
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
    
    elif name == "upload_file_to_oss":
        if not OSS_AVAILABLE:
            error_result = {
                "success": False,
                "file_path": "",
                "oss_url": "",
                "oss_key": "",
                "message": "OSS上传模块不可用",
                "error": "OSS模块不可用"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        file_path = arguments.get("file_path")
        oss_key = arguments.get("oss_key")
        
        if not file_path:
            error_result = {
                "success": False,
                "file_path": "",
                "oss_url": "",
                "oss_key": "",
                "message": "缺少必需参数: file_path",
                "error": "缺少必需参数"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        try:
            logger.info(f"调用工具 upload_file_to_oss，文件路径: {file_path}, OSS键: {oss_key or '使用文件名'}")
            
            # 调用OSS上传函数（同步函数，需要在executor中运行）
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                upload_file_to_oss,
                file_path,
                oss_key,
                None  # config参数，使用None让函数自动加载
            )
            
            # 将结果转换为JSON字符串
            result_json = json.dumps(result, ensure_ascii=False)
            
            if result.get("success"):
                logger.info(f"文件上传成功: {result.get('oss_url')}")
            else:
                logger.error(f"文件上传失败: {result.get('error') or result.get('message', '未知错误')}")
            
            return [TextContent(
                type="text",
                text=result_json
            )]
            
        except Exception as e:
            logger.error(f"处理OSS上传失败: {str(e)}", exc_info=True)
            error_result = {
                "success": False,
                "file_path": file_path,
                "oss_url": "",
                "oss_key": oss_key or "",
                "message": f"上传失败: {str(e)}",
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
    
    else:
        error_result = {
            "error": f"未知工具: {name}"
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_result, ensure_ascii=False)
        )]


@app.list_resources()
async def list_resources() -> List[Resource]:
    """
    列出MCP服务提供的所有资源
    """
    resources = []
    
    # 添加配置文件资源
    if load_config:
        resources.append(
            Resource(
                uri="config://config.yaml",
                name="配置文件",
                description="NewsFlow配置文件，包含网站列表和输出配置",
                mimeType="application/yaml"
            )
        )
    
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """
    读取资源内容
    """
    if uri == "config://config.yaml":
        if not load_config:
            raise ValueError("writer模块不可用，无法读取配置")
        
        try:
            config = load_config()
            # 将配置转换为YAML字符串返回
            import yaml
            return yaml.dump(config, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            logger.error(f"读取配置文件失败: {str(e)}", exc_info=True)
            raise ValueError(f"读取配置文件失败: {str(e)}")
    else:
        raise ValueError(f"未知资源: {uri}")


async def main():
    """
    主函数：启动MCP服务器
    """
    logger.info("=" * 60)
    logger.info("🚀 启动 NewsFlow Extract MCP Server...")
    logger.info(f"📦 WRITER_AVAILABLE = {WRITER_AVAILABLE}")
    logger.info(f"☁️ OSS_AVAILABLE = {OSS_AVAILABLE}")
    
    # 列出可用工具
    try:
        tools = await list_tools()
        logger.info(f"📋 服务提供 {len(tools)} 个工具:")
        for tool in tools:
            logger.info(f"   - {tool.name}")
    except Exception as e:
        logger.error(f"❌ 列出工具时出错: {e}", exc_info=True)
    
    logger.info("=" * 60)
    
    # 使用stdio_server运行服务器
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器停止")
    except Exception as e:
        logger.error(f"服务器运行错误: {str(e)}", exc_info=True)
        sys.exit(1)
