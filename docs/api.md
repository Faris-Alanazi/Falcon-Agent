# Falcon Agent API Reference

This document provides information about the Falcon Agent system API, both for internal agent communication and external integration.

## Core API Classes

### AgentManager

The central API for managing agent interactions and system coordination.

```python
class AgentManager:
    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize the agent manager with the given configuration."""
        pass
    
    def create_agent(self, agent_type: str, agent_id: str = None) -> Agent:
        """Create a new agent of the specified type."""
        pass
    
    def submit_request(self, request: str) -> str:
        """Submit a new user request to start the development process."""
        pass
    
    def get_status(self) -> dict:
        """Get the current status of the entire system."""
        pass
    
    def get_task_status(self, task_id: str) -> dict:
        """Get the status of a specific task."""
        pass
    
    def cancel_process(self) -> bool:
        """Cancel the current development process."""
        pass
```

### CrewFactory

API for creating and configuring the multi-agent crew using CrewAI.

```python
class CrewFactory:
    def __init__(self, agent_manager: AgentManager):
        """Initialize with the agent manager."""
        pass
    
    def create_crew(self) -> Crew:
        """Create a new crew with all necessary agents."""
        pass
    
    def get_agent(self, agent_id: str) -> Agent:
        """Get a specific agent from the crew."""
        pass
    
    def run_task(self, task_description: str) -> dict:
        """Run a specific task through the crew."""
        pass
```

## Agent APIs

Each agent exposes a specific API aligned with its responsibilities.

### RequirementerAgent

```python
class RequirementerAgent(Agent):
    def analyze_request(self, request: str) -> dict:
        """Analyze a user request and generate initial understanding."""
        pass
    
    def generate_prd(self, request: str, clarifications: dict = None) -> str:
        """Generate a complete PRD from user request and optional clarifications."""
        pass
    
    def ask_clarification(self, request: str, unclear_points: list) -> list:
        """Generate clarification questions for unclear points."""
        pass
```

### TaskerAgent

```python
class TaskerAgent(Agent):
    def create_goal_graph(self, prd: str) -> dict:
        """Create a goal graph from a PRD."""
        pass
    
    def update_task(self, task_id: str, updates: dict) -> dict:
        """Update a specific task in the goal graph."""
        pass
    
    def get_tasks(self, status: str = None) -> list:
        """Get all tasks, optionally filtered by status."""
        pass
    
    def validate_dependencies(self) -> bool:
        """Validate that task dependencies are consistent."""
        pass
```

### GoalerAgent

```python
class GoalerAgent(Agent):
    def validate_goal_graph(self, goal_graph: dict, prd: str) -> bool:
        """Validate a goal graph against the PRD."""
        pass
    
    def suggest_improvements(self, goal_graph: dict, prd: str) -> list:
        """Suggest improvements for the goal graph."""
        pass
    
    def approve_goal_graph(self, goal_graph: dict) -> bool:
        """Formally approve a goal graph for implementation."""
        pass
```

### CoderAgent

```python
class CoderAgent(Agent):
    def select_task(self) -> str:
        """Select an appropriate task to work on."""
        pass
    
    def implement_task(self, task_id: str) -> dict:
        """Implement the specified task."""
        pass
    
    def request_review(self, task_id: str, files: list) -> bool:
        """Request a review for a completed task."""
        pass
    
    def lock_file(self, file_path: str) -> bool:
        """Lock a file for editing."""
        pass
    
    def unlock_file(self, file_path: str) -> bool:
        """Unlock a previously locked file."""
        pass
```

### QualitatorAgent

```python
class QualitatorAgent(Agent):
    def review_task(self, task_id: str) -> dict:
        """Review a task that has been marked for review."""
        pass
    
    def approve_task(self, task_id: str) -> bool:
        """Approve a reviewed task."""
        pass
    
    def request_changes(self, task_id: str, feedback: str) -> bool:
        """Request changes to a task with detailed feedback."""
        pass
    
    def check_code_quality(self, file_path: str) -> dict:
        """Check the code quality of a specific file."""
        pass
```

### CommunicatorAgent

```python
class CommunicatorAgent(Agent):
    def generate_summary(self) -> str:
        """Generate a summary of the development process."""
        pass
    
    def prepare_deliverables(self) -> dict:
        """Prepare the final deliverables for the user."""
        pass
    
    def format_presentation(self, deliverables: dict) -> str:
        """Format the deliverables into a presentable format."""
        pass
```

## File System API

The API for managing file system interactions between agents.

```python
class FileManager:
    def lock_file(self, file_path: str, agent_id: str) -> bool:
        """Lock a file for exclusive access by an agent."""
        pass
    
    def unlock_file(self, file_path: str, agent_id: str) -> bool:
        """Unlock a file previously locked by an agent."""
        pass
    
    def is_locked(self, file_path: str) -> tuple:
        """Check if a file is locked and by which agent."""
        pass
    
    def read_file(self, file_path: str, agent_id: str) -> str:
        """Read a file, even if locked (but track the access)."""
        pass
    
    def write_file(self, file_path: str, content: str, agent_id: str) -> bool:
        """Write to a file if the agent has the lock."""
        pass
    
    def get_changes(self, since: datetime = None) -> dict:
        """Get all file changes since a given time."""
        pass
```

## Memory API

API for managing agent memory and shared knowledge.

```python
class MemoryManager:
    def store(self, agent_id: str, key: str, value: any, shared: bool = False) -> bool:
        """Store a value in an agent's memory, optionally shared."""
        pass
    
    def retrieve(self, agent_id: str, key: str) -> any:
        """Retrieve a value from an agent's memory."""
        pass
    
    def retrieve_shared(self, key: str) -> any:
        """Retrieve a value from shared memory."""
        pass
    
    def forget(self, agent_id: str, key: str) -> bool:
        """Remove a value from an agent's memory."""
        pass
    
    def get_context(self, agent_id: str, keys: list = None) -> dict:
        """Get the current context for an agent, optionally filtered by keys."""
        pass
```

## External API Endpoints

REST API endpoints for external integration.

### Project Management

- `POST /api/projects`: Create a new development project
- `GET /api/projects/{id}`: Get project details
- `GET /api/projects/{id}/status`: Get project status
- `DELETE /api/projects/{id}`: Cancel a project

### Tasks

- `GET /api/projects/{id}/tasks`: List all tasks
- `GET /api/projects/{id}/tasks/{task_id}`: Get task details
- `PATCH /api/projects/{id}/tasks/{task_id}`: Update task status

### Files

- `GET /api/projects/{id}/files`: List all project files
- `GET /api/projects/{id}/files/{path}`: Get file content
- `GET /api/projects/{id}/changes`: Get file change history

### UI Integration

- `GET /api/ui/status`: Get real-time system status for UI
- `GET /api/ui/events`: Event stream for UI updates
- `GET /api/ui/visualization`: Get data for UI visualization

## WebSocket Events

Real-time events for UI integration.

- `agent_status`: Updates on agent status changes
- `task_status`: Updates on task status changes
- `file_change`: Notifications of file changes
- `message`: Agent-to-agent or system-to-user messages
- `error`: Error notifications
- `completion`: Project completion notification 