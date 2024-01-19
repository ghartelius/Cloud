import httpx
import xmltodict
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock

#db connection imports
import mysql.connector
from mysql.connector import errorcode

#db connection string
config = {'host' : 'cloud-main.mysql.database.azure.com', 
          'database' : 'cloud_main', 
          'user' : 'cloud', 
          'password' : 'Fedsvin12'}


#execute query function
def execute_query(sql_query):
    result = None
    try:
        print("Making connection")
        # using ** to unpack the config dict in the connect() function. This basically means that each key-value pair are inserted as an argument (so 4 arguments in this case). 
        # so host, database, user and password becomes arguments, with their respected values inside
        connection = mysql.connector.connect(**config)
        print("connection succesfull")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("something wrong with username or pass")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("db does not exist (or something else is wrong with the db maybe)")
        else:
            print("connection NOT made :(", err)
    else:
        # if the connection is successfull and no exceptions raised, execute the following
        cursor = connection.cursor(buffered=True)
        cursor.execute(sql_query)
        print("query executed")
        if sql_query.startswith("SELECT"):
            result = cursor.fetchone()
            print("fetching one SELECT value:", result)
        else:
            connection.commit()
            print("commiting changes, since no SELECT command")
        cursor.close()
        connection.commit()
    return result

#this function checks if there is an instance in the DB

def Get_Instance():
    try:
        Instance_check_query = f"SELECT GraphID FROM cloud_main.activeinstance"
        result = execute_query(Instance_check_query)
        final_result = result[0]
        return final_result
    except:
        print("no instance found in the database")
        pass

# function definition with parameters for graph ID, simulation ID, and authentication details.
def get_enabled_events(graph_id: str, sim_id: str, auth: (str, str)):
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
    
    #print to debug (look at @pending later)
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
            e['@label'])
        #setting button_layout as button property (to manipulate the button)
        s.manipulate_box_layout = button_layout
        
        #change color if '@pending' is 'true'
        if e['@pending'] == 'true':
            s.background_color = (1, 0.569, 0, 1)  #orange color, normalized from RGB
        
            print(f"event {e['@label']} is pending, button color set to orange.") #for debugging
        #to distinguish them from non pending events
        
        button_layout.add_widget(s)

        #this is to show the updates for debuggin
        print(f"Added/Updated button for event {e['@label']}.") 
        

#custom button class for simulation events
class SimulationButton(Button):
    # initialization method for the SimulationButton
    def __init__(self, event_id: int, graph_id: str, simulation_id: str, username: str, password: str, text: str):
        # call the constructor of the parent class (Button)
        Button.__init__(self)
        self.event_id = event_id
        self.text = text
        self.graph_id = graph_id
        self.simulation_id = simulation_id
        self.username = username
        self.password = password
        # creating a new BoxLayout. This might be intended for layout manipulation but is not currently used.
        self.manipulate_box_layout = BoxLayout()

        #bind the button press event to the execute_event method
        self.bind(on_press=self.execute_event)
    
    # method that gets called when the button is pressed
    def execute_event(self, instance):
        print("I am pressed")
        # send a POST request to the simulation API to execute the event associated with this button
        response = httpx.post(f"https://repository.dcrgraphs.net/api/graphs/{self.graph_id}/sims/"
                   f"{self.simulation_id}/events/{self.event_id}", auth=(self.username, self.password))
        print("Response: " + str(response.status_code))
        # update the button layout by recreating buttons based on the current state of the simulation
        create_buttons_of_enabled_events(self.graph_id, self.simulation_id, (self.username, self.password), self.manipulate_box_layout)
        print("Executed event, refreshing buttons.")
        
class MyApp(App):
    #creating the constructor (to initiate the attributes, like labels, buttons and layout)
    def __init__(self):
        # calling the contructor of the parent class App, to ensure attributes are initialized correctly (not always necessary, but always recommended)
        App.__init__(self)
        self.Button_start = Button(text="Start the instance")
        self.Button_start.bind(on_press=self.start_sim)
        
        #adding a Button for terminating an instance
        self.Button_terminate = Button(text="Terminate Instance")
        self.Button_terminate.bind(on_press=self.terminate_sim)

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

        #adding a terminate button, that stops the instance if pressed
        layout_instance_start = BoxLayout(orientation='horizontal', padding='1pt', spacing=0)
        layout_instance_start.add_widget(self.Button_terminate)
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

        #handin2

        sql_query_search_DB = f"SELECT * FROM cloud_main.activeinstance WHERE GraphID = {self.txtinput_graphID.text}"
        db_data = execute_query(sql_query_search_DB)
        
        if db_data:
            #extracting simID from the Tuple
            sim_id = db_data[1]
            #extracting GraphID
            graph_id = db_data[0]
            print(type(sim_id)) #making sure they are strings
            print(type(graph_id))
            #creating buttons with that simID and GraphID
            create_buttons_of_enabled_events(graph_id, sim_id, (self.txtinput_username.text, self.txtinput_password.text), self.layout_buttons)
        else: 

            print("New simulation created with id:", simulation_id)
            #setting InstanceState to 1, since it is now running
            InstanceState = 1
            #saving to the instance in the database, by calling the execute_query() function
            sql_query_insert = f"INSERT INTO cloud_main.activeinstance VALUES ('{self.txtinput_graphID.text}','{simulation_id}',{InstanceState})"
            execute_query(sql_query_insert)
            #handin 1: creating the buttons matching the actions in the DCR table
            create_buttons_of_enabled_events(self.txtinput_graphID.text, simulation_id, (self.txtinput_username.text, self.txtinput_password.text), self.layout_buttons) # remember to add ".text"

    def terminate_sim(self, instance):
        
        #getting auth, graph_id and sim_id
        auth = (self.txtinput_username.text, self.txtinput_password.text)
        sql_query_search_DB = f"SELECT * FROM cloud_main.activeinstance WHERE GraphID = '{self.txtinput_graphID.text}'"
        db_data = execute_query(sql_query_search_DB)
        
        # getting the graph and sim_id
        if db_data:
            graph_id = db_data[0]
            sim_id = db_data[1]
        else:
            print("simulation not found in the database")
            return

        # calling the get_enabled_events function
        events = get_enabled_events(graph_id, sim_id, auth)
        # checking if there is is_accepting, to tell if there is pending events
        is_accepting = events['events']['@isAccepting']

        if is_accepting == "True":
            # Code to remove saved instance from the database
            sql_query_remove = f"DELETE FROM `cloud_main`.`activeinstance` WHERE (`GraphID` = '{self.txtinput_graphID.text}');"
            execute_query(sql_query_remove)
            print("Instance terminated")
            # clearning button, so the app is ready for new simulation
            self.layout_buttons.clear_widgets()
        else:
            #creating a popup. The popup activate when the terminate button is pressed when it cannot
            popup = Popup(title="Warning", content=Label(text="Cannot terminate current instance, because of pending tasks"))
            popup.size_hint = (1, 0.4)  # Set the size of the popup
            popup.open()
            #using the Clock class, to manage timed stuff in a Kivy application
            Clock.schedule_once(popup.dismiss, 4)  # close the popup after 4 seconds
            print("Cannot terminate, because of pending tasks")






if __name__ == '__main__':
    mainApp = MyApp()
    MyApp().run()