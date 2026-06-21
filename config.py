from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    retriever_k: int = int(os.getenv("RETRIEVER_K", "4"))
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))


config = Config()