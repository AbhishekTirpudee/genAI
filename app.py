
import streamlit as st
import requests

# Page configuration
st.set_page_config(
    page_title="Local Coding Assistant",
    page_icon="💻"
)

# Application heading
st.title("Local AI Coding Assistant")
st.write(
    "An AI assistant that explains, corrects "
    "and optimizes Python code using a local AI model."
)

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen:latest"

# Input section
code = st.text_area(
    "Enter your Python code:",
    height=200,
    placeholder="Paste your Python code here..."
)

# Select operation
operation = st.selectbox(
    "Select an operation:",
    [
        "Explain Code",
        "Correct Code",
        "Optimize Code"
    ]
)

# Function to communicate with Ollama
def get_ai_response(code, operation):

    prompts = {
        "Explain Code":
            "Explain this Python code step by step in simple language.",

        "Correct Code":
                """Carefully analyze the Python code for syntax errors,
    logical errors, and incorrect operations.

    Understand the intended purpose from function names,
    variable names, and code structure.

    Identify every error and explain why it is incorrect.
    Provide the complete corrected Python code.
    Ensure the corrected code has valid Python syntax.
    Do not add unnecessary brackets or change the
    intended functionality.""",

        "Optimize Code":
            "Optimize this Python code for better readability and efficiency. Explain the improvements."
    }

    prompt = prompts[operation] + "\n\nPython code:\n" + code

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    return response.json()["message"]["content"]


# Generate response
if st.button("Generate AI Response"):

    if code.strip():

        try:
            with st.spinner("AI is analyzing your code..."):

                result = get_ai_response(code, operation)

            st.subheader("AI Assistant Response")
            st.markdown(result)

        except requests.exceptions.ConnectionError:
            st.error("Ollama is not running. Please start Ollama.")

        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")

        except Exception as e:
            st.error(f"An error occurred: {e}")

    else:
        st.warning("Please enter Python code first.")
