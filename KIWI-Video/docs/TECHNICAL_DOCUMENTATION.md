# KIWI-Video 技术文档

## 📋 目录

1. [项目概述](#项目概述)
2. [系统架构](#系统架构)
3. [技术栈](#技术栈)
4. [核心模块详解](#核心模块详解)
5. [工作流程详解](#工作流程详解)
6. [智能体(Agent)系统](#智能体agent系统)
7. [服务提供者(Providers)](#服务提供者providers)
8. [API接口](#api接口)
9. [数据流与状态管理](#数据流与状态管理)
10. [文件结构与输出](#文件结构与输出)
11. [配置与环境](#配置与环境)
12. [扩展开发指南](#扩展开发指南)

---

## 项目概述

**KIWI-Video** 是一个生产级的、基于多智能体架构的文本到视频生成框架。它能够将用户的文本描述自动转换为专业质量的视频内容。

### 核心特性

- ✨ **多智能体协作架构** - 每个制作阶段由专门的AI智能体负责
- 🎬 **音频优先工作流** - 先生成音频确定时长，再据此进行精确的视频规划
- 🤖 **Google Veo集成** - 使用最先进的AI视频生成技术
- 🧠 **Gemini LLM** - 智能决策和内容生成
- 🎙️ **ElevenLabs TTS** - 高质量的语音合成和ASR
- 🔄 **完全异步** - 高性能的异步操作
- 📦 **类型安全** - 使用Pydantic进行完整的类型注解
- 🛠️ **易于扩展** - 简单添加新的提供者和智能体

### 应用场景

- 教育视频自动生成
- 营销内容快速制作
- 新闻摘要视频化
- 故事讲述可视化
- 产品演示视频

---

## 系统架构

### 总体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户输入                               │
│              "创建一个关于未来新加坡的45秒视频"               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Director Orchestrator                       │
│                    (导演编排器)                              │
│        统筹管理整个视频生成流程                              │
└───────┬─────────┬──────────┬───────────┬────────────────────┘
        │         │          │           │
        ▼         ▼          ▼           ▼
    ┌─────┐  ┌────────┐ ┌─────────┐ ┌──────────┐
    │Story│  │Voice   │ │Storyboard│ │FilmCrew  │
    │Loader│ │Actor   │ │Agent     │ │Agent     │
    │Agent │ │Agent   │ │智能体    │ │智能体    │
    │智能体│ │智能体  │ └─────────┘ └──────────┘
    └─────┘  └────────┘
        │         │          │           │
        ▼         ▼          ▼           ▼
    ┌─────────────────────────────────────────┐
    │         外部服务提供者层                │
    ├─────────────────────────────────────────┤
    │  Gemini LLM  │  ElevenLabs  │  Veo API  │
    └─────────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │    最终视频输出        │
            │    final_video.mp4     │
            └────────────────────────┘
```

### 核心设计模式

1. **编排者模式(Orchestrator Pattern)** - DirectorOrchestrator统筹所有智能体
2. **代理模式(Agent Pattern)** - 每个智能体封装特定领域的逻辑
3. **提供者模式(Provider Pattern)** - 抽象外部服务接口
4. **状态管理模式** - 集中式状态持久化和恢复

---

## 技术栈

### 核心技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 主编程语言 |
| FastAPI | 0.109.0+ | REST API框架 |
| Pydantic | 2.5.0+ | 数据验证和序列化 |
| Google Gemini | latest | 大语言模型(LLM) |
| Google Veo | latest | AI视频生成 |
| ElevenLabs | 1.0.0+ | 语音合成和ASR |
| MoviePy | 1.0.3+ | 视频处理 |
| FFmpeg | - | 底层视频操作 |

### 开发工具

- **Ruff** - 代码格式化和Linting
- **Pytest** - 测试框架
- **MyPy** - 静态类型检查
- **Uvicorn** - ASGI服务器
- **Loguru** - 日志管理

---

## 核心模块详解

### 1. 导演编排器 (DirectorOrchestrator)

**文件位置**: `kiwi_video/core/orchestrator.py`

**职责**: 统筹管理整个视频生成流程，协调各个智能体的执行顺序。

#### 关键方法

```python
async def execute_project(self, user_input: str) -> dict[str, Any]:
    """
    执行完整的视频生成工作流
    
    流程:
    1. Phase 1: 生成脚本 (StoryLoader)
    2. Phase 2: 生成音频 (VoiceActor) - 音频优先！
    3. Phase 3: 创建分镜 (Storyboard) - 使用实际音频时长
    4. Phase 4: 生成视频片段 (FilmCrew)
    5. Phase 5: 合成最终视频
    
    返回:
        包含最终视频路径和元数据的字典
    """
```

#### 工作流程顺序

```python
# Phase 1: 脚本生成
script_result = await self._run_story_loader(user_input)

# Phase 2: 音频生成 (在分镜之前！)
audio_result = await self._run_voice_actor(script_result)

# Phase 3: 分镜创建 (使用实际音频时长)
storyboard_result = await self._run_storyboard(script_result, audio_result)

# Phase 4: 视频片段生成
clips_results = await self._run_film_crew(storyboard_result, audio_result)

# Phase 5: 最终合成
final_video = await self._compile_final_video(clips_results)
```

#### 音频优先的优势

传统流程的问题:
```
脚本 → 分镜(估算时长) → 视频生成 → 音频生成 → ❌ 时长不匹配
```

KIWI-Video的音频优先流程:
```
脚本 → 音频生成(获取精确时长) → 分镜(使用实际时长) → 视频生成 → ✅ 完美同步
```

### 2. 基础智能体 (BaseAgent)

**文件位置**: `kiwi_video/core/base_agent.py`

**职责**: 所有智能体的抽象基类，提供通用功能。

#### 核心组件

```python
class BaseAgent(ABC):
    """所有智能体的基类"""
    
    def __init__(
        self,
        agent_name: str,           # 智能体名称
        llm_client: BaseLLMClient, # LLM客户端
        state_manager: StateManager,# 状态管理器
        workspace_dir: Path        # 工作目录
    ):
        self.conversation_history = []  # 对话历史
        self.tools = self.register_tools()  # 注册工具
```

#### 必须实现的抽象方法

```python
@abstractmethod
def register_tools(self) -> dict[str, Callable]:
    """注册智能体专用工具"""
    pass

@abstractmethod
def get_system_prompt(self) -> str:
    """返回系统提示词"""
    pass

@abstractmethod
def _execute_workflow(self, input_data: dict) -> dict:
    """执行智能体特定的工作流逻辑"""
    pass
```

#### 智能体循环 (Agent Loop)

```python
def agent_loop(
    self,
    objective: str,           # 目标任务
    goal_check: Callable,     # 目标检查函数
    max_turns: int = 50       # 最大轮次
) -> bool:
    """
    执行智能体循环直到目标达成
    
    循环流程:
    1. 检查目标是否达成
    2. 调用LLM获取决策
    3. 执行工具调用
    4. 更新对话历史
    5. 重复直到完成或达到最大轮次
    """
```

### 3. 状态管理器 (StateManager)

**文件位置**: `kiwi_video/core/state_manager.py`

**职责**: 管理项目状态的持久化和恢复。

#### 状态结构

```json
{
  "project_id": "test_20251211_203720",
  "status": "processing",
  "user_input": "创建视频...",
  "created_at": "2024-12-11T20:37:20",
  "updated_at": "2024-12-11T20:45:33",
  "current_phase": "film_crew",
  "phases": {
    "story_loader": {
      "status": "completed",
      "started_at": "2024-12-11T20:37:21",
      "completed_at": "2024-12-11T20:38:05",
      "result": {...}
    },
    "voice_actor": {...},
    "storyboard": {...},
    "film_crew": {...}
  },
  "scenes": {
    "scene_001": {
      "audio_path": "audio/scene_001_voice.mp3",
      "audio_duration": 8.5,
      "asr_path": "audio/scene_001_asr.json",
      "clip_path": "clips/scene_001_clip.mp4"
    }
  },
  "final_output": {
    "final_video_path": "final_video.mp4"
  }
}
```

#### 关键方法

```python
class StateManager:
    def update_state(self, updates: dict) -> None:
        """更新状态"""
        
    def start_phase(self, phase_name: str) -> None:
        """开始一个新阶段"""
        
    def complete_phase(self, phase_name: str, result: dict) -> None:
        """完成一个阶段"""
        
    def update_scene_state(self, scene_id: str, scene_data: dict) -> None:
        """更新场景状态"""
        
    def get_state(self) -> dict:
        """获取当前状态"""
```

---

## 工作流程详解

### 完整流程时序图

```
用户      Orchestrator   StoryLoader   VoiceActor   Storyboard   FilmCrew   VideoProcessor
 │             │              │             │            │           │            │
 │─输入文本─→│              │             │            │           │            │
 │             │              │             │            │           │            │
 │             │─Phase 1────→│             │            │           │            │
 │             │              │─生成脚本   │            │           │            │
 │             │              │─保存JSON   │            │           │            │
 │             │←─脚本数据───│             │            │           │            │
 │             │              │             │            │           │            │
 │             │─Phase 2──────────────────→│            │           │            │
 │             │              │             │─合成语音   │           │            │
 │             │              │             │─获取时长   │           │            │
 │             │              │             │─生成ASR    │           │            │
 │             │←─音频元数据─────────────│            │           │            │
 │             │              │             │            │           │            │
 │             │─Phase 3──────────────────────────────→│           │            │
 │             │              │             │            │─创建分镜 │            │
 │             │              │             │            │(使用实际时长)         │
 │             │←─分镜数据───────────────────────────│           │            │
 │             │              │             │            │           │            │
 │             │─Phase 4────────────────────────────────────────→│            │
 │             │              │             │            │           │─生成视频 │
 │             │              │             │            │           │─调整时长 │
 │             │              │             │            │           │─合成音频 │
 │             │←─视频片段─────────────────────────────────────│            │
 │             │              │             │            │           │            │
 │             │─Phase 5──────────────────────────────────────────────────────→│
 │             │              │             │            │           │            │─拼接视频
 │             │←─最终视频────────────────────────────────────────────────────│
 │             │              │             │            │           │            │
 │←最终结果───│              │             │            │           │            │
```

### Phase 1: 脚本生成 (StoryLoader Agent)

#### 输入
```python
{
    "topic": "创建一个关于未来新加坡的视频",
    "style": "professional"
}
```

#### 处理流程

1. **加载提示模板**
```python
# 从 config/prompts/story_loader.txt 加载
system_prompt = load_prompt("story_loader")
```

2. **构建生成提示**
```python
generation_prompt = f"""Generate a video script for the following topic:

Topic: {topic}
Style: {style}

Create 5 scenes that tell a compelling story.
Output ONLY valid JSON with this EXACT structure:

{{
  "topic": "{topic}",
  "style": "{style}",
  "total_duration": <30-90 seconds>,
  "scenes": [
    {{
      "scene_id": "scene_001",
      "scene_description": "视觉描述",
      "voice_over_text": "旁白文本",
      "duration": 8.0,
      "mood": "engaging",
      "visual_style": "professional"
    }}
  ]
}}
"""
```

3. **调用LLM生成**
```python
response = self.llm_client.stream(
    prompt=generation_prompt,
    purpose="script_generation"
)
```

4. **解析和验证**
```python
script_data = self._parse_llm_response(response)
# 验证必需字段: topic, style, scenes
# 验证每个scene: scene_id, scene_description, voice_over_text
```

5. **保存输出**
```python
# 保存脚本: annotated_script.json
# 保存风格指南: style_guide.txt
```

#### 输出示例

```json
{
  "topic": "创建一个关于未来新加坡的视频",
  "style": "professional",
  "total_duration": 45,
  "scenes": [
    {
      "scene_id": "scene_001",
      "scene_description": "未来新加坡的天际线，摩天大楼间穿梭着飞行汽车",
      "voice_over_text": "欢迎来到2050年的新加坡，一个科技与自然和谐共存的城市",
      "duration": 9.0,
      "mood": "inspiring",
      "visual_style": "professional"
    },
    {
      "scene_id": "scene_002",
      "scene_description": "垂直农场内部，绿色植物层层叠叠",
      "voice_over_text": "城市中的垂直农场为居民提供新鲜的食物，实现了粮食自给自足",
      "duration": 10.0,
      "mood": "hopeful",
      "visual_style": "professional"
    }
    // ... 更多场景
  ]
}
```

### Phase 2: 音频生成 (VoiceActor Agent)

**关键创新**: 在分镜制作之前生成音频，获取精确时长！

#### 输入
```python
{
    "scenes": [
        {
            "scene_id": "scene_001",
            "voice_over_text": "欢迎来到2050年的新加坡...",
            "duration": 9.0  # 这是估算值，会被实际音频时长替换
        }
    ]
}
```

#### 处理流程

1. **遍历所有场景**
```python
for scene in scenes:
    scene_id = scene["scene_id"]
    voice_text = scene["voice_over_text"]
    
    # 生成音频和ASR
    metadata = await self._generate_scene_audio(scene_id, voice_text)
```

2. **语音合成**
```python
# 使用ElevenLabs合成语音
await self.voice_client.synthesize(
    text=voice_text,
    voice_id=voice_id,  # 可选，使用默认声音
    output_path=audio_path  # audio/scene_001_voice.mp3
)
```

3. **获取音频时长**
```python
# 使用mutagen库读取MP3元数据
audio = MP3(str(audio_path))
duration = audio.info.length  # 实际时长，例如 8.47 秒
```

4. **生成ASR(自动语音识别)**
```python
# 使用ElevenLabs的speech-to-text获取词级时间戳
asr_data = await self.voice_client.speech_to_text(
    audio_path=audio_path,
    output_path=asr_path  # audio/scene_001_asr.json
)
```

#### ASR数据结构

```json
{
  "text": "欢迎来到2050年的新加坡，一个科技与自然和谐共存的城市",
  "duration": 8.47,
  "words": [
    {
      "word": "欢迎",
      "start": 0.0,
      "end": 0.45,
      "confidence": 0.98
    },
    {
      "word": "来到",
      "start": 0.45,
      "end": 0.89,
      "confidence": 0.97
    }
    // ... 更多单词时间戳
  ]
}
```

#### 输出

```python
{
    "scenes_processed": 5,
    "scenes_metadata": {
        "scene_001": {
            "scene_id": "scene_001",
            "audio_path": "audio/scene_001_voice.mp3",
            "asr_path": "audio/scene_001_asr.json",
            "duration": 8.47,  # ✅ 实际音频时长！
            "text_length": 45,
            "word_count": 12
        }
        // ... 更多场景
    }
}
```

### Phase 3: 分镜创建 (Storyboard Agent)

#### 输入
```python
{
    "script": {
        "scenes": [...]
    },
    "audio_metadata": {  # ✅ 来自Phase 2的实际音频数据
        "scene_001": {
            "duration": 8.47,  # 实际时长
            "audio_path": "...",
            "asr_path": "..."
        }
    }
}
```

#### 处理流程

1. **替换估算时长为实际时长**
```python
for scene in scenes:
    scene_id = scene['scene_id']
    
    # 如果有音频元数据，使用实际时长
    if scene_id in audio_metadata:
        actual_duration = audio_metadata[scene_id]['duration']
        scene['duration'] = actual_duration  # 替换估算值
        
        logger.info(
            f"使用实际音频时长: {actual_duration:.2f}s "
            f"(估算: {scene.get('duration', 0)}s)"
        )
```

2. **为每个场景规划镜头**
```python
shots = self._plan_shots_with_llm(scene)
```

3. **LLM镜头规划提示**
```python
planning_prompt = f"""Plan detailed shots for this scene:

Scene ID: {scene['scene_id']}
Description: {scene['scene_description']}
Voice-over: {scene['voice_over_text']}
Duration: {scene_duration} seconds (actual audio duration)

IMPORTANT: The total duration of all shots MUST equal {scene_duration} seconds exactly.
This is the actual recorded voice-over duration, so shots must be precisely timed.

Create 1-3 shots that effectively tell this scene's story.
Output valid JSON array of shots:

[
  {{
    "shot_id": "scene_001_shot_001",
    "shot_description": "Opening establishing shot",
    "visual_description": "Detailed visual description",
    "duration": 3.5,
    "timing": {{
      "start_time": 0.0,
      "end_time": 3.5
    }},
    "visuals": {{
      "composition": {{
        "shot_type": "wide",
        "camera_angle": "high-angle",
        "camera_movement": "drone flyover"
      }},
      "lighting": "golden hour",
      "mood": "inspiring"
    }},
    "voice_over_cue": "欢迎来到2050年的新加坡"
  }}
]
"""
```

4. **规范化镜头ID**
```python
def _normalize_shot_ids(shots, scene_id):
    """
    确保镜头ID格式统一: scene_XXX_shot_YYY
    """
    for idx, shot in enumerate(shots, start=1):
        standard_id = f"{scene_id}_shot_{idx:03d}"
        shot["shot_id"] = standard_id
```

#### 输出示例

```json
{
  "storyboard_id": "storyboard_20251211_203720",
  "created_at": "2024-12-11T20:37:25",
  "scenes": [
    {
      "scene_id": "scene_001",
      "scene_description": "未来新加坡的天际线...",
      "voice_over_text": "欢迎来到2050年的新加坡...",
      "duration": 8.47,  # ✅ 实际音频时长
      "shots": [
        {
          "shot_id": "scene_001_shot_001",
          "visual_description": "从高处俯瞰新加坡天际线，摩天大楼间飞行汽车穿梭",
          "duration": 4.0,
          "timing": {
            "start_time": 0.0,
            "end_time": 4.0
          },
          "visuals": {
            "composition": {
              "shot_type": "wide",
              "camera_angle": "high-angle",
              "camera_movement": "slow drone descent"
            },
            "lighting": "golden hour",
            "mood": "inspiring",
            "color_palette": "warm tones"
          },
          "voice_over_cue": "欢迎来到2050年的新加坡"
        },
        {
          "shot_id": "scene_001_shot_002",
          "visual_description": "特写镜头：飞行汽车在摩天大楼间穿梭",
          "duration": 4.47,
          "timing": {
            "start_time": 4.0,
            "end_time": 8.47
          },
          "visuals": {
            "composition": {
              "shot_type": "medium",
              "camera_angle": "eye-level",
              "camera_movement": "tracking shot"
            },
            "lighting": "bright daylight",
            "mood": "dynamic"
          },
          "voice_over_cue": "一个科技与自然和谐共存的城市"
        }
      ]
    }
  ]
}
```

### Phase 4: 视频制作 (FilmCrew Agent)

#### 输入
```python
{
    "scene": {
        "scene_id": "scene_001",
        "shots": [...]  # 来自分镜
    },
    "audio_metadata": {
        "duration": 8.47,
        "audio_path": "audio/scene_001_voice.mp3",
        "asr_path": "audio/scene_001_asr.json"
    }
}
```

#### 处理流程

**Step 1: 生成制作计划**

```python
def _generate_high_level_plan(scene, audio_duration, asr_path):
    """
    优先使用分镜板的镜头计划
    """
    storyboard_shots = scene.get('shots', [])
    
    if storyboard_shots:
        # ✅ 直接使用分镜板的镜头
        plan_data = {
            "scene_id": scene['scene_id'],
            "total_duration": audio_duration,  # 使用实际音频时长
            "shots": storyboard_shots,
            "composition_strategy": "Follow storyboard shot sequence"
        }
    else:
        # 后备：用LLM生成计划
        plan_data = self._generate_plan_with_llm(scene, audio_duration)
    
    return plan_data
```

**Step 2: 为每个镜头生成视频素材**

```python
for shot in plan['shots']:
    # 构建Veo提示词
    veo_prompt = self._build_veo_prompt(shot)
    
    # 调用Veo生成视频
    video_path = await self.veo_client.generate_and_download(
        prompt=veo_prompt["veo_prompt"],
        negative_prompt=veo_prompt["negative_prompt"],
        duration=int(shot['duration']),  # Veo需要整数秒
        output_path=output_path
    )
```

**Veo提示词构建**

```python
def _build_veo_prompt(shot):
    """
    从分镜数据构建Veo生成提示
    """
    visual_desc = shot['visual_description']
    
    # 提取相机参数
    camera_movement = shot['visuals']['composition']['camera_movement']
    camera_angle = shot['visuals']['composition']['camera_angle']
    shot_type = shot['visuals']['composition']['shot_type']
    
    # 构建完整提示
    veo_prompt = f"{visual_desc}, "
    veo_prompt += f"camera: {camera_movement} {camera_angle} {shot_type}, "
    veo_prompt += f"lighting: {shot['visuals']['lighting']}, "
    veo_prompt += f"mood: {shot['visuals']['mood']}, "
    veo_prompt += "cinematic quality, professional production, smooth camera work"
    
    # 负面提示
    negative_prompt = (
        "blurry, low quality, amateur, shaky camera, poorly lit, "
        "pixelated, distorted, text overlay, subtitles, watermarks"
    )
    
    return {
        "veo_prompt": veo_prompt,
        "negative_prompt": negative_prompt
    }
```

**Step 3: 调整视频时长**

Veo生成的视频可能不是精确的目标时长，需要调整：

```python
for shot, asset_path in shot_assets:
    target_duration = shot['duration']  # 例如 4.47秒
    
    # 使用VideoProcessor调整时长
    await VideoProcessor.adjust_video_duration(
        input_path=asset_path,
        target_duration=target_duration,
        output_path=adjusted_path
    )
```

**Step 4: 拼接镜头**

如果场景有多个镜头：

```python
if len(adjusted_videos) > 1:
    await VideoProcessor.concat_videos(
        video_paths=adjusted_videos,
        output_path=concatenated_path
    )
```

**Step 5: 合并音频**

```python
await VideoProcessor.merge_video_audio(
    video_path=base_video,
    audio_path=voice_path,  # 预生成的音频
    text=voice_text,  # 可选：生成字幕
    output_path=clip_path  # clips/scene_001_clip.mp4
)
```

#### 输出

```python
{
    "scene_id": "scene_001",
    "clip_path": "clips/scene_001_clip.mp4",
    "assets_created": 2,  # 生成了2个镜头
    "audio_path": "audio/scene_001_voice.mp3",
    "audio_duration": 8.47
}
```

### Phase 5: 最终合成

#### 处理流程

```python
async def _compile_final_video(clips_results):
    """
    将所有场景片段拼接成最终视频
    """
    # 提取所有片段路径
    clip_paths = [
        Path(result["clip_path"])
        for result in clips_results
        if result.get("clip_path")
    ]
    
    # 按顺序拼接
    final_video_path = workspace_dir / "final_video.mp4"
    
    await VideoProcessor.concat_videos(
        video_paths=clip_paths,
        output_path=final_video_path
    )
    
    return final_video_path
```

#### 输出

```
workspaces/test_20251211_203720/final_video.mp4
```

总时长 = 所有场景音频时长之和 = 完美同步！✅

---

## 智能体(Agent)系统

### Agent架构设计

所有智能体继承自 `BaseAgent`，实现统一接口：

```python
class CustomAgent(BaseAgent):
    def register_tools(self) -> dict[str, Callable]:
        """注册工具"""
        return {
            "tool_name": self._tool_function
        }
    
    def get_system_prompt(self) -> str:
        """返回系统提示词"""
        return "You are a ..."
    
    def _execute_workflow(self, input_data: dict) -> dict:
        """执行工作流"""
        # 实现具体逻辑
        return result
```

### StoryLoader Agent

**职责**: 将用户输入转换为结构化脚本

**关键代码位置**: `kiwi_video/agents/story_loader.py`

#### 工具集

| 工具名 | 功能 | 实现 |
|--------|------|------|
| `write_script` | 写入脚本到文件 | `_write_script()` |
| `validate_script` | 验证脚本结构 | `_validate_script()` |

#### 核心逻辑

```python
def _execute_workflow(self, input_data):
    topic = input_data['topic']
    style = input_data.get('style', 'professional')
    
    # 1. 用LLM生成脚本
    script_data = self._generate_script_with_llm(topic, style)
    
    # 2. 解析和验证
    if not self._validate_script_structure(script_data):
        script_data = self._create_fallback_script(topic, style)
    
    # 3. 保存文件
    script_path = self._save_script(script_data)
    style_guide_path = self._save_style_guide(topic, style)
    
    return {
        "script_path": str(script_path),
        "scenes": script_data["scenes"],
        "scenes_count": len(script_data["scenes"])
    }
```

#### 脚本验证规则

```python
def _validate_script_structure(script_data):
    """验证脚本必须包含"""
    required_fields = ["topic", "style", "scenes"]
    
    # 验证顶层字段
    for field in required_fields:
        if field not in script_data:
            return False
    
    # 验证场景数组
    if not isinstance(script_data["scenes"], list):
        return False
    
    # 验证每个场景
    for scene in script_data["scenes"]:
        required_scene_fields = [
            "scene_id",
            "scene_description",
            "voice_over_text"
        ]
        for field in required_scene_fields:
            if field not in scene:
                return False
    
    return True
```

### VoiceActor Agent

**职责**: 为所有场景生成高质量语音和ASR数据

**关键代码位置**: `kiwi_video/agents/voice_actor.py`

#### 工具集

| 工具名 | 功能 | 实现 |
|--------|------|------|
| `synthesize_voice` | 合成语音 | `_synthesize_voice_tool()` |
| `list_voices` | 列出可用声音 | `_list_voices_tool()` |

#### 核心逻辑

```python
async def _execute_workflow(self, input_data):
    scenes = input_data['scenes']
    scenes_metadata = {}
    
    # 为每个场景生成音频
    for scene_data in scenes:
        scene_id = scene_data['scene_id']
        voice_text = scene_data['voice_over_text']
        
        # 生成音频 + ASR
        metadata = await self._generate_scene_audio(
            scene_id=scene_id,
            voice_text=voice_text,
            generate_asr=True
        )
        
        scenes_metadata[scene_id] = metadata
    
    return {
        "scenes_processed": len(scenes_metadata),
        "scenes_metadata": scenes_metadata
    }
```

#### 音频生成详细步骤

```python
async def _generate_scene_audio(scene_id, voice_text):
    audio_path = workspace / "audio" / f"{scene_id}_voice.mp3"
    asr_path = workspace / "audio" / f"{scene_id}_asr.json"
    
    # Step 1: 合成语音
    await voice_client.synthesize(
        text=voice_text,
        voice_id=voice_id,  # 可指定特定声音
        output_path=audio_path
    )
    
    # Step 2: 获取时长
    audio = MP3(str(audio_path))
    duration = audio.info.length
    
    # Step 3: 生成ASR
    asr_data = await voice_client.speech_to_text(
        audio_path=audio_path,
        output_path=asr_path
    )
    
    return {
        "scene_id": scene_id,
        "audio_path": str(audio_path),
        "asr_path": str(asr_path),
        "duration": duration,
        "asr_data": asr_data
    }
```

### Storyboard Agent

**职责**: 创建详细的镜头级分镜

**关键代码位置**: `kiwi_video/agents/storyboard.py`

#### 核心逻辑

```python
def _execute_workflow(self, input_data):
    script_data = input_data['script']
    audio_metadata = input_data.get('audio_metadata', {})
    scenes = script_data['scenes']
    
    storyboard_scenes = []
    
    for scene in scenes:
        scene_id = scene['scene_id']
        
        # ✅ 使用实际音频时长
        if scene_id in audio_metadata:
            actual_duration = audio_metadata[scene_id]['duration']
            scene['duration'] = actual_duration
        
        # 为场景规划镜头
        scene_with_shots = self._create_shot_breakdown(scene)
        storyboard_scenes.append(scene_with_shots)
    
    # 保存分镜
    storyboard_data = {
        "storyboard_id": f"storyboard_{timestamp}",
        "scenes": storyboard_scenes
    }
    
    storyboard_path = self._save_storyboard(storyboard_data)
    
    return {
        "storyboard_path": str(storyboard_path),
        "scenes": storyboard_scenes,
        "total_shots": sum(len(s['shots']) for s in storyboard_scenes)
    }
```

#### 镜头规划策略

```python
def _create_shot_breakdown(scene):
    """
    为单个场景创建镜头分解
    """
    # 使用LLM规划镜头
    shots = self._plan_shots_with_llm(scene)
    
    if not shots:
        # 后备：创建单镜头
        shots = self._create_default_shots(scene)
    
    # 规范化镜头ID
    shots = self._normalize_shot_ids(shots, scene['scene_id'])
    
    scene['shots'] = shots
    scene['total_duration'] = scene['duration']
    
    return scene
```

### FilmCrew Agent

**职责**: 生成视频素材并合成场景片段

**关键代码位置**: `kiwi_video/agents/film_crew.py`

#### 依赖服务

- **VeoClient**: Google Veo AI视频生成
- **ElevenLabsClient**: 语音服务（如需重新生成）
- **VideoProcessor**: 视频处理工具

#### 核心逻辑

```python
async def _execute_workflow(self, input_data):
    scene = input_data['scene']
    audio_metadata = input_data['audio_metadata']
    scene_id = scene['scene_id']
    
    audio_duration = audio_metadata['duration']
    audio_path = Path(audio_metadata['audio_path'])
    asr_path = audio_metadata.get('asr_path')
    
    # Step 1: 生成制作计划（使用分镜的镜头）
    plan = self._generate_high_level_plan(scene, audio_duration, asr_path)
    
    # Step 2: 为每个镜头生成视频素材
    shot_assets = []
    for shot in plan['shots']:
        asset_path = await self._create_video_asset(shot, scene_id)
        if asset_path:
            shot_assets.append((shot, asset_path))
    
    # Step 3: 合成最终片段（调整时长 + 拼接 + 音频）
    final_clip = await self._compose_scene_clip(
        scene_id=scene_id,
        shot_assets=shot_assets,
        voice_path=audio_path,
        voice_text=scene['voice_over_text']
    )
    
    return {
        "scene_id": scene_id,
        "clip_path": str(final_clip),
        "assets_created": len(shot_assets),
        "audio_duration": audio_duration
    }
```

#### 视频合成详细流程

```python
async def _compose_scene_clip(
    scene_id,
    shot_assets,  # [(shot_data, video_path), ...]
    voice_path,
    voice_text
):
    """
    合成场景最终片段
    """
    clip_path = workspace / "clips" / f"{scene_id}_clip.mp4"
    
    # Step 1: 调整每个镜头的时长
    adjusted_videos = []
    for shot, asset_path in shot_assets:
        target_duration = shot['duration']
        adjusted_path = temp_dir / f"{shot['shot_id']}_adjusted.mp4"
        
        await VideoProcessor.adjust_video_duration(
            input_path=asset_path,
            target_duration=target_duration,
            output_path=adjusted_path
        )
        
        adjusted_videos.append(adjusted_path)
    
    # Step 2: 拼接多个镜头
    if len(adjusted_videos) > 1:
        concat_path = temp_dir / f"{scene_id}_concat.mp4"
        await VideoProcessor.concat_videos(adjusted_videos, concat_path)
        base_video = concat_path
    else:
        base_video = adjusted_videos[0]
    
    # Step 3: 合并音频
    await VideoProcessor.merge_video_audio(
        video_path=base_video,
        audio_path=voice_path,
        text=voice_text,  # 可选：生成字幕
        output_path=clip_path
    )
    
    return clip_path
```

---

## 服务提供者(Providers)

### Provider架构

所有外部服务通过Provider模式抽象，便于替换和测试。

```
providers/
├── llm/
│   ├── base.py              # BaseLLMClient抽象类
│   └── gemini_client.py     # Gemini实现
├── video/
│   ├── base.py              # BaseVideoClient抽象类
│   └── veo_client.py        # Veo实现
└── voice/
    ├── base.py              # BaseVoiceClient抽象类
    └── elevenlabs_client.py # ElevenLabs实现
```

### LLM Provider: Gemini

**文件位置**: `kiwi_video/providers/llm/gemini_client.py`

#### 核心功能

```python
class GeminiClient(BaseLLMClient):
    """Google Gemini LLM客户端"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def stream(self, prompt: str, purpose: str = "") -> str:
        """
        流式生成文本
        
        Args:
            prompt: 提示词
            purpose: 用途标识（用于日志）
        
        Returns:
            生成的文本
        """
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
        
        return response.text
    
    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict]
    ) -> dict:
        """
        带工具调用的生成（用于Agent Loop）
        
        Args:
            messages: 对话历史
            tools: 可用工具列表
        
        Returns:
            包含文本和工具调用的响应
        """
        # 实现工具调用逻辑
        pass
```

#### 使用示例

```python
llm = GeminiClient(api_key=settings.gemini_api_key)

response = llm.stream(
    prompt="Generate a video script about AI",
    purpose="script_generation"
)
```

### Video Provider: Veo

**文件位置**: `kiwi_video/providers/video/veo_client.py`

#### 核心功能

```python
class VeoClient(BaseVideoClient):
    """Google Veo AI视频生成客户端"""
    
    def __init__(self):
        self.project_id = settings.gcp_project_id
        self.location = "us-central1"
        self.client = aiplatform.gapic.PredictionServiceClient()
    
    async def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        duration: int = 8,
        aspect_ratio: str = "16:9"
    ) -> str:
        """
        生成视频并返回GCS URI
        
        Args:
            prompt: 视频描述
            negative_prompt: 负面提示
            duration: 时长（秒）
            aspect_ratio: 宽高比
        
        Returns:
            GCS URI (gs://bucket/path/to/video.mp4)
        """
        request = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "duration_seconds": duration,
            "aspect_ratio": aspect_ratio
        }
        
        response = await self.client.predict(request)
        return response.gcs_uri
    
    async def download_from_gcs(
        self,
        gcs_uri: str,
        output_path: Path
    ) -> Path:
        """
        从GCS下载视频到本地
        """
        bucket_name = gcs_uri.split('/')[2]
        blob_path = '/'.join(gcs_uri.split('/')[3:])
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(output_path))
        
        return output_path
    
    async def generate_and_download(
        self,
        prompt: str,
        output_path: Path,
        **kwargs
    ) -> Path:
        """
        便捷方法：生成并下载
        """
        gcs_uri = await self.generate(prompt, **kwargs)
        return await self.download_from_gcs(gcs_uri, output_path)
```

#### 使用示例

```python
veo = VeoClient()

video_path = await veo.generate_and_download(
    prompt="A futuristic city with flying cars, cinematic quality",
    negative_prompt="blurry, low quality",
    duration=8,
    output_path=Path("output/scene_001.mp4")
)
```

### Voice Provider: ElevenLabs

**文件位置**: `kiwi_video/providers/voice/elevenlabs_client.py`

#### 核心功能

```python
class ElevenLabsClient(BaseVoiceClient):
    """ElevenLabs语音合成和ASR客户端"""
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.elevenlabs_api_key
        self.client = ElevenLabs(api_key=self.api_key)
        self.default_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    
    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        output_path: Path | None = None
    ) -> bytes:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            voice_id: 声音ID（可选）
            output_path: 输出路径（可选）
        
        Returns:
            音频二进制数据
        """
        voice_id = voice_id or self.default_voice_id
        
        audio = self.client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2"
        )
        
        # 转换为bytes
        audio_bytes = b"".join(audio)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
        
        return audio_bytes
    
    async def speech_to_text(
        self,
        audio_path: Path,
        output_path: Path | None = None
    ) -> dict:
        """
        语音转文字（带词级时间戳）
        
        Args:
            audio_path: 音频文件路径
            output_path: ASR结果输出路径
        
        Returns:
            包含文本和时间戳的字典
        """
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        
        # 调用ASR API
        result = self.client.speech_to_text(audio_data)
        
        asr_data = {
            "text": result.text,
            "words": [
                {
                    "word": word.text,
                    "start": word.start,
                    "end": word.end,
                    "confidence": word.confidence
                }
                for word in result.words
            ]
        }
        
        if output_path:
            with open(output_path, "w") as f:
                json.dump(asr_data, f, indent=2, ensure_ascii=False)
        
        return asr_data
    
    def get_voices(self) -> list[dict]:
        """获取可用声音列表"""
        voices = self.client.voices.get_all()
        
        return [
            {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": voice.category
            }
            for voice in voices.voices
        ]
```

#### 使用示例

```python
voice = ElevenLabsClient()

# 合成语音
await voice.synthesize(
    text="Hello, this is a test",
    output_path=Path("output/test.mp3")
)

# 生成ASR
asr_data = await voice.speech_to_text(
    audio_path=Path("output/test.mp3"),
    output_path=Path("output/test_asr.json")
)

# 列出可用声音
voices = voice.get_voices()
for v in voices:
    print(f"{v['name']}: {v['voice_id']}")
```

---

## API接口

### API架构

基于FastAPI构建的RESTful API，支持异步操作。

**主要文件**:
- `kiwi_video/api/app.py` - FastAPI应用
- `kiwi_video/api/routes/projects.py` - 项目路由
- `kiwi_video/api/routes/health.py` - 健康检查

### 项目管理API

#### 1. 创建项目

**端点**: `POST /api/v1/projects`

**请求体**:
```json
{
  "prompt": "创建一个关于未来新加坡的45秒视频",
  "style": "professional",
  "duration": 45
}
```

**响应**:
```json
{
  "project_id": "project_abc123",
  "status": "initialized",
  "created_at": "2024-12-11T20:37:20Z",
  "workspace_dir": "/path/to/workspaces/project_abc123"
}
```

#### 2. 开始生成

**端点**: `POST /api/v1/projects/{project_id}/generate`

**响应**:
```json
{
  "project_id": "project_abc123",
  "status": "processing",
  "message": "Video generation started"
}
```

后台异步执行工作流。

#### 3. 查询状态

**端点**: `GET /api/v1/projects/{project_id}`

**响应**:
```json
{
  "project_id": "project_abc123",
  "status": "processing",
  "current_phase": "film_crew",
  "phases": {
    "story_loader": {
      "status": "completed",
      "started_at": "2024-12-11T20:37:21Z",
      "completed_at": "2024-12-11T20:38:05Z"
    },
    "voice_actor": {
      "status": "completed",
      "started_at": "2024-12-11T20:38:06Z",
      "completed_at": "2024-12-11T20:39:15Z"
    },
    "storyboard": {
      "status": "completed",
      "started_at": "2024-12-11T20:39:16Z",
      "completed_at": "2024-12-11T20:40:30Z"
    },
    "film_crew": {
      "status": "processing",
      "started_at": "2024-12-11T20:40:31Z"
    }
  },
  "progress": 75
}
```

#### 4. 获取结果

**端点**: `GET /api/v1/projects/{project_id}/result`

**响应**:
```json
{
  "project_id": "project_abc123",
  "status": "completed",
  "final_video_url": "/api/v1/projects/project_abc123/video",
  "duration": 45.2,
  "scenes_count": 5,
  "created_at": "2024-12-11T20:37:20Z",
  "completed_at": "2024-12-11T20:45:33Z"
}
```

#### 5. 下载视频

**端点**: `GET /api/v1/projects/{project_id}/video`

**响应**: 视频文件 (application/octet-stream)

### 健康检查API

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-12-11T20:50:00Z",
  "services": {
    "gemini": "connected",
    "veo": "connected",
    "elevenlabs": "connected"
  }
}
```

### 完整API示例流程

```bash
# 1. 创建项目
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "创建一个关于未来新加坡的45秒视频",
    "style": "professional"
  }'

# 返回: {"project_id": "project_abc123", ...}

# 2. 开始生成
curl -X POST http://localhost:8000/api/v1/projects/project_abc123/generate

# 3. 轮询状态（每5秒）
while true; do
  curl http://localhost:8000/api/v1/projects/project_abc123
  sleep 5
done

# 4. 下载视频（当status=completed）
curl -O http://localhost:8000/api/v1/projects/project_abc123/video
```

---

## 数据流与状态管理

### 数据流图

```
用户输入
   │
   ▼
┌─────────────────────────────────┐
│   DirectorOrchestrator          │
│   ┌──────────────────────────┐  │
│   │   StateManager           │  │◄─── 持久化到JSON
│   │   - project_state.json   │  │
│   │   - history.jsonl        │  │
│   └──────────────────────────┘  │
└───┬─────────────────────────────┘
    │
    ├─Phase 1: StoryLoader
    │    ├─► annotated_script.json
    │    └─► style_guide.txt
    │
    ├─Phase 2: VoiceActor
    │    ├─► audio/scene_001_voice.mp3
    │    ├─► audio/scene_001_asr.json
    │    ├─► audio/scene_002_voice.mp3
    │    └─► audio/scene_002_asr.json
    │
    ├─Phase 3: Storyboard
    │    ├─► storyboard.json
    │    └─► storyboard_summary.md
    │
    ├─Phase 4: FilmCrew (per scene)
    │    ├─► assets/scene_001/scene_001_shot_001_V0.mp4
    │    ├─► assets/scene_001/scene_001_shot_002_V0.mp4
    │    ├─► clips/scene_001_clip.mp4
    │    └─► plans/scene_001_production_plan.json
    │
    └─Phase 5: VideoProcessor
         └─► final_video.mp4
```

### 状态管理详解

#### StateManager核心功能

```python
class StateManager:
    """项目状态管理器"""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.state_file = workspace_dir / "project_state.json"
        self.history_file = workspace_dir / "history.jsonl"
        
        # 加载或初始化状态
        self.state = self._load_state()
    
    def update_state(self, updates: dict) -> None:
        """
        更新状态（支持嵌套更新）
        
        Example:
            update_state({
                "status": "processing",
                "scenes.scene_001.audio_path": "audio/scene_001.mp3"
            })
        """
        for key, value in updates.items():
            self._set_nested_value(self.state, key, value)
        
        self.state["updated_at"] = datetime.now().isoformat()
        self._save_state()
        self._log_to_history("update", updates)
    
    def start_phase(self, phase_name: str) -> None:
        """标记阶段开始"""
        self.state["phases"][phase_name] = {
            "status": "processing",
            "started_at": datetime.now().isoformat()
        }
        self.state["current_phase"] = phase_name
        self._save_state()
        self._log_to_history("phase_start", {"phase": phase_name})
    
    def complete_phase(self, phase_name: str, result: dict) -> None:
        """标记阶段完成"""
        self.state["phases"][phase_name].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result": result
        })
        self._save_state()
        self._log_to_history("phase_complete", {
            "phase": phase_name,
            "result": result
        })
    
    def fail_phase(self, phase_name: str, error: str) -> None:
        """标记阶段失败"""
        self.state["phases"][phase_name].update({
            "status": "failed",
            "failed_at": datetime.now().isoformat(),
            "error": error
        })
        self.state["status"] = "failed"
        self._save_state()
        self._log_to_history("phase_failed", {
            "phase": phase_name,
            "error": error
        })
```

#### 状态恢复机制

```python
def recover_project(project_id: str) -> DirectorOrchestrator:
    """
    从中断状态恢复项目
    """
    workspace_dir = Path("workspaces") / project_id
    state_file = workspace_dir / "project_state.json"
    
    if not state_file.exists():
        raise ValueError(f"Project {project_id} not found")
    
    # 加载状态
    with open(state_file) as f:
        state = json.load(f)
    
    # 创建编排器
    orchestrator = DirectorOrchestrator(
        project_id=project_id,
        workspace_dir=workspace_dir
    )
    
    # 确定从哪个阶段恢复
    current_phase = state.get("current_phase")
    phases = state.get("phases", {})
    
    # 如果当前阶段失败，从失败点重试
    if phases.get(current_phase, {}).get("status") == "failed":
        logger.info(f"Retrying failed phase: {current_phase}")
        # ... 重试逻辑
    
    return orchestrator
```

#### 历史日志格式 (JSONL)

```jsonl
{"timestamp": "2024-12-11T20:37:20Z", "event": "project_created", "data": {...}}
{"timestamp": "2024-12-11T20:37:21Z", "event": "phase_start", "data": {"phase": "story_loader"}}
{"timestamp": "2024-12-11T20:38:05Z", "event": "phase_complete", "data": {"phase": "story_loader", "result": {...}}}
{"timestamp": "2024-12-11T20:38:06Z", "event": "phase_start", "data": {"phase": "voice_actor"}}
...
```

---

## 文件结构与输出

### 工作区目录结构

每个项目都有独立的工作区：

```
workspaces/
└── project_abc123/                    # 项目工作区
    ├── project_state.json             # 项目状态
    ├── history.jsonl                  # 操作历史
    │
    ├── annotated_script.json          # Phase 1: 脚本
    ├── style_guide.txt                # 风格指南
    │
    ├── audio/                         # Phase 2: 音频
    │   ├── scene_001_voice.mp3        #   - 语音文件
    │   ├── scene_001_asr.json         #   - ASR数据
    │   ├── scene_002_voice.mp3
    │   └── scene_002_asr.json
    │
    ├── storyboard.json                # Phase 3: 分镜
    ├── storyboard_summary.md          # 分镜摘要
    │
    ├── plans/                         # Phase 4: 制作计划
    │   ├── scene_001_production_plan.json
    │   └── scene_002_production_plan.json
    │
    ├── assets/                        # Phase 4: 原始视频素材
    │   ├── scene_001/
    │   │   ├── scene_001_shot_001_V0.mp4
    │   │   └── scene_001_shot_002_V0.mp4
    │   └── scene_002/
    │       └── scene_002_shot_001_V0.mp4
    │
    ├── temp/                          # 临时文件
    │   ├── adjusted/                  #   - 调整时长后的视频
    │   │   ├── scene_001_shot_001_adjusted.mp4
    │   │   └── scene_001_shot_002_adjusted.mp4
    │   └── scene_001_concat.mp4       #   - 拼接临时文件
    │
    ├── clips/                         # Phase 4: 场景片段（带音频）
    │   ├── scene_001_clip.mp4
    │   ├── scene_002_clip.mp4
    │   └── scene_003_clip.mp4
    │
    └── final_video.mp4                # Phase 5: 最终输出 ✅
```

### 关键文件格式

#### annotated_script.json

```json
{
  "topic": "创建一个关于未来新加坡的45秒视频",
  "style": "professional",
  "total_duration": 45,
  "scenes": [
    {
      "scene_id": "scene_001",
      "scene_description": "未来新加坡的天际线，摩天大楼间穿梭着飞行汽车",
      "voice_over_text": "欢迎来到2050年的新加坡，一个科技与自然和谐共存的城市",
      "duration": 9.0,
      "mood": "inspiring",
      "visual_style": "professional"
    }
  ]
}
```

#### storyboard.json

```json
{
  "storyboard_id": "storyboard_20251211_203720",
  "created_at": "2024-12-11T20:37:25Z",
  "scenes": [
    {
      "scene_id": "scene_001",
      "duration": 8.47,  // 实际音频时长
      "shots": [
        {
          "shot_id": "scene_001_shot_001",
          "visual_description": "从高处俯瞰新加坡天际线",
          "duration": 4.0,
          "timing": {
            "start_time": 0.0,
            "end_time": 4.0
          },
          "visuals": {
            "composition": {
              "shot_type": "wide",
              "camera_angle": "high-angle",
              "camera_movement": "slow drone descent"
            },
            "lighting": "golden hour",
            "mood": "inspiring"
          }
        }
      ]
    }
  ]
}
```

#### audio/scene_001_asr.json

```json
{
  "text": "欢迎来到2050年的新加坡，一个科技与自然和谐共存的城市",
  "duration": 8.47,
  "words": [
    {
      "word": "欢迎",
      "start": 0.0,
      "end": 0.45,
      "confidence": 0.98
    },
    {
      "word": "来到",
      "start": 0.45,
      "end": 0.89,
      "confidence": 0.97
    }
  ]
}
```

#### project_state.json

```json
{
  "project_id": "project_abc123",
  "status": "completed",
  "user_input": "创建一个关于未来新加坡的45秒视频",
  "created_at": "2024-12-11T20:37:20Z",
  "updated_at": "2024-12-11T20:45:33Z",
  "current_phase": "completed",
  "phases": {
    "story_loader": {
      "status": "completed",
      "started_at": "2024-12-11T20:37:21Z",
      "completed_at": "2024-12-11T20:38:05Z"
    },
    "voice_actor": {
      "status": "completed",
      "started_at": "2024-12-11T20:38:06Z",
      "completed_at": "2024-12-11T20:39:15Z"
    },
    "storyboard": {
      "status": "completed",
      "started_at": "2024-12-11T20:39:16Z",
      "completed_at": "2024-12-11T20:40:30Z"
    },
    "film_crew": {
      "status": "completed",
      "started_at": "2024-12-11T20:40:31Z",
      "completed_at": "2024-12-11T20:45:20Z"
    }
  },
  "scenes": {
    "scene_001": {
      "audio_path": "audio/scene_001_voice.mp3",
      "audio_duration": 8.47,
      "asr_path": "audio/scene_001_asr.json",
      "clip_path": "clips/scene_001_clip.mp4",
      "status": "completed"
    }
  },
  "final_output": {
    "final_video_path": "final_video.mp4",
    "total_duration": 45.2,
    "scenes_count": 5
  }
}
```

---

## 配置与环境

### 环境变量配置

**文件**: `.env`

```bash
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key

# Google Cloud (for Veo)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-project-id
GCS_BUCKET=your-bucket-name

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# 工作区配置
WORKSPACE_DIR=./workspaces

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/kiwi-video.log

# API配置
API_HOST=0.0.0.0
API_PORT=8000
```

### Settings类

**文件**: `kiwi_video/utils/config.py`

```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """应用配置"""
    
    # Google API
    gemini_api_key: str
    gcp_project_id: str
    gcs_bucket: str
    google_application_credentials: Path
    
    # ElevenLabs
    elevenlabs_api_key: str
    
    # Workspace
    workspace_dir: Path = Path("./workspaces")
    
    # Logging
    log_level: str = "INFO"
    log_file: Path | None = None
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 全局配置实例
settings = Settings()
```

### 依赖管理

**文件**: `pyproject.toml`

```toml
[project]
name = "kiwi-video"
version = "0.1.0"
requires-python = ">=3.10"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "google-generativeai>=0.3.0",
    "google-cloud-aiplatform>=1.40.0",
    "google-cloud-storage>=2.14.0",
    "elevenlabs>=1.0.0",
    "moviepy>=1.0.3",
    "pillow>=10.2.0",
    "httpx>=0.26.0",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.2",
    "mutagen>=1.47.0",  # MP3元数据读取
]
```

### 安装步骤

```bash
# 1. 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -e .

# 3. 安装开发依赖（可选）
pip install -e ".[dev]"

# 4. 配置环境变量
cp env.example .env
# 编辑 .env 填入API密钥

# 5. 验证环境
python check_env.py
```

---

## 扩展开发指南

### 添加新的Agent

#### 步骤1: 创建Agent类

```python
# kiwi_video/agents/my_agent.py
from kiwi_video.core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    """我的自定义智能体"""
    
    def register_tools(self) -> dict[str, Callable]:
        """注册工具"""
        return {
            "my_tool": self._my_tool
        }
    
    def get_system_prompt(self) -> str:
        """系统提示词"""
        return """You are a specialized agent for..."""
    
    async def _execute_workflow(self, input_data: dict) -> dict:
        """执行工作流"""
        # 实现你的逻辑
        result = {"output": "..."}
        return result
    
    def _my_tool(self, param: str) -> dict:
        """工具函数"""
        return {"result": f"Processed {param}"}
```

#### 步骤2: 在Orchestrator中集成

```python
# kiwi_video/core/orchestrator.py

async def _run_my_agent(self, input_data: dict) -> dict:
    """运行自定义智能体"""
    self.state_manager.start_phase("my_agent")
    
    try:
        from kiwi_video.agents.my_agent import MyAgent
        
        if self._my_agent is None:
            self._my_agent = MyAgent(
                agent_name="my_agent",
                llm_client=self.llm_client,
                state_manager=self.state_manager,
                workspace_dir=self.workspace_dir
            )
        
        result = await self._my_agent.run(input_data)
        
        self.state_manager.complete_phase("my_agent", result)
        return result
    
    except Exception as e:
        self.state_manager.fail_phase("my_agent", str(e))
        raise
```

#### 步骤3: 修改工作流

```python
async def execute_project(self, user_input: str) -> dict:
    # ... 现有阶段 ...
    
    # 添加新阶段
    self.logger.info("Phase X: My custom phase")
    my_result = await self._run_my_agent(previous_result)
    
    # ... 继续后续阶段 ...
```

### 添加新的Provider

#### 步骤1: 定义基类

```python
# kiwi_video/providers/my_service/base.py
from abc import ABC, abstractmethod

class BaseMyServiceClient(ABC):
    """我的服务基类"""
    
    @abstractmethod
    async def do_something(self, param: str) -> str:
        """抽象方法"""
        pass
```

#### 步骤2: 实现具体Provider

```python
# kiwi_video/providers/my_service/my_implementation.py
from .base import BaseMyServiceClient

class MyImplementation(BaseMyServiceClient):
    """具体实现"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = SomeSDK(api_key=api_key)
    
    async def do_something(self, param: str) -> str:
        """实现抽象方法"""
        result = await self.client.call_api(param)
        return result
```

#### 步骤3: 在Agent中使用

```python
class MyAgent(BaseAgent):
    def __init__(self, ..., my_service_client: BaseMyServiceClient):
        super().__init__(...)
        self.my_service = my_service_client
    
    async def _execute_workflow(self, input_data):
        result = await self.my_service.do_something(input_data['param'])
        return {"result": result}
```

### 自定义提示词模板

#### 步骤1: 创建提示词文件

```
config/prompts/my_agent.txt
```

```text
You are a specialized AI agent for [specific task].

Your responsibilities:
1. [Responsibility 1]
2. [Responsibility 2]

Output format:
[Expected format description]

Tools available:
- tool_1: [Description]
- tool_2: [Description]

Important guidelines:
- [Guideline 1]
- [Guideline 2]
```

#### 步骤2: 在Agent中加载

```python
from kiwi_video.utils.prompt_loader import load_prompt

class MyAgent(BaseAgent):
    def __init__(self, ...):
        super().__init__(...)
        
        # 加载提示词
        try:
            self._system_prompt = load_prompt("my_agent")
        except Exception:
            self._system_prompt = self._get_fallback_prompt()
    
    def get_system_prompt(self) -> str:
        return self._system_prompt
```

### 添加新的API端点

```python
# kiwi_video/api/routes/my_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class MyRequest(BaseModel):
    param: str

class MyResponse(BaseModel):
    result: str

@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    """我的自定义端点"""
    try:
        # 处理逻辑
        result = do_something(request.param)
        return MyResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

```python
# kiwi_video/api/app.py
from kiwi_video.api.routes import my_routes

app.include_router(my_routes.router, prefix="/api/v1", tags=["My Feature"])
```

---

## 总结

### 核心优势

1. **音频优先架构** ⭐
   - 先生成音频获取精确时长
   - 基于实际时长规划视频
   - 完美的音视频同步

2. **模块化设计**
   - 智能体独立可测试
   - Provider抽象易于替换
   - 清晰的职责分离

3. **生产级质量**
   - 完整的错误处理
   - 状态持久化和恢复
   - 类型安全和验证

4. **易于扩展**
   - 添加新Agent只需继承BaseAgent
   - 替换Provider只需实现接口
   - 提示词可配置

### 技术亮点

- 🔄 **异步工作流** - 高性能并发处理
- 📊 **状态管理** - 完整的进度跟踪和恢复
- 🎯 **精确同步** - 音频优先确保时长匹配
- 🧩 **多智能体协作** - 专业分工,各司其职
- 🎨 **智能分镜** - LLM生成专业镜头规划
- 🚀 **生产就绪** - API、Docker、测试完备

### 未来扩展方向

1. **更多视频效果**
   - 转场效果
   - 滤镜和调色
   - 动态字幕样式

2. **智能优化**
   - 自动质量评估
   - 多版本生成和选择
   - 用户反馈学习

3. **性能提升**
   - 并行场景生成
   - 缓存复用
   - 增量渲染

4. **多模态支持**
   - 图片输入
   - 视频剪辑
   - 音乐生成

---

## 参考资源

### 官方文档
- [Google Gemini API](https://ai.google.dev/docs)
- [Google Veo Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/video/overview)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### 项目相关
- 项目仓库: [GitHub](https://github.com/your-org/kiwi-video)
- 问题追踪: [Issues](https://github.com/your-org/kiwi-video/issues)
- 贡献指南: [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**文档版本**: 1.0.0  
**最后更新**: 2024-12-11  
**维护者**: KIWI-Video Team

