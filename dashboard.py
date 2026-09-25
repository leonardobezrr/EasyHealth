import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from padronizacao import padronizar

# Configuração da Página (Layout Profissional)
st.set_page_config(
    page_title="EasyHealth Analytics",
    page_icon="🏥",
    layout="wide"
)

# --- Título e Estilo ---
st.title("🏥 EasyHealth: Monitoramento de Exames")
st.markdown("---")

# --- Função de Carregamento (Rigorosa com Datas) ---
@st.cache_data # Cache para não recarregar o CSV a cada clique
def carregar_dados():
    try:
        # Lê o CSV gerado pelo seu script principal
        df = pd.read_csv("resultadosPadronizados.csv")

        # Unifica nomes/unidades (também corrige CSVs gerados antes da padronização)
        df = padronizar(df)
        
        # CONVERSÃO CRÍTICA: Transforma string em data real
        # 'dayfirst=True' é essencial para o formato brasileiro (25/11/2025)
        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        
        # Garante que os valores são números
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        # Remove linhas que falharam na conversão (Lixo de dados)
        df = df.dropna(subset=['data', 'valor'])
        
        return df.sort_values('data')
    except FileNotFoundError:
        return None

# --- Lógica Principal ---
df = carregar_dados()

if df is None:
    st.error("❌ Arquivo 'resultadosPadronizados.csv' não encontrado. Rode o 'main.py' primeiro!")
    st.stop()

# --- Sidebar (Barra Lateral de Filtros) ---
st.sidebar.header("🔍 Filtros")

# 1. Filtro de Categoria (Opcional, se sua IA extraiu isso)
if 'categoria' in df.columns:
    categorias = df['categoria'].unique()
    cat_selecionada = st.sidebar.selectbox("Categoria", options=['Todas'] + list(categorias))
    if cat_selecionada != 'Todas':
        df = df[df['categoria'] == cat_selecionada]

# ... (Código anterior de carregamento e Filtro de Categoria mantém igual) ...

# --- 2. Filtro de Exame (MULTISELECTION) ---
lista_exames = df['exame'].unique()

# Definimos um padrão para não começar vazio (Pega o primeiro da lista)
default_exames = [lista_exames[0]] if len(lista_exames) > 0 else []

exames_selecionados = st.sidebar.multiselect(
    "Selecione os Exames (Comparação)", 
    options=lista_exames,
    default=default_exames
)

# Validação Rigorosa: O usuário pode desmarcar tudo, o que quebraria o gráfico
if not exames_selecionados:
    st.warning("⚠️ Por favor, selecione pelo menos um exame para visualizar.")
    st.stop()

# Filtragem Inteligente (isin)
df_exame = df[df['exame'].isin(exames_selecionados)]

# --- Área Visual (Main) ---

# Nota do Professor: KPIs (Cartões) ficam confusos com múltiplos exames. 
# Vamos focar no Gráfico Comparativo.

st.subheader(f"📈 Comparativo de Evolução")

if len(df_exame) > 0:
    # Gráfico Multilinha
    fig = px.line(
        df_exame, 
        x='data', 
        y='valor',
        color='exame',  # <--- O SEGREDO: Diferencia as linhas por cor
        markers=True,
        text='valor',
        template="plotly_white"
    )
    
    # Personalização para Múltiplas Séries
    fig.update_traces(textposition="top center")
    fig.update_layout(
        xaxis_title="Data da Coleta",
        yaxis_title="Valor Medido",
        legend_title_text='Exames',
        hovermode="x unified" # Mostra todos os valores ao passar o mouse numa data
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Alerta de Escala (Obrigação do Especialista)
    # Verifica se há disparidade grande nos valores (ex: > 1000 de diferença)
    max_val = df_exame['valor'].max()
    min_val = df_exame['valor'].min()
    
    if max_val > (min_val * 10) and min_val > 0:
        st.warning("⚠️ **Atenção à Escala:** Você selecionou exames com valores muito discrepantes. Isso pode distorcer a visualização. Tente comparar exames com unidades similares (ex: mg/dL com mg/dL).")

else:
    st.warning("Sem dados para os filtros selecionados.")

# --- Tabela de Dados (Mantida, mas agora mostra qual exame é qual) ---
st.markdown("### 📋 Dados Brutos")
st.dataframe(
    df_exame[['data', 'exame', 'valor', 'unidade', 'referencia']].sort_values(['exame', 'data']),
    use_container_width=True
)