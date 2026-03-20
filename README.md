# Tencent Capstone Project

这是一个围绕“AI 辅助口述史与回忆录生成”展开的毕业设计仓库。项目的核心目标，是把老照片、访谈问答和叙事生成串起来，形成一个可以实际演示、可以扩展评测、也可以继续做数据与研究沉淀的完整工作区。

当前仓库不是单一应用，而是由主系统、评测设计、模拟流水线和素材文档几个部分组成。

## 项目概览

这个项目主要解决三个问题：

- 如何根据一张老照片自动生成更像“访谈者”而不是“表单机器人”的问题。
- 如何在多轮问答后，把视觉信息和口述内容整合成一篇更自然、更连贯的故事文本。
- 如何为这类系统设计可复用的 benchmark、模拟数据和评分方法，便于后续比较不同版本的效果。

从仓库现状来看，系统已经有三个比较明确的层次：

- 演示层：面向展示的照片故事生成系统。
- 研究层：围绕追问机制、故事质量和评测指标展开的方法探索。
- 数据层：围绕模拟样本、访谈稿、回忆录素材和 benchmark 文档进行整理。

## 核心能力

主应用目前围绕“照片的故事”这个 demo 展开，已经具备以下能力：

- 单图深挖：针对单张照片做视觉分析、访谈追问和故事生成。
- 多图叙事链：把多张照片串联成跨时间线的人生叙事。
- 增强追问机制：根据回答质量、情感信息和信息缺口调整下一轮追问策略。
- 故事生成：把照片分析和访谈内容整合成第一人称或指定风格的叙事文本。
- Web 演示：提供前端页面和后端 API，便于现场展示。
- 文本评分：支持对生成故事做维度化评分。
- 评测与模拟：为后续 benchmark 和实验留有单独目录与文档。

当前默认模型后端已经统一按腾讯混元使用，文档、环境变量示例和运行说明也以混元为主。Gemini 相关逻辑仅保留为兼容备用，不再作为默认推荐方案。

## 仓库结构

以下目录是当前最重要的部分：

- [demo](demo): 主应用目录。包含命令行入口、Flask API、前端和核心 Python 模块。
- [benchmark](benchmark): 评测方法、团队说明、故事生成 benchmark 参考资料。
- [simulation](simulation): 模拟数据、配置文件、脚本和流水线草稿。
- [image](image): 项目相关图片素材与输出资源。
- [回忆录成文与访谈稿_知青篇.md](回忆录成文与访谈稿_知青篇.md): 示例回忆录文本。
- [回忆录成文与访谈稿_乡村教师篇.md](回忆录成文与访谈稿_乡村教师篇.md): 示例访谈与成文素材。
- [回忆录成文与访谈稿_个体户篇.md](回忆录成文与访谈稿_个体户篇.md): 示例人物故事素材。
- [回忆录访谈稿_三份索引.md](回忆录访谈稿_三份索引.md): 三份示例素材的索引。

如果你只是想运行和展示系统，直接从 [demo/README.md](demo/README.md) 开始就够了。

## 主应用说明

[demo](demo) 是这个仓库当前最完整、最适合直接运行的部分，主要包括：

- 命令行交互流程：选择模式、上传图片、完成访谈、生成故事。
- 后端接口：用于给前端提供分析、追问、生成和评分能力。
- 前端界面：用于实际演示照片上传、访谈交互和结果展示。
- 核心模块：图像分析、问题生成、上下文管理、故事生成、评估代理。

相关入口文件包括：

- [demo/main.py](demo/main.py): 命令行交互主入口。
- [demo/server.py](demo/server.py): Flask 后端入口。
- [demo/judge_story.py](demo/judge_story.py): 故事文本评分入口。
- [demo/src/question_generator.py](demo/src/question_generator.py): 问题生成与追问逻辑。
- [demo/src/enhanced_followup.py](demo/src/enhanced_followup.py): 增强追问策略模块。

## 快速开始

最常见的使用方式有两种。

### 1. 运行主应用

先看 [demo/README.md](demo/README.md) 的详细说明。常见步骤是：

```bash
cd demo
pip install -r requirements.txt
python main.py
```

运行前请优先在 [demo/.env](demo/.env) 中配置混元相关变量，例如 `HUNYUAN_API_KEY`。如果未配置混元密钥，主流程不会按当前推荐方式工作。

如果要跑 Web 演示，则通常是：

```bash
cd demo
pip install -r requirements.txt
python server.py
```

然后另开一个终端启动前端：

```bash
cd demo/frontend
npm install
npm run dev
```

### 2. 查看 benchmark 与研究资料

如果你现在关注的是实验设计、指标定义和研究方向，优先看这些文档：

- [benchmark/HANNA_BENCHMARK_TEAM_GUIDE.md](benchmark/HANNA_BENCHMARK_TEAM_GUIDE.md)
- [benchmark/HANNA_BENCHMARK_METRICS_AND_METHODS.md](benchmark/HANNA_BENCHMARK_METRICS_AND_METHODS.md)
- [benchmark/STORY_GENERATION_BENCHMARK_REFERENCE.md](benchmark/STORY_GENERATION_BENCHMARK_REFERENCE.md)
- [simulation/README_STEPS.md](simulation/README_STEPS.md)

## 当前仓库状态说明

这个仓库近期做过一次结构调整：原先位于仓库根目录的应用代码被整理进了 [demo](demo) 目录，所以现在：

- GitHub 仓库首页 README 位于根目录。
- 实际运行说明和应用细节位于 [demo/README.md](demo/README.md)。
- benchmark、simulation 和示例素材作为并列目录保留。

如果你看到某些旧 PR 还在引用根目录下的 `main.py`、`config.py`、`src/` 等路径，那通常是因为它们基于旧目录结构创建，不代表当前主分支仍按那种方式组织。

## 建议阅读顺序

如果你是第一次打开这个仓库，建议按这个顺序看：

1. [demo/README.md](demo/README.md)
2. [demo/main.py](demo/main.py)
3. [demo/src/question_generator.py](demo/src/question_generator.py)
4. [benchmark/HANNA_BENCHMARK_TEAM_GUIDE.md](benchmark/HANNA_BENCHMARK_TEAM_GUIDE.md)
5. [simulation/README_STEPS.md](simulation/README_STEPS.md)

这样会比较容易理解这个仓库里“应用演示、追问研究、评测设计、模拟数据”之间的关系。