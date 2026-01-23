"""
示例代码：如何使用照片故事系统
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import PhotoStorySystem


def demo_single_photo():
    """单图深挖示例"""
    print("="*60)
    print("示例1: 单图深挖")
    print("="*60)
    
    system = PhotoStorySystem()
    
    # 替换为实际的图片路径
    image_path = "path/to/your/photo.jpg"
    
    if os.path.exists(image_path):
        result = system.process_single_photo(image_path)
        
        print("\n" + "="*60)
        print("生成的故事:")
        print("="*60)
        print(result['story'])
    else:
        print(f"请提供有效的图片路径: {image_path}")


def demo_multiple_photos():
    """多图叙事链示例"""
    print("="*60)
    print("示例2: 多图叙事链")
    print("="*60)
    
    system = PhotoStorySystem()
    
    # 替换为实际的图片路径列表
    image_paths = [
        "path/to/photo1.jpg",
        "path/to/photo2.jpg",
        "path/to/photo3.jpg"
    ]
    
    # 检查文件是否存在
    valid_paths = [p for p in image_paths if os.path.exists(p)]
    
    if valid_paths:
        results = system.process_multiple_photos(valid_paths)
        
        print("\n" + "="*60)
        print("生成的连贯故事:")
        print("="*60)
        print(results['story'])
    else:
        print("请提供有效的图片路径")


def demo_evaluation():
    """评估示例"""
    print("="*60)
    print("示例3: 系统评估")
    print("="*60)
    
    system = PhotoStorySystem()
    
    # 替换为实际的测试图片路径
    test_images = [
        "path/to/test_photo1.jpg",
        "path/to/test_photo2.jpg"
    ]
    
    valid_images = [p for p in test_images if os.path.exists(p)]
    
    if valid_images:
        eval_results = system.evaluate_system(valid_images)
        
        print("\n" + "="*60)
        print("评估结果:")
        print("="*60)
        print(f"平均回答质量: {eval_results['average_metrics']['avg_answer_quality']:.2f}")
        print(f"平均相关性: {eval_results['average_metrics']['avg_relevance']:.2f}")
        print(f"平均深度: {eval_results['average_metrics']['avg_depth']:.2f}")
    else:
        print("请提供有效的测试图片路径")


if __name__ == "__main__":
    print("照片的故事系统 - 使用示例\n")
    
    # 运行示例（取消注释以运行）
    # demo_single_photo()
    # demo_multiple_photos()
    # demo_evaluation()
    
    print("\n请取消注释上面的函数调用来运行示例。")
    print("记得先配置config.py中的API密钥，并提供实际的图片路径。")
