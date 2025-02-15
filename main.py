import pygame
import random
import os
# import math

# base code for including a certain pixel in the metaball follows khan academy demo
# https://www.khanacademy.org/computer-programming/Metaballs!/6209526669246464

# marching squares, linear interp

# window position
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 0)

# usual pygame stuff
pygame.init()
screen_width = 500
screen_height = 500
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.font.init()
my_font = pygame.font.Font("segoe-ui-symbol.ttf", 12)
my_other_font = pygame.font.Font("segoe-ui-symbol.ttf", 16)

clock = pygame.time.Clock()
fps = 30

border_surface = pygame.surface.Surface((screen_width, screen_height), pygame.SRCALPHA, 32)
border_surface = border_surface.convert_alpha()

# ---> initial stuff + settings <---
running = True
WHITE = (255, 255, 255)
PX_SIZE = 25
# 500 has to be a multiple
# I do recommend having the PX_SIZE be 25, or 20. maybe 10
# it looks better with the grid :3

NUM_CIRCLES_INIT = 4

# ---> SETTINGS <---
additive = False
# True = light mixing, False = gradient

interpolation = True
circle_glow = True
debug_mode = True
grid_on = True
border_width = 5

rgbcolor_max = 225
rgbcolor_min = 75
if additive: 
    rgbcolor_max = 150
    rgbcolor_min = 20

A = 0.55 # between 0 and 1

# A is in effect for when additive == True
# that controls how much a light-ball's brightness is affected by the balls around it
# The HIGHER the A value, the less the light-balls will be affected by other colors. 
# It's a 0-1 value. ~0.7 is nice for like, 3 light-balls (25px size)
# many light-balls = brightness goes up a lot 

glow_isovalue = 0.4
# how high the value of a surrounding 0 < pixel < 1  must be
# until it is part of the glowing radius

# storage
isovaluegrid = [[0.0 for i in range(screen_width//PX_SIZE)] for i in range(screen_height//PX_SIZE)]
colors_grid = [[[-1, -1, -1] for i in range(screen_width//PX_SIZE)] for i in range(screen_height//PX_SIZE)]
circles = []

# circles init - random speed, random radius, etc
# adding this bit so it doesn't get super bright for lights

for i in range(NUM_CIRCLES_INIT):
    circles.append({
        "x": random.randint(0, screen_width),
        "y": random.randint(0, screen_height),
        "r": random.randint(40, 80),
        "vx": random.randint(-5, border_width),
        "vy": random.randint(-5, border_width),
        "red": random.randint(rgbcolor_min, rgbcolor_max),
        "green": random.randint(rgbcolor_min, rgbcolor_max),
        "blue": random.randint(rgbcolor_min, rgbcolor_max),

        "alt_red": 0,
        "alt_green": 0,
        "alt_blue": 0,
    })


b = 0.6
# 0.6 is just for balancing the brightness as u switch modes

if additive:
    # alt will be subtractive (paint)
    # make it lighter for the paint
    for c in circles: 
        c["alt_red"] = min(255, round(c["red"] / b))
        c["alt_green"] = min(255, round(c["green"] / b))
        c["alt_blue"] = min(255, round(c["blue"] / b))

else: 
    # alt will be additive
    # we'll make it darker cuz the light gets bright sorta fast
    for c in circles: 
        c["alt_red"] = round(c["red"] * b)
        c["alt_green"] = round(c["green"] * b)
        c["alt_blue"] = round(c["blue"] * b)


# PROGRAM
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        click_in = False
        space = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if mouse_x <= 130 and mouse_y <= 40:
                click_in = True
        
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            space = True

        if space or click_in:
            if additive: additive = False
            else: additive = True

            for c in circles:
                temp1 = c["red"]
                temp2 = c["green"]
                temp3 = c["blue"]

                c["red"] = c["alt_red"]
                c["green"] = c["alt_green"]
                c["blue"] = c["alt_blue"]

                c["alt_red"] = temp1
                c["alt_green"] = temp2
                c["alt_blue"] = temp3

    # refresh per frame
    
    screen.fill((0, 0, 0))
    border_surface.fill((0, 0, 0, 0))

    for i in range(len(circles)):
        c = circles[i]

        c["x"] += c["vx"]
        c["y"] += c["vy"]
        
        # circle bounce around screen
        if (c["x"] - c["r"] < 0): c["vx"] = +abs(c["vx"])
        if (c["x"] + c["r"] > screen_width): c["vx"] = -abs(c["vx"])
        if (c["y"] - c["r"] < 0): c["vy"] = +abs(c["vy"])
        if (c["y"] + c["r"] > screen_height): c["vy"] = -abs(c["vy"])
        
    # draw grid
    if grid_on:
        for i in range(0, screen_width, PX_SIZE):
            pygame.draw.line(border_surface, WHITE, [i, 0], [i, screen_height], 1)
        for j in range(0, screen_height, PX_SIZE):
            pygame.draw.line(border_surface, WHITE, [0, j], [screen_width, j], 1)

    # drawing the pixels, drawing the colors
    for y in range(0, screen_height, PX_SIZE):
        for x in range(0, screen_width, PX_SIZE):
            sum = 0
            closestD2 = float('inf')
            newRGB = [0, 0, 0]
            newclosestX = None
            newclosestY = None

            red_weight_numerator = 0
            red_weight_denom = 0
            green_weight_numerator = 0
            green_weight_denom = 0
            blue_weight_numerator = 0
            blue_weight_denom = 0

            for i in range(len(circles)):
                c = circles[i]
                dx = x - c["x"]
                dy = y - c["y"]
                d2 = dx * dx + dy * dy
                if (d2 == 0): sum = float('inf')
                else: sum += c["r"] * c["r"] / d2

                index_d2 = (dx // PX_SIZE) ** 2 + (dy // PX_SIZE) ** 2

                # ADDITIVE -> light mixing style. NOT additive -> paint mixing style
                if not additive:
                    red_weight_numerator += c["red"] * index_d2
                    red_weight_denom += index_d2
                    green_weight_numerator += c["green"] * index_d2
                    green_weight_denom += index_d2
                    blue_weight_numerator += c["blue"] * index_d2
                    blue_weight_denom += index_d2

                else: # the light mixing is sort of weird tbh
                    # A = 0.65 
                    # some kinda blending between 0 and 1

                    # I just added a + 1 so that there wouldn't be a division by 0 error when resolution is very low
                    index_d = (index_d2) ** A / (c["r"] // PX_SIZE + 1) - 1
                    if index_d < 0: index_d = 0

                    red_weight_numerator += c["red"] / (index_d + 1)
                    green_weight_numerator += c["green"] / (index_d + 1) 
                    blue_weight_numerator += c["blue"]  / (index_d +1) 


            if not additive:
                # make the fraction, values
                newRGB = [
                    round(red_weight_numerator / (red_weight_denom + 1)),
                    round(green_weight_numerator / (green_weight_denom + 1)),
                    round(blue_weight_numerator / (blue_weight_denom + 1))
                ]

            else:
                # values
                newRGB = [
                    round(red_weight_numerator),
                    round(green_weight_numerator),
                    round(blue_weight_numerator),
                ]

            # color cap at 255
            for i in range(3):
                if newRGB[i] > 255: newRGB[i] = 255
            
            # set grid
            if debug_mode and sum <= glow_isovalue: 
                # stop printing numbers once it reaches the circle glow threshold 
                # since the squares wont be blank and will have some kinda color

                text_surface = my_font.render(str(round(sum, 2)), False, (255, 255, 255))
                screen.blit(text_surface, (x , y - 2))

            if not (newRGB[0] == 0 and newRGB[1] == 0 and newRGB[2] == 0):
                colors_grid[y // PX_SIZE][x // PX_SIZE]  = newRGB

            isovaluegrid[y // PX_SIZE][x // PX_SIZE] = round(sum, 2) # now it's filled
    

    # here's all the messy marching squares stuff, and color filling
    for y in range(len(isovaluegrid) - 1):
        for x in range(len(isovaluegrid[0]) - 1):

            px = x * PX_SIZE
            py = y * PX_SIZE

            top_left = isovaluegrid[y][x]
            top_right = isovaluegrid[y][x + 1]
            bottom_left = isovaluegrid[y + 1][x]
            bottom_right = isovaluegrid[y + 1][x + 1]

            py_for_leftside_offset = PX_SIZE // 2
            py_for_rightside_offset = PX_SIZE // 2
            px_for_topside_offset = PX_SIZE // 2
            px_for_bottomside_offset = PX_SIZE // 2

            if interpolation:
                # pixelC = pixelA + [(1 - vA) / (vB - vA)] * (pixelB - pixelA)
                
                if (bottom_left - top_left) != 0: 
                    py_for_leftside_offset = ((1 - top_left) / (bottom_left - top_left)) * PX_SIZE
                
                if (bottom_right - top_right) != 0: 
                    py_for_rightside_offset = ((1 - top_right) / (bottom_right - top_right)) * PX_SIZE

                if (top_right - top_left) != 0: 
                    px_for_topside_offset = ((1 - top_left) / (top_right - top_left)) * ((PX_SIZE))
                
                if (bottom_right - bottom_left) != 0: 
                    px_for_bottomside_offset = ((1 - bottom_left) / (bottom_right - bottom_left)) * ((PX_SIZE))

            # retrieve the pixel's color
            pixel_color = colors_grid[y][x]
            border_color = pixel_color[:]

            for i in range(3):
                border_color[i] *= 1.5
                if border_color[i] > 255: border_color[i] = 255

            if circle_glow:
                v = isovaluegrid[y][x]
                # Glow threshold
                # glow_isovalue is like 0.x
                if v > glow_isovalue and not (top_left >= 1 and top_right >= 1 and bottom_left >= 1 and bottom_right >= 1):
                    # edit: + and not internally all inside the blob, we don't need to compute that

                    # this makes the colors drawn dimmer
                    r = round(min(255, pixel_color[0] * (min(1.1, v) - glow_isovalue) ))
                    g = round(min(255, pixel_color[1] * (min(1.1, v) - glow_isovalue) ))
                    b = round(min(255, pixel_color[2] * (min(1.1, v) - glow_isovalue) ))

                    if not (r == g == b == 0): 
                        pygame.draw.polygon(
                            screen,
                            [r, g, b],
                            [ 
                                (px, py), 
                                (px, py + PX_SIZE), 
                                (px + PX_SIZE, py + PX_SIZE), 
                                (px + PX_SIZE, py)
                            ]
                        )

            # Case 0: No intersection (all below the threshold)
            if top_left < 1 and top_right < 1 and bottom_left < 1 and bottom_right < 1:
                continue 
        
            # Case 1: Only bottom-left is above the threshold
            elif top_left < 1 and top_right < 1 and bottom_left >= 1 and bottom_right < 1:
                pygame.draw.polygon(screen, pixel_color, [(px, py+py_for_leftside_offset), (px+px_for_bottomside_offset, py + PX_SIZE), (px, py + PX_SIZE)])

                pygame.draw.line(border_surface, border_color, (px, py + py_for_leftside_offset), (px + px_for_bottomside_offset, py + PX_SIZE), border_width)

            # Case 2: Only bottom-right is above the threshold 
            elif top_left < 1 and top_right < 1 and bottom_left < 1 and bottom_right >= 1:

                pygame.draw.polygon(screen, pixel_color, [(px + px_for_bottomside_offset, py + PX_SIZE), (px + PX_SIZE, py + py_for_rightside_offset), (px + PX_SIZE, py + PX_SIZE)])

                pygame.draw.line(border_surface, border_color, (px + px_for_bottomside_offset, py + PX_SIZE), (px + PX_SIZE, py + py_for_rightside_offset), border_width)

            # Case 3: Both bottom-left and bottom-right are above the threshold
            elif top_left < 1 and top_right < 1 and bottom_left >= 1 and bottom_right >= 1:
            
                pygame.draw.polygon(screen, pixel_color, [(px, py + py_for_leftside_offset), (px + PX_SIZE, py + py_for_rightside_offset), (px + PX_SIZE, py + PX_SIZE), (px, py + PX_SIZE)])

                pygame.draw.line(border_surface, border_color, (px, py + py_for_leftside_offset), (px + PX_SIZE, py + py_for_rightside_offset), border_width)


            # Case 4: Only top-left is above the threshold 
            elif top_left >= 1 and top_right < 1 and bottom_left < 1 and bottom_right < 1:

                pygame.draw.polygon(screen, pixel_color, [(px + px_for_topside_offset, py), (px, py + py_for_leftside_offset), (px, py)])

                pygame.draw.line(border_surface, border_color, (px + px_for_topside_offset, py), (px, py + py_for_leftside_offset), border_width)

           # Case 5: Top-left and bottom-left are above the threshold
            elif top_left >= 1 and top_right < 1 and bottom_left >= 1 and bottom_right < 1:
                pygame.draw.polygon(screen, pixel_color, [(px + px_for_topside_offset, py), (px + px_for_bottomside_offset, py + PX_SIZE), (px, py + PX_SIZE), (px, py)])

                pygame.draw.line(border_surface, border_color, (px + px_for_topside_offset, py), (px + px_for_bottomside_offset, py + PX_SIZE), border_width)

            # Case 6: Top-left and top-right are above the threshold
            elif top_left >= 1 and top_right >= 1 and bottom_left < 1 and bottom_right < 1:
                pygame.draw.polygon(screen, pixel_color, [(px, py + py_for_leftside_offset), (px + PX_SIZE, py + py_for_rightside_offset), (px + PX_SIZE, py), (px, py)])

                pygame.draw.line(border_surface, border_color, (px, py + py_for_leftside_offset), (px + PX_SIZE, py + py_for_rightside_offset), border_width)

            # Case 7: Top-left, top-right, and bottom-left are above the threshold
            elif top_left >= 1 and top_right >= 1 and bottom_left >= 1 and bottom_right < 1:
                pygame.draw.polygon(screen, pixel_color, [(px + PX_SIZE, py + py_for_rightside_offset), (px + px_for_bottomside_offset, py + PX_SIZE), (px, py + PX_SIZE), (px, py), (px + PX_SIZE, py)])

                pygame.draw.line(border_surface, border_color, (px + PX_SIZE, py + py_for_rightside_offset), (px + px_for_bottomside_offset, py + PX_SIZE), border_width)

            # Case 8: Only top-right is above the threshold \
            elif top_left < 1 and top_right >= 1 and bottom_left < 1 and bottom_right < 1:
                pygame.draw.polygon(screen, pixel_color, [(px + px_for_topside_offset, py), (px + PX_SIZE, py + py_for_rightside_offset), (px + PX_SIZE, py)])

                pygame.draw.line(border_surface, border_color, (px + px_for_topside_offset, py), (px + PX_SIZE, py + py_for_rightside_offset), border_width)

            # Case 9: Top-right and bottom-right are above the threshold
            elif top_left < 1 and top_right >= 1 and bottom_left < 1 and bottom_right >= 1:
                pygame.draw.polygon(screen, pixel_color, [(px + px_for_topside_offset, py), (px + px_for_bottomside_offset, py + PX_SIZE), (px + PX_SIZE, py + PX_SIZE), (px + PX_SIZE, py)])

                pygame.draw.line(border_surface, border_color, (px + px_for_topside_offset, py),(px + px_for_bottomside_offset, py + PX_SIZE), border_width)

            # Case 10: Top-right and bottom-left are above the threshold //
            elif top_left < 1 and top_right >= 1 and bottom_left >= 1 and bottom_right < 1:

                pygame.draw.polygon(screen, pixel_color, [(px + px_for_topside_offset, py), (px, py + py_for_leftside_offset), (px, py + PX_SIZE), (px + px_for_bottomside_offset, py + PX_SIZE), (px + PX_SIZE, py + py_for_rightside_offset), (px + PX_SIZE, py)])

                pygame.draw.line(border_surface, border_color, (px + px_for_topside_offset, py), (px, py + py_for_leftside_offset), border_width)

                pygame.draw.line(border_surface, border_color, (px + PX_SIZE, py + py_for_rightside_offset), (px + px_for_bottomside_offset, py + PX_SIZE), border_width)

            # Case 11: Top-right, bottom-left, and bottom-right are above the threshold
            elif top_left < 1 and top_right >= 1 and bottom_left >= 1 and bottom_right >= 1:
                pygame.draw.polygon(screen, pixel_color, [(px + px_for_topside_offset, py), (px, py + py_for_leftside_offset), (px, py + PX_SIZE), (px + PX_SIZE, py + PX_SIZE), (px + PX_SIZE, py)])

                pygame.draw.line(border_surface, border_color, (px + px_for_topside_offset, py), (px, py + py_for_leftside_offset), border_width)

            # Case 12: Only top-left and bottom-right are above the threshold //

            elif top_left >= 1 and top_right < 1 and bottom_left < 1 and bottom_right >= 1:
                pygame.draw.polygon(screen, pixel_color, [(px + px_for_topside_offset, py), (px + PX_SIZE, py + py_for_rightside_offset), (px + PX_SIZE, py + PX_SIZE), (px + px_for_bottomside_offset, py + PX_SIZE), (px, py + py_for_leftside_offset), (px, py)])

                pygame.draw.line(border_surface, border_color, (px + px_for_topside_offset, py), (px + PX_SIZE, py + py_for_rightside_offset), border_width)

                pygame.draw.line(border_surface, border_color, (px, py + py_for_leftside_offset), (px + px_for_bottomside_offset, py + PX_SIZE), border_width)

            # Case 13: Top-left, bottom-left, and bottom-right are above the threshold
            elif top_left >= 1 and top_right < 1 and bottom_left >= 1 and bottom_right >= 1:
                pygame.draw.polygon(screen, pixel_color, [(px + px_for_topside_offset, py), (px + PX_SIZE, py + py_for_rightside_offset), (px + PX_SIZE, py + PX_SIZE), (px, py + PX_SIZE), (px, py)])

                pygame.draw.line(border_surface, border_color, (px + px_for_topside_offset, py), (px + PX_SIZE, py + py_for_rightside_offset), border_width)


            # Case 14: Top-left bottom right and top right are above the threshold
            elif top_left >= 1 and top_right >= 1 and bottom_right >= 1 and bottom_left < 1:
                pygame.draw.polygon(screen, pixel_color, [ (px, py + py_for_leftside_offset), (px + px_for_bottomside_offset, py + PX_SIZE), (px + PX_SIZE, py + PX_SIZE), (px + PX_SIZE, py), (px, py)])

                pygame.draw.line(border_surface, border_color, (px, py + py_for_leftside_offset), (px + px_for_bottomside_offset, py + PX_SIZE), border_width)

            # Case 15: All corners are above the threshold (no contour)
            elif top_left >= 1 and top_right >= 1 and bottom_left >= 1 and bottom_right >= 1:
                pygame.draw.polygon(screen, pixel_color, [ (px, py), (px, py + PX_SIZE), (px + PX_SIZE, py + PX_SIZE), (px + PX_SIZE, py)])

    pygame.draw.rect(border_surface, [0, 0, 0], pygame.Rect(0, 0, 130, 40))
    pygame.draw.rect(border_surface, WHITE, pygame.Rect(5, 5, 120, 30), 2)
    txt = my_other_font.render("   Additive 💡" if additive else "Subtractive 🎨", False, (255, 255, 255))
    border_surface.blit(txt, (12, 8))

    # the entire top layer surface
    screen.blit(border_surface, (0, 0))
    pygame.display.flip()
    clock.tick(fps) 
    
pygame.quit()
