#!/usr/bin/env python
from __future__ import print_function
import unittest
import sys
import random
sys.path.append('../')
from myutils.sampleTree import SampleTree as SampleTree
import os

class TestSampleTreeMethods(unittest.TestCase):

    scratchDirectory = os.environ['SCRATCH_DIR'] if 'SCRATCH_DIR' in os.environ else '.'

    def getTree(self):
        fileNames = [TestSampleTreeMethods.scratchDirectory + '/tree_%d.root'%i for i in range(10)]
        return SampleTree(fileNames)

    def test_NumberOfEntries(self):
        sampleTree = self.getTree()
        self.assertEqual(sampleTree.tree.GetEntries(), 1000000)

    def test_SimpleTreeIteration(self):
        sampleTree = self.getTree()
        nSelectedEvents = 0
        for event in sampleTree:
            if event.nJet == 9:
                s1 = sum([event.Jet[x] for x in range(event.nJet)])
                if s1 > 900:
                    nSelectedEvents += 1
        nSelectedEventsDraw = sampleTree.tree.Draw("a", "nJet==9&&Sum$(Jet)>900", "goff")
        print ("method A:", nSelectedEvents)
        print ("method B:", nSelectedEventsDraw)
        self.assertEqual(nSelectedEventsDraw, nSelectedEvents)

    # test reading 1 file and writing to many files at once
    def test_MultiOutput(self):
        sampleTree = self.getTree()

        # define some random cuts
        cuts = [
            "nJet==5&&Sum$(Jet)>500",
            "nJet==6&&Sum$(Jet)>600",
            "nJet==7&&Sum$(Jet)>700",
            "nJet==8&&Sum$(Jet)>800",
            "nJet==9 && Sum$(Jet)>800 && a<0 && (b>30 || b > 50)",
            "nJet==9 && Sum$(Jet)>800 && (a<0 && (b>30 || b > 50)) || (a>0 && (b>10 || b > 90)) || (a>0.8 && (b>5 || b > 50))",
        ]

        # add some more random cuts
        for j in range(5):
            randomCuts = ["(a<%f && (b>%f || c > %f))"%(random.gauss(0,0.5), random.uniform(0,50), random.uniform(0,2)) for i in range(50)]
            cuts.append('||'.join(randomCuts))

        # write skimmed subtrees to file
        for i, cut in enumerate(cuts):
            sampleTree.addOutputTree(TestSampleTreeMethods.scratchDirectory + '/tree_skimmed_%d.root'%i, cut, '')
        sampleTree.process()

        # load subtrees and count events
        newSampleTrees = [SampleTree([TestSampleTreeMethods.scratchDirectory + '/tree_skimmed_%d.root'%i])  for i, cut in enumerate(cuts)]
        resultsMethodA = [newSampleTree.tree.GetEntries() for newSampleTree in newSampleTrees]

        # count directly
        resultsMethodB = [sampleTree.tree.Draw("a", cut, "goff") for i, cut in enumerate(cuts)]

        print(resultsMethodA)
        print(resultsMethodB)

        self.assertTrue(all([resultsMethodA[i] == resultsMethodB[i] for i in range(len(resultsMethodA))]))

    # test if an exception is thrown, if one tries to use a branch for a cut, which does not exist in the tree
    def test_MissingBranchForFormula(self):
        sampleTree = self.getTree()
        badCut = 'thisVariableDoesNotExistInTheTree==42'
        sampleTree.addOutputTree(TestSampleTreeMethods.scratchDirectory + '/tree_dummy.root', badCut, '')
        with self.assertRaises(Exception) as e:
            sampleTree.process()

    # test if an exception is thrown, if one gives bad arguments as cut
    def test_BadCut1(self):
        sampleTree = self.getTree()
        badCut = 42
        sampleTree.addOutputTree(TestSampleTreeMethods.scratchDirectory + '/tree_dummy.root', badCut, '')
        with self.assertRaises(Exception) as e:
            sampleTree.process()

    # test if an exception is thrown, if one gives bad arguments as cut
    def test_BadCut2(self):
        sampleTree = self.getTree()
        badCut = {'BLUBB': 'BLA'}
        sampleTree.addOutputTree(TestSampleTreeMethods.scratchDirectory + '/tree_dummy.root', badCut, '')
        with self.assertRaises(Exception) as e:
            sampleTree.process()

    # test if an exception is thrown, if one gives bad arguments as cut
    def test_BadCut3(self):
        sampleTree = self.getTree()
        badCut = 'nJet===5'
        sampleTree.addOutputTree(TestSampleTreeMethods.scratchDirectory + '/tree_dummy.root', badCut, '')
        with self.assertRaises(Exception) as e:
            sampleTree.process()

    # test if an exception is thrown, if one gives bad arguments as cut
    def test_BadCut4(self):
        sampleTree = self.getTree()
        goodCut = 'nJet==5'
        badCutSequenceMode = 'LULZ'
        with self.assertRaises(Exception) as e:
            sampleTree.addOutputTree(TestSampleTreeMethods.scratchDirectory + '/tree_dummy.root', goodCut, cutSequenceMode=badCutSequenceMode)

    # test if an exception is thrown, if one gives bad arguments as cut
    def test_BadCallback(self):
        sampleTree = self.getTree()
        goodCut = 'nJet==5'
        sampleTree.addOutputTree(TestSampleTreeMethods.scratchDirectory + '/tree_dummy.root', goodCut,
                                 callbacks={'beforeLoop': 'aStringIsNotAFunction!'}
                                 )
        with self.assertRaises(Exception) as e:
            sampleTree.process()

    def test_TreeCutDict(self):

        def flattenDict(cutDict):
            if type(cutDict) == str:
                return cutDict
            elif type(cutDict) == dict:
                if 'OR' in cutDict:
                    return '||'.join(['(%s)'%flattenDict(x) for x in cutDict['OR']])
                elif 'AND' in cutDict:
                    return '&&'.join(['(%s)'%flattenDict(x) for x in cutDict['AND']])
                else:
                    raise Exception('BadTreeTypeCutDict')

        sampleTree = self.getTree()
        cutDict = {'OR':
                   [
                       {
                           'AND': [
                               'nJet>8',
                               'a>0',
                               'a>c']
                       },
                       'nJet==6&&Sum$(Jet)>600',
                       'c>1',
                       {
                           'OR': [
                               'Sum$(Jet)>1200',
                               'a>0.8',
                               'b>80',
                               {
                                   'AND': [
                                       'a>0.9',
                                       'b>80',
                                       'c>0.9',
                                   ]
                               }
                           ]
                       }
                   ]
               }
        cutFlat = flattenDict(cutDict)
        print ("flat:", cutFlat)
        sampleTree.addOutputTree(TestSampleTreeMethods.scratchDirectory + '/tree_dummy.root', cutDict, cutSequenceMode='TREE')
        sampleTree.process()

        # count number of entries written to output file
        skimmedSampleTree = SampleTree([TestSampleTreeMethods.scratchDirectory + '/tree_dummy.root'])
        resultsMethodA = skimmedSampleTree.tree.GetEntries()
        resultsMethodB = sampleTree.tree.Draw("a", cutFlat, "goff")
        self.assertEqual(resultsMethodA, resultsMethodB)

if __name__ == '__main__':
    unittest.main()
