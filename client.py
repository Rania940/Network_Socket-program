from PyQt5 import QtWidgets, QtCore, QtGui
from QtChatApp import Ui_ChatApp
from login import Ui_MainWindow
import encryption
import socket
import sys
import threading
import time

#predefined key for encryption
key = b'\xdb6\xc7r\xb3#\xbe"\x9c~C\xd4\xbe\xb8\x8f\xfa\xb6\x01\xe92+U\xde\\\xd7\xc5m\xba\xe2\r\xda\xe9'

#socket configurations
HEADER = 64 #header size
PORT = 1023
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNCET"
WARNING_MESSAGE = 'Username is already taken'



client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)
connected = True #Recieve from server while true



class login_window(QtWidgets.QMainWindow):
    def __init__(self):
        super(login_window, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.connectButton.clicked.connect(lambda: connect_click_action(self))
        

    def get_name(self):
        return self.ui.name.text()

    def get_gender(self):
        if (self.ui.femaleButton.isChecked()):
          return self.ui.femaleButton.text()

        elif (self.ui.maleButton.isChecked()):
            return self.ui.maleButton.text()   

    def get_age(self):
        return self.ui.age.text()  

def connect_click_action(win):
    global gender, age, name
    gender = win.get_gender()
    age = win.get_age()
    name = win.get_name()


    try:
        send('username:' + name)
    except:
        QtWidgets.QMessageBox.warning(win, "Connection Invalid", "Could not connect to this host and address.")
        return    

    # Checks if the entered username is already taken by the another client.

    # temp_socket.close()
    win.close()
    chat = chat_window()
    chat.show()
    






class chat_window(QtWidgets.QMainWindow):

    def __init__(self):
        super(chat_window, self).__init__()
        self.ui = Ui_ChatApp()
        self.ui.setupUi(self)
        self.idle_status = False
        # Calls send_from_lineEdit method on 'send_button' click.
        self.ui.result.setReadOnly(True)
        self.score = 0

        self.diagnosisQuestions = [  "Do you currently live with a family member who has depression?", "Have parents, other relatives, or maybe even friends accused you of being “irritated,” “nasty,” or “always in a bad mood?",
                                "Does life seem pointless?","Does it seem like it’s impossible to concentrate?","Have you withdrawn from your friends and family?","Have you noticed a sudden change in your weight?",
                                "Do you often oversleep? Do you think you get too little sleep (and may have insomnia)?", "Do you have aches and pains?",
                                "Have your grades dropped? If you’re involved in extracurricular activities, have you stopped participating or has your performance declined?","Have you thought of suicide?",""]

        self.questionIndex = 1 #number of the current question
        self.userMessage= ""
        self.yesCounter = 0


        self.display_question(self.diagnosisQuestions[0])
        
        
        




        self.timer = QtCore.QTimer(self)

        #update function for timer
        self.timer.start(100)

        #connections
        self.ui.yesButton.clicked.connect(self.yesHandling)
        self.ui.noButton.clicked.connect(self.noHandling)        
        self.timer.timeout.connect(self.check_timeout) #connect timer to check_timeout
        
        #start thread for recieving from server
        self.thread = threading.Thread(target=self.getStatus)
        self.thread.start()


    def yesHandling(self):
        """ funtion that handle yes answers then prepare the next question to be displayed  """
        self.yesCounter = self.yesCounter +1
        message_sent = self.diagnosisQuestions[self.questionIndex]

        self.userMessage = "Yes"
        
        # display user's message in the chatwindow
        self.display_user_message(self.userMessage)

        if(self.questionIndex == 10):
            # if the user finished answering all the questions then he gets the final result 
            self.getResult(0)
            return
        else:
            self.questionIndex = self.questionIndex + 1    
        self.display_question(message_sent)

        

        
    def noHandling(self):
        """ funtion that handle No answers then prepare the next question to be displayed  """

        message_sent = self.diagnosisQuestions[self.questionIndex]
        self.userMessage = "No"
        self.display_user_message(self.userMessage)

        if(self.questionIndex == 10):
            self.getResult(0)
            return

        else:
            self.questionIndex = self.questionIndex + 1
            
        self.display_question(message_sent)


       

    def display_question(self, message):
        """ Displays question to the chat  """
        self.ui.messagesList.addItem( ( "Question : " + str(message)))



    def display_user_message(self, message):
        """print user's message in the client's terminal"""
        print(message) 
        self.ui.messagesList.addItem(( "Answer :" + message + "\n"))


    
    def getResult(self,old_user_flag):
        """ prints the result of the test in the text box """
        self.ui.yesButton.hide()
        self.ui.noButton.hide()

        myscore = int(self.score)
        if not old_user_flag:
            user_data = []
            # get data >> all converted to strings
            user_data.append(name) #get name
            user_data.append(gender) #get gender
            user_data.append(age) #get age
            user_data.append(str(self.yesCounter))
            send(','.join(user_data))
            myscore = self.yesCounter

        if (myscore < 5): #normal
            self.ui.result.insert("You're fine. Keep your head up!")
        elif (myscore < 8): #depressed
            self.ui.result.insert("A little depressed. Try to take care of your self more!")
        else: #severe depression
            self.ui.result.insert("You need to go to therapy")


    #recieves from the server if the connection is idle or not
    def getStatus(self):
        
        global connected
        while connected:
            try:
                try:
                    #length of the header of the status message
                    msgLength = int(client.recv(HEADER).decode(FORMAT)) 
                    # print(msgLength)
                
                # message if the socket tried to recieve just before closing it
                except ValueError:
                    print("[FINISHED] Connection ended due to achieving required result ...")
                    connected = False
                
                # recieve status from the server
                server_message = client.recv(msgLength)
                # decrypt and decode server's message
                
                self.server_message = encryption.decrypt(key,server_message).decode(FORMAT)

                # print(self.server_message)

                # If status message is DISCONNECT_MESSAGE, disconnect the client 
                if self.server_message == DISCONNECT_MESSAGE:
                    self.idle_status = True
                    connected = False
                
                elif WARNING_MESSAGE in self.server_message:
                    # QtWidgets.QMessageBox.warning( self, "ERROR LOGIN", f"[ERROR] {WARNING_MESSAGE}")
                    self.score = self.server_message[len(WARNING_MESSAGE):]
                    self.getResult(1)
                    
                
            # If the server was closed
            except ConnectionAbortedError:
                print("[EXITING] The GUI was closed ... ")


        self.client.close()
        print("[EXITING] Exiting recieving thread .. ")
        sys.exit()


    #function to check if the client exceeds 40 secs without sending a message 
    def check_timeout(self):
        if self.idle_status:
            QtWidgets.QMessageBox.warning( self, "Connection Lost", "[IDLE] Connection was closed please open the UI again")
            sys.exit()





def send(message):
    """ encrypt and decode text and send it to server """
    message = encryption.encrypt(key,message)
    message_length = len(message)
    send_length =  str(message_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length) #send message len 
    client.send(message)     #send encrypted and encoded message



def main():
    app = QtWidgets.QApplication(sys.argv)
    login_app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(lambda : send(DISCONNECT_MESSAGE))
    # chat = chat_window()
    login = login_window()
    login.show()
    login_app.exec_()  

if __name__ == "__main__":
    main()

