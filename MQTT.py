from threading import Thread, Event, Timer
from logger import CustomLogger
from tkinter import messagebox
from paho.mqtt.client import *
from main import App
import configparser
import os
import sys

FILENAME_CONFIG = "config.ini"
CONFIG_SECTION = "MQTT"
TOPIC_SECTION = "Topic"


class MQTT_Handler(Thread):
    mainUI: None
    multicast: None
    status: str
    actualScript: str
    client: Client
    wait_timer_connect: Timer
    wait_connect: Event
    input_buffer_dict: dict

    def __init__(self, mainClass: App):
        # Configure the logging
        self.logClass = CustomLogger(name=__name__)
        self.logger = self.logClass.logger

        self.logger.debug("Init de la class MQTT")

        # Import and link the mainClass
        self.mainClass = mainClass

        # Initialiser le Thread (pas le lancer juste initialiser en tant que parent)
        Thread.__init__(self)
        self.wait_connect = Event()
        self.wait_connect.clear()

        # Définir le chemin d'accès du fichier de config et répertoire
        self.directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.fileConfig = f"{self.directory}\\{FILENAME_CONFIG}"
        self.logger.debug(f"Directory path : {self.directory} and config file : {self.fileConfig}")

        # Créer un ConfigParser
        self.config = configparser.ConfigParser()

        # Input buffer init
        self.input_buffer_dict = {}

    def run(self):
        # Link the other classes
        self.mainUI = self.mainClass.mainUI
        self.multicast = self.mainClass.multicast

        # Set the status of the MQTT class
        self.changeStatus("no_connection")
        self.actualScript = "Aucun"

        # Read config file
        try:
            self.config.read(self.fileConfig, encoding='utf-8')
        except configparser.NoSectionError:
            self.logger.error(f"Fichier de configuration non trouvé à {self.fileConfig}")
            messagebox.showerror("Fichier de config non trouvé",
                                 f"Le fichier de config n'a pas été trouvé à \n {self.fileConfig}")
            quit()

        # Import configuration for MQTT Broker
        try:
            self.username = self.config.get(CONFIG_SECTION, "username")
            self.password = self.config.get(CONFIG_SECTION, "password")
            self.client_id = self.config.get(CONFIG_SECTION, "client_id")
            self.host = self.config.get(CONFIG_SECTION, "host")
            self.port = int(self.config.get(CONFIG_SECTION, "port"))
            self.logger.debug(f"Utilisation des valeurs : user={self.username} ; pass={self.password} ; "
                              f"id={self.client_id} ; host={self.host} ; port={self.port}")
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.logger.error(f"Section [MQTT] ou une de ses options non trouvée dans le fichier de config")
            messagebox.showerror("Section MQTT non trouvée",
                                 "La section MQTT ou une de ses options dans le fichier de config n'a pas été "
                                 "trouvée...")
            exit()

        # Import MQTT topics
        try:
            self.items_topics = self.config.items(TOPIC_SECTION)
            self.topics = {}
            for element in self.items_topics:
                self.topics[element[0]] = element[1]
            self.logger.debug(f"Topics : {self. topics}")
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.logger.error("Section [Topic] ou une de ses options non trouvée dans le fichier de config")
            messagebox.showerror("Section Topic non trouvée",
                                 "La section Topic dans le fichier de config n'a pas été trouvée...")

        # Connection au MQTT broker
        self.connect_mqtt()

        # Send the init to broker
        self.initMQTT()

    def on_connect(self, client, userdata, flags, rc):
        match rc:
            case 0:
                self.logger.info("Successfully connected to the MQTT broker")
                self.changeStatus("connected")
                self.wait_connect.set()
            case 3:
                self.logger.error("Connexion error - Server unavailable")
                self.changeStatus("bad_connected_unavailable")
            case 4:
                self.logger.error("Connexion error - Bad username or password")
                self.changeStatus("bad_connected_username_password")
            case 5:
                self.logger.error("Connexion error - Not authorised")
                self.changeStatus("bad_connected_not_authorised")
            case _:
                self.logger.error("Connexion error - Autre erreur")
                self.logger.error(client, userdata, flags, rc)
                self.changeStatus("bad_connected")

    def on_message(self, client, obj, msg):
        topic = str(msg.topic)
        payload = msg.payload.decode()
        self.logger.debug(f"Msg received : {msg.qos} - {topic} - {payload}")
        # Selon le topic faire script personnalisé
        match topic:
            case s if s.startswith("cartes/"):
                card = topic.split("/")[1]
                input = topic.split("/")[2]
                if self.input_buffer_dict.get(card) is None:
                    self.input_buffer_dict[card] = {}
                self.input_buffer_dict[card][input] = int(payload)
                self.mainUI.changeDataMESD()
            case "config/runningScript":
                match payload:
                    case "false":
                        self.actualScript = "Aucun"
                    case _:
                        self.actualScript = payload
                self.mainUI.changeActualScript(self.actualScript)

    def on_publish(self, userdata, mid, qos):
        pass

    def on_disconnect(self, client, userdata, rc):
        self.changeStatus("no_connection")
        match rc:
            case 0:
                self.logger.warning("Disconnected from MQTT Broker properly")
            case _:
                self.logger.warning("Disconnected from MQTT Broker inproperly")

    def connect_mqtt(self):
        self.logger.info("Connexion au MQTT Broker en cours")
        self.client = Client(self.client_id)
        self.client.username_pw_set(self.username, self.password)
        self.defineFunctionsOnEventMQTT()
        try:
            self.client.connect(self.host, self.port)
        except TimeoutError:
            self.logger.error("Connexion error - Timeout")
            self.changeStatus("bad_connected_host")
            self.afterTimerConnection()
        except OSError:
            self.logger.error("Connexion error - Network error")
            self.changeStatus("bad_connected_network")
            self.afterTimerConnection()
        self.client.loop_start()

    def afterTimerConnection(self):
        if not self.wait_connect.is_set():
            try:
                status_formatted = self.mainUI.status_translation[self.status]
            except KeyError:
                status_formatted = self.status
            
            self.logger.error(f"Connexion impossible au broker à l'adresse {self.host} "
                              f"pour la raison : {status_formatted}")
            messagebox.showerror("Connexion impossible",
                                 f"Le programme n'a pas réussi à contacter le MQTT broker à l'adresse : {self.host}"
                                 f"\nPour la raison : {status_formatted}")
            quit()

    # Function which links / overrides the mqtt modules methods to my functions
    def defineFunctionsOnEventMQTT(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    # As the name says, it initialises the mqtt "network" --> it will reset the  rasperry pi's outputs
    def initMQTT(self):
        self.logger.info("Envoi du message d'initialisation")
        self.client.subscribe(self.topics["cartes"], qos=1)
        self.client.subscribe(self.topics["config"], qos=1)
        self.publish(self.topics["init"], "true")

    # Subscribe and publish are two function to be used by the main class as a interface with the mqtt module methods
    def subscribe(self, topic: str, qos: int = 2):
        self.logger.info(f"Subscribe on '{topic}' with qos {qos}")
        self.client.subscribe(topic=topic, qos=qos)

    def publish(self, topic: str, msg):
        self.logger.info(f"Publish on '{topic}' : '{str(msg)}'")
        result = self.client.publish(topic, msg)
        rq_status = result[0]
        if rq_status == 0:
            self.logger.debug(f"Envoi réussi de '{msg}' sur le topic '{topic}'")
        else:
            self.logger.error(f'Failed to send message to topic {topic}')
            messagebox.showerror("Envoi impossible",
                                 f"Le programme n'a pas réussi à envoyer le message : '{msg}' sur le topic : '{topic}'"
                                 f"\nEst-il encore en ligne ?")

    # Function to send the instruction of the wanted script to run
    def executeScript(self, carte, script_name):
        self.logger.info(f"Executing script {script_name} on card {carte}")
        self.publish(topic="config/currentCard", msg=carte)
        self.publish(topic="config/currentTest", msg=script_name)

    def changeStatus(self, status):
        self.status = status
        self.mainUI.changeStatus(status)

    def changeActualScript(self, script):
        self.actualScript = script
        self.mainUI.changeActualScript(script)