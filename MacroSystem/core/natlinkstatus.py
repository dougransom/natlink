__version__ = "4.2"
#
# natlinkstatus.py
#   This module gives the status of Natlink to natlinkmain
#
#  (C) Copyright Quintijn Hoogenboom, February 2008/January 2018
#  Adapted to new directories strategy with python3, and new natlinkmain.py (James Murphy, kb100)
#
#----------------------------------------------------------------------------
# previous version history to be found in git versions up to FinalCommitWithVocola, 21-8-2020
#
"""The following functions are provided in this module:
(to be used by either natlinkmain.py or natlinkconfigfunctions.py)

The functions below are put into the class NatlinkStatus.
The natlinkconfigfunctions can subclass this class, and
the configurenatlink.py (GUI) again sub-subclasses this one.

The following  functions manage information that changes at changeCallback time
(when a new user opens)

setUserInfo(args) put username and directory of speech profiles of the last opened user in this class.
getUsername: get active username (only if NatSpeak/Natlink is running)
getDNSuserDirectory: get directory of user speech profile (only if NatSpeak/Natlink is running)


The functions below should not change anything in settings, only  get information.

getDNSInstallDir:
    returns the directory where NatSpeak is installed.
    if the registry key NatspeakInstallDir exists(CURRENT_USER/Software/Natlink),
    this path is taken (if it points to a valid folder)
    Otherwise one of the default paths is taken,
    %PROGRAMFILES%/Nuance/... or %PROGRAMFILES%/ScanSoft/...
    It must contain at least a Program subdirectory or App/Program subdirectory

getDNSIniDir:
    returns the directory where the NatSpeak INI files are located,
    notably nssystem.ini and nsapps.ini.
    Can be set in natlinkstatus.ini, but mostly is got from
    %ALLUSERSPROFILE% (C:/ProgramData)

getDNSVersion:
    returns the in the version number of NatSpeak, as an integer. So 9, 8, 7, ... (???)
    note distinction is made here between different subversions.
(getDNSFullVersion: get longer version string) (obsolete, 2017, QH)
.
getWindowsVersion:
    see source below

getLanguage:
    returns the 3 letter code of the language of the speech profile that
    is open (only possible when NatSpeak/Natlink is running)

getUserLanguage:
    returns the language from changeCallback (>= 15) or config files

getUserTopic
    returns the topic of the current speech profile, via changeCallback (>= 15) or config files

getPythonVersion:
    changed jan 2013, return two character version, so without the dot! eg '26'

    new nov 2009: return first three characters of python full version ('2.5')
#    returns, as a string, the python version. Eg. "2.3"
#    If it cannot find it in the registry it returns an empty string
#(getFullPythonVersion: get string of complete version info).


getUserDirectory: get the Natlink user directory, 
    Especially Dragonfly users will use this directory for putting their grammar files in.
    Also users that have their own custom grammar files can use this user directory

getUnimacroDirectory: get the directory where the Unimacro system is.
    When git cloned, relative to the Core directory, otherwise somewhere or in the site-packages (if pipped). This grammar will (and should) hold the _control.py grammar
    and needs to be included in the load directories list of James' natlinkmain

getUnimacroGrammarsDirectory: get the directory, where the user can put his Unimacro grammars. By default
    this will be the ActiveGrammars subdirectory of the UnimacroUserDirectory.

getUnimacroUserDirectory: get the directory of Unimacro INI files, if not return '' or
      the Unimacro user directory

getVocolaDirectory: get the directory where the Vocola system is. When cloned from git, in Vocola, relative to
      the Core directory. Otherwise (when pipped) in some site-packages directory. It holds (and should hold) the
      grammar _vocola_main.py.

getVocolaUserDirectory: get the directory of Vocola User files, if not return ''
    (if run from natlinkconfigfunctions use getVocolaDirectoryFromIni, which checks inifile
     at each call...)

getVocolaGrammarsDirectory: get the directory, where the compiled Vocola grammars are/will be.
    This will normally be the "CompiledGrammars" subdirectory of the VocolaUserDirectory.

NatlinkIsEnabled:
    return 1 or 0 whether Natlink is enabled or not
    returns None when strange values are found
    (checked with the INI file settings of NSSystemIni and NSAppsIni)

getNSSYSTEMIni(): get the path of nssystem.ini
getNSAPPSIni(): get the path of nsapps.ini

getBaseModelBaseTopic:
    return these as strings, not ready yet, only possible when
    NatSpeak/Natlink is running. Obsolete 2018, use
getBaseModel
    get the acoustic model from config files (for DPI15, obsolescent)
getBaseTopic
    get the baseTopic, from ini files. Better use getUserTopic in DPI15
getDebugLoad:
    get value from registry, if set do extra output of natlinkmain at (re)load time
getDebugCallback:
    get value from registry, if set do extra output of natlinkmain at callbacks is given
getDebugOutput:
    get value from registry, output in log file of DNS, should be kept at 0

getVocolaTakesLanguages: additional settings for Vocola

new 2014:
getDNSName: return "NatSpeak" for versions <= 11 and "Dragon" for 12 (on)
getAhkExeDir: return the directory where AutoHotkey is found (only needed when not in default)
getAhkUserDir: return User Directory of AutoHotkey, not needed when it is in default.

"""
import os
import re
import win32api
import win32con
import sys
import pprint
import stat
import winreg 
import pywintypes
import time
import types
from pathqh import path   
# for getting generalised env variables:

##from win32com.shell import shell, shellcon

# adapt here
VocIniFile  = r"Vocola\Exec\vocola.ini"

lowestSupportedPythonVersion = 37

DNSPaths = []
DNSVersions = list(range(19,14,-1))
for v in DNSVersions:
    varname = "NSExt%sPath"%v
    if "NSExt%sPath"% v not in globals():
        globals()[varname] = "Nuance\\NaturallySpeaking%s"% v
    DNSPaths.append(globals()[varname])

# utility functions:
## report function:
def fatal_error(message, new_raise=None):
    """prints a fatal error when running this module"""
    print()
    print('natlinkconfigfunctions fails because of fatal error:')
    print()
    print(message)
    print()
    print('This can (hopefully) be solved by closing Dragon and then running the Natlink/Unimacro/Vocola Config program with administrator rights.')
    print()
    if new_raise:
        raise

# Nearly obsolete table, for extracting older windows versions:
# newer versions go via platform.platform()
Wversions = {'1/4/10': '98',
             '2/3/51': 'NT351',
             '2/4/0':  'NT4',
             '2/5/0':  '2000',
             '2/5/1':  'XP',
             '2/6/0':  'Vista'
             }

# the possible languages (for getLanguage)
languages = {  # from config files (if not given by args in setUserInfo)
             "Nederlands": "nld",
             "Fran\xe7ais": "fra",
             "Deutsch": "deu",
             # English is detected as second word of userLanguage
             # "UK English": "enx",
             # "US English": "enx",
             # "Australian English": "enx",
             # # "Canadian English": "enx",
             # "Indian English": "enx",
             # "SEAsian English": "enx",
             "Italiano": "ita",
             "Espa\xf1ol": "esp",
             # as passed by args in changeCallback, DPI15:
             "Dutch": "nld",
             "French": "fra",
             "German": "deu",
             # "CAN English": "enx",
             # "AUS English": "enx",
             "Italian": "ita",
             "Spanish": "esp",}

shiftKeyDict = {"nld": "Shift",
                "enx": 'shift',
                "fra": "maj",
                "deu": "umschalt",
                "ita": "maiusc",
                "esp": "may\xfas"}

reportDNSIniDirErrors = True # set after one stroke to False, if errors were there (2017, february)


class NatlinkStatus:
    """this class holds the Natlink status functions

    so, can be called from natlinkmain.

    in the natlinkconfigfunctions it is subclassed for installation things
    in the PyTest folder there are/come test functions in TestNatlinkStatus

    """
    userregnl = natlinkcorefunctions.NatlinkstatusInifileSection()

    ### from previous modules, needed or not...
    NATLINK_CLSID  = "{dd990001-bb89-11d2-b031-0060088dc929}"

    NSSystemIni  = "nssystem.ini"
    NSAppsIni  = "nsapps.ini"
    ## setting of nssystem.ini if Natlink is enabled...
    ## this first setting is decisive for NatSpeak if it loads Natlink or not
    section1 = "Global Clients"
    key1 = ".Natlink"
    value1 = 'Python Macro System'

    ## setting of nsapps.ini if Natlink is enabled...
    ## this setting is ignored if above setting is not there...
    section2 = ".Natlink"
    key2 = "App Support GUID"
    value2 = NATLINK_CLSID

    userArgsDict = {}

    # for quicker access (only once lookup in a run)
    UserDirectory = None # for Dragonfly mainly, and for user defined grammars
    BaseDirectory = None
    CoreDirectory = None
    DNSInstallDir = None
    DNSVersion = None
    DNSIniDir = None
    ## Unimacro:
    UnimacroDirectory = None
    UnimacroUserDirectory = None
    UnimacroGrammarsDirectory = None
    ## Vocola:
    VocolaUserDirectory = None
    VocolaDirectory = None
    VocolaGrammarsDirectory = None
    ## AutoHotkey:
    AhkUserDir = None
    AhkExeDir = None
    hadWarning = []

    def __init__(self, skipSpecialWarning=None):

        self.skipSpecialWarning = skipSpecialWarning

        ## start setting the CoreDirectory and BaseDirectory and other variables:
        if self.CoreDirectory is None:
            CoreDirectory = natlinkcorefunctions.getBaseFolder()
            self.__class__.CoreDirectory = CoreDirectory
            self.__class__.BaseDirectory = os.path.normpath(os.path.join(CoreDirectory, '..'))
            self.__class__.NatlinkDirectory = os.path.normpath(os.path.join(CoreDirectory, '..', '..'))
            assert os.path.isdir(self.NatlinkDirectory)
            self.correctIniSettings() # change to newer conventions
        
            ## initialise DNSInstallDir, DNSVersion and DNSIniDir
            ## other "cached" variables, like UserDirectory, are done at first call.
            try:
                result = self.getDNSInstallDir()
            except IOError:
                result = -1
            else:
                result = result or -1
            self.__class__.DNSInstallDir = result
                
                
            if result == -1:
                ## also DNSIniDir is hopeless, set value and return.
                self.__class__.DNSIniDir = result
                self.__class__.DNSVersion = result
                return
            else:
                ## proceed with other __class__ variables:
                self.__class__.DNSVersion = self.getDNSVersion()

                ## DNSIniDir:
                try:
                    result = self.getDNSIniDir()
                except IOError:
                    result = -1
                else:
                    result = result or -1

                self.__class__.DNSIniDir = result
                if result == -1:
                    return  # serious problem.

            result = self.checkNatlinkPydFile()
            if result is None:
                if not skipSpecialWarning:
                    self.warning('WARNING: invalid or no version of natlink.pyd found\nClose Dragon and then run the\nconfiguration program "configurenatlink.pyw" via "start_configurenatlink.py"')

    def getWarningText(self):
        """return a printable text if there were warnings
        """
        if self.hadWarning:
            t = 'natlinkstatus reported the following warnings:\n\n'
            t += '\n\n'.join(self.hadWarning)
            return t
        return ""

    def emptyWarning(self):
        """clear the list of warning messages
        """
        while self.hadWarning:
            self.hadWarning.pop()

    def checkSysPath(self):
        """add base, unimacro and user directory to sys.path

        if Vocola is enabled, but Unimacro is NOT and the option VocolaTakesUnimacroActions is True,
        then also include the Unimacro directory!

        (the registry is out of use, only the core directory is in the
        PythonPath / Natlink setting, for natlink be able to be started.

        Also set here the CoreDirectory and BaseDirectory
        """
        CoreDirectory = self.getCoreDirectory()

        if CoreDirectory.lower().endswith('core'):
            # check the registry setting:
            result = self.getRegistryPythonPathNatlink()
            if not result:
                print('''Natlink setting not found in Natlink section of PythonPath setting\n
Please try to correct this by running the Natlink Config Program (with administration rights)\n''')
                return
            natlinkvalue, pythonpathkey = result
            if not natlinkvalue:
                print(f'''Natlink setting not found in Natlink section of PythonPath setting {pythonpathkey} in registry\n
Please try to correct this by running the Natlink Config Program (with administration rights)''')
                return

            coreDirectory = path(natlinkvalue)
            if not coreDirectory.isdir():
                print(f'''Natlink setting "{coreDirectory}" in "{pythonpathkey}" of the registry is not a valid directory\n
Please try to correct this by running the Natlink Config Program (with administration rights)''')
#             if setting.lower() == CoreDirectory.lower():
#                 baseDir = os.path.normpath(os.path.join(CoreDirectory, ".."))
#                 self.InsertToSysPath(CoreDirectory)
#                 self.InsertToSysPath(baseDir)
#             else:
#                 print(("""PythonPath/Natlink setting in registry does not match this core directory\n
# registry: %s\nCoreDirectory: %s\n
# Please try to correct this by running the Natlink Config Program (with administration rights)"""% (
#                 setting, CoreDirectory)))
#                 return
#         else:
#             baseDir = None
#             print('non expected core directory %s, cannot find baseDirectory\nTry to run the Config Program with administrator rights'% CoreDirectory)
#         userDir = self.getUserDirectory()
#         # special for other user directories, insert also unimacro for actions etc.
#         if userDir:
#             self.InsertToSysPath(userDir)
# 
#         includeUnimacroDirectory =  self.UnimacroIsEnabled() or (self.VocolaIsEnabled() and self.getVocolaTakesUnimacroActions())
#         if  includeUnimacroDirectory:
#             if not baseDir:
#                 print('no baseDir found, cannot "IncludeUnimacroInPythonPath"')
#                 return
#             unimacroDir = os.path.join(baseDir, '..', '..', 'Unimacro')
#             unimacroDir = os.path.normpath(unimacroDir)
#             if os.path.isdir(unimacroDir):
#                 self.InsertToSysPath(unimacroDir)
#             else:
#                 print(('no valid UnimacroDir found(%s), cannot "IncludeUnimacroInPythonPath"'% \
#                     unimacroDir))

        return 1


    def checkNatlinkPydFile(self, fromConfig=None):
        """see if natlink.dll is in core directory, and uptodate, if not stop and point to the configurenatlink program

        if fromConfig, print less messages...

        if natlink.pyd is missing, or
        if NatlinkPydRegistered is absent or not correct, or
        if the original natlink26_12.pyd (for example) is newer than natlink.pyd

        # july 2013:
        now conform to the new naming conventions of Rudiger, PYD subdirectory and natlink_2.7_UNICODE.pyd etc.
        the natlink25.pyd has been moved to the PYD directory too and also is named according to the new conventions.

        the config program should be run.
        """
        # with James' installer skip this check:

        
        CoreDirectory = self.getCoreDirectory()
        pydDir = path(CoreDirectory)/'PYD'
        if not (pydDir and pydDir.isdir()):
            return 1

        originalPyd = self.getOriginalNatlinkPydFile()   # original if previously registerd (from natlinkstatus.ini file)
        wantedPyd = self.getWantedNatlinkPydFile()       # wanted original based on python version and Dragon version
        wantedPydPath = pydDir/wantedPyd
        currentPydPath = path(CoreDirectory)/'natlink.pyd'

        if not wantedPydPath.isfile():
            if not fromConfig:
                print(f'The wanted pyd "{wantedPydPath}" does not exist, Dragon/python combination not valid.')
            return

        # first check existence of natlink.pyd (probably never comes here)
        if not currentPydPath.isfile():
            if not fromConfig:
                print(f'pyd path "{currentPydPath}" does not exist...')
            return

        # check correct pyd version, with python version and Dragon version:
        if wantedPyd != originalPyd:
            if not fromConfig:
                if not originalPyd:
                    self.warning('originalPyd setting is missing in natlinkstatus.ini')
                else:
                    self.warning('incorrect originalPyd (from natlinkstatus.ini): %s, wanted: %s'% (originalPyd, wantedPyd))
            return

        # now check for updates:
        timeWantedPyd = getFileDate(wantedPydPath)
        timeCurrentPyd = getFileDate(currentPydPath)

        # check for newer (changed version) of original pyd:
        if timeCurrentPyd or timeWantedPyd:
            if timeWantedPyd > timeCurrentPyd:
                if not fromConfig:
                    self.warning('Current pyd file (%s) out of date, compared with\n%s'% (currentPydPath, wantedPydPath))
                return
        # all well
        return 1
    
    def getHiveKeyReadable(self, hive):
        if hive == winreg.HKEY_LOCAL_MACHINE: return 'HKLM'
        if hive == winreg.HKEY_CURRENT_USER: return 'HKCU'
        return 'HK??'

    def getRegistryPythonPathKey(self, silent=True):
        """returns the key to PythonPath setting in the registry
        
        This must be a 32-bit python version as given by sys.winver
        
        flag is winreg.KEY_READ (always read only) and KEY_WOW64_32KEY
        
        Returns the key, which can come from either
        CURRENT_USER (python installed for one user) or
        LOCAL_MACHINE (python installed for all users)
        
        """
        dottedVersion = sys.winver
        
        pythonPathSectionName = r"SOFTWARE\Python\PythonCore\%s\PythonPath"% dottedVersion
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            key, flags = (pythonPathSectionName, winreg.KEY_WOW64_32KEY | winreg.KEY_READ)
            try:
                pythonpath_key = winreg.OpenKeyEx(hive, key, access= flags)
                if pythonpath_key:
                    return pythonpath_key
            except FileNotFoundError:
                continue
            print(f'no valid PythonPath/Natlink key found in registry')
            return

    def getRegistryPythonPathNatlink(self, flags=winreg.KEY_READ, silent=True):
        """returns the path-to-core of Natlink and the PythonPath key in the registry
        
        returns a tuple (path-to-core, key-to-pythonpath-setting)
        
        if no Natlink key found, or no path, "" is returned
        if no PythonPath setting is found, None is return

        by default read only.
        When setting the value, from natlinkconfigfunctions,
        pass winreg.KEY_ALL_ACCESS as flags.

        """
        pythonpath_key = self.getRegistryPythonPathKey()
        if not pythonpath_key:
            print('no valid pythonpath key in registry found')
            return
        for i in range(10):
            try:
                keyName = winreg.EnumKey(pythonpath_key, i)
                if keyName.lower() == 'natlink':
                    natlink_key = winreg.OpenKey(pythonpath_key, keyName)
                    for i in range(10):
                        Value = winreg.EnumValue(natlink_key, i)
                        # print(f'values: {i}, {Value}')
                        break
                    else:
                        print(f'no valid Natlink entry found in registry section "Natlink"')
                        raise FileNotFoundError
                    
                    if type(Value) == tuple and len(Value) == 3:
                        pythonpath = Value[1]
                        natlinkmainPath = os.path.join(pythonpath, "natlinkmain.py")
                        if os.path.isfile(natlinkmainPath):
                            if not silent:
                                print(f'Natlink entry found in registry section "Natlink": "{pythonpath}"')
                            return pythonpath, natlink_key
                        else:
                            print(f'no valid Natlink entry found in registry section "Natlink": {pythonpath}, does not contain "natlinkmain.py"')
                            raise FileNotFoundError
                            
            except OSError:
                return 
        
    def InsertToSysPath(self, newdir):
        """leave "." in the first place if it is there"""
        if not newdir: return
        newdir = os.path.normpath(newdir)
        newdir = win32api.GetLongPathName(newdir)
        # keep the convention of capitalizing the drive letter:
        if len(newdir) > 1 and newdir[1] == ":":
            newdir = newdir[0].upper() + newdir[1:]

        if newdir in sys.path: return
        if sys.path[0] in ("", "."):
            sys.path.insert(1, newdir)
        else:
            sys.path.insert(0, newdir)
        #print 'inserted in sys.path: %s'% newdir

    def copyRegSettingsToInifile(self, reg, ini):
        """for firsttime use, copy values from
        """
        for k,v in list(reg.items()):
            ini.set(k, v)
        #except:
        #    print 'could not copy settings from registry into inifile. Run natlinkconfigfunctions...'

    def correctIniSettings(self):
        """change NatlinkDllRegistered to NatlinkPydRegistered

        the new value should have 25;12 (so python version and dragon version)
        """
        ini = self.userregnl
        oldSetting = ini.get('NatlinkDllRegistered')
        newSetting = ini.get('NatlinkPydRegistered')
        if oldSetting and not newSetting:
            if len(oldSetting) <= 2:
                dragonVersion = self.getDNSVersion()
                if dragonVersion <= 11:
                    # silently go over to new settings:
                    oldSetting = "%s;%s"% (oldSetting, dragonVersion)
            print('correct setting from "NatlinkDllRegistered" to "NatlinkPydRegistered"')
            ini.set('NatlinkPydRegistered', oldSetting)
            ini.delete('NatlinkDllRegistered')
        oldSetting = ini.get('UserDirectory')
        if oldSetting and oldSetting.find('Unimacro') > 0:
            ini.delete('UserDirectory')
        oldSetting = ini.get('IncludeUnimacroInPythonPath')
        if oldSetting:
            ini.delete('IncludeUnimacroInPythonPath')

    def setUserInfo(self, args):
        """set username and userdirectory at change callback user
        
        args[0] = username
        args[1] = Current directory for user profile (in programdata/nuance etc)
                  extract for example userLanguage ('Nederlands') from acoustics.ini and options.ini

        if the three letter "language" ('enx', 'nld' etc) is not found there is an error in this module: 'languages' dict.
        English dialects are detected if the userLanguage is '.... English'.
        
        if there is no connection with natlink (no speech profile on, when debugging) language 'tst' is returned in getLanguage
        
        """
        # print("setUserInfo, args: %s"% repr(args))
        if len(args) < 2:
            print('UNEXPECTED ERROR: natlinkstatus, setUserInfo: length of args to small, should be at least 2: %s (%s)'% (len(args), repr(args)))
            return

        userName = args[0]
        self.userArgsDict['userName'] = userName
        DNSuserDirectory = args[1]
        self.userArgsDict['DNSuserDirectory'] = DNSuserDirectory
        if len(args) == 2:
            userLanguage = self.getUserLanguageFromInifile()
            try:
                language = languages[userLanguage]
            except KeyError:
                englishDialect = userLanguage.split()[-1]
                if englishDialect == 'English':
                    language = 'enx'
                else:
                    print('natlinkstatus, setUserInfo: no language found for userLanguage: %s'% userLanguage)
                    print('=== please report to q.hoogenboom@antenna.nl ===')
                    language = ''
            self.userArgsDict['language'] = language
            self.userArgsDict['userLanguage'] = userLanguage
            self.userArgsDict['userTopic'] = self.getUserTopic() # will be the basetopic...

        elif len(args) == 4:
            print('natlinkstatus, setUserInfo: this case seems to be obsolete, (len(args) == 4!!): %s'% userLanguage)
            language = ''
            print('=== please report to q.hoogenboom@antenna.nl ===')
            # # 
            # # 
            # # userLanguage = args[2]
            # # try:
            # #     language = languages[userLanguage]
            # # except KeyError:
            # #     englishDialect = userLanguage.split()[-1]
            # #     if englishDialect == 'English':
            # #         language = 'enx'
            # #     else:
            # #         print('natlinkstatus, setUserInfo: no language found for userLanguage (len(args) == 4!!): %s'% userLanguage)
            # #         language = ''
            # #         print('=== please report to q.hoogenboom@antenna.nl ===')
            # #     userLanguageIni = self.getUserLanguageFromInifile()
            # #     try:
            # #         language = languages[userLanguageIni]
            # #     except KeyError:
            # #         print('SERIOUS ERROR: natlinkstatus, setUserInfo: cannot get language from  ini file either: %s'% userLanguageIni)
            # #         print('languages: %s'% languages)
            # #         language = 'zxz'
            # #     print('got language: %s, userLanguage1: %s, userLanguageIni (from config files): %s'% (language, userLanguage, userLanguageIni))
            # self.userArgsDict['language'] = language
            # self.userArgsDict['userLanguage'] = userLanguage
            # self.userArgsDict['userTopic'] = args[3]
        else:
            print('natlinkstatus, setUserInfo: unexpected length of args for userArgsDict: %s (%s)'% (len(args), repr(args)))
            print('=== please report to q.hoogenboom@antenna.nl ===')
            userLanguageIni = self.getUserLanguageFromInifile()
            try:
                language = ''
                language = languages[userLanguageIni]
            except KeyError:
                print('SERIOUS ERROR, natlinkstatus setUserInfo: cannot find language for %s'% userLanguageIni)
                print('got language: %s, userLanguageIni: %s'% (language, userLanguageIni))
                print('natlinkstatus, languages: %s'% languages)
                language = 'xyz'
            self.userArgsDict['language'] = language
            self.userArgsDict['userLanguage'] = userLanguageIni
            self.userArgsDict['userTopic'] = self.getBaseTopic()
        # print '--- natlinkstatus, set userArgsDict: %s'% self.userArgsDict

    def clearUserInfo(self):
        self.userArgsDict.clear()

    def getUserName(self):
        try:
            return self.userArgsDict['userName']
        except KeyError:
            return ''

    def getDNSuserDirectory(self):
        try:
            return self.userArgsDict['DNSuserDirectory']
        except KeyError:
            return ''

    def getOriginalNatlinkPydFile(self):
        """return the path of the original dll/pyd file

        "" if not registered before
        """
        setting = self.userregnl.get("NatlinkPydRegistered")
        if not setting:
            return ""
        if ";" in setting:
            pyth, drag = setting.split(";")
            pythonInFileName = pyth[0] + '.' + pyth[-1]
            pyth, drag = int(pyth), int(drag)
        else:
            pythonInFileName = setting[0] + '.' + setting[-1]
            pyth, drag = int(setting), 11  # which can also mean pre 11...

        if drag <= 11:
            ansiUnicode = 'ANSI'
        elif drag <= 14:
            ansiUnicode= 'UNICODE'
        else:
            ansiUnicode = 'Ver15'

        pydFilename = 'natlink_%s_%s.pyd'% (pythonInFileName, ansiUnicode)
        return pydFilename

    def getWantedNatlinkPydFile(self):
        """return the path pyd file with correct python and Dragon version

        with Dragon 12 insert _12 in the original name.
        .dll is dropped.

        """
        pyth = self.getPythonVersion()
        drag = self.getDNSVersion()
        pythonInFileName = pyth[0] + '.' + pyth[-1]
        if not pyth:
            return ""
        if not drag:
            return ""
        drag, pyth = int(drag), int(pyth)
        if drag <= 11:
            ansiUnicode = 'ANSI'
        elif drag <= 14:
            ansiUnicode= 'UNICODE'
        else:
            ansiUnicode = 'Ver15'

        pydFilename = 'natlink_%s_%s.pyd'% (pythonInFileName, ansiUnicode)
        return pydFilename

    def getWindowsVersion(self):
        """extract the windows version

        return 1 of the predefined values above, or just return what the system
        call returns
        """
        tup = win32api.GetVersionEx()
        version = "%s/%s/%s"% (tup[3], tup[0], tup[1])
        try:
            windowsVersion = Wversions[version]
        except KeyError:
            import platform
            wVersion = platform.platform()
            if '-' in wVersion:
                return wVersion.split('-')[1]
            else:
                print('Warning, probably cannot find correct Windows Version... (%s)'% wVersion)
                return wVersion
        else:
            return windowsVersion


    def getDNSIniDir(self, calledFrom=None, force=None):
        """get the path (one above the users profile paths) where the INI files
        should be located

        if force == True, refresh value (for use in config program)

        """
        global reportDNSIniDirErrors
        # first try if set (by configure dialog/natlinkinstallfunctions.py) if regkey is set:
        if self.DNSIniDir and force is None:
            return self.DNSIniDir

        key = 'DNSIniDir'
        P = self.userregnl.get(key)
        if P:
            os.path.normpath(P)
            if os.path.isdir(P):
                return P
        if calledFrom is None:
            knownDNSVersion = str(self.getDNSVersion())
        else:
            knownDNSVersion = None
    
        # the nssystem.ini and nsapps.ini are in the ProgramData directory
        # version 15: C:\ProgramData\Nuance\NaturallySpeaking15\Users

        # The User profile directory, from where the properties of the current profile are got
        # were, up to DNS15.3 in the ProgramData/Users directory
        # 
        # after DNS15.5:   %LOCALAPPDATA%s\Nuance\NS15\Users
        # but the DNSIniDir is unchanged with the upgrade to DNS15.5 or 15.6
        triedPaths = []
        ProgramDataDirectory = path('%ALLUSERSPROFILE%')
        # allusersprofileAppData = path('%LOCALAPPDATA%')
        DNSVersion = self.getDNSVersion()
        # if allusersprofileAppData.isdir():
        #     usersDir = allusersprofileAppData/('Nuance/NS%s'%DNSVersion)
        #     if usersDir.isdir():
        #         DNSIniDir = usersDir.normpath()
        #         return DNSIniDir
        #     triedPaths.append(usersDir.normpath())
        # else:
        #     triedPaths.append(allusersprofileAppData.normpath())

        if ProgramDataDirectory.isdir():
            usersDir = ProgramDataDirectory/(f'Nuance/NaturallySpeaking{DNSVersion}')
            if usersDir.isdir():
                DNSIniDir = usersDir.normpath()
                return DNSIniDir
            triedPaths.append(usersDir.normpath())
        
        if not triedPaths:
            report = []
            if reportDNSIniDirErrors:
                report.append('DNSIniDir not found, did not find paths to try from for version: %s'% self.getDNSVersion())
                report.append('Please report to q.hoogenboom@antenna.nl')

        if reportDNSIniDirErrors:
            report = []
            reportDNSIniDirErrors = False
            report.append('DNSIniDir not found, tried in directories: %s'% repr(triedPaths))
            report.append('no valid DNS INI files Dir found, please provide one in natlinkconfigfunctions (option "c") or in natlinkconfig  GUI (info panel)')
            report.append('Note: The path must end with "NaturallySpeaking%s"'% self.getDNSVersion())
            print('Errors in getDNSIniDir:')
            print('\n'.join(report))

    def getDNSFullVersion(self):
        """find the Full version string of DNS

        empty if not found, eg for older versions
        """
        print('getDNSFullVersion nearly obsolete')
        # for 9:
        iniDir = self.getDNSIniDir(calledFrom="getDNSFullVersion")
        # print 'iniDir: %s'% iniDir
        if not iniDir:
            return 0
        nssystemini = self.getNSSYSTEMIni()
        nsappsini = self.getNSAPPSIni()
        if nssystemini and os.path.isfile(nssystemini):
            version =win32api.GetProfileVal( "Product Attributes", "Version" , "",
                                          nssystemini)

            return version
        return ''


    def getDNSVersion(self):
        """find the correct DNS version number (as an integer)

        Version 15 is simply the int of the last two letters of the DNSInstallDir.

        note: 12.80 is also 13
        from 10 onwards, get as last two characters of the DNSInstallDir
        for versions 8 and 9 look in NSSystemIni, take from DNSFullVersion
        for 9 in Documents and Settings
        for 8 in Program Folder

        for earlier versions try the registry, the result is uncertain.

        """
        try:
            version = self.DNSVersion
        except AttributeError:
            pass
        else:
            if version:
                return version
        dnsPath = self.getDNSInstallDir()
        if dnsPath == -1:
            print('dnsPath not found, please ensure there is a proper DNSInstallDir')
            return 0
        # pos = dnsPath.rfind("NaturallySpeaking")
        # if pos == -1:
        #     print 'Cannot find "NaturallySpeaking" in dnsPath: "%s"'% dnsPath

        versionString = dnsPath[-2:]

        try:
            i = int(versionString[0])
        except ValueError:
            versionString = versionString[-1:]  # dragon 9
        except IndexError:
            print('versionString: "%s", dnsPath: "%s"'% (versionString, dnsPath))
        try:
            i = int(versionString)
        except ValueError:
            print('Cannot find versionString, dnsPath should end in two digits (or one for versions below 10): %s'% dnsPath)
            print('These digits must match the version number of Dragon!!!')
            return 0
        return i


    def getDNSInstallDir(self, force=None):
        """get the folder where natspeak is installed

        try from the list DNSPaths, look for 20, 19, 18, ...

        force == True: get a new value, for use in the config program

        """
        # caching mechanism:
        if self.DNSInstallDir and force is None:
            return self.DNSInstallDir

        ## get first time value:
        key = 'DNSInstallDir'
        P = self.userregnl.get(key)
        if P:
            if self.checkDNSProgramDir(P):
                return P
            else:
                if not self.skipSpecialWarning:
                    print('-'*60)
                    print('DNSInstallDir is set in natlinkstatus.ini to "%s", ...'% P)
                    print('... this does not match a valid Dragon Program Directory.')
                    print('This directory should hold a Program subdirectory or')
                    print('or the subdirectories "App\\Program"')
                    print('in which the Dragon program is located.')
                    print()
                    print('Please set or clear DNSInstallDir:')
                    print('In Config GUI, with button in the info panel, or')
                    print('Via natlinkconfigfunctions.py with option d')
                    print('-'*60)
                    raise IOError('Invalid value of DNSInstallDir: %s'% P)
                else:
                    print('invalid DNSInstallDir: %s, but proceed...'% P)
                    return ''
                
        ## get the program files (x86) directory via extended Environment variables,
        ## now in the path class. Note %PROGRAMFILES(X86)% does not work, because
        ## only [a-z0-9_] is accepted, case independent.
        pf = path('%PROGRAM_FILESX86%')
        if not pf.isdir():
            raise IOError("no valid folder for program files: %s"% pf)
        for dnsdir in DNSPaths:
            cand = pf/dnsdir
            # print('cand: %s'% cand)
            if cand.isdir():
                programfolder = cand/'Program'
                if programfolder.isdir():
                    # print('succes!: %s'% programfolder)
                    # return a str:
                    return cand.normpath()
        if not self.skipSpecialWarning:
            print('-'*60)
            print('No valid DNSInstallDir is found in the default settings of Natlink')
            print()
            print('Please exit Dragon and set a valid DNSInstallDir:')
            print('In Config GUI, with button in the info panel, or')
            print('Via natlinkconfigfunctions.py with option d')
            print('-'*60)
            raise IOError('No valid DNSInstallDir found in the default settings of Natlink')
        else:
            print('-'*60)
            print('No valid DNSInstallDir is found in the default settings of Natlink.')
            print()
            print('Please specify a valid DNSInstallDir:')
            print('In Config GUI, with button in the info panel, or')
            print('Via natlinkconfigfunctions.py with option d')

    def checkDNSProgramDir(self, checkDir):
        """check if directory is a Dragon directory

        it must be a directory, and have as subdirectories App/Program (reported by Udo) or Program.
        In this subdirectory there should be natspeak.exe
        """
        if not checkDir:
            return
        if not os.path.isdir(checkDir):
            print('checkDNSProgramDir, %s is not a directory'% checkDir)
            return
        programDirs = os.path.join(checkDir, 'Program'), os.path.join(checkDir, 'App', 'Program')
        for programDir in programDirs:
            programDir = os.path.normpath(programDir)
            programFile = os.path.join(programDir, 'natspeak.exe')
            if os.path.isdir(programDir) and os.path.isfile(programFile):
                return True
        print('checkDNSProgramDir, %s is not a valid Dragon Program Directory'%  checkDir)
        return
    #def getPythonFullVersion(self):
    #    """get the version string from sys
    #    """
    #    version2 = sys.version
    #    return version2

    def getPythonVersion(self):
        """get the version of python

        Check if the version is supported on the "lower" side.
        
        length 2, without ".", so "38" etc.
        """
        version = sys.version[:3]
        version = version.replace(".", "")
        if len(version) != 2:
            raise ValueError('getPythonVersion, length of python version should be 2, not: %s ("%s")'% (len(version), version))
        if int(version) < lowestSupportedPythonVersion:
            versionReadable = version[0] + "." + version[1]
            lspv = str(lowestSupportedPythonVersion)
            lspvReadable = lspv[0] + "." + lspv[1]
            raise ValueError('getPythonVersion, current version is: "%s".\nPython versions before "%s" are not any more supported by Natlink.\nIf you want to run NatLink on Python2.7, please use the older version of NatLink at SourceForge (https://sourceforge.net/projects/natlink/)'% (versionReadable, lspvReadable))
        return version

    def getPythonPath(self):
        """return the python path, for checking in config GUI
        """
        return sys.path
    def printPythonPath(self):
        pprint.pprint(self.getPythonPath())


    def getNSSYSTEMIni(self):
        inidir = self.getDNSIniDir()
        if inidir:
            nssystemini = os.path.join(inidir, self.NSSystemIni)
            if os.path.isfile(nssystemini):
                return os.path.normpath(nssystemini)
        print("Cannot find proper NSSystemIni file")
        print('Try to correct your DNS INI files Dir, in natlinkconfigfunctions (option "c") or in natlinkconfig  GUI (info panel)')

    def getNSAPPSIni(self):
        inidir = self.getDNSIniDir()
        if inidir:
            nsappsini = os.path.join(inidir, self.NSAppsIni)
            if os.path.isfile(nsappsini):
                return os.path.normpath(nsappsini)
        print("Cannot find proper NSAppsIni file")
        print('Try to correct your DNS INI files Dir, in natlinkconfigfunctions (option "c") or in natlinkconfig  GUI (info panel)')


    def NatlinkIsEnabled(self, silent=None):
        """check if the INI file settings are correct

    in  nssystem.ini check for:

    [Global Clients]
    .Natlink=Python Macro System

    in nsapps.ini check for
    [.Natlink]
    App Support GUID={dd990001-bb89-11d2-b031-0060088dc929}

    if both settings are set, return 1
    (if nssystem.ini setting is set, you also need the nsapps.ini setting)
    if nssystem.ini setting is NOT set, return 0

    if nsapps.ini is set but nssystem.ini is not, Natlink is NOT enabled, still return 0

    if nssystem.ini is set, but nsapps.ini is NOT, there is an error, return None and a
    warning message, UNLESS silent = 1.
    
    Also check if the registry is set properly...

        """
        try:
            isEnabled = self.cache_NatlinkIsEnabled
        except AttributeError:
            pass
        else:
            return self.cache_NatlinkIsEnabled

        result = self.getRegistryPythonPathNatlink()
        if not result:
            self.cache_NatlinkIsEnabled = False
            return   ## registry setting not of pythonpath to core directory is not OK
        coredir_from_registry, registry_key = result
        
        if self.DNSInstallDir == -1:
            self.cache_NatlinkIsEnabled = False
            return
        if self.DNSIniDir == -1:
            self.cache_NatlinkIsEnabled = False
            return
        if not self.CoreDirectory:
            self.cache_NatlinkIsEnabled = False
            return
        if self.CoreDirectory.lower() != coredir_from_registry.lower():
            self.cache_NatlinkIsEnabled = False
            return
            
        nssystemini = self.getNSSYSTEMIni() or ''
        if not os.path.isfile(nssystemini):
            self.cache_NatlinkIsEnabled = False
            return 0
            # raise IOError("NatlinkIsEnabled, not a valid file: %s"% nssystemini)
        actual1 = win32api.GetProfileVal(self.section1, self.key1, "", nssystemini)


        nsappsini = self.getNSAPPSIni()
        if not os.path.isfile(nsappsini):
            raise IOError("NatlinkIsEnabled, not a valid file: %s"% nsappsini)
        actual2 = win32api.GetProfileVal(self.section2, self.key2, "", nsappsini)
        if self.value1 == actual1:
            if self.value2 == actual2:
                # enabled:
                self.cache_NatlinkIsEnabled = True
                return 1
            else:
                #
                mess = ['Error while checking if Natlink is enabled, unexpected result: ',
                        'nssystem.ini points to NatlinkIsEnabled:',
                        '    section: %s, key: %s, value: %s'% (self.section1, self.key1, actual1),
                        'but nsapps.ini points to Natlink is not enabled:',
                      '    section: %s, key: %s, value: %s'% (self.section2, self.key2, actual2),
                      '    should have value: %s'% self.value2]
                if not silent:
                    self.warning(mess)
                
                self.cache_NatlinkIsEnabled = False
                return None # error!
        elif actual1:
            if not silent:
                self.warning("unexpected value of nssystem.ini value: %s"% actual1)
            # unexpected value, but not enabled:
            self.cache_NatlinkIsEnabled = False
            return 0
        else:
            # GUID in nsapps may be defined, natspeak first checks nssystem.ini
            # so Natlink NOT enabled
            self.cache_NatlinkIsEnabled = False
            return 0
        self.warning("unexpected, natlinkstatus should not come here!")
        self.cache_NatlinkIsEnabled = False
        return None

        

    def warning(self, text):
        "to be overloaded in natlinkconfigfunctions and configurenatlink"
        if text in self.hadWarning:
            pass
        else:
            print('Warning:')
            print(text)
            print()
            self.hadWarning.append(text)

    def VocolaIsEnabled(self):
        """Return True if Vocola is enables
        
        To be so,
        1. the VocolaUserDirectory (where the vocola command files (*.vcl) are located)
        should be defined in the user config file
        2. the VocolaDirectory should be found, and hold '_vocola_main.py'
        
        """
        if not self.NatlinkIsEnabled():
            return
        vocUserDir = self.getVocolaUserDirectory()
        if vocUserDir and path(vocUserDir).isdir():
            vocDir = self.getVocolaDirectory()
            vocGrammarsDir = self.getVocolaGrammarsDirectory()
            if vocDir and path(vocDir).isdir() and vocGrammarsDir and path(vocGrammarsDir).isdir():
                return True

    def UnimacroIsEnabled(self):
        """UnimacroIsEnabled: see if UserDirectory is there and

        _control.py is in this directory
        """
        if not self.NatlinkIsEnabled():
            return
        uuDir = self.getUnimacroUserDirectory()
        if not uuDir:
            return
        uDir = self.getUnimacroDirectory()
        if not uDir:
            # print('no valid UnimacroDirectory, Unimacro is disabled')
            return
        if uDir and path(uDir).isdir():
            files = os.listdir(uDir)
            if not '_control.py' in files:
                return   # _control.py should be in Unimacro directory
        ugDir = self.getUnimacroGrammarsDirectory()
        if ugDir and path(ugDir).isdir():
            return True  # Unimacro is enabled...            
                

    def UserIsEnabled(self):
        if not self.NatlinkIsEnabled():
            return
        userDir = self.getUserDirectory()
        if userDir:
            return 1

    def getUnimacroUserDirectory(self):
        if self.UnimacroUserDirectory != None: return self.UnimacroUserDirectory
        key = 'UnimacroUserDirectory'
        value = self.userregnl.get(key)
        if value:
            Path = isValidPath(value, wantDirectory=1)
            if Path:
                try: del self.UnimacroUserDirectory
                except AttributeError: pass

                self.UnimacroUserDirectory = Path
                return Path
            else:
                print('invalid path for %s: "%s"'% (key, value))

        try: del self.UnimacroUserDirectory
        except AttributeError: pass
        self.UnimacroUserDirectory = ''
        return ''

    def getUnimacroDirectory(self):
        """return the path to the Unimacro Directory
        
        This is the directory where the _control.py grammar is.

        When git cloned, relative to the Core directory, otherwise somewhere or in the site-packages (if pipped).
        
        This directory needs to be included in the load directories list of James' natlinkmain
        (August 2020)

        note that if using unimacro from a git clone area Unimacro will be in a /src subdirectory.
        when installed as  a package, that will not be the case.

        """
        if not self.UnimacroDirectory is None: return self.UnimacroDirectory
        uDir = path(self.NatlinkDirectory)/".."/"Unimacro/src/unimacro"
        if not uDir.isdir():
            print(f'not in git clone area, UnimacroDirectory (NatlinkDirectory is in {self.NatlinkDirectory}).')
            uDir = ""
        if uDir:
            controlGrammar = uDir/"_control.py"
            if controlGrammar.isfile():
                try: del self.UnimacroDirectory
                except AttributeError: pass
                self.UnimacroDirectory = uDir.normpath()
                self.addToPath(self.UnimacroDirectory)
                return self.UnimacroDirectory
        ## not found:
        try: del self.UnimacroDirectory
        except AttributeError: pass
        self.UnimacroDirectory = ""
        return ""
        
    def getUnimacroGrammarsDirectory(self):
        """return the path to the directory where the ActiveGrammars of Unimacro are located.
        
        Expected in "ActiveGrammars" of the UnimacroUserDirectory
        (August 2020)

        """
        if not self.UnimacroGrammarsDirectory is None: return self.UnimacroGrammarsDirectory
        
        uuDir = self.getUnimacroUserDirectory()
        if uuDir and path(uuDir).isdir():
            uuDir = path(uuDir)
            ugDir = uuDir/"ActiveGrammars"
            if not ugDir.exists():
                ugDir.mkdir()
            if ugDir.exists() and ugDir.isdir():
                ugFiles = [f for f in ugDir.listdir() if f.endswith(".py")]
                if not ugFiles:
                    print(f"UnimacroGrammarsDirectory: {ugDir} has no python grammar files (yet), please populate this directory with the Unimacro grammars you wish to use, and then toggle your microphone")
                
                try: del self.UnimacroGrammarsDirectory
                except AttributeError: pass
                self.UnimacroGrammarsDirectory= ugDir.normpath()
                return self.UnimacroGrammarsDirectory

        try: del self.UnimacroGrammarsDirectory
        except AttributeError: pass
        self.UnimacroGrammarsDirectory= ""   # meaning is not set, for future calls.
        return self.UnimacroGrammarsDirectory

    def getBaseDirectory(self):
        """return the path of the baseDirectory, MacroSystem
        """
        return self.BaseDirectory

    def getCoreDirectory(self):
        """return the path of the coreDirectory, MacroSystem/core
        """
        return self.CoreDirectory

    def getNatlinkDirectory(self):
        """return the path of the NatlinkDirectory, two above the coreDirectory
        """
        return self.NatlinkDirectory

    def getUserDirectory(self):
        """return the path to the Natlink User directory

        this one is not any more for Unimacro, but for User specified grammars, also Dragonfly

        should be set in configurenatlink, otherwise ignore...
        """
        if not self.NatlinkIsEnabled:
            return
        if not self.UserDirectory is None: return self.UserDirectory
        key = 'UserDirectory'
        value = self.userregnl.get(key)
        if value:
            Path = isValidPath(value, wantDirectory=1)
            if Path:
                self.UserDirectory = Path
                return Path
            else:
                print('invalid path for UserDirectory: "%s"'% value)
        self.UserDirectory = ''
        return ''

    def getVocolaUserDirectory(self):
        if not self.VocolaUserDirectory is None: return self.VocolaUserDirectory
        key = 'VocolaUserDirectory'

        value = self.userregnl.get(key)
        if value:
            Path = isValidPath(value, wantDirectory=1)
            if Path:
                self.VocolaUserDirectory = Path
                return Path
            else:
                print('invalid path for VocolaUserDirectory: "%s"'% value)
        self.VocolaUserDirectory = ''
        return ''

    def getVocolaDirectory(self):
        if not self.VocolaDirectory is None: return self.VocolaDirectory
        vDir1 = path(self.NatlinkDirectory)/".."/"Vocola/src/vocola2"
        vDir2 = path(self.NatlinkDirectory)/".."/"Vocola2/src/vocola2"
        if vDir1.isdir():
            vDir = vDir1
        elif vDir2.isdir():
            vDir = vDir2
        else:
            print(f'not in git clone area, VocolaDirectory (called "Vocola" or "Vocola2" (NatlinkDirectory is in {self.NatlinkDirectory}).')
            vDir = ""
        if vDir:
            controlGrammar = vDir/"_vocola_main.py"
            if controlGrammar.isfile():
                self.VocolaDirectory = vDir.normpath()
                self.addToPath(self.VocolaDirectory)
                return self.VocolaDirectory

        ## search the path for pipped packages: (not tested yet)
        for D in sys.path:
            Dir = path(D)
            controlGrammar = Dir/"_vocola_main.py"
            if controlGrammar.isfile():
                self.VocolaDirectory = Dir.normpath()
                self.addToPath(self.VocolaDirectory)
                return self.VocolaDirectory
        ## not found:
        self.VocolaDirectory = ""
        return ""

    def getVocolaGrammarsDirectory(self):
        """return the VocolaGrammarsDirectory, but only if Vocola is enabled
        
        If so, the subdirectory CompiledGrammars is created if not there yet.
        
        The path of this "CompiledGrammars" directory is returned.
        
        If Vocola is not enabled, or anything goes wrong, return ""
        
        """
        if not self.VocolaGrammarsDirectory is None: return self.VocolaGrammarsDirectory
        vUserDir = self.getVocolaUserDirectory()
        if not vUserDir:
            self.VocolaGrammarsDirectory = ''
            return ''
        vgDir = path(vUserDir)/"CompiledGrammars"
        if not vgDir.exists():
            vgDir.mkdir()
        if vgDir.exists() and vgDir.isdir():
            self.VocolaGrammarsDirectory= vgDir.normpath()
            return self.VocolaGrammarsDirectory
        ## not found:
        self.VocolaGrammarsDirectory = ""
        return ""

    def getAhkUserDir(self):
        if not self.AhkUserDir is None: return self.AhkUserDir
        return self.getAhkUserDirFromIni()

    def getAhkUserDirFromIni(self):
        key = 'AhkUserDir'

        value = self.userregnl.get(key)
        if value:
            Path = isValidPath(value, wantDirectory=1)
            if Path:
                self.AhkUserDir = Path
                return Path
            else:
                print('invalid path for AhkUserDir: "%s"'% value)
        self.AhkUserDir = ''
        return ''

    def getAhkExeDir(self):
        if not self.AhkExeDir is None: return self.AhkExeDir
        return self.getAhkExeDirFromIni()

    def getAhkExeDirFromIni(self):
        key = 'AhkExeDir'
        value = self.userregnl.get(key)
        if value:
            Path = isValidPath(value, wantDirectory=1)
            if Path:
                self.AhkExeDir = Path
                return Path
            else:
                print('invalid path for AhkExeDir: "%s"'% value)
        self.AhkExeDir = ''
        return ''


    def getUnimacroIniFilesEditor(self):
        key = 'UnimacroIniFilesEditor'
        value = self.userregnl.get(key)
        if not value:
            value = 'notepad'
        if self.UnimacroIsEnabled():
            return value
        else:
            return ''

    def _getLastUsedAcoustics(self, DNSuserDirectory):
        """get name of last used acoustics, must have DNSuserDirectory passed

        used by getLanguage, getBaseModel and getBaseTopic
        """
        if not (DNSuserDirectory and os.path.isdir(DNSuserDirectory)):
            print('probably no speech profile on')
            return ''
        #dir = r'D:\projects'  # for testing (at bottom of file)
        optionsini = os.path.join(DNSuserDirectory, 'options.ini')
        if not os.path.isfile(optionsini):
            raise ValueError('not a valid options inifile found: |%s|, check your configuration'% optionsini)

        section = "Options"
        inisection = natlinkcorefunctions.InifileSection(section=section,
                                                         filename=optionsini)
        keyname = "Last Used Acoustics"
        keyToModel = inisection.get(keyname)
        if not keyToModel:
            raise ValueError('no keyToModel value in options inifile found: (key: |%s|), check your configurationfile %s'%
                             (keyToModel, optionsini))
        return keyToModel

    def _getLastUsedTopic(self, DNSuserDirectory):
        """get name of last used topic,

        used by getBaseTopic
        """
        # Dir = self.getDNSuserDirectory()
        # #dir = r'D:\projects'  # for testing (at bottom of file)
        if not os.path.isdir(DNSuserDirectory):
            print("_getLastUsedTopic, no DNSuserDirectory, probably no speech profile on")
            return ""
        optionsini = os.path.join(DNSuserDirectory, 'options.ini')
        if not os.path.isfile(optionsini):
            raise ValueError('not a valid options inifile found: |%s|, check your configuration'% optionsini)

        section = "Options"
        inisection = natlinkcorefunctions.InifileSection(section=section,
                                                         filename=optionsini)
        keyname = "Last Used Topic"
        keyToModel = inisection.get(keyname)
        if not keyToModel:
            raise ValueError('no keyToModel value in options inifile found: (key: |%s|), check your configurationfile %s'%
                             (keyToModel, optionsini))
        return keyToModel


    # def getBaseModelBaseTopic(self, userTopic=None):
    #     """extract BaseModel and BaseTopic of current user
    #
    #     for historical reasons here,
    #     better use getBaseModel and getBaseTopic separate...
    #     """
    #     return self.getBaseModel(), self.getBaseTopic(userTopic=userTopic)

    def getBaseModel(self):
        """getting the base model, '' if error occurs
        getting obsolete in DPI15
        """
        Dir = self.getDNSuserDirectory()
        #dir = r'D:\projects'   # for testing, see bottom of file
        keyToModel = self._getLastUsedAcoustics(Dir)
        acousticini = os.path.join(Dir, 'acoustic.ini')
        section = "Base Acoustic"
        basesection = natlinkcorefunctions.InifileSection(section=section,
                                                         filename=acousticini)
        BaseModel = basesection.get(keyToModel, "")
        # print 'getBaseModel: %s'% BaseModel
        return BaseModel

    def getBaseTopic(self):
        """getting the base topic, '' if error occurs

        with DPI15, the userTopic is given by getCurrentUser, so better use that one
        """
        Dir = self.getDNSuserDirectory()
        #dir = r'D:\projects'   # for testing, see bottom of file
        keyToModel = self._getLastUsedTopic(Dir)
        if not keyToModel:
            # print('Warning, no valid key to topic found')
            return ''
        topicsini = os.path.join(Dir, 'topics.ini')
        section = "Base Topic"
        topicsection = natlinkcorefunctions.InifileSection(section=section,
                                                         filename=topicsini)
        BaseTopic = topicsection.get(keyToModel, "")
        # print 'getBaseTopic: %s'% BaseTopic
        return BaseTopic

    def getUserTopic(self):
        """return the userTopic.

        from DPI15 returned by changeCallback user, before identical to BaseTopic
        """
        try:
            return self.userArgsDict['userTopic']
        except KeyError:
            return self.getBaseTopic()

    def getLanguage(self):
        """get language from userArgsDict

        '' if not set, probably no speech profile on then

        """
        if self.userArgsDict:
            try:
                lang = self.userArgsDict['language']
                return self.userArgsDict['language']
            except KeyError:
                print('Serious error, natlinkstatus.getLanguage: no language found in userArgsDict return ""')
                return ''
        else:
            print('natlinkstatus.getLanguage: no speech profile loaded, no userArgsDict available, used for testing only, return language "tst"')
            return 'tst'

    def getUserLanguage(self):
        """get userLanguage from userArgsDict

        '' if not set, probably no speech profile on then
        """
        try:
            return self.userArgsDict['userLanguage']
        except KeyError:
            return ''

    def getUserLanguageFromInifile(self):
        """get language, userLanguage info from acoustics ini file
        """
        Dir = self.getDNSuserDirectory()

        if not (Dir and os.path.isdir(Dir)):
            return ''
        keyToModel = self._getLastUsedAcoustics(Dir)
        acousticini = os.path.join(Dir, 'acoustic.ini')
        section = "Base Acoustic"
        if not os.path.isfile(acousticini):
            print('getLanguage: Warning, language of the user cannot be found, acoustic.ini not a file in directory %s'% dir)
            return 'yyy'
        inisection = natlinkcorefunctions.InifileSection(section=section,
                                                         filename=acousticini)
        # print 'get data from section %s, key: %s, file: %s'% (section, keyToModel, acousticini)
        # print 'keys of inisection: %s'% inisection.keys()
        # print 'inisection:\n%s\n========'% repr(inisection)

        lang = inisection.get(keyToModel)
        if not lang:
            print('getLanguage: Warning, no model specification string for key %s found in "Base Acoustic" of inifile: %s'% (keyToModel, acousticini))
            print('You probably got the wrong encoding of the file, probably utf-8-BOM.')
            print('Please try to change the encoding to utf-8.')
            return 'zzz'
        lang =  lang.split("|")[0].strip()
        lang = lang.split("(")[0].strip()
        if not lang:
            print('getLanguage: Warning, no valid specification of language string (key: %s) found in "Base Acoustic" of inifile: %s'% (lang, acousticini))
            return 'www'
        return lang

    def getShiftKey(self):
        """return the shiftkey, for setting in natlinkmain when user language changes.

        used for self.playString in natlinkutils, for the dropping character bug. (dec 2015, QH).
        """
        language = self.getLanguage()
        try:
            return "{%s}"% shiftKeyDict[language]
        except KeyError:
            print('no shiftKey code provided for language: %s, take empty string.'% language)
            return ""

    # get different debug options for natlinkmain:
    def getDebugLoad(self):
        """gets value for extra info at loading time of natlinkmain"""
        key = 'NatlinkmainDebugLoad'
        value = self.userregnl.get(key, None)
        return value
    def getDebugCallback(self):
        """gets value for extra info at callback time of natlinkmain"""
        key = 'NatlinkmainDebugCallback'
        value = self.userregnl.get(key, None)
        return value

    # def getNatlinkDebug(self):
    #     """gets value for debug output in DNS logfile"""
    # obsolete (for a long time, 2015 and earlier)
    #     key = 'NatlinkDebug'
    #     value = self.userregnl.get(key, None)
    #     return value

    # def getIncludeUnimacroInPythonPath(self):
    #     """gets the value of alway include Unimacro directory in PythonPath"""
    #
    #     key = 'IncludeUnimacroInPythonPath'
    #     value = self.userregnl.get(key, None)
    #     return value

    # get additional options Vocola
    def getVocolaTakesLanguages(self):
        """gets and value for distinction of different languages in Vocola
        If Vocola is not enabled, this option will also return False
        """
        key = 'VocolaTakesLanguages'
        if self.VocolaIsEnabled():
            value = self.userregnl.get(key, None)
            return value

    def getVocolaTakesUnimacroActions(self):
        """gets and value for optional Vocola takes Unimacro actions
        If Vocola is not enabled, this option will also return False
        """
        key = 'VocolaTakesUnimacroActions'
        if self.VocolaIsEnabled():
            value = self.userregnl.get(key, None)
            return value

    def getInstallVersion(self):
        return __version__

    def getNatlinkPydRegistered(self):
        value = self.userregnl.get('NatlinkDllRegistered', None)
        return value
  
    def getDNSName(self):
        """return NatSpeak for versions <= 11, and Dragon for versions >= 12
        """
        if self.getDNSVersion() <= 11:
            return 'NatSpeak'
        else:
            return "Dragon"

    def getNatlinkStatusDict(self):
        """return actual status in a dict"""
        D = {}
        for key in ['userName', 'DNSuserDirectory', 'DNSInstallDir',
                    'DNSIniDir', 'WindowsVersion', 'DNSVersion',
                    'PythonVersion',
                    'DNSName',
                    'UnimacroDirectory', 'UnimacroUserDirectory', 'UnimacroGrammarsDirectory',
                    'DebugLoad', 'DebugCallback',
                    'VocolaDirectory', 'VocolaUserDirectory', 'VocolaGrammarsDirectory',
                    'VocolaTakesLanguages', 'VocolaTakesUnimacroActions',
                    'UnimacroIniFilesEditor',
                    'InstallVersion', 'NatlinkPydRegistered',
                    # 'IncludeUnimacroInPythonPath',
                    'AhkExeDir', 'AhkUserDir']:
##                    'BaseTopic', 'BaseModel']:
            keyCap = key[0].upper() + key[1:]
            execstring = "D['%s'] = self.get%s()"% (key, keyCap)
            exec(execstring)
        D['CoreDirectory'] = self.CoreDirectory
        D['BaseDirectory'] = self.BaseDirectory
        D['UserDirectory'] = self.getUserDirectory()
        D['natlinkIsEnabled'] = self.NatlinkIsEnabled()
        D['vocolaIsEnabled'] = self.VocolaIsEnabled()

        D['unimacroIsEnabled'] = self.UnimacroIsEnabled()
        D['userIsEnabled'] = self.UserIsEnabled()
        # extra for information purposes:
        D['NatlinkDirectory'] = self.NatlinkDirectory
        return D

    def getNatlinkStatusString(self):
        L = []
        D = self.getNatlinkStatusDict()
        if D['userName']:
            L.append('user speech profile:')
            self.appendAndRemove(L, D, 'userName')
            self.appendAndRemove(L, D, 'DNSuserDirectory')
        else:
            del D['userName']
            del D['DNSuserDirectory']
        # Natlink::

        if D['natlinkIsEnabled']:
            self.appendAndRemove(L, D, 'natlinkIsEnabled', "---Natlink is enabled")
            key = 'CoreDirectory'
            self.appendAndRemove(L, D, key)
            key = 'InstallVersion'
            self.appendAndRemove(L, D, key)

            ## Vocola::
            if D['vocolaIsEnabled']:
                self.appendAndRemove(L, D, 'vocolaIsEnabled', "---Vocola is enabled")
                for key in ('BaseDirectory', 'VocolaUserDirectory', 'VocolaDirectory',
                            'VocolaGrammarsDirectory', 'VocolaTakesLanguages',
                            'VocolaTakesUnimacroActions'):
                    self.appendAndRemove(L, D, key)
            else:
                self.appendAndRemove(L, D, 'vocolaIsEnabled', "---Vocola is disabled")
                for key in ('VocolaUserDirectory', 'VocolaDirectory',
                            'VocolaGrammarsDirectory', 'VocolaTakesLanguages',
                            'VocolaTakesUnimacroActions'):
                    del D[key]

            ## Unimacro:
            if D['unimacroIsEnabled']:
                self.appendAndRemove(L, D, 'unimacroIsEnabled', "---Unimacro is enabled")
                for key in ('UnimacroUserDirectory', 'UnimacroDirectory', 'UnimacroGrammarsDirectory'):
                    self.appendAndRemove(L, D, key)
                for key in ('UnimacroIniFilesEditor',):
                    self.appendAndRemove(L, D, key)
            else:
                self.appendAndRemove(L, D, 'unimacroIsEnabled', "---Unimacro is disabled")
                for key in ('UnimacroUserDirectory', 'UnimacroIniFilesEditor',
                            'UnimacroDirectory', 'UnimacroGrammarsDirectory'):
                    del D[key]
            ##  UserDirectory:
            if D['userIsEnabled']:
                self.appendAndRemove(L, D, 'userIsEnabled', "---User defined grammars are enabled")
                for key in ('UserDirectory',):
                    self.appendAndRemove(L, D, key)
            else:
                self.appendAndRemove(L, D, 'userIsEnabled', "---User defined grammars are disabled")
                del D['UserDirectory']

            ## remaining Natlink options:
            L.append('other Natlink info:')
            for key in ('DebugLoad', 'DebugCallback'):
                self.appendAndRemove(L, D, key)

        else:
            # Natlink disabled:
            if D['natlinkIsEnabled'] == 0:
                self.appendAndRemove(L, D, 'natlinkIsEnabled', "---Natlink is disabled")
            else:
                self.appendAndRemove(L, D, 'natlinkIsEnabled', "---Natlink is disabled (strange value: %s)"% D['natlinkIsEnabled'])
            key = 'CoreDirectory'
            self.appendAndRemove(L, D, key)
            for key in ['DebugLoad', 'DebugCallback',
                    'VocolaTakesLanguages',
                    'vocolaIsEnabled']:
                del D[key]
        # system:
        L.append('system information:')
        for key in ['DNSInstallDir',
                    'DNSIniDir', 'DNSVersion', 'DNSName',
                    'WindowsVersion', 'PythonVersion']:
            self.appendAndRemove(L, D, key)

        # forgotten???
        if D:
            L.append('remaining information:')
            for key in list(D.keys()):
                self.appendAndRemove(L, D, key)

        return '\n'.join(L)


    def appendAndRemove(self, List, Dict, Key, text=None):
        if text:
            List.append(text)
        else:
            value = Dict[Key]
            if value == None or value == '':
                value = '-'
            List.append("\t%s\t%s"% (Key,value))
        del Dict[Key]
        
    def addToPath(self, directory):
        """add to the python path if not there yet
        """
        Dir2 = path(directory)
        if not Dir2.isdir():
            print(f"natlinkstatus, addToPath, not an existing directory: {directory}")
            return
        Dir3 = Dir2.normpath()
        if Dir3 not in sys.path:
            print(f"natlinkstatus, addToPath: {Dir3}")
            sys.path.append(Dir3)

def getFileDate(modName):
    try: return os.stat(modName)[stat.ST_MTIME]
    except OSError: return 0        # file not found

# for splitting the env variables:
reEnv = re.compile('(%[A-Z_]+%)', re.I)

    #
    # # initialize recentEnv in natlinkcorefunctions (new 2018, 4.1uniform)
    # this is done from natlinkmain in changeCallback user:
    # natlinkstatus.AddExtendedEnvVariables()
    # natlinkstatus.AddNatLinkEnvironmentVariables(status=status)



def AddExtendedEnvVariables():
    """call to natlinkcorefunctions, called from natlinkmain at startup or user callback
    """
    natlinkcorefunctions.clearRecentEnv() # make a fresh start!
    natlinkcorefunctions.getAllFolderEnvironmentVariables(fillRecentEnv=1)


def AddNatlinkEnvironmentVariables(status=None):
    """make the special Natlink variables global in this module
    """
    if status is None:
        status = NatlinkStatus()
    D = status.getNatlinkStatusDict()
    natlinkVarsDict = {}
    for k, v in list(D.items()):
        if type(v) in (str, bytes) and os.path.isdir(v):
            k = k.upper()
            v = os.path.normpath(v)
            natlinkVarsDict[k] = v
            natlinkcorefunctions.addToRecentEnv(k, v)
    return natlinkVarsDict
    # print 'added to ExtendedEnvVariables:\n'
    # print '\n'.join(addedList)

def isValidPath(spec, wantFile=None, wantDirectory=None):
    """check existence of spec, allow for pseudosymbols.

    Return the normpath (expanded) if exists and optionally is a file or a directory

    ~ and %...% should be evaluated

    tested in testConfigfunctions.py
    """
    if not spec:
        return

    if os.path.exists(spec):
        spec2 = spec
    else:
        spec2 = natlinkcorefunctions.getExtendedEnv(spec)
    spec2 = os.path.normpath(spec2)
    if os.path.exists(spec2):
        if wantDirectory and wantFile:
            raise ValueError("isValidPath, only wantFile or wantDirectory may be specified, not both!")
        if wantFile:
            if  os.path.isfile(spec2):
                return spec2
            else:
                print('isValidPath, path exists, but is not a file: "%s"'% spec2)
                return
        if wantDirectory:
            if os.path.isdir(spec2):
                return spec2
            else:
                print('isValidPath, path exists, but is not a directory: "%s"'% spec2)
                return
        return spec2


if __name__ == "__main__":

    status = NatlinkStatus()
    status.checkSysPath()

    print(status.getNatlinkStatusString())
    lang = status.getLanguage()
    print('language: %s'% lang)

    # exapmles, for more tests in ...
    print('\n====\nexamples of expanding ~ and %...% variables:')
    short = path("~/Quintijn")
    AddExtendedEnvVariables()
    addedListNatlinkVariables = AddNatlinkEnvironmentVariables()


    print('All "NATLINK" extended variables:')
    print('\n'.join(addedListNatlinkVariables))

    # voccompDir = natlinkcorefunctions.expandEnvVariableAtStart('%UNIMACRODIRECTORY%/vocola_compatibility')
    # print('%%UNIMACRODIRECTORY%%/vocola_compatibility is expanded to: %s'% voccompDir)
    # print('Is valid directory: %s'% os.path.isdir(voccompDir))
    print('\nExample: the pyd directory:')
    pydDir = natlinkcorefunctions.expandEnvVariableAtStart('%COREDIRECTORY%/pyd')
    print('%%COREDIRECTORY%%/pyd is expanded to: %s'% pydDir)
    print('Pyd directory is a valid directory: %s'% os.path.isdir(pydDir))

    # next things only testable when changing the dir in the functions above
    # and copying the ini files to this dir...
    # they normally run only when natspeak is on (and from NatSpeak)
    #print 'language (test): |%s|'% lang
    #print status.getBaseModelBaseTopic()
    print(status.getBaseModel())
    print(status.getBaseTopic())
    pass