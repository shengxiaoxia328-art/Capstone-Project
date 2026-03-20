# Simulation 仿真测试集 · 接下来怎么做（分步指南）

你已有一个 `simulation` 文件夹，并按框架建好了目录。下面按**顺序**说明每一步要做什么、产出什么、下一步接什么。

---

## 当前目录结构（已就绪）

```
simulation/
  config/
    config.yaml              # 流水线参数（每段几张图、对话轮数等）
  raw/                       # 原始回忆录
    memoir_001.json          # 示例回忆录（可替换为腾讯真实数据）
  text2image/                # 阶段1 产出（待实现脚本后生成）
  pipeline_output/            # 阶段2+3 产出（待实现脚本后生成）
  evaluation/                 # 阶段4 产出（待实现脚本后生成）
  README_STEPS.md            # 本文件
```

---

## 步骤总览

| 顺序 | 步骤 | 你要做的事 | 产出 |
|------|------|------------|------|
| **0** | 准备原始数据 | 把腾讯回忆录整理成 `raw/memoir_xxx.json` 格式 | `raw/` 下的 JSON |
| **1** | 实现 Text2Image | 写脚本：读文段 → 调文生图 API → 存图 + mapping | `text2image/` 下的图片和 mapping |
| **2** | 实现用户画像提炼 | 写脚本：读回忆录 → 调 LLM → 输出 persona JSON | `config/user_persona_xxx.json` |
| **3** | 实现仿真对话流水线 | 写脚本：对每张图跑 analyzer + 问题生成 + User Sim 回答 | `pipeline_output/` 下的 analysis/dialogue |
| **4** | 实现 Judge LLM | 写脚本：对比原文与仿真对话 → 输出评分 JSON | `evaluation/` 下的 judge 结果 |
| **5** | 汇总评估结果 | 写脚本：遍历 evaluation 生成表格/报告 | 汇总表或报告文件 |

下面按步骤展开。

---

## 步骤 0：准备原始数据（优先做）

**目标**：让后续脚本能统一读取「回忆录 = 多段文本」。

1. **若腾讯给的是 JSON/表格**  
   - 转成和 `raw/memoir_001.json` 一样的结构：`memoir_id`、`title`、`segments`（每段有 `segment_id`、`text`、可选 `metadata`）。  
   - 另存为 `raw/memoir_002.json`、`raw/memoir_003.json` 等。

2. **若腾讯给的是纯文本**  
   - 约定分段方式：按段落、按字数（如每 200 字一段）、或按标题。  
   - 写一个**预处理脚本**（如 `scripts/prepare_raw.py`）：读 txt → 按规则切段 → 输出 `raw/memoir_001.json`。

**检查**：`raw/` 下至少有一个 `memoir_xxx.json`，且能被程序读入并遍历 `segments`。

### 用「一段真实数据」扩展数据集

你有了一段真实回忆录文本时，可以这样加入：

**方式一：用脚本自动添加（推荐）**

在项目根目录或 `simulation` 下执行：

```bash
# 从文本文件添加（文件里一段或多段，按空行分段）
python simulation/scripts/add_segment.py --file 我的回忆.txt --memoir memoir_001 --title "某老师回忆录"

# 只加一段，直接写文本
python simulation/scripts/add_segment.py --text "1986年春节，我们全家在院子里放鞭炮……" --memoir memoir_001

# 新建一本回忆录
python simulation/scripts/add_segment.py --file 新数据.txt --memoir memoir_002 --title "另一本回忆录"
```

脚本会把新段落追加到 `raw/memoir_001.json`（或新建 `memoir_002.json`），并自动生成 `segment_id`（seg_01, seg_02, …）。

**方式二：手动编辑 JSON**

1. 打开 `simulation/raw/memoir_001.json`（或新建 `memoir_002.json`）。
2. 在 `segments` 数组里加一个对象，例如：
   ```json
   {
     "segment_id": "seg_03",
     "text": "把你这段真实数据粘贴到这里",
     "metadata": { "theme": "可选：主题或来源说明" }
   }
   ```
3. 保存。若新建文件，文件名用 `memoir_xxx.json`，且包含 `memoir_id`、`title`、`segments`。

扩展后，后续步骤 1～5（Text2Image、画像、流水线、Judge、汇总）会自然覆盖这些新段落。

---

## 步骤 1：实现 Text2Image（文段 → 仿真图片）

**目标**：每个文段得到 1～3 张仿真图，作为后续的 Ground Truth 图片。

1. **选一种实现方式**  
   - **方式 A**：文段直接作为提示词，调用文生图 API（如腾讯混元文生图、DALL·E 等）。  
   - **方式 B**：先用 LLM 把文段改写成「图像描述」再文生图（图更可控）。

2. **建议在 simulation 下建**  
   - `scripts/text2image.py`（或 `scripts/run_text2image.py`）：  
     - 读 `config/config.yaml` 中的 `max_images_per_segment`、`raw_dir`、`text2image_dir`。  
     - 遍历 `raw/*.json` 的每个 segment，调用文生图，保存到 `text2image/{memoir_id}/{segment_id}/image_0.png`（及 image_1…）。  
     - 在同一目录写 `mapping.json`：`segment_id`、`segment_text`（或摘要）、`image_paths`、可选 `prompt_used`。

3. **运行与检查**  
   - 对 `memoir_001.json` 跑一遍，确认 `text2image/memoir_001/seg_01/` 下出现图片和 `mapping.json`。

**下一步**：有了仿真图后，才能做步骤 2 和 3（画像可先做，不依赖图）。

---

## 步骤 2：实现用户画像提炼

**目标**：从回忆录全文（或按段）提炼「用户画像」，供 User Sim 扮演回忆录主人。

1. **在 simulation 下建**  
   - `scripts/extract_persona.py`：  
     - 读 `raw/memoir_001.json`（或指定 memoir_id）。  
     - 用现有 LLM（Gemini/混元）按固定 Prompt 生成结构化画像，例如：  
       - 称呼、年龄层、身份  
       - 语言风格（简洁/啰嗦、口语/书面）  
       - 关键人物、地点、年代、事件（列表或短句）  
     - 输出保存为 `config/user_persona_memoir_001.json`。

2. **Prompt 要点**  
   - 输入：回忆录全文或拼接后的 segments。  
   - 要求：输出为 JSON，便于 User Sim 在 system prompt 里直接引用。

3. **运行与检查**  
   - 对 `memoir_001` 跑一次，确认 `config/user_persona_memoir_001.json` 存在且格式正确。

**下一步**：步骤 3 的 User Sim 会读取这个文件。

---

## 步骤 3：实现仿真对话流水线（算法 + 用户模拟）

**目标**：对每张仿真图跑一遍「多模态分析 → 问题生成 → 用户模拟回答」，得到完整 QA 对话。

1. **依赖**  
   - 需要能调用 `demo` 里的 `MultimodalAnalyzer`、`DialogueManager`（可把 `demo` 或项目根加入 `sys.path`）。  
   - 需要 User Sim：输入（当前问题 + 当前分析 + 历史 QA + 用户画像），输出一条回答（可新写 `scripts/user_sim.py` 或复用/扩展 `demo/src/evaluation_agent.py`）。

2. **在 simulation 下建**  
   - `scripts/run_pipeline.py`（或类似名字）：  
     - 读 `config/config.yaml`（如 `max_dialogue_rounds`、`text2image_dir`、`pipeline_output_dir`）。  
     - 遍历 `text2image/{memoir_id}/{segment_id}/` 下每张图（如 image_0.png）：  
       - 调用 `analyzer.analyze_image(image_path)` → 写 `pipeline_output/{memoir_id}/{segment_id}/image_0/analysis.json`。  
       - 调用 `dialogue_manager.start_dialogue(photo_id, analysis_result)` 得到初始问题。  
       - 循环：用 User Sim 根据画像 + 当前问题 + 分析 + 历史 QA 生成 answer → `add_answer(question, answer)` → 若还有下一问且未达 `max_dialogue_rounds` 则继续。  
       - 将 `get_dialogue_summary()` 的 `qa_history` 写入 `pipeline_output/.../image_0/dialogue.json`；可选同时保存 `questions.json`。

3. **运行与检查**  
   - 对已有 `text2image` 产出跑一遍，确认 `pipeline_output/.../image_0/` 下有 `analysis.json`、`dialogue.json`。

**下一步**：用这些对话 + 原文做 Judge（步骤 4）。

---

## 步骤 4：实现 Judge LLM（评估打分）

**目标**：对比「腾讯真实回忆录文段」与「该段对应仿真对话」，输出内容/风格相似度分数和评语。

1. **在 simulation 下建**  
   - `scripts/run_judge.py`：  
     - 输入：某段的原文 `segment["text"]` + 该段对应所有仿真对话拼接成的文本（或按图分条）。  
     - 调用 Judge LLM，Prompt 中写清：  
       - 两段文本分别是什么（真实回忆录 vs 基于其生成的照片访谈对话）。  
       - 维度：内容相似度（1–5）、风格相似度（1–5）、可选整体评语。  
       - 要求输出 JSON（如 `content_score`, `style_score`, `comment`）。  
     - 结果写入 `evaluation/{memoir_id}/{segment_id}_image_0_judge.json`（或你们约定命名）。

2. **运行与检查**  
   - 对已有 `pipeline_output` 跑一遍，确认 `evaluation/` 下出现对应的 judge JSON。

**下一步**：步骤 5 汇总这些 JSON。

---

## 步骤 5：汇总评估结果

**目标**：把全部 Judge 结果聚合成表格或简单报告，便于写报告和对比算法。

1. **在 simulation 下建**  
   - `scripts/aggregate_evaluation.py`：  
     - 遍历 `evaluation/**/*_judge.json`，读取 `content_score`、`style_score`、`comment`。  
     - 输出：CSV 或 Excel（列：memoir_id, segment_id, image_id, content_score, style_score, comment），或再算平均分、按段分布等。  
     - 可另存一份 `evaluation/summary.csv` 或 `evaluation/report.md`。

2. **运行与检查**  
   - 跑一次，打开汇总表确认无误。

---

## 建议的实现顺序（时间线）

1. **先做步骤 0**：把腾讯数据整理成 `raw/memoir_xxx.json`（或写预处理脚本）。  
2. **再做步骤 2**：用户画像提炼（不依赖图片，可并行或先做）。  
3. **然后步骤 1**：Text2Image，得到仿真图。  
4. **然后步骤 3**：仿真对话流水线（依赖步骤 1 的图 + 步骤 2 的画像）。  
5. **然后步骤 4**：Judge。  
6. **最后步骤 5**：汇总。

若你还没有文生图 API，可先用「占位图」或「一张通用示例图」把步骤 3 的调用链跑通，再回头接上真正的 Text2Image。

---

## 和 demo 的衔接

- **Analyzer / DialogueManager**：在 `run_pipeline.py` 里把项目根或 `demo` 加入 `sys.path`，然后 `from src.multimodal_analyzer import MultimodalAnalyzer` 等（或 `from main import PhotoStorySystem` 再取用其 analyzer 和 dialogue_manager）。  
- **API 密钥**：沿用 `demo/config.py` 和 `.env`（或在本目录复制一份给脚本用）。  
- **User Sim**：可新建 `simulation/scripts/user_sim.py`，内部读 `config/user_persona_xxx.json` 并调 LLM 生成单条回答；`run_pipeline.py` 里每轮调用它得到 answer 再交给 `add_answer`。

如果你告诉我当前卡在哪一步（例如：没有文生图 API、或不知道 User Sim 的 Prompt 怎么写），我可以按那一步写出具体脚本骨架或 Prompt 示例。
