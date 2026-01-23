#!/usr/bin/env python
"""
Script de migracion automatica de TODAS las empresas desde DBF (Clipper) a SQLite/MySQL.

Este script:
    1. Lee EMPRESA.DBF para obtener todas las empresas
    2. Crea las empresas en la base de datos
    3. Para cada empresa, migra:
       - Plan de cuentas (PLAN.DBF)
       - Transacciones/Asientos (TRANSACC.DBF)
       - Tablas de inflacion (TABLAIN.DBF)
    4. Recalcula saldos
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dbfread import DBF
from app import create_app, db
from app.models import (
    Empresa, Plan, Asiento, AsientoLinea, Saldo,
    TablaInflacion, Leyenda, EstadoAsiento
)


# DBF encoding for DOS/Clipper files
DBF_ENCODING = 'cp850'

# Base path for DBF files
BASE_PATH = r'C:\APE\VERO_CONTABLE\VERO CONTABLE\CONTA_2'


def log(message, level='INFO'):
    """Print log message with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] [{level}] {message}')


def read_dbf(filepath, encoding=DBF_ENCODING):
    """Read DBF file and return records."""
    if not os.path.exists(filepath):
        return []

    try:
        table = DBF(filepath, encoding=encoding, ignore_missing_memofile=True)
        return list(table)
    except Exception as e:
        log(f'Error leyendo {filepath}: {e}', 'ERROR')
        return []


def migrar_empresas():
    """Read EMPRESA.DBF and create all empresas in database."""
    empresa_file = os.path.join(BASE_PATH, 'EMPRESA.DBF')
    records = read_dbf(empresa_file)

    if not records:
        log('No se encontro EMPRESA.DBF', 'ERROR')
        return []

    log(f'Encontradas {len(records)} empresas en EMPRESA.DBF')

    empresas_creadas = []

    for record in records:
        try:
            nombre = str(record.get('EMPRESA', '')).strip()
            directorio = str(record.get('DIRECTORIO', '')).strip()
            comentario = str(record.get('COMENTARIO', '')).strip()

            if not directorio:
                continue

            # Check if empresa already exists
            existing = Empresa.query.filter_by(codigo=directorio.upper()).first()

            if existing:
                log(f'Empresa ya existe: {directorio} - {nombre}')
                empresas_creadas.append({
                    'empresa': existing,
                    'directorio': directorio
                })
                continue

            empresa = Empresa(
                codigo=directorio.upper(),
                nombre=nombre[:100] if nombre else f'Empresa {directorio}',
                comentario=comentario[:200] if comentario else None,
                activa=True
            )
            db.session.add(empresa)
            db.session.flush()

            log(f'Creada empresa: {directorio} - {nombre}')
            empresas_creadas.append({
                'empresa': empresa,
                'directorio': directorio
            })

        except Exception as e:
            log(f'Error creando empresa: {e}', 'ERROR')
            continue

    db.session.commit()
    return empresas_creadas


def migrar_plan(empresa_id, dbf_path):
    """Migrate chart of accounts from PLAN.DBF."""
    plan_file = os.path.join(dbf_path, 'PLAN.DBF')
    records = read_dbf(plan_file)

    if not records:
        return 0

    log(f'  Migrando {len(records)} cuentas del plan...')
    count = 0

    for record in records:
        try:
            cuenta_codigo = str(record.get('CUENTA', '')).strip()
            if not cuenta_codigo:
                continue

            # Check if account already exists
            existing = Plan.query.filter_by(
                empresa_id=empresa_id,
                cuenta=cuenta_codigo
            ).first()

            if existing:
                continue

            # Get nivel - handle None or invalid values
            nivel = record.get('NIVEL')
            if nivel is None or nivel == '':
                nivel = 1
            else:
                try:
                    nivel = int(nivel)
                    if nivel < 1 or nivel > 9:
                        nivel = 1
                except:
                    nivel = 1

            plan = Plan(
                empresa_id=empresa_id,
                cuenta=cuenta_codigo[:10],
                nombre=str(record.get('NOMBRE', '')).strip()[:60] or 'Sin nombre',
                nivel=nivel,
                imputable=str(record.get('IMPUTA', 'N')).strip().upper()[:1] or 'N',
                monetaria=str(record.get('MONETA', 'N')).strip().upper()[:1] or 'N',
                ajustable=str(record.get('AJUSTE', 'N')).strip().upper()[:1] or 'N',
                tipo_saldo=str(record.get('MOVI', 'D')).strip().upper()[:1] or 'D',
                ultimo_saldo=Decimal(str(record.get('ULTSAL', 0) or 0)),
                ultimo_movimiento=record.get('ULTMOV'),
                activa=True
            )
            db.session.add(plan)
            count += 1

        except Exception as e:
            log(f'  Error migrando cuenta {record.get("CUENTA", "?")}: {e}', 'ERROR')
            continue

    db.session.commit()
    log(f'  Migradas {count} cuentas')
    return count


def migrar_transacciones(empresa_id, dbf_path):
    """Migrate journal entries from TRANSACC.DBF."""
    trans_file = os.path.join(dbf_path, 'TRANSACC.DBF')
    records = read_dbf(trans_file)

    if not records:
        return 0

    log(f'  Procesando {len(records)} lineas de movimientos...')

    # Build lookup for accounts
    cuentas = {p.cuenta: p.id for p in Plan.query.filter_by(empresa_id=empresa_id).all()}

    if not cuentas:
        log('  No hay cuentas en el plan para esta empresa', 'WARNING')
        return 0

    # Group by nucontrol
    asientos_dict = {}
    for record in records:
        try:
            nucontrol = record.get('NUCONTROL')
            if nucontrol is None:
                continue
            nucontrol = int(nucontrol or 0)
            if nucontrol == 0:
                continue

            if nucontrol not in asientos_dict:
                asientos_dict[nucontrol] = {
                    'fecha': record.get('FECHA'),
                    'apertura': str(record.get('APERTURA', 'N')).strip().upper() == 'S',
                    'lineas': []
                }

            cuenta_codigo = str(record.get('CUENTA', '')).strip()
            cuenta_id = cuentas.get(cuenta_codigo)

            if not cuenta_id:
                continue

            importe = Decimal(str(record.get('IMPORTE', 0) or 0))
            movim = str(record.get('MOVIM', 'D')).strip().upper()

            asientos_dict[nucontrol]['lineas'].append({
                'item': int(record.get('ITEM', 1) or 1),
                'cuenta_id': cuenta_id,
                'debe': importe if movim == 'D' else Decimal('0'),
                'haber': importe if movim == 'H' else Decimal('0'),
                'leyenda': str(record.get('LEYENDA', '')).strip()[:50]
            })

        except Exception as e:
            log(f'  Error procesando registro: {e}', 'ERROR')
            continue

    # Create entries
    count = 0
    for numero, data in sorted(asientos_dict.items()):
        try:
            # Check if entry already exists
            existing = Asiento.query.filter_by(
                empresa_id=empresa_id,
                numero=numero
            ).first()

            if existing:
                continue

            if not data['lineas']:
                continue

            asiento = Asiento(
                empresa_id=empresa_id,
                numero=numero,
                fecha=data['fecha'] or datetime.now().date(),
                es_apertura=data['apertura'],
                estado=EstadoAsiento.ACTIVO
            )
            db.session.add(asiento)
            db.session.flush()

            for linea_data in sorted(data['lineas'], key=lambda x: x['item']):
                linea = AsientoLinea(
                    asiento_id=asiento.id,
                    item=linea_data['item'],
                    cuenta_id=linea_data['cuenta_id'],
                    debe=linea_data['debe'],
                    haber=linea_data['haber'],
                    leyenda=linea_data['leyenda']
                )
                db.session.add(linea)

            count += 1

            # Commit in batches
            if count % 100 == 0:
                db.session.commit()

        except Exception as e:
            log(f'  Error creando asiento {numero}: {e}', 'ERROR')
            db.session.rollback()
            continue

    db.session.commit()
    log(f'  Migrados {count} asientos')
    return count


def migrar_tablas_inflacion(empresa_id, dbf_path):
    """Migrate inflation tables from TABLAIN.DBF."""
    # Try different possible file names
    for filename in ['TABLAIN.DBF', 'TABLAS.DBF', 'TABLA.DBF']:
        filepath = os.path.join(dbf_path, filename)
        records = read_dbf(filepath)
        if records:
            break

    if not records:
        return 0

    log(f'  Migrando {len(records)} tablas de inflacion...')
    count = 0

    for record in records:
        try:
            codigo = str(record.get('CODIGO', 'A')).strip()[:1] or 'A'
            anio = int(record.get('ANIO', 0) or 0)

            if anio == 0:
                continue

            # Check if table already exists
            existing = TablaInflacion.query.filter_by(
                empresa_id=empresa_id,
                codigo=codigo,
                anio=anio
            ).first()

            if existing:
                continue

            tabla = TablaInflacion(
                empresa_id=empresa_id,
                codigo=codigo,
                anio=anio,
                titulo=str(record.get('TITULO', '')).strip()[:50]
            )

            # Set monthly indices - try different field name formats
            for mes in range(1, 13):
                for campo_format in [f'INDICE{mes:02d}', f'INDICE_{mes:02d}', f'IND{mes:02d}']:
                    valor = record.get(campo_format)
                    if valor is not None:
                        tabla.set_indice(mes, float(valor or 0))
                        break

            db.session.add(tabla)
            count += 1

        except Exception as e:
            log(f'  Error migrando tabla: {e}', 'ERROR')
            continue

    db.session.commit()
    log(f'  Migradas {count} tablas de inflacion')
    return count


def recalcular_saldos(empresa_id):
    """Recalculate all balances from migrated entries."""
    log('  Recalculando saldos...')

    # Delete existing saldos for this empresa
    Saldo.query.filter_by(empresa_id=empresa_id).delete()
    db.session.commit()

    # Get all asientos with their lineas
    asientos = Asiento.query.filter_by(
        empresa_id=empresa_id,
        estado=EstadoAsiento.ACTIVO
    ).order_by(Asiento.fecha).all()

    saldos_dict = {}  # (cuenta_id, anio, mes) -> saldo

    for asiento in asientos:
        anio = asiento.fecha.year
        mes = asiento.fecha.month

        for linea in asiento.lineas:
            key = (linea.cuenta_id, anio, mes)
            if key not in saldos_dict:
                saldos_dict[key] = Decimal('0')
            saldos_dict[key] += linea.debe - linea.haber

    # Create saldo records
    for (cuenta_id, anio, mes), monto in saldos_dict.items():
        saldo = Saldo(
            empresa_id=empresa_id,
            cuenta_id=cuenta_id,
            anio=anio,
            mes=mes,
            saldo=monto
        )
        db.session.add(saldo)

    db.session.commit()
    log(f'  Creados {len(saldos_dict)} registros de saldos')


def main():
    """Main migration function."""
    log('=' * 60)
    log('MIGRACION AUTOMATICA DE DATOS CLIPPER A PYTHON/FLASK')
    log('=' * 60)

    # Create app context
    app = create_app()
    with app.app_context():
        # Step 1: Migrate empresas
        log('')
        log('PASO 1: Migrando empresas desde EMPRESA.DBF')
        log('-' * 40)
        empresas = migrar_empresas()

        if not empresas:
            log('No se encontraron empresas para migrar', 'ERROR')
            return

        # Step 2: For each empresa, migrate data
        log('')
        log('PASO 2: Migrando datos de cada empresa')
        log('-' * 40)

        total_cuentas = 0
        total_asientos = 0
        total_tablas = 0

        for emp_data in empresas:
            empresa = emp_data['empresa']
            directorio = emp_data['directorio']

            # Find the empresa directory
            emp_path = os.path.join(BASE_PATH, directorio)

            if not os.path.isdir(emp_path):
                # Try uppercase
                emp_path = os.path.join(BASE_PATH, directorio.upper())

            if not os.path.isdir(emp_path):
                # Try lowercase
                emp_path = os.path.join(BASE_PATH, directorio.lower())

            if not os.path.isdir(emp_path):
                log(f'Directorio no encontrado para {directorio}', 'WARNING')
                continue

            log('')
            log(f'>>> Empresa: {empresa.codigo} - {empresa.nombre}')
            log(f'    Directorio: {emp_path}')

            # Migrate plan
            cuentas = migrar_plan(empresa.id, emp_path)
            total_cuentas += cuentas

            # Migrate transactions
            asientos = migrar_transacciones(empresa.id, emp_path)
            total_asientos += asientos

            # Migrate inflation tables
            tablas = migrar_tablas_inflacion(empresa.id, emp_path)
            total_tablas += tablas

            # Recalculate balances
            if asientos > 0:
                recalcular_saldos(empresa.id)

        # Summary
        log('')
        log('=' * 60)
        log('RESUMEN DE MIGRACION')
        log('=' * 60)
        log(f'Empresas procesadas: {len(empresas)}')
        log(f'Total cuentas migradas: {total_cuentas}')
        log(f'Total asientos migrados: {total_asientos}')
        log(f'Total tablas inflacion: {total_tablas}')
        log('')
        log('Migracion completada!')
        log('')
        log('Para iniciar el sistema:')
        log('  cd vero_contable')
        log('  flask run')
        log('')


if __name__ == '__main__':
    main()
