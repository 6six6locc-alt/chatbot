"""Tests for the chatbot app's error handling and model configuration."""
import inspect

from streamlit_app import classify_api_error


def test_authentication_error():
    """Authentication errors should return the invalid API key message."""
    result = classify_api_error("Authentication failed: invalid API key")
    assert "Invalid API key" in result
    assert "check your OpenAI API key" in result


def test_rate_limit_error():
    """Rate limit errors should return the rate limit message."""
    result = classify_api_error("Rate limit exceeded for requests")
    assert "Rate limit" in result
    assert "wait a moment" in result


def test_generic_error():
    """Generic errors should include the original error message."""
    result = classify_api_error("Connection timeout")
    assert "An error occurred" in result
    assert "Connection timeout" in result


def test_case_insensitive():
    """Error classification should be case insensitive."""
    result = classify_api_error("AUTHENTICATION ERROR")
    assert "Invalid API key" in result


def test_api_key_in_message():
    """Messages containing 'api key' (not just 'authentication') are caught."""
    result = classify_api_error("Incorrect API key provided")
    assert "Invalid API key" in result


def test_model_is_gpt4o_mini():
    """Verify the app uses gpt-4o-mini, not the deprecated gpt-3.5-turbo."""
    import streamlit_app
    source = inspect.getsource(streamlit_app)
    assert "gpt-4o-mini" in source
    assert "gpt-3.5-turbo" not in source