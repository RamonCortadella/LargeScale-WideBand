README

Code for the acquisition of large-scale and wide-band field potential recordings.

Recent advances in high channel-count sensing technologies have enabled the detection of spiking activity from hundreds of individual units simultaneously. However, mapping of electrophysiological activity across brain-wide cortical networks with high spatial resolution remains challenging due to the limitations in flexible electronics capable of conforming with the brain surface. The code in this repository is related to the publication "Large-scale mapping of spatio-spectral and infra-slow dynamics of local field potential across brain states enabled by graphene neural probes" in which a fully implantable sensing system based on graphene/silicon hybrid electronics for local transduction and multiplexing of brain activity signals is presented. These devices enable large-scale and high-density DC-coupled recordings in the freely-moving rat. The code in this repository is for the operation of the custom built recording system.

INSTALLATION INSTRUCTIONS

Iinstall NI-MAX
https://www.ni.com/en/support/downloads/drivers/download.system-configuration.html#532687

and NI-Daq_mx drivers
https://www.ni.com/en/support/downloads/drivers/download/packaged.ni-daq-mx.532710.html

Open the NI-MAX and check that the Daq-Card is recognized (in the Devices tab)

Install the conda environment in the Res folder
conda env create -f ECoGacq.yml


Launch the GUI for the acquisition of calibration curves by executing the script PyCharMuxGui.py in the PyCharMux folder
go to the bottom of the GUI and load configuration file "ConfigDCsweep-256gfet-v4", change the path and file name, tune the voltage sweep parameters and click "Start"

Launch the GUI for neural data acquisition by executing the script PyTMAcqGUI.py in the PyTimeMux-master folder
go to the bottom of the GUI and load configuration file "TDM-ACDC-256_v4". change the path and file name, tune bias conditions and click "Start". You can also select the channels you want to acquire from and the channels you want to visualize on real time. The displayed signal is expressed in terms of drain to source current. 

To calibrate the signals from current to the equivalent potential at the gate of the graphene transistors, 
