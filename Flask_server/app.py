from flask import Flask, render_template, request, redirect, url_for, Response
from flask_socketio import SocketIO, emit
import mysql.connector
import random, json
from threading import Thread
import time
from flask import current_app
import requests
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Database connection details
db_host = 'localhost'
db_user = 'root'
db_password = 'Gsw@1924'
db_name = 'esamproject'

data = {'voltage1': 0, 'current1': 0, 'energy1': 0, 'voltage2': 0, 'current2': 0, 'energy2': 0, 'voltage3': 0, 'current3': 0, 'energy3': 0}
data_1 = {'voltage1': 0, 'current1': 0, 'energy1': 0, 'voltage2': 0, 'current2': 0, 'energy2': 0, 'voltage3': 0, 'current3': 0, 'energy3': 0, 'total_energy':0}
state={'button_id':'load1', 'status':'OFF'}
mode={'mode':'Manual'}
# Function to validate user credentials
def validate_user(username, password):
    # Create a database connection
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    # Execute the query to check if the user exists
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    
    # Fetch the result
    result = cursor.fetchone()
    
    # Close the cursor and database connection
    cursor.close()
    conn.close()
    
    # Return True if user exists, False otherwise
    if result:
        return True
    else:
        return False

@app.route('/')
def login():
    return render_template('login.html')

# Route to handle the login page
@app.route('/login', methods=['GET', 'POST'])
def handle_login():
    if request.method == 'POST':
        # Get the username and password from the form
        username = request.form['username']
        password = request.form['password']
        
        # Validate the user credentials
        if validate_user(username, password):
            return redirect(url_for('home'))
        else:
            return 'Invalid Credentials'
    else:
        return render_template('login.html')
        
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/receive_data', methods=['POST'])
def receive_data():
    global data
    data = request.get_json()
    print(data)  # Do something with the received data
    # Extract individual values
    return 'Data received successfully'

def send_data():
    # Send random voltage, current, and energy values
    global data
    voltage1 = data['voltage1']
    current1 = data['current1']
    energy1 = data['energy1']
    voltage2 = data['voltage2']
    current2 = data['current2']
    energy2 = data['energy2']
    voltage3 = data['voltage3']
    current3 = data['current3']
    energy3 = data['energy3']
    total_energy = energy1+ energy2 + energy3
    total_energy = round(total_energy, 3)

    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    # Execute the query to check if the user exists
    query = "INSERT INTO measurements (voltage1, current1, energy1, voltage2, current2, energy2, voltage3, current3, energy3, total_energy ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (voltage1, current1, energy1, voltage2, current2, energy2, voltage3, current3, energy3, total_energy))
    conn.commit()
    rowcount=cursor.rowcount
    print(f"{rowcount} row(s) affected")

    cursor.close()
    conn.close()
    data_1 = data.copy()  # Create a copy of the original data dictionary
    data_1.update({'total_energy': total_energy})
    with app.app_context():
        try:
            socketio.emit('data', data_1)
        except RuntimeError:
            current_app.logger.error('Unable to emit data to SocketIO clients.')
        time.sleep(1)
    # Schedule the next data send in 1 second
    socketio.start_background_task(send_data)

@app.route('/get_data', methods=['GET'])
def get_data():
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = connection.cursor(dictionary=True)
    query = "SELECT id,voltage1,current1,energy1,voltage2,current2,energy2,voltage3,current3,energy3 FROM measurements ORDER BY id DESC LIMIT 100"  # Update with your table name and column names
    cursor.execute(query)
    data = cursor.fetchall()
    connection.commit()
    connection.close()
    json_data = json.dumps(data)
    return Response(json_data, content_type='application/json')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    t1 = Thread(target=send_data)
    t1.daemon = True
    t1.start()

@socketio.on('send_status')
def handle_send_status(state):
    id = None
    button_id = state['button_id']
    status=state['status']
    # Process the received status
    # For example:
    if button_id == 'load1':
        # Do something for Load 1 with the received status
        id = "relay1"
        pass
    elif button_id == 'load2':
        # Do something for Load 2 with the received status
        id = "relay2"
        pass
    elif button_id == 'load3':
        # Do something for Load 3 with the received status
        id = "relay3"
        pass
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = conn.cursor()
    query = "UPDATE loads SET state = %s WHERE Load_id = %s"
    cursor.execute(query, (status, button_id))
    conn.commit()
    cursor.close()
    conn.close()
    print(state)
    send_relay_state(id, status)

@socketio.on('send_mode')
def handle_send_mode(mode):
    Mode=mode['mode']
    print(Mode)
    send_mode_control(Mode)

@socketio.on('list_order')
def handle_list_order(jsonData):
    data_list = json.loads(jsonData)
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = conn.cursor()
    query = "UPDATE priority SET Load_id = %s WHERE id = %s"
    # Iterate over the data_list and update each row in the table
    for i, item in enumerate(data_list, start=1):
        cursor.execute(query, (item, i))
    conn.commit()
    cursor.close()
    conn.close()
    url = 'http://192.168.43.67:5000/endpoint'
    priority_list = {'id': 'priority_list'}
    priority_list.update({'priority_' + str(i): load_id for i, load_id in enumerate(data_list, start=1)})
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=priority_list, headers=headers)
    
    if response.status_code == 200:
        print('sent successfully to Python 2 server')
    else:
        print('Failed to send  to Python 2 server')
    # Process the received list order data
    # For example, you can print it or perform any other desired action
    print(priority_list)

def send_relay_state(id, stage):
    url = 'http://192.168.43.67:5000/endpoint'
    payload = {'id':id, 'state': stage}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print('Relay state sent successfully to Python 2 server')
    else:
        print('Failed to send relay state to Python 2 server')

def send_mode_control(modes):
    url = 'http://192.168.43.67:5000/endpoint'
    load = {'id':'mode', 'mode': modes}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=load, headers=headers)
    
    if response.status_code == 200:
        print('mode state sent successfully to Python 2 server')
    else:
        print('Failed to send relay state to Python 2 server')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

