"""
Module for initializing and configuring language models used in the application.
"""

from langchain_community.llms import HuggingFaceEndpoint
from langchain_openai import ChatOpenAI

from config.settings import (
    OPENAI_API_KEY,
    HUGGINGFACE_API_KEY,
    OPENAI_MODEL,
    MISTRAL_MODEL,
    TEMPERATURE_OPENAI,
    TEMPERATURE_HF
)


def init_openai_chat_model():
    """
    Initialize the OpenAI chat model.
    
    Returns:
        ChatOpenAI: Configured OpenAI chat model
    """
    return ChatOpenAI(
        model_name=OPENAI_MODEL, 
        temperature=TEMPERATURE_OPENAI,
        api_key=OPENAI_API_KEY
    )


def init_huggingface_model():
    """
    Initialize the HuggingFace model for summarization.
    
    Returns:
        HuggingFaceEndpoint: Configured HuggingFace model
    """
    return HuggingFaceEndpoint(
        repo_id=MISTRAL_MODEL,
        temperature=TEMPERATURE_HF,
        huggingfacehub_api_token=HUGGINGFACE_API_KEY
    )