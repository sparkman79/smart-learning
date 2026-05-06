import urllib.request
r = urllib.request.urlopen('https://api.ipify.org')
print(r.read().decode())
