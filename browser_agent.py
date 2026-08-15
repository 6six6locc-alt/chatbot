"""
Browser Agent — Playwright-based browser automation for the chatbot.

This module provides a simple interface for the AI to control a web browser:
navigate, click, type, extract text, and take screenshots.

Uses Playwright's sync API (not async) because Streamlit runs synchronously.
The previous async version used asyncio.run() per tool call, which created a
new event loop each time and destroyed Playwright objects bound to the
previous loop. The sync API avoids this entirely.
"""

import base64
from playwright.sync_api import sync_playwright


class BrowserAgent:
    """Wraps Playwright to provide browser actions the AI can request."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._page = None

    def _ensure_browser(self):
        """Launch the browser if it hasn't been started yet."""
        if self._page is not None:
            return
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._page = self._browser.new_page()

    def navigate(self, url: str) -> str:
        """Navigate to a URL and return the page title."""
        self._ensure_browser()
        if not url or not url.strip():
            return "Error: no URL provided."
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        try:
            self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = self._page.title()
            return f"Navigated to {url}. Page title: {title}"
        except Exception as e:
            return f"Failed to navigate to '{url}': {e}"

    def get_text(self, max_chars: int = 5000) -> str:
        """Extract visible text content from the current page."""
        self._ensure_browser()
        try:
            text = self._page.inner_text("body")
            if len(text) > max_chars:
                text = text[:max_chars] + "\n... (truncated)"
            return text
        except Exception as e:
            return f"Failed to get text: {e}"

    def get_links(self) -> str:
        """Extract all links from the current page."""
        self._ensure_browser()
        try:
            links = self._page.eval_on_selector_all(
                "a[href]",
                """els => els.map(e => ({text: e.innerText.trim().substring(0, 80), href: e.href}))"""
            )
            if not links:
                return "No links found on this page."
            lines = []
            for link in links[:20]:
                lines.append(f"- [{link['text']}]({link['href']})")
            return "\n".join(lines)
        except Exception as e:
            return f"Failed to get links: {e}"

    def click(self, selector: str) -> str:
        """Click an element matching the CSS selector."""
        self._ensure_browser()
        if not selector or not selector.strip():
            return "Error: no selector provided."
        try:
            self._page.wait_for_selector(selector, timeout=10000)
            self._page.click(selector, timeout=10000)
            return f"Clicked element: {selector}"
        except Exception as e:
            return f"Failed to click '{selector}': {e}"

    def type_text(self, selector: str, text: str) -> str:
        """Type text into an input element matching the CSS selector."""
        self._ensure_browser()
        if not selector or not selector.strip():
            return "Error: no selector provided."
        try:
            self._page.wait_for_selector(selector, timeout=10000)
            self._page.fill(selector, text, timeout=10000)
            return f"Typed '{text}' into {selector}"
        except Exception as e:
            return f"Failed to type into '{selector}': {e}"

    def press_key(self, key: str) -> str:
        """Press a keyboard key (e.g. 'Enter', 'Tab', 'Escape')."""
        self._ensure_browser()
        if not key or not key.strip():
            return "Error: no key provided."
        try:
            self._page.keyboard.press(key)
            return f"Pressed key: {key}"
        except Exception as e:
            return f"Failed to press key '{key}': {e}"

    def screenshot(self) -> str:
        """Take a screenshot and return it as base64."""
        self._ensure_browser()
        try:
            screenshot_bytes = self._page.screenshot(full_page=False)
            return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            return f"Failed to take screenshot: {e}"

    def scroll(self, direction: str = "down") -> str:
        """Scroll the page up or down."""
        self._ensure_browser()
        try:
            if direction == "down":
                self._page.mouse.wheel(0, 800)
            else:
                self._page.mouse.wheel(0, -800)
            return f"Scrolled {direction}"
        except Exception as e:
            return f"Failed to scroll: {e}"

    def close(self):
        """Close the browser and release resources. Safe to call multiple times."""
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._browser = None
        self._playwright = None


# ── Tool definitions for the AI ──────────────────────────────────────

BROWSER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": "Navigate the browser to a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to navigate to (e.g. 'google.com')"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_text",
            "description": "Extract visible text content from the current page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_chars": {"type": "integer", "description": "Maximum characters to extract (default 5000)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_links",
            "description": "Extract all links from the current page.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click an element on the page using a CSS selector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for the element to click"}
                },
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text into an input field on the page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for the input element"},
                    "text": {"type": "string", "description": "Text to type into the field"}
                },
                "required": ["selector", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a keyboard key (e.g. 'Enter', 'Tab', 'Escape').",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The key to press"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot",
            "description": "Take a screenshot of the current page.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the page up or down.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down"], "description": "Scroll direction"}
                }
            }
        }
    },
]

def execute_tool(agent: BrowserAgent, tool_name: str, arguments: dict) -> str:
    """Execute a browser tool by name with the given arguments.

    Returns a string result suitable for feeding back to the AI.
    """
    if tool_name == "navigate":
        return agent.navigate(arguments.get("url", ""))
    elif tool_name == "get_text":
        return agent.get_text(arguments.get("max_chars", 5000))
    elif tool_name == "get_links":
        return agent.get_links()
    elif tool_name == "click":
        return agent.click(arguments.get("selector", ""))
    elif tool_name == "type_text":
        return agent.type_text(arguments.get("selector", ""), arguments.get("text", ""))
    elif tool_name == "press_key":
        return agent.press_key(arguments.get("key", "Enter"))
    elif tool_name == "screenshot":
        return agent.screenshot()
    elif tool_name == "scroll":
        return agent.scroll(arguments.get("direction", "down"))
    else:
        return f"Unknown tool: {tool_name}"


# ── Tool name validation ─────────────────────────────────────────────

VALID_TOOL_NAMES = {t["function"]["name"] for t in BROWSER_TOOLS}
