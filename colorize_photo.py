
"""
老照片自动上色脚本
使用 Zhang et al. 的 ECCV16/SIGGRAPH17 深度学习上色模型 (PyTorch)
"""
import os
import numpy as np
from PIL import Image
import torch
from torchvision import transforms

# ─── 配置 ───
INPUT_IMAGE = r"照片数据库/纺织厂女工.png"
OUTPUT_IMAGE = r"照片数据库/纺织厂女工_上色版.png"


def load_image(path):
    """加载图片并转为 LAB 空间"""
    img = Image.open(path).convert("RGB")
    return img


def colorize_with_eccv16():
    """使用 ECCV16 模型上色"""
    print("=" * 50)
    print("  🎨 老照片 AI 自动上色工具")
    print("=" * 50)
    print(f"\n输入: {INPUT_IMAGE}")
    print(f"输出: {OUTPUT_IMAGE}")
    
    # 1. 加载模型 (自动从 GitHub 下载权重)
    print("\n🧠 第1步: 加载上色模型 (首次会自动下载权重)...")
    try:
        model = torch.hub.load(
            'richzhang/colorization', 
            'eccv16',
            pretrained=True,
            verbose=False
        )
    except Exception as e:
        print(f"  eccv16 加载失败: {e}")
        print("  尝试 siggraph17 模型...")
        model = torch.hub.load(
            'richzhang/colorization', 
            'siggraph17',
            pretrained=True,
            verbose=False
        )
    
    model.eval()
    print("  ✓ 模型加载成功!")
    
    # 2. 读取图像
    print("\n🖼️ 第2步: 读取图像...")
    from skimage import color
    img = np.array(Image.open(INPUT_IMAGE).convert("RGB"))
    h, w = img.shape[:2]
    print(f"  原始尺寸: {w} x {h}")
    
    # 转 LAB
    img_lab = color.rgb2lab(img / 255.0)  # (H, W, 3)
    img_l = img_lab[:, :, 0]  # L 通道
    
    # 3. 预处理
    print("\n🎨 第3步: AI 上色推理中...")
    # 模型期望输入: L 通道, 缩放到 256x256
    img_l_resized = np.resize(img_l, (1, 1, 256, 256))
    
    # 使用 PIL 更好地 resize
    from PIL import Image as PILImage
    l_pil = PILImage.fromarray(img_l.astype(np.float32), mode='F')
    l_resized = l_pil.resize((256, 256), PILImage.BILINEAR)
    l_np = np.array(l_resized)
    
    tens_l = torch.from_numpy(l_np).unsqueeze(0).unsqueeze(0).float()
    
    # 4. 推理
    with torch.no_grad():
        ab_pred = model(tens_l).cpu()  # (1, 2, 256, 256)
    
    # 5. 后处理
    print("\n✨ 第4步: 合成彩色图像...")
    ab_pred_np = ab_pred.squeeze(0).numpy().transpose(1, 2, 0)  # (256, 256, 2)
    
    # resize 回原尺寸
    from PIL import Image as PILImg2
    ab_a = PILImg2.fromarray(ab_pred_np[:, :, 0].astype(np.float32), mode='F').resize((w, h), PILImg2.BILINEAR)
    ab_b = PILImg2.fromarray(ab_pred_np[:, :, 1].astype(np.float32), mode='F').resize((w, h), PILImg2.BILINEAR)
    
    # 合成 LAB 图像
    result_lab = np.zeros((h, w, 3))
    result_lab[:, :, 0] = img_l
    result_lab[:, :, 1] = np.array(ab_a)
    result_lab[:, :, 2] = np.array(ab_b)
    
    # 转回 RGB
    result_rgb = color.lab2rgb(result_lab)
    result_rgb = (np.clip(result_rgb, 0, 1) * 255).astype(np.uint8)
    
    # 增强饱和度
    from PIL import ImageEnhance
    result_pil = Image.fromarray(result_rgb)
    enhancer = ImageEnhance.Color(result_pil)
    result_pil = enhancer.enhance(1.3)  # 增强 30%
    
    # 6. 保存
    result_pil.save(OUTPUT_IMAGE)
    print(f"\n✅ 上色完成! 保存到: {OUTPUT_IMAGE}")
    print(f"  文件大小: {os.path.getsize(OUTPUT_IMAGE)/1024:.0f} KB")
    
    print("\n" + "=" * 50)
    print("  🎉 大功告成！请查看上色后的照片")
    print("=" * 50)
    return True


if __name__ == "__main__":
    # 先检查是否有 skimage
    try:
        from skimage import color
    except ImportError:
        print("安装 scikit-image...")
        import subprocess
        subprocess.check_call(["pip", "install", "scikit-image"])
    
    colorize_with_eccv16()
