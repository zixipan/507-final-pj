README
Demo link: https://www.youtube.com/watch?v=FcZlPa9FhP8
Special requirements:
    1. The user needs to have a Sina Weibo account. Get one from : https://www.weibo.com/
    2. The user needs to request for adding their account to the developer account (Contact me if you need! My email address is zixipan@umich.edu)
    3. Understanding Chinese can help with understanding the Weibo topics, contents, and comments. (I am sorry if you can't understand the Weibo contents since this is a "Chinese Twitter")
    4.If you can't get a Weibo secret key, check this: https://docs.google.com/document/d/1k4u7f0TdJ-vwCgBIC-tBNIjBoDd7dL6zV3S0Xga48tM/edit?usp=sharing
Required Packages:
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


Brief Instructions:
    1. log in your Weibo account at the main page.
    2. Contact me to add your account to the developer account.
    3. Click the TOPIC button to see the current hot topics list.
    4. Input the index number of the topic in which users want to see the contents under that.
    5. Click the content button to see the result list.
    6. Input the index number of the content in which the user wants to see the comments under that.
    7. Click the comment button. (If the user doesn't let me add your account to the developer account, the user can't do this.)
    8. Use the dropdown list to see the bar chart of the hot topics' number and rank by choosing a hot bar option and click the draw button.
    9. Use the dropdown list to see the wordcloud of the contents under the topic user chose by choosing wordcloud option and click the draw button.
    10.  Input the topic number to the topic_number and input the track time to the follow_time for how long the user wants to see the change of the hot number.
    11. Choose the hot line option under the dropdown list and click draw to see the line chart for the topic during the time the user inputted.
