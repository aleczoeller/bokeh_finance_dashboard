# -*- coding: utf-8 -*-

"""
***************************************************
*    bokeh-finance-dashboard.py
*    --------------------------
*    Script to launch bokeh app with randomly 
*    generated financial/loan data and display
*    various aspects using different bokeh
*    displays.  Synchronizes user input and 
*    updates to different displays.
*
*    Borrows/extends features from following bokeh
*    example apps:
*    
*    @bryevdv's IMDB movie app:
*    https://github.com/bokeh/bokeh/tree/master/examples/app/movies
*
*    @mattpap and @bryevdv's table download app:
*    https://github.com/bokeh/bokeh/tree/master/examples/app/export_csv
"""

__version__ = '0.2'
__author__ = 'Alec Zoeller'


import pandas as pd
import numpy as np
from collections import Counter
import math
import os
from datetime import datetime

from bokeh.core.properties import value
from bokeh.plotting import figure
from bokeh.layouts import layout, column, row, gridplot
from bokeh.models import ColumnDataSource, Div, HoverTool, CustomJS
from bokeh.models.widgets import Slider, Select, Button, DataTable, TableColumn, NumberFormatter
from bokeh.models import NumeralTickFormatter, ColorBar
from bokeh.palettes import Spectral6
from bokeh.transform import linear_cmap
from bokeh.io import curdoc, save, output_file, show


#Set term (in months) and states used for example data
terms = [48, 60, 72, 84, 96]
states = ['Indiana', 'California', 'Florida', 'Ohio', 'Georgia', 'South Carolina', 'Utah', 
         'North Carolina', 'District of Columbia', 'Virginia', 'Maryland', 'Colorado', 'Vermont']

#Randomly generate individual loan data for display
years = np.random.randint(low=2009, high=2020, size=5000)
months = np.random.randint(low=1, high=13, size=5000)
processing = np.random.randint(low=1, high=45, size=5000)
fico = np.random.randint(low=588, high=821, size=5000)
booked = np.random.randint(low=0, high=2, size=5000)
principal = np.array([round(i, 2) for i in list(np.random.rand(5000)*100000)])
term = np.random.choice(terms, size=5000)
fixed = np.random.randint(low=0, high=2, size=5000)
rate = np.random.rand(5000)*4 + 4
states= np.random.choice(states, size=5000)


#Create dataframe with randomly generated data
df = pd.DataFrame({'Year':years, 'Month':months, 'State': states, 'Processing':processing,'FICO':fico,
                   'Booked':booked,'Principal': principal, 'Term': term, 'Fixed':fixed,'Rate':rate})
states = ['Indiana', 'California', 'Florida', 'Ohio', 'Georgia', 'South Carolina', 'Utah', 
         'North Carolina', 'District of Columbia', 'Virginia', 'Maryland', 'Colorado', 'Vermont']
states.insert(0, 'All')
terms.insert(0, 'All')

#Establish current year and previous, so display in app is always current
thisyear, thismonth = datetime.now().year, datetime.now().month
if thismonth == 1:
    lastmonth = 12
    lastyear = thisyear - 1
else:
    lastmonth = thismonth - 1
    lastyear = thisyear
principal_this_month = df[(df['Year']==thisyear) & (df['Month']==thismonth)]['Principal'].sum()
principal_last_month = df[(df['Year']==lastyear) & (df['Month']==lastmonth)]['Principal'].sum()

#Create most common loan term series for data by month and state
modet = df.groupby(["Year", "Month", "State"]).agg({'Term':lambda x: x.mode().iloc[0]})['Term'].reset_index()

#Create text objects that update automatically with data/filter change options
desc = Div(text="Loan data generated randomly - filter with options below. Scroll down for "           "finteractive table and download.", sizing_mode='scale_width')
this_month = Div(text="${} total principal this month so far.".format(str(round(principal_this_month, 2))),
                 sizing_mode='scale_width')
last_month = Div(text="${} total principal last month.".format(str(round(principal_last_month, 2))),
                sizing_mode='scale_width')

#Summarize data by month and state
df = df.groupby(["Year", "Month", "State"]).agg({'Booked':'mean', 'FICO':'mean','Fixed':'mean', 
                                                          'Principal':['mean','sum'], 'Processing': ['mean', 'count'],
                                                         'Rate':['min','max','mean'], 'Term':'median'})
df.reset_index(inplace=True)
#Apply most common loan term value to summary dataframe
df['TermMode'] = modet['Term'].values

#Create interaction widgets and their source data, as empty frame
rates = sorted(list(Counter(df['Rate']['mean'].values).keys()))
year_slider = Slider(title="Year", value=2019, start=df.reset_index()['Year'].values.min(), end=df.reset_index()['Year'].values.max())
state_select = Select(title="State", value="All", options=states)
terms = [str(i) for i in terms]
term_select = Select(title="Term (mode)", value="All", options=terms)
rate_min = Slider(title="Minimum Rate Selection", value=round(min(rates), 1), 
                  start=round(min(rates),1),end=round(max(rates), 1))
rate_max = Slider(title="Maximum Rate Selection", value=round(max(rates), 1), start=round(min(rates), 1),
                          end=round(max(rates), 1))
source = ColumnDataSource(data=dict(month=[],meanprincipal=[],totalprincipal=[],numberloans=[],
                                    state=[],year=[],fixedratio=[],dotsize=[],
                                    acceptratio=[],meanprocessing=[],meanrate=[], termmode=[]
                                    ))

#Create button for table download and link to script to download populated table
button = Button(label='Download Table', button_type='success')
button.callback = CustomJS(args=dict(source=source), code=open(os.path.join(os.path.dirname(__file__), 
                                                                            "download.js")).read())
#Create and set layout for initial graph
p = figure(plot_height=500, plot_width=500, y_range=[i for i in states if not i == 'All'], title="", toolbar_location=None,
          sizing_mode="fixed")#"scale_both")
p.xaxis.major_label_orientation = math.pi/2
p.xaxis.major_label_overrides = {1: 'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June', 7:'July',
                                8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}
#Create second graph and define tooltips
p2 = figure(plot_height=500, plot_width=500, title="", toolbar_location=None, sizing_mode="fixed")
hover = HoverTool()
hover.tooltips = [
    ("State", "@state"),
    ("Year", "@year"),
    ("Month", "@month"),
    ("Mean Principal", "$@meanprincipal{0,0.00}"),
    ("Total Principal", "$@totalprincipal{0,0.00}"),
    ("Number of Loans", "@numberloans"),
    ("Mean Interest Rate", "@meanrate"),
    ("Mean Processing (days)", "@meanprocessing"),
    ("Percentage Fixed Rate", "@fixedratio{0.2f}%"),
    ("Percentage Accepted/Completed", "@acceptratio{0.2f}%")
]
hover.formatters = {
    "Mean Principal":"printf",
    "Total Principal":"printf",
    "Percentage Fixed Rate":"printf",
    "Percentage Accepted/Completed": "printf",
}
p.tools.append(hover)
p.outline_line_width = 7
p.outline_line_alpha = 0.3
p.outline_line_color = "navy"
#Color graph by average loan rate
mapper = linear_cmap(field_name='meanrate', palette=Spectral6, low=int(min(rates)), high=int(max(rates)))
r1 = p.circle(x="month",y="state",size="dotsize",source=source, line_color='black', line_width=0.4, color=mapper)
color_bar = ColorBar(color_mapper=mapper['transform'], width=5,  location=(0,0))
p.add_layout(color_bar, 'right')
#Add tooltips to second graph
p2.tools.append(hover)
p2.outline_line_width = 7
p2.outline_line_alpha = 0.3
p2.outline_line_color = "navy"
#Set up second graph's vertical bars
r2 = p2.vbar(x="month", top="totalprincipal",
              source=source, width=0.5, color='green')
p2.xaxis.major_label_orientation = math.pi/2
p2.xaxis.major_label_overrides = {1: 'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June', 7:'July',
                                8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}
p2.yaxis[0].formatter = NumeralTickFormatter(format="0,0")
hover.renderers = [r1, r2]
#Set up table columns and define formatting
tcolumns = [
    TableColumn(field='year', title='Year'),
    TableColumn(field='month', title='Month'),
    TableColumn(field='state', title='State'),
    TableColumn(field='meanprincipal', title='Mean Principal',
                    formatter=NumberFormatter(format="$0,0.00")),
    TableColumn(field='totalprincipal', title='Total Principal', 
                    formatter=NumberFormatter(format="$0,0.00")),
    TableColumn(field='numberloans', title='Number of Loans'),
    TableColumn(field='meanrate', title='Mean Interest Rate'),
    TableColumn(field='meanprocessing', title='Average Days to Book'),
    TableColumn(field='termmode', title='Most Common Term'),
    TableColumn(field='fixedratio', title='Percentage Fixed Rate'),
    TableColumn(field='acceptratio', title='Started Loans Booked')
]
data_table = DataTable(source=source, columns=tcolumns, width=800)

#Define methods for selection and update of data by widgets/filters
def select_data():
    year_sel = year_slider.value
    state_sel = state_select.value
    term_sel = term_select.value
    rate_min_sel = rate_min.value
    rate_max_sel = rate_max.value
    
    if state_sel == 'All':
        list_states = [i for i in states if not i == 'All']
    
    selected = df[
            (df['Year'] == year_sel) &
            (df['Rate']['min'] > rate_min_sel) &
            (df['Rate']['max'] < rate_max_sel)]
    if state_sel != 'All':
        selected = selected[selected['State'] == state_sel]
    if term_sel != 'All':
        selected = selected[selected['TermMode'] == int(term_sel)]
    return selected

#Set update function to populate ALL figures
def update():
    upd_df = select_data()
    
    p.title.text = "{} loans | sized by principal | colored by rate".format(str(len(upd_df)))
    source.data = dict(
        month = upd_df['Month'],
        year = upd_df['Year'],
        state= upd_df['State'],
        meanprincipal = upd_df['Principal']['mean'],
        totalprincipal = upd_df['Principal']['sum'],
        numberloans = upd_df['Processing']['count'],
        meanrate = upd_df['Rate']['mean'],
        meanprocessing = upd_df['Processing']['mean'],
        termmode = upd_df['TermMode'],
        fixedratio = upd_df['Fixed']['mean'].apply(lambda x: (x*100)),
        acceptratio = upd_df['Booked']['mean'].apply(lambda x: (x*100)),
        dotsize = (upd_df['Principal']['sum'].values / upd_df['Principal']['sum'].values.max())*20 + 2
        )
controls = [year_slider,state_select,term_select,rate_min,rate_max]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())
inputs = column(*controls, width=320, height=500)
inputs.sizing_mode = "fixed"

l = layout(row([desc, this_month, last_month]), row([inputs, p, p2], height=600),
           row([button, data_table]),sizing_mode="fixed")
#On app load, populate data that has been created and add figures to page           
update()
curdoc().add_root(l)
curdoc().title = "Loan Status Dashboard"


