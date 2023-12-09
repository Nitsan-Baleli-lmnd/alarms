# import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
# from datetime import datetime
import os
import Levenshtein
import re
# import re
local = '/home/innereye/alarms/'
# islocal = False
try:
    if os.path.isdir(local):
        os.chdir(local)
        local = True
    csv = 'data/deaths_idf.csv'
    idf = pd.read_csv(csv)
    front = pd.read_csv('data/front.csv')
    if all(front['name'].values == idf['name'].values[:len(front)]):
        pass
    else:
        print('name mishmash')
        raise Exception('name mishmash')

    ##
    to_fill = front['front'].isnull().values
    #  from where to fill empty front cells
    if not to_fill[-1]:
        to_fill = len(to_fill)
    else:
        to_fill = np.where(~to_fill)[0][-1]+1

    changed = False
    if len(idf) >= to_fill:
        ynet = pd.read_csv('data/ynetlist.csv')
        yd = []
        for iy in range(len(ynet)):
            yd.append('|'.join([ynet['שם פרטי'][iy] + ' ' + ynet['שם משפחה'][iy],
                           str(ynet['גיל'][iy]), str(ynet['מקום מגורים'][iy])]))
        otef = '|'.join(['זיקים', 'נתיב העשרה', 'כפר עזה', 'נחל עוז', 'שדרות', 'בארי', 'כיסופים', 'מפלסים'])
        for ii in range(to_fill, len(idf)):
            st = idf['story'][ii]
            yy = ''
            ff = ''
            id = '|'.join([idf['name'][ii], str(idf['age'][ii]), str(idf['from'][ii])])
            distance = [Levenshtein.distance(id, x) for x in yd]
            if min(distance) < 3:
                yrow = np.argmin(distance)
                yy = ynet['מידע על המוות'][yrow]
            if (type(re.search(otef, yy)) == re.Match) or \
                (type(re.search(otef, st)) == re.Match):
                ff = 'עוטף עזה'
            elif (type(re.search(r'נפל בקרב.+רצוע', yy)) == re.Match) or \
                 (type(re.search(r'נפל בקרב.+רצוע', st)) == re.Match):
                ff = 'עזה'
            elif 'לבנון' in yy or 'לבנון' in st:
                ff = 'לבנון'
            elif 'נרצח' in yy or 'נרצח' in st:
                ff = 'נרצח כאזרח'
            if len(yy) > 0 or len(ff) > 0:
                changed = True
            front.loc[ii] = [idf['name'][ii], st, yy, ff]
    if changed:
        front.to_csv('data/front.csv', index=False)
except:
    print('failed front update')