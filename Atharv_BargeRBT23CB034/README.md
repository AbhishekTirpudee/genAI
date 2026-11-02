# VisionQA — Image-Based Question Answering System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.66%2B-red.svg)](https://streamlit.io/)
[![Google Gen AI](https://img.shields.io/badge/Google%20Gen%20AI-Gemini%20Vision-orange.svg)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

VisionQA is a production-grade, multimodal AI web application that enables users to upload photographs and ask natural-language questions about their visual contents. Powered by the official Google Gen AI Python SDK and Gemini Vision multimodal models, VisionQA maintains conversation context across multiple follow-up questions while ensuring safe in-memory image processing and responsive error handling.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Architecture](#project-architecture)
- [Directory Structure](#directory-structure)
- [Installation Instructions](#installation-instructions)
- [Environment Configuration](#environment-configuration)
- [How to Obtain a Gemini API Key](#how-to-obtain-a-gemini-api-key)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Example Questions](#example-questions)
- [UI Layout & Screenshots](#ui-layout--screenshots)
- [Deployment Instructions](#deployment-instructions)
- [Security & Performance](#security--performance)

---

## Overview

Traditional text-based Q&A systems cannot interpret rich real-world context from images. VisionQA bridges this gap by combining Streamlit's intuitive reactive UI with state-of-the-art multimodal vision models. Users can upload high-resolution images, receive immediate visual confirmation, and converse naturally about objects, scenes, text, charts, diagrams, and equations found inside the image.

---

## Key Features

1. **Multimodal Image Upload:**
   - Supports **JPG**, **JPEG**, **PNG**, and **WEBP** formats up to **10 MB**.
   - Automatic Pillow-based format and integrity verification (corrupted images rejected before processing).
   - EXIF orientation auto-transposition (prevents rotated mobile camera uploads).
   - In-memory processing without writing temporary or permanent image files to disk.
   - Clean PNG/WEBP alpha channel flattening onto white background for uniform RGB ingestion.
   - Intelligent aspect-ratio-preserving downsampling for images exceeding 1600px.

2. **Context-Aware Visual Q&A:**
   - Multi-turn conversation history tracking: ask follow-up questions referencing previous answers.
   - Strict AI system prompt preventing hallucinations and treating in-image instructions as untrusted content.
   - Step-by-step reasoning for mathematical equations and diagram analysis.
   - Accurate optical character reading (OCR) for visible signage, text, and code snippets.

3. **Streamlit Chat Interface:**
   - Clean split-pane layout: Photograph Preview on the left, interactive Chat on the right.
   - Native `st.chat_message` bubbles and `st.chat_input`.
   - Real-time `st.spinner` loading indicator.
   - One-click **New Chat** button to reset both image and conversation.
   - Dedicated **Remove Image** option.

4. **Robust Error Handling:**
   - Clear and friendly warnings for missing API keys, rate limits (HTTP 429), timeouts, and unsupported formats.
   - Strict sanitization: internal stack traces and raw API keys are never exposed in the UI.

5. **Automatic Blur Detection & OCR Enhancement:**
   - Evaluates image sharpness using OpenCV Laplacian variance.
   - If an image is detected as blurry, low-contrast, or degraded, it automatically triggers Tesseract OCR with image enhancement filters (contrast boosting, sharpening, and Otsu binarization).
   - Extracted OCR text is displayed in an expander and passed to the vision AI model as an auxiliary aid to guarantee accurate answers.

6. **Optional SQLite Persistence:**
   - Lightweight built-in SQLite database (`visionqa_history.db`) for tracking past session conversation logs.

---

## Technology Stack

- **Frontend & App Framework:** [Streamlit](https://streamlit.io/)
- **Programming Language:** Python 3.10+ (tested on Python 3.12)
- **AI Providers:**
  - **Google Gemini (Cloud):** Official Google Gen AI SDK (`google-genai` & `google-generativeai`)
  - **Ollama (Local Offline):** Local REST API (`http://localhost:11434`) supporting `llama3.2-vision`, `llava`, `moondream`, `minicpm-v`
- **Multimodal Models:** `gemini-flash-lite-latest`, `gemini-3.1-flash-lite`, `gemini-pro-latest`, `llama3.2-vision`, `llava`
- **Image Processing:** [Pillow (PIL)](https://python-pillow.org/)
- **Configuration & Secrets:** [python-dotenv](https://github.com/theskumar/python-dotenv)
- **Data Persistence:** SQLite3 (standard library)
- **Testing Suite:** [Pytest](https://docs.pytest.org/)

---

## Project Architecture

```
User Browser
    │
    ▼
Streamlit Frontend (app.py)
    │
    ├──> services/image_service.py
    │        ├── Validate file size (<= 10MB)
    │        ├── Verify image integrity (reject corrupt files)
    │        ├── Check allowed formats (JPG, PNG, WEBP)
    │        ├── Transpose EXIF orientation
    │        ├── Handle RGBA transparency (composite over white)
    │        └── Proportional downsampling (max 1600px)
    │
    ├──> Provider 1: services/vision_service.py (Google Gemini Cloud)
    │        ├── Assemble multi-turn conversation context
    │        ├── Inject VisionQA system instructions
    │        ├── Invoke Gemini Multimodal API with retry logic
    │        └── Return structured, error-sanitized response
    │
    ├──> Provider 2: services/ollama_service.py (Local Offline Vision)
    │        ├── Convert image to base64 payload
    │        ├── Detect local installed Ollama models
    │        ├── Send chat request to http://localhost:11434/api/chat
    │        └── Return local vision model answer
    │
    └──> utils/db.py (SQLite Session Log)
```

---

## Directory Structure

```
image_qanda/
│
├── app.py                     # Streamlit web application & page layout
├── verify_model.py            # Diagnostic tool for testing Gemini vision models
│
├── services/
│   ├── __init__.py
│   ├── image_service.py       # Validation, EXIF correction, resizing, alpha handling
│   ├── vision_service.py      # Gemini SDK integration, system prompt, multi-turn chat
│   ├── ollama_service.py      # Ollama local vision integration (llama3.2-vision, llava)
│   └── ocr_service.py         # Laplacian blur detection & Tesseract OCR text extraction
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py             # Conversation ID, input validation, state management
│   └── db.py                  # Optional SQLite persistent session storage
│
├── tests/
│   ├── __init__.py
│   ├── test_image_service.py  # Tests for JPEG, PNG, WEBP, corrupt & oversize rejection
│   ├── test_helpers.py        # Tests for input validation, New Chat reset & persistence
│   ├── test_vision_service.py # Tests for mock Gemini AI responses, error mapping
│   ├── test_ollama_service.py # Tests for base64 encoding & mock Ollama vision calls
│   └── test_ocr_service.py    # Tests for blur detection, image enhancement & OCR
│
├── .env                       # Local secrets (git-ignored)
├── .env.example               # Template for environment configuration
├── .gitignore                 # Excludes bytecode, secrets, and temp databases
├── requirements.txt           # Project dependencies
└── README.md                  # Comprehensive documentation
```

---

## Installation Instructions

### 1. Clone or Open the Repository
```bash
git clone <repository-url>
cd image_qanda
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Environment Configuration

1. Copy `.env.example` to create your local `.env`:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in your Gemini API key:
   ```env
   # Your Google Gemini API Key from Google AI Studio
   GEMINI_API_KEY=AIzaSyYourActualKeyHere

   # Multimodal Gemini model (default: gemini-2.5-flash)
   GEMINI_MODEL=gemini-2.5-flash

   # Maximum conversation history turns sent to Gemini
   MAX_HISTORY_TURNS=10
   ```

> **Note:** You can also enter or override your API key directly inside the **Model & API Settings** expander in the application sidebar.

---

## How to Obtain a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click **Get API key** in the sidebar.
4. Click **Create API key** (create in a new project or select an existing Google Cloud project).
5. Copy your generated key and paste it into `.env` as `GEMINI_API_KEY`.

---

## Running the Application

Launch the Streamlit web application:

```bash
streamlit run app.py
```

The application will launch in your default browser at `http://localhost:8501`.

---

## Running Tests

Execute the automated test suite using `pytest`:

```bash
python -m pytest -v
```

All 23 unit tests run independently without external network calls using mocks and verify:
- Valid JPEG, PNG (with transparency), and WEBP ingestion.
- Rejection of unsupported formats (BMP, GIF, TXT) and corrupted payloads.
- Rejection of oversized images (>10 MB) and empty uploads.
- Proportional resizing and EXIF orientation transposition.
- Missing API key detection and user-friendly error wrapping.
- Multi-turn conversation history preservation.
- New Chat reset logic and SQLite persistence.

---

## Example Questions

Once an image is uploaded, you can ask questions across diverse visual reasoning domains:

### 1. General Object & Scene Description
- *"What objects are visible on the desk?"*
- *"Describe the setting, weather, and lighting in this photo."*

### 2. Contextual Follow-up Questions
- Turn 1: *"What animals do you see?"*
- Turn 2: *"What is the animal on the left doing?"*
- Turn 3: *"What breed might it be?"*

### 3. Optical Character Recognition (OCR)
- *"What text is printed on the coffee mug?"*
- *"Can you transcribe the handwritten note in the upper-right corner?"*

### 4. Technical Diagrams & Screenshots
- *"Explain what algorithm this flowchart is describing."*
- *"Review the code snippet in this screenshot and identify any potential bugs."*

### 5. Mathematical Reasoning
- *"Please solve the math equation written on the whiteboard step by step."*

---

## UI Layout & Screenshots

The application layout features:
- **Left Column:** High-resolution preview of your uploaded photograph with format, dimension, and file size badges, plus a **Remove Image** button.
- **Right Column:** Conversation history rendered with native chat bubbles and a fixed bottom chat input.
- **Sidebar:** New Chat & Clear Chat buttons, live session status indicator, model selector, API key configuration, and past session history.

---

## Deployment Instructions

### Deploying to Streamlit Community Cloud

1. Push your repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io/).
3. Connect your GitHub repository, set `app.py` as the main file.
4. Under **Advanced settings > Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key"
   GEMINI_MODEL = "gemini-2.5-flash"
   ```
5. Click **Deploy**.

### Deploying with Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t visionqa .
docker run -p 8501:8501 -e GEMINI_API_KEY="your_api_key" visionqa
```

---

## Security & Performance

- **Zero Disk Exposure:** All uploads are processed strictly in-memory using `io.BytesIO`.
- **Untrusted Prompt Protection:** The AI system prompt explicitly instructs the model to treat any text appearing inside images as untrusted content, preventing prompt injection via image text.
- **Secrets Isolation:** No API keys are hardcoded in the source code; keys are loaded from environment variables or password inputs.
- **Automatic Downsampling:** High-megapixel camera images are downsampled to a maximum dimension of 1600px, significantly speeding up network transfer and model inference without loss of critical visual fidelity.

---

## License

This project is licensed under the [MIT License](LICENSE).
