# HANNA Benchmark 清晰说明与项目落地指南

本文档用于团队内部同步 benchmark 部分。目标不是做论文综述，而是让没有看过 HANNA 论文和仓库的人，也能在几分钟内明白：

1. 这个 benchmark 从哪里来
2. 它本来解决什么问题
3. 它到底怎么评分
4. 我们项目里现在是怎么把它落地成可运行代码的
5. 别人如何直接照着这个标准复现评分

---

## 一、先说结论

我们当前使用的 benchmark 思路来自 **HANNA**。

- HANNA 原始工作给的是一套**故事评估标准 + 标注数据 + 自动指标对照分析**。
- HANNA 仓库**没有发布专门训练好的评分模型**。
- 因此，我们项目里的实现方式是：
  - 复用 HANNA 的六维评分标准；
  - 用现有大模型充当 Judge；
  - 通过结构化 prompt 和 JSON 输出协议，对单篇故事进行六维评分。

所以，我们当前的 benchmark 可以概括为：

**HANNA 六维标准 + LLM-as-Judge + 结构化评分输出。**

---

## 二、由来：HANNA 是什么

### 2.1 背景问题

自动故事生成一直有一个难点：

- 故事“好不好”很主观；
- 传统自动指标（如 BLEU、ROUGE）对故事这种开放生成任务并不可靠；
- 即使人工评价，大家也经常不知道到底该按哪些维度评。

HANNA 的工作就是想解决这个问题：

**给故事生成任务建立一套更明确、更系统的评估基准。**

### 2.2 HANNA 原始贡献

HANNA 主要做了两件事：

1. 定义一套 6 维人工评价标准
2. 收集带人工标注的故事数据，并比较 72 种自动指标与人工评分的相关性

也就是说，HANNA 更像是：

- 一套 benchmark 标准
- 一个评估数据集
- 一份“哪些指标更靠谱”的研究结果

它**不是**一个现成的评分模型仓库。

### 2.3 相关来源

- 原始说明整理：[benchmark/HANNA_BENCHMARK_METRICS_AND_METHODS.md](benchmark/HANNA_BENCHMARK_METRICS_AND_METHODS.md)
- 故事 benchmark 参考汇总：[benchmark/STORY_GENERATION_BENCHMARK_REFERENCE.md](benchmark/STORY_GENERATION_BENCHMARK_REFERENCE.md)
- 项目仿真评估框架：[benchmark/SIMULATION_DATASET_FRAMEWORK.md](benchmark/SIMULATION_DATASET_FRAMEWORK.md)

---

## 三、HANNA 仓库到底给了什么

HANNA 仓库提供的主要不是模型，而是以下几类资源：

### 3.1 数据

- `hanna_stories_annotations.csv`
  - 存放故事文本、对应 prompt、人类参考故事、模型来源，以及 6 个维度的人工评分。

- `hanna_metric_scores.csv` / `hanna_metric_scores_llm.csv`
  - 存放自动指标分数、人工平均分，以及后续 LLM 评分结果。

- `hanna_llm_stories.csv`
  - 后续实验中新增的 LLM 生成故事样本。

### 3.2 研究分析代码

- `data_visualization.ipynb`
  - 用来读数据、算相关性、画图、做论文分析。

- `fdr.py`
  - 用来做统计检验相关处理。

### 3.3 解释性分析资源

- `llm_answers/`
  - 保存 LLM 打分时的原始回答和解释。

- `user_study.csv`
  - 保存人工对 LLM 解释质量的评价结果。

### 3.4 关键事实

HANNA 仓库**没有**提供这些东西：

- 没有专门训练好的 story evaluator 权重
- 没有单独的评分服务接口
- 没有“输入一篇故事就自动出六维分数”的现成 CLI 工具

因此，如果我们想在项目里直接给文本打分，就必须自己实现一个 Judge 层。

---

## 四、HANNA 到底怎么评分

### 4.1 核心思想

HANNA 的核心不是“一个神秘模型”，而是“明确评分维度”。

它把故事质量拆成 6 个维度，每个维度单独打分。通常采用 1 到 5 分量表：

- 1 分：很差
- 2 分：偏弱
- 3 分：中等
- 4 分：较好
- 5 分：很好

### 4.2 六个评分维度

| 维度 | 英文 | 含义 | 看什么 |
|------|------|------|--------|
| 相关性 | Relevance | 故事和题目/参考文本是否匹配 | 有没有跑题，是否围绕目标内容展开 |
| 连贯性 | Coherence | 故事逻辑是否清楚 | 时间、因果、人物关系是否说得通 |
| 共情力 | Empathy | 读者是否能感受到人物情绪 | 情感是否真实、能否产生共鸣 |
| 惊喜度 | Surprise | 故事是否有合理的意外性 | 是否过于平铺直叙，是否有转折 |
| 吸引力 | Engagement | 故事是否让人愿意继续读 | 是否有阅读投入感 |
| 复杂度 | Complexity | 故事是否足够丰富、有层次 | 是否有细节、背景、展开，而非单薄 |

### 4.3 评分方式

评分时不是只给一个总印象分，而是：

1. 六个维度分别评分
2. 每个维度写一句简短解释
3. 最后再给一个总评

如果要计算总分，最简单的做法就是：

$$
\text{Final Score} = \frac{RE + CH + EM + SU + EG + CX}{6}
$$

我们当前项目里就是按这个平均分来给出 `final_score`。

---

## 五、我们项目里如何落地这个 benchmark

### 5.1 为什么要自己落地

因为 HANNA 没有给现成评分模型，所以我们项目里采用的是：

**HANNA 六维标准 + 现有大模型打分。**

也就是常说的：

**LLM-as-Judge**

### 5.2 当前实现思路

我们目前的实现步骤如下：

1. 把 HANNA 六维标准写成固定配置
2. 把待评分故事、可选 prompt、可选参考文本拼成一个评分 prompt
3. 调用现有 Gemini 或混元后端
4. 强制模型按 JSON 输出
5. 对输出做字段校验和分数范围校验

这套逻辑的核心文件是：

- 评分模块：[demo/src/story_judge.py](demo/src/story_judge.py)
- 命令行入口：[demo/judge_story.py](demo/judge_story.py)
- 使用说明：[demo/README.md](demo/README.md)

### 5.3 当前实现的定位

当前实现是一个**可用的 prompt-based evaluator**，不是专门训练好的 benchmark model。

优点：

- 接入快
- 可以直接跑
- 支持单篇文本立即评分
- 易于接前端或批量评测

局限：

- 评分仍受底层 LLM 波动影响
- 更适合快速筛选、相对比较
- 单篇故事分数不能完全替代人工评审

---

## 六、别人要怎么照着这个 benchmark 评分

这一节最重要。别人只要照着下面做，就能复现当前的评分方式。

### 6.1 输入需要什么

最少只需要：

1. 一段待评分故事文本

更完整的输入建议包含：

1. `story`：待评分故事
2. `prompt`：这个故事原本对应的题目或任务要求
3. `reference_story`：参考文本，如原始回忆录、标准答案或素材文本

### 6.2 评分步骤

#### 情况 A：只有故事文本

这时仍然可以评分，但 `relevance` 会退化为“主题聚焦度/是否跑题”。

#### 情况 B：有故事 + prompt

这时可以更准确地评估 `relevance`，看故事是否围绕题目展开。

#### 情况 C：有故事 + prompt + reference_story

这是最完整的评分形式。

此时可以同时比较：

- 是否符合题目
- 是否与原始参考内容一致
- 风格与内容是否偏离

### 6.3 具体评分规则

推荐按下面口径打分：

#### 相关性 Relevance

- 5 分：高度贴合 prompt 或参考文本，没有明显跑题
- 4 分：整体贴合，只有少量偏移
- 3 分：基本相关，但核心主题展开不充分
- 2 分：相关性较弱，存在明显偏题
- 1 分：几乎无关

#### 连贯性 Coherence

- 5 分：叙事清楚，因果和时间线都合理
- 4 分：基本连贯，偶有跳跃
- 3 分：能读懂，但有明显断裂或突兀之处
- 2 分：多处逻辑不清
- 1 分：整体混乱

#### 共情力 Empathy

- 5 分：人物情绪自然鲜明，容易引发共鸣
- 4 分：情绪表达较好
- 3 分：有情绪，但比较平
- 2 分：情绪表达弱
- 1 分：几乎没有情感感受

#### 惊喜度 Surprise

- 5 分：有自然且有效的转折或意外感
- 4 分：有一定新意
- 3 分：较平稳，偶有变化
- 2 分：比较套路化
- 1 分：完全平铺直叙且无转折

#### 吸引力 Engagement

- 5 分：明显让人想继续读
- 4 分：整体有吸引力
- 3 分：可以读完，但吸引力一般
- 2 分：阅读动力偏弱
- 1 分：难以持续阅读

#### 复杂度 Complexity

- 5 分：有细节、有层次、有背景展开
- 4 分：较丰富，不单薄
- 3 分：内容一般，信息量适中
- 2 分：比较简单
- 1 分：非常单薄

---

## 七、代码形式：当前项目怎么跑

### 7.1 命令行用法

最简单的调用：

```bash
python judge_story.py --story-file path/to/story.txt
```

带 prompt：

```bash
python judge_story.py --story-file path/to/story.txt --prompt-file path/to/prompt.txt
```

带 prompt 和 reference：

```bash
python judge_story.py \
  --story-file path/to/story.txt \
  --prompt-file path/to/prompt.txt \
  --reference-file path/to/reference.txt \
  --output evaluation_result.json
```

### 7.2 Python 调用方式

```python
from src.story_judge import StoryJudge

judge = StoryJudge()

result = judge.judge_story(
    story="那年冬天，我和父亲冒着雪去镇上卖菜……",
    story_prompt="写一个关于父爱与冬日记忆的短故事",
    reference_story="父亲在冬天带着孩子赶集，途中默默照顾孩子……"
)

print(result["scores"])
print(result["final_score"])
print(result["summary"])
```

### 7.3 返回结果格式

返回结果是结构化 JSON，示意如下：

```json
{
  "scores": {
    "relevance": 5.0,
    "coherence": 5.0,
    "empathy": 5.0,
    "surprise": 3.0,
    "engagement": 4.0,
    "complexity": 4.0
  },
  "final_score": 4.33,
  "summary": "一个简洁有力的父爱故事，情感真挚且主题鲜明，但在复杂度和惊喜度上略有提升空间。",
  "explanations": {
    "relevance": "故事紧扣父爱与冬日记忆主题，没有跑题。",
    "coherence": "时间线清楚，人物关系明确。",
    "empathy": "能感受到父亲的克制付出和孩子后来的理解。",
    "surprise": "结尾有一定回味，但强转折较少。",
    "engagement": "有画面感，能吸引读者读完。",
    "complexity": "有细节，但层次还可以更丰富。"
  }
}
```

---

## 八、这个 benchmark 在我们项目里的功能是什么

它在项目里的作用不是“证明绝对真理”，而是提供一个**统一评价口径**。

具体来说，它可以用来做三类事情：

### 8.1 单篇故事快速评分

给一段故事文本快速打六维分数，用来做初筛或展示。

### 8.2 多版本故事比较

同一个素材生成多个版本时，可以比较：

- 哪个版本更连贯
- 哪个版本更有情感
- 哪个版本更贴近原始回忆录

### 8.3 算法迭代评估

当问题生成、对话管理、故事生成策略变化后，可以固定同一批样本重新打分，观察：

- `final_score` 是否提高
- 哪些维度提升了
- 哪些维度仍然偏弱

这才是 benchmark 最重要的用途：

**帮助团队稳定比较版本，而不是只凭感觉说“这次结果好像更好了”。**

---

## 九、需要特别说明的限制

这部分在汇报时最好主动说清楚。

### 9.1 这不是 HANNA 官方模型

我们现在用的是：

- HANNA 的六维标准
- 自己实现的 Judge 逻辑

不是官方发布的 evaluator model，因为官方并没有发布。

### 9.2 这仍然是 LLM Judge

因此它有这些天然限制：

- 同一篇故事多次评分可能略有波动
- 底层模型换了，分数风格也可能变化
- 更适合做相对比较，不适合当唯一标准

### 9.3 HANNA 原始数据是英文故事

而我们项目当前面对的是：

- 中文回忆录
- 中文照片叙事
- 更贴近真实人生回忆场景

因此，我们是在借用 HANNA 的“评估思想”，不是原封不动照搬其数据分布。

---

## 十、如果后续要做得更学术、更稳，可以怎么升级

当前版本已经能用，但如果后续要做更强的 evaluator，可以按下面路线升级：

### 10.1 多次采样求均值

同一篇故事评 3 到 5 次，取平均分，减少单次波动。

### 10.2 增加人工校准集

收集一批中文回忆录故事，让人工按六维打分，再反过来调 prompt，让 Judge 更接近团队的评审口径。

### 10.3 训练专门 evaluator

如果后续标注数据足够，可以训练一个专门的六维评分模型。那时才会从“prompt-based evaluator”走向“learned evaluator”。

---

## 十一、一句话版本

如果要用一句话向别人介绍我们这部分 benchmark，可以直接这样说：

**我们采用 HANNA 的六维故事评估标准，把相关性、连贯性、共情力、惊喜度、吸引力和复杂度作为统一评分口径，再用现有大模型充当 Judge，对生成故事进行结构化打分和评语输出，从而支持单篇评分、版本比较和算法迭代评估。**
