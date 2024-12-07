import asyncio
import uuid
import random
import websockets
from aiohttp import web
from chatserver import *
from globalname import *

demomode = 0
sessions = {}# Dictionary to store active sessions
# Server configuration
HOST = "0.0.0.0"
PORT = 8888
WS_PORT = 5678

box_data = {
    1: [5,9,13,17,21],
    2: [6,10,14,18,22],
    3: [7,11,15,19,23],
    4: [8,12,16,20,24]
}
probabilities = [0.6,0.2,0.19,0.009,0.001]

# Function to get the image name based on ID
def getimagename(idstr):
    id = int(idstr)
    if id < 5 and id > 0:
        return "box" + str(id) + ".jpg"
    elif id > 4 and id < 25:
        return "card" + str(id - 4) + ".jpg"
    else:
        return None

# Function to read HTML file contents
def read_html_file(filename):
    html_folder = "html"  # Specify the folder name
    file_path = os.path.join(html_folder, filename)  # Combine folder and filename

    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return None

# Function to send error response
def senderror(index):
    if index == 400:
        response = """
        <html>
            <body>
                <h1>400 Bad Request</h1>
                <p>Your request could not be understood by the server.</p>
                <button onclick="goHome()">Back</button>
                <script>
                    function goHome() {
                        window.location.href = "/";
                    }
                </script>
            </body>
        </html>
        """
        return web.Response(content_type="text/html", body=response.encode() , status=index)
    elif index == 401:
        response = """
        <html>
            <body>
                <h1>401 Unauthorized</h1>
                <p>unauthorized acces</p>
                <button onclick="goHome()">Back</button>
                <script>
                    function goHome() {
                        window.location.href = "/";
                    }
                </script>
            </body>
        </html>
        """
        return web.Response(content_type="text/html", body=response.encode() , status=index)
    elif index == 404:
        response = """
        <html>
            <body>
                <h1>404 Not Found</h1>
                <p>The requested resource could not be found.</p>
                <button onclick="goHome()">Back</button>
                <script>
                    function goHome() {
                        window.location.href = "/";
                    }
                </script>
            </body>
        </html>
        """
        return web.Response(content_type="text/html", body=response.encode() , status=index)
    elif index == 409:
        response = """
        <html>
            <body>
                <h1>409 User Already Exists</h1>
                <p>Please try another Username or gamename.</p>
                <button onclick="goHome()">Back</button>
                <script>
                    function goHome() {
                        window.location.href = "/";
                    }
                </script>
            </body>
        </html>
        """
        return web.Response(content_type="text/html", body=response.encode() , status=index)
    elif index == 500:
        response = """
        <html>
            <body>
                <h1>500 Internal Server Error</h1>
                <p>The server encountered an error and could not complete your request.</p>
                <button onclick="goHome()">Back</button>
                <script>
                    function goHome() {
                        window.location.href = "/";
                    }
                </script>
            </body>
        </html>
        """
        return web.Response(content_type="text/html", body=response.encode() , status=index)
    else:
        response = """
        <html>
            <body>
                <h1>Unknown Error</h1>
                <p>An unknown error occurred.</p>
                <button onclick="goHome()">Back</button>
                <script>
                    function goHome() {
                        window.location.href = "/";
                    }
                </script>
            </body>
        </html>
        """

        return web.Response(content_type="text/html", body=response.encode() , status=index)


#check cookie of the broswer request session
def check_session(request):
    cookie_header = request.cookies.get('session_id', None)
    if cookie_header:
        return sessions.get(cookie_header)
    return None


# HTTP route handlers using aiohttp
async def handle_home(request):
    print("New connection")
    username = check_session(request)
    if username is None:
        response = read_html_file('login.html')
        if(demomode == 1):
            announcement_html = """
            <div class="announcement"> <label for="announcement">Demo Mode:</label> 
            <textarea id="announcement" rows="4" disabled>username: admin
            \r\npassword: tufts</textarea> <br> <a href="https://github.com/shenttt123/project3" target="_blank">
            For Soucre Code, please this link </a> </div>
            """
            response = response.replace("<!-- ANNOUNCEMENT_PLACEHOLDER -->", announcement_html)
        return web.Response(content_type="text/html", body=response.encode())

    response = read_html_file("main.html")
    response = response.replace("{{username}}", gamenamelist[username])
    if (demomode == 1):
        announcement_html = """
            <div class="announcement"> <label for="announcement">Demo Mode:</label> <textarea id="announcement" rows="3" disabled>"""
        announcement_html += "cookie is " + request.cookies.get('session_id')
        announcement_html += """
            </textarea> </div>
        """
        response = response.replace("<!-- ANNOUNCEMENT_PLACEHOLDER -->", announcement_html)
    return web.Response(content_type="text/html", body=response.encode())

async def handle_registerpage(request):
    response = read_html_file("register.html")
    return web.Response(content_type="text/html", body=response.encode())

async def handle_login(request):
    if request.method != "POST":
        response = senderror(400)
        return response

    data = await request.post()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        response = senderror(401)
        return response

    users = load_user_data()

    if username in users and users[username]["password"] == password:
        session_id = str(uuid.uuid4())
        sessions[session_id] = username
        response = web.HTTPFound('/')

        # Set session cookie for 1 hour
        response.set_cookie('session_id', session_id, max_age=3600)

        return response
    else:
        return senderror(401)

async def handle_register(request):
    data = await request.post()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    gamename = data.get("gamename", "").strip()

    if not username or not password or not gamename:
        return senderror(400)

    if len(username) < 3 or len(password) < 3 or len(gamename) < 3:
        return senderror(400)

    users = load_user_data()
    if username in users:
        return senderror(409)
    else:
        for user, details in users.items():
            if details.get("gamename") == gamename:
                return senderror(409)  # Conflict: Gamename already exists
        gamenamelist[username] = gamename
        users[username] = {
            "password": password,
            "gamename": gamename,
            "earnings": 0,
            "cardset":{}
        }
        earnings[username] = 0
        users[username]["cardset"] = {str(i): 0 for i in range(1, 21)}  # Initialize card counts for IDs 1 to 20
        save_user_data(users)

        response = read_html_file('registersucc.html')
        return web.Response(content_type="text/html", body=response.encode())

async def handle_logout(request):
    session_cookie = request.cookies.get('session_id')
    if session_cookie in sessions:
        del sessions[session_cookie]

    response = web.HTTPFound('/')
    response.set_cookie('session_id', '', expires=0)
    return response

async def handle_css(request):
    response = read_html_file('styles.css')
    return web.Response(content_type="text/css", body=response.encode())


async def handle_background(request):
    with open('image/back.jpg', 'rb') as image_file:
        image_data = image_file.read()
    return web.Response(content_type="image/jpeg", body=image_data)


async def handle_package(request):
    username = check_session(request)
    if username is None:
        raise web.HTTPFound("/")
    response = read_html_file('packages.html')
    response = response.replace("{{totalmoney}}", str(earnings[username]))
    if demomode:
        announcement_html = """
        <div class="announcement"> <label for="announcement">Demo Mode:</label> 
        <textarea id="announcement" rows="16" disabled>
        normal probabilities:
         free 60%
         common 20%
         rare 19%
         epic 0.9%
         legendary 0.1%
         
        demo probabilities
         free 30%
         common 25%
         rare 20%
         epic 15%
         legendary 10%
         
        </textarea></div>
        """
        response = response.replace("<!-- ANNOUNCEMENT_PLACEHOLDER -->", announcement_html)

    return web.Response(content_type="text/html", body=response.encode())

async def handle_img(request):
    image_id = request.match_info.get("id", "1")  # Default to "1" if no ID is provided
    image_name = getimagename(image_id)

    if image_name:
        image_path = os.path.join("image", image_name)
        if os.path.exists(image_path):
            return web.FileResponse(image_path)
        else:
            return senderror(404)
    else:
        return senderror(400)

async def handle_user_card(request):
    username = check_session(request)
    if not username:
        return senderror(401)
    user_data = load_user_data()
    cardsetarr = user_data[username]['cardset']

    return web.json_response({"cardset": cardsetarr})

async def handle_carddraw(request):
    boxid = int(request.match_info.get("boxnumber", 0))
    username = check_session(request)
    if not username:
        return senderror(401)
    if boxid not in box_data:
        return senderror(400)

    if demomode:
        cards = random.choices(box_data[boxid], weights=[0.3, 0.25, 0.20, 0.15, 0.1], k = 5)
    else:
        cards = random.choices(box_data[boxid], weights=probabilities, k=5)
    print(cards)
    user_data = load_user_data()

    if user_data[username]["earnings"] < 100:
        return web.json_response({"msg": "insufficient fund"})

    earnings[username] -= 100
    user_data[username]["earnings"] = earnings[username]

    for card_id in cards:
        user_data[username]["cardset"][str(card_id - 4)] += 1
    save_user_data(user_data)
    return web.json_response({"cardnum": cards, "earnings": earnings[username]})

async def handle_chatpage(request):
    username = check_session(request)
    if username is None:
        raise web.HTTPFound("/")

    response = read_html_file('chat.html')
    response = response.replace("{{accountusername}}", username)

    return web.Response(content_type="text/html", body=response.encode())

async def handle_chathistory(request):
    chat_history = load_chat_log()
    return web.json_response(chat_history)

async def handle_earn_money(request):
    username = check_session(request)
    if username is None:
        raise web.HTTPFound("/")

    response = read_html_file('earn-money.html')
    response = response.replace("{{gameusername}}", gamenamelist[username])
    response = response.replace("{{accountusername}}", username)
    response = response.replace("{{totalmoney}}", str(earnings[username]))

    if demomode:
        announcement_html = """
        <div class="announcement"> <label for="announcement">Demo Mode:</label> 
        <textarea id="announcement" rows="4" disabled>Deme Mode income x 100 </textarea></div>
        """
        response = response.replace("<!-- ANNOUNCEMENT_PLACEHOLDER -->", announcement_html)

    return web.Response(content_type="text/html", body=response.encode())

async def start_http_server():
    app = web.Application()

    # Define routes
    app.router.add_get('/', handle_home)
    app.router.add_post('/login', handle_login)
    app.router.add_post('/register', handle_register)
    app.router.add_get('/regpage', handle_registerpage)
    app.router.add_get('/logout', handle_logout)
    app.router.add_get('/earn-money', handle_earn_money)
    app.router.add_get('/styles.css', handle_css)
    app.router.add_get('/background', handle_background)
    app.router.add_get('/packages', handle_package)
    app.router.add_get('/image/{id}', handle_img)
    app.router.add_get('/fetchusercard', handle_user_card)  # Endpoint to fetch user cards
    app.router.add_get('/draw/{boxnumber}', handle_carddraw)  # Endpoint to draw cards
    app.router.add_get("/online-trade", handle_chatpage)
    app.router.add_get("/loadchat", handle_chathistory)

    # Start the HTTP server
    print(f'Server running on http://{HOST}:{PORT}')
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()

async def websocket_handler(websocket):
    try:
        initial_message = await websocket.recv()
        user_info = json.loads(initial_message)
        username = user_info.get("username")

        type = user_info.get("type")

        if not type:
            await websocket.close()
            return

        connected_ws_clients.append(websocket)
        print(f"WebSocket client connected: {username} type is {type}")

        if type == "earnmoney":
            user_data = load_user_data()
            earnings[username] = user_data.get(username, {}).get("earnings", 0)

            async for message in websocket:
                print(f"Received message from {username}: {message}")
                try:
                    earnings[username] += int(message) * 100 if demomode else int(message)
                    update_earning_json(username, earnings[username])
                    await websocket.send(json.dumps({"username": username, "earnings": earnings[username]}))
                except ValueError:
                    print(f"Invalid message received from {username}: {message}")
        elif type == "chat":
            async for message in websocket:
                await handlechatmsg(username, message, websocket)
    except Exception as e:
        print(f"Error handling chat message: {e}")
    finally:
        connected_ws_clients.remove(websocket)

async def websocket_server():
    """Run the WebSocket server."""
    print(f"Starting WebSocket server on ws://{HOST}:{WS_PORT}")
    async with websockets.serve(websocket_handler, HOST, WS_PORT):
        await asyncio.Future()  # Keeps the WebSocket server running

async def main():
    await asyncio.gather(
        start_http_server(),
        websocket_server()
    )


if __name__ == "__main__":
    intitdatafile()
    asyncio.run(main())