# Guía de Instalación - Sistema Contabilidad (Windows)

Esta guía explica cómo instalar el sistema de Contabilidad desde cero en una máquina Windows.

---

## Requisitos Previos

- Windows 10 o superior
- Conexión a Internet
- Permisos de administrador

---

## Paso 1: Instalar Python

### 1.1 Descargar Python

1. Ir a: https://www.python.org/downloads/
2. Descargar **Python 3.11** o superior (botón amarillo "Download Python")

### 1.2 Instalar Python

1. Ejecutar el instalador descargado
2. **IMPORTANTE:** Marcar la casilla ✅ **"Add Python to PATH"** antes de instalar
3. Click en **"Install Now"**
4. Esperar a que termine la instalación
5. Click en **"Close"**

### 1.3 Verificar instalación

Abrir **CMD** (Símbolo del sistema) y ejecutar:

```cmd
python --version
```

Debe mostrar algo como: `Python 3.11.x`

---

## Paso 2: Descargar el Sistema

### Opción A: Descargar como ZIP (más fácil)

1. Ir a: https://github.com/EdVeralli/contabilidad
2. Click en el botón verde **"Code"**
3. Click en **"Download ZIP"**
4. Extraer el ZIP en una carpeta, por ejemplo: `C:\Contabilidad`

### Opción B: Clonar con Git (para desarrolladores)

Si tienes Git instalado:

```cmd
cd C:\
git clone https://github.com/EdVeralli/contabilidad.git
cd contabilidad
```

---

## Paso 3: Crear Entorno Virtual

Abrir **CMD** y navegar a la carpeta del proyecto:

```cmd
cd C:\Contabilidad
```

Crear el entorno virtual:

```cmd
python -m venv venv
```

Activar el entorno virtual:

```cmd
venv\Scripts\activate
```

> **Nota:** Verás `(venv)` al inicio de la línea de comandos cuando el entorno esté activo.

---

## Paso 4: Instalar Dependencias

Con el entorno virtual activado, ejecutar:

```cmd
pip install flask flask-sqlalchemy flask-login flask-wtf flask-migrate python-dotenv dbfread
```

O si existe el archivo requirements.txt:

```cmd
pip install -r requirements.txt
```

---

## Paso 5: Configurar Variables de Entorno

Crear un archivo llamado `.env` en la carpeta del proyecto con el siguiente contenido:

```
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=clave-secreta-cambiar-en-produccion
ITEMS_PER_PAGE=20
```

> **Nota:** Puedes crear este archivo con el Bloc de notas. Guardar como "Todos los archivos" y nombrar `.env`

---

## Paso 6: Inicializar la Base de Datos

Con el entorno virtual activado:

```cmd
flask init-db
```

Debe mostrar: `Database tables created.`

---

## Paso 7: Crear Usuario Administrador

```cmd
flask create-admin
```

Debe mostrar:
```
Created default company: Empresa Principal
Created admin user (password: admin123)
```

---

## Paso 8: Migrar Datos desde Sistema Anterior (Opcional)

Si tienes archivos DBF del sistema Clipper anterior:

### 8.1 Editar la ruta de los archivos DBF

Abrir el archivo `scripts/migrar_todo.py` y modificar la línea:

```python
BASE_PATH = r'C:\ruta\a\tus\archivos\DBF'
```

### 8.2 Ejecutar la migración

```cmd
python scripts/migrar_todo.py
```

Esto importará automáticamente:
- Todas las empresas
- Plan de cuentas
- Asientos contables
- Tablas de inflación

---

## Paso 9: Iniciar el Sistema

```cmd
flask run
```

Debe mostrar:
```
 * Running on http://127.0.0.1:5000
```

---

## Paso 10: Acceder al Sistema

1. Abrir el navegador (Chrome, Firefox, Edge)
2. Ir a: **http://127.0.0.1:5000**
3. Iniciar sesión con:
   - **Usuario:** `admin`
   - **Password:** `admin123`
4. Seleccionar una empresa para trabajar

---

## Uso Diario

Cada vez que quieras usar el sistema:

### 1. Abrir CMD

### 2. Navegar a la carpeta del proyecto
```cmd
cd C:\Contabilidad
```

### 3. Activar el entorno virtual
```cmd
venv\Scripts\activate
```

### 4. Iniciar el servidor
```cmd
flask run
```

### 5. Abrir el navegador en http://127.0.0.1:5000

---

## Crear Acceso Directo (Opcional)

Para facilitar el inicio diario, puedes crear un archivo `.bat`:

1. Abrir el Bloc de notas
2. Pegar el siguiente contenido:

```batch
@echo off
cd /d C:\Contabilidad
call venv\Scripts\activate
start http://127.0.0.1:5000
flask run
```

3. Guardar como `IniciarContabilidad.bat` en el Escritorio
4. Doble click para iniciar el sistema

---

## Solución de Problemas

### "python" no se reconoce como comando

- Reinstalar Python marcando la opción **"Add Python to PATH"**
- O agregar Python al PATH manualmente:
  1. Buscar "Variables de entorno" en Windows
  2. Editar la variable PATH
  3. Agregar: `C:\Users\TU_USUARIO\AppData\Local\Programs\Python\Python311\`

### Error al instalar dependencias

Actualizar pip:
```cmd
python -m pip install --upgrade pip
```

### El servidor no inicia

Verificar que el entorno virtual esté activado (debe verse `(venv)` en la línea de comandos)

### Error de base de datos

Eliminar el archivo `vero_contable.db` y volver a ejecutar:
```cmd
flask init-db
flask create-admin
```

### Puerto 5000 en uso

Usar otro puerto:
```cmd
flask run --port 5001
```

Y acceder a: http://127.0.0.1:5001

---

## Credenciales por Defecto

| Usuario | Contraseña |
|---------|------------|
| admin   | admin123   |

> **IMPORTANTE:** Cambiar la contraseña después del primer inicio de sesión.

---

## Soporte

Repositorio: https://github.com/EdVeralli/contabilidad

---

*Documento generado para Sistema Contabilidad v1.0*
