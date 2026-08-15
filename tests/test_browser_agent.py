"""
Tests for browser_agent.py — tool definitions, dispatch, and URL normalization.

These tests do NOT launch a real browser. They validate:
- Tool definitions are well-formed
- execute_tool dispatches correctly
- URL normalization in navigate() (mocked)
- VALID_TOOL_NAMES matches BROWSER_TOOLS
- Input validation for empty/missing arguments
- Exception and error resilience across all browser methods
"""

from unittest.mock import MagicMock, patch
import pytest
from browser_agent import BROWSER_TOOLS, VALID_TOOL_NAMES, execute_tool, BrowserAgent


# ── Tool definition tests ────────────────────────────────────────────

def test_all_tools_have_names():
    """Every tool in BROWSER_TOOLS must have a function name."""
    for tool in BROWSER_TOOLS:
        assert "function" in tool
        assert "name" in tool["function"]
        assert tool["function"]["name"]


def test_tool_names_unique():
    """All tool names must be unique."""
    names = [t["function"]["name"] for t in BROWSER_TOOLS]
    assert len(names) == len(set(names))


def test_required_tools_present():
    """The 8 expected browser tools must all be defined."""
    expected = {"navigate", "get_text", "get_links", "click", "type_text",
                "press_key", "screenshot", "scroll"}
    actual = {t["function"]["name"] for t in BROWSER_TOOLS}
    assert expected == actual


def test_valid_tool_names_matches_definitions():
    """VALID_TOOL_NAMES must match the names in BROWSER_TOOLS."""
    names_from_defs = {t["function"]["name"] for t in BROWSER_TOOLS}
    assert VALID_TOOL_NAMES == names_from_defs


def test_tools_have_valid_parameter_schemas():
    """Each tool's parameters must be a valid JSON schema dict."""
    for tool in BROWSER_TOOLS:
        params = tool["function"].get("parameters", {})
        assert isinstance(params, dict)
        assert params.get("type") == "object" or "properties" in params


# ── execute_tool dispatch tests ──────────────────────────────────────

def test_execute_tool_unknown_returns_error():
    """execute_tool should return an error message for unknown tools."""
    agent = MagicMock(spec=BrowserAgent)
    result = execute_tool(agent, "nonexistent_tool", {})
    assert "Unknown tool" in result


def test_execute_tool_navigate():
    """execute_tool should call agent.navigate with the url argument."""
    agent = MagicMock(spec=BrowserAgent)
    agent.navigate.return_value = "Navigated to https://example.com"
    result = execute_tool(agent, "navigate", {"url": "example.com"})
    agent.navigate.assert_called_once_with("example.com")
    assert "Navigated" in result


def test_execute_tool_navigate_missing_url():
    """execute_tool should default to empty string if url is missing."""
    agent = MagicMock(spec=BrowserAgent)
    agent.navigate.return_value = "Navigated"
    execute_tool(agent, "navigate", {})
    agent.navigate.assert_called_once_with("")


def test_execute_tool_get_text_default():
    """execute_tool should use default max_chars=5000 for get_text."""
    agent = MagicMock(spec=BrowserAgent)
    agent.get_text.return_value = "page text"
    execute_tool(agent, "get_text", {})
    agent.get_text.assert_called_once_with(5000)


def test_execute_tool_click():
    """execute_tool should call agent.click with the selector."""
    agent = MagicMock(spec=BrowserAgent)
    agent.click.return_value = "Clicked"
    execute_tool(agent, "click", {"selector": "#button"})
    agent.click.assert_called_once_with("#button")


def test_execute_tool_type_text():
    """execute_tool should call agent.type_text with selector and text."""
    agent = MagicMock(spec=BrowserAgent)
    agent.type_text.return_value = "Typed"
    execute_tool(agent, "type_text", {"selector": "#input", "text": "hello"})
    agent.type_text.assert_called_once_with("#input", "hello")


def test_execute_tool_press_key_default():
    """execute_tool should default to 'Enter' for press_key."""
    agent = MagicMock(spec=BrowserAgent)
    agent.press_key.return_value = "Pressed"
    execute_tool(agent, "press_key", {})
    agent.press_key.assert_called_once_with("Enter")


def test_execute_tool_scroll_default():
    """execute_tool should default to 'down' for scroll."""
    agent = MagicMock(spec=BrowserAgent)
    agent.scroll.return_value = "Scrolled"
    execute_tool(agent, "scroll", {})
    agent.scroll.assert_called_once_with("down")


# ── Input validation tests ───────────────────────────────────────────

def test_navigate_empty_url_returns_error():
    """navigate() should return an error message for empty URL."""
    agent = BrowserAgent(headless=True)
    result = agent.navigate("")
    assert "Error" in result
    assert "no URL" in result


def test_navigate_whitespace_url_returns_error():
    """navigate() should return an error message for whitespace-only URL."""
    agent = BrowserAgent(headless=True)
    result = agent.navigate("   ")
    assert "Error" in result


def test_click_empty_selector_returns_error():
    """click() should return an error message for empty selector."""
    agent = BrowserAgent(headless=True)
    result = agent.click("")
    assert "Error" in result
    assert "no selector" in result


def test_type_text_empty_selector_returns_error():
    """type_text() should return an error message for empty selector."""
    agent = BrowserAgent(headless=True)
    result = agent.type_text("", "hello")
    assert "Error" in result
    assert "no selector" in result


def test_press_key_empty_key_returns_error():
    """press_key() should return an error message for empty key."""
    agent = BrowserAgent(headless=True)
    result = agent.press_key("")
    assert "Error" in result
    assert "no key" in result


def test_press_key_whitespace_key_returns_error():
    """press_key() should return an error message for whitespace key."""
    agent = BrowserAgent(headless=True)
    result = agent.press_key("   ")
    assert "Error" in result
    assert "no key" in result


# ── URL normalization tests ──────────────────────────────────────────

def test_url_normalization_adds_https():
    """navigate() should prepend https:// if the URL lacks a protocol."""
    agent = BrowserAgent(headless=True)
    with patch.object(agent, "_ensure_browser"):
        agent._page = MagicMock()
        agent._page.title.return_value = "Test Page"
        agent.navigate("example.com")
        agent._page.goto.assert_called_once()
        called_url = agent._page.goto.call_args[0][0]
        assert called_url == "https://example.com"


def test_url_normalization_preserves_http():
    """navigate() should not modify a URL that already has http://."""
    agent = BrowserAgent(headless=True)
    with patch.object(agent, "_ensure_browser"):
        agent._page = MagicMock()
        agent._page.title.return_value = "Test Page"
        agent.navigate("http://example.com")
        called_url = agent._page.goto.call_args[0][0]
        assert called_url == "http://example.com"


def test_url_normalization_preserves_https():
    """navigate() should not modify a URL that already has https://."""
    agent = BrowserAgent(headless=True)
    with patch.object(agent, "_ensure_browser"):
        agent._page = MagicMock()
        agent._page.title.return_value = "Test Page"
        agent.navigate("https://example.com")
        called_url = agent._page.goto.call_args[0][0]
        assert called_url == "https://example.com"


# ── Exception / Resilience tests ──────────────────────────────────────

def test_navigate_exception_returns_error_message():
    """navigate() should return error message if page.goto raises."""
    agent = BrowserAgent(headless=True)
    with patch.object(agent, "_ensure_browser"):
        agent._page = MagicMock()
        agent._page.goto.side_effect = Exception("Net connection timeout")
        result = agent.navigate("https://invalid-nonexistent-domain.xyz")
        assert "Failed to navigate" in result
        assert "Net connection timeout" in result


def test_get_text_exception_returns_error_message():
    """get_text() should return error message if page.inner_text raises."""
    agent = BrowserAgent(headless=True)
    with patch.object(agent, "_ensure_browser"):
        agent._page = MagicMock()
        agent._page.inner_text.side_effect = Exception("Target closed")
        result = agent.get_text()
        assert "Failed to get text" in result
        assert "Target closed" in result


def test_get_links_exception_returns_error_message():
    """get_links() should return error message if eval_on_selector_all raises."""
    agent = BrowserAgent(headless=True)
    with patch.object(agent, "_ensure_browser"):
        agent._page = MagicMock()
        agent._page.eval_on_selector_all.side_effect = Exception("Evaluation failed")
        result = agent.get_links()
        assert "Failed to get links" in result
        assert "Evaluation failed" in result


def test_press_key_exception_returns_error_message():
    """press_key() should return error message if keyboard.press raises."""
    agent = BrowserAgent(headless=True)
    with patch.object(agent, "_ensure_browser"):
        agent._page = MagicMock()
        agent._page.keyboard.press.side_effect = Exception("Key press failed")
        result = agent.press_key("Enter")
        assert "Failed to press key" in result
        assert "Key press failed" in result


def test_screenshot_exception_returns_error_message():
    """screenshot() should return error message if page.screenshot raises."""
    agent = BrowserAgent(headless=True)
    with patch.object(agent, "_ensure_browser"):
        agent._page = MagicMock()
        agent._page.screenshot.side_effect = Exception("Screenshot error")
        result = agent.screenshot()
        assert "Failed to take screenshot" in result
        assert "Screenshot error" in result


def test_scroll_exception_returns_error_message():
    """scroll() should return error message if mouse.wheel raises."""
    agent = BrowserAgent(headless=True)
    with patch.object(agent, "_ensure_browser"):
        agent._page = MagicMock()
        agent._page.mouse.wheel.side_effect = Exception("Mouse scroll error")
        result = agent.scroll("down")
        assert "Failed to scroll" in result
        assert "Mouse scroll error" in result


# ── BrowserAgent.close() tests ───────────────────────────────────────

def test_close_safe_when_not_started():
    """close() should not raise if the browser was never started."""
    agent = BrowserAgent(headless=True)
    agent.close()  # should not raise


def test_close_clears_state():
    """close() should clear all internal state."""
    agent = BrowserAgent(headless=True)
    agent._browser = MagicMock()
    agent._playwright = MagicMock()
    agent._page = MagicMock()
    agent.close()
    assert agent._browser is None
    assert agent._playwright is None
    assert agent._page is None
