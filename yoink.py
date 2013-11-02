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
from os.path import expanduser

## DO NOT TOUCH THESE ##
user = ''
password = ''
target = ''

defaultrc=["user:",'\n',"password:",'\n',"target:"]

headers = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9) AppleWebKit/537.71 (KHTML, like Gecko) Version/7.0 Safari/537.71'
}

def download_torrent(session, tid, name):
  if not os.path.exists(target):
    print 'Target Directory does not exist, creating...'
    os.mkdir(target)

  path = os.path.join(target, name)
  if os.path.exists(path):
    print 'I already haz {}.'.format(tid)
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
  time.sleep(1)
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
    return 0
  else:
    rcf = open(rcpath)
    global user
    user = rcf.readline().rstrip('\n')[5:]
    global password
    password = rcf.readline().rstrip('\n')[9:]
    global target
    target = os.path.expanduser(rcf.readline().rstrip('\n')[7:])
    if user=='' or password=='' or target=='':
      print 'Finish filling out ~/.yoinkrc and try again!'
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

  page = 1
  while True:
    r = s.get('https://what.cd/ajax.php?action=browse&' + search_params + "&page={}".format(page), headers=headers)
    data = json.loads(r.content)
    for group in data['response']['results']:
      if 'torrents' in group:
        for torrent in group['torrents']:
          if not torrent['isFreeleech']:
            continue
          fn = clean_fn('{}. {} - {} - {} ({} - {} - {}).torrent'.format(torrent['torrentId'], group['artist'][:50], group['groupYear'], group['groupName'][:50], torrent['media'], torrent['format'], torrent['encoding']))
          download_torrent(s, torrent['torrentId'], fn)
      else:
        fn = clean_fn('{} {}.torrent'.format(group['torrentId'], group['groupName'][:100]))
        download_torrent(s, group['torrentId'], fn)

    page += 1
    if page > data['response']['pages']:
      print "Wow, done already?"
      break

  print "Phew! Now that was one intense Yoink!"


if __name__ == '__main__':
  main()
