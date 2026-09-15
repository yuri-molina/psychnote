import os
from enum import IntEnum
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel


class LLMProvider(IntEnum):
    """
    Identificador numérico do provedor de LLM.
    Passado como parâmetro de API para selecionar o backend de inferência.
    """
    OLLAMA = 1   # Execução 100% local via Ollama (Edge AI / LGPD)
    GEMINI = 2   # Execução remota via Google Gemini (requer GOOGLE_API_KEY no .env)


class PsychiatricAIEngine:
    """
    Engine para gerenciamento de LLMs compatíveis com o pipeline de triagem.
    Suporta dois backends:
      1 — Ollama local (padrão, LGPD-safe, offline-first).
      2 — Google Gemini via API (requer GOOGLE_API_KEY configurado no .env).
    """

    @staticmethod
    def get_llm(
        provider: LLMProvider = LLMProvider.OLLAMA,
        model_name: str | None = None,
        temperature: float = 0,
    ) -> BaseChatModel:
        """
        Retorna a instância de LLM configurada para o provedor solicitado.

        Args:
            provider: 1 = Ollama local, 2 = Google Gemini remoto.
            model_name: sobrescreve o modelo padrão do provedor (opcional).
            temperature: temperatura de amostragem (0 = determinístico).
        """
        if provider == LLMProvider.GEMINI:
            return PsychiatricAIEngine._get_gemini_llm(model_name=model_name, temperature=temperature)
        return PsychiatricAIEngine._get_ollama_llm(model_name=model_name, temperature=temperature)

    # ------------------------------------------------------------------
    # Backends privados
    # ------------------------------------------------------------------

    @staticmethod
    def _get_ollama_llm(
        model_name: str | None = None,
        temperature: float = 0,
    ) -> BaseChatModel:
        """
        Retorna ChatOllama configurado para o hardware Intel Core Ultra.
        num_thread=10 equilibra P-cores e E-cores conforme GEMINI.md.
        """
        resolved_model = model_name or os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q4_K_M")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        print(f"[*] Inicializando Engine (Ollama): {resolved_model} | {base_url}")

        return ChatOllama(
            model=resolved_model,
            temperature=temperature,
            num_ctx=4096,
            num_thread=10,  # Otimizado para Intel Core Ultra 5 (2 P-cores + 8 E-cores)
            base_url=base_url,
        )

    @staticmethod
    def _get_gemini_llm(
        model_name: str | None = None,
        temperature: float = 0,
    ) -> BaseChatModel:
        """
        Retorna ChatGoogleGenerativeAI configurado via GOOGLE_API_KEY.
        Requer a variável de ambiente GOOGLE_API_KEY definida no .env.

        ⚠ ATENÇÃO LGPD: Este provedor envia dados para a infraestrutura Google.
        Use exclusivamente para fins de benchmark/pesquisa com dados sintéticos.
        NUNCA utilize com dados reais de pacientes em produção.
        """
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "sua_chave_aqui":
            raise EnvironmentError(
                "[!] GOOGLE_API_KEY não configurada. "
                "Defina a chave no arquivo .env (https://aistudio.google.com/apikey)."
            )

        resolved_model = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-3.8-flash")
        print(f"[*] Inicializando Engine (Gemini): {resolved_model}")

        return ChatGoogleGenerativeAI(
            model=resolved_model,
            google_api_key=api_key,
            temperature=temperature,
        )


def get_psychiatric_llm(provider: LLMProvider = LLMProvider.OLLAMA) -> BaseChatModel:
    """Entry point para obter o modelo configurado pelo provedor."""
    return PsychiatricAIEngine.get_llm(provider=provider)


if __name__ == "__main__":
    # Teste rápido de inicialização do provedor local
    llm = get_psychiatric_llm(provider=LLMProvider.OLLAMA)
    print(f"[+] Engine Ollama configurada com sucesso: {type(llm).__name__}")
