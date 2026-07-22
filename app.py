import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from core_rag import build_rag_chain_from_files

app = FastAPI()

PROJECT_ROOT = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
UPLOADED_FILES_DIR = KNOWLEDGE_BASE_DIR / "uploads"
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".xls", ".xlsx"}

ACTIVE_CHAIN = None
ACTIVE_RETRIEVER = None
ACTIVE_CHUNK_COUNT = 0
ACTIVE_PER_FILE_COUNTS = {}


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


def _collect_file_paths() -> list[str]:
    if not KNOWLEDGE_BASE_DIR.exists():
        return []

    file_paths: list[str] = []
    for path in KNOWLEDGE_BASE_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            file_paths.append(str(path))

    return sorted(file_paths)


def _clear_local_storage() -> None:
    global ACTIVE_CHAIN, ACTIVE_RETRIEVER, ACTIVE_CHUNK_COUNT, ACTIVE_PER_FILE_COUNTS

    # 1. Reset active RAG chain states
    ACTIVE_CHAIN = None
    ACTIVE_RETRIEVER = None
    ACTIVE_CHUNK_COUNT = 0
    ACTIVE_PER_FILE_COUNTS = {}

    # 2. Reset Chroma Collection
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import HuggingFaceBgeEmbeddings
        from config import config
        import os

        embeddings = HuggingFaceBgeEmbeddings(model_name=config.embedding_model)
        collection_name = os.getenv("CHROMA_COLLECTION", "capstone_collection")
        persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", str(PROJECT_ROOT / "chroma_db"))

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
        vectorstore.delete_collection()
    except Exception as e:
        print(f"Error resetting Chroma collection: {str(e)}")

    # 3. Clean uploaded files
    if KNOWLEDGE_BASE_DIR.exists():
        try:
            shutil.rmtree(KNOWLEDGE_BASE_DIR)
        except Exception as e:
            print(f"Error clearing upload directory: {str(e)}")

    # 4. Clean local Chroma directory files
    persist_path = Path(os.getenv("CHROMA_PERSIST_DIRECTORY", str(PROJECT_ROOT / "chroma_db")))
    if persist_path.exists():
        try:
            shutil.rmtree(persist_path)
        except Exception as e:
            print(f"Error clearing Chroma directory: {str(e)}")

    # Ensure empty directories exist for new uploads
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADED_FILES_DIR.mkdir(parents=True, exist_ok=True)


def _refresh_chain() -> dict:
    global ACTIVE_CHAIN, ACTIVE_CHUNK_COUNT
    global ACTIVE_RETRIEVER, ACTIVE_PER_FILE_COUNTS

    file_paths = _collect_file_paths()
    if not file_paths:
        ACTIVE_CHAIN = None
        ACTIVE_RETRIEVER = None
        ACTIVE_CHUNK_COUNT = 0
        return {"chunk_count": 0, "file_count": 0}

    # build_rag_chain_from_files now returns (chain, retriever, chunk_count, per_file_counts)
    ACTIVE_CHAIN, ACTIVE_RETRIEVER, ACTIVE_CHUNK_COUNT, ACTIVE_PER_FILE_COUNTS = build_rag_chain_from_files(file_paths)
    return {"chunk_count": ACTIVE_CHUNK_COUNT, "file_count": len(file_paths), "per_file_counts": ACTIVE_PER_FILE_COUNTS}


@app.on_event("startup")
def startup_index() -> None:
    # Clear databases and uploaded files on server startup
    _clear_local_storage()
    _refresh_chain()


@app.post("/ask")
def ask(question: str = None, request: AskRequest = None):
    """Answer a question using the indexed knowledge base.

    Accepts either:
    - Query parameter: POST /ask?question=your_question
    - JSON body: POST /ask with {"question": "your_question"}
    """
    try:
        actual_question = question or (request.question if request else None)

        if not actual_question:
            raise HTTPException(
                status_code=400,
                detail="Question is required. Use ?question=... or provide JSON body"
            )

        if ACTIVE_CHAIN is None:
            _refresh_chain()

        # If we have an indexed chain, run a retrieval pass first so we can
        # extract the exact context returned by the vectorstore/chain.
        from evaluation.evaluator import evaluate
        from graph.workflow import run_graph_flow

        retrieved_context = None
        retrieved_docs_meta = []

        if ACTIVE_CHAIN is not None:
            try:
                retrieval_result = ACTIVE_CHAIN.invoke({"input": actual_question, "chat_history": []})
                docs = retrieval_result.get("context") or []
            except Exception as chain_error:
                print(f"Retrieval chain error: {str(chain_error)}")
                docs = []

            # Fallback to retriever APIs if the chain doesn't expose context.
            if not docs and ACTIVE_RETRIEVER is not None:
                try:
                    if hasattr(ACTIVE_RETRIEVER, "invoke"):
                        docs = ACTIVE_RETRIEVER.invoke(actual_question) or []
                    elif hasattr(ACTIVE_RETRIEVER, "get_relevant_documents"):
                        docs = ACTIVE_RETRIEVER.get_relevant_documents(actual_question) or []
                    else:
                        docs = []
                except Exception as retriever_error:
                    print(f"Retriever error: {str(retriever_error)}")
                    docs = []

            if docs:
                retrieved_context = "\n\n".join([d.page_content for d in docs])
                for d in docs:
                    retrieved_docs_meta.append({
                        "source": d.metadata.get("source"),
                        "source_type": d.metadata.get("source_type"),
                        "summary_len": len(d.page_content)
                    })

        # Run the graph-based agent pipeline. If retrieved_context is None,
        # the graph receives only the question.
        agent_result = run_graph_flow(actual_question, retrieved_context or "")

        # Simple evaluation of final agent output
        evaluation_result = evaluate(agent_result.get("edited")) if agent_result.get("edited") else {}

        return {
            "status": "success",
            "retrieved": {
                "count": len(retrieved_docs_meta),
                "docs": retrieved_docs_meta,
                "context": retrieved_context,
            },
            "agent_result": {
                "research": agent_result.get("research"),
                "written": agent_result.get("article"),
                "final": agent_result.get("edited"),
            },
            "evaluation": evaluation_result,
        }
    except HTTPException:
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Error during question answering: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@app.post("/generate")
def generate(topic: str = None, request: AskRequest = None):
    """Backward-compatible alias for /ask."""
    question = topic or (request.question if request else None)
    return ask(question=question, request=request)


@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)):
    """Store uploaded files and rebuild the active RAG chain."""
    try:
        UPLOADED_FILES_DIR.mkdir(parents=True, exist_ok=True)
        saved_files = []

        for upload in files:
            file_name = Path(upload.filename).name
            target_path = UPLOADED_FILES_DIR / file_name
            with target_path.open("wb") as target_file:
                shutil.copyfileobj(upload.file, target_file)
            saved_files.append(str(target_path))

        summary = _refresh_chain()
        return {
            "status": "success",
            "saved_files": saved_files,
            "index": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest documents: {str(e)}")


@app.post("/reindex")
def reindex():
    """Rebuild the index from the current knowledge base."""
    try:
        summary = _refresh_chain()
        return {
            "status": "success",
            "index": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild index: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "indexed_files": len(_collect_file_paths()),
        "chunks": ACTIVE_CHUNK_COUNT,
    }


@app.post("/clear")
def clear_api():
    """Wipe the uploaded files and the vector database."""
    try:
        _clear_local_storage()
        return {"status": "success", "message": "Storage successfully cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear storage: {str(e)}")