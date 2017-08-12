from django.views import generic
from django.db.models import Count, Min, Max, Sum, F, Q, Value, CharField, Subquery, OuterRef, Case, When
from django.db.models.functions import Least, Greatest, Concat, Coalesce

from .models import *
from .tables import *

from django_tables2 import SingleTableView, MultiTableMixin

# Create your views here.

class Annotater(object):

    def annotateModule(self, object):
        return object.annotate(nachbaren_count=Count('nachbaren', distinct=True),fahrplan_count=Count('fahrplaene__path', distinct=True))

    def annotateFahrplan(self, object):
        return object.annotate(zug_count=Count('zuege', distinct=True),module_count=Count('strecken_modules', distinct=True))

    def annotateFahrzeug(self, object):
        return object.annotate(variant=Concat(F('haupt_id'), Value('/'), F('neben_id'),output_field=CharField()), zug_count=Count('fahrplanzuege'))

    def annotateFuehrerstand(self, object):
        return object.annotate(fahrzeug_count=Count('fahrzeuge', distinct=True),zug_count=Count('fahrzeuge__fahrplanzuege', distinct=True))

    def annotateFahrplanZug(self, object):
        return object.annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speedMax')), 
                         gesamt_zeit=Max(Coalesce('eintraege__an','eintraege__ab')) - Min(Coalesce('eintraege__ab','eintraege__an')))

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

class FuehrerstandDetail(Annotater, MultiTableMixin, generic.DetailView):

    model = Fuehrerstand
    template_name = 'fuehrerstand/detail.html'

    def get_tables(self):
        fstand = self.get_object()
        return (FahrzeugTable(fstand.fahrzeuge.annotate(variant=Concat(F('haupt_id'), Value('/'), F('neben_id'),output_field=CharField()), zug_count=Count('fahrplanzuege')).distinct()),
                FahrplanZugTable(self.annotateFahrplanZug(FahrplanZug.objects).filter(fahrzeuge__fuehrerstand=fstand)))

class FahrplanZugList(SingleTableView):
    queryset = FahrplanZug.objects.annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speedMax')), 
                                            gesamt_zeit=Max(Coalesce('eintraege__an','eintraege__ab')) - Min(Coalesce('eintraege__ab','eintraege__an')),
                                            )
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

class FahrzeugDetail(Annotater, MultiTableMixin, generic.DetailView):
    model = FahrzeugVariante
    template_name = 'fahrzeug/detail.html'

    def get_object(self):
        return self.get_queryset().select_related('fuehrerstand').filter(**self.kwargs).get()

    def get_plain_object(self):
        return self.get_queryset().filter(**self.kwargs).get()

    def get_tables(self):
        fahrzeug = self.get_plain_object()
        return (FahrplanZugTable(self.annotateFahrplanZug(fahrzeug.fahrplanzuege)),
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

class IndexView(generic.TemplateView):
    template_name = 'home.html'

class AutorList(SingleTableView):
    queryset = Autor.objects.annotate(module_count=Count('streckenmodule',distinct=True),
                                      ftd_count=Count('fuehrerstand', distinct=True),
                                      fahrplan_count=Count('fahrplan', distinct=True),
                                      fz_count=Count('fahrzeugvariante', distinct=True))
    table_class = AutorTable
    template_name = 'autor/list.html'

class AutorDetail(Annotater, MultiTableMixin, generic.DetailView):

    model = Autor
    template_name = 'autor/detail.html'

    def get_tables(self):
        return (StreckenModuleTable(self.annotateModule(self.get_object().streckenmodule_set)),
                FahrplanTable(self.annotateFahrplan(self.get_object().fahrplan_set)),
                FuehrerstandTable(self.annotateFuehrerstand(self.get_object().fuehrerstand_set)),
                FahrzeugTable(self.annotateFahrzeug(self.get_object().fahrzeugvariante_set))
                )
