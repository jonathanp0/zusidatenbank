#coding=utf8
import copy
import datetime

from django.db import models
from django.core.validators import *
from django.urls import reverse
from django.db.models import Count, Min, Max, Sum, F, Q, Value, CharField, Subquery, OuterRef, Case, When
from django.db.models.functions import Least, Greatest, Concat, Coalesce
from django.contrib.postgres.aggregates.general import BoolOr

from django.contrib.postgres.fields import JSONField, ArrayField

from .helpers.utils import display_array

#Complete(partial)

class AutorManager(models.Manager):

  def withTableStats(self):
    return self.annotate(module_count=Count('streckenmodule',distinct=True),
                                      ftd_count=Count('fuehrerstand', distinct=True),
                                      fahrplan_count=Count('fahrplan', distinct=True),
                                      fz_count=Count('fahrzeugvariante', distinct=True))

class Autor(models.Model):
  autor_id = models.IntegerField(primary_key=True, verbose_name='ID')
  name = models.CharField(max_length=100)
  email = models.CharField(max_length=100, null=True)

  objects = AutorManager()

  def __str__(self):
    return str(self.autor_id) + ": " + self.name

  def get_absolute_url(self):
    return reverse('db:autordetail', args=[self.autor_id])

  class Meta:
    ordering = ['autor_id']

#Complete
class InventoryItem(models.Model):
  path = models.CharField(max_length=200, primary_key=True)
  name = models.CharField(max_length=100)
  autor = models.ManyToManyField(Autor)

  class Meta:
    abstract = True

class StreckenModuleManager(models.Manager):

    def withTableStats(self):
        return self.annotate(nachbaren_count=Count('nachbaren', distinct=True),fahrplan_count=Count('fahrplaene__path', distinct=True))

#Complete
class StreckenModule(InventoryItem):
  nachbaren = models.ManyToManyField('self', symmetrical=False, related_name='+')
  standorte = ArrayField(models.CharField(max_length=200),default=list)

  objects = StreckenModuleManager()

  def get_absolute_url(self):
    return reverse('db:smdetail', args=[self.path])

class FuehrerstandManager(models.Manager):
    
    def withTableStats(self):
        return self.annotate(fahrzeug_count=Count('fahrzeuge', distinct=True),zug_count=Count('fahrzeuge__fahrplanzuege', distinct=True))

#Complete(partial)
class Fuehrerstand(InventoryItem):
  ZUGSICHERUNG_CHOICES = (
    ('IndusiI54','Indusi I54',), 
    ('IndusiI60','Indusi I60'), 
    ('IndusiI60M', 'Indusi I60M'), 
    ('IndusiI60R_ZUB122','Indusi I60R + ZUB122'),
    ('IndusiI60R_ZUB262', 'Indusi I60R + ZUB262'),
    ('IndusiI60DR', 'Indusi I60DR'),
    ('PZB80', 'PZB80'),
    ('PZB90I60R_V15', 'PZB90/I60R - V1.5'),
    ('PZB90I60R_V20', 'PZB90/I60R - V2.0'),
    ('PZB90I60R_V20_ZUB122', 'PZB90/I60R - V2.0 + ZUB122'),
    ('PZB90I60R_V20_ZUB262', 'PZB90/I60R - V2.0 + ZUB262'),
    ('PZB90I60R_V20_SBahn', 'PZB90/I60R - V2.0 S-Bahn'),
    ('LZB80_I80', 'LZB80/I80'),
    ('LZB80_I80_ZUB262', 'LZB80/I80 + ZUB262'),
    ('LZB80_PZB90_20', 'LZB80/I80 PZB90 V2.0'),
    ('LZB80_PZB90_20_ZUB262', 'LZB80/I80 PZB90 V2.0 + ZUB262'),
    ('PZB60', 'PZB60'),
  )

  SIFA_CHOICES = (
    ('RZM','R.Z.M.-Sifa',),
    ('ZeitWeg','Zeit-Weg-Sifa',),
    ('ZeitZeit','Zeit-Zeit-Sifa',),
    ('66','Sifa 66',),
    ('86','Sifa 86',)
  )

  TUER_CHOICES = [('TB5','TB5'),('TB0','TB0'),('SAT','SAT'),('SST','SST'),('TAV','TAV'),('UICWTB','UIC WTB')]

  SCHLEUDERSCHUTZ_CHOICES = (
    ('Schleuderschutzbremse','Schleuderschutzbremse',),
    ('SchleuderschutzDrosselung','Schleuderschutz (Motordrosselung)',),
    ('SchleuderschutzElektr','Elektronischer Schleuderschutz',),
  )

  NOTBREMS_CHOICES = (
    ('UICNBUe','UIC-NBÜ/UIC 541-5',),
    ('NBUe2004','NBÜ 2004',)
  )

  mit_afb = models.BooleanField(default=False)
  zugsicherung = ArrayField(models.CharField(max_length=30),default=list)
  sifa = ArrayField(models.CharField(max_length=30),default=list)
  tuer_system = ArrayField(models.CharField(max_length=10),default=list)
  schleuderschutz = ArrayField(models.CharField(max_length=40),default=list)
  notbremse_system = ArrayField(models.CharField(max_length=20),default=list)

  objects = FuehrerstandManager()

  def zugsicherung_display(self):
    return display_array(self.zugsicherung, self.ZUGSICHERUNG_CHOICES)

  def sifa_display(self):
    return display_array(self.sifa, self.SIFA_CHOICES)

  def tuer_system_display(self):
    return display_array(self.tuer_system, self.TUER_CHOICES)

  def schleuderschutz_display(self):
    return display_array(self.schleuderschutz, self.SCHLEUDERSCHUTZ_CHOICES)

  def notbremse_system_display(self):
    return display_array(self.notbremse_system, self.NOTBREMS_CHOICES)

  def get_absolute_url(self):
    return reverse('db:fsdetail', args=[self.path])

class FahrzeugVarianteManager(models.Manager):
    
    def withTableStats(self):
        return self.annotate(variant=Concat(F('haupt_id'), Value('/'), F('neben_id'),output_field=CharField()), zug_count=Count('fahrplanzuege'))

#Complete(partial)
class FahrzeugVariante(models.Model):
  ANTRIEB_CHOICES = (
    ('DieselHydraulisch','Diesel Hydraulisch',), 
    ('Einfach','Einfach'), 
    ('ElektrischDrehstrom', 'Elektrisch Drehstrom'), 
    ('ElektrischReihenschluss','Elektrisch Reihenschluss')
  )

  BREMSE_CHOICES = (
    ('LuftEinlK1','Knorr K1-GP (einlösig)',),
    ('KE_GP','KE-GP-Druckluft (mehrlösig)',),
    ('KE_GPR_Klotz','KE-GPR-Klotz (mehrlösig)',),
    ('KE_GPR_Scheibe','KE-GPR-Scheiben (mehrlösig)',),
    ('Mg','Magnetisch',),
    ('LuftDirekt','Direkte Druckluft (Zusatzbremse)',),
    ('Federspeicher','Federspeicher',),
    ('KE_Tm','KE-GPR-Tm-Klotz (mehrlösig)',),
    ('KE_L2a','KE-GPR-L2a-Scheiben (mehrlösig)',),
    ('KE_L2d','KE-GPR-L2d-Scheiben (mehrlösig)',),
    ('DynHydrodynamisch','Hydrodynamisch',),
    ('DynElektrDrehstrom','Elektrische Drehstrom',),
    ('DynElektrReihenschluss','Elektrische Reihenschluss',)
  )

  root_file = models.CharField(max_length=200)
  haupt_id = models.IntegerField()
  neben_id = models.IntegerField()
  autor = models.ManyToManyField(Autor)

  #Variantedaten
  br = models.CharField(max_length=50,verbose_name='BR')
  dekozug = models.BooleanField(verbose_name='Deko')
  beschreibung = models.CharField(max_length=200, null=True)
  farbgebung = models.CharField(max_length=200, null=True)
  einsatz_ab = models.DateTimeField(null=True)
  einsatz_bis = models.DateTimeField(null=True)
  ls3_datei = models.CharField(max_length=200)

  #Grunddaten
  masse = models.IntegerField(null=True)
  laenge = models.FloatField()
  speed_max = models.IntegerField()

  bremse = ArrayField(models.CharField(max_length=50),null=True)
  tuersystem = ArrayField(models.CharField(max_length=6),null=True) #TB5,TB0,SAT.SST,TAV,UICWTB
  antrieb = ArrayField(models.CharField(max_length=50),null=True)
  neigetechnik = models.BooleanField(default=False,verbose_name='Neige')
  stromabnehmer_hoehe = models.FloatField(null=True)

  #Bilder
  bild_klein = models.ImageField(null=True,max_length=200,upload_to='fzg/')

  fuehrerstand = models.ForeignKey(Fuehrerstand, related_name='fahrzeuge', null=True)

  objects = FahrzeugVarianteManager()

  def antrieb_display(self):
    return display_array(self.antrieb, self.ANTRIEB_CHOICES)

  def tuersystem_display(self):
    return display_array(self.tuersystem, Fuehrerstand.TUER_CHOICES)

  def bremse_display(self):
    return display_array(self.bremse, self.BREMSE_CHOICES)

  def get_absolute_url(self):
    return reverse('db:fvdetail', args=[self.root_file, self.haupt_id, self.neben_id])

  def masse_tonne(self):
    return self.masse / 1000

  class Meta:
    ordering = ['root_file','haupt_id','neben_id']

class FahrplanZugManager(models.Manager):
    
    def withTableStats(self):
        return self.annotate(position_count=Max('eintraege__position'),
                             deko_fahrzeuge=BoolOr('fahrzeuge__dekozug')
                    ).annotate(fz_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speed_max')), 
                               gesamt_zeit=Case(
                                    When(position_count=0, then=Value(datetime.timedelta(0))),
                                    default=Max(Coalesce('eintraege__an','eintraege__ab')) - Min(Coalesce('eintraege__ab','eintraege__an'))
                                  ),
                               anfang_zeit=Min(Coalesce('eintraege__an','eintraege__ab')),
                               deko_zug=Case(When(deko_fahrzeuge=True, then=True), default='deko'))

    def withDetailStats(self):
        return self.annotate(zug_max_speed=Least(F('speed_zug'),Min('fahrzeuge__speed_max')),
                             fz_max_speed=Min('fahrzeuge__speed_max'))

#Complete
class FahrplanZug(InventoryItem):
  gattung = models.CharField(max_length=20)
  nummer = models.CharField(max_length=40)
  is_reisezug = models.BooleanField(verbose_name='Zugart')
  zug_lauf = models.CharField(max_length=200, null=True, verbose_name='Lauf')
  fahrplan_gruppe = models.CharField(max_length=200, null=True)
  deko = models.BooleanField(default=False)

  speed_anfang = models.IntegerField(null=True)
  speed_zug = models.IntegerField(null=True)

  fahrzeuge = models.ManyToManyField(FahrzeugVariante, related_name='fahrplanzuege')

  fahrzeug_tree = JSONField()

  bild = models.ImageField(null=True,max_length=200,upload_to='trn/')

  objects = FahrplanZugManager()

  def get_absolute_url(self):
    return reverse('db:fzdetail', args=[self.path])

  def fahrzeug_tree_with_data(self):

    fz = dict()
    for fahrzeug in self.fahrzeuge.all():
      fz[fahrzeug.id] = fahrzeug

    def walk(node):
      for item in node['items']:
          if item['type'] =='gruppe':
              walk(item)
          elif item['type'] == 'fahrzeug':
              item['data'] = fz[item['id']]

    tree = copy.deepcopy(self.fahrzeug_tree)
    walk(tree)

    return tree

#Complete
class FahrplanZugEintrag(models.Model):
  position = models.IntegerField()
  an = models.DateTimeField(null=True)
  ab = models.DateTimeField(null=True)
  ort = models.CharField(max_length = 200)
  bedarfshalt = models.BooleanField(default=False)
  kopf_machen = models.BooleanField(default=False)
  ereignis = models.BooleanField(default=False)

  zug = models.ForeignKey(FahrplanZug, related_name='eintraege')

  class Meta:
    ordering = ['position']

class FahrplanManager(models.Manager):
    
    def withTableStats(self):
        return self.annotate(zug_count=Count('zuege', distinct=True),module_count=Count('strecken_modules', distinct=True))

    def withTableStatsLight(self):
        return self.annotate(module_count=Count('strecken_modules', distinct=True))

class Fahrplan(InventoryItem):
  strecken_modules = models.ManyToManyField(StreckenModule, related_name='fahrplaene')
  zuege = models.ManyToManyField(FahrplanZug, related_name='fahrplaene')
  anfang = models.DateTimeField()

  objects = FahrplanManager()

  def get_absolute_url(self):
    return reverse('db:fpdetail', args=[self.path])
