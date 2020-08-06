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
SLEEP_TIME_LOGGING_IN = 0.5
SLEEP_TIME_MATCHING = 2
REQUEST_INTERVAL = 0.01
TIME_FORMAT = "1+0"
WHITE = "white"
BLACK = "black"


class LiChessBot():

    def __init__(self):
        self.driver = webdriver.Firefox()
        self.engine = Stockfish()
        self.engine.set_skill_level(20)
        self.last_color = WHITE
        self.last_output = None

    def enter_match(self, time_format):
        """Starts a game with the given time format."""
        self.driver.get('https://lichess.org')
        sleep(SLEEP_TIME_MATCHING)
        self.driver.find_element_by_xpath(f'//*[@data-id="{TIME_FORMAT}"]/div').click()
        sleep(SLEEP_TIME_MATCHING)
        self.color = self.find_color()
        self.game_loop()

    def login(self):
        self.driver.get('https://lichess.org/login')
        sleep(SLEEP_TIME_LOGGING_IN)
        self.driver.find_element_by_xpath('//*[@id="form3-username"]').send_keys(username)
        sleep(SLEEP_TIME_LOGGING_IN)
        self.driver.find_element_by_xpath('//*[@id="form3-password"]').send_keys(password)
        sleep(SLEEP_TIME_LOGGING_IN)
        self.driver.find_element_by_css_selector(".submit").click()
    
    def find_color(self):
        for i in range(len((script := self.request_script())) - len((key:="\"player\":{\""))):
            if script[i:i+len(key)] == key:
                return {"white": WHITE, "black": BLACK}[script[i+19:i+24]]

    def game_loop(self):
        """A game loop. Called after entering a match.
        - Scrape the board configuration.
        - Check if the game is over.
        - Output some useful information.
        - If a castle has been made, fix the coordinates to be able match it
            with the the Stockfish engine.
        - If our turn, play. 
        """
        while True:
            res = self.find_moves()
            if res:
                moves, sans, colors = res
            else:
                print(requests.get2str(self.driver.current_url))
                print("Game is over!")
                break
            output = moves[-1], sans[-1], colors[-1]
            if output != self.last_output:
                self.last_output = output
                print(output)
            for i in range(1, len(moves)):
                if sans[i] in ["O-O", "O-O-O"]:
                    moves[i] = {
                        "e8h8": "e8g8",
                        "e1a1": "e1c1",
                        "e8a8": "e8c8",
                        "e1h1": "e1g1"
                    }[moves[i]]
            if self.color == colors[-1]:
                self.engine.set_position(moves[1:])
                move = self.engine.get_best_move()
                self.click_to_coordinate(move[:2])
                self.click_to_coordinate(move[2:])
        
    def click_to_coordinate(self, sq):
        """Takes a coordinate of a square in a form like "e2", "b7" and clicks on it."""
        def get_coordinates(loc):
            x, y = ord(loc[0])-97, int(loc[1])-1
            if self.color == BLACK:
                return 7-x, 7-y
            return x, y
        x, y = get_coordinates(sq)
        ac = ActionChains(self.driver)
        elem = self.driver.find_element_by_id("main-wrap")
        ac.move_to_element(elem).move_by_offset(LEFT_B_X + x * GAP, LEFT_B_Y - y * GAP).click().perform()

    def request_script(self):
        """Sends a get request to scrape the moves on the table."""
        sleep(REQUEST_INTERVAL)
        page = requests.get2str(self.driver.current_url)
        return BeautifulSoup(page, 'html.parser').find_all("script")[2].string

    def find_uci(self, ply):
        """Returns the necessary information from the given data of the latest move."""
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

    def find_moves(self):
        """Gets the necessary information about the latest move."""
        script = self.request_script()
        moves, sans, colors = [], [], []
        for i in range(len(script) - len((key := "{\"ply\""))):
            if script[i:i+len(key)] == key:
                for j in range(i + 1, len(script)):
                    if script[j] == "}":
                        ply = script[i:j]
                uci, san = self.find_uci(ply)
                if not uci or not san:
                    return
                color = WHITE if len(moves) % 2 == 0 else BLACK
                moves.append(uci)
                sans.append(san)
                colors.append(color)
        return moves, sans, colors



if __name__ == "__main__":
    bot = LiChessBot()
    #bot.login()
    bot.enter_match(TIME_FORMAT)
