# 💰 Arbitragem PT — Retail Arbitrage Portugal

Plataforma para encontrar oportunidades de compra e revenda no **OLX** e **Vinted Portugal**.

## Estrutura
```
arbitragem/
├── database/
│   └── models.py          # SQLite com SQLAlchemy
├── scrapers/
│   ├── olx_scraper.py     # Scraper OLX Portugal
│   └── vinted_scraper.py  # Scraper Vinted Portugal
├── app/
│   └── dashboard.py       # Dashboard Streamlit
├── main.py                # Orquestrador principal
└── requirements.txt
```

## Instalação

```bash
cd arbitragem
pip install -r requirements.txt
```

## Utilização

### 1. Inserir dados de demo (sem internet)
```bash
python main.py --demo
```

### 2. Correr scrapers uma vez
```bash
python main.py
```

### 3. Correr scrapers em loop (a cada 60 min)
```bash
python main.py --loop
```

### 4. Ver dashboard
```bash
streamlit run app/dashboard.py
```

## Dashboard
O dashboard mostra:
- 📦 Total de produtos encontrados
- 💶 Lucro potencial total
- 📈 Margem média
- 🏆 Melhor oportunidade
- Tabela filtrada por fonte, categoria, margem e preço
- Gráficos de análise

### Cores da tabela
| Cor | Significado |
|-----|------------|
| 🟢 Verde | Margem ≥ 100% |
| 🟡 Amarelo | Margem 50-99% |
| 🔴 Vermelho | Margem < 50% |

## Notas
- Os **preços de venda são estimativas** (OLX ×1.5, Vinted ×1.6) — valida sempre antes de comprar
- Os scrapers usam a API pública do OLX e Vinted — sujeitos a mudanças nas APIs
- Em caso de bloqueio por rate-limit, aumenta os delays em `PESQUISAS` nos scrapers
