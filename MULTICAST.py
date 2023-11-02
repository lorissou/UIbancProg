import os
import sys
import configparser
from main import App
from threading import Thread
from tkinter import messagebox
from logger import CustomLogger

FILENAME_CONFIG = "config.ini"


class Multicast_Handler(Thread):
    mainUI: None
    mqtt: None

    def __init__(self, mainClass: App):
        # Configure the logging
        self.logClass = CustomLogger(name=__name__)
        self.logger = self.logClass.logger

        self.logger.debug("Init de la class MULTICAST")

        # Import and link the mainClass
        self.mainClass = mainClass

        # Initialiser le Thread (pas le lancer juste initialiser en tant que parent)
        Thread.__init__(self)

        # Définir le chemin d'accès du fichier de config et répertoire
        self.directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.fileConfig = f"{self.directory}\\{FILENAME_CONFIG}"
        self.logger.debug(f"Directory path : {self.directory} and config file : {self.fileConfig}")

        # Créer un ConfigParser
        self.config = configparser.ConfigParser()

    def run(self):
        # Link the other classes
        self.mainUI = self.mainClass.mainUI
        self.mqtt = self.mainClass.mqtt
