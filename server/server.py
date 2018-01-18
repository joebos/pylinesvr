
import socket
import logging
import json
from SocketServer import ForkingTCPServer, StreamRequestHandler
from server_control import ServerController
from models import LineFile
from utils.tools import ErrorUtil


# This is main user request handler. It receives data from client connection and then process commands (GET, QUIT and SHUTDOWN).
# this handler always runs in a forked child process, because Python uses PIL lock and It doesn't provide real threading concurrency.

# If user enters shutdown command, it sends the shutdown command to the server control port so that the main process can terminate the entire program
class UserRequestHandler(StreamRequestHandler):

    # This is a helper method to process user command input
    def validate_command(self, cmd_string):
        if not cmd_string:
            return False, None, None
        cmd_string = cmd_string.strip().upper()
        args = cmd_string.split()
        if args[0] == "QUIT":
            return True, "QUIT", []
        if args[0] == "SHUTDOWN":
            return True, "SHUTDOWN", []
        if args[0] == "GET" and len(args) >= 2:
            line = args[1]
            if line.isdigit():
                line_no = int(line)
                return True, "GET", [line_no]
        return False, None, None

    # The actual method for responding user commands
    def handle(self):
        try:
            logger = logging.getLogger(__name__)
            logger.info("User connection from: %s" % str(self.client_address))
            request_msg = self.rfile.readline(1024)
            while request_msg:
                logger.info("Message from user: %s" % request_msg)
                is_validate, cmd, params = self.validate_command(request_msg)
                if is_validate:
                    if cmd == "SHUTDOWN":
                        self.notify_main_server_shutdown()
                        break
                    if cmd == "QUIT":
                        break
                    if cmd == "GET":
                        line_no = params[0]
                        status, line = self.server.line_file.get_line(line_no)
                        if status == 500 and line:
                            self.wfile.write('Server error: %s' % line)
                        elif status == 200 and line:
                            self.wfile.write('OK\n%s\n' % line)
                        else:
                            self.wfile.write('ERR\n')
                        self.wfile.flush()
                        request_msg = self.rfile.readline(1024)
                        continue

                self.wfile.write('INVALID COMMAND!\n')
                self.wfile.flush()
                request_msg = self.rfile.readline(1024)

        except Exception, arg:
            error = ErrorUtil.get_error(arg)
            logger = logging.getLogger(__name__)
            logger.error(json.dumps(error, indent=4, sort_keys=True))

    # if a user enters SHUTDOWN, it will call this method to notify the main process by a TCP port
    def notify_main_server_shutdown(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server.settings["host"], self.server.settings["control_port"]))
        s.sendall(b'shutdown\n')


# This code uses Python SocketServer module - ForkingTCPServer for forking new processes for new connections.
class CustomForkTCPServer(ForkingTCPServer):

    def __init__(self, line_file, settings, *args, **kwargs):
        self.line_file = line_file
        self.settings = settings
        ForkingTCPServer.__init__(self, *args, **kwargs)


# This is the server class responsible for listening and fork a child process to handle user requests for each TCP connection.
# It uses Python SocketServer package
class Server(object):
    
    settings = {
        "host": "localhost",
        "port": 10497,
        "num_of_child_process_max": 40,
        "num_of_connections_max": socket.SOMAXCONN
    }

    def __init__(self, settings, text_file_path):
        self.settings.update(settings)
        self.line_file = LineFile(text_file_path, self.settings["num_of_lines_per_index_page"])
        self.server_controller = None
        self.tcp_server = None

    def start(self):
        try:
            # First, build indexes for line file
            self.line_file.buildIndex()

            # Prepare and start TCP socket server, which fork a new process when a user connects to the server
            tcp_server = CustomForkTCPServer(self.line_file, self.settings,
                (self.settings["host"], self.settings["port"]),
                RequestHandlerClass=UserRequestHandler,
                bind_and_activate=False)

            tcp_server.request_queue_size = self.settings["num_of_connections_max"]
            tcp_server.max_children = self.settings["num_of_child_process_max"]

            tcp_server.allow_reuse_address = True
            tcp_server.server_bind()
            tcp_server.server_activate()

            self.tcp_server = tcp_server
            self.server_controller = ServerController(self.tcp_server, self.settings)
            self.server_controller.start()

            self.tcp_server.serve_forever()

            logger = logging.getLogger(__name__)
            logger.info("The server is stopped!")

        except Exception, arg:
            error = ErrorUtil.get_error(arg)
            logger = logging.getLogger(__name__)
            logger.error(json.dumps(error, indent=4, sort_keys=True))
            logging.error("Server starting failed!")

    def cleanup(self):
        if self.tcp_server:
            self.tcp_server.shutdown()
        if self.server_controller and self.server_controller.tcp_server:
            self.server_controller.tcp_server.shutdown()
