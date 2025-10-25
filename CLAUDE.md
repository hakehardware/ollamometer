# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ollamometer is a Flask-based web application for benchmarking Ollama LLM models across different hardware configurations. It provides a user-friendly interface for running comprehensive benchmarks, viewing real-time progress, and comparing results across multiple machines.

## Architecture

**Flask Web Application** (`ollamometer.py`)
- App factory pattern with Flask blueprints
- Runs on port 5555 (configurable in `config.py`)
- Server-Sent Events (SSE) for real-time progress updates
- Thread-safe background processing for long-running operations

**Core Modules**:

- **`app/routes.py`**: Flask routes and API endpoints
  - `/` - Home page (model/prompt selection)
  - `/progress` - Real-time progress display
  - `/results` - Benchmark results with statistics
  - `/compare` - Multi-machine comparison mode
  - `/api/*` - REST API endpoints for benchmark control

- **`app/ollama_client.py`**: Ollama REST API wrapper
  - `is_available()` - Check Ollama server status
  - `pull_model()` - Download models with progress tracking
  - `generate()` - Run inference and capture metrics
  - `unload_model()` - Free memory between tests
  - `get_loaded_models()` - Check RAM/VRAM usage

- **`app/benchmark_runner.py`**: Benchmark orchestration
  - `BenchmarkRunner` class - Coordinates multi-model × multi-prompt tests
  - `BenchmarkResult` dataclass - Stores all metrics with computed properties
  - Automatic model unloading for clean state between tests
  - Memory usage tracking (RAM/VRAM)

- **`app/progress_tracker.py`**: Thread-safe progress tracking
  - `ProgressState` dataclass - Current operation state
  - `ProgressTracker` class - Thread-safe state management with locking
  - Supports cancellation of running operations
  - Metadata support for additional context

- **`app/system_info.py`**: System information utilities
  - `get_compute_mode()` - Determine CPU-only / Full GPU / Hybrid

**Key Workflow**:
1. User selects models and prompts via web UI
2. Benchmark runs in background thread
3. Progress updates sent via SSE to frontend
4. For each model × prompt × run:
   - Unload model (clean state)
   - Run inference via Ollama API
   - Capture timing and memory metrics
   - Check for cancellation
5. Calculate statistics (avg, min, max, stdev)
6. Display results with download option
7. Compare mode allows uploading multiple JSONs for comparison

**Metrics Captured**:
- Performance: `total_duration`, `load_duration`, `prompt_eval_*`, `eval_*`, `tokens_per_second`, `time_to_first_token`
- Memory: `model_size_bytes` (RAM), `model_size_vram_bytes` (VRAM)
- Compute: CPU-only / Full GPU / Hybrid mode detection
- Statistics: min, max, avg, stdev for all metrics

## Configuration

Edit `config.py` for:
- `OLLAMA_BASE_URL` - Ollama server location (default: localhost:11434)
- `AVAILABLE_MODELS` - Models to benchmark
- `BENCHMARK_PROMPTS` - Test prompts with different workload patterns
- `SYSTEM_INFO` - Hardware specifications (manual configuration)
- `PORT` / `HOST` / `DEBUG` - Flask server settings

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Configure system info in config.py
# Then run
python ollamometer.py
```

Visit `http://localhost:5555` in your browser.

## Development Guidelines

**Code Style**:
- Use type hints for all function parameters and return values
- Use dataclasses for structured data (see `BenchmarkResult`)
- Keep functions focused and single-purpose (DRY principle)
- Proper docstrings for all public methods

**Threading**:
- Long operations run in daemon threads
- Use `progress_tracker` for thread-safe state sharing
- Always use locks (`threading.Lock`) for shared state
- Check cancellation flags in loops

**Frontend**:
- Use Server-Sent Events (SSE) for real-time updates
- EventSource API for progress streaming
- Vanilla JavaScript (no frameworks)
- Dark theme CSS variables in `style.css`

**API Endpoints**:
- GET endpoints for data retrieval
- POST endpoints for actions (start benchmark, cancel, pull models)
- SSE endpoint (`/api/progress`) for streaming updates
- Return JSON with consistent error structure

## Key Files

- `ollamometer.py` - Application entry point
- `config.py` - Configuration (EDIT THIS for your setup)
- `app/routes.py` - All Flask routes and API endpoints
- `app/benchmark_runner.py` - Core benchmarking logic
- `templates/` - Jinja2 templates for all pages
- `static/css/style.css` - Dark theme styles
- `static/js/app.js` - Frontend JavaScript

## Common Tasks

**Adding a new model**:
Edit `AVAILABLE_MODELS` in `config.py`

**Adding a new prompt**:
Add entry to `BENCHMARK_PROMPTS` in `config.py`

**Adding a new metric**:
1. Update `BenchmarkResult` dataclass
2. Extract metric in `_run_single_test()`
3. Add to results table in `templates/results.html`
4. Add to statistics calculation in JavaScript

**Customizing UI**:
- Edit templates in `templates/`
- Edit CSS in `static/css/style.css`
- Edit JS in `static/js/app.js`

## Dependencies

- Flask >= 3.0.0 - Web framework
- requests >= 2.31.0 - HTTP client for Ollama API
- Python standard library (threading, json, dataclasses, typing)

## Notes

- Uses Ollama REST API (not CLI) for structured responses
- All timing metrics in nanoseconds (converted to seconds for display)
- SSE streams close automatically after operation completes
- Benchmarks can be cancelled mid-run
- JSON export includes both raw results and statistics