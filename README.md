# LocAIted - AI-Powered Event Discovery for Photojournalists

LocAIted is a multi-agent system that helps photojournalists discover newsworthy events in New York City. It automates the process of finding, verifying, and curating events worth photographing, saving journalists hours of manual research.

## Overview

LocAIted uses a sophisticated pipeline of AI agents to:
- Understand photographer interests and generate targeted event leads
- Search for evidence of real events happening
- Extract concrete event details from search results
- Curate and score events based on photographic potential

## Success Metrics (North Star)

LocAIted's performance is measured by three critical metrics:

1. **Number of Interesting Events**: How many genuinely newsworthy events are discovered
2. **Number of Events with Basic Info**: How many events include ALL essential details:
   - Clear event title
   - Specific date
   - Start time
   - Precise location (enough to plan commute)
3. **Number of Duplicate Events**: How effectively the system deduplicates similar events

### Key Features

- **Smart Event Discovery**: LLM-powered lead generation tailored to photographer interests
- **Evidence-Based Verification**: Automated web searches to verify event existence
- **Quality Curation**: Intelligent scoring and filtering to surface the best opportunities
- **Cost-Efficient**: Aggressive caching and smart batching to minimize API costs
- **Time-Aware**: Focuses on events happening in the requested timeframe

## Architecture

LocAIted v0.4.0 uses a LangGraph-orchestrated pipeline with four specialized agents:

```
User Input → Editor → Researcher → Fact-Checker → Publisher → Final Events
                ↑                                        ↓
                └──────── Retry with Feedback ───────────┘
```

### Agents

1. **Editor (LLM-based)**: Creates search profiles from user input and handles retry feedback
2. **Researcher (LLM-based)**: Generates 25 specific, searchable event leads
3. **Fact-Checker (API-based)**: Searches for evidence using Tavily web search API
4. **Publisher (LLM-based)**: Extracts events from evidence and makes quality gate decisions

## Installation

### Prerequisites

- macOS or Linux (Windows users: use WSL2)
- Python 3.11 or higher
- Micromamba (lightweight conda alternative)

### Quick Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/locaited.git
cd locaited
```

2. **Install Micromamba** (if not already installed)
```bash
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)
```

3. **Create and activate the environment**
```bash
micromamba create -f environment.yml
micromamba activate locaited
```

4. **Set up API keys**
```bash
cp .env.example .env.secret
# Edit .env.secret with your API keys:
# - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys
# - TAVILY_API_KEY: Get from https://tavily.com/
```

### Manual Setup (Alternative)

If you prefer using pip directly:

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env.secret
# Edit .env.secret with your API keys
export $(cat .env.secret | xargs)
```

## Usage

### Basic Usage

```python
from src.agents.workflow_v4 import WorkflowV4

# Initialize workflow
workflow = WorkflowV4()

# Run event discovery
result = workflow.run_workflow({
    "location": "New York City",
    "time_frame": "this week",
    "interests": ["protests", "cultural events", "political events"]
})

# Access results
events = result.get('events', [])
for event in events:
    print(f"{event['title']} - {event['date']} at {event['location']}")
```

### Command Line Testing

```bash
# Test single workflow run
micromamba run -n locaited python test_single.py

# Run benchmark against test data
micromamba run -n locaited python benchmark_simple.py

# Test specific components
micromamba run -n locaited python test_workflow_v4.py
```

## Configuration

### Environment Variables (.env.secret)

```bash
# Required API Keys
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...

# Optional Configuration
OPENAI_MODEL=gpt-4.1-mini  # Model to use
MAX_COST_PER_QUERY=0.10    # Maximum cost per workflow run
```

### Cost Management

- **OpenAI**: ~$0.006 per workflow run (3-4 LLM calls)
- **Tavily**: ~$0.025 per workflow run (25 searches)
- **Total**: ~$0.03 per complete workflow

The system includes:
- Aggressive file-based caching to avoid duplicate searches
- Token limit management to prevent oversized responses
- Cost tracking and reporting for all API calls

## Development

### Project Structure

```
locaited/
├── src/
│   ├── agents/
│   │   ├── base_agent.py      # Base classes with caching
│   │   ├── editor_v4.py       # Profile builder
│   │   ├── researcher_v4.py   # Lead generator
│   │   ├── fact_checker_v4.py # Evidence gatherer
│   │   ├── publisher_v4.py    # Event extractor
│   │   └── workflow_v4.py     # LangGraph orchestration
│   └── utils/
│       ├── llm_client.py      # OpenAI wrapper
│       └── tavily_client.py   # Tavily wrapper
├── cache/                      # Cached search results
├── test data/                  # Benchmark test data
├── environment.yml             # Micromamba environment
├── requirements.txt            # Python dependencies
└── CLAUDE.md                   # Development context
```

### Running Tests

```bash
# Run all tests
micromamba run -n locaited python test_workflow_v4.py

# Run benchmark
micromamba run -n locaited python benchmark_simple.py

# Test individual agents
micromamba run -n locaited python -c "
from src.agents.researcher_v4 import ResearcherV4
researcher = ResearcherV4()
# Test researcher...
"
```

### Key Design Principles

1. **Budget Awareness**: Limited API credits require smart caching and batching
2. **Quality Over Quantity**: Return 10-15 high-quality events rather than exhaustive lists
3. **LLM-First**: Use LLMs for text processing, parsing, and decision-making
4. **Fail Gracefully**: Handle API errors and provide meaningful feedback
5. **Cache Aggressively**: Save all API responses for reuse

## API Documentation

### WorkflowV4.run_workflow()

Main entry point for event discovery.

**Parameters:**
- `user_input` (dict): Contains:
  - `location` (str): Event location (default: "New York City")
  - `time_frame` (str): Time period (e.g., "this week", "next 2 weeks", "September 2025")
  - `interests` (list): Event types of interest (e.g., ["protests", "cultural events"])

**Returns:**
- Dictionary containing:
  - `events` (list): Curated event list with title, date, location, description
  - `gate_decision` (str): "APPROVE", "RETRY", or "ERROR"
  - `workflow_metrics` (dict): Cost and performance metrics
  - `feedback` (str): Explanation if retry needed

## Troubleshooting

### Common Issues

1. **JSON Parsing Errors**: Usually means response too large
   - Solution: Publisher now limits to 15 events max

2. **High API Costs**: Too many uncached searches
   - Solution: Enable caching, reuse test queries

3. **Wrong Date Events**: Events outside requested timeframe
   - Solution: Researcher prompts now enforce date constraints

4. **Micromamba Activation Issues**: Shell not initialized
   - Solution: Use `micromamba run -n locaited` prefix for all commands

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.INFO)  # See detailed logs
```

## Future Development

See [Future Development Index](docs/future/INDEX.md) for planned features and enhancements.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make changes following existing patterns
4. Test thoroughly (`micromamba run -n locaited python test_workflow_v4.py`)
5. Commit with clear messages
6. Push and create a Pull Request
7. For new features, consider adding a PRD in `docs/future/`

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built for photojournalists covering New York City
- Powered by OpenAI GPT-4.1-mini and Tavily Search API
- Orchestrated with LangGraph for robust agent coordination

## Contact

For questions, issues, or suggestions, please open an issue on GitHub.