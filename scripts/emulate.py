#!/usr/bin/env python3
#-----------------------------------------------------------------------------
# Title      : Eval board instance
#-----------------------------------------------------------------------------
# File       : evalBoard.py
# Author     : Ryan Herbst, rherbst@slac.stanford.edu
# Created    : 2016-09-29
# Last update: 2016-09-29
#-----------------------------------------------------------------------------
# Description:
# Rogue interface to eval board
#-----------------------------------------------------------------------------
# This file is part of the rogue_example software. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the rogue_example software, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import pyrogue.gui
import PyQt4.QtGui
import pyrogue.utilities.prbs
import pyrogue.utilities.fileio
import pyrogue
import pyrogue.smem
import rogue.interfaces.stream
import pyrogue.epics
import surf.axi
import surf.protocols.ssi
import threading
import signal
import atexit
import yaml
import time
import sys
import testBridge
import logging
import datetime
import pyrogue.simulation

#logging.getLogger("pyrogue.EpicsCaServer").setLevel(logging.INFO)
#logging.getLogger("pyrogue.MemoryBlock").setLevel(logging.DEBUG)
rogue.Logging.setLevel(rogue.Logging.Debug)

class EvalBoard(pyrogue.Root):

    def __init__(self):

        pyrogue.Root.__init__(self,'evalBoard','Evaluation Board')

        # File writer
        dataWriter = pyrogue.utilities.fileio.StreamWriter('dataWriter')
        self.add(dataWriter)

        # Create and Connect SRP to VC0
        srp = pyrogue.simulation.MemEmulate()
        
        # PRBS Receiver as secdonary receiver for VC1
        prbsRx = pyrogue.utilities.prbs.PrbsRx('prbsRx')
        self.add(prbsRx)
        
        # Add Devices
        self.add(surf.axi.AxiVersion(memBase=srp,offset=0x0))
        self.add(surf.protocols.ssi.SsiPrbsTx(memBase=srp,offset=0x30000))
        
        self.testBlock = pyrogue.RawBlock(srp)
        self.smem = pyrogue.smem.SMemControl('rogueTest',self)

        # Run control
        self.add(pyrogue.RunControl('runControl' ,
                                    rates={1:'1 Hz', 10:'10 Hz',30:'30 Hz'}))
                                    #cmd=self.SsiPrbsTx.oneShot()))

        # Export remote objects
    #    self.start(pyroGroup='rogueTest')

        # Create epics node
        pvMap = {'evalBoard.AxiVersion.UpTimeCnt':'testCnt',
                 'evalBoard.AxiVersion.ScratchPad':'testPad'}
        pvMap = None  # Comment out to enable map
        self.epics = pyrogue.epics.EpicsCaServer('rogueTest',self,pvMap)
        self.epics.start()

    def stop(self):
        self.epics.stop()
        super().stop()


if __name__ == "__main__":

    evalBoard = EvalBoard()

    # Create GUI
    appTop = PyQt4.QtGui.QApplication(sys.argv)
    guiTop = pyrogue.gui.GuiTop('rogueTest')
    guiTop.addTree(evalBoard)

    # Run gui
    appTop.exec_()
    evalBoard.stop()

