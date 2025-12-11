# KIWI-Video 快速入门指南

## 🚀 5分钟快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo>
cd KIWI-Video

# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e .
```

### 2. 配置API密钥

```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env文件,填入以下密钥:
# - GEMINI_API_KEY
# - ELEVENLABS_API_KEY
# - GOOGLE_APPLICATION_CREDENTIALS (Veo)
# - GCP_PROJECT_ID
# - GCS_BUCKET
```

### 3. 验证环境

```bash
python check_env.py
```

应该看到所有服务显示 ✅ Connected

### 4. 运行第一个视频生成

```bash
# 使用测试脚本
python test_full_workflow.py
```

等待约5-10分钟,查看生成的视频:

```bash
# 视频位置
ls workspaces/test_*/final_video.mp4

# 播放视频
open workspaces/test_*/final_video.mp4  # Mac
# 或 xdg-open workspaces/test_*/final_video.mp4  # Linux
```

### 5. 使用Python API

```python
import asyncio
from pathlib import Path
from kiwi_video.core.orchestrator import DirectorOrchestrator

async def main():
    # 创建编排器
    orchestrator = DirectorOrchestrator(
        project_id="my_first_video",
        workspace_dir=Path("workspaces/my_first_video")
    )
    
    # 生成视频
    result = await orchestrator.execute_project(
        user_input="创建一个30秒的关于人工智能的视频"
    )
    
    print(f"✅ 视频已生成: {result['final_video_path']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 6. 启动API服务

```bash
# 开发模式
make dev

# 或直接运行
uvicorn kiwi_video.api.app:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看API文档

---

## 📊 工作流程概览

```
输入: "创建一个关于AI的30秒视频"
   │
   ├─► Phase 1: StoryLoader Agent (30秒)
   │     生成5个场景的脚本
   │     输出: annotated_script.json
   │
   ├─► Phase 2: VoiceActor Agent (1分钟) ⭐ 音频优先!
   │     为每个场景生成语音
   │     输出: scene_*.mp3 + ASR数据
   │     获取实际音频时长 (例如: 28.5秒)
   │
   ├─► Phase 3: Storyboard Agent (1分钟)
   │     基于实际音频时长创建分镜
   │     输出: storyboard.json (时长=28.5秒)
   │
   ├─► Phase 4: FilmCrew Agent (5-8分钟)
   │     为每个场景生成视频并合成
   │     输出: scene_*_clip.mp4
   │
   └─► Phase 5: VideoProcessor (30秒)
         拼接所有场景
         输出: final_video.mp4 (时长=28.5秒) ✅
```

**总耗时**: 约 8-12 分钟 (取决于场景数量和Veo生成速度)

---

## 🔑 关键概念

### 音频优先工作流

**为什么音频优先?**

传统流程:
```
脚本 → 分镜(估算8秒) → 视频生成(8秒) → 音频生成(实际7.5秒) → ❌ 不匹配!
```

KIWI-Video流程:
```
脚本 → 音频生成(7.5秒) → 分镜(7.5秒) → 视频生成(7.5秒) → ✅ 完美同步!
```

### 多智能体架构

每个Agent负责专门的任务:

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| StoryLoader | 脚本生成 | 用户输入 | 场景列表 |
| VoiceActor | 语音合成 | 场景文本 | 音频+时长 |
| Storyboard | 分镜设计 | 场景+音频时长 | 镜头计划 |
| FilmCrew | 视频制作 | 分镜+音频 | 视频片段 |

### 状态管理

所有进度保存在 `project_state.json`:

```json
{
  "status": "processing",
  "current_phase": "film_crew",
  "phases": {
    "story_loader": {"status": "completed"},
    "voice_actor": {"status": "completed"},
    "storyboard": {"status": "completed"},
    "film_crew": {"status": "processing"}
  }
}
```

可以随时中断和恢复!

---

## 🛠️ 常用命令

### Makefile命令

```bash
make setup      # 首次安装
make dev        # 启动开发服务器
make test       # 运行测试
make lint       # 代码检查
make format     # 代码格式化
make clean      # 清理临时文件
```

### 项目管理

```bash
# 列出所有项目
ls workspaces/

# 查看项目状态
cat workspaces/project_*/project_state.json | jq .status

# 清理失败的项目
rm -rf workspaces/failed_project_*

# 查看日志
tail -f logs/kiwi-video.log
```

### Docker命令

```bash
# 构建镜像
docker build -t kiwi-video .

# 运行容器
docker run -p 8000:8000 -v $(pwd)/workspaces:/app/workspaces kiwi-video

# 使用docker-compose
docker-compose up -d
docker-compose logs -f
```

---

## 📝 API使用示例

### 创建项目并生成视频

```bash
# 1. 创建项目
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "创建一个关于太空探索的激动人心的视频",
    "style": "cinematic",
    "duration": 30
  }' | jq .

# 返回: {"project_id": "project_xyz", ...}

# 2. 启动生成
curl -X POST http://localhost:8000/api/v1/projects/project_xyz/generate

# 3. 查询状态 (每10秒查询一次)
watch -n 10 'curl -s http://localhost:8000/api/v1/projects/project_xyz | jq .status'

# 4. 下载视频 (当status=completed)
curl -O http://localhost:8000/api/v1/projects/project_xyz/video
```

### Python客户端

```python
import httpx
import asyncio

async def create_video(prompt: str):
    async with httpx.AsyncClient() as client:
        # 创建项目
        response = await client.post(
            "http://localhost:8000/api/v1/projects",
            json={"prompt": prompt}
        )
        project = response.json()
        project_id = project["project_id"]
        print(f"项目已创建: {project_id}")
        
        # 启动生成
        await client.post(
            f"http://localhost:8000/api/v1/projects/{project_id}/generate"
        )
        
        # 轮询状态
        while True:
            response = await client.get(
                f"http://localhost:8000/api/v1/projects/{project_id}"
            )
            status = response.json()["status"]
            print(f"状态: {status}")
            
            if status == "completed":
                break
            elif status == "failed":
                raise Exception("生成失败")
            
            await asyncio.sleep(10)
        
        # 下载视频
        response = await client.get(
            f"http://localhost:8000/api/v1/projects/{project_id}/video"
        )
        
        with open("output.mp4", "wb") as f:
            f.write(response.content)
        
        print("✅ 视频已下载: output.mp4")

# 运行
asyncio.run(create_video("创建一个关于海洋的美丽视频"))
```

---

## 🐛 故障排除

### 问题: Gemini API错误

```
Error: PERMISSION_DENIED
```

**解决方案**:
1. 检查 `GEMINI_API_KEY` 是否正确
2. 确认API密钥已启用 Gemini API
3. 检查API配额是否用完

### 问题: Veo生成失败

```
Error: Video generation timeout
```

**解决方案**:
1. Veo生成可能需要较长时间(5-10分钟)
2. 检查 `GOOGLE_APPLICATION_CREDENTIALS` 路径
3. 确认GCP项目已启用 Vertex AI API
4. 检查GCS bucket权限

### 问题: ElevenLabs音频生成慢

```
Warning: Voice synthesis taking longer than expected
```

**解决方案**:
1. 检查网络连接
2. 确认 `ELEVENLABS_API_KEY` 有效
3. 检查API配额限制
4. 考虑使用更快的voice模型

### 问题: 视频音频不同步

这不应该发生! 如果出现:

1. 检查是否使用了音频优先流程
2. 查看 `project_state.json` 中的 `audio_duration`
3. 确认 FilmCrew 使用了正确的音频时长
4. 提交Issue并附带日志

### 问题: 内存不足

```
Error: Cannot allocate memory
```

**解决方案**:
1. 减少场景数量(默认5个,可改为3个)
2. 使用更短的视频时长
3. 增加系统内存
4. 清理临时文件: `rm -rf workspaces/*/temp/`

---

## 💡 最佳实践

### 1. 提示词编写

**好的提示词**:
```
创建一个30秒的视频,展示未来城市的交通系统,包括:
- 飞行汽车在摩天大楼间穿梭
- 地下超高速列车
- 自动驾驶公交车
风格: 科幻、专业
```

**不太好的提示词**:
```
做个视频
```

### 2. 项目管理

- 使用有意义的 `project_id`:
  ```python
  orchestrator = DirectorOrchestrator(
      project_id=f"ai_education_{timestamp}"
  )
  ```

- 定期清理旧项目:
  ```bash
  find workspaces/ -mtime +7 -type d -exec rm -rf {} +
  ```

### 3. 性能优化

- 并行处理多个项目(使用异步):
  ```python
  tasks = [
      orchestrator1.execute_project(input1),
      orchestrator2.execute_project(input2)
  ]
  results = await asyncio.gather(*tasks)
  ```

- 复用Provider实例:
  ```python
  veo_client = VeoClient()  # 创建一次
  
  for scene in scenes:
      # 复用同一个client
      await veo_client.generate_and_download(...)
  ```

### 4. 错误处理

- 总是捕获异常:
  ```python
  try:
      result = await orchestrator.execute_project(input)
  except KiwiVideoError as e:
      logger.error(f"生成失败: {e}")
      # 清理资源
  ```

- 使用状态恢复:
  ```python
  if state['status'] == 'failed':
      # 从失败点重试
      orchestrator = recover_project(project_id)
  ```

---

## 📚 进阶主题

### 自定义Agent

查看 [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) 的"扩展开发指南"章节。

### 性能调优

1. **减少LLM调用次数** - 使用缓存的分镜计划
2. **并行视频生成** - 同时生成多个场景
3. **优化视频处理** - 使用硬件加速(NVENC/VideoToolbox)

### 集成到现有系统

```python
from kiwi_video.core.orchestrator import DirectorOrchestrator

# 在你的应用中
class VideoService:
    def __init__(self):
        self.orchestrator = DirectorOrchestrator()
    
    async def generate_video(self, user_prompt: str) -> str:
        result = await self.orchestrator.execute_project(user_prompt)
        return result['final_video_path']
```

---

## 🔗 相关资源

- **详细技术文档**: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
- **API参考**: [API.md](API.md)
- **贡献指南**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **示例代码**: [examples/](../examples/)
- **常见问题**: [FAQ.md](FAQ.md)

---

## 💬 获取帮助

- **GitHub Issues**: 报告bug或请求功能
- **Discussions**: 技术讨论和问答
- **Email**: support@kiwi-video.com

---

**祝你使用愉快!** 🎉

如果这份指南对你有帮助,欢迎给项目加星 ⭐

