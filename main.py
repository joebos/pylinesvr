
import os
import getopt
import sys
import json
import logging
from server.server import Server
from server.server_control import ServerController
from utils.tools import ErrorUtil, LoggingUtil
from configuration import settings
import signal


class CommandArgError(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        #signal.signal(signal.SIGINT, exit_gracefully)

        LoggingUtil.init_logging()

        opts, args = getopt.getopt(argv[1:], [])

        if len(args) < 1:
            raise CommandArgError("Invalid args! Please enter: {0} {1} {2}".format("python", "main.py", "line_file_path"))

        text_file_path = args[0]
        if not os.path.isfile(text_file_path):
            raise CommandArgError("The file %s doesn't exist!" % text_file_path)

        server = Server(settings, text_file_path)
        server.start()

        return 0

    except CommandArgError, err:
        logger = logging.getLogger(__name__)
        logger.error(err.msg)
        return -1

    # forcefully kill itself on Ctrl-C, otherwise it will stuck in TCP socket listening for loop inside ForkTCPServer
    except KeyboardInterrupt as e:
        server.tcp_server.shutdown()
        os.kill(os.getpid(), 9)

    except Exception, arg:
        error = ErrorUtil.get_error(arg)
        logger = logging.getLogger(__name__)
        logger.error(json.dumps(error, indent=4, sort_keys=True))
        return -1

    finally:
        if server:
            server.cleanup()

if __name__ == "__main__":
    sys.exit(main())
