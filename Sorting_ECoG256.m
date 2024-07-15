close('all')


LFPFs = 651.04166667;
DownFact = 10;
Tstab = 60; 

Directory = pwd;

d = dir(strcat(Directory, '/B13289O14-DH2-Rec3*AC.dat'));%DC-LP30Hz-Notch50-100Hz.dat');
Par =  LoadXml([Directory '/B13289O14-DH5-Rec5ChMirrored-ColsMirrored' 'AC.xml']);



%% get ephys data
ACLfp = [];
DCLfp = [];
ClipLfp = [];

for fn = 1:length(d)
    FileName = [d(fn).folder ,'/',d(fn).name(1:end-6)];
    ACLfp = LoadBinaryDAT([FileName 'AC.lfp'], [0:255], Par.nChannels,1)';
    DCLfp = LoadBinaryDAT([FileName 'DC.lfp'], [0:255], Par.nChannels,1)';
    LfpGeom = zeros([size(ACLfp)]);
    %rearrange channels
    LfpGeomDC = zeros([size(DCLfp)]);

    for i = 1:length(Par.AnatGrps)
        for ii = 1:length(Par.AnatGrps(i).Channels)
            display(ii,'Ch')
            display(fn,'File Number')
            LfpGeom(:,ii+(i-1)*16) = ACLfp(:,Par.AnatGrps(i).Channels(ii)+1);
            LfpGeomDC(:,ii+(i-1)*16) = DCLfp(:,Par.AnatGrps(i).Channels(ii)+1);   
        end
    end
    NameParts = split(d(fn).name,'-');
    rec = NameParts{3}(1:end-10);
    SaveName = ['Sorted/' NameParts{1} '-' NameParts{2} '-' rec];
    SaveBinary(strcat(SaveName,'-AC.lfp'), LfpGeom)
    SaveBinary(strcat(SaveName,'-DC.lfp'), LfpGeomDC)
end
   