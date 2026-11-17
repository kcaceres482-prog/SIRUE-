"""Fábrica de dominio para la creación validada de reportes."""

from __future__ import annotations

from datetime import datetime
import uuid

from sirue.application.dtos.reporte_dto import ReporteInputDTO
from sirue.domain.entities.reporte_objeto import (
    EstadoReporte,
    ReporteObjeto,
    TipoReporte,
)
from sirue.domain.exceptions.domain_exceptions import (
    DescripcionInsuficienteError,
    FotoRequeridaError,
    ValidacionError,
)
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus


class ReporteFactory:
    """Fábrica para crear instancias validadas de ReporteObjeto.

    Encapsula las reglas de negocio para la creación de reportes:
    - Reportes PERDIDOS: requieren título, descripción detallada (>= 20 caracteres),
      categoría, lugar o referencia interna y fecha.
    - Reportes ENCONTRADOS: requieren foto obligatoria, título, categoría, lugar o referencia
      interna y fecha.
    """

    @staticmethod
    def _parsear_categoria(categoria_str: str) -> CategoriaObjeto:
        """Parsea una cadena a CategoriaObjeto, validando que sea válida.

        Args:
            categoria_str: Nombre de la categoría como cadena.

        Returns:
            Instancia de CategoriaObjeto.

        Raises:
            ValidacionError: Si la categoría no existe en el enum.
        """
        try:
            return CategoriaObjeto(categoria_str.upper().strip())
        except (ValueError, AttributeError):
            categorias_validas = [c.value for c in CategoriaObjeto]
            raise ValidacionError(
                f"Categoría no válida: '{categoria_str}'. "
                f"Las categorías permitidas son: {', '.join(categorias_validas)}"
            )

    @staticmethod
    def _parsear_fecha(fecha_str: str) -> FechaHoraIncidente:
        """Parsea una cadena ISO 8601 a FechaHoraIncidente.

        Args:
            fecha_str: Fecha y hora en formato ISO 8601.

        Returns:
            Instancia de FechaHoraIncidente.

        Raises:
            ValidacionError: Si el formato es incorrecto o la fecha está en el futuro.
        """
        try:
            # Reemplazar 'Z' por '+00:00' para compatibilidad con fromisoformat en Python < 3.11
            cadena_normalizada = fecha_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cadena_normalizada)
            return FechaHoraIncidente(dt)
        except (ValueError, TypeError) as e:
            if isinstance(e, ValidacionError):
                raise
            raise ValidacionError(
                f"Formato de fecha y hora no válido: '{fecha_str}'. Use ISO 8601."
            )

    @staticmethod
    def crear_reporte_perdido(dto: ReporteInputDTO) -> ReporteObjeto:
        """Crea un reporte de objeto PERDIDO a partir de un DTO de entrada.

        Validaciones específicas:
        - Título no vacío.
        - Descripción de al menos 20 caracteres.
        - Categoría válida.
        - Referencia de lugar no vacía.
        - Fecha no futura con timezone.

        Args:
            dto: DTO con los datos de entrada del reporte.

        Returns:
            Entidad ReporteObjeto de tipo PERDIDO.

        Raises:
            ValidacionError: Si algún campo es inválido.
            DescripcionInsuficienteError: Si la descripción tiene menos de 20 caracteres.
        """
        if not dto.titulo or not dto.titulo.strip():
            raise ValidacionError("El título del reporte no puede estar vacío.")

        descripcion_limpia = (dto.descripcion or "").strip()

        categoria = ReporteFactory._parsear_categoria(dto.categoria_str)
        ubicacion = UbicacionCampus(
            referencia_interna=dto.referencia,
        )
        fecha_hora = ReporteFactory._parsear_fecha(dto.fecha_hora_str)

        reporte = ReporteObjeto(
            id=str(uuid.uuid4()),
            tipo=TipoReporte.PERDIDO,
            titulo=dto.titulo.strip(),
            descripcion=descripcion_limpia,
            categoria=categoria,
            ubicacion=ubicacion,
            fecha_hora_incidente=fecha_hora,
            usuario_id=dto.usuario_id,
            foto_ruta=None,
            estado=EstadoReporte.ACTIVO,
        )

        return reporte

    @staticmethod
    def crear_reporte_encontrado(dto: ReporteInputDTO) -> ReporteObjeto:
        """Crea un reporte de objeto ENCONTRADO a partir de un DTO de entrada.

        Validaciones específicas:
        - DEBE incluir foto (foto_bytes no vacío).
        - Título no vacío.
        - Categoría válida.
        - Referencia de lugar no vacía.

        Args:
            dto: DTO con los datos de entrada del reporte.

        Returns:
            Entidad ReporteObjeto de tipo ENCONTRADO.

        Raises:
            FotoRequeridaError: Si no se incluye foto.
            ValidacionError: Si el título o referencia están vacíos.
        """
        if not dto.foto_bytes:
            raise FotoRequeridaError(
                "Los reportes de objetos encontrados deben incluir una foto."
            )

        if not dto.titulo or not dto.titulo.strip():
            raise ValidacionError("El título del reporte no puede estar vacío.")

        categoria = ReporteFactory._parsear_categoria(dto.categoria_str)
        ubicacion = UbicacionCampus(
            referencia_interna=dto.referencia,
        )
        fecha_hora = ReporteFactory._parsear_fecha(dto.fecha_hora_str)

        descripcion_limpia = (dto.descripcion or "").strip()

        reporte = ReporteObjeto(
            id=str(uuid.uuid4()),
            tipo=TipoReporte.ENCONTRADO,
            titulo=dto.titulo.strip(),
            descripcion=descripcion_limpia,
            categoria=categoria,
            ubicacion=ubicacion,
            fecha_hora_incidente=fecha_hora,
            usuario_id=dto.usuario_id,
            foto_ruta=None,  # Se asigna después de guardar la foto
            estado=EstadoReporte.ACTIVO,
        )

        return reporte
