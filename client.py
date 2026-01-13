import socket
import threading
import time

# TODO - write your server ip address here
HOST = '127.0.0.1'
PORT = 65432

def receive_messages(sock):
    """Background function that continuously receives incoming messages from the server."""
    while True:
        try:
            data = sock.recv(1024)

            # If the connection is closed gracefully, recv() returns b'' and we exit the loop.
            if not data:
                print("\n[System] Server closed the connection.")
                break

            msg = data.decode('utf-8', errors='ignore')
            if msg:
                # Print the received message on a new line
                print(f"\n{msg}")
        except OSError:
            print("\n[System] Connection to the server was lost.")
            break


def start_client():
    # Initialize a TCP socket
    # while True:  # Optional outer loop for reconnect logic (currently disabled)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print("[System] Attempting to connect to server...")
        client.connect((HOST, PORT))
        print("[System] Connected successfully!")

        # Registration / handshake phase
        while True:
            username = input("Enter username: ").strip()

            # Local validation: if the user pressed Enter, do not send anything to the server
            if not username:
                print("Username cannot be empty. Please type something.")
                continue

            client.send(username.encode('utf-8'))

            try:
                # Wait for server validation (OK or ERROR)
                response = client.recv(1024).decode('utf-8')
                if response.startswith("OK:"):
                    print(f"Success: {response}")
                    break
                else:
                    print(f"Server refused: {response}")
            except socket.error:
                print("Lost connection to server during registration.")
                break

        # Start communication phase:
        # Start a background daemon thread to receive messages
        threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

        current_target = None  # Tracks the user currently being chatted with

        print("\n--- Welcome to the Chat ---")
        print("Commands:")
        print("  username:message  -> Start a new conversation")
        print("  exit              -> Disconnect from the current conversation")
        print("  quitApp           -> Close the application")
        print("---------------------------\n")

        while True:
            # Display the prompt based on the current target
            prompt = f"[{current_target if current_target else 'No Target'}] > "
            msg = input(prompt).strip()

            if not msg:
                continue

            # Command: exit the current conversation
            if msg.lower() == 'exit':
                if current_target:
                    print(f"Disconnected from {current_target}. Returning to main menu.")
                    # Optional: inform the other side that you left
                    goodbye = f"{current_target}:[System] {username} left the conversation."
                    client.send(goodbye.encode("utf-8"))
                    current_target = None
                else:
                    print("You are not currently in a conversation.")
                continue

            # Command: close the application entirely
            if msg.lower() == 'quitapp':
                print("Exiting... Goodbye!")
                client.close()
                return

            # Prevent switching targets without leaving the current chat first
            if ':' in msg and current_target:
                print(f"Error: You cannot talk with another person while chatting with {current_target}.")
                print("Please type 'exit' first to switch targets.")
                continue

            # New conversation format: target_user:message
            if ":" in msg:
                target_user, message_content = msg.split(":", 1)
                target_user = target_user.strip()

                # Prevent sending messages to yourself
                if target_user == username:
                    print('Error: You cannot talk to yourself.')
                    continue

                message_content = message_content.strip()

                if not target_user or not message_content:
                    print('Invalid format. Use target_user:message')
                    continue

                current_target = target_user
                client.send(msg.encode("utf-8"))
                continue

            # Routing logic: if no target is selected yet
            if current_target is None:
                print("Error: No target selected. Use 'username:message' to start.")
                continue

            # Automatically send messages to the last selected target
            payload = f"{current_target}:{msg}"
            client.send(payload.encode("utf-8"))

    except (socket.error, ConnectionResetError, ConnectionRefusedError, BrokenPipeError, OSError):
        print("\n[System] Connection lost. Closing the application.")
        client.close()


if __name__ == "__main__":
    start_client()
