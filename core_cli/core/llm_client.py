"""
TerraQore LLM Client Module
Multi-provider LLM client with automatic offline fallback support.
Supports: over 300+ models through Openrouter and Ollama local models.
"""

import time
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standard response format from LLM providers."""
    content: str
    provider: str
    model: str
    usage: Dict[str, int]
    success: bool = True
    error: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 4096):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion from the LLM.
        
        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            
        Returns:
            LLMResponse object.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API key set, etc.).
        
        Returns:
            True if available, False otherwise.
        """
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self._client = None
        
    def _init_client(self):
        """Lazy initialization of Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
                logger.info(f"Initialized Gemini client with model {self.model}")
            except ImportError:
                logger.error("google-generativeai package not installed. Run: pip install google-generativeai")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                raise
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using Gemini."""
        self._init_client()
        try:
            # Combine system prompt and user prompt
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # Generate content
            response = self._client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                }
            )
            
            # Extract usage info
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }
            
            return LLMResponse(
                content=response.text,
                provider="gemini",
                model=self.model,
                usage=usage,
                success=True
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini generation failed: {error_msg}")
            return LLMResponse(
                content="",
                provider="gemini",
                model=self.model,
                usage={},
                success=False,
                error=error_msg
            )
    
    def is_available(self) -> bool:
        """Check if Gemini is available."""
        if not self.api_key or self.api_key == "":
            return False
        try:
            import google.generativeai
            return True
        except ImportError:
            return False


class GroqProvider(LLMProvider):
    """Groq provider implementation."""
    
    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self._client = None
        
    def _init_client(self):
        """Lazy initialization of Groq client."""
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
                logger.info(f"Initialized Groq client with model {self.model}")
            except ImportError:
                logger.error("groq package not installed. Run: pip install groq")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                raise
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using Groq."""
        self._init_client()
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider="groq",
                model=self.model,
                usage=usage,
                success=True
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Groq generation failed: {error_msg}")
            return LLMResponse(
                content="",
                provider="groq",
                model=self.model,
                usage={},
                success=False,
                error=error_msg
            )
    
    def is_available(self) -> bool:
        """Check if Groq is available."""
        if not self.api_key or self.api_key == "":
            return False
        try:
            from groq import Groq
            return True
        except ImportError:
            return False


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider implementation."""
    
    def __init__(self, api_key: str, model: str = "meta-llama/llama-2-70b-chat", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self._client = None
        
    def _init_client(self):
        """Lazy initialization of OpenRouter client (uses httpx)."""
        if self._client is None:
            try:
                import httpx
                self._httpx = httpx
                logger.info(f"Initialized OpenRouter client with model {self.model}")
            except ImportError:
                logger.error("httpx package not installed. Run: pip install httpx")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter client: {e}")
                raise
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using OpenRouter."""
        self._init_client()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/terraqore-studio/terraqore",
                "X-Title": "TerraQore Studio"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            response = self._httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"Error code: {response.status_code} - {response.text}"
                logger.error(f"OpenRouter generation failed: {error_msg}")
                return LLMResponse(
                    content="",
                    provider="openrouter",
                    model=self.model,
                    usage={},
                    success=False,
                    error=error_msg
                )
            
            result = response.json()
            usage = {
                "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": result.get("usage", {}).get("total_tokens", 0)
            }
            
            return LLMResponse(
                content=result["choices"][0]["message"]["content"],
                provider="openrouter",
                model=self.model,
                usage=usage,
                success=True
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"OpenRouter generation failed: {error_msg}")
            return LLMResponse(
                content="",
                provider="openrouter",
                model=self.model,
                usage={},
                success=False,
                error=error_msg
            )
    
    def is_available(self) -> bool:
        """Check if OpenRouter is available."""
        if not self.api_key or self.api_key == "":
            return False
        try:
            import httpx
            return True
        except ImportError:
            return False


class XAIProvider(LLMProvider):
    """xAI Grok provider implementation."""

    def __init__(self, api_key: str, model: str = "grok-2-mini", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self._client = None
        self._httpx = None

    def _init_client(self):
        """Lazy initialization using httpx for xAI API."""
        if self._client is None:
            try:
                import httpx
                self._httpx = httpx
                self._client = True
                logger.info(f"Initialized xAI Grok client with model {self.model}")
            except ImportError:
                logger.error("httpx package not installed. Run: pip install httpx")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize xAI Grok client: {e}")
                raise

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using xAI Grok API."""
        self._init_client()

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages: List[Dict[str, Any]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            data = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False,
                "top_p": 1,
                "stop": None,
                # Some APIs use max_output_tokens; mirror value if supported
                "max_output_tokens": self.max_tokens,
            }

            url = "https://api.x.ai/v1/chat/completions"
            resp = self._httpx.post(url, headers=headers, json=data, timeout=30)

            if resp.status_code != 200:
                error_msg = f"Error code: {resp.status_code} - {resp.text}"
                logger.error(f"xAI Grok generation failed: {error_msg}")
                # Attempt alternative responses endpoint on non-auth related errors
                if "Incorrect API key" not in resp.text:
                    alt_url = "https://api.x.ai/v1/responses"
                    alt_payload = {
                        "model": self.model,
                        "input": [
                            {"role": "system", "content": system_prompt} if system_prompt else None,
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": self.temperature,
                        "max_output_tokens": self.max_tokens,
                    }
                    alt_payload["input"] = [x for x in alt_payload["input"] if x is not None]
                    try:
                        alt_resp = self._httpx.post(alt_url, headers=headers, json=alt_payload, timeout=30)
                        if alt_resp.status_code == 200:
                            result = alt_resp.json()
                            # Try to extract text from responses format
                            content = ""
                            try:
                                content = result.get("output", [{}])[0].get("content", [{}])[0].get("text", "")
                            except Exception:
                                content = str(result)
                            usage = result.get("usage", {}) if isinstance(result, dict) else {}
                            return LLMResponse(
                                content=content,
                                provider="xai",
                                model=self.model,
                                usage={
                                    "prompt_tokens": usage.get("input_tokens", 0),
                                    "completion_tokens": usage.get("output_tokens", 0),
                                    "total_tokens": usage.get("output_tokens", 0) + usage.get("input_tokens", 0),
                                },
                                success=True,
                            )
                    except Exception:
                        pass
                return LLMResponse(
                    content="",
                    provider="xai",
                    model=self.model,
                    usage={},
                    success=False,
                    error=error_msg,
                )

            result = resp.json()
            # xAI API is OpenAI-compatible; try to read usage if present
            usage = {
                "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": result.get("usage", {}).get("total_tokens", 0),
            }

            content = ""
            try:
                content = result["choices"][0]["message"]["content"]
            except Exception:
                # Fallback for potential non-standard response shapes
                content = result.get("choices", [{}])[0].get("text", "")

            return LLMResponse(
                content=content,
                provider="xai",
                model=self.model,
                usage=usage,
                success=True,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"xAI Grok generation failed: {error_msg}")
            return LLMResponse(
                content="",
                provider="xai",
                model=self.model,
                usage={},
                success=False,
                error=error_msg,
            )

    def is_available(self) -> bool:
        """Check if xAI Grok is available."""
        if not self.api_key or self.api_key == "":
            return False
        try:
            import httpx  # noqa: F401
            return True
        except ImportError:
            return False

class OllamaProvider(LLMProvider):
    """Ollama local model provider implementation."""
    
    def __init__(self, api_key: str, model: str = "llama3.2", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self._client = None
        self.base_url = kwargs.get('base_url', 'http://localhost:11434')
        
    def _init_client(self):
        """Lazy initialization of Ollama client."""
        if self._client is None:
            try:
                import requests
                self._requests = requests
                # Test connection
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info(f"Initialized Ollama client with model {self.model}")
                else:
                    raise Exception("Ollama server not responding")
            except ImportError:
                logger.error("requests package not installed. Run: pip install requests")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Ollama: {e}")
                raise
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using Ollama."""
        self._init_client()
        
        try:
            # Build request
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            # Make request
            response = self._requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=120
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract tokens (Ollama doesn't always provide these)
            usage = {
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
            }
            
            return LLMResponse(
                content=result.get("response", ""),
                provider="ollama",
                model=self.model,
                usage=usage,
                success=True
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ollama generation failed: {error_msg}")
            return LLMResponse(
                content="",
                provider="ollama",
                model=self.model,
                usage={},
                success=False,
                error=error_msg
            )
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class LLMClient:
    """Multi-provider LLM client with automatic fallback."""
    
    def __init__(self, primary_provider: LLMProvider, fallback_provider: Optional[LLMProvider] = None):
        """Initialize LLM client.
        
        Args:
            primary_provider: Primary LLM provider.
            fallback_provider: Optional fallback provider.
        """
        self.primary = primary_provider
        self.fallback = fallback_provider
        self.total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    @property
    def primary_provider(self) -> str:
        """Get primary provider name."""
        return self.primary.model if self.primary else "none"
    
    @property
    def primary_model(self) -> str:
        """Get primary model name."""
        return self.primary.model if self.primary else "none"
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Simple completion method that returns just the text content.
        
        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            
        Returns:
            Generated text content.
        """
        response = self.generate(prompt, system_prompt)
        if response.success:
            return response.content
        raise Exception(response.error or "Generation failed")
        
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> LLMResponse:
        """Generate completion with automatic fallback and exponential backoff.
        
        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            max_retries: Maximum retry attempts per provider.
            retry_delay: Initial delay between retries in seconds (exponentially increases).
            
        Returns:
            LLMResponse object.
        """
        # Validate inputs
        if not prompt or not isinstance(prompt, str):
            logger.error("Invalid prompt: must be non-empty string")
            return LLMResponse(
                content="",
                provider="none",
                model="none",
                usage={},
                success=False,
                error="Invalid prompt"
            )
        
        def _try_provider(provider: Optional[LLMProvider], label: str) -> Optional[LLMResponse]:
            if not provider:
                logger.warning(f"No {label} provider configured")
                return None
            if not provider.is_available():
                logger.warning(f"{label.title()} provider {provider.model} not available")
                return None

            original_temperature = getattr(provider, "temperature", None)
            original_max_tokens = getattr(provider, "max_tokens", None)

            if temperature is not None:
                provider.temperature = temperature
            if max_tokens is not None:
                provider.max_tokens = max_tokens

            try:
                for attempt in range(max_retries):
                    try:
                        logger.info(
                            f"Attempting generation with {provider.model} (attempt {attempt + 1}/{max_retries})"
                        )
                        response = provider.generate(prompt, system_prompt)

                        if response.success:
                            self._update_usage(response.usage)
                            logger.info(
                                f"Successfully generated with {response.provider} "
                                f"({response.usage.get('total_tokens', 0)} tokens)"
                            )
                            return response

                        if attempt < max_retries - 1:
                            backoff_delay = retry_delay * (2 ** attempt)
                            logger.warning(
                                f"Generation failed via {label}: {response.error}. Retrying in {backoff_delay}s..."
                            )
                            time.sleep(backoff_delay)
                    except Exception as e:
                        logger.error(f"{label.title()} provider error: {str(e)}")
                        if attempt < max_retries - 1:
                            backoff_delay = retry_delay * (2 ** attempt)
                            logger.warning(f"Retrying in {backoff_delay}s...")
                            time.sleep(backoff_delay)
            finally:
                if temperature is not None:
                    provider.temperature = original_temperature
                if max_tokens is not None:
                    provider.max_tokens = original_max_tokens

            return None

        # Try primary then fallback
        primary_response = _try_provider(self.primary, "primary")
        if primary_response:
            return primary_response

        fallback_response = _try_provider(self.fallback, "fallback")
        if fallback_response:
            return fallback_response
        
        # All attempts failed
        error_msg = "All LLM providers failed or unavailable"
        logger.error(error_msg)
        return LLMResponse(
            content="",
            provider="none",
            model="none",
            usage={},
            success=False,
            error=error_msg
        )

    def generate_with_retrieval(
        self,
        prompt: str,
        retriever: Optional[object] = None,
        k: int = 3,
        system_prompt: Optional[str] = None,
        prepend_context: bool = True,
    ) -> LLMResponse:
        """Generate using an optional retriever to supply contextual passages.

        The retriever must implement a `search(query, k)` method that returns
        a list of dicts with keys `text` and optional `metadata` (e.g. title).
        """
        augmented_prompt = prompt
        if retriever is not None:
            try:
                results = retriever.search(prompt, k=k)
                if results:
                    context_pieces = []
                    for r in results:
                        title = r.get('metadata', {}).get('title') if isinstance(r.get('metadata', {}), dict) else None
                        header = f"[{title}]" if title else f"[{r.get('doc_id', 'doc')}]"
                        context_pieces.append(f"{header} {r.get('text', '')}")
                    context_text = "\n\n".join(context_pieces)
                    if prepend_context:
                        augmented_prompt = f"{context_text}\n\nUser Query:\n{prompt}"
                    else:
                        augmented_prompt = f"{prompt}\n\nContext:\n{context_text}"
            except Exception as e:
                logger.warning(f"Retriever search failed: {e}")

        return self.generate(augmented_prompt, system_prompt)
    
    def _update_usage(self, usage: Dict[str, int]):
        """Update total usage statistics."""
        for key in self.total_usage:
            self.total_usage[key] += usage.get(key, 0)
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get total usage statistics.
        
        Returns:
            Dictionary with usage stats.
        """
        return self.total_usage.copy()

    def health_check(self, test_prompt: str = "Health check - reply 'pong'", max_retries: int = 1) -> Dict[str, Any]:
        """Perform a lightweight health check for primary and fallback providers.

        Returns a dictionary with status for primary and fallback providers.
        """
        results: Dict[str, Any] = {"primary": {}, "fallback": {}}

        # Check primary
        try:
            primary_available = self.primary.is_available()
            results["primary"]["available"] = primary_available
            if primary_available:
                # Try a single short generation to verify credentials
                try:
                    resp = self.primary.generate(test_prompt)
                    results["primary"]["success"] = bool(resp.success)
                    results["primary"]["message"] = resp.error or ("OK" if resp.success else "Failed")
                except Exception as e:
                    results["primary"]["success"] = False
                    results["primary"]["message"] = str(e)
            else:
                results["primary"]["success"] = False
                results["primary"]["message"] = "Primary provider not configured or required packages missing"
        except Exception as e:
            results["primary"]["available"] = False
            results["primary"]["success"] = False
            results["primary"]["message"] = str(e)

        # Check fallback if present
        if self.fallback:
            try:
                fallback_available = self.fallback.is_available()
                results["fallback"]["available"] = fallback_available
                if fallback_available:
                    try:
                        resp = self.fallback.generate(test_prompt)
                        results["fallback"]["success"] = bool(resp.success)
                        results["fallback"]["message"] = resp.error or ("OK" if resp.success else "Failed")
                    except Exception as e:
                        results["fallback"]["success"] = False
                        results["fallback"]["message"] = str(e)
                else:
                    results["fallback"]["success"] = False
                    results["fallback"]["message"] = "Fallback provider not configured or required packages missing"
            except Exception as e:
                results["fallback"]["available"] = False
                results["fallback"]["success"] = False
                results["fallback"]["message"] = str(e)
        else:
            results["fallback"] = {"available": False, "success": False, "message": "No fallback configured"}

        return results


def create_llm_client_from_config(config) -> LLMClient:
    """Create LLM client from TerraQore configuration.
    
    Args:
        config: TerraQoreConfig object.
        
    Returns:
        Configured LLMClient.
    """
    import os

    # Allow forcing Ollama primary for local testing via env var
    force_ollama = os.getenv('TERRAQORE_FORCE_OLLAMA', '0') == '1'

    # Create primary provider
    primary_config = config.primary_llm
    if force_ollama:
        primary_config = type(primary_config)(
            provider='ollama',
            api_key='',
            model=getattr(primary_config, 'model', 'llama3.2'),
            temperature=getattr(primary_config, 'temperature', 0.7),
            max_tokens=getattr(primary_config, 'max_tokens', 4096)
        )
    if primary_config.provider == "gemini":
        primary = GeminiProvider(
            api_key=primary_config.api_key,
            model=primary_config.model,
            temperature=primary_config.temperature,
            max_tokens=primary_config.max_tokens
        )
    elif primary_config.provider == "groq":
        primary = GroqProvider(
            api_key=primary_config.api_key,
            model=primary_config.model,
            temperature=primary_config.temperature,
            max_tokens=primary_config.max_tokens
        )
    elif primary_config.provider == "xai":
        primary = XAIProvider(
            api_key=primary_config.api_key,
            model=primary_config.model,
            temperature=primary_config.temperature,
            max_tokens=primary_config.max_tokens,
        )
    elif primary_config.provider == "openrouter":
        primary = OpenRouterProvider(
            api_key=primary_config.api_key,
            model=primary_config.model,
            temperature=primary_config.temperature,
            max_tokens=primary_config.max_tokens
        )
    elif primary_config.provider == "ollama":
        primary = OllamaProvider(
            api_key="",  # Ollama doesn't need API key
            model=primary_config.model,
            temperature=primary_config.temperature,
            max_tokens=primary_config.max_tokens
        )
    else:
        raise ValueError(f"Unsupported primary provider: {primary_config.provider}")
    
    # Create fallback provider if configured
    fallback = None
    if config.fallback_llm:
        fallback_config = config.fallback_llm
        if fallback_config.provider == "gemini":
            fallback = GeminiProvider(
                api_key=fallback_config.api_key,
                model=fallback_config.model,
                temperature=fallback_config.temperature,
                max_tokens=fallback_config.max_tokens
            )
        elif fallback_config.provider == "groq":
            fallback = GroqProvider(
                api_key=fallback_config.api_key,
                model=fallback_config.model,
                temperature=fallback_config.temperature,
                max_tokens=fallback_config.max_tokens
            )
        elif fallback_config.provider == "xai":
            fallback = XAIProvider(
                api_key=fallback_config.api_key,
                model=fallback_config.model,
                temperature=fallback_config.temperature,
                max_tokens=fallback_config.max_tokens,
            )
        elif fallback_config.provider == "openrouter":
            fallback = OpenRouterProvider(
                api_key=fallback_config.api_key,
                model=fallback_config.model,
                temperature=fallback_config.temperature,
                max_tokens=fallback_config.max_tokens
            )
        elif fallback_config.provider == "ollama":
            fallback = OllamaProvider(
                api_key="",
                model=fallback_config.model,
                temperature=fallback_config.temperature,
                max_tokens=fallback_config.max_tokens
            )
    
    client = LLMClient(primary, fallback)

    # Attach extra providers map (multi-agent support)
    client.extra_providers = {}
    try:
        # OpenRouter as a useful remote provider
        client.extra_providers['openrouter'] = OpenRouterProvider(api_key=os.getenv('OPENROUTER_API_KEY', ''), model='meta-llama/llama-2-70b-chat')
    except Exception:
        pass
    try:
        client.extra_providers['gemini2'] = GeminiProvider(api_key=os.getenv('GEMINI_API_KEY', ''), model='gemini-2')
    except Exception:
        pass
    try:
        client.extra_providers['gpt4'] = OpenRouterProvider(api_key=os.getenv('OPENROUTER_API_KEY', ''), model='gpt-4.1')
    except Exception:
        pass

    # Run a quick health check and emit helpful logs (wrapped in try-except to avoid startup failures)
    try:
        # Don't fail startup if health check times out - LLM providers may not be available yet
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Health check timed out")
        
        # Set a 5-second timeout for health check
        if hasattr(signal, 'SIGALRM'):  # Unix only
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
        
        try:
            health = client.health_check()
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancel alarm
            
            p = health.get('primary', {})
            f = health.get('fallback', {})

            if not p.get('success'):
                logger.warning(f"Primary LLM health check failed: {p.get('message')}")
            else:
                logger.info(f"Primary LLM healthy: {p.get('message')}")

            if f and not f.get('success'):
                logger.warning(f"Fallback LLM health check failed: {f.get('message')}")
            else:
                logger.info(f"Fallback LLM healthy: {f.get('message')}")
        except (TimeoutError, KeyboardInterrupt) as e:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancel alarm
            logger.warning(f"Health check interrupted or timed out during startup: {type(e).__name__}. Continuing without health verification.")
    except Exception as e:
        logger.warning(f"Could not perform health check during startup: {e}. The LLM client will be available for requests.")

    logger.info(f"Created LLM client with primary: {primary_config.model}, fallback: {fallback.model if fallback else 'None'}")
    return client