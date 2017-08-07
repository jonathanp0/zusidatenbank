import django_tables2 as tables

from .models import *
from .helpers.columns import *

class StreckenModuleTable(tables.Table):
    name = tables.LinkColumn()
    nachbaren_count = tables.Column()

    class Meta:
        model = StreckenModule
        exclude = ('standorte',)
        sequence = ('name', 'path', 'nachbaren_count')
        order_by = ('name',)
        attrs = {'class': 'table table-striped table-hover'}

class FuehrerstandTable(tables.Table):
  name = tables.LinkColumn()
  mit_afb = tables.BooleanColumn(verbose_name='AFB')
  zugsicherung = ArrayListColumn()
  sifa = ArrayListColumn()
  tuer_system = ArrayListColumn(verbose_name='Türsteuerung',orderable=False)
  schleuderschutz = ArrayBooleanColumn()
  notbremse_system = ArrayBooleanColumn(verbose_name='Notbremse')

  class Meta:
        model = Fuehrerstand
        exclude = ('path',)
        order_by = ('name',)
        attrs = {'class': 'table table-striped table-hover'}

class FahrplanZugTable(tables.Table):
    name = tables.LinkColumn()
    is_reisezug = tables.BooleanColumn(verbose_name='Reisezug')
    zug_lauf = tables.Column(verbose_name='Lauf')
    deko = tables.BooleanColumn(verbose_name='Dekozug')
    fz_max_speed = tables.Column(verbose_name='Speed Max')

    class Meta:
        model = FahrplanZug
        sequence = ('name', 'gattung', 'nummer', 'zug_lauf', 'is_reisezug', 'fz_max_speed', 'speed_anfang', 'deko')
        exclude = ('fahrzeug_tree','path', 'fahrplan_gruppe', 'speed_zug')
        order_by = ('name',)
        attrs = {'class': 'table table-striped table-hover'}
        row_attrs = {'class': lambda record: 'danger' if record.deko else None}