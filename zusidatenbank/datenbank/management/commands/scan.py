from django.core.management.base import BaseCommand, CommandError
from datenbank.models import *
import xml.etree.ElementTree as ET
from datenbank.management.commands.parsers import *

import os
import logging

class Command(BaseCommand):
    help = 'Scans for Zusi content'

    def add_arguments(self, parser):
        parser.add_argument('root', type=str)

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s|%(name)s|%(message)s')
        self.clear_all()

        self.scanFiles(options['root'], "RollingStock", ".ftd", FtdParser)
        self.scanFiles(options['root'], "RollingStock", ".rv.fzg", FzgParser)
        self.scanFiles(options['root'], os.path.join("Routes", "Deutschland"), ".st3", St3Parser)
        self.scanFiles(options['root'], "Timetables", ".trn", TrnParser)
        self.scanFiles(options['root'], "Timetables", ".fpn", FpnParser)
                
    def scanFiles(self, root, subpath, filter, handlerClass):
        handler = handlerClass()

        logger = logging.getLogger("scan" + filter)
        logger.setLevel(logging.DEBUG)
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|%(message)s')
        sh.setFormatter(formatter)
        logger.addHandler(sh)

        for scanpath, dirs, files in os.walk(os.path.join(root, subpath), topdown=False):
            logger.info("Scanning " + scanpath)
            for name in files:
                full_path = os.path.join(scanpath, name)
                rel_path = os.path.relpath(full_path, root)
                if(name.endswith(filter)):
                    logger.info("Processing " + rel_path)
                    handler.parseFile(full_path, rel_path)

        handler.finalise()

    def clear_all(self):
        Fuehrerstand.objects.all().delete()
        Autor.objects.all().delete()
        StreckenModule.objects.all().delete()
        Fahrplan.objects.all().delete()
        FahrplanZug.objects.all().delete()
        FahrplanZugEintrag.objects.all().delete()
        FahrzeugVariante.objects.all().delete()
        