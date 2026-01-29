"""
主程序入口
照片的故事 - 视觉引导式访谈与叙事生成系统
运行 python main.py 进入交互式流程：选模式 → 选图 → 分析 → 访谈 → 生成故事
"""
import os
import sys
from typing import List, Optional, Dict

# 添加项目根目录与 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.multimodal_analyzer import MultimodalAnalyzer
from src.dialogue_manager import DialogueManager
from src.context_manager import ContextManager
from src.story_generator import StoryGenerator, NARRATIVE_STYLES
from src.evaluation_agent import EvaluationAgent


class PhotoStorySystem:
    """照片故事系统：支持程序式调用与完整交互式流程"""
    
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

    # ---------- 交互式流程（运行 python main.py 时使用）----------

    def select_mode(self) -> str:
        """选择使用模式：单图深挖 / 多图叙事链"""
        print("\n" + "="*60)
        print("请选择使用模式")
        print("="*60)
        print("\n  1. 单图深挖")
        print("     围绕一张照片挖掘完整故事：分析 → 访谈 → 生成该照片的故事。")
        print("\n  2. 多图叙事链")
        print("     基于上一张照片的访谈上下文，结合新照片连续追问，串联跨越时间的人生故事，最后生成一篇连贯的多图故事。")
        print("-"*60)
        while True:
            try:
                choice = input("\n请选择 (1 或 2): ").strip()
                if choice == "1":
                    return "single"
                if choice == "2":
                    return "multi"
            except Exception:
                pass
            print("[错误] 请输入 1 或 2。")

    def select_image(self) -> Optional[str]:
        """选择图片（test_images 或自定义路径）"""
        print("\n" + "="*60)
        print("步骤1: 选择照片")
        print("="*60)
        test_dir = "test_images"
        available_images = []
        if os.path.exists(test_dir):
            for f in os.listdir(test_dir):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                    available_images.append(os.path.join(test_dir, f))
        if available_images:
            print(f"\n找到 {len(available_images)} 张图片：")
            for i, img in enumerate(available_images, 1):
                print(f"  {i}. {os.path.basename(img)}")
            print(f"  {len(available_images) + 1}. 输入自定义路径")
            try:
                choice = input(f"\n请选择图片 (1-{len(available_images) + 1}): ").strip()
                n = int(choice)
                if 1 <= n <= len(available_images):
                    return available_images[n - 1]
                if n == len(available_images) + 1:
                    path = input("请输入图片路径: ").strip()
                    return path if os.path.exists(path) else None
            except ValueError:
                pass
            return None
        print("\n未找到预设图片，请输入图片路径：")
        path = input("图片路径: ").strip()
        return path if os.path.exists(path) else None

    def analyze_photo(self, image_path: str) -> Dict:
        """分析照片并打印摘要"""
        print("\n" + "="*60)
        print("步骤2: 分析照片")
        print("="*60)
        print(f"\n正在分析: {os.path.basename(image_path)}")
        print("这可能需要30-120秒，请稍候...")
        result = self.analyzer.analyze_image(image_path=image_path)
        print("\n[完成] 照片分析完成！")
        print("\n分析结果摘要：")
        print("-"*60)
        if isinstance(result, dict):
            if result.get('overall_description'):
                print((result['overall_description'] or '')[:200] + "...")
            if result.get('visual_elements'):
                print(str(result['visual_elements'])[:200] + "...")
        else:
            print(str(result)[:300] + "...")
        print("-"*60)
        return result

    def conduct_interview(
        self,
        photo_id: str,
        analysis_result: Dict,
        initial_questions: Optional[List[str]] = None
    ) -> List[Dict]:
        """进行访谈对话；initial_questions 不为 None 时使用该问题列表（多图跨图问题）"""
        questions = self.dialogue_manager.start_dialogue(
            photo_id=photo_id, analysis_result=analysis_result
        )
        if initial_questions is not None:
            questions = initial_questions
        print("\n" + "="*60)
        print("步骤3: 访谈对话")
        print("="*60)
        print("\n系统将根据照片分析结果，向您提问一些问题。")
        print("请根据照片内容，如实回答这些问题。")
        print("输入 'skip' 跳过当前问题，'done' 提前结束访谈")
        print("-"*60)
        print(f"\n生成了 {len(questions)} 个问题，让我们开始吧！\n")
        qa_history = []
        for i, q in enumerate(questions):
            print(f"【问题 {i + 1}/{len(questions)}】")
            print("-"*60)
            print(q)
            print("-"*60)
            answer = input("\n您的回答: ").strip()
            if answer.lower() == 'done':
                print("\n[提示] 您选择提前结束访谈")
                break
            if answer.lower() == 'skip':
                continue
            if not answer:
                print("[提示] 回答不能为空，请重新输入")
                continue
            qa_history.append({"question": q, "answer": answer})
            next_q = self.dialogue_manager.add_answer(q, answer)
            if next_q:
                print(f"\n【追问】\n" + "-"*60 + "\n" + next_q + "\n" + "-"*60)
                follow = input("\n您的回答: ").strip()
                if follow.lower() == 'done':
                    break
                if follow.lower() != 'skip' and follow:
                    qa_history.append({"question": next_q, "answer": follow})
                    self.dialogue_manager.add_answer(next_q, follow)
        print(f"\n[完成] 访谈结束，共收集了 {len(qa_history)} 组问答")
        return qa_history

    def generate_story(
        self,
        photo_id: str,
        analysis_result: Dict,
        qa_history: List[Dict],
        narrative_style: str = "personal"
    ) -> str:
        """生成单图故事（第一人称叙事）"""
        print("\n" + "="*60)
        print("步骤4: 生成故事")
        print("="*60)
        print("\n叙事风格：第一人称个人叙事")
        print("正在根据照片分析和访谈内容生成故事...")
        print("这可能需要30-60秒，请稍候...")
        story = self.story_generator.generate_single_photo_story(
            photo_id=photo_id,
            analysis_result=analysis_result,
            qa_history=qa_history,
            narrative_style=narrative_style
        )
        print("\n[完成] 故事生成完成！")
        return story

    def display_result(
        self,
        photo_id: str,
        analysis_result: Dict,
        qa_history: List[Dict],
        story: str,
        narrative_style: Optional[str] = None
    ) -> None:
        """显示最终结果并询问是否保存"""
        print("\n" + "="*60)
        print("最终结果")
        print("="*60)
        print(f"\n【照片】: {photo_id}")
        if narrative_style and narrative_style in NARRATIVE_STYLES:
            print(f"【叙事风格】: {NARRATIVE_STYLES[narrative_style]['name']}")
        print(f"\n【访谈记录】: {len(qa_history)} 组问答")
        print("\n【生成的故事】:")
        print("="*60)
        print(story)
        print("="*60)
        if input("\n是否保存结果到文件？(y/n): ").strip().lower() == 'y':
            self.save_result(photo_id, analysis_result, qa_history, story, narrative_style)

    def save_result(
        self,
        photo_id: str,
        analysis_result: Dict,
        qa_history: List[Dict],
        story: str,
        narrative_style: Optional[str] = None
    ) -> None:
        """保存结果到文件"""
        safe_name = photo_id.replace('/', '_').replace('\\', '_')
        filename = f"photo_story_{safe_name}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("="*60 + "\n照片故事生成结果\n" + "="*60 + "\n\n")
            f.write(f"照片: {photo_id}\n")
            if narrative_style and narrative_style in NARRATIVE_STYLES:
                f.write(f"叙事风格: {NARRATIVE_STYLES[narrative_style]['name']}\n")
            f.write("\n【照片分析】\n" + "-"*60 + "\n")
            if isinstance(analysis_result, dict):
                for k, v in analysis_result.items():
                    f.write(f"{k}: {v}\n")
            else:
                f.write(str(analysis_result) + "\n")
            f.write("-"*60 + "\n\n【访谈记录】\n" + "-"*60 + "\n")
            for i, qa in enumerate(qa_history, 1):
                f.write(f"\n问题 {i}: {qa['question']}\n回答: {qa['answer']}\n")
            f.write("-"*60 + "\n\n【生成的故事】\n" + "="*60 + "\n" + story + "\n" + "="*60 + "\n")
        print(f"\n[已保存] 结果已保存到: {filename}")

    def run_single_flow(self) -> None:
        """单图深挖：一张照片 → 分析 → 访谈 → 生成故事"""
        print("\n" + "="*60 + "\n模式：单图深挖\n" + "="*60)
        image_path = self.select_image()
        if not image_path:
            print("\n[错误] 未选择有效图片，退出")
            return
        photo_id = os.path.basename(image_path)
        try:
            analysis_result = self.analyze_photo(image_path)
        except Exception as e:
            print(f"\n[错误] 照片分析失败: {e}")
            import traceback
            traceback.print_exc()
            return
        try:
            qa_history = self.conduct_interview(photo_id, analysis_result)
        except Exception as e:
            print(f"\n[错误] 访谈过程出错: {e}")
            import traceback
            traceback.print_exc()
            qa_history = []
        narrative_style = "personal"
        try:
            story = self.generate_story(
                photo_id, analysis_result, qa_history, narrative_style=narrative_style
            )
        except Exception as e:
            print(f"\n[错误] 故事生成失败: {e}")
            import traceback
            traceback.print_exc()
            story = "故事生成失败，请稍后重试。"
        self.display_result(
            photo_id, analysis_result, qa_history, story, narrative_style=narrative_style
        )
        print("\n" + "="*60 + "\n流程完成！感谢使用！\n" + "="*60)

    def run_multi_flow(self) -> None:
        """多图叙事链：多张照片 → 每张分析+访谈（结合上一张）→ 生成连贯故事"""
        print("\n" + "="*60 + "\n模式：多图叙事链\n" + "="*60)
        print("\n请依次添加照片，系统会结合上一张的访谈内容对新照片连续追问。")
        print("至少添加 2 张照片后可选择「完成并生成多图故事」。\n")
        self.context_manager.clear()
        all_photo_records = []
        while True:
            print("\n" + "-"*60)
            if len(all_photo_records) >= 2:
                print("  1. 添加一张照片\n  2. 完成并生成多图故事")
            else:
                print(f"  1. 添加一张照片（当前 {len(all_photo_records)} 张，至少需 2 张才能生成多图故事）")
            print("-"*60)
            choice = input("\n请选择 (1 或 2): ").strip()
            if choice == "2":
                if len(all_photo_records) < 2:
                    print("\n[提示] 至少需要 2 张照片，请先添加照片。")
                    continue
                break
            if choice != "1":
                print("[错误] 请输入 1 或 2。")
                continue
            image_path = self.select_image()
            if not image_path:
                continue
            photo_id = os.path.basename(image_path)
            idx = len(all_photo_records) + 1
            try:
                analysis_result = self.analyze_photo(image_path)
            except Exception as e:
                print(f"\n[错误] 照片分析失败: {e}")
                import traceback
                traceback.print_exc()
                continue
            if idx == 1:
                questions = self.dialogue_manager.start_dialogue(
                    photo_id=photo_id, analysis_result=analysis_result
                )
            else:
                cross_q = self.context_manager.generate_cross_photo_question(analysis_result)
                questions = self.dialogue_manager.start_dialogue(
                    photo_id=photo_id, analysis_result=analysis_result
                )
                if cross_q and cross_q.strip():
                    questions = [cross_q]
            try:
                qa_history = self.conduct_interview(
                    photo_id, analysis_result, initial_questions=questions
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                qa_history = []
            summary = self.dialogue_manager.get_dialogue_summary()
            qa_history = summary.get("qa_history", qa_history)
            self.context_manager.add_photo_dialogue(
                photo_id=photo_id, analysis_result=analysis_result, qa_history=qa_history
            )
            all_photo_records.append({
                "photo_id": photo_id,
                "analysis": analysis_result,
                "qa_history": qa_history,
            })
            print(f"\n[完成] 第 {idx} 张照片已加入叙事链，共 {len(all_photo_records)} 张。")
        print("\n" + "="*60 + "\n正在生成多图连贯故事...\n" + "="*60)
        print("叙事风格：第一人称个人叙事\n这可能需要 30–60 秒，请稍候...\n")
        try:
            story = self.story_generator.generate_multi_photo_story(all_photo_records)
        except Exception as e:
            print(f"\n[错误] 故事生成失败: {e}")
            import traceback
            traceback.print_exc()
            story = "多图故事生成失败，请稍后重试。"
        print("\n[完成] 故事生成完成！")
        print("\n" + "="*60 + "\n最终结果（多图叙事链）\n" + "="*60)
        print("\n【照片序列】:", ", ".join(r["photo_id"] for r in all_photo_records))
        print("【叙事风格】: 个人叙事风格\n【生成的故事】:\n" + "="*60)
        print(story)
        print("="*60)
        if input("\n是否保存结果到文件？(y/n): ").strip().lower() == "y":
            safe_name = "multi_" + "_".join(
                r["photo_id"].replace("/", "_").replace("\\", "_")
                for r in all_photo_records[:3]
            )
            if len(all_photo_records) > 3:
                safe_name += "_etc"
            filename = f"photo_story_{safe_name}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("="*60 + "\n多图叙事链 - 照片故事生成结果\n" + "="*60 + "\n\n")
                f.write("照片序列: " + ", ".join(r["photo_id"] for r in all_photo_records) + "\n\n")
                f.write("【生成的故事】\n" + "="*60 + "\n" + story + "\n" + "="*60 + "\n")
            print(f"\n[已保存] 结果已保存到: {filename}")
        print("\n" + "="*60 + "\n流程完成！感谢使用！\n" + "="*60)

    def run(self) -> None:
        """运行完整交互式流程：选模式 → 单图深挖 或 多图叙事链"""
        print("\n" + "="*60)
        print("照片的故事 - 交互式系统")
        print("="*60)
        print("\n欢迎使用照片故事生成系统！")
        print("系统将帮助您：分析照片 → 访谈对话 → 生成图文并茂的照片故事。")
        print("="*60)
        mode = self.select_mode()
        if mode == "single":
            self.run_single_flow()
        else:
            self.run_multi_flow()


def main():
    """主函数：直接运行即进入交互式流程，便于调试"""
    system = PhotoStorySystem()
    system.run()


if __name__ == "__main__":
    main()
