# 🤖 AI Chatbot with Browser Control

A free AI chatbot that can control a web browser using natural language. Built with Streamlit, OpenAI GPT-4o-mini, and Playwright for browser automation.

## ✨ Features

- 💬 **Chat interface** — talk to the AI in natural language
- 🌐 **Browser control** — the AI can navigate, click, type, and scrape web pages
- 🔓 **Free to run** — uses OpenAI's free-tier API (gpt-4o-mini)
- 📸 **Screenshots** — the AI can take screenshots of what it sees
- 📝 **Session history** — conversation persists during your session

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- An OpenAI API key (get one free at [platform.openai.com](https://platform.openai.com/account/api-keys))

### Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/6six6locc-alt/chatbot.git
   cd chatbot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

4. Run the app:
   ```bash
   streamlit run streamlit_app.py
   ```

5. Enter your OpenAI API key in the sidebar and start chatting!

## 🗣️ Example Commands

- "Go to google.com and search for the weather in Paris"
- "Navigate to wikipedia.org and find the article about artificial intelligence"
- "Open github.com and take a screenshot"
- "Go to news.ycombinator.com and tell me the top 5 stories"

## 🛠️ How It Works

1. You type a message in the chat
2. The AI decides if it needs to use the browser to answer
3. If yes, it uses Playwright to:
   - Navigate to URLs
   - Click elements
   - Type text
   - Extract page content
   - Take screenshots
4. The AI reads the results and responds in the chat

## 📁 Project Structure

```
chatbot/
├── streamlit_app.py      # Main Streamlit app
├── browser_agent.py      # Browser automation logic
├── requirements.txt      # Python dependencies
├── tests/
│   ├── conftest.py       # Test configuration (mocks streamlit & openai)
│   ├── test_error_handling.py    # Error handling and model tests
│   └── test_browser_agent.py     # Browser agent tool tests
└── README.md
```

## 🧪 Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE)