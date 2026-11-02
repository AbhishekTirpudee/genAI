
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import psutil
import time
import threading
from datetime import datetime

# PAGE CONFIGURATION
st.set_page_config(
    page_title="GenAI Performance Monitor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 GenAI Model Performance Monitor")
st.write("Monitor Llama 3.2 1B performance across multiple queries.")

OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.2:1b"


# MEMORY MONITOR
class MemoryMonitor:

    def __init__(self):
        self.peak = 0
        self.running = False

    def get_memory(self):
        total = 0

        for p in psutil.process_iter(["name", "memory_info"]):
            try:
                name = (p.info["name"] or "").lower()

                if "ollama" in name:
                    mem = p.info["memory_info"]
                    if mem:
                        total += mem.rss

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return total / (1024 * 1024)

    def monitor(self):
        while self.running:
            current = self.get_memory()
            self.peak = max(self.peak, current)
            time.sleep(0.05)

    def start(self):
        self.peak = self.get_memory()
        self.running = True

        self.thread = threading.Thread(
            target=self.monitor,
            daemon=True
        )
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join(timeout=2)

        self.peak = max(self.peak, self.get_memory())
        return round(self.peak, 2)


# CHECK OLLAMA CONNECTION
def check_connection():
    response = requests.get(
        OLLAMA_URL + "/api/tags",
        timeout=5
    )
    response.raise_for_status()

    models = response.json().get("models", [])
    return [m["name"] for m in models]


# PERFORMANCE MONITORING
def run_test(prompt, max_tokens):

    memory = MemoryMonitor()
    memory.start()

    start = time.perf_counter()

    try:
        response = requests.post(
            OLLAMA_URL + "/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7
                }
            },
            timeout=600
        )

        response.raise_for_status()
        result = response.json()

        end = time.perf_counter()

    finally:
        peak_memory = memory.stop()

    generated_text = result.get("response", "")

    prompt_tokens = result.get("prompt_eval_count", 0)
    generated_tokens = result.get("eval_count", 0)

    inference_time = (
        result.get("total_duration", 0) / 1_000_000_000
    )

    generation_time = (
        result.get("eval_duration", 0) / 1_000_000_000
    )

    request_time = end - start

    tps = (
        generated_tokens / generation_time
        if generation_time > 0 else 0
    )

    return {
        "Prompt": prompt,
        "Response": generated_text,
        "Prompt Length": prompt_tokens,
        "Generated Tokens": generated_tokens,
        "Inference Time (s)": round(inference_time, 3),
        "Request Time (s)": round(request_time, 3),
        "Tokens Per Second": round(tps, 2),
        "Peak Memory (MB)": peak_memory
    }


# SIDEBAR
st.sidebar.header("Model Configuration")
st.sidebar.write("Selected Model: Llama 3.2 1B")

max_tokens = st.sidebar.slider(
    "Maximum Output Tokens",
    32, 512, 128
)


# CONNECTION STATUS
st.header("1. Model Connection")

try:
    models = check_connection()

    if MODEL in models:
        st.success("Ollama Connected | Model Available")
    else:
        st.error("Llama 3.2 1B is not installed.")

except Exception:
    st.error("Ollama is not connected. Start Ollama.")


# QUERY INPUT
st.divider()
st.header("2. Enter Test Queries")

default_text = """Explain Artificial Intelligence.

---

What is Machine Learning?

---

Explain Neural Networks.

---

What is Generative AI?

---

Explain Deep Learning with examples."""

query_text = st.text_area(
    "Enter prompts separated by ---",
    value=default_text,
    height=220
)

prompts = [
    p.strip()
    for p in query_text.split("---")
    if p.strip()
]

st.write("Total queries:", len(prompts))


# RUN TESTS
if st.button("🚀 Run Performance Test", type="primary"):

    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, prompt in enumerate(prompts):

        status.info(
            f"Processing query {i+1} of {len(prompts)}"
        )

        try:
            result = run_test(prompt, max_tokens)
            results.append(result)

        except Exception as e:
            st.error(f"Query {i+1} failed: {e}")

        progress.progress((i+1) / len(prompts))

    st.session_state["results"] = results

    if results:
        df = pd.DataFrame(results)
        df["Timestamp"] = datetime.now()

        df.to_csv(
            "performance_results.csv",
            index=False
        )

        st.success("Performance testing completed!")


# DASHBOARD
st.divider()
st.header("3. Performance Dashboard")

if "results" in st.session_state:

    results = st.session_state["results"]

    if results:

        df = pd.DataFrame(results)

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Queries", len(df))

        c2.metric(
            "Avg Inference Time",
            f"{df['Inference Time (s)'].mean():.2f} s"
        )

        c3.metric(
            "Avg Tokens/Sec",
            f"{df['Tokens Per Second'].mean():.2f}"
        )

        c4.metric(
            "Peak Memory",
            f"{df['Peak Memory (MB)'].max():.2f} MB"
        )

        st.subheader("Performance Results")

        st.dataframe(
            df.drop(columns=["Response", "Prompt"]),
            use_container_width=True
        )

        st.subheader("Performance Analytics")

        fig1 = px.bar(
            df,
            y="Inference Time (s)",
            title="Inference Time per Query"
        )

        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.bar(
            df,
            y="Tokens Per Second",
            title="Tokens Per Second"
        )

        st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.bar(
            df,
            y="Peak Memory (MB)",
            title="Peak Memory Usage"
        )

        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Generated Responses")

        for i, row in df.iterrows():

            with st.expander(f"Query {i+1}"):

                st.write("Prompt:", row["Prompt"])
                st.write("Response:", row["Response"])

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Performance Report",
            csv,
            file_name="performance_report.csv",
            mime="text/csv"
        )

    else:
        st.warning("No successful test results.")

else:
    st.info("Run the tests to display performance results.")


st.divider()
st.caption("GenAI Model Performance Monitoring System")
