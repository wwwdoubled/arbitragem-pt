#!/bin/bash
# ═══════════════════════════════════════════════════
#  push_to_github.sh — Arbitragem PT → GitHub
#  Duplo-clique para correr, ou: bash push_to_github.sh
# ═══════════════════════════════════════════════════

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo ""
echo "═══════════════════════════════════════════════"
echo "  💰 Arbitragem PT — Push para GitHub"
echo "═══════════════════════════════════════════════"
echo ""

# ── 1. Instala Homebrew se não existir ──────────────
if ! command -v brew &>/dev/null; then
  echo "📦 A instalar Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "✅ Homebrew já instalado"
fi

# ── 2. Instala GitHub CLI se não existir ────────────
if ! command -v gh &>/dev/null; then
  echo "📦 A instalar GitHub CLI..."
  brew install gh
else
  echo "✅ GitHub CLI já instalado"
fi

# ── 3. Autentica no GitHub ───────────────────────────
if ! gh auth status &>/dev/null; then
  echo ""
  echo "🔑 Precisas de autenticar no GitHub."
  echo "   Vai abrir o browser para login..."
  echo ""
  gh auth login --web -h github.com
else
  echo "✅ GitHub CLI já autenticado"
fi

# ── 4. Inicializa git ────────────────────────────────
if [ ! -d ".git" ]; then
  echo ""
  echo "🗂  A inicializar repositório git..."
  git init
  git branch -m main
else
  echo "✅ Repositório git já existe"
fi

git config user.email "davidjeee@gmail.com"
git config user.name "David Dinis"

# Remove lock files deixados por processos anteriores
rm -f .git/index.lock .git/HEAD.lock .git/refs/heads/main.lock 2>/dev/null

# ── 5. Faz commit inicial ────────────────────────────
git add .
if git diff --cached --quiet; then
  echo "✅ Nada para commitar (já está tudo feito)"
else
  echo ""
  echo "📝 A fazer commit..."
  git commit -m "🚀 Initial commit — Plataforma de Arbitragem PT

- SQLite DB com SQLAlchemy
- Scraper OLX Portugal (6 categorias)
- Scraper Vinted Portugal (7 categorias)
- Dashboard Streamlit com KPIs, tabela e gráficos
- main.py com modo demo, one-shot e loop automático"
fi

# ── 6. Cria o repo no GitHub e faz push ─────────────
echo ""
echo "🚀 A criar repositório no GitHub e a fazer push..."
gh repo create arbitragem-pt \
  --public \
  --description "🛒 Retail Arbitrage Portugal — OLX & Vinted scraper + Streamlit dashboard" \
  --push \
  --source=. 2>/dev/null || {
    # Se o repo já existe, só faz push
    echo "   (repo já existe — a fazer push...)"
    git remote add origin "https://github.com/$(gh api user --jq .login)/arbitragem-pt.git" 2>/dev/null || true
    # Detecta nome do branch atual e faz push
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    git push -u origin "$BRANCH"
  }

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ Projeto no GitHub com sucesso!"
REPO_URL="https://github.com/$(gh api user --jq .login)/arbitragem-pt"
echo "  🔗 $REPO_URL"
echo "═══════════════════════════════════════════════"
echo ""
open "$REPO_URL"
