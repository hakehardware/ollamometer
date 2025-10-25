#!/usr/bin/env python3
"""
Ollamometer - LLM Hardware Benchmarking Tool

Flask web application for comprehensive hardware performance testing
with multiple LLM models and prompt types.

Usage:
    python3 ollamometer.py

Then visit: http://localhost:5555
"""

import os
import sys

# Check if config.py exists
if not os.path.exists('config.py'):
    print("=" * 60)
    print("ERROR: config.py not found!")
    print("=" * 60)
    print("\nPlease create your configuration file:")
    print("  cp config.py.example config.py")
    print("\nThen edit config.py with your system information.")
    print("=" * 60)
    sys.exit(1)

from flask import Flask
import config


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Register blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app


def main():
    """Main entry point"""
    print("=" * 60)
    print("  Ollamometer - LLM Hardware Benchmark Tool")
    print("=" * 60)
    print(f"\nStarting Flask server on http://localhost:{config.PORT}")
    print(f"Configured models: {len(config.AVAILABLE_MODELS)}")
    print(f"Benchmark prompts: {len(config.BENCHMARK_PROMPTS)}")
    print(f"\nOpen your browser and visit: http://localhost:{config.PORT}")
    print("\nMake sure Ollama is running (ollama serve)")
    print("=" * 60)
    print()

    app = create_app()
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )


if __name__ == "__main__":
    main()
