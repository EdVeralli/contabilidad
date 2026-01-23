# Vero Contable

Sistema Contable migrado de Clipper a Python/Flask con MySQL.

## Requisitos

- Python 3.10+
- MySQL 8.0+
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

### 3. Configurar base de datos

Crear la base de datos en MySQL:

```sql
CREATE DATABASE vero_contable CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configurar variables de entorno

Editar el archivo `.env` con los datos de conexion:

```
DATABASE_URL=mysql+pymysql://usuario:password@localhost/vero_contable
SECRET_KEY=tu-clave-secreta-aqui
```

### 5. Inicializar base de datos

```bash
# Crear tablas
flask db upgrade

# O usando el comando personalizado
flask init-db

# Crear usuario administrador
flask create-admin
```

### 6. Migrar datos desde DBF (opcional)

```bash
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
├── migrations/              # Migraciones de BD
├── scripts/                 # Scripts de utilidad
│   └── migrar_dbf.py        # Migracion desde DBF
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

# Migraciones
flask db migrate -m "descripcion"
flask db upgrade
flask db downgrade
```

## Tecnologias

- **Backend:** Python 3.10+, Flask 3.0
- **Base de datos:** MySQL 8.0, SQLAlchemy
- **Frontend:** Bootstrap 5, DataTables, Chart.js
- **Autenticacion:** Flask-Login
- **Migraciones:** Flask-Migrate (Alembic)
