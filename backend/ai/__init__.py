"""
AI Module for Micron Hackathon Project
Handles LLM integration, embeddings, Qdrant vector search, and RAG pipelines.
"""
from ai.llm_service import LLMService, get_llm_response

__all__ = ["LLMService", "get_llm_response"]
