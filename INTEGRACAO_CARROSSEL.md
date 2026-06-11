# Carrossel automático — como ativar

O sistema agora publica CARROSSÉIS, intercalando 3 tipos:
benefícios → curiosidades → modo de usar (um diferente a cada vez).
O conteúdo de cada óleo é escrito pela IA e revisado pelas regras da ANVISA
(sem prometer cura). Usa a foto real do produto e a mesma hospedagem do feed.

## O que subir no GitHub (Upload files)
- A pasta `src` inteira (tem os arquivos novos: rotacao.py, carrossel_conteudo.py,
  image/carrossel_arte.py).
- O arquivo `run_carrossel.py` (na raiz).

## Criar o agendamento (uma vez)
No GitHub: Add file → Create new file → no nome do arquivo escreva:
`.github/workflows/publicar-carrossel.yml`
e cole o conteúdo do arquivo `publicar-carrossel.yml` que veio junto. Commit.
Ele roda sozinho QUARTA e SÁBADO (~14h). Pra testar na hora:
aba Actions → Publicar Carrossel → Run workflow.

## Segredo da IA
O carrossel usa o segredo `ANTHROPIC_API_KEY` (o mesmo que o feed já usa).
Se o feed já escreve textos com IA, não precisa fazer nada.
Sem esse segredo, o carrossel ainda funciona, mas com textos padrão (mais genéricos).
