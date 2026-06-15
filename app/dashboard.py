"""
Dashboard de Retail Arbitrage Portugal — Streamlit
Mostra produtos encontrados no OLX e Vinted com análise de margem de lucro.
"""
import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import init_db, get_session, Produto

# ── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Arbitragem PT",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1rem;
        color: white;
    }
    .badge-olx {
        background-color: #3d2a8a;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-vinted {
        background-color: #09b1ba;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


# ── Carregamento de dados ────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def carregar_dados() -> pd.DataFrame:
    init_db()
    session = get_session()
    try:
        produtos = session.query(Produto).order_by(Produto.data_encontrado.desc()).all()
        rows = []
        for p in produtos:
            rows.append({
                "ID": p.id,
                "Título": p.titulo,
                "Fonte": p.fonte,
                "Categoria": p.categoria or "—",
                "Preço Compra (€)": p.preco_compra,
                "Preço Venda Est. (€)": p.preco_venda_est or 0,
                "Lucro (€)": p.lucro_abs or 0,
                "Margem (%)": p.margem_lucro or 0,
                "Estado": p.estado or "—",
                "Localização": p.localizacao or "—",
                "URL": p.url or "",
                "Data": p.data_encontrado,
            })
        return pd.DataFrame(rows)
    finally:
        session.close()


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://em-content.zobj.net/source/apple/354/money-bag_1f4b0.png", width=60)
    st.markdown("### ⚙️ Filtros")

    df_all = carregar_dados()

    # Fonte
    fontes_disponiveis = ["Todas"] + sorted(df_all["Fonte"].unique().tolist()) if not df_all.empty else ["Todas"]
    fonte_sel = st.selectbox("Plataforma", fontes_disponiveis)

    # Categoria
    cats = ["Todas"] + sorted(df_all["Categoria"].unique().tolist()) if not df_all.empty else ["Todas"]
    cat_sel = st.selectbox("Categoria", cats)

    # Margem mínima
    margem_min = st.slider("Margem mínima (%)", 0, 200, 30)

    # Preço máximo de compra
    preco_max = st.number_input("Preço max. de compra (€)", min_value=0, max_value=10000, value=1000)

    st.markdown("---")
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("**💡 Como usar:**")
    st.markdown("""
- Filtra por margem mínima para ver as melhores oportunidades
- Clica no link para abrir o anúncio diretamente
- Executa `main.py` para atualizar os dados
""")


# ── Cabeçalho principal ──────────────────────────────────────────────────────
st.markdown('<div class="main-header">💰 Arbitragem PT</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Oportunidades de Retail Arbitrage no OLX e Vinted Portugal</div>',
            unsafe_allow_html=True)

# ── Aplicar filtros ──────────────────────────────────────────────────────────
df = df_all.copy()
if not df.empty:
    if fonte_sel != "Todas":
        df = df[df["Fonte"] == fonte_sel]
    if cat_sel != "Todas":
        df = df[df["Categoria"] == cat_sel]
    df = df[df["Margem (%)"] >= margem_min]
    df = df[df["Preço Compra (€)"] <= preco_max]
    df = df.sort_values("Lucro (€)", ascending=False)


# ── KPIs ─────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📦 Produtos", len(df), help="Total de produtos filtrados")
with col2:
    total_lucro = df["Lucro (€)"].sum() if not df.empty else 0
    st.metric("💶 Lucro Potencial Total", f"{total_lucro:,.0f}€")
with col3:
    media_margem = df["Margem (%)"].mean() if not df.empty else 0
    st.metric("📈 Margem Média", f"{media_margem:.1f}%")
with col4:
    melhor = df["Lucro (€)"].max() if not df.empty else 0
    st.metric("🏆 Melhor Oportunidade", f"{melhor:,.0f}€")
with col5:
    n_olx = len(df[df["Fonte"] == "OLX"]) if not df.empty else 0
    n_vinted = len(df[df["Fonte"] == "Vinted"]) if not df.empty else 0
    st.metric("🛒 OLX / Vinted", f"{n_olx} / {n_vinted}")

st.markdown("---")


# ── Tabela principal ──────────────────────────────────────────────────────────
st.subheader("📋 Oportunidades Encontradas")

if df.empty:
    st.info("Nenhum produto encontrado com os filtros selecionados. Tenta ajustar os filtros ou executa os scrapers.")
else:
    # Formatar tabela para exibição
    df_display = df[[
        "Fonte", "Categoria", "Título", "Preço Compra (€)",
        "Preço Venda Est. (€)", "Lucro (€)", "Margem (%)", "Estado", "Localização", "URL"
    ]].copy()

    # Color coding da margem
    def cor_margem(val):
        if val >= 100:
            return "background-color: #d4edda; color: #155724; font-weight: bold"
        elif val >= 50:
            return "background-color: #fff3cd; color: #856404; font-weight: bold"
        else:
            return "background-color: #f8d7da; color: #721c24"

    styled = df_display.style.format({
        "Preço Compra (€)": "{:.2f}€",
        "Preço Venda Est. (€)": "{:.2f}€",
        "Lucro (€)": "{:.2f}€",
        "Margem (%)": "{:.1f}%",
    }).applymap(cor_margem, subset=["Margem (%)"])

    st.dataframe(styled, use_container_width=True, height=500,
                 column_config={
                     "URL": st.column_config.LinkColumn("🔗 Link", display_text="Abrir"),
                     "Título": st.column_config.TextColumn("Título", width="large"),
                     "Fonte": st.column_config.TextColumn("Fonte", width="small"),
                 })


# ── Gráficos ──────────────────────────────────────────────────────────────────
if not df.empty:
    st.markdown("---")
    st.subheader("📊 Análise Visual")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Top 10 por Lucro (€)**")
        top10 = df.nlargest(10, "Lucro (€)")[["Título", "Lucro (€)", "Fonte"]].copy()
        top10["Título"] = top10["Título"].str[:35] + "..."
        st.bar_chart(top10.set_index("Título")["Lucro (€)"])

    with col_g2:
        st.markdown("**Lucro por Categoria**")
        por_cat = df.groupby("Categoria")["Lucro (€)"].sum().sort_values(ascending=False)
        st.bar_chart(por_cat)

    # Distribuição fonte
    col_g3, col_g4 = st.columns(2)
    with col_g3:
        st.markdown("**Produtos por Fonte**")
        por_fonte = df["Fonte"].value_counts()
        st.bar_chart(por_fonte)

    with col_g4:
        st.markdown("**Distribuição de Margem (%)**")
        st.bar_chart(df["Margem (%)"].value_counts().sort_index())


# ── Rodapé ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#9ca3af;font-size:0.8rem;'>"
    "Arbitragem PT · Os preços de venda são estimativas baseadas em múltiplos de mercado · "
    "Valida sempre o preço real antes de comprar."
    "</div>",
    unsafe_allow_html=True
)
