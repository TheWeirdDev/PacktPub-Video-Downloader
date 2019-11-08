# PVdl: PacktPub Video Downloader

The Easiest way to download any Packt video

**Notice: You need a Packt account with subscription or free trial to download videos**

# Features

* Download any video using your subscription
* Resume downloads
* Download rate limit
* Easy to use

# How to use

Clone this repository, install requirements and run the script. For example:

```bash
chmod +x ./PVdl.py
pip -r requirements.txt

./PVdl.py -u username@example.com -p Passw0rd -l "https://subscription.packtpub.com/video/programming/9781788834995"
```

Usage:

```
usage: PVdl.py [-h] [-u USERNAME] [-p PASSWORD] [-r RATE_LIMIT] [-l LINK]

PacktPub Video Downloader

optional arguments:
  -h, --help            show this help message and exit

required arguments:
  -u USERNAME, --username USERNAME
                        Your Packt Username
  -p PASSWORD, --password PASSWORD
                        Your Password
  -r RATE_LIMIT, --rate-limit RATE_LIMIT
                        Download rate limit
  -l LINK, --link LINK  Packt Video link

```

# License

PacktPub Video Downloader is a free software and is licensed under GNU Public License v3+

For more information see [LICENSE](LICENSE)
