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
import csv, sqlite3

CACHE_COMMENT_FILENAME = "weibo_comment_cache.json"
CACHE_COMMENT_DICT = {}
CACHE_ELEMENT_FILENAME = "weibo_element_cache.json"
CACHE_ELEMENT_DICT = {}
CACHE_NUM_FILENAME = "weibo_num_cache.json"
CACHE_NUM_DICT = {}
csv_file_content='weibo_content_csv.csv'
csv_file_comment='weibo_comment_csv.csv'
db_file_content='weibo_content_csv.db'
db_file_comment='weibo_comment_csv.db'


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
    writer.writerow(['ID','comments','reports'])
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
    weibotitle = [] 
    weibohot=[]
    weiboline=[]
    weiboad=[]
    for index,item in enumerate(list):
        if index > 0:
            a_element = item.xpath('.//a')[0]
            title = a_element.text 
            href = urllib.parse.unquote(a_element.attrib.get('href')) 
            href = href.replace("#", "%23") 
            hot = item.xpath('./span')[0].text
            weibotitle.append(title)
            weibohot.append(hot)
            weiboline.append(prefix+href)
            line = str(index) + "\t" + title + "\t" + hot + "\t" + prefix + href + "\n"
            if href.find("javascript:void(0)") != -1:
                line = str(index) + "\t" + title + "\t" + hot
                weiboad.append(1)
            else:
                weiboad.append(0)
            print(line.replace("\n", ""))

        else:
            title = '排名\t关键词\t热度\t链接\n'
            print(title.replace("\n",""))
    return weibotitle,weibohot,weiboline,weiboad
    
def oauth_client():

    APP_KEY = '2283160832'
    APP_SECRET = '5fd902c37292a72ada6dda0ad9a3f5cf'
    CALLBACK_URL = 'http://pzx.work.com'  

    client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL) 

    url = client.get_authorize_url()
    print(url) 

    code = input("Input code:")
    req = client.request_access_token(code)
    access_token = req.access_token
    expires_in = req.expires_in
    client.set_access_token(access_token, expires_in) 

    return client

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

        data_text.append(CACHE_ELEMENT_DICT[request_key])
        data_mid.append(mid.attrs["mid"])

    return data_mid,data_text

def comment_get_cache(request_key,client):
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

def num_get_cache(request_key,client):
    num = client.statuses__count(ids=request_key)
    CACHE_NUM_DICT[request_key] = num
    save_cache(CACHE_NUM_DICT,CACHE_NUM_FILENAME)
    return CACHE_NUM_DICT[request_key]

if __name__ == '__main__':
    CACHE_COMMENT_DICT = open_cache(CACHE_COMMENT_FILENAME)
    CACHE_ELEMENT_DICT = open_cache(CACHE_ELEMENT_FILENAME)
    CACHE_NUM_DICT = open_cache(CACHE_NUM_FILENAME)
    content_index='tmp'
    client_flag=0
    comments_index='begin'
    df_content=open_csv(csv_file_content)
    df_comment=open_csv(csv_file_comment)
    while(1):
        if(comments_index=='begin'):
            title,hot,line,ad=weibo()
            print('---------------------------------')
            topic_value=input('please input topic index (input exit to end):')
            if(topic_value=='exit'):
                break
            topic_value=int(topic_value)
            if(ad[topic_value-1]==1):
                print('Error! It\'s an advertisement!')
                continue
            if(topic_value>len(line)):
                print('Error! Over index!')
                continue
        data_mid,data_text=element_get(line[topic_value-1])
        topic_name=title[topic_value-1]
        topic_line=line[topic_value-1]
        now_time=GetNowTime()
        count_element=0
        for i in range(len(data_text)):
            count_element=count_element+1
            tmp={'id':data_mid[i],'topic':topic_name,'content':data_text[i],'url':topic_line,'time':now_time}
            df_content=df_content.append(tmp,ignore_index=True)
            print(str(count_element)+' '+data_text[i])
            print('---------------------------------')
        #print(df_content)
        content_index=input('please input content index (input back to return):')  
        if(content_index=='back'):
            comments_index='begin'
            continue
        content_value=int(content_index)
        if(client_flag==0):
            client=oauth_client()
            client_flag=1
        num=num_get_cache(data_mid[content_value-1],client)
        statuses=comment_get_cache(data_mid[content_value-1],client)
        #transcsv('weibo_num_cache.json', 'weibo_num_cache.csv')
        print(len(statuses["comments"]))
        count_comment=0
        for comment in statuses["comments"]:
            count_comment=count_comment+1
            tmp={'id':comment["mid"],'user':comment['user']['name'],'comments':comment['text'],'comments_num':num[0]['comments'],'reposts':num[0]['reposts']}
            df_comment=df_comment.append(tmp,ignore_index=True)
            print(str(count_comment)+' '+comment["text"])
        print('---------------------------------')
        comments_index=input('please input back or input exit:')
        if(comments_index=='exit'):
            break
    save_csv(csv_file_content,df_content) 
    save_csv(csv_file_comment,df_comment) 
    transqlit(db_file_content,csv_file_content,'content')
    transqlit(db_file_comment,csv_file_comment,'comment')
