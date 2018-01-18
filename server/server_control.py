
import threading
import json
import logging
from SocketServer import ThreadingTCPServer, StreamRequestHandler
from utils.tools import ErrorUtil


# When the LineServer starts, it will start ServerControlThread as a thread to listen any control command on a TCP port (server control port)
# such as "shutdown" command from any user.
# This thread runs inside the same process as the main thread.

# When Line Server receives a user connection, it forks a new process to handle that user request (GET, QUIT, SHUTDOWN commands) so not to block other users from connecting.
# If a user enters "shutdown" command, the forked process will send "shutdown" command to the server control port,
# so that the main process can start to shutdown and terminate the Line Server.
# Basically it uses a TCP port for child processes to communicate back to the main process.

# This code uses Python SocketServer module - ThreadingTCPServer

#The actual control command handler
class ServerControlCommandHandler(StreamRequestHandler):
 
    def handle(self):
        try:
            logger = logging.getLogger(__name__)
            logger.info("control port connection from: %s" % str(self.client_address))
            request_msg = self.rfile.readline(1024)
            if request_msg and request_msg.upper().startswith("SHUTDOWN"):
                self.server.server_be_controlled.shutdown()
                self.server.shutdown()
        except Exception, arg:
            error = ErrorUtil.get_error(arg)
            logger = logging.getLogger(__name__)
            logger.error(json.dumps(error, indent=4, sort_keys=True))
            logging.error("An error occurred when processing request at control port!")


class CustomThreadingTCPServer(ThreadingTCPServer):

    def __init__(self, server_be_controlled, settings, *args, **kwargs):
        self.server_be_controlled = server_be_controlled
        self.settings = settings
        ThreadingTCPServer.__init__(self, *args, **kwargs)


#The thread class responsible for listening a control port so any user can issue "shutdown" command to terminate the server.
class ServerController(threading.Thread):

    settings = {
        "host": "localhost",
        "control_port": 8080
    }

    def __init__(self, server, settings):
        self.server_be_controlled = server
        self.tcp_server = None
        self.settings.update(settings)
        super(ServerController, self).__init__()

    def run(self):
        try:
            tcp_server = CustomThreadingTCPServer(self.server_be_controlled, self.settings,
                (self.settings["host"], self.settings["control_port"]),
                RequestHandlerClass=ServerControlCommandHandler,
                bind_and_activate=False)
            tcp_server.allow_reuse_address = True
            tcp_server.server_bind()
            tcp_server.server_activate()
            tcp_server.serve_forever()
            self.tcp_server = tcp_server
            logger = logging.getLogger(__name__)
            logger.info("control port is stopped!")
        except Exception, arg:
            error = ErrorUtil.get_error(arg)
            logger = logging.getLogger(__name__)
            logger.error(json.dumps(error, indent=4, sort_keys=True))
            logging.error("Server control port failed to start!")

    def start_server_control_command_handler(self):
        self.start()
