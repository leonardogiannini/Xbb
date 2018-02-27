import ROOT
import os
import subprocess

ROOT.gROOT.SetBatch(True)

ROOT.gSystem.Load("../../interface/VHbbNameSpace_h.so")

path_prefix = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/WlvSync'

RegionList = ['TT', 'WLF', 'WHF']
#RegionList = ['WHF']
SampleList = ['TT','Wp','WJets']
#total
#VarList = ['PU','genSign','bTag','dEtabb', 'NLOVpt', 'NLOewk','Wpt','eSelSF','uSelSF','eTrigSF','uTrigSF']
#VarList = ['PU','genSign','bTag','FitCorr', 'Vweight','LepSelSF','eTrigSF','uTrigSF']
#VarList = ['PU']
VarList = ['genSign','PU','bTag','EWKsig','EWKWjets','dEtabb','lepSF']

#AT
#SamplePath_Xbb = {'TT':'Xbb_samples/TTbar.root','Wp':'Xbb_samples/Wplus_ext.root','WJets':'Xbb_samples/WBJets.root'}
SamplePath_Xbb = {'TT':'Xbb_samples/TTbar_3.root','Wp':'Xbb_samples/Wplus_ext.root','WJets':'Xbb_samples/WBJets.root'}

#SampleVar_Xbb = {'PU':['puWeight', 50, 0, 2], 'genSign':['sign(genWeight)', 50, 0, 2],'bTag':['bTagWeightCMVAV2_Moriond', 50, 0, 2],'FitCorr':['FitCorr[0]', 50, 0, 2],'Vweight':['DYw[0]', 50, 0, 2],'LepSelSF':['weight_SF_Lepton[0]', 50, 0, 2],'eTrigSF':['eTrigSFWeight_singleEle80[0]', 50, 0, 2],'uTrigSF':['muTrigSFWeight_singlemu[0]', 50, 0, 2]}
SampleVar_Xbb = {'PU':['puWeight', 50, 0.5, 1.5], 'genSign':['sign(genWeight)', 50, 0.5, 1.5],'bTag':['bTagWeightCMVAV2_Moriond', 50, 0.5, 1.5],'FitCorr':['FitCorr[0]', 50, 0.5, 1.5],'Vweight':['DYw[0]', 50, 0.5, 1.5],'lepSF':['weight_SF_Lepton[0]*muTrigSFWeight_singlemu[0]*eTrigSFWeight_singleEle80[0]', 50, 0.5, 1.5],'EWKsig':['EWKw', 50, 0.5, 1.5],'EWKWjets':['EWKw', 50, 0.5, 1.5], 'dEtabb':['NLOw', 50, 0.5, 1.5]}

RegionCut_Xbb = {
    'TT':' Jet_pt_reg[hJCMVAV2idx[0]] > 25 & Jet_pt_reg[hJCMVAV2idx[1]] > 25 & HCMVAV2_reg_pt > 100 & V_pt > 100 & Sum$(aLeptons_pt > 15 && aLeptons_eta < 2.5 && aLeptons_relIso03< 0.1)== 0  & VHbb::deltaPhi(met_phi,vLeptons_phi[0]) < 2  & HCMVAV2_reg_mass < 250 & (vLeptons_relIso04[0] < 0.06 & Vtype == 2 || vLeptons_relIso03[0] < 0.06 & Vtype  == 3) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Sum$(Jet_pt>25 && abs(Jet_eta)<2.9 && Jet_puId>0 && Jet_pt != Jet_pt[hJCMVAV2idx[0]] && Jet_pt != Jet_pt[hJCMVAV2idx[1]]) > 1 & (Vtype == 2 || Vtype == 3 & (abs(vLeptons_eta[0]) >= 1.57 || abs(vLeptons_eta[0]) <= 1.44))  & Vtype == 2 & met_pt < 170',
    'WLF':'Jet_pt_reg[hJCMVAV2idx[0]] > 25 & Jet_pt_reg[hJCMVAV2idx[1]] > 25 & HCMVAV2_reg_pt > 100 & V_pt > 100 & Sum$(aLeptons_pt > 15 && aLeptons_eta < 2.5 && aLeptons_relIso03< 0.1) == 0  & VHbb::deltaPhi(met_phi,vLeptons_phi[0]) < 2  & HCMVAV2_reg_mass < 250 & (vLeptons_relIso04[0] < 0.06 & Vtype == 2 || vLeptons_relIso03[0] < 0.06 & Vtype  == 3) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > -0.5884 & Jet_btagCMVAV2[hJCMVAV2idx[0]] < 0.4432 & met_sig > 2.0 & (Vtype == 2 || Vtype == 3 & (abs(vLeptons_eta[0]) >= 1.57 || abs(vLeptons_eta[0]) <= 1.44)) & Vtype == 2 & met_pt < 170',
    ##Note: this is the low mass definition (WhflMu)
    #'WHF':'Jet_pt_reg[hJCMVAV2idx[0]] > 25 & Jet_pt_reg[hJCMVAV2idx[1]] > 25 & HCMVAV2_reg_pt > 100 & V_pt > 100 & Sum$(aLeptons_pt > 15 && aLeptons_eta < 2.5 && aLeptons_relIso03< 0.1) == 0  & VHbb::deltaPhi(met_phi,vLeptons_phi[0]) < 2  & HCMVAV2_reg_mass < 250 & (vLeptons_relIso04[0] < 0.06 & Vtype == 2 || vLeptons_relIso03[0] < 0.06 & Vtype  == 3) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Sum$(Jet_pt>25 && abs(Jet_eta)<2.9 && Jet_puId>0 && Jet_pt != Jet_pt[hJCMVAV2idx[0]] && Jet_pt != Jet_pt[hJCMVAV2idx[1]]) == 0 & met_sig > 2.0 & HCMVAV2_reg_mass < 90 & (Vtype == 2 || Vtype == 3 & (abs(vLeptons_eta[0]) >= 1.57 || abs(vLeptons_eta[0]) <= 1.44)) & Vtype == 2',
    'WHF':'Jet_pt_reg[hJCMVAV2idx[0]] > 25 & Jet_pt_reg[hJCMVAV2idx[1]] > 25 & HCMVAV2_reg_pt > 100 & V_pt > 100 & Sum$(aLeptons_pt > 15 && aLeptons_eta < 2.5 && aLeptons_relIso03< 0.1) == 0  & VHbb::deltaPhi(met_phi,vLeptons_phi[0]) < 2  & HCMVAV2_reg_mass < 250 & (vLeptons_relIso04[0] < 0.06 & Vtype == 2 || vLeptons_relIso03[0] < 0.06 & Vtype  == 3) & Jet_btagCMVAV2[hJCMVAV2idx[0]] > 0.9432 & Sum$(Jet_pt>25 && abs(Jet_eta)<2.9 && Jet_puId>0 && Jet_pt != Jet_pt[hJCMVAV2idx[0]] && Jet_pt != Jet_pt[hJCMVAV2idx[1]]) == 0 & met_sig > 2.0 & (HCMVAV2_reg_mass < 90 || HCMVAV2_reg_mass > 150) & (Vtype == 2 || Vtype == 3 & (abs(vLeptons_eta[0]) >= 1.57 || abs(vLeptons_eta[0]) <= 1.44)) & Vtype == 2 & met_pt < 170',
    }


#Analysis Tools
#SamplePath_AT = {'TT':'Nov20_2017_sync/wln_crs_ttpowheg.root','Wp':'Nov20_2017_sync/wln_crs_wplush125powheg.root','WJets':'Nov20_2017_sync/wln_crs_wbjetspt100to200.root'}
#using other Wp B sample (mine was broken)
#SamplePath_AT = {'TT':'Nov20_2017_sync/wln_crs_ttpowheg.root','Wp':'Nov20_2017_sync/wln_crs_wplush125powheg_12_02_18.root','WJets':'Nov20_2017_sync/wln_crs_wbjetspt100to200.root'}
SamplePath_AT = {'TT':'Nov20_2017_sync/wln_crs_ttpowheg.root','Wp':'Nov20_2017_sync/WplusH125_v3.root','WJets':'Nov20_2017_sync/wln_crs_wbjetspt100to200.root'}
#SampleVar_AT = {'PU':['puWeight', 50, 0, 2], 'genSign':['sign(genWeight)', 50, 0, 2],'bTag':['bTagWeightCMVAV2_Moriond', 50, 0, 2],'FitCorr':['FitCorr[0]', 50, 0, 2],'Vweight':['DYw[0]', 50, 0, 2],'LepSelSF':['weight_SF_Lepton[0]', 50, 0, 2],'eTrigSF':['eTrigSFWeight_singleEle80[0]', 50, 0, 2],'uTrigSF':['muTrigSFWeight_singlemu[0]', 50, 0, 2]}
SampleVar_AT = {'PU':['weight_PU', 50, 0.5, 1.5], 'genSign':['sign(genWeight)', 50, 0.5, 1.5],'bTag':['bTagWeightMoriondCMVA', 50, 0.5, 1.5],'FitCorr':['FitCorr[0]', 50, 0.5, 1.5],'Vweight':['DYw[0]', 50, 0.5, 1.5],'lepSF':['Lep_SF', 50, 0.5, 1.5],'EWKsig':['VHCorrFactor', 50, 0.5, 1.5],'EWKWjets':['weight_ptEWK', 50, 0.5, 1.5], 'dEtabb':['WJetNLOWeight*weight_ptQCD', 50, 0.5, 1.5]}
RegionCut_AT = {
    'TT':'selLeptons_relIso_0<0.06&&met_pt<170&&isWmunu&&Vtype==2&&controlSample==1',
    'WLF':'selLeptons_relIso_0<0.06&&met_pt<170&&isWmunu&&Vtype==2&&controlSample==3',
    'WHF':'selLeptons_relIso_0<0.06&&met_pt<170&&(H_mass<90||H_mass>150)&&isWmunu&&Vtype==2&&controlSample==2&&nAddJets252p9_puid<1'
    }

nevents = 'Region\tSample\tXbb\tAT\n\n'

#To check variables in common subregion

for region in RegionList:

    nevents += region + '\t\n'

    print '========='
    print region
    print '========='
    for sample in SampleList:

        nevents += '\t'+sample+'\t'

        #Create the dir to store the plots
        output_path = region
        if not os.path.exists('plots/'+region):
            os.makedirs('plots/'+region)
            subprocess.call('cp -r .htaccess ' + 'plots/'+region + '/', shell = True)
            subprocess.call('cp -r index.php ' + 'plots/'+region + '/', shell = True)

        #Xbb
        file_Xbb = ROOT.TFile.Open(SamplePath_Xbb[sample],'read')
        tree_Xbb = file_Xbb.Get('tree')
        print tree_Xbb.GetName()
        #AT
        file_AT = ROOT.TFile.Open(SamplePath_AT[sample],'read')
        tree_AT = file_AT.Get('tree')
        print tree_AT.GetName()

        #Count the number of entries
        n_Xbb =  tree_Xbb.GetEntries(RegionCut_Xbb[region])
        n_AT = tree_AT.GetEntries(RegionCut_AT[region])

        print '\n'
        print sample
        print 'Xbb yield:', n_Xbb
        print 'AT  yield:', n_AT
        print '\n'


        #Make plots for all the relevant variables
        for var in VarList:


            h_Xbb = ROOT.TH1F('h_Xbb','h_Xbb',SampleVar_Xbb[var][1], SampleVar_Xbb[var][2], SampleVar_Xbb[var][3])
            tree_Xbb.Draw('%s>>%s' %(SampleVar_Xbb[var][0], 'h_Xbb'), RegionCut_Xbb[region])

            h_AT = ROOT.TH1F('h_AT','h_AT',SampleVar_AT[var][1], SampleVar_AT[var][2], SampleVar_AT[var][3])
            tree_AT.Draw('%s>>%s' %(SampleVar_AT[var][0], 'h_AT'), RegionCut_AT[region])

            c = ROOT.TCanvas('c','c')
            c.cd()

            h_Xbb.Draw()
            h_Xbb.SetLineColor(2)
            h_Xbb.SetLineWidth(4)
            if not h_Xbb.Integral() == 0:
                h_Xbb.Scale(1./h_Xbb.Integral())
            h_AT.Draw('SAME')
            h_AT.SetLineColor(4)
            h_AT.SetLineStyle(2)
            h_AT.SetLineWidth(4)
            if not h_AT.Integral() == 0:
                h_AT.Scale(1./h_AT.Integral())

            leg = ROOT.TLegend(0.1,0.7,0.3,0.9)
            leg.AddEntry(h_Xbb, 'Xbb')
            leg.AddEntry(h_AT, 'AT')
            leg.Draw()

            c.SaveAs('plots/%s_%s_%s.pdf'%(region, sample,var))
            #c.SaveAs('plots/%s_%s_%s.png'%(region, sample,var))
            #c.SaveAs('plots/%s_%s_%s.root'%(region,sample,var))

        nevents += str(n_Xbb) + '\t'
        nevents += str(n_AT)+ '\t\n'

f = open('yields.txt', 'w')
f.write(nevents)
f.close
