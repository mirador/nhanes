'''
# Adds a composite variable to the input data and dictionary, using the provided script

@copyright: Fathom Information Design 2014
'''

import csv
import sys
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from importlib import import_module

mira_path = sys.argv[1]
user_script = sys.argv[2]

overwrite = True
append_str = ""
if len(sys.argv) == 4:
    overwrite = False
    append_str = sys.argv[3]    

work_path = os.getcwd()
[module_path, module_filename] = os.path.split(user_script);

module_path = os.path.abspath(module_path)
module_filename = module_filename.split('.')[0]
sys.path.insert(0, module_path)

module = import_module(module_filename)

try:
    # Changing to script folder just in case it opens some files during initialization
    os.chdir(module_path)
    module.init()
    os.chdir(work_path);
except AttributeError:    
    pass

print "ADDING COMPOSITE " + module.get_name() + " TO MIRADOR DATASET IN " + mira_path + "..."

datafile = mira_path + "/data.tsv"
dictfile = mira_path + "/dictionary.tsv"
grpfile = mira_path + "/groups.xml"
binfile = mira_path + "/data.bin"

if overwrite and os.path.isfile(binfile):
        os.remove(binfile)

if overwrite:
    datafile1 = datafile
    dictfile1 = dictfile
    grpfile1 = grpfile
else:
    datafile1 = mira_path + "/data" + append_str + ".tsv"
    dictfile1 = mira_path + "/dictionary" + append_str + ".tsv"
    grpfile1 = mira_path + "/groups" + append_str + ".xml"

data = []
dict = []
with open(datafile) as tsv:
    for row in csv.reader(tsv, dialect="excel-tab"):        
        data.append(row)
titles = data[0]

variables = module.variables()
var_weights = {}
weight_types = {}
with open(dictfile) as tsv:
    i = 0
    for row in csv.reader(tsv, dialect="excel-tab"):
        # Get the name from the table titles, since the dictionary will contain the aliases
        name = titles[i]
        if len(row) == 4:
            if name in variables:
                var_weights[name] = row[3]
            if row[3] == 'sample weight' or row[3] == 'subsample weight':
                 weight_types[name] = row[3]
        dict.append(row)
        i = i + 1
    
with open(datafile1, "wb") as tsv:
    writer = csv.writer(tsv, dialect="excel-tab")
    titles.append(module.get_name())
    writer.writerow(titles)
    
    for x in range(1, len(data)):
        values = {}
        for var in variables:
            values[var] = data[x][titles.index(var)]
            
        data[x].append(module.calculate(values))
        writer.writerow(data[x])

# Create dictionary entry for the composite variable
dict_entry = [module.get_title()] 
dict_entry.append(module.get_type())
dict_entry.append(module.get_range())
if 0 < len(var_weights):
    # Adding weight variable
    weight = ''
    for var in variables:
        weight1 = var_weights[var]
        if not weight:
            weight = weight1
        else:             
            t0 = weight_types[weight]
            t1 = weight_types[weight1]
            if t0 == 'sample weight' and t1 == 'sample weight' and ('INT' in weight) and ('MEC' in weight1):
                # MEC sample weights have priority over INT weights
                weight = weight1
            elif t0 == 'sample weight' and t1 == 'subsample weight':
                # Subsample weights have priority over sample weights  
                weight = weight1
            elif t0 == 'subsample weight' and t1 == 'subsample weight' and weight != var_weights[var]:
                print "Warning: the composite variable is calculated across different subsamples"
    dict_entry.append(weight)
    
with open(dictfile1, "wb") as tsv:
    writer = csv.writer(tsv, dialect="excel-tab")
    for row in dict: 
        writer.writerow(row)
    writer.writerow(dict_entry)

# Add entry to the groups file
tree = ET.parse(grpfile)
root = tree.getroot()

comp_group = None
for group in root.findall('group'):
    if group.attrib['name'] == 'Composites':
        comp_group = group
        break

# TODO: specify the location to insert the composite group as an argument
if comp_group is None:
    comp_group = ET.Element('group')
    comp_group.set("name", "Composites")
    root.insert(len(root) - 1, comp_group);    

comp_table = None
for table in comp_group.findall('table'):
    if table.attrib['name'] == module.get_table():
        comp_table = table
        break
  
if comp_table is None:
    comp_table = ET.SubElement(comp_group, "table")
    comp_table.set("name", module.get_table())

variable = ET.SubElement(comp_table, "variable")
variable.set("name", module.get_name())

# Prettyfing XML string using BeautifulSoup and writing to file
xml_soup = BeautifulSoup(ET.tostring(root), "xml")
pretty_xml = xml_soup.prettify()
xml_file = open(grpfile1, "w")
xml_file.write(pretty_xml)
xml_file.close()

print "DONE"
