import mysql.connector
import requests
import hashlib
import logging
import traceback
import os
from config import secretKey, connectionInfo, RandomAPI, GenID # config.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask import Flask, render_template, request, jsonify, session, send_file
from mysql.connector import IntegrityError
#from waitress import serve
from datetime import datetime
from flask import request, jsonify
from threading import Lock

# Arbitrary IP Blocking

from flask import request, jsonify
from functools import wraps
import logging

# Define the path to the "static" folder
STATIC_FOLDER = os.path.join(os.path.expanduser("~"), 'RelayServerStuff', 'static')
DEFAULT_PFP_PATH = os.path.join(STATIC_FOLDER, 'default_pfp.jpg')
print("STATIC_FOLDER: ", STATIC_FOLDER)
print("DEFAULT_PFP_PATH: ", DEFAULT_PFP_PATH)

def ip_check(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # Get the IP address of the client
        ip_address = request.remote_addr

        # Check if the IP address starts with "10.0.0."
        if not ip_address.startswith("10.0.0."):
            # Log the IP address
            logging.warning(f"Unauthorized access attempt from IP: {ip_address}")

            # Return a 401 status code
            return jsonify({'error': 'Unauthorized access detected. You have been banned for tampering with Department of Justice property. An official investigation is underway.'}), 401 # Get troll'd :P

        # If the IP address is valid, call the original function
        print("Local IP Address: ", ip_address)
        return func(*args, **kwargs)

    return decorated_function

# End of Arbitrary IP Blocking

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config.from_object(secretKey)
limiter = Limiter(app=app, key_func=get_remote_address)

# All database information is now stored in config.py for security
db_config = connectionInfo.database_config
host = connectionInfo.database_config['host']
user = connectionInfo.database_config['user']
password = connectionInfo.database_config['password']
database = connectionInfo.database_config['database']

# This will store the messages, each message is a dict with 'userID' and 'message' keys
messages = []
# This is to ensure thread-safety when accessing the shared 'messages' list
lock = Lock()

def generate_random_string(length):
    # Use RANDOM.org for true randomness
    api = RandomAPI()
    api_response = requests.post(api.api_base, json=api.api_data)
    api_response_data = api_response.json()
    api_response_uuid = api_response_data['result']['random']['data'][0]
    return api_response_uuid

def sessionIDGen(userID):
    gen_id = GenID()
    session_id = gen_id.generate_key()

    conn = mysql.connector.connect(**connectionInfo.database_config)
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE users SET sessionID = %s WHERE userID = %s", (session_id, userID))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return session_id

def hash_password(password):
    salt = generate_random_string(16)
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    return salt, hashed_password

def check_user_credentials(username_or_email, password):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        query = "SELECT userID, username, password, salt FROM users WHERE username = %s OR email = %s"
        cursor.execute(query, (username_or_email, username_or_email))
        user_data = cursor.fetchone()

        if user_data:
            hashed_password = hashlib.sha256((password + user_data[3]).encode()).hexdigest()
            if hashed_password == user_data[2]:
                return {'userID': user_data[0], 'username': user_data[1]}

    finally:
        cursor.close()
        conn.close()

    return None

class DuplicateEntryError(Exception):
    pass

def insert_user_data(user_data):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    if user_data['username'] == '' or user_data['password'] == '' or user_data['email'] == '' or user_data['username'] == None or user_data['password'] == None or user_data['email'] == None:
        print("Bad request")
        return jsonify({'error': 'Bad request'}), 400

    try:
        user_data['userID'] = generate_random_string(25)
        salt, hashed_password = hash_password(user_data['password'])

        insert_query = """
        INSERT INTO users
        (userID, sessionID, password, salt, userName, email, userJoinDate, lastLogin, userStatus, profilePicture, userBio, friends)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """


        cursor.execute(insert_query, (
            user_data['userID'], # userID
            None, # sessionID
            hashed_password, # password
            salt, # salt
            user_data['username'], # userName
            user_data['email'], # email
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # userJoinDate
            None,
            'offline', # userStatus
            None, # profilePicture
            None, # userBio
            None # friends
        ))

        conn.commit()

    except IntegrityError as e:
        error_message = str(e)
        mysql_error_code = e.errno

        if mysql_error_code == 1062:
            violated_key_start = error_message.find("Duplicate entry '") + len("Duplicate entry '")
            violated_key_end = error_message.find("' for key '")
            violated_key = error_message[violated_key_start:violated_key_end]

            if 'username' in violated_key:
                field_name = 'username'
            elif 'email' in violated_key:
                field_name = 'email'
            else:
                field_name = 'field'

            cleaned_field_name = field_name.replace('_', ' ').replace('"', '').replace("'", '').replace('\\', '').capitalize()

            raise DuplicateEntryError(f'The {cleaned_field_name} "{violated_key}" is already taken. Perhaps try logging in?')

        else:
            raise e

    except Exception as e:
        print(f'An unexpected error occurred: {str(e)}')
        traceback.print_exc()

    finally:
        cursor.close()
        conn.close()

socketio = SocketIO(app)

@app.route('/')
@ip_check
def home():
    return render_template('index.html')

@app.route('/nojavascript.html')
@ip_check
def no_javascript():
    return render_template('nojavascript.html')

@app.route('/register', methods=['POST'])
@ip_check
#@limiter.limit("1/days") # Limit to 1 registration per day
def register_user():
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        # Check if any of the required fields are missing
        if not (username and password and email):
            raise ValueError("Missing required fields: username, password, or email")

        # Insert user data into the database
        user_data = {'username': username, 'password': password, 'email': email}
        insert_user_data(user_data)
        print("User registered successfully")
        print(user_data)

        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        # Log the traceback for debugging purposes
        traceback.print_exc()
        print(f"Error during user registration: {e}")
        return jsonify({'error': 'An error occurred during user registration'}), 500

@app.route('/login', methods=['POST'])
@ip_check
#@limiter.limit("15/hour") # Limit to 15 login attempts per hour
def login_user():
    try:
        login_data = request.form.to_dict()
        username = login_data.get('loginUsername')
        password = login_data.get('loginPassword')

        user_info = check_user_credentials(username, password)

        if user_info:
            session['user_id'] = user_info['userID']
            session['username'] = user_info['username']
            session['userStatus'] = "online"

            # Update userStatus, lastLogin in the database
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE users SET lastLogin = %s WHERE userID = %s", (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_info['userID']))
                cursor.execute("UPDATE users SET userStatus = 'online' WHERE userID = %s", (user_info['userID'],))
                conn.commit()
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            finally:
                cursor.close()
                conn.close()

            return jsonify({
                'message': 'Login successful',
                'SID': sessionIDGen(user_info['userID']),
                'username': user_info['username'],
                'userID': user_info['userID']
                }), 200
        else:
            return jsonify({'error': 'Unauthorized'}), 401  # Unauthorized

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/fetch_friends', methods=['POST'])
@ip_check
def fetch_friends():
    try:
        user_id = request.form.get('userID')

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            # Assuming the 'friends' column contains comma-separated userIDs of friends
            cursor.execute("SELECT friends FROM users WHERE userID = %s", (user_id,))
            friends_data = cursor.fetchone()
            print("Friends data:", friends_data[0])
            if friends_data:
                friends = friends_data[0].split(',')
            else:
                friends = []
        except Exception as e:
                return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()

        return jsonify({'friends': friends}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/fetch_username', methods=['POST'])
@ip_check
def fetch_username():
    try:
        user_id = request.form.get('userID')
        print("User ID:", user_id)
        if not user_id:
            return jsonify({'error': 'User ID not provided in the request.'}), 400
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT username FROM users WHERE userID = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                username = result[0]
            else:
                # Handle the case when the user ID doesn't exist
                return jsonify({'error': f'User with ID {user_id} not found.'}), 404
        except Exception as e:
            # Print detailed error information to the terminal
            print("Error fetching username:", str(e))
            return jsonify({'error': 'Internal server error occurred. Check server logs for details.'}), 500
        finally:
            cursor.close()
            conn.close()
        return jsonify({'username': username}), 200
    except Exception as e:
        # Print detailed error information to the terminal
        print("Exception occurred:", str(e))
        return jsonify({'error': 'Internal server error occurred. Check server logs for details.'}), 500

@app.route('/fetchPFP', methods=['POST'])
@ip_check
def fetch_user_pfp():
    try:
        user_id = request.form.get('userID')

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT profilePicture FROM users WHERE userID = %s", (user_id,))
            result = cursor.fetchone()
            if result is None or result[0] is None or result[0] == "":
                print("No profile picture found for user", user_id)
                profile_picture_path = DEFAULT_PFP_PATH
            else:
                profile_picture_filename = result[0]  # Now it's just "{userID}.jpg"
                print("Profile picture found for user", user_id, "with filename", profile_picture_filename)
                # Construct the full file path
                profile_picture_path = os.path.join(STATIC_FOLDER, profile_picture_filename)
                # Check if the file exists
                if not os.path.exists(profile_picture_path):
                    print("Profile picture file does not exist:", profile_picture_path)
                    profile_picture_path = DEFAULT_PFP_PATH
        finally:
            cursor.close()
            conn.close()

        return send_file(profile_picture_path, mimetype='image/jpeg')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/send_message', methods=['POST'])
@ip_check
#@limiter.limit("25/minute") # Limit to 25 messages per minute
def send_message():
    try:
        # Parse the JSON data from the request
        data = request.json
        print(data)
        user_id = data.get('userID')
        recipient_id = data.get('recipientID')
        message = data.get('message')

        if not user_id:
            return jsonify({'error': 'You must be logged in to send a message'}), 401

        # Insert the message into the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO messages (userID, recipientID, message) VALUES (%s, %s, %s)", (user_id, recipient_id, message))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        try:
            # Broadcast the message to recipient
            print("sent message to recipient: ", recipient_id)
            socketio.emit('message', {'userID': user_id, 'message': message})#, room=recipient_id)
        except Exception as e:
            print(f"An error occurred: {e}")

        return jsonify({'success': 'Message sent'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/fetch_messages', methods=['POST'])
@ip_check
def fetch_messages():
    try:
        user_id = request.form.get('userID')
        recipient_id = request.form.get('recipientID')

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT userID, message FROM messages WHERE (userID = %s AND recipientID = %s) OR (userID = %s AND recipientID = %s) ORDER BY id", (user_id, recipient_id, recipient_id, user_id))
            messages_data = cursor.fetchall()
            print(messages_data)
        finally:
            cursor.close()
            conn.close()

        print("Fetched", len(messages_data), "messages for user", user_id, "and recipient", recipient_id)
        messages = [{'userID': message[0], 'message': message[1]} for message in messages_data]
        return jsonify({'messages': messages}), 200

    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({'error': str(e), 'traceback': tb}), 500

@app.route('/logout', methods=['POST'])
@ip_check
def logout():
    try:
        user_id = request.form.get('userID')

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET userStatus = 'offline' WHERE userID = %s", (user_id,))
            cursor.execute("UPDATE users SET sessionID = NULL WHERE userID = %s", (user_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        session.clear()

        return jsonify({'message': 'Logout successful'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/user_idle', methods=['POST'])
@ip_check
def user_idle():
    try:
        user_id = request.form.get('userID')

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET userStatus = 'idle' WHERE userID = %s", (user_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return jsonify({'message': 'User status set to idle'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/user_online', methods=['POST'])
@ip_check
def user_online():
    try:
        user_id = request.form.get('userID')

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET userStatus = 'online' WHERE userID = %s", (user_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return jsonify({'message': 'User status set to online'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # serve(app, host='0.0.0.0', port=5000)  # Waitress
    socketio.run(app, host='10.0.0.108', port=5000, debug=True)  # Debug
