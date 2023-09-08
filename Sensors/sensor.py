from requests import get, post
import time
import pandas as pd
#base_url = 'https://prova1-esame.appspot.com'
base_url = 'http://localhost:80'

sensor = 'MS469'
data = pd.read_excel('/Users/gili98/Documents/Temperature-Sensor-Simulation/Data/Journey_MS469_1.xlsx', header=12)

for i in range(27):
    print(sensor, ' invio....')
    print(i)


    data_to_send = {}
    for column in data.columns:
        data_to_send[column] = data[column].iloc[i]
    print(data_to_send)

    r = post(f'{base_url}/sensors/{sensor}', data=data_to_send)
    time.sleep(2)

print('done')
