"""
LLM Gateway - Intelligent routing for offline-first LLM access

Provides automatic routing between Ollama (offline) and cloud providers (online)
with model preloading, health checks, and fallback logic.

Author: TerraQore Team
Version: 1.0.0 (Phase 3 - Offline & Self-Hosting)
"""

import os
import logging
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

logger = logging.getLogger(__name__)


class ProviderMode(Enum):
    """LLM Provider operational modes"""
    OFFLINE = "offline"           # Use only local Ollama
    ONLINE = "online"             # Use only OpenRouter (cloud)
    SECURE_FIRST = "secure_first" # Offline for sensitive data, OpenRouter fallback
    AUTO = "auto"                 # Automatic selection based on provider health


class ProviderStatus(Enum):
    """Provider health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealth:
    """Provider health check result"""
    provider: str
    status: ProviderStatus
    latency_ms: float
    last_check: float
    error: Optional[str] = None
    model_available: bool = True


@dataclass
class GatewayConfig:
    """Gateway configuration with security-first routing"""
    mode: ProviderMode = ProviderMode.SECURE_FIRST
    offline_first: bool = True
    health_check_interval: int = 60  # seconds
    request_timeout: int = 30  # seconds
    max_retries: int = 2
    
    # Provider priorities (only Ollama and OpenRouter - Groq via OpenRouter)
    provider_priorities: Dict[str, int] = None
    
    # Model mappings (cloud model -> Ollama equivalent)
    model_mappings: Dict[str, str] = None
    
    # Preload models on startup
    preload_models: List[str] = None
    
    # Security-first routing: Task classification for data sensitivity
    sensitive_tasks: List[str] = None  # Tasks that should NEVER go to cloud
    
    def __post_init__(self):
        if self.provider_priorities is None:
            self.provider_priorities = {
                "ollama": 1,
                "openrouter": 2  # Unified cloud (includes Groq models)
            }
        
        if self.model_mappings is None:
            self.model_mappings = {
                # Consolidated via OpenRouter (remove standalone Groq)
                "openrouter/groq/llama-3.3-70b-versatile": "llama3:8b",
                "openrouter/anthropic/claude-3.5-sonnet": "llama3:8b",
                "openrouter/google/gemini-2.0-pro": "gemma2:9b",
                "gpt-4": "llama3:8b",
                "gpt-3.5-turbo": "phi3.5:latest",
                # Groq models accessed via OpenRouter (no standalone key needed)
                "groq/llama-3.3-70b": "llama3:8b"
            }
        
        if self.preload_models is None:
            self.preload_models = [
                "phi3.5:latest",      # Fast, small (3.8GB)
                "llama3:8b",          # Balanced (4.7GB)
                "gemma2:9b"           # High-quality (5.4GB)
            ]
        
        if self.sensitive_tasks is None:
            self.sensitive_tasks = [
                "security_analysis",      # Never send to cloud
                "code_review_private",    # Private code reviews
                "data_processing",        # Raw data processing
                "compliance_check",       # Compliance/legal tasks
                "internal_documentation" # Internal docs
            ]


class LLMGateway:
    """
    Intelligent LLM gateway with offline-first routing.
    
    Features:
    - Automatic provider health monitoring
    - Offline-first fallback logic
    - Model preloading and caching
    - Request routing based on availability
    - Performance tracking
    """
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self.provider_health: Dict[str, ProviderHealth] = {}
        self.last_health_check: float = 0
        self._initialized = False
        
        logger.info(f"LLM Gateway initialized in {self.config.mode.value} mode")
    
    async def initialize(self):
        """Initialize gateway - check providers, preload models"""
        if self._initialized:
            return
        
        logger.info("Initializing LLM Gateway...")
        
        # Check provider health
        await self.check_all_providers()
        
        # Preload Ollama models if in offline/auto mode
        if self.config.mode in [ProviderMode.OFFLINE, ProviderMode.AUTO]:
            await self.preload_ollama_models()
        
        self._initialized = True
        logger.info("LLM Gateway initialization complete")
    
    async def check_all_providers(self) -> Dict[str, ProviderHealth]:
        """Check health of all configured providers"""
        logger.info("Checking provider health...")
        
        # Check Ollama
        ollama_health = await self.check_ollama_health()
        self.provider_health["ollama"] = ollama_health
        
        # Check OpenRouter
        openrouter_health = await self.check_openrouter_health()
        self.provider_health["openrouter"] = openrouter_health
        
        self.last_health_check = time.time()
        
        # Log status summary
        healthy_count = sum(1 for h in self.provider_health.values() if h.status == ProviderStatus.HEALTHY)
        logger.info(f"Provider health check complete: {healthy_count}/{len(self.provider_health)} healthy")
        
        return self.provider_health
    
    async def check_ollama_health(self) -> ProviderHealth:
        """Check if Ollama is running and responsive"""
        ollama_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{ollama_url}/api/tags",
                timeout=self.config.request_timeout
            )
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                return ProviderHealth(
                    provider="ollama",
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    last_check=time.time(),
                    model_available=len(models) > 0
                )
            else:
                return ProviderHealth(
                    provider="ollama",
                    status=ProviderStatus.DEGRADED,
                    latency_ms=latency,
                    last_check=time.time(),
                    error=f"HTTP {response.status_code}",
                    model_available=False
                )
        
        except (ConnectionError, Timeout) as e:
            return ProviderHealth(
                provider="ollama",
                status=ProviderStatus.UNAVAILABLE,
                latency_ms=-1,
                last_check=time.time(),
                error=f"Connection failed: {str(e)}",
                model_available=False
            )
        
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return ProviderHealth(
                provider="ollama",
                status=ProviderStatus.UNKNOWN,
                latency_ms=-1,
                last_check=time.time(),
                error=str(e),
                model_available=False
            )
    
    async def check_openrouter_health(self) -> ProviderHealth:
        """Check OpenRouter API availability"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return ProviderHealth(
                provider="openrouter",
                status=ProviderStatus.UNAVAILABLE,
                latency_ms=-1,
                last_check=time.time(),
                error="API key not configured",
                model_available=False
            )
        
        start_time = time.time()
        
        try:
            # Simple ping to OpenRouter models endpoint
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=self.config.request_timeout
            )
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ProviderHealth(
                    provider="openrouter",
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    last_check=time.time(),
                    model_available=True
                )
            else:
                return ProviderHealth(
                    provider="openrouter",
                    status=ProviderStatus.DEGRADED,
                    latency_ms=latency,
                    last_check=time.time(),
                    error=f"HTTP {response.status_code}",
                    model_available=False
                )
        
        except Exception as e:
            return ProviderHealth(
                provider="openrouter",
                status=ProviderStatus.UNAVAILABLE,
                latency_ms=-1,
                last_check=time.time(),
                error=str(e),
                model_available=False
            )
    
    
    async def preload_ollama_models(self) -> Dict[str, bool]:
        """Preload recommended Ollama models"""
        logger.info(f"Preloading {len(self.config.preload_models)} Ollama models...")
        results = {}
        
        ollama_health = self.provider_health.get("ollama")
        if not ollama_health or ollama_health.status != ProviderStatus.HEALTHY:
            logger.warning("Ollama not available - skipping model preload")
            return results
        
        ollama_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        
        for model in self.config.preload_models:
            try:
                logger.info(f"Checking model: {model}")
                
                # Check if model already exists
                response = requests.post(
                    f"{ollama_url}/api/show",
                    json={"name": model},
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.info(f"✓ Model {model} already available")
                    results[model] = True
                else:
                    logger.info(f"Model {model} not found - pulling now")
                    results[model] = self._pull_ollama_model(ollama_url, model)
            
            except Exception as e:
                logger.error(f"Error checking model {model}: {e}")
                results[model] = False
        
        return results

    def _pull_ollama_model(self, ollama_url: str, model: str) -> bool:
        """Trigger Ollama to pull a model if missing."""
        try:
            with requests.post(
                f"{ollama_url}/api/pull",
                json={"name": model},
                timeout=900,
                stream=True,
            ) as pull_response:
                if pull_response.status_code == 200:
                    for _ in pull_response.iter_content(chunk_size=8192):
                        pass
                    logger.info(f"✓ Pulled {model} into local cache")
                    return True
                logger.error(f"Failed to pull {model}: HTTP {pull_response.status_code}")
        except RequestException as exc:
            logger.error(f"Error pulling {model}: {exc}")
        except Exception as exc:
            logger.error(f"Unexpected error pulling {model}: {exc}")
        return False
    
    def select_provider(
        self,
        requested_model: str,
        agent_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Select best provider based on health, mode, and model availability.
        
        Returns:
            (provider_name, model_name) tuple
        """
        # Refresh health if stale
        if time.time() - self.last_health_check > self.config.health_check_interval:
            asyncio.create_task(self.check_all_providers())
        
        # OFFLINE mode - force Ollama
        if self.config.mode == ProviderMode.OFFLINE:
            ollama_model = self._map_to_ollama_model(requested_model)
            return ("ollama", ollama_model)
        
        # ONLINE mode - use cloud providers only
        if self.config.mode == ProviderMode.ONLINE:
            return self._select_cloud_provider(requested_model)
        
        # AUTO mode - offline-first with fallback
        if self.config.mode == ProviderMode.AUTO:
            if self.config.offline_first:
                # Try Ollama first
                ollama_health = self.provider_health.get("ollama")
                if ollama_health and ollama_health.status == ProviderStatus.HEALTHY:
                    ollama_model = self._map_to_ollama_model(requested_model)
                    logger.info(f"Using Ollama (offline-first): {ollama_model}")
                    return ("ollama", ollama_model)
                
                # Fallback to cloud
                logger.info("Ollama unavailable - falling back to cloud provider")
                return self._select_cloud_provider(requested_model)
            else:
                # Cloud-first with Ollama fallback
                try:
                    return self._select_cloud_provider(requested_model)
                except Exception:
                    ollama_model = self._map_to_ollama_model(requested_model)
                    logger.info(f"Cloud providers unavailable - using Ollama: {ollama_model}")
                    return ("ollama", ollama_model)
        
        # HYBRID mode - not implemented yet
        raise NotImplementedError("HYBRID mode not yet implemented")
    
    def _map_to_ollama_model(self, requested_model: str) -> str:
        """Map cloud model name to Ollama equivalent"""
        # Direct match in mappings
        if requested_model in self.config.model_mappings:
            return self.config.model_mappings[requested_model]
        
        # Heuristic matching
        model_lower = requested_model.lower()
        
        if "gpt-4" in model_lower or "claude" in model_lower:
            return "llama3:8b"  # Best quality
        elif "gpt-3.5" in model_lower or "gemini" in model_lower:
            return "gemma2:9b"  # Good balance
        elif "llama" in model_lower:
            return "llama3:8b"
        elif "phi" in model_lower:
            return "phi3.5:latest"
        else:
            # Default fallback
            return "phi3.5:latest"
    
    def _select_cloud_provider(self, requested_model: str) -> Tuple[str, str]:
        """Select best available cloud provider"""
        # Sort providers by priority (lower = better)
        sorted_providers = [
            ("openrouter", self.config.provider_priorities.get("openrouter", 999))
        ]
        
        # Try each provider in priority order
        for provider, _ in sorted_providers:
            health = self.provider_health.get(provider)
            if health and health.status == ProviderStatus.HEALTHY:
                logger.info(f"Using cloud provider: {provider}")
                return (provider, requested_model)
        
        # All cloud providers unavailable
        raise Exception("No cloud providers available")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive gateway status"""
        return {
            "mode": self.config.mode.value,
            "offline_first": self.config.offline_first,
            "initialized": self._initialized,
            "last_health_check": self.last_health_check,
            "providers": {
                name: {
                    "status": health.status.value,
                    "latency_ms": health.latency_ms,
                    "model_available": health.model_available,
                    "error": health.error
                }
                for name, health in self.provider_health.items()
            },
            "preload_models": self.config.preload_models
        }


# Singleton instance
_gateway_instance: Optional[LLMGateway] = None


def get_gateway(config: Optional[GatewayConfig] = None) -> LLMGateway:
    """Get or create singleton gateway instance"""
    global _gateway_instance
    
    if _gateway_instance is None:
        _gateway_instance = LLMGateway(config)
    
    return _gateway_instance


def reset_gateway():
    """Reset gateway (for testing)"""
    global _gateway_instance
    _gateway_instance = None
