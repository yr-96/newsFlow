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
from .fetcher import fetch_html_from_url

# 导入HTML RAG模块
try:
    from .html_rag.retriever import retrieve_relevant_chunks
    HTML_RAG_AVAILABLE = True
    logger.info("✅ HTML RAG模块导入成功，retrieve_relevant_html_chunks 工具可用")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入HTML RAG模块: {e}")
    logger.warning(f"   HTML RAG检索功能将不可用")
    HTML_RAG_AVAILABLE = False
    retrieve_relevant_chunks = None
except Exception as e:
    logger.warning(f"⚠️ 导入HTML RAG模块时发生错误: {e}")
    HTML_RAG_AVAILABLE = False
    retrieve_relevant_chunks = None

# 导入writer模块（使用相对导入）
try:
    from ..newsflow_writer.writer import (
        normalize_recipients,
        save_markdown_file, 
        create_date_folder, 
        append_valuable_links_to_json,
        read_valuable_links_json,
        update_link_summary_in_json,
        update_link_error_in_json,
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
        ),
        Tool(
            name="fetch_html_from_url",
            description="从指定URL获取页面完整HTML内容。使用requests获取，适用于文章、博客、技术文档等静态或服务端渲染页面。返回HTML源码和页面标题，可用于内容提取和摘要生成。",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "页面URL，如文章链接、GitHub仓库等"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "请求超时秒数（可选，默认30）"
                    }
                },
                "required": ["url"]
            }
        )
    ]
    logger.info(f"✅ 基础工具已添加: extract_links_from_url, fetch_html_from_url")
    
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
                description="创建日期文件夹（YYYY-MM-DD格式），并在其中初始化 valuable_links.json 文件。如果文件夹已存在则不重复创建。",
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
                name="append_valuable_links_to_json",
                description="将指定网站识别出的有价值链接追加到日期文件夹中的 valuable_links.json 文件。每收集完一个网站后调用，传入网站名称和链接列表。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期（YYYY-MM-DD格式），如 2026-03-03"
                        },
                        "site_name": {
                            "type": "string",
                            "description": "来源网站名称，如 'Hacker News'、'TLDR'、'GitHub Trending'"
                        },
                        "links": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "url": {"type": "string", "description": "链接URL"},
                                    "text": {"type": "string", "description": "链接文本"}
                                },
                                "required": ["url"]
                            },
                            "description": "该网站识别出的有价值链接数组"
                        }
                    },
                    "required": ["date", "site_name", "links"]
                }
            ),
            Tool(
                name="read_valuable_links_json",
                description="从日期文件夹中读取 valuable_links.json，返回链接列表。用于第四步逐个处理链接时获取待处理链接。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期（YYYY-MM-DD格式），如 2026-03-04"
                        }
                    },
                    "required": ["date"]
                }
            ),
            Tool(
                name="update_link_summary_in_json",
                description="将链接的AI总结数据写入 valuable_links.json 中对应链接对象下。替代 save_markdown_file，将 title、summary、detailed_summary 等保存到 JSON。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期（YYYY-MM-DD格式）"
                        },
                        "url": {
                            "type": "string",
                            "description": "链接URL，用于匹配要更新的链接"
                        },
                        "title": {
                            "type": "string",
                            "description": "内容标题（格式：中文标题（英文原标题/项目名））"
                        },
                        "original_title": {
                            "type": "string",
                            "description": "内容原标题（格式：中文标题（英文原标题/项目名））"
                        },
                        "summary": {
                            "type": "string",
                            "description": "AI生成的200字简短摘要"
                        },
                        "detailed_summary": {
                            "type": "string",
                            "description": "AI生成的500-800字详细概括"
                        },
                        "skip_if_exists": {
                            "type": "boolean",
                            "description": "如果该链接已有 summary 则跳过（默认true）"
                        }
                    },
                    "required": ["date", "url", "title", "original_title", "summary", "detailed_summary"]
                }
            ),
            Tool(
                name="update_link_error_in_json",
                description="将链接处理失败时的错误信息写入 valuable_links.json 中对应链接对象下。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期（YYYY-MM-DD格式）"
                        },
                        "url": {
                            "type": "string",
                            "description": "链接URL"
                        },
                        "error_message": {
                            "type": "string",
                            "description": "错误描述"
                        }
                    },
                    "required": ["date", "url", "error_message"]
                }
            ),
            Tool(
                name="send_email_from_date_folder",
                description="读取指定日期文件夹中的 valuable_links.json，提取有 summary 的链接，生成 HTML 邮件并发送到指定邮箱（支持多个收件人）。将解析每篇内容的原名、AI总结、详细概括、原文链接，生成格式化的 HTML 邮件并发送到所有指定的收件人。",
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
        logger.info(f"✅ Writer工具已添加: save_markdown_file, create_date_folder, append_valuable_links_to_json, read_valuable_links_json, update_link_summary_in_json, update_link_error_in_json, send_email_from_date_folder")
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
    
    # 如果HTML RAG模块可用，添加HTML RAG检索工具
    if HTML_RAG_AVAILABLE:
        logger.info("🔍 HTML RAG模块可用，正在添加 HTML RAG 检索工具...")
        html_rag_tools = [
            Tool(
                name="retrieve_relevant_html_chunks",
                description="从HTML文本中检索与查询问题最相关的文本块。使用RAG架构，将HTML分块并向量化，通过相似度检索返回最相关的内容。支持多语言HTML和查询（50+语言）。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "html_text": {
                            "type": "string",
                            "description": "HTML结构的文本内容（支持多语言）"
                        },
                        "query": {
                            "type": "string",
                            "description": "查询问题，用于检索相关文本块（支持多语言，如中文、英文、日文等）"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回最相关的K个文本块（可选，默认从config.yaml读取，最终默认3）"
                        },
                        "min_similarity": {
                            "type": "number",
                            "description": "最小相似度阈值（0-1，可选，默认从config.yaml读取，最终默认0.3）"
                        }
                    },
                    "required": ["html_text", "query"]
                }
            )
        ]
        tools.extend(html_rag_tools)
        logger.info(f"✅ HTML RAG检索工具已添加: retrieve_relevant_html_chunks")
    
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

    elif name == "fetch_html_from_url":
        url = arguments.get("url")
        timeout = arguments.get("timeout", 30)

        if not url:
            error_result = {
                "success": False,
                "html": "",
                "title": "",
                "url": "",
                "error": "缺少必需参数: url",
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]

        try:
            logger.info(f"调用工具 fetch_html_from_url，URL: {url}")

            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor, fetch_html_from_url, url, timeout
            )

            result_json = json.dumps(result, ensure_ascii=False)

            if result.get("success"):
                logger.info(f"获取HTML成功，长度 {len(result.get('html', ''))} 字符")
            else:
                logger.warning(f"获取HTML失败: {result.get('error')}")

            return [TextContent(type="text", text=result_json)]

        except Exception as e:
            logger.error(f"处理工具调用失败: {str(e)}", exc_info=True)
            error_result = {
                "success": False,
                "html": "",
                "title": "",
                "url": url,
                "error": str(e),
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
    
    elif name == "append_valuable_links_to_json":
        if not WRITER_AVAILABLE:
            error_result = {
                "success": False,
                "date_folder": "",
                "site_name": "",
                "links_count": 0,
                "error": "writer模块不可用"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        date = arguments.get("date")
        site_name = arguments.get("site_name")
        links = arguments.get("links", [])
        
        if not date or not site_name:
            error_result = {
                "success": False,
                "date_folder": "",
                "site_name": site_name or "",
                "links_count": 0,
                "error": "缺少必需参数: date 和 site_name"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        try:
            logger.info(f"调用工具 append_valuable_links_to_json，日期: {date}, 网站: {site_name}, 链接数: {len(links)}")
            
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                append_valuable_links_to_json,
                date,
                site_name,
                links
            )
            
            result_json = json.dumps(result, ensure_ascii=False)
            
            if result.get("success"):
                logger.info(f"追加有价值链接成功: {site_name}, {result.get('links_count')} 条")
            else:
                logger.error(f"追加有价值链接失败: {result.get('error')}")
            
            return [TextContent(
                type="text",
                text=result_json
            )]
            
        except Exception as e:
            logger.error(f"处理工具调用失败: {str(e)}", exc_info=True)
            error_result = {
                "success": False,
                "date_folder": "",
                "site_name": site_name or "",
                "links_count": 0,
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
    
    elif name == "read_valuable_links_json":
        if not WRITER_AVAILABLE:
            error_result = {
                "success": False,
                "links": [],
                "date_folder": "",
                "error": "writer模块不可用"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        date = arguments.get("date")
        if not date:
            error_result = {
                "success": False,
                "links": [],
                "date_folder": "",
                "error": "缺少必需参数: date"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        try:
            logger.info(f"调用工具 read_valuable_links_json，日期: {date}")
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, read_valuable_links_json, date)
            result_json = json.dumps(result, ensure_ascii=False)
            return [TextContent(type="text", text=result_json)]
        except Exception as e:
            logger.error(f"处理工具调用失败: {str(e)}", exc_info=True)
            error_result = {
                "success": False,
                "links": [],
                "date_folder": "",
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
    
    elif name == "update_link_summary_in_json":
        if not WRITER_AVAILABLE:
            error_result = {
                "success": False,
                "updated": False,
                "date_folder": "",
                "url": "",
                "error": "writer模块不可用"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        date = arguments.get("date")
        url = arguments.get("url")
        title = arguments.get("title")
        original_title = arguments.get("original_title")
        summary = arguments.get("summary")
        detailed_summary = arguments.get("detailed_summary")
        skip_if_exists = arguments.get("skip_if_exists", True)
        
        if not all([date, url, title, original_title, summary, detailed_summary]):
            error_result = {
                "success": False,
                "updated": False,
                "date_folder": "",
                "url": url or "",
                "error": "缺少必需参数: date, url, title, original_title, summary, detailed_summary"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        try:
            logger.info(f"调用工具 update_link_summary_in_json，URL: {url[:50]}...")
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                update_link_summary_in_json,
                date,
                url,
                title,
                original_title,
                summary,
                detailed_summary,
                skip_if_exists,
            )
            result_json = json.dumps(result, ensure_ascii=False)
            return [TextContent(type="text", text=result_json)]
        except Exception as e:
            logger.error(f"处理工具调用失败: {str(e)}", exc_info=True)
            error_result = {
                "success": False,
                "updated": False,
                "date_folder": "",
                "url": url or "",
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
    
    elif name == "update_link_error_in_json":
        if not WRITER_AVAILABLE:
            error_result = {
                "success": False,
                "updated": False,
                "date_folder": "",
                "url": "",
                "error": "writer模块不可用"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        date = arguments.get("date")
        url = arguments.get("url")
        error_message = arguments.get("error_message", "")
        
        if not date or not url:
            error_result = {
                "success": False,
                "updated": False,
                "date_folder": "",
                "url": url or "",
                "error": "缺少必需参数: date, url, error_message"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        try:
            logger.info(f"调用工具 update_link_error_in_json，URL: {url[:50]}...")
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                update_link_error_in_json,
                date,
                url,
                error_message,
            )
            result_json = json.dumps(result, ensure_ascii=False)
            return [TextContent(type="text", text=result_json)]
        except Exception as e:
            logger.error(f"处理工具调用失败: {str(e)}", exc_info=True)
            error_result = {
                "success": False,
                "updated": False,
                "date_folder": "",
                "url": url or "",
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
                "items_count": 0,
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
                "items_count": 0,
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
                items_count = result.get("items_count", 0)
                if recipients_list:
                    recipients_str = ", ".join(recipients_list)
                    logger.info(f"邮件发送成功: {len(recipients_list)}个收件人 ({recipients_str}), 共 {items_count} 篇内容")
                else:
                    logger.info(f"邮件发送完成，共 {items_count} 篇内容")
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
                "items_count": 0,
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
    
    elif name == "retrieve_relevant_html_chunks":
        if not HTML_RAG_AVAILABLE:
            error_result = {
                "success": False,
                "query": arguments.get("query", ""),
                "results": [],
                "total_chunks": 0,
                "retrieval_time": 0.0,
                "error": "HTML RAG模块不可用",
                "error_type": "MODULE_UNAVAILABLE"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        html_text = arguments.get("html_text")
        query = arguments.get("query")
        top_k = arguments.get("top_k")
        min_similarity = arguments.get("min_similarity")
        
        # 参数校验
        if not html_text or not query:
            error_result = {
                "success": False,
                "query": query or "",
                "results": [],
                "total_chunks": 0,
                "retrieval_time": 0.0,
                "error": "缺少必需参数: html_text, query",
                "error_type": "INVALID_PARAMETERS"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )]
        
        try:
            # 加载配置
            config = None
            if load_config:
                try:
                    full_config = load_config()
                    config = full_config.get('html_rag', {})
                except Exception as e:
                    logger.warning(f"加载配置失败，使用默认配置: {e}")
                    config = {}
            else:
                config = {}
            
            # 调用检索函数（同步函数，需要在executor中运行）
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                retrieve_relevant_chunks,
                html_text,
                query,
                top_k,
                min_similarity,
                config
            )
            
            # 将结果转换为JSON字符串
            result_json = json.dumps(result, ensure_ascii=False)
            
            if result.get("success"):
                logger.info(f"检索完成，找到 {len(result.get('results', []))} 个相关chunks")
            else:
                logger.error(f"检索失败: {result.get('error')}")
            
            return [TextContent(
                type="text",
                text=result_json
            )]
            
        except Exception as e:
            logger.error(f"处理HTML RAG检索失败: {str(e)}", exc_info=True)
            error_result = {
                "success": False,
                "query": query,
                "results": [],
                "total_chunks": 0,
                "retrieval_time": 0.0,
                "error": f"检索过程出错: {str(e)}",
                "error_type": "RETRIEVAL_FAILED"
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
