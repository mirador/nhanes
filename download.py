'''
Downloads all the XPT files in the specified URL, and stores them in the
destination folder. Two arguments are mandatory: first: the source url,
and second, the destination folder. 

@copyright: Fathom Information Design 2014
'''

import sys
from ftplib import FTP
import os.path

def download_binary(block):
    ofile.write(block)

# src_url should be a string of the form:
# "ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/nhanes/2009-2010/"
src_url  = sys.argv[1]
dest_dir = sys.argv[2]

if src_url[len(src_url) - 1] != '/': src_url = src_url + '/'
if dest_dir[len(dest_dir) - 1] != '/': dest_dir = dest_dir + '/'

if src_url.find("ftp://") == 0:
    # Chopping off the protocol string
    src_url = src_url[6:len(src_url)]

n = src_url.find("/")
ftp_host = src_url[0:n]
src_dir  = src_url[n:len(src_url)]

# Anonymoyus login to the provided host
print "Opening connection with", ftp_host, "..."
ftp = FTP(ftp_host)
ftp.login()
print "Done."

print "Getting XPT files..."

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

files = ftp.nlst(src_dir)
for f in files:
    name = os.path.split(f)[1]
    ext  = os.path.splitext(name)[1].lower()   
    if ext == ".xpt":    
        fn = os.path.join(dest_dir, name)
        print "  ", f, "..."
        ofile = open(fn, "wb")
        
        for i in range(0, 5):
            try:
                ftp.retrbinary("RETR " + f, download_binary)
                break; 
            except:
                if i < 5 - 1: print "  Could not open",f,"at",ftp_host,", will try again"
                else:
                    print "  Failed opening",f,"at",ftp_host,"after 5 attempts, canceling!"
                    sys.exit()

        ofile.close()

ftp.close()
print "Done."


