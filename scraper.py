import requests
from time import time
import re

def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    """Source: Stack Overflow"""
    if not isinstance(number, int):
        raise TypeError('number must be an integer')
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36

def getRequest(url):
    responseSuccess = False
    while responseSuccess == False:
        request = requests.get(url)
        print(request)
        if repr(request) == '<Response [200]>': # Success
            responseSuccess = True
            json_response = request.json()
        else: # Failed, probably timed out or smth
            print('Retrying...')
    return json_response

class Interact:
    def __init__(self, interactId, interactType, rp):
        self.interactId = interactId
        self.interactType = interactType
        self.rp = rp

# first one for profile calls, second one for attacks
reg = ['[🥇🥈🥉🏅] Rank: ([ABCDESX]+) \(((\d+,\d+)|\d+) Rank Points\)', '🏅 [+-](.\d+) RP']

with open('rp.txt', 'w') as f:
    before = round(time()) # Start searching from current time
    before = 1675321200
    calls = 0 # number of calls
    players = {} # dict of players
    seasonStart = 1675278000 # 19:00 Feb 1 2023 GMT
    searching = True

    while searching:
        interactString = ''
        interactList = {}
        url = f"https://api.pushshift.io/reddit/search/comment/?author=KickOpenTheDoorBot&before={before}&size=500"

        # Getting bot comments
        json_response = getRequest(url)

        # Processing all bot comments        
        for comment in json_response['data']:
            if comment['stickied'] == True: pass
            if before <= seasonStart:
                searching = False
                break
            try:
                interactString += f"{base36encode(comment['parent_id'])},"
                if 'Rank:' in comment['body']: # profile call
                    rp = int(re.search(reg[0], comment['body']).group().split(' ')[3].replace('(', '').replace(',', '')) # get RP in profile call
                    interactList.update({base36encode(comment['parent_id']): Interact(comment['id'], 'profile', rp)})
                elif 'Damage Breakdown' in comment['body']: # attack
                    rp = int(re.search(reg[1], comment['body']).group().split(' ')[1].replace('+', '')) # get gained RP in attack
                    interactList.update({base36encode(comment['parent_id']): Interact(comment['id'], 'attack', rp)})
                else: # something else
                    interactList.update({base36encode(comment['parent_id']): Interact(comment['id'], 'other', 0)})
            except TypeError: pass
            before = comment['created_utc']
            beforestamp = comment['utc_datetime_str']

        # Getting player interacts from bot comments
        url = f"https://api.pushshift.io/reddit/search/comment/?ids={interactString[:-1]}&size=500"
        json_response = getRequest(url)

        # Processing player interacts
        # Every player gets an entry in the players variable. Key is player name, value is array of every interact they've made
        for comment in json_response['data']:
            interactHistory = players.get(comment['author'], [])
            interactHistory.append(interactList[comment['id']])
            newdict = {comment['author']: interactHistory}
            players.update(newdict)

        # Progress check
        calls += 1
        print(f'{calls} calls done, currently searching {beforestamp}')

    for player in players:
        interactHistory = players.get(player)
        
        # Finding most recent profile call
        lastProfile = len(interactHistory) - 1
        for index, value in enumerate(interactHistory):
            if value.interactType == 'profile':
                lastProfile = index
                break

        # Summing up gained RP since most recent profile
        rp = 0
        for i in range(lastProfile + 1):
            rp += interactHistory[i].rp

        # Writing result to file    
        f.write(f'{player}, {rp}\n')
