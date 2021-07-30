import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os, time

DEBUG = False

FILE = 'Casos_positivos_de_COVID-19.csv'

@st.cache(persist=True)
def load_csv_data(address):
    print("Reading data...")

    
    read_col = ['ID de caso','Fecha de notificación','Nombre municipio','Nombre departamento','Ubicación del caso', 'Recuperado',
                'Edad','Sexo','Estado','Fecha de muerte','Fecha de diagnóstico','Fecha de recuperación', 'fecha reporte web']

  
    data = pd.read_csv(address, usecols = read_col, low_memory = False)

    data = data.replace({'Sexo': {'f': 'F', 'm': 'M'}})

    
    data = data.replace({'Sexo': {'F': 'Femenino', 'M': 'Masculino'}})

    data = data.replace({'Nombre departamento': {'BARRANQUILLA': 'ATLANTICO',
                                                      'CARTAGENA': 'BOLIVAR',
                                                      'Buenaventura D.E.': 'VALLE',
                                                      'STA MARTA D.E.': 'MAGDALENA'}})

   
    data['Ubicación del caso'] = data['Ubicación del caso'].fillna('Fallecido NO COVID')

   
    data['Estado'] = data['Estado'].fillna('N/A')

   
    dptos = data['Nombre departamento'].dropna().unique()
    towns = data['Nombre municipio'].dropna().unique()

 
    data['fecha reporte web'] = pd.to_datetime(data['fecha reporte web'], infer_datetime_format=True, dayfirst=True)
    data['Fecha de muerte'] = pd.to_datetime(data['Fecha de muerte'], infer_datetime_format=True, dayfirst=True)
    data['Fecha de notificación'] = pd.to_datetime(data['Fecha de notificación'], infer_datetime_format=True, dayfirst=True)
    data['Fecha de diagnóstico'] = pd.to_datetime(data['Fecha de diagnóstico'], infer_datetime_format=True, dayfirst=True)
    data['Fecha de recuperación'] = pd.to_datetime(data['Fecha de recuperación'], infer_datetime_format=True, dayfirst=True)

    #
    data = data.replace({'Ubicación del caso': {'casa': 'Casa', 'CASA': 'Casa'}})
    data = data.replace({'Estado': {'moderado': 'Moderado', 'LEVE': 'Leve', 'leve': 'Leve'}})
    data = data.replace({'Recuperado': {'fallecido': 'Fallecido'}})
.

    return (data, dptos, towns)

def data_report(info, report, label, acum = False):
    '''
    Inputs:
        acum   -> True:  process the accumulated sum
                  False: process the partial sum

        info   -> An object of type Pandas DataFrame with at least two columns:
                  one called with name in 'report' param and the other 'ID de caso'
                  this must be the second column of the Dataframe

        report -> String with the column name of the report needed

        label  -> String with the column name where the data sum will be written

    Output:
        Returns an object of type DataFrame from the pandas library whose index
        is the param 'report' and has a single column whose name is the respective
        param 'label'
    '''

    info = info.groupby(report).count()[[info.columns[1]]]


    info = info.rename(columns = {info.columns[0]:label})


    if acum :
        info = info.cumsum()

    return info
#=======================================================================================================================================#
#=======================================================================================================================================#
# Caches the information
@st.cache(persist=True)
def get_summary(info, key_list, dpto_info = True):
    info = info.reset_index()
    info = info.drop(columns=info.columns[0])

    if dpto_info:
        info = info.set_index('Nombre departamento')
        col_name = 'Departamento'
    else:
        info = info.set_index('Nombre municipio')
        col_name = 'Municipio'

    info_dict = {}
    diag_acum = []
    recu = []
    fallecidos = []
    UCI = []

    for key in key_list:

        nun_fallecidos = 0
        num_UCI = 0
        num_recuperados = 0
        casos_diag = 0

        if not isinstance(info.loc[key], pd.Series):

           
            casos_diag = data_report(info.loc[key], 'fecha reporte web', 'Casos', True).max()[0]

            
            d = data_report(info.loc[key], 'Ubicación del caso', 'Casos')

           
            if 'Fallecido' in d.index:
                nun_fallecidos = d.loc['Fallecido'].array[0]

           
            if 'Hospital UCI' in d.index:
                num_UCI = d.loc['Hospital UCI'].array[0]

           
            d = data_report(info.loc[key], 'Recuperado', 'Casos')

           
            if 'Recuperado' in d.index:
                num_recuperados = d.loc['Recuperado'].array[0]

        else:
            casos_diag = 1
            atencion = info.loc[key].loc['Ubicación del caso']

           
            if atencion == 'Recuperado':
                num_recuperados = 1
            elif atencion == 'Fallecido':
                nun_fallecidos = 1
            elif atencion == 'Hospital UCI':
                num_UCI = 1

        diag_acum.append(casos_diag)
        recu.append(num_recuperados)
        fallecidos.append(nun_fallecidos)
        UCI.append(num_UCI)

    info_dict.setdefault(col_name, key_list)
    info_dict.setdefault('Confirmados', diag_acum)
    info_dict.setdefault('Recuperados', recu)
    info_dict.setdefault('Fallecidos', fallecidos)
    info_dict.setdefault('En UCI', UCI)

    df = pd.DataFrame(data=info_dict)
    df = df.sort_values(by = 'Confirmados', ascending = False).reset_index()
    df.pop('index')

    return df
#=======================================================================================================================================#
#=======================================================================================================================================#
def get_info(csv_data, key_list, dpto_summary = True):
   
  
    cases = data_report(csv_data, 'fecha reporte web', 'Casos diagnosticados')

  
    if len(key_list) == 0:
        dpto_info = None
    else:
        dpto_info = get_summary(csv_data, key_list, dpto_summary)

    
    atention = data_report(csv_data, 'Ubicación del caso', 'Número de pacientes')

    status = data_report(csv_data, 'Estado', 'Número de pacientes')

   
    recu = data_report(csv_data, 'Recuperado', 'Número de pacientes')

    return (cases, status, dpto_info, atention, recu)
(all_data, all_dptos, all_muni) = load_csv_data(FILE)


hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stButton button {border-color: #f63366;color: #f63366; transform: translate(50%,50%);}
.stButton button:hover {border-color: #f63366;color: #fff; background: #f63366;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

import base64
st.title('Información COVID-19')
st.sidebar.title('Filtros')

tipo_reporte = st.sidebar.radio('Por tipo de reporte',['Nacional', 'Departamental', 'Municipal'])
tipo_grafica = st.sidebar.radio('Por tipo de pacientes', ['Reportados', 'Fallecidos', 'Recuperados'])

if tipo_reporte == 'Nacional':
    report_data = all_data
    report_list = all_dptos
    report_name = 'Colombia'
    summary_dpto = True

elif tipo_reporte == 'Departamental':
    
    dpto_select = st.sidebar.selectbox('Departamento',all_dptos)

  
    dpto_info = all_data.set_index('Nombre departamento')

    report_data = dpto_info.loc[dpto_select]
    report_list = all_data[all_data['Nombre departamento'] == dpto_select]['Nombre municipio'].dropna().unique()
    report_name = dpto_select
    summary_dpto = False

elif tipo_reporte == 'Municipal':
    
    dpto_select = st.sidebar.selectbox('Departamento',all_dptos)


    muni_per_dpto = all_data[all_data['Nombre departamento'] == dpto_select]['Nombre municipio'].unique()

    muni_select = st.sidebar.selectbox('Municipio',muni_per_dpto)

    muni_info = all_data.set_index(['Nombre departamento', 'Nombre municipio'])

    report_data = muni_info.loc[dpto_select, :].loc[muni_select]
    report_list = []
    report_name = muni_select
    summary_dpto = True

def general_info():
    '''
    get_info() loads general information from COVID data and stores it in 5 variables:

        |==========|========================================================|
        | Variable |                    Description                         |
        |==========|========================================================|
        |     a    |  sum of diagnostic cases per day.                      |
        |     b    |  summary of patients according to their health status. |
        |     c    |  summary of data by department or municipality.        |
        |     d    |  summary of patients by case location.                 |
        |     e    |  summary of patients by 'Recuperado' columns info.     |
        |==========|========================================================|
    '''
(a, b, c, d, e) = get_info(report_data, report_list, summary_dpto)


if (tipo_grafica == 'Recuperados' and 'Recuperado' in e.index) or (tipo_grafica == 'Fallecidos' and 'Fallecido' in e.index) or (tipo_grafica == 'Reportados'):

   
    if tipo_grafica != 'Reportados':
        report_data = report_data.reset_index().set_index('Recuperado').loc[tipo_grafica[0:len(tipo_grafica)-1]]

    
    sex_report = data_report(report_data, 'Sexo', 'Número de pacientes').reset_index()


    age_data = report_data.copy()

 
    age_data['Edad'] = age_data.loc[:,'Edad'].astype(str)

    age_data = data_report(age_data, 'Edad', 'Número de pacientes').reset_index()


    bins = pd.IntervalIndex.from_tuples([(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 60),
                                         (60, 70), (70, 80), (80, 90), (90, 120)], closed = 'left')


    names = ["0 - 9", "10 - 19", "20 - 29", "30 - 39", "40 - 49","50 - 59", "60 - 69", "70 - 79", "80 - 89",
             "Mayor de 89"]

    age_data['Intervalos'] = pd.cut(age_data['Edad'].astype(int), bins)
    age_data.pop('Edad')
    age_data = age_data.groupby('Intervalos').sum().reset_index()
    age_data['Intervalos'] = age_data['Intervalos'].categories = names

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#//                                                                                                                                    //
#//                                                          GRAPHIC STAGE                                                             //
#//                                                                                                                                    //
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# Graph of accumulated diagnosed cases
fig1 = px.line(a.cumsum(), y = a.columns[0], labels={'fecha reporte web':'Fecha de reporte'},
               title = "Histórico de casos reportados en " + report_name)
st.plotly_chart(fig1)


fig2 = px.line(a, y = a.columns[0], labels={'fecha reporte web':'Fecha de reporte'},
               title = "Histórico de casos diarios reportados en " + report_name)
st.plotly_chart(fig2)

fig_A = px.pie(e.reset_index(), values='Número de pacientes', names='Recuperado',
               title='Distribución por atención de casos reportados')
st.plotly_chart(fig_A)


fig_B = px.pie(b.reset_index(), values='Número de pacientes', names='Estado',
               title='Distribución por estado de casos reportados')
st.plotly_chart(fig_B)


if tipo_reporte != 'Municipal':
    st.header("Resumen " + tipo_reporte.lower())
    fig_C = px.bar(c, x = c.columns[0], y=[c.columns[4], c.columns[3], c.columns[2], c.columns[1]],
                   labels={c.columns[0]:'', 'value': 'Número de pacientes', 'variable': 'Variable'})
    st.plotly_chart(fig_C)

st.markdown("## Para filtrar las gráficas siguientes use el filtro 'Por tipo de pacientes' ubicado al costado izquierdo")

try:
   
    fig_D = px.pie(sex_report, values=sex_report.columns[1], names=sex_report.columns[0],
                   title='Distribución por sexo de casos ' + tipo_grafica.lower())
    st.plotly_chart(fig_D)

    fig_E = px.bar(age_data, x='Intervalos', y='Número de pacientes',
                   labels={'Intervalos': 'Edad'},height=400, title = "Distribución por edad de casos " + tipo_grafica.lower())
    st.plotly_chart(fig_E)

except NameError:
    st.markdown("### ❌ No existen pacientes " + tipo_grafica.lower())
