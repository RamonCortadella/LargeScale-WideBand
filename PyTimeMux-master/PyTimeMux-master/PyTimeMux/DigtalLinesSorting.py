# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 14:14:07 2020

@author: user
"""

HwMap = {'aiChannels': {'Ch01': ('ai0', 'ai8'),
                                  'Ch02': ('ai1', 'ai9'),
                                  'Ch03': ('ai2', 'ai10'),
                                  'Ch04': ('ai3', 'ai11'),
                                  'Ch05': ('ai4', 'ai12'),
                                  'Ch06': ('ai5', 'ai13'),
                                  'Ch07': ('ai6', 'ai14'),
                                  'Ch08': ('ai7', 'ai15'),
                                  'Ch09': ('ai16', 'ai24'),
                                  'Ch10': ('ai17', 'ai25'),
                                  'Ch11': ('ai18', 'ai26'),
                                  'Ch12': ('ai19', 'ai27'),
                                  'Ch13': ('ai20', 'ai28'),
                                  'Ch14': ('ai21', 'ai29'),
                                  'Ch15': ('ai22', 'ai30'),
                                  'Ch16': ('ai23', 'ai31')},

                   'aoChannels': {'ChVs': 'ao1',
                                  'ChVds': 'ao0',
                                  'ChAo2': None,
                                  'ChAo3': None, },

        'ColOuts': {'Col01': ('line1', ),
                    'Col02': ('line2', ),
                    'Col03': ('line3', ),
                    'Col04': ('line0', ),
                    'Col05': ('line5', ),
                    'Col06': ('line7', ),
                    'Col07': ('line6', ),
                    'Col08': ('line4', ),
                    'Col09': ('line8', ),
                    'Col10': ('line11', ),
                    'Col11': ('line10', ),
                    'Col12': ('line9', ),
                    'Col13': ('line12', ),
                    'Col14': ('line15', ),
                    'Col15': ('line14', ),
                    'Col16': ('line13', ),
                    }, }

import numpy as np

# samples per column
nSampsCo = 3

# hardware mapping
doColumns = HwMap['ColOuts']

# columns to Mux
DigColumns = (
                'Col01',
                'Col03',
                'Col04',
                )

## function implementation
## def SetDigitalOutputs(self, nSampsCo):

IndexDigitalLines = {}
hwLinesMap = {}
i = 0
for ColName, hwLine in doColumns.items():
    print(ColName)
    il = int(hwLine[0][4:])
    hwLinesMap[il] = (ColName, hwLine)

j = 0
NewInd = {}
for i, c in sorted(hwLinesMap.items()):
    for n in DigColumns:
        if n == c[0]:
            NewInd[j] = c[0]
            j += 1

# Gen inverted control output, should be the next one of the digital line ('lineX', 'lineX+1')
if len(doColumns[ColName]) > 1:
    GenInvert = True
else:
    GenInvert = False

# GenInvert = False

# Gen sorted indexes for demuxing
SortIndDict = {}
for ic, coln in enumerate(sorted(DigColumns)):
    SortIndDict[coln] = ic

DOut = np.array([], dtype=np.bool)
SortDInds = np.zeros((len(DigColumns), nSampsCo), dtype=np.int8)
SwitchOrder = 0
for il, (nLine, (LineName, hwLine)) in enumerate(sorted(hwLinesMap.items())):
    Lout = np.zeros((1, nSampsCo*len(DigColumns)), dtype=np.bool)    
    if LineName in DigColumns:
        print(il, nLine, hwLine, LineName)
        Lout[0, nSampsCo * SwitchOrder: nSampsCo * (SwitchOrder + 1)] = True
        SortDInds[SortIndDict[LineName], : ] = np.arange(nSampsCo * SwitchOrder,
                                                     nSampsCo * (SwitchOrder + 1) )
        SwitchOrder += 1
    
    if GenInvert:
        Cout = np.vstack((Lout, ~Lout))
    else:
        Cout = Lout        
    DOut = np.vstack((DOut, Cout)) if DOut.size else Cout

    
# # Vigila amb el sorting dels canal per demux... segurament dependrà de l'ordre de les lines

# if GenInvert:
#     for line in DOut[0:-1:2, :]:
#         if True in line:
#             SortDInds.append(np.where(line))
# else:
#     for line in DOut:
#         if True in line:
#             SortDInds.append(np.where(line))

SortDIndsL = [inds for inds in SortDInds]
    

Dout = DOut.astype(np.uint8)
