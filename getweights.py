'''
Makes a metadata file for all the weight variables across all components.

It requires the Beautiful Soup and requests libraries for Python:
http://www.crummy.com/software/BeautifulSoup
http://docs.python-requests.org/en/latest/index.html
Installation of both packages typically just require (from command line):
easy_install beautifulsoup4
easy_install requests

The HTML parser can be set with the -parser option, and chose among the ones
listed below: 
http://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
The default is html.parser, the other ones (html5lib, lxml) need to be installed
separately.

@copyright: Fathom Information Design 2014
'''

import sys, os, csv, codecs, re
import requests
from bs4 import BeautifulSoup
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

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def clean_xml_string(str):
    # Removing EOL characters 
    str = str.replace("\r", "").replace("\n", "")
    # Removing less/greater signs to avoid problems with XML 
    str = str.replace("<=", "less or equal than").replace(">=", "greater or equal than")
    str = str.replace("<", "less than ").replace(">", "greater than")
    # Likewise for the '&' character
    str = str.replace("&", "and")
    # Removing the ":" and ";" characters, used to separate the data values
    str = str.replace(";", "").replace(":", "");
    return str

def int_or_float(datafile, name):
    file = open(datafile, 'r', encoding='latin1') 
    reader = csv.reader(file, delimiter=',', quotechar='"')
    # The replace is needed because the variable names in the source csv files
    # use "." instead of "_" even though the variable name in the codebook has
    # "_"    
    title = [x.upper().replace(".", "_") for x in next(reader)]
    if not name in title:
        file.close()
        return None    
    col = title.index(name)         
    type = "integer"     
    for row in reader:
        dat = row[col] 
        try:
            value = float(dat)
            if not value.is_integer():
                type = "float"
        except ValueError:
            # invalid numeric value, this will be catched when checking metadata             
            continue
    file.close()
    return type
                   
def get_variable_type_and_range(short_name, full_name, table, datafile):
    var_type  = None
    var_range = None
    val_list = table.tbody.find_all("tr")
    for val in val_list:
        td_list = val.find_all("td")
        val_code = td_list[0].text
        val_desc = td_list[1].text
        if val_desc == "Range of Values" or (is_number(val_code) and val_desc == val_code and var_type == None):
            if -1 < val_code.find(" to "):       
                var_range = val_code.replace(" to ", ",")
            else:
                # Single value?
                var_range = val_code + "," + val_code
                print("  Warning: range of numeric variable " + short_name + " has a single value " + val_code)
            if var_range == "00:00,23:59" or -1 < full_name.find("HH:MM") or -1 < full_name.find("HHMM"):
                var_type = "time"                             
            else:
                if -1 < var_range.find("."):
                    # If the range contains a decimal point, we know is a float value
                    var_type = "float"
                else:
                    # Otherwise we need to go through the data
                    # Send to a function that checks for integer or float which returns "integer" or "float"
                    # then var_type = the returned value
                    if os.path.exists(datafile):
                        var_type = int_or_float(datafile, short_name) 
                    else:
                        # Data file doesn't exist, variable won't be added because its type
                        # will remain undefined.
                        break                                                  
        elif val_desc == "Value was recorded" or (var_type == None and (val_desc.find("<") == 0 or val_desc.isdigit())):
            var_type = "recorded"
            var_range = "" 
            break 
        else:
            if var_type == None: 
                var_type = "category"                    
            if val_code != "." and val_desc != "Missing":
                if var_range == None: var_range = "" 
                        
                val_desc = clean_xml_string(val_desc)
						
                if var_type != "integer":
                    if var_range != "" : var_range += ";"
                    var_range += val_code + ":" + val_desc  
                else:
                    # Expanding the range when there is an additional cap value
                    expand = 0

                    try:
                        endpoints = [int(x) for x in var_range.split(",")]
                    except ValueError:
                        endpoints = []  

                    if len(endpoints) == 2:
                        val = int(val_code)                            
                        if val == endpoints[1] + 1: 
                            endpoints[1] = val
                            expand = 1
                        if val == endpoints[0] - 1: 
                            endpoints[0] = val
                            expand = 1

                    if expand:   
                        var_range = str(endpoints[0]) + "," + str(endpoints[1]) 
                    else:
                        var_range += ";" + val_code + ":" + val_desc

    return [var_type, var_range] 

def write_xml_line(line):
    ascii_line = ''.join(char for char in line if ord(char) < 128)
    if len(ascii_line) < len(line):
        print("  Warning: non-ASCII character found in line: '" + str(line.encode('ascii', 'ignore')) + "'")
    xml_file.write(ascii_line + '\n')
    xml_strings.append(ascii_line + '\n')

def get_component_weights(component, year, parser):
    request_url = "http://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=" + component + "&CycleBeginYear=" + year
    html_doc = None
    for i in range(0, 5):
        try:
            html_doc = requests.get(request_url)
            break; 
        except:
            html_doc = None          
            if i < 5 - 1: print("  Warning: Could not open " + request_url + ", will try again")
    if html_doc == None:
        sys.stderr.write("Error: Failed opening " + request_url + " after 5 attempts\n")
        sys.exit(1)
    
    html_soup = BeautifulSoup(html_doc.text, parser)
    
    if component == "Demographics":
        subsample_weight = '"no"'
    else:
        subsample_weight = '"yes"'
        
    # Getting all the codebooks in listed in the datapage
    for table in html_soup.find_all('table'): 
        links = table.find_all('a')
        for link in links:
            codebook_url = link['href']
            
            path, ext = os.path.splitext(codebook_url)
            if ext.lower() == ".htm" or ext.lower() == ".html":
        
                codebook_url = base_url + codebook_url
                print(codebook_url)

                codebook_doc = None
                for i in range(0, 5):
                    try:
                        codebook_doc = requests.get(codebook_url)
                        break; 
                    except:
                        codebook_doc = None          
                        if i < 5 - 1: print("  Warning: Could not open " + codebook_url + ", will try again")
                if codebook_doc == None:
                    sys.stderr.write("Error: Failed opening " + codebook_url + "after 5 attempts\n")
                    sys.exit(1)
            
                print("Extracting metadata from codebook " + codebook_url + "...")
                codebook_soup = BeautifulSoup(codebook_doc.text, parser)

                header = codebook_soup.find("div", {"id": "PageHeader"})            
                if header == None: continue
            
                header_table_name = header.find("h3")            
                table_name = header_table_name.contents[0].strip().replace("&", "and").encode('ascii', 'ignore')
            
                header_data_file = header.find("h4")            
                data_file = header_data_file.contents[0].split(":")[1].strip()
                data_filename = os.path.splitext(data_file)[0].upper()
                csv_data_filepath = os.path.abspath(os.path.join(data_folder, data_filename + ".csv"))
                csv_data_relpath = os.path.join(data_folder, data_filename + ".csv")

                codebook = codebook_soup.find("div", {"id": "Codebook"})
                if codebook == None: continue
                variables = codebook.find_all("div", {"class": "pagebreak"})
            
                has_seqn = False
                xml_lines = []
                table_vars = []                                           
                for var in variables:
                    var_info = var.find("dl")
                    if not var_info: 
                        print("  Warning: codebook for '" + str(var) + "' seems malformed, skipping")
                        continue
                    var_table = var.find("table")
                    info = var_info.find_all("dd")
                 
                    if 0 < len(info):
                        short_name = clean_xml_string(info[0].contents[0]).upper()
                    else:
                        print("  Warning: variable without short name, skipping")
                        continue
                    
                    short_name = short_name.strip()
                    if short_name == "":
                        print("  Warning: variable without short name, skipping")
                        continue
                        
                    if short_name == "SEQN":
                        has_seqn = True
                        
                    full_name = ""
                    if 1 < len(info) and 0 < len(info[1].contents):
                        # Trying to get full name from SAS label
                        full_name = clean_xml_string(info[1].contents[0])
                        
                    full_name = full_name.strip()
                    if full_name == "": 
                        print("  Warning: variable " + short_name + " doesn't have full name, skipping")
                        continue                        

                    fnl = full_name.lower()
                    if -1 < fnl.find("weight") and (-1 < fnl.find("interview") or -1 < fnl.find("mec") or -1 < fnl.find("sample") or -1 < fnl.find("environmental")):
                        include_weight = '"yes"'
                        if -1 < fnl.find("jack knife"):
                            include_weight = '"no"'
                     
                        if var_table == None:
                            print("  Warning: variable " + full_name + " (" + short_name + ") doesn't have a value table, skipping")
                            continue
                         
                        (var_type, var_range) = get_variable_type_and_range(short_name, full_name, var_table, csv_data_filepath)
                        
                        if var_type != "float":
                            print("  Warning: wrong type for weight variable " + full_name + " (" + short_name + ")")
                            continue
                                                    
                        if var_range == None:
                            print("  Warning: Cannot find type/range for weight variable " + full_name + " (" + short_name + ")")
                            continue 
                                                 
                        weight_vars.append(short_name)
                        if not short_name in sample_weights:
                            name_ext = os.path.split(csv_data_relpath)[1]
                            tname = name_ext.split(".")[0]
                            short_name = short_name + "." + tname
                        
                        xml_lines.append('    <var include=' + include_weight + ' weight="yes" subsample=' + subsample_weight + '><short>' + short_name + '</short><full>' + full_name + '</full><type>' + var_type + '</type><range>' + var_range + '</range><datafile>' + csv_data_relpath + '</datafile></var>')
                 
                if has_seqn:
                    if component == "Demographics":
                        for line in xml_lines: sample_xml_lines.append(line)
                    elif component == "Dietary":         
                        for line in xml_lines: dietary_xml_lines.append(line)
                    else:
                        for line in xml_lines: subsample_xml_lines.append(line)                        
                elif table_vars: 
                    print("  Warning: SEQN variable not found in this table (" + table_name + "), skipping weights variables " + table_vars)
                 
    
base_url = "https://wwwn.cdc.gov"

data_cycle     = sys.argv[1] 
data_folder    = sys.argv[2]
xml_filename   = sys.argv[3]

html_parser    = "html.parser"
if len(sys.argv) == 6 and sys.argv[4] == "-parser":
    html_parser = sys.argv[5]   

data_components = load_components()
begin_year = data_cycle.split("-")[0]

sample_weights = ["WTINT2YR", "WTMEC2YR", "WTINT4YR", "WTMEC4YR"]
weight_vars = []
sample_xml_lines = []
dietary_xml_lines = []
subsample_xml_lines = []

for component in data_components:
    get_component_weights(component, begin_year, html_parser)
                        
# Writing file in utf-8 because the input html files from
# NHANES website sometimes have characters output the ASCII range.
xml_file = codecs.open(xml_filename, "w", "utf-8")
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
