import itertools
import random

class Minesweeper():
    # basic minesweeper game

    def __init__(self, height, width, mines):
        # setup board size and mine count
        self.height = height
        self.width = width
        self.mines = set()


        total_cells = height*width
        max_reasonable_mines = total_cells - 1

        if mines < 0:
            raise ValueError(f"Mine count cannot be negative. Received: {mines}")
           # mines = 0
        elif mines >= total_cells:
            raise ValueError(f"Too many mines for board size {height}x{width}. Cannot have {mines} mines on {total_cells} cells.")
            #mines = max_reasonable_mines
        elif mines > total_cells * 0.5:
            print(f"Warning: {mines} mines on {height}x{width} board is pretty dense!")
            print(f"That's {mines/total_cells*100:.1f}% of the board!")
        
        # suggest reasonable mine count based on board size
        reasonable_mine_count = max(1, total_cells // 8)  # roughly 12.5% of board
        if mines == 0:
            print(f"Suggestion: Try {reasonable_mine_count} mines for a {height}x{width} board")    


        # make empty board first
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # randomly place mines
        if mines > 0:
           while len(self.mines) != mines:
               i = random.randrange(height)
               j = random.randrange(width)
               if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # no mines found yet
        self.mines_found = set()

    def print(self):
        # show the board with mine for mines
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        # count mines around this cell
        count = 0

        # check all 8 neighbors plus the cell itself
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                # dont count the cell itself
                if (i, j) == cell:
                    continue

                # make sure we dont go outside the board
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        # win if we found all mines
        return self.mines_found == self.mines


class Sentence():
    # represents"these cells have this many mines"

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        # if cells =count then all cells are mines
        if len(self.cells) == self.count:
            return self.cells
        else:
            return set()

    def known_safes(self):
        # if count =0 then all cells are safe
        if self.count == 0:
            return self.cells
        else:
            return set()

    def mark_mine(self, cell):
        # remove a mine from our sentence
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        # remove a safe cell from our sentence
        if cell in self.cells:
            self.cells.remove(cell)


class MinesweeperAI():
    # ai player for minesweeper

    def __init__(self, height=8, width=8):
        self.height = height
        self.width = width

        # keep track of moves and what we know
        self.moves_made = set()
        self.mines = set()
        self.safes = set()
        self.knowledge = []  # list of sentences

    def mark_mine(self, cell):
        # mark cell as mine and update all sentences
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        # mark cell as safe and update all sentences
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        # called when we click a cell and see the number
        
        # remember we made this move
        self.moves_made.add(cell)
        
        # this cell is definitely safe
        self.mark_safe(cell)

        # find all neighbors we dont know about yet
        neighbors = set()
        already_known_mines = 0
        
        # check all 8 neighbors
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                if (i, j) == cell:
                    continue
                    
                # stay in bounds
                if 0 <= i < self.height and 0 <= j < self.width:
                    # if we already know its a mine, count it
                    if (i, j) in self.mines:
                        already_known_mines += 1
                    # if we dont know if its safe, add to neighbors
                    elif (i, j) not in self.safes:
                        neighbors.add((i, j))

        # subtract mines we already know about
        remaining_count = count - already_known_mines

        # make new sentence if we have unknown neighbors
        if neighbors:
            self.knowledge.append(Sentence(neighbors, remaining_count))

        # see if we can learn anything new
        self.update_knowledge()

    def update_knowledge(self):
        # try to learn new info from what we know
        
        changed = True
        while changed:
            changed = False
            new_mines = set()
            new_safes = set()

            # check each sentence for obvious mines/safes
            for sentence in self.knowledge:
                mines = sentence.known_mines()
                safes = sentence.known_safes()

                if mines:
                    new_mines.update(mines)
                if safes:
                    new_safes.update(safes)

            # mark new mines we found
            for mine in new_mines:
                if mine not in self.mines:
                    self.mark_mine(mine)
                    changed = True

            # mark new safes we found
            for safe in new_safes:
                if safe not in self.safes:
                    self.mark_safe(safe)
                    changed = True

            # remove empty sentences
            self.knowledge = [s for s in self.knowledge if s.cells]
            
            # try to make new sentences by combining old ones
            new_sentences = []
            for sentence1 in self.knowledge:
                for sentence2 in self.knowledge:
                    # if sentence2 is subset of sentence1, we can subtract
                    if sentence1 != sentence2 and sentence2.cells.issubset(sentence1.cells) and sentence2.cells:
                        new_cells = sentence1.cells - sentence2.cells
                        new_count = sentence1.count - sentence2.count

                        if new_count >= 0:
                            new_sentence = Sentence(new_cells, new_count)
                            if new_sentence not in self.knowledge and new_sentence not in new_sentences:
                                new_sentences.append(new_sentence)
                                changed = True

            # add new sentences we figured out
            self.knowledge.extend(new_sentences)

    def make_safe_move(self):
        # pick a safe cell we havent clicked yet
        for move in self.safes:
            if move not in self.moves_made:
                return move
        return None

    def make_random_move(self):
        # pick random cell that isnt a mine or already clicked
        all_cells = set(itertools.product(range(self.height), range(self.width)))
        possible_moves = list(all_cells - self.moves_made - self.mines)

        if possible_moves:
            return random.choice(possible_moves)
        else:
            return None