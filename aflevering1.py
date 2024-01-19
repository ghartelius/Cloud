import httpx
import xmltodict
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


# function definition with parameters for graph ID, simulation ID, and authentication details.
def get_enabled_events(graph_id: str, sim_id: str, auth: (str, str)):
    
    #assigning the provided graph ID to a local variable.
    graph_id = graph_id
    # Assigning the provided simulation ID to a local variable.
    sim_id = sim_id

    # making a POST request to create a new simulation for a specific graph.
    newsim_response = httpx.post(
        url=f"https://repository.dcrgraphs.net/api/graphs/{graph_id}/sims",
        auth=auth)

    # extracting the simulation ID from the response headers and assigning it to sim_id.
    sim_id = newsim_response.headers['simulationID']
    # printing the new simulation ID to the console.
    print("New simulation created with id:", sim_id)

    # making a GET request to retrieve enabled events for the current simulation.
    next_activities_response = httpx.get("https://repository.dcrgraphs.net/api/graphs/" + graph_id +
                                         "/sims/" + sim_id + "/events?filter=only-enabled",
                                         auth=auth)

    # extracting the XML response text.
    events_xml = next_activities_response.text
    # removing the first and last character (quotes) from the XML string.
    events_xml_no_quotes = events_xml[1:len(events_xml)-1]
    # replacing escaped quotes with actual quotes in the XML string.
    events_xml_clean = events_xml_no_quotes.replace('\\\"', "\"")

    # parsing the cleaned XML string into a JSON-like dictionary.
    events_json = xmltodict.parse(events_xml_clean)
    # returning the parsed events in JSON format.
    return events_json


# function to create new buttons for every enabled event in a layout
def create_buttons_of_enabled_events(graph_id: str, sim_id: str, auth: (str, str), button_layout: BoxLayout):
    
    #calling the get_enabled_events() function, so the context of the buttons always match the events
    events_json = get_enabled_events(graph_id, sim_id, auth)
    
    #print to debug (look at @pending)
    print(events_json)
    
    
    # cleanup of previous widgets
    button_layout.clear_widgets()
    # creating an empty string to later store event details.
    events = []
    # distinguish between one and multiple events
    # using a built in function isinstance() to check if an object is an instance of the list class (checking if it is a list). Then make it a list, if it is not
    if not isinstance(events_json['events']['event'], list):
        #if 1 value, add it to the 'events' list as a single item list
        events = [events_json['events']['event']]
    else:
        #multiple values are just assigned normally
        events = events_json['events']['event']

    # iterating over each event to create and configure buttons
    for e in events:
        #create a custom button for every event
        s = SimulationButton(
            #filling in event's id, label and auth details for the button
            e['@id'],
            graph_id,
            sim_id,
            auth[0],
            auth[1],
            #the label of the event
            e['@label']
    )
        #setting button_layout as button property (to manipulate the button)
        s.manipulate_box_layout = button_layout
        # Change color if '@pending' is 'true'
        if e['@pending'] == 'true':
            s.background_color = (1, 0.569, 0, 1)  #orange color, normalized from RGB
        #to distinguish them from non pending events
        button_layout.add_widget(s)
        
# source code provided in exercise sheet

class SimulationButton(Button):
    def __init__(self, event_id: int, graph_id: str, simulation_id: str, username: str, password: str, text: str):
        Button.__init__(self)
        self.event_id = event_id
        self.text = text
        self.graph_id = graph_id
        self.simulation_id = simulation_id
        self.username = username
        self.password = password
        self.manipulate_box_layout: BoxLayout = BoxLayout()
        self.bind(on_press=self.execute_event)
    
    def execute_event(self, instance):
        httpx.post(f"https://repository.dcrgraphs.net/api/graphs/{self.graph_id}/sims/"
                   f"{self.simulation_id}/events/{self.event_id}", auth=(self.username, self.password))
        create_buttons_of_enabled_events(self.graph_id, self.simulation_id, (self.username, self.password), self.manipulate_box_layout)
        


class MyApp(App):
    #creating the constructor (to initiate the attributes, like labels, buttons and layout)
    def __init__(self):
        # calling the contructor of the parent class App, to ensure attributes are initialized correctly (not always necessary, but always recommended)
        App.__init__(self)
        self.Button_start = Button(text="Start the instance")
        self.Button_start.bind(on_press=self.start_sim)
        
        #creating label for username
        self.Label_username = Label(text='Username:')
        self.txtinput_username = TextInput(hint_text='enter username:')

        #creating label for password
        self.Label_password = Label(text='Password:')
        self.txtinput_password = TextInput(hint_text='enter password:', password=True)

        #creating label and txtinput for graph specification
        self.Label_graphID = Label(text='Graph ID:')
        self.txtinput_graphID = TextInput(hint_text='enter graph id:')

        #creating a layout to hold the buttons created when calling the button create function later
        self.layout_buttons = BoxLayout(orientation='vertical')
        
    #creating the builder (to create the structure of the app)
    def build(self):
        # creating the main horizontal layout
        layout_main = BoxLayout(orientation="horizontal", padding='1pt', spacing=0)

        # creating a vertical layout for login inputs and "start instance" button
        layout_login_and_start = BoxLayout(orientation="vertical", padding='1pt', spacing=0)

        # creating and adding layout for username
        layout_username = BoxLayout(orientation="horizontal", padding='1pt', spacing=0) #creating the boxlayout for logging in
        layout_username.add_widget(self.Label_username) #adding username label to the layout (most left)
        layout_username.add_widget(self.txtinput_username) #adding username txtinput (to the right of username label)
        layout_login_and_start.add_widget(layout_username) #adding final username layout the top of login_and_start layout

        # creating and adding layout for password (same as username, just 1 place below in login_and_start layout)
        layout_password = BoxLayout(orientation="horizontal", padding='1pt', spacing=0)
        layout_password.add_widget(self.Label_password)
        layout_password.add_widget(self.txtinput_password)
        layout_login_and_start.add_widget(layout_password)

        # creating and adding layout for Graph ID (once again the same)
        layout_graph = BoxLayout(orientation='horizontal', padding='1pt', spacing=0)
        layout_graph.add_widget(self.Label_graphID)
        layout_graph.add_widget(self.txtinput_graphID)
        layout_login_and_start.add_widget(layout_graph)

        # adding "start instance" button to the login and start layout (once again, in the buttom)
        layout_instance_start = BoxLayout(orientation='horizontal', padding='1pt', spacing=0)
        layout_instance_start.add_widget(self.Button_start)
        layout_login_and_start.add_widget(layout_instance_start)

        # Adding the login and start layout and the button layout to the main layout
        layout_main.add_widget(layout_login_and_start) #all the login stuff is now on the left, since layput_main is split in 2
        layout_main.add_widget(self.layout_buttons) #buttons on the right

        return layout_main
    
    def start_sim(self, instance):
        newsim_response = httpx.post(
            url="https://repository.dcrgraphs.net/api/graphs/" + self.txtinput_graphID.text + "/sims",
            auth=(self.txtinput_username.text, self.txtinput_password.text))
        simulation_id = newsim_response.headers['simulationID']
        print("New simulation created with id:", simulation_id)
        create_buttons_of_enabled_events(self.txtinput_graphID.text, simulation_id, (self.txtinput_username.text, self.txtinput_password.text), self.layout_buttons) # remember to add ".text"


if __name__ == '__main__':
    mainApp = MyApp()
    MyApp().run()