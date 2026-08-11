import json
import time
import streamlit as st
from openai import OpenAI
from browser_agent import BrowserAgent, BROWSER_TOOLS, execute_tool


def classify_api_error(error_msg: str) -> str:
    """Classify an OpenAI API error message and return a user-friendly message."""
    msg_lower = error_msg.lower()
    if "authentication" in msg_lower or "api key" in msg_lower:
        return "Invalid API key. Please check your OpenAI API key and try again."
    elif "rate limit" in msg_lower:
        return "Rate limit exceeded. Please wait a moment and try again."
    else:
        return f"An error occurred while contacting the OpenAI API: {error_msg}"


# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="🤖 Browser Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 Browser Chatbot")
st.write(
    "An AI chatbot that can control a web browser. "
    "Ask it to navigate, search, click, read pages, and more. "
    "Get your free OpenAI API key [here](https://platform.openai.com/account/api-keys)."
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Settings")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    headless = st.checkbox("Headless browser", value=True, help="Run browser without showing a window")
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.session_state.browser_actions = []
        # Close browser if open
        if st.session_state.get("browser_agent"):
            st.session_state.browser_agent.close()
            st.session_state.browser_agent = None
        st.rerun()
    st.markdown("---")
    st.markdown("### 🌐 Browser Actions Log")
    if "browser_actions" not in st.session_state:
        st.session_state.browser_actions = []
    for action in st.session_state.browser_actions:
        st.markdown(f"``{action}``")

# ── Main app ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful AI assistant that can control a web browser.
When the user asks you to do something on the web, use the browser tools to accomplish it.

Available browser tools:
- navigate(url): Go to a URL
- get_text(): Extract visible text from the current page
- get_links(): Get all links on the current page
- click(selector): Click an element by CSS selector
- type_text(selector, text): Type text into an input field
- press_key(key): Press a keyboard key
- screenshot(): Take a screenshot
- scroll(direction): Scroll up or down

Guidelines:
- Always navigate first if the user asks about a specific website
- Use get_text() or get_links() to read page content after navigating
- Be concise in your responses
- If you need to interact with a page (search, click), use the appropriate tools
- After performing browser actions, summarize what you found for the user
"""

if not openai_api_key:
    st.info("Please add your OpenAI API key in the sidebar to continue.", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "browser_actions" not in st.session_state:
        st.session_state.browser_actions = []
    if "browser_agent" not in st.session_state:
        st.session_state.browser_agent = None

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "screenshot" in message:
                st.image(message["screenshot"], caption="Browser screenshot")

    # Chat input
    if prompt := st.chat_input("Ask me to browse the web..."):

        # Store and display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build message list for the API (include system prompt)
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in st.session_state.messages:
            api_messages.append({"role": m["role"], "content": m["content"]})

        # Agent loop: call OpenAI, execute tools, repeat until no more tool calls
        max_iterations = 10
        max_wall_time = 120  # 2-minute timeout for the entire agent loop
        screenshot_data = None
        start_time = time.time()

        try:
            for iteration in range(max_iterations):
                # Wall-clock timeout check
                if time.time() - start_time > max_wall_time:
                    st.warning("Browser agent timed out. Try simplifying your request.")
                    break

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=api_messages,
                    tools=BROWSER_TOOLS,
                    stream=False,
                )

                choice = response.choices[0]
                message = choice.message

                # If the AI wants to call tools
                if message.tool_calls:
                    api_messages.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })

                    # Initialize browser agent if needed
                    if st.session_state.browser_agent is None:
                        st.session_state.browser_agent = BrowserAgent(headless=headless)

                    agent = st.session_state.browser_agent

                    # Execute each tool call (sync API, no asyncio.run)
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            tool_args = {}

                        # Log the action
                        action_str = f"→ {tool_name}({tool_args})"
                        st.session_state.browser_actions.append(action_str)

                        # Execute the tool (sync call, no asyncio)
                        result = execute_tool(agent, tool_name, tool_args)

                        # Handle screenshots specially
                        if tool_name == "screenshot":
                            screenshot_data = result
                            result = "Screenshot taken."

                        # Add tool result to conversation
                        api_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result[:4000]
                        })

                    continue

                # No more tool calls — the AI is ready to respond
                final_response = message.content or "I couldn't generate a response."

                msg_data = {"role": "assistant", "content": final_response}
                if screenshot_data:
                    msg_data["screenshot"] = screenshot_data
                st.session_state.messages.append(msg_data)

                with st.chat_message("assistant"):
                    st.markdown(final_response)
                    if screenshot_data:
                        st.image(screenshot_data, caption="Browser screenshot")
                break

            else:
                st.warning("Reached maximum tool calls. Try simplifying your request.")

        except Exception as e:
            st.error(classify_api_error(str(e)))
            # Clean up browser on error
            if st.session_state.get("browser_agent"):
                st.session_state.browser_agent.close()
                st.session_state.browser_agent = None