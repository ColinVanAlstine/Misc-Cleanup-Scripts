#2021-06-11, IST652, Project, Colin Van Alstine

"""
This program requires the following files to be located in a folder called C:\scripting_datasets:
    z00r.csv - bibliographic metadata
    z30.csv - item records
    z36.csv - current loans
    z36h.csv - historical loans
    z68.csv - order records
    z103.csv - linking table with keys to other tables
These files can be exported from the Aleph server as .csv output, encoded in UTF-8 and should not be modified prior to running this script
Additionally, a modified version of the country list from https://www.loc.gov/marc/countries/ is saved as countries.csv
"""

#https://github.com/unt-libraries/pycallnumber
#import pycallnumber as pycn
import pandas as pd
import numpy as np

pd.options.mode.chained_assignment = None  # default='warn'
pd.options.display.float_format = "{:,.2f}".format


"""
The following section pulls in all the loans that are stored in the z36 file (currently loaned items) and the z36h file (historical loans),
saves only the columns that are useful to this analysis (record key and loan date) and joins the two dataframes into a single dataframe
that are all the loans in the system.
"""

circ_history = pd.read_csv('C:\scripting_datasets\z36h.csv', header=0, dtype = str, usecols= ['Z36H_REC_KEY','Z36H_LOAN_DATE'])
circ_history = circ_history.rename(columns={"Z36H_REC_KEY": "REC_KEY", "Z36H_LOAN_DATE": "LOAN_DATE"})

current_circs = pd.read_csv('C:\scripting_datasets\z36.csv', header=0, dtype = str, usecols= ['Z36_REC_KEY','Z36_LOAN_DATE'])
current_circs = current_circs.rename(columns={"Z36_REC_KEY": "REC_KEY", "Z36_LOAN_DATE": "LOAN_DATE"})

circs = pd.concat([circ_history, current_circs], ignore_index=True)


"""
The next section opens the file that deals with all the items in the catalog, pulling in the columns relevant to this analysis.
It then drops rows that do not use the Library of Congress classification scheme, are held in branch libraries or are for online resources.
"""

all_items = pd.read_csv('C:\scripting_datasets\z30.csv', header=0, dtype = str, usecols= ['Z30_REC_KEY','Z30_SUB_LIBRARY', 'Z30_COLLECTION', 'Z30_NO_LOANS', 'Z30_CALL_NO_TYPE', 'Z30_CALL_NO'])

#drop lines missing any values
items = all_items.dropna(axis=0)
#drop non-LC
items.drop(items[items['Z30_CALL_NO_TYPE'] != '0'].index, inplace=True)
items.drop('Z30_CALL_NO_TYPE', axis=1, inplace=True)
#drop branch libraries
good_libraries = ['SCANN', 'SCNLS']
items = items[items.Z30_SUB_LIBRARY.isin(good_libraries)]
#drop e-resources
items.drop(items[items['Z30_COLLECTION'] == 'SCINT'].index, inplace=True)
#convert loans to numeric and get rid of 0
items['Z30_NO_LOANS'] = items['Z30_NO_LOANS'].replace({'0':np.nan, 0:np.nan})

#cleaning up MARC subfield indicators; $h, $i, $k
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$h','')
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$a','')
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$i',' ')
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$b',' ')
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$k',' ')

"""
getting errors when trying to create a new df column using .classification from pycn
    items['classification'] = items['Z30_CALL_NO'].map(lambda Z30_CALL_NO: pycn.callnumber(Z30_CALL_NO).classification)
results in error    
    AttributeError: 'Local' object has no attribute 'classification'
for the time being, I'm going to manually trim the first letter to get the subject
"""
#read the call# and get the class parts
#items['Z30_CALL_NO'] = items['Z30_CALL_NO'].map(lambda Z30_CALL_NO: pycn.callnumber(Z30_CALL_NO).classification)
#print(items.head(10))

#main classes - https://www.loc.gov/catdir/cpso/lcco/
def label_subject (Z30_CALL_NO):
    if Z30_CALL_NO.startswith('A'):
        return 'A - General Works'
    if Z30_CALL_NO.startswith('B'):
        return 'B - Philosophy, Psychology, Religion'
    if Z30_CALL_NO.startswith('C'):
        return 'C - Auxiliary Sciences of History'
    if Z30_CALL_NO.startswith('D'):
        return 'D - World History'   
    if Z30_CALL_NO.startswith('E'):
        return 'E - History of the Americas'
    if Z30_CALL_NO.startswith('F'):
        return 'F - Local History of the Americas'
    if Z30_CALL_NO.startswith('G'):
        return 'G - Geography, Anthropology, Recreation'
    if Z30_CALL_NO.startswith('H'):
        return 'H - Social Sciences'
    if Z30_CALL_NO.startswith('J'):
        return 'J - Political Science'
    if Z30_CALL_NO.startswith('K'):
        return 'K - Law'
    if Z30_CALL_NO.startswith('L'):
        return 'L - Education'
    if Z30_CALL_NO.startswith('M'):
        return 'M - Music'
    if Z30_CALL_NO.startswith('N'):
        return 'N - Fine Arts'
    if Z30_CALL_NO.startswith('P'):
        return 'P - Language and Literature'
    if Z30_CALL_NO.startswith('Q'):
        return 'Q - Science'
    if Z30_CALL_NO.startswith('R'):
        return 'R - Medicine'
    if Z30_CALL_NO.startswith('S'):
        return 'S - Agriculture'
    if Z30_CALL_NO.startswith('T'):
        return 'T - Technology'
    if Z30_CALL_NO.startswith('U'):
        return 'U - Military Science'
    if Z30_CALL_NO.startswith('V'):
        return 'V - Naval Science'
    if Z30_CALL_NO.startswith('Z'):
        return 'Z - Bibliography, Library Science'
    #return 'Error'

items['subject'] = items['Z30_CALL_NO'].map(lambda Z30_CALL_NO: label_subject(Z30_CALL_NO))

#get a count of recent circulations from the z36 dataframe and add a new column to items based on the circ data
circ_counts = circs['REC_KEY'].value_counts().to_dict()
items['recent_circs'] = items['Z30_REC_KEY'].map(circ_counts)
#print(items.head(10))


"""
Now we can ask things of the data!
This next section aggregates various datapoints from the item and circ tables and saves them to one dataframe.
"""

#total number of items in each subject
title_count = items.groupby('subject')['Z30_REC_KEY'].count()
#total all-time circulations in each subject
circ_sum = items.groupby('subject')['Z30_NO_LOANS'].sum().astype('int64')
#percentage of items that ever circulated
ever_circed = items.groupby('subject')['Z30_NO_LOANS'].count() / items.groupby('subject')['Z30_REC_KEY'].count() * 100
#percentage of items that circulated since 2006
recent_circed = items.groupby('subject')['recent_circs'].count() / items.groupby('subject')['Z30_REC_KEY'].count() * 100

#combined and renamed
callnum_analysis = pd.concat([title_count, circ_sum, ever_circed, recent_circed], axis=1)
callnum_analysis = callnum_analysis.rename(columns={'Z30_REC_KEY': "Title count", 'Z30_NO_LOANS': "Total circs", 0: "percentage items ever circed", 1: "percentage items circed recently"})
print('\nItem analysis by subject\n' + '~'*40)
print(callnum_analysis, "\n")

#circ by location
print('\nWhat percentage of items housed on campus or the annex have circulated\n' + '~'*40)
print(items.groupby('Z30_SUB_LIBRARY')['recent_circs'].count() / items.groupby('Z30_SUB_LIBRARY')['Z30_REC_KEY'].count() * 100)


"""
We now want to start looking at bibliographic metadata from the z00r table.
To get at this data, we will need to link the z30 and z00r tables using keys from z103.
"""
#get z30 ready for matching
items['ADM'] = items['Z30_REC_KEY'].str.slice(0, 9)

#import z103 table and drop all but the ADM references
z103_links = pd.read_csv('C:\scripting_datasets\z103.csv', header=0, dtype = str, usecols= ['Z103_REC_KEY','Z103_REC_KEY_1', 'Z103_LKR_TYPE'])
z103_links.drop(z103_links[z103_links['Z103_LKR_TYPE'] != 'ADM'].index, inplace=True)
z103_links.drop('Z103_LKR_TYPE', axis=1, inplace=True)

z103_links['ADM'] = z103_links['Z103_REC_KEY'].str.slice(5, 14)
z103_links.drop('Z103_REC_KEY', axis=1, inplace=True)

z103_links['bib_num'] = z103_links['Z103_REC_KEY_1'].str.slice(5)
z103_links.drop('Z103_REC_KEY_1', axis=1, inplace=True)


#join z103_links to items to merge in the bib#
items = pd.merge(items, z103_links, on ='ADM', how ='left')

#check to see if there are items that don't link to bibs, and drop them
#print(items['bib_num'].isnull().sum())
items = items.dropna(subset=['bib_num'])


"""
This next section reads in the absolutely massive z00r table, which contains MARC fields as field/value pairs.
We will be looking for country of origin, publication year, and language values.  These can be found in human-readable fields throughout the MARC record,
but the 008 fixed field contains a more stable form of all these values.  The downside is that we have to use lookup tables to display them in a meaningful way.
"""
#this is going to take a while to run...
z00r = pd.read_csv('C:\scripting_datasets\z00r.csv', header=0, dtype = str, encoding='latin-1', usecols= ['Z00R_DOC_NUMBER','Z00R_FIELD_CODE', 'Z00R_TEXT'])
z00r = z00r.rename(columns={'Z00R_DOC_NUMBER': "bib_num"})
z00r['Z00R_FIELD_CODE'] = z00r['Z00R_FIELD_CODE'].str.replace(' ', '')
z00r['bib_num'] = z00r['bib_num'].str.replace(' ', '')

#grab the 008 fixed field, which has structured data for the date of publication, language of the material and the country of origin
#there is often more detail in the 260/264 and the 300 fields, but the data is less structured
z00r_ff = z00r[z00r['Z00R_FIELD_CODE'] == '008']

#get a valid date out of the z00r results
z00r_ff['date_string'] = z00r_ff['Z00R_TEXT'].str.slice(6, 15)
z00r_ff.loc[z00r_ff['date_string'].str.startswith(('c','s', 'd', 'e', 'i', 'k', 'm', 'q', 'u')), 'pub_date'] = z00r_ff['date_string'].str.slice(1, 5)  
z00r_ff.loc[z00r_ff['date_string'].str.startswith(('p','r', 't')), 'pub_date'] = z00r_ff['date_string'].str.slice(5, 9)

z00r_ff['pub_date'] = pd.to_datetime(z00r_ff['pub_date'], format="%Y", errors='coerce')

z00r_ff.drop('date_string', axis=1, inplace=True)

#get a valid country out of the z00r (both name and region)
z00r_ff['country_code'] = z00r_ff['Z00R_TEXT'].str.slice(15, 18)
z00r_ff['country_code'] = z00r_ff['country_code'].str.replace('^', '')

#country list is found here: https://www.loc.gov/marc/countries/ and the XML was turned into a csv using OpenRefine and Excel
countries = pd.read_csv('C:\scripting_datasets\countries.csv', header=0, dtype = str)

#join the country names to the codes found in z00r_ff
#this is my new favorite help doc: https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html
z00r_ff = pd.merge(z00r_ff, countries, on ='country_code', how ='left')

#drop any rows that are missing a pubdate or a country code, then remove raw data columns
z00r_ff = z00r_ff.dropna()
z00r_ff.drop('Z00R_FIELD_CODE', axis=1, inplace=True)
z00r_ff.drop('Z00R_TEXT', axis=1, inplace=True)

#create a new dataframe where I can start aggregating bib data
bib_analysis = pd.merge(items, z00r_ff, on ='bib_num', how ='inner')

"""
publishing countries by subject - how do I only display the top 5 per subject?
attempted using .apply(lambda x: x.sort_values(ascending=False).head(5)) as well as trying nlargest() - only able to affect the subject, not the secondary grouping of country_name
"""
country_count = bib_analysis.groupby(['subject', 'country_name']).agg({'country_name': ['count']})
print('\nMost common place of publication for each classification range\n' + '~'*40)
#print(country_count[:8])
print(country_count)

#get the average year of publication for all the titles in a given subject
bib_analysis.pub_date = pd.to_datetime(bib_analysis.pub_date).values.astype(np.int64)
average_date = pd.DataFrame(pd.to_datetime(bib_analysis.groupby('subject').mean().pub_date).dt.year)
print('\nAverage publication date for the materials in each classification range\n' + '~'*40)
print(average_date, '\n')


"""
Now we should start looking at financial information associated with our materials.  z68 contains order information, which is linked to the ADMs of the associated materials
TO-DO: look for the table with the invoice transactions and total those instead of working on the local price from orders - orders are more of an anticipated price and 
invoice transactions are the real paid values.  This will be important when I expand this analysis to serials, as these have yearly reoccuring payments that really add up.
"""

orders = pd.read_csv('C:\scripting_datasets\z68.csv', header=0, dtype = str, usecols= ['Z68_REC_KEY', 'Z68_ORDER_TYPE', 'Z68_ORDER_NUMBER', 'Z68_ORDER_STATUS', 'Z68_METHOD_OF_AQUISITION', 'Z68_ORDER_DATE', 'Z68_MATERIAL_TYPE', 'Z68_ERM_TYPE', 'Z68_VENDOR_CODE', 'Z68_E_LOCAL_PRICE'])
orders['ADM'] = orders['Z68_REC_KEY'].str.slice(0, 9)
orders['Z68_ORDER_NUMBER'] = orders['Z68_ORDER_NUMBER'].str.replace(' ', '')

#why don't they store the price as a float?  seriously, as a padded string?  madness.
orders['Z68_E_LOCAL_PRICE'] = orders['Z68_E_LOCAL_PRICE'].str.slice(0, 12) + '.' + orders['Z68_E_LOCAL_PRICE'].str.slice(12, 14)
orders['Z68_E_LOCAL_PRICE'] = pd.to_numeric(orders['Z68_E_LOCAL_PRICE'],errors='coerce')

#drop serials and standing orders (for now)
orders.drop(orders[orders['Z68_ORDER_TYPE'] != 'M'].index, inplace=True)

#collapse the circs for each item into the total circs for each ADM
item_grouped = items.groupby('ADM').sum()
orders = pd.merge(orders, item_grouped, on ='ADM', how ='inner')
orders = pd.merge(orders, items[['ADM', 'subject']], on ='ADM', how ='left')  #sum() dropped non-numeric, so adding back in from items

#account for divide-by-zero with cost per use
orders.loc[orders['recent_circs'] > 0, 'tempcirc'] = orders['recent_circs']
orders.loc[orders['recent_circs'] == 0, 'tempcirc'] = 1

orders['costperuse'] = (orders['Z68_E_LOCAL_PRICE'] / orders['tempcirc'])

#get rid of inf values and replace them with NaN (could drop later)
orders.replace([np.inf, -np.inf], np.nan, inplace=True)
#duplicate rows? drop 'em
orders = orders.drop_duplicates()
#clean up tempcirc
orders.drop('tempcirc', axis=1, inplace=True)

print('\nThese are the top ten under-utilized titles in our collection, identified by the highest cost-per-use value.\n' + '~'*40)
print(orders[['Z68_ORDER_NUMBER', 'Z68_E_LOCAL_PRICE', 'recent_circs', 'subject', 'costperuse']].sort_values(by='costperuse', ascending=False).head(10), '\n')
#these are for real - we've spent thousands of dollars on multi-volume sets that barely circulated and now sit in our offsite storage

#gather up some averages and group them by subject
average_costperuse = orders.groupby(['subject']).agg({'costperuse': ['mean']})
highest_spend = orders.groupby(['subject']).agg({'Z68_E_LOCAL_PRICE': ['sum']})

orders_analysis = pd.concat([average_costperuse, highest_spend], axis=1)
print('\nAverage cost-per-use and lifetime spend, per subject.\n' + '~'*40)
print(orders_analysis)