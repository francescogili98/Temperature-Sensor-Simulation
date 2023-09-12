from flask import Flask,request,render_template,redirect,url_for
import json
from google.cloud import firestore
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from secret import secret_key
import datetime


app = Flask(__name__) # create flask application
app.config['SECRET_KEY'] = secret_key
local = True # False if deployment in gcp

login = LoginManager(app)
login.login_view = '/static/login.html' # If the application needs to request a login operation, it redirects to this html page

# dictionaries to calculate the door opening time (needed for alarms)
start_time = {}
end_time = {}
open = {}

class User(UserMixin):
    def __init__(self, username):
        super().__init__()
        self.id = username
        self.username = username
        self.par = {}

def timeDuration(timeS, timeF):
    date, time = timeS[0], timeS[1]
    yearA = int(date.split('-')[2].strip())
    if date.split('-')[1].strip().startswith('0'):
        monthA = int(date.split('-')[1].strip()[1])
    else:
        monthA = int(date.split('-')[1].strip())
    if date.split('-')[0].strip().startswith('0'):
        dayA = int(date.split('-')[0].strip()[1])
    else:
        dayA = int(date.split('-')[0].strip())
    if time.split(':')[0].strip().startswith('0'):
        hourA = int(time.split(':')[0].strip()[1])

    else:
        hourA = int(time.split(':')[0].strip())
    if time.split(':')[1].strip().startswith('0'):
        minuteA = int(time.split(':')[1].strip()[1])
    else:
        minuteA = int(time.split(':')[1].strip())

    date, time = timeF[0], timeF[1]
    yearB = int(date.split('-')[2].strip())
    if date.split('-')[1].strip().startswith('0'):
        monthB = int(date.split('-')[1].strip()[1])
    else:
        monthB = int(date.split('-')[1].strip())
    if date.split('-')[0].strip().startswith('0'):
        dayB = int(date.split('-')[0].strip()[1])
    else:
        dayB = int(date.split('-')[0].strip())
    if time.split(':')[0].strip().startswith('0'):
        hourB = int(time.split(':')[0].strip()[1])
    else:
        hourB = int(time.split(':')[0].strip())
    if time.split(':')[1].strip().startswith('0'):
        minuteB = int(time.split(':')[1].strip()[1])
    else:
        minuteB = int(time.split(':')[1].strip())

    # print(yearA, monthA, dayA, hourA, minuteA)
    # print(yearB, monthB, dayB, hourB, minuteB)

    a = datetime.datetime(yearA, monthA, dayA, hourA, minuteA, 10)

    b = datetime.datetime(yearB, monthB, dayB, hourB, minuteB, 10)

    c = b - a

    return c.total_seconds() / 60


@login.user_loader  # check if the current user is registered in firestore database.
def load_user(username):
    # credentials.json contains service account credentials. The service account has to be created in gcp.
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    user = db.collection('utenti').document(username).get()
    if user.exists:
        return User(username)
    return None


@app.route('/sensors', methods=['GET'])#@login_required
def main():
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    s = ['--']
    for doc in db.collection('sensors').stream():   # sensors collection in firestore
        s.append(doc.id)
    return json.dumps(s), 200


#@app.route('/main', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET'])
def get_home():
    return redirect(url_for('static', filename='home.html'))

# parameter 's' in the URL
@app.route('/sensors/<s>', methods=['POST'])
def add_data(s):
    global open
    global start_time
    global end_time
    if s not in open:
        open[s] = False
    opening_duration = 0

    val = {'temp': float(request.values['Temp 1']), 'lat': float(request.values['Lat/Long'].split(',')[0]), 'long': float(request.values['Lat/Long'].split(',')[1]),
           'Date': request.values['Date'], 'Time': request.values['Time']}
    print('misurazione,',val)
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    doc_ref = db.collection('sensors').document(s)  # reference to document entity
    entity = doc_ref.get()  # got the real entity, not just the reference
    if entity.exists and 'values' in entity.to_dict():
        v = entity.to_dict()['values']  # copy existing values
        v.append(val)   # append current val to the existing values
        doc_ref.update({'values': v}) # update values referred to sensor s
    else:   # in this case val is the first data point
        doc_ref.set({'values': [val]})

    if request.values['Door 1'] == 'Open' and open[s] == False:
        start_time[s] = [val['Date'], val['Time']]
        open[s] = True

    elif request.values['Door 1'] == 'Closed' and open[s] == True:
        end_time[s] = [val['Date'], val['Time']]
        opening_duration = timeDuration(start_time[s], end_time[s])
        print('opening ', opening_duration)
        open[s] = False

    if float(val['temp']) > float(request.values['maxTemp']) or opening_duration > float(request.values['maxDoor']):    # two possible alarm triggers
        temp_violation = True
        if opening_duration > float(request.values['maxDoor']) and float(val['temp']) > float(request.values['maxTemp']):
            temp_violation = '1'
        elif opening_duration > float(request.values['maxDoor']) and float(val['temp']) <= float(request.values['maxTemp']):
            temp_violation = '2'
        elif opening_duration <= float(request.values['maxDoor']) and float(val['temp']) > float(request.values['maxTemp']):
            temp_violation = '3'
            opening_duration = 'NaN'
        else:
            temp_violation = '4'
            opening_duration = 'NaN'

        doc_ref_2 = db.collection('alarms').document(s)
        entity_2 = doc_ref_2.get()
        val_2 = {'date': request.values['Date'], 'time': request.values['Time'], 'temp': str(val['temp']),
                 'opening time': str(opening_duration), 'temp alarm': temp_violation, 'location': request.values['Location']}
        print(val_2)
        if entity_2.exists and 'values' in entity_2.to_dict():
            v_2 = entity_2.to_dict()['values']
            v_2.append(val_2)
            doc_ref_2.update({'values': v_2})
        else:
            doc_ref_2.set({'values': [val_2]})
    return 'data recorded', 200


@app.route('/sensors/<s>', methods=['GET'])
@login_required
def get_data(s):
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    entity = db.collection('sensors').document(s).get()
    if entity.exists:
        return json.dumps(entity.to_dict()['values']), 200
    else:
        return redirect(url_for('static', filename='sensor404.html'))

'''
@app.route('/graph/<s>',methods=['GET'])
@login_required
def graph_data(s):
    # sono sempre i due possibili modi per accedere a firestore da locale o da remoto
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    entity = db.collection('sensors').document(s).get() #con get accedi veramente all'entità, non con doc ref
    if entity.exists:
        d = []
        d.append(['Number', s])
        t = 0
        for x in entity.to_dict()['values']:
            d.append([str(t), x['temp']])
            t += 1
            print(x['temp'])
        return render_template('graph.html', sensor=s, data=json.dumps(d))
        # gli passo una pagina html e dei parametri che userò nella pagina (quanti ne voglio, la pagina è quindi dinamica)
        # gli puoi passare anche un dizionario come parametro e usare if/cicli for nell'html per leggerci i valori
        # non è detto che devi restituire sempre una pagina html, magari il client è un'applicazione che gli bastano stringhe/dati json in risposta
    else:
        return redirect(url_for('static', filename='sensor404.html'))
        # ridirige a url con pagina static
'''

@app.route('/graphh/<s>', methods=['GET'])
@login_required
def graphh_data(s):
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    entity = db.collection('sensors').document(s).get()
    if entity.exists:
        temperature_data = []
        orari_data = []
        current_date = 'null'
        lat = 0
        long = 0
        for x in entity.to_dict()['values']:

            temperature_data.append(x['temp'])
            orari_data.append(x['Time'])
            current_date = str(x['Date'])
            lat = float(x['lat'])
            long = float(x['long'])
        temperature_data = temperature_data[-25:]
        orari_data = orari_data[-25:]

        alarms_data = []
        entity_2 = db.collection('alarms').document(s).get()
        if entity_2.exists:

            for x in entity_2.to_dict()['values']:
                alarms_data.append(
                    {'Date': x['date'], 'Time': x['time'], 'Location': x['location'], 'Temp_alarm': x['temp alarm'],
                     'TempValue': x['temp'], 'Opening_time': x['opening time']})
            alarms_data = alarms_data[-10:]

        return render_template('totalgraph.html', sensor=s, temperatureData=json.dumps(temperature_data), orariData=json.dumps(orari_data), lat=lat, long=long, AlarmsData=json.dumps(alarms_data), current_date=current_date)

    else:
        return redirect(url_for('static', filename='sensor404.html'))


@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        next_page = request.args.get('next')
        if not next_page:
            next_page = '/home'
        return redirect(next_page)
    print(request.args.get('next'))
    username = request.values['username']   # given by the form
    password = request.values['password']   # given by the form

    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    user = db.collection('utenti').document(username).get()
    if user.exists and user.to_dict()['password']==password:
        login_user(User(username))
        next_page = request.args.get('next')
        if not next_page:
            next_page = '/home'
        return redirect(next_page)
    return redirect('/static/login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/adduser', methods=['GET', 'POST'])
@login_required
def adduser():
    if current_user.username == 'francesco':
        if request.method == 'GET':
            return redirect('/static/adduser.html')
        else:
            username = request.values['username']
            password = request.values['password']
            country = request.values['country']
            email = request.values['email']
            firstname = request.values['firstname']
            lastname = request.values['lastname']
            db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
            user = db.collection('utenti').document(username)
            user.set({'username': username, 'password': password, 'email': email, 'firstname': firstname, 'lastname': lastname, 'country':country})
            return 'user registered'
    else:
        return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

