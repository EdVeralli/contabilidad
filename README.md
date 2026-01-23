# Contabilidad

Sistema Contable migrado de Clipper a Python/Flask.

## Requisitos

- Python 3.10+
- pip

## Instalacion

### 1. Crear entorno virtual

```bash
cd vero_contable
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Inicializar base de datos

Por defecto usa **SQLite** (no requiere instalacion adicional).

```bash
# Crear tablas
flask init-db

# Crear usuario administrador
flask create-admin
```

### 4. Migrar datos desde DBF (opcional)

Si tienes datos de un sistema Clipper anterior:

```bash
# Migrar todas las empresas automaticamente
python scripts/migrar_todo.py

# O migrar una empresa especifica
python scripts/migrar_dbf.py --empresa DIRE1 --path "C:\ruta\a\archivos\DBF"
```

## Ejecutar la aplicacion

### Desarrollo

```bash
flask run --debug
```

La aplicacion estara disponible en: http://localhost:5000

### Produccion

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## Credenciales por defecto

- **Usuario:** admin
- **Password:** admin123

## Base de Datos

### SQLite (por defecto)

No requiere configuracion. La base de datos se crea automaticamente en `vero_contable.db`.

### MySQL (opcional)

Si prefieres usar MySQL, edita el archivo `.env`:

```
DATABASE_URL=mysql+pymysql://usuario:password@localhost/contabilidad
```

Y crea la base de datos:

```sql
CREATE DATABASE contabilidad CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Estructura del proyecto

```
vero_contable/
├── app/
│   ├── __init__.py          # Factory pattern
│   ├── config.py            # Configuracion
│   ├── extensions.py        # SQLAlchemy, Login, etc.
│   ├── models/              # Modelos SQLAlchemy
│   ├── blueprints/          # Rutas y vistas
│   │   ├── auth/            # Autenticacion
│   │   ├── cuentas/         # Plan de cuentas
│   │   ├── asientos/        # Asientos contables
│   │   ├── informes/        # Reportes
│   │   ├── ajustes/         # Ajuste por inflacion
│   │   └── admin/           # Administracion
│   ├── services/            # Logica de negocio
│   ├── templates/           # Plantillas HTML
│   └── static/              # CSS, JS, imagenes
├── scripts/                 # Scripts de utilidad
│   ├── migrar_todo.py       # Migracion completa desde DBF
│   └── migrar_dbf.py        # Migracion por empresa
├── tests/                   # Tests
├── .env                     # Variables de entorno
├── requirements.txt         # Dependencias
└── run.py                   # Punto de entrada
```

## Funcionalidades

### Plan de Cuentas
- Alta, baja, modificacion de cuentas
- Busqueda por codigo o nombre
- Estructura jerarquica con niveles

### Asientos Contables
- Generacion de asientos con validacion de balance
- Modificacion de asientos existentes
- Anulacion de asientos (reversible)
- Actualizacion automatica de saldos

### Informes
- **Libro Diario:** Movimientos cronologicos
- **Libro Mayor:** Movimientos por cuenta con saldos
- **Sumas y Saldos:** Balance de comprobacion
- **Balance General:** Estado patrimonial jerarquico

### Ajuste por Inflacion
- Mantenimiento de tablas de indices
- Calculo de ajuste por cuenta
- Generacion automatica de asiento REI

### Administracion
- Gestion de empresas (multi-empresa)
- Gestion de usuarios
- Cambio de empresa activa

## Comandos CLI

```bash
# Inicializar tablas
flask init-db

# Crear usuario admin
flask create-admin
```

## Tecnologias

- **Backend:** Python 3.10+, Flask 3.0
- **Base de datos:** SQLite (default) / MySQL (opcional)
- **ORM:** SQLAlchemy
- **Frontend:** Bootstrap 5, DataTables
- **Autenticacion:** Flask-Login
