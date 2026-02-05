"""Tests for certo.llm.provider module."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from certo.llm.provider import (
    DEFAULT_CHECK_MODEL,
    DEFAULT_CHAT_MODEL,
    APIError,
    LLMResponse,
    NoAPIKeyError,
    call_llm,
    get_api_key,
    get_model,
)


def test_get_api_key_missing() -> None:
    """Test that missing API key raises error."""
    with patch.dict(os.environ, {}, clear=True):
        # Ensure OPENROUTER_API_KEY is not set
        os.environ.pop("OPENROUTER_API_KEY", None)
        with pytest.raises(NoAPIKeyError) as exc_info:
            get_api_key()
        assert "OPENROUTER_API_KEY" in str(exc_info.value)


def test_get_api_key_present() -> None:
    """Test that API key is returned when set."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
        assert get_api_key() == "test-key"


def test_get_model_defaults() -> None:
    """Test default model selection."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("CERTO_MODEL", None)
        assert get_model("check") == DEFAULT_CHECK_MODEL
        assert get_model("chat") == DEFAULT_CHAT_MODEL


def test_get_model_env_override() -> None:
    """Test CERTO_MODEL environment variable override."""
    with patch.dict(os.environ, {"CERTO_MODEL": "custom/model"}):
        assert get_model("check") == "custom/model"
        assert get_model("chat") == "custom/model"


def test_call_llm_no_api_key() -> None:
    """Test that call_llm raises error without API key."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("OPENROUTER_API_KEY", None)
        with pytest.raises(NoAPIKeyError):
            call_llm("test prompt")


def test_call_llm_success() -> None:
    """Test successful LLM call."""
    mock_response = {
        "choices": [{"message": {"content": "test response"}}],
        "model": "test-model",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "cost": 0.001,
        },
    }

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_cm = MagicMock()
            mock_cm.__enter__ = MagicMock(return_value=mock_cm)
            mock_cm.__exit__ = MagicMock(return_value=False)
            mock_cm.read.return_value = json.dumps(mock_response).encode()
            mock_urlopen.return_value = mock_cm

            response = call_llm("test prompt", system="system prompt")

            assert isinstance(response, LLMResponse)
            assert response.content == "test response"
            assert response.model == "test-model"
            assert response.prompt_tokens == 10
            assert response.completion_tokens == 5
            assert response.total_tokens == 15
            assert response.cost == 0.001


def test_call_llm_http_error() -> None:
    """Test handling of HTTP errors."""
    import urllib.error
    from email.message import Message

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            error = urllib.error.HTTPError(
                "http://test",
                400,
                "Bad Request",
                Message(),
                None,
            )
            mock_urlopen.side_effect = error

            with pytest.raises(APIError) as exc_info:
                call_llm("test prompt")
            assert "400" in str(exc_info.value)


def test_call_llm_network_error() -> None:
    """Test handling of network errors."""
    import urllib.error

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

            with pytest.raises(APIError) as exc_info:
                call_llm("test prompt")
            assert "network" in str(exc_info.value).lower()


def test_call_llm_json_response() -> None:
    """Test JSON response format request."""
    mock_response = {
        "choices": [{"message": {"content": '{"result": true}'}}],
        "model": "test-model",
        "usage": {},
    }

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_cm = MagicMock()
            mock_cm.__enter__ = MagicMock(return_value=mock_cm)
            mock_cm.__exit__ = MagicMock(return_value=False)
            mock_cm.read.return_value = json.dumps(mock_response).encode()
            mock_urlopen.return_value = mock_cm

            response = call_llm("test", json_response=True)
            assert response.content == '{"result": true}'

            # Check that the request included response_format
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            payload = json.loads(request.data.decode())
            assert payload.get("response_format") == {"type": "json_object"}
