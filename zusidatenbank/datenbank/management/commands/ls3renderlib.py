from ctypes import *
from PIL import Image

class LS3RenderLib:

    def __init__(self, path):
        """Ladet den LS3 Render DLL an dem angegeben Dateipfad"""
        self.dll = CDLL(path)

        self.dll.ls3render_Render.restype = c_int
        self.dll.ls3render_AddFahrzeug.restype = c_int
        self.dll.ls3render_Cleanup.restype = c_int
        self.setPixelProMeter = self.dll.ls3render_SetPixelProMeter
        self.setPixelProMeter.restype = None
        self.setMultisampling = self.dll.ls3render_SetMultisampling
        self.setMultisampling.restype = None
        self.reset = self.dll.ls3render_Reset
        self.reset.restype = None

        self.dll.ls3render_Init()

    def __del__(self):
        if self.dll.ls3render_Cleanup() == 0:
            raise RuntimeError('Fehler in ls3render_Cleanup')

    def addFahrzeug(self, datei, offsetX, laenge, gedreht, stromabnehmerHoehe, stromabnehmerOben):
        """
        Fuegt ein neues Fahrzeug hinzu. Fall einen Fehler, loest es eine RuntimeException aus.
        datei --- Dateiname Der Dateiname des Fahrzeugs (Dateisystempfad, kein Zusi-Pfad)
        offsetX --- Die horizontale Position des Fahrzeugnullpunktes in Metern. Hoehere Werte -> weiter rechts.
        laenge --- Die Fahrzeuglaenge in Metern (angegeben in den Fahrzeug-Grunddaten).
        gedreht --- Gedreht Ob das Fahrzeug gedreht eingereiht ist.
        stromabnehmerHoehe --- Die Einbauhoehe des Stromabnehmers in Metern (angegeben in den Fahrzeug-Grunddaten).
        stromabnehmerOben --- Ein Tuple von 4 Werte(Vor, Hinter, Aux Vor, Aux Hinter), mit dem Wert True wenn der Pantograph Oben gehoben sollte.
        """
        c_stromstate = [c_int(stromabnehmerOben[i]) for i in range(0, 4)]
        result = self.dll.ls3render_AddFahrzeug(c_char_p(datei.encode()), c_float(offsetX), c_float(laenge), gedreht, c_float(stromabnehmerHoehe), *c_stromstate)
        if result == 0:
            raise RuntimeError('Fehler in ls3render_AddFahrzeug')

    def renderImage(self, resample=1):
        """Rendert die Szene und gab ein Pillow Image zueruck. Fall einen Fehler, loest es eine RuntimeException aus. """
        hoehe = self.dll.ls3render_GetBildhoehe()
        breite = self.dll.ls3render_GetBildbreite()
        imgDimensions = (breite, hoehe)

        pufSize = self.dll.ls3render_GetAusgabepufferGroesse()
        puffer = (c_ubyte * pufSize)()
        result = self.dll.ls3render_Render(byref(puffer))
        if result == 0:
            raise RuntimeError('Fehler in ls3render_Render')

        #4 x 1 Byte RGBA-Daten mit Reihenfolge BGRA, beginnt mit der unteren Zeile
        img = Image.frombuffer('RGBA', imgDimensions, puffer, 'raw', 'BGRA', 0, -1).resize((int(breite / resample), int(hoehe / resample)))
        return img
