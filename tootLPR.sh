#
## Usage: tootBI.sh &ALERT_PATH 
## where &ALERT_PATH is like PTZ511.20240227_160001.jpg 
##
#set -x
cd /cygdrive/e/tootBI
PATH="/usr/bin:/cygdrive/c/Program Files/Python310/Scripts:/cygdrive/c/Program Files/Python310:$PATH"
export ALERTS=/cygdrive/e/BlueIris/Alerts
export LOG=/cygdrive/e/tootBI/tootLPR.out
echo "==================================================================================" >> $LOG
date | tee -a $LOG
echo "$*" | tee -a $LOG
if [ -r "${ALERTS}/$1" ]
then
	pic=${ALERTS}/$1
else
	b=`echo $1 | cut -f1-2 -d'.'`
	pic=`ls -1tr ${ALERTS}/${b}*.jpg | tail -1`
fi
pic=`echo $pic | sed "s!/cygdrive/e!E:!g" | sed "s!/!\\\\\\!g"`

#which python
#pwd
#toot auth -i dea42.social | tee -a $LOG
toot auth
python ./tootLPR.py ${pic} 2>&1 | tee -a $LOG
