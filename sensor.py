from requests import get, post
import time
import pandas as pd
base_url = 'https://prova1-esame.appspot.com'

#base_url = 'http://localhost:80'

sensor = 's1'

for i in range(1000):
    print(sensor,'invio....')
    r = post(f'{base_url}/sensors/{sensor}', data={'val': i})
    time.sleep(1)

print('done')
