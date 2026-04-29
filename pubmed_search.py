# -*- coding: utf-8 -*-
"""
PubMed 文献搜索模块
通过 NCBI E-utilities API 搜索和获取甲基硒代半胱氨酸(MSC)相关学术文献

参考文档：
- E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- E-search:   https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch
- E-fetch:    https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch
"""

import os
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import config


def load_sent_pmids(filepath: str = config.SENT_RECORD_FILE) -> set:
    """加载已发送过的 PMID 集合，用于去重"""
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_pmids(pmids: List[str], filepath: str = config.SENT_RECORD_FILE):
    """将新发送的 PMID 追加到记录文件"""
    existing = load_sent_pmids(filepath)
    new_pmids = set(pmids) - existing
    with open(filepath, "a", encoding="utf-8") as f:
        for pmid in sorted(new_pmids):
            f.write(pmid + "\n")
    print(f"已记录 {len(new_pmids)} 个新 PMID 到 {filepath}")


def search_pubmed(
    keyword: str,
    max_results: int = config.MAX_RESULTS,
    days_back: int = config.DAYS_BACK,
    sort_by: str = config.SORT_BY,
    exclude_sent: bool = True,
) -> List[Dict]:
    """
    通过 PubMed E-utilities (esearch + efetch) 搜索文献
    """
    # ---- Step 1: esearch 获取 PMID 列表 ----
    search_url = f"{config.PUBMED_EUTILS_BASE}/esearch.fcgi"
    
    today = datetime.now()
    since_date = (today - timedelta(days=days_back)).strftime("%Y/%m/%d")
    query = (
        f'{keyword}'
        f' AND ("{since_date}"[Date - Publication] : "3000"[Date - Publication])'
    )
    
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results * 3,
        "retmode": "json",
        "sort": sort_by,
    }
    
    headers = {}
    if config.PUBMED_API_KEY:
        headers["Authorization"] = f"Bearer {config.PUBMED_API_KEY}"
        params["api_key"] = config.PUBMED_API_KEY
    
    print(f"[搜索] 关键词: {keyword}")
    print(f"[搜索] 日期范围: {since_date} ~ 今天")
    
    resp = requests.get(search_url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    all_pmids = data.get("esearchresult", {}).get("idlist", [])
    total_count = int(data.get("esearchresult", {}).get("count", "0"))
    
    print(f"[搜索] 命中总数: {total_count}, 获取 PMID 数: {len(all_pmids)}")
    
    if not all_pmids:
        print("[搜索] 未找到匹配文献")
        return []
    
    # ---- 去重 ----
    if exclude_sent:
        sent_pmids = load_sent_pmids()
        new_pmids = [pmid for pmid in all_pmids if pmid not in sent_pmids]
        print(f"[去重] 已发: {len(sent_pmids)} 篇, 新增: {len(new_pmids)} 篇")
    else:
        new_pmids = all_pmids
    
    if not new_pmids:
        print("[去重] 所有命中文献均已推送过")
        return []
    
    new_pmids = new_pmids[:max_results]
    
    # ---- Step 2: efetch 获取详细信息 ----
    print(f"[获取] 正在获取 {len(new_pmids)} 篇文献详情...")
    articles = fetch_articles(new_pmids)
    
    return articles


def fetch_articles(pmids: List[str]) -> List[Dict]:
    """通过 efetch 获取 PubMed 文献的完整信息"""
    fetch_url = f"{config.PUBMED_EUTILS_BASE}/efetch.fcgi"
    
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    }
    
    headers = {}
    if config.PUBMED_API_KEY:
        params["api_key"] = config.PUBMED_API_KEY
    
    resp = requests.get(fetch_url, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    
    root = ET.fromstring(resp.content)
    
    articles = []
    for article_elem in root.findall(".//PubmedArticle"):
        article = parse_article_element(article_elem)
        if article:
            articles.append(article)
    
    print(f"[获取] 成功解析 {len(articles)} 篇文献")
    return articles


def parse_article_element(article_elem: ET.Element) -> Optional[Dict]:
    """解析单篇 PubMedArticle XML 元素"""
    try:
        pmid_elem = article_elem.find(".//PMID")
        pmid = pmid_elem.text.strip() if pmid_elem is not None else "unknown"
        
        title_elem = article_elem.find(".//ArticleTitle")
        title = ""
        if title_elem is not None:
            title = "".join(title_elem.itertext()).strip()
        if not title:
            title = "(无标题)"
        
        author_elems = article_elem.findall(".//Author")
        authors_list = []
        for au in author_elems:
            last_name = au.findtext("LastName", "")
            fore_name = au.findtext("ForeName", "")
            if last_name:
                if fore_name:
                    authors_list.append(f"{last_name} {fore_name[0]}.")
                else:
                    authors_list.append(last_name)
        
        if not authors_list:
            authors = "(作者不详)"
        elif len(authors_list) <= 3:
            authors = ", ".join(authors_list)
        else:
            authors = ", ".join(authors_list[:3]) + f" et al. ({len(authors_list)} 位作者)"
        
        journal = ""
        journal_elem = article_elem.find(".//Journal/Title")
        if journal_elem is not None and journal_elem.text:
            journal = journal_elem.text.strip()
        
        citation_parts = []
        if journal:
            citation_parts.append(journal)
        
        pub_date_text = ""
        date_elem = article_elem.find(".//PubDate")
        if date_elem is not None:
            year = date_elem.findtext("Year", "")
            month = date_elem.findtext("Month", "")
            day = date_elem.findtext("Day", "")
            medline_date = date_elem.findtext("MedlineDate", "")
            
            if year:
                pub_date_text = year
                if month:
                    pub_date_text += f"-{month}"
                    if day:
                        pub_date_text += f"-{day}"
            elif medline_date:
                pub_date_text = medline_date
        
        if pub_date_text:
            citation_parts.append(pub_date_text)
        
        vol = article_elem.findtext(".//Volume", "")
        issue = article_elem.findtext(".//Issue", "")
        pages = article_elem.findtext(".//MedlinePgn", "")
        
        if vol or issue:
            part = vol or ""
            if issue:
                part += f"({issue})"
            citation_parts.append(part)
        if pages:
            citation_parts.append(pages)
        
        full_citation = "; ".join(citation_parts) if citation_parts else "(期刊信息不详)"
        
        doi = ""
        for aid in article_elem.findall(".//ArticleId"):
            if aid.get("IdType") == "doi":
                doi = aid.text.strip() if aid.text else ""
        
        abstract_parts = []
        abs_elems = article_elem.findall(".//AbstractText")
        if abs_elems:
            for abs_elem in abs_elems:
                label = abs_elem.get("Label", "")
                text = "".join(abs_elem.itertext()).strip()
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
        
        abstract = "\n".join(abstract_parts) if abstract_parts else "(暂无摘要)"
        abstract = " ".join(abstract.split())
        
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        
        return {
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "journal": journal,
            "full_citation": full_citation,
            "abstract": abstract,
            "doi": doi,
            "pub_date": pub_date_text,
            "url": url,
        }
    
    except Exception as e:
        print(f"[警告] 解析文献时出错: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("PubMed 文献搜索 - 测试运行")
    print("=" * 60)
    
    articles = search_pubmed(
        keyword=config.SEARCH_KEYWORD,
        max_results=5,
        days_back=90,
        exclude_sent=False,
    )
    
    print(f"\n{'='*60}")
    print(f"搜索结果: {len(articles)} 篇\n")
    for i, art in enumerate(articles, 1):
        print(f"--- [{i}] PMID: {art['pmid']} ---")
        print(f"  标题: {art['title']}")
        print(f"  作者: {art['authors']}")
        print(f"  期刊: {art['full_citation']}")
        print(f"  DOI:  {art['doi']}")
        print(f"  链接: {art['url']}")
        print(f"  摘要: {art['abstract'][:200]}...")
        print()
