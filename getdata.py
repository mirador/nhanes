'''
Downloads all the NHANES XPT files for a specific cycle, and converts them into CSV 
files for subsequent parsing. 

@copyright: Fathom Information Design 2014
'''

import sys, os, subprocess

def run_command(cmd):
    sproc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sproc.wait()
    outfile.write("******************************************************************************************\n")    
    outfile.write(cmd + "\n")
    outfile.writelines(sproc.stdout.readlines())
    outfile.write("------------------------------------------------------------------------------------------\n")
    outfile.close()
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

ftp_folder = "ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/nhanes/" + cycle
xpt_folder = "data/sources/xpt/" + cycle
csv_folder = "data/sources/csv/" + cycle

print "GETTING NHANES FILES FOR", cycle, "CYCLE:"

if not os.path.exists(xpt_folder):
    os.makedirs(xpt_folder)

if not os.path.exists(csv_folder):
    os.makedirs(csv_folder)
    
output_filename = xpt_folder + "/process.out"
error_filename = xpt_folder + "/error.out"

outfile = open(output_filename, "w")
errorfile = open(error_filename, "w")
errorfile.close()

print "DOWNLOADING XPT FILES..."
outfile.write("DOWNLOADING XPT FILES...\n")
cmd = "python download.py " + ftp_folder + " " + xpt_folder
run_command(cmd)

output_filename0 = output_filename
output_filename = csv_folder + "/process.out"
error_filename = csv_folder + "/error.out"

outfile = open(output_filename, "w")
errorfile = open(error_filename, "w")
errorfile.close()

print "CONVERTING XPT FILES TO CSV..."
outfile.write("CONVERTING XPT FILES TO CSV...\n")
cmd = "python xpt2csv.py " + xpt_folder + " " + csv_folder
run_command(cmd)

print cycle,"DOWNLOAD AND CONVERSION COMPLETED."
print "Detailed messages saved to files " + output_filename0 + " and " + output_filename