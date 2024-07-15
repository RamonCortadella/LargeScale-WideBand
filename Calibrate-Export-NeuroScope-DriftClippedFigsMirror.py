import h5py
import numpy as np
from PhyREC.NeoInterface import NeoSegment, NeoSignal
import PhyREC.PlotWaves as Rplt
import PhyREC.SignalProcess as Rpro
import quantities as pq
import PyGFETdb.DataStructures as FETdata
import PyGFETdb.DataClass as FETcl
import matplotlib as mpl
import matplotlib.pyplot as plt
import deepdish as dd
from scipy.ndimage.filters import median_filter
from scipy import interpolate
import os
import gc

def CalcVgeff(Sig, Tchar):
    Buffer = 0.0
    Vgs = Tchar.GetVgs()
    vgs = np.linspace(np.min(Vgs), np.max(Vgs), 1000)
    Inds = np.where(vgs < Tchar.GetUd0()[0]-Buffer)[0]
    
    if len(Inds) == 0:
        Inds = [0 ,1]
        print('in')   
    
    Ids = Tchar.GetIds(Vgs=vgs[Inds])[0]

    fgm = interpolate.interp1d(Ids, vgs[Inds])
    st = fgm(np.clip(Sig, np.min(Ids), np.max(Ids)))

    print(str(Sig.name), '-> ', 'Vgs', np.mean(st))
    return Sig.duplicate_with_new_array(st)*pq.V/pq.A



def ClippedReturn(Sig, Tchar):
    Buffer = 0
    Vgs = Tchar.GetVgs()
    vgs = np.linspace(np.min(Vgs), np.max(Vgs), 1000)
    Inds = np.where(vgs < Tchar.GetUd0()[0]-Buffer)[0]
    print(len(Inds), Tchar.GetUd0()[0]-Buffer)
    if len(Inds) == 0:
        Inds = [0 ,1]
        print('in')
    Ids = Tchar.GetIds(Vgs=vgs[Inds])[0]

    clipInd = np.where((np.array(Sig)<=np.min(Ids))|(np.array(Sig) >= np.max(Ids)))[0]
 
    clip = np.zeros(len(Sig))
    clip[clipInd] = 1

    return Sig.duplicate_with_new_array(clip)


def MedianFilter(Sig,WindowSamps,SampDrop):
    sigArr = Sig.as_array()[:,0]
    
    y = median_filter(sigArr[::SampDrop], WindowSamps, mode='constant' )
    xInt= np.linspace(0,len(sigArr),len(sigArr))
    x = np.linspace(0,len(sigArr),len(sigArr[::SampDrop]))
    
    sig = np.interp(xInt,x,y)
    
    sig = sigArr-sig
    return Sig.duplicate_with_new_array(sig)

    # sig = median_filter(Sig.as_array()[:,0], WindowSamps, mode='constant' )

    # sig = Sig.duplicate_with_new_array(sig)
    # sig = Sig-sig
    # return Sig.duplicate_with_new_array(sig)

def DownSampling(Sig,DownFact):

    sig = Sig.as_array()[::DownFact,0]

    sig = Sig.duplicate_with_new_array(sig)
    sig.sampling_rate = Sig.sampling_rate/DownFact

    return sig

def LoadDemuxCal(File, StabTimeSw,StabTimeIni, SampsSwitchPeriod, DCChar, MedianFilterTime, LPF, SampDrop, DownFact,Tstab, Tend, Rows, Cols):


    CalRecAC = NeoSegment()
    CalRecDC = NeoSegment()
    CalRecDCCurr = NeoSegment()

    ColRemap = [10,9,12,11,15,16,13,14,2,1,4,3,7,8,5,6] 
    for ir in np.arange(32):
        nrows = 32
        with h5py.File(File,'r') as h5f:
            DataRows = h5f['data'][:,ir]
        print('loaded data',ir)
        gc.collect()
        
        Fs = 1e6*pq.Hz
        FsCh = Fs/(nrows*SampsSwitchPeriod*ncols)
    
        nr = nrows
        SSP = SampsSwitchPeriod
        nc = ncols
        
        CroppedDR = DataRows.reshape((SSP, -1), order='F')
    
        for ic in np.arange(nc):
    
            chdat = CroppedDR[:,ic::nc]
            StabInd = int(np.floor(StabTimeSw*Fs/(nr*pq.Hz)))+1
            s = np.mean(chdat[-StabInd:,:],axis=0)
            
            if nr >= 17:
                if ir >= 16:
                    ChName = 'Ch{}Col{}'.format(str(ir-15).zfill(2),str(ColRemap[ic-16]).zfill(2))+'AC'
                else: 
                    ChName = 'Ch{}Col{}'.format(str(ir+1).zfill(2),str(ColRemap[ic]).zfill(2))+'DC'
            else:
                ChName = 'Ch{}Col{}'.format(str(ir+1).zfill(2),str(ColRemap[ic]).zfill(2))+ty
            
            ChNameIV = ChName[:-2]
            
            sig = NeoSignal(s,
                            units='A',
                            sampling_rate=FsCh,
                            name=ChName)

            
            Tchar = FETcl.DataCharDC(DCChar[ChNameIV])

            if sig.name[-2:] == 'AC':
                
                SigDC = CalRecDCCurr.GetSignal(sig.name[:-2]+'DC')
                
                SigDCfilt = (
                            {'function': Rpro.Filter, 'args': {'Type': 'lowpass',
                                                                      'Order': 4,
                                                                      'Freqs': (0.1)}},
                            )
                SigDC.ProcessChain = SigDCfilt

                SigDC = SigDC.GetSignal(Time=(StabTimeIni*pq.s, Tend))

                SigCond1 = (
                            {'function': Rpro.Filter, 'args': {'Type': 'highpass',
                                                                      'Order': 4,
                                                                      'Freqs': (1)}},
                            )
                SigCond2 = ( 
                            {'function': CalcVgeff, 'args': {'Tchar' : Tchar}},
                            {'function': Rpro.Filter, 'args': {'Type': 'highpass',
                                                                      'Order': 4,
                                                                      'Freqs': (1)}},
                            )
                
                sig = sig.copy()
                sig.ProcessChain = SigCond1
                sig = sig.GetSignal(Time=(StabTimeIni*pq.s, Tend))

                Name = sig.name
                sig = sig+SigDC
                sig.name = Name
                sig.ProcessChain = SigCond2
                sig= sig.GetSignal(Time=None)
                CalRecAC.AddSignal(sig)
                                    
                if sig.name == 'Ch04Col08AC':
                    TriggerCh = sig

            elif sig.name[-2:] =='DC':
                
                ProcCal1  =  (
 			                {'function': Rpro.Filter, 'args': {'Type': 'lowpass',
                                                                      'Order': 8,
                                                                      'Freqs': (LPF*pq.Hz)}},
                            {'function': DownSampling, 'args': {'DownFact' : DownFact}}, 
                            )
                ProcCal2  =  (
                            {'function': CalcVgeff, 'args': {'Tchar' : Tchar}},
                            {'function': Rpro.SetZero, 'args': {'TWind': (StabTimeIni*pq.s, StabTimeIni*pq.s+1*pq.s)}},
                            {'function': MedianFilter, 'args':{'WindowSamps': 1+int(2*np.floor(FsCh*MedianFilterTime/((DownFact*SampDrop)*2))),
                                                               'SampDrop':SampDrop}},
                            )
      
                
                sig = sig.GetSignal(Time = (StabTimeIni*pq.s, Tend))
                sigProc = sig.copy()

                sigCurrent = sig.copy()

                
                    
                sigProc.ProcessChain = ProcCal1
                sigCal1= sigProc.GetSignal(Time=None)
                
                sigCal1.ProcessChain = ProcCal2
                sigCal2 = sigCal1.GetSignal(Time=None)
                
                

                CalRecDC.AddSignal(sigCal2)

                
                CalRecDCCurr.AddSignal(sigCurrent)
    
    FullBand = {'DC':CalRecDC,
                'AC':CalRecAC}

    return(FullBand,  TriggerCh)
           
if __name__ == "__main__":
       

 

# %% Settings
    plt.close('all') 
    FileNames = [
                'RawDataExample/B13289O14-DH5-example.h5',

                ]
    DCCharFiles = [
                    'RawDataExample/B13289O14-DH5-IV-example.h5',
                  ]

    for indexx in np.arange(len(FileNames)):
        DCCharFile = DCCharFiles[indexx]
        FileName = FileNames[indexx]
        
        DatFile = 'RawDataExample/DatData/'+'-'.join(FileName.split('/')[1].split('-')[0:3])
        
        Range = {'DC':30e-3,
                 'AC':3e-3,
                 'Clip':4}
        Bits = 16
        
        VdsOp = 0.1
        DownFact = 10
        MedianFilterTime = 200
        LPF = 30
        SampDrop = 60 #samples droped to increase speed of median filter
        Tstab = 20
        Tend = None
        
        ncols = 16
        SampsSwitchPeriod = 3
        StabTimeSw = 20e-6 #in 
        StabTimeIni = 1

        Types = ('AC','DC',)
        
        BrokenTrts = []
        Shortcut = []
    
        
        mpl.rcParams['xtick.labelsize'] = 12
        mpl.rcParams['ytick.labelsize'] = 12
        mpl.rcParams['font.size'] = 12   	
    #%% Map
    
        Rows = {'Ch03': 14,
                'Ch01': 15,
                'Ch07': 12,
                'Ch05': 13,
                'Ch04': 10,
                'Ch02': 11,
                'Ch08': 8,
                'Ch06': 9,
                'Ch14': 6,
                'Ch16': 7,
                'Ch10': 4,
                'Ch12': 5,
                'Ch13': 2,
                'Ch15': 3,
                'Ch09': 0,
                'Ch11': 1}
    
        Cols = {'Col04': 13,#rows of the probe BAD (assuming top to bottom inversion in the omnetics to pin-rack of the discrete electronics (right-left symetry maintained)
                'Col11': 12,
                'Col02': 15,
                'Col09': 14,
                'Col03': 9,
                'Col12': 8,
                'Col01': 11,
                'Col10': 10,
                'Col08': 5,
                'Col14': 4,
                'Col07': 7,
                'Col13': 6,
                'Col05': 1,
                'Col15': 0,
                'Col06': 3,
                'Col16': 2}

        
    
        ChNames = {}
        ind = 0
        for ty in Types:
            for row in sorted(Rows):
                for col in sorted(Cols):
                    ChNames[ind] = row + col + ty
                    ind += 1
            
        ChMap = {}
        for row, vr in Rows.items():
            for col, vc in Cols.items():
                ChMap[row + col] = (vc, vr)
        ChMap['Shape'] = (16, 16)            
    
    #%%    Get IV curves
        DCChar, _ = FETdata.LoadDataFromFile(DCCharFile)
       
    # %% Load demux and calibrate
    
        File = FileName
     
        FullBand, TriggerCh  = LoadDemuxCal(File, StabTimeSw, StabTimeIni, SampsSwitchPeriod,DCChar,MedianFilterTime,LPF, SampDrop, DownFact,Tstab,Tend, Rows,Cols)
        

    #%% Export Neuroscope
        for Coupling in FullBand.keys():
            ChNames = {val:key for (key, val) in FullBand[Coupling].SigNames.items()}
            
            SortMap = np.ndarray([16, 16], dtype=object)
            for key, val in ChMap.items():
                if key == 'Shape':
                    continue
                SortMap[val[1],val[0]] = key
            
            NeuroScopeMap = []       
            for col in SortMap:
                ColName = []
                ColCh = []
                for ch in col:
                    if ch == None:
                        continue
                    ColName.append(ch)
                    ColCh.append(FullBand[Coupling].SigNames['{}{}'.format(ch, Coupling)])
                NeuroScopeMap.append((ColName, ColCh))
            
            print(Coupling)
            print(FullBand.keys())
            ExpDat = FullBand[Coupling].ExportNeuroscope(DatFile+Coupling, Range[Coupling], Bits,'V', ChNames, NeuroScopeMap)
            