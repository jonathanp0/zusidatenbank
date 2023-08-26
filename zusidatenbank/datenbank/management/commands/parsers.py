from datenbank.models import *

import xml.etree.ElementTree as ET
import os
import sys
import re
import logging
import copy
from datetime import datetime, timedelta
import shutil
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q, F, Window
from django.db.models.functions import Lag
from pytz import timezone

from .ls3renderlib import LS3RenderLib
from .z3strbielib import *

def removeDoppel(input):

  prog = re.compile(r'(PerZufallUebernehmen="[0-9\.]+") (PerZufallUebernehmen="[0-9\.]+")')

  output = list()

  for l in input:
      s = l.decode("utf-8")
      r = prog.search(s)
      if r:
        o = s[0:r.start(1)] + s[r.end(1):]
      else:
        o = s
      output.append(o)

  ofile = "".join(output)

  return ofile

class ZusiParser(object):

    #Interface methods
    def parse(self, file, path, module_id, info):
        raise NotImplementedError

    def finalise(self):
        pass

    #Entry method
    def parseFile(self, full_path, rel_path):
        self.logger = logging.getLogger('parse.'+rel_path)

        fh = logging.FileHandler('scan.log', 'a')
        fh.setLevel(logging.WARN)
        formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|%(message)s')
        fh.setFormatter(formatter)
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(sh)

        with open(full_path, 'rb') as xml_file:

            #fixed = removeDoppel(xml_file)
            #xml = ET.fromstring(fixed)
            xml = ET.parse(xml_file)
            info = {'name': os.path.basename(rel_path),
                    'autor': list()}

            if(info['autor'] == None):
                self.logger.error("No author information")
                return

            self.parse(xml, full_path, rel_path, info) 

        fh.close()

    #XML Utils
    def getAutor(self, doc):
        autor_tags = doc.findall("Info/AutorEintrag[@AutorID][@AutorName]")
        return [self.findAutor(el) for el in autor_tags]
    
    def findAutor(self, autor_tag):
        return Autor.objects.get_or_create(autor_id = autor_tag.get('AutorID'), 
                                    defaults={'name': autor_tag.get('AutorName'), 'email': autor_tag.get('AutorEmail')})[0]

    def getAsFloat(self, tag, name):
        value = tag.get(name)
        if(value == None):
            return None
        else:
            return float(value)

    def getAttributeValues(self, doc, xpath, attribname):
        return [el.get(attribname) for el in doc.findall(xpath)]

    def getDateTime(self, tag, attribname):
        dtstr = tag.get(attribname)
        if dtstr == None:
            return None
        if len(dtstr) <= 10:
            dtstr += ' 00:00:00'
        return datetime.strptime(dtstr,'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone('UTC'))

    def hasChild(self, tag, childName):
        return tag.find(childName) != None

    #Other utils
    def toSpeed(self, msSpeed, base=5):
        if msSpeed == None:
            return None
        return int(base * round((msSpeed * 3.6)/base))

    lib = None

    def getRenderer(self, ppm):
        if ZusiParser.lib == None:
            ZusiParser.lib = LS3RenderLib(settings.LS3_DLL_PATH)
            ZusiParser.lib.setMultisampling(settings.LS3_MULTISAMPLING)
    
        ZusiParser.lib.setPixelProMeter(ppm)
        ZusiParser.lib.reset()

        return ZusiParser.lib

    strbie = None

    def getStrbie(self):
        if ZusiParser.strbie == None:
            ZusiParser.strbie = Z3StrbieLib("C:\\Program Files (x86)\\Zusi3\\z3strbie.dll")

        return ZusiParser.strbie

    def stripRouteNumber(self, zug):
        match = re.search(r"([A-Z]+)(\d{1,2})", zug.gattung)
        if match:
            zug.gattung = match.group(1)
            zug.zug_lauf = ' '.join((match.group(0),zug.zug_lauf))

class FtdParser(ZusiParser):

    LEER_IMAGE_SIZE = 901

    def parse(self, ftd, path, module_id, info):
        stand = Fuehrerstand(path=module_id, name=info['name'] )
        
        funk_el = ftd.find("Fuehrerstand/Funktionalitaeten")

        stand.mit_afb = self.hasChild(funk_el, 'AFBEinAus')

        for funk in funk_el.findall('*'):
            tag = funk.tag
            if tag.startswith('Sifa'):
                stand.sifa.append(tag.replace('Sifa', '').lstrip('_'))
            elif tag.startswith('Schleuderschutz'):
                stand.schleuderschutz.append(tag)
            elif tag.startswith('Tueren'):
                stand.tuer_system.append(tag.replace('Tueren', ''))
            elif tag.startswith('Notbremssystem'):
                stand.notbremse_system.append(tag.replace('Notbremssystem',''))
            elif tag.startswith('Indusi') or tag.startswith('PZ') or tag.startswith('LZB') or tag.startswith('ETCS') or tag.startswith('EBICAB') or tag.startswith('LZB80') or 'TrainguardBasicIndusi' == tag or 'ZBS' == tag:
                stand.zugsicherung.append(tag)

        stand.save()
        stand.autor.add(*info['autor'])

        grafik_id = 0
        for grafik in ftd.findall("Fuehrerstand/Grafik/Grunddaten"):

            name = grafik.get('GrafikName')
            bild_file = module_id.replace(os.sep,'') + str(grafik_id) + '.png'
            bild_src_path = os.path.join(settings.ROLLING_STOCK_LIST_PATH, 'RollingStock', 'List', bild_file)
            bild_dst_media_path = os.path.join('ftd', bild_file)

            # Generation with DLL
            #base_path = path.replace(module_id, '')
            #blick = FuehrerstandBlick(bild_klein=bild_dst_media_path, name=name, nummer=grafik_id, fuehrerstand=stand)
            #dst_path = os.path.normpath(blick.bild_klein.storage.path(bild_dst_media_path))
            #self.getStrbie().ftdVorschau(base_path, module_id, dst_path, grafik_id, D3DXIMAGE_FILEFORMAT.D3DXIFF_PNG, 300, 200)
            # TODO: Check returned image size to detect 'empty' images
            #blick.save()
            
            #Don't include 'empty' images, These are always 901 bytes in size
            if(os.path.exists(bild_src_path) and os.path.getsize(bild_src_path) != self.LEER_IMAGE_SIZE):
                blick = FuehrerstandBlick(bild_klein=bild_dst_media_path, name=name, nummer=grafik_id, fuehrerstand=stand)
                blick.save()
                shutil.copy(bild_src_path, blick.bild_klein.storage.path(bild_dst_media_path))

            grafik_id += 1

class St3Parser(ZusiParser):

    def __init__(self):
        self.nachbaren = dict()
    
    def parse(self, st3, path, module_id, info):

        standorte = self.getAttributeValues(st3, "Strecke/StreckenStandort[@StrInfo]", "StrInfo")
        nachbaren = self.getAttributeValues(st3, "Strecke/ModulDateien/Datei", "Dateiname")

        module = StreckenModule(path=module_id, name=info['name'], standorte=standorte)

        if len(nachbaren) > 0:
            self.nachbaren[module_id] = nachbaren

        module.save()
        module.autor.add(*info['autor'])

    def finalise(self):

        for modkey in self.nachbaren.keys():
            mod_from = StreckenModule.objects.get(path=modkey)
            for mod_to in self.nachbaren[modkey]:
                nachbarn = StreckenModule.objects.filter(path=mod_to)
                if len(nachbarn) > 0:
                    mod_from.nachbaren.add(nachbarn[0])
                else:
                    mod_from.fehlende_nachbaren.append(os.path.split(mod_to)[1])
                    mod_from.save()
                

class FpnParser(ZusiParser):

    def parse(self, fpn, path, module_id, info):
        zuege = [el.get("Dateiname") for el in fpn.findall("Fahrplan/Zug/Datei")]
        modules = [el.get("Dateiname") for el in fpn.findall("Fahrplan/StrModul/Datei")]
        
        fahrplan = Fahrplan(path=module_id, name=info['name'], anfang=self.getDateTime(fpn.find('Fahrplan'),'AnfangsZeit'))
        fahrplan.save()
        fahrplan.autor.add(*info['autor'])

        for module in modules:
            try:
                moduleobj = StreckenModule.objects.get(path=module)
                fahrplan.strecken_modules.add(moduleobj)
            except StreckenModule.DoesNotExist:
                self.logger.error("Module " + module + " missing")

        for zug in zuege:
            try:
                zugobj = FahrplanZug.objects.get(path=zug)
                fahrplan.zuege.add(zugobj)
            except FahrplanZug.DoesNotExist:
                self.logger.error("Zug " + zug + " missing")

class TrnParser(ZusiParser):

    def parse(self, fpn, path, zug_id, info):
        root_path = path.replace(zug_id, '')
        zug_tag = fpn.find('Zug')
        
        zug = FahrplanZug(path=zug_id, name=info['name'])
        zug.gattung = zug_tag.get('Gattung')
        zug.nummer = zug_tag.get('Nummer').split('_')
        zug.zug_lauf = zug_tag.get('Zuglauf')
        zug.fahrplan_gruppe = zug_tag.get('FahrplanGruppe')
        zug.deko = (zug_tag.get('Dekozug') == '1')
        zug.is_reisezug = (zug_tag.get('Zugtyp') == '1')
        self.stripRouteNumber(zug)

        zug.speed_anfang = self.toSpeed(self.getAsFloat(zug_tag, 'spAnfang'))
        zug.speed_zug = self.toSpeed(self.getAsFloat(zug_tag, 'spZugNiedriger'))

        zug.fahrzeug_tree = self.processVarianten(fpn.find('Zug/FahrzeugVarianten'))

        zug.save()
        zug.autor.add(*info['autor'])

        pos = 0
        for eintrag in fpn.findall("Zug/FahrplanEintrag"):
            an = self.getDateTime(eintrag, 'Ank')
            ab = self.getDateTime(eintrag, 'Abf')
            ort = eintrag.get('Betrst')
            bedarf =  eintrag.get('FplEintrag') == '2'
            kopf = eintrag.get('FzgVerbandAktion') != None
            ereignis = eintrag.find('Ereignis') != None
            if ort == None:
                self.logger.warn("Ignoring eintrag with empty place")
                continue
            eintrag_obj = FahrplanZugEintrag(position=pos, ort=eintrag.get('Betrst'), ab=ab, an=an, zug=zug,
                                             bedarfshalt=bedarf, kopf_machen=kopf, ereignis=ereignis)
            eintrag_obj.save()
            zug.eintraege.add(eintrag_obj)
            pos += 1
            
        for fahrzeug in fpn.iter('FahrzeugInfo'):
            path = fahrzeug.find('Datei').get('Dateiname')
            try:
                fahrzeug_obj = FahrzeugVariante.objects.get(root_file__iexact=path,haupt_id=fahrzeug.get('IDHaupt'), neben_id=fahrzeug.get('IDNeben'))
                zug.fahrzeuge.add(fahrzeug_obj)

                if not zug.steuerfahrzeug and fahrzeug_obj.fuehrerstand:
                    zug.steuerfahrzeug = fahrzeug_obj

                if not zug.triebfahrzeug and len(fahrzeug_obj.antrieb) > 0:
                    zug.triebfahrzeug = fahrzeug_obj
            except FahrzeugVariante.DoesNotExist:
                self.logger.error("Could not find Fahrzeug Variant " + path + "/" + fahrzeug.get('IDHaupt') + ":" + fahrzeug.get('IDNeben'))
                raise

        imgpath = os.path.join('trn', zug.path.replace('\\','') + ".png")
        zugrenderer = self.ZugRenderer(root_path, self.getRenderer(20))
        if not os.path.exists(zug.bild.storage.path(imgpath)):
            zugrenderer.renderImage(zug, imgpath, 1)
        zug.bild = imgpath

        zeit_diff = FahrplanZugEintrag.objects.filter(zug_id=zug_id).exclude(Q(ab=None) & Q(an=None)).annotate(
                                      zeit_previous=Window(expression=Lag('ab'),order_by=F('position').asc()),
                                      zeit_diff=Coalesce('an','ab')-F('zeit_previous')
                                    ).order_by().values_list('zeit_diff', flat=True)

        try:
            zug.zeit_bewegung = sum(zeit_diff[1:], timedelta())
        except TypeError:
            self.logger.error("Zeit in Bewegung calculation failed with:" + str(zeit_diff))

        zug.save()

    def processVariantenWithPosition(self, varianten):
        if varianten.get('FzgPosition') == None:
            position = 0
        else:
            position = int(varianten.get('FzgPosition'))

        return (position, self.processVarianten(varianten))
    
    def processVarianten(self, varianten):
        items = list()
        
        for item in varianten.findall("*"):
            if(item.tag == "FahrzeugVarianten"):
                items.insert(*self.processVariantenWithPosition(item))
            elif(item.tag == "FahrzeugInfo"):
                items.append(self.processFahrzeug(item))
            elif(item.tag == "Datei"):
                logging.error("Zugverband Datei in TRN file not supported")

        zufall = varianten.get('PerZufallUebernehmen') != None

        return {'type': 'gruppe', 'name': varianten.get('Bezeichnung'), 'zufall': zufall, 'items': items}
        
    def processFahrzeug(self, zug):
 
        try:
            fahrzeug_obj = FahrzeugVariante.objects.get(root_file__iexact=zug.find('Datei').get('Dateiname'),haupt_id=zug.get('IDHaupt'), neben_id=zug.get('IDNeben'))
        except FahrzeugVariante.DoesNotExist:
            self.logger.error("Could not find Fahrzeug Variant " + zug.find('Datei').get('Dateiname') + "/" + zug.get('IDHaupt') + ":" + zug.get('IDNeben'))
            raise

        details = {'type': 'fahrzeug', 'id': fahrzeug_obj.id}

        details['gedreht'] = zug.get('Gedreht') != None
        details['multi_traktion'] =  zug.get('DotraModus') == '1'
        details['kein_traktion'] = zug.get('DotraModus') == '2'
        if zug.get('SASchaltung') != None:
            details['stromabnehmer'] = int(zug.get('SASchaltung'))
        if zug.get('Zugart') != None:
            details['zugart'] = zug.get('Zugart')

        return details

    class ZugRenderer:

        def __init__(self, root_path, renderer):
            self.root_path = root_path
            self.renderer = renderer
            self.renderLength = 0

        def renderImage(self, zug, imgpath, resample):
            self.renderLength = 0
            self.processItem(zug.fahrzeug_tree_with_data())

            #try:
            self.renderer.renderImage(resample).save(zug.bild.storage.path(imgpath))
            return imgpath
            #except Exception as e:
            #    logging.warn("Error rendering ls3 for Fahrplanzug")
            
            #return None

        def processItem(self, item):
            if item['type'] == 'fahrzeug':
                ls3datei = os.path.join(self.root_path, item['data'].ls3_datei)
                saCode = item.get('stromabnehmer', 0)
                sa = self.decodeStromabnehmer(saCode, item['gedreht'])
                self.renderer.addFahrzeug(ls3datei, self.renderLength, item['data'].laenge, item['gedreht'], float(item['data'].stromabnehmer_hoehe or 0), sa) 
                self.renderLength += item['data'].laenge
            elif item['type'] == 'gruppe':
                if item['zufall']:
                    #Random choice, process only first choice
                    self.processItem(item['items'][0])
                else:
                    #Process everything
                    for iitem in item['items']:
                        self.processItem(iitem)

        def decodeStromabnehmer(self, sa, gedreht):
            if gedreht:
                return (sa >> 1 & 1, sa & 1, sa >> 3 & 1, sa >> 2 & 1 )
            else:
                return (sa & 1, sa >> 1 & 1, sa >> 2 & 1, sa >> 3 & 1 )

class FzgParser(ZusiParser):

    def parse(self, fzg, path, module_id, info):
        root_path = path.replace(module_id, '')
        fzg_data = {'tuersystem': [], 'bremse': [], 'antrieb': []}
        self.processDatei(root_path, module_id, fzg_data, info)

    def processDatei(self, root_path, rel_path, fzg_data, info):
        full_path = os.path.join(root_path, rel_path)
        fzg = ET.parse(full_path).getroot()

        #Add authors from the file
        info['autor'].extend(self.getAutor(fzg))

        #Process basic data for this file
        grund_el = fzg.find('Fahrzeug/FahrzeugGrunddaten')
        if(grund_el != None):
            fzg_data['masse'] = grund_el.get('Masse')
            fzg_data['laenge'] = grund_el.get('Laenge')
            fzg_data['speed_max'] = self.toSpeed(self.getAsFloat(grund_el, 'spMax'))
            neigeWinkel = grund_el.get('Neigewinkel')
            fzg_data['neigetechnik'] = (neigeWinkel != None and float(neigeWinkel) != 0.0)
            stromHoehe = grund_el.get('StromabnHoehe')
            if stromHoehe != None:
                fzg_data['stromabnehmer_hoehe'] = stromHoehe

        #Process additional features
        for el in fzg.findall('Fahrzeug/*'):
            if el.tag.startswith('FzgTuersystem'):
                fzg_data['tuersystem'].append(el.tag.replace('FzgTuersystem', ''))
            elif el.tag.find('bremse') != -1:
                fzg_data['bremse'].append(el.tag.replace('bremse',''))
            elif el.tag.find('Bremse') != -1:
                fzg_data['bremse'].append(el.tag.replace('Bremse','').lstrip('_'))
            elif el.tag.find('Antriebsmodell') != -1:
                fzg_data['antrieb'].append(el.tag.replace('Antriebsmodell', ''))

        #Mix in any included files
        extern_datei = self.getAttributeValues(fzg, 'Fahrzeug/ExterneDatei/Datei[@Dateiname]', 'Dateiname')
        for datei in extern_datei:
            self.processDatei(root_path, datei, fzg_data, info)

        #Process Varianten in this file using current data as a base
        varianten = fzg.findall('Fahrzeug/FahrzeugVariante')
        for variante in varianten:
            var_fzg_data = copy.deepcopy(fzg_data) #Make a copy for additional data for this variante only
            var_info = copy.deepcopy(info)
            self.processVariante(variante, root_path, rel_path, var_fzg_data, var_info)

    def processVariante(self, var_el, root_path, rel_path, fzg_data, info):

        #Mix in any included file
        extern_datei = self.getAttributeValues(var_el, 'ExterneDatei/Datei[@Dateiname]', 'Dateiname')
        for datei in extern_datei:
            self.processDatei(root_path, datei, fzg_data, info)

        #Create the variant using all available data
        variante = FahrzeugVariante(root_file=rel_path, haupt_id=var_el.get('IDHaupt'), neben_id=var_el.get('IDNeben'),
                                    br=var_el.get('BR'), beschreibung=var_el.get('Beschreibung'), farbgebung=var_el.get('Farbgebung'),
                                    einsatz_ab=self.getDateTime(var_el, 'EinsatzAb'), einsatz_bis=self.getDateTime(var_el, 'EinsatzBis'),
                                    **fzg_data)
        variante.dekozug = var_el.get('Dekozug') == '1'
        ls3tag = var_el.find('DateiAussenansicht[@Dateiname]')
        if ls3tag != None:
            variante.ls3_datei = ls3tag.get('Dateiname')

        #Generate the image
        if variante.ls3_datei != None:
            ls3datei = os.path.join(root_path, variante.ls3_datei)
            try:
                renderer = self.getRenderer(80)
                renderer.addFahrzeug(ls3datei, 0, float(fzg_data['laenge']), False, float(fzg_data.get('stromabnehmer_hoehe',0)), (True, True, True, True))
                imgname = rel_path.replace('\\','') + var_el.get('IDHaupt') + var_el.get('IDNeben') + ".png"
                imgpath = os.path.join('fzg', imgname)
                if not os.path.exists(variante.bild_klein.storage.path(imgpath)):
                    renderer.renderImage(4).save(variante.bild_klein.storage.path(imgpath))
                variante.bild_klein = imgpath
            except Exception:
                logging.warn("Error rendering ls3")

        #Link the FTD
        fuehrerstand_el = var_el.find('DateiFuehrerstand[@Dateiname]')
        if(fuehrerstand_el != None):
            variante.fuehrerstand = Fuehrerstand.objects.get(path__iexact=fuehrerstand_el.get("Dateiname"))
            if(fuehrerstand_el.get("Dateiname") != variante.fuehrerstand.path):
                logging.warn("Non matching Führerstand " + fuehrerstand_el.get("Dateiname"))

        variante.save()

        #Add the authors
        autor_dict = {int(a.autor_id): a for a in info['autor']}
        variante.autor.add(*autor_dict.values())

class TimetableParser(ZusiParser):

    def parse(self, timetable, path, module_id, info):

        trn_tag = timetable.find("Buchfahrplan/Datei_trn[@Dateiname]")
        if trn_tag == None:
            return

        try:
            zug = FahrplanZug.objects.get(path=trn_tag.get("Dateiname"))
        except FahrplanZug.DoesNotExist:
            self.logger.error("Timetable XML for invalid Zug " + trn_tag.get("Dateiname"))
            return

        bfp_tag = timetable.find("Buchfahrplan")

        if bfp_tag != None:
            zug.masse = self.getAsFloat(bfp_tag, "Masse")
            zug.laenge = self.getAsFloat(bfp_tag, "Laenge")
            zug.bremse_percentage = self.getAsFloat(bfp_tag, "Bremsh")

            zug.save()

class ZusiDisplayAnsageParser(ZusiParser):

    def parse(self, zda, path, module_id, info):

        for trains_tag in zda.findall("Line/Track/Trains"):
            timetable = trains_tag.get("Timetable")
            if timetable[0] == '\\':
                timetable = timetable[1:]

            for train_tag in trains_tag.findall("Train"):
                try:
                    gattung = train_tag.get('Type')
                    match = re.search(r"([A-Z]+)(\d{1,2})", gattung)
                    if match:
                        gattung = match.group(1)

                    zug = FahrplanZug.objects.get(fahrplaene__path=timetable,
                                                  gattung=gattung, 
                                                  nummer__contains=[train_tag.get('Number'),])
                    zug.fis_ansagen = True
                    zug.save()
                except FahrplanZug.DoesNotExist:
                    self.logger.warn("ZusiDisplayAnsage for invalid Zug " + timetable + "::" + gattung + "::" + train_tag.get('Number'))
                    continue
                except FahrplanZug.MultipleObjectsReturned:
                    self.logger.error("ZusiDisplayAnsage for unclear Zug " + timetable + "::" + gattung + "::" + train_tag.get('Number'))
                    continue

class FahrzeugVerbandParser(ZusiParser):

    # Global List of found files for later scanning
    verbandList = set()

    def parse(self, trn, path, zug_id, info):

        for fahrzeug in trn.iter('FahrzeugInfo'):
            path = fahrzeug.find('Datei').get('Dateiname')

            if not (path in FahrzeugVerbandParser.verbandList):
                self.logger.info("Found Fahrzeug path for verband list: " + path)
                
            if not FahrzeugVariante.objects.filter(root_file__iexact=path).exists():
                FahrzeugVerbandParser.verbandList.add(path)
                self.logger.info("Add Fahrzeug path to verband list: " + path)
