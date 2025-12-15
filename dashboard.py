import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
        df = pd.read_csv("dados_exames_estruturados.csv")
        
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
    st.error("❌ Arquivo 'dados_exames_estruturados.csv' não encontrado. Rode o 'main.py' primeiro!")
    st.stop()

# --- Sidebar (Barra Lateral de Filtros) ---
st.sidebar.header("🔍 Filtros")

# 1. Filtro de Categoria (Opcional, se sua IA extraiu isso)
if 'categoria' in df.columns:
    categorias = df['categoria'].unique()
    cat_selecionada = st.sidebar.selectbox("Categoria", options=['Todas'] + list(categorias))
    if cat_selecionada != 'Todas':
        df = df[df['categoria'] == cat_selecionada]

# 2. Filtro de Exame (Obrigatório)
# Lista apenas exames disponíveis após o filtro de categoria
lista_exames = df['exame'].unique()
exame_selecionado = st.sidebar.selectbox("Selecione o Exame", lista_exames)

# Filtragem final
df_exame = df[df['exame'] == exame_selecionado]

# --- Área Visual (Main) ---

# Métricas no topo (KPIs)
col1, col2, col3 = st.columns(3)
ultimo_resultado = df_exame.iloc[-1] # Pega o último registro cronológico

with col1:
    st.metric(
        label="Último Resultado",
        value=f"{ultimo_resultado['valor']} {ultimo_resultado['unidade']}",
        delta="Atualizado em " + ultimo_resultado['data'].strftime('%d/%m/%Y')
    )

with col2:
    # Mostra a referência para comparação rápida
    st.info(f"**Referência:**\n{ultimo_resultado['referencia']}")

# --- Gráfico de Evolução (Plotly) ---
st.subheader(f"📈 Evolução: {exame_selecionado}")

if len(df_exame) > 1:
    fig = px.line(
        df_exame, 
        x='data', 
        y='valor',
        markers=True, # Bolinhas nos pontos
        text='valor', # Mostra o valor no gráfico
        template="plotly_white"
    )
    
    # Personalização fina (Professor gosta de clareza)
    fig.update_traces(textposition="bottom right", line_color='#2E8B57') # Verde médico
    fig.update_layout(xaxis_title="Data da Coleta", yaxis_title=f"Valor ({ultimo_resultado['unidade']})")
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Você precisa de pelo menos 2 exames históricos para gerar um gráfico de evolução.")

# --- Tabela de Dados Detalhada ---
st.markdown("### 📋 Histórico Detalhado")
st.dataframe(
    df_exame[['data', 'valor', 'unidade', 'referencia', 'arquivo_origem']].style.format({
        'valor': '{:.2f}',
        'data': lambda t: t.strftime("%d/%m/%Y") # Formatação bonita da data
    }),
    use_container_width=True
)