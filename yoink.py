#!/usr/bin/env python

import time
import cPickle as pickle
import json
import requests
import HTMLParser
import os
import re
import sys
import argparse
import sqlite3
from os.path import expanduser

## SAFE TO EDIT ##
dbpath = '~/.yoink.db'

## DO NOT TOUCH THESE ##
user = ''
password = ''
target = ''
max_storage = ''
max_age = ''
storage_dir = ''
track_by_index_number = None

defaultrc=["user:",'\n',"password:",'\n',"target:"'\n',"max_age:"'\n',"max_storage_in_mb:"'\n',"storage_dir:"'\n',"track_by_index_number:TRUE"]

headers = {
  'User-Agent': 'Yoink! Beta'
}

def isStorageFull(max_storage):
  if max_storage == False:
    return False

  totalSize = sum( os.path.getsize(os.path.join(dirpath,filename)) for dirpath, dirnames, filenames in os.walk( storage_dir ) for filename in filenames ) /1024/1024
  if totalSize >= max_storage:
    return True
  else:
    return False

def torrentAlreadyDownloaded(tid):
  if track_by_index_number:
    try:
      indexdb = sqlite3.connect(os.path.expanduser(dbpath))
      indexdbc = indexdb.cursor()
      indexdbc.execute("SELECT COUNT(*) FROM snatchedtorrents WHERE torrent_id = (?)", [tid])
      if int(str(indexdbc.fetchone())[1]) == 0:
        torrent_found = False
      else:
        torrent_found = True
    except Exception,e:
      print 'Error when executing SELECT on ~/.yoink.db:'
      print str(e)
      sys.exit()
    finally:
      if indexdb:
        indexdbc.close()
      return torrent_found
  else:
    return False

def addTorrentToDB(tid):
  if track_by_index_number:
    try:
      indexdb = sqlite3.connect(os.path.expanduser(dbpath))
      indexdbc = indexdb.cursor()
      indexdbc.execute("INSERT INTO snatchedtorrents values (?)", [tid])
      indexdb.commit()
    except Exception,e:
      print 'Error when executing INSERT on ~/.yoink.db:'
      print str(e)
      sys.exit()
    finally:
      if indexdb:
        indexdbc.close()

def download_torrent(session, tid, name):
  if not os.path.exists(target):
    print 'Target Directory does not exist, creating...'
    os.mkdir(target)

  if torrentAlreadyDownloaded(tid):
    print 'I have previously downloaded {}.'.format(tid)
    return

  path = os.path.join(target, name)
  if os.path.exists(path):
    print 'I already haz {}.'.format(tid)
    addTorrentToDB(tid)
    return

  if not hasattr(download_torrent, 'authdata'):
    r = session.get('https://what.cd/ajax.php?action=index', headers=headers)
    d = json.loads(r.content)
    download_torrent.authdata = '&authkey={}&torrent_pass={}'.format(d['response']['authkey'], d['response']['passkey'])

  print '{}:'.format(tid),
  dl = session.get('https://what.cd/torrents.php?action=download&id={}{}'.format(tid, download_torrent.authdata), headers=headers)
  with open(path, 'wb') as f:
    for chunk in dl.iter_content(1024*1024):
      f.write(chunk)
  addTorrentToDB(tid)
  print 'Yoink!'

def main():

  rcpath=os.path.expanduser('~/.yoinkrc')
  if not os.path.exists(rcpath):
    rcf = open(rcpath,'w')
    rcf.writelines(defaultrc)
    rcf.flush()
    rcf.close()
    print 'Wrote initial-run configuration files to ~/.yoinkrc'
    print 'Modify it appropriately and reload Yoink!'
    print 'user:USERNAME'
    print 'password:PASSWORD'
    print 'target:TORRENTDIR'
    print 'max_age:NUMDAYS [Optional, default: 3650]'
    print 'max_storage_in_mb:NUMINMEGABYTES [Optional, if left blank will not check]'
    print 'storage_dir:STORAGEDIR [Optional, default home directory]'
    print 'track_by_index_number:TRUE or FALSE'
    return 0
  else:
    rcf = open(rcpath)
    global user
    user = rcf.readline().rstrip('\n')[5:]
    global password
    password = rcf.readline().rstrip('\n')[9:]
    global target
    target = os.path.expanduser(rcf.readline().rstrip('\n')[7:])
    global max_age
    max_age = rcf.readline().rstrip('\n')[8:]
    global max_storage
    max_storage = rcf.readline().rstrip('\n')[18:]
    global storage_dir
    storage_dir = rcf.readline().rstrip('\n')[12:]
    global track_by_index_number
    track_by_index_number = rcf.readline().rstrip('\n')[22:]
    
    if user=='' or password=='' or target=='' or track_by_index_number=='':
      print 'Finish filling out ~/.yoinkrc and try again!'
      return 0

    if max_age != '' and max_age.isdigit() == False:
      print 'Max Age (max_age) parameter must be a whole positive number.'
      return 0
    elif max_age == '':
      max_age = 3650
    else:
      max_age = int(max_age)

    if max_storage != '' and max_storage.isdigit() == False:
      print 'Max Storage (max_storage) parameter must be a whole positive number.'
      return 0
    elif max_storage == '':
      max_storage = False
    else:
      max_storage = int(max_storage)

    if storage_dir != '':
      try:
        storage_dir = os.path.expanduser(storage_dir)
        if os.path.exists(storage_dir) == False:
          raise NameError('InvalidPath')
      except:
        print 'Storage directory (storage_dir) paramater does not resolve to a known directory.'
        return 0
    else:
      storage_dir = os.path.expanduser('~')

    if track_by_index_number.upper() == 'TRUE':
      track_by_index_number = True
      if os.path.exists(os.path.expanduser(dbpath)) == False:
        open(os.path.expanduser(dbpath), 'w+').close()
      indexdb = sqlite3.connect(os.path.expanduser(dbpath))
      indexdbc = indexdb.cursor()
      indexdbc.execute("CREATE TABLE IF NOT EXISTS snatchedtorrents (torrent_id NUMBER(100))")
      indexdb.commit()
    elif track_by_index_number.upper() == 'FALSE':
      track_by_index_number = False
    else:
      print 'Track by index number (track_by_index_number) parameter must be TRUE or FALSE.'
      return 0

  search_params = 'search=&freetorrent=1'

  html_parser = HTMLParser.HTMLParser()
  fcre = re.compile('''[/\\?*:|"<>]''')
  clean_fn = lambda x: fcre.sub('', html_parser.unescape(x))

  s = requests.session()

  cookiefile = os.path.expanduser('~/.yoink.dat')
  if os.path.exists(cookiefile):
    with open(cookiefile, 'r') as f:
      s.cookies = pickle.load(f)

  r = s.get('https://what.cd/login.php')
  if r.url != u'https://what.cd/index.php':
    r = s.post('https://what.cd/login.php', data={'username': user, 'password': password})
    if r.url != u'https://what.cd/index.php':
      print "Login failed - come on, you're looking right at your password!"
      return

  with open(cookiefile, 'w') as f:
    pickle.dump(s.cookies, f)

  cur_time = int(time.time())
  oldest_time = cur_time - (int(max_age) * (24 * 60 * 60))

  continueLeeching = True
  page = 1
  while continueLeeching:
    r = s.get('https://what.cd/ajax.php?action=browse&' + search_params + "&page={}".format(page), headers=headers)
    data = json.loads(r.content)
    for group in data['response']['results']:
      if int(group['groupTime']) < oldest_time:
        continueLeeching = False
        break
      if isStorageFull(max_storage):
        continueLeeching = False
        print 'Your storage equals or exceeds ' + str(max_storage) + 'MB, exiting...'
        break
      if 'torrents' in group:
        for torrent in group['torrents']:
          if not torrent['isFreeleech']:
            continue
          fn = clean_fn('{}. {} - {} - {} ({} - {} - {}).torrent'.format(torrent['torrentId'], group['artist'][:50], group['groupYear'], group['groupName'][:50], torrent['media'], torrent['format'], torrent['encoding']))
          download_torrent(s, torrent['torrentId'], fn)
      else:
        fn = clean_fn('{} {}.torrent'.format(group['torrentId'], group['groupName'][:100]))
        download_torrent(s, group['torrentId'], fn)
      time.sleep(2)
    page += 1
    if page > data['response']['pages']:
      print "Wow, done already?"
      break

  print "Phew! Now that was one intense Yoink!"


if __name__ == '__main__':
  main()