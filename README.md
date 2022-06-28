# FHST-tools
Suite of tools for converting Swimtopia csv files to customized reports/labels

There are currently two tools (*detailed below*)
- **gen_best_times.py**: 
  
  converts a best times report exported as csv from Swimtopia into a simple 3 column report suitable for displaying on deck
  
- **gen_black_ribbons.py**: 
  
  parses the athelete report cards and creates sheets of black ribbon labels for the latest (or specified) meet

***

## gen_best_times.py

### Usage
```
> python gen_best_times.py [-h] best_times_csv [best_times_pdf]

Generate best times report from Swimtopia data

positional arguments:
  best_times_csv  best times csv file exported from Swimtopia
  best_times_pdf  name of output pdf file

optional arguments:
  -h, --help      show this help message and exit
```
### Input Data Generation

1. Log into Swimtopia as user with permission to manage the team
1. Go to Reports
1. Select Best Times under Athlete Performance.
1. Make sure the following criteria are set:
   * Season Roster: current year
   * Limit results to course: S - Short Course Meters
   * Convert times to: S - Short Course Meters
   * Only show times from: Selected season
1. Click on the "Generate Report" button
1. Click on the "Download CSV" button

*Keep track of where you downloaded the .csv file.  That is what you'll provide on input to this tool.*

## gen_black_ribbons.py

### Usage
```
> usage: gen_black_ribbons.py [-h] [--meet MEET] [--list]
                            athlete_report_card_csv [black_ribbons_pdf]
                            
Generate black ribbon labels from Swimtopia data

positional arguments:
  athlete_report_card_csv
                        athlete report card csv file exported from Swimtopia
  black_ribbons_pdf     name of output pdf file

optional arguments:
  -h, --help            show this help message and exit
  --meet MEET, -m MEET  meet number for which to generate black ribbons
  --list, -l            list meet information rather than create ribbons
```

By default, this tool will produce black ribbon labels for the most 
recent meet.  You can, however specify an earlier meet by specifying
the meet number (*as Swimtopia numbers them*).  You can find the
meet numbers by running this script with the --list option.


### Input Data Generation

1. Log into Swimtopia as user with permission to manage the team
1. Go to Reports
1. Select Athlete Report Card under Athlete Performance.
1. Make sure the following criteria are set:
   * Season Roster: current year
   * Gender: All
   * Min/Max Age: leave blank
   * Show times in course: S - Short Course Meters
   * All other options: leave unchecked
1. Click on the "Generate Report" button
1. Click on the "Download Athlete Report Card Data CSV" link

*Keep track of where you downloaded the .csv file.  That is what you'll provide on input to this tool.*
