"""
Base de dados SQLite para a plataforma de Retail Arbitrage PT
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import sqlite3 as _sq
import os

# Tenta usar a pasta do projeto; se o filesystem não suportar SQLite, usa /tmp
_project_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arbitragem.db")
_tmp_db = "/tmp/arbitragem.db"

def _resolve_db_path():
    path = os.environ.get("ARBITRAGEM_DB_PATH", _project_db)
    try:
        conn = _sq.connect(path)
        conn.execute("CREATE TABLE IF NOT EXISTS _test (x INTEGER)")
        conn.close()
        return path
    except Exception:
        return _tmp_db

DB_PATH = _resolve_db_path()
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(500), nullable=False)
    preco_compra = Column(Float, nullable=False)       # Preço no OLX/Vinted
    preco_venda_est = Column(Float, nullable=True)     # Preço estimado de revenda
    margem_lucro = Column(Float, nullable=True)        # Margem em %
    lucro_abs = Column(Float, nullable=True)           # Lucro absoluto em €
    fonte = Column(String(50), nullable=False)         # "OLX" ou "Vinted"
    categoria = Column(String(100), nullable=True)
    url = Column(Text, nullable=True)
    imagem_url = Column(Text, nullable=True)
    localizacao = Column(String(200), nullable=True)
    estado = Column(String(100), nullable=True)
    data_encontrado = Column(DateTime, default=datetime.utcnow)
    data_atualizado = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Cria as tabelas se não existirem."""
    Base.metadata.create_all(engine)
    print(f"✅ Base de dados iniciada em: {DB_PATH}")


def get_session():
    return SessionLocal()


if __name__ == "__main__":
    init_db()
