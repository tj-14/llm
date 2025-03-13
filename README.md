# LLM CLI Chat Interface

A command-line interface for interacting with various Large Language Models (LLMs) with conversation management and RAG capabilities.

## Features

- **Multi-Model Support**:
  - Mistral AI (`mistral-small-latest`)
  - OpenTyphoon (`typhoon-v2-70b-instruct`)
  - Together AI (Llama 3.3 and DeepSeek models)

- **Interactive Chat Interface**:
  - Terminal-based with streaming responses
  - Rich Markdown rendering

- **Conversation Management**:
  - Save conversations with automatic summarization
  - Load previous conversations
  - Undo messages

- **RAG (Retrieval-Augmented Generation)**:
  - Fetch content from URLs as context
  - Search local files using ripgrep and fzf

- **Utility Features**:
  - Multi-line input mode
  - Copy responses to clipboard
  - Comprehensive logging

## Installation

1. Clone the repository
2. Ensure Python 3.13+ is installed
3. Install dependencies:
   ```bash
   pip install -e .
   ```
   or
   ```bash
   uv pip install -e .
   ```

## Configuration

Create a `.env` file with your API keys:

```
MISTRAL_API_KEY=your_mistral_api_key
TOGETHER_API_KEY=your_together_api_key
OPENTYPHOON_API_KEY=your_opentyphoon_api_key
```

## Usage

Run the application:

```bash
python main.py --model [model_name]
```

Where `model_name` can be:
- `mistral` (default)
- `typhoon`
- `llama`
- `deepseek`

### Commands

During chat, you can use these special commands:

- `'` - Enter multi-line input mode (end with Ctrl+D)
- `url` - Fetch content from a URL to use as context
- `rg` - Search local files and use content as context
- `undo` - Remove the last message pair
- `save` - Save the current conversation
- `load` - Load a previous conversation
- `copy` - Copy the last response to clipboard

## Database

Conversations are stored in SQLite at `~/.llm/conversations.db`

## Logs

Chat logs are saved to `~/.llm/logs/` with timestamps