from requests import get, post
import time
import pandas as pd
#base_url = 'https://prova1-esame.appspot.com'
base_url = 'http://localhost:80'

sensor = 'MS479'
data = pd.read_excel('/Users/gili98/Documents/Temperature-Sensor-Simulation/Data/Journey_MS-479.xlsx', header=12)

for i in range(10):
    print(sensor, ' invio....')

    data_to_send = {}
    for column in data.columns:
        data_to_send[column] = data[column].iloc[i]
    data_to_send['maxTemp'] = -13
    data_to_send['maxDoor'] = 15

    r = post(f'{base_url}/sensors/{sensor}', data=data_to_send)
    time.sleep(4)

print('done')