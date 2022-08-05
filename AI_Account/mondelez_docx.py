#----------------------- Sansbury_pdf------------------------------------------------#
#Packages used
import pandas as pd
import numpy as np
from langid import classify
import re 
import string
import joblib
import mammoth
from bs4 import BeautifulSoup
from docx import Document
#------------------------------------------------------------------------------------------------
# Laser Embedding

from laserembeddings import Laser
path_to_bpe_codes = r'/Users/manirathinams/opt/anaconda3/lib/python3.9/site-packages/laserembeddings/data/93langs.fcodes'
path_to_bpe_vocab = r'/Users/manirathinams/opt/anaconda3/lib/python3.9/site-packages/laserembeddings/data/93langs.fvocab'
path_to_encoder = r'/Users/manirathinams/opt/anaconda3/lib/python3.9/site-packages/laserembeddings/data/bilstm.93langs.2018-12-26.pt'
laser = Laser(path_to_bpe_codes, path_to_bpe_vocab, path_to_encoder) 
#------------------------------------------------------------------------------------------------
# Loading MLP Classifier for classification keys

classifier=joblib.load('/Users/manirathinams/Documents/Python /Mondelez Docx/Mondelez.sav')
#------------------------------------------------------------------------------------------------
##Extracting all tables in word using beautifulsoup into indidual table

def table_extraction(file_path):
    result = mammoth.convert_to_html(file_path)
    html_file=result.value
    soup=BeautifulSoup(html_file, 'html.parser')
    all_tables=[]
    for tables in soup.find_all('table'):
        rows=[]
        for row in tables.find_all('tr'):
            cols=[]
            for cell in row.find_all('td'):
                if cell.text:
                    temp=str(cell).replace('<strong>','start_bold').replace('</strong>','end_bold').replace("<br>",'\n').replace("<br/>",'\n') 
                    cols.append((BeautifulSoup(temp, 'html.parser').text).replace('start_bold', '&lt;b&gt;').replace('end_bold','&lt;/b&gt;').replace('\xa0', '').strip())
            if len(cols) > 0:
                    rows.append(cols)
        if len(rows)>0:
            all_tables.append(rows)
    return all_tables
#------------------------------------------------------------------------------------------------
##Extracting General Information contents

def general_information(all_tables):
    temp_key=[]
    val=[]
    cntnt_ky=[]
    cntnt_vl=[]
    for table in all_tables:
        temp=''
        ##if len(element in a row)=2 1st element is key, else len(element in row)=1,take a key from prev row using pass
        for ind,row in enumerate(table):
            if len(row)==2:
                temp=row[0]
                #print('\n',row)
                temp_key.append(temp.replace('&lt;b&gt;','').replace('&lt;/b&gt;','').replace(':','').strip())
                val.append({classify(row[1])[0]:(row[1]).strip()})
                pass
            ##if prev row in table had 2 Elemnt, nxt row having 1 element with same key as a prev row 1st elemnt, get that key using pass from prev loop
            elif len(row)==1:
                if temp:
                    #print('\n',temp,row[0])
                    temp_key.append(temp.replace('&lt;b&gt;','').replace('&lt;/b&gt;','').replace(':','').strip())
                    val.append({classify(row[0])[0]:row[0].strip()})
                    pass
                ##if len(elemnt in a row)=1, did a content classification after removing bold tags to get a key like Ingredient_declaration
                else:
                    #print('\n',row[0].replace('\n','').strip())
                    text=(row[0].replace('\n','').replace('&lt;b&gt;','').replace('&lt;/b&gt;','').strip())
                    proba=classifier.predict_proba(laser.embed_sentences(text, lang='en'))[0]
                    proba.sort()
                    #print('\n',row,proba[-1],str((classifier.predict(laser.embed_sentences(text, lang='en')))[0]),len(row[0]))
                    if proba[-1]>0.75 and len(row[0])>325:
                        cntnt_ky.append(str((classifier.predict(laser.embed_sentences(text, lang='en')))[0]))
                        cntnt_vl.append({classify(row[0])[0]:row[0].strip()})
                    else:
                        cntnt_ky.append('UNMAPPED')
                        cntnt_vl.append(row[0].strip())
                    pass
    
    ##Tagging keys with GS1 elements, Nutri_key list is created to reject such a key's present in general_inform part while extracting 
    Nutri_key=['Energy','Calories','Protein','Carbohydrate','Sugar','Total Fat','Saturated Fat','Fibre','Sodium','Total Fat','Saturated Fat','Trans Fat','Cholesterol','Carbohydrate','Dietary Fibre','Sugar','Includes Added Sugars','Salt']
    key=[]
    for x in temp_key:
        key_prob=classifier.predict_proba(laser.embed_sentences(x, lang='en'))[0]
        gs1_key=str((classifier.predict(laser.embed_sentences(x, lang='en')))[0])
        key_prob.sort()
        #print('\n',x,key_prob[-1])
        if key_prob[-1]>0.75 and gs1_key not in Nutri_key:
            key.append(gs1_key)
        else:
            key.append('UNMAPPED')  
    
    ## concatinating key-value pair 
    ky=key+cntnt_ky
    vl=val+cntnt_vl
    
    ##create a dictionary key-value pair       
    gen_infor={}
    for i in range(len(ky)):
    ##setdefault will allow duplicate keys in dictionary
        gen_infor.setdefault(ky[i], []).append(vl[i])
    return gen_infor
#------------------------------------------------------------------------------------------------------------------------
#Extracting Nutri-content from normal nutrition table

def nutri_tables(all_tables):
    kys=[]
    vle=[]
    for table in all_tables:
        for ind,row in enumerate(table):
            cell=[]
            for j in range(1, len(row)):
                ##if kcal present in a row, then key should be calories.this case for when that particular key cell is empty
                if 'kcal' in row[1]:
                    row[0]='Calories'
                    if '%' in row[j] and row[j].strip()!='':
                        cell.append({'PDV':{classify(row[j])[0]:row[j].replace('&lt;b&gt;','').replace('&lt;/b&gt;','').strip()}})
                    elif row[j].strip()!='':
                        cell.append({'Value':{classify(row[j])[0]:row[j].replace('&lt;b&gt;','').replace('&lt;/b&gt;','').strip()}})
                else:
                    if '%' in row[j] and row[j].strip()!='':
                        cell.append({'PDV':{classify(row[j])[0]:row[j].replace('&lt;b&gt;','').replace('&lt;/b&gt;','').strip()}})
                    elif row[j].strip()!='':
                        cell.append({'Value':{classify(row[j])[0]:row[j].replace('&lt;b&gt;','').replace('&lt;/b&gt;','').strip()}})
            vle.append(cell)
            kys.append(row[0].replace('&lt;/b&gt;','').replace('&lt;b&gt;','').replace('>','').strip())

    ##Tagging keys with GS1 Element
    Nutri_key=['Energy','Calories','Protein','Carbohydrate','Sugar','Total Fat','Saturated Fat','Fibre','Sodium','Total Fat','Saturated Fat','Trans Fat','Cholesterol','Carbohydrate','Dietary Fibre','Sugar','Includes Added Sugars','Salt']
    key=[]
    val=[]
    for s in range(len(kys)):
        proba=classifier.predict_proba(laser.embed_sentences(kys[s], lang='en'))[0]
        proba.sort()
        predict=classifier.predict(laser.embed_sentences(kys[s], lang='en'))[0]
        classified_output=predict
        if proba[-1]>0.75 and classified_output in Nutri_key:
            key.append(classified_output)
            val.append(vle[s])

    nut={}
    for k in range(len(key)):
        nut.setdefault(key[k], []).extend(val[k])
    return nut   
#----------------------------------------------------------------------------------------------
#Extracting Nutrition content from arabic nutrition table

def arabic_nutrition(all_tables):    
    #Getting all tables rows in a list‘
    tab_rows=[]
    for tables in all_tables:
        for r in tables:
            tab_rows.append(r)
    #slicing        
    strt_ind=0
    end_ind=0
    for i in range(len(tab_rows)):
        if 'nutrition facts' in tab_rows[i][0].lower():
            strt_ind=i+1
        elif '% daily value' in tab_rows[i][0].lower():
            end_ind=i

    new_list=[tab_rows[j] for j in range(strt_ind, end_ind)]
    ##removing unwanted tags like <b>
    temp_list=[]
    for i in new_list:
        temp_list.append(('').join(i).replace('<b>','').replace('</b>','').replace('&lt;b&gt;','').replace('&lt;/b&gt;',''))

    #removing arabic & unwanted contents using "re.sub"
    regex_list=[]
    for j in temp_list:
        #reg=('').join(re.findall(r'[<.a-zA-Z0-9-(%)]', str(j)))
        reg=re.sub(r'[^\.a-zA-z-(%)\d\/\s]','',str(j))
        regex_list.append(reg)

    ##Removing unwanted strings like '\n','\xa0' and split strings based on delimiter '/'
    string=[]
    for i in regex_list:
        re_=re.split(r'/',str(i).strip().replace('\n','').replace('\xa0','').replace('lt','').replace('bgt',''))
        string.append(re_)
    ##Convert dataframe to get Nutrition key-value pair and 'UNMAPPED' values to nutri_serv dictionary
    df=pd.DataFrame(string)
    nutri_serv={}
    key=[]
    value=[]
    for i in range(0, len(df)):
        cell=[]
        for j in range(1, len(df.columns)):
            x=df.iloc[i,0].strip()
            proba=classifier.predict_proba(laser.embed_sentences(x, lang='en'))[0]
            proba.sort()
            predict=classifier.predict(laser.embed_sentences(x, lang='en'))[0]
            classified_output=predict
            if proba[-1]>0.75:
                key.append(classified_output)
                if '%' in str(df.iloc[i,j]) and df.iloc[i,j]!='' and df.iloc[i,j]!=None:
                    cell.append({'PDV':{classify(str(df.iloc[i,j]))[0]:df.iloc[i,j].strip()}})
                elif df.iloc[i,j]!='' and df.iloc[i,j]!=None:
                    cell.append({'Value':{classify(str(df.iloc[i,j]))[0]:df.iloc[i,j].strip()}})
                value.append(cell)
            else:
                classified_output='UNMAPPED'
                txt=df.iloc[i,j]
                if txt!=None and txt!='':
                    if classified_output in nutri_serv:
                        nutri_serv[classified_output].append({classify(str(txt))[0]:str(txt).strip()})
                    else:
                        nutri_serv[classified_output]=[{classify(str(txt))[0]:str(txt).strip()}]
    nut={}            
    for k in range(len(key)):
        nut.setdefault(key[k],[]).extend(value[k])
    nutri_serv['NUTRITION_FATS']=nut            
    return nutri_serv
#----------------------------------------------------------------------------------------------
#Mondelez_docx account main function

def mondelez_main(file_path):
    all_tables=table_extraction(file_path)
    General=general_information(all_tables)
    if nutri_tables(all_tables):
        General['NUTRITION_FACTS']=[nutri_tables(all_tables)]
        final=General
    elif arabic_nutrition(all_tables):
        arab_nut=arabic_nutrition(all_tables)
        # convert multiple same keys in two dictionaries to default key-val pair 
        key,val=[],[]
        for dic in [General, arab_nut]:
            for k,v in dic.items():
                key.append(k)
                val.append(v)
        final={}
        for m in range(len(key)):
            final.setdefault(key[m],[]).append(val[m])
    return final 