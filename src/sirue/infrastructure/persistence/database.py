"""Configuración de base de datos SQLAlchemy para SIRUE."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


class Database:
    """Gestiona la conexión y sesiones de la base de datos SQLite."""

    def __init__(self, db_url: str = "sqlite:///data/sirue.db") -> None:
        """Inicializa el engine y la fábrica de sesiones.

        Args:
            db_url: URL de conexión a la base de datos.
        """
        self._db_url = db_url
        connect_args: dict = {}

        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            if "///" in db_url and not db_url.startswith("sqlite:///:memory:"):
                db_path = db_url.split("///", 1)[1]
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(db_url, connect_args=connect_args, echo=False)
        self.SessionLocal: sessionmaker[Session] = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def crear_tablas(self) -> None:
        """Crea todas las tablas definidas en los modelos y asegura consistencia de esquema."""
        Base.metadata.create_all(bind=self.engine)
        self._migrar_columnas_si_aplica()

    def _migrar_columnas_si_aplica(self) -> None:
        """Asegura consistencia de esquema en SQLite (roles y activo en usuarios, lat/lon nullable en reportes)."""
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(self.engine)
            if "usuarios" in inspector.get_table_names():
                columnas = [col["name"] for col in inspector.get_columns("usuarios")]
                with self.engine.begin() as conn:
                    if "rol" not in columnas:
                        conn.execute(text("ALTER TABLE usuarios ADD COLUMN rol VARCHAR DEFAULT 'usuario'"))
                    if "password_hash" not in columnas:
                        conn.execute(text("ALTER TABLE usuarios ADD COLUMN password_hash VARCHAR"))
                    if "activo" not in columnas:
                        conn.execute(text("ALTER TABLE usuarios ADD COLUMN activo BOOLEAN NOT NULL DEFAULT 1"))
                    if "telefono" not in columnas:
                        conn.execute(text("ALTER TABLE usuarios ADD COLUMN telefono VARCHAR(30) DEFAULT ''"))

            if "reportes" in inspector.get_table_names():
                cols_rep = {col["name"]: col for col in inspector.get_columns("reportes")}
                if "latitud" in cols_rep and cols_rep["latitud"].get("nullable") is False:
                    with self.engine.begin() as conn:
                        conn.execute(text("PRAGMA foreign_keys=off;"))
                        conn.execute(text("""
                            CREATE TABLE reportes_temp_migracion (
                                id VARCHAR NOT NULL PRIMARY KEY,
                                tipo VARCHAR NOT NULL,
                                titulo VARCHAR NOT NULL,
                                descripcion TEXT NOT NULL,
                                categoria VARCHAR NOT NULL,
                                latitud FLOAT,
                                longitud FLOAT,
                                referencia_interna VARCHAR NOT NULL,
                                fecha_hora_incidente DATETIME NOT NULL,
                                usuario_id VARCHAR NOT NULL,
                                foto_ruta VARCHAR,
                                palabras_clave TEXT,
                                estado VARCHAR NOT NULL,
                                fecha_creacion DATETIME NOT NULL,
                                FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
                            );
                        """))
                        conn.execute(text("""
                            INSERT INTO reportes_temp_migracion SELECT id, tipo, titulo, descripcion, categoria, latitud, longitud,
                            referencia_interna, fecha_hora_incidente, usuario_id, foto_ruta, palabras_clave, estado, fecha_creacion
                            FROM reportes;
                        """))
                        conn.execute(text("DROP TABLE reportes;"))
                        conn.execute(text("ALTER TABLE reportes_temp_migracion RENAME TO reportes;"))
                        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_reportes_usuario_id ON reportes (usuario_id);"))
                        conn.execute(text("PRAGMA foreign_keys=on;"))
        except Exception:
            pass

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Provee una sesión transaccional con commit/rollback automático.

        Yields:
            Session de SQLAlchemy.
        """
        session: Session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
