import os
import sys
import json
import re  # <--- 新增：用于处理正则表达式
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

# ==========================================
# 1. 环境初始化与路径加载
# ==========================================
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from config import config
    from content_parsing.database import PaperDatabase
except ImportError as e:
    logger.error(f"导入模块失败，请确保当前在项目根目录下运行此脚本: {e}")
    sys.exit(1)


# ==========================================
# 2. AI 总结器核心类
# ==========================================
class LLMSummarizer:
    def __init__(self, db_path: str = None):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.model_name = os.getenv("LLM_MODEL_NAME", "deepseek-chat")
        
        if not self.api_key or self.api_key.startswith("sk-你的"):
            logger.error("LLM_API_KEY 未正确配置！请检查项目根目录的 .env 文件。")
            sys.exit(1)

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        output_base = getattr(config, "OUTPUT_DIR", "data")
        self.output_dir = os.path.join(current_dir, output_base, "summaries")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.db = PaperDatabase(db_path)
        logger.info(f"AI Summarizer 初始化成功. 模型: {self.model_name}, 输出目录: {self.output_dir}")

    def _get_safe_filename(self, title: str) -> str:
        """
        核心新增：将论文标题转换为安全的系统文件名
        """
        if not title:
            return "Untitled_Paper.md"
            
        # 1. 替换掉 Mac/Windows 系统不允许出现在文件名中的字符
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        # 2. 去掉可能存在的换行符
        safe_title = safe_title.replace('\n', ' ').replace('\r', '')
        # 3. 限制长度在 150 个字符以内，防止超出系统限制，并去除首尾空格
        safe_title = safe_title[:150].strip()
        
        return f"{safe_title}.md"

    def _extract_core_text(self, db_paper) -> dict:
        abstract = db_paper.abstract or ""
        methods_text = ""
        results_text = ""
        
        sections = db_paper.sections or []
        if isinstance(sections, str):
            try:
                sections = json.loads(sections)
            except Exception as e:
                logger.warning(f"解析论文 {db_paper.pmid} 的 sections 失败: {e}")
                sections = []

        for section in sections:
            if isinstance(section, dict):
                stype = section.get("section_type", "").lower()
                content = section.get("content", "")
                
                if stype in ["methods", "materials and methods"]:
                    methods_text += content + "\n"
                elif stype in ["results", "findings"]:
                    results_text += content + "\n"

        return {
            "title": db_paper.title,
            "journal": db_paper.journal or "Unknown Journal",
            "abstract": abstract,
            "methods": methods_text[:8000], 
            "results": results_text[:10000] 
        }

    def _build_bioinformatics_prompt(self, paper_core: dict) -> str:
        prompt = f"""你是一名资深的计算生物学与生物医学工程领域的科研专家。请阅读以下从最新学术论文中提取的结构化信息，生成一份详尽、专业、客观的文献深度概述。

【待总结论文信息】
标题: {paper_core['title']}
期刊: {paper_core['journal']}
摘要: {paper_core['abstract']}
方法片段: {paper_core['methods']}
结果片段: {paper_core['results']}

【生成要求】
1. 语言风格：极其客观、严谨的学术语言，绝对不使用任何表情符号或主观抒情修饰词。
2. 内容深度：不限制字数。请尽可能详细地还原论文的科学逻辑，如果文本中包含底层算法、大模型架构、数据处理管线、模型超参数配置，或是具体的分子机制与核心技术（如具体的 CRISPR-Cas 系统细节、序列预测方式），请务必重点且详细地阐述。
3. 必须包含以下结构块（请严格使用这些标题）：
   - 【研究背景与动机】：阐述该领域存在的痛点，以及本研究旨在解决的核心科学问题。
   - 【详尽研究方法】：详细梳理实验设计或计算工作流（包含所用数据集、模型框架、训练/预测策略或具体实验技术）。
   - 【核心数据与结果】：列出关键的性能指标或实验结果（如有模型准确率提升幅度、显著性 p 值、关键验证数据等，必须写出具体数字或定性突破）。
   - 【领域应用与启示】：客观评价该成果对该领域的实际贡献及未来可能的拓展方向。

请直接输出上述四个结构块的内容，不要包含任何前导词或结尾客套话。"""
        return prompt

    def generate_summary(self, db_paper) -> str:
        paper_core = self._extract_core_text(db_paper)
        
        if not paper_core["abstract"] and not paper_core["methods"] and not paper_core["results"]:
            logger.warning(f"论文 {db_paper.pmid} 缺乏有效文本，跳过总结。")
            return ""

        prompt = self._build_bioinformatics_prompt(paper_core)
        
        try:
            logger.info(f"正在请求 LLM ({self.model_name}) 深度总结论文: {db_paper.pmid}...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个严谨且前沿的学术专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2, 
                max_tokens=2500  
            )
            
            summary_content = response.choices[0].message.content.strip()
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{db_paper.pmid}/"
            
            # 使用全新的安全文件名生成逻辑
            md_filename = self._get_safe_filename(paper_core['title'])
            md_path = os.path.join(self.output_dir, md_filename)
            
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(f"# {paper_core['title']}\n\n")
                f.write(f"> **PMID**: {db_paper.pmid} | **Journal**: {paper_core['journal']}\n")
                f.write(f"> **Link**: [点击直达 PubMed 论文页面]({pubmed_url})\n\n")
                f.write("---\n\n")
                f.write(summary_content)
                
            logger.success(f"成功生成深度总结: {md_filename}")
            return summary_content

        except Exception as e:
            logger.error(f"请求 LLM 失败 (论文 {db_paper.pmid}): {e}")
            return ""

    def batch_process(self):
        papers = self.db.get_all_papers()
        if not papers:
            logger.warning("数据库中没有论文，请先运行解析模块！")
            return

        logger.info(f"在数据库中找到 {len(papers)} 篇论文，开始批量总结任务...")
        
        success_count = 0
        skip_count = 0
        
        for paper in papers:
            # 去重检测也必须同步更新为新的文件名逻辑
            expected_filename = self._get_safe_filename(paper.title)
            expected_md_path = os.path.join(self.output_dir, expected_filename)
            
            if os.path.exists(expected_md_path):
                logger.debug(f"论文总结已存在，跳过: {expected_filename}")
                skip_count += 1
                continue
                
            summary = self.generate_summary(paper)
            if summary:
                success_count += 1
                
        logger.info("="*50)
        logger.info(f"批量总结完成！成功生成: {success_count} 篇 | 跳过已存在: {skip_count} 篇")
        logger.info("="*50)


# ==========================================
# 3. 运行入口
# ==========================================
if __name__ == "__main__":
    summarizer = LLMSummarizer()
    summarizer.batch_process()