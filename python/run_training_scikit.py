#!/usr/bin/env python
from __future__ import print_function
from optparse import OptionParser
import ROOT
ROOT.gROOT.SetBatch(True)
from myutils import NewTreeCache as TreeCache
from myutils.sampleTree import SampleTree as SampleTree
from myutils import BetterConfigParser, ParseInfo
import resource
import os
import sys
import pickle
import glob
import shutil
import numpy as np
import math
from sklearn import tree
from sklearn.tree import DecisionTreeRegressor
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import GradientBoostingClassifier 
from sklearn.ensemble import RandomForestClassifier 
from sklearn.ensemble import ExtraTreesClassifier 
from sklearn.ensemble import RandomTreesEmbedding
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve
from sklearn.metrics import auc
from sklearn.pipeline import make_pipeline
from sklearn.externals import joblib
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from sklearn.ensemble import BaggingClassifier
from sklearn.utils import resample
from sklearn.neural_network import MLPClassifier
from sklearn import preprocessing
from xgboost import XGBClassifier
import datetime
import hashlib
import random

class MvaTrainingHelper(object):

    def __init__(self, config, mvaName):
        self.dataRepresentationVersion = 2
        self.config = config
        self.samplesPath = config.get('Directories', 'MVAin')
        self.samplesDefinitions = config.get('Directories','samplesinfo')
        self.samplesInfo = ParseInfo(self.samplesDefinitions, self.samplesPath)
        self.sampleFilesFolder = config.get('Directories', 'samplefiles')
        self.logpath = config.get('Directories', 'logpath')
        self.treeVarSet = config.get(mvaName, 'treeVarSet')
        self.mvaName = mvaName
        self.MVAsettings = config.get(mvaName,'MVAsettings')
        self.factoryname = 'scikit-test1'

        VHbbNameSpace = config.get('VHbbNameSpace', 'library')
        ROOT.gSystem.Load(VHbbNameSpace)

        # variables
        self.MVA_Vars = {}
        self.MVA_Vars['Nominal'] = config.get(self.treeVarSet, 'Nominal').strip().split(' ')

        # samples
        self.backgroundSampleNames = eval(config.get(mvaName, 'backgrounds'))
        self.signalSampleNames = eval(config.get(mvaName, 'signals'))
        self.samples = {
            'BKG': self.samplesInfo.get_samples(self.backgroundSampleNames),
            'SIG': self.samplesInfo.get_samples(self.signalSampleNames),
        }

        # MVA signal region cuts
        self.treeCutName = config.get(mvaName, 'treeCut')
        self.treeCut = config.get('Cuts', self.treeCutName)

        # split in train/test samples
        self.datasets = ['train', 'test']
        self.varsets = ['X', 'y', 'sample_weight']
        self.trainCut = config.get('Cuts', 'TrainCut') 
        self.evalCut = config.get('Cuts', 'EvalCut')

        print("TRAINING CUT:", self.trainCut)
        print("TEST CUT:", self.evalCut)

        self.globalRescale = 2.0
        
        # default parameters
        self.parameters = {
                'factoryname': self.factoryname,
                'mvaName': self.mvaName,
                'MVAregionCut': self.treeCutName + ': ' + self.treeCut,
                #'classifier': 'GradientBoostingClassifier',
                'classifier': 'RandomForestClassifier',
                #'classifier': 'ExtraTreesClassifier',
                #'classifier': 'FT_GradientBoostingClassifier',
                'max_depth': None,
                'max_leaf_nodes': None,
                'class_weight': 'balanced',
                #'criterion': 'friedman_mse',
                'criterion': 'gini',
                #'n_estimators': 3000,
                'n_estimators': 400,
                #'learning_rate': 0.1,
                'algorithm': 'SAMME.R',
                #'min_samples_leaf': 100,
                'splitter': 'best',
                'max_features': 4,
                'subsample': 0.6,
                'limit': -1,
                'additional_signal_weight': 1.0,
                'min_impurity_split': 0.0,
                'bootstrap': True,
                }

        # load parameters from config in a format similar to Root TMVA parameter string
        self.MVAsettingsEvaluated = []
        for mvaSetting in self.MVAsettings.split(':'):
             self.parameters[mvaSetting.split('=')[0].strip()] = eval(mvaSetting.split('=')[1].strip())
             try:
                 self.MVAsettingsEvaluated.append('%s'%mvaSetting.split('=')[0].strip() + '=' + '%r'%self.parameters[mvaSetting.split('=')[0].strip()])
             except:
                 print("???:", mvaSetting)
                 self.MVAsettingsEvaluated.append(mvaSetting)

        self.MVAsettingsEvaluated = ':'.join(self.MVAsettingsEvaluated)

    # load numpy arrays with training/testing data
    def loadCachedNumpyArrays(self, cachedFilesPath):
        cached = True
        try:
            with open(cachedFilesPath + '/scikit_input.dmp', 'rb') as inputFile:
                self.data = pickle.load(inputFile)
            print("INFO: found numpy arrays for input in:", cachedFilesPath)
        except:
            cached = False
        return cached

    # save numpy arrays with training/testing data
    def writeNumpyArrays(self, cachedFilesPath):
        with open(cachedFilesPath + '/scikit_input.dmp', 'wb') as outputFile:
            pickle.dump(self.data, outputFile)
        print("INFO: wrote numpy arrays for input to:", cachedFilesPath)

    def getCachedNumpyArrayPath(self):
        identifier = self.treeCut + '__VAR:' + ' '.join(self.MVA_Vars['Nominal']) + '__SIG:' + '/'.join(self.signalSampleNames) + '__BKG:' + '/'.join(self.backgroundSampleNames) + '__V:%r'%self.dataRepresentationVersion
        varsHash = hashlib.sha224(identifier).hexdigest()
        cachedFilesPath = self.logpath + '/../cache/' + varsHash + '/'
        return cachedFilesPath

    def getHash(self):
        identifier = self.treeCut + '__VAR:' + ' '.join(self.MVA_Vars['Nominal']) + '__SIG:' + '/'.join(self.signalSampleNames) + '__BKG:' + '/'.join(self.backgroundSampleNames) + '__PAR:%r'%self.parameters
        return hashlib.sha224(identifier).hexdigest()[:8]

    def prepare(self):
        # ----------------------------------------------------------------------------------------------------------------------
        # add sig/bkg x training/testing trees
        # ----------------------------------------------------------------------------------------------------------------------
        self.sampleTrees = []
        categories = ['BKG', 'SIG']
        datasetParts = {'train': self.trainCut, 'test': self.evalCut}

        cachedFilesPath = self.getCachedNumpyArrayPath() 
        try:
            os.makedirs(cachedFilesPath)
        except:
            pass
        
        # load numpy arrays from disk if they have been already created
        if self.loadCachedNumpyArrays(cachedFilesPath):
            return self

        arrayLists = {datasetName:[] for datasetName in datasetParts.iterkeys()}
        weightLists = {datasetName:[] for datasetName in datasetParts.iterkeys()}
        targetLists = {datasetName:[] for datasetName in datasetParts.iterkeys()}
        
        # standard weight expression
        weightF = self.config.get('Weights','weightF')

        for category in categories:
            for sample in self.samples[category]:
                print ('*'*80,'\n%s\n'%sample,'*'*80)
                for datasetName, additionalCut in datasetParts.iteritems():
                    # cuts
                    sampleCuts = [sample.subcut]
                    if additionalCut:
                        sampleCuts.append(additionalCut)
                    # cut from the mva region
                    if self.treeCut:
                        sampleCuts.append(self.treeCut)

                    # get ROOT tree for selected sample & region cut
                    tc = TreeCache.TreeCache(
                            sample=sample,
                            cutList=sampleCuts,
                            inputFolder=self.samplesPath,
                            config=self.config,
                            debug=True
                        )
                    sampleTree = tc.getTree()
                    if sampleTree:
                        treeScale = sampleTree.getScale(sample) * self.globalRescale
                        print ('scale:', treeScale)
                        
                        # initialize numpy array
                        nSamples = sampleTree.GetEntries()
                        features = self.MVA_Vars['Nominal']
                        nFeatures = len(features) 
                        print('nFeatures:', nFeatures)
                        inputData = np.zeros((nSamples, nFeatures), dtype=np.float32)

                        # initialize formulas for ROOT tree
                        for feature in features:
                            sampleTree.addFormula(feature)
                        sampleTree.addFormula(weightF)
                        
                        # fill numpy array from ROOT tree
                        for i, event in enumerate(sampleTree):
                            for j, feature in enumerate(features):
                                inputData[i, j] = sampleTree.evaluate(feature)
                            # total weight comes from weightF (btag, lepton sf, ...) and treeScale to scale MC to x-section
                            totalWeight = treeScale * sampleTree.evaluate(weightF)
                            weightLists[datasetName].append(totalWeight)
                            targetLists[datasetName].append(categories.index(category))

                        arrayLists[datasetName].append(inputData)

                    else:
                        print ("\x1b[31mERROR: TREE NOT FOUND:", sample.name, " -> not cached??\x1b[0m")
                        raise Exception("CachedTreeMissing")

        # concatenate all data from different samples
        self.data = {
                'train': {
                    'X': np.concatenate(arrayLists['train'], axis=0),
                    'y': np.array(targetLists['train'], dtype=np.float32),
                    'sample_weight': np.array(weightLists['train'], dtype=np.float32),
                    },
                'test': {
                    'X': np.concatenate(arrayLists['test'], axis=0),
                    'y': np.array(targetLists['test'], dtype=np.float32),
                    'sample_weight': np.array(weightLists['test'], dtype=np.float32),
                    },
                }

        # write numpy arrays to disk
        self.writeNumpyArrays(cachedFilesPath)

        return self

    def verify_data(self):
        valid = True
        for dataset in self.datasets:
            for var in self.varsets:
                print("DEBUG: self.data['{dataset}']['{var}'].shape = {shape}".format(dataset=dataset, var=var, shape=self.data[dataset][var].shape))

        for dataset in self.datasets:
            for i in range(len(self.varsets)-1):
                valid = valid and self.data[dataset][self.varsets[i]].shape[0] == self.data[dataset][self.varsets[i+1]].shape[0]
        return valid

    def run(self):

        if not self.verify_data():
            print ("\x1b[31mERROR: training input data array shapes are incompatible!\x1b[0m")
            raise Exception("BadTrainingInputData")

        applyClassWeights = False
        if self.parameters['classifier'] == 'GradientBoostingClassifier':
            clf = GradientBoostingClassifier(
                    min_samples_leaf=self.parameters['min_samples_leaf'], 
                    max_depth=self.parameters['max_depth'], 
                    max_leaf_nodes=self.parameters['max_leaf_nodes'],
                    criterion=self.parameters['criterion'],
                    max_features=self.parameters['max_features'],
                    n_estimators=self.parameters['n_estimators'], 
                    learning_rate=self.parameters['learning_rate'], 
                    subsample=self.parameters['subsample'],
                    min_impurity_split=self.parameters['min_impurity_split'],
                )
            if self.parameters['class_weight'] == 'balanced':
                applyClassWeights = True
        elif self.parameters['classifier'] == 'RandomForestClassifier':
            clf = RandomForestClassifier(
                    min_samples_leaf=self.parameters['min_samples_leaf'], 
                    max_depth=self.parameters['max_depth'], 
                    max_leaf_nodes=self.parameters['max_leaf_nodes'],
                    criterion=self.parameters['criterion'],
                    max_features=self.parameters['max_features'],
                    n_estimators=self.parameters['n_estimators'], 
                    bootstrap=self.parameters['bootstrap'],
                )
            if self.parameters['class_weight'] == 'balanced':
                applyClassWeights = True
        elif self.parameters['classifier'] == 'ExtraTreesClassifier':
            clf = ExtraTreesClassifier(
                    min_samples_leaf=self.parameters['min_samples_leaf'], 
                    max_depth=self.parameters['max_depth'], 
                    max_leaf_nodes=self.parameters['max_leaf_nodes'],
                    criterion=self.parameters['criterion'],
                    max_features=self.parameters['max_features'],
                    n_estimators=self.parameters['n_estimators'], 
                    bootstrap=self.parameters['bootstrap'],
                )
            if self.parameters['class_weight'] == 'balanced':
                applyClassWeights = True
        elif self.parameters['classifier'] == 'FT_GradientBoostingClassifier':
            rt = RandomTreesEmbedding(max_depth=3, n_estimators=20, random_state=0)
            clf0 = GradientBoostingClassifier(
                    min_samples_leaf=self.parameters['min_samples_leaf'], 
                    max_depth=self.parameters['max_depth'], 
                    max_leaf_nodes=self.parameters['max_leaf_nodes'],
                    criterion=self.parameters['criterion'],
                    max_features=self.parameters['max_features'],
                    n_estimators=self.parameters['n_estimators'], 
                    learning_rate=self.parameters['learning_rate'], 
                    subsample=self.parameters['subsample'],
                    min_impurity_split=self.parameters['min_impurity_split'],
                )
            if self.parameters['class_weight'] == 'balanced':
                applyClassWeights = True
            clf = make_pipeline(rt, clf0)
        elif self.parameters['classifier'] == 'XGBClassifier':
            clf = XGBClassifier(
                    learning_rate=self.parameters['learning_rate'],
                    max_depth=self.parameters['max_depth'],
                    n_estimators=self.parameters['n_estimators'],
                    objective='binary:logitraw',
                    colsample_bytree=self.parameters['colsample_bytree'],
                    subsample=self.parameters['subsample'],
                    min_child_weight=self.parameters['min_child_weight'],
                    gamma=self.parameters['gamma'] if 'gamma' in self.parameters else 0.0,
                    #reg_alpha=8,
                    reg_lambda=self.parameters['reg_lambda'] if 'reg_lambda' in self.parameters else 1.0,
                    reg_alpha=self.parameters['reg_alpha'] if 'reg_alpha' in self.parameters else 0.0,
                    ) 
            if self.parameters['class_weight'] == 'balanced':
                applyClassWeights = True
        elif self.parameters['classifier'] == 'MLPClassifier':
            classifierParams = {k:v for k,v in self.parameters.iteritems() if k in ['solver', 'alpha', 'hidden_layer_sizes', 'max_iter', 'warm_start', 'learning_rate_init', 'learning_rate', 'momentum', 'epsilon', 'beta_1', 'beta_2', 'validation_fraction', 'early_stopping']}
            clf = MLPClassifier(**classifierParams) 
        elif self.parameters['classifier'] in ['SVC', 'LinearSVC']:
            '''
            clf = SVC(
                        C=1.0,
                        cache_size=4000,
                        class_weight='balanced',
                        coef0=0.0,
                        decision_function_shape='ovr',
                        degree=3,
                        gamma='auto',
                        kernel='rbf',
                        max_iter=100000,
                        probability=False,
                        random_state=None,
                        shrinking=True,
                        tol=0.001,
                        verbose=True
                    )
            '''
            bagged = int(self.parameters['bagged']) if 'bagged' in self.parameters else False
            if self.parameters['classifier'] == 'LinearSVC':
                clf = LinearSVC(
                            class_weight='balanced',
                            dual=self.parameters['dual'],
                            max_iter=self.parameters['max_iter'],
                            C=self.parameters['C'],
                            penalty=self.parameters['penalty'],
                            loss=self.parameters['loss'],
                            tol=self.parameters['tol'],
                            verbose=True,
                        )
            else:
                # classifier='SVC':C=random.choice([1.0, 10.0, 100.0, 500.0, 1000.0]):kernel=random.choice(['rbf','poly','linear']):degree=random.choice([2,3,4]):gamma=random.choice(['auto', 0.1, 0.3, 0.6]):shrinking=random.choice([True, False]):max_iter=10000:penalty=random.choice(['l1','l2']):tol=random.choice([0.005, 0.001, 0.0005, 0.0001]):cache_size=1000
                clf =  SVC(
                        C=self.parameters['C'],
                        cache_size=self.parameters['cache_size'],
                        class_weight='balanced',
                        coef0=0.0,
                        decision_function_shape='ovr',
                        degree=self.parameters['degree'],
                        gamma=self.parameters['gamma'],
                        kernel=self.parameters['kernel'],
                        max_iter=self.parameters['max_iter'],
                        probability=False,
                        random_state=None,
                        shrinking=self.parameters['shrinking'],
                        tol=self.parameters['tol'],
                        verbose=True
                    )

            if bagged:
                n_estimators = bagged
                if 'bag_oversampling' in self.parameters:
                    n_estimators = int(n_estimators * self.parameters['bag_oversampling'])

                clf0 = clf
                clf = BaggingClassifier(
                        clf0,
                        max_samples=1.0 / bagged,
                        max_features=self.parameters['baggedfeatures'] if 'baggedfeatures' in self.parameters else 1.0,
                        bootstrap_features=self.parameters['bootstrapfeatures'] if 'bootstrapfeatures' in self.parameters else False,
                        n_estimators=n_estimators,
                    )

        else:
            clf = AdaBoostClassifier(
                    DecisionTreeClassifier(
                        min_samples_leaf=self.parameters['min_samples_leaf'], 
                        max_depth=self.parameters['max_depth'], 
                        class_weight=self.parameters['class_weight'], 
                        criterion=self.parameters['criterion'],
                        splitter=self.parameters['splitter'],
                        max_features=self.parameters['max_features'],
                        ), 
                    n_estimators=self.parameters['n_estimators'], 
                    learning_rate=self.parameters['learning_rate'], 
                    algorithm=self.parameters['algorithm'],
                )

        #with open("/mnt/t3nfs01/data01/shome/berger_p2/VHbb/CMSSW_9_4_0_pre3/src/Xbb/python/logs_v25//test-scikit-svm/Logs//../cache/b7d92f50a52f8474e66cf4e2c3ad3fa4725aa489e7a6b288e4ed3855//clf2018-01-31_18-22-38_be9479a2.pkl","rb") as inputFile:
        #    clf = pickle.load(inputFile)

        # preprocessing
        print("transformation...")

        if 'scaler' in self.parameters:
            if self.parameters['scaler'] == 'standard':
                self.scaler = preprocessing.StandardScaler().fit(self.data['train']['X'])
            elif self.parameters['scaler'] == 'minmax':
                self.scaler = preprocessing.MinMaxScaler().fit(self.data['train']['X'])
            elif self.parameters['scaler'] == 'robust':
                self.scaler = preprocessing.RobustScaler().fit(self.data['train']['X'])
            else:
                self.scaler = None
        else:
            self.scaler = None

        if self.scaler:
            self.data['train']['X'] = self.scaler.transform(self.data['train']['X'])
            self.data['test']['X'] = self.scaler.transform(self.data['test']['X'])

        # SHUFFLE all samples before
        self.shuffle = False
        if self.shuffle:
            print("shuffle input data...")
            for dataset in self.datasets:
                nSamples = self.data[dataset][self.varsets[0]].shape[0]
                randomPermutation = np.random.permutation(nSamples)
                for var in self.varsets:
                    self.data[dataset][var] = np.take(self.data[dataset][var], randomPermutation, axis=0)

        # LIMIT number of training samples
        # recommended to also shuffle samples before, because they are ordered by signal/background
        limitNumTrainingSamples = self.parameters['limit']
        if (limitNumTrainingSamples > 0):
            print("limit training samples to:", limitNumTrainingSamples)
            #for dataset in self.datasets:
            #    for var in self.varsets:
            #        self.data[dataset][var] = self.data[dataset][var][0:limitNumTrainingSamples]
            for dataset in self.datasets:
                self.data[dataset] = resample(self.data[dataset], n_samples=limitNumTrainingSamples, replace=False)

        # oversample
        upscale = self.parameters['upscalefactor'] if 'upscalefactor' in self.parameters else None
        if upscale:
            upscalemax =  self.parameters['upscalemax'] if 'upscalemax' in self.parameters else 10 
            upscalesignal = self.parameters['upscalefactorsignal'] if 'upscalefactorsignal' in self.parameters else 1.0 #upscalefactorsignal
            indices = []
            for i in range(len(self.data['train']['sample_weight'])):
                #print(x)
                x= self.data['train']['sample_weight'][i]
                if self.data['train']['y'][i] > 0.5:
                    x *= upscalesignal
                n = x * upscale
                # limit oversampling factor!
                if n > upscalemax:
                    n=upscalemax
                if n<1:
                    n=1
                intN = int(n)
                indices += [i]*intN
                #floatN = n-intN
                #if floatN > 0:
                #    if random.uniform(0.0,1.0) < floatN:
                #        indices += [i]

            self.data['train']['X'] = self.data['train']['X'][indices]
            self.data['train']['y'] = self.data['train']['y'][indices]
            self.data['train']['sample_weight'] = self.data['train']['sample_weight'][indices]
            self.verify_data()

        # BALANCE weights
        # calculate total weights and class_weights
        nSig = len([x for x in self.data['train']['y'] if x >= 0.5])
        nBkg = len([x for x in self.data['train']['y'] if x < 0.5])
        print("#SIG:", nSig)
        print("#BKG:", nBkg)
        weightsSignal = []
        weightsBackground = []
        for i in range(len(self.data['train']['sample_weight'])):
            if self.data['train']['y'][i] < 0.5:
                weightsBackground.append(self.data['train']['sample_weight'][i])
            else:
                weightsSignal.append(self.data['train']['sample_weight'][i])
        weightsSignal.sort()
        weightsBackground.sort()
        totalWeightSignal = sum(weightsSignal)
        totalWeightBackground = sum(weightsBackground)
        signalReweight = (totalWeightSignal+totalWeightBackground)/totalWeightSignal * self.parameters['additional_signal_weight']
        backgroundReweight = (totalWeightSignal+totalWeightBackground)/totalWeightBackground
        print("SUM of weights for signal:", totalWeightSignal)
        print("SUM of weights for background:", totalWeightBackground)
        
        if applyClassWeights:
            print("re-weight signals by:", signalReweight)
            print("re-weight background by:", backgroundReweight)
            for i in range(len(self.data['train']['sample_weight'])):
                if self.data['train']['y'][i] < 0.5:
                    self.data['train']['sample_weight'][i] *= backgroundReweight
                else:
                    self.data['train']['sample_weight'][i] *= signalReweight
        else:
            print("DO NOT re-weight signals by:", signalReweight)
        print("...")
        # TRAINING

        learningCurve = []
        if self.parameters['classifier'] == 'XGBClassifier':
            clf = clf.fit(self.data['train']['X'], self.data['train']['y'], self.data['train']['sample_weight'], verbose=True)
        else:
            try:
                clf = clf.fit(**self.data['train'])
            except:
                clf = clf.fit(X=self.data['train']['X'], y=self.data['train']['y'])
                
                if 'rounds' in self.parameters and self.parameters['rounds'] > 1:
                    for rNumber in range(self.parameters['rounds']):
                        results = clf.predict_proba(self.data['test']['X']) 
                        auc1 = roc_auc_score(self.data['test']['y'], results[:,1], sample_weight=self.data['test']['sample_weight'])
                        print(" round ", rNumber, " AUC=", auc1)
                        learningCurve.append(auc1)
                        clf = clf.fit(X=self.data['train']['X'], y=self.data['train']['y'])

        print("***** FIT done")

        # TEST
        try:
            results = clf.decision_function(self.data['test']['X'])
            print("***** EVALUATION on test sample done")
            results_train = clf.decision_function(self.data['train']['X'])
            print("***** EVALUATION on training sample done")

            print("R:", results.shape, results)

            results = np.c_[np.ones(results.shape[0]), results]
            results_train = np.c_[np.ones(results_train.shape[0]), results_train]
        except:
            results = clf.predict_proba(self.data['test']['X'])
            results_train = clf.predict_proba(self.data['train']['X'])

        # ROC curve
        print("calculating auc...")
        auc1 = roc_auc_score(self.data['test']['y'], results[:,1], sample_weight=self.data['test']['sample_weight'])
        auc_training = roc_auc_score(self.data['train']['y'], results_train[:,1], sample_weight=self.data['train']['sample_weight'])
        print("AUC:", auc1, " (training:", auc_training, ")")

        print("**** compute quantiles")
        qx = np.array([0.01, 0.99])
        qy = np.array([0.0, 0.0])
        thq = ROOT.TH1D("quant","quant",500000,-5.0,5.0)
        nS = len(results)
        for i in range(nS):
            thq.Fill(results[i][1])
        thq.GetQuantiles(2, qy, qx)

        # rescaling of SCORE to [0, 1]
        minProb = 2.0
        maxProb = -1.0
        #for i in range(len(self.data['train']['X'])):
        #    if results_train[i][1] > maxProb:
        #        maxProb = results_train[i][1]
        #    if results_train[i][1] < minProb:
        #        minProb = results_train[i][1]
        #for i in range(len(self.data['test']['X'])):
        #    if results[i][1] > maxProb:
        #        maxProb = results[i][1]
        #    if results[i][1] < minProb:
        #        minProb = results[i][1]

        minProb = qy[0]
        maxProb = qy[1]
        delta = maxProb-minProb
        minProb -= delta * 0.01
        maxProb += delta * 0.10

        useSqrt = False

        # fill TRAINING SCORE histogram (class probability)
        h1t = ROOT.TH1D("h1t","h1t",50,0.0,1.0)
        h2t = ROOT.TH1D("h2t","h2t",50,0.0,1.0)
        for i in range(len(self.data['train']['X'])):
            result = (results_train[i][1]-minProb)/(maxProb-minProb)
<<<<<<< HEAD
            if useSqrt:
                result = math.sqrt(result)
            weight = self.data['train']['sample_weight'][i] 
=======
            weight = self.data['train']['sample_weight'][i]
>>>>>>> 3df7e0593230ea62b87aaf5ce1c88e6efb9e41a8
            if self.data['train']['y'][i] < 0.5:
                h1t.Fill(result, weight)
            else:
                h2t.Fill(result, weight)
        print("entries:", h1t.GetEntries(), h2t.GetEntries())

        # fill TEST SCORE histogram (class probability)
        h1 = ROOT.TH1D("h1","h1",50,0.0,1.0)
        h2 = ROOT.TH1D("h2","h2",50,0.0,1.0)
        for i in range(len(self.data['test']['X'])):
            try:
                result = (results[i][1]-minProb)/(maxProb-minProb)
                if useSqrt:
                    result = math.sqrt(result)
                weight = self.data['test']['sample_weight'][i]
                if self.data['test']['y'][i] < 0.5:
                    h1.Fill(result, weight)
                else:
                    h2.Fill(result, weight)
            except Exception as e:
                print(e)
                pass

        timestamp = str(datetime.datetime.now()).split('.')[0].replace(' ','_').replace(':','-') + '_' + self.getHash()

        try:
            fpr, tpr, thresholds = roc_curve(self.data['test']['y'], results[:,1], sample_weight=self.data['test']['sample_weight'])
            auc2 = auc(fpr, tpr)
            print("AUC2:", auc2)

            print("fpr:",fpr)
            tgr = ROOT.TGraph(len(fpr), fpr, tpr)
            c1=ROOT.TCanvas("c1","c1",500,500)
            tgr.Draw("AL")
            tgr.GetXaxis().SetTitle('false positive rate')
            tgr.GetYaxis().SetTitle('true positive rate')
            tgr.SetTitle("ROC curve (AUC=%1.3f / %1.3f, training=%1.3f)"%(auc1,auc2,auc_training))

            fpr_train, tpr_train, thresholds_train = roc_curve(self.data['train']['y'], results_train[:,1], sample_weight=self.data['train']['sample_weight'])
            tgr_train = ROOT.TGraph(len(fpr_train), fpr_train, tpr_train)
            tgr_train.SetLineStyle(2)
            tgr_train.SetLineColor(ROOT.kOrange+2)
            tgr_train.Draw("SAME L")

            c1.SaveAs(self.logpath + '/scikit_comp_bdt_roc_' + timestamp + '.png')
            c1.SaveAs(self.logpath + '/scikit_comp_bdt_roc_' + timestamp + '.root')
        except Exception as e:
            print(e)

        h1.Scale(1.0/h1.Integral() if h1.Integral()!=0 else 1.0)
        h2.Scale(1.0/h2.Integral() if h2.Integral()!=0 else 1.0)
        h1t.Scale(1.0/h1t.Integral() if h1t.Integral()!=0 else 1.0)
        h2t.Scale(1.0/h2t.Integral() if h2t.Integral()!=0 else 1.0)

        maximum = max(h1.GetBinContent(h1.GetMaximumBin()), h2.GetBinContent(h2.GetMaximumBin()),h1t.GetBinContent(h1t.GetMaximumBin()),h2t.GetBinContent(h2t.GetMaximumBin()))
        h2.SetLineColor(ROOT.kRed)
        c1=ROOT.TCanvas("c1","c1",500,500)
        h1t.SetFillStyle( 3001)
        h1t.GetYaxis().SetRangeUser(0,1.1*maximum)
        h1t.SetFillColorAlpha(ROOT.kBlue-6, 0.5)
        h1t.SetLineColorAlpha(ROOT.kBlue-6, 0.5)
        h2t.SetFillStyle( 3001)
        h2t.SetFillColorAlpha(ROOT.kOrange-3, 0.5)
        h2t.SetLineColorAlpha(ROOT.kOrange-3, 0.5)
        h1t.SetTitle("Overtraining check")
        h1t.Draw("hist")
        h2t.Draw("hist;same")
        h1.Draw("hist;same")
        h2.Draw("hist;same")

        c1.SaveAs(self.logpath + '/scikit_comp_bdt_' + timestamp + '.png')
        c1.SaveAs(self.logpath + '/scikit_comp_bdt_' + timestamp + '.root')

        html = ['<html><head></head><body>']
        html.append('<h3>' + timestamp + '</h3>')
        html.append('<img src="scikit_comp_bdt_' + timestamp + '.png' + '">')
        html.append('<img src="scikit_comp_bdt_roc_' + timestamp + '.png' + '">')
        try:
            html.append('<br><br>%r => %r'%(clf, auc1))
        except:
            pass
        html.append('<br><br>')

        #for k,v in sorted(self.parameters.iteritems()):
        #    html.append('<b>' + k + '</b>: ' + '%r<br>'%v)

        html.append('<b>config</b>: ' + '%r<br>'%self.MVAsettings)
        html.append('<b>config</b>: ' + '%r<br>'%self.MVAsettingsEvaluated)
        html.append('<b>nSig</b>: ' + '%r<br>'%nSig)
        html.append('<b>nBkg</b>: ' + '%r<br>'%nBkg)
        html.append('<b>limitNumTrainingSamples</b>: ' + '%r<br>'%limitNumTrainingSamples)
        html.append('<b>AUC</b>: ' + '<b>%r</b> (%r) <br>'%(auc1, auc_training))
        try:
            html.append('<b>scaling</b>:%r<br>'%self.scaler)
        except:
            pass
        html.append('<b>raw-score-min</b>: ' + '%r<br>'%minProb)
        html.append('<b>raw-score-max</b>: ' + '%r<br>'%maxProb)

        try:
            for i,auc0 in enumerate(learningCurve):
                html.append('<b>step %d -&gt;%1.4f</b><br>'%(i, auc0))
        except:
            pass

        fprStepsForEfficiencies = [0.01, 0.05, 0.1, 0.2, 0.5]
        fprStepCounter = 0
        for i in range(len(fpr)):
            if fpr[i] > fprStepsForEfficiencies[fprStepCounter]:
                html.append('<b>FPR=%f</b>: '%fpr[i] + 'TPR=%f<br>'%tpr[i])
                fprStepCounter += 1
                if fprStepCounter>= len(fprStepsForEfficiencies):
                    break

        tprStepsForEfficiencies = [0.1, 0.2, 0.5, 0.75, 0.9, 0.95, 0.99]
        tprStepCounter = 0
        for i in range(len(tpr)):
            if tpr[i] > tprStepsForEfficiencies[tprStepCounter]:
                html.append('<b>TPR=%f</b>: '%tpr[i] + 'FPR=%f<br>'%fpr[i])
                tprStepCounter += 1
                if tprStepCounter>= len(tprStepsForEfficiencies):
                    break

        try:
            print("feature importances:")
            maxImportance = max(clf.feature_importances_)
            html.append("<h4>feature importance:</h4>")
            importanceList = []
            for i, v in enumerate(self.MVA_Vars['Nominal']):
                importanceList.append({'feature': v, 'importance': clf.feature_importances_[i]})
            importanceList.sort(key=lambda x:x['importance'], reverse=True)
            html.append('<table>')
            for d in importanceList:
                print((d['feature']+":").ljust(50), d['importance'])
                if len(d['feature']) > 60:
                    d['feature'] = d['feature'][:60] + '...'
                html.append("<tr><td style='width:600px;overflow:hidden;'><b>{feature}</b></td><td style='width:100px;'>{importance}</td><td style='width:520px;'><div style='width:{barWidth}px;height:20px;background-color:#226;color:white'> {relImportance}</div></td></tr>".format(feature=d['feature'], importance=d['importance'], relImportance=round(100.0*d['importance']/maxImportance,1), barWidth=d['importance']/maxImportance*500))
            html.append('</table>')
        except:
            pass

        try:
            print(clf.oob_improvement_)
        except:
            pass

        classifierOutputPath = self.getCachedNumpyArrayPath()
        classifierFileName = classifierOutputPath + '/clf' + timestamp + '.pkl'
<<<<<<< HEAD
        joblib.dump(clf, classifierFileName) 
        joblib.dump(self.scaler, classifierOutputPath + '/clf' + timestamp + '_scaler.pkl') 

=======
        joblib.dump(clf, classifierFileName)
>>>>>>> 3df7e0593230ea62b87aaf5ce1c88e6efb9e41a8
        html.append('<h3>classifier dump</h3>' + classifierFileName)

        html.append('</body></html>')
        htmlPath = self.logpath + '/scikit_comp_bdt_' + timestamp + '.html'
        with open(htmlPath, 'w') as outputfile:
            outputfile.write('\n'.join(html))
        print("INFO: html written to:", htmlPath)

        #tree.export_graphviz(clf, out_file='tree.gpv')
        #self.config.get('Directories','vhbbpath')+'/python/weights/'


        return self

    def printInfo(self):
        print("not implemented")

# read arguments
argv = sys.argv
parser = OptionParser()
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                          help="Verbose mode.")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-t","--trainingRegions", dest="trainingRegions", default='',
                      help="cut region identifier")
(opts, args) = parser.parse_args(argv)
if opts.config =="":
        opts.config = ["config"]

# Import after configure to get help message
from myutils import BetterConfigParser, mvainfo, ParseInfo

# load config
config = BetterConfigParser()
config.read(opts.config)

# initialize
trainingRegions = opts.trainingRegions.split(',')
if len(trainingRegions) > 1:
    print ("ERROR: not implemented!")
    exit(1)
for trainingRegion in trainingRegions:
    th = MvaTrainingHelper(config=config, mvaName=trainingRegion)
    th.prepare().run()
    th.printInfo()

