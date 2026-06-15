"""
Dashboard de Retail Arbitrage Portugal — Streamlit
"""
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import init_db, get_session, Produto


def _seed_demo_se_vazio():
    """Insere dados de demo se a BD estiver vazia (ex: Streamlit Cloud)."""
    session = get_session()
    try:
        if session.query(Produto).count() == 0:
            demo = [
                {"titulo": "iPhone 13 128GB Preto - Como Novo", "preco_compra": 320.0, "fonte": "OLX", "categoria": "Telemóveis", "localizacao": "Lisboa", "estado": "Bom estado", "url": "https://demo.olx.pt/1"},
                {"titulo": "PlayStation 5 Digital Edition + 2 Jogos", "preco_compra": 350.0, "fonte": "OLX", "categoria": "Videojogos", "localizacao": "Porto", "estado": "Muito bom estado", "url": "https://demo.olx.pt/2"},
                {"titulo": "MacBook Air M1 8GB 256GB Space Grey", "preco_compra": 650.0, "fonte": "OLX", "categoria": "Informática", "localizacao": "Braga", "estado": "Bom estado", "url": "https://demo.olx.pt/3"},
                {"titulo": "Nintendo Switch OLED Branco + 5 Jogos", "preco_compra": 200.0, "fonte": "OLX", "categoria": "Videojogos", "localizacao": "Lisboa", "estado": "Novo", "url": "https://demo.olx.pt/4"},
                {"titulo": "iPad Pro 11 M2 256GB WiFi", "preco_compra": 550.0, "fonte": "OLX", "categoria": "Informática", "localizacao": "Setúbal", "estado": "Muito bom estado", "url": "https://demo.olx.pt/5"},
                {"titulo": "Sony WH-1000XM5 Headphones Black", "preco_compra": 140.0, "fonte": "OLX", "categoria": "Audio", "localizacao": "Faro", "estado": "Bom estado", "url": "https://demo.olx.pt/6"},
                {"titulo": "Rolex Submariner 116610LN 2019", "preco_compra": 6500.0, "fonte": "OLX", "categoria": "Relógios", "localizacao": "Lisboa", "estado": "Muito bom estado", "url": "https://demo.olx.pt/7"},
                {"titulo": "Nike Air Jordan 1 Retro High OG sz42", "preco_compra": 85.0, "fonte": "Vinted", "categoria": "Sapatilhas", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/1"},
                {"titulo": "Adidas Yeezy 350 V2 Zebra sz43", "preco_compra": 120.0, "fonte": "Vinted", "categoria": "Sapatilhas", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/2"},
                {"titulo": "LEGO Technic Bugatti Chiron 42083", "preco_compra": 150.0, "fonte": "Vinted", "categoria": "Brinquedos", "localizacao": "", "estado": "Muito bom estado", "url": "https://demo.vinted.pt/3"},
                {"titulo": "Ralph Lauren Polo Shirt L vintage navy", "preco_compra": 18.0, "fonte": "Vinted", "categoria": "Vestuário", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/4"},
                {"titulo": "iPhone 12 Pro 256GB Cinzento Sideral", "preco_compra": 290.0, "fonte": "Vinted", "categoria": "Telemóveis", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/5"},
                {"titulo": "New Balance 550 White Green sz41", "preco_compra": 55.0, "fonte": "Vinted", "categoria": "Sapatilhas", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/6"},
                {"titulo": "Nintendo Switch OLED - Vinted", "preco_compra": 185.0, "fonte": "Vinted", "categoria": "Videojogos", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/7"},
            ]
            now = datetime.utcnow()
            fator = {"OLX": 1.5, "Vinted": 1.6}
            for p in demo:
                f = fator[p["fonte"]]
                pv = round(p["preco_compra"] * f, 2)
                session.add(Produto(
                    titulo=p["titulo"], preco_compra=p["preco_compra"],
                    preco_venda_est=pv, lucro_abs=round(pv - p["preco_compra"], 2),
                    margem_lucro=round((pv - p["preco_compra"]) / p["preco_compra"] * 100, 1),
                    fonte=p["fonte"], categoria=p["categoria"], url=p["url"],
                    imagem_url="", localizacao=p["localizacao"], estado=p["estado"],
                    data_encontrado=now,
                ))
            session.commit()
    finally:
        session.close()


# ── Inicialização ────────────────────────────────────────────────────────────
init_db()
_seed_demo_se_vazio()

# ── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Arbitragem PT",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0.2rem; }
    .sub-header { color: #6b7280; font-size: 1rem; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ── Carregamento de dados ────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def carregar_dados() -> pd.DataFrame:
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
    st.markdown("## 💰 Arbitragem PT")
    st.markdown("### ⚙️ Filtros")

    df_all = carregar_dados()

    fontes_disponiveis = ["Todas"] + sorted(df_all["Fonte"].unique().tolist()) if not df_all.empty else ["Todas"]
    fonte_sel = st.selectbox("Plataforma", fontes_disponiveis)

    cats = ["Todas"] + sorted(df_all["Categoria"].unique().tolist()) if not df_all.empty else ["Todas"]
    cat_sel = st.selectbox("Categoria", cats)

    margem_min = st.slider("Margem mínima (%)", 0, 200, 30)
    preco_max = st.number_input("Preço max. de compra (€)", min_value=0, max_value=10000, value=1000)

    st.markdown("---")
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("""**💡 Como usar:**
- Filtra por margem mínima para ver as melhores oportunidades
- Clica no link para abrir o anúncio diretamente
- Executa `main.py` para atualizar os dados
""")


# ── Cabeçalho ────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">💰 Arbitragem PT</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Oportunidades de Retail Arbitrage no OLX e Vinted Portugal</div>', unsafe_allow_html=True)

# ── Filtros ───────────────────────────────────────────────────────────────────
df = df_all.copy()
if not df.empty:
    if fonte_sel != "Todas":
        df = df[df["Fonte"] == fonte_sel]
    if cat_sel != "Todas":
        df = df[df["Categoria"] == cat_sel]
    df = df[df["Margem (%)"] >= margem_min]
    df = df[df["Preço Compra (€)"] <= preco_max]
    df = df.sort_values("Lucro (€)", ascending=False)

# ── KPIs ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("📦 Produtos", len(df))
with col2:
    st.metric("💶 Lucro Potencial", f"{df['Lucro (€)'].sum():,.0f}€" if not df.empty else "0€")
with col3:
    st.metric("📈 Margem Média", f"{df['Margem (%)'].mean():.1f}%" if not df.empty else "0%")
with col4:
    st.metric("🏆 Melhor Oportunidade", f"{df['Lucro (€)'].max():,.0f}€" if not df.empty else "0€")
with col5:
    n_olx = len(df[df["Fonte"] == "OLX"]) if not df.empty else 0
    n_vinted = len(df[df["Fonte"] == "Vinted"]) if not df.empty else 0
    st.metric("🛒 OLX / Vinted", f"{n_olx} / {n_vinted}")

st.markdown("---")

# ── Tabela ────────────────────────────────────────────────────────────────────
st.subheader("📋 Oportunidades Encontradas")

if df.empty:
    st.info("Nenhum produto encontrado com os filtros selecionados.")
else:
    df_display = df[["Fonte", "Categoria", "Título", "Preço Compra (€)", "Preço Venda Est. (€)", "Lucro (€)", "Margem (%)", "Estado", "Localização", "URL"]].copy()

    def cor_margem(val):
        if val >= 100:
            return "background-color: #d4edda; color: #155724; font-weight: bold"
        elif val >= 50:
            return "background-color: #fff3cd; color: #856404; font-weight: bold"
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
        top10 = df.nlargest(10, "Lucro (€)")[["Título", "Lucro (€)"]].copy()
        top10["Título"] = top10["Título"].str[:35] + "..."
        st.bar_chart(top10.set_index("Título")["Lucro (€)"])
    with col_g2:
        st.markdown("**Lucro por Categoria**")
        st.bar_chart(df.groupby("Categoria")["Lucro (€)"].sum().sort_values(ascending=False))

    col_g3, col_g4 = st.columns(2)
    with col_g3:
        st.markdown("**Produtos por Fonte**")
        st.bar_chart(df["Fonte"].value_counts())
    with col_g4:
        st.markdown("**Distribuição de Margem (%)**")
        st.bar_chart(df["Margem (%)"].value_counts().sort_index())

st.markdown("---")
st.markdown("<div style='text-align:center;color:#9ca3af;font-size:0.8rem;'>Arbitragem PT · Os preços de venda são estimativas · Valida sempre o preço real antes de comprar.</div>", unsafe_allow_html=True)
