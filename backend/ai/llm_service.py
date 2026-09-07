import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI, APIError, AuthenticationError, RateLimitError, APIConnectionError

# Configure module logger
logger = logging.getLogger("ai.llm_service")

# Automatically locate and load the backend/.env file
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
dotenv_path = os.path.join(backend_dir, ".env")
load_dotenv(dotenv_path=dotenv_path)

# Default configuration constants
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")


class LLMService:
    """
    Service to interact with OpenRouter LLMs using the OpenAI-compatible SDK.
    Handles authentication, error handling, token tracking, and response formatting.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None
    ):
        # Allow passing key directly, or fall back to environment variable
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL)
        self.default_model = default_model or DEFAULT_MODEL
        self._client: Optional[OpenAI] = None

        if not self.api_key:
            logger.warning(
                "OPENROUTER_API_KEY not found in environment. "
                "Make sure it is set in backend/.env before calling generate_response()."
            )

    @property
    def client(self) -> OpenAI:
        """
        Lazy-initializes and returns the OpenAI client configured for OpenRouter.
        """
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Missing OPENROUTER_API_KEY. Please add your key to backend/.env: "
                    "OPENROUTER_API_KEY=your_key_here"
                )
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers={
                    "HTTP-Referer": "https://github.com/Aabhi-k/Micron",
                    "X-Title": "Micron Codebase AI Assistant"
                }
            )
        return self._client

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Sends a prompt to OpenRouter and returns the text response and token usage.

        Args:
            prompt: The user query or task.
            system_prompt: Optional system instruction (e.g. persona, rules).
            model: OpenRouter model identifier (e.g. 'meta-llama/llama-3.3-70b-instruct:free').
            temperature: Sampling temperature (lower = more focused and deterministic).
            max_tokens: Max completion tokens to generate.

        Returns:
            Dict containing:
            {
                "content": str,
                "token_usage": {
                    "input_tokens": int,
                    "output_tokens": int,
                    "total_tokens": int
                },
                "model": str
            }
        """
        target_model = model or self.default_model
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            logger.info(f"Sending prompt to OpenRouter using model: {target_model}")
            response = self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract generated text
            content = response.choices[0].message.content or ""

            # Extract token usage safely
            usage = response.usage
            token_usage = {
                "input_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                "output_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
                "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0
            }

            return {
                "content": content,
                "token_usage": token_usage,
                "model": target_model
            }

        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise RuntimeError(
                "OpenRouter authentication failed. Please check that your OPENROUTER_API_KEY in backend/.env is valid."
            ) from e

        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise RuntimeError(
                "OpenRouter rate limit reached. Please wait a moment or switch models in backend/.env."
            ) from e

        except APIConnectionError as e:
            logger.error(f"Network connection failed: {e}")
            raise RuntimeError(
                "Could not connect to OpenRouter. Please check your internet connection or proxy settings."
            ) from e

        except APIError as e:
            logger.error(f"OpenRouter API error: {e}")
            raise RuntimeError(f"OpenRouter API error: {e.message}") from e

        except Exception as e:
            logger.error(f"Unexpected error in LLM service: {e}")
            raise


# Default singleton instance for convenient imports
default_llm_service = LLMService()


def get_llm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to quickly query the LLM without creating an instance manually.
    """
    return default_llm_service.generate_response(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model
    )


if __name__ == "__main__":
    # Test script for Phase 1 verification
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    test_prompt = "What is Retrieval-Augmented Generation?"

    print("\n" + "=" * 60)
    print("PHASE 1 VERIFICATION: OpenRouter LLM Service")
    print("=" * 60)
    print(f"Test Question: {test_prompt}\n")

    try:
        service = LLMService()
        result = service.generate_response(prompt=test_prompt)

        print("\n--- LLM Response ---")
        print(result["content"])
        print("\n--- Metadata ---")
        print(f"Model used: {result['model']}")
        print(f"Token usage: {result['token_usage']}")
        print("=" * 60)
        print("PHASE 1 TEST PASSED!")
        print("=" * 60)

    except ValueError as e:
        print(f"\n[CONFIGURATION REQUIRED]: {e}")
        print("Tip: Create backend/.env and set your OPENROUTER_API_KEY.")
    except Exception as e:
        print(f"\n[TEST FAILED]: {e}")
