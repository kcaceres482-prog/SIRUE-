"""Excepciones de dominio del sistema SIRUE."""


class SIRUEDomainError(Exception):
    """Excepción base para todos los errores de dominio de SIRUE."""
    pass


class ValidacionError(SIRUEDomainError):
    """Error lanzado cuando los datos proporcionados no son válidos."""
    pass


class ReporteNoEncontradoError(SIRUEDomainError):
    """Error lanzado cuando no se encuentra un reporte con el ID especificado."""
    pass


class UsuarioNoEncontradoError(SIRUEDomainError):
    """Error lanzado cuando no se encuentra un usuario con el ID especificado."""
    pass


class CoincidenciaNoEncontradaError(SIRUEDomainError):
    """Error lanzado cuando no se encuentra una coincidencia con el ID especificado."""
    pass


class FotoRequeridaError(SIRUEDomainError):
    """Error lanzado cuando un reporte de objeto encontrado no incluye foto."""
    pass


class DescripcionInsuficienteError(SIRUEDomainError):
    """Error lanzado cuando la descripción de un reporte de objeto perdido es insuficiente."""
    pass


class CredencialesInvalidasError(SIRUEDomainError):
    """Error lanzado cuando las credenciales de autenticación son inválidas."""
    pass


class EmailYaRegistradoError(SIRUEDomainError):
    """Error lanzado cuando se intenta registrar un usuario con un email ya existente."""
    pass


class AccesoDenegadoError(SIRUEDomainError):
    """Error lanzado cuando un usuario no tiene permisos suficientes para realizar una acción."""
    pass


class CuentaBloqueadaError(AccesoDenegadoError):
    """Error lanzado cuando una cuenta está temporalmente suspendida o bloqueada."""
    pass


class OperacionNoPermitidaError(SIRUEDomainError):
    """Error lanzado cuando una operación administrativa no es permitida (ej: autoprotección del administrador)."""
    pass
