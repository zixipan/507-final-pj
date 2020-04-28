# -*- coding: utf-8 -*-  
from weibo import APIClient 
import requests
import json
import urllib.request 
import urllib.parse
from lxml import etree
import io
import sys
from bs4 import BeautifulSoup
import re
import csv
import pandas as pd
import time
import sqlite3
import os
from flask import Flask, request,render_template,redirect,jsonify,session,make_response,Response
import plotly.graph_objs as go
import plotly
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import jieba  
from datetime import timedelta
import secrets
app = Flask(__name__)
app.secret_key = '1415926535abcdefg'
#app.config['SEND_FILE_MAX_AGE_DEFAULT']=timedelta(seconds=5)

CACHE_COMMENT_FILENAME = os.path.join(app.root_path, 'db', 'weibo_comment_cache.json')
CACHE_COMMENT_DICT = {}
CACHE_ELEMENT_FILENAME = os.path.join(app.root_path, 'db', "weibo_element_cache.json")
CACHE_ELEMENT_DICT = {}
CACHE_NUM_FILENAME = os.path.join(app.root_path, 'db', "weibo_num_cache.json")
CACHE_NUM_DICT = {}
csv_file_content=os.path.join(app.root_path, 'db', 'weibo_content_csv.csv')
csv_file_comment=os.path.join(app.root_path, 'db', 'weibo_comment_csv.csv')
db_file_content=os.path.join(app.root_path, 'db', 'weibo_content_csv.db')
db_file_comment=os.path.join(app.root_path, 'db', 'weibo_comment_csv.db')
font_path=os.path.join(app.root_path, 'static', 'simhei.ttf')
wc_path=os.path.join(app.root_path, 'static', 'images','word_cloud.png')
APP_KEY = secrets.APP_KEY
APP_SECRET = secrets.APP_SECRET
CALLBACK_URL = 'http://127.0.0.1:5000/oauth2/login/callback'  
client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL) 

def transqlit(dbfile,csvfile,tablename):
    conn= sqlite3.connect(dbfile)
    cursor = conn.cursor()
    df = pd.read_csv(csvfile)
    name=df.columns.values
    try:
        cursor.execute('create table '+tablename+' ('+name[0]+' varchar(65535),'+name[1]+' varchar(65535),'+name[2]+' varchar(65535),'+name[3]+' varchar(65535),'+name[4]+' varchar(65535))')
    except:
        print('insert to old db')
    df.to_sql(tablename, conn, if_exists='append', index=False)
    #关闭Cursor:
    cursor.close()
    conn.commit()
    conn.close()
    return 

def GetNowTime():
    return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))

def open_csv(filepath):
    try:
        tmp_lst = []
        csv_file = open(filepath, 'r',encoding='utf-8')
        reader = csv.reader(csv_file)
        for row in reader:
            tmp_lst.append(row)
        csv_dict = pd.DataFrame(tmp_lst[1:], columns=tmp_lst[0]) 
        csv_file.close()
    except:
        csv_dict = pd.DataFrame()
    return csv_dict

def save_csv(filepath,variable):
    variable.to_csv(filepath,sep=',',index=False,header=True,encoding='utf-8')
    return

def transcsv(jsonpath, csvpath):
    json_file = open(jsonpath, 'r', encoding='utf8')
    csv_file = open(csvpath, 'w', newline='',encoding='utf8')
    
    ls = json.load(json_file)  
    ids=[]
    comments=[]
    reposts=[]
    for item in ls.values():
        ids.append(item[0]["id"]) 
        comments.append(item[0]["comments"])  
        reposts.append(item[0]["reposts"])

    writer=csv.writer(csv_file)
    writer.writerow(['ID','评论数','转发数'])
    for i in range(len(ls)):
        writer.writerow([ids[i],comments[i],reposts[i]]) 
   
    json_file.close()
    csv_file.close()

def open_cache(cache_name):
    ''' opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.

    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache
    '''
    try:
        cache_file = open(cache_name, 'r',encoding='utf-8')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

CACHE_COMMENT_DICT = open_cache(CACHE_COMMENT_FILENAME)
CACHE_ELEMENT_DICT = open_cache(CACHE_ELEMENT_FILENAME)
CACHE_NUM_DICT = open_cache(CACHE_NUM_FILENAME)
df_content=open_csv(csv_file_content)
df_comment=open_csv(csv_file_comment)

def save_cache(cache_dict,cache_name):
    ''' saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict,ensure_ascii=False)
    fw = open(cache_name,"w",encoding='utf-8')
    fw.write(dumped_json_cache)
    fw.close() 

def weibo():
    url = 'https://s.weibo.com/top/summary?cate=realtimehot'
    a = urllib.request.urlopen(url)  
    html = a.read()  
    html = html.decode("utf-8")  
    tree = etree.HTML(html)
    list = tree.xpath(u'//*[@id="pl_top_realtimehot"]/table/tbody/tr/td[@class="td-02"]')
    prefix = 'https://s.weibo.com' 
    topic_list=[]
    hot_list=[]
    title_list=[]
    for index,item in enumerate(list):
        if index > 0:
            dict = {}
            a_element = item.xpath('.//a')[0]
            title = a_element.text 
            href = urllib.parse.unquote(a_element.attrib.get('href')) 
            href = href.replace("#", "%23") 
            hot = item.xpath('./span')[0].text
            dict['title']=title
            dict['hot']=hot
            dict['link']=prefix+href
            line = str(index) + "\t" + title + "\t" + hot + "\n"
            if href.find("javascript:void(0)") != -1:
                line = str(index) + "\t" + title + "\t" + hot
                dict['ad']=1
            else:
                dict['ad']=0
            dict['line']=line
            topic_list.append(dict)
            hot_list.append(hot)
            title_list.append(title)
    return topic_list,hot_list,title_list
        
def element_clean(text):
    mod1 = re.compile(r'#.*#')
    mod2 = re.compile(r'\n')
    mod3 = re.compile(r'\s')
    result = mod1.sub('', text)
    result = mod2.sub('',result)
    result = mod3.sub('',result)
    return result

def element_get(url):
    r= requests.get(url)
    r.encoding='utf-8'
    text=r.text
    soup = BeautifulSoup(text, 'lxml')
    data_text=[]
    data_mid=[]
    data_line=[]
    count=0
    for mid in soup.find_all(name="div",attrs={"class": "card-wrap","action-type":"feed_list_item"}):
        request_key=mid.attrs["mid"]
        if request_key in CACHE_ELEMENT_DICT.keys():
            print("element cache hit!", request_key)
        else:
            print("element cache miss!", request_key)
            text=mid.find(name="p",attrs={"class": "txt","node-type":"feed_list_content"}).get_text()
            text=element_clean(text)
            CACHE_ELEMENT_DICT[request_key] = json.dumps(text,ensure_ascii=False)
            save_cache(CACHE_ELEMENT_DICT,CACHE_ELEMENT_FILENAME)
        content=CACHE_ELEMENT_DICT[request_key]
        count=count+1
        line=str(count)+' '+content+' '+mid.attrs["mid"]
        data_text.append(content)
        data_mid.append(mid.attrs["mid"])
        data_line.append(line)


    return data_mid,data_text,data_line

def num_get_cache(request_key):
    num = client.statuses__count(ids=request_key)
    CACHE_NUM_DICT[request_key] = num
    save_cache(CACHE_NUM_DICT,CACHE_NUM_FILENAME)
    return CACHE_NUM_DICT[request_key]

def comment_get_cache(request_key):
    if request_key in CACHE_COMMENT_DICT.keys():
        print("comment cache hit!", request_key)
        return CACHE_COMMENT_DICT[request_key]
    else:
        print("comment cache miss!", request_key)
        statuses = client.comments__show(id=request_key)
        num = client.statuses__count(ids=request_key)
        CACHE_COMMENT_DICT[request_key] = statuses
        save_cache(CACHE_COMMENT_DICT,CACHE_COMMENT_FILENAME)
        return CACHE_COMMENT_DICT[request_key]

def comment_reconstruction(statuses,num):
    count_comment=0
    df_line=[]
    global df_comment
    for comment in statuses["comments"]:
        count_comment=count_comment+1
        tmp={'id':comment["mid"],'user':comment['user']['name'],'comments':comment['text'],'comments_num':num[0]['comments'],'reposts':num[0]['reposts']}
        df_comment=df_comment.append(tmp,ignore_index=True)
        line=str(count_comment)+' '+comment["mid"]+' '+comment['user']['name']+' '+comment['text']
        print(line)
        df_line.append(line)
    save_csv(csv_file_comment,df_comment)
    transqlit(db_file_comment,csv_file_comment,'comment')
    return df_line

@app.route('/',methods=['GET','POST'])
def main_search():
    if request.method == 'POST':
        if request.form['submit_button'] == 'topic_button':
            topic_list,hot_list,title_list=weibo()
            session['topic_list']=topic_list
            return  render_template("topic_result.html",topic=topic_list)

        elif request.form['submit_button'] == 'content_button':
            topic_list=session['topic_list']
            topic_submit_value=int(request.form.get('topic_submit'))
            data_mid,data_text,data_line=element_get(topic_list[topic_submit_value-1]['link'])
            session['data_mid']=data_mid
            global df_content
            count_element=0
            for i in range(len(data_text)):
                count_element=count_element+1
                now_time=GetNowTime()
                tmp={'id':data_mid[i],'topic':topic_list[topic_submit_value]['title'],'content':data_text[i],'url':topic_list[topic_submit_value]['link'],'time':now_time}
                df_content=df_content.append(tmp,ignore_index=True)
            #session['data_text']=data_text
            save_csv(csv_file_content,df_content)
            transqlit(db_file_content,csv_file_content,'content')
            return  render_template("content_result.html",content=data_line)

        elif request.form['submit_button'] == 'comment_button':
            data_mid=session['data_mid']
            content_submit_value=int(request.form.get('content_submit'))
            num=num_get_cache(data_mid[content_submit_value])
            statuses=comment_get_cache(data_mid[content_submit_value])
            df_line=comment_reconstruction(statuses,num)
            return  render_template("comment_result.html",comment=df_line) 

        elif request.form['submit_button'] == 'login':
            oauth_url=client.get_authorize_url()
            return redirect(oauth_url,302)

        elif request.form['submit_button'] == 'draw_button':
            select = request.form.get('select')
            if(select=='Hot Bar'):
                topic_list=session['topic_list']
                title_list=[]
                hot_list=[]
                for topic in topic_list:
                    title_list.append(topic['title'])
                    hot_list.append(topic['hot'])
                bar_data=go.Bar(x=title_list,y=hot_list)
                bl=go.Layout(title='Hot Bar',xaxis=dict(tickangle=75))
                fig=go.Figure(data=bar_data,layout=bl)
                fig.show()
                return render_template("main.html") 
            
            if(select=='Word Cloud'):
                tmp_lst = []
                csv_file = open(csv_file_content, 'r',encoding='utf-8')
                reader = csv.reader(csv_file)
                word=''
                for row in reader:
                    content=row[0]
                    content_ch = re.sub("[A-Za-z0-9\!\%\[\]\,\。]", "", content)
                    word=word+content_ch
                word = re.sub("[A-Za-z0-9\!\%\[\]\,\。]", "", word)       
                cut_text = jieba.cut(word)   
                csv_file.close()
                ww=['展开','全文','不能','还是',]
                clean_text=''
                for word in cut_text:
                    if word not in ww:
                        clean_text += word
                        clean_text += ' '
                    else:
                        clean_text += ''
                wc = WordCloud(collocations=False, font_path=font_path,width=1400, height=1400, margin=2).generate(clean_text)
                try:
                    os.remove(wc_path)
                except:
                    pass
                wc.to_file(wc_path)
                image_data = open(wc_path, "rb").read()        
                response = make_response(image_data)        
                response.headers['Content-Type'] = 'image/png'
                return response
                #return render_template("main.html") 

            if(select=='Hot Line'):
                hot_line=[]
                time_line=[]
                topic_list=session['topic_list']
                title_list=[]
                for topic in topic_list:
                    title_list.append(topic['title'])
                line_submit_value=int(request.form.get('topic_follow'))
                follow_time=int(request.form.get('follow_time'))
                target=title_list[line_submit_value-1]
                for i in range(12*follow_time):
                    topic_list,hot_list,title_list=weibo()
                    flag=0
                    for topic in topic_list:
                        if(topic['title']==target):
                            hot_line.append(topic['hot'])
                            now_time=GetNowTime()
                            time_line.append(now_time)
                            flag=1
                            break
                    if(flag==0):
                        hot_line.append(0)
                        now_time=GetNowTime()
                        time_line.append(now_time)
                    print(i)
                    time.sleep(5)
                print(hot_line)
                line_data=go.Scatter(x=time_line,y=hot_line,mode = 'lines',connectgaps = True,line = dict(color = ('rgb(205, 12, 24)'),width = 4,dash = 'dash'))
                bl=go.Layout(title='Hot Line for '+target,xaxis=dict(tickangle=75))
                fig=go.Figure(data=line_data,layout=bl)
                fig.show()
                return render_template("main.html") 

        else:
            return 'Error!Main!'
    
    elif request.method == 'GET':
        if 'user' in session:
            uid=session['user']
        else:
            uid='New User'
        return  render_template("main.html",uid=uid)

@app.route('/oauth2/login/callback')
def oauth2_callback():
    code = request.args.get('code')
    req = client.request_access_token(code)
    access_token = req.access_token
    expires_in = req.expires_in
    uid=req.uid
    client.set_access_token(access_token, expires_in)
    session['user']=uid
    return  redirect('/',302)

if __name__ == '__main__':
    #app.debug = True
    app.run()