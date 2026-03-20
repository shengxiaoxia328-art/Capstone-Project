# 照片的故事 - 视觉引导式访谈与叙事生成系统

## 项目简介

"照片的故事"是一个基于多模态大模型的智能照片故事生成系统。系统能够深度解析照片内容，自动生成针对性的访谈问题，引导用户展开对话，最终生成图文并茂的照片故事。

当前项目默认和推荐使用腾讯混元 API。仓库中的 Gemini 相关配置与代码路径仅作为兼容保留，不再作为默认说明路线。

系统支持三种使用方式：
- **Web 界面**：Material UI 前端 + Flask API，浏览器中完成选模式、上传、访谈、生成故事（推荐）
- **命令行交互**：运行 `python main.py`，在终端完成完整流程
- **程序化调用**：`main.py` 中的 `PhotoStorySystem` 提供单图/多图处理接口，适合集成

## 核心功能

### 1. 单图深挖
围绕单张照片进行深度分析，生成多个访谈问题，挖掘照片背后的完整故事。

### 2. 多图叙事链
处理多张照片时，系统会：
- 自动关联前后照片的上下文
- 生成跨照片的关联性问题
- 构建连贯的时间线叙事
- 生成完整的多图故事

### 3. 智能问题生成
基于照片的视觉细节（人物表情、服饰、背景、时代特征等）自动生成针对性问题，支持追问机制。

### 4. 上下文管理
使用向量数据库存储和管理跨图片的记忆，确保多图叙事的连贯性。

### 5. 故事生成
融合照片的视觉描述与用户访谈内容，自动生成结构化的照片故事。

### 6. 系统评估
内置评估Agent，可以对系统生成的问题质量进行评估。

## 项目结构

```
.
├── README.md                    # 项目说明文档
├── requirements.txt             # Python依赖包
├── config.py                    # 系统配置文件
├── env_example.txt              # 环境变量配置示例
├── main.py                      # 主程序入口（含交互式流程）
├── server.py                    # Web API 服务（供前端调用）
├── interactive_photo_story.py   # 交互式系统（可选，与 main 功能一致）
├── frontend/                    # Web 前端（React + Vite + Material UI）
├── src/                         # 核心模块目录
│   ├── __init__.py
│   ├── multimodal_analyzer.py  # 多模态图像分析模块
│   ├── question_generator.py   # 智能问题生成模块
│   ├── dialogue_manager.py     # 对话管理模块
│   ├── context_manager.py      # 多图上下文管理模块
│   ├── story_generator.py      # 故事生成模块
│   └── evaluation_agent.py     # 评估Agent模块
├── examples/                    # 示例代码
│   └── demo.py                 # 使用示例
├── test_images/                 # 测试图片目录（可选）
└── vector_db/                   # 向量数据库存储目录（自动生成）
```

## 安装与配置

### 1. 环境要求

- Python 3.8+
- 支持的操作系统：Windows / Linux / macOS

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

系统当前默认使用混元 API。Gemini 配置仍可保留作为兼容备用，但后续使用建议统一按混元配置。

#### 方式一：使用环境变量（推荐）

1. 复制环境变量示例文件：
   ```bash
   # Windows
   copy env_example.txt .env
   
   # Linux/Mac
   cp env_example.txt .env
   ```

2. 编辑 `.env` 文件，填入你的API密钥：
   ```env
   HUNYUAN_API_KEY=your_api_key_here
   HUNYUAN_API_ENDPOINT=https://api.hunyuan.cloud.tencent.com/v1/chat/completions
   # 可选：视觉模型
   # HUNYUAN_VISION_MODEL=hunyuan-vision
   # 可选：文本模型
   # HUNYUAN_TEXT_MODEL=hunyuan-vision
   ```

#### 方式二：直接修改 config.py

编辑 `config.py` 文件，直接设置API密钥（不推荐，安全性较低）。

### 4. 配置说明

主要配置项在 `config.py` 中：

- `HUNYUAN_API_ENDPOINT`: 混元聊天接口地址
- `HUNYUAN_VISION_MODEL`: 图片理解模型名
- `HUNYUAN_TEXT_MODEL`: 问题生成、故事生成和评分使用的文本模型名
- `MAX_DIALOGUE_ROUNDS`: 单张照片最大对话轮数（默认：10）
- `MAX_CONTEXT_LENGTH`: 最大上下文长度（默认：4000）
- `TEMPERATURE`: 生成温度（默认：0.7）
- `VECTOR_DB_PATH`: 向量数据库存储路径（默认：./vector_db）

说明：当前代码会优先读取混元配置。只有在未启用混元、且显式配置了 Gemini 的情况下，才会走 Gemini 兼容路径。

## 使用方法

### Web 界面（推荐）

使用 Material UI 前端在浏览器中完成全流程：

1. **启动后端 API**（项目根目录）：
   ```bash
   pip install -r requirements.txt   # 若未安装，需包含 flask、flask-cors
   python server.py
   ```
   服务运行在 http://127.0.0.1:5000

2. **启动前端**：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   浏览器打开 http://localhost:5173

3. 在页面中：选择模式（单图深挖 / 多图叙事链）→ 上传照片 → 按提示回答问题 → 生成故事，可复制或重新开始。

### 命令行交互模式

适合在终端中完成全流程：

```bash
python main.py
```

运行后会引导你：
1. 选择模式（单图深挖 / 多图叙事链）
2. 选择照片（支持从 `test_images/` 或自定义路径）
3. 系统分析照片并生成访谈问题，逐题回答（支持 `skip`、`done`）
4. 生成照片故事并可选保存

### 程序化调用

适合集成到其他应用或批量处理：

```python
from main import PhotoStorySystem

# 初始化系统
system = PhotoStorySystem()

# 处理单张照片
result = system.process_single_photo("path/to/photo.jpg")
print(result['story'])

# 处理多张照片
results = system.process_multiple_photos([
    "path/to/photo1.jpg",
    "path/to/photo2.jpg"
])
print(results['story'])

# 系统评估
eval_results = system.evaluate_system([
    "path/to/test1.jpg",
    "path/to/test2.jpg"
])
```

更多示例代码请参考 `examples/demo.py`。

### 故事文本评分

如果你已经有一段故事文本，想直接按 HANNA 六维标准评分，可以使用新增的命令行入口：

```bash
python judge_story.py --story-file path/to/story.txt
```

如果你还想提供原始 prompt 或参考回忆录，让相关性评分更准确，可以这样调用：

```bash
python judge_story.py \
   --story-file path/to/story.txt \
   --prompt-file path/to/prompt.txt \
   --reference-file path/to/reference.txt \
   --output evaluation_result.json
```

输出为 JSON，包含：

- `scores`：六个维度的分数（relevance、coherence、empathy、surprise、engagement、complexity）
- `final_score`：六维平均分
- `summary`：整体评语
- `explanations`：每个维度的简短解释

说明：

- 若未提供 `prompt` 或 `reference`，`relevance` 会退化为“主题聚焦度/是否跑题”的判断。
- 该评分器基于 HANNA 六维方法构建，适合快速打样和批量筛选；单篇故事评分仍应结合人工判断。

### 照片分 + 故事分融合评分

如果你已经准备好了照片 benchmark 数据和生成后的故事文本，可以直接计算最终加权分：

```bash
python judge_final.py \
   --benchmark-file path/to/benchmark_data.json \
   --sample-index 0 \
   --image-root path/to/images \
   --story-file path/to/story.txt \
   --photo-weight 0.4 \
   --story-weight 0.6 \
   --output final_evaluation.json
```

说明：

- `benchmark-file` 支持单个样本对象，或样本数组。
- `sample-index` 用来指定当前故事对应哪一条照片 benchmark 样本。
- `photo-weight` 和 `story-weight` 会自动归一化，因此只需要表达相对权重。
- 照片分会输出三部分明细：`mme`、`mmbench`、`hooks`。
- 最终 `final_score` 采用 0-5 分制，其中：
   - 照片分先按 benchmark 原始得分归一化到 0-5；
   - 故事分直接使用 HANNA 六维平均分；
   - 最终分按权重加权求和。

输出 JSON 包含：

- `final_score`：最终融合分
- `weights`：归一化后的照片/故事权重
- `photo_evaluation`：照片 benchmark 的原始分、归一化分和逐题明细
- `story_evaluation`：HANNA 六维评分结果

## 核心模块说明

### MultimodalAnalyzer
多模态图像分析模块，负责：
- 图像内容识别和描述
- 视觉元素提取（人物、场景、物品等）
- 时代特征识别

### QuestionGenerator
智能问题生成模块，负责：
- 基于图像分析结果生成初始问题
- 根据用户回答生成追问
- 问题质量优化

### DialogueManager
对话管理模块，负责：
- 管理问答历史
- 控制对话流程
- 生成对话摘要

### ContextManager
多图上下文管理模块，负责：
- 跨图片信息存储和检索
- 生成跨照片关联问题
- 构建故事时间线

### StoryGenerator
故事生成模块，负责：
- 融合视觉描述和访谈内容
- 生成结构化的照片故事
- 支持单图和多图故事生成

### EvaluationAgent
评估Agent模块，负责：
- 评估问题质量
- 评估回答相关性
- 评估故事深度

## 技术栈

- **Python 3.8+**: 主要编程语言
- **腾讯混元 API**: 当前默认的多模态与文本生成服务
- **LangChain**: 对话流程管理
- **ChromaDB**: 向量数据库，用于上下文存储
- **Sentence Transformers**: 文本向量化
- **Pillow**: 图像处理

## 工作流程

### 单图处理流程
1. 上传照片 → 2. 多模态分析 → 3. 生成问题 → 4. 用户回答 → 5. 生成故事

### 多图处理流程
1. 上传第一张照片 → 2. 分析并生成问题 → 3. 用户回答 → 4. 保存上下文
5. 上传后续照片 → 6. 分析并关联上下文 → 7. 生成关联问题 → 8. 用户回答
9. 重复步骤5-8 → 10. 生成连贯的多图故事

## 注意事项

1. **API密钥安全**：请妥善保管API密钥，不要将 `.env` 文件提交到版本控制系统
2. **图片格式**：支持常见图片格式（jpg, jpeg, png, bmp, gif）
3. **处理时间**：照片分析通常需要30-120秒，故事生成需要30-60秒
4. **向量数据库**：首次运行会自动创建 `vector_db/` 目录，用于存储上下文信息

## 许可证

本项目为腾讯Capstone项目。

## 联系方式

如有问题或建议，请通过项目Issue反馈。
