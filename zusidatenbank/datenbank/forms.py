from django.forms import ModelForm
from django.forms.widgets import NumberInput
from django import forms
from django.db.models import Q

from django.contrib.postgres.forms.ranges import IntegerRangeField, DateRangeField, FloatRangeField, RangeWidget
from .models import *

def qs_to_opt_choice(qs):
    empty = [('',''),]
    empty.extend((obj,obj) for obj in qs)
    return empty

class ZugSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ZugSearchForm, self).__init__(*args, **kwargs)
            
        self.fields['gattung'] = forms.MultipleChoiceField(required=False,choices=((obj,obj) for obj in FahrplanZug.objects.values_list('gattung', flat=True).distinct().order_by('gattung')))
        self.fields['eintragort'] = forms.ChoiceField(choices=qs_to_opt_choice(FahrplanZugEintrag.objects.exclude(Q(ort__startswith='Sbk'))
                                                                .values_list('ort', flat=True).distinct().order_by('ort')), required=False)
        self.fields['fahrplan'] = forms.MultipleChoiceField(choices=self.fahrplan_choices(), required=False)
        self.fields['baureihe'] = forms.ChoiceField(choices=qs_to_opt_choice(FahrzeugVariante.objects.values_list('br', flat=True).distinct().order_by('br')),required=False,help_text='Sucht alle Fahrzeuge in Zugreihung')

    def fahrplan_choices(self):
        return ((obj,obj.replace("Timetables\\Deutschland\\", '')) for obj in Fahrplan.objects.values_list('path', flat=True).order_by('path'))
    
    gattung = forms.ChoiceField()
    nummer = forms.CharField(required=False)
    zugart = forms.ChoiceField(choices=[(0, 'Güterzug'), (1,'Reisezug')],widget=forms.RadioSelect,required=False)
    zuglauf = forms.CharField(help_text='(Teilweise vergleichen)',required=False)
    dekozug = forms.ChoiceField(choices=[(-1, ''), (0, 'Nein'), (1,'Ja')], initial=0)
    anfang = forms.ChoiceField(choices=[(0, 'Unbeweglich'), (1,'in Bewegung')],widget=forms.RadioSelect,required=False)
    #speedmin = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≥','addon_after':'km/h'}),
    #                              label='Maximalgeschwindigkeit',required=False)
    #speedmax = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≤','addon_after':'km/h'}),
    #                              label='',required=False)
    maximalgeschwindigkeit = IntegerRangeField(help_text='? < x < ? km/h',
                                               widget=RangeWidget(forms.NumberInput()),
                                               required=False)
    #fahrzeit = IntegerRangeField(help_text='? < x < ? minuten',required=False)
    eintragort = forms.ChoiceField()
    fahrplan = forms.MultipleChoiceField()
    baureihe = forms.ChoiceField()
    antrieb = forms.MultipleChoiceField(required=False, choices=FahrzeugVariante.ANTRIEB_CHOICES)
    neigezug = forms.ChoiceField(choices=[(0, 'Nein'), (1,'Ja')],widget=forms.RadioSelect,required=False)

class FStandSearchForm(forms.Form):
    TUER_CHOICES = [('TB5','TB5'),('TB0','TB0'),('SAT','SAT'),('SST','SST'),('TAV','TAV'),('UICWTB','UIC WTB')]

    afb = forms.ChoiceField(label='AFB', choices=[(-1, ''), (0, 'Nein'), (1,'Ja')])
    zugsicherung = forms.MultipleChoiceField(required=False)
    sifa = forms.MultipleChoiceField(required=False)
    tuersystem = forms.MultipleChoiceField(required=False,choices=TUER_CHOICES) #TB5,TB0,SAT.SST,TAV,UICWTB
    schleuderschutz = forms.MultipleChoiceField(required=False)
    notbremse_system = forms.MultipleChoiceField(required=False)

class FahrzeugSearchForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(FahrzeugSearchForm, self).__init__(*args, **kwargs)
            
        self.fields['baureihe'] = forms.ChoiceField(choices=qs_to_opt_choice(FahrzeugVariante.objects.values_list('br', flat=True).distinct().order_by('br')),required=False,help_text='Sucht alle Fahrzeuge in Zugreihung')

    baureihe = forms.ChoiceField()
    deko = forms.ChoiceField(choices=[(-1, ''), (0, 'Nein'), (1,'Ja')], initial=0)
    beschreibung = forms.CharField(help_text='(Teilweise vergleichen)',required=False)
    farbgebung = forms.CharField(help_text='(Teilweise vergleichen)',required=False)
    einsatz = forms.DateField(required=False)
    masse = IntegerRangeField(help_text='? < x < ? kg',required=False)
    laenge = FloatRangeField(help_text='? < x < ? m',required=False)
    maximalgeschwindigkeit = IntegerRangeField(help_text='? < x < ? km/h',required=False)
    antrieb = forms.MultipleChoiceField(required=False, choices=FahrzeugVariante.ANTRIEB_CHOICES)
    neigetechnik = forms.ChoiceField(choices=[(0, 'Nein'), (1,'Ja')],widget=forms.RadioSelect, required=False)




