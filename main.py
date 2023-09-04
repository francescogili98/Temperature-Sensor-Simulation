from flask import Flask,request,render_template,redirect,url_for
import json
from google.cloud import firestore
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from secret import secret_key
import datetime

start_time = {}
end_time = {}
open = {}

class User(UserMixin):
    def __init__(self, username):
        super().__init__()
        self.id = username
        self.username = username
        self.par = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
local = True

login = LoginManager(app)
login.login_view = '/static/login.html'

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

@login.user_loader
def load_user(username):
    # client per accedere a firestore, il file json è il service account per autenticarsi, l'ho generato da googleCloud
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    user = db.collection('utenti').document(username).get()
    if user.exists:
        return User(username)
    return None

@app.route('/', methods=['GET', 'POST'])
@app.route('/main', methods=['GET', 'POST'])
@app.route('/sensors', methods=['GET'])
def main():
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    s = []
    for doc in db.collection('sensors').stream(): #nella collezione sensors scorro gli id dei doc
        s.append(doc.id)
    return json.dumps(s), 200 #ritorno un json con la lista s

# all'interno dell'url c'è un parametro
@app.route('/sensors/<s>', methods=['POST'])
def add_data(s):
    global open
    if s not in open:
        open[s] = False
    opening_duration = 0

    val = float(request.values['Temp 1'])
    print('VALLL,',val)
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    doc_ref = db.collection('sensors').document(s) #mi fornisce riferimento all'entità documento oppure se non c'era me la crea
    entity = doc_ref.get() #get mi restituisce l'entità vera e propria dandogli il riferimento
    if entity.exists and 'values' in entity.to_dict(): #se al sensore s corrispondono già valori allora aggiungi ad essi val
        v = entity.to_dict()['values'] #copio i valori
        v.append(val) #aggiungo val alla copia dei valori
        doc_ref.update({'values': v}) #il nuovo value è la copia aggiornata
    else: #altrimenti crei il dizionario associato con chiave values e valore lista...
        doc_ref.set({'values': [val]})

    if request.values['Door 1'] == 'Open' and open[s] == False:
        start_time[s] = [request.values['Date'], request.values['Time']]
        open[s] = True
        print('start')
    elif request.values['Door 1'] == 'Closed' and open[s] == True:
        print(start_time[s])
        end_time[s] = [request.values['Date'], request.values['Time']]
        opening_duration = timeDuration(start_time[s], end_time[s])
        print('opening ', opening_duration)
        open[s] = False
        print('end')

    if float(val) > -15 or opening_duration > 20: #oppure porte aperte troppo a lungo
        print('ALARM')
        if float(val) > -15:
            print(val)
        elif opening_duration > 20:
            print(opening_duration)
        doc_ref_2 = db.collection('alarms').document(s) #mi fornisce riferimento all'entità documento oppure se non c'era me la crea
        entity_2 = doc_ref_2.get() #get mi restituisce l'entità vera e propria dandogli il riferimento
        val_2 = request.values['Date']+' '+request.values['Time']+' '+str(val)
        print(val_2)
        if entity_2.exists and 'values' in entity_2.to_dict():  # se al sensore s corrispondono già valori allora aggiungi ad essi val
            v_2 = entity_2.to_dict()['values']  # copio i valori
            v_2.append(val_2)  # aggiungo val alla copia dei valori
            doc_ref_2.update({'values': v_2})  # il nuovo value è la copia aggiornata
        else:  # altrimenti crei il dizionario associato con chiave values e valore lista...
            doc_ref_2.set({'values': [val_2]})
    return 'ok', 200

# agli url si accede sia in modalità get che post
# client fa richiesta http al server
@app.route('/sensors/<s>',methods=['GET'])
def get_data(s):
    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    entity = db.collection('sensors').document(s).get() #accedo al documento
    if entity.exists:
        return json.dumps(entity.to_dict()['values']), 200
    else:
        return 'sensor not found', 404

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
            d.append([t,x])
            t += 1
        return render_template('graph.html', sensor=s, data=json.dumps(d))
        # gli passo una pagina html
    else:
        return redirect(url_for('static', filename='sensor404.html'))

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('/main'))
    username = request.values['u']
    password = request.values['p']

    db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
    user = db.collection('utenti').document(username).get()
    if user.exists and user.to_dict()['password']==password:
        login_user(User(username))
        next_page = request.args.get('next')
        if not next_page:
            next_page = '/main'
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
            username = request.values['u']
            password = request.values['p']
            db = firestore.Client.from_service_account_json('credentials.json') if local else firestore.Client()
            user = db.collection('utenti').document(username)
            user.set({'username':username, 'password':password})
            return 'ok'
    else:
        return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

