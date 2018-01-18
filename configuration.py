
import socket

# Some line server settings
settings = {
    "host": "0.0.0.0",
    "port": 10497,
    "num_of_child_process_max": 50,
    "num_of_connections_max": socket.SOMAXCONN,

    "control_port": 8080,

    "num_of_lines_per_index_page": 10000
}

