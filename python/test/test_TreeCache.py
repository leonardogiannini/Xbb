#!/usr/bin/env python
from __future__ import print_function
import unittest
import sys
import random
sys.path.append('../')
from myutils.sampleTree import SampleTree as SampleTree
from myutils import NewTreeCache as TreeCache
import os

class TestTreeCacheMethods(unittest.TestCase):

    def setUp(self):
        self.scratchDirectory = os.environ['SCRATCH_DIR'] if 'SCRATCH_DIR' in os.environ else '.'
        self.sampleName = 'SomeSampleWhichWillBeCached'
        self.someCut = "nJet==5&&Sum$(Jet)>500"
        self.tmpDir = self.scratchDirectory + '/tmp/'
        self.cacheDir = self.scratchDirectory + '/cache/'
        try:
            os.mkdir(self.tmpDir)
        except:
            pass
        try:
            os.mkdir(self.cacheDir)
        except:
            pass

    def getTree(self):
        fileNames = [self.scratchDirectory + '/tree_%d.root'%i for i in range(10)]
        return SampleTree(fileNames)

    def test_TreeCache1(self):

        # load sample tree
        sampleTree = self.getTree()

        # create skimmed tree (cache)
        tc = TreeCache.TreeCache(
            sample=self.sampleName,
            cutList=[self.someCut],
            inputFolder=self.scratchDirectory,
            tmpFolder=self.tmpDir,
            outputFolder=self.cacheDir,
            branches=['a', 'b', 'c'],
            debug=False
        )
        tc.setSampleTree(sampleTree).cache()
        sampleTree.process()

        # now try to load the cached tree
        tc2 = TreeCache.TreeCache(
            sample=self.sampleName,
            cutList=[self.someCut],
            inputFolder=self.scratchDirectory,
            tmpFolder=self.tmpDir,
            outputFolder=self.cacheDir,
            debug=False
        )

        # and check if cached tree is there
        self.assertTrue(tc2.isCached())
        self.assertTrue(tc2.isCachedAndValid())

        # get the sampleTree
        sampleTreeCached = tc2.getTree()

        # check if the number of events matches
        nSelectedEvents = sampleTree.tree.Draw("a", self.someCut, "goff")
        self.assertEqual(sampleTreeCached.tree.GetEntries(), nSelectedEvents)

    def test_NotCached(self):

        # now try to load the cached tree
        tc2 = TreeCache.TreeCache(
            sample='ThisSampleDoesNotExistInCache',
            cutList=[self.someCut],
            inputFolder=self.scratchDirectory,
            tmpFolder=self.tmpDir,
            outputFolder=self.cacheDir,
            debug=False
        )
        self.assertFalse(tc2.isCached())

if __name__ == '__main__':
    unittest.main()
