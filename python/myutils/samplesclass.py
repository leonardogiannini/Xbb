class Sample:
    def __init__(self,name,type):
        self.name=name
        self.type=type
        self.identifier=''
        self.prefix=''
        self.active=True
        self.group=''
        self.lumi=0.
        self.sf=1.
        self.xsec=0.
        self.weightexpression=1.0
        self.specialweight=""
        self.tree='tree'
        self.treecut=''
        self.count=1.
        self.mergeCachingSize=100
        self.skipParts=[],
        # self.count_with_PU=1.
        # self.count_with_PU2011B=1.
        self.subsample=False
        self.subcut='1'

    @property
    def get_path(self):
        return './%s%s.root' %(self.prefix,self.identifier)

    def __str__(self):
        return '%s' %self.name
    
    def __eq__(self,other):
        return self.name == other.name

    def printInfo(self):
        print "-sample-info--------"
        print "name:", self.name
        print "type:", self.type
        print "identifier:", self.identifier
        print "subsample:", self.subsample
        print "group:", self.group
        print "treecut:", self.treecut
        print "--------------------"

    def isData(self):
        return self.type=='DATA'

    def isMC(self):
        return not self.isData()
