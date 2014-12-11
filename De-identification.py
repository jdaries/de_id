# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

%cd ../person_course/

# <headingcell level=4>

# Import de-identification functions from datafly_v4.py

# <codecell>

from datafly_v4 import *
import numpy as np
import pylab as P
import pandas as pd
from decimal import *

# <codecell>

def utilValues(cursor, tableName, varName):
    """
    cursor: sqlite cursor object
    tableName: string, name of sqlite table
    varName: string, name of variable to analyze
    takes values of an integer or float variable and returns the 
    mean, standard deviation, and entropy
    """
    entQry = selUnique(cursor, tableName, varName)
    entropy = shannonEntropy(entQry)
    cursor.execute("SELECT "+varName+" FROM "+tableName)
    qry = cursor.fetchall()
    qry = colToList(qry)
    qry2 = textToFloat(qry)
    if len(qry2)==0:
        print "No values could be converted to numbers"
        return
    qryArray = np.array(qry2)
    mean = qryArray.mean()
    sd = qryArray.std()
    return entropy, mean, sd

# <codecell>

def binAvg(cursor, tableName, nomVarName, numVarName):
    """
    cursor: sqlite cursor object
    tableName: string, name of sqlite table
    nomVarName: string, name of variable with nominal categories
    numVarName: string, name of corresponding variable with numeric values
    takes a column with nominal categories and 
    """
    newVarName = nomVarName+"_avg"
    getcontext().prec = 2
    bins = selUnique(cursor,tableName,nomVarName)
    avgDic = {}
    for cat in bins:
        cursor.execute("SELECT "+numVarName+" FROM "+tableName+" WHERE "+nomVarName+" = '"+cat[0]+"'")
        qry = cursor.fetchall()
        qry = colToList(qry)
        qry2 = textToFloat(qry)
        if len(qry2)==0:
            print "No values could be converted to numbers: "+str(cat[0])
            continue
        qryArray = np.array(qry2)
        mean = qryArray.mean()
        mean = Decimal(mean)
        mean = round(mean,2)
        avgDic[cat[0]] = str(mean)
    try:
        addColumn(cursor,tableName,newVarName)
        varIndex(cursor,tableName,newVarName)
    except:
        print "column "+newVarName+" already exists, overwriting..."
        cursor.execute("UPDATE "+tableName+" SET "+newVarName+" = 'null'")
    dataUpdate(cursor,tableName,nomVarName,avgDic,True,newVarName)
        

# <codecell>

def utilMatrix(cursor, tableName, varList):
    """
    cursor: sqlite cursor object
    tableName: string, name of sqlite table
    varList: list of utility variables, in format indigenous
    to this program, which is the format that results
    from the sqlite "Pragma table_info()" command.
    This function creates a Pandas dataframe/matrix of the entropy,
    mean, and standard deviation of the utility variables, 
    index is the variable name, and columns are the statistics
    """
    varNames = []
    for var in varList:
        varNames.append(var[1])
    entropies = np.array([])
    sds = np.array([])
    means = np.array([])
    uMatrix = pd.DataFrame(columns = ["Entropy","Mean","SD"], index = varNames)
    for var in varNames:
        ent, mean, sd = utilValues(cursor, tableName, var)
        uMatrix.ix[var] = [ent, mean, sd]
    return uMatrix
    

# <codecell>

def textToFloat(txtList):
    """
    txtList: list of text values
    returns a list of float values, 
    skips values that cannot be converted
    """
    numList = []
    for i in txtList:
        try: numList.append(float(i))
        except: pass
    return numList

# <codecell>

def lDiversity(cursor, tableName, kkeyVar, senVar):
    qry = selUnique(cursor, tableName, kkeyVar)
    for i in qry:
        cursor.execute('SELECT '+senVar+' FROM '+tableName+' WHERE '+kkeyVar+' = "'+i[0]+'" GROUP BY '+senVar)
        qry2 = cursor.fetchall()
        if len(qry2) == 1:
            cursor.execute('UPDATE '+tableName+' SET '+senVar+' = " " WHERE '+kkeyVar+' = "'+i[0]+'"')

# <codecell>

def optimumDrop2(cursor, tableName, userVar, k, nonUniqueList, nComb=1):
    """                                                                                                                                                                                          
    cursor: sqlite3 cursor object                                                                                                                                                                
    tableName: string, name of main table                                                                                                                                                        
    userVar: string, name of userid var                                                                                                                                                          
    k: int, minimum cell size                                                                                                                                                                    
    nonUniqueList: list of course_combo values already cleared for k-anonymity                                                                                                                   
    nComb: int, number of courses to try to drop, default 1                                                                                                                                      
    iteratively tries 'dropping' one course for all of the records                                                                                                                               
    that are flagged as having a unique combo of courses                                                                                                                                         
    then measures the entropy of the resulting group, and                                                                                                                                        
    returns the position in courseList of the course to drop, along with the                                                                                                                     
    course_combo values that will benefit from the drop                                                                                                                                          
    """
    qry = courseUserQry(cursor, tableName, userVar, 'True')
    if len(qry)==0:
        return qry
    posLen = len(qry[0][0]) #assumes first variable in each tuple is the course combo, finds num of positions to change                                                                          
    preList = qry[:]
    preCombos = []
    for i in preList:
        preCombos.append(i[0])
    preEntropy = shannonEntropy(preList)
    postEntList = []
    preCount = 0
    for n in qry:
        preCount += n[1]
    print preCount
    iterTemp = itertools.combinations(range(posLen),nComb)
    dropCombos = []
    while True:
        try: dropCombos.append(iterTemp.next())
        except: break
    for i in dropCombos:
        #print "dropCombo:"
        #print i
        postList = []
        tmpList = qry[:]
        for j in tmpList:
            newString = ""
            for l in range(posLen):
                if l in i:
                    newString+="0"
                else:
                    newString+=j[0][l]
            postList.append((newString,j[1]))
        try:
            cursor.execute("DROP TABLE coursedrop")
            cursor.execute("CREATE TABLE coursedrop (course_combo text, Count integer)")
        except:
            cursor.execute("CREATE TABLE coursedrop (course_combo text, Count integer)")
        cursor.executemany("INSERT INTO coursedrop VALUES (?,?)",postList)
        cursor.execute("SELECT course_combo, SUM(Count) FROM coursedrop GROUP BY course_combo")
        postQry = cursor.fetchall()
        postEntropy = shannonEntropy(postQry)
        postCount = 0
        for item in postQry:
            postCount += item[1]
        changeVals = []
        for k in range(len(i)):
            oldSpots = []
            iterTemp = itertools.combinations(i,k+1)
            while True:
                try: oldSpots.append(iterTemp.next())
                except: break
            for l in oldSpots:
                for m in postQry:
                    mList = list(m[0])
                    for n in l:
                        mList[n] = '1'
                    oldString = ''
                    for p in mList:
                        oldString+=p
                    if m[1]>=k and oldString in preCombos:
                        changeVals.append(oldString)
                    elif (m[0] in nonUniqueList) and oldString in preCombos:
                        changeVals.append(oldString)
        #print "Length of ChangeVals: "+str(len(changeVals))
        if len(changeVals)>0:
            postEntList.append((i,preEntropy-postEntropy,changeVals))
    if len(postEntList) == 0:
        return []
    first = True
    low = (99,99,[])
    for n in postEntList:
        if n[1]<low[1] and n[1] > 0.0:
            low = n
    return low

# <codecell>

def userKanon2(cursor, tableName, userVar, courseVar, k):
    """                                                                                                                                                                                          
    cursor: sqlite cursor object                                                                                                                                                                 
    tableName: string, name of table                                                                                                                                                             
    userVar: string, name of userid variable                                                                                                                                                     
    courseVar: string, name of course variable                                                                                                                                                   
    k: minimum group size                                                                                                                                                                        
    creates a unique row record that is combo of                                                                                                                                                 
    courseid and userid, and then creates another variable                                                                                                                                       
    that says which courses someone has taken                                                                                                                                                    
    then checks for unique count of courses taken                                                                                                                                                
    and unique combinations of courses                                                                                                                                                           
    """
    courseList = courseComboUpdate(cursor,tableName,userVar,courseVar)
    value, uniqueList, nonUniqueList = uniqUserCheck(cursor,tableName,userVar,k)
    uniqUserFlag(cursor, tableName, uniqueList)
    dropNum = 1
    courseDrops = {}
    while value != 0.0 and dropNum != 16:  
        print "DropNum: "+str(dropNum)
        print "non-anon value: "+str(value)
        courseTup = optimumDrop2(cursor, tableName, userVar, k, nonUniqueList,dropNum)
        #print "courseTup returned from OptimumDrop:"
        if len(courseTup) == 0 or len(courseTup[2])==0:
            dropNum +=1 
            print "no more changes can be made, trying "+str(dropNum)+" courses at a time"   
            return courseDrops
        #print courseTup[:2]  
        courseNums = courseTup[0]
        #print "courseNums:"
        #print courseNums
        changeVals = courseTup[2]
        print "length of changeVals"
        print len(changeVals)
        for i in courseNums:
            courseName = courseList[i]
            print "dropping courseName:"
            print courseName
            courseDrops = courseDropper2(cursor, tableName, courseVar, courseName, changeVals, courseDrops)
        courseList = courseComboUpdate(cursor,tableName,userVar,courseVar)
        value, uniqueList, nonUniqueList = uniqUserCheck(cursor,tableName,userVar,k)
        uniqUserFlag(cursor, tableName, uniqueList)
    return courseDrops

# <codecell>

def courseDropper2(cursor, tableName, courseVar, courseName, changeVals, courseDict={}):
    """                                                                                                                                                                                          
    courseName: string, name of course to be dropped                                                                                                                                             
    changeVals: list of strings, values of course_combo to drop                                                                                                                                  
    courseDict: dictionary of courses and running tally of rows dropped                                                                                                                          
    drops course record where course equals courseName                                                                                                                                           
    AND uniqUserFlag = "True"                                                                                                                                                                    
    """
    delCount = 0
    #print "len of changeVals: "+str(len(changeVals))
    for val in changeVals:
        cursor.execute("SELECT SUM(Count) FROM "+tableName+" WHERE ("+courseVar+" = '"+courseName+"' AND uniqUserFlag = 'True' AND course_combo = '"+val+"')")
        qry = cursor.fetchall()
        #print "changeVal qry length:"+str(len(qry))
        if (qry[0][0]): delCount += qry[0][0]
    print "delCount: "+str(delCount)
    if delCount == 0:
        return courseDict
    if courseName in courseDict.keys():
        courseDict[courseName] += delCount
    else:
        courseDict[courseName] = delCount
    #confirm = raw_input("Confirm you want to delete "+str(delCount)+" records associated with "+courseName+" (y/n): ")
    #if confirm == 'n':
    #    return
    #elif confirm == 'y':
    for val in changeVals:
        cursor.execute("DELETE FROM "+tableName+" WHERE ("+courseVar+" = '"+courseName+"' AND uniqUserFlag = 'True' AND course_combo = '"+val+"')")
    #else:
    #    print "invalid choice, exiting function"
    return courseDict

# <codecell>

def kAnonIter(cursor, tableName, k, outFile):
    """                                                                                                                                                                                          
    cursor: sqlite cursor object                                                                                                                                                                 
    tableName: string, name of table                                                                                                                                                             
    k: minimum group size                                                                                                                                                                        
    wrapper function, gets list of variables from user input,                                                                                                                                    
    updates kkey, checks for k-anonymity                                                                                                                                                         
    """
    coreVarList = qiPicker(cursor, tableName)
    optVarList = qiPicker(cursor, tableName)
    iterVarList = coreVarList
    addList = []
    kkeyUpdate(cursor, tableName, iterVarList)
    varIndex = 0
    a,b = isTableKanonymous(cursor, tableName,k)
    results = [('core',b)]
    for var in optVarList:
        iterVarList.append(optVarList[varIndex])
        print iterVarList
        addList.append(optVarList[varIndex])
        print addList
        results.append((addList,))
        kkeyUpdate(cursor, tableName, iterVarList)
        a,b = isTableKanonymous(cursor,tableName,k)
        varIndex += 1
        results[varIndex] += (b,)
    outFile.write(str(results))
    return results

# <headingcell level=4>

# Name the file containing the data,
# name the database,
# and name commonly-used database variables.
# NOTE: make updates here if file specification changes

# <codecell>

file = "person_course_harvardxdb+mitxdb_2014_01_17a.csv"
table = "source"
userVar = "user_id"
courseVar = "course_id"
countryVar = "final_cc"
k=5

# <codecell>

#the file as released
db = 'kaPC_1-17-4-17-14-3.db'
c = dbOpen(db)

# <codecell>

#no changes to data
db = 'kaPC_1-17-4-17-14-orig.db'
c = dbOpen(db)

# <codecell>

#use binning for the article
db = 'kaPC_1-17-4-17-14-alt1.db'
c = dbOpen(db)

# <headingcell level=4>

# Load data into SQLite database

# <codecell>

sourceLoad(c,file,table)

# <headingcell level=4>

# Load data into another table to make comparisons to the original data

# <codecell>

sourceLoad(c,file,"original")

# <codecell>

dateSplit(c,table,"start_time")
dateSplit(c,table,"last_event")

# <codecell>

c.execute("SELECT name FROM sqlite_master WHERE type='table';")
c.fetchall()

# <headingcell level=4>

# Load column names into a variable called varList

# <codecell>

c.execute("Pragma table_info("+table+")")
varList = c.fetchall()
varList

# <headingcell level=4>

# Add indices

# <codecell>

varIndex(c,table,courseVar)
varIndex(c,table,userVar)

# <codecell>

c.execute("CREATE INDEX "+courseVar+"_idx2 ON original ("+courseVar+")")
c.execute("CREATE INDEX "+userVar+"_idx2 ON original ("+userVar+")")

# <headingcell level=4>

# Get initial count of records loaded

# <codecell>

c.execute("SELECT SUM(Count) FROM "+table)
c.fetchall()

# <headingcell level=4>

# Map country codes to country names, load table of country name to continent mappings

# <codecell>

countryNamer(c,table,countryVar)
contImport(c, table, "country_continent", countryVar+"_cname")

# <headingcell level=4>

# Delete staff

# <codecell>

c.execute("DELETE FROM "+table+" WHERE (roles = 'instructor' or roles = 'staff')")

# <codecell>

c.execute("DELETE FROM original WHERE (roles = 'instructor' or roles = 'staff')")

# <headingcell level=4>

# Generate anonymous userIDs

# <codecell>

idGen(c,table,userVar,"MHxPC13")

# <headingcell level=4>

# Get initial entropy reading

# <codecell>

addColumn(c,table,'entropy')
varIndex(c,table,'entropy')
kkeyUpdate(c, table,varList,'entropy')

# <codecell>

qry = selUnique(c,table,'entropy')

# <codecell>

beginEntropy = shannonEntropy(qry)
beginEntropy

# <headingcell level=4>

# Create utility Matrix (both for unmodified dataset and current dataset)

# <codecell>

utilVars = varList[4:7]+[varList[13]]+[varList[16]]+varList[21:25]
utilVars

# <codecell>

preUmatrix = utilMatrix(c,"original",utilVars)

# <codecell>

preUmatrix

# <codecell>

uMatrix = utilMatrix(c,table,utilVars)

# <codecell>

uMatrix

# <codecell>

uMatrix - preUmatrix
#removed rows for user k-anonymity

# <headingcell level=4>

# Establish user-wise k-anonymity

# <codecell>

 courseDrops = userKanon2(c, table, userVar, courseVar, k)

# <codecell>

for course in courseDrops.keys():
    print "Dropped "+str(courseDrops[course])+" rows for course "+course

# <codecell>

c.execute("SELECT SUM(Count) FROM "+table+" WHERE uniqUserFlag = 'True'")                                                                                                                
qry = c.fetchall()                                                                                                                           
print "Deleted "+str(qry[0][0])+" additional records for users with unique combinations of courses.\n"                                                                                   
c.execute("DELETE FROM "+table+" WHERE uniqUserFlag = 'True'")                                                                                                                                   

# <codecell>

kkeyUpdate(c, table,varList[:26],'entropy')

# <codecell>

qry = selUnique(c,table,'entropy')
tmpEntropy = shannonEntropy(qry)

# <codecell>

tmpEntropy

# <codecell>

entChg = 2**beginEntropy - 2**tmpEntropy

# <codecell>

entChg
#This one after User-K-Anonymity

# <headingcell level=4>

# Replace country names with continent names

# <codecell>

initContVal = 5000
contSwap(c,table,"final_cc_cname","continent",initContVal)
#outFile.write("Inserting continent names for countries with fewer than "+str(initContVal)+"\n")

# <headingcell level=4>

# Make gender variable that treats NA and missing as same

# <codecell>

try:
    addColumn(c,table,"gender_DI")
    varIndex(c,table,"gender_DI")
    simpleUpdate(c,table,"gender_DI","NULL")
    c.execute("UPDATE "+table+" SET gender_DI = gender")
    c.execute("UPDATE "+table+" SET gender_DI = '' WHERE gender_DI = 'NA'")
except:
    c.execute("UPDATE "+table+" SET gender_DI = gender")
    c.execute("UPDATE "+table+" SET gender_DI = '' WHERE gender_DI = 'NA'")

# <headingcell level=4>

# Get k-anonymity reading

# <codecell>

status, value = kAnonWrap(c,table,k)
print "Percent of records that will need to be deleted to be k-anonymous: "+str(value)+"\n"
#outFile.write( "Percent of records that will need to be deleted to be k-anonymous: "+str(value)+"\n")

# <headingcell level=4>

# Check k-anonymity for records with some null values

# <codecell>

print "checking k-anonymity for records with some null values"
print datetime.datetime.now().time()
#outFile.write("checking k-anonymity for records with some null values\n")
#outFile.write(str(datetime.datetime.now().time())+"\n")
iterKcheck(c,table,k)

# <codecell>

def eduClean(cursor, tableName, loeVar):
    try: 
        addColumn(cursor,tableName,loeVar+"_DI")
        varIndex(cursor,tableName,loeVar+"_DI")
    except:
        simpleUpdate(cursor,tableName,loeVar+"_DI","NULL")
    ed_dict = {'':'', 'NA':'NA','a':'Secondary','b':"Bachelor's",'el':'Less than Secondary',
               'hs':'Secondary','jhs':'Less than Secondary','learn':'','m':"Master's",'none':'',
               'other':'','p':'Doctorate','p_oth':'Doctorate','p_se':'Doctorate'}
    qry = selUnique(cursor,tableName,loeVar)
    for row in qry:
        if row[0] in ed_dict.keys():
            cursor.execute('UPDATE '+tableName+' SET '+loeVar+'_DI = "'+ed_dict[row[0]]+'" WHERE '+loeVar+' = "'+row[0]+'"')

# <codecell>

eduClean(c,table,"LoE")

# <codecell>

selUnique(c,table,"LoE")

# <codecell>

selUnique(c,table,"LoE_DI")

# <codecell>

#change 0 values to text in order to exclude them from the binning procedure
c.execute("UPDATE source SET nforum_posts = 'zero' WHERE nforum_posts = '0'")

# <codecell>

dbClose(c)

# <markdowncell>

# START HERE JUN 17 AM: NEED TO RELOAD FUNCTIONS TO TAKE IN NEW TAILFINDER AND DO TAILS ON NFORUM_POSTS AND THEN BIN.

# <codecell>

tailFinder(c,table,"nforum_posts",5)

# <codecell>

c.execute("UPDATE source SET nforum_posts = '0' WHERE nforum_posts = 'zero'")
c.execute("UPDATE source SET nforum_posts_DI = 'one' WHERE nforum_posts = '1'")
c.execute("UPDATE source SET nforum_posts_DI = 'two' WHERE nforum_posts = '2'")
c.execute("UPDATE source SET nforum_posts_DI = 'three' WHERE nforum_posts = '3'")
c.execute("UPDATE source SET nforum_posts_DI = 'four' WHERE nforum_posts = '4'")
c.execute("UPDATE source SET nforum_posts_DI = 'five' WHERE nforum_posts = '5'")
c.execute("UPDATE source SET nforum_posts_DI = 'six' WHERE nforum_posts = '6'")
c.execute("UPDATE source SET nforum_posts_DI = 'seven' WHERE nforum_posts = '7'")
c.execute("UPDATE source SET nforum_posts_DI = 'eight' WHERE nforum_posts = '8'")
c.execute("UPDATE source SET nforum_posts_DI = 'nine' WHERE nforum_posts = '9'")
c.execute("UPDATE source SET nforum_posts_DI = 'ten' WHERE nforum_posts = '10'")

# <codecell>

numBinner(c,table,"nforum_posts_DI")

# <codecell>

binAvg(c,table,"nforum_posts_DI","nforum_posts")

# <codecell>

selUnique(c,table,"nforum_posts_DI_avg")

# <codecell>

tailFinder(c,table,"YoB",50)

# <codecell>

numBinner(c,table,"YoB_DI",bw=2)

# <codecell>

selUnique(c,table,"YoB_DI")

# <codecell>

kAnonWrap(c,table,k)

# <codecell>

lDiversity(c,table,"kkey","grade")

# <codecell>

addColumn(c,table,"incomplete_flag")

# <codecell>

varIndex(c,table,"incomplete_flag")

# <codecell>

c.execute("SELECT SUM(Count) FROM source WHERE nevents = '' AND nchapters != ''")
qry = c.fetchall()
print qry
c.execute("SELECT SUM(Count) FROM source WHERE nevents = '' AND nforum_posts != '0'")
qry = c.fetchall()
print qry
c.execute("SELECT SUM(Count) FROM source WHERE nevents = '' AND ndays_act != ''")
qry = c.fetchall()
print qry

# <codecell>

c.execute("UPDATE source SET incomplete_flag = '1' WHERE nevents = '' AND nchapters != ''")

# <codecell>

c.execute("UPDATE source SET incomplete_flag = '1' WHERE nevents = '' AND nforum_posts != '0'")

# <codecell>

c.execute("UPDATE source SET incomplete_flag = '1' WHERE nevents = '' AND ndays_act != ''")

# <codecell>

c.execute("SELECT * FROM source WHERE incomplete_flag = '1'")

# <codecell>

qry = c.fetchall()

# <codecell>

len(qry)

# <codecell>

c.execute("Pragma table_info(source)")
varList = c.fetchall()
varList

# <codecell>

kkeyList = []
kkeyList.append(varList[0])
kkeyList.append(varList[36])
kkeyList.append(varList[37])
kkeyList.append(varList[47])
kkeyList.append(varList[49])
kkeyList.append(varList[50])
kkeyList

# <codecell>

kkeyUpdate(c,table,kkeyList)

# <codecell>

c.execute("SELECT SUM(Count), kkey FROM source GROUP BY kkey")
qry2 = c.fetchall()
#lessThanK = []
#badCount = 0
c.execute("UPDATE "+table+" SET kCheckFlag = 'False'")
for row in qry2:
    if row[0] >= 5:
        c.execute('UPDATE '+table+' SET kCheckFlag = "True" WHERE kkey = "'+row[1]+'"')

# <codecell>

selUnique(c,table,"kCheckFlag")

# <codecell>

c.execute("DELETE FROM source WHERE kCheckFlag = 'False'")

# <codecell>

csvExport(c,table,"HMXPC13_DI_binned_061714.csv")

# <codecell>

selUnique(c,table,"YoB_DI")

# <headingcell level=1>

# Stats on Original File

# <codecell>

dbClose(c)
db = 'kaPC_1-17-4-17-14-orig.db'
c = dbOpen(db)

# <codecell>

c.execute("Pragma table_info(source)")
c.fetchall()

# <codecell>

c.execute("UPDATE source SET Count = 1")

# <codecell>

c.execute("SELECT SUM(Count) FROM source")
total = c.fetchall()[0][0]
total

# <codecell>

view_qry = selUnique(c,table,"viewed")
view_dic = {}
for row in view_qry:
    view_dic[row[0]] = float(row[1])/float(total)
view_dic

# <codecell>

exp_qry = selUnique(c,table,"explored")
exp_dic = {}
for row in exp_qry:
    exp_dic[row[0]] = float(row[1])/float(total)
exp_dic

# <codecell>

cert_qry = selUnique(c,table,"certified")
cert_dic = {}
for row in cert_qry:
    cert_dic[row[0]] = float(row[1])/float(total)
cert_dic

# <codecell>

gen_qry = selUnique(c,table,"gender")
gen_dic = {}
gen_total = total
for row in gen_qry:
    if row[0] == '' or row[0] == 'NA' or row[0] == 'o':
        gen_total -= row[1]
    else:
        gen_dic[row[0]] = float(row[1])/float(gen_total)
gen_dic

# <codecell>

age_qry = selUnique(c,table,"YoB")
num = 0
denom = 0
for row in age_qry:
    try: age = 2013 - int(row[0])
    except: continue
    num += age * row[1]
    denom += row[1]
avg_age = float(num)/float(denom)
avg_age

# <headingcell level=2>

# Stats on De-identified file

# <codecell>

dbClose(c)
db = 'kaPC_1-17-4-17-14-3.db'
c = dbOpen(db)

# <codecell>

c.execute("SELECT SUM(Count) FROM source")
total = c.fetchall()[0][0]
total

# <codecell>

view_qry = selUnique(c,table,"viewed")
view_dic = {}
for row in view_qry:
    view_dic[row[0]] = float(row[1])/float(total)
view_dic

# <codecell>

exp_qry = selUnique(c,table,"explored")
exp_dic = {}
for row in exp_qry:
    exp_dic[row[0]] = float(row[1])/float(total)
exp_dic

# <codecell>

cert_qry = selUnique(c,table,"certified")
cert_dic = {}
for row in cert_qry:
    cert_dic[row[0]] = float(row[1])/float(total)
cert_dic

# <codecell>

gen_qry = selUnique(c,table,"gender")
gen_dic = {}
gen_total = total
for row in gen_qry:
    if row[0] == '' or row[0] == 'NA' or row[0] == 'o':
        gen_total -= row[1]
    else:
        gen_dic[row[0]] = float(row[1])/float(gen_total)
gen_dic

# <codecell>

age_qry = selUnique(c,table,"YoB")
num = 0
denom = 0
for row in age_qry:
    try: age = 2013 - int(row[0])
    except: continue
    num += age * row[1]
    denom += row[1]
avg_age = float(num)/float(denom)
avg_age

# <codecell>

c.execute("Pragma database_list")
c.fetchall()

# <codecell>

selUnique(c,table,"YoB")

# <codecell>


# <codecell>

uMatrix - preUmatrix
#This one taken after K-Anonymous

