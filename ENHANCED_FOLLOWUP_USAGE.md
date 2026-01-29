# 增强追问机制使用说明

## 概述

增强的追问机制基于学术论文研究，提供了更智能、更自适应的追问策略。它能够：

1. **分析回答质量** - 评估用户回答的详细程度、情感含量和信息密度
2. **识别信息缺口** - 自动识别哪些关键信息还未收集
3. **选择问题类型** - 根据回答质量和信息缺口选择最合适的问题类型
4. **生成针对性问题** - 生成能够深入挖掘信息的问题

## 功能特性

### 1. 回答质量分析

系统会自动分析用户回答的质量，包括：
- **长度**: 回答的字符数
- **详细程度**: low/medium/high
- **情感检测**: 是否包含情感关键词
- **信息密度**: 基于关键词数量的信息密度评分
- **具体性**: 回答中包含具体细节的程度
- **质量评分**: 综合评分（0-1）

### 2. 信息缺口识别

系统会识别以下关键信息维度是否已收集：
- **人物**: 谁、人物、关系等
- **地点**: 哪里、地方、位置等
- **时间**: 什么时候、时间、年代等
- **情感**: 感觉、心情、意义等
- **事件**: 发生、事情、经过等
- **细节**: 细节、具体、特征等

### 3. 问题类型选择

系统会根据情况自动选择以下问题类型之一：

- **clarification** (澄清性问题): 当回答不够详细时
- **emotion_deepening** (情感深化): 当回答包含情感时
- **detail_expansion** (细节扩展): 当需要更多细节时
- **connection** (关联性问题): 连接不同信息点
- **contextual** (上下文问题): 基于照片分析的问题

## 使用方法

### 基本使用

增强的追问机制已经集成到 `QuestionGenerator` 中，默认启用：

```python
from src.question_generator import QuestionGenerator

# 创建问题生成器（默认启用增强追问）
generator = QuestionGenerator()

# 生成初始问题
questions = generator.generate_initial_questions(analysis_result)

# 生成追问（自动使用增强机制）
followup_question = generator.generate_followup_question(
    analysis_result=analysis_result,
    previous_qa=[
        {"question": "照片中的人是谁？", "answer": "那是我的爷爷。"}
    ]
)
```

### 禁用增强追问

如果需要使用原始的简单追问机制：

```python
# 禁用增强追问
generator = QuestionGenerator(use_enhanced_followup=False)
```

### 直接使用增强模块

也可以直接使用增强的追问生成器：

```python
from src.enhanced_followup import EnhancedFollowupGenerator

generator = EnhancedFollowupGenerator()

# 生成增强的提示词
prompt = generator.generate_enhanced_followup_prompt(
    analysis_result=analysis_result,
    previous_qa=qa_history,
    context=None
)

# 然后使用这个提示词调用API生成问题
```

## 工作原理

### 1. 回答质量分析流程

```
用户回答 → 质量分析器 → 质量指标
                ↓
        详细程度、情感、信息密度、具体性
                ↓
            质量评分
```

### 2. 信息缺口识别流程

```
问答历史 + 照片分析 → 话题提取 → 维度检查 → 信息缺口列表
```

### 3. 问题类型选择流程

```
质量评分 + 信息缺口 → 类型选择器 → 问题类型
```

### 4. 提示词生成流程

```
分析结果 + 问答历史 + 质量分析 + 信息缺口 + 问题类型
                ↓
        增强的提示词
                ↓
            API调用
                ↓
            生成问题
```

## 配置选项

可以在 `config.py` 中添加以下配置：

```python
# 追问机制配置
USE_ENHANCED_FOLLOWUP = True  # 是否使用增强追问机制
FOLLOWUP_MAX_CONTEXT_LENGTH = 500  # 对话历史最大长度
FOLLOWUP_QUALITY_THRESHOLD = 0.3  # 质量评分阈值
```

## 测试

运行测试脚本查看增强追问机制的效果：

```bash
python3 examples/test_enhanced_followup.py
```

## 改进建议

基于学术论文研究，未来可以考虑以下改进：

1. **引入RAG机制**: 使用检索增强生成来更好地利用历史对话
2. **对话依赖建模**: 建立问题之间的依赖关系图
3. **混合主动对话**: 平衡系统主动性和用户主导性
4. **多模态融合**: 更好地结合照片分析和对话历史

## 相关论文

详细的论文研究总结请参考：`FOLLOWUP_QUESTION_IMPROVEMENT.md`

## 示例输出

增强的追问机制会生成包含以下信息的提示词：

```
照片信息：...
之前的对话历史：...
回答质量分析：
- 详细程度：medium
- 包含情感：是
- 信息密度：0.40
- 质量评分：0.55
信息缺口：时间, 情感
问题类型：emotion_deepening
...
```

这使LLM能够生成更智能、更有针对性的追问问题。
