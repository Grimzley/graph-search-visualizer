from js import document
from pyodide.ffi import create_proxy
import asyncio

canvas = document.getElementById("grid")
ctx = canvas.getContext("2d")
runBtn = document.getElementById("run")
resetBtn = document.getElementById("reset")
clearBtn = document.getElementById("clear")
dropdown = document.getElementById("dropdownMenuButton")
toggleBtn = document.getElementById("toggleDiagonal")
algoText = document.getElementById("selectedAlgoText")
statText = document.getElementById("statText")

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
    5: "#5dade2",   # Queued
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
    
    def getNeighbors(self):
        up = Node(self.y - 1, self.x, self)
        right = Node(self.y, self.x + 1, self)
        down = Node(self.y + 1, self.x, self)
        left = Node(self.y, self.x - 1, self)
        if DIAGONAL:
            ur = Node(self.y - 1, self.x + 1, self)
            dr = Node(self.y + 1, self.x + 1, self)
            dl = Node(self.y + 1, self.x - 1, self)
            ul = Node(self.y - 1, self.x - 1, self)
            return up, right, down, left, ur, dr, dl, ul
        return up, right, down, left
    
    def fCost(self):
        return self.gCost + self.hCost

def main():
    global START, END, open, closed, DIAGONAL, ALGORITHM, searching
    global mouse_pos, mouse_over_canvas, mouse_down, draw_mode, hover

    START = None
    END = None
    open = []
    closed = []
    DIAGONAL = True
    set_algorithm(None, "astar", "A*")
    searching = False

    mouse_pos = {"x": 0, "y": 0}
    mouse_over_canvas = False
    mouse_down = False
    hover = None

    START = setStart(1, 1)
    END = setEnd(COLS - 2, ROWS - 2)

    draw_grid()

    canvas.addEventListener("contextmenu", create_proxy(disable_context_menu))
    canvas.addEventListener("mousedown", create_proxy(handleDown))
    document.addEventListener("mouseup", create_proxy(handleUp))
    canvas.addEventListener("mousemove", create_proxy(handleMove))
    canvas.addEventListener("mouseenter", create_proxy(handleMouseEnter))
    canvas.addEventListener("mouseleave", create_proxy(handleMouseLeave))
    document.addEventListener("keydown", create_proxy(handleKey))
    runBtn.addEventListener("click", create_proxy(runPathfinding))
    resetBtn.addEventListener("click", create_proxy(reset))
    clearBtn.addEventListener("click", create_proxy(clear))
    toggleBtn.addEventListener("click", create_proxy(toggleDiagonal))

    document.getElementById("astar").addEventListener(
        "click", create_proxy(lambda e: set_algorithm(e, "astar", "A*"))
    )
    document.getElementById("greedy").addEventListener(
        "click", create_proxy(lambda e: set_algorithm(e, "greedy", "Greedy BFS"))
    )
    document.getElementById("bfs").addEventListener(
        "click", create_proxy(lambda e: set_algorithm(e, "bfs", "BFS"))
    )
    document.getElementById("dfs").addEventListener(
        "click", create_proxy(lambda e: set_algorithm(e, "dfs", "DFS"))
    )
    
def disable_context_menu(event):
    event.preventDefault()

async def runPathfinding(event=None):
    global ALGORITHM, searching
    toggleButtons()
    start()
    while searching:
        found = ALGORITHM()
        if found == True:
            pathLength = reconstructPath()
            searching = False
        elif found == False:
            pathLength = "N/A"
            searching = False
        draw_grid()
        await asyncio.sleep(0.01)
    statText.innerText = f"Observed Cells: {len(closed)}, Queued Cells: {len(open)}, Path Length: {pathLength}"
    toggleButtons()

##############################
#         User Input         #
##############################

def handleDown(event):
    global mouse_down, draw_mode
    mouse_down = True
    draw_mode = "wall" if event.button == 0 else "erase"
    updateCell(mouse_pos["x"], mouse_pos["y"])

def handleUp(event):
    global mouse_down
    mouse_down = False

def handleMove(event):
    global hover
    x, y = getCoordsFromPosition(event.offsetX, event.offsetY)
    mouse_pos["x"] = x
    mouse_pos["y"] = y
    if 0 <= x < COLS and 0 <= y < ROWS:
        hover = (x, y)
    else:
        hover = None
    if mouse_down:
        updateCell(x, y)
    draw_grid()

def handleMouseEnter(event):
    global mouse_over_canvas
    mouse_over_canvas = True

def handleMouseLeave(event):
    global mouse_over_canvas
    mouse_over_canvas = False

async def handleKey(event):
    if not searching:
        key = event.key
        if mouse_over_canvas:
            x = mouse_pos["x"]
            y = mouse_pos["y"]
            if key.lower() == "s":
                global START
                START = setStart(x, y)
            elif key.lower() == "e":
                global END
                END = setEnd(x, y)
        if key.lower() == "d":
            toggleBtn.checked = not toggleBtn.checked
            toggleDiagonal()
        elif key == " ":
            await runPathfinding()
        elif key.lower() == "r":
            reset()
        elif key.lower() == "c":
            clear()
        draw_grid()

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

def set_algorithm(event, algo, label):
    global ALGORITHM
    ALGORITHMS = {
        "astar": AStar,
        "greedy": Greedy,
        "bfs": BFS,
        "dfs": DFS,
    }
    ALGORITHM = ALGORITHMS[algo] 
    algoText.innerText = label

def updateCell(x, y):
    if 0 <= x < COLS and 0 <= y < ROWS:
        GRID[y][x] = 1 if draw_mode == "wall" else 0

def getCoordsFromPosition(xPos, yPos):
    return xPos // CELL_SIZE, yPos // CELL_SIZE

def toggleDiagonal(event=None):
    global DIAGONAL
    if not searching:
        DIAGONAL = not DIAGONAL

def start():
    global searching
    open.clear()
    open.append(START)
    closed.clear()
    for x in range(0, COLS):
        for y in range(0, ROWS):
            if GRID[y][x] in [4, 5, 6]:
                GRID[y][x] = 0
    GRID[START.y][START.x] = 2
    GRID[END.y][END.x] = 3 
    searching = True

def reset(event=None):
    global searching
    open.clear()
    closed.clear()
    for x in range(0, COLS):
        for y in range(0, ROWS):
            if GRID[y][x] in [4, 5, 6]:
                GRID[y][x] = 0
    GRID[START.y][START.x] = 2
    GRID[END.y][END.x] = 3
    searching = False
    draw_grid()

def clear(event=None):
    global searching
    for x in range(0, COLS):
        for y in range(0, ROWS):
            GRID[y][x] = 0
    GRID[START.y][START.x] = 2
    GRID[END.y][END.x] = 3
    searching = False
    draw_grid()

def toggleButtons():
    runBtn.disabled = not runBtn.disabled
    resetBtn.disabled = not resetBtn.disabled
    clearBtn.disabled = not clearBtn.disabled
    dropdown.disabled = not dropdown.disabled
    toggleBtn.disabled = not toggleBtn.disabled

def inGrid(x, y):
    return (x >= 0 and x < COLS) and (y >= 0 and y < ROWS)

def isPath(node):
    return inGrid(node.x, node.y) and GRID[node.y][node.x] != 1
    
def HCost(node):
    dy = abs(END.y - node.y)
    dx = abs(END.x - node.x)
    if DIAGONAL:
        return max(dy, dx)
    else:
        return dy + dx

def reconstructPath():
    curr = closed[-1]
    parent = curr.parent
    pathLength = 1
    while parent != None:
        GRID[curr.y][curr.x] = 6
        curr, parent = parent, parent.parent
        pathLength = pathLength + 1
    GRID[START.y][START.x] = 2
    GRID[END.y][END.x] = 3
    return pathLength

##############################
#         Algorithms         #
##############################

def DFS():
    if not open:
        return False
    curr = open.pop()
    closed.append(curr)
    GRID[curr.y][curr.x] = 4
    if curr == END:
        return True
    neighbors = curr.getNeighbors()
    for neighbor in neighbors:
        if isPath(neighbor) and neighbor not in closed and neighbor not in open:
            open.append(neighbor)
            GRID[neighbor.y][neighbor.x] = 5

def BFS():
    if not open:
        return False
    curr = open.pop(0)
    closed.append(curr)
    GRID[curr.y][curr.x] = 4
    if curr == END:
        return True
    neighbors = curr.getNeighbors()
    for neighbor in neighbors:
        if isPath(neighbor) and neighbor not in closed and neighbor not in open:
            open.append(neighbor)
            GRID[neighbor.y][neighbor.x] = 5

def Greedy():
    if not open:
        return False
    open.sort(key = lambda node: node.hCost)
    curr = open.pop(0)
    closed.append(curr)
    GRID[curr.y][curr.x] = 4
    if curr == END:
        return True
    neighbors = curr.getNeighbors()
    for neighbor in neighbors:
        if isPath(neighbor) and neighbor not in closed and neighbor not in open:
            neighbor.hCost = HCost(neighbor)
            open.append(neighbor)
            GRID[neighbor.y][neighbor.x] = 5

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
    