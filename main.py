"""
main.py — Orquestrador da Plataforma de Arbitragem PT
======================================================
Executa os scrapers do OLX e Vinted e atualiza a base de dados.
Pode correr uma vez ou em modo de agendamento contínuo.

Uso:
    python main.py              # corre uma vez
    python main.py --loop       # corre a cada INTERVALO_MINUTOS
    python main.py --demo       # insere dados de demo e sai
"""
import sys
import os
import time
import argparse
from datetime import datetime

# Garante que o root do projeto está no path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from database.models import init_db, get_session, Produto

# ── Configuração ────────────────────────────────────────────────────────────
INTERVALO_MINUTOS = 60   # Intervalo entre scrapes em modo --loop
LIMITE_POR_PESQUISA = 20  # Nº de resultados por pesquisa


def banner():
    print("\n" + "═" * 55)
    print("  💰  Arbitragem PT  |  Retail Arbitrage Portugal")
    print("═" * 55)
    print(f"  🕐  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 55 + "\n")


def correr_scrapers():
    """Executa ambos os scrapers e devolve o total de novos produtos."""
    total = 0

    # ── OLX ──────────────────────────────────────────────────────────────
    print("🏪 A correr scraper OLX...")
    try:
        from scrapers.olx_scraper import run as olx_run
        n = olx_run(LIMITE_POR_PESQUISA)
        total += n
    except Exception as e:
        print(f"  ❌ Erro no scraper OLX: {e}")

    print()

    # ── Vinted ───────────────────────────────────────────────────────────
    print("👗 A correr scraper Vinted...")
    try:
        from scrapers.vinted_scraper import run as vinted_run
        n = vinted_run(LIMITE_POR_PESQUISA)
        total += n
    except Exception as e:
        print(f"  ❌ Erro no scraper Vinted: {e}")

    return total


def estatisticas():
    """Mostra estatísticas rápidas da base de dados."""
    session = get_session()
    try:
        total = session.query(Produto).count()
        olx = session.query(Produto).filter_by(fonte="OLX").count()
        vinted = session.query(Produto).filter_by(fonte="Vinted").count()

        # Melhor oportunidade
        melhor = (
            session.query(Produto)
            .order_by(Produto.lucro_abs.desc())
            .first()
        )

        print("\n📊 Base de dados:")
        print(f"   Total de produtos : {total}")
        print(f"   OLX               : {olx}")
        print(f"   Vinted            : {vinted}")
        if melhor:
            print(f"\n🏆 Melhor oportunidade:")
            print(f"   {melhor.titulo[:50]}")
            print(f"   Compra: {melhor.preco_compra}€ → Venda: {melhor.preco_venda_est}€")
            print(f"   Lucro: {melhor.lucro_abs}€ ({melhor.margem_lucro}%)")
    finally:
        session.close()


def inserir_demo():
    """Insere dados de demonstração para testar o dashboard sem acesso à internet."""
    from datetime import timedelta
    import random

    print("🎭 A inserir dados de demonstração...")
    init_db()
    session = get_session()

    # Limpa dados anteriores de demo
    session.query(Produto).filter(Produto.url.like("https://demo.%")).delete(synchronize_session=False)
    session.commit()

    demo_produtos = [
        # ── OLX ───────────────────────────────────────────────────────────
        {"titulo": "iPhone 13 128GB Preto - Como Novo", "preco_compra": 320.0, "fonte": "OLX", "categoria": "Telemóveis", "localizacao": "Lisboa", "estado": "Bom estado", "url": "https://demo.olx.pt/1"},
        {"titulo": "PlayStation 5 Digital Edition + 2 Jogos", "preco_compra": 350.0, "fonte": "OLX", "categoria": "Videojogos", "localizacao": "Porto", "estado": "Muito bom estado", "url": "https://demo.olx.pt/2"},
        {"titulo": "MacBook Air M1 8GB 256GB Space Grey", "preco_compra": 650.0, "fonte": "OLX", "categoria": "Informática", "localizacao": "Braga", "estado": "Bom estado", "url": "https://demo.olx.pt/3"},
        {"titulo": "Bicicleta Trek Marlin 5 2022 M", "preco_compra": 280.0, "fonte": "OLX", "categoria": "Desporto", "localizacao": "Coimbra", "estado": "Bom estado", "url": "https://demo.olx.pt/4"},
        {"titulo": "Nintendo Switch OLED Branco + 5 Jogos", "preco_compra": 200.0, "fonte": "OLX", "categoria": "Videojogos", "localizacao": "Lisboa", "estado": "Novo", "url": "https://demo.olx.pt/5"},
        {"titulo": "iPad Pro 11 M2 256GB WiFi", "preco_compra": 550.0, "fonte": "OLX", "categoria": "Informática", "localizacao": "Setúbal", "estado": "Muito bom estado", "url": "https://demo.olx.pt/6"},
        {"titulo": "Sony WH-1000XM5 Headphones Black", "preco_compra": 140.0, "fonte": "OLX", "categoria": "Audio", "localizacao": "Faro", "estado": "Bom estado", "url": "https://demo.olx.pt/7"},
        # ── Vinted ────────────────────────────────────────────────────────
        {"titulo": "Nike Air Jordan 1 Retro High OG sz42", "preco_compra": 85.0, "fonte": "Vinted", "categoria": "Sapatilhas", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/1"},
        {"titulo": "Adidas Yeezy 350 V2 Zebra sz43", "preco_compra": 120.0, "fonte": "Vinted", "categoria": "Sapatilhas", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/2"},
        {"titulo": "LEGO Technic Bugatti Chiron 42083 Completo", "preco_compra": 150.0, "fonte": "Vinted", "categoria": "Brinquedos", "localizacao": "", "estado": "Muito bom estado", "url": "https://demo.vinted.pt/3"},
        {"titulo": "Ralph Lauren Polo Shirt L vintage navy", "preco_compra": 18.0, "fonte": "Vinted", "categoria": "Vestuário", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/4"},
        {"titulo": "iPhone 12 Pro 256GB Cinzento Sideral", "preco_compra": 290.0, "fonte": "Vinted", "categoria": "Telemóveis", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/5"},
        {"titulo": "New Balance 550 White Green sz41", "preco_compra": 55.0, "fonte": "Vinted", "categoria": "Sapatilhas", "localizacao": "", "estado": "Bom estado", "url": "https://demo.vinted.pt/6"},
        {"titulo": "Rolex Submariner 116610LN 2019", "preco_compra": 6500.0, "fonte": "OLX", "categoria": "Relógios", "localizacao": "Lisboa", "estado": "Muito bom estado", "url": "https://demo.olx.pt/8"},
    ]

    fator_map = {"OLX": 1.5, "Vinted": 1.6}
    now = datetime.utcnow()
    novos = 0

    for i, p in enumerate(demo_produtos):
        fator = fator_map[p["fonte"]]
        preco_venda = round(p["preco_compra"] * fator, 2)
        lucro = round(preco_venda - p["preco_compra"], 2)
        margem = round(((preco_venda - p["preco_compra"]) / p["preco_compra"]) * 100, 1)

        prod = Produto(
            titulo=p["titulo"],
            preco_compra=p["preco_compra"],
            preco_venda_est=preco_venda,
            lucro_abs=lucro,
            margem_lucro=margem,
            fonte=p["fonte"],
            categoria=p["categoria"],
            url=p["url"],
            imagem_url="",
            localizacao=p["localizacao"],
            estado=p["estado"],
            data_encontrado=now - timedelta(hours=i),
        )
        session.add(prod)
        novos += 1

    session.commit()
    session.close()
    print(f"  ✅ {novos} produtos de demo inseridos com sucesso!")


def main():
    parser = argparse.ArgumentParser(description="Arbitragem PT — Orquestrador")
    parser.add_argument("--loop", action="store_true", help=f"Corre em loop a cada {INTERVALO_MINUTOS} min")
    parser.add_argument("--demo", action="store_true", help="Insere dados de demo e sai")
    args = parser.parse_args()

    banner()
    init_db()

    if args.demo:
        inserir_demo()
        estatisticas()
        print(f"\n🚀 Para ver o dashboard, corre:\n   streamlit run app/dashboard.py\n")
        return

    if args.loop:
        print(f"⏰ Modo contínuo: scrape a cada {INTERVALO_MINUTOS} minutos\n")
        while True:
            try:
                novos = correr_scrapers()
                estatisticas()
                print(f"\n⏳ Aguarda {INTERVALO_MINUTOS} min para próximo scrape...\n")
                time.sleep(INTERVALO_MINUTOS * 60)
            except KeyboardInterrupt:
                print("\n\n🛑 Parado pelo utilizador.")
                break
    else:
        novos = correr_scrapers()
        estatisticas()
        print(f"\n✅ Concluído: {novos} produtos novos adicionados.")
        print(f"🚀 Para ver o dashboard:\n   streamlit run app/dashboard.py\n")


if __name__ == "__main__":
    main()
