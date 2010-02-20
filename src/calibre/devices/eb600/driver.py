# -*- coding: utf-8 -*-

__license__   = 'GPL v3'
__copyright__ = '2009, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

'''
Device driver for the Netronix EB600

Windows PNP strings:
 ('USBSTOR\\DISK&VEN_NETRONIX&PROD_EBOOK&REV_062E\\6&1A275569&0&EB6001009
2W00000&0', 2, u'F:\\')
        ('USBSTOR\\DISK&VEN_NETRONIX&PROD_EBOOK&REV_062E\\6&1A275569&0&EB6001009
2W00000&1', 3, u'G:\\')

'''
import re

from calibre.devices.usbms.driver import USBMS

class EB600(USBMS):

    name           = 'Netronix EB600 Device Interface'
    description    = _('Communicate with the EB600 eBook reader.')
    author         = 'Kovid Goyal'
    supported_platforms = ['windows', 'osx', 'linux']

    # Ordered list of supported formats
    FORMATS     = ['epub', 'mobi', 'prc', 'chm', 'djvu', 'html', 'rtf', 'txt',
        'pdf']
    DRM_FORMATS = ['prc', 'mobi', 'html', 'pdf', 'txt']

    VENDOR_ID   = [0x1f85]
    PRODUCT_ID  = [0x1688]
    BCD         = [0x110]

    VENDOR_NAME      = 'NETRONIX'
    WINDOWS_MAIN_MEM = 'EBOOK'
    WINDOWS_CARD_A_MEM = 'EBOOK'

    OSX_MAIN_MEM = 'EB600 Internal Storage Media'
    OSX_CARD_A_MEM = 'EB600 Card Storage Media'

    MAIN_MEMORY_VOLUME_LABEL  = 'EB600 Main Memory'
    STORAGE_CARD_VOLUME_LABEL = 'EB600 Storage Card'

    EBOOK_DIR_MAIN = ''
    EBOOK_DIR_CARD_A = ''
    SUPPORTS_SUB_DIRS = True

    def windows_sort_drives(self, drives):
        main = drives.get('main', None)
        card = drives.get('carda', None)
        if card and main and card < main:
            drives['main'] = card
            drives['carda'] = main

        return drives


class COOL_ER(EB600):

    name = 'Cool-er device interface'
    gui_name = 'Cool-er'

    FORMATS = ['epub', 'mobi', 'prc', 'pdf', 'txt']

    VENDOR_NAME = 'COOL-ER'
    WINDOWS_MAIN_MEM = 'EREADER'

    OSX_MAIN_MEM = 'COOL-ER eReader Media'

    EBOOK_DIR_MAIN = 'my docs'

class SHINEBOOK(EB600):

    name = 'ShineBook device Interface'

    gui_name = 'ShineBook'

    FORMATS = ['epub', 'prc', 'rtf', 'pdf', 'txt']

    VENDOR_NAME      = 'LONGSHIN'
    WINDOWS_MAIN_MEM = 'ESHINEBOOK'
    MAIN_MEMORY_VOLUME_LABEL  = 'ShineBook Main Memory'
    STORAGE_CARD_VOLUME_LABEL = 'ShineBook Storage Card'


    @classmethod
    def can_handle(cls, dev, debug=False):
        return dev[4] == 'ShineBook'



class POCKETBOOK360(EB600):

    # Device info on OS X
    # (8069L, 5768L, 272L, u'', u'', u'1.00')

    name = 'PocketBook 360 Device Interface'

    gui_name = 'PocketBook 360'

    FORMATS = ['epub', 'fb2', 'prc', 'mobi', 'pdf', 'djvu', 'rtf', 'chm', 'txt']

    VENDOR_NAME = 'PHILIPS'
    WINDOWS_MAIN_MEM = 'MASS_STORGE'
    WINDOWS_CARD_A_MEM = 'MASS_STORGE'

    OSX_MAIN_MEM   = 'Philips Mass Storge Media'
    OSX_CARD_A_MEM = 'Philips Mass Storge Media'
    OSX_MAIN_MEM_VOL_PAT = re.compile(r'/Pocket')

    @classmethod
    def can_handle(cls, dev, debug=False):
        return dev[-1] == '1.00' and not dev[-2] and not dev[-3]

class GER2(EB600):

    name = 'Ganaxa GeR2 Device Interface'
    gui_name = 'Ganaxa GeR2'

    FORMATS = ['pdf']

    VENDOR_ID   = [0x3034]
    PRODUCT_ID  = [0x1795]
    BCD         = [0x132]

    VENDOR_NAME = 'GANAXA'
    WINDOWS_MAIN_MEN = 'GER2_________-FD'
    WINDOWS_CARD_A_MEM = 'GER2_________-SD'

class ITALICA(EB600):

    name = 'Italica Device Interface'
    gui_name = 'Italica'
    icon = I('devices/italica.png')

    FORMATS = ['epub', 'rtf', 'fb2', 'html', 'prc', 'mobi', 'pdf', 'txt']

    VENDOR_NAME = 'ITALICA'
    WINDOWS_MAIN_MEM = 'EREADER'
    WINDOWS_CARD_A_MEM = WINDOWS_MAIN_MEM

    OSX_MAIN_MEM = 'Italica eReader Media'
    OSX_CARD_A_MEM = OSX_MAIN_MEM

    MAIN_MEMORY_VOLUME_LABEL  = 'Italica Main Memory'
    STORAGE_CARD_VOLUME_LABEL = 'Italica Storage Card'


class ECLICTO(EB600):

    name = 'eClicto Device Interface'
    gui_name = 'eClicto'

    FORMATS = ['epub', 'pdf', 'htm', 'html', 'txt']

    VENDOR_NAME = 'ECLICTO'
    WINDOWS_MAIN_MEM = 'EBOOK'
    WINDOWS_CARD_A_MEM = 'EBOOK'

    EBOOK_DIR_MAIN = 'Text'
    EBOOK_DIR_CARD_A = ''

class DBOOK(EB600):

    name = 'Airis Dbook Device Interface'
    gui_name = 'Airis Dbook'

    FORMATS = ['epub', 'mobi', 'prc', 'fb2', 'html', 'pdf', 'rtf', 'txt']

    VENDOR_NAME = 'INFINITY'
    WINDOWS_MAIN_MEM = 'AIRIS_DBOOK'
    WINDOWS_CARD_A_MEM = 'AIRIS_DBOOK'

class INVESBOOK(EB600):

    name = 'Inves Book Device Interface'
    gui_name = 'Inves Book 600'

    FORMATS = ['epub', 'mobi', 'prc', 'fb2', 'html', 'pdf', 'rtf', 'txt']

    VENDOR_NAME = 'INVES_E6'
    WINDOWS_MAIN_MEM = '00INVES_E600'
    WINDOWS_CARD_A_MEM = '00INVES_E600'

class BOOQ(EB600):
    name = 'Booq Device Interface'
    gui_name = 'Booq'

    FORMATS = ['epub', 'mobi', 'prc', 'fb2', 'pdf', 'doc', 'rtf', 'txt', 'html']

    VENDOR_NAME = 'NETRONIX'
    WINDOWS_MAIN_MEM = 'EB600'
    WINDOWS_CARD_A_MEM = 'EB600'

