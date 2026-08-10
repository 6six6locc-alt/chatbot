"""
Browser Agent — Playwright-based browser automation for the chatbot.

This module provides a simple interface for the AI to control a web browser:
navigate, click, type, extract text, and take screenshots.
"""

import asyncio
import base64
import re
from playwright.async_api import async_playwright


class BrowserAgent:
    """Wraps Playwright to provide browser actions the AI can request."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._page = None

    async def _ensure_browser(self):
        """Launch the browser if it hasn't been started yet."""
        if self._page is not None:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()

    async def navigate(self, url: str) -> str:
        """Navigate to a URL and return the page title."""
        await self._ensure_browser()
        if not url.startswith("http"):
            url = "https://" + url
        await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
        title = await self._page.title()
        return f"Navigated to {url}. Page title: {title}"

    async def get_text(self, max_chars: int = 5000) -> str:
        """Extract visible text content from the current page."""
        await self._ensure_browser()
        text = await self._page.inner_text("body")
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... (truncated)"
        return text

    async def get_links(self) -> str:
        """Extract all links from the current page."""
        await self._ensure_browser()
        links = await self._page.eval_on_selector_all(
            "a[href]",
            """els => els.map(e => ({text: e.innerText.trim().substring(0, 80), href: e.href}))"""
        )
        if not links:
            return "No links found on this page."
        lines = []
        for link in links[:20]:
            lines.append(f"- [{link['text']}]({link['href']})")
        return "\n".join(lines)

    async def click(self, selector: str) -> str:
        """Click an element matching the CSS selector."""
        await self._ensure_browser()
        try:
            await self._page.click(selector, timeout=10000)
            return f"Clicked element: {selector}"
        except Exception as e:
            return f"Failed to click '{selector}': {e}"

    async def type_text(self, selector: str, text: str) -> str:
        """Type text into an input element matching the CSS selector."""
        await self._ensure_browser()
        try:
            await self._page.fill(selector, text, timeout=10000)
            return f"Typed '{text}' into {selector}"
        except Exception as e:
            return f"Failed to type into '{selector}': {e}"

    async def press_key(self, key: str) -> str:
        """Press a keyboard key (e.g. 'Enter', 'Tab')."""
        await self._ensure_browser()
        await self._page.keyboard.press(key)
        return f"Pressed key: {key}"

    async def screenshot(self) -> str:
        """Take a screenshot and return it as base64."""
        await self._ensure_browser()
        screenshot_bytes = await self._page.screenshot(full_page=False)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def scroll(self, direction: str = "down") -> str:
        """Scroll the page up or down."""
        await self._ensure_browser()
        if direction == "down":
            await self._page.mouse.wheel(0, 800)
        else:
            await self._page.mouse.wheel(0, -800)
        return f"Scrolled {direction}"

    async def close(self):
        """Close the browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._browser = None
        self._playwright = None


# ── Tool definitions for the AI ──────────────────────────────────────────────

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


async def execute_tool(agent: BrowserAgent, tool_name: str, arguments: dict) -> str:
    """Execute a browser tool by name with the given arguments."""
    if tool_name == "navigate":
        return await agent.navigate(arguments.get("url", ""))
    elif tool_name == "get_text":
        return await agent.get_text(arguments.get("max_chars", 5000))
    elif tool_name == "get_links":
        return await agent.get_links()
    elif tool_name == "click":
        return await agent.click(arguments.get("selector", ""))
    elif tool_name == "type_text":
        return await agent.type_text(arguments.get("selector", ""), arguments.get("text", ""))
    elif tool_name == "press_key":
        return await agent.press_key(arguments.get("key", "Enter"))
    elif tool_name == "screenshot":
        return await agent.screenshot()
    elif tool_name == "scroll":
        return await agent.scroll(arguments.get("direction", "down"))
    else:
        return f"Unknown tool: {tool_name}"