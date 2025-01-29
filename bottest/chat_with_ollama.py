import ollama
import subprocess
import re

def load_signal_options(filename):
    """
    Loads the list of signal options from the specified file.
    Ensures all options are stripped of whitespace and retains the original case.
    """
    try:
        with open(filename, "r") as file:
            return [line.strip() for line in file.readlines() if line.strip()]  # Remove empty lines without altering case
    except FileNotFoundError:
        print(f"Error: The file {filename} does not exist.")
        return []

def chat_with_ollama():
    print("Welcome to the Ollama chat. Type 'Exit' to end the conversation")
    
    # Load the signal options from the file
    signal_options = load_signal_options("signal_options.txt")
    if not signal_options:
        print("No signals were found in the file 'signal_options.txt'.")
        return
    
    #print(f"Loaded signal options: {', '.join(signal_options)}")
    
    while True:
        user_input = input("You: ")  # Keep user input in its original case
        
        if user_input.lower() in ['exit', 'salir']:
            print("Goodbye!!")
            break
        
        # Check if "número de descarga" or "shot number" is mentioned and if any signals match
        shot_match = re.search(r'(numero de descarga|shot number) (\d+)', user_input, re.IGNORECASE)
        if shot_match:
            shot = shot_match.group(2)  # Extract the shot number
            matching_signals = [signal for signal in signal_options if re.search(rf'\b{re.escape(signal)}\b', user_input)]
            
            if matching_signals:
                print(f"Running the script 'diagramasWeb.py' with shot number {shot} and signals: {', '.join(matching_signals)}...")
                
                try:
                    # Pass the matching signals and shot number to the program as arguments
                    '''subprocess.run([
                        "python.exe", 
                        "diagramasWeb.py", 
                        "--shot", shot, 
                        "--signals"] + matching_signals, check=True)'''
                    subprocess.run([
                        "/Users/sofiamorenolasa/Desktop/TFGJaime/Shared_TFG/venv/bin/python", 
                        "diagramasWeb.py", 
                        "--shot", shot, 
                        "--signals"] + matching_signals, check=True)
                except subprocess.CalledProcessError as e:
                    print("There was an error running 'diagramasWeb.py':", e)
                continue
            else:
                print("No valid signals were found in the user's message.")
        
        # Generate response
        response = ollama.generate(model='llama3', prompt=user_input)
        print("Bot: ", response['response'])


# Start the chat
chat_with_ollama()
