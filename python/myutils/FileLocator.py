from __future__ import print_function
import os
import shutil
import sys
import subprocess
import ROOT
import hashlib

class FileLocator(object):

    def __init__(self, config=None):
        self.config = config
        self.debug = 'XBBDEBUG' in os.environ
        try:
            self.xrootdRedirectors = [x.strip() for x in self.config.get('Configuration', 'xrootdRedirectors').split(',') if len(x.strip())>0]
            if len(self.xrootdRedirectors) < 1:
                print("WARNING: empty list of xrootd redirectors given!")
        except Exception as e:
            if config:
                print (e)
                print("WARNING: no xrootd redirector given!")
            self.xrootdRedirectors = None
        try:
            self.pnfsStoragePath = self.config.get('Configuration', 'pnfsStoragePath').strip()
        except:
            if config:
                print("WARNING: no pnfs storage path given!")
            self.pnfsStoragePath = None

        self.storagePathPrefix = '/store/'
        self.pnfsPrefix = '/pnfs/'
        # TODO: use XrootD python bindings
        self.remoteStatDirectory = 'xrdfs {server} stat -q IsDir {path}'
        self.remoteStatFile = 'xrdfs {server} stat {path}'
        self.remoteMkdir = 'xrdfs {server} mkdir {path}'
        self.remoteRm = 'xrdfs {server} rm {path}'
        self.remoteCp = 'xrdcp -d 1 -f --posc --nopbar {source} {target}'
        self.makedirsMinLevel = 5   # don't even try to create/access the 5 lowest levels in the path

    # special Xbb function: get filename after prep step from original file name
    def getFilenameAfterPrep(self, inputFile):
        subfolder = inputFile.split('/')[-4]
        filename = inputFile.split('/')[-1]
        filename = filename.split('_')[0]+'_'+subfolder+'_'+filename.split('_')[1]
        hash = hashlib.sha224(filename).hexdigest()
        return filename.replace('.root','')+'_'+str(hash)+'.root'

    # check if path is relative to /store/
    def isStoragePath(self, path):
        return path.startswith(self.storagePathPrefix)

    # check if a path is a PNFS directory (with or without redirector)
    def isPnfs(self, path):
        return self.pnfsPrefix in path

    def isRemotePath(self, path):
        return self.isPnfs(path) or '://' in path 

    def isValidRootFile(self, path):
        f = ROOT.TFile.Open(path, 'read')
        if f:
            isValid = not (f.IsZombie() or f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered))
            try:
                f.Close()
            except:
                pass
            return isValid
        else:
            return False

    def runCommand(self, command):
        if self.debug:
            print ("RUN: \x1b[32m",command,"\x1b[0m")
            return subprocess.call([command], shell=True)
        else:
            with open(os.devnull, 'w') as fp:
                result = subprocess.call([command], shell=True, stdout=fp, stderr=fp)
            return result 

    def getRemoteFileserver(self, path=None):
        if path and '://' in path:
            server = path.split('://')[1].split('/')[0].split(':')[0].strip()
        else:
            server = self.xrootdRedirectors[0].split('://')[1].split('/')[0].split(':')[0].strip()
        return server

    def getRedirector(self, path):
        if '://' in path:
            redirector = path.split('://')[0] + '://' + path.split('://')[1].split('/')[0]
        else:
            redirector = None
        return redirector

    def remoteDirectoryExists(self, path):
        statCommand = self.remoteStatDirectory.format(server=self.getRemoteFileserver(path), path=self.getLocalFileName(path))
        result = self.runCommand(statCommand)
        return result==0

    def remoteFileExists(self, path):
        statCommand = self.remoteStatFile.format(server=self.getRemoteFileserver(path), path=self.getLocalFileName(path))
        result = self.runCommand(statCommand)
        return result==0

    def remoteFileRm(self, path):
        command = self.remoteRm.format(server=self.getRemoteFileserver(path), path=self.getLocalFileName(path))
        result = self.runCommand(command)
        return result==0

    def remoteCopy(self, source, target):
        command = self.remoteCp.format(source=source, target=target)
        result = self.runCommand(command)
        return result==0

    def cp(self, source, target):
        if self.isRemotePath(source) or self.isRemotePath(target):
            return self.remoteCopy(source, target)
        else:
            shutil.copyfile(source, target)
            return True

    def rm(self, path):
        if self.isRemotePath(path):
            self.remoteFileRm(path)
        else:
            os.remove(path)

    def exists(self, path):
        if self.isRemotePath(path):
            return self.remoteFileExists(path)
        else:
            return os.path.exists(path)

    def mkdir(self, path):
        status = False
        if not self.isRemotePath(path):
            try:
                os.mkdir(path)
                status = True
            except:
                pass
        else:
            command = self.remoteMkdir.format(server=self.getRemoteFileserver(), path=self.getLocalFileName(path))
            status = self.runCommand(command)
        return status

    # create folder and parent folders 
    def makedirs(self, path):
        status = True
        # use os functionality for local files
        if not self.isRemotePath(path):
            try:
                os.makedirs(path)
            except:
                status = False
        else:
            if not self.remoteDirectoryExists(path):
                localName = self.getLocalFileName(path.strip('/'))
                directories = localName.split('/')
                i = len(directories)
                while i>self.makedirsMinLevel:
                    parentDirectory = self.getRemoteFileName('/'.join(directories[:i-1]))
                    if self.remoteDirectoryExists(parentDirectory):
                        break
                    i -= 1
                for j in range(i, len(directories) + 1):
                    remoteName = self.getRemoteFileName('/'.join(directories[:j]))
                    self.mkdir(remoteName)
        return status

    def fileExists(self, fileName):
        return os.path.isfile(self.getLocalFileName(fileName))

    def directoryExists(self, fileName):
        return os.path.isdir(self.getLocalFileName(fileName))

    def getRemoteFileName(self, path):
        # only xrootd protocol supported at the moment
        return self.getXrootdFileName(path)

    def removeRedirector(self, fileName):
        if '://' in fileName:
            fileName = '/'.join(fileName.split('://')[1].split('/')[1:])
        return fileName

    def addRedirector(self, redirector=None, fileName=None):
        if redirector is None:
            redirector = self.xrootdRedirectors[0]
        if fileName is None:
            fileName = ""
        return redirector + '/' + fileName

    # ------------------------------------------------------------------------------
    # get file name WITH redirector
    # ------------------------------------------------------------------------------
    def getXrootdFileName(self, rawFileName):
        xrootdFileName = rawFileName.strip()
        if self.isStoragePath(xrootdFileName):
            xrootdFileName = self.pnfsStoragePath + xrootdFileName.strip()
        if self.isPnfs(xrootdFileName):
            # replace already existing redirectors with primary one
            if self.xrootdRedirectors:
                xrootdFileName = self.addRedirector(fileName=self.removeRedirector(xrootdFileName), redirector=self.xrootdRedirectors[0])
            return xrootdFileName.strip()
        else:
            return xrootdFileName.strip()

    # ------------------------------------------------------------------------------
    # get file name WITHOUT redirector, but with complete PNFS path in case of a 
    # /store/ path.
    # ------------------------------------------------------------------------------
    def getLocalFileName(self, rawFileName):
        if rawFileName:
            localFileName = self.removeRedirector(rawFileName.strip())
            if localFileName.startswith('/store/') and self.pnfsStoragePath:
                localFileName = self.pnfsStoragePath + localFileName.strip()
            return localFileName
        else:
            print ("\x1b[31mERROR: invalid file name\x1b[0m")
            raise Exception("InvalidFileName")

