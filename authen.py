import argparse
import platform    
import json
from subprocess import Popen, PIPE
import shutil
import getpass
import signal
import time
import requests
import sys
import os

username = ''
password = ''
ipAddress= ''
acip="10.252.13.10"
umac = '7486e2507746'
time_repeat = 10  # seconds
max_login_attempt = 20

client_ip = ''
server_url = 'https://portal.kmitl.ac.th:19008/portalauth/login'
data = ''
agent = requests.session()


# handle Ctrl+C
def signal_handler(signal, frame):
    print_format('Good bye!', end='\n')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# determine terminal size
large_terminal = True
column, line = shutil.get_terminal_size()
if column < 108:
    large_terminal = False


# arguments parser
parser = argparse.ArgumentParser(
    description='Automatically authenticate into KMITL network system.')
parser.add_argument('-u', '--username', dest='username',
                    help='username without @kmitl.ac.th (usually student ID)')
parser.add_argument('-p', '--password', dest='password', help='password')
parser.add_argument('-ip', '--IpAddress', dest='ipAddress', help='ipAddress')
parser.add_argument('-i', '--interval', dest='interval', type=int,
                    help='heartbeat interval in second (default: {} seconds)'.format(time_repeat))
parser.add_argument('--max-login-attempt', dest='max_attempt', type=int,
                    help='maximum login attempt (default: {} times)'.format(max_login_attempt))
parser.add_argument('--config', dest='config', action='store_const',
                    const=True, default=False, help='create config file')

def print_format(*args, large_only=False, small_only=False, show_time=True, end='\n\n', **kwargs):
    if (large_only and not large_terminal) or (small_only and large_terminal):
        return

    if large_terminal:
        print('\t', end='')
    if show_time:
        print(time.asctime(time.localtime()), '[x]', end=' ')
    print(*args, **kwargs, end=end)


def print_error(*args, **kwargs):
    print_format(*args, **kwargs, end='\n')
    #sys.exit(1)


def init():
    logo = '''
         ██████╗███████╗    ██╗  ██╗ ██████╗ ██╗   ██╗███████╗███████╗
        ██╔════╝██╔════╝    ██║  ██║██╔═══██╗██║   ██║██╔════╝██╔════╝
        ██║     █████╗      ███████║██║   ██║██║   ██║███████╗█████╗  
        ██║     ██╔══╝      ██╔══██║██║   ██║██║   ██║╚════██║██╔══╝  
        ╚██████╗███████╗    ██║  ██║╚██████╔╝╚██████╔╝███████║███████╗
         ╚═════╝╚══════╝    ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝
                                                              
'''
    print_format(logo, large_only=True, show_time=False)
    print_format('\nCE-HOUSE', small_only=True, show_time=False)

def login():
    global data

    try:
        url = server_url
        content = agent.post(url,params={'userName': username, 'userPass': password,'uaddress': ipAddress,'umac':umac,'agreed':1,'acip':acip,'authType':1})
    except requests.exceptions.RequestException:
        print_format('Connection lost...')
        time.sleep(1)
        return
    content_dict = json.loads(content.text)

    # check if request is successful
    if not content_dict['success']:
        print_error('Error! Something went wrong (maybe too many attempt?)...')

    data = content_dict['data']

    if content.status_code != 200:
        print_error(
            'Error! Something went wrong (maybe wrong username and/or password?)...')
    elif content.status_code == 200:
        print("HeartBeat is OK")
def checkConnection():
    command = "ping"
    arguments = []
    if platform.system().lower()=='windows':
        arguments = ["-n", "3", "google.com"]
    else:
        arguments = ["-c", "3", "google.com"]
    process = Popen([command] + arguments, stdout=PIPE, stderr=PIPE, text=True)
    stdout, stderr = process.communicate()
    if("TTL=" in stdout):
        return False
    elif stderr:
        return False
    else:
        return True

def start():
    login_attempt = 0
    printed_logged_in = False
    while True:
        connection = checkConnection()
        if(connection):
            if not printed_logged_in:  # print only when log in successful
                print_format('Welcome {}!'.format(username), end='\n')
                print_format('Your IP:', ipAddress, end='\n')
                print_format('Heatbeat every', time_repeat, 'seconds')
                print_format('Max login attempt:', max_login_attempt)
                printed_logged_in = True
            login()
            time.sleep(time_repeat)
        else:
            login()
            login_attempt += 1
        time.sleep(10)

def create_config():
    input_username = input('Your username (mostly student ID): ')
    input_password = getpass.getpass('Your password: ')
    input_yourIp = input('Your PublicIp: ')

    data = {}
    if input_username != '':
        data.update({'username': input_username})
    if input_password != '':
        data.update({'password': input_password})
    if input_yourIp != '':
        data.update({'ipAddress': input_yourIp})

    with open('config.json', 'w') as config_file:
        json.dump(data, config_file, indent=4)

if __name__ == '__main__':
    # get arguments
    args = parser.parse_args()
    if args.config:
        create_config()

    if not os.path.isfile('config.json'):
        try:
            to_create = input(
                'Cannot found \'config.json\', do you want to create a new one? (Y/n): ').lower()
            if to_create not in ['n', 'no']:
                create_config()
        except EOFError:
            print('\nGood bye!')
            sys.exit(0)

    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            if 'username' in config:
                username = config['username']
            if 'password' in config:
                password = config['password']
            if 'ipAddress' in config:
                ipAddress = config['ipAddress']
    except FileNotFoundError:
        pass

    # get username and password from args
    if args.username is not None:
        username = args.username
    if args.password is not None:
        password = args.password

    # get heartbeat interval from args
    if args.ipAddress is not None:
        ipAddress = args.ipAddress

    # get maximum login attempt from args
    if args.max_attempt is not None:
        max_login_attempt = args.max_attempt

    # check if username and password are provided
    if username == '' or password == '' or username is None or password is None or ipAddress == '' or ipAddress is None:
        print('Error! Please provide username and password...')
        sys.exit(1)

    init()

    print_format('Logging in with username \'{}\'...'.format(username))

    while True:
        start()
