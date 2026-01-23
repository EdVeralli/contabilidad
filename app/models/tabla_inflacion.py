"""TablaInflacion (Inflation Index) model."""
from app.extensions import db


class TablaInflacion(db.Model):
    """Model for inflation index tables."""

    __tablename__ = 'tabla_inflacion'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    codigo = db.Column(db.String(1), nullable=False)  # Inflation table code
    anio = db.Column(db.SmallInteger, nullable=False)
    titulo = db.Column(db.String(50))

    # Monthly indexes
    indice_01 = db.Column(db.Numeric(15, 6), default=0)
    indice_02 = db.Column(db.Numeric(15, 6), default=0)
    indice_03 = db.Column(db.Numeric(15, 6), default=0)
    indice_04 = db.Column(db.Numeric(15, 6), default=0)
    indice_05 = db.Column(db.Numeric(15, 6), default=0)
    indice_06 = db.Column(db.Numeric(15, 6), default=0)
    indice_07 = db.Column(db.Numeric(15, 6), default=0)
    indice_08 = db.Column(db.Numeric(15, 6), default=0)
    indice_09 = db.Column(db.Numeric(15, 6), default=0)
    indice_10 = db.Column(db.Numeric(15, 6), default=0)
    indice_11 = db.Column(db.Numeric(15, 6), default=0)
    indice_12 = db.Column(db.Numeric(15, 6), default=0)

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'codigo', 'anio', name='uk_empresa_tabla_anio'),
    )

    def get_indice(self, mes):
        """Get index for a specific month (1-12)."""
        if 1 <= mes <= 12:
            return getattr(self, f'indice_{mes:02d}')
        return 0

    def set_indice(self, mes, valor):
        """Set index for a specific month (1-12)."""
        if 1 <= mes <= 12:
            setattr(self, f'indice_{mes:02d}', valor)

    def get_all_indices(self):
        """Get all monthly indices as a list."""
        return [self.get_indice(m) for m in range(1, 13)]

    def __repr__(self):
        return f'<TablaInflacion {self.codigo} {self.anio}>'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'codigo': self.codigo,
            'anio': self.anio,
            'titulo': self.titulo,
            'indices': {
                'enero': float(self.indice_01) if self.indice_01 else 0,
                'febrero': float(self.indice_02) if self.indice_02 else 0,
                'marzo': float(self.indice_03) if self.indice_03 else 0,
                'abril': float(self.indice_04) if self.indice_04 else 0,
                'mayo': float(self.indice_05) if self.indice_05 else 0,
                'junio': float(self.indice_06) if self.indice_06 else 0,
                'julio': float(self.indice_07) if self.indice_07 else 0,
                'agosto': float(self.indice_08) if self.indice_08 else 0,
                'septiembre': float(self.indice_09) if self.indice_09 else 0,
                'octubre': float(self.indice_10) if self.indice_10 else 0,
                'noviembre': float(self.indice_11) if self.indice_11 else 0,
                'diciembre': float(self.indice_12) if self.indice_12 else 0
            }
        }
