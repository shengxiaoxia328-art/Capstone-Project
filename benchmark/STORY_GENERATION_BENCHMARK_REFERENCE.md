# 故事生成板块 · Benchmark 与论文参考

本文档整理**故事生成**相关领域的现有 benchmark、评估框架与重要论文，供本项目的「照片引导访谈 → 叙事/故事生成」模块设计合理 benchmark 时参考。
项目背景：基于多模态理解的视觉引导式访谈与叙事生成系统（回忆录场景），最终产出为「照片故事」文本。

---

## 一、现有 Benchmark 概览

### 1. 纯文本故事生成与写作

| Benchmark                 | 发表/来源               | 任务与数据规模                                         | 评估方式                                                                         | 资源链接                                                                                             |
| ------------------------- | ----------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **WritingBench**    | 2025 (arXiv 2503.05244) | 6 大写作域、100 子域；通用生成式写作                   | Query-dependent 评估框架；细粒度 critic 模型（风格、格式、长度）；支持 7B 级模型 | [GitHub](https://github.com/X-PLUG/WritingBench), [Hugging Face](https://huggingface.co/papers/2503.05244) |
| **STORYWARS**       | 2023                    | 40k+ 协作故事、9.4k 作者；12 类任务（7 理解 + 5 生成） | 全监督 / 少样本 / 零样本；INSTRUCTSTORY 指令微调基线                             | [ADS](https://ui.adsabs.harvard.edu/abs/2023arXiv230508152D/abstract)                                   |
| **Tell Me A Story** | 2024, Google DeepMind   | 复杂写作 prompt + 人类撰写故事                         | 长叙事评估框架；自动指标 + 人工评估                                              | [GitHub](https://github.com/google-deepmind/tell_me_a_story)                                            |
| **WebNovelBench**   | 2025                    | 4k+ 中文网络小说；长篇叙事生成                         | 8 个叙事质量维度；LLM-as-Judge + PCA 聚合                                        | 见 arXiv 2505.14818                                                                                  |

### 2. 多模态故事：图/视频 → 故事 或 故事 → 图/视频

| Benchmark              | 发表/来源               | 任务与数据规模                                                                 | 评估方式                                                                          | 资源链接                                                                                                                                                                               |
| ---------------------- | ----------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **StoryBench**   | NeurIPS 2023            | 连续故事**可视化**（文本→视频）；基于 DiDeMo、OOPS、UVO                 | 人类评估指南 + 自动指标（如 FID/Inception）；三任务：动作执行、故事延续、故事生成 | [GitHub](https://github.com/google/storybench), [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2023/hash/f63f5fbed1a4ef08c857c5f377b5d33a-Abstract-Datasets_and_Benchmarks.html) |
| **ViStoryBench** | 2025 (arXiv 2505.24862) | 80 故事片段、344 角色、509 参考图；**故事可视化**（角色+剧本→图像序列） | 角色一致性、风格相似、提示对齐、美学质量、生成伪影；自动化指标 + 人工验证         | [官网](https://vistorybench.github.io/), [arXiv](https://arxiv.org/html/2505.24862v4)                                                                                                        |
| **SEED-Story**   | ICCV 2025 Workshop      | 多模态长故事生成（文本+图像交织）；StoryStream 数据集                          | 图像风格一致性、故事吸引力、图文连贯性                                            | [Open Access](https://openaccess.thecvf.com/content/ICCV2025W/HiGen/papers/Yang_SEED-Story_Multimodal_Long_Story_Generation_with_Large_Language_Model_ICCVW_2025_paper.pdf)               |
| **MSBench**      | 2024                    | 长视频 + 辅助信息（如音频）→ 叙事式文本                                       | 叙事式输出（非模板 QA）；自动构造数据减少人工标注                                 | 见 arXiv 2412.14965                                                                                                                                                                    |

### 3. 故事生成「评估指标」的 Benchmark（元评估）

| Benchmark          | 发表/来源   | 目标                                               | 维度与数据                                                                                                                         | 资源链接                                                                                                                                                           |
| ------------------ | ----------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **OpenMEVA** | ACL 2021    | 评估「开放域故事生成」所用**自动指标**的好坏 | 与人工判断相关性、跨数据集泛化、连贯性判断、对扰动的鲁棒性；人工标注 + 自动构造样本                                                | [ACL](https://aclanthology.org/2021.acl-long.500/), [GitHub](https://github.com/thu-coai/OpenMEVA), [HF Dataset](https://huggingface.co/datasets/Jiann/OpenMEVA)            |
| **HANNA**    | COLING 2022 | 人类评估标准 + 自动指标与人工的相关性              | 1,056 篇故事（96 prompt × 10 系统）；6 个人工维度：Relevance, Coherence, Empathy, Surprise, Engagement, Complexity；72 种自动指标 | [ACL](https://aclanthology.org/2022.coling-1.509/), [GitHub](https://github.com/dig-team/hanna-benchmark-asg), [Papers with Code](https://paperswithcode.com/dataset/hanna) |

### 4. 叙事理解与长文生成

| Benchmark              | 发表/来源               | 任务与数据规模                                  | 评估方式                                                               | 资源链接                                                                                   |
| ---------------------- | ----------------------- | ----------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **NarraBench**   | 2025 (arXiv 2510.09869) | 叙事理解任务分类 + 78 个现有 benchmark 综述     | 仅约 27% 叙事任务被现有 benchmark 覆盖；缺口：事件、风格、视角、揭示等 | [arXiv](https://arxiv.org/html/2510.09869v2)                                                  |
| **LongGenBench** | ICLR 2025               | 长文生成（16K/32K token）；设计文档、创意写作等 | 多场景、多指令类型、多长度；10 个 SOTA LLM 均表现不足                  | [GitHub](https://github.com/mozhu621/LongGenBench), [arXiv](https://arxiv.org/html/2409.02076v7) |

---

## 二、重要论文列表（按主题）

### 2.1 故事评估综述与标准

- **What Makes a Good Story and How Can We Measure It? A Comprehensive Survey of Story Evaluation**
  - 作者：Dingyi Yang, Qin Jin
  - arXiv: 2408.14622 (2024)
  - 内容：故事讲述任务（文本→文本、视觉→文本、文本→视觉）、评估难点、人工标准、benchmark 数据集、评估指标分类、人机协作评估。
  - 用途：为本项目定义「好故事」维度和指标时做理论依据。

### 2.2 自动指标与人工一致性

- **OpenMEVA: A Benchmark for Evaluating Open-ended Story Generation Metrics**

  - ACL 2021
  - 链接：https://aclanthology.org/2021.acl-long.500/
  - 结论：现有自动指标与人工判断相关性差、难以识别语篇级不连贯、缺乏因果/推理知识；OpenMEVA 提供四维测试套件。
- **Of Human Criteria and Automatic Metrics: A Benchmark of the Evaluation of Story Generation (HANNA)**

  - COLING 2022
  - 链接：https://aclanthology.org/2022.coling-1.509/
  - 结论：提出 6 个正交人工维度（相关性、连贯、共情、惊喜、参与度、复杂度），并系统比较 72 种自动指标与人工的相关性。

### 2.3 多模态与可视化故事

- **StoryBench: A Multifaceted Benchmark for Continuous Story Visualization**

  - NeurIPS 2023 Datasets and Benchmarks
  - 链接：https://proceedings.neurips.cc/paper_files/paper/2023/hash/f63f5fbed1a4ef08c857c5f377b5d33a-Abstract-Datasets_and_Benchmarks.html
  - 内容：文本→视频的连续故事可视化；人类标注与自动指标（如 FID）结合。
- **SEED-Story: Multimodal Long Story Generation with Large Language Model**

  - ICCV 2025 Workshop (HiGen)
  - 内容：图文交织的长故事生成；StoryStream 数据集；风格一致性、故事吸引力、图文连贯性评估。
- **ViStoryBench: Comprehensive Benchmark Suite for Story Visualization**

  - arXiv 2505.24862 (2025)
  - 内容：角色+剧本→图像序列；角色一致性、风格、对齐、美学等自动指标。

### 2.4 写作与长文生成

- **WritingBench: A Comprehensive Benchmark for Generative Writing**

  - arXiv 2503.05244 (2025)
  - 内容：多域写作评估、query-dependent 标准、critic 模型；可借鉴「风格/格式/长度」的细粒度设计。
- **LongGenBench: Benchmarking Long-Form Generation in Long Context LLMs**

  - ICLR 2025
  - 内容：长文生成能力评估；若回忆录/故事较长可参考其长度与指令设计。

### 2.5 叙事与评估框架

- **NarraBench: A Comprehensive Framework for Narrative Benchmarking**
  - arXiv 2510.09869 (2025)
  - 内容：叙事理解任务分类、78 个 benchmark 综述、当前评估缺口（事件、风格、视角等）；适合做「叙事维度」设计的参考。

---

## 三、与本项目的对应关系

| 本项目环节                                | 可参考的 Benchmark/论文                                                | 可借鉴点                                                                                  |
| ----------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **故事生成质量**（访谈+图像→故事） | WritingBench, Tell Me A Story, OpenMEVA, HANNA                         | 写作/叙事维度（风格、连贯、长度）；人工维度（相关性、连贯、参与度）；自动指标与人工的取舍 |
| **多模态一致性**（图+对话→故事）   | SEED-Story, ViStoryBench, StoryBench                                   | 图文一致性、风格一致性、叙事连贯性                                                        |
| **评估标准与 Judge**                | HANNA 六维、OpenMEVA 四维、SIMULATION_DATASET_FRAMEWORK 中的 Judge LLM | 内容相似度、风格相似度、完整性；可增加「与回忆录原文/访谈对话的一致性」                   |
| **长叙事与回忆录体**                | LongGenBench, WebNovelBench, NarraBench                                | 长文结构、叙事视角、时间线、人物一致性                                                    |
| **自动化 vs 人工**                  | OpenMEVA, HANNA, “What Makes a Good Story” 综述                      | 自动指标用于开发迭代，人工/Judge 用于最终评估与校准                                       |

---

## 四、设计本项目 Benchmark 的实用建议

1. **明确故事生成输入与输出**

   - 输入：本系统 = 多模态分析结果 + 多轮访谈 QA（+ 可选单图/多图）。
   - 输出：一段「照片故事」文本（回忆录风格）。
   - Ground Truth：腾讯回忆录原文（或仿真对话拼接）可作为内容/风格参照。
2. **评估维度建议（结合 HANNA + 现有 Judge 设计）**

   - **内容一致性**：与回忆录原文/仿真对话在事实、人物、时间、地点上的一致（已有）。
   - **风格相似度**：语气、用词、叙事方式与回忆录或目标风格的接近程度（已有）。
   - **连贯性**：句间、段间、多图间逻辑与时间顺序（可参考 OpenMEVA/NarraBench）。
   - **完整性**：是否覆盖关键信息、是否有明显缺失或重复（可参考 WebNovelBench 的维度）。
   - 可选：**参与度/可读性**（HANNA）、**与图像的对应**（多模态维度）。
3. **数据与规模**

   - 沿用 `benchmark/SIMULATION_DATASET_FRAMEWORK.md`：回忆录文段 → 仿真图 → 仿真对话 → 生成故事；同一批数据上可对比「不同故事生成策略/提示/模型」。
   - 若需与社区对比，可选用 OpenMEVA/HANNA 的 prompt 或故事子集做「纯文本故事」的补充实验。
4. **自动指标与 Judge**

   - 自动：可引入与 OpenMEVA 兼容的连贯性/重复率等指标，或 SEED-Story 风格的图文对齐分数（若有多模态模型接口）。
   - Judge：继续用 LLM-as-Judge，将上述维度写进 Prompt，输出 1–5 分 + 评语；建议用 HANNA/人工抽检做校准。
5. **论文与代码复用**

   - 实现与报告时可直接引用：OpenMEVA（指标评估）、HANNA（人工维度）、WritingBench（写作评估框架）、NarraBench（叙事任务分类）、SEED-Story/ViStoryBench（多模态故事）。

---

## 五、资源链接汇总

- **OpenMEVA**: https://github.com/thu-coai/OpenMEVA
- ***HANNA**: https://github.com/dig-team/hanna-benchmark-asg*
- **WritingBench**: https://github.com/X-PLUG/WritingBench
- ***StoryBench**: https://github.com/google/storybench*
- **Tell Me A Story**: https://github.com/google-deepmind/tell_me_a_story
- **ViStoryBench**: https://vistorybench.github.io/
- **LongGenBench**: https://github.com/mozhu621/LongGenBench
- **ACL Anthology (OpenMEVA)**: https://aclanthology.org/2021.acl-long.500/
- **ACL Anthology (HANNA)**: https://aclanthology.org/2022.coling-1.509/
- **故事评估综述**: https://arxiv.org/abs/2408.14622
- **NarraBench**: https://arxiv.org/html/2510.09869v2

---

*文档整理自公开 benchmark 与论文检索，供团队内部参考；实施时请以各项目官方仓库与论文为准。*
