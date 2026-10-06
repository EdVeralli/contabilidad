# Deploy en APE — Guía paso a paso

Instalación del sistema Contabilidad migrado en la PC de APE (reemplaza la versión anterior).

**Fecha:** 2026-10-06
**Versión:** Base migrada con todas las empresas del Clipper (11.159 asientos, 1.226 cuentas, 75 ejercicios)

---

## Antes de empezar

### Checklist

- [ ] Pendrive listo con los siguientes archivos en la raíz:
  - `Instalar_Contabilidad.bat`
  - `Backup_Contabilidad.bat`
  - carpeta `contabilidad\` (con la base `vero_contable.db` migrada ~3.9 MB)
- [ ] En la PC de APE: Python 3.11.9 ya instalado (verificar en CMD: `python --version`).
- [ ] Internet disponible en APE (necesario para que pip baje las dependencias).
- [ ] Avisar al cliente que el sistema va a estar fuera de servicio ~10 minutos.

### Si Python NO está instalado en APE

En ese caso también vas a necesitar el instalador de Python. En tu PC:

```powershell
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "D:\installers\python-3.11.9-amd64.exe"
```

Después en APE: doble click en `D:\installers\python-3.11.9-amd64.exe` → marcar **"Add python.exe to PATH"** → Install Now. Reiniciar la PC si Python no responde después.

---

## PASO 1 — Preparar la PC de APE

### 1.1 Cerrar el sistema viejo

Si está corriendo el sistema Flask:

- Buscar la ventana negra (CMD) con mensajes de Flask.
- Apretar `Ctrl + C` para detenerlo.
- Cerrar la ventana negra.
- Cerrar el navegador si está abierto en `http://127.0.0.1:5000`.

### 1.2 Hacer backup de la base actual (por si acaso)

Aunque sabemos que no hay datos valiosos en APE, por las dudas:

```powershell
Copy-Item "C:\Contabilidad\vero_contable.db" "C:\Contabilidad\vero_contable.db.backup_pre_deploy" -Force
```

---

## PASO 2 — Conectar el pendrive y ejecutar el instalador

### 2.1 Conectar el pendrive

Enchufar en un puerto USB. Esperar que Windows lo reconozca y que aparezca la letra de unidad (usualmente `D:` o `E:` o `F:`).

### 2.2 Ejecutar el instalador

Abrir el Explorador de Windows → ir al pendrive → **doble click en `Instalar_Contabilidad.bat`**.

Si Windows pregunta si querés abrir un archivo de un dispositivo removible → **Sí**.

Si Windows Defender SmartScreen bloquea el .bat → click en **"Más información"** → **"Ejecutar de todas formas"**.

### 2.3 Seguir los 6 pasos del instalador

Se abre una ventana negra que muestra:

```
============================================================
   INSTALADOR SISTEMA CONTABILIDAD
============================================================
```

Y hace 6 pasos:

**Paso 1/6 — Verifica Python**
- Debe decir: `OK - Python 3.11.9`
- Si falla, instalar Python 3.11.9 (ver "Si Python NO está instalado" arriba).

**Paso 2/6 — Verifica archivos del pendrive**
- Debe decir: `OK`

**Paso 3/6 — Copia a `C:\Contabilidad\`**
- Como la carpeta ya existe, pregunta:
  ```
  ATENCION: La carpeta C:\Contabilidad ya existe.
  Desea sobrescribir el contenido? (S/N):
  ```
- **Escribí `S` y Enter.**
- Se copia todo (puede tardar 10-30 segundos).

**Paso 4/6 — Crea entorno virtual**
- Borra el `venv` anterior y crea uno nuevo. Tarda ~30 segundos.

**Paso 5/6 — Instala dependencias**
- Descarga Flask, SQLAlchemy, WeasyPrint, etc. desde internet.
- Tarda **2-5 minutos** (depende de la velocidad de internet).
- Ver muchas líneas tipo `Collecting...`, `Downloading...`, `Installing...`.
- Debe terminar con `OK`.

**Paso 6/6 — Crea accesos directos**
- Pone 2 iconos en el Escritorio y en el Menú Inicio:
  - **Sistema Contabilidad** (icono de carpeta)
  - **Backup Contabilidad** (icono de disquete)

### 2.4 Mensaje final

Al terminar, muestra:

```
============================================================
   INSTALACION COMPLETADA CORRECTAMENTE
============================================================

USO DIARIO (despues de prender la PC):

  1. Doble click en el icono "Sistema Contabilidad" del Escritorio
  2. El navegador se abre automaticamente con el sistema
  3. Iniciar sesion con las credenciales de abajo

============================================================
   CREDENCIALES DE ACCESO
============================================================

    Usuario:     admin
    Contrasena:  admin123

============================================================

Presione una tecla para continuar . . .
```

Apretar una tecla para cerrar.

---

## PASO 3 — Verificar que todo funciona

### 3.1 Arrancar el sistema

Doble click en el icono **"Sistema Contabilidad"** del Escritorio.

Debería pasar esto:
- Se abre una ventana negra (NO cerrarla mientras usás el sistema).
- Después de 5-10 segundos, se abre el navegador en `http://127.0.0.1:5000`.
- Aparece la pantalla de login con estilo Windows XP.

### 3.2 Login

- **Usuario:** `admin`
- **Contraseña:** `admin123`

Click en **Ingresar**.

### 3.3 Verificar empresas

Después del login:

1. Click en **"Cambiar Empresa"** (arriba a la derecha o en el menú lateral).
2. Debería mostrar la lista:
   - APE
   - APE RIO GALLEGOS
   - CIPELE 3
   - LA RIOJA
   - CIPELE 1
   - CIPELE 2
   - CIPELE 10
   - CIPELE 4
3. Click en **APE RIO GALLEGOS**.

### 3.4 Verificar Plan de Cuentas

Menú lateral → **Plan de Cuentas**.

Debe mostrar ~247 cuentas (incluyendo algunas "(RECUPERADA)" si hubo huérfanas).

### 3.5 Verificar Asientos

Menú lateral → **Asientos**.

Debe mostrar la pantalla con filtros (Ejercicio, Fecha Desde, Hasta, etc.) y los asientos cargados.

Seleccionar en el desplegable **Ejercicio** → debe haber 24 ejercicios (2002-2025).

### 3.6 ✅ EL TEST CLAVE — Sumas y Saldos

Esta es LA razón por la que migramos. Antes rompía con `Data Width Error` en el Clipper.

1. Menú lateral → **Informes → Sumas y Saldos**.
2. Dejar los filtros en default (fecha hasta hoy, todos los ejercicios).
3. Click en **Generar**.
4. **Verificar:**
   - ✅ El informe sale sin errores.
   - ✅ Headers "SUMAS / SALDOS / Debe / Haber / Deudor / Acreedor" en **blanco sobre gris oscuro**.
   - ✅ Montos se muestran con formato normal (ej: `11.865.677.608,74`), **sin asteriscos `***`**.
   - ✅ Totales de Debe y Haber **coinciden exactamente** al final.
   - ✅ Totales Deudor y Acreedor **coinciden exactamente**.
   - ✅ Mensaje verde: "**El balance esta cuadrado correctamente**".

**Totales esperados para APERG** (al 06/10/2026, todos los ejercicios):
- Total Debe = Total Haber = **$ 38.473.110.524,95**
- Total Deudor = Total Acreedor = **$ 363.183.768,68**

### 3.7 Opcional — Verificar otras pantallas

- **Informes → Libro Diario** (de un rango de fechas corto, ej: una semana).
- **Informes → Libro Mayor** (seleccionar una cuenta cualquiera).
- **Informes → Balance General** (de un ejercicio).

---

## PASO 4 — Probar también otras empresas

Opcional pero recomendado — verificar que las otras empresas con datos también funcionan:

1. Click en **"Cambiar Empresa"** → seleccionar **APE**.
2. Ir a **Informes → Sumas y Saldos** → **Generar**.
3. Confirmar que sale sin errores.

Repetir para **CIPELE 3** y **LA RIOJA**.

---

## PASO 5 — Configurar backup automático diario (opcional)

Si querés que se haga backup automático de la base todos los días (recomendado):

Abrir **PowerShell como Administrador** y correr:

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Contabilidad\Backup_Contabilidad.bat" -Argument "/S"
$trigger = New-ScheduledTaskTrigger -Daily -At 20:00
Register-ScheduledTask -TaskName "Backup Contabilidad Diario" -Action $action -Trigger $trigger -Description "Backup automatico de vero_contable.db"
```

(Cambiá `20:00` por la hora que prefieras. Por defecto va a las 20:00.)

Los backups quedan en `C:\Contabilidad\backups\` con nombre tipo `vero_contable_2026-10-06_200000.db`.

---

## PASO 6 — Expulsar el pendrive

Ya no se necesita. Expulsar de forma segura:

- Click en el icono de USB en la barra de tareas (abajo a la derecha).
- Click en **"Expulsar [nombre del pendrive]"**.
- Esperar el cartel "Es seguro retirar el hardware".
- Desconectar.

---

## PASO 7 — Entregar al cliente

Mostrar al usuario de APE:

- **Icono en el Escritorio:** "Sistema Contabilidad" → doble click para arrancar.
- **Login:** `admin` / `admin123` (sugerir cambiar la contraseña desde el menú del usuario).
- **Para cerrar:** cerrar la pestaña del navegador + cerrar la ventana negra con la X.
- **Importante:** la ventana negra debe quedar abierta mientras se usa el sistema. Si se cierra, el sistema deja de funcionar.
- **Backup:** si quiere hacer backup manual en cualquier momento, doble click en el icono **"Backup Contabilidad"** del Escritorio.

---

## Troubleshooting

### "python no se reconoce como comando"

Python no está instalado o no está en el PATH.

**Solución:**
1. Instalar Python desde `D:\installers\python-3.11.9-amd64.exe`.
2. **MARCAR la casilla "Add python.exe to PATH"** durante la instalación.
3. Reiniciar PowerShell/CMD y probar `python --version`.

### Error al instalar dependencias (paso 5)

**Causa:** Sin internet o pip viejo.

**Solución:**
1. Verificar que haya internet (abrir una página en el navegador).
2. En CMD como admin:
   ```
   cd C:\Contabilidad
   venv\Scripts\activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

### Puerto 5000 en uso

**Causa:** Otro programa usa el puerto.

**Solución:** editar `C:\Contabilidad\run.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```
Y acceder a `http://127.0.0.1:5001`.

### El navegador dice "No se puede acceder a este sitio"

**Causa:** El servidor Flask no está corriendo.

**Solución:**
1. Verificar que la ventana negra esté abierta y diga `Running on http://127.0.0.1:5000`.
2. Si no está, doble click en el icono "Sistema Contabilidad" del Escritorio.

### La pantalla de login se ve mal (letras invisibles, layout roto)

**Causa:** El navegador tiene cache viejo del fix de CSS.

**Solución:** `Ctrl + F5` para refrescar sin cache.

### Al abrir Sumas y Saldos aparecen asteriscos

**Causa:** Esto NO debería pasar en el sistema nuevo (es lo que pasaba en Clipper).

**Solución:** Si aparece, hacer captura de pantalla y escribirme — es un bug nuevo.

### No se ven los ejercicios en el desplegable

**Causa:** Los ejercicios no se crearon durante la migración.

**Solución:** En CMD:
```
cd C:\Contabilidad
venv\Scripts\activate
python scripts\crear_ejercicios.py
```

---

## Rollback (si todo salió mal)

Si por algún motivo necesitás volver a la versión anterior:

```powershell
# Detener el sistema Flask (Ctrl+C en la ventana negra, cerrarla)

# Restaurar la base vieja
Copy-Item "C:\Contabilidad\vero_contable.db.backup_pre_deploy" "C:\Contabilidad\vero_contable.db" -Force

# Volver a arrancar
C:\Contabilidad\IniciarContabilidad.bat
```

(La base vieja la hiciste en el Paso 1.2.)

---

## Contacto

Ante cualquier problema, mandar captura del error (pantalla negra del CMD o navegador) por chat.

---

*Guía de deploy generada el 2026-10-06*
