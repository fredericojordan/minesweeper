import numpy as np
import os
import random
import sys

import pygame
from pygame.locals import *

from network import Network

# AI
#AI_TYPE = "FRED"
AI_TYPE = "RANDOM"
#AI_TYPE = "ANN"
#AI_TYPE = "HUMAN"

# TRAINING
TRAINING = True
TRAINING_COMPLETE = 10000

# DIFFICULTY
BEGINNER = (9, 9, 10)
INTERMEDIATE = (16, 16, 40)
EXPERT = (30, 16, 99)
TEST = (4, 4, 2)

FIELDWIDTH, FIELDHEIGHT, MINESTOTAL = TEST

# UI
FPS = 30
BOXSIZE = 30
WINDOWWIDTH = FIELDWIDTH*BOXSIZE+85
WINDOWHEIGHT = FIELDHEIGHT*BOXSIZE+135
XMARGIN = int((WINDOWWIDTH-(FIELDWIDTH*BOXSIZE))/2)
YMARGIN = XMARGIN+50

# INPUT
LEFT_CLICK = 1
RIGHT_CLICK = 3

# assertions
assert MINESTOTAL < FIELDHEIGHT*FIELDWIDTH, 'More mines than boxes'
assert BOXSIZE^2 * (FIELDHEIGHT*FIELDWIDTH) < WINDOWHEIGHT*WINDOWWIDTH, 'Boxes will not fit on screen'
assert BOXSIZE/2 > 5, 'Bounding errors when drawing rectangle, cannot use half-5 in draw_mines_numbers'

# COLORS
LIGHTGRAY = (225, 225, 225)
DARKGRAY = (160, 160, 160)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

BGCOLOR = LIGHTGRAY
TEXTCOLOR = BLACK
HIGHLIGHTCOLOR = DARKGRAY
RESETBGCOLOR = LIGHTGRAY

# set up font 
FONTTYPE = 'Courier New'
FONTSIZE = 20

MINE = 'X'
FLAGGED = -2
HIDDEN = -1


class Minesweeper:
    
    def __init__(self):
        # random.seed(0)  # Seed the RNG for DEBUG purposes
        pygame.init()
        pygame.display.set_caption('Minesweeper')
        
        self.clock = pygame.time.Clock()
        
        # load GUI
        self._display_surface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        self._BASICFONT = pygame.font.SysFont(FONTTYPE, FONTSIZE)
#         self._RESET_SURF, self._RESET_RECT = self.draw_button('RESET', TEXTCOLOR, RESETBGCOLOR, WINDOWWIDTH/2, 50)
        self._images = {    
            '0': pygame.transform.scale(pygame.image.load(os.path.join('media', '0.png')), (BOXSIZE, BOXSIZE)),
            '1': pygame.transform.scale(pygame.image.load(os.path.join('media', '1.png')), (BOXSIZE, BOXSIZE)),
            '2': pygame.transform.scale(pygame.image.load(os.path.join('media', '2.png')), (BOXSIZE, BOXSIZE)),
            '3': pygame.transform.scale(pygame.image.load(os.path.join('media', '3.png')), (BOXSIZE, BOXSIZE)),
            '4': pygame.transform.scale(pygame.image.load(os.path.join('media', '4.png')), (BOXSIZE, BOXSIZE)),
            '5': pygame.transform.scale(pygame.image.load(os.path.join('media', '5.png')), (BOXSIZE, BOXSIZE)),
            '6': pygame.transform.scale(pygame.image.load(os.path.join('media', '6.png')), (BOXSIZE, BOXSIZE)),
            '7': pygame.transform.scale(pygame.image.load(os.path.join('media', '7.png')), (BOXSIZE, BOXSIZE)),
            '8': pygame.transform.scale(pygame.image.load(os.path.join('media', '8.png')), (BOXSIZE, BOXSIZE)),
            'hidden': pygame.transform.scale(pygame.image.load(os.path.join('media', 'hidden.png')), (BOXSIZE, BOXSIZE)),
            'flag': pygame.transform.scale(pygame.image.load(os.path.join('media', 'flag.png')), (BOXSIZE, BOXSIZE)),
            'mine': pygame.transform.scale(pygame.image.load(os.path.join('media', 'mine.png')), (BOXSIZE, BOXSIZE)),
        }
        
        self.database = []
        self.mine_field, self.revealed_boxes, self.flagged_mines = self.new_game() #, self.game_over
        
    def new_game(self):
        """Set up mine field data structure, list of all zeros for recursion, and revealed box boolean data structure"""
        self._RESET_SURF, self._RESET_RECT = self.draw_smiley(WINDOWWIDTH/2, 50, 'smiley.png')
        #self.game_over = False
        self.mine_field = self.get_random_minefield()
        self.revealed_boxes = self.get_field_with_value(False)
        self.flagged_mines = self.get_field_with_value(False)

        return self.mine_field, self.revealed_boxes, self.flagged_mines #, self.game_over
    
    def get_image(self, box_x, box_y):
        if self.flagged_mines[box_x][box_y]:
            return self._images.get('flag')
        if self.revealed_boxes[box_x][box_y]:
            if self.mine_field[box_x][box_y] == MINE:
                return self._images.get('mine')
            else:
                return self._images.get(str(self.mine_field[box_x][box_y]))
        else:
            return self._images.get('hidden')
        
    def draw_field(self):
        """Draws field GUI"""
        self._display_surface.fill(BGCOLOR)
    
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                left, top = self.get_left_top_xy(box_x, box_y)
                self._display_surface.blit(self.get_image(box_x, box_y), (left,top))
    
        self._display_surface.blit(self._RESET_SURF, self._RESET_RECT)
                        
    def highlight_box(self, box_x, box_y):
        """Highlight box when mouse hovers over it"""
        left, top = self.get_left_top_xy(box_x, box_y)
        pygame.draw.rect(self._display_surface, HIGHLIGHTCOLOR, (left, top, BOXSIZE, BOXSIZE), 4)
    
    def highlight_button(self, butRect):
        """Highlight button when mouse hovers over it"""
        linewidth = 4
        pygame.draw.rect(self._display_surface, HIGHLIGHTCOLOR, (butRect.left-linewidth, butRect.top-linewidth, butRect.width+2*linewidth, butRect.height+2*linewidth), linewidth)

    def is_game_won(self):
        """Checks if player has revealed all boxes"""
        not_mine_count = 0
    
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                if self.revealed_boxes[box_x][box_y] == True:
                    if self.mine_field[box_x][box_y] != MINE:
                        not_mine_count += 1
    
        if not_mine_count >= (FIELDWIDTH*FIELDHEIGHT) - MINESTOTAL:
            return True
        else:
            return False
        
    def _save_turn(self):
        info = self.available_info()
            
        score = 0
        for col in info:
            score += sum(i != MINE and i != -1 for i in col)
        
        self.database.append({
            "turn": info,
            "score": score,
        })
#         print(self.database[-1])

    def save_turn(self):
    # Saves input for ANN training
        turn = []
        for i in range(FIELDWIDTH):
            for j in range(FIELDHEIGHT):
                square = []
                if self.revealed_boxes[i][j]:
                    square.append(self.mine_field[i][j])
                else:
                    square.append(-1)
                turn.append(square)
        return turn

    def save_chosen_square(self, chosen_square):
    # Saves output for ANN training
        print('Chosen box:',chosen_square)
        output = []
        for _ in range(FIELDHEIGHT * FIELDWIDTH):
            output.append([0])
        output[chosen_square[0][0]*FIELDHEIGHT+chosen_square[0][1]] = [1]

        return output

    def available_info(self):
        info = []
        
        for x in range(len(self.mine_field)):
            line = []
            for y in range(len(self.mine_field[x])):
                if self.flagged_mines[x][y]:
                    line.append(FLAGGED)
                else:
                    try:
                        line.append(int(self.mine_field[x][y]) if self.revealed_boxes[x][y] else HIDDEN)
                    except:
                        line.append('X')
            info.append(line)
    
#         self.debug_field(info, 'info')
        return info
    
    def toggle_flag_box(self, x, y):
        """Toggles if mine box is flagged"""
        if not self.flagged_mines[x][y] and not self.revealed_boxes[x][y]:
            self.flagged_mines[x][y] = True
        else:
            self.flagged_mines[x][y] = False
    
    def reveal_box(self, x, y):
        """Reveals box clicked"""
        self.game_over = False
        self.revealed_boxes[x][y] = True
                                               
        if self.is_game_won():
            print('WIN!!!')
            self._RESET_SURF, self._RESET_RECT = self.draw_smiley(WINDOWWIDTH/2, 50, 'win.png')
            self.game_over = True
            if AI_TYPE != 'HUMAN':
                self.new_game() 

        # when 0 is revealed, show relevant boxes
        if self.mine_field[x][y] == 0:
            self.reveal_empty_squares(x, y)

        # when mine is revealed, show mines
        if self.mine_field[x][y] == MINE:
            self.show_mines()
            self._RESET_SURF, self._RESET_RECT = self.draw_smiley(WINDOWWIDTH/2, 50, 'lose.png')
            self.game_over = True
            if AI_TYPE != 'HUMAN':
                self.new_game() 
        
        return self.game_over

    def reveal_empty_squares(self, box_x, box_y): #, zero_list_xy=[]):
        """Modifies revealed_boxes data structure if chosen box_x & box_y is 0
        Shows all boxes using recursion
        """
        self.revealed_boxes[box_x][box_y] = True
                
        if box_x > 0 and box_y > 0:
            if self.revealed_boxes[box_x-1][box_y-1] == False:
                self.reveal_box(box_x-1, box_y-1)
            
        if box_y > 0:
            if self.revealed_boxes[box_x][box_y-1] == False:
                self.reveal_box(box_x, box_y-1)
            
        if box_x < FIELDWIDTH-1 and box_y > 0:
            if self.revealed_boxes[box_x+1][box_y-1] == False:
                self.reveal_box(box_x+1, box_y-1)
            
        if box_x > 0:
            if self.revealed_boxes[box_x-1][box_y] == False:
                self.reveal_box(box_x-1, box_y)
            
        if box_x < FIELDWIDTH-1:
            if self.revealed_boxes[box_x+1][box_y] == False:
                self.reveal_box(box_x+1, box_y)
            
        if box_x > 0 and box_y < FIELDHEIGHT-1:
            if self.revealed_boxes[box_x-1][box_y+1] == False:
                self.reveal_box(box_x-1, box_y+1)
            
        if box_y < FIELDHEIGHT-1:
            if self.revealed_boxes[box_x][box_y+1] == False:
                self.reveal_box(box_x, box_y+1)
            
        if box_x < FIELDWIDTH-1 and box_y < FIELDHEIGHT-1:
            if self.revealed_boxes[box_x+1][box_y+1] == False:
                self.reveal_box(box_x+1, box_y+1)

    def show_mines(self):     
        """Modifies revealed_boxes data structure if chosen box_x & box_y is X"""
        for i in range(FIELDWIDTH):
            for j in range(FIELDHEIGHT):
                if self.mine_field[i][j] == MINE:
                    self.revealed_boxes[i][j] = True

    def draw_button(self, text, color, bgcolor, center_x, center_y):
        """Similar to draw_text but text has bg color and returns obj & rect"""
        but_surf = self._BASICFONT.render(text, True, color, bgcolor)
        but_rect = but_surf.get_rect()
        but_rect.centerx = center_x
        but_rect.centery = center_y

        return but_surf, but_rect
    
    def draw_smiley(self, center_x, center_y, filename):
        surface = pygame.image.load(os.path.join('media', filename))
        surface = pygame.transform.scale(surface, (50, 50))
        rect = surface.get_rect()
        rect.centerx = center_x
        rect.centery = center_y
        return surface, rect

    def is_there_mine(self, field, x, y):
        """Checks if mine is located at specific box on field"""
        return field[x][y] == MINE

    def place_numbers(self, field):
        """Places numbers in FIELDWIDTH x FIELDHEIGHT data structure"""
        for x in range(FIELDWIDTH):
            for y in range(FIELDHEIGHT):
                if not self.is_there_mine(field, x, y):
                    field[x][y] = [
                        field[neighbour_x][neighbour_y]
                        for neighbour_x, neighbour_y in self.get_neighbour_squares([x, y])
                    ].count(MINE)

    def get_random_minefield(self):
        """Places mines in FIELDWIDTH x FIELDHEIGHT data structure"""
        field = self.get_field_with_value(0)
        mine_count = 0
        xy = []
        while mine_count < MINESTOTAL:
            x = random.randint(0, FIELDWIDTH - 1)
            y = random.randint(0, FIELDHEIGHT - 1)
            if [x, y] not in xy:
                xy.append([x, y])
                field[x][y] = MINE
                mine_count += 1

        self.place_numbers(field)
        return field

    def get_field_with_value(self, value):
        """Returns FIELDWIDTH x FIELDHEIGHT data structure completely filled with VALUE"""
        revealed_boxes = []
        for _ in range(FIELDWIDTH):
            revealed_boxes.append([value] * FIELDHEIGHT)
        return revealed_boxes

    def terminate(self):
        """Simple function to exit game"""
        pygame.quit()
        sys.exit()

    def draw_text(self, text, font, color, surface, x, y):
        """Function to easily draw text and also return object & rect pair"""
        textobj = font.render(text, True, color)
        textrect = textobj.get_rect()
        textrect.centerx = x
        textrect.centery = y
        surface.blit(textobj, textrect)

    def get_left_top_xy(self, box_x, box_y):
        """Get left & top coordinates for drawing mine boxes"""
        left = XMARGIN + box_x*BOXSIZE
        top = YMARGIN + box_y*BOXSIZE
        return left, top

    def get_center_xy(self, box_x, box_y):
        """Get center coordinates for drawing mine boxes"""
        center_x = XMARGIN + BOXSIZE / 2 + box_x*BOXSIZE
        center_y = YMARGIN + BOXSIZE / 2 + box_y*BOXSIZE
        return center_x, center_y

    def get_box_at_pixel(self, x, y):
        """Gets coordinates of box at mouse coordinates"""
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                left, top = self.get_left_top_xy(box_x, box_y)
                boxRect = pygame.Rect(left, top, BOXSIZE, BOXSIZE)
                if boxRect.collidepoint(x, y):
                    return (box_x, box_y)
        return (None, None)

    def debug_field(self, board, title=None):
        """Prints minefield for debug purposes"""
        if title:
            print(title)
        for y in range(len(board)):
            print([board[x][y] for x in range(len(board[y]))])
        print()

    def get_neighbour_squares(self, square, min_x=0, max_x=FIELDWIDTH - 1, min_y=0, max_y=FIELDHEIGHT - 1):
        """Returns list of squares that are adjacent to specified square"""
        neighbours = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                neighbours.append([square[0] + i, square[1] + j])
        neighbours.remove(square)

        if min_x is not None:
            neighbours = [item for item in neighbours if item[0] >= min_x]

        if max_x is not None:
            neighbours = [item for item in neighbours if item[0] <= max_x]

        if min_y is not None:
            neighbours = [item for item in neighbours if item[1] >= min_y]

        if max_y is not None:
            neighbours = [item for item in neighbours if item[1] <= max_y]

        return neighbours

    def get_uncertain_neighbours(self, square, available_info):
        """Returns adjacent squares that are uncertain (flagged not included)"""
        hidden_squares = []
        for x, y in self.get_neighbour_squares(square):
            if available_info[x][y] == HIDDEN:
                hidden_squares.append([x, y])
        return hidden_squares

    def get_flagged_neighbours(self, square, available_info):
        """Returns adjacent squares that have been flagged"""
        flagged_squares = []
        for x, y in self.get_neighbour_squares(square):
            if available_info[x][y] == FLAGGED:
                flagged_squares.append([x, y])
        return flagged_squares

    def get_hidden_neighbours(self, square, available_info):
        """Returns adjacent squares that have not been clicked yet"""
        hidden = self.get_uncertain_neighbours(square, available_info)
        hidden.extend(self.get_flagged_neighbours(square, available_info))
        return hidden

    def get_AI_flagged_squares(self, available_info):
        """Returns list of squares that are sure to contain mines"""
        flagged_squares = []

        for x, y in [(x, y) for x in range(len(available_info)) for y in range(len(available_info[x]))]:
            neighbours = self.get_hidden_neighbours([x, y], available_info)
            if available_info[x][y] == len(neighbours):
                unflagged = [square for square in neighbours
                             if available_info[square[0]][square[1]] == HIDDEN and
                             square not in flagged_squares]
                flagged_squares.extend(unflagged)

        return flagged_squares

    def get_AI_safe_squares(self, available_info, guess=False):
        """Returns list of squares that are sure to NOT contain mines"""
        safe_squares = []

        for x in range(FIELDWIDTH):
            for y in range(FIELDHEIGHT):
                flagged = self.get_flagged_neighbours([x, y], available_info)
                if available_info[x][y] == len(flagged):
                    safe_squares.extend(self.get_uncertain_neighbours([x, y], available_info))

        if not safe_squares and guess:
            safe_squares.append([random.choice(range(FIELDWIDTH)), random.choice(range(FIELDHEIGHT))])

        return safe_squares

    def get_AI_input(self, info):
        """Returns both the safe squares and the flagged squares"""
        # TODO: Apply flagged squares to game state before calculating safe squares
        flagged_squares = self.get_AI_flagged_squares(info)
        safe_squares = self.get_AI_safe_squares(info, guess=True)
        return safe_squares, flagged_squares

    def data_treat(self, db):
        '''Prepares date to be trained'''
        new_db = []
        while len(db) > 0:
            input = db[0][0]
            output = db[0][1]
            to_delete = [0]
            for i in range(1,len(db)):
                if np.array_equal(db[i][0], db[0][0]):
                    output += db[i][1]
                    to_delete = [i] + to_delete
            for j in to_delete:
                del(db[j])
            output[np.nonzero(output)] = 1
            new_db.append((input, output))
        return new_db
    
def main():
    tries = 0
    plays = 0
    db_good = []
    db_bad = []
    
    minesweeper = Minesweeper()
    
    # stores XY of mouse events
    mouse_x = 0
    mouse_y = 0
    
    while True:
        has_game_ended = False
        game_over = False

        minesweeper.new_game()
        
        tries += 1
        print('Jogo', tries)

        # For random training
        chosen_squares = []
        chosen_squares_length = 1

        # Main game loop
        while not has_game_ended:
            # Initialize variables
            mouse_clicked = False
            safe_squares = []
            flagged_squares = []
            new_position = False # For random training

            # Draw screen
            minesweeper.draw_field()

            # Get Fred's AI input
            if AI_TYPE == 'FRED':
                info = minesweeper.available_info()
                safe_squares, flagged_squares = minesweeper.get_AI_input(info)

            # Get random position
            if AI_TYPE == 'RANDOM':
                while not new_position:
                    choice = [[random.choice(range(FIELDWIDTH)),random.choice(range(FIELDHEIGHT))]]
                    if minesweeper.revealed_boxes[choice[0][0]][choice[0][1]] == False:
                        new_position = True
                safe_squares = choice

            # Get player input
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and (event.key == K_ESCAPE or event.key == K_q)):
                    minesweeper.terminate()
                elif event.type == MOUSEMOTION:
                    mouse_x, mouse_y = event.pos
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == LEFT_CLICK:
                        mouse_x, mouse_y = event.pos
                        mouse_clicked = True
                        box_x, box_y = minesweeper.get_box_at_pixel(mouse_x, mouse_y)
                        if box_x is not None and box_y is not None:
                            safe_squares = [(box_x, box_y)]
                    if event.button == RIGHT_CLICK:
                        mouse_x, mouse_y = event.pos
                        box_x, box_y = minesweeper.get_box_at_pixel(mouse_x, mouse_y)
                        if box_x is not None and box_y is not None:
                            flagged_squares = [(box_x, box_y)]

            # Keeps track of chosen squares
            if len(safe_squares) > 0:
                chosen_squares.append(safe_squares)

            # Checks if game is over for AI
            if AI_TYPE != 'HUMAN':
                if game_over:
                    has_game_ended = True

            # Saves turn
            if TRAINING and chosen_squares_length == len(chosen_squares):
                turn = minesweeper.save_turn()

            # Apply game changes
            if not game_over:
                for x, y in flagged_squares:
                    minesweeper.toggle_flag_box(x, y)

                for x, y in safe_squares:
                    minesweeper._RESET_SURF, minesweeper._RESET_RECT = minesweeper.draw_smiley(WINDOWWIDTH/2, 50, 'check.png')
                    game_over = minesweeper.reveal_box(x, y)

            #Add play to DB
            if TRAINING and chosen_squares_length == len(chosen_squares) and len(safe_squares) > 0:
                chosen_squares_length += 1
                turn_chosen_square = minesweeper.save_chosen_square(safe_squares)
                if minesweeper.mine_field[safe_squares[0][0]][safe_squares[0][1]] != 'X':
                    db_good.append((np.asarray(turn),np.asarray(turn_chosen_square)))
                    #print('GOOD', db_good[-1])
                
                if minesweeper.mine_field[safe_squares[0][0]][safe_squares[0][1]] == 'X':
                    db_bad.append((np.asarray(turn),np.asarray(turn_chosen_square)))
                    #print('BAD', db_bad[-1])
                
                plays += 1            
                if plays > TRAINING_COMPLETE:
                    db_good = minesweeper.data_treat(db_good)
                    db_bad = minesweeper.data_treat(db_bad)
                    print('GOOD',db_good[0])
                    print('BAD',db_bad[0])
                    div = int(len(db_good)*.8)
                    training_data = db_good[:div]
                    test_data = db_good[div:]
                    net = Network([FIELDHEIGHT*FIELDWIDTH, 32, 16, FIELDHEIGHT*FIELDWIDTH])
                    print('Network training started...\n')
                    net.SGD(training_data, 30, 10, 0.1, lmbda=5.0)
                    net.save('ANN_test')

                    print('score = {:.2f} %'.format(net.accuracy(test_data)/100))
                    minesweeper.terminate()

            # Check if reset box is clicked
            if minesweeper._RESET_RECT.collidepoint(mouse_x, mouse_y):
                minesweeper.highlight_button(minesweeper._RESET_RECT)
                if mouse_clicked:
                    minesweeper.new_game()
                    has_game_ended = True

            # Highlight unrevealed box
            box_x, box_y = minesweeper.get_box_at_pixel(mouse_x, mouse_y)
            if box_x is not None and box_y is not None and not minesweeper.revealed_boxes[box_x][box_y]:
                minesweeper.highlight_box(box_x, box_y)

            # Update screen, wait clock tick
            pygame.display.update()
            minesweeper.clock.tick(FPS)

if __name__ == '__main__':
    main()
