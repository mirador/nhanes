## NHANES DATA SCRIPTS 

This set of Python scripts downloads, parses, and aggregates the public data from the [National Health and Nutrition Examination Survey](http://www.cdc.gov/nchs/nhanes.htm) (NHANES), and outputs several files, among them a tsv table containing all the data aggregated into a single file, and xml files holding the variable metadata from the online codebooks. The data tsv file together with the dictionary file and a xml file with the grouping structure can be used as input for visualization with Mirador.

### DEPENDENCIES

The scripts have the following dependencies:

1. Python 3.7 or higher (not compatible with 2.x, tested with 3.7.5) and the following packages:
  * rpy2: http://rpy.sourceforge.net/rpy2_documentation.html 
  * BeautifulSoup: http://www.crummy.com/software/BeautifulSoup
  * Requests: http://docs.python-requests.org/en/latest/index.html
  * lxml: https://lxml.de/
  * These dependencies can be installed by running:<br> 
  `pip install -r requirements.txt`
2. [R](https://www.r-project.org/) (tested with version 3.6.1), and the Hmisc package: https://cran.r-project.org/web/packages/Hmisc/index.html
3. A convenient way to install all of the software tools mentioned above is through the [Anaconda Python/R distribution](https://www.anaconda.com/distribution/), or with the minimal version of Anaconda, called [Miniconda](https://docs.conda.io/en/latest/miniconda.html). In the latter case, you will still have to run `pip install -r requirements.txt` to install the additional Python dependencies (not included in Miniconda), as well as R and hmisc manually, which can be easily done with the conda package management tool included with Miniconda. This involves running the two following commands:<br>
`conda install r-core`<br>
`conda install r-hmisc`

### CREATING AND MERGING DATASETS

The sequence of steps to generate a Mirador-valid dataset is to first download the  individual data files from the NHANES ftp server, and then run the scripts that parse and  aggregate these files into a single table. These scripts use the following folder structure:

```
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
```

where root is the folder containing all the python scripts and associated files. The raw data from NHANES is provided in the SAS Transport Files (.xpt), which the download script stores in sources/xpt. These files are converted into Comma-Separated Values (.csv) files, which are created in the sources/csv folder. The dataset for each cycle will be stored in the corresponding subfolder under data/mirador, as shown in the diagram. Consecutive cycles can also be aggregated into a single dataset, and the aggregation scripts take  into account properly merging the sample and subsample weights (see appendix), and also the equivalence between variable names across cycles.

**1)** Downloads the data for a given cycle:

```bash
python getdata.py 1999-2000
```

**2)** Creates Mirador dataset:

```bash
python makedataset.py 1999-2000
```

**3)** Creates an aggregated dataset, by merging all the cycles encompassed by the specified
interval:

```bash
python mergedatasets.py 1999-2010
```

**4)** Finish dataset, by deleting temporary files and adding a Mirador configuration file. Once finished, it cannot be used for merging, because the merging scripts use temporary  files that are removed by this step. The contents of the dataset folder are ready to load from Mirador:

```bash
python finishdataset.py 1999-2010
```

If the temporary files are needed to redo merging operations, once can add the -keep 
parameter:

```bash
python finishdataset.py 1999-2010 -keep
```

### ADDING COMPOSITE VARIABLES

Composite variables are defined as function of existing variables in the dataset, and they can be added by using the composite script and providing a python script that defines the functional relationship. This script must implement a series of functions to be properly executed by composite.py, a fully commented template is provided in composites/template.py. The result of the calculation can simply overwrite the source  dataset, or stored in another set of data, dictionary, and grouping files.

**1)** Adding a composite, overwriting the original dataset

```bash
python composite.py data/mirador/1999-2000 composites/obesity.py
```

**2)** Adding a composite, without overwriting the original dataset. The new files will be 
called data_obesity.tsv, dictionary_obesity.tsv, and groups_obesity.xml, and stored in the
same dataset folder. 

```bash
python composite.py data/mirador/1999-2000 composites/obesity.py _obesity
```

### ADVANCED USE

#### STEP BY STEP EXECUTION

The getdata, makedataset, and mergedatasets scripts execute several intermediate steps, which can be run individually in the case an error occurs and one needs to isolate the  source of the problem, and also to have more control on the location where the files are stored, etc. 

**1)** Download data:

```bash
python download.py 1999-2000 data/sources/xpt/1999-2000
```

**2)** Convert to csv:

```bash
python xpt2csv.py data/sources/xpt/1999-2000 data/sources/csv/1999-2000
```

An alternative to use the provided xpt2csv script, which internall calls R to read the xpt files and then save them as csv is to use the [xport reader/writer for Python](https://pypi.org/project/xport/).

**3)** Make metadata file, the additional argument -nodetails can be used to disable verbose 
output of messages:

```bash
python getweights.py 1999-2000 data/sources/csv/1999-2000 data/mirador/1999-2000/weights.xml
python makemeta.py 1999-2000 Demographics data/sources/csv/1999-2000 data/mirador/1999-2000/demo.xml -nodetails
python makemeta.py 1999-2000 Examination data/sources/csv/1999-2000 data/mirador/1999-2000/exam.xml -nodetails
python makemeta.py 1999-2000 Laboratory data/sources/csv/1999-2000 data/mirador/1999-2000/lab.xml -nodetails
python makemeta.py 1999-2000 Questionnaire data/sources/csv/1999-2000 data/mirador/1999-2000/question.xml -nodetails
```

Also, make sure of creating the mirador data folder, as these scripts will not create it if it is missing. In this case, the path would be `data/mirador/1999-2000`.

**4)** Validate metadata:

```bash
python checkmeta.py data/mirador/1999-2000/weights.xml
python checkmeta.py data/mirador/1999-2000/demo.xml
python checkmeta.py data/mirador/1999-2000/exam.xml
python checkmeta.py data/mirador/1999-2000/lab.xml
python checkmeta.py data/mirador/1999-2000/question.xml
```

**5)** Create aggregated data file:

```bash
python aggregate.py data/mirador/1999-2000 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv
```

**6)** Create dictionary file:

```bash
python makedict.py data/mirador/1999-2000 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv dictionary.tsv
```

**7)** Create groups file

```bash
python makegroups.py data/mirador/1999-2000 demo.xml exam.xml lab.xml question.xml weights.xml groups.xml
```

**8)** Check the aggregated file against the original csv files:

```bash
python checkdata.py data/mirador/1999-2000 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv
```

**9)** Merge metadata from different cycles (and each step updates weights.list):

```bash
python mergemeta.py demo.xml 1999-2010 Demographics data/mirador data/mirador/1999-2010 varequiv
python mergemeta.py exam.xml 1999-2010 Examination data/mirador data/mirador/1999-2010 varequiv
python mergemeta.py lab.xml 1999-2010 Laboratory data/mirador data/mirador/1999-2010 varequiv
python mergemeta.py question.xml 1999-2010 Questionnaire data/mirador data/mirador/1999-2010 varequiv
```

**10)** Calculate merged weights csv and weights.xml:

```bash
python makeweights.py data/mirador/1999-2010 weights.list weights.csv weights.xml
```

**11)** Validate merged metadata:

```bash
python checkmeta.py data/mirador/1999-2010/weights.xml
python checkmeta.py data/mirador/1999-2010/demo.xml
python checkmeta.py data/mirador/1999-2010/exam.xml
python checkmeta.py data/mirador/1999-2010/lab.xml
python checkmeta.py data/mirador/1999-2010/question.xml
```

**12)** Created merged datafiles, using the aggregate script again:

```bash
python aggregate.py data/mirador/1999-2010 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv
```

**13)** Create dictionary file

```bash
python makedict.py data/mirador/1999-2010 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv dict.tsv
```

**14)** Create groups file

```bash
python makegroups.py data/mirador/1999-2010 demo.xml exam.xml lab.xml question.xml weights.xml groups.xml
```

**15)** Check the aggregated merged data against the original csv files.

```bash
python checkdata.py data/mirador/1999-2010 demo.xml lab.xml exam.xml question.xml weights.xml data.tsv
```

#### CUSTOM HTML PARSERS

The getweights.py and makemeta.py scripts parse the online NHANES codebooks using the  BeautifulSoup library, and can use a custom HTML parser, specified the -parser option, and chose among the ones listed in [this page](http://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser). The default is html.parser, the other ones (html5lib, lxml) need to be installed separately.

#### ADDING/REMOVING COMPONENTS

The NHANES components to use in the parsing/aggregation can be set by editing the components file provide alongside the scripts

### APPENDIX

**1)** Relevant links on NHANES weighting:

* [Introduction to Specifying Weighting Parameters](http://www.cdc.gov/nchs/tutorials/nhanes/SurveyDesign/Weighting/intro.htm)
* [Key Concepts About Weighting in NHANES](http://www.cdc.gov/nchs/tutorials/NHANES/SurveyDesign/Weighting/OverviewKey.htm)
* [Examples Demonstrating Importance of Using Weights](http://www.cdc.gov/nchs/tutorials/NHANES/SurveyDesign/Weighting/OverviewExamples.htm)
* [Key Concepts About the NHANES Sample Weights](http://www.cdc.gov/nchs/tutorials/dietary/SurveyOrientation/SurveyDesign/Info2.htm)
* [2007-2010 Survey Design Changes and Combining Data Across other Survey Cycles](http://www.cdc.gov/nchs/data/nhanes/analyticnote_2007-2010.pdf)
* [When and How to Construct Weights When Combining Survey Cycles](http://www.cdc.gov/nchs/tutorials/nhanes/SurveyDesign/Weighting/Task2.htm)
