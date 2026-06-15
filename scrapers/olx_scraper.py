"""
Scraper para OLX Portugal — usa a API interna do OLX.
Procura por categorias e guarda os resultados na BD.
"""
import requests
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import init_db, get_session, Produto

# ── Configuração ────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "pt-PT,pt;q=0.9",
}

# Multiplicador de margem: preço de venda estimado = preço_compra * MARGEM_FACTOR
# Baseia-se em produtos OLX tipicamente vendidos 40% abaixo do valor de mercado
MARGEM_FACTOR = 1.5

# Categorias e termos de pesquisa a monitorizar
PESQUISAS = [
    {"keyword": "iphone", "categoria": "Telemóveis"},
    {"keyword": "playstation", "categoria": "Videojogos"},
    {"keyword": "bicicleta", "categoria": "Desporto"},
    {"keyword": "macbook", "categoria": "Informática"},
    {"keyword": "consola nintendo", "categoria": "Videojogos"},
    {"keyword": "rolex", "categoria": "Relógios"},
]

OLX_API = "https://www.olx.pt/api/v1/offers/"


def _preco_venda_estimado(preco_compra: float) -> float:
    """Preço de venda estimado com base no múltiplo de mercado."""
    return round(preco_compra * MARGEM_FACTOR, 2)


def _calcular_margem(preco_compra: float, preco_venda: float) -> float:
    if preco_compra <= 0:
        return 0.0
    return round(((preco_venda - preco_compra) / preco_compra) * 100, 1)


def scrape_olx(keyword: str, categoria: str, limite: int = 20) -> list[dict]:
    """Faz a pesquisa no OLX e devolve lista de produtos."""
    params = {
        "offset": 0,
        "limit": limite,
        "query": keyword,
        "currency": "EUR",
        "sort_by": "created_at:desc",
    }
    try:
        r = requests.get(OLX_API, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ⚠️  OLX [{keyword}]: {e}")
        return []

    produtos = []
    for item in data.get("data", []):
        try:
            titulo = item.get("title", "").strip()
            params_item = {p["key"]: p.get("value", {}).get("label", "") for p in item.get("params", [])}
            preco_raw = item.get("price", {}).get("value", {}).get("value")
            if not preco_raw:
                continue
            preco_compra = float(preco_raw)
            if preco_compra <= 0:
                continue

            preco_venda = _preco_venda_estimado(preco_compra)
            margem = _calcular_margem(preco_compra, preco_venda)
            lucro = round(preco_venda - preco_compra, 2)

            url = item.get("url", "")
            imagem = ""
            fotos = item.get("photos", [])
            if fotos:
                imagem = fotos[0].get("link", "").replace("{width}", "400").replace("{height}", "300")

            localizacao = item.get("location", {}).get("city", {}).get("name", "")
            estado = params_item.get("state", "")

            produtos.append({
                "titulo": titulo,
                "preco_compra": preco_compra,
                "preco_venda_est": preco_venda,
                "margem_lucro": margem,
                "lucro_abs": lucro,
                "fonte": "OLX",
                "categoria": categoria,
                "url": url,
                "imagem_url": imagem,
                "localizacao": localizacao,
                "estado": estado,
            })
        except Exception:
            continue

    return produtos


def guardar_produtos(produtos: list[dict]):
    """Guarda produtos na base de dados (ignora duplicados por URL)."""
    if not produtos:
        return 0

    session = get_session()
    novos = 0
    try:
        for p in produtos:
            # Verifica duplicado pela URL
            if p.get("url"):
                existe = session.query(Produto).filter_by(url=p["url"]).first()
                if existe:
                    continue
            prod = Produto(**p)
            session.add(prod)
            novos += 1
        session.commit()
    finally:
        session.close()
    return novos


def run(limite_por_pesquisa: int = 20):
    """Ponto de entrada principal do scraper OLX."""
    init_db()
    total = 0
    for pesquisa in PESQUISAS:
        kw = pesquisa["keyword"]
        cat = pesquisa["categoria"]
        print(f"  🔍 OLX: pesquisando '{kw}'...")
        produtos = scrape_olx(kw, cat, limite_por_pesquisa)
        novos = guardar_produtos(produtos)
        total += novos
        print(f"      → {len(produtos)} encontrados, {novos} novos guardados")
        time.sleep(1)  # respeita o rate limit
    print(f"\n✅ OLX concluído: {total} produtos novos no total")
    return total


if __name__ == "__main__":
    run()
