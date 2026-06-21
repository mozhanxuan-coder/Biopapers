import os
from dotenv import load_dotenv

# 自动加载根目录下的 .env 文件
load_dotenv()

class Config:
    # 1. PubMed & 爬虫配置
    PUBMED_API_BASE_URL = os.getenv("PUBMED_API_BASE_URL", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils")
    PUBMED_EMAIL = os.getenv("PUBMED_EMAIL", "")
    PUBMED_API_KEY = os.getenv("PUBMED_API_KEY", "")
    UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL", "")
    PUBMED_TOOL = os.getenv("PUBMED_TOOL", "BioPapersCrawler")

    # 2. 目录配置 (让所有代码都能自动找到 data 文件夹)
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data")
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")

    # 3. 爬虫控制参数
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", 2))
    REQUEST_INTERVAL_MIN = float(os.getenv("REQUEST_INTERVAL_MIN", 1.0))
    REQUEST_INTERVAL_MAX = float(os.getenv("REQUEST_INTERVAL_MAX", 3.0))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))

config = Config()