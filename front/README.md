# KIWI-Video Frontend

一个使用 Next.js 15 App Router 和 Clerk 身份验证构建的现代视频平台前端。

## 技术栈

- **框架**: Next.js 15 (App Router)
- **身份验证**: Clerk
- **样式**: Tailwind CSS
- **语言**: TypeScript

## 快速开始

### 1. 安装依赖

```bash
cd front
npm install
```

### 2. 配置环境变量

复制 `env.example` 为 `.env.local`：

```bash
cp env.example .env.local
```

然后在 [Clerk Dashboard](https://dashboard.clerk.com/last-active?path=api-keys) 获取你的 API 密钥，并填入 `.env.local` 文件。

### 3. 启动开发服务器

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看应用。

## Project Structure

```
KIWI-Video/
└── front/
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx          # Root layout (ClerkProvider)
    │   │   ├── page.tsx            # Home page
    │   │   ├── globals.css         # Global styles
    │   │   ├── dashboard/
    │   │   │   └── page.tsx        # Dashboard (voice recording)
    │   │   ├── sign-in/
    │   │   │   └── [[...sign-in]]/
    │   │   │       └── page.tsx    # Sign in page
    │   │   └── sign-up/
    │   │       └── [[...sign-up]]/
    │   │           └── page.tsx    # Sign up page
    │   └── middleware.ts           # Clerk middleware (route protection)
    ├── env.example
    ├── tailwind.config.ts
    └── package.json
```

## Features

- 🎨 **Black/White/Gray Clean Design** - Modern UI inspired by ChatGPT
- 🔐 **Clerk Authentication** - Secure user authentication
- 📱 **Responsive Design** - Adapts to all device sizes
- ⚡ **Next.js 15** - Latest App Router architecture
- 🌙 **Dark Theme** - Eye-friendly dark interface
- 🎤 **Voice Recording** - Record voice to describe video
- 🔄 **Real-time Updates** - WebSocket for live progress
- 📺 **Dashboard** - Video creation workspace

## 许可证

MIT

