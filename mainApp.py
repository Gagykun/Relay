import sys
import requests
import pyautogui
from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer
from login import Ui_LoginWindow # Login Window
from test import Ui_MainWindow # Chat Window

base_api_url = "http://10.0.0.108:5000/"
api_mode = "login"

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
                    register_data = {'loginUsername': str(self.usernameField.text()), 'loginPassword': str(self.passwordField.text()), 'email': str(self.emailField.text())}
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

            except requests.exceptions.HTTPError as errh:
                print ("Http Error:",errh)
                self.LRStatus.setText("Unauthorized!")
            except requests.exceptions.ConnectionError as errc:
                print ("Error Connecting:",errc)
                self.LRStatus.setText("Connection Error!")
            except requests.exceptions.Timeout as errt:
                print ("Timeout Error:",errt)
                self.LRStatus.setText("Timed out")
            except requests.exceptions.RequestException as err:
                print ("Something went wrong",err)
                self.LRStatus.setText("Critical Error!")
    

        self.LRConfirmBtn.clicked.connect(LRUser)
        self.LRSwapBtn.clicked.connect(swapMode)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.session_id = None
        self.sendChatButton.clicked.connect(self.send_message)
        self.timer = QTimer() # Timer to check for new messages
        self.timer.timeout.connect(self.fetch_messages)
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self.check_for_idle)
        self.idle_timer.start(5 * 60 * 1000)  # Check for idle every 5 minutes
        self.last_mouse_pos = pyautogui.position()
        self.activity_timer = QTimer() # Timer to check for user activity after idle
        self.activity_timer.timeout.connect(self.check_for_activity)

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

    def handle_request_exception(self, e):
        if isinstance(e, requests.exceptions.HTTPError):
            print("Http Error:", e)
        elif isinstance(e, requests.exceptions.ConnectionError):
            print("Error Connecting:", e)
        elif isinstance(e, requests.exceptions.Timeout):
            print("Timeout Error:", e)
        elif isinstance(e, requests.exceptions.RequestException):
            print("Something went wrong", e)

    def showEvent(self, event):
        super().showEvent(event)
        if self.session_id is not None:
            print("Session ID found!")
            self.timer.start(5000)
        else:
            print("No session ID found!")
            self.session_check_timer = QTimer()
            self.session_check_timer.timeout.connect(self.check_for_session_id)
            self.session_check_timer.start(5000)

    def check_for_session_id(self):
        if self.session_id is not None:
            print("Session ID found!")
            self.timer.start(5000)
            self.session_check_timer.stop()

    def userSessionSetup(self, session_id, session_user, session_userID):
        print("GOT SID:"+session_id)
        print("GOT USER:"+session_user)
        print("GOT USERID:"+session_userID)
        self.session_id = session_id
        self.userID = session_userID
        self.sendingUserUsername.setText(session_user)

    def send_message(self):
        print("Got button press!")
        message = self.chatEntryBox.toPlainText()
        print(self.session_id, message)
        self.chatEntryBox.clear()
        recipientID = "0Vzf3Q544fymv44P"  # Assuming the recipientID is the same as the userID
        data = {'message': message, 'userID': self.userID, 'userName': self.sendingUserUsername.text(), 'recipientID': recipientID}
        print(data)
        try:
            response = requests.post(base_api_url + 'send_message', json=data)
            response.raise_for_status()
        except Exception as e:
            self.handle_request_exception(e)

    def fetch_messages(self):
        print("Checking for messages...")
        try:
            response = requests.get(base_api_url + 'get_messages', params={'userID': self.userID})
            response.raise_for_status()
            messages = response.json()
            # Update the chat window with the new messages
            for message in messages:
                self.messageDialog.setText(f"{message['userID']}: {message['message']}")
        except Exception as e:
            self.handle_request_exception(e)

    def closeEvent(self, event):
        try:
            response = requests.post(base_api_url + 'logout', data={'userID': self.userID})
            response.raise_for_status()
        except Exception as e:
            self.handle_request_exception(e)
        finally:
            event.accept()

app = QtWidgets.QApplication(sys.argv)
loginwindow = LoginWindow()
loginwindow.show()

chatWindow = MainWindow()
sys.exit(app.exec())