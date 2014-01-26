<center>![Yoink!](https://i.imgur.com/C8OW3yw.png)</center>

*A Freeleech Torrent Grabber for What.CD*
---

Requires python2.7 + pip + `$ pip install json requests HTMLParser`

Usage: `python yoink.py [option]`

Options:

- `--add-all-torrents-to-db`: adds all existing freeleech torrents to the yoink database without downloading the .torrent file. Use this option if you want to ignore all existing freeleech torrents and only yoink new ones.
- `--recreate-yoinkrc`: deletes existing ~/.yoinkrc and generates new file with default settings. Use this if migrating from another version of yoink.py
- `--help` or `-h` or `-?`: shows help message

Yoink settings are stored in ~/.yoinkrc and this file will be auto-generated on initial run. Accepted parameters are:

- `user`: your what.cd username
- `pass`: your what.cd password
- `target`: your torrent client watch directory
- `max_age`: the maximum age of a torrent in days that yoink will download. If left blank, yoink will not check the age of the torrent.
- `max_storage_in_mb`: the maximum size in megabytes of your storage directory. If the size of your storage directory exceeds the specified size, yoink will stop downloading new torrents. This runs on the assumption that your torrent client preallocated the space required for each torrent immediately after the .torrent folder is added to your watch directory. If left blank, yoink will not check the size of your storage area. This is intended for seedboxes with limited storage quotas.
- `storage_dir`: Your torrent data directory. If left blank, defaults to your home directory.
- `track_by_index_number`: TRUE or FALSE. If true, will write all downloaded torrent IDs to ~/.yoink.db and use this as the primary mechanism for checking if a given torrent has already been yoinked.

To create a cron job that executes this script every hour, simply:

`$ crontab -e`

and add:

`00 * * * * python /path/to/yoink.py`

*Now work out that buffer! (without blowing your storage quota)*

**Contributors:  [tobbez![<3](http://i.imgur.com/kX2q6Bm.png)](https://what.cd/user.php?id=605)  [phracker![<3](http://i.imgur.com/kX2q6Bm.png)](https://what.cd/user.php?id=260077)  [evanjd/notarebel![<3](http://i.imgur.com/kX2q6Bm.png)](https://what.cd/user.php?id=417)**
