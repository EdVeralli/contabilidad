#!/usr/bin/env python
"""
Script de migracion de datos desde DBF (Clipper) a MySQL.

Uso:
    python scripts/migrar_dbf.py --empresa DIRE1 --path "C:\APE\VERO_CONTABLE\VERO CONTABLE\CONTA_2\DIRE1"

Este script migra:
    - Plan de cuentas (PLAN.DBF)
    - Transacciones/Asientos (MOVIM.DBF o TRANS.DBF)
    - Leyendas (LEYENDAS.DBF si existe)
    - Tablas de inflacion (TABLAS.DBF si existe)
"""

import os
import sys
import argparse
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dbfread import DBF
from app import create_app, db
from app.models import (
    Empresa, Plan, Asiento, AsientoLinea, Saldo,
    TablaInflacion, Leyenda
)


# DBF encoding for DOS/Clipper files
DBF_ENCODING = 'cp850'


def log(message, level='INFO'):
    """Print log message with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] [{level}] {message}')


def read_dbf(filepath, encoding=DBF_ENCODING):
    """Read DBF file and return records."""
    if not os.path.exists(filepath):
        log(f'Archivo no encontrado: {filepath}', 'WARNING')
        return []

    try:
        table = DBF(filepath, encoding=encoding, ignore_missing_memofile=True)
        return list(table)
    except Exception as e:
        log(f'Error leyendo {filepath}: {e}', 'ERROR')
        return []


def migrar_plan(empresa_id, dbf_path):
    """Migrate chart of accounts from PLAN.DBF.

    Expected DBF structure:
        CUENTA  C(10)   - Account code
        NOMBRE  C(60)   - Account name
        NIVEL   N(1)    - Level (1-9)
        IMPUTA  C(1)    - Imputable S/N
        MONETA  C(1)    - Monetary S/N
        AJUSTE  C(1)    - Adjustable S/N
        MOVI    C(1)    - D=Debit, A=Credit
        ULTSAL  N(15,2) - Last balance
        ULTMOV  D       - Last movement date
    """
    plan_file = os.path.join(dbf_path, 'PLAN.DBF')
    records = read_dbf(plan_file)

    if not records:
        log('No se encontro PLAN.DBF o esta vacio', 'WARNING')
        return 0

    log(f'Migrando {len(records)} cuentas del plan...')
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

            plan = Plan(
                empresa_id=empresa_id,
                cuenta=cuenta_codigo,
                nombre=str(record.get('NOMBRE', '')).strip()[:60],
                nivel=int(record.get('NIVEL', 1) or 1),
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
            log(f'Error migrando cuenta {record}: {e}', 'ERROR')
            continue

    db.session.commit()
    log(f'Migradas {count} cuentas')
    return count


def migrar_transacciones(empresa_id, dbf_path):
    """Migrate journal entries from MOVIM.DBF or TRANS.DBF.

    Expected DBF structure:
        NUCONTROL N(8)   - Entry number (groups lines)
        FECHA     D      - Date
        CUENTA    C(10)  - Account code
        ITEM      N(3)   - Line number
        IMPORTE   N(15,2)- Amount
        MOVIM     C(1)   - D=Debit, H=Credit
        LEYENDA   C(50)  - Description
        APERTURA  C(1)   - S if opening entry
    """
    # Try different possible file names
    trans_files = ['MOVIM.DBF', 'TRANS.DBF', 'TRANSAC.DBF']
    records = []

    for filename in trans_files:
        filepath = os.path.join(dbf_path, filename)
        records = read_dbf(filepath)
        if records:
            log(f'Usando archivo: {filename}')
            break

    if not records:
        log('No se encontro archivo de transacciones', 'WARNING')
        return 0

    log(f'Procesando {len(records)} lineas de movimientos...')

    # Build lookup for accounts
    cuentas = {p.cuenta: p.id for p in Plan.query.filter_by(empresa_id=empresa_id).all()}

    # Group by nucontrol
    asientos_dict = {}
    for record in records:
        try:
            nucontrol = int(record.get('NUCONTROL', 0) or 0)
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
                log(f'Cuenta no encontrada: {cuenta_codigo} en asiento {nucontrol}', 'WARNING')
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
            log(f'Error procesando registro: {e}', 'ERROR')
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
                es_apertura=data['apertura']
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
                log(f'Procesados {count} asientos...')

        except Exception as e:
            log(f'Error creando asiento {numero}: {e}', 'ERROR')
            db.session.rollback()
            continue

    db.session.commit()
    log(f'Migrados {count} asientos')
    return count


def migrar_tablas_inflacion(empresa_id, dbf_path):
    """Migrate inflation tables from TABLAS.DBF.

    Expected DBF structure:
        CODIGO    C(1)   - Table code
        ANIO      N(4)   - Year
        TITULO    C(50)  - Title
        INDICE01-12 N(15,6) - Monthly indices
    """
    tablas_file = os.path.join(dbf_path, 'TABLAS.DBF')
    records = read_dbf(tablas_file)

    if not records:
        log('No se encontro TABLAS.DBF', 'WARNING')
        return 0

    log(f'Migrando {len(records)} tablas de inflacion...')
    count = 0

    for record in records:
        try:
            codigo = str(record.get('CODIGO', 'A')).strip()[:1]
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

            # Set monthly indices
            for mes in range(1, 13):
                campo = f'INDICE{mes:02d}'
                valor = record.get(campo, 0) or 0
                tabla.set_indice(mes, float(valor))

            db.session.add(tabla)
            count += 1

        except Exception as e:
            log(f'Error migrando tabla: {e}', 'ERROR')
            continue

    db.session.commit()
    log(f'Migradas {count} tablas de inflacion')
    return count


def recalcular_saldos(empresa_id):
    """Recalculate all balances from migrated entries."""
    from app.services.saldo_service import SaldoService

    log('Recalculando saldos...')
    SaldoService.recalcular_saldos(empresa_id)
    log('Saldos recalculados')


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrar datos de DBF a MySQL')
    parser.add_argument('--empresa', required=True, help='Codigo de empresa (ej: DIRE1)')
    parser.add_argument('--path', required=True, help='Ruta a la carpeta con archivos DBF')
    parser.add_argument('--skip-plan', action='store_true', help='Omitir migracion del plan')
    parser.add_argument('--skip-trans', action='store_true', help='Omitir migracion de transacciones')
    parser.add_argument('--skip-tablas', action='store_true', help='Omitir migracion de tablas')
    parser.add_argument('--skip-saldos', action='store_true', help='Omitir recalculo de saldos')

    args = parser.parse_args()

    # Validate path
    if not os.path.isdir(args.path):
        log(f'Directorio no encontrado: {args.path}', 'ERROR')
        sys.exit(1)

    # Create app context
    app = create_app()
    with app.app_context():
        # Get or create empresa
        empresa = Empresa.query.filter_by(codigo=args.empresa.upper()).first()
        if not empresa:
            log(f'Creando empresa: {args.empresa}')
            empresa = Empresa(
                codigo=args.empresa.upper(),
                nombre=f'Empresa {args.empresa}',
                activa=True
            )
            db.session.add(empresa)
            db.session.commit()

        log(f'Empresa: {empresa.codigo} (ID: {empresa.id})')
        log(f'Ruta DBF: {args.path}')
        log('=' * 50)

        # Run migrations
        if not args.skip_plan:
            migrar_plan(empresa.id, args.path)

        if not args.skip_trans:
            migrar_transacciones(empresa.id, args.path)

        if not args.skip_tablas:
            migrar_tablas_inflacion(empresa.id, args.path)

        if not args.skip_saldos:
            recalcular_saldos(empresa.id)

        log('=' * 50)
        log('Migracion completada!')


if __name__ == '__main__':
    main()
