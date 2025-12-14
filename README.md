# 🥝 KIWI-Video

**Voice-to-Video Generation Platform with Multi-Agent Architecture**

Transform your voice or text descriptions into stunning AI-generated videos using Google's Veo 3 technology. KIWI-Video features intelligent clarification dialogs and automatic multi-scene story segmentation.

![Next.js](https://img.shields.io/badge/Next.js-15.2-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![Gemini](https://img.shields.io/badge/Gemini-Veo_3.0-4285F4)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6)

---

## ✨ Features

- 🎤 **Voice Input** - Record audio directly in the browser
- 💬 **Intelligent Clarification** - AI asks follow-up questions to understand your vision
- 🎬 **Multi-Scene Stories** - Automatically splits narratives into scenes
- 🔗 **Video Stitching** - Combines multiple scenes into one video
- ⚡ **Real-time Progress** - WebSocket-based live status updates
- 🔐 **Secure Authentication** - Powered by Clerk

---

## 📁 Project Structure

```
KIWI-Video/
├── backend/                    # FastAPI Backend
│   ├── agents/                 # Multi-Agent Architecture
│   │   ├── base.py            # Base agent class
│   │   ├── speech_agent.py    # Audio → Text (Gemini)
│   │   ├── clarification_agent.py  # Intent clarification
│   │   ├── intent_agent.py    # Text → Intent analysis
│   │   ├── script_analyzer_agent.py # Scene segmentation
│   │   ├── prompt_agent.py    # Intent → Video prompt
│   │   ├── video_agent.py     # Prompt → Video (Veo 3)
│   │   ├── video_stitch_agent.py   # Multi-video concatenation
│   │   └── orchestrator.py    # Agent coordinator
│   ├── api/
│   │   ├── routes.py          # REST API endpoints
│   │   └── websocket.py       # WebSocket handlers
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── conversation_manager.py  # Conversation state
│   │   ├── gemini_service.py  # Gemini API wrapper
│   │   └── task_manager.py    # Async task management
│   ├── generated/videos/      # Output video files
│   ├── main.py                # Application entry point
│   ├── config.py              # Configuration settings
│   └── requirements.txt       # Python dependencies
│
├── front/                      # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx     # Root layout with Clerk
│   │   │   ├── page.tsx       # Landing page
│   │   │   ├── dashboard/     # Main application
│   │   │   ├── sign-in/       # Clerk sign-in
│   │   │   └── sign-up/       # Clerk sign-up
│   │   └── middleware.ts      # Auth middleware
│   ├── tailwind.config.ts     # Tailwind CSS config
│   └── package.json           # Node dependencies
│
└── README.md                   # This file
```

---

## 🏗️ Architecture

### Multi-Agent System

KIWI-Video uses a **Multi-Agent Architecture** where specialized agents collaborate to transform voice/text input into video:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                                 │
│                    (Coordinates all agents)                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  SpeechAgent  │       │  IntentAgent    │       │ ScriptAnalyzer  │
│  Audio → Text │──────▶│  Text → Intent  │──────▶│ Scene Detection │
│   (Gemini)    │       │    (Gemini)     │       │    (Gemini)     │
└───────────────┘       └─────────────────┘       └─────────────────┘
                                                           │
                              ┌────────────────────────────┤
                              │                            │
                              ▼                            ▼
                    ┌─────────────────┐          ┌─────────────────┐
                    │  PromptAgent    │          │  PromptAgent    │
                    │  Scene 1 Prompt │          │  Scene N Prompt │
                    └────────┬────────┘          └────────┬────────┘
                              │                            │
                              ▼                            ▼
                    ┌─────────────────┐          ┌─────────────────┐
                    │   VideoAgent    │          │   VideoAgent    │
                    │   Veo 3 Gen     │          │   Veo 3 Gen     │
                    └────────┬────────┘          └────────┬────────┘
                              │                            │
                              └────────────┬───────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │   VideoStitchAgent      │
                              │   Concatenate Videos    │
                              └─────────────────────────┘
```

### Agent Descriptions

| Agent | Purpose | Technology |
|-------|---------|------------|
| **SpeechAgent** | Transcribes audio to text | Gemini 2.5 Flash |
| **ClarificationAgent** | Asks follow-up questions for unclear requests | Gemini 2.5 Flash |
| **IntentAgent** | Extracts structured intent (topic, style, mood) | Gemini 2.5 Flash |
| **ScriptAnalyzerAgent** | Detects multi-scene narratives and segments | Gemini 2.5 Flash |
| **PromptAgent** | Generates optimized video prompts | Gemini 2.5 Flash |
| **VideoAgent** | Creates videos from prompts | Veo 3.0 |
| **VideoStitchAgent** | Concatenates multiple video clips | MoviePy |
| **Orchestrator** | Coordinates the entire pipeline | Custom |

### Data Flow

```
User Input (Voice/Text)
         │
         ▼
    ┌─────────┐      ┌─────────────────┐
    │ Frontend│─────▶│ POST /api/video │
    │ (React) │      │   /create       │
    └─────────┘      └────────┬────────┘
         │                    │
         │ WebSocket          ▼
         │ /ws/{task_id}  ┌─────────┐
         │◀───────────────│ Backend │
         │                └────┬────┘
         │                     │
         ▼                     ▼
    Real-time          Agent Pipeline
    Progress           (Multi-Agent)
    Updates                   │
         │                    ▼
         │            Generated Video
         │                    │
         ▼                    ▼
    ┌─────────┐      ┌─────────────────┐
    │ Display │◀─────│ GET /api/video  │
    │  Video  │      │   /file/{id}    │
    └─────────┘      └─────────────────┘
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.11+** (recommended: 3.13)
- **Node.js 18+** (recommended: 20 LTS)
- **npm** or **yarn**
- **Google Gemini API Key** (with Veo 3 access)
- **Clerk Account** (for authentication)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/KIWI-Video.git
cd KIWI-Video
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Frontend Setup

```bash
# Navigate to frontend
cd ../front

# Install dependencies
npm install

# Create environment file
cp env.example .env.local

# Edit .env.local and add Clerk keys
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
# CLERK_SECRET_KEY=sk_test_xxx
```

### 4. Configure API Keys

**Backend `.env`:**
```env
GEMINI_API_KEY=your_gemini_api_key
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
```

**Frontend `.env.local`:**
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
```

---

## ▶️ Running the Application

### Start Backend Server

```bash
cd backend
source venv/bin/activate  # If using virtual environment
python main.py
```

The backend will start at `http://localhost:8000`

- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Start Frontend Server

```bash
cd front
npm run dev
```

The frontend will start at `http://localhost:3000`

### Both Running Together

You need **two terminal windows**:

**Terminal 1 (Backend):**
```bash
cd backend && python main.py
```

**Terminal 2 (Frontend):**
```bash
cd front && npm run dev
```

---

## 📖 Usage Guide

### 1. Sign In

Navigate to `http://localhost:3000` and sign in with your Clerk account.

### 2. Dashboard

After signing in, you'll be redirected to the dashboard with two modes:

#### Mode 1: Direct Generation

1. Click the **microphone button** and describe your video
2. Or type your description in the text input
3. Click **"Generate Directly"** to skip the conversation
4. Wait for video generation (typically 30-60 seconds per scene)
5. Watch your generated video!

#### Mode 2: AI Discussion (Recommended)

1. Describe your initial idea via voice or text
2. Click **"Discuss with AI"**
3. Answer the AI's clarification questions
4. Once satisfied, click **"Generate Video"**
5. The AI will create a more refined video based on your conversation

### 3. Multi-Scene Stories

For complex narratives, KIWI-Video automatically:

1. Detects if your description contains multiple scenes
2. Segments the story (e.g., "wake up, drink coffee, go to work" → 3 scenes)
3. Generates each scene separately
4. Stitches all scenes into one final video

**Example:**
```
"A person wakes up in the morning, stretches, goes to the kitchen 
 to make coffee, and then walks out the door to go to work"
```
→ Automatically creates 3 separate video clips and combines them

---

## 🔌 API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/video/create` | Create video generation task |
| `GET` | `/api/task/{task_id}` | Get task status |
| `GET` | `/api/video/file/{filename}` | Download generated video |
| `POST` | `/api/conversation/message` | Send conversation message |
| `POST` | `/api/conversation/{id}/generate` | Generate from conversation |

### WebSocket

Connect to `/ws/{task_id}` for real-time updates:

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${taskId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.phase, data.progress, data.message);
  // { phase: "execution", progress: 75, message: "Generating video..." }
};
```

---

## 🛠️ Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python main.py  # Auto-reload enabled
```

### Frontend Development

```bash
cd front
npm run dev     # Hot reload enabled
```

### Adding New Agents

1. Create a new file in `backend/agents/`
2. Extend `BaseAgent` class
3. Implement `process()` method
4. Register in `orchestrator.py`
5. Export in `agents/__init__.py`

```python
from .base import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MyNewAgent",
            description="Does something amazing"
        )
    
    async def process(self, input_data):
        # Your logic here
        return {"success": True, "result": ...}

my_new_agent = MyNewAgent()
```

---

## 🔧 Configuration

### Backend Config (`config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server host |
| `API_PORT` | `8000` | Server port |
| `DEBUG` | `true` | Debug mode with auto-reload |
| `GEMINI_API_KEY` | - | Google Gemini API key |

### Frontend Environment

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key |
| `CLERK_SECRET_KEY` | Clerk secret key |

---

## 📦 Tech Stack

### Backend
- **FastAPI** - High-performance async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **google-genai** - Gemini & Veo 3 SDK
- **MoviePy** - Video processing
- **WebSockets** - Real-time communication

### Frontend
- **Next.js 15** - React framework (App Router)
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Clerk** - Authentication

---

## ⚠️ Known Limitations

1. **Veo 3 Access** - Requires Google AI Studio Veo 3 access (not available in all regions)
2. **Video Duration** - Maximum 8 seconds per scene
3. **Generation Time** - Each scene takes 30-60 seconds to generate
4. **API Quotas** - Subject to Gemini API rate limits

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) - AI models and Veo video generation
- [Clerk](https://clerk.com/) - Authentication
- [Next.js](https://nextjs.org/) - React framework
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework

---

<p align="center">
  Made with 💚 by the KIWI-Video Team
</p>


