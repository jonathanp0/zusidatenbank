#coding=utf8
import ntpath

import django_tables2 as tables

from .models import *
from .helpers.columns import *

class StreckenModuleTable(tables.Table):
    name = tables.LinkColumn()
    nachbaren_count = tables.Column(verbose_name='Nachbar Module', order_by=('nachbaren_count','name'))
    fahrplan_count = tables.Column(verbose_name='Fahrpläne', order_by=('fahrplan_count','name'))

    class Meta:
        model = StreckenModule
        exclude = ('standorte', 'fehlende_nachbaren')
        sequence = ('name', 'path', 'nachbaren_count', 'fahrplan_count')
        order_by = ('name',)
        attrs = {'class': 'table table-striped table-hover'}
        row_attrs = {'class': lambda record: 'danger' if not record.nachbaren_count else 'warning' if not record.fahrplan_count else None}

class FuehrerstandTable(tables.Table):
  name = tables.LinkColumn()
  mit_afb = tables.BooleanColumn(verbose_name='AFB')
  zugsicherung = ArrayListColumn(choices=Fuehrerstand.ZUGSICHERUNG_CHOICES)
  sifa = ArrayListColumn(choices=Fuehrerstand.SIFA_CHOICES)
  tuer_system = ArrayListColumn(verbose_name='Türsteuerung',orderable=False,choices=Fuehrerstand.TUER_CHOICES)
  schleuderschutz = ArrayBooleanColumn()
  #notbremse_system = ArrayBooleanColumn(verbose_name='Notbremse')
  fahrzeug_count = tables.Column(verbose_name='Fahrzeugnutzen', order_by=('fahrzeug_count','name'))
  zug_count = tables.Column(verbose_name='Fahrplanzüge', order_by=('zug_count','name'))

  class Meta:
        model = Fuehrerstand
        exclude = ('path','notbremse_system')
        order_by = ('name',)
        attrs = {'class': 'table table-striped table-hover'}
        row_attrs = {'class': lambda record: 'danger' if not record.fahrzeug_count else 'warning' if not record.zug_count else None}

class FahrplanZugTable(tables.Table):
    name = tables.LinkColumn()
    nummer = ArrayListColumn(seperator=' ')
    deko_zug = tables.BooleanColumn(verbose_name='Deko')
    fz_max_speed = SpeedColumn(verbose_name='Speed Max*')
    anfang_zeit = tables.DateTimeColumn(short=True)
    gesamt_zeit = tables.Column(verbose_name='Gesamt Fahrzeit')
    masse = tables.Column(verbose_name='Masse*')
    laenge = tables.Column(verbose_name='Laenge*')
    bremse_percentage = tables.Column(verbose_name='Brems%*')
    steuerfahrzeug = tables.Column(verbose_name='Fahrzeug')
    zeit_bewegung = tables.Column(verbose_name='Zeit in Bewegung')

    def render_gesamt_zeit(self, value):
        return "{0:02}:{1:02}".format(value.seconds//3600, (value.seconds//60)%60)

    def render_zeit_bewegung(self, value):
        return "{0:02}:{1:02}".format(value.seconds//3600, (value.seconds//60)%60)

    def render_is_reisezug(self, value):
        return 'Reisezug' if value else 'Güterzug'

    def render_masse(self, value):
        return "{0} t".format(int(value/1000))

    def render_laenge(self, value):
        return "{0} m".format(int(value))

    def render_bremse_percentage(self, value):
        return "{0} %".format(int(value*100))

    def render_steuerfahrzeug(self, value, record):
        if record.triebfahrzeug and record.triebfahrzeug != value:
            return "{0}/{1}".format(value, record.triebfahrzeug)
        else:
            return value

    class Meta:
        model = FahrplanZug
        sequence = ('name', 'gattung', 'nummer', 'zug_lauf', 'is_reisezug', 'fz_max_speed', 'deko_zug', 'masse', 'laenge', 'bremse_percentage', 'steuerfahrzeug', 'anfang_zeit', 'gesamt_zeit', 'zeit_bewegung')
        exclude = ('fahrzeug_tree','path', 'fahrplan_gruppe', 'speed_zug', 'speed_anfang', 'bild', 'deko', 'bremsstellung', 'triebfahrzeug', 'is_reisezug')
        order_by = ('name',)
        attrs = {'class': 'table table-striped table-hover'}
        row_attrs = {'class': lambda record: 'danger' if record.deko_zug else None}

class FahrplanTable(tables.Table):
    path = tables.LinkColumn(text=lambda r: r.path.replace('Timetables\\','').replace('Deutschland\\',''))
    anfang = tables.DateTimeColumn(format='D d.m.Y H:i')
    module_count = tables.Column(verbose_name='Modules')
    zug_count = tables.Column(verbose_name='Züge', order_by=('zug_count','name'))

    class Meta:
        model = Fahrplan
        exclude = ('name',)
        order_by = ('path',)
        attrs = {'class': 'table table-striped table-hover'}

class FahrzeugTable(tables.Table):
    root_file = tables.LinkColumn(verbose_name='File', text = lambda r : ntpath.basename(r.root_file))
    variant = tables.Column()
    speed_max = SpeedColumn(verbose_name='Speed Max')
    antrieb = ArrayListColumn(choices=FahrzeugVariante.ANTRIEB_CHOICES)
    masse = tables.TemplateColumn('{{ value }} kg')
    laenge = tables.TemplateColumn('{{ value|floatformat }} m')
    zug_count = tables.Column(verbose_name='Züge*')

    class Meta:
        model = FahrzeugVariante
        exclude = ('id', 'einsatz_ab', 'einsatz_bis', 'bremse', 'tuersystem', 'fuehrerstand', 'neben_id', 'haupt_id', 'masse','laenge', 'stromabnehmer_hoehe', 'ls3_datei', 'bild_klein')
        sequence = ('root_file', 'variant', 'br', 'beschreibung','farbgebung','speed_max','antrieb','neigetechnik','dekozug', 'zug_count')
        attrs = {'class': 'table table-striped table-hover'}
        row_attrs = {'class': lambda record: 'danger' if not record.zug_count else 'warning' if record.dekozug else 'active' if len(record.antrieb) else None}

class AutorTable(tables.Table):
    name = tables.LinkColumn()
    module_count = tables.Column(verbose_name='Streckenmodule')
    fahrplan_count = tables.Column(verbose_name='Fahrpläne')
    ftd_count = tables.Column(verbose_name='Führerstande')
    fz_count = tables.Column(verbose_name='Fahrzeug Variante')

    class Meta:
        model = Autor
        exclude = ('email',)
        attrs = {'class': 'table table-striped table-hover'}
