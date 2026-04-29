# -*- coding: utf-8 -*-
"""
主程序入口 - 甲基硒代半胱氨酸(MSC)每日文献自动收集系统
"""

import sys
import os
import argparse
import logging
from datetime import datetime

import config
import pubmed_search as searcher
import email_sender as mailer

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run(
    max_results: int = config.MAX_RESULTS,
    days_back: int = config.DAYS_BACK,
    keyword: str = None,
    dry_run: bool = False,
    no_send: bool = False,
) -> int:
    """主执行流程"""
    log.info("=" * 60)
    log.info("MSC 文献自动收集系统 启动")
    log.info("=" * 60)

    search_keyword = keyword or config.SEARCH_KEYWORD
    log.info(f"搜索关键词: {search_keyword}")
    log.info(f"回溯天数: {days_back}, 目标数量: {max_results}")

    # Step 1: 搜索文献
    try:
        articles = searcher.search_pubmed(
            keyword=search_keyword,
            max_results=max_results,
            days_back=days_back,
            exclude_sent=(not dry_run),
        )
    except Exception as e:
        log.error(f"文献搜索失败: {e}")
        return 1

    if not articles:
        log.info("未找到新的文献，任务结束")
        return 0

    log.info(f"成功获取 {len(articles)} 篇文献，准备发送邮件...")

    # Step 2: 发送邮件
    if not no_send:
        try:
            mailer.send_literature_email(articles)
        except Exception as e:
            log.error(f"邮件发送失败: {e}")
            return 2
    else:
        log.info("[NO_SEND 模式] 跳过邮件发送")

    # Step 3: 记录已发送 PMID
    if not dry_run:
        pmids = [a["pmid"] for a in articles]
        searcher.save_pmids(pmids)
        log.info(f"已标记 {len(pmids)} 篇文献为已发送")
    else:
        log.info("[DRY_RUN 模式] 未写入发送记录")

    log.info("=" * 60)
    log.info(f"任务完成! 共处理 {len(articles)} 篇文献")
    log.info("=" * 60)
    return 0


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="MSC 文献自动收集系统 - 每日从 PubMed 收集文献并发送邮件"
    )
    parser.add_argument(
        "--max-results", type=int, default=config.MAX_RESULTS,
        help=f"每次最多收集文献数 (默认: {config.MAX_RESULTS})"
    )
    parser.add_argument(
        "--days-back", type=int, default=config.DAYS_BACK,
        help=f"搜索最近 N 天的文献 (默认: {config.DAYS_BACK})"
    )
    parser.add_argument(
        "--keyword", type=str, default=None,
        help=f"覆盖搜索关键词 (默认: {config.SEARCH_KEYWORD})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="演练模式：运行完整流程但不发送邮件、不写记录"
    )
    parser.add_argument(
        "--no-send", action="store_true",
        help="搜索并解析，但不发送邮件（调试用）"
    )

    args = parser.parse_args()

    exit_code = run(
        max_results=args.max_results,
        days_back=args.days_back,
        keyword=args.keyword,
        dry_run=args.dry_run,
        no_send=args.no_send,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
