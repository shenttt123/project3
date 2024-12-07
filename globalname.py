import json
import os

gamenamelist = {}#store game to easy find the name instead of reading json file all the time
earnings = {}#store earnins same reason as above

#store connected websocket clients for chat function. select the websocket to communicate with, if select all, then it is broadcast.
connected_ws_clients = []

#use a list global_State because python doesn't take int as global variable
global_state = {
    #track unique id for the trade for easy modify trade status in the future
    "totaltraderequestcount": 0
}

user_data_file = "user.json"
CHAT_LOG_FILE = "chat_log.json"

def save_user_data(users):
    """Save user data to user.json."""
    with open(user_data_file, "w") as file:
        json.dump(users, file, indent=4)

def load_user_data():
    user_data_file = "user.json"
    try:
        with open(user_data_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def load_chat_log():
    try:
        with open(CHAT_LOG_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_chat_log(chat_log):
    with open(CHAT_LOG_FILE, "w") as file:
        json.dump(chat_log, file, indent=4)

def update_earning_json(username, updated_earnings):
    user_data = load_user_data()
    if username in user_data:
        user_data[username]["earnings"] = updated_earnings
    else:
        return
    with open(user_data_file, "w") as f:
        json.dump(user_data, f, indent=4)

def intitdatafile():
    #create the files if not exist, also json need to first written  {}
    if not os.path.exists(user_data_file):
        with open(user_data_file, "w") as file:
            json.dump({}, file, indent=4)
    if not os.path.exists(CHAT_LOG_FILE):
        with open(CHAT_LOG_FILE, "w") as file:
            json.dump({}, file, indent=4)

    chat_log = load_chat_log()
    #msg attribute need to be written too
    if "msg" not in chat_log:
        chat_log["msg"] = []
        save_chat_log(chat_log)

    user_data = load_user_data()

    #if admin account not exist, create it
    makeAdminaccount(user_data)

    for username in user_data:
        #init the two local variable
        earnings[username] = user_data.get(username, {}).get("earnings", 0)
        gamenamelist[username]  = user_data.get(username, {}).get("gamename", 0)
    for entry in chat_log["msg"]:
        try:
            if(entry["type"] == "trade"):
                #init the trade count id
                global_state["totaltraderequestcount"] += 1
        except:
            pass
    #print(global_state["totaltraderequestcount"])


def findtradeinfofromid(tradeid):
    chat_log = load_chat_log()
    #print('in find')
    #print(tradeid)
    for entry in chat_log["msg"]:
        try:
            if(entry["type"] == "trade"):
                #print(f"entry['tradeid']: {entry['tradeid']} (type: {type(entry['tradeid'])})")
                #print(f"tradeid: {tradeid} (type: {type(tradeid)})")
                if(entry['tradeid'] == tradeid):
                    #print('match!!!!!!')
                    return entry
        except:
            pass
    return None

def updatetradedstatusfromid(tradeid, tradedusername):
    chat_log = load_chat_log()
    updated = False

    for entry in chat_log.get("msg", []):  # Use .get() to avoid KeyError
        if entry.get("type") == "trade" and entry.get("tradeid") == tradeid:
            entry["traded"] = tradedusername
            updated = True
            break  # Exit the loop after finding and updating the match

    if updated:
        save_chat_log(chat_log)
    else:
        print(f"No trade entry found with tradeid: {tradeid}")


def makeAdminaccount(users):
    if('admin' not in users):
        cardset = {str(i): 9999 for i in range(1, 21)}
        newgamename = 'game god'
        earnings['admin'] = 9999999
        gamenamelist['admin'] = newgamename
        users['admin'] = {
            "password": 'tufts',
            "gamename": gamenamelist['admin'],
            "earnings": earnings['admin'],
            "cardset": cardset
        }
        save_user_data(users)
        print('god account made')