"""
交互式照片故事生成系统
完整的用户体验流程：上传图片 -> 分析 -> 对话 -> 生成故事
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from main import PhotoStorySystem
from src.multimodal_analyzer import MultimodalAnalyzer
from src.dialogue_manager import DialogueManager
from src.context_manager import ContextManager
from src.story_generator import StoryGenerator, NARRATIVE_STYLES


class InteractivePhotoStory:
    """交互式照片故事系统：支持单图深挖与多图叙事链两种模式"""
    
    def __init__(self):
        """初始化系统"""
        self.system = PhotoStorySystem()
        self.analyzer = MultimodalAnalyzer()
        self.dialogue_manager = DialogueManager()
        self.context_manager = ContextManager()
        self.story_generator = StoryGenerator()
    
    def select_mode(self):
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
    
    def select_image(self):
        """选择图片"""
        print("\n" + "="*60)
        print("步骤1: 选择照片")
        print("="*60)
        
        # 查找test_images目录中的图片
        test_dir = "test_images"
        available_images = []
        
        if os.path.exists(test_dir):
            for file in os.listdir(test_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                    available_images.append(os.path.join(test_dir, file))
        
        if available_images:
            print(f"\n找到 {len(available_images)} 张图片：")
            for i, img in enumerate(available_images, 1):
                print(f"  {i}. {os.path.basename(img)}")
            print(f"  {len(available_images) + 1}. 输入自定义路径")
            
            try:
                choice = input(f"\n请选择图片 (1-{len(available_images) + 1}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(available_images):
                    return available_images[choice_num - 1]
                elif choice_num == len(available_images) + 1:
                    custom_path = input("请输入图片路径: ").strip()
                    if os.path.exists(custom_path):
                        return custom_path
                    else:
                        print(f"[错误] 文件不存在: {custom_path}")
                        return None
                else:
                    print("[错误] 无效选择")
                    return None
            except ValueError:
                print("[错误] 请输入数字")
                return None
        else:
            print("\n未找到预设图片，请输入图片路径：")
            custom_path = input("图片路径: ").strip()
            if os.path.exists(custom_path):
                return custom_path
            else:
                print(f"[错误] 文件不存在: {custom_path}")
                return None
    
    def analyze_photo(self, image_path):
        """分析照片"""
        print("\n" + "="*60)
        print("步骤2: 分析照片")
        print("="*60)
        print(f"\n正在分析: {os.path.basename(image_path)}")
        print("这可能需要30-120秒，请稍候...")
        
        analysis_result = self.analyzer.analyze_image(image_path=image_path)
        
        print("\n[完成] 照片分析完成！")
        print("\n分析结果摘要：")
        print("-"*60)
        if isinstance(analysis_result, dict):
            if 'overall_description' in analysis_result:
                print(f"整体描述: {analysis_result['overall_description'][:200]}...")
            if 'visual_elements' in analysis_result:
                print(f"视觉元素: {analysis_result['visual_elements'][:200]}...")
        else:
            print(str(analysis_result)[:300] + "...")
        print("-"*60)
        
        return analysis_result
    
    def conduct_interview(self, photo_id, analysis_result, initial_questions=None):
        """进行访谈对话。initial_questions 为 None 时由系统生成；多图模式下可传入跨图关联问题列表。"""
        # 先生成问题，再一起展示说明与第一个问题
        questions = self.dialogue_manager.start_dialogue(photo_id=photo_id, analysis_result=analysis_result)
        if initial_questions is not None:
            questions = initial_questions
        
        print("\n" + "="*60)
        print("步骤3: 访谈对话")
        print("="*60)
        print("\n系统将根据照片分析结果，向您提问一些问题。")
        print("请根据照片内容，如实回答这些问题。")
        print("输入 'skip' 可以跳过当前问题")
        print("输入 'done' 可以提前结束访谈")
        print("-"*60)
        print(f"\n生成了 {len(questions)} 个问题，让我们开始吧！\n")
        
        qa_history = []
        question_index = 0
        
        while question_index < len(questions):
            question = questions[question_index]
            
            print(f"【问题 {question_index + 1}/{len(questions)}】")
            print("-"*60)
            print(question)
            print("-"*60)
            
            # 获取用户回答
            answer = input("\n您的回答: ").strip()
            
            if answer.lower() == 'done':
                print("\n[提示] 您选择提前结束访谈")
                break
            elif answer.lower() == 'skip':
                print("[跳过] 跳过当前问题")
                question_index += 1
                continue
            elif not answer:
                print("[提示] 回答不能为空，请重新输入")
                continue
            
            # 记录问答
            qa_history.append({
                "question": question,
                "answer": answer
            })
            
            # 添加到对话管理器
            next_question = self.dialogue_manager.add_answer(question, answer)
            
            # 如果有追问，继续提问
            if next_question:
                print(f"\n【追问】")
                print("-"*60)
                print(next_question)
                print("-"*60)
                
                followup_answer = input("\n您的回答: ").strip()
                
                if followup_answer.lower() == 'done':
                    print("\n[提示] 您选择提前结束访谈")
                    break
                elif followup_answer.lower() == 'skip':
                    print("[跳过] 跳过追问")
                elif followup_answer:
                    qa_history.append({
                        "question": next_question,
                        "answer": followup_answer
                    })
                    self.dialogue_manager.add_answer(next_question, followup_answer)
            
            question_index += 1
        
        print(f"\n[完成] 访谈结束，共收集了 {len(qa_history)} 组问答")
        
        return qa_history
    
    def generate_story(self, photo_id, analysis_result, qa_history, narrative_style="personal"):
        """生成故事（默认第一人称叙事风格）"""
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
    
    def display_result(self, photo_id, analysis_result, qa_history, story, narrative_style=None):
        """显示最终结果（可显示所选叙事风格）"""
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
        
        # 询问是否保存
        save_choice = input("\n是否保存结果到文件？(y/n): ").strip().lower()
        if save_choice == 'y':
            self.save_result(photo_id, analysis_result, qa_history, story, narrative_style)
    
    def save_result(self, photo_id, analysis_result, qa_history, story, narrative_style=None):
        """保存结果到文件（可含叙事风格）"""
        safe_name = photo_id.replace('/', '_').replace('\\', '_')
        filename = f"photo_story_{safe_name}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write("照片故事生成结果\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"照片: {photo_id}\n")
            if narrative_style and narrative_style in NARRATIVE_STYLES:
                f.write(f"叙事风格: {NARRATIVE_STYLES[narrative_style]['name']}\n")
            f.write("\n")
            
            f.write("【照片分析】\n")
            f.write("-"*60 + "\n")
            if isinstance(analysis_result, dict):
                for key, value in analysis_result.items():
                    f.write(f"{key}: {value}\n")
            else:
                f.write(str(analysis_result) + "\n")
            f.write("-"*60 + "\n\n")
            
            f.write("【访谈记录】\n")
            f.write("-"*60 + "\n")
            for i, qa in enumerate(qa_history, 1):
                f.write(f"\n问题 {i}: {qa['question']}\n")
                f.write(f"回答: {qa['answer']}\n")
            f.write("-"*60 + "\n\n")
            
            f.write("【生成的故事】\n")
            f.write("="*60 + "\n")
            f.write(story + "\n")
            f.write("="*60 + "\n")
        
        print(f"\n[已保存] 结果已保存到: {filename}")
    
    def run_single_flow(self):
        """单图深挖：一张照片 → 分析 → 访谈 → 生成故事"""
        print("\n" + "="*60)
        print("模式：单图深挖")
        print("="*60)
        
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
            if not qa_history:
                print("\n[提示] 没有收集到问答记录，将使用空记录生成故事")
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
        print("\n" + "="*60)
        print("流程完成！感谢使用！")
        print("="*60)
    
    def run_multi_flow(self):
        """多图叙事链：多张照片 → 每张分析+访谈（结合上一张上下文）→ 生成连贯故事"""
        print("\n" + "="*60)
        print("模式：多图叙事链")
        print("="*60)
        print("\n请依次添加照片，系统会结合上一张的访谈内容对新照片进行连续追问。")
        print("至少添加 2 张照片后可选择「完成并生成多图故事」。\n")
        
        self.context_manager.clear()
        all_photo_records = []
        
        while True:
            print("\n" + "-"*60)
            if len(all_photo_records) >= 2:
                print("  1. 添加一张照片")
                print("  2. 完成并生成多图故事")
            else:
                print("  1. 添加一张照片（当前 %d 张，至少需 2 张才能生成多图故事）" % len(all_photo_records))
            print("-"*60)
            try:
                choice = input("\n请选择 (1 或 2): ").strip()
            except Exception:
                choice = ""
            if choice == "2":
                if len(all_photo_records) < 2:
                    print("\n[提示] 至少需要 2 张照片才能生成多图故事，请先添加照片。")
                    continue
                break
            if choice != "1":
                print("[错误] 请输入 1 或 2。")
                continue
            
            image_path = self.select_image()
            if not image_path:
                print("\n[提示] 未选择图片，请重新选择操作。")
                continue
            
            photo_id = os.path.basename(image_path)
            idx = len(all_photo_records) + 1
            
            print("\n正在处理第 %d 张照片：%s" % (idx, photo_id))
            try:
                analysis_result = self.analyze_photo(image_path)
            except Exception as e:
                print(f"\n[错误] 照片分析失败: {e}")
                import traceback
                traceback.print_exc()
                continue
            
            # 第一张：常规问题；后续：结合上一张生成跨图关联问题
            if idx == 1:
                questions = self.dialogue_manager.start_dialogue(photo_id=photo_id, analysis_result=analysis_result)
            else:
                cross_question = self.context_manager.generate_cross_photo_question(analysis_result)
                questions = self.dialogue_manager.start_dialogue(photo_id=photo_id, analysis_result=analysis_result)
                if cross_question and cross_question.strip():
                    questions = [cross_question]
            
            try:
                qa_history = self.conduct_interview(photo_id, analysis_result, initial_questions=questions)
            except Exception as e:
                print(f"\n[错误] 访谈过程出错: {e}")
                import traceback
                traceback.print_exc()
                qa_history = []
            
            dialogue_summary = self.dialogue_manager.get_dialogue_summary()
            qa_history = dialogue_summary.get("qa_history", qa_history)
            self.context_manager.add_photo_dialogue(
                photo_id=photo_id,
                analysis_result=analysis_result,
                qa_history=qa_history
            )
            all_photo_records.append({
                "photo_id": photo_id,
                "analysis": analysis_result,
                "qa_history": qa_history,
            })
            print("\n[完成] 第 %d 张照片已加入叙事链，共 %d 张。" % (idx, len(all_photo_records)))
        
        # 生成多图连贯故事
        print("\n" + "="*60)
        print("正在生成多图连贯故事...")
        print("="*60)
        print("叙事风格：第一人称个人叙事")
        print("这可能需要 30–60 秒，请稍候...\n")
        try:
            story = self.story_generator.generate_multi_photo_story(all_photo_records)
        except Exception as e:
            print(f"\n[错误] 故事生成失败: {e}")
            import traceback
            traceback.print_exc()
            story = "多图故事生成失败，请稍后重试。"
        
        # 展示与保存多图结果
        print("\n[完成] 故事生成完成！")
        print("\n" + "="*60)
        print("最终结果（多图叙事链）")
        print("="*60)
        print("\n【照片序列】: %s" % ", ".join(r["photo_id"] for r in all_photo_records))
        print("【叙事风格】: 个人叙事风格")
        print("\n【生成的故事】:")
        print("="*60)
        print(story)
        print("="*60)
        save_choice = input("\n是否保存结果到文件？(y/n): ").strip().lower()
        if save_choice == "y":
            safe_name = "multi_" + "_".join(
                r["photo_id"].replace("/", "_").replace("\\", "_") for r in all_photo_records[:3]
            )
            if len(all_photo_records) > 3:
                safe_name += "_etc"
            filename = "photo_story_%s.txt" % safe_name
            with open(filename, "w", encoding="utf-8") as f:
                f.write("="*60 + "\n多图叙事链 - 照片故事生成结果\n" + "="*60 + "\n\n")
                f.write("照片序列: %s\n\n" % ", ".join(r["photo_id"] for r in all_photo_records))
                f.write("【生成的故事】\n" + "="*60 + "\n%s\n" % story + "="*60 + "\n")
            print("\n[已保存] 结果已保存到: %s" % filename)
        
        print("\n" + "="*60)
        print("流程完成！感谢使用！")
        print("="*60)
    
    def run(self):
        """运行：先选模式，再执行单图深挖或多图叙事链"""
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
    """主函数"""
    app = InteractivePhotoStory()
    app.run()

if __name__ == "__main__":
    main()
