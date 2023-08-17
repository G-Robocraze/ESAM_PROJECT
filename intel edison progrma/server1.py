import random
import time
import httplib
import json
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

voltage1 = 0
current1 = 0
energy1 = 0
voltage2 = 0
current2 = 0
energy2 = 0
voltage3 = 0
current3 = 0
energy3 = 0
relay_state1 = 1
relay_state2 = 1
relay_state3 = 1
relay_id = None
load_1 =0
load_2 =0
load_3 = 0
operation_mode = 'Manual'
priority_list = ['load1','load2','load3']  # Priority list to be updated from Flask server
energy_limit = 200  # Set your desired energy limit here

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global voltage1, current1, energy1, voltage2, current2, energy2, voltage3, current3, energy3, relay_state1, relay_state2, relay_state3, relay_id, priority_list, operation_mode
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)
        json_data = json.loads(data)
        #print(json_data)  # Process the received JSON data as desired

        if json_data.get('id') == 'load1':
            voltage1 = json_data.get('voltage')
            current1 = json_data.get('current')
            energy1 = json_data.get('power')
        elif json_data.get('id') == 'load2':
            voltage2 = json_data.get('voltage')
            current2 = json_data.get('current')
            energy2 = json_data.get('power')
        elif json_data.get('id') == 'load3':
            voltage3 = json_data.get('voltage')
            current3 = json_data.get('current')
            energy3 = json_data.get('power')
        elif json_data.get('id') == 'mode':
            operation_mode = json_data.get('mode')
            print(operation_mode)
        elif json_data.get('id') == 'relay1':
            relay_stage = json_data.get('state')
            print(relay_stage)
            relay_id = 'relay1'
            if relay_stage == "ON":
                relay_state1 = 1
            elif relay_stage == "OFF":
                relay_state1 = 0
        elif json_data.get('id') == 'relay2':
            relay_id = 'relay2'
            relay_stage = json_data.get('state')
            #print(relay_stage)
            if relay_stage == "ON":
                relay_state2 = 1
            elif relay_stage == "OFF":
                relay_state2 = 0
        elif json_data.get('id') == 'relay3':
            relay_id = 'relay3'
            relay_stage = json_data.get('state')
            #print(relay_stage)
            if relay_stage == "ON":
                relay_state3 = 1
            elif relay_stage == "OFF":
                relay_state3 = 0
        elif json_data.get('id') == 'priority_list':
            next_priorities = []
            for i in range(1, len(json_data)):
                priority_key = 'priority_' + str(i)
                priority_load = json_data.get(priority_key)
                if priority_load:
                    next_priorities.append(priority_load)
            #print("Next priorities:", next_priorities)
            priority_list.extend(next_priorities)
            #print("Updated priority list:", priority_list)


        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        global relay_state1, relay_state2, relay_state3, relay_id
        if self.path == '/endpoint/state':
            response_data = {
                'relay1': relay_state1,
                'relay2': relay_state2,
                'relay3': relay_state3
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

def run_server():
    server_address = ('', 5000)
    httpd = HTTPServer(server_address, RequestHandler)
    print('Starting server on port 5000...')
    httpd.serve_forever()

def send_data():
    global voltage1, current1, energy1, voltage2, current2, energy2, voltage3, current3, energy3
    while True:
        data = {
            'voltage1': voltage1,
            'current1': current1,
            'energy1': energy1,
            'voltage2': voltage2,
            'current2': current2,
            'energy2': energy2,
            'voltage3': voltage3,
            'current3': current3,
            'energy3': energy3
        }

        # Convert data to JSON format
        json_data = json.dumps(data)

        # Send the data to the server
        conn = httplib.HTTPConnection('192.168.43.244', 5000)
        headers = {'Content-type': 'application/json'}
        conn.request('POST', '/receive_data', json_data, headers)
        response = conn.getresponse()

        if response.status == 200:
            #print('Data sent successfully')
            flag=0
        else:
            print('Failed to send data')

        conn.close()

        time.sleep(1)  # Delay for 1 second before sending the next data

def manage_loads():
    global energy_limit, priority_list, relay_state1, relay_state2, relay_state3, load_1, load_2,load_3, energy1, energy2, energy3, operation_mode

    def cut_load(load_id):
        global relay_state1, relay_state2, relay_state3, load_1, load_2, load_3

        if load_id == 'load1' and relay_state1 == 1:
            relay_state1 = 0
            load_1 = energy1
            print("Turning off load1")
        elif load_id == 'load2' and relay_state2 == 1:
            relay_state2 = 0
            load_2 = energy2
            print("Turning off load2")
        elif load_id == 'load3' and relay_state3 == 1:
            relay_state3 = 0
            load_3 = energy3
            print("Turning off load3")

    def activate_load(load_id):
        global relay_state1, relay_state2, relay_state3, load_1, load_2, load_3

        if load_id == 'load1' and relay_state1 == 0:
            relay_state1 = 1
            load_1 = 0
            print("Turning on load1")
        elif load_id == 'load2' and relay_state2 == 0:
            relay_state2 = 1
            load_2 = 0
            print("Turning on load2")
        elif load_id == 'load3' and relay_state3 == 0:
            relay_state3 = 1
            load_3 = 0
            print("Turning on load3")

    while True:
        if operation_mode == 'Auto':    
            LOAD_REDUCTION_AMOUNT = load_1 + load_2 + load_3
            total_energy = energy1 + energy2 + energy3
            print("total_energy: ", total_energy )

            if total_energy > energy_limit:
                print("Auto operation started")
                # Excess load detected, start shedding loads
                for load_id in reversed(priority_list):
                    cut_load(load_id)
                    total_energy -= globals()['energy' + load_id[-1]]
                    time.sleep(1)

                    if total_energy <= energy_limit:
                        break

            elif total_energy + LOAD_REDUCTION_AMOUNT <= energy_limit:
                # Remaining load decreased by a certain amount, start restoring loads
                for load_id in (priority_list):
                    if globals()['energy' + load_id[-1]] <= energy_limit - total_energy:
                        activate_load(load_id)
                        total_energy += globals()['energy' + load_id[-1]]
            print(load_1 ,':', load_2,':', load_3)
            if total_energy+load_1 <= energy_limit:
                activate_load('load1')
                print("Activating Load1")
                time.sleep(1)
            if total_energy+load_2 <= energy_limit:
                activate_load('load2')
                print("Activating Load2")
                time.sleep(1)
            if total_energy+load_3 <= energy_limit:
                activate_load('load3')
                print("Activating Load3")
                time.sleep(1)

            time.sleep(1)  # Delay for 1 second before checking again

if __name__ == '__main__':
    # Start the server in a separate thread
    import threading
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Start sending data
    send_data_thread = threading.Thread(target=send_data)
    send_data_thread.daemon = True
    send_data_thread.start()

    # Start load management
    manage_loads_thread = threading.Thread(target=manage_loads)
    manage_loads_thread.daemon = True
    manage_loads_thread.start()

    while True:
        time.sleep(1)
