'''
Validates the input metadata file against the csv files in the 
specified folder.

@copyright: Fathom Information Design 2014
'''

import sys, os, csv, math
import xml.etree.ElementTree as ET

def get_variables(xml, var_names, var_types, var_ranges, var_fnames, var_equiv):
    vname = ""
    vtype = ""
    vold = []
    vranges = []
    for child in xml:
        if child.tag == "short":             
            vname = child.text
        if child.tag == "old":
            vold = child.text.split(";")                     
        if child.tag == "type":
            vtype = child.text
        if child.tag == "datafile":   
            files = child.text.split(";")
            for f in files: var_fnames.add(f)
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
        var_equiv[vname] = vold

def validate_values(data, typ, rang):
    for d in data:
        if d == "NA" or d == '': continue

        if typ == "float":
            try:
                val = float(d)
            except ValueError:
                print("  In variable " + var + " the value " + d + " is not a valid number")
                return False  
            if not ((math.floor(rang[0]) <= val and val <= math.ceil(rang[1])) or (2 < len(rang) and val in rang[2:len(rang)])):
                print("  In variable " + var + " the value " + str(val) + " is outside the range [" + ",".join([str(x) for x in rang]) + "]")
                return False
        elif typ == "integer":            
            if -1 < d.find("."):
                print("  In integer variable " + var + " the value " + d + " contains a decimal part")
                return False
            else: 
                try:
                    val = int(d)
                except ValueError:
                    print("  In variable " + var + " the value " + d + " is not a valid number")
                    return False
                if not (rang[0] <= val and val <= rang[1] or (2 < len(rang) and val in rang[2:len(rang)])):
                    print("  In variable " + var + " the value " + str(val) + " is outside the range [" + ",".join([str(x) for x in rang]) + "]")
                    return False
        elif typ == "category":            
            if not d in rang: 
                print("  In variable " + var + " the value + '" + d + "' is outside the range [" + ",".join([str(x) for x in rang]) + "]")
                return False

    return True

xml_filename = sys.argv[1]

tree = ET.parse(xml_filename)
root = tree.getroot()

print("Validating metadata file " + xml_filename + "...")

all_ok = True
for table in root: 
    if (table.tag == "table"):
        if table.attrib["include"] != "yes": continue
        filename = ""        
        var_names = []
        var_types = {} 
        var_ranges = {}
        var_equiv = {}
        var_filenames = set()        
        for child in table:    
            if child.tag == "var" and child.attrib["include"] == "yes":                            
                get_variables(child, var_names, var_types, var_ranges, var_filenames, var_equiv)
 
        if var_names != []:
            var_loaded = {}
            if len(var_filenames) == 0:
                print("  Didn't find any datafiles")
                all_ok = False
                continue
                    
            for filename in var_filenames:
                if not os.path.exists(filename):
                    print("  Didn't find datafile " + filename)
                    all_ok = False
                    continue
 
                name_ext = os.path.split(filename)[1]
                tname = name_ext.split(".")[0]
                            
                csv_file = open(filename, 'r', encoding='latin1') 
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                # The replace is needed because the variable names in the source csv files
                # use "." instead of "_" even though the variable name in the codebook has
                # "_"                
                title_row = [x.upper().replace(".", "_") for x in next(csv_reader)]

                # Transpose the rows: 
                columns = list(zip(*csv_reader))

                for var in var_names:
                    vars = [var] + var_equiv[var]
                    found = False
                    
                    for v in vars:
                        if -1 < v.find("."): 
                            vparts = v.split(".")
                            v = vparts[0]
                            fn = vparts[1]
                            if tname != fn: continue
                                                
                        if v in title_row:
                            found = True
                            col = title_row.index(v)
                            var_loaded[var] = True
                            if not validate_values(columns[col], var_types[var], var_ranges[var]):
                                all_ok = False 

                csv_file.close()
                
            for var in var_names:
               if not var_loaded.get(var, False):
                   print("  Variable " + var + " is missing from " + ",".join(list(var_filenames)))
                   all_ok = False

if all_ok:
    print("Done: No problems detected.")
else: 
    print("Done: Some problems detected.")
