import copy

from django.db import models
from django.core.validators import *
from django.urls import reverse

from django.contrib.postgres.fields import JSONField, ArrayField

#Complete(partial)
class Autor(models.Model):
  autor_id = models.IntegerField(primary_key=True)
  name = models.CharField(max_length=100)
  email = models.CharField(max_length=100, null=True)

  def __str__(self):
    return str(self.autor_id) + ": " + self.name

  class Meta:
    ordering = ['autor_id']

#Complete
class InventoryItem(models.Model):
  path = models.CharField(max_length=200, primary_key=True)
  name = models.CharField(max_length=100)
  autor = models.ManyToManyField(Autor)

  class Meta:
    abstract = True

#Complete
class StreckenModule(InventoryItem):
  nachbaren = models.ManyToManyField('self', symmetrical=False, related_name='+')
  standorte = ArrayField(models.CharField(max_length=200),default=list)

  def get_absolute_url(self):
    return reverse('db:smdetail', args=[self.path])

#Complete(partial)
class Fuehrerstand(InventoryItem): #TODO
  mit_afb = models.BooleanField(default=False)
  zugsicherung = ArrayField(models.CharField(max_length=20),default=list)
  sifa = ArrayField(models.CharField(max_length=30),default=list)
  tuer_system = ArrayField(models.CharField(max_length=10),default=list)
  schleuderschutz = ArrayField(models.CharField(max_length=40),default=list)
  notbremse_system = ArrayField(models.CharField(max_length=20),default=list)

  def get_absolute_url(self):
    return reverse('db:fsdetail', args=[self.path])

#Complete(partial)
class FahrzeugVariante(models.Model):
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

  #Grunddaten
  masse = models.IntegerField(null=True)
  laenge = models.FloatField()
  speedMax = models.IntegerField()

  bremse = ArrayField(models.CharField(max_length=50),null=True)
  tuersystem = ArrayField(models.CharField(max_length=6),null=True) #TB5,TB0,SAT.SST,TAV,UICWTB
  antrieb = ArrayField(models.CharField(max_length=50),null=True)
  neigetechnik = models.BooleanField(default=False,verbose_name='Neige')

  fuehrerstand = models.ForeignKey(Fuehrerstand, related_name='fahrzeuge', null=True)

  def get_absolute_url(self):
    return reverse('db:fzedetail', args=[self.root_file, self.haupt_id, self.neben_id])

  def masse_tonne(self):
    return self.masse / 1000

  class Meta:
    ordering = ['root_file','haupt_id','neben_id']

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

class Fahrplan(InventoryItem):
  strecken_modules = models.ManyToManyField(StreckenModule, related_name='fahrplaene')
  zuege = models.ManyToManyField(FahrplanZug, related_name='fahrplaene')
  anfang = models.DateTimeField()
