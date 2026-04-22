# 多模型评测方案 - 快速开始指南

## 📋 目录结构

```
simulation/
├── config/
│   ├── test_samples.json          # 评测样本集（含图片路径、题目、参考故事）
│   └── models.yaml                # 模型配置（API密钥、端点、开关）
├── scripts/
│   ├── eval_single_model.py       # 单模型评测引擎（主脚本）
│   └── aggregate_results.py       # 结果汇总和可视化
├── evaluation/                     # 评测结果输出目录（自动生成）
│   ├── gemini/
│   │   └── gemini_results.json
│   ├── hunyuan/
│   │   └── hunyuan_results.json
│   ├── summary_table.csv          # 对比表
│   ├── benchmark_comparison.png   # 柱状图
│   └── radar_comparison.png       # 雷达图
└── README_STEPS.md
```

## 🚀 快速使用步骤

### 第一步：配置模型 API

编辑 `simulation/config/models.yaml`，填入你的 API 密钥：

```yaml
models:
  gemini:
    enabled: true
    api_key: "your-gemini-api-key"
  hunyuan:
    enabled: true
    api_key: "your-hunyuan-api-key"
```

或通过环境变量：
```bash
export GEMINI_API_KEY="your-key"
export HUNYUAN_API_KEY="your-key"
```

### 第二步：准备测评样本

编辑或扩展 `simulation/config/test_samples.json`：

```json
[
  {
    "sample_id": "sample_001",
    "image_path": "image/path/to/photo.jpg",
    "image_description": "照片描述...",
    "memoir_text": "回忆录原文...",
    "mme_tasks": [...],
    "mmbench_tasks": [...],
    "hooks": [...],
    "reference_story": "参考故事（可选）"
  }
]
```

每个样本必须包含：
- `sample_id`: 唯一标识符
- `image_path`: 相对于项目根的图片路径
- `image_description`: 图片文本描述
- `memoir_text`: 回忆录原文（作为故事输入）
- `mme_tasks`: MME 是/否题
- `mmbench_tasks`: MMBench 多选题
- `hooks`: 关键叙事钩子列表
- `reference_story`: 参考故事（可选，用于相关性评分）

### 第三步：运行单模型评测

```bash
cd simulation/scripts

# 评测混元模型
python eval_single_model.py --model hunyuan

# 评测 Gemini 模型
python eval_single_model.py --model gemini

# 评测其他模型（需先在 models.yaml 中配置）
python eval_single_model.py --model claude
```

**输出示例**：
```
============================================================
开始评测模型: gemini
样本数: 1
============================================================

[1/1] 评测样本: sample_001... ✓ 完成

============================================================
模型: gemini - 评测完成
============================================================
样本总数: 1
成功: 1
失败: 0

指标         平均分   标准差   最小分   最大分
--------------------------------------------------
photo        4.20     0.00     4.20     4.20
story        3.80     0.00     3.80     3.80
interview    0.00     0.00     0.00     0.00
final        3.64     0.00     3.64     3.64
```

**结果文件**：
```
simulation/evaluation/gemini/gemini_results.json
```

### 第四步：汇总和可视化

```bash
python aggregate_results.py
```

**输出**：
1. 对比表 (CSV)：
   ```
   simulation/evaluation/summary_table.csv
   ```

2. 柱状图：
   ```
   simulation/evaluation/benchmark_comparison.png
   ```
   
3. 雷达图：
   ```
   simulation/evaluation/radar_comparison.png
   ```

## 📊 输出详解

### `{model}_results.json` 结构

```json
{
  "model_name": "gemini",
  "eval_time": "2026-03-27T12:30:00.000000",
  "total_samples": 10,
  "successful_samples": 10,
  "failed_samples": 0,
  "photo": {
    "mean": 4.15,
    "std": 0.35,
    "min": 3.50,
    "max": 4.80
  },
  "story": {
    "mean": 3.92,
    "std": 0.42,
    "min": 3.10,
    "max": 4.60
  },
  "interview": {
    "mean": 3.98,
    "std": 0.38,
    "min": 3.20,
    "max": 4.70
  },
  "final": {
    "mean": 4.02,
    "std": 0.35,
    "min": 3.30,
    "max": 4.70
  },
  "samples": [
    {
      "sample_id": "sample_001",
      "photo_score": 4.20,
      "story_score": 3.80,
      "interview_score": 0.00,
      "final_score": 3.64
    }
  ]
}
```

### `summary_table.csv` 格式

```
模型,样本数,成功数,失败数,照片分(平均),照片分(标准差),故事分(平均),故事分(标准差),访谈分(平均),访谈分(标准差),最终分(平均),最终分(标准差)
gemini,10,10,0,4.15,0.35,3.92,0.42,3.98,0.38,4.02,0.35
hunyuan,10,10,0,4.08,0.38,3.85,0.45,4.05,0.40,3.96,0.38
```

## 🔧 高级用法

### 添加新样本

1. 收集图片、访谈记录、参考故事
2. 设计 MME 和 MMBench 题目
3. 提取关键叙事钩子
4. 添加到 `test_samples.json`：

```python
import json

# 读取现有样本
with open("simulation/config/test_samples.json", "r", encoding="utf-8") as f:
    samples = json.load(f)

# 添加新样本
samples.append({
    "sample_id": "sample_xxx",
    "image_path": "...",
    # ... 其他字段
})

# 保存
with open("simulation/config/test_samples.json", "w", encoding="utf-8") as f:
    json.dump(samples, f, ensure_ascii=False, indent=2)
```

### 添加新模型

1. 在 `models.yaml` 中配置新模型
2. 运行评测脚本（脚本会自动检测）
3. 结果会自动包含在汇总中

```yaml
myllm:
  provider: "custom"
  name: "my-llm-v1"
  api_key: "${MY_LLM_API_KEY}"
  endpoint: "https://api.myllm.com/v1"
  enabled: true
```

## 📈 评分权重

默认权重配置在 `simulation/config/models.yaml`：
- 照片分权重：**0.3**（图片理解能力）
- 故事分权重：**0.5**（故事生成质量）
- 访谈分权重：**0.2**（问答过程质量）

可在 `eval_single_model.py` 中修改。

## ⚠️ 常见问题

### Q: 评测时间太长？
A: 每个样本需要调用多个 LLM API，时间取决于网络和模型响应速度。建议：
- 从少数样本开始测试
- 使用快速模型（如 flash 版本）
- 并行评测多个样本（需修改脚本）

### Q: 图片路径找不到？
A: 确保 `test_samples.json` 中的 `image_path` 是相对于项目根目录的相对路径。

### Q: 访谈分总是 0？
A: 访谈分需要提供 `--qa-history-file`。当前脚本默认权重为 0（可选）。

### Q: 如何只评测部分样本？
A: 修改 `test_samples.json`，临时删除不需要的样本）。

## 📞 下一步

- **扩展样本集**：从你的数据库中添加 10-20 个代表性样本
- **对比更多模型**：在 `models.yaml` 中配置 Claude、LLaMA 等
- **自定义权重**：根据项目重点调整评分权重
- **深度分析**：对低分样本进行人工审查和改进
