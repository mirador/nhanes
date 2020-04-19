'''
Cleans up the folder of a Mirador dataset and any required adds configuration files, 
leaving it ready for distribution

@copyright: Fathom Information Design 2014
'''

import sys, os
import shutil

def load_workfiles():
  ifile = open('components', 'r')
  workfiles = []
  for line in ifile.readlines():
      line = line.strip()
      if line == "" or line[0] == "#": continue
      parts = line.split()
      if len(parts) == 2:
          workfiles.append(parts[1])
  ifile.close()
  workfiles.append("weights.xml")
  workfiles.append("weights.csv")  
  workfiles.append("weights.list")    
  return workfiles

cycle = sys.argv[1]
keep_workfiles = False
if len(sys.argv) == 3 and sys.argv[2] == '-keep':
    keep_workfiles = True

[year0, year1] = cycle.split("-")
year_diff = int(year1) - int(year0)

workfiles = load_workfiles()

output_folder = "data/mirador/" + cycle
output_filename = output_folder + "/process.out"
error_filename = output_folder + "/error.out"

print("PREPARING", cycle, "MIRADOR DATASET FOR RELEASE...")

if not keep_workfiles:
    # Removing temporary work files...
    if os.path.isfile(output_filename):
        os.remove(output_filename)
    if os.path.isfile(error_filename):
        os.remove(error_filename)
    for work in workfiles:
        work_filename = output_folder + "/" + work
        if os.path.isfile(work_filename):
            os.remove(work_filename)

# Creating Mirador configuration file
template_config = "config.mira"
project_config = output_folder + "/" + "config.mira"

template_file = open(template_config, 'r')
project_file = open(project_config, 'w')
lines = template_file.readlines()
for line in lines:
    line = line.strip()
    if line == "project.title=":
        line = line + "NHANES cycle " + cycle
    elif line == "project.url=":
        if year_diff == 1:
            y0 = year0[2:4]
            y1 = year1[2:4]
            line = line + "http://wwwn.cdc.gov/nchs/nhanes/search/nhanes" + y0 + "_" + y1 + ".aspx"
        else: 
            continue
    project_file.write(line + '\n') 
template_file.close()
project_file.close()

print(cycle, "DATASET READY.")
