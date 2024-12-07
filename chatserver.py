
from datetime import datetime
from globalname import *

async def handlechatmsg(username, jsonmsg, client):
    print(f"Received message from {username}: {jsonmsg}")
    msg = json.loads(jsonmsg)
    current_timestamp = datetime.now().timestamp()
    newmessage = {}#create a empty newmessage in case it need to be sent later
    if msg['type'] == "chatmsg":
        newmessage = {"type": "chatmsg", "username": gamenamelist[username], "time": current_timestamp, "message": msg["message"]}

    elif msg['type'] == "trade":
        giveaway = int(msg["num"][0])
        request = int(msg["num"][1])
        global_state["totaltraderequestcount"] += 1
        newmessage = {"type": "trade", "tradeid": global_state["totaltraderequestcount"], "username": gamenamelist[username], "time": current_timestamp, "traded": 0, "num":[giveaway, request]}

    elif msg['type'] == "accept_trade":
        currentuseraccountname = username
        requestinguseraccountname = ''
        currenttradeid = int(msg['tradeid'])
        tradedetails = findtradeinfofromid(currenttradeid)
        if tradedetails is None:
            return
        if(tradedetails['traded'] != 0):
            newmessage = {"alert": "Trade closed"}
            await client.send(json.dumps(newmessage))
            return
        print(tradedetails)

        for key, value in gamenamelist.items():
            if value == tradedetails['username']:
                requestinguseraccountname = key
                break
        #print(currentuseraccountname)
        #print(requestinguseraccountname)
        if(currentuseraccountname == requestinguseraccountname):
            newmessage =  {"alert": "Can't trade with yourself"}
            await client.send(json.dumps(newmessage))
            return
        user_data = load_user_data()
        trade_nums = tradedetails["num"]#list first element is the requesting

        # Check if the current user has the card to trade
        if user_data[currentuseraccountname]['cardset'][str(trade_nums[1])] > 0:
            #print(user_data[currentuseraccountname]['cardset'][str(trade_nums[1])])
            # Check if the requesting user still has the card to trade
            if user_data[requestinguseraccountname]['cardset'][str(trade_nums[0])] > 0:
                #print(user_data[requestinguseraccountname]['cardset'][str(trade_nums[0])])
                user_data[requestinguseraccountname]["cardset"][str(trade_nums[0])] -= 1
                user_data[currentuseraccountname]["cardset"][str(trade_nums[1])] -= 1
                user_data[currentuseraccountname]["cardset"][str(trade_nums[0])] += 1
                user_data[requestinguseraccountname]["cardset"][str(trade_nums[1])] += 1
                save_user_data(user_data)
                #print('trade success')
                updatetradedstatusfromid(currenttradeid, gamenamelist[username])
                newmessage = {"alert": "Trade success"}
                await client.send(json.dumps(newmessage))
                newmessage = {"type": "updatetrade", "tradeid": currenttradeid, "tradeduser": gamenamelist[username]}#broadcast this msg later on in real time
            else:
                newmessage = {"alert": tradedetails['username'] + "no longer have that card!"}
                await client.send(json.dumps(newmessage))
                return
        else:
            newmessage = {"alert": "You do not have the request card!"}
            await client.send(json.dumps(newmessage))
            return
    else:
        return

    chat_log = load_chat_log()
    chat_log["msg"].append(newmessage)
    save_chat_log(chat_log)

    for client in connected_ws_clients:
        await client.send(json.dumps(newmessage))