"""
Scraper para Vinted Portugal — usa a API pública do Vinted.
Procura artigos baratos com alto potencial de revenda.
"""
import requests
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import init_db, get_session, Produto

# ── Configuração ────────────────────────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-PT,pt;q=0.9",
    "Referer": "https://www.vinted.pt/",
    "Origin": "https://www.vinted.pt",
})

VINTED_API = "https://www.vinted.pt/api/v2/catalog/items"

# Fator de margem: produtos Vinted tipicamente vendem 60% abaixo do valor de mercado
MARGEM_FACTOR = 1.6

PESQUISAS = [
    {"keyword": "iphone", "categoria": "Telemóveis"},
    {"keyword": "adidas yeezy", "categoria": "Sapatilhas"},
    {"keyword": "nike air jordan", "categoria": "Sapatilhas"},
    {"keyword": "playstation 5", "categoria": "Videojogos"},
    {"keyword": "lego", "categoria": "Brinquedos"},
    {"keyword": "ralph lauren", "categoria": "Vestuário"},
    {"keyword": "nintendo switch", "categoria": "Videojogos"},
]


def _obter_token_csrf() -> str:
    """O Vinted requer um cookie de sessão antes de aceitar chamadas à API."""
    try:
        r = SESSION.get("https://www.vinted.pt/", timeout=10)
        token = r.cookies.get("_vinted_fr_session", "")
        return token
    except Exception:
        return ""


def _preco_venda_estimado(preco_compra: float) -> float:
    return round(preco_compra * MARGEM_FACTOR, 2)


def _calcular_margem(preco_compra: float, preco_venda: float) -> float:
    if preco_compra <= 0:
        return 0.0
    return round(((preco_venda - preco_compra) / preco_compra) * 100, 1)


def scrape_vinted(keyword: str, categoria: str, limite: int = 20) -> list[dict]:
    """Pesquisa no Vinted e devolve lista de produtos."""
    params = {
        "search_text": keyword,
        "per_page": limite,
        "page": 1,
        "order": "newest_first",
    }
    try:
        r = SESSION.get(VINTED_API, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ⚠️  Vinted [{keyword}]: {e}")
        return []

    produtos = []
    items = data.get("items", [])

    for item in items:
        try:
            titulo = item.get("title", "").strip()
            preco_raw = item.get("price", None)
            if preco_raw is None:
                # tenta estrutura alternativa
                preco_raw = item.get("price_numeric", None)
            if preco_raw is None:
                continue
            preco_compra = float(str(preco_raw).replace(",", "."))
            if preco_compra <= 0:
                continue

            preco_venda = _preco_venda_estimado(preco_compra)
            margem = _calcular_margem(preco_compra, preco_venda)
            lucro = round(preco_venda - preco_compra, 2)

            item_id = item.get("id", "")
            url = f"https://www.vinted.pt/items/{item_id}" if item_id else ""

            foto = item.get("photo", {})
            imagem = foto.get("full_size_url", foto.get("url", "")) if foto else ""

            estado_id = item.get("status", "")
            estado_map = {1: "Novo com etiqueta", 2: "Novo sem etiqueta", 3: "Muito bom estado",
                          4: "Bom estado", 5: "Aceitável"}
            estado = estado_map.get(estado_id, str(estado_id))

            produtos.append({
                "titulo": titulo,
                "preco_compra": preco_compra,
                "preco_venda_est": preco_venda,
                "margem_lucro": margem,
                "lucro_abs": lucro,
                "fonte": "Vinted",
                "categoria": categoria,
                "url": url,
                "imagem_url": imagem,
                "localizacao": "",
                "estado": estado,
            })
        except Exception:
            continue

    return produtos


def guardar_produtos(produtos: list[dict]) -> int:
    if not produtos:
        return 0
    session = get_session()
    novos = 0
    try:
        for p in produtos:
            if p.get("url"):
                existe = session.query(Produto).filter_by(url=p["url"]).first()
                if existe:
                    continue
            session.add(Produto(**p))
            novos += 1
        session.commit()
    finally:
        session.close()
    return novos


def run(limite_por_pesquisa: int = 20):
    """Ponto de entrada principal do scraper Vinted."""
    init_db()
    print("  🍪 Vinted: a obter sessão...")
    _obter_token_csrf()
    time.sleep(1)

    total = 0
    for pesquisa in PESQUISAS:
        kw = pesquisa["keyword"]
        cat = pesquisa["categoria"]
        print(f"  🔍 Vinted: pesquisando '{kw}'...")
        produtos = scrape_vinted(kw, cat, limite_por_pesquisa)
        novos = guardar_produtos(produtos)
        total += novos
        print(f"      → {len(produtos)} encontrados, {novos} novos guardados")
        time.sleep(1.5)

    print(f"\n✅ Vinted concluído: {total} produtos novos no total")
    return total


if __name__ == "__main__":
    run()
