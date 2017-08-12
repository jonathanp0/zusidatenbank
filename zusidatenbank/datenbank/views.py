from django.views import generic
from django.db.models import Count, Min, F, Value, CharField
from django.db.models.functions import Least, Concat

from .models import *
from .tables import *

from django_tables2 import SingleTableView, MultiTableMixin

# Create your views here.

class StreckenModuleList(SingleTableView):
    table_class = StreckenModuleTable
    queryset = StreckenModule.objects.annotate(nachbaren_count=Count('nachbaren', distinct=True),fahrplan_count=Count('fahrplaene',distinct=True))
    template_name = 'streckenmodule/list.html'

class StreckenModuleDetail(MultiTableMixin, generic.DetailView):

    model = StreckenModule
    template_name = 'streckenmodule/detail.html'

    def get_table_pagination(self, table):
        return False

    def get_tables(self):
        return (StreckenModuleTable(self.get_object().nachbaren.annotate(nachbaren_count=Count('nachbaren', distinct=True),fahrplan_count=Count('fahrplaene',distinct=True))),
                FahrplanTable(self.get_object().fahrplaene))


class FuehrerstandList(SingleTableView):
    queryset = Fuehrerstand.objects.annotate(fahrzeug_count=Count('fahrzeuge', distinct=True),zug_count=Count('fahrzeuge__fahrplanzuege', distinct=True))

    table_class = FuehrerstandTable
    template_name = 'fuehrerstand/list.html'

class FuehrerstandDetail(MultiTableMixin, generic.DetailView):

    model = Fuehrerstand
    template_name = 'fuehrerstand/detail.html'

    def get_tables(self):
        fstand = self.get_object()
        return (FahrzeugTable(fstand.fahrzeuge.annotate(variant=Concat(F('haupt_id'), Value('/'), F('neben_id'),output_field=CharField()), zug_count=Count('fahrplanzuege')).distinct()),
                FahrplanZugTable(FahrplanZug.objects.filter(fahrzeuge__fuehrerstand=fstand).annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speedMax')))))

class FahrplanZugList(SingleTableView):
    queryset = FahrplanZug.objects.annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speedMax')))
    table_class = FahrplanZugTable
    template_name = 'fahrplanzug/list.html'

class FahrplanZugDetail(generic.DetailView):
    template_name = 'fahrplanzug/detail.html'
    queryset = FahrplanZug.objects.annotate(zug_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speedMax')), fz_max_speed=Min('fahrzeuge__speedMax'))

class FahrzeugList(SingleTableView):
    table_class = FahrzeugTable
    template_name = 'fahrzeug/list.html'

    def get_queryset(self):
        base = FahrzeugVariante.objects
        if 'root_file' in self.kwargs:
            base = base.filter(root_file=self.kwargs['root_file'])
        return base.annotate(variant=Concat(F('haupt_id'), Value('/'), F('neben_id'),output_field=CharField()), zug_count=Count('fahrplanzuege'))

class FahrzeugDetail(MultiTableMixin, generic.DetailView):
    model = FahrzeugVariante
    template_name = 'fahrzeug/detail.html'

    def get_object(self):
        return self.get_queryset().select_related('fuehrerstand').filter(**self.kwargs).get()

    def get_plain_object(self):
        return self.get_queryset().filter(**self.kwargs).get()

    def get_tables(self):
        fahrzeug = self.get_plain_object()
        return (FahrplanZugTable(fahrzeug.fahrplanzuege.annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speedMax')))),
                FahrplanTable(Fahrplan.objects.filter(zuege__fahrzeuge__id=fahrzeug.id).distinct()))

class FahrplanList(SingleTableView):
    queryset = Fahrplan.objects.annotate(zug_count=Count('zuege', distinct=True),module_count=Count('strecken_modules', distinct=True))
    table_class = FahrplanTable
    template_name = 'fahrplan/list.html'

class FahrplanDetail(MultiTableMixin, generic.DetailView):

    model = Fahrplan
    template_name = 'fahrplan/detail.html'

    def get_tables(self):
        return (FahrplanZugTable(self.get_object().zuege.annotate(zug_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speedMax')), fz_max_speed=Min('fahrzeuge__speedMax'))),
                StreckenModuleTable(StreckenModule.objects.annotate(nachbaren_count=Count('nachbaren', distinct=True),fahrplan_count=Count('fahrplaene__path', distinct=True)).filter(fahrplaene__path=self.get_object().path)))

