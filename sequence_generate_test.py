# -*- coding: utf-8 -*-

import requests
import time
import sys
if len(sys.argv) >= 2 and sys.argv[1] and int(sys.argv[1]):
    port = int(sys.argv[1])
else:
    port = 5000
num = 500
time.sleep(3)

while num > 0:
	r = requests.post('http://127.0.0.1:' + str(port) + '/increase')
	num = num - 1