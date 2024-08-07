import os
from PIL import Image
import tkinter as tk
from tkinter import filedialog

##Pointer
Start = 2401803
End = 256*256*2

mountain_folder_path = 'Mountain'
map_path = 'SheetCompilation.png'
image_width = 256

##Crop sizes for Heresy mask
HeresyDictionary = {0:[1152,1456,1728+1152,1456+1216]}
##Tiles that can have mountains
MountainList = (0x59,0xC7,0x6F,0x64,0x7A)


def extract_tiles_from_map(tile_map_path, tile_size=(16, 16)):
    #Gets the tiles from the tile sheet
    tile_map = Image.open(tile_map_path)
    tile_map_width, tile_map_height = tile_map.size

    tiles = []
    for y in range(0, tile_map_height, tile_size[1]):
        for x in range(0, tile_map_width, tile_size[0]):
            tile = tile_map.crop((x, y, x + tile_size[0], y + tile_size[1]))
            tiles.append(tile)
    return tiles

def load_tiles(folder_path,col,rang):
    #Gets the mountain tiles. Don't ask why it is so bad hush.
    tiles = []
    for i in range(rang):
        tile_path = os.path.join(folder_path, f"0x{i:03X}.png")
        if os.path.exists(tile_path):
            tile = Image.open(tile_path).convert('RGBA')
            tiles.append(tile)
        else:
            tiles.append(Image.new('RGBA', (16, 16), color=col))
    return tiles

def construct_image(binary_data, tiles,mountain, image_width, HD):
    #Makes the image
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
            mask = byte & 0x0F
            tile = tiles[mask*(16*16)+tempByte]
            constructed_image.paste(tile, position)
            #Mountain check
            if byte & 0x40 == 0x40 and mask*(16*16)+tempByte in MountainList:
                tile = mountain[tempByte]
                constructed_image.paste(tile, position)
            #Visibility check
            if valid[2] == False and byte & 0x80 == 0:
                tile = mountain[0]
                constructed_image.paste(tile, position, tile)
    #Set alpha to opaque and black
    if valid[2] == False:
        constructed_image = Image.alpha_composite(black_background, constructed_image)
        constructed_image.convert('RGB')
    #Crop and resize
    if valid[3] == True:
        try:
            constructed_image = constructed_image.crop((HeresyDictionary[HD]))
        except:
            print(f"Hermit's Heresy not supported yet! {HD}")
        constructed_image = constructed_image.resize((constructed_image.size[0]//2, constructed_image.size[1]//2), Image.LANCZOS)
    return constructed_image


def process(binary_file_path, tile_folder_path,mountain_folder_path,image_width, islands,folder_path):
    # Load the binary data from the file
    with open(binary_file_path, 'rb') as f:
        binary_data = list(f.read())

    # Load the tiles from the folder
    tiles = extract_tiles_from_map(map_path)
    mountain = load_tiles(mountain_folder_path,'red',256)
    
    Pointer = Start
    c = 1
    for i in range(15):
        if i in islands:
            path_Check.config(text="Please wait...("+str(c)+"/"+str(len(islands))+")",fg = "orange")
            root.update()
            constructed_image = construct_image(binary_data[Pointer+(256*2):Pointer+End], tiles,mountain, image_width, i)
            constructed_image.save(folder_path+"//Minimap"+str(i+1).zfill(2)+".png", 'PNG')
            c += 1
        Pointer = Pointer + End
    path_Check.config(text="Export complete!",fg = "green")
    

############################################################################################################

############################################################################################################


Island_names = ((-1,"Select\nAll","gold"),(0,"Isle of\nAwakening\n\nからっぽ島","aqua"),(1,"Furrowfield\n\nモンゾーラ島","medium sea green"),
                (2,"Khrumbul-Dun\n\nオッカムル島","orange"),(3,"Moonbrooke\n\nムーンブルク島","#00FFC0"),(4,"Malhalla\n\n破壊天体シドー","#BBBBFF"),
                (8,"Skelkatraz\n\n監獄島","grey"),(10,"Buildertopia 1\n\nかいたく島1","#FFDDDD"),(11,"Buildertopia 2\n\nかいたく島2","#FFE6DD"),
                (13,"Buildertopia 3\n\nかいたく島3","#FFEEDD"))

valid = [False,"",True,False] #Python.... [Valid, Folder_Path, Visible, Hermit_Mask]


def export_check():
    #Checks requirements and sends the info to the export func.
    if valid[0] == True:
        folder_path = filedialog.askdirectory(
            title="Select a Folder"
        )
        if folder_path:
            Islands = []
            c = 1
            for i in button_vars[1:]:
                if i.get() == 1:
                    Islands.append(Island_names[c][0])
                c += 1
            path_Check.config(text="Please wait...",fg = "orange")
            root.update()
            process(valid[1], tile_folder_path, mountain_folder_path, image_width, Islands,folder_path)
        
def checkfile(file_path):
    #Tries to see if the file is valid. Fails miserably.
    with open(file_path, 'rb') as f:
        binary_data = list(f.read())
    if list(binary_data[0:8]) == list([252, 255, 190, 62, 180, 255, 127, 192]):
        path_Check.config(text="Valid file!",fg = "green")
        valid[0] = True
    else:
        if len(binary_data) == 0x55DD3A:
            path_Check.config(text="Valid file! (Steam save)",fg = "lime")
            valid[0] = True
        else:
            path_Check.config(text="Invalid file!",fg = "red")
            valid[0] = False
            
def open_file_dialog():
    # Open a file dialog and allow the user to select a file
    file_path = filedialog.askopenfilename(
        title="Select binary file (Turtle-Insect's exported CMN.DAT)",
        filetypes=[("All Files", "*.*")]
    )
    if file_path:
        path_Label.config(text=f"Selected file: {file_path}")
        checkfile(file_path)
        valid[1] = file_path
    else:
        path_Label.config(text="No file selected")


def on_button_click(index):
    #Island click
    if button_vars[index].get() == 0:
        button_vars[index].set(1)
    else:
        button_vars[index].set(0)
    if index == 0:
        if button_vars[0].get() == 1:
            upda = 1
        else:
            upda = 0
        for var in button_vars:
            var.set(upda)

def visible_command():
    #Visible click
    if valid[2] == False:
        valid[2] = True
        visible_button.config(bg = "SystemButtonFace")
    else:
        valid[2] = False
        visible_button.config(bg = "gold")
        
def heresy_command():
    #Hermit click (yes I know its not optimal but I have better things to do it works so its FINE)
    if valid[3]:
        valid[3] = False
        heresy_button.config(bg = "SystemButtonFace")
    else:
        valid[3] = True
        heresy_button.config(bg = "gold")


# Create the main window
root = tk.Tk()
root.title("Minimap Exporter")
root.iconbitmap('icon.ico')

#No comments get lost future me 
button_size = 100
button_vars = []
buttons = []

open_file_button = tk.Button(
    root,
    text="Open File",
    command=open_file_dialog
)

open_file_button.pack(pady=20)

path_Label = tk.Label(root, width=100, bg = "white")
path_Label.pack(pady=0, padx=10)
path_Check = tk.Label(root, width=100)
path_Check.pack(pady=0, padx=10)

options_frame = tk.Frame(root)
options_frame.pack(padx=0, pady=0)

visible_button = tk.Button(
    options_frame,
    text="Hide unexplored tiles",
    command=visible_command
)

visible_button.pack(pady=0)
visible_button.grid(row=0, column=0, padx=5, pady=5)

heresy_button = tk.Button(
    options_frame,
    text="Hermit's Heresy mask",
    command=heresy_command
)

heresy_button.grid(row=0, column=1, padx=5, pady=5)

button_frame = tk.Frame(root)
button_frame.pack(padx=10, pady=10)

export_button = tk.Button(
    root,
    text="Export!",
    command=export_check
)

export_button.pack(pady=20)

# Island buttons
for i in range(10):
    var = tk.IntVar()
    button_vars.append(var)
    
    button = tk.Button(
        button_frame,
        text=Island_names[i][1],
        width=button_size // 5,
        height=button_size // 20,
        command=lambda i=i: on_button_click(i)
    )
    button.grid(row=i//5, column=i%5, padx=5, pady=5)
    buttons.append(button)

# Color buttons
def update_button_colors():
    for i, button in enumerate(buttons):
        if button_vars[i].get() == 1:
            button.config(bg=Island_names[i][2])
        else:
            button.config(bg='SystemButtonFace')

# "Attach the update_button_colors function to each IntVar" sure i believe u
for var in button_vars:
    var.trace_add("write", lambda *args: update_button_colors())

# Main loop
root.mainloop()
