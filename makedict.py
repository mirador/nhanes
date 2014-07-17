'''
Creates the dictionary file from the input metadata

@copyright: Fathom Information Design 2014
@author: Andres Colubri 
'''

import sys, os, csv, math
import xml.etree.ElementTree as ET

def get_variables(xml, var_names, var_aliases, var_types, var_ranges, var_weights):
    vname = ""
    valias = ""    
    vtype = ""
    vrange = ""
    vweight = ""
    
    if xml.attrib["weight"] == "yes":
        if xml.attrib["subsample"] == "yes":
            vweight = "subsample weight"
        else:
            vweight = "sample weight"
    
    for child in xml:
        if child.tag == "short":
            vname = child.text
        if child.tag == "full":
            valias = child.text
        if child.tag == "type":        
            vtype = child.text
            if vtype == "integer": vtype = "int"
        if child.tag == "range":
            vrange = child.text
        if child.tag == "weight":
            vweight = child.text

    if vname != "":
        var_names.append(vname)
        var_aliases[vname] = valias
        var_types[vname] = vtype
        var_ranges[vname] = vrange
        var_weights[vname] = vweight

argc = len(sys.argv)
data_folder = sys.argv[1]
in_metadata = sys.argv[2:argc - 2]
data_file = sys.argv[argc - 2]
dict_file = sys.argv[argc - 1]

print "Loading data..."
data_filename = os.path.abspath(os.path.join(data_folder, data_file))
csv_file = open(data_filename, 'rb')
csv_reader = csv.reader(csv_file, delimiter='\t', quotechar='"')
title_row = csv_reader.next()
csv_file.close()                  
print "Done."

print "Loading metadata..."
var_names = []
var_aliases = {}
var_types = {}  
var_ranges = {}
var_weights = {}

for meta in in_metadata:
    xml_filename = os.path.abspath(os.path.join(data_folder, meta))  
    tree = ET.parse(xml_filename)
    root = tree.getroot()
    for el in root:
        if (el.tag == "table"):
          if el.attrib["include"] != "yes": continue          
          for child in el: 
              if child.tag == "var":
                  if child.attrib["include"] == "yes":
                      get_variables(child, var_names, var_aliases, var_types, var_ranges, var_weights)
print "Done."

print "Creating dictionary file..."
dict_filename = os.path.abspath(os.path.join(data_folder, dict_file))
dfile = open(dict_filename, 'w')
for name in title_row:
    line = var_aliases[name] + '\t' + var_types[name] + '\t' + var_ranges[name] + '\t' + var_weights[name] + '\n'
    dfile.write(line)  
dfile.close()
print "Done."
