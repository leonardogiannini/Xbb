import ROOT
import os
import sys
import subprocess
from copy import copy
import json

ROOT.gROOT.SetBatch(True)

ROOT.gSystem.Load("../../interface/VHbbNameSpace_h.so")

path_prefix = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/WlvSync'


###########
##General info (sample, region, variables)
###########

#All
RegionList = ['TTel','ZLFel','ZHFel','TTul','ZLFul','ZHFul','TTeh','ZLFeh','ZHFeh','TTuh','ZLFuh','ZHFuh']
SampleList = ['TT','ZHbb','DY400']
VarList = ['Vtype',
    'lepPt',
    'HTpt',
    'CMVAmin',
    'Vmass',
    'CMVAmax',
    'Vpt',
    'HVdPhi',
    'lepRelIso1',
    'jetleadpt',
    'jetsubleadpt',
    'PU',
    'MET',
    'count',
    'Hmass',
    'lepRelIso2'
]

###Test
#RegionList = ['TTel']
#SampleList = ['TT']
#VarList = ['HTpt','Hmass']
#VarList = ['count']

###############
#Xbb dictionnaries
###############

SamplePath_Xbb = {'TT':'Xbb/Sample/TT.root','ZHbb':'Xbb/Sample/ZHbb.root','DY400':'Xbb/Sample/DYH400.root'}
#Variable definitions
SampleVar_Xbb = {'Vtype':'Vtype_new','lepPt':'vLeptons_new_pt[0]','HTpt':'HCMVAV2_reg_pt','CMVAmin':'Jet_btagCMVAV2[hJCMVAV2idx[1]]','Vmass':'V_mass','CMVAmax':'Jet_btagCMVAV2[hJCMVAV2idx[0]]','Vpt':'V_pt','HVdPhi':'VHbb::deltaPhi(HCMVAV2_phi,V_phi)','lepRelIso1':'vLeptons_new_relIso04[0]','jetleadpt':'Jet_pt[hJCMVAV2idx[0]]','jetsubleadpt':'Jet_pt[hJCMVAV2idx[1]]','PU':'puWeight','MET':'met_pt','count':'1','Hmass':'HCMVAV2_reg_mass','lepRelIso2':'vLeptons_new_relIso04[0]','nAddJets':'Sum$(Jet_pt>30 && abs(Jet_eta)<5.2 && Jet_puId>=4)'}
#Kinematic region definitions
RegionCut_Xbb = {
    'TTel':'(V_new_mass > 10 & (V_new_mass < 75 || V_new_mass > 120) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Jet_btagCMVAV2[hJCMVAV2idx[1]] > -0.5884  & (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20))) & (Vtype_new == 1 && (abs(vLeptons_new_eta[0]) >= 1.57 || abs(vLeptons_new_eta[0]) <= 1.44) & (abs(vLeptons_new_eta[1])>=1.57 || abs(vLeptons_new_eta[1])<=1.44) && vLeptons_new_relIso03[0] < 0.15 && vLeptons_new_relIso03[1] < 0.15) & (V_new_pt > 50 & V_new_pt < 150)',
    'ZLFel':'((V_new_mass > 75. && V_new_mass < 105. && Jet_btagCMVAV2[hJCMVAV2idx[0]] < -0.5884 && Jet_btagCMVAV2[hJCMVAV2idx[1]] < -0.5884 && abs(VHbb::deltaPhi(HCMVAV2_reg_phi,V_new_phi)) > 2.5  & (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20))) && V_new_pt > 50) && (HCMVAV2_reg_mass > 90 && HCMVAV2_reg_mass < 150) & (Vtype_new == 1 && (abs(vLeptons_new_eta[0]) >= 1.57 || abs(vLeptons_new_eta[0]) <= 1.44) & (abs(vLeptons_new_eta[1])>=1.57 || abs(vLeptons_new_eta[1])<=1.44) && vLeptons_new_relIso03[0] < 0.15 && vLeptons_new_relIso03[1] < 0.15) & (V_new_pt > 50 & V_new_pt < 150)',
    'ZHFel':'(abs(VHbb::deltaPhi(HCMVAV2_reg_phi,V_new_phi)) > 2.5  & V_new_mass > 85. & V_new_mass < 97. & met_pt < 60 & (HCMVAV2_reg_mass < 90 || HCMVAV2_reg_mass > 150) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Jet_btagCMVAV2[hJCMVAV2idx[1]] > -0.5884 &  (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20)) & V_new_pt > 50) & (Vtype_new == 1 && (abs(vLeptons_new_eta[0]) >= 1.57 || abs(vLeptons_new_eta[0]) <= 1.44) & (abs(vLeptons_new_eta[1])>=1.57 || abs(vLeptons_new_eta[1])<=1.44) && vLeptons_new_relIso03[0] < 0.15 && vLeptons_new_relIso03[1] < 0.15) & (V_new_pt > 50 & V_new_pt < 150)',
    'ZHFeh':'(abs(VHbb::deltaPhi(HCMVAV2_reg_phi,V_new_phi)) > 2.5  & V_new_mass > 85. & V_new_mass < 97. & met_pt < 60 & (HCMVAV2_reg_mass < 90 || HCMVAV2_reg_mass > 150) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Jet_btagCMVAV2[hJCMVAV2idx[1]] > -0.5884 &  (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20)) & V_new_pt > 50) & (Vtype_new == 1 && (abs(vLeptons_new_eta[0]) >= 1.57 || abs(vLeptons_new_eta[0]) <= 1.44) & (abs(vLeptons_new_eta[1])>=1.57 || abs(vLeptons_new_eta[1])<=1.44) && vLeptons_new_relIso03[0] < 0.15 && vLeptons_new_relIso03[1] < 0.15) & (V_new_pt > 150)',
    'TTul':'(V_new_mass > 10 & (V_new_mass < 75 || V_new_mass > 120) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Jet_btagCMVAV2[hJCMVAV2idx[1]] > -0.5884  & (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20))) & (Vtype_new == 0) & (V_new_pt > 50 & V_new_pt < 150)',
    'ZLFul':'((V_new_mass > 75. && V_new_mass < 105. && Jet_btagCMVAV2[hJCMVAV2idx[0]] < -0.5884 && Jet_btagCMVAV2[hJCMVAV2idx[1]] < -0.5884 && abs(VHbb::deltaPhi(HCMVAV2_reg_phi,V_new_phi)) > 2.5  & (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20))) && V_new_pt > 50) && (HCMVAV2_reg_mass > 90 && HCMVAV2_reg_mass < 150) & (Vtype_new == 0) & (V_new_pt > 50 & V_new_pt < 150)',
    'ZHFul':'(abs(VHbb::deltaPhi(HCMVAV2_reg_phi,V_new_phi)) > 2.5  & V_new_mass > 85. & V_new_mass < 97. & met_pt < 60 & (HCMVAV2_reg_mass < 90 || HCMVAV2_reg_mass > 150) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Jet_btagCMVAV2[hJCMVAV2idx[1]] > -0.5884 &  (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20)) & V_new_pt > 50) & (Vtype_new == 0) & (V_new_pt > 50 & V_new_pt < 150)',
    'TTeh':'(V_new_mass > 10 & (V_new_mass < 75 || V_new_mass > 120) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Jet_btagCMVAV2[hJCMVAV2idx[1]] > -0.5884  & (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20))) & (Vtype_new == 1 && (abs(vLeptons_new_eta[0]) >= 1.57 || abs(vLeptons_new_eta[0]) <= 1.44) & (abs(vLeptons_new_eta[1])>=1.57 || abs(vLeptons_new_eta[1])<=1.44) && vLeptons_new_relIso03[0] < 0.15 && vLeptons_new_relIso03[1] < 0.15) & (V_new_pt > 150)',
    'ZLFeh':'((V_new_mass > 75. && V_new_mass < 105. && Jet_btagCMVAV2[hJCMVAV2idx[0]] < -0.5884 && Jet_btagCMVAV2[hJCMVAV2idx[1]] < -0.5884 && abs(VHbb::deltaPhi(HCMVAV2_reg_phi,V_new_phi)) > 2.5  & (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20))) && V_new_pt > 50) && (HCMVAV2_reg_mass > 90 && HCMVAV2_reg_mass < 150) & (Vtype_new == 1 && (abs(vLeptons_new_eta[0]) >= 1.57 || abs(vLeptons_new_eta[0]) <= 1.44) & (abs(vLeptons_new_eta[1])>=1.57 || abs(vLeptons_new_eta[1])<=1.44) && vLeptons_new_relIso03[0] < 0.15 && vLeptons_new_relIso03[1] < 0.15) & (V_new_pt > 150)',
    'TTuh':' (V_new_mass > 10 & (V_new_mass < 75 || V_new_mass > 120) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Jet_btagCMVAV2[hJCMVAV2idx[1]] > -0.5884  & (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20))) & (Vtype_new == 0) & (V_new_pt > 150)',
    'ZLFuh':'((V_new_mass > 75. && V_new_mass < 105. && Jet_btagCMVAV2[hJCMVAV2idx[0]] < -0.5884 && Jet_btagCMVAV2[hJCMVAV2idx[1]] < -0.5884 && abs(VHbb::deltaPhi(HCMVAV2_reg_phi,V_new_phi)) > 2.5  & (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20))) && V_new_pt > 50) && (HCMVAV2_reg_mass > 90 && HCMVAV2_reg_mass < 150) & (Vtype_new == 0) & (V_new_pt > 150)',
    'ZHFuh':'(abs(VHbb::deltaPhi(HCMVAV2_reg_phi,V_new_phi)) > 2.5  & V_new_mass > 85. & V_new_mass < 97. & met_pt < 60 & (HCMVAV2_reg_mass < 90 || HCMVAV2_reg_mass > 150) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Jet_btagCMVAV2[hJCMVAV2idx[1]] > -0.5884 &  (BasicCutsCMVA && ( hJetCMVAV2_pt_reg_0 > 20 &&  hJetCMVAV2_pt_reg_1 > 20) && (vLeptons_new_pt[0]>20 && vLeptons_new_pt[1]>20)) & V_new_pt > 50) & (Vtype_new == 0) & (V_new_pt > 150)'
    }

###############
#AT dictionnaries
###############

#SamplePath_AT= {'TT':'AT/Heiner_mail_18_01_2018/CR_2LeptREGION/TT_powheg.root','ZHbb':'AT/Heiner_mail_18_01_2018/CR_2LeptREGION/ZH125_powheg.root','DY400':'AT/Heiner_mail_18_01_2018/CR_2LeptREGION/DYToLL_HT400to600.root'}
#SamplePath_AT= {'TT':'AT/Heiner_07_02_18/CR_2LeptREGION/TT_powheg.root','ZHbb':'AT/Heiner_07_02_18/CR_2LeptREGION/ZH125_powheg.root','DY400':'AT/Heiner_07_02_18/CR_2LeptREGION/DYToLL_HT400to600.root'}
SamplePath_AT= {'TT':'AT/Heiner_mail_11_02_18/CR_2LeptREGION/TT_powheg.root','ZHbb':'AT/Heiner_mail_11_02_18/CR_2LeptREGION/ZH125_powheg.root','DY400':'AT/Heiner_mail_11_02_18/CR_2LeptREGION/DYToLL_HT400to600.root'}
#
SampleVar_AT = {'Vtype':'Vtype','lepPt':'lepPt','HTpt':'Hpt','CMVAmin':'CMVAmin','Vmass':'Vmass','CMVAmax':'CMVAmax','Vpt':'Vpt','cutFlow':'cutFlow','HVdPhi':'HVdPhi','lepRelIso1':'lepRelIso1','nAddLeptons':'nAddLeptons','lepMetDPhi':'lepMetDPhi','sigma_met_pt':'sigma_met_pt','jetleadpt':'jetleadpt','jetsubleadpt':'jetsubleadpt','':'controlSample','PU':'puWeight','MET':'met_pt','MetTkMetDPhi':'MetTkMetDPhi','count':'count','BDT':'BDT','Hmass':'Hmass','lepRelIso2':'lepRelIso2','nAddJets':'nAddJets','minMetjDPhi':'minMetjDPhi'}

#Analysis Tools
#Histograms location in files from Heiner
DirName = {'TTel':'CR_2Lepton_lowVpt_TTbar_El',
    'ZLFel':'CR_2Lepton_lowVpt_VpLF_El',
    'ZHFel':'CR_2Lepton_lowVpt_VpHF_El',
    'TTul':'CR_2Lepton_lowVpt_TTbar_Mu',
    'ZLFul':'CR_2Lepton_lowVpt_VpLF_Mu',
    'ZHFul':'CR_2Lepton_lowVpt_VpHF_Mu',
    'TTeh':'CR_2Lepton_highVpt_TTbar_El',
    'ZLFeh':'CR_2Lepton_highVpt_VpLF_El',
    'ZHFeh':'CR_2Lepton_highVpt_VpHF_El',
    'TTuh':'CR_2Lepton_highVpt_TTbar_Mu',
    'ZLFuh':'CR_2Lepton_highVpt_VpLF_Mu',
    'ZHFuh':'CR_2Lepton_highVpt_VpHF_Mu'
    }

############
#Read all the AT histograms
############


def GetHisto(inputfile, region):
    '''Get all the histograms from a given region and inputfile'''
    histoList = {}
    file = ROOT.TFile.Open(inputfile,'read')
    nextkey = ROOT.TIter(ROOT.gDirectory.GetListOfKeys())
    key = nextkey.Next()
    #Loop over the region
    while (key):
        kname = key.GetName()
        if kname == DirName[region]:
            ROOT.gDirectory.cd(kname)
            #Loop over all the histograms
            nexth = ROOT.TIter(ROOT.gDirectory.GetListOfKeys())
            h = nexth.Next()
            #Loop over the variables
            while (h):
                hname = h.GetName()
                hobj = copy(ROOT.gDirectory.Get(hname))
                histoList[hname] = hobj
                h = nexth.Next()
            break
        key = nextkey.Next()
    return histoList

def MakeSampleDic(region, sampleList):
    '''For a given region, returns a dic like {'sample1':[variable1, variable2,...], 'sample2', [variable1, variable2,...]}'''
    SampleDic = {}

    #Check first if this is a low or high region
    LO = (region[-1] == 'l')
    Vpt = ''
    if LO: Vpt = 'LO'
    else: Vpt = 'HI'
    for s in sampleList:
        inputfile = SamplePath_AT[s].replace('REGION',Vpt)
        SampleDic[s] = GetHisto(inputfile, region)
    return SampleDic

def MakeRegionDic(regionList, sampleList):
    '''For a given region, returns a dic like {'region':'{'sample1':[variable1, variable2,...], 'sample2', [variable1, variable2,...]}'}'''
    RegionDic = {}
    for r in regionList:
        RegionDic[r] = MakeSampleDic(r, sampleList)
    return RegionDic

def GetEventList(tree, cut):
    '''Used in Xbb tree only. Make JSON containing list of events for one given tree and region'''
    eventList = []
    cutFormula = ROOT.TTreeFormula("cutFormula", cut, tree)
    for event in tree:
        n = cutFormula.GetNdata()
        s = cutFormula.EvalInstance()
        if s:
            eventList.append(event.evt)
    return eventList



##For test
hlist = GetHisto('AT/Heiner_mail_18_01_2018/CR_2LeptLO/DYToLL_HT400to600.root', 'ZLFel')
#print 'hlist is', hlist
#sys.exit()
#slist = MakeSampleDic('ZLFel', SampleList)
#print 'slist is', slist
#rlist = MakeRegionDic(RegionList, SampleList)
#print 'rlist is', rlist

#Create dic organising all the histograms from AT
AT_AllHist = MakeRegionDic(RegionList, SampleList)

nevents = 'Region\tSample\tXbb\tAT\n\n'

if not os.path.exists('plots'):
    os.makedirs('plots')
    subprocess.call('cp -r .htaccess ' + 'plots/', shell = True)
    subprocess.call('cp -r index.php ' + 'plots/', shell = True)

#To make the json
data = {}

#To check variables in common subregion
for region in RegionList:

    nevents += region + '\t\n'

    print '========='
    print region
    print '========='
    #
    #Create folder for each region if doesn't exist
    #
    output_path = region
    if not os.path.exists('plots/'+region):
        os.makedirs('plots/'+region)
        subprocess.call('cp -r .htaccess ' + 'plots/'+region + '/', shell = True)
        subprocess.call('cp -r index.php ' + 'plots/'+region + '/', shell = True)

    #To make the Json

    #To write the yield information

    for sample in SampleList:

        nevents += '\t'+sample+'\t'
        Xbbcount = -1
        ATcount = -1

        #Xbb
        file_Xbb = ROOT.TFile.Open(SamplePath_Xbb[sample],'read')
        tree_Xbb = file_Xbb.Get('tree')
        print tree_Xbb.GetName()

        #To creat JSON
        if not ('sample:%s'%sample) in data:
            data['sample:%s'%sample] = {}
        if not ('region:%s'%region) in data['sample:%s'%sample]:
            data['sample:%s'%sample]['region:%s'%region] = {}
        #print RegionCut_Xbb[region]
        #data['sample:%s'%sample]['region:%s'%region] = GetEventList(tree_Xbb, RegionCut_Xbb[region])
        data['sample:%s'%sample]['region:%s'%region] = 1
        ##AT

        ##Count the number of entries
        #n_Xbb =  tree_Xbb.GetEntries(RegionCut_Xbb[region])

        #Make plots for all the relevant variables
        for var in VarList:

            #print '-------------------'
            #print AT_AllHist[region][sample]
            #sys.exit()
            h_AT = AT_AllHist[region][sample][SampleVar_AT[var]]
            nbins= h_AT.GetNbinsX()
            xmin = h_AT.GetXaxis().GetBinLowEdge(1)
            xmax = h_AT.GetXaxis().GetBinLowEdge(nbins+1)

            h_Xbb = ROOT.TH1F('h_Xbb','h_Xbb', nbins, xmin, xmax)
            tree_Xbb.Draw('%s>>%s' %(SampleVar_Xbb[var], 'h_Xbb'), RegionCut_Xbb[region])

            c = ROOT.TCanvas('c','c')
            c.cd()

            h_Xbb.Draw()
            h_Xbb.SetLineColor(2)
            h_Xbb.SetLineWidth(4)

            Xbb_count_ = h_Xbb.Integral()
            if not h_Xbb.Integral() == 0:
                h_Xbb.Scale(1./Xbb_count_)
            h_AT.Draw('SAME')
            h_AT.SetLineColor(4)
            h_AT.SetLineStyle(2)
            h_AT.SetLineWidth(4)

            AT_count_ = h_AT.Integral()
            if not h_AT.Integral() == 0:
                h_AT.Scale(1./AT_count_)

            leg = ROOT.TLegend(0,0.8,0.15,1)
            leg.AddEntry(h_Xbb, 'Xbb')
            leg.AddEntry(h_AT, 'AT')
            leg.Draw()

            #Max histogram value
            ymax = max(h_Xbb.GetMaximum(),h_AT.GetMaximum())
            h_Xbb.GetYaxis().SetRangeUser(0,ymax*1.2)


            c.SaveAs('plots/%s/%s_%s_%s.pdf'%(output_path,region, sample,var))
            c.SaveAs('plots/%s/%s_%s_%s.png'%(output_path,region, sample,var))
            c.SaveAs('plots/%s/%s_%s_%s.root'%(output_path,region,sample,var))

            if var == 'count':
                Xbbcount = Xbb_count_
                ATcount = AT_count_
        nevents += str(Xbbcount) + '\t'
        nevents += str(ATcount)+ '\t\n'

f = open('plots/yields.txt', 'w')
f.write(nevents)
f.close

with open ('plots/event.json','w') as f:
    json.dump(data, f, sort_keys = False, indent = 4)


