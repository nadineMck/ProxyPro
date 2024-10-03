# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 16:04:48 2023

@author: User
"""


import socket
import threading
import re
from datetime import datetime, timedelta
from email.utils import formatdate, parsedate_to_datetime
import pickle
import signal
import sys
import time
import base64
import requests
from uuid import uuid4

class HttpProxy:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.proxy_username = "user"  
        self.proxy_password = "password"
        self.cache_file = 'cache.pkl'
        self.cache_save_interval = timedelta(seconds=5)
        self.uuid_list = []
        self.load_cache()
        #Add IP addresses to the blacklist 
        self.blacklist = ["192.168.0.2", "10.0.0.5"]
        # Add destination IP addresses to the blacklist
        self.destination_blacklist = ["192.168.0.10", "10.0.0.7"]  
        #Create source_destination blacklist
        self.source_destination_blacklist = [
            {"source": "192.168.0.1", "destination": "10.0.0.1"},
            {"source": "192.168.0.2", "destination": "10.0.0.2"},
            # Add more pairs as needed
        ]
        #Rules for attacks
        self.waf_rules = [
            r"(?i)<script.*?>.*?<\/script.*?>",  # Example rule for detecting script tags
            r"(?i)<.*?on[a-z]+\s*=\s*\"[^\"]+\".*?>",  # Example rule for detecting event attributes
            # Add more rules as needed
        ]
        self.sql_injection_patterns= [
        r'\b(?:select|union|insert|update|delete|from|where)\b',
        r'\b(?:exec|sp_executesql|xp_cmdshell)\b',
        r'\b(?:alter|create|drop)\b\s+(?:table|database|procedure)',
        r'\b(?:--|#|\/\*)[^\n]*\b'  # Detect comments for comment-based injection
        ]
        
        # Start a thread to periodically save the cache
        threading.Thread(target=self.periodic_cache_maintenance).start()
        
        
    def remove_expired_cache_entries(self):
        current_time = datetime.now()

        # Create a list of cache keys to remove
        keys_to_remove = [key for key, entry in self.cache.items() if 'expiration_time' in entry and entry['expiration_time'] is not None and current_time.timestamp() > entry['expiration_time'].timestamp()]

        # Remove the expired entries from the cache
        for key in keys_to_remove:
            print(f"[*] Removing expired cache entry for {key}")
            del self.cache[key]

        # Save the updated cache
        self.save_cache()
        
        
    def apply_waf(self, data):
        # Apply WAF rules to the provided data
        for rule in self.waf_rules:
            if re.search(rule, data):
                return True  # WAF detected a potential attack
        for rule in self.sql_injection_patterns:
            if re.search(rule,data):
                return True
        return False    
    
    def check_blacklist(self, client_address):
        # Check if the client's IP address is in the blacklist
        return client_address[0] in self.blacklist
    
    def check_destination_blacklist(self, destination_address):
        # Check if the destination IP address is in the blacklist
        return destination_address[0] in self.destination_blacklist
    
    def check_source_destination_blacklist(self, source_address, destination_address):
        # Check if the source-destination pair is in the blacklist
        return {"source": source_address[0], "destination": destination_address[0]} in self.source_destination_blacklist
    
    def authenticate_user(self, client_socket):
        # Get credentials from the client
        basecreds =  client_socket.recv(1024) 
        credentials = basecreds.decode('utf-8').strip().split(':')
        if credentials[-1] in self.uuid_list:             
            return basecreds
        elif len(credentials) == 2 and credentials[0] == self.proxy_username and credentials[1] == self.proxy_password:
            uuid = str(uuid4())
            
            self.uuid_list.append(uuid)
            client_socket.sendall(uuid.encode("utf-8"))
            return True
        else:
            client_socket.sendall(b"Authentication failed. Please try again.")
            
            
    def load_cache(self):
        try:
            with open(self.cache_file, 'rb') as file:
                self.cache = pickle.load(file)
        except FileNotFoundError:
            self.cache = {}

    def save_cache(self):
        with open(self.cache_file, 'wb') as file:
            pickle.dump(self.cache, file)
            
    def periodic_cache_maintenance(self):
        while True:
            # Perform cache save
            self.save_cache()

            # Remove expired entries from the cache
            self.remove_expired_cache_entries()
            
            # Sleep for the specified interval
            time.sleep(self.cache_save_interval.total_seconds())

    def start(self):
        # Create a server socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the server socket to a specific address and port
        server.bind((self.address, self.port))

        # Start listening for incoming connections
        server.listen(5)
         
        # Start a thread for periodic cache maintenance
        threading.Thread(target=self.periodic_cache_maintenance).start()
        
        print(f'[*] Proxy Server listening on {self.address}:{self.port}')

        while True:
            # Accept an incoming connection
            client, addr = server.accept()
            print(f'[*] Accepted connection from {addr[0]}:{addr[1]}')

            # Create a thread to handle the client
            client_handler = threading.Thread(target=self.handle_client, args=(client,))
            client_handler.start()

    def extract_destination_host(self, request_data):
        # Extract the host from the client's request
        host_match = re.search(rb'Host: ([^\r\n]+)', request_data)
        if host_match:
            # Separate host and port if included in the host
            destination_host_port = host_match.group(1).decode('utf-8')
            destination_parts = destination_host_port.split(':')
            if len(destination_parts) == 2:
                return destination_parts[0], int(destination_parts[1])
            else:
                return destination_host_port, 80  # Default to port 80 if not specified
        else:
            # Default to www.example.com if Host header is not present
            return 'www.example.com', 80
    def extract_url_from_request(self,request_data):
        # Assuming the request_data is a bytes object
        request_str = request_data.decode('utf-8')
    
        # Split the request string by spaces to get individual components
        request_parts = request_str.split()
    
        # Assuming the URL is the second component in the request
        if len(request_parts) > 1:
            url = request_parts[1]
            return url
    
        return None 
    def handle_client(self, client_socket):
     try:
         
         # Get the client's address
        client_address = client_socket.getpeername()
        # Print when the request is received from the user
        print(f"[1] Received request from {client_address} at {datetime.now()}")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Check if the client's IP address is in the blacklist
        if self.check_blacklist(client_address):
            client_socket.sendall(b"HTTP/1.1 403 Forbidden\n\nAccess Denied. This IP address is blacklisted.")
            return
         
         
        response = self.authenticate_user(client_socket)
        print(response)
        request_data = None
        if not response:
            return
        # Receive the client's request data
        elif not type(response) is bool:
            request_data = response
        else :
            request_data = client_socket.recv(4096)
        print(request_data,"HEYEYEYEYEY")
        
        # Apply WAF to the request data
        if self.apply_waf(request_data.decode('utf-8')):
            client_socket.sendall(b"HTTP/1.1 403 Forbidden\n\nAccess Denied. Potential attack detected.")
            self.blacklist.append(client_address)
            return
        
        # Extract the destination host and port from the client's request
        destination_info = self.extract_destination_host(request_data)
        if destination_info is None:
            raise ValueError("Failed to extract destination information from the request.")
            
        destination_host, destination_port = destination_info  

        # Print when the proxy sends a request to the web server
        print(f"[2] Proxy sending request to {destination_host}:{destination_port} at {datetime.now()}")  
        # Check if the destination IP address is in the blacklist
        destination_address = (socket.gethostbyname(destination_host), destination_port)
        if self.check_destination_blacklist(destination_address):
            client_socket.sendall(b"HTTP/1.1 403 Forbidden\n\nAccess Denied. This destination IP address is blacklisted.")
            return
        source_destination_pair = {
                "source": client_address[0],
                "destination": socket.gethostbyname(destination_host),
            }
        if self.check_source_destination_blacklist(client_address, (destination_host, destination_port)):
            client_socket.sendall(b"Access Denied. This source-destination pair is blacklisted.")
            return

        print(f"[*] Destination Host: {destination_host}, Destination Port: {destination_port}")
        #ill add here the code to download a file
        
        approved_extensions = ['xlsx', 'ppt', 'pdf']
        if any(ext in request_data.decode() for ext in approved_extensions):
             url = self.extract_url_from_request(request_data)
             response = requests.get(url)
             response.raise_for_status()
             
             file_path = "C:/Users/User/Documents/project.xlsx"
             

             # Write only the content to the file
             with open(file_path, 'wb') as file:
                  file.write(response.content)
             #with open(file_path, 'wb') as file:
              #  file.write(content)
             print("File downloaded and saved at:", file_path)
             client_socket.send("HTTP/1.1 200 OK\n\nFile downloaded successfully".encode())
             return
        # Check cache for the URL
        cache_key = f"{destination_host}:{destination_port}"
        if cache_key in self.cache:
            expiration_time = self.cache[cache_key].get('expiration_time', None)

            # If there's an expiration time and it has passed, consider the content expired
            if expiration_time and datetime.now().timestamp() > expiration_time.timestamp():
                print(f"[*] Cache expired for {cache_key}")
                
            else:    
                last_modified_timestamp = self.cache[cache_key].get('last_modified', None)
                conditional_request = f"GET / HTTP/1.1\r\nHost: {destination_host}\r\n"
            if last_modified_timestamp:
                conditional_request += f"If-Modified-Since: {formatdate(timeval=last_modified_timestamp.timestamp(), localtime=False, usegmt=True)}\r\n"

            conditional_request += "\r\n"
            # Forward a conditional request to the destination server
            
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((destination_host, destination_port))
            server_socket.send(conditional_request.encode())

            # Receive the response from the destination server
            response_data = server_socket.recv(4096)
            

            print(f"Uno responsia {response_data}")
            # Check if the content has been modified
            if b"304 Not Modified" not in response_data:
                print(f"[*] Updating Cache for {cache_key}")
                
                # Update cache with the new response and timestamp + expiration time if present
                last_modified_header = re.search(rb'Last-Modified: ([^\r\n]+)', response_data)
                expiration_header = re.search(rb'Expires: ([^\r\n]+)', response_data)
                last_modified_timestamp = parsedate_to_datetime(last_modified_header.group(1).decode('utf-8')) if last_modified_header else None
                expiration_time = parsedate_to_datetime(expiration_header.group(1).decode('utf-8')) if expiration_header else None

                self.cache[cache_key] = {'response': response_data, 'last_modified': last_modified_timestamp, 'expiration_time': expiration_time}
                self.save_cache()
            else:
                print(f"[*] Serving from Cache for {cache_key}")
                # Serve the cached content
                print("Send cachedd")
                print(self.cache[cache_key]['response'])
                client_socket.sendall(self.cache[cache_key]['response'])
                return
        
        # Forward the original request to the destination server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((destination_host, destination_port))
        server_socket.send(request_data)

        # Receive the response from the destination server
        response_data = server_socket.recv(4096)
         #Print when the server responds to the proxy
        print(f"[3] Server response received from {destination_host}:{destination_port} at {datetime.now()}")
    

        # Forward the response back to the client
        print(f"La Responsia {response_data}")
        client_socket.send(response_data)
        # Print when the proxy sends the data to the client
        print(f"[4] Proxy sending data to {client_socket.getpeername()} at {datetime.now()}")
        
        print(f"[*] Forwarded response to {client_socket.getpeername()} at {datetime.now()}")

        print(f"[*] Response sent with the exact time: {datetime.now()}")

        print(f"[*] Request-Response cycle completed successfully")
        print("new info in my CACHE WOW")
        print(f"[*] Updating Cache for {cache_key}")
        
        # Update cache with the new response and timestamp
        last_modified_header = re.search(rb'Last-Modified: ([^\r\n]+)', response_data)
        last_modified_header = re.search(rb'Last-Modified: ([^\r\n]+)', response_data)
        expiration_header = re.search(rb'Expires: ([^\r\n]+)', response_data)
        last_modified_timestamp = parsedate_to_datetime(last_modified_header.group(1).decode('utf-8')) if last_modified_header else None
        expiration_time = parsedate_to_datetime(expiration_header.group(1).decode('utf-8')) if expiration_header else None

        self.cache[cache_key] = {'response': response_data, 'last_modified': last_modified_timestamp, 'expiration_time': expiration_time}
        self.save_cache()
             
        
     except Exception as e:
        print(f"Exception in handle_client: {e}")
     finally:
        # Close the sockets
        server_socket.close()
        client_socket.close()
        
    def signal_handler(self, sig, frame):
        # Save the cache when receiving a termination signal
        self.save_cache()
        sys.exit(0)

if __name__ == '__main__':
    # Set your desired username and password
    credentials = "your_username:your_password"

    # Create an instance of the HttpProxy class with credentials
    proxy = HttpProxy(address='127.0.0.1', port=8000)

    # Start the proxy server
    proxy.start()
