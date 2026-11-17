"""Procedimiento autorizado de siembra (seeding) de usuarios institucionales UAB."""

from __future__ import annotations

from sirue.application.services.password_hasher import PasswordHasher
from sirue.domain.entities.usuario import RolUsuario, Usuario
from sirue.infrastructure.container import Container
from sirue.infrastructure.persistence.models.usuario_model import UsuarioModel


def sembrar_usuarios_autorizados(container: Container) -> None:
    """Siembra y asegura la existencia de usuarios iniciales autorizados para la UAB.

    Garantiza que existan cuentas institucionales válidas:
    - Administrador: administrador@uab.edu.bo (clave: admin123)
    - Estudiante:   estudiante@uab.edu.bo    (clave: password123)

    Además, realiza limpieza de cuentas heredadas de demostración no pertenecientes a @uab.edu.bo.
    """
    with container.database.get_session() as session:
        # 1. Limpieza de usuarios demo obsoletos que no pertenezcan al dominio institucional
        cuentas_obsoletas = ["admin@campus.edu", "carlos@campus.edu", "ana@campus.edu"]
        for email_obsoleto in cuentas_obsoletas:
            u_antiguo = session.query(UsuarioModel).filter_by(email=email_obsoleto).first()
            if u_antiguo:
                session.delete(u_antiguo)
        session.commit()

        # 2. Sembrar o actualizar administrador autorizado institucional
        u_repo = container.usuario_repository(session)
        admin = u_repo.obtener_por_email("administrador@uab.edu.bo")
        if not admin:
            admin = Usuario(
                id="usr-admin-uab-001",
                nombre="Administrador Campus UAB",
                email="administrador@uab.edu.bo",
                telefono="70000000",
                rol=RolUsuario.ADMIN,
                password_hash=PasswordHasher.hashear_password("admin123"),
            )
            u_repo.guardar(admin)
            session.commit()
        elif not admin.es_admin() or not admin.password_hash:
            admin.rol = RolUsuario.ADMIN
            if not admin.password_hash:
                admin.password_hash = PasswordHasher.hashear_password("admin123")
            u_repo.actualizar(admin)
            session.commit()

        # 3. Sembrar o actualizar estudiante institucional
        estudiante = u_repo.obtener_por_email("estudiante@uab.edu.bo")
        if not estudiante:
            estudiante = Usuario(
                id="usr-estudiante-uab-002",
                nombre="Estudiante UAB",
                email="estudiante@uab.edu.bo",
                telefono="71112233",
                rol=RolUsuario.USUARIO,
                password_hash=PasswordHasher.hashear_password("password123"),
            )
            u_repo.guardar(estudiante)
            session.commit()
        elif not estudiante.password_hash:
            estudiante.password_hash = PasswordHasher.hashear_password("password123")
            u_repo.actualizar(estudiante)
            session.commit()
