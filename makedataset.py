'''
Runs all the steps necessary to create a Mirador dataset

@copyright: Fathom Information Design 2014
'''

import sys, os, subprocess

def load_components():
  ifile = open('components', 'rb')
  components = {}
  metadata = []
  for line in ifile.readlines():
      line = line.strip()
      if line == "" or line[0] == "#": continue
      parts = line.split()
      if len(parts) == 2:
          comp_name = parts[0]
          comp_file = parts[1]
          components[comp_name] = comp_file
          metadata.append(comp_file)
  ifile.close()
  metadata.append("weights.xml")
  return [components, metadata]

def run_command(cmd):
    sproc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sproc.wait()
    outfile.write("******************************************************************************************\n")    
    outfile.write(cmd + "\n")
    outfile.writelines(sproc.stdout.readlines())
    outfile.write("------------------------------------------------------------------------------------------\n")
    if sproc.returncode:
        print "AN ERROR OCURRED!"
        print "Command: " + cmd
        print "Error message saved to file " + error_filename 
        errorfile = open(error_filename, "w")
        errorfile.write("Command: " + cmd + "\n")
        errorfile.writelines(sproc.stderr.readlines())
        errorfile.close()
        exit(1)

cycle = sys.argv[1]

[components, metadata] = load_components()

all_files = " ".join(metadata)

output_folder = "data/mirador/" + cycle
output_filename = output_folder + "/process.out"
error_filename = output_folder + "/error.out"

print "MAKING MIRADOR DATASET FOR", cycle, "CYCLE:"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    
outfile = open(output_filename, "w")
errorfile = open(error_filename, "w")
errorfile.close()

print "OBTAINING WEIGHTS..."
outfile.write("OBTAINING WEIGHTS...\n")
cmd = "python getweights.py " + cycle + " data/sources/csv/" + cycle + " " + output_folder + "/weights.xml"
run_command(cmd)
    
print "CREATING METADATA..."
outfile.write("CREATING METADATA...\n")
for comp in components:
    xml = components[comp]
    cmd = "python makemeta.py " + cycle + " " + comp + " data/sources/csv/" + cycle + " " + output_folder + "/" + xml
    run_command(cmd)
	
print "VALIDATING METADATA..."
outfile.write("VALIDATING METADATA...\n")
for xml in metadata:
    cmd = "python checkmeta.py " + output_folder + "/" +  xml
    run_command(cmd)

print "AGGREGATING DATA..."
outfile.write("AGGREGATING DATA...\n")
cmd = "python aggregate.py " + output_folder + " " + all_files + " data.tsv"
run_command(cmd)

print "CREATING DICTIONARY..."
outfile.write("CREATING DICTIONARY...\n")
cmd = "python makedict.py " + output_folder + " " + all_files + " data.tsv dictionary.tsv"
run_command(cmd)

print "CREATING GROUPS..."
outfile.write("CREATING GROUPS...\n")
cmd = "python makegroups.py " + output_folder + " " + all_files + " groups.xml"
run_command(cmd)

print "VALIDATING DATA..."
outfile.write("VALIDATING DATA...\n")
cmd = "python checkdata.py " + output_folder + " " + all_files + " data.tsv"
run_command(cmd)

outfile.close()

print cycle,"DATASET COMPLETED."
print "Detailed messages saved to file " + output_filename
