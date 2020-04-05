'''
Downloads all the XPT files in the specified URL, and stores them in the
destination folder. Two arguments are mandatory: first: the desired NHANES cycle,
and second, the destination folder. 

@copyright: Fathom Information Design 2014
'''

import sys
import os.path
from bs4 import BeautifulSoup
import requests
import urllib

def request_file(src_url, dest_fn):
    try:
        r = requests.get(src_url, stream = True)
        with open(dest_fn, 'wb') as f:
            for ch in r:
                f.write(ch)
    except:
        print("  Failed downloading file", src_url, ", canceling!")
        sys.exit()

components = ["Demographics", "Dietary", "Examination", "Laboratory", "Questionnaire"]

cycle = sys.argv[1]
dest_dir = sys.argv[2]

begin_year = cycle.split('-')[0]

print("Getting XPT files for cycle " + cycle + "...")

base_url = "https://wwwn.cdc.gov"
url_template = "https://wwwn.cdc.gov/nchs/nhanes/Search/DataPage.aspx?Component=${comp}&CycleBeginYear=${year}"

for comp in components:
    url = url_template.replace("${comp}", comp).replace("${year}", begin_year)
    print(comp, "component")
    content = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(content, features="lxml")
    table = soup.find( "table")
    
    for a in table.find_all("a", href=True):
        url = a["href"]
        name = os.path.split(url)[1]
        ext  = os.path.splitext(name)[1].lower()
        if ext == ".xpt":
            dest_fn = os.path.join(dest_dir, name)
            full_url = base_url + url
            print("  ", full_url, "...", dest_fn)
            request_file(full_url, dest_fn)

print("Done.")