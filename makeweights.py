'''
Calculates the merged weights according to the information stored in the list file,
saves them to the csv file and creates the corresponding xml metadata.

@copyright: Fathom Information Design 2014
'''

import sys, os, csv, codecs
from xml.dom.minidom import parseString

def write_xml_line(line):
    ascii_line = ''.join(char for char in line if ord(char) < 128)
    if len(ascii_line) < len(line):
        print("  Warning: non-ASCII character found in line: '" + line.encode('ascii', 'ignore') + "'")
    xml_file.write(ascii_line + '\n')
    xml_strings.append(ascii_line + '\n')

out_folder = sys.argv[1]
list_file = sys.argv[2]
csv_file = sys.argv[3]
xml_file = sys.argv[4]

weights_files = {}
weights_factors = {}
weights_subsamples = {}
wfile = open(out_folder + "/" + list_file, "r")
lines = wfile.readlines()
for line in lines:
    parts = line.split("\t")
    wname = parts[0].strip()
    wdef = parts[1].strip()
    wfac = parts[2].strip()
    wsub = parts[3].strip()
    weights_files[wname] = wdef
    weights_factors[wname] = wfac
    weights_subsamples[wname] = wsub
wfile.close()

print("Loading source weights...")

num_cycles = 0

all_seqn = set([])
all_var_values = []
all_var_names = []
all_var_ranges = []
for var in weights_files:
    all_var_names.append(var)
    values_dict = {}
    
    factors_str = weights_factors[var].split(",")
    factors = [0.0] * len(factors_str)
    for i in range(0, len(factors_str)):        
        [numerator, denominator] = factors_str[i].split("/")
        factors[i] = float(numerator) / float(denominator)
    
    min_value = float("inf")
    max_value = float("-inf")    
    files = weights_files[var].split(";")
    
    if 0 < num_cycles:
        if num_cycles != len(files):
            print("Error: inconsistent cycle length across variables: " + num_cycles + " != " + len(files))
            sys.exit(1)
    else:
        num_cycles = len(files)
        
    for i in range(0, num_cycles):
        file = files[i] 
        factor = factors[i]
        [name, filename] = file.split(":")
        
        data_file = open(filename, 'r')
        csv_reader = csv.reader(data_file, delimiter=',', quotechar='"')
        # The replace is needed because the variable names in the source csv files
        # use "." instead of "_" even though the variable name in the codebook has
        # "_"                  
        title_row = [x.upper().replace(".", "_") for x in next(csv_reader)]   
        data_rows = [row for row in csv_reader]
        
        if "SEQN" in title_row:
            seqn_col = title_row.index("SEQN")
        else:
            print("Error: Cannot load weights for variable " + name + " because SEQN is missing from its datafile " + filename)
            sys.exit(1)
                           
        if name in title_row:                  
            var_col = title_row.index(name)       
        else:
            print("Error: Cannot load weights for variable " + name + " because the values are missing from its datafile " + filename)
            sys.exit(1)
                         
        for row in data_rows:
            seqn = int(row[seqn_col]) 
            all_seqn.add(seqn)
            value = row[var_col]
 
            try:
                num = factor * float(value)                   
                values_dict[seqn] = str(num)
            except ValueError:
                num = 0.0
                values_dict[seqn] = value
        
            if num < min_value: min_value = num
            if num > max_value: max_value = num 
        
        data_file.close()

    all_var_ranges.append([min_value, max_value])    
    all_var_values.append(values_dict)

title_line = "SEQN"
count = len(all_var_names)
for i in range(0, count):
    name = all_var_names[i]
    title_line = title_line + "," + name
             
print("Writing merged weights...")
weights_filename = out_folder + "/" + csv_file
weights_file = open(weights_filename, 'w')
weights_file.write(title_line + "\n")
rowCount = 0
list_seqn = list(all_seqn)
list_seqn.sort()
for seqn in list_seqn:
    colCount = 1
    line = str(seqn)
    for i in range(0, count):
        colCount = colCount + 1        
        vali = all_var_values[i] 
        if seqn in vali:                
            if vali[seqn] == "NA" or vali[seqn] == "":
                line = line + ",NA"
            else:        
                line = line + "," + vali[seqn]  
        else:
            line = line + ",NA"                 
    if colCount != count + 1: 
        sys.stderr.write("Number of columns is inconsistent at row " + rowCount + ". It is " + colCount + "but should be " + count + "\n")
        sys.exit(1)
    rowCount = rowCount + 1
    weights_file.write(line + "\n")
weights_file.close()
print("Done: written",rowCount,"rows and",count,"columns.")

print("Writing metadata for merged weights...")

sample_xml_lines = []
dietary_xml_lines = []
subsample_xml_lines = []

year_str = str(2 * num_cycles) + " Year"

for var in weights_files:
    idx = all_var_names.index(var)
    short_name = var    
    var_range = str(all_var_ranges[idx][0]) + "," + str(all_var_ranges[idx][1])
        
    subsample = weights_subsamples[var] == "True"    
    if subsample: 
        subsample_str = '"yes"'
        full_name = "Subsample " + year_str + " weights"
    else: 
        subsample_str = '"no"'
        if -1 < var.find("WTINT"):
            full_name = "Full Sample " + year_str + " Interview Weight"
        elif -1 < var.find("WTMEC"):
            full_name = "Full Sample " + year_str + " MEC Exam Weight"        
        else:
            full_name = "Full Sample " + year_str + " Weight"
            print("  Warning: Full sample weight that is neither Interview nor MEC")
        
    line = '    <var include="yes" weight="yes" subsample=' + subsample_str + '><short>' + short_name + '</short><full>' + full_name + '</full><type>float</type><range>' + var_range + '</range><datafile>' + weights_filename + '</datafile></var>'

    # Dietary is not implemented!
    if subsample:
        subsample_xml_lines.append(line)
    else:
        sample_xml_lines.append(line)

# Writing file in utf-8 because the input html files from
# NHANES website sometimes have characters output the ASCII range.
xml_file = codecs.open(out_folder + "/" + xml_file, "w", "utf-8")
xml_strings = []

write_xml_line('<?xml version="1.0"?>')
write_xml_line('<data name="Weights">')
            
if sample_xml_lines:            
    write_xml_line('  <table include="yes" name="Sample weights">') 
    for line in sample_xml_lines: write_xml_line(line)
    write_xml_line('  </table>')

if dietary_xml_lines:
    write_xml_line('  <table include="yes" name="Dietary weights">') 
    for line in dietary_xml_lines: write_xml_line(line)
    write_xml_line('  </table>')
            
if subsample_xml_lines:            
    write_xml_line('  <table include="yes" name="Subsample weights">') 
    for line in subsample_xml_lines: write_xml_line(line)
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
