import os
import urllib.request
from loguru import logger

# 启用维基媒体底层核心路由 (Special:FilePath) - 自动重定向真实地址，彻底告别 404！
IMAGES = {
    # 巨幕背景图 (bg.jpg)：绝美深色系荧光神经元网络
    "bg.jpg": "https://commons.wikimedia.org/wiki/Special:FilePath/Neuron_-_fluorescent.jpg",
    
    # 卡片图 1：经典 DNA 双螺旋 (透明背景 PNG)
    "1.jpg": "https://commons.wikimedia.org/wiki/Special:FilePath/B-DNA_Spacefilled_Side_View.png",
    
    # 卡片图 2：显微镜下的 T 细胞与抗原激活 (科研感极强)
    "2.jpg": "https://commons.wikimedia.org/wiki/Special:FilePath/T_cell_activation.png",
    
    # 卡片图 3：大肠杆菌高倍电子显微镜扫描图 (黑白高对比度)
    "3.jpg": "https://commons.wikimedia.org/wiki/Special:FilePath/EscherichiaColi_NIAID.jpg",
    
    # 卡片图 4：肌红蛋白 3D 丝带折叠模型
    "4.jpg": "https://commons.wikimedia.org/wiki/Special:FilePath/Myoglobin.png",
    
    # 卡片图 5：实验室人类细胞系切片 (HEK 293T)
    "5.jpg": "https://commons.wikimedia.org/wiki/Special:FilePath/HEK_293T_cells.jpg"
}

def download_images():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    logger.info(f"正在通过 Wikimedia 核心路由精准拉取科研大图至: {assets_dir}")
    
    # 基础伪装头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for filename, url in IMAGES.items():
        filepath = os.path.join(assets_dir, filename)
        try:
            req = urllib.request.Request(url, headers=headers)
            # Python 的 urlopen 会自动处理 302 重定向，直接抓取到深层原图
            with urllib.request.urlopen(req, timeout=20) as response:
                with open(filepath, 'wb') as out_file:
                    out_file.write(response.read())
            logger.success(f"✅ 成功追踪并获取: {filename}")
        except Exception as e:
            logger.error(f"❌ 下载 {filename} 失败: {e}")

if __name__ == "__main__":
    download_images()