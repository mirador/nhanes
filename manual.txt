NHANES DATA SCRIPTS 
===================

This set of Python scripts downloads, parses, and aggregates the public data from the 
National Health and Nutrition Examination Survey (NHANES, 
http://www.cdc.gov/nchs/nhanes.htm), and outputs several files, among them a tsv table
containing all the data aggregated into a single file, and xml files holding the variable
metadata from the online codebooks. The data tsv file together with the dictionary file 
and a xml file with the grouping structure can be used as input for visualization with 
Mirador.


DEPENDENCIES
============

The scripts have the following dependencies:

* Python 2.7.3+ (not tested with 3+) and the following packages:
  - rpy2: http://rpy.sourceforge.net/rpy2_documentation.html 
  - BeautifulSoup: http://www.crummy.com/software/BeautifulSoup
  - Requests: http://docs.python-requests.org/en/latest/index.html  
* R, with Hmisc package
* Windows note: The easy_install for Python on Windows 64bit can be obtained from the 
setuptools package available at http://www.lfd.uci.edu/~gohlke/pythonlibs/


CREATING AND MERGING DATASETS
=============================

The sequence of steps to generate a Mirador-valid dataset is to first download the 
individual data files from the NHANES ftp server, and then run the scripts that parse and 
aggregate these files into a single table. These scripts use the following folder 
structure:

/ root
|
\---- sources
|        |
|        \--- xpt
|        |
|        \--- csv   
|
\---- data
        |
        \--- mirador
               |
               \---- 1999-2000
               |
               \---- 2001-2002
                     ...   

where root is the folder containing all the python scripts and associated files. The raw
data from NHANES is provided in the SAS Transport Files (.xpt), which the download script
stores in sources/xpt. These files are converted into Comma-Separated Values (.csv) files,
which are created in the sources/csv folder. The dataset for each cycle will be stored in
the corresponding subfolder under data/mirador, as shown in the diagram. Consecutive 
cycles can also be aggregated into a single dataset, and the aggregation scripts take 
into account properly merging the sample and subsample weights (see appendix), and also 
the equivalence between variable names across cycles.

1) Downloads the data for a given cycle:
python getdata.py 1999-2000

2) Creates Mirador dataset:
python makedataset.py 1999-2000

3) Creates an aggregated dataset, by merging all the cycles encompassed by the specified
interval:
python mergedatasets.py 1999-2010

4) Finish dataset, by deleting temporary files and adding a Mirador configuration file. 
Once finished, it cannot be used for merging, because the merging scripts use temporary 
files that are removed by this step. The contents of the dataset folder are ready to load
from Mirador:
python finishdataset.py 1999-2010


ADDING COMPOSITE VARIABLES
==========================

Composite variables are defined as function of existing variables in the dataset, and they
can be added by using the composite script and providing a python script that defines the
functional relationship. This script must implement a series of functions to be properly
executed by composite.py, a fully commented template is provided in 
composites/template.py. The result of the calculation can simply overwrite the source 
dataset, or stored in another set of data, dictionary, and grouping files.

1) Adding a composite, overwriting the original dataset
python composite.py data/mirador/1999-2000 composites/obesity.py

2) Adding a composite, without overwriting the original dataset. The new files will be 
called data_obesity.tsv, dictionary_obesity.tsv, and groups_obesity.xml, and stored in the
same dataset folder. 
python composite.py data/mirador/1999-2000 composites/obesity.py _obesity


ADVANCED USE
============

* STEP BY STEP EXECUTION

The getdata, makedataset, and mergedatasets scripts execute several intermediate steps, 
which can be run individually in the case an error occurs and one needs to isolate the 
source of the problem, and also to have more control on the location where the files are
stored, etc. 

1) Download data:
python download.py ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/nhanes/1999-2000 data/sources/xpt/1999-2000

2) Convert to csv:
python xpt2csv.py data/sources/xpt/1999-2000 data/sources/csv/1999-2000

3) Make metadata file, the additional argument -nodetails can be used to disable verbose 
output of messages:
python getweights.py 1999-2000 data/sources/csv/1999-2000 data/mirador/1999-2000/weights.xml
python makemeta.py 1999-2000 Demographics data/sources/csv/1999-2000 data/mirador/1999-2000/demo.xml -nodetails
python makemeta.py 1999-2000 Examination data/sources/csv/1999-2000 data/mirador/1999-2000/exam.xml -nodetails
python makemeta.py 1999-2000 Laboratory data/sources/csv/1999-2000 data/mirador/1999-2000/lab.xml -nodetails
python makemeta.py 1999-2000 Questionnaire data/sources/csv/1999-2000 data/mirador/1999-2000/question.xml -nodetails

4) Validate metadata:
python checkmeta.py data/mirador/1999-2000/weights.xml
python checkmeta.py data/mirador/1999-2000/demo.xml
python checkmeta.py data/mirador/1999-2000/exam.xml
python checkmeta.py data/mirador/1999-2000/lab.xml
python checkmeta.py data/mirador/1999-2000/question.xml

5) Create aggregated data file:
python aggregate.py data/mirador/1999-2000 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv

6) Create dictionary file:
python makedict.py data/mirador/1999-2000 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv dictionary.tsv

7) Create groups file
python makegroups.py data/mirador/1999-2000 demo.xml exam.xml lab.xml question.xml weights.xml groups.xml

8) Check the aggregated file against the original csv files:
python checkdata.py data/mirador/1999-2000 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv

9) Merge metadata from different cycles (and each step updates weights.list):
python mergemeta.py demo.xml 1999-2010 Demographics data/mirador data/mirador/1999-2010 varequiv
python mergemeta.py exam.xml 1999-2010 Examination data/mirador data/mirador/1999-2010 varequiv
python mergemeta.py lab.xml 1999-2010 Laboratory data/mirador data/mirador/1999-2010 varequiv
python mergemeta.py question.xml 1999-2010 Questionnaire data/mirador data/mirador/1999-2010 varequiv

10) Calculate merged weights csv and weights.xml:
python makeweights.py data/mirador/1999-2010 weights.list weights.csv weights.xml

11) Validate merged metadata:
python checkmeta.py data/mirador/1999-2010/weights.xml
python checkmeta.py data/mirador/1999-2010/demo.xml
python checkmeta.py data/mirador/1999-2010/exam.xml
python checkmeta.py data/mirador/1999-2010/lab.xml
python checkmeta.py data/mirador/1999-2010/question.xml

12) Created merged datafiles, using the aggregate script again:
python aggregate.py data/mirador/1999-2010 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv

13) Create dictionary file
python makedict.py data/mirador/1999-2010 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv dict.tsv

14) Create groups file
python makegroups.py data/mirador/1999-2010 demo.xml exam.xml lab.xml question.xml weights.xml groups.xml

15) Check the aggregated merged data against the original csv files.
python checkdata.py data/mirador/1999-2010 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv

* CUSTOM HTML PARSERS

The getweights.py and makemeta.py scripts parse the online NHANES codebooks using the 
BeautifulSoup library, and can use a custom HTML parser, specified the -parser option, 
and chose among the ones listed in the following page: 
http://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
The default is html.parser, the other ones (html5lib, lxml) need to be installed
separately.

* ADDING/REMOVING COMPONENTS

The NHANES components to use in the parsing/aggregation can be set by editing the components
file provide alongside the scripts


APPENDIX
========

1. Relevant links on NHANES weighting:
http://www.cdc.gov/nchs/tutorials/nhanes/SurveyDesign/Weighting/intro.htm
http://www.cdc.gov/nchs/tutorials/NHANES/SurveyDesign/Weighting/OverviewKey.htm
http://www.cdc.gov/nchs/tutorials/NHANES/SurveyDesign/Weighting/OverviewExamples.htm
http://www.cdc.gov/nchs/tutorials/dietary/SurveyOrientation/SurveyDesign/Info2.htm
http://www.cdc.gov/nchs/data/nhanes/analyticnote_2007-2010.pdf
http://www.cdc.gov/nchs/tutorials/nhanes/SurveyDesign/Weighting/Task2.htm
