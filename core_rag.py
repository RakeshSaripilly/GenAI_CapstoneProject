import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import httpx
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_classic.chains import create_retrieval_chain, create_history_aware_retriever

class GroqEmbeddings(Embeddings):
    """Custom embedding class leveraging Groq's hosted nomic-embed-text-v1.5 model."""
    def __init__(self, api_key: str, model_name: str = "nomic-embed-text-v1.5"):
        self.api_key = api_key
        self.model_name = model_name
        self.url = "https://api.groq.com/openai/v1/embeddings"
        
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": texts,
            "model": self.model_name
        }
        with httpx.Client() as client:
            response = client.post(self.url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
            
    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import config


DOCX_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

load_dotenv()


def _clean_cell_value(value):
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _dataframe_to_documents(frame, source_name, sheet_name=None):
    documents = []
    frame = frame.fillna("")

    for row_number, (_, row) in enumerate(frame.iterrows(), start=2):
        fields = []
        for column_name, value in row.items():
            cleaned_value = _clean_cell_value(value)
            if cleaned_value:
                fields.append(f"{column_name}: {cleaned_value}")

        if not fields:
            continue

        content_parts = [f"Source: {source_name}"]
        if sheet_name:
            content_parts.append(f"Sheet: {sheet_name}")
        content_parts.append(f"Row {row_number}: " + "; ".join(fields))

        metadata = {
            "source_type": "xlsx" if sheet_name else "csv",
            "source": source_name,
            "row_number": row_number,
        }
        if sheet_name:
            metadata["sheet_name"] = sheet_name

        documents.append(Document(page_content="\n".join(content_parts), metadata=metadata))

    return documents


def _load_docx_documents(file_path):
    source_name = Path(file_path).name
    documents = []

    with zipfile.ZipFile(file_path) as archive:
        document_xml = archive.read("word/document.xml")

    root = ET.fromstring(document_xml)

    paragraph_texts = []
    for paragraph in root.findall(".//w:p", DOCX_NAMESPACE):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", DOCX_NAMESPACE)).strip()
        if text:
            paragraph_texts.append(text)

    paragraph_text = "\n\n".join(paragraph_texts)
    if paragraph_text:
        documents.append(
            Document(
                page_content=paragraph_text,
                metadata={
                    "source_type": "docx",
                    "source": source_name,
                    "section": "paragraphs",
                },
            )
        )

    for table_index, table in enumerate(root.findall(".//w:tbl", DOCX_NAMESPACE), start=1):
        rows = table.findall(".//w:tr", DOCX_NAMESPACE)
        if not rows:
            continue

        headers = [
            ("".join(node.text or "" for node in cell.findall(".//w:t", DOCX_NAMESPACE)).strip() or f"Column {index + 1}")
            for index, cell in enumerate(rows[0].findall(".//w:tc", DOCX_NAMESPACE))
        ]
        table_lines = [f"Table {table_index}"]

        for row_number, row in enumerate(rows[1:], start=1):
            cells = row.findall(".//w:tc", DOCX_NAMESPACE)
            values = ["".join(node.text or "" for node in cell.findall(".//w:t", DOCX_NAMESPACE)).strip() for cell in cells]
            pairs = []
            for index, value in enumerate(values):
                if not value:
                    continue
                header = headers[index] if index < len(headers) else f"Column {index + 1}"
                pairs.append(f"{header}: {value}")

            if pairs:
                table_lines.append(f"Row {row_number}: " + "; ".join(pairs))

        if len(table_lines) > 1:
            documents.append(
                Document(
                    page_content="\n".join(table_lines),
                    metadata={
                        "source_type": "docx",
                        "source": source_name,
                        "section": "table",
                        "table_number": table_index,
                    },
                )
            )

    return documents


def load_documents(file_path):
    suffix = Path(file_path).suffix.lower()
    source_name = Path(file_path).name

    if suffix == ".pdf":
        loader = PyPDFLoader(file_path)
        return loader.load()

    if suffix == ".docx":
        return _load_docx_documents(file_path)

    if suffix == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()

    if suffix == ".csv":
        frame = pd.read_csv(file_path)
        return _dataframe_to_documents(frame, source_name)

    if suffix in {".xls", ".xlsx"}:
        sheets = pd.read_excel(file_path, sheet_name=None)
        documents = []
        for sheet_name, frame in sheets.items():
            documents.extend(_dataframe_to_documents(frame, source_name, sheet_name=sheet_name))
        return documents

    raise ValueError(f"Unsupported file format: {suffix}")


def _build_chain_from_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("No content could be extracted from the uploaded file(s).")

    embeddings = GroqEmbeddings(api_key=os.getenv("GROQ_API_KEY"))

    # Use ChromaDB only for persistence and retrieval.
    from langchain_community.vectorstores import Chroma

    collection_name = os.getenv("CHROMA_COLLECTION", "capstone_collection")
    persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", str(Path(__file__).resolve().parent / "chroma_db"))
    vectorstore = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name=collection_name,
        persist_directory=persist_directory,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": config.retriever_k})

    llm = ChatGroq(
        model=config.llm_model,
        temperature=config.llm_temperature,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    qa_system_prompt = (
        "You are a helpful study assistant. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, just say that you don't know. "
        "\n\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # Return chain and retriever so callers can fetch raw context if they
    # want to route documents into custom agent workflows.
    return rag_chain, retriever, len(chunks)


def build_rag_chain(file_path: str):
    """Loads a supported document, creates a vector store, and returns a conversational RAG chain."""
    documents = load_documents(file_path)
    return _build_chain_from_documents(documents)


def build_rag_chain_from_files(file_paths: list[str]):
    # Split each file separately to compute per-file chunk counts, then
    # combine all chunks and build a single vectorstore/chain.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    per_file_counts = {}
    all_chunks = []

    for file_path in file_paths:
        docs = load_documents(file_path)
        file_chunks = splitter.split_documents(docs)
        per_file_counts[Path(file_path).name] = len(file_chunks)
        all_chunks.extend(file_chunks)

    if not all_chunks:
        raise ValueError("No content could be extracted from the uploaded file(s).")

    embeddings = GroqEmbeddings(api_key=os.getenv("GROQ_API_KEY"))
    from langchain_community.vectorstores import Chroma

    collection_name = os.getenv("CHROMA_COLLECTION", "capstone_collection")
    persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", str(Path(__file__).resolve().parent / "chroma_db"))
    vectorstore = Chroma.from_documents(
        all_chunks,
        embeddings,
        collection_name=collection_name,
        persist_directory=persist_directory,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": config.retriever_k})

    llm = ChatGroq(
        model=config.llm_model,
        temperature=config.llm_temperature,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    qa_system_prompt = (
        "You are a helpful study assistant. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, just say that you don't know. "
        "\n\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    total_chunks = len(all_chunks)
    return rag_chain, retriever, total_chunks, per_file_counts