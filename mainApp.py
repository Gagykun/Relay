import sys
import requests
import pyautogui
import socketio
import traceback
import json
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTimer, QPropertyAnimation, QVariantAnimation, Qt, pyqtSignal
from login import Ui_LoginWindow  # Login Window
from mainTest import Ui_MainWindow  # Chat Window

base_api_url = "http://10.0.0.108:5000/"
WS_URL = "ws://10.0.0.108:5000"
api_mode = "login"

# Setup SocketIO
sio = socketio.Client()
sio.connect(WS_URL)


class LoginWindow(QtWidgets.QMainWindow, Ui_LoginWindow):
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
                        'username': str(self.usernameField.text()),  # Add username field
                        'password': str(self.passwordField.text()),  # Add password field
                        'email': str(self.emailField.text())  # Add email field
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

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    new_message_signal = pyqtSignal(dict)
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.new_message_signal.connect(self.invoke_message_handler)
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
        self.DMList.setLayout(QtWidgets.QVBoxLayout())
        self.MessageTemplate_3.setVisible(False)
        self.DMFriend.setVisible(False)
        self.verticalLayout_3.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

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

    def invoke_message_handler(self, message):
        try:
            QtCore.QMetaObject.invokeMethod(self, "process_incoming_message", QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(QtCore.QVariant, message))
        except Exception as e:
            self.handle_request_exception(e)

    def create_chat_message_widget(self, username, message):
        # Create a new QFrame and copy the contents of MessageTemplate_3
        message_widget = QtWidgets.QFrame()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.MessageTemplate_3.sizePolicy().hasHeightForWidth())
        message_widget.setSizePolicy(sizePolicy)
        message_widget.setMinimumSize(QtCore.QSize(739, 71))
        message_widget.setMaximumSize(QtCore.QSize(739, 71))
        message_widget.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        message_widget.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        message_widget.setObjectName("MessageTemplate_3")

        # Copy the contents of MessageTemplate_3
        layout = QtWidgets.QGridLayout(message_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(0)
        layout.setParent(message_widget)

        messagePFP = QtWidgets.QLabel(parent=self.MessageTemplate_3)
        messagePFP.setMinimumSize(QtCore.QSize(50, 50))
        messagePFP.setMaximumSize(QtCore.QSize(50, 50))
        messagePFP.setText("")
        messagePFP.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        messagePFP.setObjectName("messagePFP")
        pixmap = QtGui.QPixmap(self.fetchPFP(username))
        scaled_pixmap = pixmap.scaled(50, 50, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        messagePFP.setPixmap(scaled_pixmap)
        messagePFP.setScaledContents(True)
        messagePFP.setParent(message_widget)

        messageUsername = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(8)
        font.setBold(True)
        messageUsername.setFont(font)
        messageUsername.setTextFormat(QtCore.Qt.TextFormat.AutoText)
        messageUsername.setScaledContents(True)
        messageUsername.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignVCenter)
        messageUsername.setObjectName("messageUsername_3")
        messageUsername.setParent(message_widget)
        layout.addWidget(messageUsername, 0, 1, 2, 1)

        messageContents = QtWidgets.QLabel()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(messageContents.sizePolicy().hasHeightForWidth())
        messageContents.setSizePolicy(sizePolicy)
        messageContents.setMinimumSize(QtCore.QSize(739, 71))
        messageContents.setMaximumSize(QtCore.QSize(739, 71))
        messageContents.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        messageContents.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(9)
        messageContents.setFont(font)
        messageContents.setObjectName("messageContents_3")
        messageContents.setParent(message_widget)
        layout.addWidget(messageContents, 2, 1, 2, 1)
        message_widget.update()

        # Set the message content
        messageUsername.setText(username)
        messageContents.setText(message)

        return message_widget

    @QtCore.pyqtSlot(QtCore.QVariant)
    def process_incoming_message(self, message):
        username = self.fetch_username(message['userID'])
        message = message['message']
        try:
            new_message_widget = self.create_chat_message_widget(username, message)
            self.verticalLayout_3.addWidget(new_message_widget)
            self.scrollArea.ensureWidgetVisible(new_message_widget)
            self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        except Exception as e:
            self.handle_request_exception(e)


    def check_for_idle(self):
        current_mouse_pos = pyautogui.position() # Get the current mouse position
        if current_mouse_pos == self.last_mouse_pos: # If the mouse hasn't moved
            self.set_user_as_idle()
        else:
            self.last_mouse_pos = current_mouse_pos

    def check_for_activity(self):
        current_mouse_pos = pyautogui.position()
        if current_mouse_pos != self.last_mouse_pos: # The mouse has moved, so the user is active
            self.set_user_as_active()

    def set_user_as_active(self):
        print("User is active!")
        self.activity_timer.stop()
        self.idle_timer.start(5 * 60 * 1000)  # Check for idle every 5 minutes
        try:
            response = requests.post(base_api_url + 'user_online', data={'userID': self.userID})
            response.raise_for_status()
        except Exception as e:
            self.handle_request_exception(e)

    def set_user_as_idle(self):
        print("User is idle!")
        self.idle_timer.stop()
        self.activity_timer.start(5 * 1000)  # Check for activity every 5 seconds
        try:
            response = requests.post(base_api_url + 'user_idle', data={'userID': self.userID})
            response.raise_for_status()
        except Exception as e:
            self.handle_request_exception(e)

    def handle_request_exception(self, e, response=None):
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

    def showEvent(self, event):
        super().showEvent(event)
        if self.session_id is not None:
            print("Session ID found!")
        else:
            print("No session ID found!")
            self.session_check_timer = QTimer()
            self.session_check_timer.timeout.connect(self.check_for_session_id)
            self.session_check_timer.start(5000)

    def check_for_session_id(self):
        if self.session_id is not None:
            print("Session ID found!")
            self.session_check_timer.stop()
    
    def fetch_username(self, user_id):
        try:
            response = requests.post(base_api_url + 'fetch_username', data={'userID': user_id})
            response.raise_for_status()
            return response.json()['username']
        except Exception as e:
            self.handle_request_exception(e)
    
    def fetchFriends(self):
        try:
            response = requests.post(base_api_url + 'fetch_friends', data={'userID': self.userID})
            response.raise_for_status()
            friend_ids = response.json()['friends']
            for friend_id in friend_ids:
                username = self.fetch_username(friend_id)
                print(f"Creating widget for {username}")
                clone_widget = self.create_new_friend_widget(username, friend_id)
                print("Created new widget!")
                self.DMList.layout().addWidget(clone_widget)  # Add the widget to the layout
        except Exception as e:
            self.handle_request_exception(e)

    def create_new_friend_widget(self, username, friend_id):
        try:
            # Create a new QFrame and copy the contents of DMFriend
            new_widget = QtWidgets.QFrame()
            new_widget.setObjectName("DMFriend")
            new_widget.setMinimumSize(QtCore.QSize(221, 51))
            new_widget.setMaximumSize(QtCore.QSize(221, 51))
            new_widget.setFrameStyle(1)

            # Create a layout for the new widget
            layout = QtWidgets.QHBoxLayout(new_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Create a QLabel for the friend's profile picture
            DMListPFP = QtWidgets.QLabel()
            DMListPFP.setMinimumSize(QtCore.QSize(50, 50))
            DMListPFP.setMaximumSize(QtCore.QSize(50, 50))
            DMListPFP.setText("")
            DMListPFP.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            DMListPFP.setObjectName("DMListPFP")
            pixmap = self.fetchPFP(None)
            pixmap = QtGui.QPixmap(self.fetchPFP(friend_id))
            scaled_pixmap = pixmap.scaled(50, 50, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            DMListPFP.setPixmap(scaled_pixmap)

            # Create a QPushButton for the friend's username
            new_button = QtWidgets.QPushButton(username)
            new_button.setMinimumSize(QtCore.QSize(100, 20))
            new_button.setMaximumSize(QtCore.QSize(160, 50))
            font = QtGui.QFont()
            font.setFamily("Segoe UI")
            font.setPointSize(9)
            font.setBold(False)
            new_button.setFont(font)
            new_button.setAutoFillBackground(True)
            new_button.setIconSize(QtCore.QSize(0, 0))
            layout.addWidget(new_button)

            # Connect the button to the openDM method with friend_id and username as arguments
            new_button.clicked.connect(lambda: self.openDM(friend_id, username))

            # Insert the new widget at the top of DMList
            self.verticalLayout_4.insertWidget(0, new_widget)

            return new_widget
        except Exception as e:
            self.handle_request_exception(e)
    
    def fetchPFP(self, recipientID):
        userID = self.userID if recipientID is None else recipientID
        try:
            response = requests.post(base_api_url + 'fetchPFP', data={'userID': userID}, stream=True)
            response.raise_for_status()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(response.raw.read())
            return pixmap
        except Exception as e:
            print("Error fetching profile picture")
            self.handle_request_exception(e)

    def userSessionSetup(self, session_id, session_user, session_userID):
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

    def openDM(self, friendID, username):
        global recipientID
        recipientID = friendID
        print("Opening DM with", friendID, username)
        self.stackedWidget.setCurrentWidget(self.chatPage)
        self.friendUserName.setText(username)
        self.messageEntryBox.setPlaceholderText(f"Message {username}")
        self.fetch_message_history(recipientID)
        pixmap = self.fetchPFP(None)
        pixmap = QtGui.QPixmap(self.fetchPFP(friendID))
        scaled_pixmap = pixmap.scaled(50, 50, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.userProfilePicture.setPixmap(scaled_pixmap)
    
    def send_message(self):
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

    def fetch_message_history(self, recipientID):
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
    def on_message(self, message):
        print("Received message from server:", message)
        print("Message data:", message)
        self.new_message_signal.emit(message)

    def closeEvent(self, event):
        try:
            response = requests.post(base_api_url + 'logout', data={'userID': self.userID})
            response.raise_for_status()
            sio.disconnect()
            event.accept()
        except Exception as e:
            self.handle_request_exception(e)
        finally:
            event.accept()

app = QtWidgets.QApplication(sys.argv)
loginwindow = LoginWindow()
loginwindow.show()

chatWindow = MainWindow()
sys.exit(app.exec())