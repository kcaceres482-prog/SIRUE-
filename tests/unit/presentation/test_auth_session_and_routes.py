"""Pruebas unitarias para protección de rutas y gestión de sesión (NiceGUI)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, PropertyMock, patch
import unittest
import uuid

from nicegui import app
from nicegui.storage import Storage

from sirue.application.dtos.usuario_dto import UsuarioOutputDTO
from sirue.domain.entities.reporte_objeto import EstadoReporte, ReporteObjeto, TipoReporte
from sirue.domain.entities.usuario import RolUsuario, Usuario
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus
from sirue.infrastructure.container import Container
from sirue.presentation.auth_session import (
    cerrar_sesion,
    esta_autenticado,
    iniciar_sesion,
    obtener_usuario_actual,
    ruta_protegida,
)
from sirue.presentation.pages.admin import crear_pagina_admin


class TestAuthSessionAndRoutes(unittest.TestCase):
    """Pruebas sobre el ciclo de vida de la sesión, protección y autorización de rutas."""

    def setUp(self) -> None:
        self.container = Container(db_url="sqlite:///:memory:")
        self.container.init()

        # Mock del almacén en memoria para app.storage.user fuera del contexto de servidor web
        self.fake_storage: dict[str, object] = {}
        self.storage_patcher = patch.object(
            Storage,
            "user",
            new_callable=PropertyMock,
            return_value=self.fake_storage,
        )
        self.storage_patcher.start()

        # Crear usuarios institucionales en base de datos en memoria
        with self.container.database.get_session() as s:
            u_repo = self.container.usuario_repository(s)
            self.usuario_std = Usuario(
                id=str(uuid.uuid4()),
                nombre="Estudiante Test",
                email="estudiante@uab.edu.bo",
                rol=RolUsuario.USUARIO,
            )
            self.usuario_admin = Usuario(
                id=str(uuid.uuid4()),
                nombre="Admin Test",
                email="administrador@uab.edu.bo",
                rol=RolUsuario.ADMIN,
            )
            u_repo.guardar(self.usuario_std)
            u_repo.guardar(self.usuario_admin)
            s.commit()

    def tearDown(self) -> None:
        self.storage_patcher.stop()

    # 9. Bloqueo de rutas sin autenticación
    @patch("sirue.presentation.auth_session.ui.navigate.to")
    def test_bloqueo_ruta_sin_autenticacion_redirige_a_login(self, mock_nav: MagicMock) -> None:
        mock_page_func = MagicMock()
        pagina_protegida = ruta_protegida(self.container)(mock_page_func)

        # Sin autenticación previa
        self.assertFalse(esta_autenticado())
        resultado = pagina_protegida()

        # Debe bloquear la ejecución de la página y redirigir a /login
        self.assertIsNone(resultado)
        mock_page_func.assert_not_called()
        mock_nav.assert_called_once_with("/login")

    # 9 & 8. Bloqueo de ruta administrativa para usuario estándar
    @patch("sirue.presentation.auth_session.ui.navigate.to")
    @patch("sirue.presentation.auth_session.ui.notify")
    def test_bloqueo_ruta_admin_para_usuario_estandar(
        self, mock_notify: MagicMock, mock_nav: MagicMock
    ) -> None:
        # Iniciar sesión como usuario estándar
        dto = UsuarioOutputDTO(
            id=self.usuario_std.id,
            nombre=self.usuario_std.nombre,
            email=self.usuario_std.email,
            telefono=None,
            rol="usuario",
            fecha_registro="",
            es_admin=False,
        )
        iniciar_sesion(dto)
        self.assertTrue(esta_autenticado())

        mock_admin_page = MagicMock()
        pagina_admin = ruta_protegida(self.container, solo_admin=True)(mock_admin_page)

        resultado = pagina_admin()

        # Debe denegar el acceso a la vista admin y redirigir a /
        self.assertIsNone(resultado)
        mock_admin_page.assert_not_called()
        mock_notify.assert_called_once()
        mock_nav.assert_called_once_with("/")

    # 8. Acceso permitido para usuario admin en ruta administrativa
    @patch("sirue.presentation.auth_session.ui.navigate.to")
    def test_acceso_permitido_admin_en_ruta_admin(self, mock_nav: MagicMock) -> None:
        dto = UsuarioOutputDTO(
            id=self.usuario_admin.id,
            nombre=self.usuario_admin.nombre,
            email=self.usuario_admin.email,
            telefono=None,
            rol="admin",
            fecha_registro="",
            es_admin=True,
        )
        iniciar_sesion(dto)

        mock_admin_page = MagicMock(return_value="render_admin_ok")
        pagina_admin = ruta_protegida(self.container, solo_admin=True)(mock_admin_page)

        resultado = pagina_admin()
        self.assertEqual(resultado, "render_admin_ok")
        mock_admin_page.assert_called_once()
        mock_nav.assert_not_called()

    # 10. Cierre correcto de sesión
    @patch("sirue.presentation.auth_session.ui.navigate.to")
    @patch("sirue.presentation.auth_session.ui.notify")
    def test_cierre_correcto_de_sesion(
        self, mock_notify: MagicMock, mock_nav: MagicMock
    ) -> None:
        # Iniciar sesión
        dto = UsuarioOutputDTO(
            id=self.usuario_std.id,
            nombre=self.usuario_std.nombre,
            email=self.usuario_std.email,
            telefono=None,
            rol="usuario",
            fecha_registro="",
            es_admin=False,
        )
        iniciar_sesion(dto)
        self.assertTrue(esta_autenticado())
        self.assertIsNotNone(obtener_usuario_actual(self.container))

        # Ejecutar cierre de sesión
        cerrar_sesion()

        # Verificar que la sesión fue completamente purgada
        self.assertFalse(esta_autenticado())
        self.assertIsNone(obtener_usuario_actual(self.container))
        self.assertEqual(len(self.fake_storage), 0)
        mock_notify.assert_called_once()
        mock_nav.assert_called_once_with("/login")

    @patch("sirue.presentation.auth_session.ui.navigate.to")
    def test_usuario_bloqueado_limpia_sesion_y_redirige(self, mock_nav: MagicMock) -> None:
        dto = UsuarioOutputDTO(
            id=self.usuario_std.id,
            nombre=self.usuario_std.nombre,
            email=self.usuario_std.email,
            telefono=None,
            rol="usuario",
            fecha_registro="",
            es_admin=False,
            activo=True,
        )
        iniciar_sesion(dto)
        self.assertTrue(esta_autenticado())

        # Bloquear usuario en base de datos
        with self.container.database.get_session() as s:
            u_repo = self.container.usuario_repository(s)
            u = u_repo.obtener_por_id(self.usuario_std.id)
            self.assertIsNotNone(u)
            u.bloquear()
            u_repo.actualizar(u)
            s.commit()

        # Al verificar la sesión, debe detectar que está inactivo, limpiar y retornar None
        actual = obtener_usuario_actual(self.container)
        self.assertIsNone(actual)
        self.assertEqual(len(self.fake_storage), 0)

        # Si intenta acceder a una ruta protegida, se le redirige a /login
        mock_page = MagicMock()
        pagina_protegida = ruta_protegida(self.container)(mock_page)
        res = pagina_protegida()
        self.assertIsNone(res)
        mock_page.assert_not_called()
        mock_nav.assert_called_once_with("/login")

    def test_renderizado_panel_admin_con_reporte_estado_resuelto_no_falla(self) -> None:
        """Verifica que el panel admin renderiza sin lanzar ValueError ante reportes en estado RESUELTO."""
        with self.container.database.get_session() as s:
            r_repo = self.container.reporte_repository(s)
            rep_resuelto = ReporteObjeto(
                id=str(uuid.uuid4()),
                tipo=TipoReporte.PERDIDO,
                titulo="Laptop devuelta",
                descripcion="Laptop recuperada por su dueño",
                categoria=CategoriaObjeto.LAPTOP,
                ubicacion=UbicacionCampus(referencia_interna="Aula B-101"),
                fecha_hora_incidente=FechaHoraIncidente(datetime.now(timezone.utc)),
                usuario_id=self.usuario_admin.id,
                estado=EstadoReporte.RESUELTO,
            )
            r_repo.guardar(rep_resuelto)
            s.commit()

        # Configurar sesión como admin
        self.fake_storage.clear()
        self.fake_storage.update({
            "autenticado": True,
            "usuario_id": self.usuario_admin.id,
            "es_admin": True,
        })

        # Al invocar crear_pagina_admin no debe lanzarse ValueError por opciones de ui.select
        try:
            crear_pagina_admin(self.container)
        except ValueError as e:
            self.fail(f"crear_pagina_admin lanzó ValueError inesperado: {e}")


if __name__ == "__main__":
    unittest.main()
