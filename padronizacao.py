"""
Padronização determinística dos nomes e unidades dos exames.

Cada laboratório escreve o mesmo exame de um jeito ("TGO", "TGO (AST)",
"Transaminase Oxalacética (TGO/AST)"...). O prompt já pede padronização,
mas o modelo só enxerga um PDF por vez — então a unificação final é feita
aqui, com um dicionário fixo, para o dashboard conseguir comparar o mesmo
exame ao longo do tempo.

Uso avulso (corrige um CSV já gerado, sem chamar a API de novo):
    python padronizacao.py
"""
import re
import sys
import unicodedata
import pandas as pd


def _chave(nome):
    """Normaliza para comparação: minúsculo, sem acento, sem pontos, espaços simples."""
    s = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    s = s.lower().replace(".", "")
    return re.sub(r"\s+", " ", s).strip()


# chave normalizada -> nome padrão
_SINONIMOS = {
    "Hemoglobina glicada (HbA1c)": [
        "hemoglobina glicada", "hemoglobina glicada (a1c)", "hemoglobina glicada (hba1c)",
    ],
    "Glicemia média estimada": ["glicemia media estimada", "glicose media estimada"],
    "Glicose em jejum": ["glicose", "glicose em jejum", "glicose jejum", "glicemia", "glicemia, dosagem"],
    "Vitamina D (25-OH)": [
        "vitamina d - 25 oh", "vitamina d - 25(oh)", "vitamina d - 25 hidroxi", "vitamina d (25-oh)",
    ],
    "TGO (AST)": ["tgo", "tgo (ast)", "transaminase oxalacetica (tgo/ast)"],
    "TGP (ALT)": ["tgp", "tgp (alt)", "transaminase piruvica (tgp/alt)"],
    "Ureia": ["ureia"],
    "Colesterol total": ["colesterol total"],
    "TFG estimada (CKD-EPI)": [
        "taxa de filtracao glomerular estimada (ckd-epi)", "etfg (ckd-epi) - nao negro",
        "tfg estimada (ckd-epi)",
    ],
    "Hemácias": ["hemacias", "eritrocitos"],
    "VCM": ["vcm", "volume corpuscular medio (vcm)"],
    "HCM": ["hcm", "hgb corpuscular media (hcm)"],
    "CHCM": ["chcm", "concentracao de hgb corpuscular media (chcm)"],
    "RDW": ["rdw"],
}
MAPA_NOMES = {_chave(s): padrao for padrao, lista in _SINONIMOS.items() for s in lista}

# Diferencial do leucograma: alguns laboratórios reportam em %, outros em
# valor absoluto (/mm³). São grandezas diferentes, então viram exames
# separados — "Segmentados (%)" e "Segmentados (/mm³)" — em vez de
# misturar 37% com 2450/mm³ no mesmo gráfico.
_DIFERENCIAL = {
    "bastonetes": "Bastonetes", "bastoes": "Bastonetes",
    "segmentados": "Segmentados",
    "eosinofilos": "Eosinófilos",
    "basofilos": "Basófilos",
    "linfocitos": "Linfócitos", "linfocitos tipicos": "Linfócitos",
    "linfocitos atipicos": "Linfócitos atípicos",
    "monocitos": "Monócitos",
}

MAPA_UNIDADES = {
    "/mm3": "/mm³",
    "mil/mm3": "mil/mm³",
    "ml/min/1,73m2": "mL/min/1,73m²",
    "ml/min/1,73m²": "mL/min/1,73m²",
}


def _nome_diferencial(exame, unidade):
    base = re.sub(r"\s*\((absoluto|%|/mm³)\)\s*$", "", _chave(exame))
    if base not in _DIFERENCIAL:
        return None
    sufixo = "%" if str(unidade).strip() == "%" else "/mm³"
    return f"{_DIFERENCIAL[base]} ({sufixo})"


def padronizar(df):
    """Unifica nomes de exames e unidades. Pode ser aplicada várias vezes sem efeito colateral."""
    df = df.copy()

    df["unidade"] = df["unidade"].map(
        lambda u: MAPA_UNIDADES.get(str(u).strip().lower(), u) if pd.notna(u) else u
    )

    def nome(row):
        dif = _nome_diferencial(row["exame"], row["unidade"])
        return dif or MAPA_NOMES.get(_chave(row["exame"]), row["exame"])

    df["exame"] = df.apply(nome, axis=1)

    # Plaquetas: alguns laudos trazem 145000 /mm³, outros 145 mil/mm³.
    # Converte tudo para mil/mm³.
    valor = pd.to_numeric(df["valor"], errors="coerce")
    plaq_abs = (df["exame"] == "Plaquetas") & (df["unidade"] == "/mm³") & (valor > 1000)
    df.loc[plaq_abs, "valor"] = valor[plaq_abs] / 1000
    df.loc[plaq_abs, "unidade"] = "mil/mm³"

    return df


if __name__ == "__main__":
    arquivo = sys.argv[1] if len(sys.argv) > 1 else "resultadosPadronizados.csv"
    df = pd.read_csv(arquivo)
    antes = df["exame"].nunique()
    df = padronizar(df)
    df.to_csv(arquivo, index=False)
    print(f"✅ {arquivo} padronizado: {antes} → {df['exame'].nunique()} nomes de exame distintos.")
