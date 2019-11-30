#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 21:02:09 2019

@author: @TheWeirdDev
"""

import requests, json, sys, os, re
from os import path
import urllib.request
from tqdm import tqdm
import pycurl

import argparse


access_jwt = ""
refresh_token = ""
sess = requests.Session();

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[1;31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def check_error(j):
    if "errorCode" in j.keys():
        print_err("Error: " + j['message'])

def print_err(err):
    print(bcolors.FAIL + str(err) + bcolors.ENDC)
    exit(1)

        
SYMBOLS = {
    'customary'     : ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'),
    'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'),
}
def human2bytes(s):
    init = s
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for name, sset in SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == 'k':
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = SYMBOLS['customary']
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]:1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])
  

class DownloadProgressBar(tqdm):
    def curl_progress(self, total, existing, upload_t, upload_d):
        self.total = total
        self.update(existing - self.n)


def curl_limit_rate(url, filename, rate_limit, desc):
    """Rate limit in bytes"""
    with DownloadProgressBar(unit='B', unit_scale=True,
                               miniters=1, desc=desc) as pbar:
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.MAX_RECV_SPEED_LARGE, rate_limit)
        if os.path.exists(filename):
            file_id = open(filename, "ab")
            c.setopt(c.RESUME_FROM, os.path.getsize(filename))
        else:
            file_id = open(filename, "wb")
    
        c.setopt(c.WRITEDATA, file_id)
        c.setopt(c.NOPROGRESS, 0)
        c.setopt(c.PROGRESSFUNCTION, pbar.curl_progress)
        c.perform()
    
def download_url(url, output_path, limit_rate):
    try:
        desc = output_path.split(os.sep)[-1]
        desc = desc[:desc.index(".mp4")]
        #with DownloadProgressBar(unit='B', unit_scale=True,
        #                    miniters=1, desc=desc) as t:
        #   urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)
        curl_limit_rate(url, output_path, limit_rate, desc)
    except (Exception, KeyboardInterrupt) as e:
        print_err(e)
        
def refresh():
    global refresh_token
    global access_jwt
    login = sess.post("https://services.packtpub.com/auth-v1/users/me/tokens",
                      json.dumps({"refresh": refresh_token}),
                      headers={'Authorization': 'Bearer ' + access_jwt})
    
    login_data = json.loads(login.content)
    check_error(login_data)
    
    refresh_token = login_data['data']['refresh']
    access_jwt = login_data['data']['access']
    
def login(username, password):
    login = sess.post("https://services.packtpub.com/auth-v1/users/tokens",
                      json.dumps({"username": username,"password": password}))
    login_data = json.loads(login.content)
    check_error(login_data)
    
    global access_jwt
    global refresh_token
    refresh_token = login_data['data']['refresh']
    access_jwt = login_data['data']['access']

def get_video_url(vid_id, video_id):
    worked = False
    while(not worked):
        url = "https://services.packtpub.com/products-v1/products/{}/{}".format(vid_id, video_id)
        data = sess.get(url, headers={'Authorization': 'Bearer ' + access_jwt})
        vid = json.loads(data.content)
        if ("message" in vid.keys()) and vid["message"] == "jwt expired":
            refresh()
            continue
        worked = True
    if not ("data" in vid.keys()):
        print_err("Error: Can't get video url")
        
    return vid["data"]
    
def get_chapters(vid_id, limit_rate):
    url = 'https://static.packt-cdn.com/products/{}/summary'.format(vid_id)
    data = sess.get(url)
    details = json.loads(data.content)
    
    if not ("title" in details.keys()):
        print_err("Error: Wrong link. No video found.")
        
    title = details["title"]
    title = re.sub(r"[<>|/\\?*]", "_" ,title);
    os.makedirs(title, 0o755, exist_ok=True)
        
    url = 'https://static.packt-cdn.com/products/{}/toc'.format(vid_id)
    data = sess.get(url)
    details = json.loads(data.content)
    
    if not ("chapters" in details.keys()):
        print_err("Error: Wrong link. No video found.")
        
    all_chapters = details['chapters']
    for x,i in enumerate(all_chapters):
        section = i['title']
        section = re.sub(r"[<>|/\\?*]", "_" , section)
        s_path = "{}{}{:02}-{}".format(title, os.sep, x+1, section)
        os.makedirs(s_path, 0o755, exist_ok=True)
        print(bcolors.OKGREEN + "\nChapter {}/{}:".format(x+1, len(all_chapters)), section, "\n" + bcolors.ENDC)
        for y,c in enumerate(i['sections']):
            chapter = c['title']
            chapter = re.sub(r"[<>|/\\?*]", "_" , chapter)
            c_path = "{}{}{:02}-{}.mp4".format(s_path, os.sep , y+1, chapter)
            video_id = i['id'] + '/' + c['id']
            video_url = get_video_url(vid_id, video_id)
            download_url(video_url, c_path, limit_rate)

    
def start_download(username, password, vid_id, limit_rate):
    login(username, password)
    r = sess.get('https://services.packtpub.com/users-v1/users/me/metadata', headers={'Authorization': 'Bearer ' + access_jwt})
    metadata = json.loads(r.content)
    check_error(metadata)
    
    name = metadata['name']
    print(bcolors.HEADER + "Logged in as '{} {}'".format(name['firstName'], name['lastName']))
    print("mail: {}".format(metadata['mail']))
    print("uuid: {}".format(metadata['uuid'])+ bcolors.ENDC)
    
    subscription = metadata['subscription']
    if not (subscription['subscribed'] or subscription['freeTrial']):
        print_err("You don't have a valid subscription")
    
    print(bcolors.OKGREEN + "You have a valid Subscription" + bcolors.ENDC)
    
    get_chapters(vid_id, limit_rate)
    
def main():
    try:
        parser = argparse.ArgumentParser(description='PacktPub Video Downloader', prog="pvdl.py")
        required_args = parser.add_argument_group('required arguments')
        required_args.add_argument('-u', '--username', help='Your Packt Username')
        required_args.add_argument('-p', '--password', help='Your Password')
        required_args.add_argument('-r', '--rate-limit', default = 0, help='Download rate limit')
        required_args.add_argument('-l', '--link', help='Packt Video link')
        
        args = parser.parse_args()
        if not (args.username or args.password or args.link):
            parser.print_help()
            exit(1)
            
        link = args.link
        username = args.username
        password = args.password
        if(args.rate_limit):
            limit_rate = human2bytes(args.rate_limit)
        else:
            limit_rate = 0
            
        vid_id = re.findall(r"https://.*packtpub.*video/.*/(\d+)/?$", link)
        if len(vid_id) < 1:
            print_err("Error: Invalid link")
            
        vid_id = vid_id[0]
        start_download(username, password, vid_id, limit_rate)
    except KeyboardInterrupt:
        print("Interrupted")
        exit(1)
    

if __name__ == "__main__":
    main()


