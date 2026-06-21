import os
import sys
import re
import random
import base64
import json
import sqlite3
from datetime import datetime
import streamlit as st

# ==========================================
# 1. 动态获取当前根目录
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 2. 本地图片加载器
# ==========================================
ASSETS_DIR = os.path.join(current_dir, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
            ext = image_path.split('.')[-1].lower()
            mime_type = "image/png" if ext == "png" else "image/jpeg"
            return f"data:{mime_type};base64,{encoded_string}"
    return None

# ==========================================
# 3. 真实流量数据追踪引擎 (持久化 JSON 记录)
# ==========================================
STATS_FILE = os.path.join(current_dir, "data", "visit_stats.json")

def track_and_get_visits():
    """轻量级本地流量统计系统 - 初始底数为 0"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    stats = {"total_visits": 0, "daily_visits": 0, "last_date": today_str}
    
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except Exception: pass
            
    if stats.get("last_date") != today_str:
        stats["daily_visits"] = 0
        stats["last_date"] = today_str
        
    if "has_counted_visit" not in st.session_state:
        stats["total_visits"] += 1
        stats["daily_visits"] += 1
        st.session_state.has_counted_visit = True
        
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)
            
    return stats["total_visits"], stats["daily_visits"]

# ==========================================
# 4. 万能安全字段提取器
# ==========================================
def safe_get(item, key, default=""):
    if item is None: return default
    if isinstance(item, dict): return item.get(key) or default
    if hasattr(item, key): return getattr(item, key, default) or default
    return default

# ==========================================
# 5. 路由与状态初始化 (包含冷缓存锁死)
# ==========================================
if "current_view" not in st.session_state: st.session_state.current_view = "about"
if "selected_paper_title" not in st.session_state: st.session_state.selected_paper_title = None
if "view_history" not in st.session_state: st.session_state.view_history = []
if "page_all" not in st.session_state: st.session_state.page_all = 1
if "page_search" not in st.session_state: st.session_state.page_search = 1
if "home_cited_papers" not in st.session_state: st.session_state.home_cited_papers = []
if "home_viewed_papers" not in st.session_state: st.session_state.home_viewed_papers = []

# ==========================================
# 6. Apple 级绝对防脱流、防塌陷 CSS 注入
# ==========================================
st.set_page_config(page_title="BioPapers", layout="wide", initial_sidebar_state="collapsed")
anim_name = f"viewFadeUp_{st.session_state.current_view}"

st.markdown(f"""
    <style>
    /* 彻底隐藏白色的原生 Header 元素 */
    header {{ display: none !important; }}
    .stApp {{ background-color: #fbfbfd !important; overflow-x: hidden !important; }}
    
    /* 顶部留出 60px 给固定的导航条，防止下方内容被遮挡 */
    .block-container {{ padding-top: 60px !important; padding-bottom: 3rem !important; max-width: 1040px !important; }}
    hr {{ border-color: #d2d2d7 !important; margin-top: 2.5rem !important; margin-bottom: 2.5rem !important; }}

    /* 轻量级淡入上浮动画 */
    @keyframes {anim_name} {{
        0% {{ opacity: 0; transform: translateY(15px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}
    .full-bleed-image, .full-bleed-white, .welcome-animation, .apple-h2, [data-testid="stVerticalBlockBorderWrapper"], .stat-number, .stat-label, .apple-hero {{
        animation: {anim_name} 0.45s cubic-bezier(0.25, 1, 0.5, 1) both;
    }}

    /* =========================================================
       🍏 纯正苹果官网级：满宽深黑导航条 (绝对防崩溃版)
       ========================================================= */
    /* 隐藏锚点 */
    div[data-testid="stElementContainer"]:has(.nav-teleport) {{
        display: none !important;
        position: absolute !important;
        width: 0 !important; height: 0 !important;
    }}

    /* 精准锁定导航横块：全宽极深黑毛玻璃 */
    div[data-testid="stHorizontalBlock"]:has(.nav-teleport) {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100vw !important;
        max-width: 100vw !important;
        height: 48px !important; 
        background-color: rgba(0, 0, 0, 0.95) !important; /* 极深黑 */
        backdrop-filter: saturate(180%) blur(20px) !important;
        -webkit-backdrop-filter: saturate(180%) blur(20px) !important;
        z-index: 999999 !important;
        margin: 0 !important;
        padding: 0 15% !important; /* 左右不贴边 */
        gap: 0 !important; 
    }}

    /* 内部对齐 */
    div[data-testid="stHorizontalBlock"]:has(.nav-teleport) > div[data-testid="column"] {{
        padding: 0 !important;
        margin: 0 !important;
        height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    /* 按钮化身纯文本无边框 */
    div[data-testid="stHorizontalBlock"]:has(.nav-teleport) button {{
        background: transparent !important; 
        border: none !important; 
        color: #a1a1a6 !important; /* 灰色 */
        font-size: 13px !important; 
        font-weight: 400 !important; 
        letter-spacing: 0.02em !important;
        box-shadow: none !important; 
        width: 100% !important; 
        height: 48px !important; 
        border-radius: 0 !important; 
        padding: 0 !important;
        margin: 0 !important;
        transition: color 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    /* 悬停纯白无色块 */
    div[data-testid="stHorizontalBlock"]:has(.nav-teleport) button:hover,
    div[data-testid="stHorizontalBlock"]:has(.nav-teleport) button:active,
    div[data-testid="stHorizontalBlock"]:has(.nav-teleport) button:focus {{ 
        color: #ffffff !important; 
        background: transparent !important; 
        outline: none !important;
    }}

    div[data-testid="stHorizontalBlock"]:has(.nav-teleport) button p {{
        margin: 0 !important;
        padding: 0 !important;
        line-height: 48px !important;
    }}
    /* ========================================================= */

    /* 大屏巨幕画布 */
    .full-bleed-image {{ width: 100vw; height: 460px; margin-left: calc(-50vw + 50%); margin-bottom: 40px; position: relative; background-color: #000; background-size: cover; background-position: center; border-radius: 18px; overflow: hidden; }}
    .image-hero-overlay {{ position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0, 0, 0, 0.45); z-index: 1; }}
    .image-hero-content {{ position: relative; z-index: 2; text-align: center; color: #ffffff; padding: 0 20px; top: 50%; transform: translateY(-50%); }}
    .full-bleed-white {{ width: 100vw; background-color: #ffffff; margin-left: calc(-50vw + 50%); padding-top: 50px; padding-bottom: 50px; border-bottom: 1px solid #e5e5ea; display: flex; justify-content: center; margin-bottom: 40px; }}
    .hero-content-wrapper {{ text-align: center; max-width: 900px; padding: 0 20px; width: 100%; }}
    .hero-h1 {{ font-size: 60px; font-weight: 700; letter-spacing: -0.015em; margin-bottom: 10px; line-height: 1.1; }}
    .hero-p {{ font-size: 22px; font-weight: 400; max-width: 800px; line-height: 1.4; color: #f5f5f7; margin: 0 auto; }}
    .apple-h1 {{ font-size: 52px; font-weight: 700; color: #1d1d1f; margin-bottom: 15px; letter-spacing: -0.015em; }}
    .apple-intro {{ font-size: 22px; color: #86868b; line-height: 1.33; }}
    .apple-h2 {{ font-size: 30px; font-weight: 600; color: #1d1d1f; margin-top: 30px; margin-bottom: 20px; }}

    .welcome-animation {{ margin-top: 20px; font-size: 18px; font-weight: 500; color: #2997ff; display: flex; flex-direction: column; align-items: center; gap: 8px; animation: welcomeFloat 2s ease-in-out infinite; cursor: default; }}

    /* 立体论文卡片 */
    [data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 18px !important; background-color: #ffffff !important; border: none !important; box-shadow: 0 8px 24px rgba(0,0,0,0.04) !important; transition: transform 0.3s ease, box-shadow 0.3s ease !important; padding: 22px !important; margin-bottom: 24px !important; }}
    [data-testid="stVerticalBlockBorderWrapper"]:hover {{ transform: translateY(-4px) !important; box-shadow: 0 16px 32px rgba(0,0,0,0.09) !important; }}

    .stat-number {{ font-size: 56px; font-weight: 700; color: #1d1d1f; letter-spacing: -0.02em; }}
    .stat-label {{ color: #86868b; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}

    /* 贯穿式底部页脚 */
    .apple-footer-wrapper {{ width: 100vw; margin-left: calc(-50vw + 50%); background-color: #f5f5f7; padding: 40px 0; border-top: 1px solid #d2d2d7; margin-top: 60px; }}
    .apple-footer-content {{ max-width: 1000px; margin: 0 auto; text-align: center; font-size: 12px; color: #86868b; line-height: 2; }}
    .apple-footer-content a, .footer-link {{ color: #424245; text-decoration: none; font-weight: 500; cursor: pointer; transition: color 0.2s; }}
    .apple-footer-content a:hover, .footer-link:hover {{ color: #1d1d1f; text-decoration: underline; }}
    </style>
""", unsafe_allow_html=True)

SUMMARIES_DIR = os.path.join(current_dir, "data", "summaries")

# ==========================================
# 7. 底层 SQLite 纯净直连读取
# ==========================================
def get_papers_data():
    try:
        db_path = os.path.join(current_dir, "data", "papers.db")
        if not os.path.exists(db_path): return []
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        
        target_table = "papers"
        if "papers" not in tables:
            if "paper" in tables: target_table = "paper"
            elif tables: target_table = next((t for t in tables if t != "sqlite_sequence"), tables[0])
                
        cursor.execute(f"SELECT * FROM {target_table}")
        rows = cursor.fetchall()
        conn.close()
        
        all_papers = [dict(row) for row in rows]
        return sorted(all_papers, key=lambda x: str(safe_get(x, 'pub_date', '')), reverse=True)
    except Exception as e:
        return []

papers = get_papers_data()

def truncate_title(max_len=45, title=""): 
    return title if len(title or "") <= max_len else title[:max_len] + "..."

def change_view(view_name):
    st.session_state.current_view = view_name
    st.session_state.page_all = 1
    st.session_state.page_search = 1
    st.rerun()

# ==========================================
# 8. 🍏 无缝隙・深黑毛玻璃导航 🍏
# ==========================================
nav_cols = st.columns(5) 
with nav_cols[0]:
    # 放置隐形锚点
    st.markdown('<div class="nav-teleport" style="display:none;"></div>', unsafe_allow_html=True)
    if st.button("BioPapers", use_container_width=True): change_view("about")
with nav_cols[1]:
    if st.button("首页看板", use_container_width=True): change_view("home")
with nav_cols[2]:
    if st.button("全部论文", use_container_width=True): change_view("all_papers")
with nav_cols[3]:
    if st.button("浏览历史", use_container_width=True): change_view("history")
with nav_cols[4]:
    if st.button("搜索", use_container_width=True): change_view("search")

# ==========================================
# 9. 模块级高品质带图组件组 (恢复原图)
# ==========================================
def get_card_image_html(pmid, height="140px", radius="10px"):
    idx = (int(pmid or 0) % 5) + 1
    local_img = os.path.join(ASSETS_DIR, f"{idx}.jpg")
    base64_str = get_base64_image(local_img)
    if base64_str: 
        return f'<img src="{base64_str}" style="width:100%; height:{height}; object-fit:cover; border-radius:{radius}; margin-bottom:12px;">'
    return f'<div style="width:100%; height:{height}; border-radius:{radius}; background: #e3e3e8; margin-bottom:12px;"></div>'

def render_paper_card(paper, tag_color, tag_text, section_key):
    pmid = safe_get(paper, 'pmid')
    title = safe_get(paper, 'title', '未知文献')
    
    with st.container(border=True):
        st.markdown(get_card_image_html(pmid), unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 12px; font-weight: 600; color: {tag_color}; margin-bottom: 8px;'>{tag_text}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 18px; font-weight: 600; color: #1d1d1f; line-height: 1.3; margin-bottom: 15px; height: 46px; overflow: hidden;'>{truncate_title(45, title)}</div>", unsafe_allow_html=True)
        
        st.markdown(f"""<style>div[data-testid="stVerticalBlock"] div:nth-child({section_key}) button {{ background: transparent !important; color: #06c !important; border: none !important; font-size: 15px !important; padding: 0 !important; justify-content: left !important; }} div[data-testid="stVerticalBlock"] div:nth-child({section_key}) button:hover {{ text-decoration: underline !important; }}</style>""", unsafe_allow_html=True)
        if st.button("深入了解 >", key=f"btn_{section_key}_{pmid}", use_container_width=True):
            st.session_state.selected_paper_title = title
            st.session_state.current_view = "detail"
            if title in st.session_state.view_history: st.session_state.view_history.remove(title)
            st.session_state.view_history.insert(0, title)
            st.rerun()

def render_apple_hero(title, subtitle):
    st.markdown(f"""
        <div class="apple-hero" style="padding: 20px 0 10px 0;">
            <h1 style="font-size: 64px; font-weight: 700; color: #1d1d1f; margin: 0 0 12px 0; letter-spacing: -0.02em; line-height: 1.1;">{title}</h1>
            <p style="font-size: 24px; color: #86868b; font-weight: 400; margin: 0; line-height: 1.4; letter-spacing: -0.01em;">{subtitle}</p>
        </div>
        <hr style="border: none; height: 1px; background-color: #d2d2d7; margin: 25px 0 45px 0;">
    """, unsafe_allow_html=True)

def render_pagination(total_items, items_per_page, state_key, unique_position="bottom"):
    total_pages = max(1, (total_items - 1) // items_per_page + 1)
    if st.session_state[state_key] > total_pages: st.session_state[state_key] = total_pages
    current = st.session_state[state_key]
    
    if total_pages > 1:
        if unique_position == "bottom":
            st.write("---")
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        with col2:
            if st.button("← 上一页", key=f"prev_{state_key}_{unique_position}", disabled=(current == 1), use_container_width=True):
                st.session_state[state_key] -= 1; st.rerun()
        with col3:
            st.markdown(f"<div style='text-align: center; padding-top: 10px; color: #86868b; font-weight: 500;'>第 {current} / {total_pages} 页</div>", unsafe_allow_html=True)
        with col4:
            if st.button("下一页 →", key=f"next_{state_key}_{unique_position}", disabled=(current == total_pages), use_container_width=True):
                st.session_state[state_key] += 1; st.rerun()
        if unique_position == "top":
             st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    return (current - 1) * items_per_page, (current - 1) * items_per_page + items_per_page

# ==========================================
# 10. 双层安全隐形彩蛋页脚
# ==========================================
def render_apple_footer():
    jokes_pool = [
        "生物系学生在显微镜下观察了半天，激动地问老师：<br>『老师，这个黑乎乎、动来动去的是什么新细胞？』<br>老师看了一眼：『那是你的睫毛。』",
        "为什么程序员总是分不清万圣节和圣诞节？<br>因为 31 Oct == 25 Dec。",
        "世界上有 10 种人，<br>一种懂二进制，另一种不懂。",
        "做生信分析最大的错觉：<br>跑完这个 pipeline，我就能按时下班了。",
        "问：怎么用最快的方法得到一个随机的 DNA 序列？<br>答：让一个 C++ 程序员去写个指针越界。",
        "程序员被提 bug 后的标准反应：<br>『不可能啊，在我电脑上明明是好的！』",
        "医生：『你最近压力大吗？』<br>生信研究员：『不大呀，为什么这么问？』<br>医生：『因为你的心电图长得像 Python 报错栈。』"
    ]
    
    selected_jokes = random.sample(jokes_pool, 5)
    link_names = ["隐私政策", "使用条款", "销售政策", "法律信息", "网站地图"]
    
    modals_html = ""
    links_html = ""
    
    for i in range(5):
        modals_html += f"""
        <input type="checkbox" id="joke-modal-toggle-{i}" class="joke-toggle" style="display: none !important; position: absolute !important; opacity: 0 !important; visibility: hidden !important; width: 0 !important; height: 0 !important; pointer-events: none !important;">
        <div class="joke-modal">
            <div class="joke-modal-content">
                <div class="joke-title">暂未完成，不过写上感觉很好看！</div>
                <div style="color: #86868b; font-size: 14px; margin-bottom: 15px;">以表歉意，送你一个笑话：</div>
                <div class="joke-text">{selected_jokes[i]}</div>
                <label for="joke-modal-toggle-{i}" class="joke-close">我笑了，关闭</label>
            </div>
        </div>
        """
        separator = " &nbsp;|&nbsp; " if i < 4 else ""
        links_html += f'<label for="joke-modal-toggle-{i}" class="footer-link">{link_names[i]}</label>{separator}'

    st.markdown(f"""
        <style>
        .joke-toggle {{ display: none !important; visibility: hidden !important; }}
        .joke-modal {{
            display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: rgba(0, 0, 0, 0.4); z-index: 1000000;
            justify-content: center; align-items: center; backdrop-filter: blur(5px);
        }}
        .joke-toggle:checked + .joke-modal {{ display: flex; }}
        .joke-modal-content {{
            background: #ffffff; padding: 40px; border-radius: 20px; max-width: 450px; text-align: center; color: #1d1d1f;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2); transform: translateY(20px); animation: modalFadeIn 0.3s forwards;
        }}
        @keyframes modalFadeIn {{ to {{ transform: translateY(0); }} }}
        .joke-title {{ font-size: 20px; font-weight: 600; margin-bottom: 15px; color: #007aff; }}
        .joke-text {{ line-height: 1.6; font-size: 16px; font-weight: 500; margin-bottom: 30px; }}
        .joke-close {{ display: inline-block; padding: 10px 30px; background: #007aff; color: #fff; font-weight: 500; border-radius: 20px; cursor: pointer; transition: opacity 0.2s; }}
        .joke-close:hover {{ opacity: 0.8; }}
        </style>
        
        {modals_html}

        <div class="apple-footer-wrapper">
            <div class="apple-footer-content">
                <div style="margin-bottom: 10px;">
                    Copyright © 2026 BioPapers Inc. 保留所有权利。 
                    <span style="margin: 0 10px;">|</span> 
                    如有任何修改意见，欢迎发送邮件至 <a href="mailto:mozhanxuan@gmail.com">mozhanxuan@gmail.com</a>
                </div>
                <div>
                    {links_html}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ==========================================
# 11. 标题预加载与分流中心 (绝对防止闪烁)
# ==========================================
view_titles = {
    "about": ("BioPapers", "基于大模型的多模态生物医学文献深度解析平台。<br>全自动化：PubMed 实时抓取 ➔ 结构化解析 ➔ AI 深度阅读。"),
    "home": ("首页看板", "全系核心文献概览。探索最新科研动向与高影响力文章。"),
    "all_papers": ("全部论文", "浏览并检索系统收录的所有前沿医学文献。"),
    "history": ("浏览历史", "快速找回您最近查阅过的 AI 深度解析报告。"),
    "search": ("全局检索", "通过标题、期刊名或 PMID 极速定位文献。"),
    "detail": ("", "") 
}

h_title, h_subtitle = view_titles.get(st.session_state.current_view, ("", ""))

current_paper = None 
cover_html = "" 
content_md = "未找到该文献的 AI 深度解析文档。" 
h_subtitle_str = ""

if st.session_state.current_view == "detail":
    raw_title = st.session_state.selected_paper_title
    if raw_title:
        h_title = raw_title
        h_subtitle = "" 
        for p in papers:
            if safe_get(p, 'title') == raw_title:
                current_paper = p; break
        
        # 预加载详情页图片和数据
        if current_paper:
            pmid = safe_get(current_paper, 'pmid', '0')
            h_subtitle_str = f"PMID: {pmid} &nbsp;|&nbsp; 期刊: {safe_get(current_paper, 'journal', '未知')} &nbsp;|&nbsp; 日期: {safe_get(current_paper, 'pub_date', '近期')}"
            cover_html = get_card_image_html(pmid, height="260px", radius="14px")

        # 预加载 Markdown
        safe_title = re.sub(r'[\\/*?:"<>|]', "", str(raw_title)).replace('\n', ' ').replace('\r', '')[:150].strip()
        md_path = os.path.join(SUMMARIES_DIR, f"{safe_title}.md")
        if os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f: content_md = f.read()
            except Exception as e: content_md = f"读取解析报告失败: {e}"
else:
    h_title, h_subtitle = view_titles.get(st.session_state.current_view, ("", ""))

# 除了 about 和 detail，其他页面统一渲染大标题，彻底杜绝闪烁
if h_title and st.session_state.current_view not in ["about", "detail"]:
    render_apple_hero(h_title, h_subtitle)


# ==========================================
# 12. 主页面纯净内容分流
# ==========================================
if st.session_state.current_view == "about":
    bg_url = "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=1920&q=80"
    st.markdown(f"""
        <div class="apple-hero" style="width: 100%; height: 420px; background-image: url('{bg_url}'); background-size: cover; background-position: center; border-radius: 24px; position: relative; margin-bottom: 40px; box-shadow: 0 20px 40px rgba(0,0,0,0.15);">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0, 0, 0, 0.4); border-radius: 24px;"></div>
            <div style="position: absolute; bottom: 40px; left: 40px; color: #ffffff;">
                <h2 style="font-size: 36px; margin: 0 0 10px 0; font-weight: 700; letter-spacing: -0.01em;">全新工作流。</h2>
                <p style="font-size: 22px; margin: 0; font-weight: 500; opacity: 0.9;">探索学术世界的全新维度。</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    total_visits, daily_visits = track_and_get_visits()
    total_papers = len(papers) if papers else 0
    st.markdown(f"""
        <div class="apple-hero" style="display: flex; justify-content: space-around; padding: 40px; background: #ffffff; border-radius: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #e5e5ea;">
            <div style="text-align: center;"><div class="stat-number">{total_papers:,}</div><div class="stat-label">总收录论文数</div></div>
            <div style="text-align: center;"><div class="stat-number">{total_visits:,}</div><div class="stat-label">系统总访问量</div></div>
            <div style="text-align: center;"><div class="stat-number">{daily_visits:,}</div><div class="stat-label">今日实时访问</div></div>
        </div>
    """, unsafe_allow_html=True)

elif st.session_state.current_view == "home":
    if papers:
        st.markdown('<div class="apple-h2" style="margin-top: 0;">今日更新</div>', unsafe_allow_html=True)
        cols1 = st.columns(3)
        for i, paper in enumerate(papers[:3]):
            with cols1[i % 3]: render_paper_card(paper, "#bf4800", "最新收录", f"new_{i}")
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        st.markdown('<div class="apple-h2">1个月内高引论文</div>', unsafe_allow_html=True)
        # 🚀 修复2：修复 NoneType 报错，稳固锁定缓存
        if not st.session_state.home_cited_papers:
            st.session_state.home_cited_papers = random.sample(papers, min(3, len(papers))) if len(papers) >= 3 else papers
        
        cols2 = st.columns(3)
        for i, paper in enumerate(st.session_state.home_cited_papers[:3]):
            with cols2[i % 3]: render_paper_card(paper, "#007aff", "高引经典", f"cited_{i}")
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        st.markdown('<div class="apple-h2">全网热门阅读</div>', unsafe_allow_html=True)
        # 🚀 修复2：修复 NoneType 报错，稳固锁定缓存
        if not st.session_state.home_viewed_papers:
            st.session_state.home_viewed_papers = random.sample(papers, min(3, len(papers))) if len(papers) >= 3 else papers
            
        cols3 = st.columns(3)
        for i, paper in enumerate(st.session_state.home_viewed_papers[:3]):
            with cols3[i % 3]: render_paper_card(paper, "#e94057", "热门趋势", f"viewed_{i}")
    else: st.info("数据通道已就绪，目前数据库中暂无数据。")

# 列表页全部恢复左图右文结构
elif st.session_state.current_view == "all_papers":
    if papers:
        start_idx, end_idx = render_pagination(len(papers), 10, "page_all", unique_position="top")
        sorted_papers = sorted(papers, key=lambda x: str(safe_get(x, 'title', '')))
        for paper in sorted_papers[start_idx:end_idx]:
            pmid = safe_get(paper, 'pmid')
            with st.container(border=True):
                col_img, col_text, col_btn = st.columns([1.2, 4.8, 1])
                with col_img:
                    st.markdown(get_card_image_html(pmid, height="95px", radius="8px"), unsafe_allow_html=True)
                with col_text:
                    st.markdown(f"<div style='font-size: 20px; font-weight: 600; color: #1d1d1f; margin-bottom: 5px; line-height: 1.3;'>{safe_get(paper, 'title')}</div>", unsafe_allow_html=True)
                    st.caption(f"期刊: {safe_get(paper, 'journal', '未知')} | 日期: {safe_get(paper, 'pub_date', '近期')}")
                with col_btn:
                    st.write(""); st.write("") 
                    if st.button("深入了解 >", key=f"all_{pmid}", use_container_width=True):
                        st.session_state.selected_paper_title = safe_get(paper, 'title'); st.session_state.current_view = "detail"; st.rerun()
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        render_pagination(len(papers), 10, "page_all", unique_position="bottom")

elif st.session_state.current_view == "history":
    if st.session_state.view_history:
        if st.button("清空历史记录"): st.session_state.view_history = []; st.rerun()
        st.write(""); title_to_paper = {safe_get(p, 'title'): p for p in papers}
        for idx, title in enumerate(st.session_state.view_history):
            paper = title_to_paper.get(title)
            if paper:
                pmid = safe_get(paper, 'pmid')
                with st.container(border=True):
                    col_img, col_text, col_btn = st.columns([1.2, 4.8, 1])
                    with col_img:
                        st.markdown(get_card_image_html(pmid, height="95px", radius="8px"), unsafe_allow_html=True)
                    with col_text:
                        st.markdown(f"<div style='font-size: 20px; font-weight: 600; color: #1d1d1f; margin-bottom: 5px; line-height: 1.3;'>{title}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size: 13px; font-weight: 500; color: #bf4800;'>上次阅读于本次会话</div>", unsafe_allow_html=True)
                    with col_btn:
                        st.write(""); st.write("")
                        if st.button("继续阅读 >", key=f"hist_{pmid}_{idx}", use_container_width=True):
                            st.session_state.selected_paper_title = title; st.session_state.current_view = "detail"; st.rerun()
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

elif st.session_state.current_view == "search":
    search_query = st.text_input("输入检索词...", key="search_input")
    if search_query:
        query_lower = search_query.lower()
        search_results = [p for p in papers if query_lower in str(safe_get(p, 'title', '')).lower() or query_lower in str(safe_get(p, 'journal', '')).lower() or query_lower in str(safe_get(p, 'pmid', ''))]
        if search_results:
            st.success(f"共找到 {len(search_results)} 篇相关文献")
            start_idx, end_idx = render_pagination(len(search_results), 12, "page_search", unique_position="top")
            cols_s = st.columns(4)
            for i, paper in enumerate(search_results[start_idx:end_idx]):
                with cols_s[i % 4]: render_paper_card(paper, "#1d1d1f", "匹配结果", f"search_res_{safe_get(paper, 'pmid')}")
            render_pagination(len(search_results), 12, "page_search", unique_position="bottom")
        else: st.warning("未能找到相关文献。")

elif st.session_state.current_view == "detail":
    # 返回按钮
    col_back, _ = st.columns([1, 8])
    with col_back:
        if st.button("‹ 返回上页", use_container_width=True):
            st.session_state.current_view = "home"; st.session_state.selected_paper_title = None; st.rerun()
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # 详情页完美融合排版 (图与文)，标题使用渲染的 h_title 避免闪烁
    st.markdown(f"""
        <div class="apple-hero" style="background-color: #ffffff; padding: 45px 50px; border-radius: 20px; box-shadow: 0 4px 24px rgba(0,0,0,0.03); border: 1px solid #e5e5ea;">
            <div style="display: flex; gap: 40px; align-items: flex-start; margin-bottom: 35px;">
                <div style="width: 200px; flex-shrink: 0;">{cover_html}</div>
                <div style="flex-grow: 1; padding-top: 5px;">
                    <div style="font-size: 34px; font-weight: 700; color: #1d1d1f; line-height: 1.25; letter-spacing: -0.015em; margin-bottom: 16px;">
                        {h_title}
                    </div>
                    <div style="font-size: 14px; color: #86868b; font-weight: 500; display: inline-block; background: #f5f5f7; padding: 8px 16px; border-radius: 8px;">
                        {h_subtitle_str}
                    </div>
                </div>
            </div>
            <hr style="border: none; height: 1px; background-color: #e5e5ea; margin: 0 0 35px 0;">
            <div style="line-height: 1.8; font-size: 16px; color: #1d1d1f;">
                {content_md}
            </div>
        </div>
    """, unsafe_allow_html=True)

render_apple_footer()