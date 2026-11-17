#!/usr/bin/env python3
"""Punto de entrada principal para el Sistema Digital de Objetos Perdidos y Encontrados (SIRUE).

Ejecuta el servidor web y la interfaz responsiva en NiceGUI para la Universidad Adventista de Bolivia (UAB).
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

# Agregar 'src' al path de búsqueda de módulos de Python
current_dir = Path(__file__).parent.resolve()
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Si nicegui no está en el entorno actual pero existe .venv, auto-conmutar a .venv
try:
    from nicegui import ui
except ImportError:
    venv_python = current_dir / ".venv" / "bin" / "python"
    if venv_python.exists() and sys.executable != str(venv_python):
        if sys.argv and any("main.py" in arg for arg in sys.argv):
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    raise

from sirue.infrastructure.container import Container
from sirue.infrastructure.seeding import sembrar_usuarios_autorizados
from sirue.presentation.app import crear_app


def main() -> None:
    """Función de arranque e inicialización del sistema SIRUE."""
    host = os.environ.get("SIRUE_HOST", "0.0.0.0")
    port = int(os.environ.get("SIRUE_PORT", "8080"))
    db_path = os.environ.get("SIRUE_DB_PATH", "data/sirue.db")
    upload_path = os.environ.get("SIRUE_UPLOAD_PATH", "uploads")

    print("=" * 60)
    print("   S I R U E — Universidad Adventista de Bolivia (UAB)")
    print("   Sistema Digital de Objetos Perdidos y Encontrados")
    print("   Arquitectura Limpia & DDD — Entorno Universitario")
    print("=" * 60)
    print(f"[*] Base de datos SQLite: {db_path}")
    print(f"[*] Carpeta de subidas:   {upload_path}")
    print(f"[*] Servidor web NiceGUI: http://{host}:{port}")
    print("=" * 60)

    # 1. Instanciar e inicializar contenedor de dependencias
    container = Container(
        db_url=f"sqlite:///{db_path}",
        upload_path=upload_path,
    )
    container.init()

    # 2. Siembra autorizada de usuarios institucionales UAB (Admin y Estudiante)
    sembrar_usuarios_autorizados(container)

    # 3. Configurar rutas y páginas de la interfaz de usuario con protección
    crear_app(container)

    # 4. Determinar apertura del navegador y arrancar servidor NiceGUI
    show_browser_env = os.environ.get("SIRUE_SHOW_BROWSER", "auto").lower()
    if show_browser_env in ("0", "false", "no"):
        show = False
    elif show_browser_env in ("1", "true", "yes"):
        show = True
    else:
        # Abrir navegador solo si existe display gráfico activo
        show = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    ui.run(
        host="0.0.0.0",
        port=8080,
        title="SIRUE — Universidad Adventista de Bolivia",
        favicon="🎒",
        storage_secret="sirue_secret_key_campus_educational_2026",
        reload=False,
        show=show,
    )


if __name__ == "__main__":
    main()
