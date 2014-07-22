'''
Aggregates all the variables in the supplied metadata files 
into a single csv output file for input in visualization.
It also generates the dictionary file with the type for each
variable

@copyright: Fathom Information Design 2014
'''

import sys, os, csv, math
import xml.etree.ElementTree as ET

def get_variables(xml, var_names, var_types, var_ranges, var_files, var_equiv):
    vname = ""
    vname_full = ""
    vname_old = []
    vtype = ""
    vranges = []
    for child in xml:
        if child.tag == "short":             
            vname = child.text
            if vname == 'SEQN': 
                return 
        if child.tag == "old":
            vname_old = child.text.split(";")        
        if child.tag == "full":
            vname_full = child.text
        if child.tag == "type":
            vtype = child.text
        if child.tag == "datafile":
            filenames = child.text.split(";")
            for fn in filenames:
                if not fn in var_files: var_files[fn] = set()
                var_files[fn].add(vname)
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
        var_names.append([vname, vname_full])
        var_types[vname] = vtype
        var_ranges[vname] = vranges
        var_equiv[vname] = vname_old   

argc = len(sys.argv)
out_folder  = sys.argv[1]
in_metadata = sys.argv[2:argc - 1]
data_file = sys.argv[argc - 1]

out_data_filename = os.path.abspath(os.path.join(out_folder, data_file))

all_seqn = set([])
all_var_values = []
all_var_names = []
all_var_types = []
all_var_ranges = []

print "Getting variable values..."
for meta in in_metadata:
  xml_filename = os.path.abspath(os.path.join(out_folder, meta))  
  tree = ET.parse(xml_filename)
  root = tree.getroot()
  for el in root:
      if (el.tag == "data"):
          group = el.attrib["name"]
                  
      if (el.tag == "table"):
          if el.attrib["include"] != "yes": continue

          var_names = []
          var_types = {}  
          var_ranges = {}
          var_files = {}
          var_equiv = {}
          for child in el: 
              if child.tag == "var": 
                  if child.attrib["include"] == "yes":
                      get_variables(child, var_names, var_types, var_ranges, var_files, var_equiv)

          if var_names != []:
              for filename in var_files.keys():
                  if not os.path.exists(filename):
                      print "  Warning: File " + filename + " is missing, won't add values for variables " + ",".join(list(var_files[filename]))
                      continue              
                    
                  csv_file = open(filename, 'rb')
                  csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                  # The replace is needed because the variable names in the source csv files
                  # use "." instead of "_" even though the variable name in the codebook has
                  # "_"                  
                  title_row = [x.upper().replace(".", "_") for x in csv_reader.next()]   
                  data_rows = [row for row in csv_reader]
                  
                  # Getting the values for each variable
                  var_set = var_files[filename] 
                  for var in var_set:                  
                      typ = var_types[var]
                      rang = var_ranges[var]
                      
                      if "SEQN" in title_row:
                          seqn_col = title_row.index("SEQN")
                      else:
                          print "  Warning: Not adding the values of variable " + var + " because SEQN is missing from its datafile " + filename
                          continue

                      try:                          
                          if -1 < var.find("."): var0 = var.split(".")[0]
                          else: var0 = var
                          var_col = title_row.index(var0)
                      except ValueError:
                          for oname in var_equiv[var]:
                              if -1 < oname.find("."): oname = oname.split(".")[0]
                              try:
                                  var_col = title_row.index(oname)
                                  break
                              except ValueError:
                                  idx = -1                           
                          
                      if var_col == -1:
                          print "  Warning: Variable " + var + " is missing from " + filename
                          continue
                    
                      idx = 0 
                      try:
                          idx = all_var_names.index(var)
                      except ValueError:
                          idx = -1
                      
                      if idx == -1:
                          all_var_names.append(var)
                          all_var_types.append(typ)
                          all_var_ranges.append(rang)
                          values_dict = {}
                          all_var_values.append(values_dict)
                      else:
                          values_dict = all_var_values[idx]
                         
                      for row in data_rows:
                          seqn = int(row[seqn_col]) 
                          all_seqn.add(seqn)
                          value = row[var_col] 
                          values_dict[seqn] = value

                  csv_file.close()

print "Done."

# Construct title line
name = "SEQN"
title_line = name
count = len(all_var_names)
for i in range(0, count):
    nami = all_var_names[i]
    typi = all_var_types[i]
    if typi != "recorded": 
        name = nami
        title_line = title_line + "\t" + name

print "Writing aggregated data file..."
data_file = open(out_data_filename, 'w')
data_file.write(title_line + "\n")
rowCount = 0
list_seqn = list(all_seqn)
list_seqn.sort()
for seqn in list_seqn:
    colCount = 1
    line = str(seqn)
    for i in range(0, count):
        typi = all_var_types[i]
        if typi != "recorded":    
            colCount = colCount + 1        
            vali = all_var_values[i] 
            if vali.has_key(seqn):                
                if vali[seqn] == "NA" or vali[seqn] == "":
                    line = line + "\t\N"
                else:        
                    line = line + "\t" + vali[seqn]  
            else:
                line = line + "\t\N" 
    if colCount != count + 1: 
        sys.stderr.write("Number of columns is inconsistent at row " + rowCount + ". It is " + colCount + "but should be " + count + "\n")
        sys.exit(1)
    rowCount = rowCount + 1
    data_file.write(line + "\n")
data_file.close()
print "Done: written",rowCount,"rows and",count,"columns."
