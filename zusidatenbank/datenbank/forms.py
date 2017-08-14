from django.forms import ModelForm
from django import forms
from django.db.models import Q

from django.contrib.postgres.forms.ranges import IntegerRangeField, DateRangeField

from .models import FahrplanZug, FahrplanZugEintrag, Fahrplan, FahrzeugVariante

class ZugSearchForm(forms.Form):
    
    gattung = forms.ModelMultipleChoiceField(required=False,queryset=FahrplanZug.objects.values_list('gattung', flat=True).distinct().order_by('gattung'), to_field_name='gattung')
    nummer = forms.CharField(required=False)
    zugart = forms.ChoiceField(choices=[(0, 'Güterzug'), (1,'Reisezug')],widget=forms.RadioSelect,required=False)
    zuglauf = forms.CharField(help_text='(Teilweise vergleichen)',required=False)
    dekozug = forms.ChoiceField(choices=[(-1, ''), (0, 'Nein'), (1,'Ja')], initial=0)
    anfang = forms.ChoiceField(choices=[(0, 'Unbeweglich'), (1,'in Bewegung')],widget=forms.RadioSelect,required=False)
    maximalgeschwindigkeit = IntegerRangeField(help_text='? < x < ? km/h',required=False)
    fahrzeit = IntegerRangeField(help_text='? < x < ? minuten',required=False)
    eintragort = forms.ModelChoiceField(queryset=FahrplanZugEintrag.objects.exclude(Q(ort__startswith='Sbk'))
                                                                .values_list('ort', flat=True).distinct().order_by('ort'), to_field_name='ort',required=False)
    fahrplan = forms.ModelMultipleChoiceField(queryset=Fahrplan.objects.values_list('path', flat=True).order_by('path'), to_field_name='path',required=False)
    baureihe = forms.CharField(help_text='Sucht alle Fahrzeuge in Zugreihung',required=False)
    antrieb = forms.MultipleChoiceField(required=False)
    neigezug = forms.ChoiceField(choices=[(0, 'Nein'), (1,'Ja')],widget=forms.RadioSelect,required=False)

class FStandSearchForm(forms.Form):
    TUER_CHOICES = [('TB5','TB5'),('TB0','TB0'),('SAT','SAT'),('SST','SST'),('TAV','TAV'),('UICWTB','UIC WTB')]

    afb = forms.ChoiceField(label='AFB', choices=[(0, 'Nein'), (1,'Ja')])
    zugsicherung = forms.MultipleChoiceField(required=False)
    sifa = forms.MultipleChoiceField(required=False)
    tuersystem = forms.MultipleChoiceField(required=False,choices=TUER_CHOICES) #TB5,TB0,SAT.SST,TAV,UICWTB
    schleuderschutz = forms.MultipleChoiceField(required=False)
    notbremse_system = forms.MultipleChoiceField(required=False)

class FahrzeugSearchForm(forms.Form):
    #baureihe = forms.CharField(required=False)
    baureihe = forms.ModelChoiceField(queryset=FahrzeugVariante.objects.values_list('br', flat=True).distinct().order_by('br'), to_field_name='br',required=False)
    deko = forms.ChoiceField(choices=[(-1, ''), (0, 'Nein'), (1,'Ja')], initial=0)
    beschreibung = forms.CharField(help_text='(Teilweise vergleichen)',required=False)
    farbgebung = forms.CharField(help_text='(Teilweise vergleichen)',required=False)
    einsatz = DateRangeField(required=False)
    masse = IntegerRangeField(help_text='? < x < ? kg',required=False)
    laenge = IntegerRangeField(help_text='? < x < ? m',required=False)
    maximalgeschwindigkeit = IntegerRangeField(help_text='? < x < ? km/h',required=False)

    antrieb = forms.MultipleChoiceField(required=False)

    neigetechnik = forms.ChoiceField(choices=[(0, 'Nein'), (1,'Ja')],widget=forms.RadioSelect, required=False)




