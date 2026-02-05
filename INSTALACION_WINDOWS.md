# Guia de Instalacion - Sistema Contabilidad (Windows)

Esta guia explica como instalar el sistema de Contabilidad en una maquina cliente,
incluyendo todos los datos ya migrados (empresas, cuentas, asientos, etc).

---

## RESUMEN RAPIDO

1. Instalar Python 3.11+
2. Copiar la carpeta `vero_contable` al cliente
3. Crear entorno virtual
4. Instalar dependencias
5. Ejecutar `IniciarContabilidad.bat`

---

## Paso 1: Instalar Python en la maquina cliente

### 1.1 Descargar Python

1. Abrir el navegador e ir a: **https://www.python.org/downloads/**
2. Click en el boton amarillo **"Download Python 3.xx"** (la version mas reciente)
3. Guardar el archivo en Descargas

### 1.2 Instalar Python

1. Ejecutar el archivo descargado (doble click en `python-3.xx.x-amd64.exe`)
2. **MUY IMPORTANTE:** En la primera pantalla, marcar la casilla:

   ☑ **"Add python.exe to PATH"**

   (Esta opcion esta ABAJO de todo, NO olvidar marcarla!)

3. Click en **"Install Now"**
4. Esperar que termine (puede tardar 1-2 minutos)
5. Click en **"Close"**

### 1.3 Verificar que Python se instalo correctamente

1. Presionar **Windows + R**
2. Escribir `cmd` y presionar Enter
3. En la ventana negra, escribir:
   ```
   python --version
   ```
4. Debe mostrar algo como: `Python 3.11.9` o similar
5. Si dice "no se reconoce como comando", reinstalar Python marcando la opcion del PATH

---

## Paso 2: Copiar el Sistema al Cliente

### 2.1 Preparar el pendrive o carpeta de red

En tu maquina (donde ya funciona el sistema), copiar **TODA** la carpeta:

```
C:\APE\VERO_CONTABLE\VERO CONTABLE\CONTA_2\vero_contable
```

Esta carpeta contiene:
- `app/` - Codigo del sistema
- `vero_contable.db` - Base de datos con TODOS los datos migrados
- `requirements.txt` - Lista de dependencias
- `run.py` - Archivo principal
- `.env` - Configuracion
- Otros archivos necesarios

**IMPORTANTE:** Copiar TODO, incluyendo el archivo `vero_contable.db` que tiene los datos.

### 2.2 Pegar en la maquina cliente

1. Conectar el pendrive en la maquina cliente
2. Crear una carpeta en C:\ llamada `Contabilidad`:
   ```
   C:\Contabilidad
   ```
3. Copiar TODO el contenido de la carpeta `vero_contable` dentro de `C:\Contabilidad`

Al terminar, la estructura debe quedar asi:
```
C:\Contabilidad\
    ├── app\
    │   ├── blueprints\
    │   ├── models\
    │   ├── templates\
    │   └── ...
    ├── .env
    ├── .gitignore
    ├── IniciarContabilidad.bat
    ├── INSTALACION_WINDOWS.md
    ├── README.md
    ├── requirements.txt
    ├── run.py
    └── vero_contable.db       <-- BASE DE DATOS CON TODOS LOS DATOS
```

---

## Paso 3: Crear el Entorno Virtual

**NOTA:** El entorno virtual (`venv`) NO se copia porque depende de cada maquina.
Hay que crearlo nuevo en el cliente.

### 3.1 Abrir CMD como Administrador

1. Presionar **Windows + R**
2. Escribir `cmd` y presionar **Ctrl + Shift + Enter** (esto lo abre como administrador)
3. Si pregunta "Desea permitir...?" click en **Si**

### 3.2 Navegar a la carpeta del sistema

Escribir:
```
cd C:\Contabilidad
```

### 3.3 Crear el entorno virtual

Escribir:
```
python -m venv venv
```

Esperar unos segundos. No muestra nada si funciona correctamente.

### 3.4 Verificar que se creo

Escribir:
```
dir venv
```

Debe mostrar carpetas como `Include`, `Lib`, `Scripts`

---

## Paso 4: Activar el Entorno Virtual e Instalar Dependencias

### 4.1 Activar el entorno virtual

Escribir:
```
venv\Scripts\activate
```

Ahora debe aparecer `(venv)` al inicio de la linea:
```
(venv) C:\Contabilidad>
```

### 4.2 Instalar las dependencias

Escribir:
```
pip install -r requirements.txt
```

Esto descargara e instalara todos los paquetes necesarios.
Puede tardar 2-5 minutos dependiendo de la conexion a internet.

Veran muchas lineas de texto. Al final debe decir algo como:
```
Successfully installed Flask-x.x.x ...
```

---

## Paso 5: Probar el Sistema

### 5.1 Iniciar el servidor

Con el entorno virtual activado (debe verse `(venv)`), escribir:
```
python run.py
```

Debe mostrar algo como:
```
==================================================
  SISTEMA DE CONTABILIDAD - Vero Contable
==================================================
Servidor iniciando en: http://127.0.0.1:5000
```

### 5.2 Abrir el navegador

1. Abrir **Chrome**, **Firefox** o **Edge**
2. Ir a la direccion: **http://127.0.0.1:5000**
3. Debe aparecer la pantalla de login con estilo Windows XP

### 5.3 Iniciar sesion

- **Usuario:** `admin`
- **Contrasena:** `admin`

### 5.4 Verificar los datos

1. Despues de iniciar sesion, ir a **"Cambiar Empresa"**
2. Deben aparecer todas las empresas migradas (8 empresas)
3. Seleccionar una empresa
4. Ir a **"Plan de Cuentas"** - deben verse las cuentas
5. Ir a **"Asientos"** - deben verse los asientos

---

## Paso 6: Crear Acceso Directo para Uso Diario

El archivo `IniciarContabilidad.bat` ya viene configurado y funciona automaticamente
desde cualquier carpeta donde se copie el sistema.

### Crear acceso directo en el Escritorio

1. Ir a la carpeta donde se instalo el sistema (ej: `C:\Contabilidad`)
2. Click derecho en `IniciarContabilidad.bat`
3. Seleccionar **"Enviar a"** → **"Escritorio (crear acceso directo)"**
4. Ahora hay un icono en el escritorio para iniciar el sistema

---

## Uso Diario del Sistema

### Para iniciar el sistema:

1. Doble click en **"IniciarContabilidad.bat"** (o el acceso directo)
2. Se abre una ventana negra (CMD) - NO CERRARLA
3. Se abre automaticamente el navegador con el sistema
4. Iniciar sesion con usuario y contrasena

### Para cerrar el sistema:

1. Cerrar el navegador
2. En la ventana negra (CMD), presionar **Ctrl + C**
3. Cerrar la ventana

### IMPORTANTE:

- La ventana negra debe permanecer abierta mientras se usa el sistema
- Si se cierra la ventana negra, el sistema deja de funcionar

---

## Datos Incluidos

El sistema ya incluye todos los datos migrados:

| Contenido | Cantidad |
|-----------|----------|
| Empresas | 8 |
| Cuentas contables | 805+ |
| Asientos | 6162+ |
| Ejercicios fiscales | Varios |

---

## Credenciales de Acceso

| Usuario | Contrasena | Rol |
|---------|------------|-----|
| admin | admin | Administrador |

**RECOMENDACION:** Cambiar la contrasena despues de la primera instalacion.
(Menu usuario → Cambiar Contrasena)

---

## Solucion de Problemas

### "python" no se reconoce como comando

**Causa:** Python no se agrego al PATH durante la instalacion.

**Solucion:**
1. Desinstalar Python (Panel de control → Programas)
2. Volver a instalar Python
3. MARCAR la opcion **"Add python.exe to PATH"**

---

### Error "No module named flask" o similar

**Causa:** Las dependencias no se instalaron correctamente.

**Solucion:**
1. Abrir CMD
2. Navegar a la carpeta: `cd C:\Contabilidad`
3. Activar entorno: `venv\Scripts\activate`
4. Reinstalar: `pip install -r requirements.txt`

---

### El navegador muestra "No se puede acceder a este sitio"

**Causa:** El servidor no esta corriendo.

**Solucion:**
1. Verificar que la ventana negra (CMD) este abierta
2. Verificar que diga "Servidor iniciando en..."
3. Si hay error, leer el mensaje y buscar la solucion

---

### La base de datos esta vacia (no hay empresas)

**Causa:** No se copio el archivo `vero_contable.db`

**Solucion:**
1. Verificar que existe el archivo `C:\Contabilidad\vero_contable.db`
2. El archivo debe tener aproximadamente 2.3 MB de tamano
3. Si no existe, copiar desde la maquina original

---

### Puerto 5000 en uso

**Causa:** Otro programa esta usando el puerto 5000.

**Solucion:**
1. Editar el archivo `run.py`
2. Buscar la linea que dice `port=5000`
3. Cambiar por `port=5001`
4. Acceder a: http://127.0.0.1:5001

---

## Resumen de Archivos Importantes

| Archivo | Descripcion |
|---------|-------------|
| `vero_contable.db` | Base de datos SQLite con todos los datos |
| `run.py` | Archivo principal para iniciar el servidor |
| `.env` | Configuracion del sistema |
| `requirements.txt` | Lista de dependencias de Python |
| `IniciarContabilidad.bat` | Script para iniciar facilmente |
| `app/templates/base.html` | Template visual (tema Windows XP) |

---

## Contacto / Soporte

En caso de problemas, contactar al administrador del sistema.

---

*Sistema Contabilidad - Vero Contable v1.0*
*Tema visual: Windows XP Luna*
