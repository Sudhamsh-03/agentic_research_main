from app.config import get_settings


class LLMConfigurationError(RuntimeError):
    pass


def build_chat_model(temperature: float | None = None):
    """Return a LangChain chat model, or None when running without a provider.

    Offline mode is a first-class path: the nodes fall back to deterministic template
    output so the pipeline can be demonstrated end to end without credentials.
    """
    settings = get_settings()
    provider = settings.llm_provider.lower()
    resolved_temperature = (
        settings.llm_temperature if temperature is None else temperature
    )

    if provider == "offline":
        return None

    if provider == "openai":
        if not settings.openai_api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": settings.llm_model,
            "temperature": resolved_temperature,
            "api_key": settings.openai_api_key,
        }
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return ChatOpenAI(**kwargs)

    if provider == "google":
        if not settings.google_api_key:
            raise LLMConfigurationError("GOOGLE_API_KEY is required when LLM_PROVIDER=google")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:  # optional extra
            raise LLMConfigurationError(
                "langchain-google-genai is not installed; run "
                "pip install langchain-google-genai"
            ) from exc
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=resolved_temperature,
            google_api_key=settings.google_api_key,
        )

    raise LLMConfigurationError(f"unknown LLM_PROVIDER '{settings.llm_provider}'")
