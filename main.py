import os
import time
import json
import base64
import glob
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import prompt
from padronizacao import padronizar

load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ ERRO: Chave API não encontrada! Verifique o arquivo .env (variável OPENAI_API_KEY)")

client = OpenAI(api_key=api_key)

# Modelo: pode ser trocado pelo .env (OPENAI_MODEL) sem mexer no código.
# Precisa ser um modelo com visão (lê texto e imagem das páginas do PDF).
# Rode check_setup.py para ver quais modelos sua conta tem disponíveis.
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-astra")

# Structured Outputs em modo strict: a API garante que a resposta segue
# exatamente esse schema, em vez de confiar que o modelo "vai lembrar" de
# responder só em JSON.
SCHEMA_EXAMES = {
    "type": "json_schema",
    "name": "extrair_exames",
    "strict": True,
    "schema": {
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
                    "additionalProperties": False,
                },
            }
        },
        "required": ["exames"],
        "additionalProperties": False,
    },
}


def processar_exame_medico(caminho_pdf):
    print(f"🔬 Iniciando análise rigorosa do arquivo: {caminho_pdf}")

    with open(caminho_pdf, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=prompt.prompt_especialista,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": os.path.basename(caminho_pdf),
                            "file_data": f"data:application/pdf;base64,{pdf_base64}",
                        },
                        {"type": "input_text", "text": "Extraia os dados deste exame."},
                    ],
                }
            ],
            text={"format": SCHEMA_EXAMES},
        )

        # Com o schema strict, output_text é sempre um JSON válido nesse
        # formato — não precisa tratar markdown/crases na resposta.
        dados = json.loads(response.output_text).get("exames", [])

        if not dados:
            print(f"⚠️ Nenhum exame extraído de {caminho_pdf}.")
            return None

        df = pd.DataFrame(dados)
        df["arquivo_origem"] = os.path.basename(caminho_pdf)

        if "valor" in df.columns:
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

        return padronizar(df)

    except Exception as e:
        print(f"❌ Erro ao processar {caminho_pdf}: {e}")
        return None


# --- Execução (em lote) ---
if __name__ == "__main__":
    pasta_exames = "./exames"
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
