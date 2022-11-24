import streamlit as st
import pandas as pd
import psycopg2
import time
import random
from PIL import Image
import datetime
from datetime import date
from st_aggrid import AgGrid, GridUpdateMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from sqlalchemy import create_engine
import sqlalchemy
import numpy as np
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
img=Image.open('lo.jfif')
st.set_page_config(page_title="Dashboard", page_icon=img)

hide_menu_style= """
          <style>
          #MainMenu {visibility: hidden; }
          footer {visibility: hidden;}
          </style>
          """

engine = create_engine('postgresql+psycopg2://{}:{}@{}/{}'.format(st.secrets["postgres"]['user'],st.secrets["postgres"]['password'],st.secrets["postgres"]['host'],st.secrets["postgres"]['dbname']))
st.markdown(hide_menu_style, unsafe_allow_html=True)
# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

conn.autocommit = True

sql="""select count(*) from dash_db;"""
cursor = conn.cursor()
cursor.execute(sql)
nind=cursor.fetchall()

sql = """select * from Dash_User"""
cursor = conn.cursor()
cursor.execute(sql)
df=pd.DataFrame(cursor.fetchall(),columns=['ID','User', 'nome',	'Dipartimento',	'Qualifica', 'Tariffa'])

sql = """select * from Dash_Cl"""
cursor = conn.cursor()
cursor.execute(sql)
dg=pd.DataFrame(cursor.fetchall(),columns=['ID','cliente', 'attivita',	'Chiave',	'Referente', 'codice'])

def check_password():
    """Returns `True` if the user had a correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            #del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True , st.session_state["username"]

#if "t0" not in st.session_state:
#    st.session_state["t0"] = time.time()
#####################################################Buttons and session state
if "Create Table" not in st.session_state:
    st.session_state["Create Table"] = False

if "Confirm" not in st.session_state:
    st.session_state["Confirm"] = False

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1', startrow=1, header=False)
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    cell_format = workbook.add_format()
    cell_format.set_align('center')
    cell_format.set_align('vcenter')
    worksheet.set_column('A:ZZ', 25,cell_format)
    header_format = workbook.add_format({
    'bold': True,
    'text_wrap': True,
    'valign': 'vdistributed',
    'align' : 'center',
    'fg_color': '#A5F5B0'})#,
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    worksheet.set_column('A:ZZ', 25)
    writer.save()
    processed_data = output.getvalue()
    return processed_data
###########################################################

@st.cache(allow_output_mutation=True)
def get_data():
    return []

d = date.today()
A=d.weekday()
C=[]
for i in range(7):
    #C.append((d + datetime.timedelta(days=i-A)).strftime("%y-%m-%d"))
    C.append('{} - {}'.format((d + datetime.timedelta(days=i-A)).strftime("%y-%m-%d"), (d + datetime.timedelta(days=i-A)).strftime("%A") ))

#att_op = ('Recupero Crediti', 'Consulenza legale', 'DD','Contenzioso')
#clients_op=tuple(dg['cliente'].tolist())
dat_op=tuple(C)
if check_password():
    kos,st.session_state["username"]=check_password()
    if st.session_state["username"] not in ['Marco_Troisi', 'Antonio_Schiavone', 'Sina_Kian']:
        st.session_state["aut"] = 'user'
    else:
        st.session_state["aut"] = 'sup'
    DFST=get_data()
    dfs=df[df['User']==st.session_state["username"]][df.columns[1:]]
    st.image(
        #"https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/apple/325/floppy-disk_1f4be.png",
        "https://media-exp1.licdn.com/dms/image/C560BAQE17_4itIWOLw/company-logo_200_200/0/1570546904891?e=2147483647&v=beta&t=w-App-ZgjSHDlEDDFQeNB7XU2L7QgY2EF-vFj2Il8q8",
        width=150,
    )

    st.title("Timesheet 📅")
    st.write(dfs)
    st.write("")
    if st.session_state["aut"] == 'user':
        st.markdown(
            """This is a demo of a  `Timesheet` that you have to insert your daily **activities**."""
            )
        st.markdown('Please select the **_clients_** you worked for this week.')
        options = st.multiselect(
        '',
        dg['cliente'],
        )
        das= pd.DataFrame(columns=['dat', 'cliente','effort'],index=range(15))
        st.write("")
        st.write("")
        st.subheader("① Fill and select cells")
        st.info("💡 Please check the **boxes** after filling _Table_.")
        st.caption("")
        #das.reset_index(inplace=True)
        gd = GridOptionsBuilder.from_dataframe(das)
        gd.configure_pagination(enabled=True)
        gd.configure_default_column(editable=True, groupable=True)
        gd.configure_selection(selection_mode="multiple", use_checkbox=True)
        #gd.configure_column('attivita', editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': att_op })
        gd.configure_column('cliente', editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': options })
        gd.configure_column('dat', editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': dat_op })
        gridoptions = gd.build()
        grid_table = AgGrid(
            das,
            fit_columns_on_grid_load=True,
            width=20,
            gridOptions=gridoptions,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            theme="streamlit",
        )


        st.subheader(" ② Check your selection")
        st.info("💡 Please type Your User to **Create Table** and control the data, if it is alright then Confirm.")
        user_conf = st.text_input("", "User Name", help="No spaces allowed (Use '_')")
        if st.button("Create Table"):
            st.session_state["Create Table"] = not st.session_state["Create Table"]
        if user_conf==st.session_state["username"]:
            if st.session_state["Create Table"]:
                dash_data=pd.merge(pd.DataFrame(grid_table["selected_rows"]),dg[['cliente', 'codice']], on=['cliente'], how='left')
                dash_data=dash_data[dash_data.columns[1:]].fillna(0)
                dash_data['nome']=[dfs['nome'].iloc[0]]*len(dash_data)
                dash_data=dash_data[['nome']+dash_data.columns[:-1].tolist()]
                st.write(dash_data)
                dash_data['effort'] = dash_data['effort'].astype(float)
                st.dataframe(pd.pivot_table(dash_data, values='effort', index=['dat'],aggfunc=np.sum).style.format({"effort":"{:.3}"}))
                st.warning('If You confirm, data will be saved in DataBase!', icon="⚠️")
                if st.button("Confirm"):
                    st.session_state["Confirm"] = not st.session_state["Confirm"]
                if st.session_state["Confirm"]:
                    DF=pd.merge(dash_data,df, on='nome', how='left')
                    DFF=pd.merge(DF,dg, on=['cliente','codice'], how='left')
                    DFF['effort']=DFF['effort'].astype(float)
                    DFF['costo']=DFF['effort']*DFF['Tariffa']
                    for i in DFF.index:
                        DFF['dat'].loc[i]=DFF['dat'].loc[i].split(' ')[0]
                    DFF['dat'] = pd.to_datetime(DFF['dat'],format="%y-%m-%d")
                    DFF['mese']=['']*len(DFF)
                    DFF['anno']=['']*len(DFF)
                    for i in DFF.index:
                        DFF['mese'].loc[i]=DFF['dat'].loc[i].month
                        DFF['anno'].loc[i]=DFF['dat'].loc[i].year
                    DFF=DFF[['nome', 'Qualifica', 'cliente', 'dat', 'attivita', 'effort', 'Tariffa','costo','mese','anno', 'Referente','codice']]
                    DFF.columns=['risorsa', 'qualifica', 'commessa', 'data', 'attivita',
                                               'effort', 'tariffa', 'costo', 'mese', 'anno', 'referente', 'codice']
                    DFF.index=range(nind[0][0],nind[0][0]+len(DFF))
                    DFF.fillna("",inplace=True)
                    DFF.to_sql('dash_db',engine,
                                          if_exists = 'append',
                                          index = True,
                                          )
                    st.snow()
    elif st.session_state["aut"] == 'sup':
        todo = st.selectbox(
        'What do you want to do?',
        ['Insert to dashboard', 'Extract excel', 'Modify DataBase', 'Dashboarding Charts'],
        )
        if todo=='Insert to dashboard':
            st.markdown(
                """This is a demo of a  `Timesheet` that you have to insert your daily **activities**."""
                )
            st.markdown('Please select the **_clients_** you worked for this week.')
            options = st.multiselect(
            '',
            dg['cliente'],
            )
            das= pd.DataFrame(columns=['dat', 'cliente','effort'],index=range(15))
            st.write("")
            st.write("")
            st.subheader("① Fill and select cells")
            st.info("💡 Please check the **boxes** after filling _Table_.")
            st.caption("")
            #das.reset_index(inplace=True)
            gd = GridOptionsBuilder.from_dataframe(das)
            gd.configure_pagination(enabled=True)
            gd.configure_default_column(editable=True, groupable=True)
            gd.configure_selection(selection_mode="multiple", use_checkbox=True)
            #gd.configure_column('attivita', editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': att_op })
            gd.configure_column('cliente', editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': options })
            gd.configure_column('dat', editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': dat_op })
            gridoptions = gd.build()
            grid_table = AgGrid(
                das,
                fit_columns_on_grid_load=True,
                width=20,
                gridOptions=gridoptions,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                theme="streamlit",
            )


            st.subheader(" ② Check your selection")
            st.info("💡 Please type Your User to **Create Table** and control the data, if it is alright then Confirm.")
            user_conf = st.text_input("", "User Name", help="No spaces allowed (Use '_')")
            if st.button("Create Table"):
                st.session_state["Create Table"] = not st.session_state["Create Table"]
            if user_conf==st.session_state["username"]:
                if st.session_state["Create Table"]:
                    dash_data=pd.merge(pd.DataFrame(grid_table["selected_rows"]),dg[['cliente', 'codice']], on=['cliente'], how='left')
                    dash_data=dash_data[dash_data.columns[1:]].fillna(0)
                    dash_data['nome']=[dfs['nome'].iloc[0]]*len(dash_data)
                    dash_data=dash_data[['nome']+dash_data.columns[:-1].tolist()]
                    st.write(dash_data)
                    dash_data['effort'] = dash_data['effort'].astype(float)
                    st.dataframe(pd.pivot_table(dash_data, values='effort', index=['dat'],aggfunc=np.sum).style.format({"effort":"{:.3}"}))
                    st.warning('If You confirm, data will be saved in DataBase!', icon="⚠️")
                    if st.button("Confirm"):
                        st.session_state["Confirm"] = not st.session_state["Confirm"]
                    if st.session_state["Confirm"]:
                        DF=pd.merge(dash_data,df, on='nome', how='left')
                        DFF=pd.merge(DF,dg, on=['cliente','codice'], how='left')
                        DFF['effort']=DFF['effort'].astype(float)
                        DFF['costo']=DFF['effort']*DFF['Tariffa']
                        for i in DFF.index:
                            DFF['dat'].loc[i]=DFF['dat'].loc[i].split(' ')[0]
                        DFF['dat'] = pd.to_datetime(DFF['dat'],format="%y-%m-%d")
                        DFF['mese']=['']*len(DFF)
                        DFF['anno']=['']*len(DFF)
                        for i in DFF.index:
                            DFF['mese'].loc[i]=DFF['dat'].loc[i].month
                            DFF['anno'].loc[i]=DFF['dat'].loc[i].year
                        DFF=DFF[['nome', 'Qualifica', 'cliente', 'dat', 'attivita', 'effort', 'Tariffa','costo','mese','anno', 'Referente','codice']]
                        DFF.columns=['risorsa', 'qualifica', 'commessa', 'data', 'attivita',
                                                   'effort', 'tariffa', 'costo', 'mese', 'anno', 'referente', 'codice']
                        DFF.index=range(nind[0][0],nind[0][0]+len(DFF))
                        DFF.fillna("",inplace=True)
                        DFF.to_sql('dash_db',engine,
                                              if_exists = 'append',
                                              index = True,
                                              )
                        st.snow()
        elif todo=='Extract excel':
            tabex = st.radio('Which table do you want to extract from DataBase?',('Clients','Employees','Timesheet'),horizontal=True)
            if tabex=='Timesheet':
                sql="""select * from dash_db;"""
                cursor = conn.cursor()
                cursor.execute(sql)
                dex=pd.DataFrame(cursor.fetchall(), columns=['index', 'risorsa', 'qualifica' , 'commessa' , 'data' ,'attivita', 'effort', 'tariffa', 'costo',  'mese', 'anno',  'referente'  ,'codice'])
                final_file = to_excel(dex)
                st.download_button(
                   "Press to Download",
                   final_file,
                   "Timesheet_{}.xlsx".format(d.strftime("%m_%d_%y")),
                   "text/csv",
                   key='download-excel'
                )
            elif tabex=='Clients':
                final_file = to_excel(dg)
                st.download_button(
                   "Press to Download",
                   final_file,
                   "Clients_{}.xlsx".format(d.strftime("%m_%d_%y")),
                   "text/csv",
                   key='download-excel'
                )
            elif tabex=='Employees':
                final_file = to_excel(df)
                st.download_button(
                   "Press to Download",
                   final_file,
                   "Employees_{}.xlsx".format(d.strftime("%m_%d_%y")),
                   "text/csv",
                   key='download-excel'
                )
        elif todo=='Modify DataBase':
            CRUD=st.radio("Please Select what do you want to modify?",['Add', 'Modify', 'Delete'],horizontal=False)
            table = st.selectbox(
            'Which table do you want to edit?',
            ['Clients', 'Employees'],
            )
            if (CRUD=='Add') and (table=='Clients'):
                st.write("")
                st.write("")
                st.write("")
                st.info("Please insert the requested data to add a new client")
                sql="""select count(*) from dash_cl;"""
                cursor = conn.cursor()
                cursor.execute(sql)
                cind=cursor.fetchall()
                s1 = st.text_input('Nome Cliente', '')
                s2= st.selectbox('Tipologia:', ['Recupero Crediti', 'Consulenza legale', 'DD','Contenzioso'])
                s3= st.text_input('Chiave', '')
                s4= st.selectbox('Referente:', ['Simone Tumino', 'Giulia Galati', 'Antonio Schiavone', 'Antonio Rabossi', 'Marco Troisi', 'Michele Pellicciari', 'Ilaria Bini', 'Chiara Valenti', 'Valeria Sangalli', 'Andrea Unfer', 'Luca Puterio', 'Davide Corrado', 'Isabella Marchetti', 'Vittorio Petruzzi', 'Margaret Scolaro', 'Claudia Vennara', 'Benedetto Daluiso', 'Alessandro Di Paola', 'Lamberto Banfi', 'Stefano Menghini', 'Alessandra Torchi', 'Giulia Piccolantonio', 'Federica Morandotti', 'Davide Sarina', 'Ester Famao', 'Eleonora Gioia', 'Angela Romano', 'Alice Giubbi', 'Giuseppe Provinzano', 'Manuela Consoli', 'Ilenia Febbi', 'Federica Colombo', 'Cristiano Laspesa'])
                s5= st.text_input('Codice', '')
                if st.button('Add Client'):
                    sql= '''insert into dash_cl ("index","cliente", "tipologia", "chiave", "referente", "codice") values ('{}', '{}', '{}', '{}', '{}','{}');'''.format(cind[0][0],s1,s2,s3,s4,s5)
                    cursor.execute(sql)
                    conn.commit()
                    with st.spinner('Wait for it...'):
                        time.sleep(1)
                    st.success('New Client is inserted!')
                    st.balloons()
            elif (CRUD=='Add') and (table=='Employees'):
                st.write("")
                st.write("")
                st.write("")
                st.info("Please insert the requested data to add a new employee")
                sql="""select count(*) from dash_user;"""
                cursor = conn.cursor()
                cursor.execute(sql)
                cind=cursor.fetchall()
                s2= st.text_input('Name and Last name', '')
                s1 = s2.replace(' ','_')
                s3= st.selectbox('Dipartimento:', ['Intrum Law Italy', 'LML', 'Gextra'])
                s4= st.selectbox('Qualifica:', ['Managing Partner', 'Senior Legal Advisor', 'Partner',
                                                'Senior Partner', 'Legal Advisor', 'Junior Legal Advisor', 'Staff',
                                                'Paralegal'])
                st.info('Insert Numeric valuers for Tariffa', icon="ℹ️")
                s5= st.text_input('Tariffa', '')
                if st.button('Add Employee'):
                    sql= '''insert into dash_user ("index","user", "nome", "dipartimento", "qualifica", "tariffa") values ('{}', '{}', '{}', '{}', '{}','{}');'''.format(cind[0][0],s1,s2,s3,s4,s5)
                    cursor.execute(sql)
                    conn.commit()
                    with st.spinner('Wait for it...'):
                        time.sleep(1)
                    st.success('New User is inserted!')
                    st.balloons()
            elif (CRUD=='Delete') and (table=='Clients'):
                st.write("")
                st.write("")
                st.write("")
                st.info("Please insert the requested data to delete the unwanted client")
                s= st.selectbox('Client name:', dg['cliente'])
                if st.button('Delete Client'):
                    sql= '''delete from dash_cl
                            where dash_cl.cliente={};'''.format(s)
                    cursor.execute(sql)
                    conn.commit()
                    with st.spinner('Wait for it...'):
                        time.sleep(1)
                    st.success('Client is removed!')
                    st.balloons()
            elif (CRUD=='Delete') and (table=='Employees'):
                st.write("")
                st.write("")
                st.write("")
                st.info("Please insert the requested data to delete the unwanted employee")
                s= st.selectbox('Employee name:', df['nome'])
                if st.button('Delete Employee'):
                    sql= '''delete from dash_user
                            where dash_user.nome='{}';'''.format(s)
                    cursor.execute(sql)
                    conn.commit()
                    with st.spinner('Wait for it...'):
                        time.sleep(1)
                    st.success('Employee is removed!')
                    st.balloons()
            elif (CRUD=='Modify') and (table=='Employees'):
                st.write("")
                st.write("")
                st.write("")
                st.info("Please insert the requested data to edit the employee's data")
                s1= st.selectbox('Employee name:', df['nome'])
                s2= st.selectbox('Choose what you want to modify:', ['qualifica', 'tariffa'])
                if s2=='qualifica':
                    s3=st.selectbox('qualifica nuova:', df['Qualifica'].unique().tolist())
                elif s2=='tariffa':
                    st.info('Insert Numeric valuers for Tariffa\n example: 35', icon="ℹ️")
                    s3=st.text_input('tariffa nuova:', '')
                if st.button('Modify'):
                    sql= '''UPDATE dash_user
                            SET {}='{}'
                            where nome='{}';'''.format(s2,s3,s1)
                    st.write(sql)
                    cursor.execute(sql)
                    conn.commit()
                    with st.spinner('Wait for it...'):
                        time.sleep(1)
                    st.success('edit done!')
                    st.balloons()
            elif (CRUD=='Modify') and (table=='Clients'):
                st.write("")
                st.write("")
                st.write("")
                st.warning("You cannot modify clients' data!")
