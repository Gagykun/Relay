import mysql.connector
import random
import string
import hashlib
import logging
from flask import Flask, render_template, request, jsonify, session
from mysql.connector import IntegrityError
from waitress import serve
from datetime import datetime

# Set the logging level to DEBUG
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_url_path='/static', static_folder='static')  # Configure static file serving
print("Serving...")

database_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'apassword',  # No password for testing purposes
    'database': 'relay',
}

# Function to generate UUID-like string
def generate_random_string(length):
    return ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for _ in range(length))

# Function to hash the password
def hash_password(password):
    salt = generate_random_string(16)
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    return salt, hashed_password

# Function to insert user data into the database
from mysql.connector import IntegrityError

# Function to check user credentials for login
def check_user_credentials(username, password):
    conn = mysql.connector.connect(**database_config)
    cursor = conn.cursor()

    try:
        # SQL query to fetch user data for the provided username
        query = "SELECT userID, username, password, salt FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user_data = cursor.fetchone()

        if user_data:
            # If user exists, verify the provided password
            _, hashed_password = hash_password(password + user_data[3])  # Use stored salt
            if hashed_password == user_data[2]:
                return {'userID': user_data[0], 'username': user_data[1]}

    finally:
        cursor.close()
        conn.close()

    return None

# Function to insert user data into the database
def insert_user_data(user_data):
    # Establish a database connection
    conn = mysql.connector.connect(**database_config)
    cursor = conn.cursor()

    try:
        # Generating a random UUID-like string with 25 characters
        user_data['userID'] = generate_random_string(25)

        # Hash the password before storing it
        salt, hashed_password = hash_password(user_data['password'])
        
        # SQL query to insert user data
        insert_query = """
        INSERT INTO users
        (userID, username, password, salt, email, userJoinDate, lastLogin, userStatus)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Execute the SQL query with user data
        cursor.execute(insert_query, (
            user_data['userID'],   # userID
            user_data['username'], # username
            hashed_password,       # password
            salt,                  # salt
            user_data['email'],    # email
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),   # userJoinDate
            None,                  # lastLogin
            'offline',             # userStatus
        ))

        # Commit the changes to the database
        conn.commit()

    except IntegrityError as e:
        error_message = str(e)
        mysql_error_code = e.errno

        if mysql_error_code == 1062:
            # Extract the violated key from the error message
            violated_key_start = error_message.find("Duplicate entry '") + len("Duplicate entry '")
            violated_key_end = error_message.find("' for key '")
            violated_key = error_message[violated_key_start:violated_key_end]

            # Determine if the violated key corresponds to 'username' or 'email'
            if 'username' in violated_key:
                field_name = 'username'
            elif 'email' in violated_key:
                field_name = 'email'
            else:
                field_name = 'field'

            # Clean up the field name for better user presentation
            cleaned_field_name = field_name.replace('_', ' ').replace('"', '').replace("'", '').replace('\\', '').capitalize()

            # Raise a custom exception for duplicate entry error
            raise DuplicateEntryError(f'The {cleaned_field_name} "{violated_key}" is already taken. Perhaps try logging in?')

        else:
            # Re-raise the IntegrityError for other cases
            raise e

    except Exception as e:
        # Handle other exceptions
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

    finally:
        # Close the cursor and database connection
        cursor.close()
        conn.close()


# Custom exception for duplicate entry error
class DuplicateEntryError(Exception):
    pass

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register_user():
    try:
        user_data = request.form.to_dict()
        insert_user_data(user_data)
        return jsonify({'message': 'User registered successfully'}), 201

    except DuplicateEntryError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Route for user login
@app.route('/login', methods=['POST'])
def login_user():
    try:
        login_data = request.form.to_dict()
        username = login_data.get('loginUsername')  # Updated to match form field
        password = login_data.get('loginPassword')

        # Check user credentials
        user_info = check_user_credentials(username, password)

        if user_info:
            # Set session data upon successful login
            session['user_id'] = user_info['userID']
            session['username'] = user_info['username']

            return jsonify({'message': 'Login successful'}), 200
        else:
            error_message = 'Invalid credentials. Please check your username and password.'
            return render_template('index.html', login_error=error_message)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
if __name__ == '__main__':
    # Use Waitress instead of Flask's development server
    serve(app, host='0.0.0.0', port=5000)