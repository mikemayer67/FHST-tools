# FHST-tools
Suite of tools for converting Swimtopia csv files to customized reports/labels

## gen_best_times.py
This script converts a best times report exported as csv from Swimtopia into
a simple 3 column report suitable for displaying on deck.

###Usage###
```
> python gen_best_times.py [-h] best_times_csv [best_times_pdf]

Generate best times report from Swimtopia data

positional arguments:
  best_times_csv  best times csv file exported from Swimtopia
  best_times_pdf  name of output pdf file

optional arguments:
  -h, --help      show this help message and exit

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
```
