## 多模型评测框架 - 实施步骤

**✅ 基础设施状态：已完成**
- 评测引擎架构：正常
- 样本集配置：已创建（1 个模板）
- 模型配置：已创建
- 聚合可视化模块：已创建
- 脚本导入：通过验证

---

## 第一步：配置 API 密钥

### 方式 A：更新 models.yaml（推荐）

```yaml
# simulation/config/models.yaml
models:
  gemini:
    enabled: true
    api_key: "${GEMINI_API_KEY}"  # 从 Google AI Studio 获取
  hunyuan:
    enabled: true
    api_key: "${HUNYUAN_API_KEY}"  # 从 Tencent 控制台获取
  qwen:
    enabled: false
    api_key: "${QWEN_API_KEY}"
  deepseek:
    enabled: false
    api_key: "${DEEPSEEK_API_KEY}"
  minimax:
    enabled: false
    api_key: "${MINIMAX_API_KEY}"
  kimi:
    enabled: false
    api_key: "${KIMI_API_KEY}"
  claude:
    enabled: false
    api_key: "${CLAUDE_API_KEY}"
```

### 方式 B：环境变量

```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your_key"
$env:HUNYUAN_API_KEY = "your_key"
$env:QWEN_API_KEY = "your_key"
$env:DEEPSEEK_API_KEY = "your_key"
$env:MINIMAX_API_KEY = "your_key"
$env:KIMI_API_KEY = "your_key"
$env:CLAUDE_API_KEY = "your_key"

# Windows CMD
set GEMINI_API_KEY=your_key
set HUNYUAN_API_KEY=your_key
```

### 方式 C：直接走通用模型入口（适合手动调试）

```powershell
$env:MODEL_PROVIDER = "openai_compatible"
$env:MODEL_API_KEY = "your_key"
$env:MODEL_API_ENDPOINT = "https://your-endpoint.example.com/v1"
$env:MODEL_TEXT_MODEL = "your_text_model"
$env:MODEL_VISION_MODEL = "your_vision_model"
```

---

## 第二步：扩展测试样本

编辑 `simulation/config/test_samples.json`，从现有图片库中添加 10-20 个样本。

**每个样本需包含：**
```json
{
  "sample_id": "sample_002",
  "image_path": "image/回忆录访谈稿_三份索引/image_name.png",
  "image_description": "图片的文字描述",
  "memoir_text": "与图片相关的回忆录文段",
  "mme_tasks": [
    {"question": "是否有人物?", "answer": "yes"},
    {"question": "是否为黑白照?", "answer": "no"}
  ],
  "mmbench_tasks": [
    {"question": "照片年代?", "options": {"A": "1960s", "B": "1980s"}, "answer": "B"}
  ],
  "hooks": ["时间", "地点", "人物"],
  "reference_story": "模型应生成的参考故事文本"
}
```

**数据来源：**
- 图片路径：`image/回忆录访谈稿_三份索引/` 中已有的图片
- 文本：从 markdown 访谈稿中提取相关段落
  - `回忆录成文与访谈稿_知青篇.md`
  - `回忆录成文与访谈稿_乡村教师篇.md`
  - `回忆录成文与访谈稿_个体户篇.md`

---

## 第三步：运行单模型评测

```bash
cd "d:\desktop\Tencent Capstone Project"

# 评测 Gemini
python simulation/scripts/eval_single_model.py --model gemini --verbose

# 评测 Hunyuan
python simulation/scripts/eval_single_model.py --model hunyuan --verbose

# 评测所有启用的模型
python simulation/scripts/eval_single_model.py --all-models
```

**输出位置：**
- `simulation/evaluation/gemini/gemini_results.json`
- `simulation/evaluation/hunyuan/hunyuan_results.json`

---

## 第四步：汇总与可视化

```bash
# 生成对比表格与图表
python simulation/scripts/aggregate_results.py

# 输出：
# - simulation/evaluation/summary_table.csv
# - simulation/evaluation/benchmark_comparison.png
# - simulation/evaluation/radar_comparison.png
```

---

## 关键参数说明

| 参数 | 说明 | 默认值 |
|-----|------|--------|
| photo_weight | 图片任务权重 | 0.3 |
| story_weight | 故事生成权重 | 0.5 |
| interview_weight | 访谈质量权重 | 0.2 |
| timeout | 单个样本评测超时(秒) | 120 |

---

## 评分标准（0-5 分制）

### Photo Score（图片理解）
- 计算：(正确任务数 / 总任务数) × 5

### Story Score（故事生成）
- 基于 HANNA 六维评估：
  - 相关性、连贯性、同理心、惊喜度、参与度、复杂度

### Interview Score（访谈质量）
- 四维评分加权：
  - 答案质量：35%
  - 信息完整性：35%
  - 问题深度：20%
  - 话题覆盖：10%

### Final Score（综合分）
```
Final = Photo × 0.3 + Story × 0.5 + Interview × 0.2
```

---

## 常见问题

### Q: 调用 demo/judge_final.py 时出错
A: 检查 demo/src/ 中的三个 judge 模块是否完整（photo_judge.py, story_judge.py, interview_judge.py）

### Q: matplotlib 不可用
A: `pip install matplotlib numpy`

### Q: 样本图片路径找不到
A: 确保 test_samples.json 中的 image_path 相对于项目根目录正确

### Q: 如何添加新模型
A: 在 models.yaml 中添加新条目，并选择 provider 为 `gemini` / `hunyuan` / `openai_compatible` / `anthropic`

---

## 下一步快速检查清单

- [ ] 获取 Gemini API Key（Google AI Studio）
- [ ] 获取 Hunyuan API Key（Tencent 控制台）
- [ ] 如需 7 模型评测，补齐 Qwen / DeepSeek / MiniMax / Kimi / Claude 的 API Key
- [ ] 更新 models.yaml 中的 API 密钥
- [ ] 准备 10-20 个样本到 test_samples.json
- [ ] 运行 `python simulation/scripts/eval_single_model.py --model gemini --verbose`
- [ ] 验证 `simulation/evaluation/gemini/` 中生成了 JSON 结果
- [ ] 所有模型完成后运行 `python simulation/scripts/aggregate_results.py`
- [ ] 检查 PNG 图表是否正确生成
