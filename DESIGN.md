## Architecture Overview

```mermaid
graph TD
    LLMClient --> OpenAI: Uses AsyncOpenAI SDK
    LLMClient --> PromptManager: Loads prompts via Jinja2 templates
    LLMConfig --> LLMProviderConfig: Configures primary and fallback providers
    PromptManager --> Templates: Loads from config/prompts/
```

## Components

### 1. LLMClient (src/llm/client.py)
- **Purpose**: Abstracts LLM interactions with support for multiple providers.
- **Dependencies**:
  - `openai.AsyncOpenAI`
  - `LLMConfig` from src/config.py
- **Key Functionality**:
  - Methods: complete(), complete_json(), classify(), summarize()
  - Fallback chain on provider failures

### 2. PromptManager (src/llm/prompts.py)
- **Purpose**: Manages Jinja2 templates for prompt generation.
- **Dependencies**:
  - `jinja2.Environment`
  - Templates from config/prompts/
- **Key Functionality**:
  - Loads and renders templates with variables

### 3. __init__.py (src/llm/__init__.py)
- **Purpose**: Exports LLMClient and PromptManager.
- **Dependencies**:
  - Internal module imports
- **Key Functionality**:
  - Export statements for public API

### 4. Templates (config/prompts/)
- **Purpose**: Stores Jinja2 templates for prompts.
- **Dependencies**:
  - None
- **Key Functionality**:
  - Example template: example_template.j2

### 5. Tests (tests/test_llm_client.py)
- **Purpose**: Unit tests for LLMClient and PromptManager.
- **Dependencies**:
  - pytest
  - Mock OpenAI client
- **Key Functionality**:
  - Test all methods, fallback behavior, JSON parsing

## Interface Definitions

### LLMClient (src/llm/client.py)

```python
from typing import Optional, Dict, List
import openai
from pydantic import BaseModel

class LLMConfig(BaseModel):
    primary: LLMProviderConfig
    fallback: Optional[LLMProviderConfig] = None
    max_attempts: int = 3

class LLMProviderConfig(BaseModel):
    base_url: str
    api_key: str
    model_name: str

class LLMClient:
    def __init__(self, config: LLMConfig) -> None:
        """Initialize with LLM configuration."""
        self.config = config
        # Initialize OpenAI clients for primary and fallback providers
        self.primary_client = openai.AsyncOpenAI(
            base_url=config.primary.base_url,
            api_key=config.primary.api_key
        )
        if config.fallback:
            self.fallback_client = openai.AsyncOpenAI(
                base_url=config.fallback.base_url,
                api_key=config.fallback.api_key
            )

    async def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Send a chat completion request and return the text response."""
        pass

    async def complete_json(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """Parse the response as JSON, retries on failure up to 3 times."""
        pass

    async def classify(self, text: str, categories: List[str], **kwargs) -> str:
        """Return one of the provided categories based on the text."""
        pass

    async def summarize(self, text: str, max_length: int = 200, **kwargs) -> str:
        """Summarize the text with a maximum length constraint."""
        pass
```

### PromptManager (src/llm/prompts.py)

```python
from typing import Optional, Dict
import jinja2

class PromptManager:
    def __init__(self, template_dir: str = "config/prompts/") -> None:
        """Initialize with template directory path."""
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=False
        )

    def load_prompt(self, template_name: str, **variables) -> str:
        """Load and render a Jinja2 template with variables."""
        pass
```

## Data Models

### LLMConfig (src/config.py)

```python
from pydantic import BaseModel
from typing import Optional

class LLMProviderConfig(BaseModel):
    base_url: str
    api_key: str
    model_name: str

class LLMConfig(BaseModel):
    primary: LLMProviderConfig
    fallback: Optional[LLMProviderConfig] = None
    max_attempts: int = 3
```

### LLMClient (src/llm/client.py)

```python
from typing import Optional, Dict, List
import openai

class LLMClient:
    def __init__(self, config: LLMConfig) -> None:
        pass

    async def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        pass

    async def complete_json(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        pass

    async def classify(self, text: str, categories: List[str], **kwargs) -> str:
        pass

    async def summarize(self, text: str, max_length: int = 200, **kwargs) -> str:
        pass
```

### PromptManager (src/llm/prompts.py)

```python
from typing import Optional, Dict

class PromptManager:
    def __init__(self, template_dir: str = "config/prompts/") -> None:
        pass

    def load_prompt(self, template_name: str, **variables) -> str:
        pass
```

## File Changes

| Action | Path | Description |
|--------|------|-------------|
| CREATE | src/llm/client.py | LLMClient implementation with async methods |
| CREATE | src/llm/prompts.py | PromptManager for Jinja2 template management |
| CREATE | src/llm/__init__.py | Export LLMClient and PromptManager |
| CREATE | config/prompts/example_template.j2 | Example Jinja2 template |
| CREATE | tests/test_llm_client.py | Unit tests for LLMClient and PromptManager |

## Test Strategy

### Unit Tests
1. **Test complete() method**:
   - Mock OpenAI client response
   - Verify correct API call parameters
   - Test fallback behavior on primary provider failure

2. **Test complete_json() method**:
   - Mock successful JSON response
   - Test retry logic on parse failure
   - Verify corrective prompt is used

3. **Test classify() method**:
   - Mock classification response
   - Verify categories are properly validated
   - Test fallback behavior

4. **Test summarize() method**:
   - Mock summarization response
   - Verify max_length constraint
   - Test retry logic on API errors

5. **Test PromptManager**:
   - Load and render example template with variables
   - Handle missing templates gracefully
   - Validate Jinja2 syntax errors

### Integration Tests
1. **End-to-end LLM operations**:
   - Use test providers (e.g., mock OpenAI)
   - Verify fallback chain works as expected
   - Test JSON parsing retries

## Implementation Order

1. Create src/llm/client.py with LLMClient implementation
2. Implement src/llm/prompts.py with PromptManager
3. Export classes in src/llm/__init__.py
4. Add example template to config/prompts/
5. Write tests in tests/test_llm_client.py

## Risk Analysis

### Potential Risks
1. **Configuration Errors**:
   - Incorrect base_url or model names
   - Mitigation: Use Pydantic validation and clear error messages

2. **Template Loading Issues**:
   - Missing templates or incorrect paths
   - Mitigation: Comprehensive logging and tests

3. **Fallback Mechanism Failures**:
   - Fallback not triggered when needed
   - Mitigation: Thorough unit testing of fallback logic

4. **JSON Parsing Errors**:
   - Invalid responses from providers
   - Mitigation: Retry with corrective prompt up to 3 times

5. **Asynchronous Code Issues**:
   - Race conditions or incorrect async usage
   - Mitigation: Follow Python asyncio best practices and test concurrency

### Mitigations
- Use type hints consistently
- Implement comprehensive logging
- Write thorough unit tests
- Validate all external inputs
- Follow PEP 8 standards