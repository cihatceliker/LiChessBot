import random, sys
import faster_than_requests as requests
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
from stockfish import Stockfish
from selenium.webdriver.common.action_chains import ActionChains
from login_info import username, password

def login():
    email_in = driver.find_element_by_xpath('//*[@id="form3-username"]')
    email_in.send_keys(username)
    sleep(1)
    pw_in = driver.find_element_by_xpath('//*[@id="form3-password"]')
    pw_in.send_keys(password)
    sleep(1)
    driver.find_element_by_css_selector(".submit").click()

def find_uci(ply, key):
    uci_found = False
    for pc in ply.split(":"):
        if uci_found:
            return pc.split(",")[0][1:-1]
        if pc[-len(key):] == key:
            uci_found = True

def find_ply(idx, script):
    for i in range(idx + 1, len(script)):
        if script[i] == "}":
            return script[idx:i]

def find_moves(key="{\"ply\""):
    script = request_script()
    moves = []
    sans = []
    for i in range(len(script) - len(key)):
        if script[i:i+len(key)] == key:
            moves.append(find_uci((tm:=find_ply(i, script)), key="\"uci\""))
            sans.append(find_uci(tm, key="\"san\""))
    return moves[1:], sans[1:]

def request_script():
    page = requests.get2str(driver.current_url)
    return BeautifulSoup(page, 'html.parser').find_all("script")[2].string

def click_to_coordinate(x, y):
    ac = ActionChains(driver)
    elem = driver.find_element_by_id("main-wrap")
    ac.move_to_element(elem).move_by_offset(left_bottom_x + x * width, left_bottom_y - y * width).click().perform()

def act(move, sleep_time):
    # "e2e4"
    #if move in {
    #    "e8h8": "e8g8"
    #}:
    f, t = get_coordinates(move[:2]), get_coordinates(move[2:])
    click_to_coordinate(*f)
    sleep(sleep_time)
    click_to_coordinate(*t)
    
def find_color():
    # finding the color
    for i in range(len((script := request_script())) - 6):
        if script[i:i+6] == "player":
            color = script[i+18:i+23]
    return {"white": 0, "black": 1}[color]

def get_coordinates(loc):
    x, y = ord(loc[0])-97, int(loc[1])-1
    if color:
        return 7-x, 7-y
    return x, y

driver = webdriver.Firefox()
driver.get('https://lichess.org')
#driver.get('https://lichess.org/login')
#sleep(1)
#login()

time_format = "3+0"

sleep(2)
btn = driver.find_element_by_xpath(f'//*[@data-id="{time_format}"]/div')
btn.click()
sleep(2)

# orgX: -300, orgY: 300
left_bottom_x = -300
left_bottom_y = 300
width = 80

stockfish = Stockfish(parameters={"Threads": 8})
stockfish.set_skill_level(20)

color = find_color()

while True:
    moves, sans = find_moves()
    if moves:
        for i in range(len(moves)):
            if sans[i] in ["O-O", "O-O-O"]:
                moves[i] = {
                    "e8h8": "e8g8",
                    "e1a1": "e1c1",
                    "e8a8": "e8c8",
                    "e1h1": "e1g1"
                }[moves[i]]
    stockfish.set_position(moves)
    move = stockfish.get_best_move()
    act(move, 0.01)
    print(moves, move)