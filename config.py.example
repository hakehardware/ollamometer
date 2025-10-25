"""
Configuration for Ollamometer benchmarking tool
"""

# Server configuration
PORT = 5555
HOST = "0.0.0.0"  # Bind to all interfaces
DEBUG = True  # Set to False in production

# Ollama API configuration
# Change this to your Ollama server URL (default: local Ollama instance)
OLLAMA_BASE_URL = "http://localhost:11434"

# Models available for testing
# Add or remove models as needed
AVAILABLE_MODELS = [
    "llama3.2:1b",
    "llama3.2:3b",
    "qwen2.5:3b",
    "mistral:7b",
]

# Benchmark prompts with different workload characteristics
# Each prompt tests different aspects of hardware performance
BENCHMARK_PROMPTS = [
    {
        "id": "quick_qa",
        "name": "Quick Q&A",
        "category": "Factual",
        "icon": "[QA]",
        "prompt": "What is recursion in programming? Give a brief explanation.",
        "description": "Tests TTFT and cold start performance",
        "complexity": "short_short"  # prompt_length_response_length
    },
    {
        "id": "code_generation",
        "name": "Code Generation",
        "category": "Coding",
        "icon": "[CODE]",
        "prompt": "Write a Python function that finds the longest palindrome substring in a given string. Include detailed comments explaining the algorithm and handle edge cases.",
        "description": "Tests sustained generation performance",
        "complexity": "short_long"
    },
    {
        "id": "creative_writing",
        "name": "Creative Writing",
        "category": "Creative",
        "icon": "[WRITE]",
        "prompt": "Write a short story (approximately 300 words) about a time traveler who accidentally changes a small detail in history and must deal with the unexpected consequences.",
        "description": "Tests long output generation",
        "complexity": "short_long"
    },
    {
        "id": "reasoning",
        "name": "Multi-Step Reasoning",
        "category": "Analytical",
        "icon": "[MATH]",
        "prompt": "A train leaves Chicago at 3:00 PM traveling east at 60 mph. Another train leaves New York at 4:00 PM traveling west at 80 mph. The cities are 800 miles apart. When and where will the trains meet? Show your work step by step.",
        "description": "Tests computational reasoning",
        "complexity": "short_medium"
    },
    {
        "id": "analysis",
        "name": "Detailed Analysis",
        "category": "Analytical",
        "icon": "[ANALYZE]",
        "prompt": "Compare and contrast the bubble sort and merge sort algorithms. Discuss their time complexity (best, average, worst case), space complexity, stability, and practical use cases. When would you choose one over the other?",
        "description": "Tests analytical processing",
        "complexity": "short_long"
    }
]

# Default number of runs per model/prompt combination
DEFAULT_RUNS_PER_TEST = 3

# Options for runs per test (shown in UI dropdown)
RUNS_OPTIONS = [1, 2, 3, 5, 10]

# System information (manual configuration)
# IMPORTANT: Edit these values to match YOUR machine's hardware specs
# This info appears in benchmark results for hardware comparison
SYSTEM_INFO = {
    "name": "my-pc",  # Name of the machine running Ollama
    "cpu_model": "Intel Core i7-12700K",  # Your CPU model
    "cpu_cores": 12,  # Number of CPU cores
    "cpu_arch": "x86_64",  # Architecture (x86_64, arm64, etc.)
    "ram_gb": 32.0,  # Total system RAM in GB
    "gpu_model": "NVIDIA RTX 4070",  # GPU model or "CPU-only"
    "gpu_vram_gb": 12.0,  # GPU VRAM in GB (0.0 for CPU-only)
    "gpu_driver": "546.33",  # GPU driver version or "N/A"
    "os_name": "Windows",  # Operating system (Windows, Linux, macOS)
    "os_version": "11",  # OS version
}
