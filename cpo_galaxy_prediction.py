#!/home/jjjjia/.conda/envs/py36/bin/python

#$ -S /home/jjjjia/.conda/envs/py36/bin/python
#$ -V             # Pass environment variables to the job
#$ -N CPO_pipeline    # Replace with a more specific job name
#$ -wd /home/jjjjia/testCases           # Use the current working dir
#$ -pe smp 8      # Parallel Environment (how many cores)
#$ -l h_vmem=11G  # Memory (RAM) allocation *per core*
#$ -e ./logs/$JOB_ID.err
#$ -o ./logs/$JOB_ID.log
#$ -m ea
#$ -M bja20@sfu.ca

#./prediction.py -i ~/testCases/cpoResults/contigs/BC11-Kpn005_S2.fa -m ~/testCases/predictionResultsQsubTest/predictions/BC11-Kpn005_S2.mlst -c ~/testCases/predictionResultsQsubTest/predictions/BC11-Kpn005_S2.recon/contig_report.txt -f ~/testCases/predictionResultsQsubTest/predictions/BC11-Kpn005_S2.recon/mobtyper_aggregate_report.txt -a ~/testCases/predictionResultsQsubTest/predictions/BC11-Kpn005_S2.cp -r ~/testCases/predictionResultsQsubTest/predictions/BC11-Kpn005_S2.rgi.txt -e "Klebsiella"
import subprocess
import pandas
import optparse
import os
import datetime
import sys
import time
import urllib.request
import gzip
import collections
import json
import numpy


debug = False #debug skips the shell scripts and also dump out a ton of debugging messages

if not debug:
    #parses some parameters
    parser = optparse.OptionParser("Usage: %prog [options] arg1 arg2 ...")
    #required
    #MLSTHIT, mobsuite, resfinder, rgi, mlstscheme
    parser.add_option("-i", "--id", dest="id", type="string", help="identifier of the isolate")    
    parser.add_option("-m", "--mlst", dest="mlst", type="string", help="absolute file path to mlst result")
    parser.add_option("-c", "--mobfinderContig", dest="mobfinderContig", type="string", help="absolute path to mobfinder aggregate result")
    parser.add_option("-f", "--mobfinderAggregate", dest="mobfinderAggregate", type="string", help="absolute path to mobfinder plasmid results")
    parser.add_option("-a", "--abricate", dest="abricate", type="string", help="absolute path to abricate results")
    parser.add_option("-r", "--rgi", dest="rgi", type="string", help="absolute path to rgi results")
    parser.add_option("-e", "--expected", dest="expectedSpecies", default="NA/NA/NA", type="string", help="expected species of the isolate")
    parser.add_option("-s", "--mlst-scheme", dest="mlstScheme", default= "./scheme_species_map.tab", type="string", help="absolute file path to mlst scheme")
    parser.add_option("-p", "--plasmidfinder", dest="plasmidfinder", type="string", help="absolute file path to plasmidfinder ")
    parser.add_option("-d", "--mash", dest="mash", type="string", help="absolute file path to mash plasmiddb result")

    #parallelization, useless, these are hard coded to 8cores/64G RAM
    #parser.add_option("-t", "--threads", dest="threads", default=8, type="int", help="number of cpu to use")
    #parser.add_option("-p", "--memory", dest="memory", default=64, type="int", help="memory to use in GB")

    (options,args) = parser.parse_args()
    #if len(args) != 8:
        #parser.error("incorrect number of arguments, all 7 is required")
    curDir = os.getcwd()
    ID = str(options.id).lstrip().rstrip()
    mlst = str(options.mlst).lstrip().rstrip()
    mobfindercontig = str(options.mobfinderContig).lstrip().rstrip()
    mobfinderaggregate = str(options.mobfinderAggregate).lstrip().rstrip()
    abricate = str(options.abricate).lstrip().rstrip()
    rgi = str(options.rgi).lstrip().rstrip()
    expectedSpecies = str(options.expectedSpecies).lstrip().rstrip()
    mlstScheme = str(options.mlstScheme).lstrip().rstrip()
    plasmidfinder = str(options.plasmidfinder).lstrip().rstrip()
    mash = str(options.mash).lstrip().rstrip()
    outputDir = "./"
    print(mlst)
    print(mobfindercontig)
    print(mobfinderaggregate)
    print(abricate)
    print(rgi)
    print(expectedSpecies)
    print(mlstScheme)
    print(mash)

else:
    curDir = os.getcwd()
    ID = "BC11"
    mlst = "D:\OneDrive\ProjectCDC\ProjectCDCInPython\ProjectCDCInPython\pipelineTest\predictions\BC11-Kpn005_S2.mlst"
    mobfindercontig = "D:\OneDrive\ProjectCDC\ProjectCDCInPython\ProjectCDCInPython\pipelineTest\predictions\BC11-Kpn005_S2.recon\contig_report.txt"
    mobfinderaggregate = "D:\OneDrive\ProjectCDC\ProjectCDCInPython\ProjectCDCInPython\pipelineTest\predictions\BC11-Kpn005_S2.recon\mobtyper_aggregate_report.txt"
    abricate = "D:\OneDrive\ProjectCDC\ProjectCDCInPython\ProjectCDCInPython\pipelineTest\predictions\BC11-Kpn005_S2.cp"
    rgi = "D:\OneDrive\ProjectCDC\ProjectCDCInPython\ProjectCDCInPython\pipelineTest\predictions\BC11-Kpn005_S2.rgi.txt"
    expectedSpecies = "Escherichia coli"
    mlstScheme = "D:\OneDrive\ProjectCDC\ProjectCDCInPython\ProjectCDCInPython\pipelineTest\scheme_species_map.tab"
    plasmidfinder = "D:\OneDrive\ProjectCDC\ProjectCDCInPython\ProjectCDCInPython\pipelineTest\predictions\BC11-Kpn005_S2.origins"
    mash = "D:\OneDrive\ProjectCDC\ProjectCDCInPython\ProjectCDCInPython\pipelineTest\predictions\mash.tsv"
    outputDir = "./"

#region result objects
#define some objects to store values from results
#//TODO this is not the proper way of get/set private object variables. every value has manually assigned defaults intead of specified in init(). Also, use property(def getVar, def setVar).
class starFinders(object):
    def __init__(self):
        self.file = ""
        self.sequence = ""
        self.start = 0
        self.end = 0
        self.gene = ""
        self.shortGene = ""
        self.coverage = ""
        self.coverage_map = ""
        self.gaps = ""
        self.pCoverage = 100.00
        self.pIdentity = 100.00
        self.database = ""
        self.accession = ""
        self.product = ""
        self.source = "chromosome"
        self.row = ""

class PlasFlowResult(object):
    def __init__(self):
        self.sequence = ""
        self.length = 0
        self.label = ""
        self.confidence = 0
        self.usefulRow = ""
        self.row = ""

class MlstResult(object):
    def __init__(self):
        self.file = ""
        self.speciesID = ""
        self.seqType = 0
        self.scheme = ""
        self.species = ""
        self.row=""

class mobsuiteResult(object):
    def __init__(self):
        self.file_id = ""
        self.cluster_id	= ""
        self.contig_id	= ""
        self.contig_num = 0
        self.contig_length	= 0
        self.circularity_status	= ""
        self.rep_type	= ""
        self.rep_type_accession = ""	
        self.relaxase_type	= ""
        self.relaxase_type_accession = ""	
        self.mash_nearest_neighbor	 = ""
        self.mash_neighbor_distance	= 0.00
        self.repetitive_dna_id	= ""
        self.match_type	= ""
        self.score	= 0
        self.contig_match_start	= 0
        self.contig_match_end = 0
        self.row = ""

class mobsuitePlasmids(object):
    def __init__(self):
        self.file_id = ""
        self.num_contigs = 0
        self.total_length = 0
        self.gc = ""
        self.rep_types = ""
        self.rep_typeAccession = ""
        self.relaxase_type= ""
        self.relaxase_type_accession	= ""
        self.mpf_type	= ""
        self.mpf_type_accession= ""	
        self.orit_type	= ""
        self.orit_accession	= ""
        self.PredictedMobility	= ""
        self.mash_nearest_neighbor	= ""
        self.mash_neighbor_distance	= 0.00
        self.mash_neighbor_cluster= 0
        self.row = ""

class RGIResult(object):
    def __init__(self):
        self.ORF_ID	= ""
        self.Contig	= ""
        self.Start	= -1
        self.Stop	= -1
        self.Orientation = ""	
        self.Cut_Off	= ""
        self.Pass_Bitscore	= 100000
        self.Best_Hit_Bitscore	= 0.00
        self.Best_Hit_ARO	= ""
        self.Best_Identities	= 0.00
        self.ARO = 0
        self.Model_type	= ""
        self.SNPs_in_Best_Hit_ARO	= ""
        self.Other_SNPs	= ""
        self.Drug_Class	= ""
        self.Resistance_Mechanism	= ""
        self.AMR_Gene_Family	= ""
        self.Predicted_DNA	= ""
        self.Predicted_Protein	= ""
        self.CARD_Protein_Sequence	= ""
        self.Percentage_Length_of_Reference_Sequence	= 0.00
        self.ID	= ""
        self.Model_ID = 0
        self.source = ""
        self.row = ""

class MashResult(object):
    def __init__(self):
        self.size = 0.0
        self.depth = 0.0
        self.identity = 0.0
        self.sharedHashes = ""
        self.medianMultiplicity = 0
        self.pvalue = 0.0
        self.queryID= ""
        self.queryComment = ""
        self.species = ""
        self.row = ""
        self.accession = ""
        self.gcf=""
        self.assembly=""

    def toDict(self): #doesnt actually work
        return dict((name, getattr(self, name)) for name in dir(self) if not name.startswith('__')) 


#endregion

#region useful functions
def read(path):
    return [line.rstrip('\n') for line in open(path)]
def execute(command):
    process = subprocess.Popen(command, shell=False, cwd=curDir, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
        return output
    else:
        raise subprocess.CalledProcessError(exitCode, command)
def httpGetFile(url, filepath=""):
    if (filepath == ""):
        return urllib.request.urlretrieve(url)
    else:
        urllib.request.urlretrieve(url, filepath)
        return True
def gunzip(inputpath="", outputpath=""):
    if (outputpath == ""):
        with gzip.open(inputpath, 'rb') as f:
            gzContent = f.read()
        return gzContent
    else:
        with gzip.open(inputpath, 'rb') as f:
            gzContent = f.read()
        with open(outputpath, 'wb') as out:
            out.write(gzContent)
        return True
def ToJson(dictObject, outputPath):
    #outDir = outputDir + '/summary/' + ID + ".json/"
    #if not (os.path.exists(outDir)):
        #os.makedirs(outDir)
    #with open(outputPath, 'w') as f:
      #json.dump([ob.__dict__ for ob in dictObject.values()], f, ensure_ascii=False)
    return ""
#endregion

#region functions to parse result files
def ParseMLSTResult(pathToMLSTResult, scheme):
    _mlstResult = {}
    scheme = pandas.read_csv(scheme, delimiter='\t', header=0)
    scheme = scheme.replace(numpy.nan, '', regex=True)

    taxon = {}
    #record the scheme as a dictionary
    taxon["-"] = "No MLST Match"
    for i in range(len(scheme.index)):
        key = scheme.iloc[i,0]
        if (str(scheme.iloc[i,2]) == "nan"):
            value = str(scheme.iloc[i,1])
        else:
            value = str(scheme.iloc[i,1]) + " " + str(scheme.iloc[i,2])
        
        if (key in taxon.keys()):
            taxon[key] = taxon.get(key) + ";" + value
        else:
            taxon[key] = value
    #read in the mlst result
    mlst = pandas.read_csv(pathToMLSTResult, delimiter='\t', header=None)
    _mlstHit = MlstResult()

    _mlstHit.file = mlst.iloc[0,0]
    _mlstHit.speciesID = (mlst.iloc[0,1])
    _mlstHit.seqType = str(mlst.iloc[0,2])
    for i in range(3, len(mlst.columns)):
        _mlstHit.scheme += mlst.iloc[0,i] + ";"
    _mlstHit.species = taxon[_mlstHit.speciesID]
    _mlstHit.row = "\t".join(str(x) for x in mlst.ix[0].tolist())
    _mlstResult[_mlstHit.speciesID]=_mlstHit

    return _mlstResult

def ParsePlasmidFinderResult(pathToPlasmidFinderResult):
    #pipelineTest/contigs/BC110-Kpn005.fa	contig00019	45455	45758	IncFIC(FII)_1	8-308/499	========/=.....	8/11	59.52	75.65	plasmidfinder	AP001918	IncFIC(FII)_1__AP001918
    #example resfinder:
    #pipelineTest/contigs/BC110-Kpn005.fa	contig00038	256	1053	OXA-181	1-798/798	===============	0/0	100.00	100.00	bccdc	AEP16366.1	  OXA-48 family carbapenem-hydrolyzing class D beta-lactamase OXA-181 

    _pFinder = {} #***********************
    plasmidFinder = pandas.read_csv(pathToPlasmidFinderResult, delimiter='\t', header=0)
    plasmidFinder = plasmidFinder.replace(numpy.nan, '', regex=True)


    for i in range(len(plasmidFinder.index)):
        pf = starFinders()
        pf.file = str(plasmidFinder.iloc[i,0])
        pf.sequence = str(plasmidFinder.iloc[i,1])
        pf.start = int(plasmidFinder.iloc[i,2])
        pf.end = int(plasmidFinder.iloc[i,3])
        pf.gene = str(plasmidFinder.iloc[i,4])
        pf.shortGene = pf.gene[:pf.gene.index("_")]
        pf.coverage = str(plasmidFinder.iloc[i,5])
        pf.coverage_map = str(plasmidFinder.iloc[i,6])
        pf.gaps = str(plasmidFinder.iloc[i,7])
        pf.pCoverage = float(plasmidFinder.iloc[i,8])
        pf.pIdentity = float(plasmidFinder.iloc[i,9])
        pf.database = str(plasmidFinder.iloc[i,10])
        pf.accession = str(plasmidFinder.iloc[i,11])
        pf.product = str(plasmidFinder.iloc[i,12])
        pf.source = "plasmid"
        pf.row = "\t".join(str(x) for x in plasmidFinder.ix[i].tolist())
        _pFinder[pf.gene]=pf
        #row = "\t".join(str(x) for x in plasmidFinder.ix[i].tolist())
        #plasmidFinderContigs.append(str(plasmidFinder.iloc[i,1]))
        #origins.append(str(plasmidFinder.iloc[i,4][:plasmidFinder.iloc[i,4].index("_")]))
    return _pFinder

def ParseMobsuiteResult(pathToMobsuiteResult):
    _mobsuite = {}
    mResult = pandas.read_csv(pathToMobsuiteResult, delimiter='\t', header=0)
    mResult = mResult.replace(numpy.nan, '', regex=True)

    for i in range(len(mResult.index)):
        mr = mobsuiteResult()
        mr.file_id = str(mResult.iloc[i,0])
        mr.cluster_id = str(mResult.iloc[i,1])
        if (mr.cluster_id == "chromosome"):
            break
        mr.contig_id = str(mResult.iloc[i,2])
        mr.contig_num = mr.contig_id[(mr.contig_id.find("contig")+6):mr.contig_id.find("_len=")]
        mr.contig_length = int(mResult.iloc[i,3])
        mr.circularity_status = str(mResult.iloc[i,4])
        mr.rep_type = str(mResult.iloc[i,5])
        mr.rep_type_accession = str(mResult.iloc[i,6])
        mr.relaxase_type = str(mResult.iloc[i,7])
        mr.relaxase_type_accession = str(mResult.iloc[i,8])
        mr.mash_nearest_neighbor = str(mResult.iloc[i,9])
        mr.mash_neighbor_distance = float(mResult.iloc[i,10])
        mr.repetitive_dna_id = str(mResult.iloc[i,11])
        mr.match_type = str(mResult.iloc[i,12])
        if (mr.match_type == ""):
            mr.score = -1
            mr.contig_match_start = -1
            mr.contig_match_end = -1
        else:
            mr.score = int(mResult.iloc[i,13])
            mr.contig_match_start = int(mResult.iloc[i,14])
            mr.contig_match_end = int(mResult.iloc[i,15])
        mr.row = "\t".join(str(x) for x in mResult.ix[i].tolist())
        _mobsuite[mr.contig_id]=(mr)
    return _mobsuite

def ParseMobsuitePlasmids(pathToMobsuiteResult):
    _mobsuite = {}
    mResults = pandas.read_csv(pathToMobsuiteResult, delimiter='\t', header=0)
    mResults = mResults.replace(numpy.nan, '', regex=True)

    for i in range(len(mResults.index)):
        mr = mobsuitePlasmids()
        mr.file_id = str(mResults.iloc[i,0])
        mr.num_contigs = int(mResults.iloc[i,1])
        mr.total_length = int(mResults.iloc[i,2])
        mr.gc = int(mResults.iloc[i,3])
        mr.rep_types = str(mResults.iloc[i,4])
        mr.rep_typeAccession = str(mResults.iloc[i,5])
        mr.relaxase_type = str(mResults.iloc[i,6])
        mr.relaxase_type_accession = str(mResults.iloc[i,7])
        mr.mpf_type = str(mResults.iloc[i,8])
        mr.mpf_type_accession = str(mResults.iloc[i,9])
        mr.orit_type = str(mResults.iloc[i,10])
        mr.orit_accession = str(mResults.iloc[i,11])
        mr.PredictedMobility = str(mResults.iloc[i,12])
        mr.mash_nearest_neighbor = str(mResults.iloc[i,13])
        mr.mash_neighbor_distance = float(mResults.iloc[i,14])
        mr.mash_neighbor_cluster = int(mResults.iloc[i,15])
        mr.row = "\t".join(str(x) for x in mResults.ix[i].tolist())
        _mobsuite[mr.file_id] = mr
    return _mobsuite

def ParseResFinderResult(pathToResFinderResults, plasmidContigs, likelyPlasmidContigs):
    _rFinder = {}
    resFinder = pandas.read_csv(pathToResFinderResults, delimiter='\t', header=0)
    resFinder = resFinder.replace(numpy.nan, '', regex=True)

    for i in range(len(resFinder.index)):
        rf = starFinders()
        rf.file = str(resFinder.iloc[i,0])
        rf.sequence = str(resFinder.iloc[i,1])
        rf.start = int(resFinder.iloc[i,2])
        rf.end = int(resFinder.iloc[i,3])
        rf.gene = str(resFinder.iloc[i,4])
        rf.shortGene = rf.gene
        rf.coverage = str(resFinder.iloc[i,5])
        rf.coverage_map = str(resFinder.iloc[i,6])
        rf.gaps = str(resFinder.iloc[i,7])
        rf.pCoverage = float(resFinder.iloc[i,8])
        rf.pIdentity = float(resFinder.iloc[i,9])
        rf.database = str(resFinder.iloc[i,10])
        rf.accession = str(resFinder.iloc[i,11])
        rf.product = str(resFinder.iloc[i,12])
        rf.row = "\t".join(str(x) for x in resFinder.ix[i].tolist())
        if (rf.sequence[6:] in plasmidContigs):
            rf.source = "plasmid"
        elif (rf.sequence[6:] in likelyPlasmidContigs):
            rf.source = "likely plasmid"
        else:
            rf.source = "likely chromosome"
        _rFinder[rf.gene]=rf
    return _rFinder

def ParseRGIResult(pathToRGIResults, plasmidContigs, likelyPlasmidContigs):
    _rgiR = {}
    RGI = pandas.read_csv(pathToRGIResults, delimiter='\t', header=0)
    RGI = RGI.replace(numpy.nan, '', regex=True)

    for i in range(len(RGI.index)):
        r = RGIResult()
        r.ORF_ID = str(RGI.iloc[i,0])
        r.Contig = str(RGI.iloc[i,1])
        r.Contig_Num = r.Contig[6:r.Contig.find("_")]
        r.Start = int(RGI.iloc[i,2])
        r.Stop = int(RGI.iloc[i,3])
        r.Orientation = str(RGI.iloc[i,4])
        r.Cut_Off = str(RGI.iloc[i,5])
        r.Pass_Bitscore = int(RGI.iloc[i,6])
        r.Best_Hit_Bitscore = float(RGI.iloc[i,7])
        r.Best_Hit_ARO = str(RGI.iloc[i,8])
        r.Best_Identities = float(RGI.iloc[i,9])
        r.ARO = int(RGI.iloc[i,10])
        r.Model_type = str(RGI.iloc[i,11])
        r.SNPs_in_Best_Hit_ARO = str(RGI.iloc[i,12])
        r.Other_SNPs = str(RGI.iloc[i,13])
        r.Drug_Class = str(RGI.iloc[i,14])
        r.Resistance_Mechanism = str(RGI.iloc[i,15])
        r.AMR_Gene_Family = str(RGI.iloc[i,16])
        r.Predicted_DNA = str(RGI.iloc[i,17])
        r.Predicted_Protein = str(RGI.iloc[i,18])
        r.CARD_Protein_Sequence = str(RGI.iloc[i,19])
        r.Percentage_Length_of_Reference_Sequence = float(RGI.iloc[i,20])
        r.ID = str(RGI.iloc[i,21])
        r.Model_ID = int(RGI.iloc[i,22])
        r.row = "\t".join(str(x) for x in RGI.ix[i].tolist())
        if (r.Contig_Num in plasmidContigs):
            r.source = "plasmid"
        elif (r.Contig_Num in likelyPlasmidContigs):
            r.source = "likely plasmid"
        else:
            r.source = "likely chromosome"
        _rgiR[r.Model_ID]=r
    return _rgiR

def ParsePlasmidFinderResult(pathToPlasmidFinderResult):
    #pipelineTest/contigs/BC110-Kpn005.fa	contig00019	45455	45758	IncFIC(FII)_1	8-308/499	========/=.....	8/11	59.52	75.65	plasmidfinder	AP001918	IncFIC(FII)_1__AP001918
    #example resfinder:
    #pipelineTest/contigs/BC110-Kpn005.fa	contig00038	256	1053	OXA-181	1-798/798	===============	0/0	100.00	100.00	bccdc	AEP16366.1	  OXA-48 family carbapenem-hydrolyzing class D beta-lactamase OXA-181 

    _pFinder = {} #***********************
    plasmidFinder = pandas.read_csv(pathToPlasmidFinderResult, delimiter='\t', header=0)

    for i in range(len(plasmidFinder.index)):
        pf = starFinders()
        pf.file = str(plasmidFinder.iloc[i,0])
        pf.sequence = str(plasmidFinder.iloc[i,1])
        pf.start = int(plasmidFinder.iloc[i,2])
        pf.end = int(plasmidFinder.iloc[i,3])
        pf.gene = str(plasmidFinder.iloc[i,4])
        if (pf.gene.find("_") > -1):
            pf.shortGene = pf.gene[:pf.gene.index("_")]
        else:
            pf.shortGene = pf.gene
        pf.coverage = str(plasmidFinder.iloc[i,5])
        pf.coverage_map = str(plasmidFinder.iloc[i,6])
        pf.gaps = str(plasmidFinder.iloc[i,7])
        pf.pCoverage = float(plasmidFinder.iloc[i,8])
        pf.pIdentity = float(plasmidFinder.iloc[i,9])
        pf.database = str(plasmidFinder.iloc[i,10])
        pf.accession = str(plasmidFinder.iloc[i,11])
        pf.product = str(plasmidFinder.iloc[i,12])
        pf.source = "plasmid"
        pf.row = "\t".join(str(x) for x in plasmidFinder.ix[i].tolist())
        _pFinder[pf.gene]=pf
        #row = "\t".join(str(x) for x in plasmidFinder.ix[i].tolist())
        #plasmidFinderContigs.append(str(plasmidFinder.iloc[i,1]))
        #origins.append(str(plasmidFinder.iloc[i,4][:plasmidFinder.iloc[i,4].index("_")]))
    return _pFinder

def ParseMashResult(pathToMashScreen):
    mashScreen = pandas.read_csv(pathToMashScreen, delimiter='\t', header=None)

    _mashPlasmidHits = {} #***********************
    #parse what the species are.
    for i in (range(len(mashScreen.index))):
        mr = MashResult()
        mr.identity = float(mashScreen.ix[i, 0])
        mr.sharedHashes = mashScreen.ix[i, 1]
        mr.medianMultiplicity = int(mashScreen.ix[i, 2])
        mr.pvalue = float(mashScreen.ix[i, 3])
        mr.name = mashScreen.ix[i, 4] #accession
        mr.row = "\t".join(str(x) for x in mashScreen.ix[i].tolist())
        _mashPlasmidHits[mr.name] = mr
    return _mashPlasmidHits
#endregion

def Main():
    outputDir = "./"
    notes = []
    #init the output list
    output = []
    jsonOutput = []

    print(str(datetime.datetime.now()) + "\n\nID: " + ID + "\nAssembly: " + ID)
    output.append(str(datetime.datetime.now()) + "\n\nID: " + ID + "\nAssembly: " + ID)

    #region parse the mlst results
    print("step 3: parsing mlst, plasmid, and amr results")
    
    print("identifying MLST")    
    mlstHit = ParseMLSTResult(mlst, str(mlstScheme))#***********************
    ToJson(mlstHit, "mlst.json") #write it to a json output
    mlstHit = list(mlstHit.values())[0]

    #endregion

    #region parse mobsuite, resfinder and rgi results
    print("identifying plasmid contigs and amr genes")

    plasmidContigs = []
    likelyPlasmidContigs = []
    origins = []

    #parse mobsuite results
    mSuite = ParseMobsuiteResult(mobfindercontig) #outputDir + "/predictions/" + ID + ".recon/contig_report.txt")#*************
    ToJson(mSuite, "mobsuite.json") #*************
    mSuitePlasmids = ParseMobsuitePlasmids(mobfinderaggregate)#outputDir + "/predictions/" + ID + ".recon/mobtyper_aggregate_report.txt")#*************
    ToJson(mSuitePlasmids, "mobsuitePlasmids.json") #*************

    for key in mSuite:
        if mSuite[key].contig_num not in plasmidContigs and mSuite[key].contig_num not in likelyPlasmidContigs:
            if not (mSuite[key].rep_type == ''):
                plasmidContigs.append(mSuite[key].contig_num)
            else:
                likelyPlasmidContigs.append(mSuite[key].contig_num)
    for key in mSuite:
        if mSuite[key].rep_type not in origins:
            origins.append(mSuite[key].rep_type)

    #parse resfinder AMR results
    pFinder = ParsePlasmidFinderResult(plasmidfinder)
    ToJson(pFinder, "origins.json")

    rFinder = ParseResFinderResult(abricate, plasmidContigs, likelyPlasmidContigs)#outputDir + "/predictions/" + ID + ".cp", plasmidContigs, likelyPlasmidContigs) #**********************
    ToJson(rFinder, "resfinder.json") #*************

    rgiAMR = ParseRGIResult(rgi, plasmidContigs, likelyPlasmidContigs) # outputDir + "/predictions/" + ID + ".rgi.txt", plasmidContigs, likelyPlasmidContigs)#***********************
    ToJson(rgiAMR, "rgi.json") #*************

    plasmidFamily = ParseMashResult(mash)
    ToJson(plasmidFamily, "mash.json")

    carbapenamases = [] 
    resfinderCarbas = [] #list of rfinder objects for lindaout list
    amrGenes = []
    for keys in rFinder:
        carbapenamases.append(rFinder[keys].shortGene + "(" + rFinder[keys].source + ")")
        resfinderCarbas.append(rFinder[keys])
    for keys in rgiAMR:
        if (rgiAMR[keys].Drug_Class.find("carbapenem") > -1 and rgiAMR[keys].AMR_Gene_Family.find("beta-lactamase") > -1):
            if ((rgiAMR[keys].Best_Hit_ARO+ "(" + rgiAMR[keys].source + ")") not in carbapenamases):
                carbapenamases.append(rgiAMR[keys].Best_Hit_ARO+ "(" + rgiAMR[keys].source + ")")
        else:
            if ((rgiAMR[keys].Best_Hit_ARO+ "(" + rgiAMR[keys].source + ")") not in amrGenes):
                amrGenes.append(rgiAMR[keys].Best_Hit_ARO+ "(" + rgiAMR[keys].source + ")")
    #endregion

    #region output parsed mlst information
    print("formatting mlst outputs")
    output.append("\n\n\n~~~~~~~MLST summary~~~~~~~")
    output.append("MLST determined species: " + mlstHit.species)
    output.append("\nMLST Details: ")
    output.append(mlstHit.row)

    output.append("\nMLST information: ")
    if (mlstHit.species == expectedSpecies):
        output.append("MLST determined species is the same as expected species")
        #notes.append("MLST determined species is the same as expected species")
    else:
        output.append("!!!MLST determined species is NOT the same as expected species, contamination? mislabeling?")
        notes.append("MLST: Not expected species. Possible contamination or mislabeling")

    #endregion

    #region output the parsed plasmid/amr results
    output.append("\n\n\n~~~~~~~~Plasmids~~~~~~~~\n")
    
    output.append("predicted plasmid origins: ")
    output.append(";".join(origins))

    output.append("\ndefinitely plasmid contigs")
    output.append(";".join(plasmidContigs))
    
    output.append("\nlikely plasmid contigs")
    output.append(";".join(likelyPlasmidContigs))

    output.append("\nmob-suite prediction details: ")
    for key in mSuite:
        output.append(mSuite[key].row)

    output.append("\n\n\n~~~~~~~~AMR Genes~~~~~~~~\n")
    output.append("predicted carbapenamase Genes: ")
    output.append(",".join(carbapenamases))
    output.append("other RGI AMR Genes: ")
    for key in rgiAMR:
        output.append(rgiAMR[key].Best_Hit_ARO + "(" + rgiAMR[key].source + ")")

    output.append("\nDetails about the carbapenamase Genes: ")
    for key in rFinder:
        output.append(rFinder[key].row)
    output.append("\nDetails about the RGI AMR Genes: ")
    for key in rgiAMR:
        output.append(rgiAMR[key].row)

    #write summary to a file
    summaryDir = outputDir + "/summary/" + ID
    out = open("summary.txt", 'w')
    for item in output:
        out.write("%s\n" % item)


    #TSV output
    lindaOut = []
    tsvOut = []
    lindaOut.append("ID\tQUALITY\tExpected Species\tMLST Scheme\tSequence Type\tMLST_ALLELE_1\tMLST_ALLELE_2\tMLST_ALLELE_3\tMLST_ALLELE_4\tMLST_ALLELE_5\tMLST_ALLELE_6\tMLST_ALLELE_7\tSEROTYPE\tK_CAPSULE\tPLASMID_2_RFLP\tPLASMID_1_FAMILY\tPLASMID_1_BEST_MATCH\tPLASMID_1_COVERAGE\tPLASMID_1_SNVS_TO_BEST_MATCH\tPLASMID_1_CARBAPENEMASE\tPLASMID_1_INC_GROUP\tPLASMID_2_RFLP\tPLASMID_2_FAMILY\tPLASMID_2_BEST_MATCH\tPLASMID_2_COVERAGE\tPLASMID_2_SNVS_TO_BEST_MATCH\tPLASMID_2_CARBAPENEMASE\tPLASMID_2_INC_GROUP")
    lindaTemp = ID + "\t" #id
    lindaTemp += "\t" #quality
    lindaTemp += expectedSpecies + "\t" #expected
    lindaTemp += mlstHit.species + "\t" #mlstscheme
    lindaTemp += str(mlstHit.seqType)  + "\t" #seq type
    lindaTemp += "\t".join(mlstHit.scheme.split(";")) + "\t"#mlst alleles x 7
    lindaTemp += "\t\t" #sero and kcap
    
    #resfinderCarbas
    index = 0
    for carbs in resfinderCarbas:
        if (carbs.source == "plasmid"): #
            lindaTemp += "\t"
            plasmid = plasmidFamily[list(plasmidFamily.keys())[index]]
            lindaTemp += plasmid.name + "\t"
            lindaTemp += str(plasmid.identity) + "\t"
            lindaTemp += plasmid.sharedHashes + "\t"
            lindaTemp += carbs.shortGene + "\t" #found an carbapenase
            contig = carbs.sequence[6:] #this is the contig number
            for i in mSuite.keys():
                if (str(mSuite[i].contig_num) == str(contig)): #found the right plasmid
                    clusterid = mSuite[i].cluster_id
                    rep_types = mSuitePlasmids["plasmid_" + str(clusterid) + ".fasta"].rep_types
                    lindaTemp += rep_types
    lindaOut.append(lindaTemp)
    out = open("summary.linda.tsv", 'w')
    for item in lindaOut:
        out.write("%s\n" % item)

    tsvOut.append("new\tID\tExpected Species\tMLST Species\tSequence Type\tMLST Scheme\tCarbapenem Resistance Genes\tOther AMR Genes\tPlasmid Best Match\tPlasmid Identity\tPlasmid Shared Hash\tTotal Plasmids\tPlasmids ID\tNum_Contigs\tPlasmid Length\tPlasmid RepType\tPlasmid Mobility\tNearest Reference\tDefinitely Plasmid Contigs\tLikely Plasmid Contigs")
    #start with ID
    temp = "\t"
    temp += (ID + "\t")
    temp += expectedSpecies + "\t"

    #move into MLST
    temp += mlstHit.species + "\t"
    temp += str(mlstHit.seqType) + "\t"
    temp += mlstHit.scheme + "\t"
    
    #now onto AMR genes
    temp += ";".join(carbapenamases) + "\t"
    temp += ";".join(amrGenes) + "\t"

    #lastly plasmids
    temp += str(plasmidFamily[list(plasmidFamily.keys())[0]].name) + "\t"
    temp += str(plasmidFamily[list(plasmidFamily.keys())[0]].identity) + "\t"
    temp += str(plasmidFamily[list(plasmidFamily.keys())[0]].sharedHashes) + "\t"
    temp+= str(len(mSuitePlasmids)) + "\t"
    plasmidID = ""
    contigs = ""
    lengths = ""
    rep_type = ""
    mobility = ""
    neighbour = ""
    for keys in mSuitePlasmids:
        plasmidID += str(mSuitePlasmids[keys].mash_neighbor_cluster) + ";"
        contigs += str(mSuitePlasmids[keys].num_contigs) + ";"
        lengths += str(mSuitePlasmids[keys].total_length) + ";"
        rep_type += str(mSuitePlasmids[keys].rep_types) + ";"
        mobility += str(mSuitePlasmids[keys].PredictedMobility) + ";"
        neighbour += str(mSuitePlasmids[keys].mash_nearest_neighbor) + ";"
    temp += plasmidID + "\t" + contigs + "\t" + lengths + "\t" + rep_type + "\t" + mobility + "\t" + neighbour + "\t"
    temp += ";".join(plasmidContigs) + "\t"
    temp += ";".join(likelyPlasmidContigs)
    tsvOut.append(temp)

    summaryDir = outputDir + "/summary/" + ID
    out = open("summary.tsv", 'w')
    for item in tsvOut:
        out.write("%s\n" % item)
    #endregion


start = time.time()#time the analysis
print("Starting workflow...")
#analysis time
Main()

end = time.time()
print("Finished!\nThe analysis used: " + str(end-start) + " seconds")