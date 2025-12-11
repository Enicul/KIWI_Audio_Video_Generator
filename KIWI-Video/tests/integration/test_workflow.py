"""Integration tests for complete workflow."""

import pytest
from pathlib import Path

from kiwi_video.core.orchestrator import DirectorOrchestrator
from kiwi_video.core.state_manager import StateManager
from kiwi_video.schemas.project import ProjectStatus


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace."""
    workspace = tmp_path / "test_projects"
    workspace.mkdir()
    return workspace


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires actual API keys and may take long time")
async def test_full_workflow(temp_workspace):
    """
    Test complete video generation workflow.
    
    Note: This test requires actual API credentials and will make real API calls.
    """
    # Create orchestrator
    orchestrator = DirectorOrchestrator(
        project_id="test_project_001",
        workspace_dir=temp_workspace / "test_project_001"
    )

    # Execute project
    result = await orchestrator.execute_project(
        user_input="Create a short inspiring video about artificial intelligence"
    )

    # Verify result
    assert result["status"] == "success"
    assert "final_video_path" in result
    assert Path(result["final_video_path"]).exists()


def test_state_manager_initialization(temp_workspace):
    """Test state manager initialization."""
    project_dir = temp_workspace / "test_project"
    project_dir.mkdir()

    state_manager = StateManager(project_dir)

    # Verify state file created
    assert state_manager.state_file.exists()

    # Verify initial state
    state = state_manager.get_state()
    assert state["status"] == "initialized"
    assert "phases" in state


def test_state_manager_phase_tracking(temp_workspace):
    """Test phase status tracking."""
    project_dir = temp_workspace / "test_project"
    project_dir.mkdir()

    state_manager = StateManager(project_dir)

    # Start a phase
    state_manager.start_phase("story_loader")
    state = state_manager.get_state()
    assert state["phases"]["story_loader"]["status"] == "in_progress"

    # Complete the phase
    state_manager.complete_phase("story_loader", {"output": "test"})
    state = state_manager.get_state()
    assert state["phases"]["story_loader"]["status"] == "completed"


def test_orchestrator_initialization(temp_workspace):
    """Test orchestrator initialization."""
    orchestrator = DirectorOrchestrator(
        project_id="test_init",
        workspace_dir=temp_workspace / "test_init"
    )

    assert orchestrator.project_id == "test_init"
    assert orchestrator.workspace_dir.exists()
    assert orchestrator.state_manager is not None


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires mock implementations")
async def test_orchestrator_phases(temp_workspace):
    """Test orchestrator phase execution."""
    orchestrator = DirectorOrchestrator(
        project_id="test_phases",
        workspace_dir=temp_workspace / "test_phases"
    )

    # This would require mocking the agents
    # For now, just verify initialization
    assert orchestrator._story_loader is None
    assert orchestrator._storyboard is None

