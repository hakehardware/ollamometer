"""
Flask routes for Ollamometer web interface
"""

from flask import Blueprint, render_template, jsonify, Response, request, stream_with_context
from app.ollama_client import OllamaClient
from app.progress_tracker import progress_tracker
from app.benchmark_runner import BenchmarkRunner
import config
import json
import time
import threading

bp = Blueprint('main', __name__)

# Initialize Ollama client
ollama = OllamaClient(config.OLLAMA_BASE_URL)

# Global benchmark runner (stores latest results)
benchmark_runner = None


@bp.route('/')
def index():
    """Home page with model and prompt selection"""
    return render_template(
        'index.html',
        prompts=config.BENCHMARK_PROMPTS,
        runs_options=config.RUNS_OPTIONS,
        default_runs=config.DEFAULT_RUNS_PER_TEST
    )


@bp.route('/progress')
def progress():
    """Progress page showing real-time updates"""
    return render_template('progress.html')


@bp.route('/results')
def results():
    """Results page showing benchmark results"""
    return render_template('results.html')


@bp.route('/compare')
def compare():
    """Comparison page for uploading and comparing multiple benchmark results"""
    return render_template('compare.html')


@bp.route('/api/models')
def get_models():
    """API endpoint to get list of models with download status"""
    model_status = ollama.get_model_status(config.AVAILABLE_MODELS)

    return jsonify({
        "models": [
            {
                "name": m.name,
                "downloaded": m.downloaded,
                "size": m.size
            }
            for m in model_status
        ]
    })


@bp.route('/api/status')
def check_status():
    """Check if Ollama is available"""
    available = ollama.is_available()
    return jsonify({
        "ollama_available": available,
        "message": "Ollama is running" if available else "Ollama is not available"
    })


@bp.route('/api/pull', methods=['POST'])
def pull_model():
    """Trigger model pull operation"""
    data = request.get_json()
    model_name = data.get('model')

    if not model_name:
        return jsonify({"error": "Model name required"}), 400

    # Check if already running
    if progress_tracker.is_running():
        return jsonify({"error": "Another operation is already running"}), 409

    # Start pull in background thread
    def pull_worker():
        progress_tracker.start('pull', model_name)

        def progress_callback(status, completed, total):
            # Format bytes nicely
            if total > 0:
                mb_completed = completed / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                message = f"{status}: {mb_completed:.1f} MB / {mb_total:.1f} MB"
            else:
                message = status

            progress_tracker.update(
                message=message,
                completed=completed,
                total=total
            )

        try:
            success = ollama.pull_model(model_name, progress_callback)
            if success:
                progress_tracker.complete(f"Successfully pulled {model_name}")
            else:
                progress_tracker.error(f"Failed to pull {model_name}")
        except Exception as e:
            progress_tracker.error(str(e))

    thread = threading.Thread(target=pull_worker, daemon=True)
    thread.start()

    return jsonify({"message": "Pull started", "model": model_name})


@bp.route('/api/progress')
def progress_stream():
    """SSE endpoint for progress updates"""

    def generate():
        """Generate SSE events"""
        last_state = None

        while True:
            state = progress_tracker.get_state()

            # Only send update if state changed
            if state != last_state:
                if state is None:
                    # No operation running
                    yield f"data: {json.dumps({'status': 'idle'})}\n\n"
                else:
                    yield f"data: {json.dumps(state)}\n\n"

                last_state = state

                # If operation is complete, cancelled, or error, close stream after a delay
                if state and state['status'] in ['complete', 'cancelled', 'error']:
                    time.sleep(2)  # Give client time to process
                    break

            time.sleep(0.5)  # Poll every 500ms

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@bp.route('/api/benchmark', methods=['POST'])
def start_benchmark():
    """Start a benchmark run"""
    global benchmark_runner

    data = request.get_json()
    models = data.get('models', [])
    prompt_ids = data.get('prompts', [])
    runs = data.get('runs', 3)

    # Validate input
    if not models:
        return jsonify({"error": "No models specified"}), 400
    if not prompt_ids:
        return jsonify({"error": "No prompts specified"}), 400

    # Check if already running
    if progress_tracker.is_running():
        return jsonify({"error": "Another operation is already running"}), 409

    # Get full prompt objects from config
    prompts = []
    for prompt_id in prompt_ids:
        prompt_obj = next((p for p in config.BENCHMARK_PROMPTS if p['id'] == prompt_id), None)
        if prompt_obj:
            prompts.append(prompt_obj)

    if not prompts:
        return jsonify({"error": "No valid prompts found"}), 400

    # Start benchmark in background thread
    def benchmark_worker():
        global benchmark_runner

        try:
            # Create new runner
            benchmark_runner = BenchmarkRunner(ollama)

            # Run benchmark
            benchmark_runner.run_benchmark(
                models=models,
                prompts=prompts,
                runs_per_test=runs
            )

        except Exception as e:
            print(f"Benchmark error: {e}")

    thread = threading.Thread(target=benchmark_worker, daemon=True)
    thread.start()

    return jsonify({
        "message": "Benchmark started",
        "models": models,
        "prompts": prompt_ids,
        "runs": runs,
        "total_tests": len(models) * len(prompts) * runs
    })


@bp.route('/api/benchmark/cancel', methods=['POST'])
def cancel_benchmark():
    """Cancel the currently running benchmark"""
    if not progress_tracker.is_running():
        return jsonify({"error": "No benchmark is currently running"}), 400

    # Trigger cancellation
    progress_tracker.cancel()

    return jsonify({"message": "Benchmark cancellation requested"})


@bp.route('/api/results')
def get_results():
    """Get benchmark results"""
    global benchmark_runner

    if benchmark_runner is None:
        return jsonify({"error": "No benchmark has been run yet"}), 404

    results = benchmark_runner.get_results()

    if not results:
        return jsonify({"error": "No results available"}), 404

    return jsonify({
        "system_info": benchmark_runner.system_info,
        "results": results,
        "total_tests": len(results)
    })
