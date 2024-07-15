
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 10:26:32 2020

@author: Javier
"""
#

from __future__ import print_function
from PyQt5 import Qt
from qtpy.QtWidgets import (QHeaderView, QCheckBox, QSpinBox, QLineEdit,
                            QDoubleSpinBox, QTextEdit, QComboBox,
                            QTableWidget, QAction, QMessageBox, QFileDialog,
                            QInputDialog)

from qtpy import QtWidgets, uic
import numpy as np
import time
import os
import sys
from pyqtgraph.parametertree import Parameter, ParameterTree

import PyqtTools.FileModule as FileMod
import PyqtTools.PlotModule as PltMod
import PyqtTools.CharacterizationModule as Charact

from PyqtTools.PlotModule import Plotter as TimePlt
from PyqtTools.PlotModule import PlotterParameters as TimePltPars
from PyqtTools.PlotModule import PSDPlotter as PSDPlt
from PyqtTools.PlotModule import PSDParameters as PSDPltPars



import PyCharAcqCore.PyCharAcqThread as AcqMod


class MainWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self):
        super(MainWindow, self).__init__()

        self.threadAcq = None
        self.threadSave = None
        self.threadPlotter = None
        self.threadPSDPlotter = None
        self.threadPlotterRaw = None
        self.threadCharact = None
        self.RefreshGrapg = None

        layout = Qt.QVBoxLayout(self)

        self.btnAcq = Qt.QPushButton("Start Acq!")
        layout.addWidget(self.btnAcq)

        self.ResetGraph = Qt.QPushButton("Reset Graphics")
        layout.addWidget(self.ResetGraph)

        self.SamplingPar = AcqMod.SampSetParam(name='SampSettingConf')
        self.Parameters = Parameter.create(name='App Parameters',
                                           type='group',
                                           children=(self.SamplingPar,))

        self.SamplingPar.NewConf.connect(self.on_NewConf)
        self.SamplingPar.Fs.sigValueChanged.connect(self.on_FsChanged)
        self.SamplingPar.FsxCh.sigValueChanged.connect(self.on_FsxChChanged)

        self.SwParams = Charact.SweepsConfig(QTparent=self, name='Sweeps Configuration')
        self.Parameters.addChild(self.SwParams)

        self.PlotParams = TimePltPars(name='TimePlt',
                              title='Time Plot Options')

        self.PlotParams.NewConf.connect(self.on_NewPlotConf)
        # self.Parameters.addChild(self.PlotParams)

        self.RawPlotParams = TimePltPars(name='RawPlot')
        # self.Parameters.addChild(self.RawPlotParams)

        self.PsdPlotParams = PSDPltPars(name='PSDPlt',
                                        title='PSD Plot Options')
        # self.Parameters.addChild(self.PsdPlotParams)

        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')

        layout.addWidget(self.treepar)

        self.setGeometry(750, 40, 500, 900)
        self.setWindowTitle('MainWindow')

        self.btnAcq.clicked.connect(self.on_btnStart)
        self.ResetGraph.clicked.connect(self.on_ResetGraph)

        self.FileParameters = FileMod.SaveFileParameters(QTparent=self,
                                                          name='Record File')
        # self.Parameters.addChild(self.FileParameters)

        self.ConfigParameters = FileMod.SaveSateParameters(QTparent=self,
                                                           name='Configuration File')
        self.Parameters.addChild(self.ConfigParameters)
        self.on_FsChanged()
        self.on_FsxChChanged()
        self.on_NewConf()

    def on_FsChanged(self):
        self.RawPlotParams.param('Fs').setValue(self.SamplingPar.Fs.value())

    def on_FsxChChanged(self):
        print('FSXCH', self.SamplingPar.FsxCh.value())
        self.PlotParams.param('Fs').setValue(self.SamplingPar.FsxCh.value())
        self.PsdPlotParams.param('Fs').setValue(self.SamplingPar.FsxCh.value())

    def on_pars_changed(self, param, changes):
        print("tree changes:")
        for param, change, data in changes:
            path = self.Parameters.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
        print('  parameter: %s' % childName)
        print('  change:    %s' % change)
        print('  data:      %s' % str(data))
        print('  ----------')

        if childName == 'SampSettingConf.Sampling Settings.Vgs':
            if self.threadAcq:
                Vds = self.threadAcq.DaqInterface.Vds
                self.threadAcq.DaqInterface.SetBias(Vgs=data, Vds=Vds,
                                                    ChAo2=None, ChAo3=None)

        if childName == 'SampSettingConf.Sampling Settings.Vds':
            if self.threadAcq:
                Vgs = self.threadAcq.DaqInterface.Vgs
                self.threadAcq.DaqInterface.SetBias(Vgs=Vgs, Vds=data,
                                                    ChAo2=None, ChAo3=None)

    def on_NewPSDConf(self):
        if self.threadPSDPlotter is not None:
            nFFT = self.PsdPlotParams.param('nFFT').value()
            nAvg = self.PsdPlotParams.param('nAvg').value()
            self.threadPSDPlotter.InitBuffer(nFFT=nFFT, nAvg=nAvg)

    def on_NewConf(self):
        # self.PlotParams.SetChannels(self.SamplingPar.GetChannelsNames())
        self.PlotParams.SetChannels(self.SamplingPar.GetChannelsNames()[1])
        self.RawPlotParams.SetChannels(self.SamplingPar.GetRowNames())
        self.PsdPlotParams.ChannelConf = self.PlotParams.ChannelConf
        nChannels = self.PlotParams.param('nChannels').value()
        self.PsdPlotParams.param('nChannels').setValue(nChannels)

    def on_NewPlotConf(self):
        if self.threadPlotter is not None:
            ViewTime = self.PlotParams.param('ViewTime').value()
            self.threadPlotter.SetViewTime(ViewTime)        
            RefreshTime = self.PlotParams.param('RefreshTime').value()
            self.threadPlotter.SetRefreshTime(RefreshTime)        

    def on_ResetGraph(self):
        if self.threadAcq is None:
            return

        # Plot and PSD threads are stopped
        if self.threadPlotter is not None:
            self.threadPlotter.stop()
            self.threadPlotter = None

        if self.threadPSDPlotter is not None:
            self.threadPSDPlotter.stop()
            self.threadPSDPlotter = None

        if self.threadPlotterRaw is not None:
            self.threadPlotterRaw.stop()
            self.threadPlotterRaw = None

        if self.PlotParams.param('PlotEnable').value():
            Pltkw = self.PlotParams.GetParams()
            self.threadPlotter = TimePlt(**Pltkw)
            self.threadPlotter.start()

        if self.PsdPlotParams.param('PlotEnable').value():
            PSDKwargs = self.PsdPlotParams.GetParams()
            self.threadPSDPlotter = PSDPlt(**PSDKwargs)
            self.threadPSDPlotter.start()

        if self.RawPlotParams.param('PlotEnable').value():
            RwPltkw = self.RawPlotParams.GetParams()
            self.threadPlotterRaw = TimePlt(**RwPltkw)
            self.threadPlotterRaw.start()

    def on_btnStart(self):
        if self.threadAcq is None:
            GenKwargs = self.SamplingPar.GetSampKwargs()
            GenChanKwargs = self.SamplingPar.GetChannelsConfigKwargs()
            AvgIndex = self.SamplingPar.SampSet.param('nAvg').value()
            ChannelsNames = self.SamplingPar.GetChannelsNames()[1]
            print(ChannelsNames, '-->ChannelsNames')

            # Characterization part
            self.SweepsKwargs = self.SwParams.GetConfigSweepsParams()
            self.DcSaveKwargs = self.SwParams.GetSaveSweepsParams()

            self.threadCharact = Charact.StbDetThread(
                                                      nChannels=len(ChannelsNames),
                                                      ChnName=ChannelsNames,
                                                      PlotterDemodKwargs=self.PsdPlotParams.GetParams(),
                                                       **self.SweepsKwargs
                                                      )
            self.threadCharact.NextVg.connect(self.on_NextVg)
            self.threadCharact.NextVd.connect(self.on_NextVd)
            self.threadCharact.CharactEnd.connect(self.on_CharactEnd)
            
            GenKwargs['Vgs'] = self.threadCharact.NextVgs
            GenKwargs['Vds'] = self.threadCharact.NextVds

            # Acquisition part
            self.threadAcq = AcqMod.DataAcquisitionThread(ChannelsConfigKW=GenChanKwargs,
                                                          SampKw=GenKwargs,
                                                          AvgIndex=AvgIndex,
                                                          )

            self.threadAcq.NewMuxData.connect(self.on_NewSample)

            self.threadCharact.start()
            self.threadAcq.start()

            # PlotterKwargs = self.PlotParams.GetParams()

            # FileName = self.FileParameters.FilePath()
            # print('Filename', FileName)
            # if FileName == '':
            #     print('No file')
            # else:
            #     if os.path.isfile(FileName):
            #         print('Remove File')
            #         os.remove(FileName)
            #     MaxSize = self.FileParameters.param('MaxSize').value()
            #     self.threadSave = FileMod.DataSavingThread(FileName=FileName,
            #                                                nChannels=PlotterKwargs['nChannels'],
            #                                                MaxSize=MaxSize)
            #     self.threadSave.start()

            # self.on_ResetGraph()

            self.btnAcq.setText("Stop Gen")
            self.OldTime = time.time()
            self.Tss = []
        else:
            self.threadAcq.DaqInterface.Stop()
            self.threadAcq = None

            if self.threadCharact is not None:
                self.threadCharact.stop()
                # self.threadCharact.CharactEnd.disconnect()
                self.threadCharact = None
            # if self.threadSave is not None:
            #     self.threadSave.terminate()
            #     self.threadSave = None
            # if self.PlotParams.param('PlotEnable').value():
            #     self.threadPlotter.terminate()
            #     self.threadPlotter = None
            # if self.threadPSDPlotter is not None:
            #     self.threadPSDPlotter.stop()
            #     self.threadPSDPlotter = None
            # if self.threadPlotterRaw is not None:
            #     self.threadPlotterRaw.stop()
            #     self.threadPlotterRaw = None

            self.btnAcq.setText("Start Gen")

    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.Tss.append(Ts)
        self.OldTime = time.time()

        # if self.threadSave is not None:
        #     self.threadSave.AddData(self.threadAcq.OutData.transpose()) # Change for aiData?? TODO

        if self.threadCharact is not None: #Flag estable and ACenable
            if self.threadCharact.Stable and self.threadCharact.ACenable:
                self.threadCharact.AddData(self.threadAcq.OutDataAC.transpose())
            else:
                self.threadCharact.AddData(self.threadAcq.OutDataDC.transpose())

        # if self.threadPlotter is not None:
        #     self.threadPlotter.AddData(self.threadAcq.OutDataDC.transpose())

        # if self.threadPSDPlotter is not None:
        #     self.threadPSDPlotter.AddData(self.threadAcq.OutDataAC.transpose())

        # if self.threadPlotterRaw is not None:
        #     self.threadPlotterRaw.AddData(self.threadAcq.aiData.transpose())
        print('sample time', Ts, np.mean(self.Tss))

           
# #############################Restart Timer Stabilization####################
    def on_NextVg(self):
        self.threadAcq.DaqInterface.SetBias(Vgs=self.threadCharact.NextVgs,
                                            Vds=self.threadCharact.NextVds,
                                            ChAo2=None,
                                            ChAo3=None)
        print('NEXT VGS SWEEP')

# #############################Nex Vd Value##############################
    def on_NextVd(self):        
        self.threadAcq.DaqInterface.SetBias(Vgs=self.threadCharact.NextVgs,
                                            Vds=self.threadCharact.NextVds,
                                            ChAo2=None,
                                            ChAo3=None)

        
    def on_CharactEnd(self):
        print('END Charact')
        self.threadCharact.NextVg.disconnect()
        self.threadCharact.NextVd.disconnect()
        self.threadCharact.CharactEnd.disconnect()
        CharactDCDict = self.threadCharact.DCDict
        CharactACDict = self.threadCharact.ACDict

        self.threadCharact.SaveDCAC.SaveDicts(Dcdict=CharactDCDict,
                                              Acdict=CharactACDict,
                                              **self.DcSaveKwargs)
        self.threadAcq.NewMuxData.disconnect()
        
        self.threadAcq.DaqInterface.Stop()
        self.threadAcq.terminate()
        self.threadAcq = None

        if self.threadSave is not None:
            self.threadSave.terminate()
            self.threadSave = None

        if self.threadPlotter is not None:
            self.threadPlotter.terminate()
            self.threadPlotter = None


def main():
    import argparse
    import pkg_resources

    # Add version option
    __version__ = pkg_resources.require("PyqtTools")[0].version
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(
                            version=__version__))
    parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()