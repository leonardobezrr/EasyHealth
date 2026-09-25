"""
Diagnóstico rápido: confirma que a OPENAI_API_KEY está configurada
corretamente e lista os modelos disponíveis pra essa conta.

IMPORTANTE: a chave é lida SEMPRE de variável de ambiente (.env), nunca
escrita direto no código — evita repetir o problema do check.models.py
antigo, que tinha uma chave exposta direto no arquivo.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ ERRO: OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=api_key)

print(f"⚙️ Modelo configurado: {os.getenv('OPENAI_MODEL', 'gpt-6-astra')}")
print("🔍 Listando modelos disponíveis para sua chave API...")
try:
    for m in sorted(client.models.list(), key=lambda m: m.id):
        print(f"✅ Disponível: {m.id}")
except Exception as e:
    print(f"❌ Erro ao listar modelos: {e}")
