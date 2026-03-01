## Problem Statement

The application requires an abstraction layer to interact with Large Language Models (LLMs) from multiple providers such as OpenAI, DeepSeek, vLLM, Ollama, and any OpenAI-compatible endpoint. This layer must provide consistent interfaces for common LLM operations like text completion, JSON parsing, classification, and summarization while supporting fallback mechanisms for reliability.

## Functional Requirements

1. **FR-1**: Implement `LLMClient` class with the following methods:
   - `async complete(prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str`: Sends a chat completion request and returns the text response.
   - `async complete_json(prompt: str, system_prompt: Optional[str] = None, schema: Optional[Dict] = None, **kwargs) -> Dict`: Parses the response as JSON, retries on parse failure up to 3 times with a corrective prompt.
   - `async classify(text: str, categories: List[str], **kwargs) -> str`: Returns one of the provided categories based on the text.
   - `async summarize(text: str, max_length: int = 200, **kwargs) -> str`: Summarizes the text with a maximum length constraint.

2. **FR-2**: Implement `PromptManager` class:
   - Loads Jinja2 templates from `config/prompts/`.
   - Renders templates with provided variables using `load_prompt(template_name: str, **variables) -> str`.

3. **FR-3**: Support fallback chain in `LLMClient`:
   - Attempt primary provider up to `max_attempts`.
   - On failure, switch to fallback provider.

4. **FR-4**: Initialize `LLMClient` from `LLMConfig` which includes configurations for primary and fallback providers.

5. **FR-5**: Ensure all methods are asynchronous and compatible with Python 3.11+.

6. **FR-6**: Create example Jinja2 template in `config/prompts/`.

7. **FR-7**: Implement tests in `tests/test_llm_client.py`:
   - Mock OpenAI client to test all methods.
   - Verify fallback behavior, JSON parsing, and retry logic.

## Non-Functional Requirements

1. **NFR-1**: Performance
   - Latency for LLM operations should be under 5 seconds for typical requests.
   - Throughput should support up to 10 concurrent requests without degradation.

2. **NFR-2**: Reliability
   - Fallback mechanism ensures availability when primary provider is down.
   - Retry logic with exponential backoff for transient errors.

3. **NFR-3**: Scalability
   - Design should handle increased load by adjusting concurrency limits or scaling infrastructure.

4. **NFR-4**: Security
   - No hardcoding of API keys or sensitive information.
   - Use environment variables for secrets.

5. **NFR-5**: Maintainability
   - Clean, well-documented code with comprehensive tests.
   - Adherence to PEP 8 standards and type hints.

6. **NFR-6**: Logging
   - Structured logging with correlation IDs for tracing requests.
   - Log levels: DEBUG for detailed information, INFO for normal operation, WARNING for issues, ERROR for failures, CRITICAL for severe problems.

7. **NFR-7**: Monitoring
   - Export metrics for request counts, latencies, errors, and success rates.

## Constraints

1. Use `openai.AsyncOpenAI` SDK exclusively; do not interact with HTTP directly.
2. Base URL and model names must be configurable via `LLMConfig`; no hardcoding.
3. All methods are asynchronous.
4. JSON parsing retries up to 3 times with a corrective prompt on failure.
5. No emojis allowed in system prompts or outputs.

## Success Criteria

- [ ] LLMClient initializes correctly from LLMConfig.
- [ ] complete() method successfully sends and returns chat completions.
- [ ] complete_json() parses responses as JSON, retries on failure.
- [ ] classify() returns one of the provided categories accurately.
- [ ] summarize() produces text under max_length constraint.
- [ ] Fallback chain works: primary provider failures trigger fallback.
- [ ] PromptManager loads and renders Jinja2 templates correctly.
- [ ] Tests in test_llm_client.py pass with mocked OpenAI client.

## Out of Scope

1. Synchronous implementations of LLMClient methods.
2. Support for non-OpenAI-compatible providers (e.g., Anthropic, Hugging Face).
3. Advanced features like rate limiting or quota management.
4. User interface components or configuration tools.
5. Additional template formats beyond Jinja2.

## Open Questions

1. What specific retry conditions should trigger fallback vs. retries on the same provider?
2. How to handle different response formats from various providers while maintaining compatibility with OpenAI SDK?
3. Should additional metrics be collected beyond those specified in NFR-7?