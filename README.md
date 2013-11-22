French Touch Repository
===============

French Touch is a repository plugin for XDM (eXtendable Download Manager), a plugin based media collection manager.
This repository is made by Torf and is not official.

#Plugin List

###Indexer Plugin

#####Gks
Gks is a torrent indexer plugin importing torrents from *Gks.gs tracker*. 
```
This plugin uses your own Gks.gs authkey (from https://gks.gs/m/account/) in order to find and download torrents. 
It is currently in BETA but authkey safe.
```
  
===
#####T411
T411 is a torrent indexer plugin importing torrents from *t411.me tracker*.
```
This plugin uses your own t411.me account (login and password) in order to find and download torrents.
It is currently in BETA but account safe.
```

=============

###Downloader Plugin
#####Rutorrent
Rutorrent is a torrent downloader plugin using *RPC plugin* of your Rutorrent.
Rutorrent plugin permits to :
- Add new torrent to your Rutorrent
- Follow the progress of an added torrent
- Follow the status of an added torrent (downloading, completed or failed)

```
Rtorrent and Rutorrent must be running in order to use this plugin.
You don't have to config anything on your server.
This plugin uses your own Rutorrent account in order to access to it.
It is currently in BETA but account safe.
```

===
#####Rss
Rss is a torrent downloader plugin using [RSS Broadcatching](http://en.wikipedia.org/wiki/Broadcatching) by generating a RSS feed.
The RSS feed contains all snatched torrents and can be understand by the majority of torrent downloader (like Rutorrent, transmission or µTorrent).
Rss plugin permits only to add a new torrent to your torrent downloader software. 
```
Rss feed can be accessed with the link http://myserver:8500/api/rest/fr.torf.rss/Default/rssFeed.
The host configuration permits to change the host of torrent link value in rss feed.
```

===
#####Transmission
Transmission is a torrent downloader plugin using *Transmission integrated RPC API*.
Transmission plugin permits to :
- Add new torrent to your Transmission server
- Follow the progress of an added torrent
- Follow the status of an added torrent (downloading, completed or failed)

```
Transmission must be running in order to use this plugin.
You may have to allow access from XDM to Transmission via transmission port.
This plugin uses your own Transmission account in order to access to it.
It is currently in BETA but account safe.
```

# Install

Add this repository to your repositories list in XDM using this link :
<pre>https://raw.github.com/Torf/XDM-French-Touch/master/meta.json</pre>

