'''
Converts all the XPT files in the specified folder to csv. It
uses R for the conversion, through the RPy2 interface:
http://rpy.sourceforge.net/rpy2_documentation.html
To install rpy2, run from the command line:
easy_install rpy2
The extension tsv is used instead of csv so the files
are automatically opened by libreoffice.

The Hmisc package should be installed in R:
install.packages("Hmisc") (from R)

@copyright: Fathom Information Design 2014
'''

import rpy2.robjects as robjects

import sys, os

xpt_dir = sys.argv[1]
csv_dir = sys.argv[2]

if not os.path.exists(csv_dir):
    os.makedirs(csv_dir)

print "Converting XPT files to CSV..."

robjects.r("library(Hmisc)")
files = os.listdir(xpt_dir)
for f in files:
    xpt_fn = os.path.abspath(os.path.join(xpt_dir, f))
    name_full = os.path.split(f)[1]
    (name_base, name_ext) = os.path.splitext(name_full)
    if name_ext.lower() == '.xpt':
        # Importing XPT file into a data frame and exporting as csv
        robjects.r('file_data <- sasxport.get("' + xpt_fn + '")')
        csv_fn = os.path.abspath(os.path.join(csv_dir, name_base.upper() + ".csv"))        
        try:
            robjects.r('write.csv(file_data, file = "' + csv_fn + '", row.names = FALSE)')
        except:
            print "Error converting " + xpt_fn + " to CSV, skipping."
print "Done."
