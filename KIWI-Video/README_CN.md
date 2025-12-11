# KIWI-Video: 多智能体文本到视频生成框架

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](README.md) | 简体中文

KIWI-Video 是一个生产级的、基于多智能体架构的AI视频生成框架。只需输入文本描述，即可自动生成专业质量的视频内容。

## ✨ 核心特性

- 🤖 **多智能体协作** - 4个专业AI智能体各司其职
- 🎙️ **音频优先工作流** - 先生成音频确定精确时长，确保完美音视频同步
- 🎬 **Google Veo集成** - 使用最先进的AI视频生成技术
- 🧠 **Gemini驱动** - 智能脚本生成和决策
- 🎵 **ElevenLabs TTS** - 高质量语音合成和ASR
- ⚡ **完全异步** - 高性能异步处理
- 🔧 **易于扩展** - 模块化设计，轻松添加新功能

## 🎥 演示视频

```
输入: "创建一个关于未来新加坡的45秒视频"
          ↓
    [8-12分钟处理]
          ↓
输出: final_video.mp4 (完美同步的专业视频)
```

## 🚀 快速开始

### 1. 安装

```bash
# 克隆项目
git clone <your-repo-url>
cd KIWI-Video

# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

### 2. 配置

```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env，填入以下API密钥:
# - GEMINI_API_KEY (Google Gemini)
# - ELEVENLABS_API_KEY (ElevenLabs)
# - GOOGLE_APPLICATION_CREDENTIALS (Google Veo)
# - GCP_PROJECT_ID
# - GCS_BUCKET
```

### 3. 运行

```bash
# 验证环境
python check_env.py

# 运行测试脚本
python test_full_workflow.py

# 或启动API服务
make dev
# 访问 http://localhost:8000/docs
```

## 📖 完整文档

访问 [docs/](docs/) 目录查看详细文档:

- **[快速入门指南](docs/QUICK_START_GUIDE.md)** - 5分钟快速上手
- **[技术文档](docs/TECHNICAL_DOCUMENTATION.md)** - 完整技术说明
- **[架构图](docs/ARCHITECTURE_DIAGRAMS.md)** - 系统架构和流程图
- **[文档导航](docs/README.md)** - 文档中心索引

## 🏗️ 系统架构

```
用户输入 → DirectorOrchestrator (导演编排器)
              ↓
    ┌─────────┼─────────┬─────────┐
    ↓         ↓         ↓         ↓
StoryLoader VoiceActor Storyboard FilmCrew
 (脚本)     (音频)     (分镜)    (视频)
    ↓         ↓         ↓         ↓
    └─────────┴─────────┴─────────┘
              ↓
        VideoProcessor
              ↓
        final_video.mp4
```

### 工作流程

```
Phase 1: StoryLoader Agent (30秒)
   ↓  生成5个场景的结构化脚本

Phase 2: VoiceActor Agent (1分钟) ⭐ 音频优先!
   ↓  为每个场景生成语音并获取精确时长

Phase 3: Storyboard Agent (1分钟)
   ↓  基于实际音频时长创建详细分镜

Phase 4: FilmCrew Agent (5-8分钟)
   ↓  生成视频素材并合成场景片段

Phase 5: VideoProcessor (30秒)
   ↓  拼接所有场景

最终输出: 完美同步的视频 ✅
```

## 🎯 音频优先创新

### 为什么音频优先？

**传统流程的问题**:
```
脚本 → 分镜(估算8秒) → 视频(8秒) → 音频(实际7.5秒) 
→ ❌ 时长不匹配，需要手动调整
```

**KIWI-Video的解决方案**:
```
脚本 → 音频生成(7.5秒) → 分镜(7.5秒) → 视频(7.5秒) 
→ ✅ 完美同步!
```

先生成音频获取精确时长，再基于实际时长规划视频，确保音视频完美同步。

## 💻 使用示例

### Python API

```python
import asyncio
from pathlib import Path
from kiwi_video.core.orchestrator import DirectorOrchestrator

async def main():
    # 创建编排器
    orchestrator = DirectorOrchestrator(
        project_id="my_video",
        workspace_dir=Path("workspaces/my_video")
    )
    
    # 生成视频
    result = await orchestrator.execute_project(
        user_input="创建一个30秒的关于人工智能的激动人心的视频"
    )
    
    print(f"✅ 视频已生成: {result['final_video_path']}")

asyncio.run(main())
```

### REST API

```bash
# 创建项目
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"prompt": "创建一个关于太空探索的视频"}'

# 返回: {"project_id": "project_xyz", ...}

# 启动生成
curl -X POST http://localhost:8000/api/v1/projects/project_xyz/generate

# 查询状态
curl http://localhost:8000/api/v1/projects/project_xyz

# 下载视频
curl -O http://localhost:8000/api/v1/projects/project_xyz/video
```

## 🧩 核心模块

### 智能体系统

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **StoryLoader** | 脚本生成 | 用户输入 | 结构化场景 |
| **VoiceActor** | 语音合成 | 场景文本 | 音频+ASR+时长 |
| **Storyboard** | 分镜设计 | 场景+音频时长 | 镜头计划 |
| **FilmCrew** | 视频制作 | 分镜+音频 | 视频片段 |

### 服务提供者

- **Gemini LLM** - 脚本生成、分镜规划、制作决策
- **Google Veo** - AI视频生成
- **ElevenLabs** - 语音合成和语音识别

## 📁 项目结构

```
KIWI-Video/
├── kiwi_video/              # 核心代码
│   ├── agents/              # 智能体实现
│   │   ├── story_loader.py  # 脚本生成
│   │   ├── voice_actor.py   # 语音合成
│   │   ├── storyboard.py    # 分镜设计
│   │   └── film_crew.py     # 视频制作
│   ├── core/                # 核心模块
│   │   ├── orchestrator.py  # 编排器
│   │   ├── base_agent.py    # Agent基类
│   │   └── state_manager.py # 状态管理
│   ├── providers/           # 服务提供者
│   │   ├── llm/             # LLM接口
│   │   ├── video/           # 视频生成
│   │   └── voice/           # 语音服务
│   ├── api/                 # REST API
│   └── utils/               # 工具函数
├── config/                  # 配置文件
│   └── prompts/             # 提示词模板
├── docs/                    # 文档
├── tests/                   # 测试
└── workspaces/              # 工作区(生成的文件)
```

## 🔧 开发工具

```bash
# 运行测试
make test

# 代码检查
make lint

# 代码格式化
make format

# 启动开发服务器
make dev

# Docker构建
make docker-build

# Docker运行
make docker-up
```

## 🌟 技术亮点

### 1. 音频优先架构 ⭐

先生成音频获取精确时长，再基于此规划视频，确保完美同步。

### 2. 多智能体协作

4个专业AI智能体各司其职，模块化设计易于维护和扩展。

### 3. 状态持久化

完整的状态管理系统，支持中断恢复和进度跟踪。

### 4. 异步处理

全异步架构，高性能并发处理，充分利用资源。

### 5. 类型安全

使用Pydantic进行数据验证，完整的类型注解。

## 📊 性能指标

- **脚本生成**: ~30秒
- **音频生成**: ~1分钟 (5个场景)
- **分镜创建**: ~1分钟
- **视频制作**: ~5-8分钟 (取决于Veo)
- **总耗时**: ~8-12分钟

## 🐛 故障排除

### Gemini API错误

```bash
# 检查API密钥
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"

# 验证环境
python check_env.py
```

### Veo生成超时

Veo生成需要5-10分钟，这是正常的。确保:
1. GCP凭证正确配置
2. Vertex AI API已启用
3. GCS bucket权限正确

### 音频生成失败

检查ElevenLabs API密钥和配额:
```bash
# 验证API密钥
python -c "from elevenlabs import ElevenLabs; client = ElevenLabs(); print(client.voices.get_all())"
```

更多问题请查看[故障排除指南](docs/QUICK_START_GUIDE.md#🐛-故障排除)。

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 开发流程

```bash
# 1. Fork项目
# 2. 创建特性分支
git checkout -b feature/amazing-feature

# 3. 提交更改
git commit -m 'Add amazing feature'

# 4. 推送到分支
git push origin feature/amazing-feature

# 5. 提交Pull Request
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- Google Gemini & Veo 团队
- ElevenLabs
- FastAPI 社区
- 所有贡献者

## 📞 联系我们

- **GitHub Issues**: [报告问题](https://github.com/your-org/kiwi-video/issues)
- **Discussions**: [技术讨论](https://github.com/your-org/kiwi-video/discussions)
- **Email**: support@kiwi-video.com

## 🚀 路线图

### v0.2.0 (计划中)
- [ ] 并行场景生成
- [ ] 更多转场效果
- [ ] 自定义字幕样式
- [ ] 视频质量自动评估

### v0.3.0 (规划中)
- [ ] 多语言支持
- [ ] 图片输入支持
- [ ] 视频编辑功能
- [ ] 背景音乐生成

### 长期目标
- [ ] Web界面
- [ ] 多用户管理
- [ ] 云端部署
- [ ] 商业版本

## ⭐ 给我们加星

如果这个项目对你有帮助，欢迎给我们加星 ⭐！

---

**由 KIWI-Video 团队用 ❤️ 打造**

