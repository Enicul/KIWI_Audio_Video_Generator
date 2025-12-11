# KIWI-Video 架构图

本文档包含KIWI-Video系统的各种架构图和流程图。

---

## 系统总体架构

```mermaid
graph TB
    User[用户输入] --> Director[DirectorOrchestrator<br/>导演编排器]
    
    Director --> StoryLoader[StoryLoader Agent<br/>脚本生成]
    Director --> VoiceActor[VoiceActor Agent<br/>语音合成]
    Director --> Storyboard[Storyboard Agent<br/>分镜设计]
    Director --> FilmCrew[FilmCrew Agent<br/>视频制作]
    
    StoryLoader --> Gemini1[Gemini LLM]
    VoiceActor --> ElevenLabs[ElevenLabs API]
    Storyboard --> Gemini2[Gemini LLM]
    FilmCrew --> Gemini3[Gemini LLM]
    FilmCrew --> Veo[Google Veo API]
    
    FilmCrew --> VideoProcessor[VideoProcessor<br/>视频处理]
    
    VideoProcessor --> Output[最终视频<br/>final_video.mp4]
    
    Director -.-> StateManager[StateManager<br/>状态管理]
    StateManager -.-> Storage[(project_state.json<br/>状态持久化)]
    
    style Director fill:#4CAF50,stroke:#2E7D32,color:#fff
    style Output fill:#FF9800,stroke:#E65100,color:#fff
    style StateManager fill:#2196F3,stroke:#1565C0,color:#fff
```

---

## 完整工作流程序列图

```mermaid
sequenceDiagram
    participant U as 用户
    participant D as DirectorOrchestrator
    participant SL as StoryLoader Agent
    participant VA as VoiceActor Agent
    participant SB as Storyboard Agent
    participant FC as FilmCrew Agent
    participant VP as VideoProcessor
    participant SM as StateManager
    
    U->>D: 用户输入: "创建视频..."
    D->>SM: 初始化项目状态
    
    rect rgb(200, 230, 200)
    Note over D,SL: Phase 1: 脚本生成
    D->>SL: 生成脚本
    SL->>SL: 调用Gemini LLM
    SL-->>D: 返回场景列表<br/>(5个场景)
    D->>SM: 保存脚本数据
    end
    
    rect rgb(255, 230, 200)
    Note over D,VA: Phase 2: 音频生成 (音频优先!)
    D->>VA: 为所有场景生成音频
    loop 每个场景
        VA->>VA: 合成语音
        VA->>VA: 获取音频时长
        VA->>VA: 生成ASR数据
    end
    VA-->>D: 返回音频元数据<br/>(实际时长)
    D->>SM: 保存音频路径和时长
    end
    
    rect rgb(200, 220, 255)
    Note over D,SB: Phase 3: 分镜创建
    D->>SB: 创建分镜(使用实际音频时长)
    SB->>SB: 调用Gemini LLM
    SB->>SB: 规划镜头 (基于实际时长)
    SB-->>D: 返回分镜数据
    D->>SM: 保存分镜
    end
    
    rect rgb(255, 220, 220)
    Note over D,FC: Phase 4: 视频制作
    loop 每个场景
        D->>FC: 制作场景视频
        FC->>FC: 生成制作计划
        loop 每个镜头
            FC->>FC: 调用Veo生成视频
            FC->>FC: 调整视频时长
        end
        FC->>FC: 拼接镜头
        FC->>FC: 合并预生成的音频
        FC-->>D: 返回场景片段
        D->>SM: 更新场景状态
    end
    end
    
    rect rgb(220, 200, 255)
    Note over D,VP: Phase 5: 最终合成
    D->>VP: 拼接所有场景
    VP->>VP: 使用FFmpeg合并
    VP-->>D: 返回最终视频路径
    D->>SM: 保存最终输出
    end
    
    D-->>U: 返回结果<br/>final_video.mp4
```

---

## 音频优先工作流对比

### 传统流程 (有问题)

```mermaid
graph LR
    A[脚本] --> B[分镜<br/>估算8秒]
    B --> C[视频生成<br/>8秒视频]
    C --> D[音频生成<br/>实际7.5秒]
    D --> E[❌ 时长不匹配<br/>需要调整]
    
    style E fill:#f44336,stroke:#c62828,color:#fff
```

### KIWI-Video音频优先流程 (正确)

```mermaid
graph LR
    A[脚本] --> B[音频生成<br/>实际7.5秒]
    B --> C[分镜<br/>使用7.5秒]
    C --> D[视频生成<br/>7.5秒视频]
    D --> E[✅ 完美同步]
    
    style E fill:#4CAF50,stroke:#2E7D32,color:#fff
```

---

## Agent详细工作流

### StoryLoader Agent

```mermaid
flowchart TD
    Start([开始]) --> Input[接收用户输入]
    Input --> BuildPrompt[构建生成提示词]
    BuildPrompt --> CallLLM[调用Gemini LLM]
    CallLLM --> ParseJSON[解析JSON响应]
    ParseJSON --> Validate{验证脚本结构}
    
    Validate -->|有效| SaveScript[保存脚本文件]
    Validate -->|无效| Fallback[使用后备脚本]
    
    Fallback --> SaveScript
    SaveScript --> SaveGuide[保存风格指南]
    SaveGuide --> Return[返回脚本数据]
    Return --> End([结束])
    
    style Start fill:#4CAF50,stroke:#2E7D32,color:#fff
    style End fill:#FF9800,stroke:#E65100,color:#fff
```

### VoiceActor Agent

```mermaid
flowchart TD
    Start([开始]) --> GetScenes[获取场景列表]
    GetScenes --> LoopStart{遍历场景}
    
    LoopStart -->|下一个场景| ExtractText[提取voice_over_text]
    ExtractText --> Synthesize[调用ElevenLabs合成]
    Synthesize --> GetDuration[读取音频时长<br/>使用mutagen]
    GetDuration --> GenerateASR[生成ASR<br/>词级时间戳]
    GenerateASR --> SaveMetadata[保存元数据]
    
    SaveMetadata --> LoopStart
    LoopStart -->|完成| Return[返回音频元数据]
    Return --> End([结束])
    
    style Start fill:#4CAF50,stroke:#2E7D32,color:#fff
    style End fill:#FF9800,stroke:#E65100,color:#fff
    style GetDuration fill:#FFC107,stroke:#F57C00,color:#000
```

### Storyboard Agent

```mermaid
flowchart TD
    Start([开始]) --> GetData[获取脚本和音频元数据]
    GetData --> LoopStart{遍历场景}
    
    LoopStart -->|下一个场景| ReplaceTime[替换时长<br/>使用实际音频时长]
    ReplaceTime --> PlanShots[规划镜头<br/>调用Gemini LLM]
    PlanShots --> NormalizeIDs[规范化镜头ID]
    NormalizeIDs --> AddToScene[添加镜头到场景]
    
    AddToScene --> LoopStart
    LoopStart -->|完成| SaveStoryboard[保存分镜JSON]
    SaveStoryboard --> CreateSummary[生成摘要Markdown]
    CreateSummary --> Return[返回分镜数据]
    Return --> End([结束])
    
    style Start fill:#4CAF50,stroke:#2E7D32,color:#fff
    style End fill:#FF9800,stroke:#E65100,color:#fff
    style ReplaceTime fill:#FFC107,stroke:#F57C00,color:#000
```

### FilmCrew Agent

```mermaid
flowchart TD
    Start([开始]) --> GetScene[获取场景和音频数据]
    GetScene --> GenPlan[生成制作计划<br/>使用分镜镜头]
    
    GenPlan --> ShotLoop{遍历镜头}
    ShotLoop -->|下一个镜头| BuildPrompt[构建Veo提示词]
    BuildPrompt --> CallVeo[调用Veo生成视频]
    CallVeo --> DownloadVideo[从GCS下载视频]
    DownloadVideo --> ShotLoop
    
    ShotLoop -->|完成| AdjustLoop{调整每个视频}
    AdjustLoop -->|下一个| AdjustDuration[调整到目标时长<br/>使用FFmpeg]
    AdjustDuration --> AdjustLoop
    
    AdjustLoop -->|完成| ConcatCheck{多个镜头?}
    ConcatCheck -->|是| ConcatShots[拼接镜头]
    ConcatCheck -->|否| SingleShot[使用单个镜头]
    
    ConcatShots --> MergeAudio[合并预生成的音频]
    SingleShot --> MergeAudio
    
    MergeAudio --> Return[返回场景片段路径]
    Return --> End([结束])
    
    style Start fill:#4CAF50,stroke:#2E7D32,color:#fff
    style End fill:#FF9800,stroke:#E65100,color:#fff
    style CallVeo fill:#9C27B0,stroke:#6A1B9A,color:#fff
```

---

## 数据流图

```mermaid
flowchart LR
    subgraph Input
        UI[用户输入]
    end
    
    subgraph Phase1[Phase 1: 脚本]
        Script[annotated_script.json]
        Guide[style_guide.txt]
    end
    
    subgraph Phase2[Phase 2: 音频]
        Audio[audio/*.mp3]
        ASR[audio/*_asr.json]
    end
    
    subgraph Phase3[Phase 3: 分镜]
        Storyboard[storyboard.json]
        Summary[storyboard_summary.md]
    end
    
    subgraph Phase4[Phase 4: 视频]
        Plans[plans/*.json]
        Assets[assets/*/*.mp4]
        Clips[clips/*.mp4]
    end
    
    subgraph Output
        Final[final_video.mp4]
    end
    
    subgraph State
        ProjectState[project_state.json]
        History[history.jsonl]
    end
    
    UI --> Script
    UI --> Guide
    
    Script --> Audio
    Script --> ASR
    
    Audio -.实际时长.-> Storyboard
    ASR -.词级时间戳.-> Storyboard
    Script --> Storyboard
    Storyboard --> Summary
    
    Storyboard -.镜头计划.-> Plans
    Audio -.音频文件.-> Clips
    Plans --> Assets
    Assets --> Clips
    
    Clips --> Final
    
    Script -.-> ProjectState
    Audio -.-> ProjectState
    Storyboard -.-> ProjectState
    Clips -.-> ProjectState
    
    ProjectState -.-> History
    
    style Final fill:#FF9800,stroke:#E65100,color:#fff
    style ProjectState fill:#2196F3,stroke:#1565C0,color:#fff
```

---

## 状态转换图

```mermaid
stateDiagram-v2
    [*] --> Initialized: 创建项目
    
    Initialized --> Processing: 开始生成
    
    Processing --> StoryLoading: Phase 1
    StoryLoading --> VoiceActing: Phase 2
    VoiceActing --> Storyboarding: Phase 3
    Storyboarding --> FilmCrew: Phase 4
    FilmCrew --> Compiling: Phase 5
    
    Compiling --> Completed: 成功
    
    StoryLoading --> Failed: 错误
    VoiceActing --> Failed: 错误
    Storyboarding --> Failed: 错误
    FilmCrew --> Failed: 错误
    Compiling --> Failed: 错误
    
    Failed --> Processing: 重试
    
    Completed --> [*]
    
    note right of Processing
        可以从任何阶段
        恢复或重试
    end note
```

---

## Provider架构

```mermaid
classDiagram
    class BaseLLMClient {
        <<abstract>>
        +stream(prompt) str
        +generate_with_tools(messages, tools) dict
    }
    
    class BaseVideoClient {
        <<abstract>>
        +generate(prompt, duration) str
        +download(uri, path) Path
    }
    
    class BaseVoiceClient {
        <<abstract>>
        +synthesize(text, voice_id) bytes
        +speech_to_text(audio_path) dict
    }
    
    class GeminiClient {
        -model: GenerativeModel
        +stream(prompt) str
        +generate_with_tools(messages, tools) dict
    }
    
    class VeoClient {
        -project_id: str
        -location: str
        +generate(prompt, duration) str
        +download_from_gcs(uri, path) Path
        +generate_and_download(prompt, path) Path
    }
    
    class ElevenLabsClient {
        -api_key: str
        -default_voice_id: str
        +synthesize(text, voice_id) bytes
        +speech_to_text(audio_path) dict
        +get_voices() list
    }
    
    BaseLLMClient <|-- GeminiClient
    BaseVideoClient <|-- VeoClient
    BaseVoiceClient <|-- ElevenLabsClient
    
    class BaseAgent {
        <<abstract>>
        #llm_client: BaseLLMClient
        #workspace_dir: Path
        +register_tools() dict
        +get_system_prompt() str
        +run(input_data) dict
    }
    
    class StoryLoaderAgent {
        +register_tools() dict
        -_generate_script_with_llm()
    }
    
    class VoiceActorAgent {
        -voice_client: BaseVoiceClient
        +register_tools() dict
        -_generate_scene_audio()
    }
    
    class FilmCrewAgent {
        -veo_client: BaseVideoClient
        -voice_client: BaseVoiceClient
        +register_tools() dict
        -_create_video_asset()
    }
    
    BaseAgent <|-- StoryLoaderAgent
    BaseAgent <|-- VoiceActorAgent
    BaseAgent <|-- FilmCrewAgent
    
    StoryLoaderAgent --> GeminiClient: uses
    VoiceActorAgent --> ElevenLabsClient: uses
    FilmCrewAgent --> GeminiClient: uses
    FilmCrewAgent --> VeoClient: uses
```

---

## 工作区文件结构

```mermaid
graph TD
    Root[workspaces/project_xyz/] --> State[project_state.json]
    Root --> History[history.jsonl]
    Root --> Script[annotated_script.json]
    Root --> Guide[style_guide.txt]
    
    Root --> AudioDir[audio/]
    AudioDir --> Audio1[scene_001_voice.mp3]
    AudioDir --> ASR1[scene_001_asr.json]
    AudioDir --> Audio2[scene_002_voice.mp3]
    AudioDir --> ASR2[scene_002_asr.json]
    
    Root --> Storyboard[storyboard.json]
    Root --> Summary[storyboard_summary.md]
    
    Root --> PlansDir[plans/]
    PlansDir --> Plan1[scene_001_production_plan.json]
    PlansDir --> Plan2[scene_002_production_plan.json]
    
    Root --> AssetsDir[assets/]
    AssetsDir --> Scene1Dir[scene_001/]
    Scene1Dir --> Shot1[scene_001_shot_001_V0.mp4]
    Scene1Dir --> Shot2[scene_001_shot_002_V0.mp4]
    
    Root --> ClipsDir[clips/]
    ClipsDir --> Clip1[scene_001_clip.mp4]
    ClipsDir --> Clip2[scene_002_clip.mp4]
    
    Root --> TempDir[temp/]
    TempDir --> AdjustedDir[adjusted/]
    TempDir --> ConcatFile[scene_001_concat.mp4]
    
    Root --> Final[final_video.mp4]
    
    style State fill:#2196F3,stroke:#1565C0,color:#fff
    style Final fill:#FF9800,stroke:#E65100,color:#fff
    style Audio1 fill:#FFC107,stroke:#F57C00,color:#000
    style Audio2 fill:#FFC107,stroke:#F57C00,color:#000
```

---

## API端点架构

```mermaid
graph TB
    Client[客户端] --> API[FastAPI应用]
    
    API --> Health[GET /health<br/>健康检查]
    API --> CreateProject[POST /api/v1/projects<br/>创建项目]
    API --> StartGen[POST /api/v1/projects/:id/generate<br/>开始生成]
    API --> GetStatus[GET /api/v1/projects/:id<br/>查询状态]
    API --> GetResult[GET /api/v1/projects/:id/result<br/>获取结果]
    API --> DownloadVideo[GET /api/v1/projects/:id/video<br/>下载视频]
    
    CreateProject --> Orchestrator[DirectorOrchestrator]
    StartGen --> Orchestrator
    GetStatus --> StateManager[StateManager]
    GetResult --> StateManager
    DownloadVideo --> FileSystem[(文件系统)]
    
    Orchestrator --> Agents[Agents]
    Orchestrator --> StateManager
    
    style API fill:#4CAF50,stroke:#2E7D32,color:#fff
    style Orchestrator fill:#FF9800,stroke:#E65100,color:#fff
```

---

## 部署架构 (Docker)

```mermaid
graph TB
    subgraph Docker容器
        API[FastAPI应用<br/>:8000]
        Workers[后台Worker]
        
        API --> Orchestrator[DirectorOrchestrator]
        Workers --> Orchestrator
    end
    
    subgraph 外部服务
        Gemini[Google Gemini API]
        Veo[Google Veo API]
        ElevenLabs[ElevenLabs API]
        GCS[Google Cloud Storage]
    end
    
    subgraph 持久化存储
        Workspaces[(workspaces/<br/>挂载卷)]
        Logs[(logs/<br/>挂载卷)]
    end
    
    Client[客户端] -->|HTTP请求| API
    
    Orchestrator --> Gemini
    Orchestrator --> Veo
    Orchestrator --> ElevenLabs
    
    Veo --> GCS
    Orchestrator --> GCS
    
    Orchestrator --> Workspaces
    API --> Logs
    
    style Docker容器 fill:#E3F2FD
    style 外部服务 fill:#FFF3E0
    style 持久化存储 fill:#F1F8E9
```

---

## 性能优化流程

```mermaid
graph LR
    subgraph 串行处理[传统串行处理]
        S1[场景1] --> S2[场景2]
        S2 --> S3[场景3]
        S3 --> S4[场景4]
        S4 --> S5[场景5]
    end
    
    subgraph 优化处理[音频优先+并行优化]
        A[批量音频生成]
        
        A --> P1[场景1视频]
        A --> P2[场景2视频]
        A --> P3[场景3视频]
        A --> P4[场景4视频]
        A --> P5[场景5视频]
        
        P1 --> M[合并]
        P2 --> M
        P3 --> M
        P4 --> M
        P5 --> M
    end
    
    style 优化处理 fill:#C8E6C9
    style 串行处理 fill:#FFCCBC
```

---

## 错误处理和重试机制

```mermaid
flowchart TD
    Start([执行任务]) --> Try[尝试执行]
    Try --> Success{成功?}
    
    Success -->|是| SaveState[保存状态]
    SaveState --> Complete([完成])
    
    Success -->|否| LogError[记录错误]
    LogError --> CheckRetry{可重试?}
    
    CheckRetry -->|是| Wait[等待]
    Wait --> Retry{重试次数<3?}
    Retry -->|是| Try
    Retry -->|否| MarkFailed[标记失败]
    
    CheckRetry -->|否| MarkFailed
    MarkFailed --> Notify[通知用户]
    Notify --> SaveFailState[保存失败状态]
    SaveFailState --> End([结束])
    
    style Complete fill:#4CAF50,stroke:#2E7D32,color:#fff
    style End fill:#f44336,stroke:#c62828,color:#fff
```

---

以上架构图展示了KIWI-Video系统的各个方面。这些图表可以帮助理解:

1. **整体架构** - 系统各组件如何协作
2. **工作流程** - 从用户输入到最终视频的完整流程
3. **Agent设计** - 每个智能体的内部逻辑
4. **数据流向** - 数据如何在各阶段间传递
5. **状态管理** - 项目状态如何变化
6. **API设计** - 外部接口如何暴露功能
7. **部署架构** - 如何在生产环境部署

如需更详细的说明,请参考 [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)

