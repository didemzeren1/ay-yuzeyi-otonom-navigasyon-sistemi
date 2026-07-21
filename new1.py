import numpy as np          # NumPy library for numerical computations
import cv2                   # OpenCV library for image processing
import rasterio              # For reading geographic raster files such as GeoTIFF
import heapq                 # Python's built-in module for priority queue (min-heap)
import random                # For generating a random starting point

FILE = 'LRO_LOLA_ClrSlope_Global_16ppd.tif'  # Path to the lunar slope map TIF file
END  = (800, 600)                              # Target pixel coordinate the route should reach (x, y)
LOG_STEP = 50                                  # How often (in steps) the A* algorithm prints info to the console

# -------------------------------------------------------------
# FUNCTION: prepare_map
# Reads the TIF file, normalises the image, creates a colour
# mask, and builds a cost matrix for every pixel.
# -------------------------------------------------------------
def prepare_map():
    with rasterio.open(FILE) as src:                    # Open the TIF file with rasterio
        data = src.read([1, 2, 3]).transpose(1, 2, 0)    # Read R, G, B bands; rearrange axes (channel,row,col) -> (row,col,channel)
        img = cv2.normalize(data, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')  # Normalise pixel values to 0-255 and convert to uint8

    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)           # Convert image from RGB to HSV colour space (better for colour detection)
    border = cv2.addWeighted(img, 0.5, cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB), 0.5, 0)  # Blend RGB and HSV->RGB 50/50 for visual richness (kept for future visualisation)

    mask = cv2.inRange(hsv, np.array([10, 100, 100]), np.array([35, 255, 255]))  # Detect yellow-orange range (H:10-35) in HSV -> safe-zone mask

    rows, cols = img.shape[:2]  # Get the number of rows (height) and columns (width) of the image

    cost_matrix = np.ones((rows, cols), dtype=np.float32) * 100  # Mark all pixels as costly (dangerous) with initial value 100
    cost_matrix[mask > 0] = 1                                    # Lower the cost of yellow-orange (safe) pixels to 1

    print(f"[MAP] Size: {cols}x{rows} pixels")                    # Print map dimensions to console
    safe = np.sum(mask > 0)                                       # Count the number of safe pixels
    print(f"[MAP] Safe: {safe} px | Dangerous: {rows*cols-safe} px")  # Print safe/dangerous pixel statistics

    return img, cost_matrix, hsv, cols, rows  # Return normalised image, cost matrix, HSV image, and dimensions


# -------------------------------------------------------------
# FUNCTION: detect_colour
# Returns a text label describing the risk zone at pixel (x, y)
# based on its HSV values.
# -------------------------------------------------------------
def detect_colour(hsv, x, y):
    h, s, v = hsv[y, x]       # Get Hue, Saturation, Value of the target pixel

    if s < 50:               # Low saturation means the colour is pale/white/grey
        return "White/Grey"
    elif 10 <= h <= 35:      # Hue 10-35 -> yellow-orange -> safe zone
        return "Yellow-Orange (Safe)"
    elif 35 < h <= 85:       # Hue 35-85 -> green -> medium-risk zone
        return "Green (Medium Risk)"
    elif 85 < h <= 130:      # Hue 85-130 -> blue -> high-risk zone
        return "Blue (High Risk)"
    else:                    # Other hue values -> red/purple -> dangerous zone
        return "Red/Purple (Dangerous)"


# -------------------------------------------------------------
# FUNCTION: astar
# Uses the cost matrix to find the lowest-cost route from
# start to end via the A* algorithm.
# Heuristic: Manhattan distance (|dx| + |dy|)
# -------------------------------------------------------------
def astar(cost_matrix, start, end):
    rows, cols = cost_matrix.shape             # Get dimensions of the cost matrix
    sx, sy = start                             # Unpack start coordinates
    ex, ey = end                               # Unpack end coordinates

    print(f"\n[A*] Start: {start} -> Target: {end}")                                  # Print start and target info
    print(f"[A*] Start zone: {'safe' if cost_matrix[sy,sx]==1 else 'DANGEROUS'}")    # Check whether start is safe or dangerous
    print(f"[A*] Target zone: {'safe' if cost_matrix[ey,ex]==1 else 'DANGEROUS'}")   # Check whether target is safe or dangerous

    heap = []                                              # Initialise the min-heap (priority queue)
    heapq.heappush(heap, (0, 0, sx, sy, None))             # Push start node: (f_score, g_score, x, y, parent)

    g_map = np.full((rows, cols), np.inf)                  # Initialise real cost from start to every pixel as infinity
    g_map[sy, sx] = 0                                      # Set cost of start pixel to 0

    parent_map = {}       # Dictionary tracking which pixel each pixel was reached from (for path backtracking)
    visited = set()       # Set of already-processed (visited) pixels

    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]  # 8-directional movement: up, down, left, right, and 4 diagonals

    step = 0              # Counter for the number of processed nodes

    while heap:                                    # Loop until the queue is empty
        f, g, x, y, parent = heapq.heappop(heap)  # Pop the node with the lowest f score

        if (x, y) in visited:   # Skip if already processed (stale, higher-cost copy)
            continue

        visited.add((x, y))          # Mark point as visited
        parent_map[(x, y)] = parent  # Record which node we came from
        step += 1                    # Increment step counter

        if step % LOG_STEP == 0:                                               # Print status report every LOG_STEP steps
            remaining = abs(x - ex) + abs(y - ey)                              # Calculate Manhattan distance remaining to target
            zone = 'safe' if cost_matrix[y, x] == 1 else 'DANGEROUS'        # Determine safety status of current zone
            print(f"[SCAN #{step:>5}] Pos: ({x:>4},{y:>4}) | Remaining: {remaining:>4} px | {zone}")  # Print position and status

        if (x, y) == (ex, ey):                        # Target reached - reconstruct path by backtracking
            print(f"\n[A*] Target reached! Nodes scanned: {step}")  # Print success message and scanned node count
            path = []                                  # Initialise path list
            node = (ex, ey)                            # Start backtracking from the target
            while node is not None:                    # Follow parents until start is reached
                path.append(node)                      # Add current node to path
                node = parent_map[node]                # Move to the previous node (parent)
            path.reverse()                             # Reverse list (start -> target order)
            return path, g                             # Return full path and total cost

        for dx, dy in directions:              # Loop over 8 neighbouring directions
            nx, ny = x + dx, y + dy              # Compute neighbour pixel coordinates

            if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in visited:  # Process if inside map bounds and unvisited
                move_cost = cost_matrix[ny, nx] * (1.414 if dx != 0 and dy != 0 else 1)  # Movement cost: multiply by sqrt(2)~1.414 for diagonal, 1 for straight
                new_g = g + move_cost                                                         # New cumulative real cost (g score)

                if new_g < g_map[ny, nx]:                         # Update if this path is cheaper than the one previously found
                    g_map[ny, nx] = new_g                         # Update cost in the g map
                    h = abs(nx - ex) + abs(ny - ey)                # Heuristic: Manhattan distance to target
                    heapq.heappush(heap, (new_g + h, new_g, nx, ny, (x, y)))  # Push with f = g + h score

    return [], 0  # Queue exhausted but target not reached; return empty path and zero cost


# -------------------------------------------------------------
# MAIN PROGRAM FLOW
# -------------------------------------------------------------

img, cost_matrix, hsv, cols, rows = prepare_map()  # Prepare map; get image, cost matrix, and dimensions

START = (random.randint(0, cols-1), random.randint(0, rows-1))  # Generate a random starting coordinate within the map

colour = detect_colour(hsv, START[0], START[1])    # Determine the colour/risk category of the start pixel
h, s, v = hsv[START[1], START[0]]                  # Get raw HSV values of the start pixel

print(f"\n[START] Coordinate: {START}")             # Print start coordinate
print(f"[START] HSV: H={h}, S={s}, V={v}")          # Print HSV values of start pixel
print(f"[START] Colour: {colour}")                  # Print colour/risk info of start zone
print(f"[START] Cost: {cost_matrix[START[1], START[0]]:.0f}")  # Print cost value of start pixel

path, total_cost = astar(cost_matrix, START, END)  # Run A* algorithm; get the found path and total cost

if path:  # If a valid path was found, process and visualise results
    safe_steps = sum(1 for (x,y) in path if cost_matrix[y,x] == 1)             # Count safe steps on the path
    print(f"\n[RESULT] Total steps: {len(path)}")                                  # Print total step count
    print(f"[RESULT] Safe: {safe_steps} | Dangerous: {len(path)-safe_steps}")     # Print safe/dangerous step breakdown

    output = img.copy()                                                            # Create a copy of the original image for drawing

    for (x, y) in path:
        cv2.circle(output, (x, y), 3, (255, 0, 0), -1)                            # Draw a small blue circle on each path pixel

    cv2.circle(output, START, 8, (0, 255, 0), 20)                                 # Mark start point with a green circle
    cv2.circle(output, END,   8, (0, 0, 255), 20)                                 # Mark end point with a red circle

    cv2.imwrite("moon_result.png", cv2.cvtColor(output, cv2.COLOR_RGB2BGR))      # Convert to BGR and save result image as PNG
    print(f"[FILE] moon_result.png saved.")                                        # Confirm file was saved to console

else:  # Queue exhausted and target unreachable - print error message
    print("\n[ERROR] Route not found!")  # Print error indicating no route was found