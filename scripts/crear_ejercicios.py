#!/usr/bin/env python
"""
Script para crear los Ejercicios fiscales automaticamente
a partir de los asientos ya migrados.

Para cada empresa, crea un Ejercicio por cada año calendario
que aparezca en al menos un asiento (fecha_inicio=yyyy-01-01, fecha_fin=yyyy-12-31).

Uso:
    python scripts/crear_ejercicios.py
    python scripts/crear_ejercicios.py --empresa APERG
"""
import os
import sys
import argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Empresa, Asiento, Ejercicio


def crear_ejercicios_empresa(emp):
    """Crea los ejercicios de una empresa basados en las fechas de sus asientos."""
    # Obtener los años distintos de los asientos
    asientos = Asiento.query.filter_by(empresa_id=emp.id).all()
    if not asientos:
        print(f'[{emp.codigo}] sin asientos, no se crean ejercicios')
        return 0

    anios = sorted({a.fecha.year for a in asientos if a.fecha})

    print(f'[{emp.codigo}] años detectados: {anios[0]} a {anios[-1]} ({len(anios)} años con movimientos)')

    creados = 0
    for anio in anios:
        # Chequear si ya existe
        existing = Ejercicio.query.filter_by(empresa_id=emp.id, anio=anio).first()
        if existing:
            continue
        ej = Ejercicio(
            empresa_id=emp.id,
            anio=anio,
            fecha_inicio=date(anio, 1, 1),
            fecha_fin=date(anio, 12, 31),
            cerrado=False,
        )
        db.session.add(ej)
        creados += 1

    db.session.commit()
    print(f'[{emp.codigo}] ejercicios creados: {creados}')
    return creados


def main():
    parser = argparse.ArgumentParser(description='Crea ejercicios fiscales automaticamente')
    parser.add_argument('--empresa', help='Codigo de empresa unica (opcional)')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.empresa:
            emps = Empresa.query.filter_by(codigo=args.empresa).all()
        else:
            emps = Empresa.query.all()

        if not emps:
            print('No se encontraron empresas')
            sys.exit(1)

        total_creados = 0
        for emp in emps:
            total_creados += crear_ejercicios_empresa(emp)

        print()
        print(f'TOTAL ejercicios creados: {total_creados}')


if __name__ == '__main__':
    main()
