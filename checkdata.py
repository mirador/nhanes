'''
Validates the input metadata file against the csv files in the 
specified folder.

@copyright: Fathom Information Design 2014
'''

import sys, os, csv, math
import xml.etree.ElementTree as ET

def get_variables(xml, var_names, var_types, var_ranges, var_files, var_equiv):
    vname = ""
    vtype = ""
    vold = []
    vranges = []
    vfiles = []
    for child in xml:
        if child.tag == "short":
            vname = child.text
        if child.tag == "old":
            vold = child.text.split(";")            
        if child.tag == "type":
            vtype = child.text
        if child.tag == "datafile":   
            vfiles = child.text.split(";")
        if child.tag == "range":
            rstr = child.text
            if vtype == "float":
                temp = rstr.split(";")
                vranges = [float(x) for x in temp[0].split(",")]
                if 1 < len(temp):
                    for x in temp[1:len(temp)]:
                        vranges.append(float(x.split(":")[0]))
            elif vtype == "integer":
                temp = rstr.split(";")
                vranges = [int(x) for x in temp[0].split(",")]
                if 1 < len(temp):
                    for x in temp[1:len(temp)]:
                        vranges.append(int(x.split(":")[0]))
            elif vtype == "category":
                vranges = [x.split(":")[0] for x in rstr.split(";")]
    if vname != "":
        var_names.append(vname)
        var_types[vname] = vtype
        var_ranges[vname] = vranges
        var_files[vname] = vfiles
        var_equiv[vname] = vold        

def validate_variable(var_name, seqn_column, values_column, source_values):
    ok = True
    n = len(seqn_column)
    for i in range(0, n):
        seqn = seqn_column[i]
        value = values_column[i]
        if not seqn in source_values:
            if value != "NA":
                ok = False
                sys.stderr.write("Sequence number " + str(seqn) + " not found in source data for variable " + var_name + ", its value is " + value + "\n")
        else:    
            svalue = source_values[seqn]
            if svalue == "": svalue = "NA"            
            if value != svalue:
                ok = False
                sys.stderr.write("Value for variable " + var_name + " at sequence number " + seqn + " is different from source: " + value + " != " + svalue + "\n")
    return ok

argc = len(sys.argv)
data_folder = sys.argv[1]
in_metadata = sys.argv[2:argc - 1]
data_file = sys.argv[argc - 1]

print("Loading data...")
data_filename = os.path.abspath(os.path.join(data_folder, data_file))
csv_file = open(data_filename, 'r')
csv_reader = csv.reader(csv_file, delimiter='\t', quotechar='"')
title_row = [x.upper() for x in next(csv_reader)]
data_columns = list(zip(*csv_reader))
print("Done.")

print("Loading metadata...")
var_names = []
var_types = {}  
var_ranges = {}
var_files = {}
var_equiv = {}
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
                      get_variables(child, var_names, var_types, var_ranges, var_files, var_equiv)
print("Done.")

if "SEQN" in title_row:
    scol = title_row.index("SEQN")
else:    
    sys.stderr.write("Error: the data is missing the sequence column\n")
    sys.exit(1)
    
seqn = [int(x) for x in data_columns[scol]]

print("Validating data...")
all_ok = True
source_data = {}
for var in title_row:
    if var == "SEQN": continue
    col = title_row.index(var)
    
    source_values = {}
    for filename in var_files[var]:
        if filename in source_data:
            [titles, rows] = source_data[filename]
        else:    
            file = open(filename, 'r', encoding='latin1')
            reader = csv.reader(file, delimiter=',', quotechar='"')
            # The replace is needed because the variable names in the source csv files
            # use "." instead of "_" even though the variable name in the codebook has
            # "_"
            titles = [x.upper().replace(".", "_") for x in next(reader)]
            rows = [row for row in reader]
            source_data[filename] = [titles, rows]
            file.close()
        
        s = titles.index("SEQN")        
        vars = [var] + var_equiv[var]
        for v in vars:
            if -1 < v.find("."): 
                v = v.split(".")[0]
            if not v in titles: continue
            c = titles.index(v)
            for row in rows:
                source_values[int(row[s])] = row[c]
            break
            
    var_ok = validate_variable(var, seqn, data_columns[col], source_values)
    all_ok = all_ok and var_ok
    
csv_file.close() 
    
if all_ok:
    print("No problems detected.")
else: 
    sys.stderr.write("Some problems detected\n.")
    sys.exit(1)