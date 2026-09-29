# Plan de Migración — Sistema Clipper → Sistema Flask

Documento que describe la estrategia completa para migrar **todas las empresas** del sistema contable Clipper (basado en DBF) al sistema nuevo Flask/SQLite.

---

## 1. Contexto

El sistema Clipper viejo (`\CONTABLE\CONTA_2\`) empezó a fallar con el error `DBFCMX/1021 Data width error` al ejecutar la opción **"Regenerar Saldos"** del menú. Adicionalmente, el informe **"Sumas y Saldos"** muestra asteriscos (`***`) en las cuentas grandes porque el formato de display quedó chico frente a los saldos actuales inflados.

Ambos problemas tienen la misma raíz: los campos numéricos del DBF y los formatos hardcodeados del código Clipper quedaron chicos frente a la inflación argentina acumulada. Se podrían arreglar tocando el código y recompilando, pero se decidió avanzar directamente con la **migración definitiva al sistema nuevo**, que ya usa `Numeric(15,2)` (máximo 999.999.999.999,99) y no tiene esta limitación.

---

## 2. Alcance

Se migran **todas las empresas** del sistema viejo, no solo APE Rio Gallegos:

### Empresas con datos operativos (prioridad ALTA)

| Empresa | Código | Cuentas (Abr-2025) | Asientos (Abr-2025) |
|---------|--------|-------------------|--------------------|
| APE | APE01 | 223 | 4.599 |
| APE Rio Gallegos | APERG | 238 | 342 |
| CIPELE 3 | DIRE3 | 121 | 1.222 |
| La Rioja | MEDO01 | 223 | 0 |

### Empresas vacías (prioridad BAJA, solo migrar estructura)

| Empresa | Código |
|---------|--------|
| Empresa Principal | DEFAULT |
| CIPELE 1 | DIRE1 |
| CIPELE 2 | DIRE2 |
| CIPELE 10 | DIRE10 |

Estas se migran igual para mantener la estructura del multi-empresa, aunque no tengan asientos.

---

## 3. Ruta de los archivos fuente

El sistema Clipper vive en la PC de APE (Windows 98) en la ruta:

```
C:\CONTABLE\CONTA_2\<CODIGO_EMPRESA>\
```

Con los siguientes DBFs por empresa:

| DBF | Contenido | Ancho crítico |
|-----|-----------|---------------|
| `PLAN.DBF` | Plan de cuentas | `ULTSAL N(13,2)` |
| `TRANSACC.DBF` | Movimientos/Asientos | `IMPORTE N(12,2)` |
| `SALDOS.DBF` | Saldos por período | `SALDO N(13,2)` |
| `LEYENDA.DBF` | Textos/leyendas | — |
| `TABLAIN.DBF` | Tablas de inflación | `INDICE01-12 N(15,6)` |
| `AJUSTA.DBF` | Ajustes por inflación | — |
| `EMPRESA.DBF` | Datos de la empresa | — |

---

## 4. Etapas de la migración

### Etapa 0 — Preparación (antes del día D)

- [x] Sistema nuevo desarrollado y probado con snapshot de Abril 2025.
- [x] Script de migración `scripts/migrar_dbf.py` funcionando.
- [x] Sistema instalable con `Instalar_Contabilidad.bat` en la PC del cliente.
- [x] Backup automático diario configurado (`Backup_Contabilidad.bat`).
- [ ] Comunicar a APE la fecha de corte y qué hacer entretanto.
- [ ] Instruir a APE: **NO usar "Regenerar Saldos"** en el Clipper hasta el corte.

### Etapa 1 — Congelar la carga en Clipper

- [ ] Definir un día/hora de corte con APE.
- [ ] Aviso previo (3-5 días) para que cierren asientos pendientes.
- [ ] El día D: cerrar el sistema Clipper y no volver a cargar allí.

### Etapa 2 — Obtener los DBFs actualizados

- [ ] En la PC de APE, copiar TODA la carpeta `C:\CONTABLE\CONTA_2\` a CD o pendrive.
- [ ] Verificar tamaños (los TRANSACC.DBF grandes deberían pesar 1-3 MB c/u).
- [ ] Verificar que estén los DBFs de todas las 8 empresas listadas.
- [ ] Trasladar a la PC de trabajo.

### Etapa 3 — Migrar al sistema nuevo

En la PC de trabajo:

```powershell
# 1. Copiar los DBFs a una carpeta conocida
Copy-Item -Recurse "D:\CONTA_2" "C:\APE\CONTA_2_ACTUAL"

# 2. Backup de la base actual del sistema nuevo (por las dudas)
cd "C:\Errores APE\contabilidad"
python -c "import shutil; shutil.copy('vero_contable.db', f'vero_contable_pre_migracion_{__import__(\"datetime\").datetime.now():%Y-%m-%d_%H%M%S}.db')"

# 3. Activar entorno virtual
venv\Scripts\activate

# 4. Correr la migracion para cada empresa
python scripts\migrar_dbf.py --empresa APE01  --path "C:\APE\CONTA_2_ACTUAL\APE01"
python scripts\migrar_dbf.py --empresa APERG  --path "C:\APE\CONTA_2_ACTUAL\APERG"
python scripts\migrar_dbf.py --empresa DIRE3  --path "C:\APE\CONTA_2_ACTUAL\DIRE3"
python scripts\migrar_dbf.py --empresa MEDO01 --path "C:\APE\CONTA_2_ACTUAL\MEDO01"
python scripts\migrar_dbf.py --empresa DEFAULT --path "C:\APE\CONTA_2_ACTUAL\DEFAULT"
python scripts\migrar_dbf.py --empresa DIRE1  --path "C:\APE\CONTA_2_ACTUAL\DIRE1"
python scripts\migrar_dbf.py --empresa DIRE2  --path "C:\APE\CONTA_2_ACTUAL\DIRE2"
python scripts\migrar_dbf.py --empresa DIRE10 --path "C:\APE\CONTA_2_ACTUAL\DIRE10"
```

**Nota importante:** el script actual usa `filter_by(...).first()` para evitar duplicar. O sea que si se re-corre, no duplica registros. Pero para una migración limpia se recomienda **borrar los datos de la empresa antes** de re-migrar (o borrar toda la base y arrancar de cero). Esto se decide al momento del corte.

### Etapa 4 — Validación en el sistema nuevo

En la PC de trabajo, arrancar el sistema:

```powershell
cd "C:\Errores APE\contabilidad"
IniciarContabilidad.bat
```

Chequeos por empresa:

- [ ] Cambiar de empresa desde el menú y probar cada una.
- [ ] Verificar cantidad de cuentas en Plan de Cuentas.
- [ ] Verificar cantidad de asientos en el listado de Asientos.
- [ ] Sacar informe **Sumas y Saldos** — que no haya asteriscos y los totales cierren.
- [ ] Sacar **Libro Mayor** de una cuenta con muchos movimientos.
- [ ] Sacar **Libro Diario** del último mes.
- [ ] Verificar **Balance General**.

Comparar contra los últimos informes válidos del Clipper (para APE01 y DIRE3, que tienen historia larga).

### Etapa 5 — Deploy en APE

- [ ] Actualizar el pendrive con la última versión del sistema y la nueva base:
  ```powershell
  robocopy "C:\Errores APE\contabilidad" "D:\contabilidad" /E /XD venv __pycache__ .git .claude /PURGE
  Copy-Item "C:\Errores APE\Instalar_Contabilidad.bat" "D:\Instalar_Contabilidad.bat" -Force
  Copy-Item "C:\Errores APE\Backup_Contabilidad.bat" "D:\Backup_Contabilidad.bat" -Force
  ```
- [ ] Llevar el pendrive a APE.
- [ ] Instalar Python 3.11.9 desde `D:\installers\`.
- [ ] Ejecutar `D:\Instalar_Contabilidad.bat`.
- [ ] Verificar iconos de "Sistema Contabilidad" y "Backup Contabilidad" en Escritorio.
- [ ] Primera prueba: login (`admin`/`admin123`), cambiar empresa, ver Sumas y Saldos.

### Etapa 6 — Corte definitivo

- [ ] Que APE opere una semana en paralelo (cargar los mismos asientos en ambos sistemas para comparar).
- [ ] Al final de la semana, si no hay diferencias:
  - [ ] Congelar el Clipper (renombrar `CMENU.EXE` a `CMENU_OLD.EXE` para que no lo abran por error).
  - [ ] Toda carga nueva va al sistema Flask.
  - [ ] El Clipper queda solo para consulta histórica de años anteriores.

---

## 5. Plan de rollback

Si algo falla en la migración o en producción:

1. **Base de datos:** volver al backup `vero_contable_pre_migracion_YYYY-MM-DD_HHMMSS.db` (se hace en la Etapa 3).
2. **Sistema:** desinstalar el Flask de APE y volver a usar Clipper (renombrar `CMENU_OLD.EXE` a `CMENU.EXE`).
3. **DBFs:** los originales quedan intactos porque el script solo los LEE. No los modifica.

Riesgo: pérdida de asientos cargados en el sistema Flask entre el corte y el rollback. Mitigación: la semana de operación en paralelo (Etapa 6) es justamente para no depender solo del Flask hasta estar seguros.

---

## 6. Consideraciones técnicas

### Encoding

Los DBFs Clipper usan **CP850** (DOS Español). El script ya lo maneja con `DBF_ENCODING = 'cp850'` en `scripts/migrar_dbf.py`.

### Nombres alternativos de archivos

El script busca movimientos en varios nombres posibles: `MOVIM.DBF`, `TRANS.DBF`, `TRANSAC.DBF`. En la práctica, el archivo real es **`TRANSACC.DBF`** (con doble C). Si el script no lo encuentra, hay que renombrarlo antes de correr la migración, o agregar `TRANSACC.DBF` a la lista de nombres candidatos.

### Duplicados

El script usa `Plan.query.filter_by(empresa_id=X, cuenta=Y).first()` y `Asiento.query.filter_by(empresa_id=X, numero=Y).first()` para saltear registros ya existentes. Sin embargo, si un asiento cambió en el Clipper después de la primera migración, la nueva versión NO se actualiza — se ignora. Por eso conviene **empezar de una base limpia** para la migración final.

Para limpiar antes de re-migrar una empresa, ejecutar en el shell de Flask:

```python
# En Python, dentro del venv activado
from app import create_app, db
from app.models import Empresa, Plan, Asiento, AsientoLinea, Saldo
app = create_app()
with app.app_context():
    emp = Empresa.query.filter_by(codigo='APERG').first()
    if emp:
        AsientoLinea.query.filter(AsientoLinea.asiento_id.in_(
            db.session.query(Asiento.id).filter_by(empresa_id=emp.id)
        )).delete(synchronize_session=False)
        Asiento.query.filter_by(empresa_id=emp.id).delete()
        Plan.query.filter_by(empresa_id=emp.id).delete()
        Saldo.query.filter_by(empresa_id=emp.id).delete()
        db.session.commit()
        print(f'Limpiado {emp.codigo}')
```

### Recálculo de saldos post-migración

Después de importar los asientos, el sistema Flask **recalcula los saldos por su cuenta** — no depende de `SALDOS.DBF` del Clipper. Esto es una ventaja: si el Clipper tenía saldos desactualizados o corruptos (por el error de Regenerar Saldos), el sistema nuevo los calcula bien desde cero.

---

## 7. Cronograma tentativo

| Día | Actividad | Responsable |
|-----|-----------|-------------|
| Semana 1 (lunes-jueves) | APE sigue cargando en Clipper (sin Regenerar Saldos) | APE |
| Semana 1 (viernes) | APE cierra asientos, se copian los DBFs al CD | APE + yo |
| Sábado / domingo | Migración al sistema nuevo, validación de reportes | yo |
| Semana 2 (lunes) | Deploy en APE, capacitación básica | yo + APE |
| Semana 2 (mar-vier) | Operación en paralelo, comparar resultados | APE |
| Semana 3 (lunes) | Corte definitivo, Clipper solo consulta | APE + yo |

---

## 8. Checklist final antes del corte

- [ ] Backup completo de `C:\CONTABLE\CONTA_2\` (los DBFs originales del Clipper) guardado en 2 lugares distintos.
- [ ] Backup del `vero_contable.db` post-migración guardado en 2 lugares distintos.
- [ ] Sistema nuevo instalado y probado en la PC de APE.
- [ ] Los usuarios de APE saben usar el nuevo sistema (login, cambio de empresa, cargar asiento, ver informes).
- [ ] Backup automático diario funcionando (Task Scheduler configurado).
- [ ] Documentación entregada.

---

## 9. Post-migración: mejoras futuras

Una vez estabilizado el nuevo sistema, evaluar:

- Exportar informes a PDF/Excel directamente desde el sistema (Sumas y Saldos, Balance).
- Cierre automático de ejercicios.
- Multi-usuario con roles diferenciados (contador, auditor, admin).
- Ajuste por inflación automático (ya está estructurado, hay que activarlo).
- Backup en la nube (OneDrive / Google Drive) además del local.

---

## 10. Contacto y soporte

- **Repositorio del sistema:** https://github.com/EdVeralli/contabilidad
- **Documentación de instalación:** `INSTALACION_WINDOWS.md`
- **Documentación de sesión de desarrollo:** `../BITACORA_SESION_2026-05-06.md` (fuera del repo)

---

*Documento generado el 2026-09-28. Actualizar a medida que se avance en las etapas.*
