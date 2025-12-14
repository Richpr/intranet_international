import psutil

def check_server(port, pid):
    try:
        p = psutil.Process(pid)
        print(f"Process {pid} found: {p.name()}")
        print(f"Status: {p.status()}")
        
        # Check listening connections
        found_connection = False
        for conn in p.connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                print(f"Process is listening on port {port}.")
                found_connection = True
                break
        if not found_connection:
            print(f"Process {pid} is NOT listening on port {port}.")

        # Check process output (this is harder without direct redirection)
        # For now, just confirming it's running and listening.

    except psutil.NoSuchProcess:
        print(f"No process found with PID {pid}.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    server_pid = 13261 # This was the last PID I got for the server. I will update it after starting the server again.
    server_port = 8002
    
    print(f"Checking server with PID {server_pid} on port {server_port}...")
    check_server(server_port, server_pid)
    
    # You might want to run this in a loop or after a short delay
    # time.sleep(5)
    # check_server(server_port, server_pid)
