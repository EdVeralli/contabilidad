# Contabilidad - Sistema Contable

Sistema contable migrado de Clipper/DOS a Python/Flask. Incluye la base de datos SQLite con todos los datos ya migrados desde los archivos DBF originales.

## Datos incluidos

El repositorio incluye `vero_contable.db` con los datos migrados:

| Datos | Cantidad |
|-------|----------|
| Empresas | 8 (DIRE1, DIRE2, DIRE3, APE01, DIRE10, MEDO01, APERG, DEFAULT) |
| Plan de Cuentas | 805 cuentas |
| Asientos | 6,162 |
| Lineas de asientos | 29,187 |
| Saldos | 8,110 |
| Tablas de inflacion | 18 |

---

## Instalacion desde cero (Windows)

### 1. Instalar Python

1. Descargar Python 3.11+ desde https://www.python.org/downloads/
2. Al instalar, marcar **"Add Python to PATH"**
3. Verificar en CMD:

```cmd
python --version
```

### 2. Descargar el proyecto

**Opcion A - Con Git:**

```cmd
git clone https://github.com/EdVeralli/contabilidad.git
cd contabilidad
```

**Opcion B - Sin Git:**

1. Ir a https://github.com/EdVeralli/contabilidad
2. Click en **Code** > **Download ZIP**
3. Extraer en una carpeta (ej: `C:\Contabilidad`)

### 3. Crear entorno virtual e instalar dependencias

```cmd
cd contabilidad
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Ejecutar

```cmd
python run.py
```

### 5. Abrir en el navegador

Ir a: **http://127.0.0.1:5000**

Credenciales:
- **Usuario:** `admin`
- **Contrasena:** `admin123`

Seleccionar una empresa y listo.

---

## Instalacion desde cero (Linux / Mac)

```bash
git clone https://github.com/EdVeralli/contabilidad.git
cd contabilidad
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Abrir http://127.0.0.1:5000 en el navegador.

---

## Uso diario

Cada vez que quieras usar el sistema:

```cmd
cd contabilidad
venv\Scripts\activate
python run.py
```

Y abrir http://127.0.0.1:5000 en el navegador.

### Acceso directo (Windows)

Crear un archivo `IniciarContabilidad.bat` en el Escritorio:

```batch
@echo off
cd /d C:\ruta\a\contabilidad
call venv\Scripts\activate
start http://127.0.0.1:5000
python run.py
```

Doble click para iniciar.

---

## Funcionalidades

### Plan de Cuentas
- Alta, baja y modificacion de cuentas
- Busqueda por codigo o nombre
- Estructura jerarquica con niveles

### Asientos Contables
- Carga de asientos con validacion de balance (Debe = Haber)
- Modificacion y anulacion de asientos
- Actualizacion automatica de saldos

### Informes
- **Libro Diario:** movimientos cronologicos
- **Libro Mayor:** movimientos por cuenta con saldos
- **Sumas y Saldos:** balance de comprobacion
- **Balance General:** estado patrimonial jerarquico

### Ajuste por Inflacion
- Mantenimiento de tablas de indices mensuales
- Calculo de ajuste por cuenta monetaria/no monetaria
- Generacion automatica de asiento REI

### Administracion
- Gestion multi-empresa
- Gestion de usuarios
- Ejercicios fiscales

---

## Estructura del proyecto

```
contabilidad/
├── app/
│   ├── __init__.py            # App factory
│   ├── config.py              # Configuracion
│   ├── extensions.py          # SQLAlchemy, Login, etc.
│   ├── models/                # Modelos de datos
│   ├── blueprints/
│   │   ├── auth/              # Login, seleccion de empresa
│   │   ├── cuentas/           # Plan de cuentas
│   │   ├── asientos/          # Asientos contables
│   │   ├── informes/          # Libro diario, mayor, balance
│   │   ├── ajustes/           # Ajuste por inflacion
│   │   └── admin/             # Empresas, usuarios, ejercicios
│   ├── services/              # Logica de negocio
│   └── templates/             # Plantillas HTML
├── scripts/
│   ├── migrar_dbf.py          # Migracion individual desde DBF
│   └── migrar_todo.py         # Migracion masiva desde DBF
├── vero_contable.db           # Base de datos con datos migrados
├── .env                       # Variables de entorno
├── requirements.txt           # Dependencias Python
└── run.py                     # Punto de entrada
```

---

## Configuracion opcional

### Usar MySQL en vez de SQLite

Editar `.env` y agregar:

```
DATABASE_URL=mysql+pymysql://usuario:password@localhost/contabilidad
```

Crear la base en MySQL:

```sql
CREATE DATABASE contabilidad CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Luego inicializar:

```cmd
flask init-db
flask create-admin
```

### Re-migrar datos desde DBF

Si tenes los archivos DBF originales del sistema Clipper:

```cmd
python scripts/migrar_dbf.py --empresa DIRE1 --path "C:\ruta\a\DIRE1"
```

### Cambiar puerto

Si el puerto 5000 esta ocupado:

```cmd
flask run --port 5001
```

---

## Solucion de problemas

| Problema | Solucion |
|----------|----------|
| `python` no se reconoce | Reinstalar Python marcando "Add to PATH" |
| Error al instalar dependencias | `python -m pip install --upgrade pip` y reintentar |
| Puerto 5000 en uso | Usar `flask run --port 5001` |
| No aparecen las empresas | Verificar que no haya otro servidor corriendo en el mismo puerto |
| Error de base de datos | Eliminar `vero_contable.db`, ejecutar `flask init-db` y `flask create-admin` |

---

## Tecnologias

- **Backend:** Python 3.11+, Flask 3.0
- **Base de datos:** SQLite (incluida) / MySQL (opcional)
- **ORM:** SQLAlchemy
- **Frontend:** Bootstrap 5, DataTables
- **Autenticacion:** Flask-Login
- **Interfaz:** Tema Windows XP Luna

---

## Credenciales por defecto

| Usuario | Contrasena |
|---------|------------|
| admin   | admin123   |

Cambiar la contrasena despues del primer inicio de sesion.

---

Repositorio: https://github.com/EdVeralli/contabilidad
