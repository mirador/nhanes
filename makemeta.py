'''
Makes a metadata file for all the variables in the tables contained in the html 
document specified. The metadata is saved as an xml file formatted for easy
manual editing.

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
import xml.etree.ElementTree as ET

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

def var_inside_file(datafile, name):
    csv_file = open(datafile, 'rb') 
    csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
    title_row = [x.upper().replace(".", "_") for x in csv_reader.next()]
    csv_file.close()
    return name in title_row

def int_or_float(datafile, name):
    file = open(datafile, 'rb') 
    reader = csv.reader(file, delimiter=',', quotechar='"')
    # The replace is needed because the variable names in the source csv files
    # use "." instead of "_" even though the variable name in the codebook has
    # "_"    
    title = [x.upper().replace(".", "_") for x in reader.next()]
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
    if not table.tbody: 
        print "  Warning: codebook of variable " + short_name + " seems malformed"
        return [var_type, var_range] 
    val_list = table.tbody.find_all("tr")
    for val in val_list:
        if not val.td: 
            print "  Warning: codebook of variable " + short_name + " seems malformed"        
            continue

        if 0 < len(val.th.contents):
            val_code = val.th.contents[0].strip()
        else:        
            print "  Warning: codebook of variable " + short_name + " seems malformed"        
            continue
              
        val_desc = ""            
        if 0 < len(val.td.contents):
            val_desc = val.td.contents[0].strip()

        if val_desc == "Range of Values" or (is_number(val_code) and val_desc == val_code and var_type == None):
            if -1 < val_code.find(" to "):       
                var_range = val_code.replace(" to ", ",")
            else:
                # Single value?
                var_range = val_code + "," + val_code
                print "  Warning: range of numeric variable " + short_name + " has a single value " + val_code
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
        print "  Warning: non-ASCII character found in line: '" + line.encode('ascii', 'ignore') + "'"
    xml_file.write(ascii_line + '\n')
    xml_strings.append(ascii_line + '\n')

def strip_units(name):
    # Regular expression sear to identify a substring of the form
    # "(mL/g), i.e.: measurement units    
    match = re.search(r'\([\w]*./[\w+\s\w+]*\)', name)
    if match:
        p0 = match.start()
        p1 = match.end()
        return name[0:match.start()] + name[match.end():len(name)]
    else:
        return None    

def repeated_var(newname, oldnames):
    newnameNU = strip_units(newname)
    if not newnameNU: return None
    for oldname in oldnames:
        oldnameNU = strip_units(oldname[1])
        if newnameNU == oldnameNU: 
            return oldname 
    return None

def get_weight_vars(filename):
    vars = []
    tree = ET.parse(filename)
    root = tree.getroot()
    for table in root: 
        if (table.tag == "table"):
            for var in table:    
                for child in var:
                    if child.tag == "short":  
                        vars.append(child.text)
    return vars

data_cycle     = sys.argv[1] 
data_component = sys.argv[2]
data_folder    = sys.argv[3]
xml_filename   = sys.argv[4]

html_parser    = "html.parser"
print_detail_info = 1
for i in range(5, len(sys.argv)):
    if sys.argv[i] == "-parser":
        html_parser = sys.argv[i + 1]
    elif sys.argv[i] == "-nodetails":
        print_detail_info = 0        

data_components = ["Demographics", "Dietary", "Examination", "Laboratory", "Questionnaire"]
sample_weights = ["WTINT2YR", "WTMEC2YR", "WTINT4YR", "WTMEC4YR"]

xml_folder = os.path.split(xml_filename)[0]
weights_file = os.path.join(xml_folder, "weights.xml")
if os.path.exists(weights_file):
    weight_vars = get_weight_vars(weights_file)
else:
    weight_vars = []

if not data_component in data_components:
    sys.stderr.write("Error: component must be one of the following: Demographics, Dietary, Examination, Laboratory or Questionnaire\n")
    sys.exit(1)

begin_year = data_cycle.split("-")[0]
request_url = "http://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=" + data_component + "&CycleBeginYear=" + begin_year

html_doc = None
for i in range(0, 5):
    try:
        html_doc = requests.get(request_url)
        break; 
    except:
        html_doc = None          
        if i < 5 - 1: print "  Warning: Could not open " + request_url + ", will try again"
if html_doc == None:
    sys.stderr.write("Error: Failed opening " + request_url + " after 5 attempts\n")
    sys.exit(1)

html_soup = BeautifulSoup(html_doc.text, html_parser)

# Writing file in utf-8 because the input html files from
# NHANES website sometimes have characters output the ASCII range.
xml_file = codecs.open(xml_filename, "w", "utf-8")
xml_strings = []

write_xml_line('<?xml version="1.0"?>')
write_xml_line('<data name="' + data_component + '">')

# Getting all the codebooks in listed in the datapage
all_vars = []
for table in html_soup.find_all('table'): 
    links = table.find_all('a')
    for link in links: 
        codebook_url = link['href']
        path, ext = os.path.splitext(codebook_url)
        if ext.lower() == ".htm" or ext.lower() == ".html":
        
            codebook_doc = None
            for i in range(0, 5):
                try:
                    codebook_doc = requests.get(codebook_url)
                    break; 
                except:
                    codebook_doc = None          
                    if i < 5 - 1: print "  Warning: Could not open " + codebook_url + ", will try again"
            if codebook_doc == None:
                sys.stderr.write("Error: Failed opening " + codebook_url + " after 5 attempts\n")
                sys.exit(1)
            
            print "Extracting metadata from codebook " + codebook_url + "..."
            codebook_soup = BeautifulSoup(codebook_doc.text, html_parser)            
            header = codebook_soup.find("div", {"id": "PageHeader"})            
            if header == None: continue
            
            header_table_name = header.find("h3")            
            table_name = header_table_name.contents[0].strip().replace("&", "and").encode('ascii', 'ignore')
            
            header_data_file = header.find("h4")            
            data_file = header_data_file.contents[0].split(":")[1].strip()
            data_filename = os.path.splitext(data_file)[0].upper()
            csv_data_filepath = os.path.abspath(os.path.join(data_folder, data_filename + ".csv"))
            if not os.path.exists(csv_data_filepath):
                print "  Warning: data file " + csv_data_filepath + " missing, skipping codebook " + codebook_url
                continue                
            csv_data_relpath = os.path.join(data_folder, data_filename + ".csv")
            
            codebook = codebook_soup.find("div", {"id": "Codebook"})
            if codebook == None: continue
            variables = codebook.find_all("div", {"class": "pagebreak"})
            
            write_xml_line('  <table include="yes" name="' + table_name + '">')
            
            has_seqn = False
            xml_lines = []
            table_vars = []
            weight_var = ""
            
            weighted_by = ""
            if weight_vars:
                # Default weight variables
               if (data_component == "Demographics" or data_component == "Questionnaire"):
                   if "WTINT2YR" in weight_vars: weighted_by = "<weight>WTINT2YR</weight>"
               elif "WTMEC2YR" in weight_vars:
                   weighted_by = "<weight>WTMEC2YR</weight>"

            for var in variables:
                var_info = var.find("dl")
                if not var_info: 
                    print "  Warning: codebook for '" + str(var) + "' seems malformed, skipping"
                    continue 
                var_table = var.find("table")
                info = var_info.find_all("dd")
                 
                if 0 < len(info):
                    short_name = clean_xml_string(info[0].contents[0]).upper()
                else:
                    print "  Warning: variable without short name, skipping"
                    continue
                                                                                
                short_name = short_name.strip()
                if short_name == "":
                    print "  Warning: variable without short name, skipping"
                    continue

                if short_name != "SEQN" and short_name in all_vars:                                    
                    print "  Warning: variable " + short_name + " duplicated, skipping"
                    continue

                if not var_inside_file(csv_data_filepath, short_name):
                    print "  Warning: variable " + short_name + " is not included in the source datafile " + csv_data_filepath + ", skipping"
                    continue            
                    
                full_name = ""
                if 1 < len(info) and 0 < len(info[1].contents):
                    # Trying to get full name from SAS label
                    full_name = clean_xml_string(info[1].contents[0])
 
                full_name = full_name.strip()
                if full_name == "": 
                    print "  Warning: variable " + short_name + " doesn't have full name, skipping"
                    continue
                                
                if var_table == None and short_name != "SEQN":
                    print "  Warning: variable " + full_name + " (" + short_name + ") doesn't have a value table, skipping"
                    continue

                include_var = '"yes"'
                weight_var = '"no"'              
                fnl = full_name.lower()

                if -1 < fnl.find("weight") and (-1 < fnl.find("sample") or -1 < fnl.find("environmental")):                    
                    weight_var = '"yes"'

                if -1 < fnl.find("weight") and (-1 < fnl.find("interview") or -1 < fnl.find("mec") or -1 < fnl.find("sample") or -1 < fnl.find("environmental")):             
                    name_ext = os.path.split(csv_data_relpath)[1]
                    tname = name_ext.split(".")[0]
                    weight_name = short_name + "." + tname                            
                                    
                    if weight_vars and weight_name in weight_vars and data_component != "Demographics":
                        if data_component == "Dietary":
                            # Need special handling for dietary weights (the first and second day
                            # tables seem to contain the two weights)
                            tnl = table_name.lower()
                            if -1 < tnl.find("first day") and -1 < weight_name.find("WTDRD1"):
                                weighted_by = "<weight>WTDRD1." + tname + "</weight>"
                            if -1 < tnl.find("second day") and -1 < weight_name.find("WTDR2D"):
                                weighted_by = "<weight>WTDR2D." + tname + "</weight>"
                            # Don't do anything otherwise, WTMEC2YR will be used. 
                        elif -1 < short_name.find("2YR"):
                            weighted_by = "<weight>" + weight_name + "</weight>"
                    continue

                # PSU and stratum variables are not included        
                if short_name == "SDMVPSU" or short_name == "SDMVSTRA":
                    if print_detail_info: print "  Warning: Variable " + full_name + " (" + short_name + ") is not included because is a PSU or stratum variable"                
                    include_var = '"no"'    
        
                # Comment variables are not included
                if -1 < fnl.find("comment"):
                    if print_detail_info: print "  Warning: Variable " + full_name + " (" + short_name + ") is not included because it seems to be a comment variable"
                    include_var = '"no"'

                # Status code variables are not included
                if -1 < fnl.find("status code"):
                    if print_detail_info: print "  Warning: Variable " + full_name + " (" + short_name + ") is not included because it seems to be a code variable"
                    include_var = '"no"'
            
                # Flag variables are not included
                if -1 < fnl.find("imputation flag") or -1 < fnl.find("mode flag") or -1 < fnl.find(" flag "):
                    if print_detail_info: print "  Warning: Variable " + full_name + " (" + short_name + ") is not included because it seems to be a flag variable"
                    include_var = '"no"'
                     
                # Replicate numbers are not included
                if -1 < fnl.find("replicate number"):
                    if print_detail_info: print "  Warning: Variable " + full_name + " (" + short_name + ") is not included because it seems to be a replication number variable"
                    include_var = '"no"'
                    
                # Food or modification codes are not included                    
                if -1 < fnl.find("food code") or -1 < fnl.find("modification code"):
                    if print_detail_info: print "  Warning: Variable " + full_name + " (" + short_name + ") is not included because it seems to be a food or modification code variable"
                    include_var = '"no"'                    
                            
                # Repeated variables within the same table (i.e.: same quantity expressed in different units)
                # are not included. It seems that another, simpler way of finding unit duplicates is by comparing
                # the short name, because the duplicated variables seem always to be in SI units, which is indicated
                # by appending "SI" to the variable name, for example: LBDGLTSI and LBDGLT.
                repvar = repeated_var(fnl, table_vars)
                if repvar:
                    if print_detail_info: print "  Warning: Variable " + full_name + " (" + short_name + ") is not included because it seems to be a duplicate of " + repvar[1] + " (" + repvar[0] + ")"
                    include_var = '"no"'
            
                if short_name == "SEQN":
                    has_seqn = True
                    var_type = "integer"
                    var_range = "1,1000000"
                    if data_component != "Demographics":
                        # SEQN only appears in the demographics metadata
                        continue
                else:
                    (var_type, var_range) = get_variable_type_and_range(short_name, full_name, var_table, csv_data_filepath)                    
                    # Check for single value ranges, except it the variable is SDDSRVYR
                    # (Data Release Number) which it is used to aggregate cycles. 
                    if var_range and short_name != "SDDSRVYR":
                        # Check for singled-value variables
                        single_valued = False
                        if var_type == "integer" or var_type == "float":
                            values = var_range.split(",")    
                            single_valued = len(values) < 2 or values[0] == values[1]
                        elif var_type == "category":
                            values = var_range.split(";")                    
                            single_valued = len(values) < 2
                        if single_valued:
                            print "  Warning: Variable " + full_name + " (" + short_name + ") is single-valued, skipping"
                            include_var = '"no"'
                            
                if include_var == '"yes"':
                    table_vars.append([short_name, fnl]) 

                if var_type != None and var_range != None and var_type != "time" and var_type != "recorded": 
                    if short_name != "SEQN": all_vars.append(short_name)
                    xml_lines.append('    <var include=' + include_var + ' weight=' + weight_var + '><short>' + short_name + '</short><full>' + full_name + '</full><type>' + var_type + '</type><range>' + var_range + '</range>' + weighted_by + '<datafile>' + csv_data_relpath + '</datafile></var>')
                else:
                    if var_type == "time":
                        if print_detail_info: print "  Warning: Variable " + full_name + " (" + short_name + ") is a time variable, skipping because time variables are not yet supported"
                    elif var_type == "recorded":
                        if print_detail_info: print "  Warning: Variable " + full_name + " (" + short_name + ") is a recorded variable, skipping because recorded variables are not yet supported"
                    else:
                        print "  Warning: Cannot find type/range for variable " + full_name + " (" + short_name + ")"
                 
            if has_seqn:
                for line in xml_lines:
                    write_xml_line(line)
            else:             
                print "  Warning: SEQN variable not found in table " + table_name + ", skipping variables " + ",".join([nam[0] for nam in table_vars])

            write_xml_line('  </table>')            
            
write_xml_line('</data>')
xml_file.close()

# For XML validation.
try:
    doc = parseString(''.join(xml_strings))
    doc.toxml()
    print "Done."    
except:
    sys.stderr.write("XML validation error:\n")
    raise