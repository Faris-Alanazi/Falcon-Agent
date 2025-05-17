# Falcon Agent 🦅

An intelligent coding agentic system capable of developing enterprise-level code through a coordinated network of specialized AI agents.

## Overview

Falcon Agent transforms natural language requirements into production-ready code through a series of specialized agents that handle different aspects of the software development lifecycle. The system minimizes human intervention while maximizing output quality.

### Core Features

- **Multi-Agent Ecosystem**: Six specialized agents working in coordination
- **AI-Powered Development**: Based on the Qwen3:8b open-source model
- **Autonomous Execution**: Full development pipeline from requirements to code
- **Real-Time Visualization**: Browser-based UI to monitor development
- **File System Management**: Smart collaboration between agents

## System Architecture

### Technical Foundation

- **AI Model**: Qwen3:8b open-source model
- **Framework**: CrewAI framework for agent coordination
- **Backend**: Python-based system architecture
- **Frontend**: Browser-based modern UI
- **Execution Environment**: Local file system with web visualization

### Agent Specifications

The system employs six specialized agents:

1. **Requirementer Agent**: Analyzes user requests and produces a PRD
2. **Tasker Agent**: Transforms PRDs into actionable Goal Graphs
3. **Goaler Agent**: Validates Goal Graphs against requirements
4. **Coder Agents**: Implement code based on specifications
5. **Qualitator Agent**: Ensures code quality and alignment
6. **Communicator Agent**: Presents completed projects to users

## Installation

### Prerequisites

- Python 3.9+
- Git
- Access to AI model API (if using remote models)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/faris-alanazi/falcon-agent.git
   cd falcon-agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   # or
   pip install -r requirements.txt
   ```

4. Configure API keys:
   Create a `.env` file with necessary API keys (see `.env.example`)

## Usage

### Basic Usage

```bash
python -m src.main --input "Create a simple React web application with a to-do list feature"
```

### Advanced Configuration

Edit `config.yaml` to customize:
- Model parameters
- Agent behavior
- UI configuration
- File system management

## Development

### Project Structure

- `src/agents/`: Agent implementations
- `src/utils/`: Utility functions
- `src/core/`: Core system functionality
- `src/models/`: Model integrations
- `src/ui/`: User interface components
- `src/tools/`: Tool implementations
- `tests/`: Test suite

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgements

- [CrewAI Framework](https://github.com/joaomdmoura/crewAI)
- [Qwen LLM](https://huggingface.co/Qwen) 