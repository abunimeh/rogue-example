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
import pyrogue.protocols
import PyQt4.QtGui
import pyrogue.utilities.prbs
import pyrogue.utilities.fileio
import pyrogue
import pyrogue.smem
import pyrogue.mysql
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

#logging.getLogger("pyrogue.PollQueue").setLevel(logging.DEBUG)
#logging.getLogger("pyrogue").setLevel(logging.DEBUG)
#rogue.Logging.setLevel(rogue.Logging.Debug)
#rogue.Logging.setFilter("pyrogue.rssi",rogue.Logging.Debug)
#rogue.Logging.setFilter("pyrogue.memory.Master",rogue.Logging.Info)

class EvalBoard(pyrogue.Root):

    def __init__(self):

        pyrogue.Root.__init__(self,name='evalBoard',description='Evaluation Board')

        # File writer
        dataWriter = pyrogue.utilities.fileio.StreamWriter(name='dataWriter')
        self.add(dataWriter)

        # Create the PGP interfaces
        udp = pyrogue.protocols.UdpRssiPack(host='192.168.2.194',port=8192,size=1400)

        # Create and Connect SRP to VC0
        srp = rogue.protocols.srp.SrpV3()
        pyrogue.streamConnectBiDir(srp,udp.application(0))

        # Add configuration stream to file as channel 0
        pyrogue.streamConnect(self,dataWriter.getChannel(0x0))

        pyrogue.streamConnect(udp.application(1),dataWriter.getChannel(0x1))

        # PRBS Receiver as secdonary receiver for VC1
        #prbsRx = pyrogue.utilities.prbs.PrbsRx('prbsRx')
        #pyrogue.streamTap(udp.application(1),prbsRx)
        #self.add(prbsRx)

        # Add Devices
        self.add(surf.axi.AxiVersion(memBase=srp,offset=0x0,expand=False))
        #self.add(surf.protocols.ssi.SsiPrbsTx(memBase=srp,offset=0x40000))

        self.add(pyrogue.LocalVariable(name='list',value=([0] * 10)))

        self.smem = pyrogue.smem.SMemControl(group='rogueTest',root=self)

        # Run control
        self.add(pyrogue.RunControl(name='runControl' ,
                                    rates={1:'1 Hz', 10:'10 Hz',30:'30 Hz'}))
                                    #cmd=self.SsiPrbsTx.oneShot()))

        # Export remote objects
        #self.start(pollEn=True,pyroGroup='rogueTest',pyroHost='134.79.229.11',pyroNs='134.79.229.11')
        #self.start(pollEn=True,pyroGroup='rogueTest',pyroHost='134.79.229.11')
        #self.start(pollEn=True,pyroGroup='rogueTest')
        self.start(pollEn=True,pyroGroup='rogueTest')

        # Create epics node
        pvMap = {'evalBoard.AxiVersion.UpTimeCnt':'testCnt',
                 'evalBoard.AxiVersion.ScratchPad':'testPad'}
        pvMap = None  # Comment out to enable map
        self.epics = pyrogue.epics.EpicsCaServer(base='rogueTest',root=self,pvMap=pvMap)
        self.epics.start()

        self.mysql = pyrogue.mysql.MysqlGw(dbHost='localhost',dbName='rogue',dbUser='rogue',dbPass='rogue',root=self)
        self.mysql.start()

    def stop(self):
        self.epics.stop()
        self.mysql.stop()
        super().stop()

if __name__ == "__main__":

    evalBoard = EvalBoard()

    appTop = PyQt4.QtGui.QApplication(sys.argv)
    guiTop = pyrogue.gui.GuiTop(group='rogueTest')
    guiTop.addTree(evalBoard)

    # Run gui
    appTop.exec_()
    evalBoard.stop()

