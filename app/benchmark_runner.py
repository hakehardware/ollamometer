"""
Benchmark runner for executing LLM performance tests
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from app.ollama_client import OllamaClient
from app.progress_tracker import progress_tracker
from app.system_info import get_compute_mode
import config
import time


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""
    model: str
    prompt_id: str
    prompt_text: str
    run_number: int

    # Raw metrics from Ollama API (nanoseconds)
    total_duration_ns: int
    load_duration_ns: int
    prompt_eval_count: int
    prompt_eval_duration_ns: int
    eval_count: int
    eval_duration_ns: int

    # Memory metrics (bytes)
    model_size_bytes: int = 0
    model_size_vram_bytes: int = 0

    # Metadata
    timestamp: str = ""

    @property
    def total_duration_s(self) -> float:
        """Total duration in seconds"""
        return self.total_duration_ns / 1e9

    @property
    def load_duration_s(self) -> float:
        """Load duration in seconds"""
        return self.load_duration_ns / 1e9

    @property
    def prompt_eval_duration_s(self) -> float:
        """Prompt evaluation duration in seconds"""
        return self.prompt_eval_duration_ns / 1e9

    @property
    def eval_duration_s(self) -> float:
        """Evaluation duration in seconds"""
        return self.eval_duration_ns / 1e9

    @property
    def tokens_per_second(self) -> float:
        """Generation speed in tokens per second"""
        if self.eval_duration_ns == 0:
            return 0.0
        return self.eval_count / (self.eval_duration_ns / 1e9)

    @property
    def prompt_tokens_per_second(self) -> float:
        """Prompt processing speed in tokens per second"""
        if self.prompt_eval_duration_ns == 0:
            return 0.0
        return self.prompt_eval_count / (self.prompt_eval_duration_ns / 1e9)

    @property
    def time_to_first_token_s(self) -> float:
        """Time to first token in seconds (load + prompt processing)"""
        return (self.load_duration_ns + self.prompt_eval_duration_ns) / 1e9

    @property
    def model_size_mb(self) -> float:
        """Total model size in MB"""
        return self.model_size_bytes / (1024 * 1024)

    @property
    def model_size_vram_mb(self) -> float:
        """Model VRAM usage in MB"""
        return self.model_size_vram_bytes / (1024 * 1024)

    @property
    def compute_mode(self) -> str:
        """Compute mode: CPU-only, Full GPU, or Hybrid"""
        return get_compute_mode(self.model_size_mb, self.model_size_vram_mb)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with computed properties"""
        data = asdict(self)
        data['total_duration_s'] = self.total_duration_s
        data['load_duration_s'] = self.load_duration_s
        data['prompt_eval_duration_s'] = self.prompt_eval_duration_s
        data['eval_duration_s'] = self.eval_duration_s
        data['tokens_per_second'] = self.tokens_per_second
        data['prompt_tokens_per_second'] = self.prompt_tokens_per_second
        data['time_to_first_token_s'] = self.time_to_first_token_s
        data['model_size_mb'] = self.model_size_mb
        data['model_size_vram_mb'] = self.model_size_vram_mb
        data['compute_mode'] = self.compute_mode
        return data


class BenchmarkRunner:
    """Runs benchmarks and tracks progress"""

    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client
        self.results: List[BenchmarkResult] = []
        self.system_info: Dict[str, Any] = config.SYSTEM_INFO.copy()

    def run_benchmark(
        self,
        models: List[str],
        prompts: List[Dict[str, str]],
        runs_per_test: int = 3
    ) -> List[BenchmarkResult]:
        """
        Run complete benchmark suite

        Args:
            models: List of model names to test
            prompts: List of prompt dictionaries with 'id' and 'prompt' keys
            runs_per_test: Number of runs per model/prompt combination

        Returns:
            List of BenchmarkResult objects
        """
        self.results = []

        # Calculate total tests
        total_tests = len(models) * len(prompts) * runs_per_test
        completed_tests = 0

        # Start tracking
        progress_tracker.start('benchmark', 'Initializing', total=total_tests)

        try:
            # Run benchmarks for each model
            for model_idx, model in enumerate(models):
                # Check for cancellation
                if progress_tracker.is_cancelled():
                    self.results = []  # Clear partial results
                    return self.results

                # Unload model once at the start for clean state
                self.client.unload_model(model)
                time.sleep(1)  # Give it a moment to unload

                # Notify that model will be loading on first inference
                progress_tracker.update(
                    message=f"Preparing {model} - model will load on first test",
                    current_item=model,
                    completed=completed_tests,
                    total=total_tests,
                    metadata={'model': model, 'status': 'preparing'}
                )

                for prompt_idx, prompt_dict in enumerate(prompts):
                    # Check for cancellation
                    if progress_tracker.is_cancelled():
                        self.results = []  # Clear partial results
                        return self.results

                    prompt_id = prompt_dict['id']
                    prompt_text = prompt_dict['prompt']

                    # Run multiple iterations for this model/prompt combination
                    for run_num in range(1, runs_per_test + 1):
                        # Check for cancellation
                        if progress_tracker.is_cancelled():
                            self.results = []  # Clear partial results
                            return self.results

                        # Show loading message on first run of first prompt
                        if prompt_idx == 0 and run_num == 1:
                            progress_tracker.update(
                                message=f"Loading {model} into memory...",
                                current_item=f"{model} (Loading)",
                                completed=completed_tests,
                                total=total_tests,
                                metadata={'model': model, 'status': 'loading'}
                            )

                        # Update progress
                        current_item = f"{model} - {prompt_dict['name']} (Run {run_num}/{runs_per_test})"
                        progress_tracker.update(
                            message=f"Testing: {current_item}",
                            current_item=current_item,
                            completed=completed_tests,
                            total=total_tests,
                            metadata={
                                'prompt_name': prompt_dict['name'],
                                'prompt_text': prompt_text[:200] + ('...' if len(prompt_text) > 200 else ''),
                                'model': model,
                                'run': run_num,
                                'total_runs': runs_per_test
                            }
                        )

                        # Run inference (model will auto-load on first inference)
                        result = self._run_single_test(
                            model=model,
                            prompt_id=prompt_id,
                            prompt_text=prompt_text,
                            run_number=run_num
                        )

                        if result:
                            self.results.append(result)

                        completed_tests += 1

                        # Update progress
                        progress_tracker.update(
                            message=f"Completed: {current_item}",
                            completed=completed_tests,
                            total=total_tests
                        )

                # Unload model after finishing all tests for this model
                self.client.unload_model(model)

            # Mark complete (only if not cancelled)
            if not progress_tracker.is_cancelled():
                progress_tracker.complete(f"Benchmark complete! Ran {completed_tests} tests.")

        except Exception as e:
            progress_tracker.error(f"Benchmark failed: {str(e)}")
            raise

        return self.results

    def _run_single_test(
        self,
        model: str,
        prompt_id: str,
        prompt_text: str,
        run_number: int
    ) -> Optional[BenchmarkResult]:
        """
        Run a single inference test

        Args:
            model: Model name
            prompt_id: Prompt identifier
            prompt_text: Actual prompt text
            run_number: Which run this is (1, 2, 3, etc.)

        Returns:
            BenchmarkResult or None if failed
        """
        try:
            # Run inference
            response = self.client.generate(model, prompt_text)

            # Get memory usage for the loaded model
            model_size = 0
            model_size_vram = 0
            loaded_models = self.client.get_loaded_models()
            for loaded_model in loaded_models:
                # Check if this is our model (handle both "model:tag" and "model" formats)
                model_name = loaded_model.get('name', '')
                if model_name == model or model_name.startswith(model + ':'):
                    model_size = loaded_model.get('size', 0)
                    model_size_vram = loaded_model.get('size_vram', 0)
                    break

            # Extract metrics from response
            result = BenchmarkResult(
                model=model,
                prompt_id=prompt_id,
                prompt_text=prompt_text,
                run_number=run_number,
                total_duration_ns=response.get('total_duration', 0),
                load_duration_ns=response.get('load_duration', 0),
                prompt_eval_count=response.get('prompt_eval_count', 0),
                prompt_eval_duration_ns=response.get('prompt_eval_duration', 0),
                eval_count=response.get('eval_count', 0),
                eval_duration_ns=response.get('eval_duration', 0),
                model_size_bytes=model_size,
                model_size_vram_bytes=model_size_vram,
                timestamp=datetime.now().isoformat()
            )

            return result

        except Exception as e:
            print(f"Error running test for {model} with {prompt_id}: {e}")
            return None

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all results as list of dictionaries"""
        return [result.to_dict() for result in self.results]

    def clear_results(self) -> None:
        """Clear stored results"""
        self.results = []
