# KIWI-Video: Multi-Agent Text-to-Video Generation Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

KIWI-Video is a production-ready, multi-agent framework for generating professional videos from text using AI. It orchestrates multiple specialized AI agents to handle script generation, storyboarding, video production, and voice synthesis.

## ✨ Features

- **Multi-Agent Architecture**: Specialized agents for each stage of video production
- **Google Veo Integration**: State-of-the-art AI video generation
- **Gemini LLM**: Intelligent decision-making and content generation
- **ElevenLabs TTS**: High-quality voice synthesis
- **REST API**: Production-ready FastAPI interface
- **Async/Await**: High-performance async operations
- **Type-Safe**: Full type annotations with Pydantic
- **Extensible**: Easy to add new providers and agents

## 🏗️ Architecture

```
User Input → Director Orchestrator
               ↓
    ┌──────────┴──────────┬──────────────┬──────────────┐
    ↓                     ↓              ↓              ↓
StoryLoader          Storyboard      FilmCrew      VoiceActor
  Agent               Agent           Agent          Agent
    ↓                     ↓              ↓              ↓
    └──────────┬──────────┴──────────────┴──────────────┘
               ↓
        Final Video Output
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Cloud account (for Veo)
- Gemini API key
- ElevenLabs API key

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/kiwi-video.git
cd kiwi-video

# Setup environment
make setup

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` file with your credentials:

```bash
GEMINI_API_KEY=your_gemini_key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET=your_bucket_name
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### Run Development Server

```bash
make dev
```

The API will be available at `http://localhost:8000`

## 📖 Usage

### Python API

```python
from kiwi_video import DirectorOrchestrator

# Create orchestrator
orchestrator = DirectorOrchestrator(project_id="my_project")

# Generate video
result = await orchestrator.execute_project(
    user_input="Create an inspiring video about space exploration"
)

print(f"Video generated: {result['final_video_path']}")
```

### REST API

```bash
# Create a new video project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create an inspiring video about space exploration"}'

# Get project status
curl http://localhost:8000/api/v1/projects/{project_id}
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=kiwi_video --cov-report=html
```

## 🛠️ Development

```bash
# Format code
make format

# Run linting
make lint

# Run full check
make check
```

## 📦 Docker Deployment

```bash
# Build image
make docker-build

# Start containers
make docker-up

# View logs
make docker-logs
```

## 📚 Documentation

For detailed documentation, see:

- [API Documentation](docs/api.md)
- [Agent Guide](docs/agents.md)
- [Configuration](docs/configuration.md)
- [Contributing](CONTRIBUTING.md)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini & Veo teams
- ElevenLabs
- FastAPI community
- All contributors

## 📧 Contact

For questions and support, please open an issue on GitHub.

