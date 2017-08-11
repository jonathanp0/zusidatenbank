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
        return (StreckenModuleTable(self.get_object().nachbaren.annotate(nachbaren_count=Count('nachbaren'))),
                FahrplanTable(self.get_object().fahrplaene))


class FuehrerstandList(SingleTableView):
    queryset = Fuehrerstand.objects.annotate(fahrzeug_count=Count('fahrzeuge', distinct=True),zug_count=Count('fahrzeuge__fahrplanzuege', distinct=True))

    table_class = FuehrerstandTable
    template_name = 'fuehrerstand/list.html'

class FuehrerstandDetail(generic.DetailView):

    model = Fuehrerstand
    template_name = 'fuehrerstand/detail.html'

class FahrplanZugList(SingleTableView):
    queryset = FahrplanZug.objects.annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speedMax')))
    table_class = FahrplanZugTable
    template_name = 'fahrplanzug/list.html'

class FahrzeugList(SingleTableView):
    queryset = FahrzeugVariante.objects.annotate(variant=Concat(F('haupt_id'), Value('/'), F('neben_id'),output_field=CharField()), zug_count=Count('fahrplanzuege'))
    table_class = FahrzeugTable
    template_name = 'fahrzeug/list.html'

class FahrzeugDetail(generic.DetailView):
    model = FahrzeugVariante
    template_name = 'fahrzeug/detail.html'

    def get_object(self):
        return self.get_queryset().filter(**self.kwargs).get()

    
