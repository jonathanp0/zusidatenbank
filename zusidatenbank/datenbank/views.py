from django.views import generic
from django.db.models import Count, Min, Max, Sum, F, Q, Value, CharField, Subquery, OuterRef, Case, When
from django.db.models.functions import Least, Greatest, Concat, Coalesce

from .models import *
from .tables import *
from .forms import *

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
        return object.annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speed_max')), 
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

class FahrplanZugList(Annotater, SingleTableView):
    table_class = FahrplanZugTable
    template_name = 'fahrplanzug/list.html'

    def get_queryset(self):
        form = ZugSearchForm(self.request.GET)
        if not form.is_valid():
            form = None

        qs = self.annotateFahrplanZug(FahrplanZug.objects)

        if form:
            if(form.cleaned_data['gattung']):
                qs = qs.filter(gattung__in=form.cleaned_data['gattung'])
            if(form.cleaned_data['nummer']):
                qs = qs.filter(nummer=form.cleaned_data['nummer'])
            if(form.cleaned_data['zugart']):
                qs = qs.filter(is_reisezug=form.cleaned_data['zugart'])
            if(form.cleaned_data['zuglauf']):
                qs = qs.filter(zug_lauf__icontains=form.cleaned_data['zuglauf'])
            if(form.cleaned_data['dekozug'] and form.cleaned_data['dekozug'] != '-1'):
                qs = qs.filter(deko=form.cleaned_data['dekozug'])
            if(form.cleaned_data['anfang']):
                qs = qs.filter(speed_anfang__gt=form.cleaned_data['anfang'])
            if(form.cleaned_data['maximalgeschwindigkeit']):
                bound = form.cleaned_data['maximalgeschwindigkeit']
                if bound.lower:
                    qs = qs.filter(fz_max_speed__gte=form.cleaned_data['maximalgeschwindigkeit'].lower)
                if bound.upper:
                    qs = qs.filter(fz_max_speed__lte=form.cleaned_data['maximalgeschwindigkeit'].upper)
            if(form.cleaned_data['eintragort']):
                qs = qs.filter(eintraege__ort=form.cleaned_data['eintragort'])
            if(form.cleaned_data['fahrplan']):
                qs = qs.filter(fahrplaene__path__in=form.cleaned_data['fahrplan'])
            if(form.cleaned_data['baureihe']):
                qs = qs.filter(fahrzeuge__br=form.cleaned_data['baureihe'])
            if(form.cleaned_data['antrieb']):
                qs = qs.filter(fahrzeuge__antrieb__overlap=form.cleaned_data['antrieb'])
            if(form.cleaned_data['neigezug']):
                qs = qs.filter(fahrzeuge__neigetechnik=form.cleaned_data['neigezug'])

        return qs

class FahrplanZugDetail(generic.DetailView):
    template_name = 'fahrplanzug/detail.html'
    queryset = FahrplanZug.objects.annotate(zug_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speed_max')), fz_max_speed=Min('fahrzeuge__speed_max'))

class FahrzeugList(Annotater, SingleTableView):
    table_class = FahrzeugTable
    template_name = 'fahrzeug/list.html'

    def get_queryset(self):
        qs = self.annotateFahrzeug(FahrzeugVariante.objects)

        if 'root_file' in self.kwargs:
            qs = qs.filter(root_file=self.kwargs['root_file'])
        
        form = FahrzeugSearchForm(self.request.GET)

        if form.is_valid():
            if(form.cleaned_data['baureihe']):
                qs = qs.filter(br=form.cleaned_data['baureihe'])
            if(form.cleaned_data['deko'] and form.cleaned_data['deko'] != '-1'):
                qs = qs.filter(dekozug=form.cleaned_data['deko'])
            if(form.cleaned_data['beschreibung']):
                qs = qs.filter(beschreibung__icontains=form.cleaned_data['beschreibung'])
            if(form.cleaned_data['farbgebung']):
                qs = qs.filter(farbgebung__icontains=form.cleaned_data['farbgebung'])
            if(form.cleaned_data['einsatz']):
                qs = qs.filter(Q(einsatz_ab__gte=form.cleaned_data['einsatz']) & Q(einsatz_bis__lte=form.cleaned_data['einsatz']))
            if(form.cleaned_data['masse']):
                bound = form.cleaned_data['masse']
                if bound.lower:
                    qs = qs.filter(masse__gte=form.cleaned_data['masse'].lower)
                if bound.upper:
                    qs = qs.filter(masse__lte=form.cleaned_data['masse'].upper)
            if(form.cleaned_data['laenge']):
                bound = form.cleaned_data['laenge']
                if bound.lower:
                    qs = qs.filter(laenge__gte=form.cleaned_data['laenge'].lower)
                if bound.upper:
                    qs = qs.filter(laenge__lte=form.cleaned_data['laenge'].upper)
            if(form.cleaned_data['maximalgeschwindigkeit']):
                bound = form.cleaned_data['maximalgeschwindigkeit']
                if bound.lower:
                    qs = qs.filter(speed_max__gte=form.cleaned_data['maximalgeschwindigkeit'].lower)
                if bound.upper:
                    qs = qs.filter(speed_max__lte=form.cleaned_data['maximalgeschwindigkeit'].upper)
            if(form.cleaned_data['antrieb']):
                qs = qs.filter(antrieb__overlap=form.cleaned_data['antrieb'])
            if(form.cleaned_data['neigetechnik']):
                qs = qs.filter(neigetechnik=form.cleaned_data['neigetechnik'])


        return qs

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
        return (FahrplanZugTable(self.get_object().zuege.annotate(zug_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speed_max')), fz_max_speed=Min('fahrzeuge__speed_max'))),
                StreckenModuleTable(StreckenModule.objects.annotate(nachbaren_count=Count('nachbaren', distinct=True),fahrplan_count=Count('fahrplaene__path', distinct=True)).filter(fahrplaene__path=self.get_object().path)))

class IndexView(generic.TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
            context = super(IndexView, self).get_context_data(**kwargs)

            context['zug_form'] = ZugSearchForm()
            context['fstand_form'] = FStandSearchForm()
            context['fahrzeug_form'] = FahrzeugSearchForm()

            context['zug_count'] = FahrplanZug.objects.all().count()
            context['fahrzeug_count'] = FahrzeugVariante.objects.all().count()
            context['module_count'] = StreckenModule.objects.all().count()
            context['fstand_count'] = Fuehrerstand.objects.all().count()
            return context

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
