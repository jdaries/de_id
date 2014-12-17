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


*********************
*Useful Definitions *
*********************

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
   See Latanya Sweeney's work. A dataset is k-anonymous if 
   you cannot distinguish any one record from k-1 other records
   based on identifiers or quasi-identifiers.

4) L-diversity
   Even if a dataset is k-anonymous, if it is not l-diverse then
   sensitive information can still be disclosed. Within a k-anonymous
   block, even if you cannot distinguish any individual record from
   another based on quasi-identifiers, if the value of any sensitive
   variable is uniform, then you know the value for all individuals
   matching that set of quasi-identifiers.

5) Quasi-identifier
   A variable that alone may not identify an individual, but in combiation
   with other information may prove uniquely identifying. Example is gender
   or country of origin.

*********************
*General User Manual*
*********************

This is intended as a VERY broad overview of the process as it was designed.
For more information, read the documents accompanying the data release, read
the comments in the code, or email daries@mit.edu.

1) The IPython Notebook inclued in this repository is intended as the step-by-step
manual to the de-identification process. It does not use all of the possible functions
but it does the minimum and is basically what was done for the first year of data.
Start there.

2) The De_id_functions.py was the first code written, so it includes functions 
that may be helpful but may not be referenced in the IPython Notebook. It is commented
fairly well, so be sure to read through it to see if there is a function there you 
may want to use.

3) This was not written as, nor should it be, a push-button process. The process
involves making a change, evaluating the results, and then choosing the next course of action.

4) If you have a scale variable that you are treating as a quasi-identifier
but want to reduce granularity in order to increase k-anonymity, use the tailFinder
and the numBinner functions together, in that order. TailFinder will show you a rudimentary
distribution of the tails based upon the paramaters you give it, so that you can choose where
to cut off the tails and replace them with strings like "<10". After trimming the tails into
these text categories, numBinner will allow you to then group the middle of the distribution
into buckets of uniform size. It will skip non-integer values, so the tails will be maintained.
Think of bucket size when you trim tails, so you don't end up with a funky-sized bucket
at the end. The code is not sophisticated enough to always get it right, so you need to 
set it up correctly so that the bins and the tails match up perfectly.

5) Per a suggestion from Andrew Ho (HarvardGSE), instead of just the strings 
that describe the endpoints of the bins, you can create a second variable
using binAvg function that will give the true mean of the members of a bin.

6) The Utility Matrix can help keep track of how much values have changed
as a result of the de-identification process. Run it many times and measure the
difference from the original. This process is in the IPython Notebook.

7) Be sure to delete any non-k-anonymous records before exporting.

8) Export only the coluns that are properly de-identified.

Good luck!