#!/bin/bash

first_year=$1
last_year=$2
last_year1=$((last_year - 1))

for (( year0=$first_year; year0<=$last_year1; year0+=2 ))
do
  year1=$((year0 + 1));
  python getdata.py $year0-$year1;
  python makedataset.py $year0-$year1;
done

python mergedatasets.py $last_year-$last_year

for (( year0=$first_year; year0<=$last_year1; year0+=2 ))
do
  year1=$((year0 + 1));
  python finaldataset.py $year0-$year1;
done

python finaldataset.py $last_year-$last_year