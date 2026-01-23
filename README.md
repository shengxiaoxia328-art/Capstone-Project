# 照片的故事 - 视觉引导式访谈与叙事生成系统

## 项目简介

"照片的故事"是一个基于多模态大模型的智能照片故事生成系统。系统能够深度解析照片内容，自动生成针对性的访谈问题，引导用户展开对话，最终生成图文并茂的照片故事。

系统支持两种使用模式：
- **交互式模式**：完整的命令行交互体验，适合个人用户
- **程序化调用**：提供API接口，适合集成到其他应用

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
├── main.py                      # 主程序入口（程序化调用）
├── interactive_photo_story.py   # 交互式系统（推荐使用）
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

系统支持 Gemini API（推荐）或混元API。配置方式有两种：

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
   GEMINI_API_KEY=your_api_key_here
   GEMINI_API_ENDPOINT=https://your_endpoint_here
   ```

#### 方式二：直接修改 config.py

编辑 `config.py` 文件，直接设置API密钥（不推荐，安全性较低）。

### 4. 配置说明

主要配置项在 `config.py` 中：

- `GEMINI_MODEL_NAME`: 使用的模型名称（默认：gemini-2.5-pro）
- `MAX_DIALOGUE_ROUNDS`: 单张照片最大对话轮数（默认：10）
- `MAX_CONTEXT_LENGTH`: 最大上下文长度（默认：4000）
- `TEMPERATURE`: 生成温度（默认：0.7）
- `VECTOR_DB_PATH`: 向量数据库存储路径（默认：./vector_db）

## 使用方法

### 交互式模式（推荐）

适合个人用户，提供完整的交互体验：

```bash
python interactive_photo_story.py
```

运行后会引导你：
1. 选择照片（支持从 `test_images/` 目录选择或输入自定义路径）
2. 系统自动分析照片内容
3. 回答系统生成的访谈问题（支持 `skip` 跳过、`done` 提前结束）
4. 自动生成照片故事
5. 可选择保存结果到文件

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
- **Gemini API / 混元API**: 多模态大模型服务
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
