#!/usr/bin/env  python

__license__   = 'GPL v3'
__copyright__ = '2008, Kovid Goyal <kovid at kovidgoyal.net>'
'''
Embedded console for debugging.
'''

import sys, os, re
from calibre.utils.config import OptionParser
from calibre.constants import iswindows, isosx
from calibre.libunzip import update

def option_parser():
    parser = OptionParser(usage='''\
%prog [options]

Run an embedded python interpreter.
''')
    parser.add_option('--update-module', help='Update the specified module in the frozen library. '+
    'Module specifications are of the form full.name.of.module,path_to_module.py', default=None
    )
    parser.add_option('-c', '--command', help='Run python code.', default=None)
    parser.add_option('-e', '--exec-file', default=None, help='Run the python code in file.')
    parser.add_option('-d', '--debug-device-driver', default=False, action='store_true', 
                      help='Debug the specified device driver.')
    parser.add_option('-g', '--gui',  default=False, action='store_true',
                      help='Run the GUI',)
    parser.add_option('--migrate', action='store_true', default=False, 
                      help='Migrate old database. Needs two arguments. Path to library1.db and path to new library folder.')
    return parser

def update_zipfile(zipfile, mod, path):
    if 'win32' in sys.platform:
        print 'WARNING: On Windows Vista using this option may cause windows to put library.zip into the Virtual Store (typically located in c:\Users\username\AppData\Local\VirtualStore). If it does this you must delete it from there after you\'re done debugging).' 
    pat = re.compile(mod.replace('.', '/')+r'\.py[co]*')
    name = mod.replace('.', '/') + os.path.splitext(path)[-1]
    update(zipfile, [pat], [path], [name])


def update_module(mod, path):
    if not hasattr(sys, 'frozen'):
        raise RuntimeError('Modules can only be updated in frozen installs.')
    zp = None
    if iswindows:
        zp = os.path.join(os.path.dirname(sys.executable), 'library.zip')
    elif isosx:
        zp = os.path.join(os.path.dirname(getattr(sys, 'frameworks_dir')),
                            'Resources', 'lib', 
                            'python'+'.'.join(map(str, sys.version_info[:2])), 
                            'site-packages.zip')
    else:
        zp = os.path.join(getattr(sys, 'frozen_path'), 'loader.zip')
    if zp is not None:
        update_zipfile(zp, mod, path)
    else:
        raise ValueError('Updating modules is not supported on this platform.')

def migrate(old, new):
    from calibre.utils.config import prefs
    from calibre.library.database import LibraryDatabase
    from calibre.library.database2 import LibraryDatabase2
    from calibre.utils.terminfo import ProgressBar
    from calibre import terminal_controller
    class Dummy(ProgressBar):
        def setLabelText(self, x): pass
        def setAutoReset(self, y): pass
        def reset(self): pass
        def setRange(self, min, max):
            self.min = min
            self.max = max
        def setValue(self, val):
            self.update(float(val)/getattr(self, 'max', 1))
            
    db = LibraryDatabase(old)
    db2 = LibraryDatabase2(new)
    db2.migrate_old(db, Dummy(terminal_controller, 'Migrating database...'))
    prefs['library_path'] = os.path.abspath(new)
    print 'Database migrated to', os.path.abspath(new)
    
def debug_device_driver():
    from calibre.devices.scanner import DeviceScanner
    s = DeviceScanner()
    s.scan()
    print 'USB devices on system:', repr(s.devices)
    if iswindows:
        wmi = __import__('wmi', globals(), locals(), [], -1) 
        drives = []
        print 'Drives detected:'
        print '\t', '(ID, Partitions, Drive letter)' 
        for drive in wmi.WMI().Win32_DiskDrive():
            if drive.Partitions == 0:
                continue
            try:
                partition = drive.associators("Win32_DiskDriveToDiskPartition")[0]
                logical_disk = partition.associators('Win32_LogicalDiskToPartition')[0]
                prefix = logical_disk.DeviceID+os.sep
                drives.append((str(drive.PNPDeviceID), drive.Index, prefix))
            except IndexError:
                drives.append(str(drive.PNPDeviceID))
        for drive in drives:
            print '\t', drive
    from calibre.devices import devices
    for dev in devices():
        print 'Looking for', dev.__name__
        connected = s.is_device_connected(dev)
        if connected:
            print 'Device Connected:', dev
            print 'Trying to open device...'
            d = dev()
            d.open()
            print 'Total space:', d.total_space()
            break
        

def main(args=sys.argv):
    opts, args = option_parser().parse_args(args)
    if opts.gui:
        from calibre.gui2.main import main
        main(['calibre'])
    elif opts.update_module:
        mod, path = opts.update_module.partition(',')[0], opts.update_module.partition(',')[-1]
        update_module(mod, os.path.expanduser(path))
    elif opts.command:
        sys.argv = args[:1]
        exec opts.command
    elif opts.exec_file:
        sys.argv = args[:1]
        execfile(opts.exec_file)
    elif opts.debug_device_driver:
        debug_device_driver()
    elif opts.migrate:
        if len(args) < 3:
            print 'You must specify the path to library1.db and the path to the new library folder'
            return 1
        migrate(args[1], args[2])
    else:
        from IPython.Shell import IPShellEmbed
        ipshell = IPShellEmbed()
        ipshell()



    return 0

if __name__ == '__main__':
    sys.exit(main())
