"""
主程序入口
照片的故事 - 视觉引导式访谈与叙事生成系统
"""
import os
import sys
from typing import List, Optional, Dict
from PIL import Image

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.multimodal_analyzer import MultimodalAnalyzer
from src.dialogue_manager import DialogueManager
from src.context_manager import ContextManager
from src.story_generator import StoryGenerator
from src.evaluation_agent import EvaluationAgent


class PhotoStorySystem:
    """照片故事系统主类"""
    
    def __init__(self):
        """初始化系统"""
        self.analyzer = MultimodalAnalyzer()
        self.dialogue_manager = DialogueManager()
        self.context_manager = ContextManager()
        self.story_generator = StoryGenerator()
    
    def process_single_photo(
        self,
        image_path: str,
        photo_id: str = None
    ) -> Dict:
        """
        处理单张照片（单图深挖）
        
        Args:
            image_path: 图片路径
            photo_id: 照片ID（可选）
            
        Returns:
            包含分析、问答和故事的字典
        """
        if photo_id is None:
            photo_id = os.path.basename(image_path)
        
        print(f"正在分析照片: {photo_id}")
        
        # 1. 多模态分析
        analysis_result = self.analyzer.analyze_image(image_path=image_path)
        print("[完成] 照片分析完成")
        
        # 2. 开始对话
        initial_questions = self.dialogue_manager.start_dialogue(
            photo_id=photo_id,
            analysis_result=analysis_result
        )
        print(f"[完成] 生成了 {len(initial_questions)} 个初始问题")
        
        # 3. 交互式问答（这里简化，实际应该是用户输入）
        print("\n=== 访谈开始 ===")
        for i, question in enumerate(initial_questions, 1):
            print(f"\n问题 {i}: {question}")
            # 实际应用中，这里应该等待用户输入
            # answer = input("您的回答: ")
            # 为了演示，使用模拟回答
            answer = f"这是关于问题{i}的回答（模拟）"
            print(f"回答: {answer}")
            
            next_question = self.dialogue_manager.add_answer(question, answer)
            if next_question:
                print(f"\n追问: {next_question}")
                # 继续问答...
        
        # 4. 获取对话摘要
        dialogue_summary = self.dialogue_manager.get_dialogue_summary()
        
        # 5. 生成故事
        print("\n正在生成故事...")
        story = self.story_generator.generate_single_photo_story(
            photo_id=photo_id,
            analysis_result=analysis_result,
            qa_history=dialogue_summary['qa_history']
        )
        print("[完成] 故事生成完成")
        
        return {
            "photo_id": photo_id,
            "analysis": analysis_result,
            "dialogue": dialogue_summary,
            "story": story
        }
    
    def process_multiple_photos(
        self,
        image_paths: List[str],
        photo_ids: List[str] = None
    ) -> Dict:
        """
        处理多张照片（多图叙事链）
        
        Args:
            image_paths: 图片路径列表
            photo_ids: 照片ID列表（可选）
            
        Returns:
            包含所有照片信息和连贯故事的字典
        """
        if photo_ids is None:
            photo_ids = [os.path.basename(path) for path in image_paths]
        
        all_photo_records = []
        
        print(f"开始处理 {len(image_paths)} 张照片...\n")
        
        for idx, (image_path, photo_id) in enumerate(zip(image_paths, photo_ids), 1):
            print(f"\n{'='*50}")
            print(f"处理第 {idx} 张照片: {photo_id}")
            print(f"{'='*50}")
            
            # 1. 分析照片
            analysis_result = self.analyzer.analyze_image(image_path=image_path)
            
            # 2. 获取上下文（如果是第一张照片，上下文为空）
            context = None
            if idx > 1:
                context = self.context_manager.get_relevant_context(analysis_result)
                print(f"[完成] 获取到相关上下文: {len(context.get('previous_photos', []))} 条")
            
            # 3. 开始对话
            if idx == 1:
                # 第一张照片：生成初始问题
                questions = self.dialogue_manager.start_dialogue(
                    photo_id=photo_id,
                    analysis_result=analysis_result
                )
            else:
                # 后续照片：生成跨照片关联问题
                cross_question = self.context_manager.generate_cross_photo_question(
                    analysis_result
                )
                if cross_question:
                    questions = [cross_question]
                    self.dialogue_manager.start_dialogue(
                        photo_id=photo_id,
                        analysis_result=analysis_result
                    )
                else:
                    questions = self.dialogue_manager.start_dialogue(
                        photo_id=photo_id,
                        analysis_result=analysis_result
                    )
            
            # 4. 问答交互（简化版）
            print(f"\n生成了 {len(questions)} 个问题")
            for question in questions:
                print(f"\n问题: {question}")
                answer = f"关于{photo_id}的回答（模拟）"
                print(f"回答: {answer}")
                self.dialogue_manager.add_answer(question, answer)
            
            # 5. 保存到上下文
            dialogue_summary = self.dialogue_manager.get_dialogue_summary()
            self.context_manager.add_photo_dialogue(
                photo_id=photo_id,
                analysis_result=analysis_result,
                qa_history=dialogue_summary['qa_history']
            )
            
            # 6. 记录
            all_photo_records.append({
                "photo_id": photo_id,
                "analysis": analysis_result,
                "qa_history": dialogue_summary['qa_history']
            })
        
        # 7. 生成连贯故事
        print(f"\n{'='*50}")
        print("正在生成连贯故事...")
        print(f"{'='*50}")
        story = self.story_generator.generate_multi_photo_story(all_photo_records)
        print("✓ 故事生成完成\n")
        
        return {
            "photos": all_photo_records,
            "story": story,
            "timeline": self.context_manager.get_story_timeline()
        }
    
    def evaluate_system(
        self,
        test_images: List[str],
        persona_file: str = None
    ) -> Dict:
        """
        使用评估Agent评估系统
        
        Args:
            test_images: 测试图片路径列表
            persona_file: 人设文件路径
            
        Returns:
            评估结果
        """
        agent = EvaluationAgent(persona_file=persona_file)
        evaluation_results = []
        
        print("开始系统评估...\n")
        
        for image_path in test_images:
            print(f"评估照片: {image_path}")
            
            # 分析照片
            analysis = self.analyzer.analyze_image(image_path=image_path)
            
            # 生成问题
            questions = self.dialogue_manager.start_dialogue(
                photo_id=os.path.basename(image_path),
                analysis_result=analysis
            )
            
            # Agent评估
            eval_result = agent.evaluate_interview(questions, analysis)
            evaluation_results.append(eval_result)
            
            print(f"  - 问题数量: {eval_result['question_count']}")
            print(f"  - 回答质量: {eval_result['answer_quality']:.2f}")
            print(f"  - 相关性: {eval_result['relevance']:.2f}")
            print(f"  - 深度: {eval_result['depth']:.2f}\n")
        
        # 计算平均指标
        avg_metrics = {
            "avg_answer_quality": sum(r['answer_quality'] for r in evaluation_results) / len(evaluation_results),
            "avg_relevance": sum(r['relevance'] for r in evaluation_results) / len(evaluation_results),
            "avg_depth": sum(r['depth'] for r in evaluation_results) / len(evaluation_results)
        }
        
        return {
            "individual_results": evaluation_results,
            "average_metrics": avg_metrics
        }


def main():
    """主函数"""
    print("="*60)
    print("照片的故事 - 视觉引导式访谈与叙事生成系统")
    print("="*60)
    print()
    
    # 初始化系统
    system = PhotoStorySystem()
    
    # 示例：处理单张照片
    # 注意：需要提供实际的图片路径
    # result = system.process_single_photo("path/to/photo.jpg")
    # print("\n生成的故事:")
    # print(result['story'])
    
    # 示例：处理多张照片
    # results = system.process_multiple_photos([
    #     "path/to/photo1.jpg",
    #     "path/to/photo2.jpg"
    # ])
    # print("\n生成的连贯故事:")
    # print(results['story'])
    
    print("\n系统已就绪！")
    print("请修改main.py中的示例代码，提供实际的图片路径来运行。")
    print("\n使用说明:")
    print("1. 配置config.py中的混元API密钥")
    print("2. 安装依赖: pip install -r requirements.txt")
    print("3. 运行: python main.py")


if __name__ == "__main__":
    main()
