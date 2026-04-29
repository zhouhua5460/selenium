# -*- coding: utf-8 -*-
"""
配置文件 - 甲基硒代半胱氨酸(MSC)每日文献自动收集系统
"""

# ============================================================
# 搜索配置
# ============================================================
SEARCH_KEYWORD = "Methylselenocysteine"   # PubMed 标准检索词（MSC 的英文名）
SEARCH_KEYWORDS_ALT = [                    # 备选关键词，增加召回率
    "Se-methylselenocysteine",
    "MSC selenium",
    "methylselenocysteine cancer",
    "methylselenocysteine chemoprevention",
]
MAX_RESULTS = 10                           # 每次最多收集文献数
DAYS_BACK = 30                             # 搜索最近 N 天的文献（MSC 是小众方向，30 天更稳妥）
SORT_BY = "pub_date"                       # 排序方式：pub_date(最新发布) / relevance(相关度)

# 已发送记录文件路径（用于去重，避免重复推送）
SENT_RECORD_FILE = "sent_pmids.txt"

# ============================================================
# 邮件配置
# ============================================================
SMTP_SERVER = "smtp.163.com"
SMTP_PORT = 465                            # SSL 端口（163 邮箱用 465）
SENDER_EMAIL = "zhhua-1@163.com"
RECEIVER_EMAIL = "zhhua-1@163.com"

# 发件人密码/授权码：
# - 建议通过环境变量 SENDER_PASSWORD 传入，不要硬编码
# - 163 邮箱需要在设置中开启 SMTP 服务并生成授权码
import os
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

# ============================================================
# PubMed API 配置（可选）
# ============================================================
PUBMED_API_KEY = os.environ.get("PUBMED_API_KEY", "")
# 申请地址：https://www.ncbi.nlm.nih.gov/account/settings/
# 有 API Key：10 次/秒；无 API Key：3 次/秒

# ============================================================
# API 基础地址
# ============================================================
PUBMED_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
