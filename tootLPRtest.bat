echo on
e:
cd \tootBI
set pic=PTZ508.20240301_153305
del /q debug.pics\%pic%*
copy %pic%* E:\BlueIris\Alerts /v
sh -x ./tootLPR.sh %pic%.jpg 

pause
