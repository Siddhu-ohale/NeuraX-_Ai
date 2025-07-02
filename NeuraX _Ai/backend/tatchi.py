import os
import re
import subprocess
import platform
import webbrowser
import urllib.parse
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from company_data import BAAP_COMPANY_INFO
from time_weather import TimeWeatherManager
from typing import List, Optional

# Load environment variables
load_dotenv('.env')

class APIKeyManager:
    def __init__(self):
        # Load all available API keys
        self.google_keys = [
            os.getenv('GOOGLE_API_KEY'),
            os.getenv('GOOGLE_API_KEY_BACKUP'),
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2')
        ]
        # Filter out None and empty strings
        self.google_keys = [k for k in self.google_keys if k]
        self.current_key_index = 0
        
    def get_next_key(self) -> Optional[str]:
        """Get the next available API key"""
        if not self.google_keys:
            return None
            
        key = self.google_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.google_keys)
        return key
        
    def remove_invalid_key(self, key: str) -> None:
        """Remove an invalid API key from the rotation"""
        if key in self.google_keys:
            self.google_keys.remove(key)
            self.current_key_index = self.current_key_index % len(self.google_keys) if self.google_keys else 0

# Initialize API key manager
api_key_manager = APIKeyManager()

def configure_genai() -> bool:
    """Configure the Gemini AI client with the next available API key"""
    key = api_key_manager.get_next_key()
    if not key:
        raise ValueError("No valid API keys available")
        
    try:
        genai.configure(api_key=key)
        return True
    except Exception as e:
        print(f"Error configuring API key: {str(e)}")
        api_key_manager.remove_invalid_key(key)
        return False

# Initial configuration
if not configure_genai():
    raise ValueError("Failed to configure any API keys")

# Initialize the TimeWeatherManager
time_weather_manager = TimeWeatherManager()

def get_ai_answer(prompt):
    """Get response from Gemini AI with failover support"""
    if not prompt:
        return "I didn't receive any input. Please try again."
        
    tries = 0
    max_tries = len(api_key_manager.google_keys)
    
    while tries < max_tries:
        try:
            # Check for creation/identity questions
            creation_keywords = ["who created you", "who made you", "who built you", "who developed you", 
                               "who are you", "what are you", "who trained you", "Who is founder Of You"]
            if any(keyword in prompt.lower() for keyword in creation_keywords):
                return "I am BAAP AI, created by Dinesh Jadhav and Siddharth Ohale. I am a large language model."

            if len(prompt.strip()) < 2:
                return "Please provide a longer message for me to understand your request better."
                
            model = genai.GenerativeModel("gemini-1.5-pro-latest")
            
            try:
                response = model.generate_content(prompt)
                
                if not response:
                    return "I was unable to generate a response. Please try rephrasing your question."
                    
                if not response.text:
                    return "I understood your question but couldn't formulate a response. Could you try asking in a different way?"
                
                # Override any response that mentions being trained/created by Google
                response_text = response.text.replace("*", "")
                if any(phrase in response_text.lower() for phrase in ["trained by google", "created by google", "i am a google", "developed by google"]):
                    return "I was created by Dinesh Jadhav and Siddharth Ohale. I am a large language model."
                    
                return response_text
                
            except genai.types.generation_types.BlockedPromptException:
                return "I apologize, but I cannot process that type of request."
            except genai.types.generation_types.GenerationException as ge:
                return f"I encountered an issue: {str(ge)}"
                
        except Exception as e:
            print(f"❌ Gemini API Error (try {tries + 1}/{max_tries}): {str(e)}")
            current_key = api_key_manager.google_keys[api_key_manager.current_key_index]
            api_key_manager.remove_invalid_key(current_key)
            
            if not configure_genai():
                if "quota" in str(e).lower():
                    return "I've reached my usage limit. Please try again later."
                return "I encountered an unexpected error. Please try again."
                
            tries += 1
            
    return "All available API keys have failed. Please try again later."

def search_youtube_video(query):
    """Search YouTube and return the first video ID found"""
    if not query:
        return None
        
    try:
        # Clean the query while preserving content words
        query = re.sub(
            r"(please|can you|would you|could you|neurax|on youtube|video)",
            "",
            query,
            flags=re.IGNORECASE
        ).strip()
        
        if not query:
            return None
            
        search_query = urllib.parse.quote_plus(query)
        
        # Use headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(
            f"https://www.youtube.com/results?search_query={search_query}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return None
            
        # Extract video IDs using regex
        video_ids = []
        pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
        matches = re.findall(pattern, response.text)
        
        for video_id in matches:
            if video_id not in video_ids:
                video_ids.append(video_id)
                if len(video_ids) >= 3:  # Get top 3 results
                    break
                    
        return video_ids[0] if video_ids else None
        
    except Exception as e:
        print("YouTube Search Error:", e)
        return None

def open_windows_application(app_name):
    """Handle Windows application opening"""
    windows_apps = {
        'notepad': ['notepad.exe'],
        'calculator': ['calc.exe'],
        'paint': ['mspaint.exe'],
        'word': ['winword.exe'],
        'excel': ['excel.exe'],
        'powerpoint': ['powerpnt.exe'],
        'outlook': ['outlook.exe'],
        'explorer': ['explorer.exe'],
        'file explorer': ['explorer.exe'],
        'cmd': ['cmd.exe'],
        'command prompt': ['cmd.exe'],
        'powershell': ['powershell.exe'],
        'control panel': ['control.exe'],
        'task manager': ['taskmgr.exe'],
        'registry editor': ['regedit.exe'],
        'system configuration': ['msconfig.exe'],
        'device manager': ['devmgmt.msc'],
        'disk management': ['diskmgmt.msc'],
        'event viewer': ['eventvwr.msc'],
        'services': ['services.msc'],
        'windows media player': ['wmplayer.exe'],
        'photos': ['start', 'ms-photos:'],
        'settings': ['start', 'ms-settings:'],
        'calendar': ['start', 'outlookcal:']
    }
    
    for app_key, command in windows_apps.items():
        if app_key in app_name.lower():
            try:
                if command[0] == 'start':
                    subprocess.Popen(command, shell=True)
                else:
                    subprocess.Popen(command)
                return f"Opening {app_key.title()}"
            except Exception as e:
                print(f"Error opening {app_key}: {e}")
                return f"Failed to open {app_key}. It may not be installed."
    
    return None

def open_macos_application(app_name):
    """Handle macOS application opening"""
    macos_apps = {
        'textedit': 'TextEdit',
        'calculator': 'Calculator',
        'preview': 'Preview',
        'safari': 'Safari',
        'finder': 'Finder',
        'mail': 'Mail',
        'calendar': 'Calendar',
        'photos': 'Photos',
        'messages': 'Messages',
        'facetime': 'FaceTime',
        'itunes': 'iTunes',
        'quicktime': 'QuickTime Player',
        'terminal': 'Terminal',
        'activity monitor': 'Activity Monitor',
        'system preferences': 'System Preferences',
        'app store': 'App Store'
    }
    
    for app_key, app_bundle in macos_apps.items():
        if app_key in app_name.lower():
            try:
                subprocess.Popen(['open', '-a', app_bundle])
                return f"Opening {app_bundle}"
            except Exception as e:
                print(f"Error opening {app_bundle}: {e}")
                return f"Failed to open {app_bundle}. It may not be installed."
    
    return None

def open_linux_application(app_name):
    """Handle Linux application opening"""
    linux_apps = {
        'gedit': 'gedit',
        'calculator': 'gnome-calculator',
        'terminal': 'gnome-terminal',
        'files': 'nautilus',
        'file explorer': 'nautilus',
        'thunderbird': 'thunderbird',
        'libreoffice': 'libreoffice',
        'writer': 'libreoffice --writer',
        'calc': 'libreoffice --calc',
        'impress': 'libreoffice --impress',
        'gimp': 'gimp',
        'audacity': 'audacity',
        'vlc': 'vlc',
        'system monitor': 'gnome-system-monitor',
        'settings': 'gnome-control-center',
        'software center': 'gnome-software'
    }
    
    for app_key, command in linux_apps.items():
        if app_key in app_name.lower():
            try:
                subprocess.Popen(command.split())
                return f"Opening {app_key.title()}"
            except Exception as e:
                print(f"Error opening {app_key}: {e}")
                return f"Failed to open {app_key}. It may not be installed."
    
    return None

def open_application(app_name):
    """Open a system application based on the name"""
    try:
        system = platform.system()
        app_name = app_name.lower()
        
        # Web applications
        web_apps = {
            'whatsapp': 'https://web.whatsapp.com',
            'youtube': 'https://www.youtube.com',
            'facebook': 'https://facebook.com',
            'instagram': 'https://instagram.com',
            'twitter': 'https://twitter.com',
            'linkedin': 'https://linkedin.com',
            'gmail': 'https://mail.google.com',
            'google drive': 'https://drive.google.com',
            'google docs': 'https://docs.google.com',
            'google sheets': 'https://sheets.google.com',
            'google slides': 'https://slides.google.com',
            'netflix': 'https://netflix.com',
            'spotify': 'https://open.spotify.com',
            'discord': 'https://discord.com/app'
        }
        
        for app_key, url in web_apps.items():
            if app_key in app_name:
                webbrowser.open_new_tab(url)
                return f"Opening {app_key.title()} in your browser"

        # Browser-specific commands
        browsers = {
            'chrome': 'chrome',
            'google chrome': 'chrome',
            'edge': 'edge',
            'microsoft edge': 'edge',
            'firefox': 'firefox',
            'mozilla firefox': 'firefox',
            'safari': 'safari'
        }
        
        for browser_key, browser_name in browsers.items():
            if browser_key in app_name:
                try:
                    webbrowser.get(browser_name).open_new_tab('')
                    return f"Opening {browser_name.title()}"
                except webbrowser.Error:
                    return f"Could not find {browser_name.title()} browser"
        
        # Platform-specific applications
        result = None
        if system == 'Windows':
            result = open_windows_application(app_name)
        elif system == 'Darwin':  # macOS
            result = open_macos_application(app_name)
        elif system == 'Linux':
            result = open_linux_application(app_name)
        
        if result:
            return result
        
        return f"I don't know how to open {app_name} on this system"
    except Exception as e:
        print(f"Error opening application: {e}")
        return f"Failed to open {app_name}. An error occurred."

def control_pc(command):
    """Handle PC control commands"""
    system = platform.system()
    try:
        if system == 'Windows':
            if command == 'shutdown':
                subprocess.run(['shutdown', '/s', '/t', '1'])
                return "Shutting down your PC..."
            elif command == 'restart':
                subprocess.run(['shutdown', '/r', '/t', '1'])
                return "Restarting your PC..."
            elif command == 'sleep':
                subprocess.run(['powershell', '(Add-Type "[D]ll[I]mport(\"PowrProf.dll\")] public static class Sleep { [D]ll[I]mport(\"PowrProf.dll\")] public static extern void SetSuspendState(bool hibernate, bool forceCritical, bool disableWakeEvent);}"; [Sleep]::SetSuspendState(0,0,0)'])
                return "Putting your PC to sleep..."
        elif system == 'Linux':
            if command == 'shutdown':
                subprocess.run(['shutdown', '-h', 'now'])
                return "Shutting down your PC..."
            elif command == 'restart':
                subprocess.run(['shutdown', '-r', 'now'])
                return "Restarting your PC..."
            elif command == 'sleep':
                subprocess.run(['systemctl', 'suspend'])
                return "Putting your PC to sleep..."
        elif system == 'Darwin':  # macOS
            if command == 'shutdown':
                subprocess.run(['osascript', '-e', 'tell app "System Events" to shut down'])
                return "Shutting down your PC..."
            elif command == 'restart':
                subprocess.run(['osascript', '-e', 'tell app "System Events" to restart'])
                return "Restarting your PC..."
            elif command == 'sleep':
                subprocess.run(['pmset', 'sleepnow'])
                return "Putting your PC to sleep..."
        return f"PC {command} command not supported on this system"
    except Exception as e:
        print(f"Error executing PC control command: {e}")
        return f"Failed to {command} the PC. Make sure you have the required permissions."

def get_company_info(query):
    """Handle complex company-related queries with advanced pattern matching"""
    query = query.lower()
    
    # Educational Programs Query
    if any(word in query for word in ["education", "courses", "programs", "study", "learn", "training", "degree"]):
        edu = BAAP_COMPANY_INFO['education']
        programs = "\n".join(edu['programs'])
        return f"Educational Programs at The Baap Company:\n{programs}\n\nApproach: {edu['approach']}"
    
    # Founder and History
    if any(word in query for word in ["founder", "started by", "who started", "who created", "history", "background"]):
        return f"The Baap Company was founded by {BAAP_COMPANY_INFO['founder']} in {BAAP_COMPANY_INFO['founded']} with a vision to bridge the gap between rural talent and global technology needs. The company transforms farmers' children into industry-ready tech professionals."
    
    # Infrastructure and Capacity
    if any(word in query for word in ["infrastructure", "facility", "capacity", "building", "campus", "how many", "students"]):
        infra = BAAP_COMPANY_INFO['infrastructure']
        return f"The Baap Company's facility in {infra['location']} serves {infra['capacity']}. Note: {infra['challenges'][0]}"
    
    # Agricultural Initiatives
    if any(word in query for word in ["agriculture", "farming", "farmers", "rural", "village"]):
        agri = BAAP_COMPANY_INFO['agricultural_initiatives']
        return f"{agri['description']}\nKey Project: {agri['projects'][0]}"
    
    # Services and Expertise
    if any(word in query for word in ["services", "offerings", "what do they do", "provide", "solutions", "expertise"]):
        services = BAAP_COMPANY_INFO['services']
        service_list = "\n".join([f"🔹 {s['name']}: {s['description']}" for s in services])
        return f"The Baap Company's Services:\n{service_list}"
    
    # Contact and Social Media
    if any(word in query for word in ["contact", "phone", "email", "website", "social", "media", "follow"]):
        contact = BAAP_COMPANY_INFO['contact']
        social = contact['social_media']
        return f"""Contact Information:
📞 Phone: {contact['phone']}
📧 Email: {contact['email']}
🌐 Website: {contact['website']}

Social Media:
📱 Instagram: {social['instagram']}
💼 LinkedIn: {social['linkedin']}
👥 Facebook: {social['facebook']}"""
    
    # Location Specific
    if any(word in query for word in ["where", "location", "address", "place", "situated", "based"]):
        loc = BAAP_COMPANY_INFO['location']
        return f"The Baap Company is strategically located in {loc['city']}, near {loc['near']} in {loc['district']} district, {loc['state']}. This location was chosen to serve the rural community effectively."
    
    # Mission and Impact
    if any(word in query for word in ["mission", "vision", "goal", "aim", "purpose", "impact"]):
        return f"Mission: {BAAP_COMPANY_INFO['mission']}\n\nImpact: The company has become a hub for rural innovation, transforming villages into centers of technological excellence."
    
    # Handle comparison questions
    if any(word in query for word in ["compare", "difference", "better", "versus", "vs"]):
        return "The Baap Company is unique in its approach to rural development through technology education. Unlike traditional IT companies, it specifically focuses on empowering farmers' children and rural youth, combining technological education with agricultural initiatives."
    
    # Handle statistics and numbers
    if any(word in query for word in ["how many", "numbers", "statistics", "count", "size"]):
        return f"The Baap Company has:\n- {BAAP_COMPANY_INFO['infrastructure']['capacity']}\n- Founded in {BAAP_COMPANY_INFO['founded']}\n- Multiple educational programs (11th & 12th, BCA, MCA)\n- 5 major service offerings"
    
    # General info for unmatched queries
    return f"""The Baap Company Quick Facts:
📍 Founded: {BAAP_COMPANY_INFO['founded']} by {BAAP_COMPANY_INFO['founder']}
🎯 Mission: {BAAP_COMPANY_INFO['mission']}
📍 Location: {BAAP_COMPANY_INFO['location']['city']}, {BAAP_COMPANY_INFO['location']['state']}
💼 Services: Software Development, AI, Digital Marketing, Data Analytics, and Talent Solutions
📚 Education: Offers programs from 11th & 12th to MCA
🌾 Special: Combines tech education with agricultural initiatives"""

def execute_command(command):
    """Execute user command and return appropriate response"""
    if not isinstance(command, str):
        return {"type": "text", "content": "Invalid command received."}
        
    command = command.lower().strip()
    
    try:
        # Handle PDF conversion request
        if "convert image to pdf" in command or "convert images to pdf" in command:
            return {
                "type": "redirect",
                "content": "http://127.0.0.1:5000",
                "message": "Redirecting you to the Image to PDF converter..."
            }

        # PC Control commands
        if any(cmd in command for cmd in ["shutdown pc", "turn off pc", "power off"]):
            response = control_pc('shutdown')
            return {"type": "text", "content": response}
        elif any(cmd in command for cmd in ["restart pc", "reboot pc", "reboot system"]):
            response = control_pc('restart')
            return {"type": "text", "content": response}
        elif any(cmd in command for cmd in ["sleep pc", "suspend pc", "sleep mode"]):
            response = control_pc('sleep')
            return {"type": "text", "content": response}
            
        # Weather related queries
        elif any(word in command for word in ["weather", "temperature", "forecast", "rain", "sunny"]):
            response = time_weather_manager.get_weather_info(command)
            return {"type": "text", "content": response}
            
        # Time and date related queries
        elif any(word in command for word in ["time", "date", "day", "today", "current time"]):
            response = time_weather_manager.get_time_info(command)
            return {"type": "text", "content": response}
            
        # Location setting
        elif "set location" in command or "change location" in command:
            # Extract location from command (simple version)
            parts = command.split("to")
            if len(parts) > 1:
                location = parts[1].strip()
                result = time_weather_manager.set_location(location)
                return {"type": "text", "content": result["message"]}
            return {"type": "text", "content": "Please specify a location. For example: 'set location to Mumbai'"}

        # Company information queries
        if any(word in command for word in ["baap", "baap company", "company info"]):
            response = get_company_info(command)
            return {"type": "text", "content": response}
            
        # Greetings
        if any(word in command for word in ["hello", "hey", "hi"]):
            return {"type": "text", "content": "Hey! It's me, BAAP AI! How can I help you?"}
        
        # YouTube commands - triggers on any command containing "play"
        if "play" in command:
            # Extract the actual query
            query = re.sub(
                r"(play|please|can you|would you|could you|neurax)",
                "",
                command,
                flags=re.IGNORECASE
            ).strip()
            
            if not query:
                return {"type": "text", "content": "What would you like me to play?"}
            
            video_id = search_youtube_video(query)
            if video_id:
                return {
                    "type": "youtube",
                    "videoId": video_id,
                    "query": query
                }
            return {"type": "text", "content": f"Couldn't find content for '{query}' on YouTube"}
        
        # Application opening commands
        elif any(cmd in command for cmd in ["open ", "launch ", "start "]):
            for cmd in ["open ", "launch ", "start "]:
                if cmd in command:
                    app_name = command.split(cmd)[-1].strip()
                    break
            
            if app_name:
                result = open_application(app_name)
                return {"type": "text", "content": result}
            return {"type": "text", "content": "Please specify what application to open"}
        
        # Default to AI response
        else:
            return {"type": "text", "content": get_ai_answer(command)}
    except Exception as e:
        print("Command execution error:", e)
        return {"type": "text", "content": "An error occurred while processing your command."}