# 照片的故事 - 前端

基于 React + Vite + Material UI 的 Web 界面。

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器（需先启动后端 API）
npm run dev
```

浏览器访问 http://localhost:5173 。Vite 会将 `/api` 代理到后端 `http://127.0.0.1:5000`。

## 构建

```bash
npm run build
npm run preview  # 预览构建结果
```

## 后端

在项目根目录启动 API 服务：

```bash
python server.py
```

默认运行在 http://127.0.0.1:5000 。
