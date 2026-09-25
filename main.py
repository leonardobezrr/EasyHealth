import os
import time
import base64
import glob
import pandas as pd
import anthropic
from dotenv import load_dotenv
import prompt

load_dotenv(override=True)

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("❌ ERRO: Chave API não encontrada! Verifique o arquivo .env (variável ANTHROPIC_API_KEY)")

client = anthropic.Anthropic(api_key=api_key)

# Modelo: Sonnet dá o melhor equilíbrio entre precisão (importante em dado de
# saúde) e custo. Se quiser reduzir custo e o volume de exames for grande,
# "claude-haiku-4-5-20251001" também processa PDF e costuma ser suficiente
# para exames com formatação limpa.
MODEL = "claude-sonnet-5"

# Definição da ferramenta: força o Claude a devolver dados nesse formato
# exato, em vez de confiar que ele "vai lembrar" de responder só em JSON.
FERRAMENTA_EXTRACAO = {
    "name": "extrair_exames",
    "description": "Registra os resultados de exames laboratoriais extraídos do documento.",
    "input_schema": {
        "type": "object",
        "properties": {
            "exames": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Data da coleta, formato dd/mm/aaaa"},
                        "exame": {"type": "string", "description": "Nome padronizado do analito/exame"},
                        "valor": {"type": "string", "description": "Valor numérico, ex: '78.6'"},
                        "unidade": {"type": "string"},
                        "referencia": {"type": "string", "description": "Faixa de referência, como está no documento"},
                        "referencia_suspeita": {"type": "boolean", "description": "true se a referência parecer inconsistente"},
                    },
                    "required": ["data", "exame", "valor", "unidade", "referencia", "referencia_suspeita"],
                },
            }
        },
        "required": ["exames"],
    },
}


def processar_exame_medico(caminho_pdf):
    print(f"🔬 Iniciando análise rigorosa do arquivo: {caminho_pdf}")

    with open(caminho_pdf, "rb") as f:
        pdf_base64 = base64.standard_b64encode(f.read()).decode("utf-8")

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=prompt.prompt_especialista,
            tools=[FERRAMENTA_EXTRACAO],
            tool_choice={"type": "tool", "name": "extrair_exames"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64,
                            },
                        },
                        {"type": "text", "text": "Extraia os dados deste exame."},
                    ],
                }
            ],
        )

        # Com tool_choice forçado, o bloco de resposta é sempre um tool_use
        # com .input já parseado como dict — não precisa fazer json.loads
        # nem tratar markdown/crases na resposta.
        tool_block = next(b for b in response.content if b.type == "tool_use")
        dados = tool_block.input.get("exames", [])

        if not dados:
            print(f"⚠️ Nenhum exame extraído de {caminho_pdf}.")
            return None

        df = pd.DataFrame(dados)
        df["arquivo_origem"] = os.path.basename(caminho_pdf)

        if "valor" in df.columns:
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

        return df

    except Exception as e:
        print(f"❌ Erro ao processar {caminho_pdf}: {e}")
        return None


# --- Execução (em lote) ---
if __name__ == "__main__":
    pasta_exames = "./exames"
    # Nome unificado com o que dashboard.py espera (antes havia um
    # descompasso: main.py escrevia em "dados_exames_estruturados.csv" e
    # dashboard.py lia "resultadosPadronizados.csv" — o dashboard nunca
    # achava o arquivo).
    arquivo_saida = "resultadosPadronizados.csv"

    lista_pdfs = glob.glob(os.path.join(pasta_exames, "*.pdf"))
    print(f"🔎 Encontrados {len(lista_pdfs)} arquivos para processar.")

    for caminho_arquivo in lista_pdfs:
        df_resultado = processar_exame_medico(caminho_arquivo)

        if df_resultado is not None and not df_resultado.empty:
            escrever_cabecalho = not os.path.exists(arquivo_saida)
            df_resultado.to_csv(arquivo_saida, mode="a", index=False, header=escrever_cabecalho)
            print(f"💾 Dados de {os.path.basename(caminho_arquivo)} salvos.")

            print("💤 Resfriando API (2s)...")
            time.sleep(2)
        else:
            print(f"⚠️ Nenhum dado extraído de {caminho_arquivo}.")

    print("\n🏁 Processamento finalizado.")
