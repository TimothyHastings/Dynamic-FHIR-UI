"""
Parse a FHIR json resource.
Build a list of tokens.
Display the FHIR resource in a simple list view.
The program uses a look ahead and look behind strategy
to parse a json FHIR resource.

Tim Hastings
August 2024
"""
import json

# Test FHIR Resource Files
#FHIR_FILE_NAME = 'patient_V5_no_urls.json'
#FHIR_FILE_NAME = 'observation_V5.json'
FHIR_FILE_NAME = 'patient_V5.json'


# A Token is a section, list, attribute or value.
class Token:
    def __init__(self):
        self.token_type = ""
        self.token_data = ""
        self.token_start = ""
        self.token_end = ""
    def update(self, type, data, start, end):
        self.token_type = type
        self.token_data = data.strip()
        self.token_start = start
        self.token_end = end
    def display(self):
        print(self.token_type, self.token_data, self.token_start, self.token_end)
    def get_data(self):
        # Return the unquoted data
        return self.token_data.replace("'", "")

# Load a json file and return as a json string.        
def load(name):
    with open(name) as json_file:
        j = json.load(json_file)
    return str(j)

# Look 1 step behind the current cursor position.
def look_behind(s, i):
    if i < 0:
        print('Error: look_behind out of range')
        return ''
    return s[i]

# Look 1 step ahead of the current cursor postion.
def look_ahead(s, i):
    if i >= len(s)-1:   
        print('Error: look_ahead out of range')      
        return "?"  
    return s[i+1]

# Look 2 steps ahead of the current cursor postion.
def look_ahead2(s, i):
    if i >= len(s)-1:      
        return ""  
    return s[i+2]

# Get the prvevious token.
def get_previous_token(tl):
    if len(tl) > 0:
        return tl[len(tl)-1]
    else:
        return Token()
    
# Get the html data.
def get_html(s, i):
    # TODO Skip to opening quote properly.  i += 3 VERY WEAK
    i += 3
    d = ""
    while i < len(s):
        d += s[i]
        if s[i] == "'":
            break
        i += 1 
    return i, d

# Get the next token in a sequence using rules.
def get_token(seq, start, tokens):
    index = start
    token = Token()
    found = False
    s = ""

    # If the previous token is a url or div attribute then
    # move along the sequence until the end of the url or div.
    # The end is determined by a quote.
    p = get_previous_token(tokens)
    data = p.get_data()

    is_html = False
    if p.token_type == 'attribute' and data.lower() == 'div':
        is_html = True
    if p.token_type == 'attribute' and data.lower() == 'url':
        is_html = True
    if is_html:
        i, html = get_html(seq, index)
        index = i
        html_token = Token()
        html_token.update('value', html, index+i, index)
        #print(html)
        html_token.display()
        return html_token, index
    
    # Process all other tokens.
    while not found and index < len(seq):
        ch = seq[index]
        s += ch

        # Skip these tokens.
        if  ch == '{':
            found = True
        elif ch == '}':
            found = True
        elif ch == ':':
            found = True
        elif ch == ',':
            found = True
        elif ch == '[':
            found = True
        elif ch == ']':
            found = True
        else:
            # Process a section, list, attribute or value
            la = look_ahead(seq, index)   
            lb = look_behind(seq, index-len(s))
            la2 = look_ahead2(seq, index)

            # Rules to determin Token context.
            if lb == ',' and la == ':' and la2 == '{':
                token.update('section', s, la, lb)
                found = True
            elif lb == ',' and la == ':' and la2 == '[':
                token.update('section', s, la, lb)
                found = True
            elif lb == '{' and la == ':':
                if la2 == '[':
                    token.update('list', s, la, lb)
                else:
                    token.update('attribute', s.title(), la, lb)
                found = True
            elif lb == ':' and la == ',':
                token.update('value', s, la, lb)
                found = True
            elif lb == ',' and la == ':':
                token.update('attribute', s, la, lb)
                found = True
            elif lb == ':' and la == '}':
                token.update('value', s, la, lb)
                found = True
            elif lb == '[' and la == ',':
                token.update('value', s, la, lb)
                found = True
            elif lb == ',' and la == ']':
                token.update('value', s, la, lb)
                found = True
            # List Items
            elif lb == ',' and la == ',':
                token.update('value', s, la, lb)
                found = True
            else:
                found = False
        index += 1 

    # Return a tuple.
    return token, index

# Get the next quote and return the index.
def get_next_quote(s):
    i = 1
    d = ""
    while i < len(s):
        if s[i] == "'":
            break
        i += 1 
    return i

# Create a token list from the FHIR json.
def tokenise(js:str):
    t_list = list()
    # Create a list of tokens.
    run = True
    i = 1
    while run:
        if i >= len(js):
            run = False
        t, i = get_token(js, i, t_list)
        if not t.token_type == '':
            t_list.append(t)

    return t_list

# For debug print the list of tokens.
def print_tokens(tokens):
    print('\nNum Tokens:', len(tokens))
    for t in tokens:
        print(t.token_type, t.token_data, t.token_start, t.token_end)

# Definition of a attribute/value row.
class Row:
    def __init__(self, a, b):
        self.a = a
        self.b = b

# Create a table of tokens to be displayed.
def create_table(tokens):
    table = list()
    run = True
    index = 0
    while run and index < len(tokens):
        token = Token()
        token = tokens[index]
        if token.token_type == 'attribute':
            s = token.get_data().title()
            if index < len(tokens) - 1:
                index += 1 
                token = tokens[index]
            row = Row(s+':', token.get_data())
            table.append(row)
        elif token.token_type == 'section':
            row = Row(token.get_data().title()+':','')
            table.append(row)
        else:
            # This is a list item!!
            row = Row('', token.get_data())
            table.append(row)

        if index < len(tokens) - 1:
            index += 1
        else:
            run = False

    return table

# PyQT python component libraries.
from PyQt5.QtWidgets import (QWidget, QLineEdit, QLabel, QPushButton, QScrollArea,QApplication,
                             QMainWindow, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
import sys

# Display a FHIR Resource as attribute value pairs.
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.scroll = QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
        self.widget = QWidget()                 # Widget that contains the collection of Vertical Box
        self.vbox = QGridLayout()               # The Vertical Box that contains the Horizontal Boxes of  labels and buttons

         # Read the FHIR resource and tokenise it.
        data = load(FHIR_FILE_NAME)
        tokens = tokenise(data)

        # Create the table to be displayed
        table = create_table(tokens)

        # Print the tokens - remove, debug only
        for t in table:
            print(t.a, t.b)

        # Build the UI
        i = 0
        for row in table:
            # Attribute
            a = row.a
            v = row.b
            self.vbox.addWidget(QLabel(row.a),i,0)
            # Value
            val = QLineEdit(row.b)
            if row.b == '':
                val.hide()
       
            self.vbox.addWidget(val,i,1)
           
            i += 1

        self.widget.setLayout(self.vbox)

        # Scroll Area Properties
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        self.setCentralWidget(self.scroll)

        self.setGeometry(100, 100, 600, 800)
        self.setWindowTitle('FHIR Viewer')
        self.show()

        return

###############################################
#
# Program start
#
###############################################

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec_())
