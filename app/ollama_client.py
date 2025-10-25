"""
Ollama API client for interacting with Ollama server
"""

import requests
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Information about a model"""
    name: str
    downloaded: bool
    size: Optional[int] = None  # Size in bytes if not downloaded


class OllamaClient:
    """Client for interacting with Ollama REST API"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def is_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def list_downloaded_models(self) -> List[str]:
        """
        Get list of models already downloaded

        Returns:
            List of model names (e.g., ['llama3.2:1b', 'qwen2.5:3b'])
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            # Extract model names from response
            models = []
            for model in data.get("models", []):
                name = model.get("name", "")
                if name:
                    models.append(name)

            return models
        except requests.exceptions.RequestException as e:
            print(f"Error listing models: {e}")
            return []

    def get_model_status(self, configured_models: List[str]) -> List[ModelInfo]:
        """
        Get download status for configured models

        Args:
            configured_models: List of model names from config

        Returns:
            List of ModelInfo objects with download status
        """
        downloaded = set(self.list_downloaded_models())

        status_list = []
        for model in configured_models:
            status_list.append(ModelInfo(
                name=model,
                downloaded=model in downloaded,
                size=None  # TODO: Could fetch size from registry if needed
            ))

        return status_list

    def pull_model(self, model: str, progress_callback: Optional[Callable] = None) -> bool:
        """
        Pull/download a model with optional progress tracking

        Args:
            model: Model name to pull
            progress_callback: Optional callback function that receives progress updates
                              callback(status, completed, total)

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": True},
                stream=True
            )
            response.raise_for_status()

            # Process streaming response
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get("status", "")
                    completed = data.get("completed", 0)
                    total = data.get("total", 0)

                    if progress_callback:
                        progress_callback(status, completed, total)

                    # Check if done
                    if status == "success" or data.get("done", False):
                        return True

            return True

        except requests.exceptions.RequestException as e:
            print(f"Error pulling model {model}: {e}")
            return False

    def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Generate text completion

        Args:
            model: Model name
            prompt: Text prompt
            stream: Whether to stream response (not implemented yet)

        Returns:
            API response dictionary with metrics, or None on error
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False  # Always non-streaming for benchmarking
                }
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error generating with model {model}: {e}")
            return None

    def unload_model(self, model: str) -> bool:
        """
        Unload a model from memory

        Args:
            model: Model name to unload

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "keep_alive": 0
                }
            )
            response.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            print(f"Error unloading model {model}: {e}")
            return False

    def get_loaded_models(self) -> List[Dict[str, Any]]:
        """
        Get list of currently loaded models with memory usage

        Returns:
            List of model info dictionaries
        """
        try:
            response = self.session.get(f"{self.base_url}/api/ps")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])

        except requests.exceptions.RequestException as e:
            print(f"Error getting loaded models: {e}")
            return []
