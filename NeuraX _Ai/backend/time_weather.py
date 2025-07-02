from datetime import datetime, timedelta
import pytz
import requests
from typing import Dict, Any, Optional

class TimeWeatherManager:
    def __init__(self):
        # Time zones for different Indian cities
        self.INDIA_ZONES = {
            "mumbai": "Asia/Kolkata",
            "delhi": "Asia/Kolkata",
            "bangalore": "Asia/Kolkata",
            "sangamner": "Asia/Kolkata",
            "ahmednagar": "Asia/Kolkata",
            "pune": "Asia/Kolkata"
        }
        
        # Default location
        self.default_location = {
            "city": "Sangamner",
            "state": "Maharashtra",
            "country": "India",
            "lat": 19.5772,
            "lon": 74.2113
        }
        
        self.current_location = self.default_location.copy()
        
    def get_current_time(self, city: str = None) -> Dict[str, Any]:
        """Get current time for a given city"""
        try:
            timezone = self.INDIA_ZONES.get(city.lower() if city else self.current_location["city"].lower(), "Asia/Kolkata")
            tz = pytz.timezone(timezone)
            current = datetime.now(tz)
            
            return {
                "status": "success",
                "time": current.strftime("%I:%M %p"),
                "date": current.strftime("%B %d, %Y"),
                "day": current.strftime("%A"),
                "timezone": str(timezone)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting time: {str(e)}"
            }

    def get_weather(self, city: str = None) -> Dict[str, Any]:
        """Get current and forecasted weather for a location"""
        try:
            # For demo purposes, returning simulated weather data
            # In production, you would integrate with a real weather API
            current = datetime.now()
            
            # Simulated weather data
            weather_data = {
                "current": {
                    "temp": 32,  # Celsius
                    "humidity": 65,
                    "description": "Partly Cloudy",
                    "feels_like": 34
                },
                "forecast": [
                    {
                        "date": (current + timedelta(days=1)).strftime("%Y-%m-%d"),
                        "temp_max": 33,
                        "temp_min": 24,
                        "description": "Sunny",
                        "humidity": 60
                    },
                    {
                        "date": (current + timedelta(days=2)).strftime("%Y-%m-%d"),
                        "temp_max": 31,
                        "temp_min": 23,
                        "description": "Scattered Clouds",
                        "humidity": 65
                    }
                ]
            }
            
            return {
                "status": "success",
                "location": city or self.current_location["city"],
                "data": weather_data
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting weather: {str(e)}"
            }

    def set_location(self, city: str, state: str = None, country: str = None) -> Dict[str, str]:
        """Update current location"""
        try:
            self.current_location["city"] = city
            if state:
                self.current_location["state"] = state
            if country:
                self.current_location["country"] = country
                
            return {
                "status": "success",
                "message": f"Location updated to {city}, {self.current_location['state']}, {self.current_location['country']}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error updating location: {str(e)}"
            }

    def get_time_info(self, query: str) -> str:
        """Handle time-related queries"""
        query = query.lower()
        time_info = self.get_current_time()
        
        if "time" in query:
            return f"Current time in {self.current_location['city']} is {time_info['time']}"
        elif "date" in query:
            return f"Today's date is {time_info['date']}"
        elif "day" in query:
            return f"Today is {time_info['day']}"
        else:
            return f"Current time and date in {self.current_location['city']}:\n" \
                   f"🕒 Time: {time_info['time']}\n" \
                   f"📅 Date: {time_info['date']}\n" \
                   f"📆 Day: {time_info['day']}"

    def get_weather_info(self, query: str) -> str:
        """Handle weather-related queries"""
        query = query.lower()
        weather_data = self.get_weather()
        
        if weather_data["status"] == "error":
            return f"Sorry, I couldn't get the weather information: {weather_data['message']}"
            
        data = weather_data["data"]
        location = weather_data["location"]
        
        # Handle tomorrow's weather query
        if "tomorrow" in query:
            tomorrow = data["forecast"][0]
            return f"Weather forecast for tomorrow in {location}:\n" \
                   f"🌡️ Temperature: {tomorrow['temp_min']}°C to {tomorrow['temp_max']}°C\n" \
                   f"💧 Humidity: {tomorrow['humidity']}%\n" \
                   f"☁️ Conditions: {tomorrow['description']}"
                   
        # Handle temperature specific query
        elif "temperature" in query:
            if "tomorrow" in query:
                tomorrow = data["forecast"][0]
                return f"Tomorrow's temperature in {location}: {tomorrow['temp_min']}°C to {tomorrow['temp_max']}°C"
            else:
                return f"Current temperature in {location}: {data['current']['temp']}°C (feels like {data['current']['feels_like']}°C)"
                
        # Default to current weather
        return f"Current weather in {location}:\n" \
               f"🌡️ Temperature: {data['current']['temp']}°C\n" \
               f"💧 Humidity: {data['current']['humidity']}%\n" \
               f"☁️ Conditions: {data['current']['description']}\n" \
               f"🌡️ Feels like: {data['current']['feels_like']}°C"