de_id
=====

De-identification scripts from first year of MITx and HarvardX courses
---

*******************************************
*Technology required to run these scripts:*
*******************************************

Python 2.7
iPython Notebook
sqlite3

**********************************
*Inputs required for this process*
**********************************

1) A .csv (comma-delimited text file) version of the Person-Course
dataset. 

+Person-course is a secondary dataset that is generated
based upon registration data and activity data, so is a merge of
the edX tracking logs and student-level demographics. The original
incarnation included such values as the number of courseware 
interactions, the number of video play events, and the number
of forum posts. The year two dataset likely includes more computed
values, so care should be taken with these scripts that it is not
run blindly, please do evaluate which columns are quasi-identifiers
and make sure that any new columns are either included or not
based upon informed choices.

2) A determination of which columns are quasi-identifiers. 

+In the first year, we used gender, country, year of birth, level of 
education, and number of forum posts. Care should be taken to 
choose variables that could reasonably be used to re-identify,
but also don't choose so many that the dataset is completely
obliterated.

3) A file that maps countries into continents. 

+A pickled dictionary of mapping is included here.


*****************************
*   Useful Definitions      *
*****************************

1) Utility values
   This term is taken from a Cynthia Dwork (Microsoft Research)
   paper. The general idea is to have some key variables that 
   you monitor while you make changes to the dataset. For the
   purposes of this project, I chose to take the mean, SD, 
   and the entropy. The Utility Matrix is basically just a
   table of these values for columns specified to that 
   function. 

2) Entropy
   Suggestion for this as a measure of change from Ike Chuang
   (MIT). Using the e-based definititon. Just a measure of 
   "information." Look at Wikipedia for more info, very simple
   formula.

3) K-anonymity

4) L-diversity
