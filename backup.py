"""Backup dos dados do DataStudy.

Copia a pasta `data/` para `backups/backup_AAAA-MM-DD_HH-MM-SS/`.
Rode manualmente ou agende no Agendador de Tarefas do Windows.

Uso:
    python backup.py
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATA_DIR = RAIZ / "data"
BACKUP_DIR = RAIZ / "backups"


def fazer_backup() -> Path:
    if not DATA_DIR.exists() or not any(DATA_DIR.iterdir()):
        print("⚠️  Pasta data/ está vazia ou não existe. Nada para fazer backup.")
        raise SystemExit(1)

    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destino = BACKUP_DIR / f"backup_{agora}"
    shutil.copytree(DATA_DIR, destino)

    # Limpa backups antigos (mantém os 10 mais recentes)
    backups = sorted(BACKUP_DIR.iterdir(), reverse=True)
    for antigo in backups[10:]:
        shutil.rmtree(antigo)
        print(f"🗑️  Backup antigo removido: {antigo.name}")

    print(f"✅ Backup salvo em: {destino}")
    print(f"   Arquivos copiados: {len(list(destino.iterdir()))}")
    return destino


if __name__ == "__main__":
    fazer_backup()
