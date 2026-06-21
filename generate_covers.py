import os
import fitz  # PyMuPDF

def pdf_to_cover(pdf_path, cover_path):
    try:
        # 打开 PDF 文件
        doc = fitz.open(pdf_path)
        # 获取第一页
        page = doc[0]
        # 将第一页渲染成图片 (dpi=150 清晰度足够且体积小)
        pix = page.get_pixmap(dpi=150)
        # 保存为 PNG 图片
        pix.save(cover_path)
        print(f"[成功] 已为 {os.path.basename(pdf_path)} 生成封面")
    except Exception as e:
        print(f"[错误] 无法为 {os.path.basename(pdf_path)} 生成封面，原因: {e}")

def batch_generate_covers():
    pdf_dir = "data/pdfs"
    assets_dir = "assets"
    
    # 确保 assets 文件夹存在
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    # 遍历 pdfs 文件夹
    for file in os.listdir(pdf_dir):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, file)
            # 用 PDF 的文件名（去掉扩展名）加上 .png 作为封面文件名
            cover_name = file.replace(".pdf", ".png")
            cover_path = os.path.join(assets_dir, cover_name)
            
            # 如果封面已经存在，就不重复生成了
            if not os.path.exists(cover_path):
                pdf_to_cover(pdf_path, cover_path)

if __name__ == "__main__":
    batch_generate_covers()