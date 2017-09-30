from ctypes import *
from PIL import Image

class LS3RenderLib:

    def __init__(self, path):
        self.dll = CDLL(path)

        self.dll.ls3render_Render.restype = c_int
        self.dll.ls3render_AddFahrzeug.restype = c_int

        self.setPixelProMeter = self.dll.ls3render_SetPixelProMeter
        self.setPixelProMeter.restype = None
        self.setMultisampling = self.dll.ls3render_SetMultisampling
        self.setMultisampling.restype = None
        self.reset = self.dll.ls3render_Reset
        self.reset.restype = None

        self.dll.ls3render_Init()

    def __del__(self):
        self.dll.ls3render_Cleanup()

    def addFahrzeug(self, datei, offsetX, laenge, gedreht, stromabnehmerHoehe, stromabnehmerOben):
        c_stromstate = [c_int(stromabnehmerOben[i]) for i in range(0, 4)]
        result = self.dll.ls3render_AddFahrzeug(c_char_p(datei.encode()), c_float(offsetX), c_float(laenge), gedreht, c_float(stromabnehmerHoehe), *c_stromstate)
        if result == 0:
            raise Exception('Fehler in ls3render_AddFahrzeug')

    def renderImage(self):
        hoehe = self.dll.ls3render_GetBildhoehe()
        breite = self.dll.ls3render_GetBildbreite()
        imgDimensions = (breite, hoehe)

        pufSize = self.dll.ls3render_GetAusgabepufferGroesse()
        puffer = (c_ubyte * pufSize)()
        result = self.dll.ls3render_Render(byref(puffer))
        if result == 0:
            raise Exception('Fehler in ls3render_Render')

        img = Image.frombuffer('RGBA', imgDimensions, puffer, 'raw', 'BGRA', 0, -1)
        return img
