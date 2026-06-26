import logging
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from src.utils.interfaces import ILLMFactory
from src.config.settings import Settings

logger = logging.getLogger("llm_factory")

class LLMFactory(ILLMFactory):
    def get_llm(self, model_name: str | None = None, **kwargs) -> BaseChatModel:
        provider = Settings.AI_PROVIDER
        api_key = Settings.AI_API_KEY
        model = model_name or Settings.AI_MODEL
        
        if not api_key:
            logger.error(f"AI_API_KEY is missing for provider: {provider}")
            raise ValueError(f"AI_API_KEY is not set for AI_PROVIDER={provider}")
            
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model or "gpt-4o-mini", api_key=api_key, **kwargs)
            
        elif provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(model=model or "llama-3.3-70b-versatile", api_key=api_key, **kwargs)
            
        elif provider == "huggingface":
            from langchain_huggingface import HuggingFaceEndpoint
            from langchain_community.chat_models.huggingface import ChatHuggingFace
            llm = HuggingFaceEndpoint(repo_id=model or "meta-llama/Meta-Llama-3-8B-Instruct", huggingfacehub_api_token=api_key, **kwargs)
            return ChatHuggingFace(llm=llm)
            
        elif provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model or "gemini-2.5-flash", google_api_key=api_key, **kwargs)
            
        else:
            logger.error(f"Unsupported AI_PROVIDER: {provider}")
            raise ValueError(f"Unsupported AI_PROVIDER: {provider}")

    def get_embeddings(self, model_name: str | None = None, **kwargs) -> Embeddings:
        provider = Settings.EMBEDDING_PROVIDER
        api_key = Settings.EMBEDDING_API_KEY
        model = model_name or Settings.EMBEDDING_MODEL
        
        if not api_key:
            logger.error(f"EMBEDDING_API_KEY is missing for provider: {provider}")
            raise ValueError(f"EMBEDDING_API_KEY is not set for EMBEDDING_PROVIDER={provider}")
            
        if provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            # Force 768 dimensions for OpenAI (only works on text-embedding-3 models) to match Qdrant
            return OpenAIEmbeddings(model=model or "text-embedding-3-small", api_key=api_key, dimensions=768, **kwargs)
            
        elif provider == "huggingface":
            from langchain_huggingface import HuggingFaceEndpointEmbeddings
            return HuggingFaceEndpointEmbeddings(model=model or "sentence-transformers/all-MiniLM-L6-v2", huggingfacehub_api_token=api_key, **kwargs)
            
        elif provider == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(model=model or "models/embedding-001", google_api_key=api_key, **kwargs)
            
        else:
            logger.error(f"Unsupported EMBEDDING_PROVIDER: {provider}")
            raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")
