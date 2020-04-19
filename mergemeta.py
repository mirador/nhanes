'''
Merges the common variables in the supplied metadata files 
into the corresponding merged metadata.

@copyright: Fathom Information Design 2014
'''

import sys, os, csv, math, codecs
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

def load_components():
  ifile = open('components', 'r')
  components = []
  for line in ifile.readlines():
      line = line.strip()
      if line == "" or line[0] == "#": continue
      parts = line.split()
      if len(parts) == 2:
          comp_name = parts[0]
          components.append(comp_name)
  ifile.close()
  return components

def load_varequiv(fn):
  ifile = open(fn, 'r')
  old_to_new = {}
  new_to_old = {}
  for line in ifile.readlines():
      line = line.strip()
      if line == "" or line[0] == "#": continue
      parts = line.split()
      if 0 < len(parts):
          nname = parts[0]
          oldnames = set(parts[1:len(parts)])
          new_to_old[nname] = oldnames
          for oname in oldnames:
              old_to_new[oname] = nname
  ifile.close()  
  return [old_to_new, new_to_old]
  
def get_variables(xml, var_names, var_types, var_ranges, var_files, var_weights, inc_seqn, use_4yr):
    vname = ""
    vname_full = ""
    vtype = ""
    vranges = []
    vweight = ""
    for child in xml:
        if child.tag == "short":             
            vname = child.text           
            if vname == 'SEQN' and not inc_seqn:
                return 
        if child.tag == "full":
            vname_full = child.text
        if child.tag == "type":
            vtype = child.text
        if child.tag == "weight":
            if use_4yr:
                vweight  = child.text.replace("2YR", "4YR")
            else:        
                vweight  = child.text
        if child.tag == "datafile":   
            var_files[vname] = child.text
        if child.tag == "range":
            rstr = child.text
            vranges = rstr.split(";")
    if vname != "":        
        var_names.append([vname, vname_full])
        var_types[vname] = vtype
        var_ranges[vname] = vranges
        var_weights[vname] = vweight;

def write_xml_line(line):
    ascii_line = ''.join(char for char in line if ord(char) < 128)
    if len(ascii_line) < len(line):
        print("  Warning: Non-ASCII character found in line: '" + line.encode('ascii', 'ignore') + "'")
    xml_file.write(ascii_line + '\n')
    xml_strings.append(ascii_line + '\n')

def add_range(range0, range1, typ):
    merged = []
    if typ == "float" or typ == "integer":
        if 0 < len(range0):
            if typ == "integer":
                interval0 = [int(x) for x in range0[0].split(',')]
            else: 
                interval0 = [float(x) for x in range0[0].split(',')]
        else:
            interval0 = [float("inf"), float("-inf")]    
        if 0 < len(range1):            
            if typ == "integer":
                interval1 = [int(x) for x in range1[0].split(',')]
            else: 
                interval1 = [float(x) for x in range1[0].split(',')]
        else:
            interval1 = [float("inf"), float("-inf")] 
            
        if interval1[0] < interval0[0]:
            interval0[0] = interval1[0]
        if interval0[1] < interval1[1]:
            interval0[1] = interval1[1]

        merged = [str(interval0[0]) + "," + str(interval0[1])]
            
        start = 1 
    elif typ == "category":
        start = 0
        
    extra = {}
    if start < len(range0):
        for v in range0[start:len(range0)]:
            val_alias = v.split(':')
            #if len(val_alias) == 2:
            extra[val_alias[0]] = val_alias[1]
    if start < len(range1):
        for v in range1[start:len(range1)]:
            val_alias = v.split(':')
            #if len(val_alias) == 2:            
            extra[val_alias[0]] = val_alias[1]
            
    for k in sorted(extra.keys()):
        merged.append(k + ":" + extra[k])
    
    return merged    
    
def get_weight_vars(filename):
    vars = {}
    tree = ET.parse(filename)
    root = tree.getroot()
    for table in root: 
        if (table.tag == "table"):           
            for var in table:    
                subsample = var.attrib["subsample"] == "yes"
                wname = ""
                wfile = ""
                for child in var:
                    if child.tag == "short":  
                        wname = child.text        
                    if child.tag == "datafile":
                        wfile = child.text
                vars[wname] = [wfile, subsample]
    return vars    

def make_range_string(range):
    return ';'.join(range)

meta_file = sys.argv[1]
aggr_cycles = sys.argv[2]
data_component = sys.argv[3]
base_folders = sys.argv[4]
out_folder = sys.argv[5]
equiv_file = sys.argv[6]

[year0, year1] = [int(x) for x in aggr_cycles.split("-")]
inc_4yr = year0 == 1999
year_diff = (year1 - year0 + 1)
num_cycles = int(year_diff / 2)
in_folders = [""] * num_cycles
cycle_string = str(year_diff) + "YR"

# Reverse order to make sure that the most recent cycle is used to get table names, etc.
for cycle in range(num_cycles - 1, -1, -1):
    cy0 = year0 + 2 * cycle
    cy1 = cy0 + 1
    in_folders[num_cycles - cycle - 1] = base_folders + "/" + str(cy0) + "-" + str(cy1)

data_components = load_components()
[new_names, old_names] = load_varequiv(equiv_file)

if not data_component in data_components:
    sys.stderr.write("Error: component must be one of the following: Demographics, Dietary, Examination, Laboratory or Questionnaire")
    sys.exit(1)
    
inc_seqn = data_component == "Demographics"

if num_cycles < 2:
    sys.stderr.write("Error: not enough input folders (need at least 2 for merging)")
    sys.exit(1)

# Initialize the sets for each folder
all_vars = [set([]) for f in in_folders]
all_fnames = [{} for f in in_folders]
all_tables = [{} for f in in_folders]
all_types = [{} for f in in_folders]
all_ranges = [{} for f in in_folders]
all_datafiles = [{} for f in in_folders]
all_weights = [{} for f in in_folders]

cycle_weights = [{} for f in in_folders]

print("Reading input metadata...")
for i in range(0, num_cycles):
    folder = in_folders[i]
    xml_filename = os.path.join(folder, meta_file)
    
    weights_file = os.path.join(folder, "weights.xml")
    if os.path.exists(weights_file):
        cycle_weights[i] = get_weight_vars(weights_file)
    else:
        cycle_weights[i] = {}

    tree = ET.parse(xml_filename)
    root = tree.getroot()
    for table in root:
        if (table.tag == "table"):
            if table.attrib["include"] != "yes": continue
            tname = table.attrib["name"]
            var_names = []
            var_types = {}  
            var_ranges = {}
            var_files = {}
            var_weights = {}
            for child in table:
                if child.tag == "var": 
                    if child.attrib["include"] == "yes" and child.attrib["weight"] == "no":
                        get_variables(child, var_names, var_types, var_ranges, var_files, var_weights, inc_seqn, inc_4yr and num_cycles - 2 <= i)
            for names in var_names:
                name0 = names[0]
                name1 = names[1]                
                sname = new_names.get(name0, name0)
                all_vars[i].add(sname)
                all_tables[i][sname] = tname
                all_fnames[i][sname] = name1
                all_types[i][sname] = var_types[name0]
                all_ranges[i][sname] = var_ranges[name0]
                all_datafiles[i][sname] = var_files[name0]
                
                # Collecting all the weight information 
                weight = var_weights.get(name0, None)
                if weight in cycle_weights[i]:
                    all_weights[i][sname] = [weight, cycle_weights[i][weight][0], cycle_weights[i][weight][1]]
                else:
                    all_weights[i][sname] = [None, None, None]
                
print("Merging metadata...")

# Get variables common to all cycles
common = set.intersection(*all_vars)
print("Found", len(common), "common variables.")

print("Merging weights...")

new_weights = {}
new_weights_factors = {}
new_weights_subsamples = {}
fn = out_folder + "/weights.list"
if os.path.exists(fn):
    wfile = open(fn, "r")
    lines = wfile.readlines()
    for line in lines:
        parts = line.split("\t")
        wname = parts[0].strip()
        wdef = parts[1].strip()
        wfac = parts[2].strip()
        wsub = parts[3].strip()
        new_weights[wname] = wdef
        new_weights_factors[wname] = wfac
        new_weights_subsamples[wname] = wsub
    wfile.close()

toRemove = []
common_weights = {}
for nam in common:
    # Construct name of the weight variable for variable nam
    cweight = all_weights[0][nam] # The weight for variable nam in the most recent cycle (remember they are stored in descending time order)
    weight_name = cweight[0].replace(".", "-")
    subsample_weight = cweight[2]
    
    # Construct definition for the weight variable, concatenating the source files for the weights
    # of variable nam in each cycle
    weight_def = ""
    scale_factors = [0] * num_cycles
    for i in range(0, num_cycles):
        # The scaling factors for each cycle are determined by dividing the number of years
        # encompassed by the weights (4 years for the 1999-2000 and 2001-2002 cycles in 
        # aggregations staring in 1999, 2 years otherwise). For details see:
        # http://www.cdc.gov/nchs/tutorials/nhanes/SurveyDesign/Weighting/Task2.htm
        # http://www.cdc.gov/nchs/data/nhanes/analyticnote_2007-2010.pdf
        if inc_4yr and num_cycles - 2 <= i:
            scale_factors[i] = "4/" + str(year_diff)
        else:
            scale_factors[i] = "2/" + str(year_diff)
        
        cweight = all_weights[i][nam]
        if cweight[2]: subsample_weight = True        
        if weight_def != "": weight_def = weight_def + ";"
        if cweight[0]:
            # In each file, the name of the weight variable doesn't need wherever its after
            # the ".", this was added to ensure that the names are unique inside the aggregated data file.            
            wname = cweight[0].split(".")[0]
            wfile = cweight[1]
            weight_def = weight_def + wname + ":" + wfile
        else:
            # Variable nam is missing a weight file, marked for removal
            toRemove.append(nam)
            continue

    if -1 < weight_name.find("2YR"): weight_name = weight_name.replace("2YR", cycle_string)
    elif -1 < weight_name.find("4YR"): weight_name = weight_name.replace("4YR", cycle_string)
    else: print("  Warning: weight variable for variable " + nam + " doesn't have a standard name: " + weight_name)
    
    # Checking if the weight variable is new, and updating name if necessary
    if weight_name in new_weights:
        weight_def0 = new_weights[weight_name]
        if weight_def0 != weight_def:
            found = False
            for w in new_weights:
                if weight_def == new_weights[w]:
                    # Another variable found with the same definition, using its name
                    # instead
                    found = True
                    weight_name = w
                    break
            if not found:         
                # Didn't find any weight variable with the same definition 
                letters = list(map(chr, range(65, 91)))
                ll = len(letters)
                weight_name_b = weight_name
                i = 0
                while weight_name_b in new_weights:                     
                    if i < ll:
                        weight_name_b = weight_name + "_" + letters[i]
                    else:
                        weight_name_b = weight_name + "_" + letters[ll - 1] + str(i - ll)                        
                    i = i + 1   
                weight_name = weight_name_b
                new_weights[weight_name] = weight_def
    else:
        # This weight variable is truly new, adding new entry to the dictionary
        new_weights[weight_name] = weight_def

    new_weights_factors[weight_name] = ",".join(scale_factors)        
    new_weights_subsamples[weight_name] = str(subsample_weight)
    common_weights[nam] = weight_name

for nam in toRemove:
    print("  Warning: Removing common variable " + nam + " because its missing a weight file")
    common.remove(nam)
            
wfile = open(out_folder + "/weights.list", "w")
for wname in new_weights:
    wfile.write(wname + "\t" + new_weights[wname] + "\t" + new_weights_factors[wname] + "\t" + new_weights_subsamples[wname] + "\n")
wfile.close()

print("Writing merged metadata...")

# Make list of variables per table
tables = {}
for nam in common:
    tab = all_tables[0][nam]
    if tab in tables:
        if nam == "SEQN":
            # SEQN must always appear as the first variable
            tables[tab].insert(0, nam)
        else:
            tables[tab].append(nam)
    else:
        tables[tab] = [nam]

xml_filename = os.path.join(out_folder, meta_file)
xml_file = codecs.open(xml_filename, "w", "utf-8")
xml_strings = []

write_xml_line('<?xml version="1.0"?>')
write_xml_line('<data name="' + data_component + '">')

for tab in tables:
    write_xml_line('  <table include="yes" name="' + tab + '">')
    vars = tables[tab]
    
    for short_name in vars:
        # The full name in the first dataset takes precedence.
        full_name = all_fnames[0][short_name]
        var_type = all_types[0][short_name] 
        skip_var = 0
        var_range = []
        var_datafiles = ""
        for i in range(0, num_cycles):
            if var_datafiles != "": var_datafiles = var_datafiles + ";"
            var_datafiles = var_datafiles + all_datafiles[i][short_name]     
        
            typ = all_types[i][short_name]
            if typ == "time" or typ == "recorded":
                skip_var = 1
                print("  Warning: Skipping common variable " + short_name + " (" + full_name + ") because its type is " + typ + ". Only integer, float, or category variables will be merged.")
                break
            if var_type != typ:
                if (var_type == "integer" and typ == "float") or (var_type == "float" and typ == "integer"):
                    var_type = "float"
                else:    
                    skip_var = 1
                    print("  Warning: Skipping common variable " + short_name + " (" + full_name + ") because its type across datasets is not consistent: " + var_type + " and " + typ)
                    break
            var_range = add_range(var_range, all_ranges[i][short_name], var_type)
            if not var_range:
                print("  Warning: Skipping common variable " + short_name + " (" + full_name + ") because cannot add the range:")
                print(all_ranges[i][short_name])
                continue
            
        equiv_names = ""
        if short_name in old_names:
            names = old_names[short_name]          
            for name in names:
                if equiv_names != "": equiv_names = equiv_names + ";"
                equiv_names = equiv_names + name
            equiv_names = "<old>" + equiv_names + "</old>"      
                                            
        if not skip_var:
            write_xml_line('    <var include="yes" weight="no"><short>' + short_name + '</short>' + equiv_names + '<full>' + full_name + '</full><type>' + var_type + '</type><range>' + make_range_string(var_range) + '</range><weight>' + common_weights[short_name] + '</weight><datafile>' + var_datafiles + '</datafile></var>')

    write_xml_line('  </table>')
write_xml_line('</data>')
xml_file.close()

# For XML validation.
try:
    doc = parseString(''.join(xml_strings))
    doc.toxml()
    print("Done.")
except:
    sys.stderr.write("XML validation error:\n")
    raise

