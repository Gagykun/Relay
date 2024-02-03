import mysql.connector
import random
import hashlib
from config import Config  # Contains secret key
from flask import Flask, render_template, request, jsonify, session
from mysql.connector import IntegrityError
from waitress import serve
from datetime import datetime

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config.from_object(Config)

print("Serving...")

database_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'apassword',  # No password for testing purposes
    'database': 'relay',
}

def generate_random_string(length):
    return ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for _ in range(length))

def hash_password(password):
    salt = generate_random_string(16)
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    return salt, hashed_password

def check_user_credentials(username, password):
    conn = mysql.connector.connect(**database_config)
    cursor = conn.cursor()

    try:
        query = "SELECT userID, username, password, salt FROM users WHERE username = %s"
        cursor.execute(query, (username,))
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
    conn = mysql.connector.connect(**database_config)
    cursor = conn.cursor()

    try:
        user_data['userID'] = generate_random_string(25)
        salt, hashed_password = hash_password(user_data['password'])

        insert_query = """
        INSERT INTO users
        (userID, username, password, salt, email, userJoinDate, lastLogin, userStatus)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            user_data['userID'],
            user_data['username'],
            hashed_password,
            salt,
            user_data['email'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            None,
            'offline',
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
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/nojavascript.html')
def no_javascript():
    return render_template('nojavascript.html')

@app.route('/register', methods=['POST'])
def register_user():
    try:
        username = request.form.get('loginUsername')
        password = request.form.get('loginPassword')
        email = request.form.get('email')

        user_data = {'username': username, 'password': password, 'email': email}

        insert_user_data(user_data)

        return jsonify({'message': 'User registered successfully'}), 201

    except DuplicateEntryError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

@app.route('/login', methods=['POST'])
def login_user():
    try:
        login_data = request.form.to_dict()
        username = login_data.get('loginUsername')
        password = login_data.get('loginPassword')

        user_info = check_user_credentials(username, password)

        if user_info:
            session['user_id'] = user_info['userID']
            session['username'] = user_info['username']

            return jsonify({'message': 'Login successful'}), 200
        else:
            error_message = 'Invalid credentials. Please check your username and password.'
            return jsonify({'error': error_message}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # serve(app, host='0.0.0.0', port=5000)  # Waitress
    app.run(debug=True)  # Debug
