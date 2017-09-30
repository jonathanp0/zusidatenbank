from datenbank.models import *

import xml.etree.ElementTree as ET
import os
import sys
import logging
import copy
from datetime import datetime
from django.conf import settings
from django.core.files.storage import default_storage

from .ls3renderlib import LS3RenderLib

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

        xml = ET.parse(full_path).getroot()
        info = {'name': os.path.basename(rel_path),
                'autor': self.getAutor(xml)}

        if(info['autor'] == None):
            self.logger.error("No author information")
            return

        self.parse(xml, full_path, rel_path, info) 

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
        return datetime.strptime(dtstr,'%Y-%m-%d %H:%M:%S')

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

class FtdParser(ZusiParser):

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
            elif tag.startswith('Indusi') or tag.startswith('PZ') or tag.startswith('LZB'):
                stand.zugsicherung.append(tag)

        stand.save()
        stand.autor.add(*info['autor'])

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
                try:
                    mod_from.nachbaren.add(StreckenModule.objects.get(path=mod_to))
                except StreckenModule.DoesNotExist:
                    self.logger.error("Link to invalid neighbour " + str(mod_to) + " from " + modkey)
                

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
        zug.nummer = zug_tag.get('Nummer')
        zug.zug_lauf = zug_tag.get('Zuglauf')
        zug.fahrplan_gruppe = zug_tag.get('FahrplanGruppe')
        zug.deko = (zug_tag.get('Dekozug') == '1')
        zug.is_reisezug = (zug_tag.get('Zugtyp') == '1')

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
                return
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
            except FahrzeugVariante.DoesNotExist:
                self.logger.error("Could not find FV" + path + "/" + fahrzeug.get('IDHaupt') + ":" + fahrzeug.get('IDNeben'))

        zug.bild = self.renderImage(zug, root_path)
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

        zufall = varianten.get('PerZufallUebernehmen') != None

        return {'type': 'gruppe', 'name': varianten.get('Bezeichnung'), 'zufall': zufall, 'items': items}
        
    def processFahrzeug(self, zug):
 
        try:
            fahrzeug_obj = FahrzeugVariante.objects.get(root_file__iexact=zug.find('Datei').get('Dateiname'),haupt_id=zug.get('IDHaupt'), neben_id=zug.get('IDNeben'))
        except FahrzeugVariante.DoesNotExist:
            return None

        details = {'type': 'fahrzeug', 'id': fahrzeug_obj.id}

        details['gedreht'] = zug.get('Gedreht') != None
        details['multi_traktion'] =  zug.get('DotraModus') == '1'
        details['kein_traktion'] = zug.get('DotraModus') == '2'
        if zug.get('Zugart') != None:
            details['zugart'] = zug.get('Zugart')

        return details

    def renderImage(self, zug, root_path):
        fahrzeuge = zug.fahrzeug_tree_with_data()
        renderer = self.getRenderer(20)
        self.renderLength = 0

        self.procItem(fahrzeuge, renderer, root_path)
        
        imgpath = os.path.join('trn', zug.path.replace('\\','') + ".png")
        try:
            if not os.path.exists(zug.bild.storage.path(imgpath)):
                renderer.renderImage().save(zug.bild.storage.path(imgpath))
            return imgpath
        except Exception as e:
            logging.warn("Error rendering ls3")
        
        return None

    def procItem(self, item, renderer, root_path):
        if item['type'] == 'fahrzeug':
            sa = not item['kein_traktion']
            ls3datei = os.path.join(root_path, item['data'].ls3_datei)
            renderer.addFahrzeug(ls3datei, self.renderLength, item['data'].laenge, item['gedreht'], float(item['data'].stromabnehmer_hoehe or 0), (sa, sa, sa, sa)) 
            self.renderLength += item['data'].laenge
        elif item['type'] == 'gruppe':
            if item['zufall']:
                self.procItem(item['items'][0], renderer, root_path)
            else:
                for iitem in item['items']:
                    self.procItem(iitem, renderer, root_path)

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
            renderer = self.getRenderer(20)
            renderer.addFahrzeug(ls3datei, 0, float(fzg_data['laenge']), False, float(fzg_data.get('stromabnehmer_hoehe',0)), (True, True, True, True))
            imgname = rel_path.replace('\\','') + var_el.get('IDHaupt') + var_el.get('IDNeben') + ".png"
            imgpath = os.path.join('fzg', imgname)
            try:
                renderer.renderImage().save(variante.bild_klein.storage.path(imgpath))
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