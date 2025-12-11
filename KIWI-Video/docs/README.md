# KIWI-Video 文档中心

欢迎来到 KIWI-Video 文档中心！这里包含了所有你需要了解的关于 KIWI-Video 的信息。

---

## 📚 文档导航

### 🚀 新手入门

如果你是第一次使用 KIWI-Video，从这里开始：

1. **[快速入门指南](QUICK_START_GUIDE.md)** ⭐
   - 5分钟快速上手
   - 第一个视频生成示例
   - 常用命令和API使用
   - 故障排除

### 🏗️ 架构与设计

了解 KIWI-Video 的系统设计：

2. **[架构图和流程图](ARCHITECTURE_DIAGRAMS.md)**
   - 系统总体架构
   - 完整工作流程序列图
   - Agent详细工作流
   - 数据流图
   - 状态转换图

### 🔧 技术深入

深入了解技术实现细节：

3. **[技术文档](TECHNICAL_DOCUMENTATION.md)**
   - 项目概述
   - 系统架构详解
   - 核心模块详解
   - 工作流程详解
   - 智能体(Agent)系统
   - 服务提供者(Providers)
   - API接口
   - 数据流与状态管理
   - 文件结构与输出
   - 配置与环境
   - 扩展开发指南

---

## 📖 按主题浏览

### 安装和配置

- [环境准备](QUICK_START_GUIDE.md#1-环境准备)
- [配置API密钥](QUICK_START_GUIDE.md#2-配置api密钥)
- [验证环境](QUICK_START_GUIDE.md#3-验证环境)
- [配置与环境](TECHNICAL_DOCUMENTATION.md#配置与环境)

### 使用指南

- [Python API使用](QUICK_START_GUIDE.md#5-使用python-api)
- [REST API使用](QUICK_START_GUIDE.md#📝-api使用示例)
- [Docker部署](QUICK_START_GUIDE.md#-常用命令)

### 核心概念

- [音频优先工作流](QUICK_START_GUIDE.md#音频优先工作流)
- [多智能体架构](QUICK_START_GUIDE.md#多智能体架构)
- [状态管理](QUICK_START_GUIDE.md#状态管理)
- [工作流程详解](TECHNICAL_DOCUMENTATION.md#工作流程详解)

### 开发扩展

- [添加新的Agent](TECHNICAL_DOCUMENTATION.md#添加新的agent)
- [添加新的Provider](TECHNICAL_DOCUMENTATION.md#添加新的provider)
- [自定义提示词模板](TECHNICAL_DOCUMENTATION.md#自定义提示词模板)
- [添加新的API端点](TECHNICAL_DOCUMENTATION.md#添加新的api端点)

---

## 🎯 快速链接

### 常见任务

| 任务 | 文档链接 |
|------|----------|
| 生成第一个视频 | [快速入门 - 运行第一个视频生成](QUICK_START_GUIDE.md#4-运行第一个视频生成) |
| 理解工作流程 | [技术文档 - 工作流程详解](TECHNICAL_DOCUMENTATION.md#工作流程详解) |
| API集成 | [快速入门 - API使用示例](QUICK_START_GUIDE.md#📝-api使用示例) |
| 故障排除 | [快速入门 - 故障排除](QUICK_START_GUIDE.md#🐛-故障排除) |
| 自定义开发 | [技术文档 - 扩展开发指南](TECHNICAL_DOCUMENTATION.md#扩展开发指南) |

### 架构图表

| 图表 | 文档链接 |
|------|----------|
| 系统架构图 | [架构图 - 系统总体架构](ARCHITECTURE_DIAGRAMS.md#系统总体架构) |
| 工作流序列图 | [架构图 - 完整工作流程序列图](ARCHITECTURE_DIAGRAMS.md#完整工作流程序列图) |
| 音频优先对比 | [架构图 - 音频优先工作流对比](ARCHITECTURE_DIAGRAMS.md#音频优先工作流对比) |
| 数据流图 | [架构图 - 数据流图](ARCHITECTURE_DIAGRAMS.md#数据流图) |
| 状态转换图 | [架构图 - 状态转换图](ARCHITECTURE_DIAGRAMS.md#状态转换图) |

---

## 🔍 深入了解

### Phase 1: 脚本生成 (StoryLoader)

- **概述**: [工作流程 - Phase 1](TECHNICAL_DOCUMENTATION.md#phase-1-脚本生成-storyloader-agent)
- **架构**: [StoryLoader Agent流程](ARCHITECTURE_DIAGRAMS.md#storyloader-agent)
- **代码**: `kiwi_video/agents/story_loader.py`

### Phase 2: 音频生成 (VoiceActor) ⭐

- **概述**: [工作流程 - Phase 2](TECHNICAL_DOCUMENTATION.md#phase-2-音频生成-voiceactor-agent)
- **架构**: [VoiceActor Agent流程](ARCHITECTURE_DIAGRAMS.md#voiceactor-agent)
- **代码**: `kiwi_video/agents/voice_actor.py`
- **为什么音频优先**: [音频优先架构](ARCHITECTURE_DIAGRAMS.md#音频优先工作流对比)

### Phase 3: 分镜创建 (Storyboard)

- **概述**: [工作流程 - Phase 3](TECHNICAL_DOCUMENTATION.md#phase-3-分镜创建-storyboard-agent)
- **架构**: [Storyboard Agent流程](ARCHITECTURE_DIAGRAMS.md#storyboard-agent)
- **代码**: `kiwi_video/agents/storyboard.py`

### Phase 4: 视频制作 (FilmCrew)

- **概述**: [工作流程 - Phase 4](TECHNICAL_DOCUMENTATION.md#phase-4-视频制作-filmcrew-agent)
- **架构**: [FilmCrew Agent流程](ARCHITECTURE_DIAGRAMS.md#filmcrew-agent)
- **代码**: `kiwi_video/agents/film_crew.py`

### Phase 5: 最终合成

- **概述**: [工作流程 - Phase 5](TECHNICAL_DOCUMENTATION.md#phase-5-最终合成)
- **代码**: `kiwi_video/utils/video_processor.py`

---

## 💡 最佳实践

### 提示词编写

详见: [快速入门 - 最佳实践](QUICK_START_GUIDE.md#1-提示词编写)

**好的提示词示例**:
```
创建一个30秒的视频,展示未来城市的交通系统,包括:
- 飞行汽车在摩天大楼间穿梭
- 地下超高速列车
- 自动驾驶公交车
风格: 科幻、专业
```

### 性能优化

详见: [快速入门 - 最佳实践](QUICK_START_GUIDE.md#3-性能优化)

- 并行处理多个项目
- 复用Provider实例
- 定期清理旧项目

### 错误处理

详见: [快速入门 - 最佳实践](QUICK_START_GUIDE.md#4-错误处理)

- 总是捕获异常
- 使用状态恢复机制

---

## 🔧 技术参考

### 核心模块

| 模块 | 文档 | 代码位置 |
|------|------|----------|
| DirectorOrchestrator | [详细说明](TECHNICAL_DOCUMENTATION.md#1-导演编排器-directororchestrator) | `kiwi_video/core/orchestrator.py` |
| BaseAgent | [详细说明](TECHNICAL_DOCUMENTATION.md#2-基础智能体-baseagent) | `kiwi_video/core/base_agent.py` |
| StateManager | [详细说明](TECHNICAL_DOCUMENTATION.md#3-状态管理器-statemanager) | `kiwi_video/core/state_manager.py` |

### Providers

| Provider | 文档 | 代码位置 |
|----------|------|----------|
| Gemini LLM | [详细说明](TECHNICAL_DOCUMENTATION.md#llm-provider-gemini) | `kiwi_video/providers/llm/gemini_client.py` |
| Google Veo | [详细说明](TECHNICAL_DOCUMENTATION.md#video-provider-veo) | `kiwi_video/providers/video/veo_client.py` |
| ElevenLabs | [详细说明](TECHNICAL_DOCUMENTATION.md#voice-provider-elevenlabs) | `kiwi_video/providers/voice/elevenlabs_client.py` |

### API端点

| 端点 | 文档 | 代码位置 |
|------|------|----------|
| 项目管理 | [详细说明](TECHNICAL_DOCUMENTATION.md#项目管理api) | `kiwi_video/api/routes/projects.py` |
| 健康检查 | [详细说明](TECHNICAL_DOCUMENTATION.md#健康检查api) | `kiwi_video/api/routes/health.py` |

---

## 📁 文件结构参考

### 工作区结构

详见: [技术文档 - 工作区目录结构](TECHNICAL_DOCUMENTATION.md#工作区目录结构)

```
workspaces/project_abc123/
├── project_state.json          # 项目状态
├── history.jsonl              # 操作历史
├── annotated_script.json      # 脚本
├── audio/                     # 音频文件
├── storyboard.json            # 分镜
├── assets/                    # 视频素材
├── clips/                     # 场景片段
└── final_video.mp4           # 最终输出
```

### 关键文件格式

- [annotated_script.json](TECHNICAL_DOCUMENTATION.md#annotated_scriptjson)
- [storyboard.json](TECHNICAL_DOCUMENTATION.md#storyboardjson)
- [audio/scene_*_asr.json](TECHNICAL_DOCUMENTATION.md#audioscene_001_asrjson)
- [project_state.json](TECHNICAL_DOCUMENTATION.md#project_statejson)

---

## ❓ 常见问题

### 安装和配置

**Q: 为什么需要Google Cloud凭证？**

A: KIWI-Video使用Google Veo API进行视频生成，需要GCP服务账户凭证。详见[配置指南](QUICK_START_GUIDE.md#2-配置api密钥)。

**Q: 可以不使用Veo吗？**

A: 可以，你可以实现自己的VideoProvider来替换Veo。详见[添加新Provider](TECHNICAL_DOCUMENTATION.md#添加新的provider)。

### 使用问题

**Q: 生成视频需要多长时间？**

A: 通常8-12分钟，取决于场景数量。详见[工作流程概览](QUICK_START_GUIDE.md#📊-工作流程概览)。

**Q: 如何控制视频时长？**

A: 在用户输入中指定时长，例如"创建一个30秒的视频"。系统会自动规划场景时长。

**Q: 为什么音频和视频完美同步？**

A: 我们采用音频优先工作流，先生成音频获取精确时长，再基于此生成视频。详见[音频优先架构](ARCHITECTURE_DIAGRAMS.md#音频优先工作流对比)。

### 故障排除

**Q: Gemini API报错怎么办？**

A: 检查API密钥、配额和网络。详见[故障排除](QUICK_START_GUIDE.md#🐛-故障排除)。

**Q: Veo生成超时？**

A: Veo生成需要5-10分钟，是正常现象。确保GCP配置正确。

**Q: 如何恢复中断的项目？**

A: 使用状态恢复机制。详见[状态恢复](TECHNICAL_DOCUMENTATION.md#状态恢复机制)。

---

## 🚀 高级主题

### 自定义开发

- [添加新的Agent](TECHNICAL_DOCUMENTATION.md#添加新的agent)
- [添加新的Provider](TECHNICAL_DOCUMENTATION.md#添加新的provider)
- [自定义提示词](TECHNICAL_DOCUMENTATION.md#自定义提示词模板)

### 性能调优

- [并行处理](QUICK_START_GUIDE.md#3-性能优化)
- [资源优化](ARCHITECTURE_DIAGRAMS.md#性能优化流程)

### 生产部署

- [Docker部署](QUICK_START_GUIDE.md#docker命令)
- [部署架构](ARCHITECTURE_DIAGRAMS.md#部署架构-docker)

---

## 📞 获取帮助

### 文档内搜索

使用浏览器的搜索功能 (Ctrl/Cmd + F) 在文档中查找关键词。

### 社区支持

- **GitHub Issues**: 报告bug或请求功能
- **GitHub Discussions**: 技术讨论和问答
- **Email**: support@kiwi-video.com

### 贡献文档

文档有误或需要改进？欢迎提交PR！

---

## 📄 许可证

KIWI-Video 采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。

---

**文档版本**: 1.0.0  
**最后更新**: 2024-12-11  

有问题或建议？欢迎在 [GitHub Issues](https://github.com/your-org/kiwi-video/issues) 反馈！

