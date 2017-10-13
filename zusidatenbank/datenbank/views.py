from django.views import generic
from django.db.models import Count, Min, Max, Sum, F, Q, Value, CharField, Subquery, OuterRef, Case, When
from django.db.models.functions import Least, Greatest, Concat, Coalesce
from django.conf import settings

from .models import *
from .tables import *
from .forms import *

from django_tables2 import SingleTableView, MultiTableMixin
from pytz import timezone
import datetime
from random import randint

def filterBooleanCheckbox(data):
        options = [False, False]
        for opt in data:
            options[int(opt)] = True
        if options[0] != options[1]:
            if options[0]:
                return 0
            elif options[1]:
                return 1
        return -1

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
        return object.annotate(position_count=Max('eintraege__position'),
                             deko_fahrzeuge=BoolOr('fahrzeuge__dekozug')
                    ).annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speed_max')), 
                               gesamt_zeit=Case(
                                    When(position_count=0, then=Value(datetime.timedelta(0))),
                                    default=Max(Coalesce('eintraege__an','eintraege__ab')) - Min(Coalesce('eintraege__ab','eintraege__an'))
                                  ),
                               anfang_zeit=Min(Coalesce('eintraege__an','eintraege__ab')),
                               deko_zug=Case(When(deko_fahrzeuge=True, then=True), default='deko'))


class StreckenModuleList(SingleTableView):
    table_class = StreckenModuleTable
    queryset = StreckenModule.objects.withTableStats()
    template_name = 'streckenmodule/list.html'

class StreckenModuleDetail(Annotater, MultiTableMixin, generic.DetailView):

    model = StreckenModule
    template_name = 'streckenmodule/detail.html'

    def get_table_pagination(self, table):
        return False

    def get_tables(self):
        return (StreckenModuleTable(self.get_object().nachbaren.annotate(nachbaren_count=Count('nachbaren', distinct=True),fahrplan_count=Count('fahrplaene',distinct=True))),
                #FahrplanTable(self.annotateFahrplan(self.get_object().fahrplaene)))
                FahrplanTable(Fahrplan.objects.withTableStats().filter(strecken_modules__path=self.get_object().path)))


class FuehrerstandList(Annotater, SingleTableView):
    table_class = FuehrerstandTable
    template_name = 'fuehrerstand/list.html'

    def get_queryset(self):
        qs = Fuehrerstand.objects.withTableStats()
        
        form = FuehrerstandSearchForm(self.request.GET)

        if form.is_valid():
            if filterBooleanCheckbox(form.cleaned_data['afb']) != -1:
                qs = qs.filter(mit_afb=filterBooleanCheckbox(form.cleaned_data['afb']))
            if(form.cleaned_data['zugsicherung']):
                qs = qs.filter(zugsicherung__overlap=form.cleaned_data['zugsicherung'])
            if(form.cleaned_data['sifa']):
                qs = qs.filter(sifa__overlap=form.cleaned_data['sifa'])
            if(form.cleaned_data['tuersystem']):
                qs = qs.filter(tuer_system__overlap=form.cleaned_data['tuersystem'])
            if(form.cleaned_data['schleuderschutz']):
                qs = qs.filter(schleuderschutz__overlap=form.cleaned_data['schleuderschutz'])
            if(form.cleaned_data['notbremse_system']):
                qs = qs.filter(notbremse_system__overlap=form.cleaned_data['notbremse_system'])

        return qs

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

        qs = FahrplanZug.objects.withTableStats()

        #Fahrplan group list
        if 'path' in self.kwargs:
            qs = qs.filter(fahrplaene__path=self.kwargs['path']).filter(fahrplan_gruppe=self.kwargs['gruppe'])

        if form:
            if(form.cleaned_data['gattung']):
                qs = qs.filter(gattung__in=form.cleaned_data['gattung'])
            if(form.cleaned_data['nummer']):
                qs = qs.filter(nummer=form.cleaned_data['nummer'])
            if filterBooleanCheckbox(form.cleaned_data['zugart']) != -1:
                qs = qs.filter(is_reisezug=filterBooleanCheckbox(form.cleaned_data['zugart']))
            if(form.cleaned_data['zuglauf']):
                qs = qs.filter(zug_lauf__icontains=form.cleaned_data['zuglauf'])
            if filterBooleanCheckbox(form.cleaned_data['dekozug']) != -1:
                qs = qs.filter(deko_zug=filterBooleanCheckbox(form.cleaned_data['dekozug']))
            if filterBooleanCheckbox(form.cleaned_data['anfang']) == 1:
                qs = qs.filter(speed_anfang__gt=0)
            if filterBooleanCheckbox(form.cleaned_data['anfang']) == 0:
                qs = qs.filter(speed_anfang=None)
            if form.cleaned_data['speed_min']:
                qs = qs.filter(fz_max_speed__gte=form.cleaned_data['speed_min'])
            if form.cleaned_data['speed_max']:
                qs = qs.filter(fz_max_speed__lte=form.cleaned_data['speed_max'])
            if(form.cleaned_data['eintragort']):
                qs = qs.filter(eintraege__ort__in=form.cleaned_data['eintragort'])
            if(form.cleaned_data['fahrplan']):
                qs = qs.filter(fahrplaene__path__in=form.cleaned_data['fahrplan'])
            if(form.cleaned_data['baureihe']):
                qs = qs.filter(fahrzeuge__br=form.cleaned_data['baureihe'])
            if(form.cleaned_data['antrieb']):
                qs = qs.filter(fahrzeuge__antrieb__overlap=form.cleaned_data['antrieb'])
            if filterBooleanCheckbox(form.cleaned_data['neigezug']) != -1:
                qs = qs.filter(fahrzeuge__neigetechnik=filterBooleanCheckbox(form.cleaned_data['neigezug']))

            if(form.cleaned_data['search']=='time'):
                now = datetime.datetime.now(timezone(settings.TIME_ZONE_DE))
                now_plus_window = now + datetime.timedelta(minutes=form.cleaned_data['time_window'])
                qs = qs.filter(Q(anfang_zeit__time__gte=now) & Q(anfang_zeit__time__lt=now_plus_window))

        return qs

class FahrplanZugDetail(generic.DetailView):
    template_name = 'fahrplanzug/detail.html'
    queryset = FahrplanZug.objects.withDetailStats()

class FahrzeugList(Annotater, SingleTableView):
    table_class = FahrzeugTable
    template_name = 'fahrzeug/list.html'

    def get_queryset(self):
        qs = FahrzeugVariante.objects.withTableStats()

        if 'root_file' in self.kwargs:
            qs = qs.filter(root_file=self.kwargs['root_file'])
        
        form = FahrzeugSearchForm(self.request.GET)

        if form.is_valid():
            if(form.cleaned_data['baureihe']):
                qs = qs.filter(br=form.cleaned_data['baureihe'])
            if filterBooleanCheckbox(form.cleaned_data['deko']) != -1:
                qs = qs.filter(dekozug=filterBooleanCheckbox(form.cleaned_data['deko']))
            if(form.cleaned_data['beschreibung']):
                qs = qs.filter(beschreibung__icontains=form.cleaned_data['beschreibung'])
            if(form.cleaned_data['farbgebung']):
                qs = qs.filter(farbgebung__icontains=form.cleaned_data['farbgebung'])
            if(form.cleaned_data['einsatz']):
                qs = qs.filter(Q(einsatz_ab__lte=form.cleaned_data['einsatz']) & Q(einsatz_bis__gte=form.cleaned_data['einsatz']))
            if form.cleaned_data['masse_min']:
                qs = qs.filter(masse__gte=form.cleaned_data['masse_min'])
            if form.cleaned_data['masse_max']:
                qs = qs.filter(masse__lte=form.cleaned_data['masse_max'])
            if form.cleaned_data['laenge_min']:
                qs = qs.filter(laenge__gte=form.cleaned_data['laenge_min'])
            if form.cleaned_data['laenge_max']:
                qs = qs.filter(laenge__lte=form.cleaned_data['laenge_max'])
            if form.cleaned_data['speed_min']:
                qs = qs.filter(speed_max__gte=form.cleaned_data['speed_min'])
            if form.cleaned_data['speed_max']:
                qs = qs.filter(speed_max__lte=form.cleaned_data['speed_max'])
            if(form.cleaned_data['antrieb']):
                qs = qs.filter(antrieb__overlap=form.cleaned_data['antrieb'])
            if(form.cleaned_data['bremse']):
                qs = qs.filter(bremse__overlap=form.cleaned_data['bremse'])
            if filterBooleanCheckbox(form.cleaned_data['neigetechnik']) != -1:
                qs = qs.filter(neigetechnik=filterBooleanCheckbox(form.cleaned_data['neigetechnik']))

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
                FahrplanTable(Fahrplan.objects.withTableStatsLight().filter(zuege__fahrzeuge__id=fahrzeug.id)))

class FahrplanList(SingleTableView):
    queryset = Fahrplan.objects.withTableStats()
    table_class = FahrplanTable
    template_name = 'fahrplan/list.html'

class FahrplanDetail(Annotater, MultiTableMixin, generic.DetailView):

    model = Fahrplan
    template_name = 'fahrplan/detail.html'

    def get_context_data(self, **kwargs):
            context = super(FahrplanDetail, self).get_context_data(**kwargs)

            context['fahrplan_gruppen'] = FahrplanZug.objects.filter(fahrplaene=self.get_object()).values('fahrplan_gruppe').annotate(Count('fahrplan_gruppe')).order_by('fahrplan_gruppe')
            return context

    def get_tables(self):
        return (FahrplanZugTable(self.annotateFahrplanZug(self.get_object().zuege)),
                StreckenModuleTable(StreckenModule.objects.withTableStats().filter(fahrplaene__path=self.get_object().path)))

class IndexView(generic.TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
            context = super(IndexView, self).get_context_data(**kwargs)

            zugsearchform = ZugSearchForm()
            #Hack so we can use extra buttons for this field
            del zugsearchform.fields['search']
            del zugsearchform.fields['time_window']
            context['zug_form'] = zugsearchform
            context['fstand_form'] = FuehrerstandSearchForm()
            context['fahrzeug_form'] = FahrzeugSearchForm()

            context['zug_count'] = FahrplanZug.objects.all().count()
            context['fahrzeug_count'] = FahrzeugVariante.objects.all().count()
            context['module_count'] = StreckenModule.objects.all().count()
            context['fstand_count'] = Fuehrerstand.objects.all().count()

            random_index = randint(0, context['zug_count'] - 1)
            context['random_zug'] = FahrplanZug.objects.all()[random_index]

            return context

class AutorList(SingleTableView):
    queryset = Autor.objects.withTableStats()
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
