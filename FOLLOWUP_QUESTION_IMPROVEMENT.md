# 追问机制改进方案 - 基于学术论文研究

## 一、相关论文总结

### 1. 核心论文

#### 1.1 Recent Advances in Neural Question Generation (2019)
- **作者**: Liangming Pan, Wenqiang Lei, Tat-Seng Chua
- **链接**: https://arxiv.org/abs/1905.08949v3
- **核心观点**:
  - 神经问题生成(NQG)开始整合更多样化的输入
  - 生成需要更高认知水平的问题
  - 强调上下文感知和多样性

#### 1.2 Multi-turn dialogue-oriented pretrained question generation model (2020)
- **作者**: Yanmeng Wang, Wenge Rong, Jianfei Zhang
- **链接**: https://www.semanticscholar.org/paper/47009687fde55ba56c435670e01f7226e65428ab
- **核心观点**:
  - 专门针对多轮对话的问题生成模型
  - 强调对话连贯性和上下文理解
  - 引用数: 6

#### 1.3 Dependency Dialogue Acts (2023)
- **作者**: Jon Z. Cai, Brendan King, Margaret Perkoff
- **链接**: https://arxiv.org/abs/2302.12944v1
- **核心观点**:
  - 引入依赖对话行为(DDA)框架
  - 捕获多轮对话中说话者意图的结构
  - 强调对话的依赖关系和层次结构

#### 1.4 Controllable Mixed-Initiative Dialogue Generation (2023)
- **作者**: Maximillian Chen, Xiao Yu, Weiyan Shi
- **链接**: https://arxiv.org/abs/2305.04147v1
- **核心观点**:
  - 混合主动对话任务涉及信息和对话控制的重复交换
  - 通过生成遵循特定对话意图的响应来获得控制权
  - 强调可控性和主动性

#### 1.5 Towards Adaptive Context Management for Conversational Question Answering (2025)
- **作者**: Manoj Madushanka Perera, Adnan Mahmood, Kasun Eranda Wijethilake
- **链接**: https://arxiv.org/abs/2509.17829v1
- **核心观点**:
  - 自适应上下文管理(ACM)框架
  - 优化上下文使用，提高对话问答系统性能
  - 强调动态上下文管理

#### 1.6 DH-RAG: Dynamic Historical Context-Powered Retrieval-Augmented Generation (2025)
- **作者**: Feiyuan Zhang, Dezhi Zhu, James Ming
- **链接**: https://www.semanticscholar.org/paper/352614d576a4b219032aa7c6025f4a19d8dbbbbd
- **核心观点**:
  - 动态历史上下文驱动的检索增强生成
  - 针对多轮对话的RAG系统改进
  - 引用数: 5

### 2. 关键研究方向

#### 2.1 上下文感知问题生成
- **核心思想**: 基于完整对话历史和照片分析结果生成问题
- **实现要点**:
  - 维护对话历史摘要
  - 识别信息缺口
  - 基于已收集信息生成深入问题

#### 2.2 自适应追问策略
- **核心思想**: 根据用户回答的质量和详细程度动态调整追问策略
- **实现要点**:
  - 评估回答的信息量
  - 识别需要深入挖掘的话题
  - 选择合适的问题类型（事实性/情感性/关联性）

#### 2.3 对话依赖关系建模
- **核心思想**: 理解问题之间的依赖关系和层次结构
- **实现要点**:
  - 识别问题类型（初始问题/追问/跨照片问题）
  - 建立问题之间的逻辑关系
  - 避免重复和无关问题

#### 2.4 混合主动对话
- **核心思想**: 系统主动引导对话，同时适应用户的回应
- **实现要点**:
  - 平衡系统主动性和用户主导性
  - 根据对话状态调整主动性
  - 在关键时刻引导对话方向

## 二、当前系统分析

### 2.1 现有实现
- **位置**: `src/question_generator.py`
- **功能**:
  - `generate_initial_questions()`: 生成初始问题
  - `generate_followup_question()`: 生成后续问题
  - `generate_cross_photo_question()`: 生成跨照片问题

### 2.2 存在的问题
1. **追问策略单一**: 仅基于之前的问答对生成，缺乏深度分析
2. **上下文利用不足**: 没有充分利用对话历史和照片分析结果
3. **缺乏自适应机制**: 无法根据回答质量调整追问策略
4. **问题类型单一**: 没有区分不同类型的问题（事实性/情感性/关联性）
5. **信息缺口识别缺失**: 无法识别哪些信息还需要深入挖掘

## 三、改进方案

### 3.1 增强上下文管理
```python
class EnhancedContextManager:
    """增强的上下文管理器"""
    
    def __init__(self):
        self.dialogue_history = []
        self.information_gaps = []
        self.topic_coverage = {}
    
    def analyze_answer_quality(self, answer: str) -> Dict:
        """分析回答质量"""
        return {
            "length": len(answer),
            "detail_level": self._assess_detail_level(answer),
            "emotion_present": self._detect_emotion(answer),
            "information_density": self._calculate_information_density(answer)
        }
    
    def identify_information_gaps(self, qa_history: List[Dict], 
                                   analysis_result: Dict) -> List[str]:
        """识别信息缺口"""
        gaps = []
        # 检查关键信息是否已收集
        # - 人物关系
        # - 时间地点
        # - 情感体验
        # - 故事背景
        return gaps
```

### 3.2 自适应追问策略
```python
class AdaptiveFollowupStrategy:
    """自适应追问策略"""
    
    def select_question_type(self, answer_quality: Dict, 
                            context: Dict) -> str:
        """根据回答质量选择问题类型"""
        if answer_quality["detail_level"] == "low":
            return "clarification"  # 澄清性问题
        elif answer_quality["emotion_present"]:
            return "emotion_deepening"  # 情感深化
        elif answer_quality["information_density"] < 0.5:
            return "detail_expansion"  # 细节扩展
        else:
            return "connection"  # 关联性问题
```

### 3.3 问题依赖关系建模
```python
class QuestionDependencyGraph:
    """问题依赖关系图"""
    
    def __init__(self):
        self.question_types = {
            "factual": ["who", "what", "where", "when"],
            "emotional": ["how_feel", "why_important", "meaning"],
            "relational": ["connection", "comparison", "influence"]
        }
        self.dependency_rules = {
            "factual -> emotional": "先收集事实，再挖掘情感",
            "factual -> relational": "先了解基本信息，再建立关联"
        }
```

### 3.4 动态历史上下文
```python
class DynamicHistoryContext:
    """动态历史上下文管理器"""
    
    def build_context_summary(self, qa_history: List[Dict], 
                             max_length: int = 500) -> str:
        """构建上下文摘要"""
        # 提取关键信息
        # 压缩历史对话
        # 保留重要细节
        pass
    
    def retrieve_relevant_history(self, current_question: str,
                                  qa_history: List[Dict]) -> List[Dict]:
        """检索相关历史对话"""
        # 基于语义相似度
        # 基于话题相关性
        pass
```

## 四、具体实现建议

### 4.1 短期改进（1-2周）
1. **增强追问提示词**
   - 添加回答质量分析
   - 明确问题类型指导
   - 增加信息缺口识别

2. **改进上下文利用**
   - 构建对话历史摘要
   - 提取关键信息点
   - 识别未覆盖话题

3. **问题类型分类**
   - 事实性问题
   - 情感性问题
   - 关联性问题
   - 深化性问题

### 4.2 中期改进（1-2月）
1. **实现自适应策略**
   - 根据回答质量调整追问
   - 动态选择问题类型
   - 智能跳过已充分回答的问题

2. **信息缺口识别**
   - 定义关键信息维度
   - 评估信息完整性
   - 生成针对性问题

3. **对话依赖建模**
   - 建立问题层次结构
   - 避免重复和无关问题
   - 优化问题序列

### 4.3 长期改进（3-6月）
1. **引入检索增强生成(RAG)**
   - 基于历史对话检索相关上下文
   - 动态更新上下文窗口
   - 优化上下文利用效率

2. **混合主动对话**
   - 平衡系统主动性和用户主导性
   - 根据对话状态调整策略
   - 实现更自然的对话流程

3. **多模态上下文融合**
   - 结合照片分析和对话历史
   - 跨照片信息关联
   - 视觉-文本联合理解

## 五、评估指标

### 5.1 问题质量指标
- **相关性**: 问题与照片和对话历史的相关程度
- **深度**: 问题挖掘信息的深度
- **多样性**: 问题类型的多样性
- **连贯性**: 问题之间的逻辑连贯性

### 5.2 对话效果指标
- **信息收集完整性**: 收集到的信息是否全面
- **用户参与度**: 用户回答的详细程度
- **故事连贯性**: 最终生成故事的连贯性
- **情感挖掘深度**: 情感信息的挖掘深度

## 六、参考文献

1. Pan, L., Lei, W., & Chua, T. S. (2019). Recent Advances in Neural Question Generation. arXiv:1905.08949

2. Wang, Y., Rong, W., & Zhang, J. (2020). Multi-turn dialogue-oriented pretrained question generation model.

3. Cai, J. Z., King, B., & Perkoff, M. (2023). Dependency Dialogue Acts -- Annotation Scheme and Case Study. arXiv:2302.12944

4. Chen, M., Yu, X., & Shi, W. (2023). Controllable Mixed-Initiative Dialogue Generation through Prompting. arXiv:2305.04147

5. Perera, M. M., Mahmood, A., & Wijethilake, K. E. (2025). Towards Adaptive Context Management for Intelligent Conversational Question Answering. arXiv:2509.17829

6. Zhang, F., Zhu, D., & Ming, J. (2025). DH-RAG: Dynamic Historical Context-Powered Retrieval-Augmented Generation Method for Multi-Turn Dialogue.
