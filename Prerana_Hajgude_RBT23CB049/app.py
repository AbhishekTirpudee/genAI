"""
app.py - Streamlit Chat UI for AI Technical Support System.
Features:
- Sidebar to upload PDF manuals and re-index ChromaDB.
- Router Agent to filter non-hardware queries.
- Troubleshooting Agent to diagnose hardware issues with citations.
- Collapsible 'Sources' expander under each answer displaying file name, page number, and chunk content.
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv

# Ensure stdout handles UTF-8 on Windows
if sys.platform.startswith("win"):
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Load environment variables
load_dotenv()

from ingest import ingest_manuals, DEFAULT_MANUALS_DIR, DEFAULT_CHROMA_DIR, DEFAULT_COLLECTION_NAME
from retriever import get_relevant_chunks
from agents import RouterAgent, TroubleshootingAgent, get_api_key
import chromadb

# Page setup
st.set_page_config(
    page_title="AI Technical Support System",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .source-box {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 10px 14px;
        margin-bottom: 10px;
        border-radius: 4px;
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def get_current_chunk_count(chroma_dir: str = DEFAULT_CHROMA_DIR) -> int:
    """Returns number of chunks in the collection."""
    try:
        client = chromadb.PersistentClient(path=chroma_dir)
        collection = client.get_collection(DEFAULT_COLLECTION_NAME)
        return collection.count()
    except Exception:
        return 0


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ Support System Settings")
    st.caption("AI-powered hardware diagnostic agent grounded in verified PDF technical manuals.")
    
    # 1. API Key Configuration
    st.markdown("### 🔑 Gemini API Configuration")
    env_api_key = os.getenv("GEMINI_API_KEY", "")
    
    if "api_key" not in st.session_state:
        st.session_state.api_key = env_api_key

    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Reads from .env by default. You can enter or override your key here.",
        placeholder="Enter your GEMINI_API_KEY..."
    )
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input

    active_key = get_api_key(st.session_state.api_key)
    if active_key:
        st.success("✅ Gemini API Key Active", icon="🟢")
    else:
        st.info("ℹ️ Running in **Offline Demo Mode** (API key not detected). Add `GEMINI_API_KEY` to `.env` or paste it above to activate live Gemini models.", icon="⚡")

    st.divider()

    # 2. Manual Upload & Knowledge Base
    st.markdown("### 📂 Upload Hardware Manuals")
    uploaded_files = st.file_uploader(
        "Upload Technical Manuals (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload hardware maintenance manuals, service guides, or spec sheets."
    )

    if uploaded_files:
        os.makedirs(DEFAULT_MANUALS_DIR, exist_ok=True)
        new_files = 0
        for uploaded_file in uploaded_files:
            file_path = os.path.join(DEFAULT_MANUALS_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            new_files += 1

        st.success(f"Saved {new_files} manual(s) to `/manuals`!")
        if st.button("📥 Index Uploaded Manuals Now", type="primary"):
            with st.spinner("Chunking into 800 tokens and embedding into ChromaDB..."):
                res = ingest_manuals(manuals_dir=DEFAULT_MANUALS_DIR, chroma_dir=DEFAULT_CHROMA_DIR)
                st.success(f"Indexed {res['chunk_count']} chunks from {res['pdf_count']} manual(s)!")
                st.rerun()

    # Ingest / Re-index button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Re-index", use_container_width=True):
            with st.spinner("Re-indexing manuals..."):
                res = ingest_manuals(manuals_dir=DEFAULT_MANUALS_DIR, chroma_dir=DEFAULT_CHROMA_DIR)
                st.success(f"Updated: {res['chunk_count']} chunks.")
                st.rerun()

    with col2:
        if st.button("🗑️ Clear DB", use_container_width=True):
            try:
                client = chromadb.PersistentClient(path=DEFAULT_CHROMA_DIR)
                client.delete_collection(DEFAULT_COLLECTION_NAME)
                st.warning("Database cleared.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # Display database status
    chunk_count = get_current_chunk_count()
    manual_files = [
        f for f in os.listdir(DEFAULT_MANUALS_DIR)
        if f.lower().endswith(".pdf")
    ] if os.path.exists(DEFAULT_MANUALS_DIR) else []

    st.markdown("### 📊 Knowledge Base Status")
    st.markdown(f"- **PDF Manuals:** `{len(manual_files)}`")
    st.markdown(f"- **Indexed 800-token Chunks:** `{chunk_count}`")
    if manual_files:
        with st.expander("View Available Manuals", expanded=False):
            for m in manual_files:
                st.text(f"• {m}")

    st.divider()
    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# --- MAIN CHAT INTERFACE ---
st.markdown('<div class="main-header">🛠️ AI Technical Support System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Hardware Diagnostics & Troubleshooting Assistant powered by Gemini API, '
    'Router & Troubleshooting Agents, and ChromaDB Manual Retrieval.</div>',
    unsafe_allow_html=True
)

# Suggested prompt buttons
st.markdown("**💡 Sample Questions:**")
sample_cols = st.columns([1.8, 1.6, 1.6, 1.8])
clicked_prompt = None

with sample_cols[0]:
    if st.button("🔇 My laptop fan is very loud", use_container_width=True):
        clicked_prompt = "My laptop fan is very loud"
with sample_cols[1]:
    if st.button("🔋 Battery draining quickly", use_container_width=True):
        clicked_prompt = "The battery discharges abnormally fast and notebook fails to hold charge"
with sample_cols[2]:
    if st.button("💾 How do I upgrade RAM?", use_container_width=True):
        clicked_prompt = "What is the procedure to upgrade or replace the RAM memory?"
with sample_cols[3]:
    if st.button("🚫 Write a poem about cars", use_container_width=True):
        clicked_prompt = "Write a poem about fast racing cars"

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I am your **AI Technical Support Specialist**. "
                "I can diagnose hardware faults, loud fans, overheating, battery issues, and component replacement procedures "
                "strictly using your verified technical manuals.\n\n"
                "How can I assist your hardware troubleshooting today?"
            ),
            "sources": None
        }
    ]

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display Sources expander under assistant answer if sources exist
        if msg.get("sources"):
            with st.expander(f"📚 Sources ({len(msg['sources'])} manual chunks cited)", expanded=False):
                for idx, src in enumerate(msg["sources"], 1):
                    st.markdown(
                        f"**Source {idx}:** `{src.get('file_name', 'Unknown')}` — "
                        f"**Page {src.get('page_number', 'Unknown')}** "
                        f"*(Relevance Distance: {src.get('distance', 0.0):.4f})*"
                    )
                    st.info(src.get("text", ""))
                    st.divider()


# Handle User Input
user_input = st.chat_input("Ask a hardware troubleshooting question (e.g., 'My laptop fan is very loud')...")
prompt_to_process = clicked_prompt or user_input

if prompt_to_process:
    # 1. Append User Message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt_to_process,
        "sources": None
    })
    
    with st.chat_message("user"):
        st.markdown(prompt_to_process)

    # 2. Process with Agents
    with st.chat_message("assistant"):
        with st.spinner("Routing request and consulting hardware manuals..."):
            api_key = get_api_key(st.session_state.api_key)
            router = RouterAgent(api_key=api_key)
            is_hardware, refusal = router.route(prompt_to_process, custom_key=api_key)

            if not is_hardware:
                # Non-hardware refusal
                response_text = refusal or (
                    "I specialize exclusively in hardware technical support and equipment diagnostics. "
                    "Your question does not appear to be hardware-related. "
                    "Please ask a question regarding your device's hardware, components, or cooling system."
                )
                sources = None
                st.warning(response_text)
            else:
                # Hardware question: Retrieve top 4 chunks
                chunks = get_relevant_chunks(
                    query=prompt_to_process,
                    n_results=4,
                    chroma_dir=DEFAULT_CHROMA_DIR
                )

                # Run Troubleshooting Agent
                troubleshooter = TroubleshootingAgent(api_key=api_key)
                response_text = troubleshooter.troubleshoot(
                    user_query=prompt_to_process,
                    retrieved_chunks=chunks,
                    custom_key=api_key
                )
                sources = chunks

                st.markdown(response_text)

                # Render Sources expander under the answer
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)} manual chunks cited)", expanded=False):
                        for idx, src in enumerate(sources, 1):
                            st.markdown(
                                f"**Source {idx}:** `{src.get('file_name', 'Unknown')}` — "
                                f"**Page {src.get('page_number', 'Unknown')}** "
                                f"*(Relevance Distance: {src.get('distance', 0.0):.4f})*"
                            )
                            st.info(src.get("text", ""))
                            st.divider()

        # Save to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "sources": sources
        })

