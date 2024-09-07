import os
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import zlib

#####################################
#TILES: 0x0000 in little endian.
# Most Significant Bit -> VISIBILITY
# 2nd Most Significant Bit -> MOUNTAIN (used)

#TILE ID -> (TILE-1) & 0x3FFF // 11

#TILE TYPE -> (TILE-1) & 0x3FFF modulo 11:

#+0 -> Normal tile
#+1 -> Trees
#+2 -> UNUSED Castle tile
#+3 -> Palm trees
#+4 -> NULL
#+5 -> NULL
#+6 -> Room
#+7 -> UNUSED Mountain 1
#+8 -> UNUSED Mountain 2
#+9 -> UNUSED Mountain 3
#+10 -> UNUSED Mountain 4

#Tile -1 is not valid and crashes the minimap. The game gets stuck in saving
#####################################


##Pointer
Start = 2401803
End = 256*256*2

map_path = 'Data//SheetRetro.png'
map_chunky_path = 'Data//SheetChunky.png'
image_width = 256

##Crop sizes for Heresy mask
HeresyDictionary = {0:[1152,1456,1728+1152,1456+1216],
                    1:[320,816,2816+320,2048+816],
                    2:[1024,1008,1920+1024,1664+1008],
                    20:[1024,1008,1920+1024,1664+1008],
                    21:[1024,1008,1920+1024,1664+1008],
                    3:[832,304,2304+832,3072+304],
                    4:[576,48,2112+576,2880+48],
                    8:[1344,560,1728+1344,1856+560],
                    7:[1088,1392,1088+704,1392+640],
                    12:[1728,1776,1728+576,1776+512]
                    }
##Tiles that can have mountains
MountainDic = {8:8,9:10,10:9,11:7,18:8}

def extract_tiles_from_map(tile_map_path, tile_size=(16, 16)):
    #Gets the tiles from the tile sheet
    tile_map = Image.open(tile_map_path)
    tile_map_width, tile_map_height = tile_map.size

    tiles = []
    for y in range(0, tile_map_height, tile_size[1]):
        for x in range(0, tile_map_width, tile_size[0]):
            tile = tile_map.crop((x, y, x + tile_size[0], y + tile_size[1]))
            if valid[4] == 16:
                tile = tile.resize((16,16),Image.NEAREST)
            tiles.append(tile)
    return tiles

def BuildertopiaProcess(binary_data):
    TopRow = 9999
    BottomRow = 0
    LeftCol = 9999
    RightCol = 0
    for index, byte in enumerate(binary_data):
        if index%2 == 0:
            #Calc the position and save the byte
            row = (index// 2) // image_width
            col = (index//2) % image_width
            tempByte = byte
        if index%2 == 1:
            tempByte = tempByte + ((byte&0x3F)*16*16) -1
            if tempByte != 0 and tempByte < 26*11:
                if row < TopRow:
                    TopRow = row
                if row > BottomRow:
                    BottomRow = row
                if col < LeftCol:
                    LeftCol = col
                if col > RightCol:
                    RightCol = col
    TopRow = (TopRow+1)//4
    LeftCol = (LeftCol//4)
    RightCol = (RightCol//4)+1
    BottomRow = ((BottomRow)//4)+1
    return[LeftCol*64,(TopRow*64)-16,RightCol*64,(BottomRow*64)-16]
                
def construct_image(binary_data, tiles, image_width, HD):
    #Makes the image
    if valid[4] == 1:
        tile_size = (1, 1)
    else:
        tile_size = (16, 16)

    num_tiles = 256*255

    # Calculate the number of rows based on the number of tiles and specified width
    num_rows = (num_tiles + image_width - 1) // image_width
    
    constructed_image = Image.new('RGBA', (image_width * tile_size[0], num_rows * tile_size[1]),(0,0,0,0))
    black_background = Image.new('RGBA', (image_width * tile_size[0], num_rows * tile_size[1]), (0, 0, 0, 255)) #Not optimal at ALL
    
    for index, byte in enumerate(binary_data):
        #tiles are stored in groups of 2 bytes
        if index%2 == 0:
            #Calc the position and save the byte
            row = (index// 2) // image_width
            col = (index//2) % image_width
            position = (col * tile_size[0], row * tile_size[1])
            tempByte = byte
        if index%2 == 1:
            #Get the second byte and do some optimizing magic
            tempByte = tempByte + ((byte&0x3F)*16*16) -1

            #Tile ID and Tile Type
            TileID = tempByte // 11
            TileType = tempByte % 11
            
            #Paste the tile
            try:
                tile = tiles[TileID]
            except: #If tile error, this only happens when hacking.
                tile = tiles[992]
            constructed_image.paste(tile, position)
            
            #Here depending on the "Tile Type" it fetches the appropiate overlay. Tile types explained at the beggining.
            if TileID != -1:
                tile = tiles[993+TileType]
                constructed_image.paste(tile, position, tile)
            
            #Hard-coded mountain
            if byte & 0x40 == 0x40 and TileType == 0:
                if TileID in MountainDic.keys():
                    tile = tiles[MountainDic[TileID]+993]
                    constructed_image.paste(tile, position, tile)
                else: #This is still not understood. What are ya doing game? Asking some other function perhaps?
                    pass
                    #tile = tiles[0] #What the game seems to default to, I copy
            #Visibility check
            if valid[2] < 2 and byte & 0x80 == 0:
                tile = tiles[992]
                if valid[2] == 1:
                    constructed_image.paste(tile, position, tile)
                else:
                    constructed_image.paste(tile, position)
    #Set alpha to opaque and black
    if valid[2] < 2:
        constructed_image = Image.alpha_composite(black_background, constructed_image)
        constructed_image.convert('RGB')
    #Crop and resize
    if valid[3] == True:
        if valid[4] == 1:
            constructed_image = constructed_image.resize((constructed_image.size[0]*16, constructed_image.size[1]*16), Image.NEAREST)
        try:
            constructed_image = constructed_image.crop((HeresyDictionary[HD]))
        except:
            constructed_image = constructed_image.crop((BuildertopiaProcess(binary_data)))
        if valid[4]:
            constructed_image = constructed_image.resize((constructed_image.size[0]//2, constructed_image.size[1]//2), Image.NEAREST)
        else:    
            constructed_image = constructed_image.resize((constructed_image.size[0]//2, constructed_image.size[1]//2), Image.LANCZOS)
    return constructed_image

def process(binary_file_path,image_width, islands,folder_path):
    # Load the binary data from the file
    with open(binary_file_path, 'rb') as f:
        binary_data = f.read()
    if valid[5]:
        binary_data= zlib.decompress(binary_data[0x2A444:])
    binary_data = list(binary_data)
    # Load the tiles from the folder
    if not valid[4]:
        tiles = extract_tiles_from_map(map_path)
    else:
        tiles = extract_tiles_from_map(map_chunky_path,(1, 1))
    Pointer = Start
    c = 1
    for i in range(24):
        if i in islands:
            path_Check.config(text="Please wait...("+str(c)+"/"+str(len(islands))+")",fg = "orange")
            root.update()
            constructed_image = construct_image(binary_data[Pointer+(256*2):Pointer+End], tiles, image_width, i)
            constructed_image.save(folder_path+"//"+Name_dictionary[i]+".png", 'PNG')
            c += 1
        Pointer = Pointer + End + 4
    path_Check.config(text="Export complete!",fg = "green")
    

############################################################################################################

############################################################################################################


Island_names = ((0,"Isle of\nAwakening\n\nからっぽ島","aqua"),(1,"Furrowfield\n\nモンゾーラ島","medium sea green"),
                (2,"Khrumbul-Dun\nオッカムル島","orange"),(20,"Upper level","#C47400"),(21,"Lower level","#944D00"),
                (3,"Moonbrooke\n\nムーンブルク島","#00FFC0"),(4,"Malhalla\n\n破壊天体シドー","#BBBBFF"),
                (8,"Skelkatraz\n\n監獄島","grey"),(10,"Buildertopia 1\n\nかいたく島1","#FFDDDD"),(11,"Buildertopia 2\n\nかいたく島2","#FFE6DD"),
                (13,"Buildertopia 3\n\nかいたく島3","#FFEEDD"),(7,"Angler's Isle\n\nツリル島","#DDF0FF"),(12,"Battle Atoll   バトル島","#FF9999"))

valid = [False,"",2,False,0,False] #Python.... [Valid, Folder_Path, Visible, Hermit_Mask, chunky_configuration, cmndat]
        
def Text_List_Lan():
    with open("Data//MenuText.txt", 'r',encoding='utf-8') as file:
        lines = file.readlines()
        Text_List = [line.strip() for line in lines]
    while len(Text_List) < 35:
        Text_List.append(str(len(Text_List)))
    return Text_List

Text_List = Text_List_Lan()
Name_dictionary = {0:Text_List[19],1:Text_List[20],2:Text_List[21]+"Surface",20:Text_List[21]+"Upper",21:Text_List[21]+"Lower",3:Text_List[22],
                   4:Text_List[23],7:Text_List[24],8:Text_List[25],10:Text_List[26],11:Text_List[27],12:Text_List[28],13:Text_List[29]}

def export_check():
    #Checks requirements and sends the info to the export func.
    if valid[0] == True:
        folder_path = filedialog.askdirectory(
            title= Text_List[0]#Select a Folder
        )
        if folder_path:
            Islands = []
            c = 0
            for i in button_vars:
                if i.get() == 1:
                    Islands.append(Island_names[c][0])
                c += 1
            path_Check.config(text=Text_List[1],fg = "orange") #Please wait...
            root.update()
            process(valid[1], image_width, Islands, folder_path)
        
def checkfile(file_path):
    for i in range(13):
        if button_vars[i].get() == -1:
            button_vars[i].set(0)
    #Tries to see if the file is valid. Fails miserably.
    with open(file_path, 'rb') as f:
        binary_data = list(f.read())
    if list(binary_data[0:8]) == list([252, 255, 190, 62, 180, 255, 127, 192]):
        path_Check.config(text=Text_List[2],fg = "green") #Valid file!
        valid[0] = True
        valid[5] = False
    else:
        if len(binary_data) == 0x55DD3A:
            path_Check.config(text=f"{Text_List[2]} (Debug save failsafe)",fg = "lime") #Valid file! (Debug save failsafe)
            valid[0] = True
            valid[5] = False
        else:
            if list(binary_data[0:6]) == list([0x61,0x65,0x72,0x43,0x02,0x01]):
                path_Check.config(text=f"{Text_List[2]} (CMNDAT.bin)",fg = "green") #Valid file! (CMNDAT.bin)
                valid[5] = True
                valid[0] = True
            else:
                valid[5] = False
                path_Check.config(text=Text_List[3],fg = "red") #Invalid file!
                valid[0] = False
    if valid[0]: ##WELCOME TO SPAGUETTI CODE LAND
        IslandsCheck = []
        if valid[5]:
            with open(file_path, 'rb') as f:
                binary_data = f.read()
                binary_data= zlib.decompress(binary_data[0x2A444:])
                binary_data = list(binary_data)
        c = 0
        for i in button_vars:
            IslandsCheck.append(Island_names[c][0])
            c += 1
        c = 0
        CheckPointer = Start
        for i in range(24):
            if i in IslandsCheck:
                if binary_data[CheckPointer] == 0:
                    button_vars[IslandsCheck.index(i)].set(-1)
            CheckPointer = CheckPointer + End + 4
        
            
def open_file_dialog():
    # Open a file dialog and allow the user to select a file
    file_path = filedialog.askopenfilename(
        title=Text_List[4], #Select binary file (Turtle-Insect's exported CMN.DAT)
        filetypes=[("All Files", "*.*")]
    )
    if file_path:
        path_Label.config(text=f"{Text_List[5]}:{file_path}") #Selected file:
        checkfile(file_path)
        valid[1] = file_path
    else:
        path_Label.config(text=Text_List[6]) #No file selected


def on_button_click(index):
    #Island click
    if button_vars[index].get() != -1:
        if button_vars[index].get() == 0:
            button_vars[index].set(1)
            if (index == 8 or index == 9 or index == 10) and valid[3] == True:
                BuildertopiaLabel.config(fg = "red") #BUILDERTOPIA ERROR
        else:
            button_vars[index].set(0)
            if button_vars[8].get()== 0 and button_vars[9].get()== 0 and button_vars[10].get() == 0:
                BuildertopiaLabel.config(fg = "SystemButtonFace") #BUILDERTOPIA ERROR

def select_command(upda):
    for var in button_vars:
        if var.get() != -1:
            var.set(upda)

def visible_command(button):
    #Visible click
    if valid[2] == button:
        valid[2] = 2
        visible_button.config(bg = "SystemButtonFace")
        visibleFull_button.config(bg = "SystemButtonFace")
    else:
        valid[2] = button
        if button == 1:
            visible_button.config(bg = "gold")
            visibleFull_button.config(bg = "SystemButtonFace")
        else:
            visible_button.config(bg = "SystemButtonFace")
            visibleFull_button.config(bg = "gold")
        
def heresy_command():
    #Hermit click (yes I know its not optimal but I have better things to do it works so its FINE)
    if valid[3]:
        valid[3] = False
        heresy_button.config(bg = "SystemButtonFace")
        BuildertopiaLabel.config(fg = "SystemButtonFace") #BUILDERTOPIA ERROR
    else:
        valid[3] = True
        heresy_button.config(bg = "gold")
        if button_vars[10].get() == 1 or button_vars[8].get() == 1 or button_vars[9].get() == 1:
            BuildertopiaLabel.config(fg = "red") #BUILDERTOPIA ERROR

def chunky_command(button):
    if button == valid[4]:
        valid[4] = 0
        chunky_button_1x.config(bg = "SystemButtonFace")
        chunky_button_16x.config(bg = "SystemButtonFace")
    else:
        if button == 16:
            valid[4] = 16
            chunky_button_1x.config(bg = "SystemButtonFace")
            chunky_button_16x.config(bg = "gold")
        else:
            valid[4] = 1
            chunky_button_1x.config(bg = "gold")
            chunky_button_16x.config(bg = "SystemButtonFace")

# Create the main window
root = tk.Tk()
root.title(Text_List[7]+ " v0.2.2")
root.iconbitmap('Data//icon.ico')

#No comments get lost future me 
button_size = 100
button_vars = []
buttons = []

open_file_button = tk.Button(
    root,
    text=Text_List[8], #Open File
    command=open_file_dialog
)

open_file_button.pack(pady=20)

path_Label = tk.Label(root, width=100, bg = "white")
path_Label.pack(pady=0, padx=10)
path_Check = tk.Label(root, width=100)
path_Check.pack(pady=0, padx=10)

options_frame = tk.Frame(root)
options_frame.pack(padx=0, pady=0)

select_button = tk.Button(
    options_frame,
    width = 13,
    text=Text_List[9], #Select All
    command=lambda i=True:select_command(i)
)

select_button.pack(pady=0)
select_button.grid(row=0, column=0, padx=10, pady=0, sticky="nesw")

unselect_button = tk.Button(
    options_frame,
    width = 13,
    text=Text_List[10], #Unselect All
    command=lambda i=False:select_command(i)
)

unselect_button.grid(row=1, column=0, padx=10, pady=0, sticky="nesw")

Visible_Label = tk.Label(options_frame,text=f"{Text_List[11]} {Text_List[12]}", borderwidth=2, relief="groove")
Visible_Label.grid(row=0, column=1, columnspan=2,sticky="nesw", padx=0)

visible_button = tk.Button(
    options_frame,
    width = 10,
    text= f"{Text_List[30]}",#Partial
    command=lambda i=1:visible_command(i)
)

visible_button.grid(row=1, column=1, padx=0, pady=0,sticky="nesw")

visibleFull_button = tk.Button(
    options_frame,
    width = 10,
    text=f"{Text_List[31]}",#Full
    command=lambda i=0:visible_command(i)
)

visibleFull_button.grid(row=1, column=2, padx=0, pady=0,sticky="nesw")

heresy_button = tk.Button(
    options_frame,
    height = 3,
    text=f"{Text_List[13]}\n{Text_List[14]}", #Hermit's Heresy\nmask
    command=heresy_command
)

heresy_button.grid(row=0, column=3,rowspan=2, padx=10, pady=0,sticky="ns")

chunky_button_1x = tk.Button(
    options_frame,
    width = 13,
    text=Text_List[15], #Chunky Tiles 1x
    command=lambda i=1:chunky_command(i),
    pady=0
)

chunky_button_1x.grid(row=0, column=4, padx=0, pady=0,sticky="nesw")

chunky_button_16x = tk.Button(
    options_frame,
    width = 13,
    text=Text_List[16], #Chunky Tiles 16x
    command=lambda i=16:chunky_command(i),
    pady=0
)

chunky_button_16x.grid(row=1, column=4, padx=0, pady=0,sticky="nesw")

button_frame = tk.Frame(root)
button_frame.pack(padx=10, pady=10)

export_button = tk.Button(
    button_frame,
    width = 30,
    text=Text_List[17], #Export!
    command=export_check
)

export_button.grid(row=6,column=1,columnspan=3,padx=0, pady=20)

BuildertopiaLabel = tk.Label(button_frame,text=f"{Text_List[32]}\n{Text_List[33]}\n{Text_List[34]}", fg = "SystemButtonFace")
BuildertopiaLabel.grid(row=6, column=0,sticky="nesw", padx=0)

# Island buttons
co = 0
for i in range(12):
    var = tk.IntVar()
    button_vars.append(var)
    if i in (2,3,4):
        button = tk.Button(
            button_frame,
            text=Island_names[i][1],
            width=button_size // 5,
            command=lambda i=i: on_button_click(i),padx=0, pady=0
            
        )
        button.grid(row=i-2, column=co%5, padx=0, pady=0)
        if i == 4:
            co += 1
    else:
        button = tk.Button(
            button_frame,
            text=Island_names[i][1],
            width=button_size // 5,
            height=button_size // 20,
            command=lambda i=i: on_button_click(i)
        )
        button.grid(row=(co//5)*3 , column=co%5, rowspan=3, padx=5, pady=5)
        co += 1
    buttons.append(button)

var = tk.IntVar()
button_vars.append(var)

battle_button = tk.Button(
    button_frame,
    width = button_size // 5,
    text=Island_names[12][1], #Export!
    command=lambda i=12: on_button_click(i)
)

battle_button.grid(row=6,column=4,padx=0, pady=20)
buttons.append(battle_button)

# Color buttons
def update_button_colors():
    for i, button in enumerate(buttons):
        if button_vars[i].get() == 1:
            button.config(bg=Island_names[i][2])
        else:
            if button_vars[i].get() == 0:
                button.config(bg='SystemButtonFace')
            else:
                button.config(bg='#999999')

# "Attach the update_button_colors function to each IntVar" sure i believe u
for var in button_vars:
    var.trace_add("write", lambda *args: update_button_colors())

# Main loop
root.mainloop()
