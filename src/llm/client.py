"""
Wrapper fino sobre a API do Claude.
Ponto único de chamada ao LLM. Permite injetar uma função de geração
alternativa (usado nos testes, para não gastar API e ser determinístico).
"""
from src import config

# Modelos: Haiku para volume (barato), Sonnet para raciocínio estratégico
MODELO_PADRAO = "claude-haiku-4-5-20251001"
MODELO_ESTRATEGIA = "claude-sonnet-4-6"


class LLMClient:
    def __init__(self, gerar_fn=None, modelo: str = MODELO_PADRAO):
        # gerar_fn injetável: se fornecido, substitui a chamada real (testes)
        self._gerar_fn = gerar_fn
        self.modelo = modelo

    def gerar(self, prompt: str, system: str = "", max_tokens: int = 900) -> str:
        if self._gerar_fn is not None:
            return self._gerar_fn(prompt=prompt, system=system, max_tokens=max_tokens)

        # Chamada real à API Anthropic
        import anthropic
        cliente = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = cliente.messages.create(
            model=self.modelo,
            max_tokens=max_tokens,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
