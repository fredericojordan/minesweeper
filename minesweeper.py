import random
import sys

import pygame
from pygame.locals import *

# AI
AI_ENABLED = True

# BEGINNER
FIELDWIDTH = 8
FIELDHEIGHT = 8
MINESTOTAL = 10
#  
# # INTERMEDIATE
# FIELDWIDTH = 16
# FIELDHEIGHT = 16
# MINESTOTAL = 40
# 
# # EXPERT
# FIELDWIDTH = 24
# FIELDHEIGHT = 24
# MINESTOTAL = 99

# UI
FPS = 30
BOXSIZE = 30
GAPSIZE = 5
WINDOWWIDTH = FIELDWIDTH*(BOXSIZE+GAPSIZE)+85
WINDOWHEIGHT = FIELDWIDTH*(BOXSIZE+GAPSIZE)+135
XMARGIN = int((WINDOWWIDTH-(FIELDWIDTH*(BOXSIZE+GAPSIZE)))/2)
YMARGIN = XMARGIN

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
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 128, 0)

BGCOLOR = WHITE
FIELDCOLOR = BLACK
BOXCOLOR_COV = DARKGRAY # covered box color
BOXCOLOR_REV = LIGHTGRAY # revealed box color
MINECOLOR = BLACK
TEXTCOLOR = BLACK
HILITECOLOR = GREEN
RESETBGCOLOR = LIGHTGRAY
MINEMARK_COV = RED
NUMBER_COLORS = [
    (  0,   0,   0),  # 0
    (  0,   0, 255),  # 1
    (  0, 127,   0),  # 2
    (255,   0,   0),  # 3
    (  0,   0, 127),  # 4
    (127,   0,   0),  # 5
    (  0, 127, 127),  # 6
    (  0,   0,   0),  # 7
    (127, 127, 127),  # 8
]

# set up font 
FONTTYPE = 'Courier New'
FONTSIZE = 20

MINE = 'X'
MARKED = -2
HIDDEN = -1

class Minesweeper():
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Minesweeper')
        
        self.clock = pygame.time.Clock()
        self._display_surface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        self._BASICFONT = pygame.font.SysFont(FONTTYPE, FONTSIZE)
    
        # obtain reset surface and rect
        self._RESET_SURF, self._RESET_RECT = self.draw_button('RESET', TEXTCOLOR, RESETBGCOLOR, WINDOWWIDTH/2, WINDOWHEIGHT-50)
        
        self.database = []
        self.new_game()
        
    def new_game(self):
        """Set up mine field data structure, list of all zeros for recursion, and revealed box boolean data structure"""
        self.mine_field = get_random_minefield()
        self.revealed_boxes = get_field_with_value(False)
        self.marked_mines = get_field_with_value(False)
        
    def draw_field(self):
        """Draws field GUI"""
        self._display_surface.fill(BGCOLOR)
        pygame.draw.rect(self._display_surface, FIELDCOLOR, (XMARGIN-5, YMARGIN-5, (BOXSIZE+GAPSIZE)*FIELDWIDTH+5, (BOXSIZE+GAPSIZE)*FIELDHEIGHT+5))
    
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                left, top = get_left_top_xy(box_x, box_y)
                pygame.draw.rect(self._display_surface, BOXCOLOR_REV, (left, top, BOXSIZE, BOXSIZE))
    
        self._display_surface.blit(self._RESET_SURF, self._RESET_RECT)
        
        self.draw_mines_numbers()
        self.draw_covers()

    def draw_mines_numbers(self):
        """Draws mines and numbers onto GUI"""
        half = int(BOXSIZE*0.5) 
        quarter = int(BOXSIZE*0.25)
        eighth = int(BOXSIZE*0.125)
        
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                left, top = get_left_top_xy(box_x, box_y)
                center_x, center_y = get_center_xy(box_x, box_y)
                if self.mine_field[box_x][box_y] == MINE:
                    pygame.draw.circle(self._display_surface, MINECOLOR, (left+half, top+half), quarter)
                    pygame.draw.circle(self._display_surface, WHITE, (left+half, top+half), eighth)
                    pygame.draw.line(self._display_surface, MINECOLOR, (left+eighth, top+half), (left+half+quarter+eighth, top+half))
                    pygame.draw.line(self._display_surface, MINECOLOR, (left+half, top+eighth), (left+half, top+half+quarter+eighth))
                    pygame.draw.line(self._display_surface, MINECOLOR, (left+quarter, top+quarter), (left+half+quarter, top+half+quarter))
                    pygame.draw.line(self._display_surface, MINECOLOR, (left+quarter, top+half+quarter), (left+half+quarter, top+quarter))
                else: 
                    for i in range(1,9):
                        if self.mine_field[box_x][box_y] == i:
                            draw_text(str(i), self._BASICFONT, NUMBER_COLORS[i], self._display_surface, center_x, center_y)
                            
    def draw_covers(self):
        """Uses revealedBox FIELDWIDTH x FIELDHEIGHT data structure to determine whether to draw box covering mine/number
        Draws red cover instead of gray cover over marked mines
        """
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                if not self.revealed_boxes[box_x][box_y]:
                    left, top = get_left_top_xy(box_x, box_y)
                    if self.marked_mines[box_x][box_y]:
                        pygame.draw.rect(self._display_surface, MINEMARK_COV, (left, top, BOXSIZE, BOXSIZE))
                    else:
                        pygame.draw.rect(self._display_surface, BOXCOLOR_COV, (left, top, BOXSIZE, BOXSIZE))
                        
    def highlight_box(self, box_x, box_y):
        """Highlight box when mouse hovers over it"""
        left, top = get_left_top_xy(box_x, box_y)
        pygame.draw.rect(self._display_surface, HILITECOLOR, (left, top, BOXSIZE, BOXSIZE), 4)
    
    
    def highlight_button(self, butRect):
        """Highlight button when mouse hovers over it"""
        linewidth = 4
        pygame.draw.rect(self._display_surface, HILITECOLOR, (butRect.left-linewidth, butRect.top-linewidth, butRect.width+2*linewidth, butRect.height+2*linewidth), linewidth)

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

    def available_info(self):
        info = []
        
        for x in range(len(self.mine_field)):
            line = []
            for y in range(len(self.mine_field[x])):
                if self.marked_mines[x][y]:
                    line.append(MARKED)
                else:
                    try:
                        line.append(int(self.mine_field[x][y]) if self.revealed_boxes[x][y] else HIDDEN)
                    except:
                        line.append('X')
            info.append(line)
    
#         debug_field(info, 'info')
        return info

    def reveal_empty_squares(self, box_x, box_y, zero_list_xy=[]):
        """Modifies revealedBox data structure if chosen box_x & box_y is 0
        Shows all boxes using recursion
        """
        self.revealed_boxes[box_x][box_y] = True
        self.reveal_adjacent_boxes(box_x, box_y)
        for i, j in get_neighbour_squares([box_x, box_y]):
            if self.mine_field[i][j] == 0 and [i,j] not in zero_list_xy:
                zero_list_xy.append([i,j])
                self.reveal_empty_squares(i, j, zero_list_xy)
                
    def reveal_adjacent_boxes(self, box_x, box_y):
        """Modifies revealed_boxes data structure so that all adjacent boxes to (box_x, box_y) are set to True"""
        if box_x != 0: 
            self.revealed_boxes[box_x-1][box_y] = True
            if box_y != 0: 
                self.revealed_boxes[box_x-1][box_y-1] = True
            if box_y != FIELDHEIGHT-1: 
                self.revealed_boxes[box_x-1][box_y+1] = True
        if box_x != FIELDWIDTH-1:
            self.revealed_boxes[box_x+1][box_y] = True
            if box_y != 0: 
                self.revealed_boxes[box_x+1][box_y-1] = True
            if box_y != FIELDHEIGHT-1: 
                self.revealed_boxes[box_x+1][box_y+1] = True
        if box_y != 0: 
            self.revealed_boxes[box_x][box_y-1] = True
        if box_y != FIELDHEIGHT-1: 
            self.revealed_boxes[box_x][box_y+1] = True

    def show_mines(self):     
        """Modifies revealedBox data structure if chosen box_x & box_y is X"""
        for i in range(FIELDWIDTH):
            for j in range(FIELDHEIGHT):
                if self.mine_field[i][j] == MINE:
                    self.revealed_boxes[i][j] = True

    def draw_button(self, text, color, bgcolor, center_x, center_y):
        """Similar to draw_text but text has bg color and returns obj & rect"""
        butSurf = self._BASICFONT.render(text, True, color, bgcolor)
        butRect = butSurf.get_rect()
        butRect.centerx = center_x
        butRect.centery = center_y
    
        return (butSurf, butRect)


def main():
    tries = 0
    
    minesweeper = Minesweeper()
    
    # stores XY of mouse events
    mouse_x = 0
    mouse_y = 0
    
    while True:
        has_game_ended = False

        minesweeper.new_game()
        
        tries +=1
        print(tries)

        # main game loop
        while not has_game_ended:
            # initialize input booleans
            mine_clicked = False
            mine_flagged = False

            minesweeper.draw_field()

            # event handling loop
            for event in pygame.event.get():
                
                if event.type == QUIT or (event.type == KEYDOWN and (event.key == K_ESCAPE or event.key == K_q)):
                    terminate()
                elif event.type == MOUSEMOTION:
                    mouse_x, mouse_y = event.pos
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == LEFT_CLICK:
                        mouse_x, mouse_y = event.pos
                        mine_clicked = True
                    if event.button == RIGHT_CLICK:
                        mouse_x, mouse_y = event.pos
                        mine_flagged = True
  
            # determine boxes at clicked areas
            box_x, box_y = get_box_at_pixel(mouse_x, mouse_y)
            
            if AI_ENABLED:
                info = minesweeper.available_info()
            
                for s in AI_mark_squares(info):
                    minesweeper.marked_mines[s[0]][s[1]] = True
    
                safe_squares = AI_reveal_safe_squares(info)
                if safe_squares:
                    box_x, box_y = safe_squares[0][0], safe_squares[0][1]
                    mine_clicked = True
                else:
                    box_x, box_y = (random.choice(range(FIELDWIDTH)), random.choice(range(FIELDHEIGHT)))
                    mine_clicked = True

            # mouse not over a box in field
            if (box_x, box_y) == (None, None):

                # check if reset box is clicked
                if minesweeper._RESET_RECT.collidepoint(mouse_x, mouse_y):
                    minesweeper.highlight_button(minesweeper._RESET_RECT)
                    if mine_clicked: 
                        minesweeper.new_game()

            # mouse currently over box in field
            else:
                # highlight unrevealed box
                if not minesweeper.revealed_boxes[box_x][box_y]: 
                    minesweeper.highlight_box(box_x, box_y)

                    # mark mines
                    if mine_flagged:
                        if minesweeper.marked_mines[box_x][box_y]:
                            minesweeper.marked_mines[box_x][box_y] = True
                        else:
                            minesweeper.marked_mines[box_x][box_y] = False
                        
                    # reveal clicked boxes
                    if mine_clicked:
                        minesweeper.revealed_boxes[box_x][box_y] = True
                                               
                        if minesweeper.is_game_won():
                            print('WIN!!!')
                            has_game_ended = True
                        
                        minesweeper._save_turn()

                        # when 0 is revealed, show relevant boxes
                        if minesweeper.mine_field[box_x][box_y] == 0:
                            minesweeper.reveal_empty_squares(box_x, box_y)

                        # when mine is revealed, show mines
                        if minesweeper.mine_field[box_x][box_y] == MINE:
                            minesweeper.show_mines()
                            has_game_ended = True
                
            # redraw screen, wait clock tick
            pygame.display.update()
            minesweeper.clock.tick(FPS)


def blank_field():
    """Creates blank FIELDWIDTH x FIELDHEIGHT data structure"""
    field = []
    for _ in range(FIELDWIDTH):
        field.append([0 for _ in range(FIELDHEIGHT)]) 
            
    return field


def get_random_minefield(): 
    """Places mines in FIELDWIDTH x FIELDHEIGHT data structure"""
    field = blank_field()
    mine_count = 0
    xy = [] 
    while mine_count < MINESTOTAL: 
        x = random.randint(0, FIELDWIDTH-1)
        y = random.randint(0, FIELDHEIGHT-1)
        xy.append([x, y]) 
        if xy.count([x, y]) > 1: 
            xy.remove([x, y]) 
        else: 
            field[x][y] = MINE 
            mine_count += 1
    
    place_numbers(field)
    return field


def is_there_mine(field, x, y): 
    """Checks if mine is located at specific box on field"""
    return field[x][y] == MINE


def place_numbers(field): 
    """Places numbers in FIELDWIDTH x FIELDHEIGHT data structure"""
    for x in range(FIELDWIDTH):
        for y in range(FIELDHEIGHT):
            if not is_there_mine(field, x, y):
                count = 0
                if x != 0: 
                    if is_there_mine(field, x-1, y):
                        count += 1
                    if y != 0: 
                        if is_there_mine(field, x-1, y-1):
                            count += 1
                    if y != FIELDHEIGHT-1: 
                        if is_there_mine(field, x-1, y+1):
                            count += 1
                if x != FIELDWIDTH-1: 
                    if is_there_mine(field, x+1, y):
                        count += 1
                    if y != 0: 
                        if is_there_mine(field, x+1, y-1):
                            count += 1
                    if y != FIELDHEIGHT-1: 
                        if is_there_mine(field, x+1, y+1):
                            count += 1
                if y != 0: 
                    if is_there_mine(field, x, y-1):
                        count += 1
                if y != FIELDHEIGHT-1: 
                    if is_there_mine(field, x, y+1):
                        count += 1
                field[x][y] = count


def get_field_with_value(value):
    """Returns FIELDWIDTH x FIELDHEIGHT data structure different from the field data structure
    Each item in data structure is boolean (value) to show whether box at those fieldwidth & fieldheight coordinates should be revealed
    """
    revealed_boxes = []
    for _ in range(FIELDWIDTH):
        revealed_boxes.append([value] * FIELDHEIGHT)
    return revealed_boxes


def draw_text(text, font, color, surface, x, y):  
    """Function to easily draw text and also return object & rect pair"""
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.centerx = x
    textrect.centery = y
    surface.blit(textobj, textrect)


def get_left_top_xy(box_x, box_y):
    """Get left & top coordinates for drawing mine boxes"""
    left = XMARGIN + box_x*(BOXSIZE+GAPSIZE)
    top = YMARGIN + box_y*(BOXSIZE+GAPSIZE)
    return left, top


def get_center_xy(box_x, box_y):
    """Get center coordinates for drawing mine boxes"""
    center_x = XMARGIN + BOXSIZE/2 + box_x*(BOXSIZE+GAPSIZE)
    center_y = YMARGIN + BOXSIZE/2 + box_y*(BOXSIZE+GAPSIZE)
    return center_x, center_y


def get_box_at_pixel(x, y):
    """Gets coordinates of box at mouse coordinates"""
    for box_x in range(FIELDWIDTH):
        for box_y in range(FIELDHEIGHT):
            left, top = get_left_top_xy(box_x, box_y)
            boxRect = pygame.Rect(left, top, BOXSIZE, BOXSIZE)
            if boxRect.collidepoint(x, y):
                return (box_x, box_y)
    return (None, None)


def terminate():
    """Simple function to exit game"""
    pygame.quit()
    sys.exit()


def debug_field(board, title=None):
    """Prints minefield for debug purposes"""
    if title:
        print(title)
    for y in range(len(board)):
        print([board[x][y] for x in range(len(board[y]))])
    print()


def get_neighbour_squares(square, min_x=0, max_x=FIELDWIDTH-1, min_y=0, max_y=FIELDHEIGHT-1):
    """Returns list of squares that are adjacent to specified square"""
    neighbours = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            neighbours.append([square[0]+i, square[1]+j])
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


def get_hidden_neighbours(square, available_info):
    """Returns adjacent squares that are hidden (marked not included)"""
    hidden_squares = []
    for x, y in get_neighbour_squares(square):
        if available_info[x][y] == HIDDEN:
            hidden_squares.append([x, y])
    return hidden_squares


def get_marked_neighbours(square, available_info):
    """Returns adjacent squares that are marked"""
    marked_squares = []
    for x, y in get_neighbour_squares(square):
        if available_info[x][y] == MARKED:
            marked_squares.append([x, y])
    return marked_squares


def AI_mark_squares(available_info):
    """Returns list of squares that are sure to contain mines"""
    marked = []
    for x in range(len(available_info)):
        for y in range(len(available_info[x])):
            neighbours = get_hidden_neighbours([x, y], available_info)
            neighbours.extend(get_marked_neighbours([x, y], available_info))
            if available_info[x][y] == len(neighbours):
                marked.extend(neighbours)
    return marked


def AI_reveal_safe_squares(available_info):
    """Returns list of squares that are sure to NOT contain mines"""
    revealed = []
    for x in range(len(available_info)):
        for y in range(len(available_info[x])):
            marked = get_marked_neighbours([x, y], available_info)
            if available_info[x][y] == len(marked):
                revealed.extend(get_hidden_neighbours([x, y], available_info))
    return revealed


if __name__ == '__main__':
    main()
