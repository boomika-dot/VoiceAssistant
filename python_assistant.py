"""Voice-Activated Personal Assistant
A Python-based personal assistant that performs tasks like setting reminders,
checking weather, reading news, and telling jokes using speech recognition.

Features:
*Voice activation with wake word
*Reminder management with persistence
*Real-time weather updates
*News headlines
*Joke functionality
*Speech recognition and text-to-speech"""

import speech_recognition as sr  
import pyttsx3  
import datetime  
import winsound
import requests  
import os  
import time  
import threading  
import random

# Initialize speech recognizer
recognizer = sr.Recognizer()  
reminders = []

# Configuration
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Fetch constants and API keys from environment
WAKE_WORD = os.getenv("WAKE_WORD")
SLEEP_WORD = os.getenv("SLEEP_WORD")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
DEFAULT_CITY = os.getenv("DEFAULT_CITY")
DEFAULT_NEWS_COUNTRY = os.getenv("DEFAULT_NEWS_COUNTRY")
REMINDERS_FILE = os.getenv("REMINDERS_FILE")

# Optional: check they loaded
print(WAKE_WORD, OPENWEATHER_API_KEY)

# Jokes for offline mode
FALLBACK_JOKES= [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "Why did the Python programmer not respond to the email? It was spam.",
    "What's a programmer's favorite hangout place? Foo Bar!",
    "Why do Java developers wear glasses? Because they don't C#!",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
    "Why did the developer go broke? Because he used up all his cache!",
    "What do you call a programmer from Finland? Nerdic!",
    "Why don't programmers like nature? It has too many bugs!",
    "What's the object-oriented way to become wealthy? Inheritance!",
    "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?"
]


def clear_screen():
    """Clear console screen for better readability"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Display application header"""
    clear_screen()
    print("=" * 70)
    print("VOICE-ACTIVATED PERSONAL ASSISTANT")
    print("=" * 70)
    print()


def print_separator():
    """Print visual separator line"""
    print("-" * 70)


def load_reminders():
    """Load saved reminders from file"""
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            loaded = []
            for line in f:
                parts = line.strip().split(" | ")
                if len(parts) == 2:
                    loaded.append((parts[0], parts[1]))
            return loaded
    return []


def save_reminders():
    """Save reminders to file for persistence"""
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        for r in reminders:
            f.write(f"{r[0]} | {r[1]}\n")


def speak(text):
    """Convert text to speech and display on console"""
    print(f"\nAssistant: {text}")
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"   [Text-to-Speech Error: {e}]")
    print()


def listen():
    """Listen to microphone input and convert to text"""
    with sr.Microphone() as source:
        print("\nStatus: Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            print("Status: Processing speech...")
            command = recognizer.recognize_google(audio).lower()
            print(f"You said: {command}")
            print_separator()
            return command
            
        except sr.WaitTimeoutError:
            print("Status: Timeout - No speech detected")
            print_separator()
            return ""
        except sr.UnknownValueError:
            print("Status: Could not understand audio")
            print_separator()
            return ""
        except sr.RequestError as e:
            print(f"Status: Speech recognition service error - {e}")
            print_separator()
            return ""


def beep():
    """Play wake-up sound"""
    winsound.Beep(1000, 300)


def confirm_beep():
    """Play confirmation sound"""
    winsound.Beep(1500, 150)


def get_weather(city=DEFAULT_CITY):
    """Fetch weather information from OpenWeatherMap API"""
    if not OPENWEATHER_API_KEY:
        return "Weather API key not configured."
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        print(f"   [Fetching weather data for {city}...]")
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        if "main" in data:
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            desc = data["weather"][0]["description"]
            
            weather_report = f"""
Weather Report for {city.title()}:
   - Condition: {desc.title()}
   - Temperature: {temp} degrees Celsius
   - Feels Like: {feels_like} degrees Celsius
   - Humidity: {humidity}%
"""
            return weather_report.strip()
        else:
            return "Unable to fetch weather information at this time."
    
    except requests.exceptions.RequestException as e:
        return f"Weather service unavailable: {str(e)}"


def get_news(country=DEFAULT_NEWS_COUNTRY):
    """Fetch top news headlines from GNews API"""
    if not GNEWS_API_KEY:
        return ["News API key not configured."]
    
    url = f"https://gnews.io/api/v4/top-headlines?token={GNEWS_API_KEY}&lang=en&country={country.lower()}&max=5"
    
    try:
        print("   [Fetching latest news headlines...]")
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        if "articles" in data:
            return [article["title"] for article in data["articles"]][:5]
        else:
            return ["Unable to fetch news at this time."]
    
    except requests.exceptions.RequestException:
        return ["News service unavailable."]


def tell_joke():
    """Fetch random joke from JokeAPI with local fallback"""
    url = "https://v2.jokeapi.dev/joke/Programming,Miscellaneous,Pun?blacklistFlags=nsfw,religious,political,racist,sexist,explicit"
    
    try:
        print("   [Fetching joke...]")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("type") == "single":
            return data.get("joke", random.choice(FALLBACK_JOKES))
        elif data.get("type") == "twopart":
            setup = data.get("setup", "")
            delivery = data.get("delivery", "")
            return f"{setup} ... {delivery}"
        else:
            return random.choice(FALLBACK_JOKES)
    
    except Exception:
        return random.choice(FALLBACK_JOKES)


def show_commands():
    """Display list of available commands"""
    commands_text = """
 ____________________________________________________________________
|                      AVAILABLE COMMANDS                            |
|____________________________________________________________________|
|  'time'           - Get current time                               |
|  'date'           - Get today's date                               |
|  'add reminder'   - Set a new reminder                             |
|  'show reminders' - Display all saved reminders                    |
|  'weather'        - Get weather information                        |
|  'news'           - Get latest news headlines                      |
|  'joke'           - Hear a random joke                             |
|  'help'           - Display this command list                      |
|  'go to sleep'    - Put assistant in sleep mode                    |
|  'exit' or 'stop' - Quit the assistant                             |
|____________________________________________________________________|

"""
    print(commands_text)


def reminder_checker():
    """Background thread to check and trigger reminders"""
    checked = set()
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        for task_time, task_text in reminders:
            reminder_key = f"{task_time}-{task_text}"
            if task_time == now and reminder_key not in checked:
                print("\n" + "=" * 70)
                print("                    REMINDER ALERT")
                print("=" * 70)
                speak(f"Reminder: {task_text}")
                beep()
                checked.add(reminder_key)
        
        # Clear checked reminders periodically to prevent memory buildup
        if len(checked) > 50:
            checked.clear()
        
        time.sleep(30)


def main():
    """Main program loop"""
    global reminders
    reminders = load_reminders()
    awake = False
    
    print_header()
    speak("Hello! I am your personal voice assistant.")
    speak("Say 'Hey Assistant' to wake me up, or say 'Exit' to quit.")
    print_separator()
    
    # Start reminder checking in background thread
    threading.Thread(target=reminder_checker, daemon=True).start()
    
    while True:
        command = listen()
        
        # Wake word detection
        if not awake:
            if WAKE_WORD in command:
                beep()
                awake = True
                print_header()
                print("Status: ASSISTANT ACTIVATED")
                print_separator()
                speak("Yes, I am listening. How can I help you?")
                show_commands()
        
        # Process commands when awake
        else:
            if command:
                confirm_beep()
            
            # Time command
            if "time" in command:
                now = datetime.datetime.now().strftime("%H:%M:%S")
                speak(f"The current time is {now}")
            
            # Date command
            elif "date" in command:
                today = datetime.datetime.now().strftime("%A, %d %B %Y")
                speak(f"Today is {today}")
            
            # Add reminder command
            elif "add reminder" in command:
                speak("Please say the reminder in format: HH:MM followed by the task. For example: 19:30 study")
                reminder_input = listen()
                
                if reminder_input:
                    parts = reminder_input.split(" ", 1)
                    if len(parts) == 2:
                        task_time, task_text = parts
                        try:
                            # Validate time format
                            datetime.datetime.strptime(task_time, "%H:%M")
                            reminders.append((task_time, task_text))
                            save_reminders()
                            confirm_beep()
                            print(f"\nReminder Added: {task_time} - {task_text}\n")
                            speak(f"Reminder set at {task_time} for {task_text}")
                        except ValueError:
                            speak("Invalid time format. Please use HH:MM format like 19:30")
                    else:
                        speak("Sorry, I did not understand the format. Please try again.")
                else:
                    speak("I did not catch that. Please try again.")
            
            # Show reminders command
            elif "show reminders" in command or "list reminders" in command:
                if reminders:
                    print("\nYOUR SAVED REMINDERS:")
                    print_separator()
                    speak(f"You have {len(reminders)} reminders.")
                    for i, (task_time, task_text) in enumerate(reminders, 1):
                        print(f"   {i}. {task_time} - {task_text}")
                        speak(f"At {task_time}, {task_text}")
                    print_separator()
                else:
                    speak("You have no reminders saved.")
            
            # Weather command
            elif "weather" in command:
                speak("Which city would you like the weather for?")
                city = listen()
                if not city:
                    city = DEFAULT_CITY
                    speak(f"Using default city: {city}")
                
                report = get_weather(city)
                print(f"\n{report}\n")
                speak(report)
            
            # News command
            elif "news" in command:
                speak("Fetching the top news headlines.")
                headlines = get_news()
                
                print("\nTOP NEWS HEADLINES:")
                print_separator()
                for i, headline in enumerate(headlines, 1):
                    print(f"   {i}. {headline}")
                    speak(f"Headline {i}: {headline}")
                print_separator()
            
            # Joke command
            elif "joke" in command or "tell me a joke" in command or "make me laugh" in command:
                speak("Here is a joke for you.")
                joke = tell_joke()
                print(f"\nJoke: {joke}\n")
                speak(joke)
            
            # Help command
            elif "help" in command or "commands" in command:
                show_commands()
            
            # Sleep command
            elif SLEEP_WORD in command:
                print("\nStatus: ASSISTANT GOING TO SLEEP")
                print_separator()
                speak("Okay, I will go back to sleep. Say 'Hey Assistant' to wake me again.")
                awake = False
            
            # Exit command
            elif "exit" in command or "stop" in command or "quit" in command:
                print("\nStatus: SHUTTING DOWN")
                print_separator()
                speak("Goodbye! Have a great day.")
                break
            
            # Unknown command
            elif command:
                speak("I did not understand that command. Say 'help' to see available commands.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
    except Exception as e:
        print(f"\nFatal error occurred: {e}")
        print("Please restart the assistant.")