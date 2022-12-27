from tkinter import *
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
from tkcalendar import DateEntry
import pyodbc
import pandas as pd
import datetime

#global function
def sql_conn():
    try:
        conn = pyodbc.connect('DRIVER={SQL SERVER};'
                      'SERVER=ssapatsc.database.windows.net;'
                       'DATABASE=PATSC; UID=ssa.admin; PWD=$$Asatdb;Trusted_connection = yes')
    except Exception as e:
        print('task is terminated')
        tkinter.messagebox.showerror("Connection Error", "ไม่สามารถเชื่อมต่อกับฐานข้อมูลได้\nกรุณาตรวจสอบสถานะอินเทอร์เน็ต")
    return conn

def sql_read(read_statement):
    conn = sql_conn()
    SQL_Query = pd.read_sql_query(read_statement,conn)
    conn.close()
    #print(SQL_Query)
    return SQL_Query

def sql_insert(insert_statement, data):
    conn = sql_conn()
    cursor = conn.cursor()
    try:
        print(data)
        cursor.execute(insert_statement, data)
    except Exception as e:
        cursor.rollback()
        print(e.value)
        print('transaction rolled back')
        tkinter.messagebox.showerror("Insert rror",
                                     "ไม่สามารถเขียนข้อมูล ลงฐานข้อมูลได้")
    else:
        print('records inserted successfully')
        cursor.commit()
        cursor.close()
    finally:
        print('connection closed')
        conn.close()

def norad_uniq_check(norad, fiscalY, read_statement):
    sqlTB_u = sql_read(read_statement)
    sqlTB_u_fisY = sqlTB_u[sqlTB_u['Budget_Year'] == fiscalY]
    sqlTB_uniq = sqlTB_u_fisY.drop_duplicates('Norad_ID', keep='first')
    if int(norad) not in sqlTB_uniq['Norad_ID'].values:
        check_u = 1 # New NORAD in plan table
    else:
        check_u = 0 # Duplicate NORAD in plan table
    return check_u

def norad_month_check(norad, fiscalY, Date, read_statement):
    pic_month = (datetime.datetime.strptime(str(Date), "%Y-%m-%d")).month
    sqlTB_m = sql_read(read_statement)
    sqlTB_m_fisY = sqlTB_m[sqlTB_m['Budget_Year'] == fiscalY]
    sqlTB_month = sqlTB_m_fisY.loc[(sqlTB_m_fisY['Date'].astype('datetime64[ns]')).dt.month == pic_month]
    if int(norad) not in sqlTB_month['Norad_ID'].values:
        check_m = 1 # New NORAD in plan table this month
    else:
        check_m = 0 # don't add to plan table
    return check_m

def month_check(StartD, StopD):
    if (datetime.datetime.strptime(StartD, "%Y-%m-%d")).month == \
            (datetime.datetime.strptime(StopD, "%Y-%m-%d")).month:
        Dupl = 0 # same month
    else:
        Dupl = 1 # difference month need to duplicate input data
    return Dupl

def get_inputed(df,Norad, SatName, Orbit, SatCat):
    inputed_df  = df.append({'NORAD' : str(Norad), 'Satellite Name' : str(SatName), 'Orbit' : str(Orbit)
                                        , 'Satellite Category' : str(SatCat)}, ignore_index=True)
    return inputed_df

#Data or List to global use
inputed_df = pd.DataFrame()
fiscal_year_list= [66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81]
SCat_list = ['Thai', 'Military', 'ASEAN', 'Other']
site_list = ['Doi Inthanon', 'Ko Samui']
shift_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
sqlTB_SatData = sql_read('''SELECT * FROM [dbo].[Sat_data]''') #read satellite data

##frame setting
root = Tk()
root.title("SSA_Satellite_Count")
root.geometry('600x600')

Tab_notebook = ttk.Notebook(root)
Tab_notebook.pack()

Tab_frame_plan = Frame(Tab_notebook, width=600, height=400, bg='#d5e1df')
Tab_frame_pic = Frame(Tab_notebook, width=600, height=400, bg='#ffeead')

Tab_notebook.add(Tab_frame_plan, text='แผนการเฝ้าระวังทางอวกาศ')
Tab_notebook.add(Tab_frame_pic, text='ภาพถ่ายดาวเทียม')
Tab_notebook.pack(fill='both', expand='true')
#-----------------------------------------------------------------------------------------------------------------------

##Tab_frame_plan
#plan connection statement
insert_statement_plan = """
    INSERT INTO Planning
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
read_statement_plan = '''SELECT * FROM [dbo].[Planning]'''
#fuction
def DelText_plan():
    plan_fiscalY_choice.set('')
    plan_StartD_cal.delete(0,END)
    plan_StopD_cal.delete(0,END)
    plan_Norad.delete(0, END)
    plan_SCat_choice.set('')
    plan_Name.delete(1.0, END)
    plan_orbit.delete(1.0, END)
    plan_Country.delete(1.0, END)

def AddData_plan(plan_fiscalY,plan_StartD,plan_StopD,plan_norad,plan_SCat,plan_name, plan_orbit,plan_Country,insert_statement_plan, read_statement_plan):
    check_plan_new = norad_uniq_check(plan_norad, plan_fiscalY, read_statement_plan)
    dupl_plan = month_check(plan_StartD, plan_StopD)

    if check_plan_new == 1:
        plan_input = [plan_norad, plan_fiscalY, plan_StartD, plan_SCat, plan_name, plan_orbit, plan_Country, check_plan_new]
        sql_insert(insert_statement_plan, plan_input)
    else:
        check_plan_month = norad_month_check(plan_norad, plan_fiscalY, plan_StartD, read_statement_plan)
        if check_plan_month == 1:
            input_2plan_m = [plan_norad, plan_fiscalY, plan_StartD, plan_SCat, plan_name, plan_orbit, plan_Country, 0]
            sql_insert(insert_statement_plan, input_2plan_m)

    if dupl_plan == 1:
        check_dupl_month = norad_month_check(plan_norad, plan_fiscalY, plan_StopD, read_statement_plan)
        if check_dupl_month == 1:
            input_dupl_m = [plan_norad, plan_fiscalY, plan_StopD, plan_SCat, plan_name, plan_orbit, plan_Country, 0]
            sql_insert(insert_statement_plan, input_dupl_m)

def check_plan():
    plan_fiscalY = plan_fiscalY_choice.get()
    plan_StartD = str(plan_StartD_cal.get_date())
    plan_StopD = str(plan_StopD_cal.get_date())
    plan_norad = plan_Norad_txt.get()
    plan_SCat = plan_SCat_choice.get()
    plan_name_value = plan_Name.get(1.0, 'end-1c')
    plan_Orbit_value = plan_orbit.get(1.0, 'end-1c')
    plan_country_value = plan_Country.get(1.0, 'end-1c')
    confirm = tkinter.messagebox.askquestion('ยืนยันความถูกต้อง',' ปีงบประมาณ:  '+ str(plan_fiscalY)
                                             +'\n วันเริ่มต้นแผน:  '+ str(plan_StartD)
                                             +'\n วันสิ้นสุดแผน:  ' + str(plan_StopD)
                                             +'\n Norad ID:  ' + str(plan_norad)
                                             +'\n ประเภทดาวเทียม:  ' + str(plan_SCat)
                                             +'\n ชื่อดาวเทียม:  ' + plan_name_value
                                             +'\n Orbit type:  ' + str(plan_Orbit_value)
                                             +'\n ประเทศ:  ' + str(plan_country_value))
    if confirm == 'yes':
        show_df = get_inputed(inputed_df, plan_norad, plan_name_value, plan_Orbit_value, plan_SCat)
        plan_show.insert(tk.END, show_df)
        plan_show.insert(tk.END, '\n')
        AddData_plan(plan_fiscalY, plan_StartD, plan_StopD, plan_norad, plan_SCat, plan_name_value, plan_Orbit_value, plan_country_value,
                     insert_statement_plan, read_statement_plan)
        plan_Norad.delete(0, END)
        plan_SCat_choice.set('')
        plan_Name.delete(1.0, END)
        plan_orbit.delete(1.0, END)
        plan_Country.delete(1.0, END)
        tkinter.messagebox.showinfo("บันทึกข้อมูล", "บันทึกข้อมูล แผนการเฝ้าระวังทางอวกาศ\nเรียบร้อยแล้ว")

def call_NORAD_data_plan():
    plan_Name.delete(1.0, END)
    plan_orbit.delete(1.0, END)
    plan_Country.delete(1.0, END)
    norad = int(plan_Norad_txt.get())
    satdata_plan = sqlTB_SatData.where(sqlTB_SatData['NORAD'] == norad).dropna()
    satname_plan = (satdata_plan['SatelliteName'].values)[0]
    satorbit_plan = (satdata_plan['Orbit'].values)[0]
    satcountry_plan = (satdata_plan['Country'].values)[0]
    plan_Name.insert(tk.END,satname_plan)
    plan_orbit.insert(tk.END, satorbit_plan)
    plan_Country.insert(tk.END, satcountry_plan)


#grid config
Tab_frame_plan.columnconfigure(0, weight=1)
Tab_frame_plan.columnconfigure(1, weight=1)
Tab_frame_plan.columnconfigure(2, weight=1)
Tab_frame_plan.columnconfigure(3, weight=1)
Tab_frame_plan.columnconfigure(4, weight=1)
Tab_frame_plan.rowconfigure(0, weight=1)
Tab_frame_plan.rowconfigure(1, weight=1)
Tab_frame_plan.rowconfigure(2, weight=1)
Tab_frame_plan.rowconfigure(3, weight=1)
Tab_frame_plan.rowconfigure(4, weight=1)
Tab_frame_plan.rowconfigure(5, weight=1)
Tab_frame_plan.rowconfigure(6, weight=1)
Tab_frame_plan.rowconfigure(7, weight=1)
Tab_frame_plan.rowconfigure(8, weight=2)

#interface
Label_plan_header = Label(Tab_frame_plan, text='แผนการเฝ้าระวังทางอวกาศ', font=60, bg='#d5e1df').grid(row=0, column=0,columnspan =3)

Label_plan_fiscalY = Label(Tab_frame_plan, text='ปีงบประมาณ', bg='#d5e1df').grid(row=0, column=3) #fiscal year part
plan_fiscalY_choice = IntVar()
plan_fiscalY_combo = ttk.Combobox(Tab_frame_plan, textvariable=plan_fiscalY_choice, width= 10)
plan_fiscalY_combo['values']=(fiscal_year_list)
plan_fiscalY_combo.grid(row=0, column=4, sticky=tk.W)

Label_plan_StartD = Label(Tab_frame_plan, text='วันเริ่มแผน', font=5, bg='#d5e1df').grid(row=2, column=0, sticky=tk.W, padx= 10) #Start date
plan_StartD_cal = DateEntry(Tab_frame_plan, selectmode='day', width= 8, font=5)
plan_StartD_cal.grid(row=2, column=1, sticky=tk.W)

Label_plan_StopD = Label(Tab_frame_plan, text='วันสิ้นสุดแผน', font=5, bg='#d5e1df').grid(row=2, column=3, sticky=tk.W, padx= 10) #Stop date
StopD = StringVar()
plan_StopD_cal = DateEntry(Tab_frame_plan, textvariable=StopD, selectmode='day', width= 8, font=5)
plan_StopD_cal.grid(row=2, column=4, sticky=tk.W)

Label_plan_Norad = Label(Tab_frame_plan, text='NORAD ID', font=5, bg='#d5e1df').grid(row=3, column=0, sticky=tk.W, padx= 10) #Norad
plan_Norad_txt = StringVar()
plan_Norad = Entry(Tab_frame_plan, textvariable=plan_Norad_txt,width= 15, font=5)
plan_Norad.grid(row=3, column=1, sticky=tk.W)

plan_btnCheck = Button(Tab_frame_plan, text='ตรวจสอบข้อมูลดาวเทียม',font=24, bg='#0000cc', fg="white" , command=call_NORAD_data_plan).grid(row=3, column=3, columnspan=2)#NORAD check

Label_plan_Name = Label(Tab_frame_plan, text='ชื่อดาวเทียม', font=5, bg='#d5e1df').grid(row=4, column=0, sticky=tk.W, padx= 10) #Name
plan_Name = tk.Text(Tab_frame_plan,bg = 'white', width= 15, height = 1, font=1)
plan_Name.grid(row=4, column=1, sticky=tk.W)

Label_plan_orbit = Label(Tab_frame_plan, text='Orbit type', font=5, bg='#d5e1df').grid(row=4, column=3, sticky=tk.W, padx= 10) #Orbit type
plan_orbit = tk.Text(Tab_frame_plan,bg = 'white', width= 10, height = 1, font=1)
plan_orbit.grid(row=4, column=4, sticky=tk.W)

Label_plan_Country = Label(Tab_frame_plan, text='ประเทศ', font=5, bg='#d5e1df').grid(row=5, column=0, sticky=tk.W, padx= 10) #Country
plan_Country = tk.Text(Tab_frame_plan,bg = 'white', width= 15, height = 1, font=1)
plan_Country.grid(row=5, column=1, sticky=tk.W)

Label_plan_SCat = Label(Tab_frame_plan, text='ประเภทดาวเทียม', font=5, bg='#d5e1df').grid(row=5, column=3, sticky=tk.W, padx= 10) #Sat CAT
plan_SCat_choice = StringVar()
plan_SCat_combo = ttk.Combobox(Tab_frame_plan, textvariable=plan_SCat_choice, width= 8, font=5)
plan_SCat_combo['values']=(SCat_list)
plan_SCat_combo.grid(row=5,column=4, sticky=tk.W)

Label_plan_show = Label(Tab_frame_plan, text='ข้อมูลที่บันทึกแล้ว', font=5, bg='#d5e1df').grid(row=6, column=0, sticky=tk.W, padx= 10) #Show
plan_show = tk.Text(Tab_frame_plan,bg = 'white', width= 50, height = 5, font=1)
plan_show.grid(row=7, columnspan=5)

plan_btnClear = Button(Tab_frame_plan, text='ล้างข้อมูลทั้งหมด',font=30, bg='#c94c4c', fg="white" , command= DelText_plan).grid(row=8, column=3,sticky=tk.W)#Clear text button
plan_btnAdd = Button(Tab_frame_plan, text='เพิ่มข้อมูล',font=30,width=10, bg='#405d27', fg="white", command=check_plan).grid(row=8, column=4,sticky=tk.W)#check then Add data
#-----------------------------------------------------------------------------------------------------------------------

##Tab_frame_pic
#pic connection statement
insert_statement_pic = """
    INSERT INTO Tracking
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
read_statement_pic = '''SELECT * FROM [dbo].[Tracking]'''
#fuction
def DelText_pic():
    pic_fiscalY_choice.set('')
    pic_Date_cal.delete(0,END)
    pic_site_choice.set('')
    pic_shift_choice.set('')
    pic_Norad.delete(0, END)
    pic_Name.delete(1,END)
    pic_Country.delete(1,END)
    pic_orbit.delete(1,END)
    pic_SCat_choice.set('')

def AddData_pic(pic_fiscalY, pic_Date, pic_site, pic_shift, pic_norad, pic_name, pic_SCat, pic_Country, pic_orbit,insert_statement_plan, read_statement_plan,insert_statement_pic, read_statement_pic):
    check_pic_new_inplan = norad_uniq_check(pic_norad, pic_fiscalY, read_statement_plan)
    if check_pic_new_inplan == 1:
        pic_input_2plan = [pic_norad, pic_fiscalY, pic_Date, pic_SCat, pic_name, pic_orbit, pic_Country, 1]
        sql_insert(insert_statement_plan, pic_input_2plan)
    else:
        check_pic_month_inplan = norad_month_check(pic_norad, pic_fiscalY, pic_Date, read_statement_plan)
        if check_pic_month_inplan == 1:
            pic_input_2plan_m = [pic_norad, pic_fiscalY, pic_Date, pic_SCat, pic_name, pic_orbit, pic_Country, 0]
            sql_insert(insert_statement_plan, pic_input_2plan_m)

    check_pic_new = norad_uniq_check(pic_norad, pic_fiscalY, read_statement_pic)
    pic_input = [pic_norad, pic_fiscalY,  pic_Date, pic_site, pic_shift, pic_name, pic_SCat, pic_orbit, pic_Country,check_pic_new]
    sql_insert(insert_statement_pic, pic_input)

def check_pic():
    pic_fiscalY = pic_fiscalY_choice.get()
    pic_Date = str(pic_Date_cal.get_date())
    pic_site = pic_site_choice.get()
    pic_shift = pic_shift_choice.get()
    pic_norad = pic_Norad_txt.get()
    pic_name_value = pic_Name.get(1.0, 'end-1c')
    pic_Country_value = pic_Country.get(1.0, 'end-1c')
    pic_orbit_value = pic_orbit.get(1.0, 'end-1c')
    pic_SCat = pic_SCat_choice.get()
    confirm = tkinter.messagebox.askquestion('ยืนยันความถูกต้อง',' ปีงบประมาณ:  '+ str(pic_fiscalY)
                                             +'\n วันที่ถ่ายภาพได้:  '+ str(pic_Date)
                                             +'\n หอดูดาว:  ' + str(pic_site)
                                             +'\n ผลัดราชการที่:  ' + str(pic_shift)
                                             +'\n Norad ID:  ' + str(pic_norad)
                                             +'\n ชื่อดาวเทียม:  ' + pic_name_value
                                             +'\n ประเภทดาวเทียม:  ' + str(pic_SCat)
                                             +'\n Orbit type:  ' + str(pic_orbit_value)
                                             +'\n ประเทศ:  ' + str(pic_Country_value))
    if confirm == 'yes':
        show_df = get_inputed(inputed_df, pic_norad, pic_name_value, pic_orbit_value, pic_SCat)
        pic_show.insert(tk.END, show_df)
        pic_show.insert(tk.END, '\n')
        AddData_pic(pic_fiscalY, pic_Date, pic_site, pic_shift, pic_norad, pic_name_value, pic_SCat, pic_Country_value, pic_orbit_value,insert_statement_plan, read_statement_plan, insert_statement_pic, read_statement_pic)
        pic_Norad.delete(0, END)
        pic_Name.delete(1.0, END)
        pic_orbit.delete(1.0, END)
        pic_Country.delete(1.0, END)
        pic_SCat_choice.set('')
        tkinter.messagebox.showinfo("บันทึกข้อมูล", "บันทึกข้อมูล ผลการถ่ายภาพดาวเทียม\nเรียบร้อยแล้ว")

def call_NORAD_data_pic():
    pic_Name.delete(1.0, END)
    pic_orbit.delete(1.0, END)
    pic_Country.delete(1.0, END)
    norad = int(pic_Norad_txt.get())
    satdata_pic = sqlTB_SatData.where(sqlTB_SatData['NORAD'] == norad).dropna()
    satname_pic = (satdata_pic['SatelliteName'].values)[0]
    satorbit_pic = (satdata_pic['Orbit'].values)[0]
    satcountry_pic = (satdata_pic['Country'].values)[0]
    pic_Name.insert(tk.END,satname_pic)
    pic_orbit.insert(tk.END, satorbit_pic)
    pic_Country.insert(tk.END, satcountry_pic)

# grid config
Tab_frame_pic.columnconfigure(0, weight=1)
Tab_frame_pic.columnconfigure(1, weight=1)
Tab_frame_pic.columnconfigure(2, weight=1)
Tab_frame_pic.columnconfigure(3, weight=1)
Tab_frame_pic.columnconfigure(4, weight=1)
Tab_frame_pic.rowconfigure(0, weight=1)
Tab_frame_pic.rowconfigure(1, weight=1)
Tab_frame_pic.rowconfigure(2, weight=1)
Tab_frame_pic.rowconfigure(3, weight=1)
Tab_frame_pic.rowconfigure(4, weight=1)
Tab_frame_pic.rowconfigure(5, weight=1)
Tab_frame_pic.rowconfigure(6, weight=1)
Tab_frame_pic.rowconfigure(7, weight=1)
Tab_frame_pic.rowconfigure(8, weight=2)

#interface
Label_pic_header = Label(Tab_frame_pic, text='ผลการถ่ายภาพดาวเทียม', font=10, bg='#ffeead').grid(row=0, column=0,columnspan =3)

Label_pic_fiscalY = Label(Tab_frame_pic, text='ปีงบประมาณ', bg='#ffeead').grid(row=0, column=3) #fiscal year part
pic_fiscalY_choice = IntVar()
pic_fiscalY_combo = ttk.Combobox(Tab_frame_pic, textvariable=pic_fiscalY_choice, width= 10)
pic_fiscalY_combo['values']=(fiscal_year_list)
pic_fiscalY_combo.grid(row=0, column=4, sticky=tk.W)

Label_pic_Date = Label(Tab_frame_pic, text='วันถ่ายภาพ', font=5, bg='#ffeead').grid(row=1, column=0, sticky=tk.W, padx= 10) #Picture date
pic_Date_cal = DateEntry(Tab_frame_pic, selectmode='day', width= 8, font=5)
pic_Date_cal.grid(row=1, column=1, sticky=tk.W)

Label_pic_site = Label(Tab_frame_pic, text='หอดูดาว', font=5, bg='#ffeead').grid(row=1, column=3, sticky=tk.W, padx= 10) #Site
pic_site_choice = StringVar()
pic_site_combo = ttk.Combobox(Tab_frame_pic, textvariable=pic_site_choice, width= 8, font=5)
pic_site_combo['values']=(site_list)
pic_site_combo.grid(row=1, column=4, sticky=tk.W)

Label_pic_shift = Label(Tab_frame_pic, text='ผลัดที่', font=5, bg='#ffeead').grid(row=2, column=0, sticky=tk.W, padx= 10) #Shift
pic_shift_choice = IntVar()
pic_shift_combo = ttk.Combobox(Tab_frame_pic, textvariable=pic_shift_choice,width= 8, font=5)
pic_shift_combo['values']=(shift_list)
pic_shift_combo.grid(row=2, column=1, sticky=tk.W)

Label_pic_Norad = Label(Tab_frame_pic, text='NORAD ID', font=5, bg='#ffeead').grid(row=3, column=0, sticky=tk.W, padx= 10) #Norad
pic_Norad_txt = StringVar()
pic_Norad = Entry(Tab_frame_pic, textvariable=pic_Norad_txt,width= 15, font=5)
pic_Norad.grid(row=3, column=1, sticky=tk.W)

pic_btnCheck = Button(Tab_frame_pic, text='ตรวจสอบข้อมูลดาวเทียม',font=24, bg='#0000cc', fg="white" , command=call_NORAD_data_pic).grid(row=3, column=3, columnspan=2)#NORAD check

Label_pic_Name = Label(Tab_frame_pic, text='ชื่อดาวเทียม', font=5, bg='#ffeead').grid(row=4, column=0, sticky=tk.W, padx= 10) #Name
pic_Name = tk.Text(Tab_frame_pic,bg = 'white', width= 15, height = 1, font=1)
pic_Name.grid(row=4, column=1, sticky=tk.W)

Label_pic_orbit = Label(Tab_frame_pic, text='Orbit type', font=5, bg='#ffeead').grid(row=4, column=3, sticky=tk.W, padx= 10) #Orbit type
pic_orbit = tk.Text(Tab_frame_pic,bg = 'white', width= 10, height = 1, font=1)
pic_orbit.grid(row=4, column=4, sticky=tk.W)

Label_pic_Country = Label(Tab_frame_pic, text='ประเทศ', font=5, bg='#ffeead').grid(row=5, column=0, sticky=tk.W, padx= 10) #Country
pic_Country = tk.Text(Tab_frame_pic,bg = 'white', width= 15, height = 1, font=1)
pic_Country.grid(row=5, column=1, sticky=tk.W)

Label_pic_SCat = Label(Tab_frame_pic, text='ประเภทดาวเทียม', font=5, bg='#ffeead').grid(row=5, column=3, sticky=tk.W, padx= 10) #Sat CAT
pic_SCat_choice = StringVar()
pic_SCat_combo = ttk.Combobox(Tab_frame_pic, textvariable=pic_SCat_choice, width= 8, font=5)
pic_SCat_combo['values'] = (SCat_list)
pic_SCat_combo.grid(row=5,column=4, sticky=tk.W)

Label_pic_show = Label(Tab_frame_pic, text='ข้อมูลที่บันทึกแล้ว', font=5, bg='#ffeead').grid(row=6, column=0, sticky=tk.W, padx= 10) #Country
pic_show = tk.Text(Tab_frame_pic,bg = 'white', width= 50, height = 5, font=1)
pic_show.grid(row=7, columnspan=5)

pic_btnClear = Button(Tab_frame_pic, text='ล้างข้อมูลทั้งหมด',font=30, bg='#c94c4c', fg="white" , command= DelText_pic).grid(row=8, column=3,sticky=tk.W)#Clear text button
pic_btnAdd = Button(Tab_frame_pic, text='เพิ่มข้อมูล',font=30,width=10, bg='#405d27', fg="white", command=check_pic).grid(row=8, column=4,sticky=tk.W)#check then Add data
#-----------------------------------------------------------------------------------------------------------------------

root.mainloop()