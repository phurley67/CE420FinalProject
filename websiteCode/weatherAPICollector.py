# -*- coding: utf-8 -*-

import requests
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import csv
import json
import re

# Base URL for Open-Meteo API
BASE_URL = "https://api.open-meteo.com/v1"

def celsius_to_fahrenheit(celsius):
    return round(celsius * 9/5 + 32,1)

def get_current_temperature(latitude, longitude):
    endpoint = f"{BASE_URL}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True
    }
    response = requests.get(endpoint, params=params)
    data = response.json()
    temp_c = data["current_weather"]["temperature"]
    return celsius_to_fahrenheit(temp_c)

def get_weekly_forecast(latitude, longitude):
    endpoint = f"{BASE_URL}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto"
    }
    response = requests.get(endpoint, params=params)
    data = response.json()
    forecast = []
    for day, max_temp, min_temp, precip in zip(
            data["daily"]["time"],
            data["daily"]["temperature_2m_max"],
            data["daily"]["temperature_2m_min"],
            data["daily"]["precipitation_sum"]):
        forecast.append({
            "date": day,
            "max_temp": celsius_to_fahrenheit(max_temp),
            "min_temp": celsius_to_fahrenheit(min_temp),
            "precipitation": precip
        })
    return forecast

def get_historical_data(latitude, longitude, past_days=7):
    endpoint = f"{BASE_URL}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "past_days": past_days,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto"
    }
    response = requests.get(endpoint, params=params)
    data = response.json()
    historical_data = []
    for day, max_temp, min_temp, precip in zip(
            data["daily"]["time"],
            data["daily"]["temperature_2m_max"],
            data["daily"]["temperature_2m_min"],
            data["daily"]["precipitation_sum"]):
        historical_data.append({
            "date": day,
            "max_temp": celsius_to_fahrenheit(max_temp),
            "min_temp": celsius_to_fahrenheit(min_temp),
            "precipitation": precip
        })
    return historical_data

def get_weather_data(latitude, longitude):
    weather_data = {
        "Location": {
            "latitude":latitude,
            "longitude":longitude
        },
        "current_temperature": get_current_temperature(latitude, longitude),
        "weekly_forecast": get_weekly_forecast(latitude, longitude),
        "historical_precipitation": get_historical_data(latitude, longitude)
    }
    return weather_data

zips = {}
repath = r"/(\d{5})"
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Access the requested URL path
        requested_path = self.path
        print(f"Requested URL: {requested_path}")

        match = re.match(repath, requested_path)
        code = 404
        if match:
            zip_code = match.group(1)
            if zip_code in zips:
                latitude, longitude = zips[zip_code]
                response = get_weather_data(latitude, longitude)
                code = 200
            else:
                response = { "error": "Zip code not found" }
        else:
            response = { "error": "path not found" }

        self.send_response(200)
        self.send_header("Content-type", "text/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

# Read the zip code data from the CSV file
with open('uszips.csv', mode='r') as file:
    reader = csv.DictReader(file)
    
    # Loop through the rows in the file
    for row in reader:
        zips[row['zip']] = (float(row['lat']), float(row['lng']))

# Define server address and port
server_address = ('', 8000)  # '' means listen on all available interfaces
httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)

print("Serving on port 8000...")
httpd.serve_forever()