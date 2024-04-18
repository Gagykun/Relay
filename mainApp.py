import sys
import requests
import pyautogui
import socketio
import traceback
import json
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from login import Ui_LoginWindow  # Login Window
from mainTest import Ui_MainWindow  # Chat Window

base_api_url = "http://10.0.0.108:5000/" # The base URL for the API
WS_URL = "ws://10.0.0.108:5000" # The WebSocket URL
api_mode = "login" # The default API mode

# Setup SocketIO
sio = socketio.Client()
sio.connect(WS_URL)


class LoginWindow(QtWidgets.QMainWindow, Ui_LoginWindow): # The not so head honcho, the login window
    def __init__(self, *args, **kwargs):
        super(LoginWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.usernameField.setVisible(False)
        self.emailField.setPlaceholderText("Email/Username")
        self.LRStatus.setText("")

        def swapMode(args):
            global api_mode
            if api_mode == "register":
                api_mode = "login"
                self.emailField.setPlaceholderText("Email/Username")
                self.usernameField.setVisible(False)
                self.LRConfirmBtn.setText("Login")
                self.LRSwapBtn.setText("New user?")
            else:
                api_mode = "register"
                self.emailField.setPlaceholderText("Email")
                self.usernameField.setVisible(True)
                self.LRConfirmBtn.setText("Register")
                self.LRSwapBtn.setText("Existing user?")

        def LRUser(args):
            global api_mode
            try:
                if api_mode == "register":
                    self.LRStatus.setText("Registering...")
                    register_data = {
                        'username': str(self.usernameField.text()),
                        'password': str(self.passwordField.text()),
                        'email': str(self.emailField.text())
                    }
                    print(register_data)
                    response = requests.post(base_api_url + 'register', data=register_data)
                    response.raise_for_status()
                    self.LRStatus.setText("Account created!")
                    print('User registered successfully')
                else:
                    self.LRStatus.setText("Logging in...")
                    login_data = {'loginUsername': self.emailField.text(), 'loginPassword': self.passwordField.text()}
                    response = requests.post(base_api_url + 'login', data=login_data)
                    response.raise_for_status()
                    print('User logged in successfully')
                    session_id = response.json()['SID']
                    session_user = response.json()['username']
                    session_userID = response.json()['userID']
                    chatWindow.userSessionSetup(session_id, session_user, session_userID)
                    self.LRStatus.setText("Logged in!")
                    loginwindow.hide()
                    chatWindow.show()

                # Check for JSON response errors
                error_message = response.json().get('error')
                if error_message:
                    print("Jsonify Error:", error_message)
                    self.LRStatus.setText(error_message)

            except requests.exceptions.RequestException as req_err:
                print("Request Error:", req_err)
                self.LRStatus.setText("Request Error!")
            except json.JSONDecodeError as json_err:
                print("JSON Decode Error:", json_err)
                self.LRStatus.setText("JSON Decode Error!")
            except Exception as e:
                print("Unhandled error:", e)
                self.LRStatus.setText("Critical Error!")
    

        self.LRConfirmBtn.clicked.connect(LRUser)
        self.LRSwapBtn.clicked.connect(swapMode)

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow): # The head honcho, the main chat window
    new_message_signal = pyqtSignal(dict) # Signal used by PyQT to emit new messages
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.new_message_signal.connect(self.invoke_message_handler) # Connect the signal to the message handler
        global main_window
        main_window = self
        self.setupUi(self)
        self.session_id = None
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self.check_for_idle)
        self.idle_timer.start(5 * 60 * 1000)  # Check for idle every 5 minutes
        self.last_mouse_pos = pyautogui.position()
        self.activity_timer = QTimer() # Timer to check for user activity after idle
        self.activity_timer.timeout.connect(self.check_for_activity)
        self.stackedWidget.setCurrentWidget(self.startPage)
        self.DMFriendsList.setLayout(QtWidgets.QVBoxLayout())
        self.messageTemplate.setVisible(False)
        self.DMFriend.setVisible(False)
        self.scrollAreaLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.pfpCache = {} # Cache for profile pictures to reduce API calls

        # Connect to SocketIO events
        sio.on('message', self.invoke_message_handler)
        sio.on('connect', self.on_connect)
        sio.on('disconnect', self.on_disconnect)
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Enter or event.key() == QtCore.Qt.Key.Key_Return and self.stackedWidget.currentWidget() == self.chatPage:
            self.send_message()
        event.accept()

    def on_connect(self):
        print('Connected to server')

    def on_disconnect(self):
        print('Disconnected from server')

    @QtCore.pyqtSlot(dict) # Decorator to allow the method to accept a dictionary as an argument or else we get mismatching parent errors.
    def invoke_message_handler(self, message):
        try:
            QtCore.QMetaObject.invokeMethod(self, "process_incoming_message", QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(QtCore.QVariant, message))
        except Exception as e:
            self.handle_request_exception(e)


    def create_chat_message_widget(self, username, message, recipientID): # You have no idea how long this took to figure out. I blame sizing. >:(
        messageTemplate = QtWidgets.QWidget(self.scrollAreaContents)
        messageTemplate.setMaximumSize(QtCore.QSize(800, 80))
        messageTemplate.setObjectName("messageTemplate")

        messageGridLayout = QtWidgets.QGridLayout(parent=messageTemplate)
        messageGridLayout.setObjectName("messageGridLayout")

        messageUsername = QtWidgets.QLabel(parent=messageTemplate)
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(9)
        font.setBold(True)
        messageUsername.setFont(font)
        messageUsername.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignVCenter)
        messageUsername.setObjectName("messageUsername")
        messageUsername.setText(username)
        messageGridLayout.addWidget(messageUsername, 0, 1, 1, 1)

        messageContents = QtWidgets.QLabel(parent=messageTemplate)
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(8)
        messageContents.setFont(font)
        messageContents.setObjectName("messageContents")
        messageContents.setText(message)
        messageGridLayout.addWidget(messageContents, 1, 1, 1, 1)

        messagePFP = QtWidgets.QLabel(parent=messageTemplate)
        messagePFP.setMinimumSize(QtCore.QSize(50, 50))
        messagePFP.setMaximumSize(QtCore.QSize(50, 50))
        messagePFP.setText("")
        pixmap = QtGui.QPixmap(self.fetchPFP(recipientID))
        scaled_pixmap = pixmap.scaled(50, 50, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        messagePFP.setPixmap(scaled_pixmap)
        messagePFP.setScaledContents(True)
        messagePFP.setObjectName("messagePFP")
        messageGridLayout.addWidget(messagePFP, 0, 0, 2, 1)

        return messageTemplate

    @QtCore.pyqtSlot(QtCore.QVariant)
    def process_incoming_message(self, message):
        print(message)
        user_id = message['userID']
        username = self.fetch_username(user_id)
        message_text = message['message']
        try:
            recipient_id = message.get('userID')
            message_widget = self.create_chat_message_widget(username, message_text, recipient_id)
            self.scrollAreaLayout.addWidget(message_widget)
            QtCore.QTimer.singleShot(100, lambda: self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum()))
        except Exception as e:
            self.handle_request_exception(e)



    def check_for_idle(self): # Check if the user is idle
        current_mouse_pos = pyautogui.position() # Get the current mouse position
        if current_mouse_pos == self.last_mouse_pos: # If the mouse hasn't moved
            self.set_user_as_idle()
        else:
            self.last_mouse_pos = current_mouse_pos

    def check_for_activity(self): # Check if the user is active
        current_mouse_pos = pyautogui.position()
        if current_mouse_pos != self.last_mouse_pos: # The mouse has moved, so the user is active
            self.set_user_as_active()

    def set_user_as_active(self): # Set the user as active
        print("User is active!")
        self.activity_timer.stop()
        self.idle_timer.start(5 * 60 * 1000)  # Check for idle every 5 minutes
        try:
            response = requests.post(base_api_url + 'user_online', data={'userID': self.userID})
            response.raise_for_status()
        except Exception as e:
            self.handle_request_exception(e)

    def set_user_as_idle(self): # Set the user as idle
        print("User is idle!")
        self.idle_timer.stop()
        self.activity_timer.start(5 * 1000)  # Check for activity every 5 seconds
        try:
            response = requests.post(base_api_url + 'user_idle', data={'userID': self.userID})
            response.raise_for_status()
        except Exception as e:
            self.handle_request_exception(e)

    def handle_request_exception(self, e, response=None): # Handle all exceptions
        print("Request Error:", e)
        if response is not None:
            print("Response content:", response.content)
        traceback.print_exc()  # Print the traceback including the line number where the exception occurred
        if isinstance(e, requests.exceptions.HTTPError):
            print("Http Error:", e)
        elif isinstance(e, requests.exceptions.ConnectionError):
            print("Error Connecting:", e)
        elif isinstance(e, requests.exceptions.Timeout):
            print("Timeout Error:", e)
        elif isinstance(e, requests.exceptions.RequestException):
            print("Something went wrong", e)
        else:
            print("An unknown error occurred:", e)

    def showEvent(self, event): # Check for session ID when the window is shown
        super().showEvent(event)
        if self.session_id is not None:
            print("Session ID found!")
        else:
            print("No session ID found!")
            self.session_check_timer = QTimer()
            self.session_check_timer.timeout.connect(self.check_for_session_id)
            self.session_check_timer.start(5000)

    def check_for_session_id(self): # Check for session ID
        if self.session_id is not None:
            print("Session ID found!")
            self.session_check_timer.stop()
    
    def fetch_username(self, user_id): # A function to fetch the username of a users ID
        print(f"Fetching username for {user_id}")
        try:
            response = requests.post(base_api_url + 'fetch_username', data={'userID': user_id})
            response.raise_for_status()
            return response.json()['username']
        except Exception as e:
            self.handle_request_exception(e)
    
    def fetchFriends(self): # Fetch the friends of the user using their ID
        try:
            response = requests.post(base_api_url + 'fetch_friends', data={'userID': self.userID})
            response.raise_for_status()
            friend_ids = [friend_id.strip() for friend_id in response.json()['friends']]
            print(friend_ids)
            for friend_id in friend_ids:
                username = self.fetch_username(friend_id)
                print(f"Creating widget for {username}")
                clone_widget = self.create_new_friend_widget(username, friend_id)
                print("Created new widget!")
                self.DMFriendsList.layout().addWidget(clone_widget)  # Add the widget to the layout
        except Exception as e:
            self.handle_request_exception(e)

    def create_new_friend_widget(self, username, friend_id): # Create a new friend widget
        try:
            DMFriend = QtWidgets.QWidget(parent=self.DMFriendsListContents)
            DMFriend.setEnabled(True)
            DMFriend.setMinimumSize(QtCore.QSize(221, 51))
            DMFriend.setMaximumSize(QtCore.QSize(221, 51))
            DMFriend.setObjectName("DMFriend")

            horizontalLayout = QtWidgets.QHBoxLayout(DMFriend)
            horizontalLayout.setContentsMargins(0, 0, 0, 0)
            horizontalLayout.setSpacing(0)
            horizontalLayout.setObjectName("horizontalLayout")

            DMListPFP = QtWidgets.QLabel(DMFriend)
            DMListPFP.setMinimumSize(QtCore.QSize(50, 50))
            DMListPFP.setMaximumSize(QtCore.QSize(50, 50))
            DMListPFP.setText("")
            pixmap = QtGui.QPixmap(self.fetchPFP(friend_id))
            scaled_pixmap = pixmap.scaled(50, 50, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            DMListPFP.setPixmap(scaled_pixmap)
            DMListPFP.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            DMListPFP.setObjectName("DMListPFP")
            horizontalLayout.addWidget(DMListPFP)

            DMListFriendName = QtWidgets.QPushButton(DMFriend)
            DMListFriendName.setMinimumSize(QtCore.QSize(100, 20))
            DMListFriendName.setMaximumSize(QtCore.QSize(160, 50))
            font = QtGui.QFont()
            font.setFamily("Segoe UI")
            font.setPointSize(9)
            font.setBold(False)
            DMListFriendName.setFont(font)
            DMListFriendName.setAutoFillBackground(True)
            DMListFriendName.setIconSize(QtCore.QSize(0, 0))
            DMListFriendName.setObjectName("DMListFriendName")
            DMListFriendName.setText(self.fetch_username(friend_id))
            horizontalLayout.addWidget(DMListFriendName)

            # Connect the button to the openDM method with friend_id and username as arguments
            DMListFriendName.clicked.connect(lambda: self.openDM(friend_id, username))

            # Insert the new widget at the top of DMFriendsList
            self.DMFriendsListContentsLayout.insertWidget(0, DMFriend)

            return DMFriend
        except Exception as e:
            self.handle_request_exception(e)
    
    def fetchPFP(self, recipientID): # Fetch the profile picture of a user based on their ID
        userID = self.userID if recipientID is None else recipientID
        # Check if the profile picture is in the cache. saves bandwidth and API calls
        if userID in self.pfpCache:
            print("Using cached profile picture for", userID)
            return self.pfpCache[userID]
        try:
            response = requests.post(base_api_url + 'fetchPFP', data={'userID': userID}, stream=True)
            response.raise_for_status()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(response.raw.read())
            # Store the profile picture in the cache
            self.pfpCache[userID] = pixmap
            print("pfpCache KB: ", round(sys.getsizeof(self.pfpCache) / 1024, -2), "KB")
            return pixmap
        except Exception as e:
            print("Error fetching profile picture")
            self.handle_request_exception(e)

    def userSessionSetup(self, session_id, session_user, session_userID): # Sets up critical session data
        self.session_id = session_id
        self.userID = session_userID
        self.userName.setText(session_user)
        self.fetchFriends()
        welcomeMsg = f"Welcome {session_user}, click a user to start chatting or add more friends!"
        self.titleHeader.setText(welcomeMsg)
        pixmap = self.fetchPFP(None)
        pixmap = QtGui.QPixmap(self.fetchPFP(session_userID))
        scaled_pixmap = pixmap.scaled(50, 50, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.userProfilePicture.setPixmap(scaled_pixmap)

    def openDM(self, friendID, username): # Open a direct message with a friend
        global recipientID
        recipientID = friendID
        self.stackedWidget.setCurrentWidget(self.chatPage)
        self.friendUserName.setText(username)
        self.messageEntryBox.setPlaceholderText(f"Message {username}")
    
        # Clear the scrollArea
        layout = self.scrollArea.widget().layout()
        for i in reversed(range(layout.count())): 
            layout.itemAt(i).widget().setParent(None)
    
        self.fetch_message_history(recipientID)
        pixmap = self.fetchPFP(None)
        pixmap = QtGui.QPixmap(self.fetchPFP(friendID))
        scaled_pixmap = pixmap.scaled(50, 50, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.recipientPFP.setPixmap(scaled_pixmap)
    
    def send_message(self): # Function to send a message
        global recipientID
        print("sending message to", recipientID)
        message = self.messageEntryBox.toPlainText()
        self.messageEntryBox.clear()
        data = {'message': message, 'userID': self.userID, 'userName': self.friendUserName.text(), 'recipientID': recipientID}
        try:
            response = requests.post(base_api_url + 'send_message', json=data)
            response.raise_for_status()
        except Exception as e:
            self.handle_request_exception(e)

    def fetch_message_history(self, recipientID): # Fetch the message history of a user based on their ID
        print("Fetching message history...")
        try:
            response = requests.post(base_api_url + 'fetch_messages', data={'userID': self.userID, 'recipientID': recipientID})
            response.raise_for_status()
            messages = response.json()['messages']
            for message in messages:
                self.process_incoming_message(message)
        except Exception as e:
            self.handle_request_exception(e, response)

    @sio.event
    @sio.on('message')
    def on_message(self, message): # SocketIO event for receiving messages
        print("Received message from server:", message)
        print("Message data:", message)
        self.new_message_signal.emit(message)

    def closeEvent(self, event): # This function runs when the window is closed ensuring everything is gracefully closed
        try:
            response = requests.post(base_api_url + 'logout', data={'userID': self.userID})
            response.raise_for_status()
            sio.disconnect()
            event.accept()
            print("Logged out and disconnected")
        except Exception as e:
            self.handle_request_exception(e)
        finally:
            event.accept()

app = QtWidgets.QApplication(sys.argv)
loginwindow = LoginWindow()
loginwindow.show()

chatWindow = MainWindow()
sys.exit(app.exec())

# could eat a sandwich right now.