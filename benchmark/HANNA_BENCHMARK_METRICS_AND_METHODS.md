# HANNA Benchmark：指标与方法说明

本文档基于 **HANNA** 原仓库与 COLING 2022 论文 *Of Human Criteria and Automatic Metrics: A Benchmark of the Evaluation of Story Generation*，整理其**人工评估维度**、**自动指标分类**与**元评估方法**，便于复现或迁移到本项目的故事生成评估中。

- **仓库**：https://github.com/dig-team/hanna-benchmark-asg  
- **COLING 2022 资源**：`coling` 分支  
- **论文**：https://aclanthology.org/2022.coling-1.509  

---

## 一、数据集与任务设定

### 1.1 HANNA 数据概览

| 项目 | 说明 |
|------|------|
| **数据来源** | WritingPrompts (Fan et al., 2018) |
| **故事总数** | 1,056 篇 |
| **Prompt 数** | 96 个（每个 prompt 对应 1 篇人类故事 + 10 个系统生成的故事） |
| **生成系统** | 10 个：Human（参考）、BertGeneration、CTRL、GPT、GPT-2、GPT-2 (tag)、RoBERTa、XLNet、Fusion、HINT、TD-VAE |
| **人工标注** | 每篇故事 3 名标注者 × 6 个维度，共 19,008 次标注 |
| **自动指标** | 72 种（基于 SummEval 等库计算） |

### 1.2 仓库中的核心文件

| 文件 | 内容 |
|------|------|
| `hanna_stories_annotations.csv` | 原始人工标注：Story ID、Prompt、Human、Story、Model、六维分数、Worker ID、Assignment ID、Work time in seconds、Name |
| `hanna_metrics_scores.csv` (coling) / `hanna_metric_scores_llm.csv` (main) | 每系统每故事的自动指标分数 +（main 分支）LLM 评分 |
| `data_visualization.ipynb` | 复现论文图表与相关性分析 |
| `requirements.txt` | 依赖（含 `pingouin`, `scipy`, `pandas`, `seaborn` 等） |

---

## 二、人工评估维度（6 个）

论文基于社会心理学与叙事学文献，定义了一组**正交、可操作**的人工标准，并配有 5 点 Likert 量表（1–5）。定义如下（与仓库中列名一致）。

### 2.1 维度定义（论文 Section 3.4）

| 缩写 | 英文 | 含义与文献依据 |
|------|------|----------------|
| **RE** | Relevance | 故事与 **prompt** 的匹配程度；对应 Jhamtani & Berg-Kirkpatrick (2020)、Goldfarb-Tarrant et al. (2020) 中的相关性评估。 |
| **CH** | Coherence | 故事是否**说得通**（逻辑、因果、时间顺序）；对应 Xu et al. (2018)、Peng et al. (2018)、Yao et al. (2019)、Pascual et al. (2021) 中的连贯性。 |
| **EM** | Empathy | 读者对**角色情感**的理解与共鸣；源于情感评论 (McCabe & Peterson, 1984)、激情 (Dickman, 2003)、共情 (Keen et al., 2007; Bae et al., 2021)。 |
| **SU** | Surprise | **结局/发展**的意外程度（合理范围内的“惊喜”）；源于 schema 违反、意外性 (Schank, 1978; Bae et al., 2021)、可后验性 (Behrooz et al., 2019)、新颖性 (Randall, 1999)。 |
| **EG** | Engagement | 读者**投入程度**（是否愿意读下去、是否有主观判断与期待）；与意愿模态投射 (Toolan, 2012)、故事结果 (Iran-Nejad, 1987) 相关。 |
| **CX** | Complexity | 故事的**精细度**（细节描写、问题解决、世界构建）；源于 McCabe & Peterson (1984)、Roine (2016) 等。 |

后四个维度（EM、SU、EG、CX）是论文的**原创贡献**，用于与常用的 RE、CH 区分，覆盖更多“好故事”的侧面。

### 2.2 标注协议要点（论文 Section 3.5）

- **平台**：Amazon Mechanical Turk。  
- **每篇故事**：3 名标注者，6 个维度各打 1–5 分。  
- **参考**：同时展示**人类参考故事**，便于校准。  
- **质量控制**：仅接受英美加澳新地区、Masters Qualification；拒绝 <30 秒完成的 HIT；要求写出“故事中第一个出现的虚构角色名”以确认阅读。  
- **最终分数**：对每篇故事、每个维度，取 3 名标注者的**平均分**。  

### 2.3 人工维度间的相关性（论文 Section 4.2）

- **Story-level**：Kendall 相关约 16%（RE–SU）到 62%（CH–EG），平均约 40.7%，说明 6 个维度相对独立、非冗余。  
- **System-level**：维度间相关更高，同一系统在不同维度上倾向一致地好或差。  
- **ICC2k**（论文 Tab. 3）：各维度在 29%–56% 之间，与现有 NLG 标注文献一致，论文未设硬性一致性阈值，而是强调协议透明与置信区间报告。  

---

## 三、自动指标分类（72 种）

论文将 72 种自动指标按**是否需要参考文本**与**计算方式**分为以下几类（对应论文 Tab. 1 与 Section 2.2）。符号约定：**[ref]** = 基于参考（reference-based），**[noref]** = 无参考（reference-free）；**[str]** = 字符串级，**[emb]** = 嵌入级，**[model]** = 模型级。

### 3.1 基于参考（Reference-based, [ref]）

| 类型 | 指标示例 | 说明 |
|------|----------|------|
| **字符串 [str]** | BLEU (Papineni et al., 2002)、ROUGE (Lin, 2004)、METEOR (Banerjee & Lavie, 2005)、CHRF (Popović, 2015)、CIDEr (Vedantam et al., 2015) | 与参考文本在 n-gram/词级比对；无法处理同义改写。 |
| **嵌入 [emb]** | ROUGE-WE (Ng & Abrecht, 2015)、BERTScore (Zhang et al., 2020)、MoverScore (Zhao et al., 2019)、BaryScore (Colombo et al., 2021)、DepthScore (Staerman et al., 2021) | 基于词向量或上下文嵌入的相似度。 |
| **模型 [model]** | S3 (Peyrard et al., 2017)、SummaQA (Scialom et al., 2019)、InfoLM (Colombo et al., 2022)、BARTScore (Yuan et al., 2021) | 用预训练/回归模型对“候选–参考”打分。 |

### 3.2 无参考（Reference-free, [noref]）

| 类型 | 指标示例 | 说明 |
|------|----------|------|
| **字符串 [str]** | Coverage、Density、Compression (Grusky et al., 2018)、Text length、Novelty、Repetition (Fabbri et al., 2021) | 仅从候选文本或 prompt 统计得到。 |
| **嵌入 [emb]** | SUPERT (Gao et al., 2020) | 无参考的语义/摘要质量估计。 |
| **模型 [model]** | BLANC (Vasilyev et al., 2020) | 无参考的模型打分。 |

BARTScore 在论文中可按设定作为 reference-based 或 reference-free 使用。

### 3.3 仓库 notebook 中的“过滤指标”子集

`data_visualization.ipynb` 中为画图与展示选取了部分代表性子集（含人类六维 + LLM 评分 + 下列自动指标）：

- **字符串**：BLEU[ref][str]、ROUGE-1 (Recall/Precision/F)[ref][str]、METEOR[ref][str]、chrF[ref][str]、Coverage[noref][str]、Repetition-1[noref][str]  
- **嵌入**：ROUGE-WE-3[ref][emb]、BERTScore F1[ref][emb]、MoverScore[ref][emb]、DepthScore[ref][emb]、BaryScore-W[ref][emb]、SUPERT-PS[noref][emb]  
- **模型**：S3-Pyramid[ref][model]、SummaQA[ref][model]、InfoLM-FisherRao[ref][model]、BARTScore-SH[ref][model]、BLANC-Tune-PS[noref][model]  

完整 72 种指标由 **SummEval**（https://github.com/Yale-LILY/SummEval）等库计算，详见论文附录与该库文档。

---

## 四、元评估方法（Meta-evaluation）

目标：评估**自动指标与人工维度**之间的一致性，以及**不同自动指标**之间的一致性。

### 4.1 符号与数据

- `y_i^j`：系统 j 对 prompt i 生成的故事。  
- `m(y_i^j)`：某（人工或自动）指标 m 对 y_i^j 的分数。  
- N=96（prompt 数），S=10（系统数，不含或含 Human 视分析而定）。  

### 4.2 两种相关层次（论文 Section 3.6）

**1. Story-level 相关（K_story(m1,m2)）**

- 对**每个 prompt i**，在 S 个系统的故事上算两个指标 m1, m2 的相关系数 K，再对 i=1..N 取平均。  
- 含义：若把指标当损失或奖励做**逐篇**优化，该指标与人工的 story-level 相关越高，越适合作为训练信号。  
- 公式：K_story(m1,m2) = (1/N) Σ_i K(C_m1,i_story, C_m2,i_story)，其中 C_m,i_story = (m(y_i^1), ..., m(y_i^S))。  

**2. System-level 相关（K_sys(m1,m2)）**

- 对每个系统 j，先在 N 个 prompt 上对 m1, m2 各自取平均，得到两个长度为 S 的向量，再算这两个向量的 K。  
- 含义：用于**比较系统优劣**时，该指标与人工在“系统排名”上的一致性。  
- 公式：K_sys(m1,m2) = K( (1/N)C_m1_sys, (1/N)C_m2_sys )，其中 C_m_sys = [ Σ_i m(y_i^1), …, Σ_i m(y_i^S) ]。  

### 4.3 相关系数类型

- **Pearson r**、**Spearman rho**、**Kendall tau** 三种均可；论文图表中多用 **Kendall** 与 **Pearson**，并报告**绝对值**以便比较方向不一致的指标。  

### 4.4 统计显著性（Williams test）

- 同一批数据上算出的多个相关系数（如“指标 A 与 RE”“指标 B 与 RE”）**不独立**。  
- 论文采用 **Williams test**（Williams, 1959; Moon, 2019, nlp-williams）检验“相关 rho1 是否显著高于 rho2”。  
- 结论示例：与人工各维度相关性最高的 Top 3 指标之间，多数**差异不显著**；但 **chrF[ref][str]、BERTScore[ref][emb]** 相对 **BLEU[ref][str]、ROUGE[ref][str]** 的**提升**在统计上显著。  

### 4.5 其他分析

- **Pairwise system comparison**：对所有系统对做 paired bootstrap，得到“系统 A 是否显著优于 B”的 0/1/2 标签，再与各自动指标预测的排序比较，用 **weighted macro F1** 衡量指标能否复现人工系统排序。  
- **Top-k systems**：仅保留表现最好的 k 个系统，观察与人工的 system-level 相关随 k 的变化（论文 Fig. 8）。  
- **聚合排序**：对 Kendall、Pearson、Spearman 下的指标排名做 **Borda Count (BC)** 近似 **Kemeny consensus**（Colombo et al., 2022a, RankingNLPSystems），得到“综合”推荐指标（论文 Tab. 6）。  

### 4.6 人工故事的处理

- 与 Mathur et al. (2020) 一致，计算“自动指标 vs 人工维度”相关时，多数实验**剔除 Human 系统**，以减少人类故事作为“生成结果”的离群影响。  

---

## 五、论文主要结论与推荐指标

### 5.1 与人工各维度最相关的指标（论文 Tab. 5 摘要）

- **Story-level**：  
  - RE：BARTScore[noref][model]、SUPERT[noref][emb] 等无参考指标较好；
  - CH：Repetition-3[noref][str]、BERTScore[ref][emb]、S3[ref][model]；
  - SU：Novelty-1[noref][str]、chrF[ref][str]、ROUGE-1[ref][str]；
  - EG/CX：BERTScore[ref][emb]、chrF[ref][str]、ROUGE-1[ref][str] 等。
- **System-level**：
  - RE：ROUGE-S*[ref][str] 系列；
  - CH/EM：BaryScore[ref][emb]、BERTScore[ref][emb]；
  - SU/EG：BARTScore[ref][model]、DepthScore[ref][emb]、SUPERT[noref][emb]；
  - CX：DepthScore[ref][emb]、BERTScore[ref][emb]、Compression[noref][str]。

### 5.2 Borda Count 综合排序（论文 Tab. 6）

- **Story-level 推荐**：chrF[ref][str]、S3[ref][model]、ROUGE-1[ref][str]、BERTScore[ref][emb] 等。
- **System-level 推荐**：BARTScore[ref][model]、BaryScore[ref][emb]、BERTScore[ref][emb]、MoverScore[ref][emb]、DepthScore[ref][emb]。
- **结论**：**BLEU[ref][str]** 在综合排序中未进前列；**chrF[ref][str]**、**BERTScore[ref][emb]**、**BARTScore[ref][model]** 更适合作 ASG 评估；在缺乏专用 ASG 指标时，**建议以人工标注为主**，自动指标为辅。

### 5.3 实践建议（论文 Section 6）

1. 若用自动指标，优先选用 **chrF[str]**、**BERTScore[emb]**、**BARTScore[model]** 等，而非仅 BLEU/ROUGE。  
2. **Relevance (RE)** 最难被现有自动指标刻画，无参考的 SUPERT[noref][emb] 等相对有用。  
3. **Surprise (SU)** 等维度上，简单统计（如 Novelty、Repetition）有时优于复杂模型指标，说明当前指标对“惊喜”“新颖”的建模不足。  
4. 系统级比较时，参考型指标整体优于无参考型；但逐篇质量（story-level）时，两者各有优劣。  

---

## 六、仓库使用与复现

### 6.1 环境与依赖

```bash
git clone https://github.com/dig-team/hanna-benchmark-asg.git
cd hanna-benchmark-asg
# COLING 2022 版本使用 coling 分支
git checkout coling   # 可选
pip install -r requirements.txt
```

- **Notebook** 中“Williams”部分依赖 [nlp-williams](https://github.com/inmoonlight/nlp-williams) 的 `williams.py`（许可原因未包含在仓库）；若不跑该节，可注释对应 import。  
- **coling** 分支中“Ranking DFs”部分依赖 [RankingNLPSystems](https://github.com/PierreColombo/RankingNLPSystems) 的 `utils.py`。  

### 6.2 数据列与代码对应

- **人工六维**：`Relevance`, `Coherence`, `Empathy`, `Surprise`, `Engagement`, `Complexity`（与 CRITERIA / CRITERIA_LABELS 一致）。  
- **自动指标**：`METRICS_DF.columns[6:]` 为所有自动（及 main 分支下 LLM）指标列；论文分析基于其中 72 种。  
- **相关计算**：notebook 中 `get_overall_correlation` 对应 story-level，`get_system_level_correlation` 对应 system-level；`get_correlation_df` 可生成指标×维度的相关矩阵。  

### 6.3 引用

**COLING 2022（数据集与 72 指标、6 人工维度）：**

```bibtex
@inproceedings{chhun-etal-2022-human,
  title = "Of Human Criteria and Automatic Metrics: A Benchmark of the Evaluation of Story Generation",
  author = "Chhun, Cyril and Colombo, Pierre and Suchanek, Fabian M. and Clavel, Chlo{\'e}",
  booktitle = "Proceedings of the 29th International Conference on Computational Linguistics",
  month = oct,
  year = "2022",
  address = "Gyeongju, Republic of Korea",
  publisher = "International Committee on Computational Linguistics",
  url = "https://aclanthology.org/2022.coling-1.509",
  pages = "5794--5836",
}
```

**TACL 2024（LLM 评估扩展）：** 见仓库 main 分支 README 中的 Citation 块。

---

## 七、与本项目融合的要点

- **人工维度**：可直接将 RE/CH/EM/SU/EG/CX 作为 Judge LLM 的评分维度（或选取子集），并参照论文定义撰写 prompt 中的维度说明与 1-5 分标准。  
- **自动指标**：若对“照片故事”做自动评估，可优先实现或调用 **chrF、BERTScore、BARTScore**；若关心与参考回忆录/访谈的相似度，可保留 reference-based 指标；若关心无参考质量，可加入 **SUPERT**、**Repetition**、**Novelty** 等。  
- **元评估**：若自建故事数据且有多系统/多模型输出，可沿用 **story-level / system-level 相关** + **Kendall/Pearson/Spearman** + **Williams test** 检验指标与人工或与既有 HANNA 维度的一致性。  

以上内容均来自 HANNA 原仓库与 COLING 2022 论文，可直接作为本 benchmark 的指标与方法文档使用与引用。
