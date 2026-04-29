# -*- coding: utf-8 -*-
"""
邮件发送模块
将文献列表以精美的 HTML 格式通过 163 邮箱 SMTP 发送
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import config


def build_html_email(articles: list) -> str:
    """构建美观的 HTML 邮件正文"""
    today = datetime.now().strftime("%Y年%m月%d日")
    count = len(articles)
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  body {{
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial,
               "PingFang SC", "Microsoft YaHei", sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f9f9f9;
  }}
  .header {{
    background: linear-gradient(135deg, #1a5276, #2e86c1);
    color: white;
    padding: 24px 28px;
    border-radius: 10px 10px 0 0;
    margin-bottom: 0;
  }}
  .header h1 {{
    margin: 0 0 8px 0;
    font-size: 22px;
  }}
  .header .meta {{
    opacity: 0.9;
    font-size: 14px;
  }}
  .stats {{
    background: #eaf2f8;
    padding: 14px 28px;
    border-left: 4px solid #2e86c1;
    font-size: 15px;
    color: #1a5276;
  }}
  .content {{
    background: white;
    padding: 20px 28px 30px;
    border-radius: 0 0 10px 10px;
  }}
  .article {{
    border-bottom: 1px solid #eaeaea;
    padding: 20px 0;
  }}
  .article:last-child {{
    border-bottom: none;
  }}
  .article-title {{
    font-size: 16px;
    font-weight: 600;
    color: #1a5276;
    margin-bottom: 6px;
    line-height: 1.4;
  }}
  .article-meta {{
    font-size: 13px;
    color: #777;
    margin-bottom: 8px;
  }}
  .article-meta span {{
    margin-right: 14px;
  }}
  .article-abstract {{
    font-size: 13.5px;
    color: #444;
    background: #f8f9fa;
    padding: 12px 14px;
    border-radius: 6px;
    border-left: 3px solid #bdc3c7;
    line-height: 1.7;
  }}
  .article-links {{
    margin-top: 8px;
  }}
  .article-links a {{
    display: inline-block;
    font-size: 12.5px;
    padding: 4px 12px;
    border-radius: 4px;
    text-decoration: none;
    margin-right: 8px;
  }}
  .btn-pubmed {{
    background-color: #2e86c1;
    color: white !important;
  }}
  .btn-doi {{
    background-color: #27ae60;
    color: white !important;
  }}
  .footer {{
    text-align: center;
    font-size: 12px;
    color: #aaa;
    margin-top: 20px;
    padding-top: 14px;
    border-top: 1px solid #eee;
  }}
  .index-badge {{
    display: inline-block;
    background: #2e86c1;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    text-align: center;
    line-height: 24px;
    font-size: 12px;
    font-weight: bold;
    margin-right: 8px;
    vertical-align: middle;
  }}
</style>
</head>
<body>

<div class="header">
  <h1>&#128218; 甲基硒代半胱氨酸(MSC) 每日文献推送</h1>
  <div class="meta">自动采集自 PubMed &middot; {today}</div>
</div>

<div class="stats">
  &#128196; 本次推送 <b>{count}</b> 篇相关文献 &emsp;|&emsp;
  关键词: <b>Methylselenocysteine (MSC)</b> &emsp;|&emsp;
  数据来源: <a href="https://pubmed.ncbi.nlm.nih.gov/" style="color:#2e86c1;">PubMed.gov</a>
</div>

<div class="content">
"""
    
    for i, art in enumerate(articles, 1):
        title = escape_html(art.get("title", "(无标题)"))
        authors = escape_html(art.get("authors", ""))
        citation = escape_html(art.get("full_citation", ""))
        abstract = escape_html(art.get("abstract", "(暂无摘要)"))
        pmid = art.get("pmid", "")
        doi = art.get("doi", "")
        pubmed_url = art.get("url", "")
        
        html += f"""
  <div class="article">
    <div class="article-title">
      <span class="index-badge">{i}</span>{title}
    </div>
    <div class="article-meta">
      <span>&#128100; {authors}</span>
      <span>&#128214; {citation}</span>
    </div>
    <div class="article-abstract">{abstract}</div>
    <div class="article-links">
      <a href="{pubmed_url}" class="btn-pubmed" target="_blank">&#128279; PubMed 原文</a>"""
        
        if doi:
            doi_url = f"https://doi.org/{doi}"
            html += f"""
      <a href="{doi_url}" class="btn-doi" target="_blank">&#128220; DOI 全文</a>"""
        
        html += """
    </div>
  </div>
"""
    
    html += f"""
</div>

<div class="footer">
  此邮件由 MSC Literature Bot 自动生成并发送<br/>
  Powered by PubMed E-utilities API &middot; {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
</div>

</body>
</html>
"""
    return html


def escape_html(text: str) -> str:
    """HTML 转义"""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def send_literature_email(
    articles: list,
    sender_email: str = config.SENDER_EMAIL,
    receiver_email: str = config.RECEIVER_EMAIL,
    sender_password: str = None,
    smtp_server: str = config.SMTP_SERVER,
    smtp_port: int = config.SMTP_PORT,
) -> bool:
    """将文献列表以 HTML 格式邮件发送"""
    
    if not articles:
        print("[邮件] 没有文献需要发送")
        return False
    
    password = sender_password or config.SENDER_PASSWORD or os.environ.get("SENDER_PASSWORD", "")
    if not password:
        raise ValueError(
            "未配置发件人密码！请设置以下任一方式:\n"
            "  1. 环境变量 SENDER_PASSWORD\n"
            "  2. config.py 中 SENDER_PASSWORD\n"
            "  3. 调用时传入 sender_password 参数"
        )
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[MSC文献日报] 甲基硒代半胱氨酸最新文献 ({today}) | 共{len(articles)}篇"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    
    html_body = build_html_email(articles)
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    
    plain_text = build_plain_text(articles)
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    
    print(f"[邮件] 正在连接 SMTP: {smtp_server}:{smtp_port}")
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"[邮件] 发送成功! 收件人: {receiver_email}, 文献数: {len(articles)}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[邮件] SMTP 认证失败！请检查:")
        print("     - 授权码是否正确（不是登录密码）")
        print("     - 163邮箱是否已开启SMTP服务")
        raise
    except Exception as e:
        print(f"[邮件] 发送失败: {e}")
        raise


def build_plain_text(articles: list) -> str:
    """构建纯文本版本"""
    lines = [
        "=" * 60,
        "甲基硒代半胱氨酸(MSC) 每日文献推送",
        f"日期: {datetime.now().strftime('%Y年%m月%d日')}",
        f"共 {len(articles)} 篇文献",
        "=" * 60,
        "",
    ]
    for i, art in enumerate(articles, 1):
        lines.append(f"[{i}] {art['title']}")
        lines.append(f"    作者: {art['authors']}")
        lines.append(f"    期刊: {art['full_citation']}")
        if art.get("doi"):
            lines.append(f"    DOI:  https://doi.org/{art['doi']}")
        lines.append(f"    链接: {art['url']}")
        lines.append(f"    摘要: {art['abstract'][:300]}...")
        lines.append("")
    
    lines.append("-" * 60)
    lines.append("此邮件由 MSC Literature Bot 自动生成")
    return "\n".join(lines)


if __name__ == "__main__":
    test_articles = [
        {
            "pmid": "12345678",
            "title": "Methylselenocysteine induces apoptosis in cancer cells via the mitochondrial pathway",
            "authors": "Zhang Y., Wang L., Li J. et al. (5 位作者)",
            "journal": "Journal of Biological Chemistry",
            "full_citation": "Journal of Biological Chemistry. 2025;298(5):102-115",
            "abstract": (
                "Methylselenocysteine (MSC), a naturally occurring selenium compound, "
                "has shown promising chemopreventive effects in various cancer models."
            ),
            "doi": "10.1016/j.jbc.2025.01.001",
            "pub_date": "2025-03-15",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        },
    ]
    
    print("=" * 60)
    print("邮件模块 - 测试运行")
    print("(仅输出 HTML 到文件，不实际发送)")
    print("=" * 60)
    
    html = build_html_email(test_articles)
    output_file = "test_email_output.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\nHTML 邮件已保存到: {output_file}")
