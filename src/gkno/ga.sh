#!/usr/bin/env bash

# usage -- ./ga.sh program_name
# eg.   -- ./ga.sh freebayes

if [ -z $1 ]
then
   printf "usage -- ./ga.sh program_name\n"
   printf "eg.   -- ./ga.sh freebayes\n"
   exit
fi

program=$1

#generate random number to stop caching
random=""
for i in {1..10}
do
   random="$random$((RANDOM%10))"
done

curl --get "http://www.google-analytics.com/__utm.gif?utmwv=5.3.2&utms=1&utmn=$random&utmhn=gkno8&utmsr=1440x900&utmvp=1428x288&utmsc=24-bit&utmul=en-us&utmje=1&utmfl=11.3%20r300&utmdt=crazygiftest&utmhid=1929576895&utmr=http%3A%2F%2Fwww.google.com%2Furl%3Fsa%3Dt%26rct%3Dj%26q%3D%26esrc%3Ds%26source%3Dweb%26cd%3D3%26ved%3D0CF0QFjAC%26url%3Dhttp%253A%252F%252Fautomateeverything.tumblr.com%252Fpost%252F20500736298%252Fgoogle-analytics-without-javascript-or-cookies%26ei%3DzgTrT8DyL6nr0gHMtLDIBQ%26usg%3DAFQjCNHRMDn1LH73y2SDTEskhawphhqYgQ%26sig2%3DXjqZ9TR9pTiLjGUGRHpozg&utmp=%2F$program&utmac=UA-32956625-1&utmcc=__utma%3D234084878.1276509624.1340802447.1340802447.1340808764.2%3B%2B__utmz%3D234084878.1340808764.2.2.utmcsr%3Dgoogle%7Cutmccn%3D(organic)%7Cutmcmd%3Dorganic%7Cutmctr%3D(not%2520provided)%3B&utmu=q~"