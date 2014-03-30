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
add_all_torrents_to_db = False

defaultrc=["user:",'\n',"password:",'\n',"target:"'\n',"max_age:"'\n',"max_storage_in_mb:"'\n',"storage_dir:"'\n',"track_by_index_number:TRUE",'\n',"encoding:",'\n',"format:",'\n',"media:",'\n',"releasetype:"]

headers = {
  'User-Agent': 'Yoink! Beta'
}

def printHelpMessage(header = ''):
  if len(header) > 0:
    print header
  print 'Yoink! A Freeleech Torrent Grabber for What.CD'
  print 'Developed by tobbez, forked by phracker and evanjd.'
  print 'usage: python yoink.py [option]'
  print 'Options:'
  print '--add-all-torrents-to-db : adds all existing freeleech torrents to the yoink'
  print '                           database without downloading the .torrent file.'
  print '                           Use this option if you want to ignore all'
  print '                           existing freeleech torrents and only yoink new ones.'
  print '--recreate-yoinkrc       : deletes existing ~/.yoinkrc and generates new file'
  print '                           with default settings. Use this if migrating from'
  print '                           another version of yoink.py'
  print '--help, -h -?            : this help message'
  print '\n'
  print 'Yoink settings are stored in ~/.yoinkrc. Accepted paramaters are:'
  print '   user:                  [your what.cd username]'
  print '   password:              [your what.cd password]'
  print '   target:                [your torrent client watch dir]'
  print '   max_age:               [the maximum age of a torrent in days that'
  print '                          yoink will download].'
  print '                          If left blank, will not check age of torrent.'
  print '   max_storage_in_mb:     [the maximum size in megabytes of your storage dir]'
  print '                          If the size of your storage folder exceeds the'
  print '                          specified size, yoink will stop downloading'
  print '                          new torrents.'
  print '                          Intended for seedboxes with limited storage quotas.'
  print '                          If left blank, will not check size of storage dir.'
  print '   storage_dir:           [your torrent data dir]'
  print '                          If left blank, defaults to home directory.'
  print '   track_by_index_number: [TRUE or FALSE]'
  print '                          if true, will write all downloaded torrent IDs to'
  print '                          ~/.yoink.db and use this as the primary mechanism'
  print '                          for checking if a given torrent has already'
  print '                          been yoinked.'
  print '\n'
  print 'Please see the readme for filter options: http://git.io/kKuYrw'
  print '\n'
  print 'NOTE: Parameters must be in the provided order!'

def isStorageFull(max_storage):
  if not max_storage:
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
    if not torrentAlreadyDownloaded(tid):
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

def checkForArg(arg):
  for clarg in sys.argv[1:]:
    if arg.lower() == clarg.lower():
      return True
  return False

def download_torrent(session, tid, name):
  if not os.path.exists(target):
    print 'Target Directory does not exist, creating...'
    os.mkdir(target)

  if add_all_torrents_to_db == True:
    addTorrentToDB(tid)
    print 'Added {} to database.'.format(tid)
    return

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

  if checkForArg('--help') or checkForArg('-h') or checkForArg('-?'):
    printHelpMessage()
    return 0

  if checkForArg('--recreate-yoinkrc'):
    if os.path.exists(rcpath):
      os.remove(rcpath)

  if not os.path.exists(rcpath):
    rcf = open(rcpath,'w')
    rcf.writelines(defaultrc)
    rcf.flush()
    rcf.close()
    printHelpMessage('Wrote initial-run configuration file to ~/.yoinkrc\nYou will need to modify this file before continuing!\nSee below for accepted parameters:\n')
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
    global encoding
    encoding = rcf.readline().rstrip('\n')[9:]
    global format
    format = rcf.readline().rstrip('\n')[7:]
    global media
    media = rcf.readline().rstrip('\n')[6:]
    global releasetype
    releasetype = rcf.readline().rstrip('\n')[12:]

    if user=='' or password=='' or target=='' or track_by_index_number=='':
      printHelpMessage('ERROR: The ~/.yoinkrc configuration file appears incomplete!\nYou may need to use option --recreate-yoinkrc to revert your ~/.yoinkrc to the initial-run state for this version of Yoink.\n')
      return 0

    if max_age != '' and not max_age.isdigit():
      printHelpMessage('ERROR: Max Age (max_age) parameter must be a whole positive number.\n')
      return 0
    elif max_age == '':
      max_age = False
    else:
      max_age = int(max_age)

    if max_storage != '' and not max_storage.isdigit():
      printHelpMessage('ERROR: Max Storage (max_storage) parameter must be a whole positive number.\n')
      return 0
    elif max_storage == '':
      max_storage = False
    else:
      max_storage = int(max_storage)

    if storage_dir != '':
      try:
        storage_dir = os.path.expanduser(storage_dir)
        if not os.path.exists(storage_dir):
          raise NameError('InvalidPath')
      except:
        printHelpMessage('ERROR: Storage directory (storage_dir) paramater does not resolve to a known directory.\n')
        return 0
    else:
      storage_dir = os.path.expanduser('~')

    if track_by_index_number.upper() == 'TRUE':
      track_by_index_number = True
      if not os.path.exists(os.path.expanduser(dbpath)):
        open(os.path.expanduser(dbpath), 'w+').close()
      indexdb = sqlite3.connect(os.path.expanduser(dbpath))
      indexdbc = indexdb.cursor()
      indexdbc.execute("CREATE TABLE IF NOT EXISTS snatchedtorrents (torrent_id NUMBER(100))")
      indexdb.commit()
    elif track_by_index_number.upper() == 'FALSE':
      track_by_index_number = False
    else:
      printHelpMessage('ERROR: Track by index number (track_by_index_number) parameter must be TRUE or FALSE.\n')
      return 0

    if checkForArg('--add-all-torrents-to-db'):
      global add_all_torrents_to_db
      add_all_torrents_to_db = True
      if not track_by_index_number:
        print 'WARNING: Adding all torrents to database with tracking by index number disabled will make this operation useless until you re-enable index number tracking.'

  search_params = 'search=&freetorrent=1' + '&encoding=' + encoding + '&format=' + format + '&media=' + media + '&releasetype=' + releasetype

  html_parser = HTMLParser.HTMLParser()
  fcre = re.compile('''[/\\?*:|"<>]''')
  clean_fn = lambda x: fcre.sub('', html_parser.unescape(x))

  s = requests.session()

  cookiefile = os.path.expanduser('~/.yoink.dat')
  if os.path.exists(cookiefile):
    with open(cookiefile, 'r') as f:
      s.cookies = pickle.load(f)

  connected = False
  connectionAttempts = 0

  while connected == False and connectionAttempts < 10:
    try:
      connectionAttempts += 1
      r = s.get('https://what.cd/login.php')
      connected = True
    except requests.exceptions.TooManyRedirects:
      s.cookies.clear()
    except requests.exceptions.RequestException as e:
      print e
      sys.exit(1)  

  if r.url != u'https://what.cd/index.php':
    r = s.post('https://what.cd/login.php', data={'username': user, 'password': password, 'keeplogged': 1}, headers=headers)
    if r.url != u'https://what.cd/index.php':
      printHelpMessage("Login failed - come on, you're looking right at your password!\n")
      return

  with open(cookiefile, 'w') as f:
    pickle.dump(s.cookies, f)

  if max_age != False:
    cur_time = int(time.time())
    oldest_time = cur_time - (int(max_age) * (24 * 60 * 60))

  continueLeeching = True
  page = 1
  while continueLeeching:
    r = s.get('https://what.cd/ajax.php?action=browse&' + search_params + "&page={}".format(page), headers=headers)
    data = json.loads(r.content)
    for group in data['response']['results']:
      if max_age != False:
        if int(group['groupTime']) < oldest_time and not add_all_torrents_to_db:
          continueLeeching = False
          break
      if isStorageFull(max_storage) and not add_all_torrents_to_db:
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
    if data['response']['results'] == []:
      print '\n'
      print 'Your search returned 0 results. Please check your filters for conflicts such as FLAC + 320.'
      print '\n'
      return
    else:
      if page > data['response']['pages']:
        break
      time.sleep(2)

  print '\n'
  print "Phew! All done."
  print '\n'
  print "Yoink!: The Freeleech Torrent Grabber for What.CD"
  print "\"Go Yoink! Yourself!\""

if __name__ == '__main__':
  main()
