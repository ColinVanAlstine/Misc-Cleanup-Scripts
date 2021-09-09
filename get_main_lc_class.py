#2021-06-17, Colin Van Alstine, get main LC class

import pandas as pd
#import numpy as np

pd.options.mode.chained_assignment = None  # default='warn'
#pd.options.display.float_format = "{:,.2f}".format

all_items = pd.read_csv('z30_all_lc.csv', header=0, dtype = str)

#drop lines missing any values
items = all_items.dropna(axis=0)

#cleaning up MARC subfield indicators; $h, $i, $k
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$h','')
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$a','')
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$i',' ')
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$b',' ')
items['Z30_CALL_NO'] = items['Z30_CALL_NO'].str.replace('\$\$k',' ')

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

items['ADM'] = items['Z30_REC_KEY'].str.slice(0, 9)

item_count = items.groupby('subject')['Z30_REC_KEY'].nunique()
title_count = items.groupby('subject')['ADM'].nunique()

main_class_counts = pd.concat([title_count, item_count], axis=1)
main_class_counts = main_class_counts.rename(columns={'Z30_REC_KEY': "Item count", 'ADM': "Title count"})
print(main_class_counts)