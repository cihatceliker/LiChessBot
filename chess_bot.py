import random, sys
import faster_than_requests as requests
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
from stockfish import Stockfish
from selenium.webdriver.common.action_chains import ActionChains
from login_info import username, password


LEFT_B_X = -300
LEFT_B_Y = 300
GAP = 80
SLEEP_BETWEEN_MOVE_CLICKS = 0.01
SLEEP_TIME_LOGGING_IN = 0.5
SLEEP_TIME_MATCHING = 3
TIME_FORMAT = "3+0"
WHITE = "white"
BLACK = "black"


class LiChessBot():
    def __init__(self):
        self.driver = webdriver.Firefox()
        self.driver.get('https://lichess.org')
        self.engine = Stockfish(parameters={"Threads": 8})
        self.engine.set_skill_level(20)
        sleep(SLEEP_TIME_MATCHING)
        self.last_color = WHITE

    def enter_match(self, time_format):
        self.driver.find_element_by_xpath(f'//*[@data-id="{TIME_FORMAT}"]/div').click()
        sleep(SLEEP_TIME_MATCHING)
        self.color = self.find_color()

    def login(self):
        self.driver.get('https://lichess.org/login')
        sleep(SLEEP_TIME_LOGGING_IN)
        self.driver.find_element_by_xpath('//*[@id="form3-username"]').send_keys(username)
        sleep(SLEEP_TIME_LOGGING_IN)
        self.driver.find_element_by_xpath('//*[@id="form3-password"]').send_keys(password)
        sleep(SLEEP_TIME_LOGGING_IN)
        self.driver.find_element_by_css_selector(".submit").click()
    
    def find_color(self):
        # finding the color
        for i in range(len((script := self.request_script())) - len((key:="\"player\":{\""))):
            if script[i:i+len(key)] == key:
                return {"white": WHITE, "black": BLACK}[script[i+19:i+24]]

    def get_coordinates(self, loc):
        x, y = ord(loc[0])-97, int(loc[1])-1
        if self.color == BLACK:
            return 7-x, 7-y
        return x, y

    def game_loop(self, time_format):
        self.enter_match(time_format)
        print(self.color)
        while True:
            moves, sans, colors = self.find_moves()
            print(moves, sans, colors)
            for i in range(1, len(moves)):
                if sans[i] in ["O-O", "O-O-O"]:
                    moves[i] = {
                        "e8h8": "e8g8",
                        "e1a1": "e1c1",
                        "e8a8": "e8c8",
                        "e1h1": "e1g1"
                    }[moves[i]]
            if self.color == colors[-1]:
                self.move(moves)
    
    def move(self, moves):
        self.engine.set_position(moves[1:])
        self.act(self.engine.get_best_move())
        
    def click_to_coordinate(self, x, y):
        ac = ActionChains(self.driver)
        elem = self.driver.find_element_by_id("main-wrap")
        ac.move_to_element(elem).move_by_offset(LEFT_B_X + x * GAP, LEFT_B_Y - y * GAP).click().perform()

    def act(self, move):
        f, t = self.get_coordinates(move[:2]), self.get_coordinates(move[2:])
        self.click_to_coordinate(*f)
        sleep(SLEEP_BETWEEN_MOVE_CLICKS)
        self.click_to_coordinate(*t)

    def request_script(self):
        sleep(0.1)
        page = requests.get2str(self.driver.current_url)
        return BeautifulSoup(page, 'html.parser').find_all("script")[2].string
            
    def find_uci(self, ply):
        ply = ply.split(":")
        def find_key(key):
            key_found = False
            for pc in ply:
                if key_found:
                    return pc.split(",")[0][1:-1]
                if pc[-len(key):] == key:
                    key_found = True
        uci = find_key("\"uci\"")
        san = find_key("\"san\"")
        return uci, san

    def find_ply(self, idx, script):
        for i in range(idx + 1, len(script)):
            if script[i] == "}":
                return script[idx:i]

    def find_moves(self):
        script = self.request_script()
        moves, sans, colors = [], [], []
        key = "{\"ply\""
        for i in range(len(script) - len(key)):
            if script[i:i+len(key)] == key:
                ply = self.find_ply(i, script)
                uci, san = self.find_uci(ply)
                color = WHITE if len(moves) % 2 == 0 else BLACK
                moves.append(uci)
                sans.append(san)
                colors.append(color)
        return moves, sans, colors



if __name__ == "__main__":
    bot = LiChessBot()
    #bot.login()
    bot.game_loop(TIME_FORMAT)
