import os
import time
import json
import glob 
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv 
import prompt

load_dotenv(override=True)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("❌ ERRO: Chave API não encontrada! Verifique o arquivo .env")

genai.configure(api_key=api_key)

def processar_exame_medico(caminho_pdf):
    print(f"🔬 Iniciando análise rigorosa do arquivo: {caminho_pdf}")
    
    arquivo_upload = genai.upload_file(caminho_pdf)
    
    while arquivo_upload.state.name == "PROCESSING":
        print("⏳ Processando PDF nos servidores do Google...")
        time.sleep(2)
        arquivo_upload = genai.get_file(arquivo_upload.name)
        
    if arquivo_upload.state.name == "FAILED":
        print(f"❌ Falha no processamento do arquivo: {caminho_pdf}") # Mudei para print para não parar o loop
        return None

    print("✅ PDF pronto. Enviando para o Gemini 2.5 Flash...")

    prompt_especialista = prompt.prompt_especialista

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=prompt_especialista
    )

    safety_settings = {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    }

    try:
        response = model.generate_content(
            [arquivo_upload, "Extraia os dados deste exame para JSON."],
            generation_config={"response_mime_type": "application/json"},
            safety_settings=safety_settings
        )
        
        dados_json = json.loads(response.text)
        df = pd.DataFrame(dados_json)
        
        # Adiciona coluna para identificar de qual exame veio o dado
        df['arquivo_origem'] = os.path.basename(caminho_pdf) 
        
        # Tratamento de erro caso a coluna 'valor' não exista no JSON retornado
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        elif 'resultado_valor' in df.columns: # Fallback para o nome comum em prompts
             df['resultado_valor'] = pd.to_numeric(df['resultado_valor'], errors='coerce')
        
        return df
    except Exception as e: # Capturei Exception genérica para garantir que o loop continue
        print(f"❌ Erro ao processar {caminho_pdf}: {e}")
        return None

# --- Execução (ALTERADA PARA LOTE) ---
if __name__ == "__main__":
    pasta_exames = "./exames"
    arquivo_saida = "dados_exames_estruturados.csv"
    
    # 2. Busca todos os PDFs na pasta
    lista_pdfs = glob.glob(os.path.join(pasta_exames, "*.pdf"))
    
    print(f"🔎 Encontrados {len(lista_pdfs)} arquivos para processar.")

    for caminho_arquivo in lista_pdfs:
        df_resultado = processar_exame_medico(caminho_arquivo)
        
        if df_resultado is not None and not df_resultado.empty:
            # 3. Lógica de Append (Adicionar sem sobrescrever)
            # Só escreve o cabeçalho se o arquivo AINDA NÃO existir
            escrever_cabecalho = not os.path.exists(arquivo_saida)
            
            df_resultado.to_csv(arquivo_saida, mode='a', index=False, header=escrever_cabecalho)
            print(f"💾 Dados de {os.path.basename(caminho_arquivo)} salvos.")
            
            # Pausa obrigatória para não estourar a cota gratuita (Professor avisa!)
            print("💤 Resfriando API (5s)...")
            time.sleep(5)
        else:
            print(f"⚠️ Nenhum dado extraído de {caminho_arquivo}.")
            
    print("\n🏁 Processamento finalizado.")