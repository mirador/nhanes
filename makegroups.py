'''
Creates the groups file from the input metadata

@copyright: Fathom Information Design 2014
'''

import sys, os, codecs
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET

def write_xml_line(line):
    xml_file.write(line + '\n')
    xml_strings.append(line + '\n')

def get_variable(xml):
    vname = ""
    valias = ""    
    
    for child in xml:
        if child.tag == "short":
            vname = child.text
        if child.tag == "full":
            valias = child.text

    return [vname, valias]

argc = len(sys.argv)
data_folder = sys.argv[1]
in_metadata = sys.argv[2:argc - 1]
groups_file = sys.argv[argc - 1]

xml_filename = os.path.abspath(os.path.join(data_folder, groups_file))

# Writing file in utf-8 because the input html files from
# NHANES website sometimes have characters output the ASCII range.
xml_file = codecs.open(xml_filename, "w", "utf-8")
xml_strings = []

write_xml_line('<?xml version="1.0" encoding="utf-8" ?>')

print("Creating groups file...")
write_xml_line('<data>')
for meta in in_metadata:
    xml_filename = os.path.abspath(os.path.join(data_folder, meta))  
    tree = ET.parse(xml_filename)
    root = tree.getroot()
    print(root.attrib["name"], str(root.attrib["name"]))
    write_xml_line(' <group name="' + str(root.attrib["name"]) + '">')
    for el in root:      
        if (el.tag == "table"):
          if el.attrib["include"] != "yes": continue
          print(el.attrib["name"], str(el.attrib["name"]))     
          write_xml_line('  <table name="' + str(el.attrib["name"]) + '">')
          for child in el: 
              if child.tag == "var":
                  if child.attrib["include"] == "yes":
                      [name, alias] = get_variable(child)
                      write_xml_line('   <variable name="' + str(name) + '"/>')
          write_xml_line('  </table>')                      
    write_xml_line(' </group>')
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
