import socket
import threading


def receive_messages(sock):
    """Background function that continuously receives incoming messages from the server."""
    while True:
        try:
            msg = sock.recv(1024).decode('utf-8')
            if msg:
                # Print the received message on a new line
                print(f"\n{msg}")
        except:
            print("\n[System] Connection to the server was lost.")
            break


def start_client():
    # Initialize TCP Socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('127.0.0.1', 65432))
    except ConnectionRefusedError:
        print("Error: Server is offline.")
        return

    # Registration Handshake Phase
    while True:
        username = input("Enter username: ").strip()

        # Local check: If the user just pressed Enter, do not send to server to avoid deadlock
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
            return

    # Start Communication Phase
    # Start a background daemon thread to receive messages
    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    current_target = None  # Tracks the person currently being chatted with

    print("\n--- Welcome to the Chat ---")
    print("Commands:")
    print("  username:message  -> Start a new conversation")
    print("  exit              -> Disconnect from current conversation")
    print("  quitApp           -> Close the application")
    print("---------------------------\n")

    while True:
        # Display the prompt based on the current target
        prompt = f"[{current_target if current_target else 'No Target'}] > "
        msg = input(prompt).strip()

        if not msg:
            continue

        # Command: Exit the current conversation
        if msg.lower() == 'exit':
            if current_target:
                print(f"Disconnected from {current_target}. Returning to main menu.")
                # Optional: Inform the other side that you left
                goodbye = f"{current_target}:[System] {username} left the conversation."
                client.send(goodbye.encode("utf-8"))
                current_target = None
            else:
                print("You are not currently in a conversation.")
            continue

        # Command: Close the application entirely
        if msg.lower() == 'quitapp':
            print("Exiting... Goodbye!")
            client.close()
            break

        # Check if user tries to switch targets without typing 'exit' first
        if ':' in msg and current_target:
            print(f"Error: You cannot talk with another person while chatting with {current_target}.")
            print("Please type 'exit' first to switch targets.")
            continue

        # New conversation format: target_user:message
        if ":" in msg:
            target_user, message_content = msg.split(":", 1)
            target_user = target_user.strip()

            # Prevent talking to self
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

        # Routing logic: If no target is selected yet
        if current_target is None:
            print("Error: No target selected. Use 'username:message' to start.")
            continue

        # Automatically send message to the last selected target
        payload = f"{current_target}:{msg}"
        client.send(payload.encode("utf-8"))


if __name__ == "__main__":
    start_client()