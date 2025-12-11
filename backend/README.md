# KIWI-Video Backend

Backend API for voice-to-video generation using Multi-Agent architecture.

## Tech Stack

- **Framework**: FastAPI
- **Task Management**: In-memory async task manager
- **Real-time Updates**: WebSocket
- **Agent Framework**: Simple custom agents (Phase 1)

## Quick Start

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp env.example .env
# Edit .env with your API keys
```

### 4. Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info |
| GET | `/api/health` | Health check |
| POST | `/api/video/create` | Create video generation task |
| GET | `/api/video/status/{task_id}` | Get task status |
| GET | `/api/video/tasks` | List all tasks |
| DELETE | `/api/video/task/{task_id}` | Delete a task |

### WebSocket

Connect to `ws://localhost:8000/ws/{task_id}` to receive real-time updates.

#### Message Types

- `connected` - Initial connection with current status
- `progress` - Progress update during processing
- `complete` - Task completed successfully
- `error` - Task failed

## Example Usage

### Create a video task

```bash
curl -X POST http://localhost:8000/api/video/create \
  -H "Content-Type: application/json" \
  -d '{"text_input": "Create a 30-second promotional video about AI technology"}'
```

Response:
```json
{
  "task_id": "abc123...",
  "status": "pending",
  "message": "Video generation task created..."
}
```

### Check status

```bash
curl http://localhost:8000/api/video/status/abc123...
```

### WebSocket connection (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/abc123...');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

## Project Structure

```
backend/
├── main.py              # FastAPI entry point
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── api/
│   ├── routes.py        # REST endpoints
│   └── websocket.py     # WebSocket handler
├── agents/
│   ├── base.py          # Agent base class
│   └── orchestrator.py  # Main orchestrator
├── models/
│   └── schemas.py       # Pydantic models
└── services/
    └── task_manager.py  # Task management
```

## Features

### Phase 1 ✅
- ✅ Basic API structure
- ✅ Task creation and management
- ✅ WebSocket real-time updates
- ✅ Simple intent parsing
- ✅ Basic script generation

### Phase 2 ✅
- ✅ Gemini integration for intent understanding
- ✅ AI-powered script generation
- ✅ Fallback mode when API key not configured
- ✅ Audio data handling

### Phase 3 (Coming)
- ⏳ Video generation with Runway/Pika
- ⏳ Audio generation
- ⏳ Video editing and composition

## License

MIT

