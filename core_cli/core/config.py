"""
TerraQore Core Configuration Module
Handles all configuration, API keys, and settings management.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    
    
@dataclass
class TerraQoreConfig:
    """Main TerraQore configuration."""
    primary_llm: LLMConfig
    fallback_llm: Optional[LLMConfig] = None
    project_root: Path = field(default_factory=lambda: Path.cwd())
    data_dir: Path = field(default_factory=lambda: Path.cwd() / "data")
    logs_dir: Path = field(default_factory=lambda: Path.cwd() / "logs")
    max_retries: int = 3
    timeout: int = 30
    debug: bool = False
    

class ConfigManager:
    """Manages TerraQore configuration and settings."""
    
    DEFAULT_CONFIG = {
        "llm": {
            "primary_provider": "gemini",
            "fallback_provider": "groq",
            "gemini": {
                "model": "models/gemini-2.5-flash",
                "temperature": 0.7,
                "max_tokens": 4096
            },
            "groq": {
                "model": "llama-3.1-70b-versatile",
                "temperature": 0.7,
                "max_tokens": 4096
            }
        },
        "system": {
            "max_retries": 3,
            "timeout": 30,
            "debug": False
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        self.config_path = config_path or Path.cwd() / "config" / "settings.yaml"
        self.config_data: Dict[str, Any] = {}
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Ensure required directories exist."""
        dirs = [
            Path.cwd() / "config",
            Path.cwd() / "data",
            Path.cwd() / "logs"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            
    def load(self) -> TerraQoreConfig:
        """Load configuration from file or create default.
        
        Returns:
            TerraQoreConfig object with loaded settings.
        """
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config_data = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_path}")
        else:
            self.config_data = self.DEFAULT_CONFIG.copy()
            self.save()
            logger.info("Created default configuration")
            
        return self._build_config()
    
    def _build_config(self) -> TerraQoreConfig:
        """Build TerraQoreConfig from loaded data with validation."""
        llm_config = self.config_data.get("llm", {})
        system_config = self.config_data.get("system", {})
        
        # Validate LLM config exists
        if not llm_config:
            raise ValueError("Missing 'llm' configuration in settings")
        
        # Get primary provider
        primary_provider = llm_config.get("primary_provider", "gemini")
        if not primary_provider:
            raise ValueError("No primary_provider specified in config")
        
        primary_settings = llm_config.get(primary_provider, {})
        primary_api_key = primary_settings.get("api_key") or os.getenv(f"{primary_provider.upper()}_API_KEY", "")
        
        # Validate primary provider is supported
        supported_providers = ["gemini", "groq", "openrouter", "ollama"]
        if primary_provider not in supported_providers:
            logger.warning(f"Unknown primary provider: {primary_provider}. Expected one of {supported_providers}")
        
        # Validate API key availability for non-local providers
        if primary_provider != "ollama" and not primary_api_key:
            logger.warning(f"No API key found for {primary_provider}. Set {primary_provider.upper()}_API_KEY environment variable")
        
        primary_llm = LLMConfig(
            provider=primary_provider,
            api_key=primary_api_key,
            model=primary_settings.get("model", "gemini-1.5-flash"),
            temperature=min(max(primary_settings.get("temperature", 0.7), 0.0), 2.0),  # Clamp to 0-2
            max_tokens=max(primary_settings.get("max_tokens", 4096), 1)  # At least 1 token
        )
        
        # Get fallback provider if configured
        fallback_llm = None
        fallback_provider = llm_config.get("fallback_provider")
        if fallback_provider:
            if fallback_provider not in supported_providers:
                logger.warning(f"Unknown fallback provider: {fallback_provider}")
            
            fallback_settings = llm_config.get(fallback_provider, {})
            fallback_api_key = fallback_settings.get("api_key") or os.getenv(f"{fallback_provider.upper()}_API_KEY", "")
            
            if fallback_api_key or fallback_provider == "ollama":
                fallback_llm = LLMConfig(
                    provider=fallback_provider,
                    api_key=fallback_api_key,
                    model=fallback_settings.get("model", "llama-3.1-70b-versatile"),
                    temperature=min(max(fallback_settings.get("temperature", 0.7), 0.0), 2.0),
                    max_tokens=max(fallback_settings.get("max_tokens", 4096), 1)
                )
            else:
                logger.warning(f"Fallback provider {fallback_provider} configured but no API key found")
        
        # Validate system config
        max_retries = system_config.get("max_retries", 3)
        if not isinstance(max_retries, int) or max_retries < 1:
            logger.warning(f"Invalid max_retries: {max_retries}, using default 3")
            max_retries = 3
        
        timeout = system_config.get("timeout", 30)
        if not isinstance(timeout, int) or timeout < 1:
            logger.warning(f"Invalid timeout: {timeout}, using default 30")
            timeout = 30
        
        return TerraQoreConfig(
            primary_llm=primary_llm,
            fallback_llm=fallback_llm,
            max_retries=max_retries,
            timeout=timeout,
            debug=system_config.get("debug", False)
        )
    
    def save(self):
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config_data, f, default_flow_style=False)
        logger.info(f"Saved configuration to {self.config_path}")
        
    def update(self, updates: Dict[str, Any]):
        """Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates.
        """
        def deep_update(base: dict, updates: dict):
            for key, value in updates.items():
                if isinstance(value, dict) and key in base:
                    deep_update(base[key], value)
                else:
                    base[key] = value
                    
        deep_update(self.config_data, updates)
        self.save()
        logger.info("Configuration updated")
        
    def get_api_key_instructions(self) -> str:
        """Get instructions for setting up API keys.
        
        Returns:
            Formatted instructions string.
        """
        return """
╔══════════════════════════════════════════════════════════════╗
║                   TerraQore API KEY SETUP                        ║
╚══════════════════════════════════════════════════════════════╝

To use TerraQore, you need to set up API keys as environment variables:

GEMINI (Recommended - Free Tier):
  1. Visit: https://makersuite.google.com/app/apikey
  2. Create a free API key (no credit card required)
  3. Set environment variable:
     Windows (PowerShell): $env:GEMINI_API_KEY="your_key_here"
     Windows (CMD): set GEMINI_API_KEY=your_key_here

GROQ (Optional - Free Fallback):
  1. Visit: https://console.groq.com/
  2. Sign up and get free API key
  3. Set environment variable:
     Windows (PowerShell): $env:GROQ_API_KEY="your_key_here"
     Windows (CMD): set GROQ_API_KEY=your_key_here

To make keys persistent on Windows:
  1. Search for "Environment Variables" in Windows
  2. Click "Environment Variables" button
  3. Add new User variables with your API keys

After setting keys, restart your terminal and run: TerraQore init
"""


# Singleton instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get or create the global configuration manager.
    
    Returns:
        ConfigManager singleton instance.
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager