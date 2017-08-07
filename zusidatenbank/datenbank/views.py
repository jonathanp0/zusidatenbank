from django.views import generic
from django.db.models import Count, Min, F
from django.db.models.functions import Least

from .models import *
from .tables import *

from django_tables2 import SingleTableView

# Create your views here.

class StreckenModuleList(SingleTableView):
    table_class = StreckenModuleTable
    queryset = StreckenModule.objects.annotate(nachbaren_count=Count('nachbaren'))
    template_name = 'streckenmodule/list.html'

class FuehrerstandList(SingleTableView):
    model = Fuehrerstand
    table_class = FuehrerstandTable
    template_name = 'fuehrerstand/list.html'

class FahrplanZugList(SingleTableView):
    queryset = FahrplanZug.objects.annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speedMax')))
    table_class = FahrplanZugTable
    template_name = 'fahrplanzug/list.html'