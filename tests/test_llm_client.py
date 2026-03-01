import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.llm.client import LLMClient, LLMConfig, LLMProviderConfig
from src.llm.prompts import PromptManager
import json

@pytest.fixture
def mock_openai_client():
    return AsyncMock()

@pytest.fixture
def llm_config(mock_openai_client):
    primary = LLMProviderConfig(base_url="https://api.openai.com", api_key="primary_key", model_name="gpt-4")
    fallback = LLMProviderConfig(base_url="https://fallback.api.com", api_key="fallback_key", model_name="gpt-3.5-turbo")
    config = LLMConfig(primary=primary, fallback=fallback)
    return config

@pytest.fixture
def llm_client(llm_config):
    client = LLMClient(config=llm_config)
    client.primary_client.chat.completions.create = AsyncMock()
    if client.fallback_client:
        client.fallback_client.chat.completions.create = AsyncMock()
    return client

@pytest.fixture
def prompt_manager():
    manager = PromptManager(template_dir="config/prompts/")
    manager.env.get_template = MagicMock()
    return manager

@pytest.mark.asyncio
async def test_complete(llm_client):
    llm_client.primary_client.chat.completions.create.return_value.choices[0].message.content = "Hello, World!"
    response = await llm_client.complete(prompt="Test prompt")
    assert response == "Hello, World!"

@pytest.mark.asyncio
async def test_complete_json_success(llm_client):
    json_response = {"key": "value"}
    text_response = json.dumps(json_response)
    llm_client.primary_client.chat.completions.create.return_value.choices[0].message.content = text_response
    response = await llm_client.complete_json(prompt="Test prompt")
    assert response == json_response

@pytest.mark.asyncio
async def test_complete_json_retry(llm_client):
    invalid_json = "Invalid JSON"
    valid_json = '{"key": "value"}'
    responses = [invalid_json, valid_json]
    llm_client.primary_client.chat.completions.create.side_effect = [AsyncMock(choices=[MagicMock(message=MagicMock(content=response))]) for response in responses]
    response = await llm_client.complete_json(prompt="Test prompt")
    assert response == json.loads(valid_json)

@pytest.mark.asyncio
async def test_classify(llm_client):
    category_response = "Category1"
    llm_client.primary_client.chat.completions.create.return_value.choices[0].message.content = category_response
    categories = ["Category1", "Category2"]
    response = await llm_client.classify(text="Test text", categories=categories)
    assert response == category_response

@pytest.mark.asyncio
async def test_summarize(llm_client):
    summary_response = "Summary of the text"
    llm_client.primary_client.chat.completions.create.return_value.choices[0].message.content = summary_response
    response = await llm_client.summarize(text="Test text", max_length=100)
    assert len(response) <= 100 and response == summary_response

@pytest.mark.asyncio
async def test_prompt_manager_load_prompt(prompt_manager):
    template_content = "Hello, {{ name }}!"
    prompt_manager.env.get_template.return_value.render.return_value = template_content
    rendered_prompt = prompt_manager.load_prompt("example.j2", name="World")
    assert rendered_prompt == template_content

@pytest.mark.asyncio
async def test_fallback_on_primary_failure(llm_client):
    llm_client.primary_client.chat.completions.create.side_effect = Exception("Primary failure")
    llm_client.fallback_client.chat.completions.create.return_value.choices[0].message.content = "Fallback response"
    response = await llm_client.complete(prompt="Test prompt")
    assert response == "Fallback response"

@pytest.mark.asyncio
async def test_fallback_on_json_parse_failure(llm_client):
    invalid_json = "Invalid JSON"
    valid_json = '{"key": "value"}'
    responses = [invalid_json, valid_json]
    llm_client.primary_client.chat.completions.create.side_effect = [AsyncMock(choices=[MagicMock(message=MagicMock(content=response))]) for response in responses]
    response = await llm_client.complete_json(prompt="Test prompt")
    assert response == json.loads(valid_json)

@pytest.mark.asyncio
async def test_fallback_on_classify_failure(llm_client):
    llm_client.primary_client.chat.completions.create.side_effect = Exception("Primary failure")
    llm_client.fallback_client.chat.completions.create.return_value.choices[0].message.content = "Category1"
    categories = ["Category1", "Category2"]
    response = await llm_client.classify(text="Test text", categories=categories)
    assert response == "Category1"

@pytest.mark.asyncio
async def test_fallback_on_summarize_failure(llm_client):
    llm_client.primary_client.chat.completions.create.side_effect = Exception("Primary failure")
    llm_client.fallback_client.chat.completions.create.return_value.choices[0].message.content = "Summary of the text"
    response = await llm_client.summarize(text="Test text", max_length=100)
    assert len(response) <= 100 and response == "Summary of the text"

@pytest.mark.asyncio
async def test_prompt_manager_missing_template(prompt_manager):
    prompt_manager.env.get_template.side_effect = jinja2.TemplateNotFound("missing.j2")
    with pytest.raises(jinja2.TemplateNotFound):
        prompt_manager.load_prompt("missing.j2", name="World")

@pytest.mark.asyncio
async def test_prompt_manager_jinja_syntax_error(prompt_manager):
    prompt_manager.env.get_template.return_value.render.side_effect = jinja2.TemplateSyntaxError("Syntax error", lineno=1)
    with pytest.raises(jinja2.TemplateSyntaxError):
        prompt_manager.load_prompt("example.j2", name="World")