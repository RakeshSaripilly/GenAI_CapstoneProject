import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests
import streamlit as st

# Automatically launch the backend API if it isn't running
def start_backend_if_needed(port=8000):
    # Check if the port is already bound (API is already running)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        is_running = s.connect_ex(("127.0.0.1", port)) == 0
        
    if not is_running:
        try:
            # Start FastAPI backend in the background using the current Python environment
            backend_cmd = [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port)]
            # Direct uvicorn logs to backend.log to debug issues
            log_file = open("backend.log", "w", encoding="utf-8")
            subprocess.Popen(backend_cmd, stdout=log_file, stderr=subprocess.STDOUT)
            # Give it a moment to boot
            time.sleep(4)
        except Exception as e:
            st.error(f"Could not auto-start backend API: {str(e)}")

# Try to auto-start backend
start_backend_if_needed(8000)

env_api_url = os.getenv("RAG_API_URL", "").strip()
API_URL = env_api_url if env_api_url else "http://127.0.0.1:8000"

def wait_for_backend(port=8000, timeout=45):
    """Poll the backend port until it is ready to accept connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(1)
    return False

def make_api_request(method, endpoint, **kwargs):
    """Safely execute HTTP request after ensuring backend is fully running and active."""
    # Ensure background process is started
    start_backend_if_needed(8000)
    
    # Wait for backend to be ready to accept connections
    if not wait_for_backend(8000, timeout=45):
        # Retrieve logs to see why the API failed to start
        log_content = ""
        try:
            log_path = Path("backend.log")
            if log_path.exists():
                with open(log_path, "r", encoding="utf-8") as f:
                    log_content = f.read()[-1500:] # Show the last 1500 chars of logs
        except Exception as log_err:
            log_content = f"Failed to retrieve backend logs: {str(log_err)}"
            
        raise ConnectionError(
            f"The backend API failed to respond on port 8000 after 45 seconds.\n\n"
            f"🔍 **Backend Startup Logs:**\n```\n{log_content}\n```"
        )
        
    url = f"{API_URL}{endpoint}"
    return requests.request(method, url, **kwargs)

st.set_page_config(page_title="RAG Knowledge Assistant", layout="wide")
st.title("RAG Knowledge Assistant")
st.write("Upload mixed file types, rebuild the index, and ask grounded questions.")

with st.sidebar:
    st.header("Knowledge Base")
    st.caption("Supported file types: PDF, DOCX, TXT, CSV, XLS, XLSX.")
    uploaded_files = st.file_uploader(
        "Add documents",
        type=["pdf", "docx", "txt", "csv", "xls", "xlsx"],
        accept_multiple_files=True,
    )

    # Keep a session-scoped map of filename -> chunk_count so UI can show
    # counts until files are removed from the knowledge base.
    if "file_chunks" not in st.session_state:
        st.session_state["file_chunks"] = {}

    # Display tracked files and counts for this session
    if st.session_state["file_chunks"]:
        st.markdown("**Indexed files (tracked this session)**")
        for name, cnt in list(st.session_state["file_chunks"].items()):
            cols = st.columns([4, 1])
            cols[0].write(f"{name} — {cnt} chunk(s)")
            if cols[1].button("Remove", key=f"remove_{name}"):
                # Remove from session-only tracking; does not delete server file
                st.session_state["file_chunks"].pop(name, None)
                st.experimental_rerun()

    if st.button("Index uploaded documents"):
        if not uploaded_files:
            st.warning("Upload at least one document first.")
        else:
            try:
                multipart_files = [
                    (
                        "files",
                        (
                            Path(uploaded_file.name).name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        ),
                    )
                    for uploaded_file in uploaded_files
                ]
                
                with st.status("Indexing documents...", expanded=True) as status:
                    status.write("📤 Uploading files to the backend server...")
                    time.sleep(1)
                    status.write("📄 Extracting text and parsing document layout...")
                    
                    response = make_api_request("POST", "/ingest", files=multipart_files, timeout=600)
                    response.raise_for_status()
                    data = response.json()
                    
                    status.write("🧠 Splitting text into chunks and generating vector embeddings...")
                    time.sleep(1)
                    status.write("💾 Indexing vectors into local Chroma database...")
                    time.sleep(0.5)
                    status.update(label="Document indexing complete!", state="complete", expanded=False)

                index_info = data.get("index") or {}
                chunk_count = index_info.get("chunk_count", 0)
                file_count = index_info.get("file_count", len(uploaded_files))
                per_file = index_info.get("per_file_counts", {})

                # Update UI session map with per-file counts
                for name, cnt in per_file.items():
                    st.session_state["file_chunks"][name] = cnt

                # Display summary metrics
                st.markdown("### 📊 Indexing Summary")
                col1, col2 = st.columns(2)
                col1.metric("Files Processed", f"📁 {file_count}")
                col2.metric("Total Chunks Created", f"🧠 {chunk_count}")

                if per_file:
                    with st.expander("Show detailed chunks breakdown", expanded=True):
                        for name, cnt in per_file.items():
                            st.write(f"📄 `{name}`: **{cnt}** chunks")
            except Exception as e:
                st.error(f"Failed to index documents: {str(e)}")

    if st.button("Rebuild index from project sources"):
        try:
            with st.status("Rebuilding index...", expanded=True) as status:
                status.write("🔎 Scanning project directories for compatible documents...")
                time.sleep(1)
                status.write("📄 Loading and parsing documents...")
                
                response = make_api_request("POST", "/reindex", timeout=600)
                response.raise_for_status()
                data = response.json()
                
                status.write("🧠 Chunking contents and running embedding model...")
                time.sleep(1)
                status.write("💾 Updating the Chroma vector store...")
                time.sleep(0.5)
                status.update(label="Reindexing complete!", state="complete", expanded=False)

            index_info = data.get("index") or {}
            chunk_count = index_info.get("chunk_count", 0)
            file_count = index_info.get("file_count", 0)
            per_file = index_info.get("per_file_counts", {})

            # Refresh session map from server mapping
            st.session_state["file_chunks"].update(per_file)

            # Display summary metrics
            st.markdown("### 📊 Reindex Summary")
            col1, col2 = st.columns(2)
            col1.metric("Files Processed", f"📁 {file_count}")
            col2.metric("Total Chunks Created", f"🧠 {chunk_count}")

            if per_file:
                with st.expander("Show detailed chunks breakdown", expanded=True):
                    for name, cnt in per_file.items():
                        st.write(f"📄 `{name}`: **{cnt}** chunks")
        except Exception as e:
            st.error(f"Failed to rebuild index: {str(e)}")

    st.markdown("---")
    if st.button("Clear Database & Session", help="Wipe all uploaded documents and reset vector database storage"):
        try:
            with st.spinner("Clearing storage..."):
                response = make_api_request("POST", "/clear", timeout=30)
                response.raise_for_status()
            st.session_state["file_chunks"] = {}
            st.success("Session storage cleared successfully!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to clear session: {str(e)}")

question = st.text_area(
    "Ask a question about the indexed documents",
    height=140,
    placeholder="Example: What does the document say about the workflow or setup?",
)

if st.button("Ask"):
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        try:
            # Create a placeholder to inject the custom CSS pulsing loader animation
            loader_placeholder = st.empty()
            with loader_placeholder.container():
                st.markdown("""
                    <div class="loading-box">
                        <div class="loading-content">
                            <div class="spinner-ring"></div>
                            <div class="pulsing-orb"></div>
                        </div>
                        <div class="loading-msg">🤖 RAG Agents are researching and writing...</div>
                    </div>
                    <style>
                    .loading-box {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        padding: 30px;
                        margin: 20px 0;
                        border-radius: 15px;
                        background: rgba(139, 92, 246, 0.05);
                        border: 1px solid rgba(139, 92, 246, 0.15);
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                        backdrop-filter: blur(8px);
                        animation: fadeIn 0.4s ease-out;
                    }
                    .loading-content {
                        position: relative;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        width: 80px;
                        height: 80px;
                    }
                    .spinner-ring {
                        box-sizing: border-box;
                        width: 70px;
                        height: 70px;
                        border: 4px solid transparent;
                        border-top: 4px solid #6366f1;
                        border-right: 4px solid #8b5cf6;
                        border-bottom: 4px solid #ec4899;
                        border-radius: 50%;
                        animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
                    }
                    .pulsing-orb {
                        position: absolute;
                        width: 32px;
                        height: 32px;
                        background: radial-gradient(circle, #a78bfa 0%, #8b5cf6 50%, #6366f1 100%);
                        border-radius: 50%;
                        box-shadow: 0 0 15px rgba(99, 102, 241, 0.6), 0 0 30px rgba(139, 92, 246, 0.4);
                        animation: pulse 1.8s ease-in-out infinite;
                    }
                    .loading-msg {
                        margin-top: 20px;
                        font-family: 'Outfit', -apple-system, sans-serif;
                        color: #a78bfa;
                        font-size: 1.15rem;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                        text-align: center;
                        animation: blink 2s ease-in-out infinite;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    @keyframes pulse {
                        0%, 100% { transform: scale(0.9); opacity: 0.8; box-shadow: 0 0 15px rgba(99, 102, 241, 0.5); }
                        50% { transform: scale(1.15); opacity: 1; box-shadow: 0 0 25px rgba(99, 102, 241, 0.8), 0 0 45px rgba(139, 92, 246, 0.6); }
                    }
                    @keyframes blink {
                        0%, 100% { opacity: 0.7; }
                        50% { opacity: 1; }
                    }
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(8px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    </style>
                """, unsafe_allow_html=True)

            try:
                response = make_api_request(
                    "POST",
                    "/ask",
                    json={"question": question},
                    timeout=180,
                )
                response.raise_for_status()
                data = response.json()
            finally:
                # Always clean up the loader placeholder from screen
                loader_placeholder.empty()

            # New API returns top-level keys: 'retrieved', 'agent_result', 'evaluation'
            retrieved = data.get("retrieved") or {}
            agent_result = data.get("agent_result") or {}
            evaluation = data.get("evaluation") or {}

            # Backwards compatibility: older API placed results under 'result'
            if not agent_result and data.get("result"):
                legacy = data.get("result")
                # try common legacy fields
                agent_result = {
                    "final": legacy.get("answer") or legacy.get("final") or "",
                    "research": None,
                    "written": None,
                }

            st.subheader("Answer (Agent final output)")
            final_text = agent_result.get("final") or ""
            if final_text and final_text.strip():
                st.write(final_text)
            else:
                st.info("No final agent output returned.")

            st.subheader("Retrieved Context")
            context_text = retrieved.get("context") if isinstance(retrieved, dict) else None
            if context_text and context_text.strip():
                st.text_area("Context sent to agents", value=context_text, height=200)
            else:
                st.info("No context returned or no documents indexed.")

            # Show meta information
            st.markdown("**Retrieval summary**")
            st.write(f"Documents returned: {retrieved.get('count', 0)}")
            if retrieved.get("docs"):
                st.write(retrieved.get("docs"))

            st.markdown("**Evaluation**")
            if evaluation:
                st.json(evaluation)

            st.subheader("Agent pipeline outputs")
            if agent_result:
                with st.expander("Research output"):
                    st.text(agent_result.get("research") or "(none)")
                with st.expander("Written output"):
                    st.text(agent_result.get("written") or "(none)")
            else:
                st.info("No agent outputs available.")

            with st.expander("Full API response"):
                st.json(data)
        except Exception as e:
            st.error(
                f"Connection error: {str(e)}\n\nMake sure the API server is running on {API_URL}"
            )
