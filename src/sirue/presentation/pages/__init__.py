"""Módulo de páginas de la aplicación SIRUE."""

from sirue.presentation.pages.admin import crear_pagina_admin
from sirue.presentation.pages.coincidencias import crear_pagina_coincidencias
from sirue.presentation.pages.home import crear_pagina_home
from sirue.presentation.pages.login import crear_pagina_login
from sirue.presentation.pages.mis_reportes import crear_pagina_mis_reportes
from sirue.presentation.pages.registrar_encontrado import (
    crear_pagina_registrar_encontrado,
)
from sirue.presentation.pages.registrar_perdido import (
    crear_pagina_registrar_perdido,
)

__all__ = [
    "crear_pagina_home",
    "crear_pagina_registrar_perdido",
    "crear_pagina_registrar_encontrado",
    "crear_pagina_mis_reportes",
    "crear_pagina_coincidencias",
    "crear_pagina_login",
    "crear_pagina_admin",
]
