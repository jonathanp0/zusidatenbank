import django_tables2 as tables

from .models import *
from .helpers.columns import *

class StreckenModuleTable(tables.Table):
    name = tables.LinkColumn()
    nachbaren_count = tables.Column(verbose_name='Nachbar Modules')
    fahrplan_count = tables.Column(verbose_name='Fahrpläne')

    class Meta:
        model = StreckenModule
        exclude = ('standorte',)
        sequence = ('name', 'path', 'nachbaren_count', 'fahrplan_count')
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
  fahrzeug_count = tables.Column(verbose_name='Fahrzeugnutzen')
  zug_count = tables.Column(verbose_name='Fahrplanzüge')

  class Meta:
        model = Fuehrerstand
        exclude = ('path',)
        order_by = ('name',)
        attrs = {'class': 'table table-striped table-hover'}
        row_attrs = {'class': lambda record: 'danger' if not record.fahrzeug_count else 'warning' if not record.zug_count else None}

class FahrplanZugTable(tables.Table):
    name = tables.LinkColumn()
    deko = tables.BooleanColumn(verbose_name='Dekozug')
    fz_max_speed = SpeedColumn(verbose_name='Speed Max*')
    speed_anfang = SpeedColumn()

    def render_is_reisezug(self, value):
        return 'Reisezug' if value else 'Güterzug'

    class Meta:
        model = FahrplanZug
        sequence = ('name', 'gattung', 'nummer', 'zug_lauf', 'is_reisezug', 'fz_max_speed', 'speed_anfang', 'deko')
        exclude = ('fahrzeug_tree','path', 'fahrplan_gruppe', 'speed_zug')
        order_by = ('name',)
        attrs = {'class': 'table table-striped table-hover'}
        row_attrs = {'class': lambda record: 'danger' if record.deko else None}

class FahrplanTable(tables.Table):
    #name = tables.LinkColumn()
    #nachbaren_count = tables.Column(verbose_name='Nachbar Modules')

    class Meta:
        model = Fahrplan
        #exclude = ('standorte',)
        #sequence = ('name', 'path', 'nachbaren_count')
        order_by = ('name',)
        attrs = {'class': 'table table-striped table-hover'}