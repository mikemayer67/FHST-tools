#!/usr/bin/env python

import argparse
import csv
import sys
import re
import os.path
import datetime

from fpdf import FPDF


############################################################
# CSV Input File
############################################################
ExpectedColumns = [
    'AgeGroup',
    'FirstName',
    'LastName',
    'Age',
    'Event',
    'Time',
    'ConvertedTime',
    'ConvertedHundredths',
    'Date',
    'SwimMeet',
]
############################################################
# MCSL Specfic Events Data
############################################################

_AgeGroups = [
    'Girls 8 & Under',
    'Boys 8 & Under',
    'Girls 9-10',
    'Boys 9-10',
    'Girls 11-12',
    'Boys 11-12',
    'Girls 13-14',
    'Boys 13-14',
    'Women 15-18',
    'Men 15-18',
]

_EventNames = (
    'Freestyle',
    'Backstroke',
    'Breaststroke',
    'Butterfly',
    'Individual Medley',
)

_EventDistances = {
    'Freestyle':         [25, 50, 100],
    'Backstroke':        [25, 50, 100], 
    'Breaststroke':      [25, 50, 100],
    'Butterfly':         [25, 50],
    'Individual Medley': [100],
}

_AgeDistances = {
    'Girls 8 & Under': [ 25,  25,  25,  25, 100],
    'Boys 8 & Under':  [ 25,  25,  25,  25, 100],
    'Girls 9-10':      [ 50,  25,  25,  25, 100],
    'Boys 9-10':       [ 50,  25,  25,  25, 100],
    'Girls 11-12':     [ 50,  50,  50,  50, 100],
    'Boys 11-12':      [ 50,  50,  50,  50, 100],
    'Girls 13-14':     [ 50,  50,  50,  50, 100],
    'Boys 13-14':      [ 50,  50,  50,  50, 100],
    'Women 15-18':     [100, 100, 100,  50, 100],
    'Men 15-18':       [100, 100, 100,  50, 100],
}

_AgeEvents = {
    ag:[f"{d} {e}" for e,d in zip(_EventNames, _AgeDistances[ag])] 
    for ag in _AgeGroups
}

_AllEvents = tuple(f"{d} {e}" for e in _EventNames for d in _EventDistances[e])

############################################################
# Output page layout
############################################################

_PageFormat = "Letter"

_LeftEdge   =  10
_RightEdge  = 205
_TopEdge    =  30
_BottomEdge = 260

_HeaderPad    = 5
_HeaderHeight = 10

_FooterPad    = 5 
_FooterHeight = 10

_ColumnCount = 3
_ColumnPad = 2

_TimeWidth = 12

_HeaderFont   = ['Times','B',16]
_FooterFont   = ['Times','',12]
_AgeGroupFont = ['Times','B',12]
_EventFont    = ['Times','B',10]
_ContFont     = ['Times','I',12]
_SwimmerFont  = ['Times','',9]

_AgeGroupHeight = 8
_EventHeight    = 5
_SwimmerHeight  = 3.5

_AgeGroupIndent = _ColumnPad
_EventIndent    = _AgeGroupIndent + 5
_SwimmerIndent  = _EventIndent + 5

_AgeGroupPad = 3
_EventPad    = 2
_CellPad     = 1
_ContPad     = 2

############################################################
# Data Parsing
############################################################

def read_data(src):
    lines = list()
    try:
        with open(src,mode='r') as file:
            reader = csv.reader(file)
            lines = [line for line in reader]
    except FileNotFoundError:
        print(f"Sorry:: Could not find {src}")
        sys.exit(1)
    except Exception as e:
        print(f"Sorry:: Failed to parse {src}: {e}")
        sys.exit(1)

    header = lines[:1][0]
    lines = lines[1:]

    try:
        n_expected_columns = len(ExpectedColumns)
        assert len(header) == n_expected_columns, (
            f"Best times file should have {n_expected_columns} columns of data"
        )
        for i,(found,expected) in enumerate(zip(header,ExpectedColumns)):
            assert found==expected, f"Column {i+1} should be {expected}, not {found}"
    except Exception as e:
        print(f"Sorry:: {src} does not appear to be properly formatted:\n\n {e}")
        sys.exit(1)

    data = {
        ag:{e:list() for e in _AgeEvents[ag]}
        for ag in _AgeGroups
    }

    for line in lines:
        (age_group, first_name, last_name, age, event, _, _, time, date, _) = line

        assert age_group in _AgeGroups, f"Unrecognized age group in data: {age_group}"

        swimmer = f"{first_name} {last_name} ({age})"
        time = int(time)/100

        if age_group not in data:
            raise KeyError(f"Unrecognized age_group: {age_group}")

        if event not in data[age_group]:
            print(f"Swim up is adding {event} to {age_group}")
            data[age_group][event] = list()

        data[age_group][event].append( (swimmer, time, date) )

    return data


def gen_unformatted_report(data):
    return [ (ag, gen_unformatted_events(data[ag]))
        for ag in _AgeGroups
    ]

def gen_unformatted_events(data):
    return [ (e, gen_unformatted_swimmers(data[e]))
            for e in _AllEvents 
            if e in data
           ]

def gen_unformatted_swimmers(data):
    return sorted(data,key=lambda x:x[1])


############################################################
# Formatted Report Generation
############################################################

class PDF(FPDF):
    def header(self):
        self.set_font(*_HeaderFont)
        self.set_y(_HeaderPad + _HeaderHeight)
        self.cell( 0, _HeaderHeight,
            f"Flower Hill Dolphins Top Times",
            align='C',
            )

    def footer(self):
        now = datetime.datetime.now()
        now = now.strftime("%A %B %d, %Y  at  %-I:%H %p")
        self.set_font(*_FooterFont)
        self.set_y(-_FooterPad-_FooterHeight)
        self.cell(0,_FooterHeight, f"Page {self.page_no()}", align='R')
        self.set_y(-_FooterPad-_FooterHeight)
        self.cell(0,_FooterHeight, f"Generated: {now}")

def format_time(t):
    if t >= 60:
        (m,s) = divmod(t,60)
        return f"{int(m)}:{s:05.2f}"
    else:
        return f"{t:.2f}"

def add_page(pdf, w_col, age_group=None):
    pdf.add_page()

    for i in range(1,_ColumnCount):
        x = _LeftEdge + i*w_col
        pdf.line(x, _TopEdge, x, _BottomEdge)

    if age_group:
        pdf.set_font(*_AgeGroupFont)
        pdf.set_xy(_LeftEdge +_AgeGroupIndent, _TopEdge)
        pdf.cell(w_col-_AgeGroupIndent, _AgeGroupHeight, age_group)

        dx = pdf.get_string_width(age_group) + _ContPad
        pdf.set_x(_LeftEdge + _AgeGroupIndent + dx)
        pdf.set_font(*_ContFont)
        pdf.cell(w_col - _AgeGroupIndent - dx, _AgeGroupHeight, '(cont)')

def gen_formatted_report(data,dst):

    pdf = PDF(format=_PageFormat)

    w_col = (_RightEdge - _LeftEdge) // _ColumnCount

    add_page(pdf,w_col)

    c = 0
    x = _LeftEdge
    y = _TopEdge
    for ag,events in data:
        # jump to next column/page if necessary
        nswimmers = len(events[0][1])
        required_height = (
            _AgeGroupHeight + _EventHeight + _EventPad + nswimmers * _SwimmerHeight 
            )
        if y + required_height > _BottomEdge:
            c += 1
            x += w_col
            y = _TopEdge
            if c > 2:
                add_page(pdf,w_col)
                c = 0
                x = _LeftEdge

        # add age group header to output
        pdf.set_font(*_AgeGroupFont)
        pdf.set_xy(x + _AgeGroupIndent, y)
        pdf.cell(w_col-_AgeGroupIndent, _AgeGroupHeight, ag)
        y += _AgeGroupHeight

        for event,swimmers in events:
            # jump to next column/page if necessary
            nswimmers = len(swimmers)
            required_height = _EventHeight + _EventPad + nswimmers * _SwimmerHeight
            if y + required_height > _BottomEdge:
                c += 1
                x += w_col
                y = _TopEdge
                if c > 2:
                    add_page(pdf,w_col,age_group=ag)
                    c = 0
                    x = _LeftEdge
                    y += _AgeGroupHeight

            pdf.set_font(*_EventFont)
            pdf.set_xy(x+_EventIndent,y)
            pdf.cell(w_col-_EventIndent,_EventHeight,event)
            y += _EventHeight

            for name, time, _ in swimmers:
                pdf.set_font(*_SwimmerFont)
                w_name = w_col - (_SwimmerIndent + _TimeWidth + _CellPad + _ColumnPad)
                w_actual = pdf.get_string_width(name)
                if w_actual > w_name:
                    scaled_size = _SwimmerFont[2] * w_name / w_actual
                    pdf.set_font( _SwimmerFont[0], _SwimmerFont[1], scaled_size)
                pdf.set_xy(x + _SwimmerIndent, y)
                pdf.cell(w_name, _SwimmerHeight, name)

                pdf.set_font(*_SwimmerFont)
                pdf.set_x(x + w_col - _TimeWidth - _ColumnPad)
                pdf.cell(_TimeWidth, _SwimmerHeight, format_time(time),align="R")
                y += _SwimmerHeight

            y += _EventPad
        y += _AgeGroupPad

    pdf.output(dst,'F')


############################################################
# Main
############################################################

def main():
    args = parse_args()
    data = read_data(args.src)
    report = gen_unformatted_report(data)
    gen_formatted_report(report,args.dst)

def parse_args():
    epilog = """
    To create the input CSV file:
        Go to Reports in Swimtopia
        Select Best Times under Athlete Performance.  

        Make sure the following criteria are set:
          Season Roster: current year
          Limit results to course: S - Short Course Meters
          Convert times to: S - Short Course Meters
          Only show times from: Selected season

        Click on the "Generate Report" button
        Click on the "Download CSV" button
    """
    parser = argparse.ArgumentParser(
        description='Generate best times report from Swimtopia data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )
    parser.add_argument(
        'src',
        metavar='best_times_csv',
        help='best times csv file exported from Swimtopia',
    )

    parser.add_argument(
        'dst',
        nargs='?',
        default=None,
        metavar='best_times_pdf',
        help='name of output pdf file',
    )

    args = parser.parse_args()
    if args.dst is None:
        (root,ext) = os.path.splitext(args.src)
        args.dst = f"{root}.pdf"

    return args

 
if __name__ == "__main__":
    main()
  
