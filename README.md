<center>![Yoink!](https://i.imgur.com/C8OW3yw.png)</center>

*A Freeleech Torrent Grabber for What.CD*
---

>Requires python2.7 + pip + `$ pip install json requests HTMLParser`
>
>Usage: `$ python yoink.py`
>
>This is a forked version of tobbez's what.cd grabber, with some additions:
>* Added some new features, represented by the below parameters:
>	* max_age: The maximum age in days that freeleech torrents should be downloaded. This was cherrypicked from [bitfoo's commit](https://github.com/bitfoo/yoink/commit/2b980191c80f8c17b83235fcd431ed7af53af4e8).
>	* max_storage_in_mb: Applicable to seedboxes with limited storage, the maximum capacity (in MB) of your storage area. If left blank, the size of your storage area will not be evaluated.
>	* storage_dir: The folder that will be evaluated when checking if the maximum capacity of your storage area has been exceeded. Defaults to your home directory.
>	* track_by_index_number: If TRUE, will track and check torrent IDs in a sqlite db (~/.yoink.db) in addition to checking for the torrent file in your watch directory.
>* Changed the sleep between yoinks to occur after each API request, rather than each torrent download.
>
>On the initial run, a file called `~/.yoinkrc` will be generated.
>
>Edit this file to include the proper information, then re-run `$ python yoink.py`
>
>To create a cron job that executes this script every hour, simply:
>
>`$ crontab -e`
>
>and add:
>
>`00 * * * * python /path/to/yoink.py`


**Now work out that buffer! (without blowing your storage quota)**

*<3 [tobbez](https://what.cd/user.php?id=605)*
*<3 [evanjd/notarebel](https://what.cd/user.php?id=417)*