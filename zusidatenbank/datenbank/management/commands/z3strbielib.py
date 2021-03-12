from ctypes import *
from enum import IntEnum

# https://docs.microsoft.com/en-us/windows/win32/direct3d9/d3dximage-fileformat
class D3DXIMAGE_FILEFORMAT(IntEnum):
  D3DXIFF_BMP          = 0
  D3DXIFF_JPG          = 1
  D3DXIFF_TGA          = 2
  D3DXIFF_PNG          = 3
  D3DXIFF_DDS          = 4
  D3DXIFF_PPM          = 5
  D3DXIFF_DIB          = 6
  D3DXIFF_HDR          = 7
  D3DXIFF_PFM          = 8
  D3DXIFF_FORCE_DWORD  = 0x7fffffff

def _c_str(string):
    return c_char_p(string.encode())

class Z3StrbieLib:

    def __init__(self, path):
        self.dll = WinDLL(path)

        self.dll.ftdVorschau.restype = c_bool

    def ftdVorschau(self, arbeitsverzeichnis, ftdDatei, imgDatei, ansicht, format, width, height):
        x = c_int()
        y = c_int()

        """
        function ftdVorschau( Arbeitsverzeichnis,                // Datenverzeichnis der Zusi-Daten
                              DateiName,                         // Dateiname der ftd-Datei relativ zum Datenverzeichnis 
                              BMPDateiname:PChar;                // voller Pfad der zu erzeugenden Bilddatei
                              Modus:Byte;                        // bisher ohne Funktion
                              DXHandle:THandle;                  // Handle des aufrufenden Programms
                              AnsichtNr,                         // laufende Nummer der Grafikansicht
                              BMPWidth, BMPHeight:integer;       // Abmessungen des Bilds
                              BMPFormat:TD3DXImageFileformat;    // Dateityp des Bilds, siehe unten
                              var x,y:integer                    // RÃ¼ckgabe: AuflÃ¶sung der Grafikansicht
                              ):Boolean; stdcall;
        """
        result = self.dll.ftdVorschau(_c_str(arbeitsverzeichnis), _c_str(ftdDatei), _c_str(imgDatei), c_byte(0), c_uint32(0), c_int(ansicht), c_int(width), c_int(height), c_uint32(format), byref(x), byref(y))

        if result == False:
            raise RuntimeError("Fehler in ftdVorschau für " + ftdDatei + "/" + str(ansicht))

        return (x.value, y.value)
