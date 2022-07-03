#!/usr/bin/env python
import csv
import sys
import re
import os.path
import glob
import subprocess

from gen_best_times import ExpectedColumns as BestTimesColumns
from gen_black_ribbons import LeadColumns as BlackLeadColumns
from gen_black_ribbons import TailColumns as BlackTailColumns
from gen_black_ribbons import MeetColumns as BlackMeetColumns

def is_best_times_file(file):
    try:
        with open(file,mode='r') as f:
            reader = csv.reader(f)
            header = next(reader)
        assert len(header) == len(BestTimesColumns)
        for found,expected in zip(header,BestTimesColumns):
            assert found == expected
    except:
        return False
    return True
        
def validate_black_ribbon_file(file):
    try:
        with open(file,mode='r') as f:
            reader = csv.reader(f)
            header = next(reader)

            n_lead = len(BlackLeadColumns)
            n_tail = len(BlackTailColumns)
            n_meet = len(BlackMeetColumns)
            n_meet_columns = len(header) - n_lead - n_tail
            assert n_meet_columns > 0
            n_meets,n_extra = divmod(n_meet_columns,n_meet)
            assert n_extra == 0

            meet_columns = tuple( 
                f"Meet{i+1}-{mc}" 
                for i in range(n_meets) 
                for mc in BlackMeetColumns )

            expected_columns = (
                BlackLeadColumns + meet_columns + BlackTailColumns )
            for found,expected in zip(header,expected_columns):
                assert found == expected

            meets_in_file = dict()
            for line in reader:
                for meet in range(n_meets):
                    if line[n_lead + 2 + meet*n_meet]:
                        if meet not in meets_in_file:
                            meets_in_file[meet] = line[n_lead + meet*n_meet]

    except:
        return None
    else:
        return meets_in_file
    

best_times_file = None
best_times_mtime = 0
black_ribbon_file = None
black_ribbon_meets = None

csv_dir = os.path.dirname(os.path.abspath(__file__))
for file in glob.glob(f"{csv_dir}/*.csv"):
    if is_best_times_file(file):
        s = os.stat(file)
        if s.st_mtime > best_times_mtime:
            best_times_mtime = s.st_mtime
            best_times_file = file
    else:
        meets = validate_black_ribbon_file(file)
        if meets:
            if black_ribbon_file:
                if max(meets.keys()) > max(black_ribbon_meets.keys()):
                    black_ribbon_file = file
                    black_ribbon_meets = meets
            else:
                black_ribbon_file = file
                black_ribbon_meets = meets


assert best_times_file, f"No best times file found in {csv_dir}"
assert black_ribbon_file, f"No athlete report card found in {csv_dir}"

pdf_out = f"{csv_dir}/best_times.pdf"
cmd = ["python3"] + [f"{csv_dir}/gen_best_times.py",best_times_file, pdf_out]
subprocess.run(cmd,capture_output=True)
    
for meet,name in black_ribbon_meets.items():
    if meet == 0: continue
    name = name.lower().split(" ")
    ab = name[0]
    name = '_'.join(name[3:])
    pdf_out = f"{csv_dir}/black_ribbons_{ab}_{name}.pdf"
    cmd = ["python3"] + [f"{csv_dir}/gen_black_ribbons.py",black_ribbon_file, pdf_out,"--meet",str(meet)]
    subprocess.run(cmd,capture_output=True)

