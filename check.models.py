import google.generativeai as genai
import os

# Configure sua chave aqui novamente se não estiver nas variáveis de ambiente
os.environ["GOOGLE_API_KEY"] = "AIzaSyDJfxO7aqkZ4Q_1SoYRuxYC_jn51bHzTnE"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("🔍 Listando modelos disponíveis para sua chave API...")

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Disponível: {m.name}")
except Exception as e:
    print(f"❌ Erro ao listar modelos: {e}")