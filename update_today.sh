#!/bin/bash -v -x
COVID_REPO=/Users/wckdouglas/codes/covid19_MD
WEB_REPO=/Users/wckdouglas/codes/wckdouglas.github.io
TODAY=$(date +"%Y-%m-%d")
echo Running $TODAY

#Fetch data
cd $COVID_REPO
git pull
poetry run python dashboard.py get --date $TODAY > data/${TODAY}.tsv
echo Fetched $TODAY
git add data/${TODAY}.tsv
git commit -am "added ${TODAY}"
git push

# generate dashboard
poetry run python dashboard.py update -o /data/dashboard.html --datadir /data/data
cd $WEB_REPO
git pull
cat $COVID_REPO/dashboard.html | sed 's/<!DOCTYPE html>//g' > $WEB_REPO/_includes/COVID.html
git commit -am "updated dashboard ${TODAY}"
git push
echo Updated webpage 
