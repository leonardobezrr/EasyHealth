# EasyHealth — Auxiliando na saúde generalizada

Extrai dados estruturados de exames laboratoriais (PDF) usando IA, e
exibe a evolução dos resultados ao longo do tempo num dashboard.

## Como funciona

1. Você coloca os PDFs de exames numa pasta `exames/`
2. `main.py` manda cada PDF pra API da Anthropic (Claude), que extrai
   cada resultado (exame, valor, unidade, referência, data) em formato
   estruturado — via *tool use*, o que garante que a resposta sempre
   vem no formato esperado, sem precisar validar/consertar texto solto
3. Os dados viram `resultadosPadronizados.csv`
4. `dashboard.py` (Streamlit) lê esse CSV e mostra gráficos comparativos
   de evolução por exame

## Instalação

```bash
pip install -r requirements.txt
cp .env.example .env
# edite o .env e cole sua chave da Anthropic (console.anthropic.com/settings/keys)
```

## Uso

```bash
# 1. Extrair dados dos PDFs (coloque os arquivos em ./exames/ antes)
python main.py

# 2. Abrir o dashboard
streamlit run dashboard.py
```

`check_setup.py` é opcional — roda ele se quiser só confirmar que sua
chave está funcionando e ver quais modelos estão disponíveis, sem
processar nenhum PDF:
```bash
python check_setup.py
```

## Segurança

- A chave de API **nunca** deve ser colada direto no código — sempre
  via `.env` (que já está no `.gitignore`).
- Este projeto não armazena nem transmite dados de pacientes a
  terceiros além da própria API usada para extração.

## Aviso

Esta ferramenta organiza e visualiza dados de exames — ela **não
interpreta resultados clinicamente nem substitui avaliação médica**.
