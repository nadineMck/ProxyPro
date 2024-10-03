from flask import Flask, render_template, request,redirect
from http_clientA import HttpClient
from test1 import emailer
app = Flask(__name__)
client = HttpClient(proxy_address='127.0.0.1:8000')
sender= emailer()

@app.route('/')
def index():
    if client.is_authenticated() : 
        return redirect('/dashboard')
    return render_template('welcome.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not client.is_authenticated() : 
        return redirect('/')
    return render_template('authenticated.html', username= client.credentials[0])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if client.is_authenticated() : 
        return redirect('/dashboard')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if client.authenticate((username,password)):
            # Authentication successful
            return redirect('/dashboard')
        else:
            # Authentication failed
            return render_template('login_failed.html')

    # If it's a GET request or the form submission failed, render the login page
    return render_template('index.html')

@app.route('/action', methods=['POST'])
def choose_action():
    if not client.is_authenticated(): 
        return redirect('/')
    choice = request.form['choice']

    if choice == '1':
        # Access a website
        return render_template('access_website.html')
    elif choice == '2':
        # Download a file
        return render_template('download_file.html')
    elif choice == '3':
        # Download a file
        return render_template('email_file.html')
    else:
        return render_template('invalid_choice.html')

@app.route('/perform_action', methods=['POST'])
def perform_action():
    if not client.is_authenticated(): 
        return redirect('/')
    choice = request.form['choice']

    if choice == '1':
        # Access a website
        if 'url' in request.form:
            url = request.form['url']
            # Use the HttpClient send_request method with the provided URL
            response = client.send_request(url)
            if not response:
                return redirect('/')
            print("Got einen response")
            # Display the result to the user
            return render_template('result.html', result=response)
        else:
            # Handle the case where 'url' is not present in the form data
            return render_template('invalid_choice.html')

    elif choice == '2':
        # Download a file
        if 'file_url' in request.form:
            file_url = request.form['file_url']
            # Use the HttpClient download_file method with the provided file URL
            response = client.download_file(file_url)
            if response:
                 return render_template('result.html', result="Successfully downloaded file")
            # Display the result to the user
            else:
                return render_template('result.html', result="Failed to download file")
           
        else:
            # Handle the case where 'file_url' is not present in the form data
            return render_template('invalid_choice.html')
        
    elif choice == '3':
        # Use the HttpClient send_request method with the provided URL
        try:
            sender.send()
            return render_template('result.html', result="Successfully sent email")
        
        except Exception as e:
            return render_template('result.html', result=e)
        
    else:
        return render_template('invalid_choice.html')

if __name__ == '__main__':
    app.run(debug=True)
