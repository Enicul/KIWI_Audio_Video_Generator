"""Unit tests for agents."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from kiwi_video.agents.story_loader import StoryLoaderAgent
from kiwi_video.agents.storyboard import StoryboardAgent
from kiwi_video.core.state_manager import StateManager


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = Mock()
    client.generate = AsyncMock(return_value="Generated text")
    client.stream = Mock(return_value='{"topic": "test", "scenes": []}')
    return client


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def state_manager(temp_workspace):
    """Create state manager."""
    return StateManager(temp_workspace)


class TestStoryLoaderAgent:
    """Tests for StoryLoaderAgent."""

    def test_initialization(self, mock_llm_client, state_manager, temp_workspace):
        """Test agent initialization."""
        agent = StoryLoaderAgent(
            agent_name="story_loader",
            llm_client=mock_llm_client,
            state_manager=state_manager,
            workspace_dir=temp_workspace
        )

        assert agent.agent_name == "story_loader"
        assert agent.workspace_dir == temp_workspace

    def test_fallback_script_generation(self, mock_llm_client, state_manager, temp_workspace):
        """Test fallback script generation."""
        agent = StoryLoaderAgent(
            agent_name="story_loader",
            llm_client=mock_llm_client,
            state_manager=state_manager,
            workspace_dir=temp_workspace
        )

        script = agent._create_fallback_script("space exploration", "professional")

        assert "topic" in script
        assert "scenes" in script
        assert len(script["scenes"]) == 3
        assert script["topic"] == "space exploration"


class TestStoryboardAgent:
    """Tests for StoryboardAgent."""

    def test_initialization(self, mock_llm_client, state_manager, temp_workspace):
        """Test agent initialization."""
        agent = StoryboardAgent(
            agent_name="storyboard",
            llm_client=mock_llm_client,
            state_manager=state_manager,
            workspace_dir=temp_workspace
        )

        assert agent.agent_name == "storyboard"

    def test_default_shots_creation(self, mock_llm_client, state_manager, temp_workspace):
        """Test default shots creation."""
        agent = StoryboardAgent(
            agent_name="storyboard",
            llm_client=mock_llm_client,
            state_manager=state_manager,
            workspace_dir=temp_workspace
        )

        scene = {
            "scene_id": "scene_001",
            "scene_description": "Test scene",
            "voice_over_text": "Test narration",
            "duration": 8.0
        }

        shots = agent._create_default_shots(scene)

        assert len(shots) == 1
        assert shots[0]["shot_id"] == 1
        assert "visuals" in shots[0]

