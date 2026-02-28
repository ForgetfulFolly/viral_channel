# Task: Build the LLM abstraction layer with provider support

Priority: 2
Status: queued
Created: 2026-02-28T02:03:00Z
Depends-On: agent/task-20260228020100-fix-conftest-imports
Scope: src/llm/__init__.py, src/llm/client.py, src/llm/prompts.py, config/prompts/, tests/test_llm_client.py

## Description
Implement the LLM abstraction layer as described in SPEC.md Section 8.

Create the following in src/llm/:
- client.py: LLMClient class with methods:
  - async complete(prompt, system_prompt=None, **kwargs) -> str
  - async complete_json(prompt, system_prompt=None, schema=None, **kwargs) -> dict
  - async classify(text, categories, **kwargs) -> str
  - async summarize(text, max_length=200, **kwargs) -> str
- prompts.py: PromptManager class that loads Jinja2 templates from config/prompts/
  - load_prompt(template_name, **variables) -> str

The LLMClient uses the openai AsyncOpenAI SDK with configurable base_url.
This makes it compatible with OpenAI, DeepSeek, vLLM, Ollama, and any
OpenAI-compatible endpoint.

Implement fallback chain: try primary provider, retry on failure up to
max_attempts, then try fallback provider.

Create src/llm/__init__.py that exports LLMClient and PromptManager.

Create config/prompts/ directory with at least one example .j2 template.

## Acceptance Criteria
- [ ] LLMClient initializes from LLMConfig (primary + fallback)
- [ ] complete() sends a chat completion request and returns the text response
- [ ] complete_json() parses the response as JSON, retries if parse fails
- [ ] classify() returns one of the provided categories
- [ ] summarize() returns text under max_length
- [ ] Fallback chain works: primary fails -> retry -> fallback provider
- [ ] PromptManager loads .j2 templates and renders with variables
- [ ] tests/test_llm_client.py mocks the openai client and tests all methods,
      fallback behavior, JSON parsing, retry logic

## Critical Constraints
- Use the openai Python SDK (openai.AsyncOpenAI) -- NOT httpx directly
- base_url and model come from config -- never hardcoded
- All methods are async
- JSON parsing retries up to 3 times with a corrective prompt
- No emojis in any system prompt or output

## Reference Files
- SPEC.md (Section 8)
- src/config.py (LLMConfig, LLMProviderConfig classes for initialization)
