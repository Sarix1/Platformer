import sdl2.ext
import sdl2.sdlimage
from time import sleep

g_resources    = sdl2.ext.Resources(__file__, ".")
g_width        = 320
g_height       = 200
g_tick         = 0
g_default_size = 32
g_tile_size    = 32
g_block_size   = 128
g_gravity      = 1         
g_bounce       = 0.50     
g_accelerate   = 0.50    
g_decelerate   = 0.20  
g_stop_vel     = 0.20    
g_max_move_vel = 10       
g_jump_vel     = 16

def get_map_pos(x, y):
  map_x = int(x // g_tile_size)
  map_y = int(y // g_tile_size)

  return (map_x, map_y)

def get_tile_at(map, x, y):
  try:
    tile = map[int(y // g_tile_size)][int(x // g_tile_size)]
    return tile
  except:
    return 0

class Map:
  grid = []

  def __init__(self, filename):
    if filename == None:
      rows = 7
      cols = 10

      for i in range(rows):
        col = []
        for j in range(cols):
          col.append(0)
        self.grid.append(col)

      for col in range(10):
        self.grid[6][col] = 1
      
      self.grid[5][0] = 1
      self.grid[5][1] = 1
      self.grid[3][5] = 1

  def draw(self, surface):
    color1 = sdl2.ext.Color(128, 128, 255) # blue bg
    color2 = sdl2.ext.Color(64, 255, 64) # green tile
    x = 0
    y = 0

    for row in self.grid:
      for col in row:
        if col == 1:
          sdl2.ext.fill(surface, color2, (x, y, g_tile_size, g_tile_size))
        else:
          sdl2.ext.fill(surface, color1, (x, y, g_tile_size, g_tile_size))

        x += g_tile_size
      x = 0
      y += g_tile_size

class Screen:
  def __init__(self, w, h):
    self.width    = w
    self.height   = h
    self.window   = sdl2.ext.Window("Plat!", size=(w, h), flags=sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
    self.surface  = self.window.get_surface()
    self.buffer_surface = (sdl2.SDL_CreateRGBSurface(0, w, h, 32, 0xff000000, 0x00ff0000, 0x0000ff00, 0x000000ff)).contents
    self.pixels   = sdl2.ext.PixelView(self.surface)
    self.window.show()

  def fill(self, r,g,b):
    sdl2.ext.fill(self.buffer_surface, sdl2.ext.Color(r,g,b), None)

  def refresh(self):
    sdl2.SDL_BlitScaled(self.buffer_surface, None, self.surface, None)
    self.window.refresh()

class Blockmap:
  grid = []

  def __init__(self, w, h):
    self.width = w
    self.height = h

    for row in range(h):
      self.grid.append([])
      for i in range(w):
        self.grid[row].append([])


  def draw(self, surface):
    x = 0
    y = 0

    for row in self.grid:
      for col in row:
        thing_count = len(col)
        color = sdl2.ext.Color(thing_count * 100, thing_count * 100, thing_count * 100)
        sdl2.ext.fill(surface, color, (x, y, g_block_size, g_block_size))

        x += g_block_size

      x = 0
      y += g_block_size

  def add_point(self, thing, x, y):      
    if thing not in self.grid[y][x]:
      self.grid[y][x].append(thing)

  def add_thing(self, thing):
    square_list = []
    square_list.append((int(thing.x - thing.width//2) // g_block_size, int(thing.y - thing.height//2) // g_block_size))
    square_list.append((int(thing.x + thing.width//2) // g_block_size, int(thing.y - thing.height//2) // g_block_size))
    square_list.append((int(thing.x - thing.width//2) // g_block_size, int(thing.y + thing.height//2) // g_block_size))
    square_list.append((int(thing.x + thing.width//2) // g_block_size, int(thing.y + thing.height//2) // g_block_size))

    for square in square_list:
      self.add_point(thing, square[0], square[1])

    return square_list

  def remove_thing(self, thing, square_list):
    for square in square_list:
      try:
        self.grid[square[1]][square[0]].remove(thing)
      except:
        continue

class Animation:
  def __init__(self, source_surface, w, h, frames):
    self.width   = w
    self.height  = h
    self.frames  = frames
    self.surface = source_surface

class Sprite:
  width       = g_default_size
  height      = g_default_size
  frame       = 0
  animation   = 0
  animations  = []

  def __init__(self, source_surface, w, h, anims):
    self.width  = w
    self.height = h

    if isinstance(source_surface, str):
      source_surface = sdl2.ext.load_image(g_resources.get_path(source_surface))

    if len(anims) == 0:
      new_anim = Animation(source_surface, 1)
      self.animations.append(new_anim)
    else:
      for anim in range(len(anims)):
        anim_surface = sdl2.ext.subsurface(source_surface, (0, anim*self.height, anims[anim]*self.width, self.height))
        new_anim = Animation(anim_surface, w, h, anims[anim])
        self.animations.append(new_anim)

  def draw(self, target_surface, x, y, w, h):
    if w == 0:
      w = self.width

    if h == 0:
      h = self.height

    if self.frame >= self.animations[self.animation].frames:
      self.frame = 0

    sdl2.SDL_BlitScaled(
      self.animations[self.animation].surface,
      sdl2.SDL_Rect(self.frame*self.width, 0, self.width, self.height),
      target_surface,
      sdl2.SDL_Rect(x, y, w, h)
    )

class Controller:
  left  = 0
  right = 0
  up    = 0
  down  = 0

class GameObject:
  vel_x = 0
  vel_y = 0
  square_list = []
  controller  = Controller()
  sprite_offset_x = 0
  sprite_offset_y = 0
    
  def __init__(self, x, y, w, h, sprite):
    self.x          = x
    self.y          = y
    self.width      = w
    self.height     = h
    self.direction  = 1
    
    self.bounce_x     = g_bounce
    self.bounce_y     = g_bounce          
    self.accelerate   = g_accelerate  
    self.decelerate   = g_decelerate   
    self.max_move_vel = g_max_move_vel   
    self.jump_vel     = g_jump_vel  
    self.floating     = 1
    
    self.sprite          = sprite
    self.sprite_offset_x = -self.sprite.width//2
    self.sprite_offset_y = -self.sprite.height//2
    
  def do_control(self):
    if self.controller.left and not self.controller.right:
      if self.vel_x > -self.max_move_vel:
        self.vel_x -= self.accelerate

    elif self.controller.right:
      if self.vel_x < self.max_move_vel:
        self.vel_x += self.accelerate

    else:
      if self.vel_x > 0:
        self.vel_x -= self.decelerate
      elif self.vel_x < 0:
        self.vel_x += self.decelerate

    if self.controller.up and not self.floating:
      self.vel_y = -self.jump_vel
    
  def do_physics(self):
    if self.floating:
      self.vel_y += g_gravity

    if abs(self.vel_x) < g_stop_vel:
      self.vel_x = 0
    
    self.x += self.vel_x
    self.y += self.vel_y

  def do_edge_collision(self, x, y, w, h):
    if self.x - self.width//2 < x:
      self.x -= self.x - self.width//2
      if self.vel_x < 0:
        self.do_bounce_x()
    elif self.x + self.width//2 > w-1:
      self.x -= self.x + self.width//2 - w
      if self.vel_x > 0:
        self.do_bounce_x()

    if self.y - self.height//2 < y:
      self.y -= self.y - self.height//2
      if self.vel_y < 0:
        self.do_bounce_y()
    elif self.y + self.height//2 > h-1:
      self.y -= self.y + self.height//2 - h
      if self.vel_y > 0:
        self.do_bounce_y()
      self.floating = 0
    else:
      self.floating = 1

  def do_map_collision(self, map):
    #(map_x, map_y) = get_map_pos(self.x, self.y)
    nw = get_tile_at(map, self.x - self.width//2, self.y - self.height//2)
    ne = get_tile_at(map, self.x + self.width//2, self.y - self.height//2)
    sw = get_tile_at(map, self.x - self.width//2, self.y + self.height//2)
    se = get_tile_at(map, self.x + self.width//2, self.y + self.height//2)

    print(nw, ne, sw, se)

    if nw or ne:
      self.y += g_tile_size - (self.y-self.height//2) % g_tile_size
      self.vel_y = 0
    elif sw or se:
      self.y -= (self.y+self.height//2) % g_tile_size
      self.vel_y = 0
      self.floating = 0
    else:
      self.floating = 1

    nw = get_tile_at(map, self.x - self.width//2, self.y - self.height//2)
    ne = get_tile_at(map, self.x + self.width//2, self.y - self.height//2)
    sw = get_tile_at(map, self.x - self.width//2, self.y + self.height//2-1)
    se = get_tile_at(map, self.x + self.width//2, self.y + self.height//2-1)

    if nw or sw:
      self.x += g_tile_size - (self.x-self.width//2) % g_tile_size
      self.vel_x = 0
    elif ne or se:
      self.x -= (self.x+self.width//2) % g_tile_size
      self.vel_x = 0

  def do_bounce_x(self):
    self.vel_x *= -self.bounce_x
      
  def do_bounce_y(self):   
    self.vel_y *= -self.bounce_y

  def update_blockmap(self, blockmap):
    blockmap.remove_thing(self, self.square_list)
    self.square_list = blockmap.add_thing(self)

  # animate should be moved elsewhere
  def animate(self):
    if self.vel_x > 0:
      self.direction = 1
    elif self.vel_x < 0:
      self.direction = 0

    if self.floating:
      self.sprite.animation = 6
    else:
      if abs(self.vel_x) > g_max_move_vel*0.90:
        self.sprite.animation = 5 - self.direction
      elif self.vel_x:
        self.sprite.animation = 3 - self.direction
      else:
        self.sprite.animation = 1 - self.direction

    if g_tick % 3 == 0:
      self.sprite.frame += 1
      
  def draw(self, target_surface):
    self.sprite.draw(target_surface, int(self.x)+self.sprite_offset_x, int(self.y)+self.sprite_offset_y, self.sprite.width, self.sprite.height)

def process_events(controller):
  events = sdl2.ext.get_events()

  for event in events:
    if event.type == sdl2.SDL_QUIT:
      return False
    elif event.type == sdl2.SDL_KEYDOWN:
      if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
        return False
  
  keyboard_state    = sdl2.SDL_GetKeyboardState(None)
  controller.left   = keyboard_state[sdl2.SDL_SCANCODE_LEFT]
  controller.right  = keyboard_state[sdl2.SDL_SCANCODE_RIGHT]
  controller.up     = keyboard_state[sdl2.SDL_SCANCODE_UP]
  controller.down   = keyboard_state[sdl2.SDL_SCANCODE_DOWN]

  return True

def CreateCharacter(sprite):


def run():

  global g_tick

  sprites = dict()
  sprites

  test_sprite     = Sprite("sonic.png", 48, 48, [1, 1, 8, 8, 4, 4, 4])
  test_collidable = GameObject(160, 100, 30, 40, test_sprite)
  test_collidable.sprite_offset_y -= 4
  test_collidable.bounce_y        = 0
  test_collidable.bounce_x        = 0.9

  running = True
  while running == True:
    running = process_events(test_collidable.controller)

    test_collidable.do_control()
    test_collidable.do_physics()
    test_collidable.do_map_collision(g_map.grid)
    #test_collidable.do_edge_collision(0, 0, g_screen.width, g_screen.height)
    test_collidable.update_blockmap(g_blockmap)

    g_screen.fill(100, 130, 255)
    #g_blockmap.draw(g_screen.buffer_surface)
    g_map.draw(g_screen.buffer_surface)
    test_collidable.animate()
    test_collidable.draw(g_screen.buffer_surface)
    g_screen.refresh()

    g_tick += 1
    sleep(1/60)

g_screen    = Screen(g_width, g_height)
g_blockmap  = Blockmap(g_screen.width//g_block_size+1, g_screen.height//g_block_size+1)
g_map       = Map(None)

run()