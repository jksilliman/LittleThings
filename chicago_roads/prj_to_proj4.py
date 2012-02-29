#!/usr/bin/env python

# This script was found on the internet

import osr
import sys

def main(prj_file):
    prj_text = open(prj_file, 'r').read()
    srs = osr.SpatialReference()
    if srs.ImportFromWkt(prj_text):
        raise ValueError("Error importing PRJ information from: %s" % prj_file)
    print srs.ExportToProj4()
    #print srs.ExportToWkt()

if __name__=="__main__":
    main(sys.argv[1])
