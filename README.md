# Ollamometer

A web-based benchmarking tool for measuring LLM performance across different hardware configurations using Ollama.

## Features

- **Multi-Model Testing**: Benchmark multiple LLM models in a single run
- **Comprehensive Prompts**: 5 different prompt types to test various workload patterns
- **Real-Time Progress**: Live updates with Server-Sent Events (SSE)
- **Detailed Metrics**: Speed (tok/s), TTFT, memory usage (RAM/VRAM), and more
- **Statistics**: Min/max/standard deviation for performance analysis
- **Hardware Comparison**: Upload and compare results from multiple machines
- **Benchmark Cancellation**: Stop long-running benchmarks anytime
- **Auto-Pull Models**: Automatically download missing models with progress tracking

## Quick Start

### Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed and running

**Note**: You don't need to pre-download any models! Ollamometer will automatically pull any missing models when you start a benchmark.

### Installation

1. Clone this repository:
```bash
git clone https://github.com/hakehardware/ollamometer.git
cd ollamometer
```

2. Create your configuration file:
```bash
cp config.py.example config.py
```

3. Create and activate a virtual environment:

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

If you get a script execution error in PowerShell, use one of these solutions:

**Option A**: Use Command Prompt instead of PowerShell (recommended for simplicity)

**Option B**: Enable script execution in PowerShell (run as Administrator):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Option C**: Bypass for this session only:
```powershell
powershell -ExecutionPolicy Bypass -File venv\Scripts\Activate.ps1
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure your system (edit `config.py`):
   - Set `OLLAMA_BASE_URL` if Ollama is on a different machine
   - Update `SYSTEM_INFO` with your hardware specifications
   - Customize `AVAILABLE_MODELS` if desired

6. Run the application:
```bash
python ollamometer.py
```

7. Open your browser to `http://localhost:5555`

**Note**: To deactivate the virtual environment when done, simply run `deactivate`.

## Configuration

**Note**: Your `config.py` file is not tracked by git, so pulling updates won't overwrite your settings. After pulling updates, check `config.py.example` for any new configuration options.

### Ollama Server

By default, Ollamometer connects to `http://localhost:11434`. If your Ollama instance is running elsewhere:

1. Edit `config.py`
2. Change `OLLAMA_BASE_URL` to your Ollama server URL
3. If remote, ensure Ollama allows network connections (see Ollama docs)

### System Information

Edit the `SYSTEM_INFO` dictionary in `config.py` to match your hardware:

```python
SYSTEM_INFO = {
    "name": "my-gaming-pc",
    "cpu_model": "Intel Core i7-12700K",
    "cpu_cores": 12,
    "ram_gb": 32.0,
    "gpu_model": "NVIDIA RTX 4070",
    "gpu_vram_gb": 12.0,
    "os_name": "Windows",
    "os_version": "11",
}
```

This information is included in benchmark results for hardware comparison.

### Models

Add or remove models in `config.py`:

```python
AVAILABLE_MODELS = [
    "llama3.2:1b",
    "llama3.2:3b",
    "qwen2.5:3b",
    "mistral:7b",
]
```

## Usage

### Running a Benchmark

1. Visit `http://localhost:5555`
2. Select models to test (checkboxes)
   - Models with "Ready" badge are downloaded
   - Models with "Need Pull" badge will be auto-downloaded when you start
3. Select prompts to use (checkboxes)
4. Choose number of runs per test (dropdown)
5. Click "Start Benchmark"
   - If any models need downloading, they'll be pulled automatically with progress bar
6. View real-time progress during benchmark
7. See results with detailed metrics and statistics
8. Download results as JSON for comparison

### Cancelling a Benchmark

During a running benchmark:
1. Click the red "Cancel Benchmark" button
2. Confirm cancellation
3. Benchmark stops and returns to home

### Comparing Hardware

To compare performance across multiple machines:

1. Run benchmarks on each machine
2. Download the JSON results from each
3. Go to `/compare` page
4. Upload all JSON files
5. View side-by-side performance comparison

The comparison view shows:
- System specifications table
- Performance metrics with filtering
- Best/worst performer highlighting
- Statistical analysis (avg, min, max, stdev)

## Metrics Captured

### Performance Metrics
- **Speed**: Tokens per second (generation speed)
- **TTFT**: Time to First Token (latency)
- **Total Duration**: End-to-end inference time
- **Load Duration**: Model loading time

### Memory Metrics
- **RAM Usage**: Total model size in system memory
- **VRAM Usage**: GPU memory usage
- **Compute Mode**: CPU-only / Full GPU / Hybrid

### Statistics
- Average, minimum, maximum values
- Standard deviation (performance consistency)
- Per-model, per-prompt breakdown

## Benchmark Prompts

Ollamometer includes 5 carefully designed prompts:

1. **Quick Q&A**: Tests TTFT and cold start (short/short)
2. **Code Generation**: Tests sustained generation (short/long)
3. **Creative Writing**: Tests long output generation (short/long)
4. **Multi-Step Reasoning**: Tests analytical performance (short/medium)
5. **Detailed Analysis**: Tests comprehensive workload (short/long)

You can customize these in `config.py`.

## Use Cases

- **Hardware Comparison**: Clone to multiple PCs (e.g., 5 different GPUs), run identical benchmarks, upload all results to comparison page to see performance rankings
- **Model Selection**: Find the best model for your specific hardware configuration
- **Performance Tuning**: Validate system optimizations and see measurable improvements
- **Before/After Testing**: Compare performance after hardware upgrades or software changes
- **Multi-Machine Showcase**: Generate comprehensive performance reports across different systems

## Project Structure

```
ollamometer/
├── app/
│   ├── __init__.py
│   ├── routes.py              # Flask routes and API endpoints
│   ├── ollama_client.py       # Ollama API wrapper
│   ├── benchmark_runner.py    # Benchmark orchestration
│   ├── progress_tracker.py    # Thread-safe progress tracking
│   └── system_info.py         # System information utilities
├── static/
│   ├── css/
│   │   └── style.css          # Dark theme styles
│   └── js/
│       └── app.js             # Frontend JavaScript
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Home page (model/prompt selection)
│   ├── progress.html          # Real-time progress page
│   ├── results.html           # Results display and export
│   └── compare.html           # Multi-machine comparison
├── config.py                  # Configuration file
├── ollamometer.py            # Application entry point
└── requirements.txt          # Python dependencies
```

## Development

### Running in Debug Mode

Debug mode is enabled by default in `config.py`:

```python
DEBUG = True  # Set to False in production
```

### Modifying the UI

- CSS: Edit `static/css/style.css`
- Templates: Edit files in `templates/`
- JavaScript: Edit `static/js/app.js`

### Adding New Metrics

1. Update `BenchmarkResult` dataclass in `app/benchmark_runner.py`
2. Add metric extraction in `_run_single_test()`
3. Update `templates/results.html` to display new metric
4. Update JSON export structure if needed

## Troubleshooting

### Ollama Connection Failed

- Ensure Ollama is running: `ollama serve`
- Check URL in `config.py` matches your Ollama instance
- For remote Ollama, enable network connections in Ollama settings

### Models Not Showing

- Pull at least one model: `ollama pull llama3.2:3b`
- Verify models in `AVAILABLE_MODELS` exist in your Ollama
- Check Ollama API is accessible

### Port Already in Use

Change the port in `config.py`:

```python
PORT = 8080  # Or any available port
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Acknowledgments

- Built for [Ollama](https://ollama.ai/)
- Uses Flask for the web interface
- Inspired by the need for hardware-specific LLM benchmarking

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
