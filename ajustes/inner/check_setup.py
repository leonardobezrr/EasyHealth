"""
Diagnóstico rápido: confirma que a ANTHROPIC_API_KEY está configurada
corretamente e lista os modelos disponíveis pra essa conta.

IMPORTANTE: a chave é lida SEMPRE de variável de ambiente (.env), nunca
escrita direto no código — evita repetir o problema do check.models.py
antigo, que tinha uma chave exposta direto no arquivo.
"""
import os
import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("❌ ERRO: ANTHROPIC_API_KEY não encontrada no .env")

client = anthropic.Anthropic(api_key=api_key)

print("🔍 Listando modelos disponíveis para sua chave API...")
try:
    for m in client.models.list():
        print(f"✅ Disponível: {m.id}")
except Exception as e:
    print(f"❌ Erro ao listar modelos: {e}")
