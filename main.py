from kivy.app import App
#importing BoxLayout class from Kivy's boxlayout module. BoxLayout is used for arranging widgets in a vertical or horizontal box.
from kivy.uix.boxlayout import BoxLayout

# importing Button class from Kivy's button module. This is used to create interactive button widgets in the app.
from kivy.uix.button import Button

#importing Label class from Kivy's label module. Label is used to display text.
from kivy.uix.label import Label

#importing TextInput class from Kivy's textinput module. TextInput is used for user input of text.
from kivy.uix.textinput import TextInput

#to get httpx requests and send em
import httpx

#main app class (the actual GUI)
class MyWordApp(App):
    #creating the constructor (to initiate the attributes, like labels, buttons and layout)
    def __init__(self):
        # calling the contructor of the parent class App, to ensure attributes are initialized correctly (not always necessary, but always recommended)
        App.__init__(self)
        self.Button_start = Button(text="Start the instance")
       
        #creating empty spaces
        self.empty1 = Label(text='') #to simulate empty space
        self.empty2 = Label(text='') #to simulate empty space
        self.empty3 = Label(text='') #to simulate empty space
        self.empty4 = Label(text='') #to simulate empty space
        self.empty5 = Label(text='') #to simulate empty space
        self.empty6 = Label(text='') #to simulate empty space
        self.empty7 = Label(text='') #to simulate empty space


        #creating label for username
        self.Label_username = Label(text='Username:')
        self.txtinput_username = TextInput(hint_text='enter username:') #hint_text is so the text disappears when you start writing

        #creating label for password
        self.Label_password = Label(text='Password:')
        self.txtinput_password = TextInput(hint_text='enter password:', password=True) #remeber to add password=True if it is password field '*' will show instead of actual text

        #creating label and txtinput for graph specification
        self.Label_graphID = Label(text='Graph ID:')
        self.txtinput_graphID = TextInput(hint_text='enter graph id:')

        

    #creating the builder (to create the structure of the app)
    def build(self):
        #creating layout foundation
        layout_main = BoxLayout(orientation="vertical", padding='1pt', spacing=0)
        layout_username = BoxLayout(orientation="horizontal", padding='1pt', spacing=0)
        layout_password = BoxLayout(orientation="horizontal", padding='1pt', spacing=0)
        layout_graph = BoxLayout(orientation='horizontal', padding='1pt', spacing=0)
        layout_instance_start = BoxLayout(orientation='horizontal', padding='1pt', spacing=0)
        #this layout is to make the "start instance" button as large as username, password and graph id
        layout_split = BoxLayout(orientation='vertical', padding='1pt', spacing=0) 

        # adding Username label and text input
        layout_username.add_widget(self.Label_username) 
        layout_username.add_widget(self.txtinput_username)
        layout_username.add_widget(self.empty1)
        layout_username.add_widget(self.empty2)
        layout_split.add_widget(layout_username)

        # adding password and text input
        layout_password.add_widget(self.Label_password)
        layout_password.add_widget(self.txtinput_password)
        layout_password.add_widget(self.empty3)
        layout_password.add_widget(self.empty4)
        layout_split.add_widget(layout_password)
        
        #adding the graphID specification
        layout_graph.add_widget(self.Label_graphID)
        layout_graph.add_widget(self.txtinput_graphID)
        layout_graph.add_widget(self.empty5)
        layout_graph.add_widget(self.empty6)
        layout_split.add_widget(layout_graph)
        
        #adding "start instance" button
        layout_instance_start.add_widget(self.Button_start)
        layout_instance_start.add_widget(self.empty7)
        layout_main.add_widget(layout_split)
        layout_main.add_widget(layout_instance_start)
        
        return layout_main
    
    def create_instance(self):
        newsim_response = httpx.post(
            url="https://repository.dcrgraphs.net/api/graphs/{your graph id}/sims", 
            auth=(self.username.text, self.password.text))

    
# to actually start the app

if __name__ == '__main__':
    MyWordApp().run()


class MyDCRApp(App):
    def __init__(self):
        App.__init__(self)
        self.password = TextInput(hint_text="Enter password", password=True)
        self.username = TextInput(hint_text="Enter username")
        self.graph_id = 1702933
        self.layout_box = BoxLayout(orientation='vertical')

    def build(self):
        b = Button(text="Create New Instance")
        b.bind(on_press=self.b_press)
        self.b_outer = BoxLayout()
        b_inner = BoxLayout()
        b_inner.add_widget(self.username)
        b_inner.add_widget(self.password)
        self.b_outer.add_widget(b)
        self.b_outer.add_widget(b_inner)
        return self.b_outer

    def b_press(self, instance):
        self.create_instance()

    def create_instance(self):
        newsim_response = httpx.post(
            url="https://repository.dcrgraphs.net/api/graphs/" + str(self.graph_id) + "/sims",
            auth=(self.username.text, self.password.text))

        simulation_id = newsim_response.headers['simulationID']
        print("New simulation created with id:", simulation_id)

        next_activities_response = httpx.get(
            "https://repository.dcrgraphs.net/api/graphs/" + str(self.graph_id) +
            "/sims/" + simulation_id + "/events?filter=only-enabled",
            auth=(self.username.text, self.password.text))

        events_xml = next_activities_response.text
        events_xml_no_quotes = events_xml[1:len(events_xml) - 1]
        events_xml_clean = events_xml_no_quotes.replace('\\\"', "\"")

        events_json = xmltodict.parse(events_xml_clean)

        for e in events_json['events']['event']:
            self.layout_box.add_widget(Label(text=e['@label']))
            print(e['@label'])

        self.b_outer.add_widget(self.layout_box)


if __name__ == '__main__':
    MyDCRApp().run()