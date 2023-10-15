import requests
import pandas as pd
from html import unescape
import os
import sys
import re
import numpy as np
try:
    local = '/home/innereye/alarms/'
    islocal = False
    if os.path.isdir(local):
        os.chdir(local)
        islocal = True
        sys.path.append(local + 'code')
except Exception as e:
    print('set path failed?')
    print(e)

from map_deaths import map_deaths
replace = [['כדורגלן עבר', ''],
           ['ממבטחים', 'מבטחים'],
           ['מבטחים', 'ממבטחים']]
name_errors = 0
cols = {'name': 'name', 'gender':'gender', 'age': 'age', 'from': 'loc', 'story': 'story'}
data = pd.read_csv('data/deaths.csv', keep_default_na=False)
try:
# if True:
    r = requests.get('https://ynet-projects.webflow.io/news/attackingaza?01ccf7e0_page=100000000')
    bad = len(r.text)
    # marker seperates between people
    marker = '<div class="fallen-text-top w-condition-invisible">'
    gpa = 'gazaattack-place-age'
    gns = 'gazaattack-name-story'
    dfs = []
    page = 0
    more = True
    while more:
        page += 1
        # r = requests.get('https://ynet-projects.webflow.io/news/attackingaza')
        r = requests.get(f'https://ynet-projects.webflow.io/news/attackingaza?01ccf7e0_page={page}')
        if len(r.text) == bad or page > 100:
            more = False
        else:
            r.encoding = r.apparent_encoding,
            txt = r.text
            txt = unescape(txt)
            for rep in replace:
                txt = txt.replace(rep[0], rep[1])
            idx_marker = [m.end() for m in re.finditer(marker, txt)]
            # segment = txt.split('r-field="name" class="gazaattack-name"')
            ##

            seg_count = -1
            for iseg in range(len(idx_marker)):  # segment[1:]:
                gender = ''
                age = 0
                loc = ''
                story = ''
                # name = ''
                # age.append(0)
                seg = txt[idx_marker[iseg]+len('<div fs-cmsfilter-field="name" class="gazaattack-name">'):]
                if iseg < len(idx_marker)-2:
                    seg = seg[:(idx_marker[iseg+1]-idx_marker[iseg])]
                name = seg[:seg.index('<')]
                if 'טל לוי' in seg[:8]:
                    story = 'מ"כ בגדוד 50'
                else:
                    segs = seg.split('<div fs-cmsfilter-field="age" class="gazaattack-place-age">')
                    for s in segs:
                        a = s.replace('</div>', '')
                        if a.isnumeric():
                            age = int(a)
                            break
                    segs = seg.split('<div fs-cmsfilter-field="age" class="gazaattack-place-age">')
                    for s in segs:
                        if '<div class="redlinegazaattack"></div>' in s:
                            ll = s[:s.index('<')]
                            if ll.replace(' ', '').isalpha() and not ll == name:
                                loc = ll
                                break
                if " class=" in name:
                    name_errors += 1
                    print(f'name errors: {name_errors}')
                    bug = True
                    if 'עינבר' in seg and 'נרצחה במסיבה ברעים' in seg:
                        name = 'עינבר שם טוב'
                        gender = 'F'
                        story = 'נרצחה במסיבה ברעים'
                    elif 'באר שבע' in seg and 'נהרג בקיבוץ עלומים' in seg:
                        name = 'ישי סלוטקי'
                        gender = 'M'
                        story = 'נהרג בקיבוץ עלומים'
                    elif '1%D7%9E%D7%95%D7%A8-%D7%9B%D7%94%D7%9F%20' in seg:
                        name = 'מור כהן'
                        gender = 'M'
                        age = 24
                        loc = 'אזור'
                    elif '%D7%A2%D7%99%D7%9C%D7%99%20%D7%91%D7%A8%D7%A2%D7%9D' in seg:
                        name = 'עילי ברעם'
                        age = 27
                        gender = 'M'
                    elif '%D7%A1%D7%99%D7%95%D7%9F%20%D7%90%D7%9C%D7%A7%D7%91%D7%A5' in seg:
                        name = 'סיון אלקבץ'
                    else:
                        name = ''
                else:
                    bug = False
                if age == 0 and not bug:
                    if gpa in seg:
                        idx = seg.index(gpa)
                        segan = seg[idx + len(gpa) + 1:]
                        segan = segan[:segan.index('<')]
                        if '>בת' in segan:
                            gender = 'F'
                            gindex = segan.index('>בת')+1
                        elif '>בן' in segan:
                            gender = 'M'
                            gindex = segan.index('>בן')+1
                        else:
                            # gender[iseg] = '')
                            gindex = None
                        if gindex is None:
                            # print('no age for ' + name[-1])
                            # age.append(0)
                            segan_split = segan.split(' ')
                            im = []
                            for ii in range(len(segan_split)):
                                if segan_split[ii].replace('>', '')[0] == 'מ':
                                    im.append(ii)
                            if len(im) == 0:
                                lc = segan.replace('>', '')
                                lc = lc.replace('w-dyn-bind-empty"', '')
                                loc = lc
                            else:
                                lc = ' '.join(segan_split[im[-1]:]).replace('>', '')
                                lc = lc.replace('-dyn-bind-empty">', '')
                                loc = lc
                        else:
                            ag = segan[gindex+3:]
                            if len(ag) > 0 and ag[0].isnumeric():
                                for ichar in range(1, len(ag)):
                                    if ag[ichar].isnumeric():
                                        a = int(ag[:ichar+1])
                                    else:
                                        break
                                age = a
                                if ichar != len(ag)-1:
                                    # loc[iseg] = '')
                                # else:
                                    loc = ag[ichar:].replace(',', '').strip()
                                if len(loc) > 0 and loc[0] == 'מ':
                                    loc = loc[1:]
                            else:
                                # raise Exception('no age here?')
                                # age.append(0)
                                loc = '?'
                if gns in seg and not bug:
                    seg = seg[seg.index(gns):]
                    story = seg[len(gns)+2:seg.index('<')].replace('-dyn-bind-empty">', '')
                row = np.where(data['name'] == name)[0]
                if len(name) > 0:
                    if len(row) == 0:
                        data.loc[len(data)] = [name, gender, age, loc, story]
                    else:
                        row = row[0]
                        if len(data['name'].values[row]) == 0 and len(name) > 0:
                            data.at[row, 'name'] = name
                        if data['age'].values[row] == 0 and age > 0:
                            data.at[row, 'age'] = age
                        if len(data['from'].values[row]) == 0 and len(loc) > 0:
                            data.at[row, 'from'] = loc
                        if len(data['gender'].values[row]) == 0 and len(gender) > 0:
                            data.at[row, 'gender'] = gender
                        if len(data['story'].values[row]) == 0 and len(story) > 0:
                            data.at[row, 'story'] = story
    data.to_excel('data/deaths.xlsx', index=False)
    data.to_csv('data/deaths.csv', index=False)
    success = True
except Exception as e:
    print('scraping ynet failed')
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print(e)
    success = False
# age0 = txt.index('gazaattack-place-age')
if success:
    try:
        map_deaths()
    except Exception as e:
        print('death map creation failed')
        print(e)
print('done')


##

# else:
# story[iseg] = '')
# df = pd.DataFrame(name, columns=['name'])
# df['gender'] = gender
# df['age'] = age
# df['from'] = loc
# df['story'] = story
# dfs.append(df)
# merged = pd.concat(dfs)
