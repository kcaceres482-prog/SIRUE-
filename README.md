# SIRUE — Sistema Digital de Objetos Perdidos y Encontrados


**SIRUE** (Sistema Inteligente de Recuperación de Objetos Universitarios Extraviados) es una plataforma digital moderna diseñada para gestionar de forma eficiente el ciclo completo de reporte, hallazgo, coincidencia proactiva y recuperación de pertenencias dentro de un campus educativo.

---

## Tabla de Contenidos

1. [Descripción General y Flujo Funcional](#descripción-general-y-flujo-funcional)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Modelado de Dominio (DDD)](#modelado-de-dominio-ddd)
5. [Motor Heurístico de Coincidencias](#motor-heurístico-de-coincidencias)
6. [Stack Tecnológico por Capas](#stack-tecnológico-por-capas)
7. [Instalación y Despliegue en Linux Fedora](#instalación-y-despliegue-en-linux-fedora)
8. [Despliegue con Docker y Docker Compose](#despliegue-con-docker-y-docker-compose)
9. [Ejecución de Pruebas Automatizadas](#ejecución-de-pruebas-automatizadas)
10. [Rutas de la Interfaz de Usuario](#rutas-de-la-interfaz-de-usuario)
11. [Licencia](#licencia)

---

## Descripción General y Flujo Funcional

El sistema resuelve la problemática de pérdida de objetos en entornos universitarios a través de un flujo sincronizado:

```
[ Estudiante A: Carlos ]                                     [ Estudiante B: Ana ]
         │                                                            │
         ▼ (Pierde mochila en Aula A-203 a las 10:30)                 ▼ (Encuentra mochila en Pasillo B a las 11:15)
   [Registra Pérdida]                                          [Registra Hallazgo]
   - Descripción detallada                                     - Fotografía obligatoria
   - Referencia de aula                                        - Coordenadas GPS del móvil
   - Punto en Mapa Leaflet                                     - Punto en Mapa Leaflet
         │                                                            │
         └─────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
                   ┌───────────────────────────────┐
                   │    MOTOR DE COINCIDENCIAS     │
                   │  - Categoría (30%)            │
                   │  - Similitud Jaccard (30%)    │
                   │  - Proximidad Espacial (20%)  │
                   │  - Proximidad Temporal (20%)  │
                   └───────────────┬───────────────┘
                                   │
                                   ▼ (Match >= 70%)
                   ┌───────────────────────────────┐
                   │   Notificación Automática     │
                   │   y Confirmación Mutua        │
                   └───────────────┬───────────────┘
                                   │
                                   ▼
                   [ Ambos reportes RESUELTOS ]
```

---

## Arquitectura del Sistema

El proyecto combina estrictamente **Clean Architecture**, **Arquitectura Hexagonal (Puertos y Adaptadores)** y **Domain-Driven Design (DDD)**, garantizando que el núcleo de negocio sea completamente agnóstico a bases de datos, frameworks web o interfaces de usuario.

### Diagrama de Capas y Regla de Dependencia

```
 +-----------------------------------------------------------------------+
 |                     CAPA EXTERNA: ADAPTADORES                         |
 |                                                                       |
 |   [ PRESENTACIÓN (Adaptador Primario) ]                               |
 |   - NiceGUI Web Server                                                |
 |   - Leaflet / OpenStreetMap                                           |
 |   - Geolocation API (Navegador)                                       |
 |                                                                       |
 |   [ INFRAESTRUCTURA (Adaptador Secundario) ]                          |
 |   - SQLAlchemy ORM & SQLite                                           |
 |   - LocalPhotoStorage (Archivos físicos)                             |
 |   - InAppNotificationService                                          |
 +-----------------------------------------------------------------------+
                                    │
                                    ▼ (depende de)
 +-----------------------------------------------------------------------+
 |                  CAPA INTERMEDIA: APLICACIÓN                          |
 |                                                                       |
 |   - Casos de Uso:                                                     |
 |       * RegistrarObjetoPerdido                                        |
 |       * RegistrarObjetoEncontrado                                     |
 |       * ProcesarCoincidenciasYNotificar                               |
 |   - Fábricas: ReporteFactory (Instanciación validada)                 |
 |   - Servicios: MotorCoincidencias (Afinidad ponderada)                |
 |   - DTOs: ReporteInputDTO, ReporteOutputDTO, CoincidenciaOutputDTO    |
 +-----------------------------------------------------------------------+
                                    │
                                    ▼ (depende de)
 +-----------------------------------------------------------------------+
 |                  CAPA INTERNA: DOMINIO (DDD PURO)                     |
 |                                                                       |
 |   - Entidades: Usuario, ReporteObjeto, Coincidencia                   |
 |   - Value Objects: UbicacionCampus, FechaHoraIncidente, Categoria     |
 |   - Excepciones: SIRUEDomainError, ValidacionError, FotoRequerida...  |
 |   - Puertos (Interfaces):                                             |
 |       * UsuarioRepository, ReporteRepository, CoincidenciaRepository  |
 |       * FotoStorage, NotificacionService                              |
 +-----------------------------------------------------------------------+
```

---

## Estructura del Proyecto

```text
SIRUE/
├── data/                                         # Volumen persistente para SQLite (sirue.db)
├── uploads/                                      # Volumen persistente para fotos subidas
├── src/
│   └── sirue/
│       ├── domain/                               # Núcleo de Dominio puro (sin dependencias externas)
│       │   ├── entities/                         # Entidades con identidad y métodos de negocio
│       │   │   ├── usuario.py
│       │   │   ├── reporte_objeto.py
│       │   │   └── coincidencia.py
│       │   ├── value_objects/                    # Value Objects inmutables con validación propia
│       │   │   ├── ubicacion_campus.py           # Coordenadas y fórmula de Haversine
│       │   │   ├── fecha_hora_incidente.py       # Control de fecha UTC y desfases
│       │   │   └── categoria_objeto.py           # Enum y compatibilidad comodín
│       │   ├── exceptions/                       # Jerarquía de errores de dominio
│       │   │   └── domain_exceptions.py
│       │   └── ports/                            # Contratos abstractos (Interfaces ABC)
│       │       ├── usuario_repository.py
│       │       ├── reporte_repository.py
│       │       ├── coincidencia_repository.py
│       │       ├── foto_storage.py
│       │       └── notificacion_service.py
│       │
│       ├── application/                          # Casos de uso y orquestación
│       │   ├── dtos/                             # DTOs para entrada y salida desacoplada
│       │   │   └── reporte_dto.py
│       │   ├── factories/                        # Factory Method para validar según tipo
│       │   │   └── reporte_factory.py
│       │   ├── services/                         # Algoritmo de coincidencias
│       │   │   └── motor_coincidencias.py
│       │   └── use_cases/                        # Orquestadores de negocio
│       │       ├── registrar_objeto_perdido.py
│       │       ├── registrar_objeto_encontrado.py
│       │       └── procesar_coincidencias.py
│       │
│       ├── infrastructure/                       # Implementaciones concretas de puertos
│       │   ├── container.py                      # Contenedor IoC / Inyección de dependencias
│       │   ├── persistence/                      # Persistencia relacional
│       │   │   ├── database.py                   # Conexión SQLAlchemy y gestión de sesiones
│       │   │   ├── models/                       # Modelos ORM relacionales
│       │   │   └── repositories/                 # Adaptadores concretos de repositorio
│       │   ├── storage/                          # Gestor de archivos en disco
│       │   │   └── local_photo_storage.py
│       │   └── notifications/                    # Adaptador de notificaciones in-app
│       │       └── in_app_notification_service.py
│       │
│       └── presentation/                         # Interfaz gráfica de usuario
│           ├── app.py                            # Registro de rutas y configuración de estáticos
│           ├── components/                       # Componentes visuales reutilizables
│           │   ├── header.py                     # Navegación responsiva y perfiles
│           │   └── modal_detalle_reporte.py      # Modal de detalle y contacto de reportes
│           ├── pages/                            # Vistas completas de la aplicación
│           │   ├── home.py
│           │   ├── registrar_perdido.py
│           │   ├── registrar_encontrado.py
│           │   ├── mis_reportes.py
│           │   └── coincidencias.py
│           └── static/                           # Assets estáticos
│               └── css/styles.css                # Estilos responsive mobile-first
│
├── tests/                                        # Suite de pruebas automatizadas
│   ├── unit/
│   │   ├── domain/                               # Pruebas unitarias de reglas de dominio
│   │   └── application/                          # Pruebas de factories y algoritmos
│   └── integration/                              # Pruebas con base de datos y storage
│
├── Dockerfile                                    # Imagen de producción Python 3.12 Slim
├── docker-compose.yml                            # Orquestación de contenedores y volúmenes
├── requirements.txt                              # Dependencias pip
├── pyproject.toml                                # Configuración de empaquetado y pytest
├── .env.example                                  # Plantilla de variables de entorno
├── .gitignore                                    # Archivos excluidos de control de versiones
└── main.py                                       # Punto de entrada de la aplicación
```

---

## Modelado de Dominio (DDD)

### Entidades
- **`Usuario`**: Modela a los miembros de la comunidad universitaria. Valida estructura de email mediante expresiones regulares e identidad única.
- **`ReporteObjeto`**: Modela una pertenencia extraviada o hallada. Incluye extracción automática de palabras clave depuradas (eliminando *stopwords* del español y palabras con longitud $\le 2$). Administra estados (`ACTIVO`, `RESUELTO`, `EXPIRADO`).
- **`Coincidencia`**: Representa la vinculación heurística entre una pérdida y un hallazgo. Contiene la puntuación normalizada en $[0.0, 1.0]$ y métodos de ciclo de vida (`confirmar()`, `descartar()`, `es_relevante()`).

### Value Objects
- **`UbicacionCampus`**: Inmutable (`frozen=True`). Coordenadas GPS y referencia física en campus. Contiene el cálculo de distancia esférica mediante la **fórmula de Haversine** en metros.
- **`FechaHoraIncidente`**: Inmutable. Exige marcas de tiempo *timezone-aware* en UTC, rechaza incidentes futuros y calcula la diferencia horaria con `diferencia_horas()`.
- **`CategoriaObjeto`**: Enum tipado con soporte comodín para objetos diversos (`OTRO`).

---

## Motor Heurístico de Coincidencias

El cálculo de afinidad se ejecuta ponderando cuatro dimensiones complementarias:

$$S_{\text{total}} = 0.30 \cdot S_{\text{cat}} + 0.30 \cdot S_{\text{kw}} + 0.20 \cdot S_{\text{espacio}} + 0.20 \cdot S_{\text{tiempo}}$$

1. **Categoría ($30\%$)**: $1.0$ si son idénticas, $0.3$ si alguna es `OTRO`, $0.0$ si difieren.
2. **Palabras Clave ($30\%$)**: Coeficiente de similitud de **Jaccard**:
   $$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$
3. **Proximidad Espacial ($20\%$)**: Distancia en metros calculada mediante Haversine:
   - $d \le 100\text{ m} \implies 1.0$
   - $100\text{ m} < d < 1000\text{ m} \implies 1.0 - \frac{d - 100}{900}$
   - $d \ge 1000\text{ m} \implies 0.0$
4. **Proximidad Temporal ($20\%$)**: Diferencia horaria absoluta $\Delta t$:
   - $\Delta t \le 1\text{ h} \implies 1.0$
   - $1\text{ h} < \Delta t < 24\text{ h} \implies 1.0 - \frac{\Delta t - 1}{23}$
   - $\Delta t \ge 24\text{ h} \implies 0.0$

---

## Stack Tecnológico por Capas

| Capa | Tecnologías | Propósito |
| :--- | :--- | :--- |
| **Frontend / UI** | **NiceGUI 2.x**, Tailwind CSS, HTML5, CSS3 | Interfaz web interactiva y reactiva con diseño *mobile-first*. |
| **Mapas / Geo** | **Leaflet 1.9**, **OpenStreetMap**, **Geolocation API** | Georreferenciación interactiva y captura GPS en tiempo real. |
| **Aplicación** | Python 3.10+, Dataclasses, DTOs, Factory Pattern | Casos de uso y orquestación de la lógica de negocio. |
| **Dominio** | Python 3 puro (Typing estricto, ABC) | Entidades, Value Objects e interfaces de repositorio desacopladas. |
| **Persistencia** | **SQLite 3**, **SQLAlchemy ORM 2.x** | Persistencia relacional liviana y portable a través de repositorios. |
| **Almacenamiento** | Python `pathlib` + UUID | Gestión de fotografías en servidor guardando solo la ruta en BD. |
| **Calidad / Tests** | **PyTest**, `unittest` nativo, `pytest-cov` | Pruebas unitarias y de integración continuas. |
| **Contenedores** | **Docker**, **Docker Compose** | Empaquetado y aislamiento con volúmenes persistentes. |

---

## Instalación y Despliegue en Linux Fedora

### 1. Requisitos Previos en Fedora
Instalar Python, pip y herramientas de desarrollo desde los repositorios oficiales de Fedora:

```bash
sudo dnf install -y python3 python3-pip python3-devel gcc git curl
```

### 2. Clonar el Repositorio y Configurar Entorno Virtual
```bash
git clone https://github.com/tu-usuario/SIRUE.git
cd SIRUE

# Crear entorno virtual
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate

# Actualizar pip e instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno (Opcional)
```bash
cp .env.example .env
```

### 4. Ejecutar la Aplicación
```bash
python main.py
```

La aplicación quedará disponible en:
👉 **`http://localhost:8080`**

### 5. Habilitar Puerto en el Firewall de Fedora (si se accede desde la red del campus)
```bash
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

---

## Despliegue con Docker y Docker Compose

El despliegue contenerizado garantiza persistencia total de la base de datos SQLite y de las imágenes subidas mediante volúmenes Docker gestionados.

### 1. Construir e Iniciar el Servicio
```bash
docker compose up -d --build
```

### 2. Verificar Estado y Logs del Contenedor
```bash
# Ver estado del contenedor y su healthcheck
docker compose ps

# Ver registros en tiempo real
docker compose logs -f sirue
```

### 3. Detener el Servicio Preservando Datos
```bash
docker compose down
```
*(Los datos en `sirue_data_volume` y `sirue_uploads_volume` se mantendrán intactos).*

---

## Ejecución de Pruebas Automatizadas

El proyecto incluye pruebas unitarias para el dominio y la aplicación, así como pruebas de integración para el almacenamiento y la base de datos.

### Ejecución con PyTest (Recomendado)
```bash
# Ejecutar todas las pruebas con reporte detallado
pytest tests/ -v

# Ejecutar únicamente las pruebas unitarias
pytest tests/unit/ -v

# Ejecutar únicamente las pruebas de integración
pytest tests/integration/ -v

# Medir cobertura de código
pytest --cov=sirue tests/
```

### Ejecución con el Runner Nativo de Python (Sin dependencias externas)
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

---

## Rutas de la Interfaz de Usuario

| Ruta | Nombre | Descripción |
| :--- | :--- | :--- |
| **`/`** | **Inicio / Dashboard** | Vista panorámica del campus con estadísticas y mapa interactivo de reportes activos. |
| **`/reportar-perdido`** | **Reportar Pérdida** | Formulario con validación de descripción ($\ge 20$ chars), selector de lugar y mapa interactivo. |
| **`/reportar-encontrado`** | **Registrar Hallazgo** | Formulario con captura de foto obligatoria y botón de geolocalización GPS móvil. |
| **`/mis-reportes`** | **Mis Reportes** | Historial de publicaciones del estudiante con opción para marcar reportes como resueltos. |
| **`/coincidencias`** | **Centro de Coincidencias** | Comparativa visual de reportes compatibles, medidor de afinidad y confirmación mutua. |

---

## Licencia

Distribuido bajo la Licencia **MIT**. Consulta el archivo `LICENSE` para mayores detalles.
