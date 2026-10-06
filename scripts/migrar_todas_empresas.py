#!/usr/bin/env python
"""
Script de migracion completa de TODAS las empresas desde los DBFs actualizados.

Hace un WIPE TOTAL de la base (preserva solo usuarios) y re-importa todo
desde los DBFs del sistema Clipper.

Uso:
    python scripts/migrar_todas_empresas.py --path "C:\\APE\\CONTA_2_ACTUAL"
    python scripts/migrar_todas_empresas.py --path "..." --only APERG
    python scripts/migrar_todas_empresas.py --path "..." --no-backup
"""
import os
import sys
import argparse
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date

from app import create_app, db
from app.models import (
    Empresa, Plan, Asiento, AsientoLinea, Saldo,
    TablaInflacion, Leyenda
)
# Modelos opcionales que pueden existir
try:
    from app.models import Ejercicio
except ImportError:
    Ejercicio = None
try:
    from app.models import AsientoTipo, AsientoTipoLinea
except ImportError:
    AsientoTipo = None
    AsientoTipoLinea = None

# Importar funciones del script existente
from migrar_dbf import (
    migrar_plan, migrar_transacciones, migrar_tablas_inflacion,
    log, DBF_ENCODING
)


# Empresas a migrar (deben coincidir con nombres de subcarpetas, case-insensitive)
EMPRESAS = {
    'APE01':   'APE',
    'APERG':   'APE RIO GALLEGOS',
    'DIRE3':   'CIPELE 3',
    'MEDO01':  'LA RIOJA',
    'DIRE1':   'CIPELE 1',
    'DIRE2':   'CIPELE 2',
    'DIRE10':  'CIPELE 10',
    'DIRE4':   'CIPELE 4',
    'DEFAULT': 'Empresa Principal',
}


def hacer_backup_db():
    """Backup de la DB actual con timestamp."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'vero_contable.db')
    if not os.path.exists(db_path):
        log('No hay base previa, se creara una nueva.', 'INFO')
        return None
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = db_path.replace('.db', f'_pre_migracion_{ts}.db')
    shutil.copy2(db_path, backup)
    log(f'Backup creado: {os.path.basename(backup)}')
    return backup


def wipe_total():
    """Borra TODOS los datos contables (preserva usuarios para poder loguearse)."""
    log('')
    log('========== WIPE TOTAL de la base ==========')
    # Orden importante por foreign keys: hijos primero, padres al final
    tablas = []
    if AsientoTipoLinea:
        tablas.append((AsientoTipoLinea, 'asiento_tipo_linea'))
    if AsientoTipo:
        tablas.append((AsientoTipo, 'asiento_tipo'))
    tablas += [
        (AsientoLinea, 'asiento_linea'),
        (Asiento, 'asiento'),
        (Saldo, 'saldo'),
        (Plan, 'plan'),
        (Leyenda, 'leyenda'),
        (TablaInflacion, 'tabla_inflacion'),
    ]
    if Ejercicio:
        tablas.append((Ejercicio, 'ejercicio'))
    tablas.append((Empresa, 'empresa'))

    for model, nombre in tablas:
        try:
            n = model.query.delete()
            log(f'   {nombre:<22} borrado: {n:>8,} registros')
        except Exception as e:
            log(f'   {nombre:<22} ERROR: {e}', 'WARNING')
            db.session.rollback()

    db.session.commit()
    log('WIPE completado. (usuarios preservados para poder loguearse)')
    log('')


def crear_empresa(codigo, nombre):
    """Crea una empresa nueva (asume que ya se hizo wipe)."""
    emp = Empresa(codigo=codigo, nombre=nombre, activa=True)
    db.session.add(emp)
    db.session.commit()
    log(f'[{codigo}] empresa creada: {nombre}')
    return emp


def migrar_empresa(codigo, nombre, base_path):
    """Migra una empresa completa (asume que la base esta limpia)."""
    carpeta = os.path.join(base_path, codigo)
    # Intentar tambien con nombre en minusculas (hay un 'medo01' en el disco)
    if not os.path.exists(carpeta):
        carpeta_lower = os.path.join(base_path, codigo.lower())
        if os.path.exists(carpeta_lower):
            carpeta = carpeta_lower
        else:
            log(f'[{codigo}] carpeta no encontrada ({carpeta}), se saltea', 'WARNING')
            return 0, 0

    log('')
    log(f'========== Migrando {codigo} ({nombre}) ==========')
    log(f'Origen: {carpeta}')

    emp = crear_empresa(codigo, nombre)

    n_plan = migrar_plan(emp.id, carpeta)
    n_trans = migrar_transacciones(emp.id, carpeta)
    migrar_tablas_inflacion(emp.id, carpeta)
    crear_ejercicios(emp)

    return n_plan, n_trans


def crear_ejercicios(emp):
    """Crea ejercicios por año calendario basados en las fechas de los asientos."""
    if not Ejercicio:
        return 0
    asientos = Asiento.query.filter_by(empresa_id=emp.id).all()
    if not asientos:
        return 0
    anios = sorted({a.fecha.year for a in asientos if a.fecha})
    creados = 0
    for anio in anios:
        existing = Ejercicio.query.filter_by(empresa_id=emp.id, anio=anio).first()
        if existing:
            continue
        db.session.add(Ejercicio(
            empresa_id=emp.id,
            anio=anio,
            fecha_inicio=date(anio, 1, 1),
            fecha_fin=date(anio, 12, 31),
            cerrado=False,
        ))
        creados += 1
    db.session.commit()
    if creados:
        log(f'[{emp.codigo}] ejercicios creados: {creados} (años {anios[0]}-{anios[-1]})')
    return creados


def main():
    parser = argparse.ArgumentParser(description='Migracion completa de todas las empresas desde DBFs')
    parser.add_argument('--path', required=True, help='Ruta base donde estan las carpetas por empresa (ej: C:\\APE\\CONTA_2_ACTUAL)')
    parser.add_argument('--only', help='Codigo de empresa unica a migrar (opcional)')
    parser.add_argument('--no-backup', action='store_true', help='Saltear el backup previo')
    parser.add_argument('--no-wipe', action='store_true', help='No borrar la base previa (solo agregar - no recomendado)')
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        log(f'ERROR: no existe la ruta base: {args.path}', 'ERROR')
        sys.exit(1)

    app = create_app()
    with app.app_context():
        if not args.no_backup:
            hacer_backup_db()

        if not args.no_wipe and not args.only:
            # WIPE total solo si se migran todas (no cuando se pide --only)
            wipe_total()
        elif args.only:
            log(f'MODO --only: no se hace WIPE total, se migra solo {args.only}', 'WARNING')

        empresas_a_migrar = {args.only: EMPRESAS[args.only]} if args.only else EMPRESAS

        resumen = []
        for codigo, nombre in empresas_a_migrar.items():
            try:
                n_plan, n_trans = migrar_empresa(codigo, nombre, args.path)
                resumen.append((codigo, n_plan, n_trans))
            except Exception as e:
                log(f'[{codigo}] ERROR: {e}', 'ERROR')
                db.session.rollback()
                resumen.append((codigo, 0, 0))

        # Reporte final
        log('')
        log('=' * 60)
        log('RESUMEN DE MIGRACION')
        log('=' * 60)
        log(f'{"EMPRESA":<10} {"CUENTAS":>10} {"ASIENTOS":>10}')
        log('-' * 60)
        for codigo, n_plan, n_trans in resumen:
            log(f'{codigo:<10} {n_plan:>10,} {n_trans:>10,}')
        log('=' * 60)

        total_plan = sum(x[1] for x in resumen)
        total_trans = sum(x[2] for x in resumen)
        log(f'{"TOTAL":<10} {total_plan:>10,} {total_trans:>10,}')


if __name__ == '__main__':
    main()
