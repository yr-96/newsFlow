"""
邮件发送模块
提供邮件发送相关功能
"""
import logging
import smtplib
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

logger = logging.getLogger(__name__)


def normalize_recipients(recipients: Any) -> List[str]:
    """
    规范化收件人列表，支持字符串、列表或None
    
    参数:
        recipients: 收件人，可以是字符串、列表或None
    
    返回:
        收件人邮箱地址列表
    """
    if recipients is None:
        return []
    
    if isinstance(recipients, str):
        return [recipients]
    
    if isinstance(recipients, list):
        # 过滤掉None和空字符串
        return [email for email in recipients if email and isinstance(email, str)]
    
    return []


def send_email(
    recipients: Any,
    subject: str,
    html_content: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    通过SMTP发送邮件到多个收件人
    
    参数:
        recipients: 收件人邮箱地址（可以是字符串、列表或None）
        subject: 邮件主题
        html_content: HTML格式的邮件正文
        config: 邮件配置字典
    
    返回:
        {
            "success": True/False,
            "message": "成功/错误消息",
            "recipients": "成功发送的收件人列表",
            "failed": "发送失败的收件人列表（如果有）"
        }
    """
    try:
        # 规范化收件人列表
        recipient_list = normalize_recipients(recipients)
        
        if not recipient_list:
            return {
                "success": False,
                "message": "没有有效的收件人邮箱地址",
                "recipients": [],
                "failed": []
            }
        
        email_config = config.get("email", {})
        
        smtp_server = email_config.get("smtp_server")
        smtp_port = email_config.get("smtp_port", 587)
        sender_email = email_config.get("sender_email")
        sender_name = email_config.get("sender_name", "NewsFlow")  # 发件人显示名称，默认为NewsFlow
        sender_password = email_config.get("sender_password")
        use_tls = email_config.get("use_tls", True)
        
        if not all([smtp_server, sender_email, sender_password]):
            return {
                "success": False,
                "message": "邮件配置不完整，请检查config.yaml中的email配置",
                "recipients": [],
                "failed": recipient_list
            }
        
        # 为每个收件人创建独立的SMTP连接（方案1：提高稳定性）
        successful_recipients = []
        failed_recipients = []
        
        for recipient in recipient_list:
            server = None
            try:
                # 为每个收件人创建独立的SMTP连接
                logger.debug(f"为 {recipient} 创建新的SMTP连接")
                
                if use_tls:
                    # 使用TLS/STARTTLS
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                else:
                    # 使用SSL
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                
                server.login(sender_email, sender_password)
                
                # 为每个收件人创建单独的邮件消息（这样每个收件人看不到其他收件人）
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                # 使用 formataddr 正确处理中文名称的编码，避免乱码
                msg['From'] = formataddr((sender_name, sender_email))
                msg['To'] = recipient
                
                # 添加HTML内容
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
                
                # 发送邮件
                refused = server.send_message(msg)
                # send_message 返回一个字典，包含被拒绝的收件人
                # 如果字典中有该收件人，说明发送失败
                if refused:
                    logger.debug(f"send_message 返回的 refused 字典: {refused}")
                    # 检查该收件人是否在拒绝列表中
                    if recipient in refused:
                        error_info = refused[recipient]
                        # error_info 是一个元组 (code, msg, email)
                        if isinstance(error_info, tuple) and len(error_info) >= 2:
                            error_code = error_info[0]
                            error_msg = error_info[1]
                            if isinstance(error_msg, bytes):
                                error_msg = error_msg.decode('utf-8', errors='ignore')
                            else:
                                error_msg = str(error_msg)
                            failed_recipients.append({
                                "email": recipient,
                                "error": f"SMTP拒绝: {error_msg} (代码: {error_code})"
                            })
                            logger.error(f"向 {recipient} 发送邮件失败: SMTP拒绝 - {error_msg} (代码: {error_code})")
                        else:
                            # 如果格式不符合预期，记录原始信息
                            failed_recipients.append({
                                "email": recipient,
                                "error": f"SMTP返回异常格式: {error_info}"
                            })
                            logger.error(f"向 {recipient} 发送邮件失败: {error_info}")
                    else:
                        # 该收件人不在拒绝列表中，发送成功
                        successful_recipients.append(recipient)
                        logger.info(f"邮件发送成功: {recipient}")
                else:
                    # 没有拒绝的收件人，发送成功
                    successful_recipients.append(recipient)
                    logger.info(f"邮件发送成功: {recipient}")
                
            except smtplib.SMTPSenderRefused as e:
                # 发送者被拒绝的异常
                error_code = getattr(e, 'smtp_code', -1)
                error_msg = getattr(e, 'smtp_error', str(e.smtp_error) if hasattr(e, 'smtp_error') else str(e))
                if isinstance(error_msg, bytes):
                    # 清理字节中的空字符
                    error_msg = error_msg.replace(b'\x00', b'').decode('utf-8', errors='ignore')
                else:
                    error_msg = str(error_msg)
                # 移除可能的空字符
                error_msg = error_msg.replace('\x00', '').strip()
                failed_recipients.append({
                    "email": recipient,
                    "error": f"SMTP发送者被拒绝 (代码 {error_code}): {error_msg}"
                })
                logger.error(f"向 {recipient} 发送邮件失败: SMTP发送者被拒绝 - {error_msg} (代码: {error_code})")
            except smtplib.SMTPRecipientsRefused as e:
                # 收件人被拒绝的异常
                failed_recipients.append({
                    "email": recipient,
                    "error": f"SMTP收件人被拒绝: {str(e)}"
                })
                logger.error(f"向 {recipient} 发送邮件失败: SMTP收件人被拒绝 - {str(e)}")
            except smtplib.SMTPDataError as e:
                # 邮件数据错误
                failed_recipients.append({
                    "email": recipient,
                    "error": f"SMTP数据错误: {str(e)}"
                })
                logger.error(f"向 {recipient} 发送邮件失败: SMTP数据错误 - {str(e)}")
            except smtplib.SMTPException as e:
                # 其他SMTP异常
                failed_recipients.append({
                    "email": recipient,
                    "error": f"SMTP异常: {str(e)}"
                })
                logger.error(f"向 {recipient} 发送邮件失败: SMTP异常 - {str(e)}")
            except Exception as e:
                # 其他未知异常
                error_type = type(e).__name__
                error_msg = str(e)
                failed_recipients.append({
                    "email": recipient,
                    "error": f"{error_type}: {error_msg}"
                })
                logger.error(f"向 {recipient} 发送邮件失败: {error_type} - {error_msg}", exc_info=True)
            finally:
                # 确保每个连接都被正确关闭
                if server:
                    try:
                        server.quit()
                        logger.debug(f"已关闭 {recipient} 的SMTP连接")
                    except Exception as e:
                        logger.warning(f"关闭 {recipient} 的SMTP连接时出错: {str(e)}")
                        try:
                            server.close()
                        except:
                            pass
        
        # 生成结果消息
        if successful_recipients and not failed_recipients:
            message = f"邮件已成功发送到 {len(successful_recipients)} 个收件人: {', '.join(successful_recipients)}"
        elif successful_recipients and failed_recipients:
            message = f"部分成功：成功发送到 {len(successful_recipients)} 个收件人，{len(failed_recipients)} 个失败"
        else:
            message = f"所有邮件发送失败"
        
        return {
            "success": len(successful_recipients) > 0,
            "message": message,
            "recipients": successful_recipients,
            "failed": failed_recipients
        }
    except Exception as e:
        logger.error(f"邮件发送功能异常: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"邮件发送功能异常: {str(e)}",
            "recipients": [],
            "failed": []
        }

