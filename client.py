import socket
import threading
import time


def receive_messages(sock):
    """
    Background daemon thread function.
    Continuously listens for incoming messages from the server.
    """
    while True:
        try:
            # Receive up to 1024 bytes and decode to UTF-8
            msg = sock.recv(1024).decode('utf-8')
            if msg:
                # Print the received message and keep the prompt clean
                print(f"\n{msg}")
        except:
            # Triggered if the socket is closed or connection is lost
            print("\n[System] Connection to the server was lost.")
            break


def start_client():
    """
    Main client logic including reconnection loops, registration,
    and the primary messaging interface.
    """
    while True:  # Outer loop for persistent reconnection logic
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("[System] Attempting to connect to server...")
            client.connect(('127.0.0.1', 65432))
            print("[System] Connected successfully!")

            # --- Registration Handshake Phase ---
            while True:
                username = input("Enter username: ").strip()

                if not username:
                    print("Username cannot be empty. Please type something.")
                    continue

                client.send(username.encode('utf-8'))

                try:
                    # Wait for server approval (OK:...) or rejection (ERROR:...)
                    response = client.recv(1024).decode('utf-8')
                    if response.startswith("OK:"):
                        print(f"Success: {response}")
                        break
                    else:
                        print(f"Server refused: {response}")
                except socket.error:
                    print("Lost connection to server during registration.")
                    break

            # --- Communication Phase ---
            # Create a background thread to handle incoming data
            threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

            current_target = None  # Persistent target for auto-routing messages

            print("\n--- Welcome to the Chat ---")
            print("Commands:")
            print("  username:message  -> Start a new conversation")
            print("  exit              -> Disconnect from current conversation")
            print("  quitApp           -> Close the application")
            print("---------------------------\n")

            while True:
                prompt = f"[{current_target if current_target else 'No Target'}] > "
                msg = input(prompt).strip()

                if not msg:
                    continue

                # Disconnect from current partner but stay online
                if msg.lower() == 'exit':
                    if current_target:
                        print(f"Disconnected from {current_target}. Returning to main menu.")
                        goodbye = f"{current_target}:[System] {username} left the conversation."
                        client.send(goodbye.encode("utf-8"))
                        current_target = None
                    else:
                        print("You are not currently in a conversation.")
                    continue

                # Close the socket and terminate the client application
                if msg.lower() == 'quitapp':
                    print("Exiting... Goodbye!")
                    client.close()
                    return

                # Prevent switching targets without typing 'exit'
                if ':' in msg and current_target:
                    print(f"Error: You cannot talk with another person while chatting with {current_target}.")
                    print("Please type 'exit' first to switch targets.")
                    continue

                # Routing: Set new target if ':' is used
                if ":" in msg:
                    target_user, message_content = msg.split(":", 1)
                    target_user = target_user.strip()

                    if target_user == username:
                        print('Error: You cannot talk to yourself.')
                        continue

                    if not target_user or not message_content.strip():
                        print('Invalid format. Use target_user:message')
                        continue

                    current_target = target_user
                    client.send(msg.encode("utf-8"))
                    continue

                # Auto-routing: Send message to current active target
                if current_target is None:
                    print("Error: No target selected. Use 'username:message' to start.")
                    continue

                payload = f"{current_target}:{msg}"
                client.send(payload.encode("utf-8"))

        except (socket.error, ConnectionResetError, ConnectionRefusedError):
            # Reconnection logic triggered on network failure
            print("\n[System] Connection lost. Retrying in 5 seconds...")
            client.close()
            time.sleep(5)
            continue

if __name__ == "__main__":
    start_client()