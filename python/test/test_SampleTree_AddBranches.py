#!/usr/bin/env python
from __future__ import print_function
import unittest
import sys
import ROOT
import random
sys.path.append('../')
from myutils.sampleTree import SampleTree as SampleTree
import os

# this does some stuff
#  and can go to a separate file in a real application
class BlablaCorrector(object):

    # initialize heavy stuff once
    correctionFactor = 1.0
    correctionOffset = 0.0

    # this static methods are applied to every entry and passed as a function to SampleTree class
    @staticmethod
    def applyCorrection(tree):
        return (tree.a+tree.b+tree.c) * BlablaCorrector.correctionFactor + BlablaCorrector.correctionOffset

    @staticmethod
    def applyOtherCorrection(tree):
        return (tree.a+tree.b+tree.c) * 4 + 200

    @staticmethod
    def addVector(tree, destinationArray):
        destinationArray[0] = min(tree.a, tree.b, tree.c)
        destinationArray[1] = max(tree.a, tree.b, tree.c)
        destinationArray[2] = tree.a+tree.b+tree.c
        destinationArray[3] = tree.b * 10 + 42

class TestSampleTreeAddBranchesMethods(unittest.TestCase):

    scratchDirectory = os.environ['SCRATCH_DIR'] if 'SCRATCH_DIR' in os.environ else '.'

    def getTree(self):
        fileNames = [TestSampleTreeAddBranchesMethods.scratchDirectory + '/tree_%d.root'%i for i in range(1)]
        return SampleTree(fileNames)

    def test_AddBranches(self):

        sampleTree = self.getTree()

        # you can add a string
        sampleTree.addOutputBranch('jetSum', 'Sum$(Jet)')
        sampleTree.addOutputBranch('abcSum', 'a+b+c')

        # or a function, including lambdas
        sampleTree.addOutputBranch('abcSum2', lambda tree: tree.a + tree.b + tree.c)

        # alternative syntax
        vectorLength = 4
        sampleTree.addOutputBranches([
            {
                'name': 'abcSum3',
                'formula': BlablaCorrector.applyCorrection,
            },
            {
                'name': 'stuff',
                'formula': BlablaCorrector.applyOtherCorrection,
            },
            {
                'name': 'vectorstuff',
                'formula': BlablaCorrector.addVector,
                'length': vectorLength,
            },
        ]
        )

        # write output tree and apply also a cut
        sampleTree.addOutputTree(
            TestSampleTreeAddBranchesMethods.scratchDirectory + '/tree_withaddedbranches.root',
            cut='1',
        )
        sampleTree.process()

        # compare histograms of tree with new branches with expected result
        newSampleTree = SampleTree([TestSampleTreeAddBranchesMethods.scratchDirectory + '/tree_withaddedbranches.root'])
        newTree = newSampleTree.tree
        outfile = ROOT.TFile.Open(TestSampleTreeAddBranchesMethods.scratchDirectory + '/histograms.root', 'recreate')
        h1 = ROOT.TH1F('h1', 'h1', 200, 0, 200)
        h2 = ROOT.TH1F('h2', 'h2', 200, 0, 200)

        # new branch
        newTree.Draw('vectorstuff[2]>>h1')

        # expected result
        sampleTree.tree.Draw('a+b+c>>h2')

        m1 = h1.GetMean()
        m2 = h2.GetMean()
        self.assertTrue(abs(m1-m2) < 0.00001)
        self.assertTrue(abs(m1/m2) < 1.00001)
        self.assertTrue(abs(m1/m2) > 0.99999)
        print("histogram means:", m1, m2, " check histograms h1 and h2 in histograms.root")
        outfile.Write()
        outfile.Close()

        # test if we really have a vector with 4 entries in our output tree
        h3 = ROOT.TH1F('h3', 'h3', 2000, -1000, 10000)
        h4 = ROOT.TH1F('h4', 'h4', 2000, -1000, 10000)
        newTree.Draw('vectorstuff>>h3')
        sampleTree.tree.Draw('a>>h4')
        self.assertTrue(h3.GetEntries() > 0)
        self.assertEqual(h3.GetEntries(), h4.GetEntries()*vectorLength)

if __name__ == '__main__':
    unittest.main()
