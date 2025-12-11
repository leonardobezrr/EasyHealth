import os
import time
import json
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv 

load_dotenv()

# 2. Pega a chave do sistema (agora segura)
api_key = os.getenv("GOOGLE_API_KEY")

# Verificação de segurança (Professor Rigoroso não confia, ele verifica)
if not api_key:
    raise ValueError("❌ ERRO: Chave API não encontrada! Verifique o arquivo .env")

genai.configure(api_key=api_key)

def processar_exame_medico(caminho_pdf):
    print(f"🔬 Iniciando análise rigorosa do arquivo: {caminho_pdf}")
    
    # 2. Upload do Arquivo (Gemini 1.5 Pro lê PDFs nativamente)
    # Isso é superior a usar PyPDF2 porque a IA "vê" o layout da tabela.
    arquivo_upload = genai.upload_file(caminho_pdf)
    
    # Aguarda o processamento do arquivo pelo Google
    while arquivo_upload.state.name == "PROCESSING":
        print("⏳ Processando PDF nos servidores do Google...")
        time.sleep(2)
        arquivo_upload = genai.get_file(arquivo_upload.name)
        
    if arquivo_upload.state.name == "FAILED":
        raise ValueError("Falha no processamento do arquivo pela API.")

    print("✅ PDF pronto. Enviando para o Gemini 1.5 Pro...")

    # 3. Definição do Modelo e Prompt
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction="""
        Você é um extrator de dados laboratoriais. 
        Analise o PDF fornecido. 
        Extraia TODOS os resultados de exames.
        Para o Hemograma, extraia cada linha (Hemácias, Leucócitos, etc) como um item separado.
        Responda APENAS com um array JSON válido, sem formatação Markdown.
        Esquema: [{"data": "dd/mm/aaaa", "exame": "Nome", "valor": "0.00", "unidade": "un", "referencia": "texto"}]
        """
    )

    # Configuração de segurança para evitar bloqueios indevidos em termos médicos
    safety_settings = {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    }

    # 4. Geração
    response = model.generate_content(
        [arquivo_upload, "Extraia os dados deste exame para JSON."],
        generation_config={"response_mime_type": "application/json"},
        safety_settings=safety_settings
    )

    # 5. Tratamento da Resposta
    try:
        dados_json = json.loads(response.text)
        df = pd.DataFrame(dados_json)
        
        # Limpeza fina (Professor Rigoroso)
        # Garante que 'valor' seja numérico para o Dashboard somar/fazer médias depois
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce') 
        
        return df
    except json.JSONDecodeError:
        print("❌ Erro: A IA não retornou um JSON válido.")
        print("Raw response:", response.text)
        return None

# --- Execução ---
if __name__ == "__main__":
    # Substitua pelo caminho real do seu arquivo
    caminho_arquivo = "Dez2025.pdf" 
    
    if os.path.exists(caminho_arquivo):
        df_resultado = processar_exame_medico(caminho_arquivo)
        
        if df_resultado is not None:
            print("\n📊 Amostra dos Dados Estruturados:")
            print(df_resultado.head(10))
            
            # Salva para uso posterior no Dashboard
            df_resultado.to_csv("dados_exames_estruturados.csv", index=False)
            print("\n💾 Arquivo 'dados_exames_estruturados.csv' salvo com sucesso.")
    else:
        print(f"Arquivo {caminho_arquivo} não encontrado.")