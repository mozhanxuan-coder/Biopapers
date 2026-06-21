import os
import sys
import glob
import subprocess
import argparse
from loguru import logger

def get_latest_json(directory="data"):
    """
    扫描指定目录，获取最新生成的 papers_*.json 文件
    """
    search_pattern = os.path.join(directory, "papers_*.json")
    files = glob.glob(search_pattern)
    if not files:
        return None
    # 按照文件的最后修改时间进行排序，返回最新的文件
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def run_pipeline(keywords: str, max_results: int):
    """
    按顺序执行爬取、解析和 AI 总结的完整管线
    """
    logger.info("=" * 60)
    logger.info(f"启动全链路自动化分析 | 关键词: '{keywords}' | 抓取数量: {max_results}")
    logger.info("=" * 60)

    # --------------------------------------------------
    # 步骤 1: 运行爬虫
    # --------------------------------------------------
    logger.info(">>> [步骤 1/3] 启动网络爬虫模块...")
    crawl_cmd = [
        sys.executable, "-m", "crawling.crawler",
        "--keywords", keywords,
        "--max-results", str(max_results)
    ]
    crawl_result = subprocess.run(crawl_cmd)
    if crawl_result.returncode != 0:
        logger.error("爬虫模块执行异常，流水线终止。")
        sys.exit(1)

    # 自动获取刚刚生成的 JSON 文件路径
    latest_json = get_latest_json()
    if not latest_json:
        logger.error("未检测到爬虫输出的 JSON 文件，流水线终止。")
        sys.exit(1)
    logger.info(f"自动锁定最新数据文件: {latest_json}")

    # --------------------------------------------------
    # 步骤 2: 运行解析与入库
    # --------------------------------------------------
    logger.info(">>> [步骤 2/3] 启动内容解析与数据库写入模块...")
    parse_cmd = [
        sys.executable, "content_parsing/main.py",
        "--input", latest_json
    ]
    parse_result = subprocess.run(parse_cmd)
    if parse_result.returncode != 0:
        logger.error("内容解析模块执行异常，流水线终止。")
        sys.exit(1)

    # --------------------------------------------------
    # 步骤 3: 运行 AI 总结
    # --------------------------------------------------
    logger.info(">>> [步骤 3/3] 启动大模型深度总结模块...")
    ai_cmd = [
        sys.executable, "ai_summarizer.py"
    ]
    ai_result = subprocess.run(ai_cmd)
    if ai_result.returncode != 0:
        logger.error("AI 总结模块执行异常，流水线终止。")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("全链路自动化任务执行完毕，请前往 data/summaries/ 目录查看结果。")
    logger.info("=" * 60)


if __name__ == "__main__":
    # 配置命令行参数解析
    parser = argparse.ArgumentParser(description="生物医学文献自动化检索与 AI 总结流水线")
    parser.add_argument("--keywords", type=str, required=True, help="需要检索的学术关键词 (例如: 'CRISPR Cas9')")
    parser.add_argument("--max-results", type=int, default=3, help="最大抓取论文数量 (默认: 3)")
    
    args = parser.parse_args()
    run_pipeline(args.keywords, args.max_results)