# GitHub 上传指南

## 步骤1：在GitHub上创建新仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角的 "+" 号，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: 例如 `photo-story-system` 或 `tencent-capstone-project`
   - **Description**: 照片的故事 - 视觉引导式访谈与叙事生成系统
   - **Visibility**: 选择 Public 或 Private
   - **不要**勾选 "Initialize this repository with a README"（因为我们已经有了）
4. 点击 "Create repository"

## 步骤2：连接本地仓库到GitHub

在GitHub创建仓库后，会显示一个页面，里面有仓库的URL。复制这个URL，然后运行：

```bash
# 添加远程仓库（将 YOUR_USERNAME 和 REPO_NAME 替换为你的实际信息）
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 或者使用SSH（如果你配置了SSH密钥）
# git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git
```

## 步骤3：推送代码到GitHub

```bash
# 推送代码到GitHub（首次推送）
git branch -M main
git push -u origin main
```

## 后续更新工作流程

每次修改代码后，使用以下命令更新GitHub：

```bash
# 1. 查看修改的文件
git status

# 2. 添加修改的文件
git add .

# 或者只添加特定文件
# git add README.md src/story_generator.py

# 3. 提交更改（写清楚这次修改了什么）
git commit -m "描述你的修改内容"

# 4. 推送到GitHub
git push
```

## 常用Git命令

```bash
# 查看当前状态
git status

# 查看提交历史
git log

# 查看远程仓库
git remote -v

# 拉取远程更新（如果多人协作）
git pull

# 创建新分支
git checkout -b feature/new-feature

# 切换分支
git checkout main
```

## 注意事项

1. **不要提交敏感信息**：
   - `.env` 文件（已配置在.gitignore中）
   - API密钥
   - 个人配置信息

2. **提交前检查**：
   - 运行 `git status` 查看要提交的文件
   - 确保没有意外添加敏感文件

3. **提交信息要清晰**：
   - 使用有意义的提交信息
   - 例如："修复故事生成中的bug"、"添加多图处理功能"

## 如果遇到问题

### 问题1：推送被拒绝
```bash
# 如果远程仓库有README等文件，先拉取
git pull origin main --allow-unrelated-histories
# 解决冲突后再次推送
git push
```

### 问题2：忘记添加.gitignore中的文件
```bash
# 从Git中移除但保留本地文件
git rm --cached .env
git commit -m "Remove .env from tracking"
```

### 问题3：修改远程仓库URL
```bash
# 查看当前远程仓库
git remote -v

# 修改远程仓库URL
git remote set-url origin https://github.com/YOUR_USERNAME/NEW_REPO_NAME.git
```
