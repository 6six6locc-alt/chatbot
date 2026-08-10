import streamlit as st
from openai import OpenAI


def classify_api_error(error_msg: str) -> str:
    """Classify an OpenAI API error message and return a user-friendly message."""
    msg_lower = error_msg.lower()
    if "authentication" in msg_lower or "api key" in msg_lower:
        return "Invalid API key. Please check your OpenAI API key and try again."
    elif "rate limit" in msg_lower:
        return "Rate limit exceeded. Please wait a moment and try again."
    else:
        return f"An error occurred while contacting the OpenAI API: {error_msg}"


# Show title and description.
st.title("🤖 Chatbot")
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-4o-mini model to generate responses. "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# Ask user for their OpenAI API key via `st.text_input`.
openai_api_key = st.text_input("OpenAI API Key", type="password")

# Add a sidebar with a clear chat button.
with st.sidebar:
    st.header("Settings")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Create a session state variable to store the chat messages.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field.
    if prompt := st.chat_input("What is up?"):
        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate a response with error handling.
        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )

            with st.chat_message("assistant"):
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            st.error(classify_api_error(str(e)))