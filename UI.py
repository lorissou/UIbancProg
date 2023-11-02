from tkinter import Tk, messagebox, StringVar, Menu, Scrollbar, YES, BOTH, NSEW, E, PhotoImage
from tkinter.ttk import Frame, LabelFrame, Label, Style, Treeview, Button
from logger import CustomLogger
from main import App
import configparser
import webbrowser
import threading
import sys
import os

FILENAME_CONFIG = "config.ini"
STATUS_SECTION = "Status"


class MainUI(Tk):
    mqtt: None
    multicast: None
    configuration: configparser.ConfigParser
    items_status: list
    status_translation: dict
    nodeREDurlButton: Button
    threadRun: bool
    style: Style
    menubar: Menu
    actualiseMenuOption: Menu
    actualiseRunningMenuOption: Menu
    headerFrame: Frame
    choixTestLabelFrame: LabelFrame
    choixTestTreeView: Treeview
    infosMESD: LabelFrame
    MESDTreeViewScrollbar: Scrollbar
    dataMESDTreeView: Treeview
    infosTest: LabelFrame
    testCoursStringVar: StringVar
    testCoursLabel: Label
    testCoursVarLabel: Label
    etatTestStringVar: StringVar
    etatTestLabel: Label
    etatTestVarLabel: Label
    optionsLabelFrame: LabelFrame
    stateFalseCardButton: Button
    rapportButton: Button
    forceMenuCascade: Menu
    padding: int

    def __init__(self, mainClass: App):
        # Configure the logging
        self.logClass = CustomLogger(name=__name__)
        self.logger = self.logClass.logger

        # Init the Tk class
        self.logger.debug("Init de la class UI")
        super().__init__()
        self.title("Tests MESD")

        # Import and link the mainClass
        self.mainClass = mainClass

        # Définir le chemin d'accès du fichier de config et répertoire
        self.directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.fileConfig = f"{self.directory}\\{FILENAME_CONFIG}"
        self.logger.debug(f"Directory path : {self.directory} and config file : {self.fileConfig}")

        # Import config
        self.readConfig()

    def run(self):
        # Link the MQTT and multicast class
        self.mqtt = self.mainClass.mqtt
        self.multicast = self.mainClass.multicast

        # Create the UI
        self.createUI()

        # Finish the UI (populating big elements)
        self.addDataTreeViewChoix()
        self.addFieldsMenuBar()

        # Run the app
        self.mainloop()

    def createUI(self):
        self.logger.debug("Création de l'Interface Utilisateur")
        # Create styles
        self.style = Style(self)
        self.style.configure("Heading", font=("Helvetica", 15))
        self.style.configure("Body", font=("Helvetica", 11))
        self.style.configure("Treeview.Heading", font=("Helvetica", 11))
        self.style.configure("Label.Warning", font=("Helvetica", 11), foreground="orange")
        self.style.configure("Label.Alert", font=("Helvetica", 11), foreground="red")

        # Adding menubar
        self.menubar = Menu(self)

        # Add icon to window
        icon = PhotoImage(file=f'{self.directory}\\ressources\\icon.png')
        # Set it as the window icon.
        self.iconphoto(True, icon)

        self.config(menu=self.menubar)

        # Define elements - Header Frame of the UI
        self.headerFrame = Frame(self)

        # Define elements - Frame with the test selection via the TreeView
        self.choixTestLabelFrame = LabelFrame(self, text="Choix test")
        self.choixTestTreeView = Treeview(self.choixTestLabelFrame)
        self.choixTestTreeView.heading("#0", text="Scripts Disponibles")

        # Define elements - Frame with the information of state of the MESD via the TreeView
        self.infosMESD = LabelFrame(self, text="Infos MESD")

        # /!\ 11 inputs pour l'instant car BRIO mais il va falloir changer pour RIOM
        columns = tuple([str(i) for i in range(1, int(self.getFromConfig("UI", "nb_inputs_BRIO")) + 1)])

        self.dataMESDTreeView = Treeview(self.infosMESD, columns=columns, height=4)
        self.dataMESDTreeView.column("#0", width=110)
        self.dataMESDTreeView.heading("#0", text="Carte")
        for i in columns:
            eval(f'self.dataMESDTreeView.heading("#{i}", text="I{i}")')
            eval(f'self.dataMESDTreeView.column("#{i}", width=30, minwidth=30)')
        self.dataMESDTreeView.tag_configure("GPIO", background='yellow')

        # Define elements - Frame with the actual states of the different parts of the program
        self.infosTest = LabelFrame(self, text="Infos Tests")

        self.testCoursStringVar = StringVar(self.infosTest)
        self.testCoursLabel = Label(self.infosTest, text="Tests en cours : ")
        self.testCoursVarLabel = Label(self.infosTest, textvariable=self.testCoursStringVar)

        self.etatTestStringVar = StringVar(self.infosTest)
        self.etatTestLabel = Label(self.infosTest, text="Etat MQTT : ")
        self.etatTestVarLabel = Label(self.infosTest, textvariable=self.etatTestStringVar)

        # Define elements - Frame with button to execute functions aka Simulate Card or export a report
        self.optionsLabelFrame = LabelFrame(self, text="Raccourcis")

        self.stateFalseCardButton = Button(self.optionsLabelFrame, text="Simuler une carte",
                                           command=lambda: self.simulateCard())
        self.rapportButton = Button(self.optionsLabelFrame, text="Exporter un rapport")
        url = f"https://{self.configuration.get('MQTT', 'host')}:{self.configuration.get('MQTT', 'port_NodeRED')}"
        self.nodeREDurlButton = Button(self.optionsLabelFrame, text="🔗 NodeRED", command=lambda: webbrowser.open(url))

        # Define the padding width
        self.padding = 4

        # Pack / grid elements
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.headerFrame.grid(row=0, column=0, columnspan=2)

        self.choixTestLabelFrame.grid(row=1, column=0, rowspan=2, sticky=NSEW, pady=self.padding, padx=self.padding)
        self.choixTestLabelFrame.grid_rowconfigure(0, weight=1)
        self.choixTestLabelFrame.grid_columnconfigure(0, weight=1)
        self.choixTestTreeView.pack(expand=YES, fill=BOTH)

        self.infosMESD.grid(row=1, column=1, sticky=NSEW, pady=self.padding, padx=self.padding)
        self.infosMESD.grid_columnconfigure(0, weight=1)
        self.infosMESD.grid_rowconfigure(0, weight=1)
        self.dataMESDTreeView.pack(expand=False, fill=BOTH)

        self.infosTest.grid(row=2, column=1, sticky=NSEW, pady=self.padding, padx=self.padding)
        self.infosTest.grid_columnconfigure(0, weight=1)
        self.infosTest.grid_columnconfigure(1, weight=1)
        self.testCoursLabel.grid(row=0, column=0)
        self.testCoursVarLabel.grid(row=0, column=1)
        self.etatTestLabel.grid(row=1, column=0)
        self.etatTestVarLabel.grid(row=1, column=1)

        self.optionsLabelFrame.grid(row=3, column=0, columnspan=2, sticky=NSEW, pady=self.padding, padx=self.padding)
        self.stateFalseCardButton.grid(row=0, column=0)
        self.rapportButton.grid(row=0, column=1)
        self.nodeREDurlButton.grid(row=0, column=2)

    def addDataTreeViewChoix(self):
        self.logger.debug("Ajout des données dans le TreeView de choix des tests")

        # Supprimer tous les élements avant de le repopuler au cas où il contient déjà des données
        while self.choixTestTreeView.get_children().__len__() > 0:
            self.choixTestTreeView.delete(self.choixTestTreeView.get_children()[0])

        # Ajout des Catégories et leurs Sous-Catégories depuis le fichier de config dans le TreeView
        try:
            categories = self.configuration.items("Menu")
            # Pour toutes les Catégories → les ajouter dans le parent ""
            for categorie in categories:
                string_categorie = categorie[0].upper()
                self.choixTestTreeView.insert("", "end", string_categorie,
                                              text=string_categorie, tags="categorie")
                sousCategories = self.configuration.items(categorie[1])
                # Pour toutes les sous-catégories → les ajouter dans le parent catégorie en question
                for sousCategorie in sousCategories:
                    string_sousCategorie = sousCategorie[0].upper()
                    tag_sousCategorie = f"{string_categorie}.{string_sousCategorie}"
                    script_name = self.getFromConfig(categorie[1], string_sousCategorie)
                    self.choixTestTreeView.insert(string_categorie, "end", tag_sousCategorie,
                                                  text=string_sousCategorie, tags=("sousCategorie", tag_sousCategorie))
                    self.choixTestTreeView.tag_bind(tag_sousCategorie, "<Double-Button-1>",
                                                    lambda e, carte=string_categorie, script=script_name:
                                                    self.mqtt.executeScript(carte, script))
        # Si la section n'est pas trouvée
        except configparser.NoSectionError:
            self.logger.error(f"Section non trouvée dans le fichier de config pour le menu de choix de tests")
            messagebox.showerror("Mauvaise config", "Le fichier de config comporte un problème de section pour le menu "
                                                    "de choix...")
        # Si l'option en question n'est pas trouvée...
        except configparser.NoOptionError:
            self.logger.error(f"Option non trouvée dans le fichier de config pour le menu de choix de tests")
            messagebox.showerror("Mauvaise config", "Le fichier de config comporte un "
                                                    "problème d'option pour le menu de choix...")

    def addFieldsMenuBar(self):
        # Main "Menu" class / item is created in the createUI method
        self.logger.debug("Ajout des données dans la barre de menu")

        # Menu - Actualiser
        self.actualiseMenuOption = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Actualiser", menu=self.actualiseMenuOption)
        self.actualiseMenuOption.add_command(label="Intialiser les relais MESD", command=lambda: self.mqtt.initMQTT())
        self.actualiseMenuOption.add_separator()
        self.actualiseMenuOption.add_command(label="Recharger la configuration", command=lambda: self.reloadApp())
        self.actualiseMenuOption.add_separator()
        self.actualiseRunningMenuOption = Menu(self.menubar, tearoff=0)
        self.actualiseMenuOption.add_cascade(label="Commutation de l'état d'éxectution",
                                             menu=self.actualiseRunningMenuOption)
        self.actualiseRunningMenuOption.add_command(label="Lancer le rafraîchissement",
                                                    command=lambda: self.startRefreshApp())
        self.actualiseRunningMenuOption.add_command(label="Stopper le rafraîchissement",
                                                    command=lambda: self.stopRefreshApp())

        # Menu - Forçages
        self.forceMenuCascade = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Forçages", menu=self.forceMenuCascade)
        self.forceMenuCascade.add_command(label="Forcer 'no_connection'",
                                          command=lambda: self.forceChangeStatus("no_connection"))
        self.forceMenuCascade.add_command(label="Forcer 'connected'",
                                          command=lambda: self.forceChangeStatus("connected"))
        self.forceMenuCascade.add_command(label="Forcer 'bad_connected'",
                                          command=lambda: self.forceChangeStatus("bad_connected"))
        self.forceMenuCascade.add_command(label="Forcer 'a'",
                                          command=lambda: self.forceChangeStatus("a"))
        self.forceMenuCascade.add_separator()
        self.forceMenuCascade.add_command(label="Simuler une carte", command=lambda: self.simulateCard())

    def readConfig(self):
        self.logger.debug("Lecture de la configuration")
        self.configuration = configparser.ConfigParser()
        try:
            self.configuration.read(self.fileConfig, encoding='utf-8')
        except configparser.NoSectionError:
            self.logger.error(f"Fichier de configuration non trouvé à {self.fileConfig}")
            messagebox.showerror("Fichier de config non trouvé",
                                 f"Le fichier de config n'a pas été trouvé à \n {self.fileConfig}")
            quit()
            # Import status translation
        try:
            self.items_status = self.configuration.items(STATUS_SECTION)
            self.status_translation = {}
            for element in self.items_status:
                self.status_translation[element[0]] = element[1]
            self.logger.debug(f"Status translation : {self.status_translation}")
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.logger.error("Section [Status] ou une de ses options non trouvée dans le fichier de config")
            messagebox.showerror("Section Status non trouvée",
                                 "La section Status dans le fichier de config n'a pas été trouvée...")

    def getFromConfig(self, section, option):
        try:
            return self.configuration.get(section=section, option=option)

        except configparser.NoSectionError:
            self.logger.error(f"Section [{section}] non trouvée dans le fichier de config")
            messagebox.showerror("Erreur dans le fichier de config", f"La section {section} n'a pas été trouvée"
                                                                     f"dans le fichier de config")
            return None

        except configparser.NoOptionError:
            self.logger.error(f"L'option {option} dans la section [{section}] non trouvée dans le fichier de config")
            messagebox.showerror("Erreur dans le fichier de config", f"L'option {option} dans {section} n'a pas "
                                                                     f"été trouvée dans le fichier de config")
            return None

    def reloadApp(self):
        self.readConfig()
        self.addDataTreeViewChoix()
        messagebox.showinfo("Rechargement fini", "L'application a bien été rechargée")

    def changeStatus(self, status):
        # Update the current status state
        try:
            formatted_status = self.status_translation[status]
        except KeyError:
            formatted_status = status
        try:
            match status:
                case "connected":
                    self.etatTestVarLabel.configure(foreground="green")
                case "no_connection":
                    self.etatTestVarLabel.configure(foreground="red")
                case s if s.startswith("bad_"):
                    self.etatTestVarLabel.configure(foreground="orange")
                case _:
                    self.etatTestVarLabel.configure(foreground="black")

            # Actualisation du Label de l'état de la connexion et des tests
            self.etatTestStringVar.set(formatted_status)
        except AttributeError:
            pass  # Mouais...

    def changeActualScript(self, actualScript):
        # Update the actual script state
        try:
            self.testCoursStringVar.set(actualScript)
        except AttributeError:
            pass  # Mouais...

    def changeDataMESD(self, data=None):
        # Update the table
        try:
            for row in self.dataMESDTreeView.get_children():
                self.dataMESDTreeView.delete(row)
            inputs = self.mqtt.input_buffer_dict  # Pour l'instant car pas encore multicast d'implémenté
            for card in inputs:
                inputs_card = tuple(inputs[card].values())
                self.dataMESDTreeView.insert("", "end", card, text=card, values=inputs_card, tags=('GPIO',))
        except AttributeError:
            pass  # Mouais...

    def stopRefreshApp(self):
        self.threadRun = False

    def startRefreshApp(self):
        self.threadRun = True
        threading.Thread(target=self.updateData, daemon=True).start()

    def forceChangeStatus(self, status):
        self.mqtt.status = status
        self.mainClass.event_refresh.set()

    def simulateCard(self):
        self.mqtt.input_buffer_dict["Test BRIO"] = {"I1": 1, "I2": 1, "I3": 1, "I4": 1, "I5": 1, "I6": 1, "I7": 1,
                                                    "I8": 1, "I9": 1, "I10": 1, "I11": 1}
        self.mainClass.event_refresh.set()
