#!/usr/bin/env python3
"""
测试增强的追问机制
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.enhanced_followup import (
    AnswerQualityAnalyzer,
    InformationGapIdentifier,
    QuestionTypeSelector,
    EnhancedFollowupGenerator
)


def test_answer_quality_analyzer():
    """测试回答质量分析器"""
    print("=" * 80)
    print("测试回答质量分析器")
    print("=" * 80)
    
    analyzer = AnswerQualityAnalyzer()
    
    test_answers = [
        "是的",  # 简短回答
        "那是我的爷爷，我们关系很好。",  # 中等回答
        "那是我的爷爷，我们关系很好。他是一位退休教师，平时喜欢看书。这张照片是在80年代拍的，当时我们一家人去公园玩，爷爷很开心。",  # 详细回答
        "那是我的爷爷。看到这张照片，我想起了很多往事。那时候的生活虽然简单，但很温暖。这张照片对我来说有特殊的意义，因为它记录了我们一家人在一起的快乐时光。",  # 包含情感
    ]
    
    for i, answer in enumerate(test_answers, 1):
        print(f"\n测试回答 {i}: {answer}")
        quality = analyzer.analyze(answer)
        print(f"  长度: {quality['length']}")
        print(f"  详细程度: {quality['detail_level']}")
        print(f"  包含情感: {quality['emotion_present']}")
        print(f"  信息密度: {quality['information_density']:.2f}")
        print(f"  具体性: {quality['specificity']:.2f}")
        print(f"  质量评分: {quality['quality_score']:.2f}")


def test_information_gap_identifier():
    """测试信息缺口识别器"""
    print("\n" + "=" * 80)
    print("测试信息缺口识别器")
    print("=" * 80)
    
    identifier = InformationGapIdentifier()
    
    # 模拟问答历史
    qa_history = [
        {"question": "照片中的人是谁？", "answer": "那是我的爷爷。"},
        {"question": "这张照片是在什么地方拍的？", "answer": "在公园里拍的。"},
    ]
    
    # 模拟分析结果
    analysis_result = {
        "overall_description": "照片中有一位老人，背景是公园，拍摄于80年代，人物表情很开心。"
    }
    
    gaps = identifier.identify_gaps(qa_history, analysis_result)
    print(f"\n问答历史:")
    for qa in qa_history:
        print(f"  Q: {qa['question']}")
        print(f"  A: {qa['answer']}")
    
    print(f"\n识别的信息缺口: {gaps}")


def test_question_type_selector():
    """测试问题类型选择器"""
    print("\n" + "=" * 80)
    print("测试问题类型选择器")
    print("=" * 80)
    
    selector = QuestionTypeSelector()
    
    test_cases = [
        {
            "answer_quality": {"quality_score": 0.2, "emotion_present": False, "information_density": 0.2},
            "information_gaps": ["时间", "情感"],
            "qa_history": [{"question": "谁？", "answer": "爷爷"}]
        },
        {
            "answer_quality": {"quality_score": 0.6, "emotion_present": True, "information_density": 0.5},
            "information_gaps": [],
            "qa_history": [{"question": "谁？", "answer": "那是我的爷爷，我们关系很好，看到照片很怀念。"}]
        },
        {
            "answer_quality": {"quality_score": 0.4, "emotion_present": False, "information_density": 0.3},
            "information_gaps": ["地点"],
            "qa_history": [{"question": "谁？", "answer": "爷爷"}]
        },
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"  回答质量: {case['answer_quality']}")
        print(f"  信息缺口: {case['information_gaps']}")
        question_type = selector.select_type(
            case["answer_quality"],
            case["information_gaps"],
            case["qa_history"]
        )
        print(f"  选择的问题类型: {question_type}")
        print(f"  类型描述: {QuestionTypeSelector.QUESTION_TYPES[question_type]['description']}")


def test_enhanced_followup_generator():
    """测试增强的追问生成器"""
    print("\n" + "=" * 80)
    print("测试增强的追问生成器")
    print("=" * 80)
    
    generator = EnhancedFollowupGenerator()
    
    # 模拟数据
    analysis_result = {
        "overall_description": "照片中有一位老人，背景是公园，拍摄于80年代，人物表情很开心，穿着朴素。"
    }
    
    qa_history = [
        {"question": "照片中的人是谁？", "answer": "那是我的爷爷。"},
        {"question": "这张照片是在什么地方拍的？", "answer": "在公园里拍的。"},
    ]
    
    prompt = generator.generate_enhanced_followup_prompt(
        analysis_result, qa_history
    )
    
    print("\n生成的增强提示词:")
    print("-" * 80)
    print(prompt)
    print("-" * 80)


if __name__ == "__main__":
    test_answer_quality_analyzer()
    test_information_gap_identifier()
    test_question_type_selector()
    test_enhanced_followup_generator()
    
    print("\n" + "=" * 80)
    print("所有测试完成！")
    print("=" * 80)
