"""Pruebas unitarias para los Casos de Uso de la capa de aplicación SIRUE."""

from datetime import datetime, timezone
from typing import Optional
import unittest
import uuid

from sirue.application.dtos.reporte_dto import ReporteInputDTO
from sirue.application.services.motor_coincidencias import MotorCoincidencias
from sirue.application.use_cases.procesar_coincidencias import (
    ProcesarCoincidenciasYNotificar,
)
from sirue.application.use_cases.registrar_objeto_encontrado import (
    RegistrarObjetoEncontrado,
)
from sirue.application.use_cases.registrar_objeto_perdido import (
    RegistrarObjetoPerdido,
)
from sirue.domain.entities.coincidencia import Coincidencia, EstadoCoincidencia
from sirue.domain.entities.reporte_objeto import (
    EstadoReporte,
    ReporteObjeto,
    TipoReporte,
)
from sirue.domain.entities.usuario import Usuario
from sirue.domain.exceptions.domain_exceptions import (
    FotoRequeridaError,
    UsuarioNoEncontradoError,
)
from sirue.domain.ports.coincidencia_repository import CoincidenciaRepository
from sirue.domain.ports.foto_storage import FotoStorage
from sirue.domain.ports.notificacion_service import NotificacionService
from sirue.domain.ports.reporte_repository import ReporteRepository
from sirue.domain.ports.usuario_repository import UsuarioRepository


# --- Implementaciones Fake en Memoria para Pruebas Aisladas ---


class FakeUsuarioRepository(UsuarioRepository):
    def __init__(self) -> None:
        self.usuarios: dict[str, Usuario] = {}

    def guardar(self, usuario: Usuario) -> Usuario:
        self.usuarios[usuario.id] = usuario
        return usuario

    def obtener_por_id(self, id: str) -> Optional[Usuario]:
        return self.usuarios.get(id)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        for u in self.usuarios.values():
            if u.email == email.lower().strip():
                return u
        return None

    def listar_todos(self) -> list[Usuario]:
        return list(self.usuarios.values())

    def actualizar(self, usuario: Usuario) -> Usuario:
        self.usuarios[usuario.id] = usuario
        return usuario

    def eliminar(self, id: str) -> bool:
        if id in self.usuarios:
            del self.usuarios[id]
            return True
        return False


class FakeReporteRepository(ReporteRepository):
    def __init__(self) -> None:
        self.reportes: dict[str, ReporteObjeto] = {}

    def guardar(self, reporte: ReporteObjeto) -> ReporteObjeto:
        self.reportes[reporte.id] = reporte
        return reporte

    def obtener_por_id(self, id: str) -> Optional[ReporteObjeto]:
        return self.reportes.get(id)

    def listar_todos(self) -> list[ReporteObjeto]:
        return list(self.reportes.values())

    def listar_por_usuario(self, usuario_id: str) -> list[ReporteObjeto]:
        return [r for r in self.reportes.values() if r.usuario_id == usuario_id]

    def listar_por_tipo(self, tipo: TipoReporte) -> list[ReporteObjeto]:
        return [r for r in self.reportes.values() if r.tipo == tipo]

    def listar_activos(self) -> list[ReporteObjeto]:
        return [r for r in self.reportes.values() if r.esta_activo()]

    def listar_activos_por_tipo(self, tipo: TipoReporte) -> list[ReporteObjeto]:
        return [
            r for r in self.reportes.values() if r.esta_activo() and r.tipo == tipo
        ]

    def listar_por_estado(self, estado: EstadoReporte) -> list[ReporteObjeto]:
        return [r for r in self.reportes.values() if r.estado == estado]

    def actualizar(self, reporte: ReporteObjeto) -> ReporteObjeto:
        self.reportes[reporte.id] = reporte
        return reporte


class FakeCoincidenciaRepository(CoincidenciaRepository):
    def __init__(self) -> None:
        self.coincidencias: dict[str, Coincidencia] = {}

    def guardar(self, coincidencia: Coincidencia) -> Coincidencia:
        self.coincidencias[coincidencia.id] = coincidencia
        return coincidencia

    def obtener_por_id(self, id: str) -> Optional[Coincidencia]:
        return self.coincidencias.get(id)

    def listar_por_reporte(self, reporte_id: str) -> list[Coincidencia]:
        return [
            c
            for c in self.coincidencias.values()
            if c.reporte_perdido_id == reporte_id
            or c.reporte_encontrado_id == reporte_id
        ]

    def listar_pendientes(self) -> list[Coincidencia]:
        return [
            c
            for c in self.coincidencias.values()
            if c.estado == EstadoCoincidencia.PENDIENTE
        ]

    def actualizar(self, coincidencia: Coincidencia) -> Coincidencia:
        self.coincidencias[coincidencia.id] = coincidencia
        return coincidencia

    def existe_coincidencia(self, perdido_id: str, encontrado_id: str) -> bool:
        return any(
            c.reporte_perdido_id == perdido_id
            and c.reporte_encontrado_id == encontrado_id
            for c in self.coincidencias.values()
        )


class FakeFotoStorage(FotoStorage):
    def __init__(self) -> None:
        self.archivos: dict[str, bytes] = {}

    def guardar_foto(self, archivo_bytes: bytes, nombre_archivo: str) -> str:
        ruta = f"uploads/{nombre_archivo}"
        self.archivos[ruta] = archivo_bytes
        return ruta

    def obtener_ruta(self, nombre_archivo: str) -> str:
        return f"uploads/{nombre_archivo}"

    def eliminar_foto(self, nombre_archivo: str) -> None:
        ruta = f"uploads/{nombre_archivo}"
        self.archivos.pop(ruta, None)


class FakeNotificacionService(NotificacionService):
    def __init__(self) -> None:
        self.notificaciones_enviadas: list[dict] = []

    def notificar_coincidencia(
        self,
        usuario: Usuario,
        coincidencia: Coincidencia,
        reporte_propio: ReporteObjeto,
        reporte_match: ReporteObjeto,
    ) -> None:
        self.notificaciones_enviadas.append(
            {
                "usuario_id": usuario.id,
                "coincidencia_id": coincidencia.id,
                "propio_id": reporte_propio.id,
                "match_id": reporte_match.id,
            }
        )


# --- Suite de Pruebas ---


class TestCasosDeUso(unittest.TestCase):
    """Pruebas de orquestación de casos de uso."""

    def setUp(self) -> None:
        self.usuario_repo = FakeUsuarioRepository()
        self.reporte_repo = FakeReporteRepository()
        self.coincidencia_repo = FakeCoincidenciaRepository()
        self.foto_storage = FakeFotoStorage()
        self.notif_service = FakeNotificacionService()
        self.motor = MotorCoincidencias()

        # Crear usuarios base (Carlos y Ana)
        self.carlos = Usuario(
            id=str(uuid.uuid4()),
            nombre="Carlos Estudiante",
            email="carlos@uab.edu.bo",
        )
        self.ana = Usuario(
            id=str(uuid.uuid4()),
            nombre="Ana Compañera",
            email="ana@uab.edu.bo",
        )
        self.usuario_repo.guardar(self.carlos)
        self.usuario_repo.guardar(self.ana)

        self.ahora_iso = datetime.now(timezone.utc).isoformat()

    def test_registrar_objeto_perdido_exitoso(self) -> None:
        """Verifica que un reporte perdido se crea sin requerir GPS."""
        caso_uso = RegistrarObjetoPerdido(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            coincidencia_repo=self.coincidencia_repo,
            motor_coincidencias=self.motor,
            notificacion_service=self.notif_service,
        )
        dto = ReporteInputDTO(
            titulo="Mochila Totto roja",
            descripcion="Mochila con parches dejada olvidada en segunda fila",
            categoria_str="MOCHILA",
            referencia="Aula A-203",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.carlos.id,
        )
        output, matches = caso_uso.ejecutar(dto)

        self.assertEqual(output.titulo, "Mochila Totto roja")
        self.assertEqual(output.tipo, "PERDIDO")
        self.assertEqual(output.nombre_usuario, "Carlos Estudiante")
        # No hay encontrados activos aún, matches debe ser vacío
        self.assertEqual(len(matches), 0)

    def test_reporte_perdido_no_requiere_gps(self) -> None:
        """Verifica que crear un reporte perdido NO requiere coordenadas GPS."""
        caso_uso = RegistrarObjetoPerdido(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            coincidencia_repo=self.coincidencia_repo,
            motor_coincidencias=self.motor,
        )
        # Solo con referencia_interna, sin lat/lon
        dto = ReporteInputDTO(
            titulo="Laptop Dell negra",
            descripcion="Laptop Dell Inspiron negra con sticker de Python en la tapa",
            categoria_str="LAPTOP",
            referencia="Bloque B – B003",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.carlos.id,
        )
        output, _ = caso_uso.ejecutar(dto)
        self.assertIsNotNone(output.id)
        self.assertEqual(output.tipo, "PERDIDO")

    def test_registrar_objeto_encontrado_con_foto_exitoso(self) -> None:
        """Verifica que un reporte con foto se crea correctamente sin GPS."""
        caso_uso = RegistrarObjetoEncontrado(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            foto_storage=self.foto_storage,
            coincidencia_repo=self.coincidencia_repo,
            motor_coincidencias=self.motor,
        )
        dto = ReporteInputDTO(
            titulo="Mochila azul encontrada",
            descripcion="Mochila azul hallada sobre banca en pasillo central",
            categoria_str="MOCHILA",
            referencia="Pasillo Central – Piso 2",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.ana.id,
            foto_bytes=b"\xFF\xD8\xFF\xE0simulacion_foto_jpg",
            foto_nombre="mochila_azul.jpg",
        )
        output, _ = caso_uso.ejecutar(dto)

        self.assertIsNotNone(output.id)
        self.assertEqual(output.tipo, "ENCONTRADO")
        self.assertIsNotNone(output.foto_ruta)
        # Verificar que la foto fue guardada en el storage
        self.assertTrue(len(self.foto_storage.archivos) > 0)

    def test_registrar_objeto_encontrado_sin_foto_lanza_error(self) -> None:
        """Verifica que FotoRequeridaError se lanza cuando no hay foto."""
        caso_uso = RegistrarObjetoEncontrado(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            foto_storage=self.foto_storage,
            coincidencia_repo=self.coincidencia_repo,
            motor_coincidencias=self.motor,
        )
        dto = ReporteInputDTO(
            titulo="Llaves sin foto",
            descripcion="Llaves encontradas en la cafetería",
            categoria_str="LLAVES",
            referencia="Cafetería",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.ana.id,
            foto_bytes=None,  # Sin foto
        )
        with self.assertRaises(FotoRequeridaError):
            caso_uso.ejecutar(dto)

    def test_registrar_objeto_perdido_usuario_inexistente_falla(self) -> None:
        caso_uso = RegistrarObjetoPerdido(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            coincidencia_repo=self.coincidencia_repo,
            motor_coincidencias=self.motor,
        )
        dto = ReporteInputDTO(
            titulo="Mochila",
            descripcion="Descripción con más de veinte caracteres de prueba",
            categoria_str="MOCHILA",
            referencia="Aula A-203",
            fecha_hora_str=self.ahora_iso,
            usuario_id="id_inexistente",
        )
        with self.assertRaises(UsuarioNoEncontradoError):
            caso_uso.ejecutar(dto)

    def test_flujo_completo_perdido_luego_encontrado_detecta_coincidencia(self) -> None:
        # 1. Carlos reporta mochila perdida
        uc_perdido = RegistrarObjetoPerdido(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            coincidencia_repo=self.coincidencia_repo,
            motor_coincidencias=self.motor,
            notificacion_service=self.notif_service,
        )
        dto_perdido = ReporteInputDTO(
            titulo="Mochila Totto roja",
            descripcion="Mochila roja con parches olvidada durante clase",
            categoria_str="MOCHILA",
            referencia="Aula A-203",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.carlos.id,
        )
        out_perdido, _ = uc_perdido.ejecutar(dto_perdido)

        # 2. Ana registra hallazgo de la misma mochila en el pasillo adyacente
        uc_encontrado = RegistrarObjetoEncontrado(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            foto_storage=self.foto_storage,
            coincidencia_repo=self.coincidencia_repo,
            motor_coincidencias=self.motor,
            notificacion_service=self.notif_service,
        )
        dto_encontrado = ReporteInputDTO(
            titulo="Mochila Totto roja encontrada",
            descripcion="Mochila roja encontrada en pasillo cerca de aula",
            categoria_str="MOCHILA",
            referencia="Pasillo B",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.ana.id,
            foto_bytes=b"\xFF\xD8...foto_mochila",
            foto_nombre="mochila_ana.jpg",
        )
        out_encontrado, matches = uc_encontrado.ejecutar(dto_encontrado)

        # Debe haber detectado la coincidencia con el reporte de Carlos
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].reporte_perdido_id, out_perdido.id)
        self.assertEqual(matches[0].reporte_encontrado_id, out_encontrado.id)
        self.assertTrue(matches[0].puntuacion >= 0.40)

        # Debe haber notificado a Carlos y Ana
        self.assertEqual(len(self.notif_service.notificaciones_enviadas), 2)

    def test_confirmar_coincidencia_marca_reportes_resueltos(self) -> None:
        # Registrar perdido y encontrado
        uc_perdido = RegistrarObjetoPerdido(
            self.reporte_repo, self.usuario_repo, self.coincidencia_repo, self.motor
        )
        out_p, _ = uc_perdido.ejecutar(
            ReporteInputDTO(
                titulo="Calculadora Casio fx-991",
                descripcion="Calculadora científica plateada con tapa negra",
                categoria_str="OTRO",
                referencia="Lab 1",
                fecha_hora_str=self.ahora_iso,
                usuario_id=self.carlos.id,
            )
        )

        uc_encontrado = RegistrarObjetoEncontrado(
            self.reporte_repo,
            self.usuario_repo,
            self.foto_storage,
            self.coincidencia_repo,
            self.motor,
        )
        out_e, matches = uc_encontrado.ejecutar(
            ReporteInputDTO(
                titulo="Calculadora Casio encontrada",
                descripcion="Calculadora científica plateada hallada en mesón",
                categoria_str="OTRO",
                referencia="Lab 1",
                fecha_hora_str=self.ahora_iso,
                usuario_id=self.ana.id,
                foto_bytes=b"bytes_foto_calculadora",
            )
        )
        self.assertTrue(len(matches) > 0)
        coincidencia_id = matches[0].id

        # Confirmar la coincidencia
        uc_proc = ProcesarCoincidenciasYNotificar(
            coincidencia_repo=self.coincidencia_repo,
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
        )
        res = uc_proc.confirmar_coincidencia(coincidencia_id)

        self.assertEqual(res.estado, "CONFIRMADA")

        # Verificar que ambos reportes están en estado RESUELTO
        rep_p = self.reporte_repo.obtener_por_id(out_p.id)
        rep_e = self.reporte_repo.obtener_por_id(out_e.id)
        self.assertIsNotNone(rep_p)
        self.assertIsNotNone(rep_e)
        self.assertEqual(rep_p.estado, EstadoReporte.RESUELTO)
        self.assertEqual(rep_e.estado, EstadoReporte.RESUELTO)

    def test_registrar_objeto_perdido_sin_gps_y_descripcion_corta_o_vacia(self) -> None:
        """Verifica la creación exitosa de un reporte perdido con descripción corta y sin GPS."""
        uc = RegistrarObjetoPerdido(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            coincidencia_repo=self.coincidencia_repo,
            motor_coincidencias=self.motor,
            notificacion_service=self.notif_service,
        )
        dto = ReporteInputDTO(
            titulo="Lapto",
            descripcion="Sin daño",
            categoria_str="LAPTOP",
            referencia="Bloque B",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.carlos.id,
        )
        out, matches = uc.ejecutar(dto)
        self.assertIsNotNone(out.id)
        self.assertEqual(out.titulo, "Lapto")
        self.assertEqual(out.descripcion, "Sin daño")
        self.assertEqual(out.referencia, "Bloque B")
        self.assertFalse(hasattr(out, "latitud"))
        self.assertFalse(hasattr(out, "longitud"))

    def test_registrar_objeto_encontrado_con_foto_sin_gps_y_descripcion_corta(self) -> None:
        """Verifica la creación exitosa de un reporte encontrado con foto, descripción corta/vacía y sin GPS."""
        uc = RegistrarObjetoEncontrado(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            foto_storage=self.foto_storage,
            coincidencia_repo=self.coincidencia_repo,
            motor_coincidencias=self.motor,
            notificacion_service=self.notif_service,
        )
        dto = ReporteInputDTO(
            titulo="Llave",
            descripcion="",
            categoria_str="LLAVES",
            referencia="B003",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.ana.id,
            foto_bytes=b"bytes_foto_llave",
            foto_nombre="llave.png",
        )
        out, matches = uc.ejecutar(dto)
        self.assertIsNotNone(out.id)
        self.assertEqual(out.titulo, "Llave")
        self.assertEqual(out.descripcion, "")
        self.assertEqual(out.referencia, "B003")
        self.assertIsNotNone(out.foto_ruta)
        self.assertFalse(hasattr(out, "latitud"))
        self.assertFalse(hasattr(out, "longitud"))


if __name__ == "__main__":
    unittest.main()
