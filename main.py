from logger import CustomLogger
from threading import Event

class App():
    def __init__(self):
        import MULTICAST
        import MQTT
        import UI
        # Init the logging
        self.logClass = CustomLogger(name=__name__)
        self.logger = self.logClass.logger

        # Create the classes
        self.mqtt = MQTT.MQTT_Handler(self)
        self.multicast = MULTICAST.Multicast_Handler(self)
        self.mainUI = UI.MainUI(self)

        # Start the MQTT Class as a Thread
        self.logger.info('Starting the MQTT Class as a thread')
        self.mqtt.start()

        # Start de multicast Class as a Thread
        self.logger.info('Starting the MULTICAST Class as a thread')
        self.multicast.start()

        # Start the Main UI tkinter Class as a Thread
        self.logger.info('Starting the UI Class not in a thread')
        self.mainUI.run()

if __name__ == "__main__":
    App()
