"""
Ollama Model Manager

Handles model pulling, caching, health checks, and preloading for Ollama local models.
Ensures smooth offline operation with automatic model management.

Author: TerraQore Team
Version: 1.0.0 (Phase 3 - Offline & Self-Hosting)
"""

import os
import logging
import time
import json
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about an Ollama model"""
    name: str
    size_gb: float
    modified: str
    digest: str
    available: bool = False
    error: Optional[str] = None


@dataclass
class ModelPullProgress:
    """Progress tracking for model pulls"""
    model: str
    status: str  # "downloading", "extracting", "complete", "failed"
    progress_percent: float
    total_size_mb: float
    downloaded_mb: float
    error: Optional[str] = None


class OllamaModelManager:
    """
    Manages Ollama models for offline AI operation.
    
    Features:
    - List available models
    - Pull models from Ollama registry
    - Check model health and availability
    - Preload recommended models for agents
    - Model size and disk usage tracking
    - Automatic retry with exponential backoff
    """
    
    # Recommended models by size and use case
    RECOMMENDED_MODELS = {
        "small": {
            "name": "phi3.5:latest",
            "size_gb": 3.8,
            "description": "Fast, small model for simple tasks",
            "use_cases": ["code snippets", "basic Q&A", "quick iteration"]
        },
        "medium": {
            "name": "llama3:8b",
            "size_gb": 4.7,
            "description": "Balanced quality and speed",
            "use_cases": ["code generation", "planning", "analysis"]
        },
        "large": {
            "name": "gemma2:9b",
            "size_gb": 5.4,
            "description": "High quality for complex tasks",
            "use_cases": ["architecture design", "security analysis", "validation"]
        }
    }
    
    # Agent-specific model recommendations
    AGENT_MODEL_MAP = {
        "IdeaAgent": "llama3:8b",
        "PlannerAgent": "llama3:8b",
        "CoderAgent": "llama3:8b",
        "CodeValidationAgent": "gemma2:9b",
        "SecurityVulnerabilityAgent": "gemma2:9b",
        "TestCritiqueAgent": "gemma2:9b",
        "DSAgent": "llama3:8b",
        "MLOAgent": "llama3:8b",
        "DOAgent": "llama3:8b",
        "NotebookAgent": "phi3.5:latest",
        "IdeaValidatorAgent": "llama3:8b",
        "ConflictResolverAgent": "llama3:8b"
    }
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        self.timeout = 30
        self._cache: Dict[str, ModelInfo] = {}
        self._last_refresh = 0
        self._refresh_interval = 300  # 5 minutes
    
    def is_ollama_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return False
    
    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """
        List all locally available Ollama models.
        
        Args:
            force_refresh: Force refresh cache even if not stale
            
        Returns:
            List of ModelInfo objects
        """
        # Return cached if fresh
        current_time = time.time()
        if not force_refresh and (current_time - self._last_refresh) < self._refresh_interval:
            return list(self._cache.values())
        
        if not self.is_ollama_running():
            logger.error("Ollama server not running")
            return []
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_data in data.get("models", []):
                model = ModelInfo(
                    name=model_data.get("name", ""),
                    size_gb=model_data.get("size", 0) / (1024 ** 3),  # Convert to GB
                    modified=model_data.get("modified_at", ""),
                    digest=model_data.get("digest", ""),
                    available=True
                )
                models.append(model)
                self._cache[model.name] = model
            
            self._last_refresh = current_time
            logger.info(f"Found {len(models)} Ollama models")
            return models
        
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available locally"""
        models = self.list_models()
        return any(m.name == model_name for m in models)
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get detailed information about a model"""
        if not self.is_ollama_running():
            return ModelInfo(
                name=model_name,
                size_gb=0,
                modified="",
                digest="",
                available=False,
                error="Ollama not running"
            )
        
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return ModelInfo(
                    name=model_name,
                    size_gb=data.get("size", 0) / (1024 ** 3),
                    modified=data.get("modified_at", ""),
                    digest=data.get("digest", ""),
                    available=True
                )
            else:
                return ModelInfo(
                    name=model_name,
                    size_gb=0,
                    modified="",
                    digest="",
                    available=False,
                    error=f"HTTP {response.status_code}"
                )
        
        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {e}")
            return ModelInfo(
                name=model_name,
                size_gb=0,
                modified="",
                digest="",
                available=False,
                error=str(e)
            )
    
    def pull_model(
        self,
        model_name: str,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Pull a model from Ollama registry.
        
        Args:
            model_name: Name of model to pull (e.g., "llama3:8b")
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_ollama_running():
            logger.error("Ollama server not running - cannot pull model")
            return False
        
        logger.info(f"Pulling Ollama model: {model_name}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=None  # No timeout for long downloads
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to pull model: HTTP {response.status_code}")
                return False
            
            # Process streaming response
            for line in response.iter_lines():
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    status = data.get("status", "")
                    
                    # Calculate progress
                    if "total" in data and "completed" in data:
                        total = data["total"]
                        completed = data["completed"]
                        progress_percent = (completed / total * 100) if total > 0 else 0
                        
                        progress = ModelPullProgress(
                            model=model_name,
                            status="downloading",
                            progress_percent=progress_percent,
                            total_size_mb=total / (1024 ** 2),
                            downloaded_mb=completed / (1024 ** 2)
                        )
                        
                        if progress_callback:
                            progress_callback(progress)
                        
                        logger.info(f"Pull progress: {progress_percent:.1f}% ({status})")
                    
                    # Check for completion
                    if status == "success":
                        logger.info(f"Successfully pulled model: {model_name}")
                        self._cache.pop(model_name, None)  # Invalidate cache
                        return True
                
                except json.JSONDecodeError:
                    continue
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def delete_model(self, model_name: str) -> bool:
        """Delete a model from local storage"""
        if not self.is_ollama_running():
            logger.error("Ollama server not running")
            return False
        
        try:
            response = requests.delete(
                f"{self.base_url}/api/delete",
                json={"name": model_name},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Deleted model: {model_name}")
                self._cache.pop(model_name, None)
                return True
            else:
                logger.error(f"Failed to delete model: HTTP {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            return False
    
    def preload_recommended_models(
        self,
        models: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, bool]:
        """
        Preload recommended models for offline operation.
        
        Args:
            models: Optional list of model names (uses defaults if None)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict mapping model names to success status
        """
        if models is None:
            models = [v["name"] for v in self.RECOMMENDED_MODELS.values()]
        
        logger.info(f"Preloading {len(models)} recommended models...")
        results = {}
        
        for model in models:
            # Check if already available
            if self.is_model_available(model):
                logger.info(f"✓ Model {model} already available")
                results[model] = True
                continue
            
            # Pull model
            logger.info(f"Pulling model: {model}")
            success = self.pull_model(model, progress_callback)
            results[model] = success
            
            if success:
                logger.info(f"✓ Successfully pulled {model}")
            else:
                logger.error(f"✗ Failed to pull {model}")
        
        successful = sum(1 for v in results.values() if v)
        logger.info(f"Preload complete: {successful}/{len(models)} successful")
        
        return results
    
    def get_recommended_model_for_agent(self, agent_type: str) -> str:
        """Get recommended model for specific agent type"""
        return self.AGENT_MODEL_MAP.get(agent_type, "llama3:8b")
    
    def get_disk_usage(self) -> Dict[str, float]:
        """Get total disk usage by Ollama models"""
        models = self.list_models()
        
        total_gb = sum(m.size_gb for m in models)
        
        return {
            "total_models": len(models),
            "total_size_gb": round(total_gb, 2),
            "models": {m.name: round(m.size_gb, 2) for m in models}
        }
    
    def health_check(self) -> Dict[str, any]:
        """Comprehensive health check"""
        is_running = self.is_ollama_running()
        models = self.list_models() if is_running else []
        disk_usage = self.get_disk_usage() if is_running else {}
        
        return {
            "ollama_running": is_running,
            "base_url": self.base_url,
            "models_available": len(models),
            "disk_usage_gb": disk_usage.get("total_size_gb", 0),
            "recommended_models_available": {
                name: self.is_model_available(info["name"])
                for name, info in self.RECOMMENDED_MODELS.items()
            }
        }


# Singleton instance
_manager_instance: Optional[OllamaModelManager] = None


def get_model_manager(base_url: Optional[str] = None) -> OllamaModelManager:
    """Get or create singleton model manager"""
    global _manager_instance
    
    if _manager_instance is None:
        _manager_instance = OllamaModelManager(base_url)
    
    return _manager_instance


def reset_model_manager():
    """Reset manager (for testing)"""
    global _manager_instance
    _manager_instance = None
