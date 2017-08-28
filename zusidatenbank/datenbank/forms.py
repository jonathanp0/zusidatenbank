from django.forms import ModelForm
from django.forms.widgets import NumberInput
from django import forms
from django.db.models import Q

from .models import *

def qs_to_opt_choice(qs):
    empty = [('',''),]
    empty.extend((obj,obj) for obj in qs)
    return empty

class ZugSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ZugSearchForm, self).__init__(*args, **kwargs)
            
        self.fields['gattung'] = forms.MultipleChoiceField(help_text='Mehrfachauswahl möglich',required=False,choices=((obj,obj) for obj in FahrplanZug.objects.values_list('gattung', flat=True).distinct().order_by('gattung')))
        self.fields['eintragort'] = forms.ChoiceField(help_text='Sucht alle Orte im Zugfahrplan',choices=qs_to_opt_choice(FahrplanZugEintrag.objects.exclude(Q(ort__startswith='Sbk'))
                                                                .values_list('ort', flat=True).distinct().order_by('ort')), required=False)
        self.fields['fahrplan'] = forms.MultipleChoiceField(choices=self.fahrplan_choices(), required=False,help_text='Mehrfachauswahl möglich')
        self.fields['baureihe'] = forms.ChoiceField(choices=qs_to_opt_choice(FahrzeugVariante.objects.values_list('br', flat=True).distinct().order_by('br')),required=False,help_text='Sucht alle Fahrzeuge in Zugreihung')

    def fahrplan_choices(self):
        return ((obj,obj.replace("Timetables\\Deutschland\\", '')) for obj in Fahrplan.objects.exclude(path__contains='_Docu').values_list('path', flat=True).order_by('path'))
    
    gattung = forms.ChoiceField()
    nummer = forms.CharField(required=False)
    fahrplan = forms.MultipleChoiceField()
    eintragort = forms.ChoiceField()
    zuglauf = forms.CharField(help_text='(Teilweise vergleichen)',required=False,widget=forms.TextInput(attrs={'placeholder':'z.b. Berlin'}))
    zugart = forms.ChoiceField(choices=[(0, 'Güterzug'), (1,'Reisezug')],widget=forms.RadioSelect,required=False)
    dekozug = forms.ChoiceField(choices=[(-1, ''), (0, 'Nein'), (1,'Ja')], initial=0)
    anfang = forms.ChoiceField(choices=[(0, 'Unbeweglich'), (1,'in Bewegung')],widget=forms.RadioSelect,required=False)
    speed_min = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≥','addon_after':'km/h'}),
                                  label='Maximalgeschwindigkeit',required=False)
    speed_max = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≤','addon_after':'km/h'}),
                                  label='',required=False)
    speed_min = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≥','addon_after':'km/h'}),
                                  label='Maximalgeschwindigkeit',required=False)
    speed_max = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≤','addon_after':'km/h'}),
                                  label='',required=False)
    #fahrzeit_min = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≥','addon_after':'minuten'}),
    #                              label='Farhzeit',required=False)
    #fahrzeit_max = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≤','addon_after':'minuten'}),
    #                              label='',required=False)
    baureihe = forms.ChoiceField()
    antrieb = forms.MultipleChoiceField(required=False, choices=FahrzeugVariante.ANTRIEB_CHOICES,help_text='Mehrfachauswahl möglich')
    neigezug = forms.ChoiceField(choices=[(0, 'Nein'), (1,'Ja')],widget=forms.RadioSelect,required=False)

class FuehrerstandSearchForm(forms.Form):

    afb = forms.ChoiceField(label='AFB', choices=[(-1, ''), (0, 'Nein'), (1,'Ja')])
    zugsicherung = forms.MultipleChoiceField(required=False,choices=Fuehrerstand.ZUGSICHERUNG_CHOICES,help_text='Mehrfachauswahl möglich')
    sifa = forms.MultipleChoiceField(required=False,choices=Fuehrerstand.SIFA_CHOICES,help_text='Mehrfachauswahl möglich')
    tuersystem = forms.MultipleChoiceField(required=False,choices=Fuehrerstand.TUER_CHOICES,help_text='Mehrfachauswahl möglich') #TB5,TB0,SAT.SST,TAV,UICWTB
    schleuderschutz = forms.MultipleChoiceField(required=False,choices=Fuehrerstand.SCHLEUDERSCHUTZ_CHOICES,help_text='Mehrfachauswahl möglich')
    notbremse_system = forms.MultipleChoiceField(required=False,choices=Fuehrerstand.NOTBREMS_CHOICES,help_text='Mehrfachauswahl möglich')

class FahrzeugSearchForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(FahrzeugSearchForm, self).__init__(*args, **kwargs)
            
        self.fields['baureihe'] = forms.ChoiceField(choices=qs_to_opt_choice(FahrzeugVariante.objects.values_list('br', flat=True).distinct().order_by('br')),required=False,help_text='Sucht alle Fahrzeuge in Zugreihung')

    baureihe = forms.ChoiceField()
    deko = forms.ChoiceField(choices=[(-1, ''), (0, 'Nein'), (1,'Ja')], initial=0)
    beschreibung = forms.CharField(help_text='(Teilweise vergleichen)',required=False)
    farbgebung = forms.CharField(help_text='(Teilweise vergleichen)',required=False)
    einsatz = forms.DateField(required=False,widget=forms.DateInput(attrs={'placeholder':'dd.mm.yy'}))
    masse_min = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≥','addon_after':'kg'}),
                                  label='Masse',required=False)
    masse_max = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≤','addon_after':'kg'}),
                                  label='',required=False)
    laenge_min = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≥','addon_after':'m'}),
                                  label='Länge',required=False)
    laenge_max = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≤','addon_after':'m'}),
                                  label='',required=False)
    speed_min = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≥','addon_after':'km/h'}),
                                  label='Maximalgeschwindigkeit',required=False)
    speed_max = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder':'','addon_before':'≤','addon_after':'km/h'}),
                                  label='',required=False)
    antrieb = forms.MultipleChoiceField(required=False, choices=FahrzeugVariante.ANTRIEB_CHOICES,help_text='Mehrfachauswahl möglich')
    neigetechnik = forms.ChoiceField(choices=[(0, 'Nein'), (1,'Ja')],widget=forms.RadioSelect, required=False)
