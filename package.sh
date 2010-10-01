#!/bin/bash

FILE='dolphin_hunter'

cat includes.py > $FILE
echo >> $FILE
cat functions.py >> $FILE
echo >> $FILE
sed -E '/^from|import|(# Local Imports)/d' < mysqlinfo.py >> $FILE
echo >> $FILE
sed -E '/^from|import|(# Local Imports)/d' < innoparse.py >> $FILE
echo >> $FILE
sed -E '/^from|improt|(# Local Imports)/d' < mysql_analyzer.py >> $FILE



#(cat includes.py;echo;sed '/^from|import/d' < mysqlinfo.py;echo;sed -E '/^(from|import)/d' < mysql_analyzer.py;sed -E '/^from|import/d' < innoparse.py) > $FILE

#(cat functions.py;echo;sed '/^from functions/d' < mysqlinfo.py;echo;sed -E '/^from (functions|mysqlinfo)/d' < mysql_analyzer.py) > exe.py

chmod +x $FILE
