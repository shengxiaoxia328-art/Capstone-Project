from typing import Dict, List, Any, Optional
import re

class QuestionBenchmark:    
    def __init__(self):
        # 记忆激发关键词库
        self.memory_keywords = [
            '记得', '回忆', '想起', '曾经', '以前', '当年', 
            '小时候', '那时候', '过去', '往事', '记忆',
            '感觉', '觉得', '感受', '心情', '经历', '印象',
            '还记不记得', '有没有印象', '能不能想起'
        ]
        
        # 情感关键词
        self.emotion_keywords = [
            '感动', '温暖', '开心', '快乐', '幸福', '难过', 
            '思念', '怀念', '珍惜', '不舍', '温馨', '甜蜜'
        ]
        
    
    def score_image_understanding(self, question: str, image_keywords: List[str]) -> float:
        """评分维度1：图片理解能力"""
        if not image_keywords:
            return 5.0
        
        matched = 0
        matched_words = []
        
        for keyword in image_keywords:
            if keyword in question:
                matched += 1
                matched_words.append(keyword)
        
        coverage = matched / len(image_keywords)
        base_score = coverage * 10
        
        if matched == 0:
            return 2.0
        
        bonus = min(2.0, matched * 0.5)
        score = min(10.0, base_score + bonus)
        
        print(f"  📊 图片关键词匹配: {matched}/{len(image_keywords)} = {coverage:.1%}")
        if matched_words:
            print(f"    匹配的词: {', '.join(matched_words)}")
        
        return round(score, 1)
    
    def score_memory_evocation(self, question: str) -> float:
        """评分维度2：记忆激发能力"""
        memory_count = 0
        memory_found = []
        for word in self.memory_keywords:
            if word in question:
                memory_count += 1
                memory_found.append(word)
        
        emotion_count = 0
        emotion_found = []
        for word in self.emotion_keywords:
            if word in question:
                emotion_count += 1
                emotion_found.append(word)
        
        base_score = 5.0
        memory_bonus = min(3.0, memory_count * 1.0)
        emotion_bonus = min(2.0, emotion_count * 0.7)
        
        question_words = ['什么', '怎么', '如何', '为什么', '是否', '吗', '呢', '哪', '谁']
        has_question_word = any(q in question for q in question_words)
        has_question_mark = '?' in question or '？' in question
        format_bonus = 1.0 if (has_question_word or has_question_mark) else 0
        
        score = base_score + memory_bonus + emotion_bonus + format_bonus
        score = min(10.0, score)
        
        print(f"  📊 记忆词: {memory_count}个 ({', '.join(memory_found) if memory_found else '无'})")
        print(f"  📊 情感词: {emotion_count}个 ({', '.join(emotion_found) if emotion_found else '无'})")
        print(f"  📊 问句形式: {'是' if has_question_word or has_question_mark else '否'}")
        
        return round(score, 1)
    
    def score_question_quality(self, question: str) -> float:
        """评分维度3：问题设计质量"""
        score = 7.0
        
        length = len(question)
        if length < 5:
            score -= 3.0
            print("  ⚠️ 问题太短")
        elif length > 50:
            score += 0.5
            print("  ✅ 问题长度适中")
        else:
            score += 0.5
            print("  ✅ 问题长度合适")
        
        has_punctuation = any(p in question for p in ['。', '？', '?', '！', '!'])
        if has_punctuation:
            score += 0.5
            print("  ✅ 有正确标点")
        
        has_subject = any(s in question for s in ['你', '我', '他', '她', '它', '这', '那'])
        if has_subject:
            score += 0.5
            print("  ✅ 有明确主语")
        
        awkward_words = ['请回答', '必须', '立即', '马上', '快快']
        has_awkward = any(w in question for w in awkward_words)
        if has_awkward:
            score -= 1.0
            print("  ⚠️ 包含生硬词汇")
        
        return round(min(10.0, max(0, score)), 1)
    
    def evaluate(self, question: str, image_keywords: List[str]) -> Dict[str, Any]:
        """综合评测问题"""
        print(f"\n📝 评测问题: {question}")
        print(f"🖼️  图片关键词: {image_keywords}")
        print("=" * 50)
        
        understanding = self.score_image_understanding(question, image_keywords)
        memory = self.score_memory_evocation(question)
        quality = self.score_question_quality(question)
        # 先将各维度分数从10分制转为30分制
        understanding_30 = understanding * 3
        memory_30 = memory * 3
        quality_30 = quality * 3

#        计算总分（30分制）
        total = (understanding_30 * 0.4 + memory_30 * 0.3 + quality_30 * 0.3)
        
        result = {
            "scores": {
                "image_understanding": understanding,
                "memory_evocation": memory,
                "question_quality": quality
            },
            "total_score": round(total, 1)
        }
        
        print("=" * 50)
        print(f"📊 图片理解: {understanding}/10")
        print(f"📊 记忆激发: {memory}/10") 
        print(f"📊 设计质量: {quality}/10")
        print(f"🎯 总分: {result['total_score']}/10")
        print("=" * 50)
        
        return result


def format_question_result(result: Dict[str, Any]) -> str:
    """格式化问题评测结果"""
    output = []
    output.append("\n" + "=" * 60)
    output.append("❓ 问题生成评测结果")
    output.append("=" * 60)
    
    if "scores" in result:
        output.append("\n📊 三维评分:")
        dim_names = {
            "image_understanding": "图片理解",
            "memory_evocation": "记忆激发",
            "question_quality": "设计质量"
        }
        for dim, score in result["scores"].items():
            dim_zh = dim_names.get(dim, dim)
            bar = "█" * int(score) + "░" * (10 - int(score))
            output.append(f"  {dim_zh}: {score:4.1f}/10 {bar}")
    
    if "total_score" in result:
        output.append(f"\n🎯 总分: {result['total_score']:.1f}/30")
    
    output.append("=" * 60)
    return "\n".join(output)
