from js import document
from pyodide.ffi import create_proxy
import asyncio

canvas = document.getElementById("grid")
ctx = canvas.getContext("2d")
run = document.getElementById("run")

GRID_WIDTH = 900
GRID_HEIGHT = 600
CELL_SIZE = 30
ROWS = GRID_HEIGHT // CELL_SIZE
COLS = GRID_WIDTH // CELL_SIZE
GRID = [[0 for x in range(COLS)] for y in range(ROWS)]

COLORS = {
    0: "#ecf0f1",   # Path
    1: "#2c3e50",   # Wall
    2: "#27ae60",   # Start
    3: "#c0392b",   # End
    4: "#2980b9",   # Observed
    5: "#1abc9c",   # Queued
    6: "#f39c12",   # Path
    7: "rgba(155, 89, 182, 0.5)"    # Hover
}

class Node:
    def __init__(self, y, x, parent):
        self.y = y
        self.x = x
        self.parent = parent
        
        self.gCost = 0
        self.hCost = 0
    
    def __eq__(self, node):
        return isinstance(node, Node) and self.y == node.y and self.x == node.x
    
    def getPos(self):
        return self.y, self.x
    
    def getNeighbors(self):  
        up = Node(self.y - 1, self.x, self)
        right = Node(self.y, self.x + 1, self)
        down = Node(self.y + 1, self.x, self)
        left = Node(self.y, self.x - 1, self)

        ur = Node(self.y - 1, self.x + 1, self)
        dr = Node(self.y + 1, self.x + 1, self)
        dl = Node(self.y + 1, self.x - 1, self)
        ul = Node(self.y - 1, self.x - 1, self)

        return up, right, down, left, ur, dr, dl, ul
    
    def fCost(self):
        return self.gCost + self.hCost

def main():
    global START, END, open, closed
    global mouse_down, draw_mode, hover

    START = None
    END = None
    open = []
    closed = []
    mouse_down = False
    hover = None

    START = setStart(1, 1)
    END = setEnd(COLS - 2, ROWS - 2)

    draw_grid()

    canvas.addEventListener("contextmenu", create_proxy(disable_context_menu))
    canvas.addEventListener("mousedown", create_proxy(handleDown))
    document.addEventListener("mouseup", create_proxy(handleUp))
    canvas.addEventListener("mousemove", create_proxy(handleMove))
    run.addEventListener("click", create_proxy(runPathfinding))

def disable_context_menu(event):
    event.preventDefault()

async def runPathfinding(event=None):
    run.disabled = True
    found = False
    start()
    while not found:
        found = AStar()
        if found == True:
            reconstructPath()
        elif found == False:
            break
        draw_grid()
        await asyncio.sleep(0.01)
    run.disabled = False

##############################
#      Helper Functions      #
##############################

def draw_grid():
    for x in range(COLS):
        for y in range(ROWS):
            ctx.fillStyle = COLORS[GRID[y][x]]
            ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            ctx.strokeRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    if hover:
        x, y = hover
        ctx.fillStyle = COLORS[7]
        ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

def setStart(x, y):
    if START:
        GRID[START.y][START.x] = 0
    GRID[y][x] = 2
    return Node(y, x, None)

def setEnd(x, y): 
    if END:
        GRID[END.y][END.x] = 0
    GRID[y][x] = 3
    return Node(y, x, None)

def handleDown(event):
    global mouse_down, draw_mode
    mouse_down = True
    draw_mode = "wall" if event.button == 0 else "erase"
    updateCell(event)

def handleUp(event):
    global mouse_down
    mouse_down = False

def handleMove(event):
    global hover
    x, y = getCoordsFromPosition(event.offsetX, event.offsetY)
    if 0 <= x < COLS and 0 <= y < ROWS:
        hover = (x, y)
    else:
        hover = None
    if mouse_down:
        updateCell(event)
    else:
        draw_grid()

def updateCell(event):
    x, y = getCoordsFromPosition(event.offsetX, event.offsetY)
    if 0 <= x < COLS and 0 <= y < ROWS:
        GRID[y][x] = 1 if draw_mode == "wall" else 0
        draw_grid()

def getCoordsFromPosition(xPos, yPos):
    return xPos // CELL_SIZE, yPos // CELL_SIZE

def start():
    open.clear()
    open.append(START)
    closed.clear()
    for x in range(0, COLS):
        for y in range(0, ROWS):
            if GRID[y][x] in [4, 5, 6]:
                GRID[y][x] = 0
    GRID[START.y][START.x] = 2
    GRID[END.y][END.x] = 3 

def inGrid(x, y):
    return (x >= 0 and x < COLS) and (y >= 0 and y < ROWS)

def isPath(node):
    return inGrid(node.x, node.y) and GRID[node.y][node.x] != 1
    
def HCost(node):
    dy = abs(END.y - node.y)
    dx = abs(END.x - node.x)
    return max(dy, dx)

def reconstructPath():
    curr = closed.pop()
    parent = curr.parent
    while parent != None:
        GRID[curr.y][curr.x] = 6
        for node in closed:
            if parent == node:
                curr, parent = node, node.parent
                break
    
    GRID[START.y][START.x] = 2
    GRID[END.y][END.x] = 3

##############################
#         Algorithms         #
##############################

def AStar():
    if not open:
        return False
    open.sort(key = lambda node: node.fCost())
    curr = open.pop(0)
    closed.append(curr)
    GRID[curr.y][curr.x] = 4
    if curr == END:
        return True
    neighbors = curr.getNeighbors()
    for neighbor in neighbors:
        if isPath(neighbor) and neighbor not in closed:
            neighbor.gCost = curr.gCost + 1
            neighbor.hCost = HCost(neighbor)
            if neighbor in open:
                for i in range(len(open)):
                    if open[i] == neighbor and neighbor.gCost < open[i].gCost:
                        open[i] = neighbor
            else:
                open.append(neighbor)
                GRID[neighbor.y][neighbor.x] = 5

if __name__ == "__main__":
    main()