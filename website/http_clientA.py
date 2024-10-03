
import socket
import time
import base64

class HttpClient:
    def __init__(self, proxy_address):
        self.proxy_address = proxy_address
        self.authenticated = False
        self.credentials = None
        self.key = None
    def authenticate(self, credentials):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(self.parse_proxy_address(self.proxy_address))
            # Send credentials to the proxy for authentication
            client_socket.sendall(f"{credentials[0]}:{credentials[1]}".encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            if response != "Authentication failed. Please try again.":
                self.key = response
                self.authenticated = True
                self.credentials = credentials
                return True
            else:
                print("Authentication failed. Exiting.")
                return False
    def send_request(self,url):
        
        # Create a socket connection to the proxy server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(self.parse_proxy_address(self.proxy_address))
            authenticated = self.authenticated
            if not authenticated:
                return False
            
            if authenticated:
                # Parse the URL to extract the hostname and path
                hostname, path = self.parse_url(url)
                # Construct the HTTP request
                http_request = f"GET {path} HTTP/1.1\r\nHost: {hostname}\r\n\r\n" + ":" + self.key
    
                # Send the request to the proxy server
                client_socket.sendall(http_request.encode("utf-8"))
    
                # Receive the response from the proxy
                response = client_socket.recv(4096).decode("utf-8")
                print(f"La responsia: {response}")
                # Process the response and return it
                return response
        #if its not working just remove it from here    
    def download_file(self,file_url):
          with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
               authenticated = self.authenticated
               client_socket.connect(self.parse_proxy_address(self.proxy_address))
               if not authenticated:
                   return False
               if authenticated:    
                   github_url = file_url
                   request = "GET " + github_url + " HTTP/1.1\n\n" + ":" + self.key
                   client_socket.send(request.encode('utf-8'))
                   print(request)
                   response = client_socket.recv(2048).decode()
                   print(response)
                   
                   file_content = client_socket.recv(2048).decode()
                   print(file_content)
                   return True
                   # Handle the file content as needed
    
    @staticmethod
    def parse_url(url):
        # Extract hostname and path from the URL
        url_parts = url.split('/', 3)
        hostname = url_parts[2]
        path = f'/{url_parts[3]}' if len(url_parts) > 3 else '/'
        return hostname, path

    @staticmethod
    def parse_proxy_address(proxy_address):
        # Parse the proxy address to get the IP address and port
        parts = proxy_address.split(':')
        return parts[0], int(parts[1])
    def is_authenticated(self):
        if self.authenticated : 
            return True
        return False

