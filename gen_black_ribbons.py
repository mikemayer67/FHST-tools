#!/usr/bin/env python

import argparse
import csv
import sys
import re
import os.path

from fpdf import FPDF

############################################################
# CSV Input Columns
############################################################

LeadColumns = (
    'AgeGroup',
    'AthleteId',
    'LastName',
    'FirstName',
    'LastName_FirstName',
    'Age',
    'EventDistance',
    'EventStroke',
    )
TailColumns = (
    'TotalResults',
    'TotalImproved',
    'TotalPoints',
    'AmountImprovedSec',
    'PercentImproved',
    )
MeetColumns = (
    'Name',
    'Result',
    'ResultSec',
    'Improved',
    'Points',
    'Date',
    )

############################################################
# Stroke Names
############################################################

_StrokeNames = {
    'free':'Freestyle',
    'back':'Backstroke',
    'breast':'Breaststroke',
    'fly':'Butterfly',
    'im':'Individual Medley',
    }


############################################################
# Avery Labels 8160
#   left/right margins = 3/16"
#   top/bottom margins = 0.5"
#   label width  = 2 5/8"
#   label height = 1"
############################################################

# internally, FPDF uses millimeters, but Avery reports label
#   offsets and sizes in inches. We will let python do the
#   conversions for us.  One inch = 25.4 mm 
_inch = 25.4 

_PageFormat = "Letter"
_PageHeight = 11.0 * _inch
_PageWidth  =  8.5 * _inch

_LeftRightMargin = 0.1825 * _inch
_TopBottomMargin = 0.5    * _inch

_LeftEdge    = _LeftRightMargin
_TopEdge     = _TopBottomMargin

_LabelWidth  = 2.625  * _inch
_LabelHeight = 1.0    * _inch

_NumColumns =  3
_NumRows    = 10

_ExcessWidth = _PageWidth - 2*_LeftRightMargin - _NumColumns*_LabelWidth
_WidthGap    = _ExcessWidth / (_NumColumns-1)

_ExcessHeight = _PageHeight - 2*_TopBottomMargin - _NumRows*_LabelHeight
_HeightGap    = _ExcessHeight / (_NumRows-1)

############################################################
# Label Formatting
############################################################
# We will be laying out the label as depicted below:
#
#   +---------------------------------------------+
#   | Swimmer Name (age)                          |
#   +---------------------------------+-----------+
#   | Event                           | Date      |
#   +---------------------------------+-----------+
#   | Meet Name                                   |
#   +-------------------------------+-------------|
#   + New Best Time                 | Delta Time  |
#   +-------------------------------+-------------|
#
_LabelTopMargin    = 0.125 * _inch
_LabelBottomMargin = 0.125  * _inch
_LabelLeftMargin   = 0.25  * _inch
_LabelRightMargin  = 0.25  * _inch

_NameFont  = ['Times','B',10]
_EventFont = ['Times','',10]
_DateFont  = ['Times','',10]
_MeetFont  = ['Times','',10]
_TimeFont  = ['Times','B',10]

_DateWidth = 0.5 * _inch
_DeltaWidth = 0.5 * _inch
_CellPad = 1

############################################################
# Data Parsing
############################################################

_NumLeadColumns = len(LeadColumns)
_NumTailColumns = len(TailColumns)
_NumColumnsPerMeet = len(MeetColumns)


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

        n_col = len(header)
        n_overhead = _NumLeadColumns + _NumTailColumns
        n_meet_col = n_col - n_overhead

        assert n_meet_col >= _NumColumnsPerMeet, (
            "Athlete report card file should have at least "
            f"{_NumColumnsPerMeet + n_overhead} columns of data")

        n_meet, n_extra = divmod(n_meet_col, _NumColumnsPerMeet)
            
        assert n_extra == 0, (
            f"Athlete report card file should have {_NumColumnsPerMeet} columns per meet" )

        expected_columns = (
            LeadColumns +
            tuple( f"Meet{i+1}-{mc}" for i in range(n_meet) for mc in MeetColumns ) +
            TailColumns )

        for i,(found,expected) in enumerate(zip(header,expected_columns)):
            assert found==expected, (
                f"Column {i+1} should be {expected}, not {found}" )

    except Exception as e:
        print(f"Sorry:: {src} does not appear to be properly formatted:\n\n {e}")
        sys.exit(1)

    meets = [None for i in range(n_meet)]
    for line in lines:
        for i in range(n_meet):
            start = _NumLeadColumns + i*_NumColumnsPerMeet
            end   = start + _NumColumnsPerMeet
            (meet_name, result, _, _, _, date) = line[start:end]

            if meet_name and result and meets[i] is None:
                meets[i] = (meet_name, date)

    return meets, lines


def gen_unformatted_labels(data,meet):
    labels = list()
    for line in data:
        label = gen_unformatted_label(line,meet)
        if label:
            labels.append(label)

    return labels

def gen_unformatted_label(line,meet):
    (age_group, _, last_name, first_name, _, age, distance, stroke) = line[:8]

    times = tuple( line[_NumLeadColumns + 2 + i*_NumColumnsPerMeet]
        for i in range(meet+1)
        )

    meet_time = times[-1]

    if not meet_time:
        return None

    meet_time = float(meet_time)

    prior_times = tuple(float(t) for t in times[:-1] if t)
    if not prior_times:
        return None

    prior_best = min(prior_times)
    if meet_time >= prior_best:
        return None

    date = line[_NumLeadColumns + 5 + meet*_NumColumnsPerMeet]

    return { 
        'meet':meet,
        'swimmer':f"{first_name} {last_name} ({age})", 
        'age_group':age_group, 
        'distance':distance, 
        'stroke':stroke,
        'new_time':meet_time,
        'time_drop':prior_best - meet_time,
        }


############################################################
# Meet Information
############################################################

def show_meets(meets):
    print("\nMeets")
    for i, meet in enumerate(meets[1:]):
        if meet:
            print(f"  {i+1:2} - {meet[1]} {meet[0]}")

def validate_selected_meet(meets, meet_number):
    try:
        meet_info = meets[meet_number]
        assert meet_info is not None
    except:
        print("")
        print(f"Sorry:: there is no meet #{meet_number}")
        print("")
        print("  Rerun with the --list argument to see list of meets")
        sys.exit(1)

def select_latest_meet(meets,src):
    weeks = tuple(i for i,v in enumerate(meets) if v)
    if len(weeks) < 2:
        print("")
        print(f"Sorry:: cannot find any meet data in {src}")
        sys.exit(1)
    return max(weeks)


############################################################
# Formatted Report Generation
############################################################

def format_time(t):
    if t >= 60:
        (m,s) = divmod(t,60)
        return f"{int(m)}:{s:05.2f}"
    else:
        return f"{t:.2f}"

def gen_formatted_labels(labels,meets,dst):

    pdf = FPDF(format=_PageFormat)

    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    line_height = (_LabelHeight - _LabelTopMargin - _LabelBottomMargin) / 4
    line_width  = (_LabelWidth - _LabelLeftMargin - _LabelRightMargin)

    r = 0
    c = 0
    for label in labels:
        (meet_name,meet_date) = meets[label["meet"]]

        x = _LeftEdge + c*(_LabelWidth + _WidthGap) + _LabelLeftMargin
        y = _TopEdge + r*(_LabelHeight + _HeightGap) + _LabelTopMargin

        pdf.set_font(*_NameFont)
        pdf.set_xy(x,y)
        pdf.cell(line_width, line_height, label['swimmer'])

        y += line_height

        distance = label['distance']
        stroke = _StrokeNames[label['stroke'].lower()]

        event = f"{distance}M {stroke}"
        pdf.set_font(*_EventFont)
        pdf.set_xy(x,y)
        pdf.cell(line_width-_DateWidth-_CellPad,line_height,event)

        pdf.set_font(*_DateFont)
        pdf.set_x(x + line_width - _DateWidth)
        pdf.cell(_DateWidth, line_height, meet_date)

        y += line_height

        pdf.set_font(*_MeetFont)
        pdf.set_xy(x,y)
        pdf.cell(line_width,line_height,meet_name)

        y += line_height

        pdf.set_font(*_TimeFont)
        pdf.set_xy(x,y)
        new_time = format_time(label['new_time'])
        pdf.cell(line_width - _DeltaWidth - _CellPad, line_height, new_time)

        pdf.set_font(*_TimeFont)
        pdf.set_xy(x+line_width-_DeltaWidth,y)
        time_drop = format_time(label['time_drop'])
        pdf.cell(_DeltaWidth, line_height, f"-{time_drop}S")

        r += 1
        if r == _NumRows:
            r = 0
            c += 1
            if c == _NumColumns:
                c = 0
                pdf.add_page()

    pdf.output(dst,'F')

############################################################
# Main
############################################################

def main(src, *, dst=None, meet=None, show_list=False ):
    meets, data = read_data(src)

    if show_list:
        show_meets(meets)
        sys.exit(0)

    if meet:
        validate_selected_meet(meets,meet)
    else:
        meet = select_latest_meet(meets, src)

    labels = gen_unformatted_labels(data,meet)
    gen_formatted_labels(labels,meets,dst)
    

def parse_args():
    epilog = """
    To create the input CSV file:
        Go to Reports in Swimtopia
        Select Athlete Report Card under Athlete Performance.  

        Make sure the following criteria are set:
          Season Roster: current year
          Gender: All
          Min/Max Age: leave blank
          Show times in course: S - Short Course Meters
          All other options: leave unchecked

        Click on the "Generate Report" button
        Click on the "Download Athlete Report Card Data CSV" link
    """
    parser = argparse.ArgumentParser(
        description='Generate black ribbon labels from Swimtopia data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )
    parser.add_argument(
        'src',
        metavar='athlete_report_card_csv',
        help='athlete report card csv file exported from Swimtopia',
    )

    parser.add_argument(
        'dst',
        nargs='?',
        default='black_ribbons.pdf',
        metavar='black_ribbons_pdf',
        help='name of output pdf file',
    )

    def _positive(value):
        try:
            value=int(value)
            assert value >= 1
        except:
            raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
        return value

    parser.add_argument(
        '--meet', '-m',
        type=_positive,
        default=None,
        help='meet number for which to generate black ribbons',
        )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        default=False,
        help='list meet information rather than create ribbons',
        )

    return parser.parse_args()

 
if __name__ == "__main__":
    args = parse_args()

    kwargs = dict()
    if args.dst:
        kwargs['dst'] = args.dst
    if args.meet:
        kwargs['meet'] = args.meet
    if args.list:
        kwargs['show_list'] = args.list

    main(args.src, **kwargs)
  
