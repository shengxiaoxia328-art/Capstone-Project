## 多模型评测框架 - 快速开始 (5 分钟上手)

**系统验证状态：✅ 95% 通过**

---

## 🚀 立即开始 (3 步)

### 1️⃣ 配置 API 密钥 (1 分钟)

**推荐 7 模型名单**
- 国内：Hunyuan、Qwen、DeepSeek、MiniMax、Kimi
- 国外：Gemini、Claude

**你当前这套推荐直接配**
- OpenRouter: mimo / gpt54 / claude_opus / kimi / grok / qwen
- Hunyuan: 官方接口单独配

**获取密钥**
- **Gemini**: https://aistudio.google.com/app/apikeys
- **Hunyuan**: https://hunyuan.cloud.tencent.com/
- **Qwen**: 阿里云百炼
- **DeepSeek**: DeepSeek 开放平台
- **MiniMax**: MiniMax 开放平台
- **Kimi**: Moonshot / Kimi 开放平台
- **Claude**: Anthropic Platform

**设置方式**

**Windows PowerShell：先测试 Hunyuan / Gemini**
```powershell
$env:GEMINI_API_KEY = "your_key_here"
$env:HUNYUAN_API_KEY = "your_key_here"
```

**Windows PowerShell：手动测试通用模型入口**
```powershell
$env:MODEL_PROVIDER = "openai_compatible"
$env:MODEL_API_KEY = "your_key_here"
$env:MODEL_API_ENDPOINT = "https://your-endpoint.example.com/v1"
$env:MODEL_TEXT_MODEL = "your_text_model"
$env:MODEL_VISION_MODEL = "your_vision_model"
```

**Windows PowerShell：你当前这套 OpenRouter + 混元**
```powershell
$env:OPENROUTER_API_KEY = "your_openrouter_key"
$env:OPENROUTER_API_ENDPOINT = "https://openrouter.ai/api/v1"
$env:HUNYUAN_API_KEY = "your_hunyuan_key"
```

**或编辑** `simulation/config/models.yaml`:
```yaml
models:
  gemini:
    enabled: true
    api_key: "your_gemini_key"
  hunyuan:
    enabled: true
    api_key: "your_hunyuan_key"
```

### 2️⃣ 扩展测试样本 (2 分钟)

编辑 `simulation/config/test_samples.json` 添加 10-20 个样本，或者直接使用你现成的 `benchmark_data.json`

**最小 JSON 格式**:
```json
{
  "sample_id": "sample_002",
  "image_path": "image/回忆录访谈稿_三份索引/your_image.png",
  "image_description": "图片描述文字",
  "memoir_text": "与图片关联的回忆录段落",
  "mme_tasks": [
    {"question": "照片中有人吗?", "answer": "yes"},
    {"question": "这是彩照吗?", "answer": "no"}
  ],
  "mmbench_tasks": [
    {
      "question": "照片的年代?",
      "options": {"A": "1960s", "B": "1980s", "C": "2000s", "D": "2020s"},
      "answer": "B"
    }
  ],
  "hooks": ["关键词1", "关键词2", "关键词3"],
  "reference_story": "参考故事文本"
}
```

**兼容的真实数据格式**:
- 支持 `memoir_path` / `interview_path`，脚本会自动读取文本
- 支持 `q` / `a` 字段，脚本会自动转换成评测所需的 `question` / `answer`
- 没有 `sample_id` 时，会自动用图片文件名生成

**快速工具**: 
```bash
python simulation/scripts/sample_manager.py
```

### 3️⃣ 运行评测 (1 秒)

```bash
# 评测单个模型
python simulation/scripts/eval_single_model.py --model mimo --verbose

# 直接跑你自己的 benchmark_data.json
python simulation/scripts/eval_single_model.py --model mimo --samples-file benchmark_data_complete.json --verbose

# 或评测所有配置的模型
python simulation/scripts/eval_single_model.py --all-models

# 聚合所有结果
python simulation/scripts/aggregate_results.py
```

---

## 📊 输出物

运行完成后你会得到：

| 文件 | 说明 |
|-----|------|
| `simulation/evaluation/{model}/results.json` | 模型详细评分 |
| `simulation/evaluation/summary_table.csv` | 对比表格 |
| `simulation/evaluation/benchmark_comparison.png` | 4图表对比 |
| `simulation/evaluation/radar_comparison.png` | 雷达图对比 |

---

## 🎯 评分维度

| 维度 | 权重 | 说明 |
|-----|------|------|
| **Photo** | 30% | MME + MMBench 正确率 |
| **Story** | 50% | 相关性、连贯性、同理心、惊喜度、参与度、复杂度 |
| **Interview** | 20% | 追问深度、信息覆盖、答案质量 |

**综合分数**:
```
Final = Photo × 0.3 + Story × 0.5 + Interview × 0.2
```

---

## 🔧 高级用法

### 修改评分权重
编辑 `simulation/config/models.yaml`:
```yaml
evaluation:
  photo_weight: 0.4      # 改为 0.4
  story_weight: 0.4      # 改为 0.4
  interview_weight: 0.2
```

### 添加新模型
1. 在 `simulation/config/models.yaml` 中新增模型配置
2. 选择 provider：`gemini` / `hunyuan` / `openai_compatible` / `anthropic`
3. 填入 text_model、vision_model、endpoint、api_key
4. 运行 `python simulation/scripts/eval_single_model.py --model new_model`

### 当前 7 模型模板
- `mimo`
- `gpt54`
- `claude_opus`
- `kimi`
- `grok`
- `qwen`
- `hunyuan`

### 单样本快速测试
```bash
python simulation/scripts/eval_single_model.py --model mimo --sample-id 镇长上任 --samples-file benchmark_data_complete.json --verbose
```

---

## ❓ 常见问题

### Q: 评测超时怎么办?
A: 在 `models.yaml` 中调整 `timeout` 参数（单位秒，默认 120s）

### Q: 查看样本详情
A: `python -c "import json; print(json.dumps(json.load(open('simulation/config/test_samples.json'))[0], indent=2, ensure_ascii=False))"`

### Q: 如何从 markdown 提取文本?
A: `python simulation/scripts/sample_manager.py` → 选项 2 → 选择 markdown 文件

### Q: 图表没有生成?
A: 检查 matplotlib 是否安装 → `pip install matplotlib numpy`

---

## 📋 完整流程示例

```bash
# 1. 进入项目目录
cd "d:\desktop\Tencent Capstone Project"

# 2. 配置密钥（一次性）
$env:GEMINI_API_KEY = "xxxxx"
$env:HUNYUAN_API_KEY = "xxxxx"

# 3. 检查系统
python simulation/verify_system.py

# 4. 添加样本（可选：使用工具生成）
# - 手动编辑 simulation/config/test_samples.json
# - 或使用 python simulation/scripts/sample_manager.py

# 5. 运行评测
python simulation/scripts/eval_single_model.py --model gemini
python simulation/scripts/eval_single_model.py --model hunyuan

# 6. 生成报告
python simulation/scripts/aggregate_results.py

# 7. 查看输出
# - simulation/evaluation/summary_table.csv (Excel 打开)
# - simulation/evaluation/benchmark_comparison.png (查看对比图)
```

---

## 📞 调试命令

```bash
# 验证系统完整性
python simulation/verify_system.py

# 查看当前配置
cat simulation/config/models.yaml

# 列出所有样本
python -c "import json; samples = json.load(open('simulation/config/test_samples.json')); print(f'{len(samples)} samples:', [s['sample_id'] for s in samples])"

# 单步调试（评测 Gemini 的第一个样本）
python simulation/scripts/eval_single_model.py --model gemini --sample-id sample_001 --verbose --debug
```

---

## ⏱️ 预期时间消耗

| 步骤 | 时间 | 
|-----|------|
| API 密钥配置 | 1-2 分钟 |
| 样本准备 (10-20个) | 5-10 分钟 |
| 评测运行 (10 样本 × 2 модели) | 5-15 分钟 |
| 报告生成 | <1 分钟 |
| **总计** | **15-30 分钟** |

---

## 🎓 文件树

```
simulation/
├── config/
│   ├── test_samples.json          # 测试样本库
│   └── models.yaml                # 模型配置
├── scripts/
│   ├── eval_single_model.py       # 单模型评测引擎
│   ├── aggregate_results.py       # 结果聚合与可视化
│   └── sample_manager.py          # 样本管理辅助工具
├── evaluation/                    # 结果输出目录
│   ├── summary_table.csv
│   ├── benchmark_comparison.png
│   └── radar_comparison.png
├── verify_system.py               # 系统验证脚本
├── QUICK_START.md                 # 上一个版本的指南
├── IMPLEMENTATION_CHECKLIST.md    # 实施清单
└── README_STEPS.md
```

---

## ✨ 经验法则

- **最少样本**: 8-10 个 (快速验证)
- **推荐样本**: 15-20 个 (有效对比)
- **生产级样本**: 50+ 个 (完整评估)

---

**准备好了吗? 👉 立即运行:**
```bash
python simulation/verify_system.py
```
