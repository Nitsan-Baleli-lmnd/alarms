import requests
from matplotlib import colors
import folium
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import plotly.express as px


local = '/home/innereye/alarms/'
islocal = False
if os.path.isdir(local):
    os.chdir(local)
    islocal = True

prev = pd.read_csv('data/alarms.csv')
last_alarm = pd.to_datetime(prev['time'][len(prev)-1])
last_alarm = last_alarm.tz_localize('Israel')
tzeva = requests.get('https://api.tzevaadom.co.il/alerts-history').json()
df = pd.DataFrame(tzeva)
df = df.explode('alerts')
df1 = pd.DataFrame(list(df['alerts']))
dt = np.asarray([pd.to_datetime(ds, utc=True, unit='s').astimezone(tz='Israel') for ds in df1['time']])
id = np.asarray(df['id'])
new = np.where(dt > last_alarm)[0]
if len(new) > 0:
    for n in new[::-1]:
        citiesc = df1['cities'][n]
        x = []
        for cit in citiesc:
            x.extend(cit.split(', '))
        citiesc = np.unique(x)
        idc = id[n]
        dtc = dt[n].replace(tzinfo=None)
        threatc = df1['threat'][n]
        # if df['description'][n] is None:
        if threatc == 0:
            desc = 'ירי רקטות וטילים'
        elif threatc == 2:
            desc = 'חדירת מחבלים'
        else:
            desc = ''
        for cit in citiesc:
            prev.loc[len(prev.index)] = [dtc, cit, threatc, idc, desc]
    prev.to_csv('data/alarms.csv', index=False, sep=',')
    news = True
else:
    news = False

if islocal or news:
    prev = prev[prev['threat'] == 0]
    prev = prev.reset_index(drop=True)
    yyyy = np.array([int(str(date)[:4]) for date in prev['time']])
    mm = np.array([int(str(date)[5:7]) for date in prev['time']])
    now = np.datetime64('now', 'ns')
    dt = pd.to_datetime(prev['time']).to_numpy()
    dif = now - dt
    dif_sec = dif.astype('timedelta64[s]').astype(float)
    dif_days = dif_sec / 60 ** 2 / 24
    past_24h = dif_days <= 1
    past_7d = dif_days <= 7
    n = []
    mmyy = []
    for year in range(2019, 2024):
        for month in range(1, 13):
            idx = (yyyy == year) & (mm == month)
            n.append(len(np.unique(prev['id'][idx])))
            mmyy.append(str(month)+'.'+str(year))


    fig = px.bar(x=mmyy, y=n, log_y=True)
    # fig = px.bar(prev, y=n, x='date',log_y=True)
    html = fig.to_html()
    file = open('docs/rockets_timeline.html', 'w')
    a = file.write(html)
    file.close()
    ##
    # Make map
    title_html = '''
                 <h3 align="center" style="font-size:16px"><b>Rocket alarms in Israel since July 2019, data from <a href="https://www.oref.org.il" target="_blank">THE NATIONAL EMERGENCY PORTAL</a>
                 via <a href="https://www.tzevaadom.co.il/" target="_blank">צבע אדום</a></b></h3>
                 '''
    gnames = ['2019', '2020', '2021', '2022', '2023', '7 days', '24 h']
    co = [[0.25, 0.25, 1.0], [0.25, 0.9, 0.8], [0.25, 1, 0.25], [0.75, 0.75, 0.25], [0.82, 0.5, 0.35],
          [1.0, 0.25, 0.25], [0, 0, 0]]
    chex = []
    for c in co:
        chex.append(colors.to_hex(c))
    lgd_txt = '<span style="color: {col};">{txt}</span>'
    grp = []
    for ic, gn in enumerate(gnames):
        grp.append(folium.FeatureGroup(name=lgd_txt.format(txt=gn, col=chex[ic])))

    coo = pd.read_csv('data/coord.csv')
    center = [coo['lat'].mean(), coo['long'].mean()]
    ##
    map = folium.Map(location=center, zoom_start=7.5, tiles='openstreetmap')
    tiles = ['cartodbpositron', 'stamenterrain']
    for tile in tiles:
        folium.TileLayer(tile).add_to(map)
    map.get_root().html.add_child(folium.Element(title_html))

    for year in range(2019, 2024):
        idx = (yyyy == year)
        loc = np.asarray(prev['cities'][idx])
        locu = np.unique(loc)
        size = np.zeros(len(locu), int)
        for iloc in range(len(locu)):
            row_coo = coo['loc'] == locu[iloc]
            if np.sum(row_coo) == 1:
                size[iloc] = np.sum(loc == locu[iloc])
                lat = float(coo['lat'][row_coo])
                long = float(coo['long'][coo['loc'] == locu[iloc]])
                tip = locu[iloc]+'('+str(year) + '):  ' + str(size[iloc])  # + str(mag[ii]) + depth  + '<br> '
                folium.CircleMarker(location=[lat, long],
                                    tooltip=tip,
                                    radius=float(np.max([size[iloc]**0.5*2, 1])),
                                    fill=True,
                                    fill_color=chex[year-2019],
                                    color=chex[year-2019],
                                    opacity=0.5,
                                    fill_opacity=0.5
                                    ).add_to(grp[year-2019])
            else:
                print('cannot find coord for '+locu[iloc])
    pasts = [np.where(past_7d)[0], np.where(past_24h)[0]]
    for last in [0, 1]:
        idx = pasts[last]
        if len(idx) > 0:
            loc = np.asarray(prev['cities'][idx])
            locu = np.unique(loc)
            size = np.zeros(len(locu), int)
            for iloc in range(len(locu)):
                size[iloc] = np.sum(loc == locu[iloc])
                lat = float(coo['lat'][coo['loc'] == locu[iloc]])
                long = float(coo['long'][coo['loc'] == locu[iloc]])
                tip = locu[iloc]+'('+str(year) + '):  ' + str(size[iloc])  # + str(mag[ii]) + depth  + '<br> '
                folium.CircleMarker(location=[lat, long],
                                    tooltip=tip,
                                    radius=float(np.max([size[iloc]**0.5*2, 1])),
                                    fill=True,
                                    fill_color=chex[5+last],
                                    color=chex[5+last],
                                    opacity=1,
                                    fill_opacity=1
                                    ).add_to(grp[5+last])


    for ig in range(len(gnames)):
        grp[ig].add_to(map)
    folium.map.LayerControl('topleft', collapsed=False).add_to(map)
    map.save("docs/alarms_by_year.html")
print('done')
