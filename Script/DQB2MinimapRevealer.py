import os
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import zlib
import struct
from datetime import datetime

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

def process(binary_file_path, islands):
    # Load the binary data from the file
    with open(binary_file_path, 'rb') as f:
        binary_data_raw = f.read()
    binary_data= zlib.decompress(binary_data_raw[0x2A444:])
    binary_data = bytearray(binary_data)
    # Load the tiles from the folder
    Pointer = Start
    c = 1
    for i in range(24):
        if i in islands:
            path_Check.config(text="Please wait...("+str(c)+"/"+str(len(islands))+")",fg = "orange")
            root.update()
            if valid[2]:
                for i in range(Pointer+1,Pointer+End,2):
                    binary_data[i] = binary_data[i] | 0x80
            else:
                if valid[4]:
                    for i in range(Pointer+1,Pointer+End,2):
                        binary_data[i] = binary_data[i] & 0x7F
            if valid[5] == 1:
                TileBytes = bytearray([0x01,0x80])
                for i in range(Pointer,Pointer+End,2):
                    TileBytes[0] = binary_data[i]
                    TileBytes[1] = binary_data[i+1] & 0x3F                 
                    Value = struct.unpack('<H', TileBytes)[0]
                    #Look at type
                    if Value % 11 not in (1,2,4,7):
                        Value = Value - (Value % 11) + 1 #Set to air
                        TileBytes = bytearray(struct.pack('<H', Value))
                        binary_data[i] = TileBytes[0]
                        binary_data[i+1] = (binary_data[i+1] & 0xC0) + TileBytes[1]
            else:
                if valid[5] == 2:
                    for i in range(Pointer,Pointer+End,2):
                        if binary_data[i] != 0x01 or binary_data[i+1] != 0x80:
                            binary_data[i] = 155
                            binary_data[i+1] = 0x80
            if valid[3] > -1: #Reloading of tiles
                counter = 0
                for i in range(Pointer+1024,Pointer+End-1024,2):
                    if binary_data[i] != 0x01 and binary_data[i] != 0x00:
                        counter += 1
                        if counter % 5 == valid[3]:
                            binary_data[i] = 159
                            binary_data[i+1] = 0x80
                
            c += 1
        Pointer = Pointer + End + 4
    binary_data_edit= zlib.compress(binary_data)
    with open(binary_file_path, 'wb') as fin:
        fin.write(binary_data_raw[:0x2A444])
        fin.write(binary_data_edit)
    path_Check.config(text="Edit complete.",fg = "light green")
    

############################################################################################################

############################################################################################################


Island_names = ((0,"Isle of\nAwakening\n\nからっぽ島","#0080A0"),(1,"Furrowfield\n\nモンゾーラ島","#009040"),
                (2,"Khrumbul-Dun\nオッカムル島","#C78000"),(20,"Upper level","#995A00"),(21,"Lower level","#733B00"),
                (3,"Moonbrooke\n\nムーンブルク島","#00B080"),(4,"Malhalla\n\n破壊天体シドー","#5000A0"),
                (8,"Skelkatraz\n\n監獄島","#6F6F6F"),(10,"Buildertopia 1\n\nかいたく島1","#C08080"),(11,"Buildertopia 2\n\nかいたく島2","#C09080"),
                (13,"Buildertopia 3\n\nかいたく島3","#C0A080"),(7,"Angler's Isle\n\nツリル島","#306080"),(12,"Battle Atoll   バトル島","#990000"))

valid = [False,"",False,-1,False,0] #Python.... [Valid, Folder_Path, Explore, Reset, Hide, Fix]
        
def Text_List_Lan():
    with open("Data//MenuText.txt", 'r',encoding='utf-8') as file:
        lines = file.readlines()
        Text_List = [line.strip() for line in lines]
    while len(Text_List) < 41:
        Text_List.append(str(len(Text_List)))
    return Text_List

Text_List = Text_List_Lan()
Name_dictionary = {0:Text_List[19],1:Text_List[20],2:Text_List[21]+"Surface",20:Text_List[21]+"Upper",21:Text_List[21]+"Lower",3:Text_List[22],
                   4:Text_List[23],7:Text_List[24],8:Text_List[25],10:Text_List[26],11:Text_List[27],12:Text_List[28],13:Text_List[29]}

def export_check():
    #Checks requirements and sends the info to the export func.
    if valid[0] == True:
        with open(valid[1], 'rb') as f:
            binary_data_raw = f.read()
        backup = str(datetime.now()).split(".")[0].replace(":","-")
        with open("Backup//"+backup+" CMNDAT.BIN", 'wb') as backf:
            backf.write(binary_data_raw)
        Islands = []
        c = 0
        for i in button_vars:
            if i.get() == 1:
                Islands.append(Island_names[c][0])
            c += 1
        path_Check.config(text=Text_List[1],fg = "orange") #Please wait...
        root.update()
        process(valid[1], Islands)
        
def checkfile(file_path):
    for i in range(13):
        if button_vars[i].get() == -1:
            button_vars[i].set(0)
    #Tries to see if the file is valid. Fails miserably.
    with open(file_path, 'rb') as f:
        binary_data_raw = f.read()
        binary_data = list(binary_data_raw)
    if list(binary_data[0:6]) == list([0x61,0x65,0x72,0x43,0x02,0x01]):
        path_Check.config(text=f"{Text_List[2]} (CMNDAT.bin)",fg = "light green") #Valid file! (CMNDAT.bin)
        valid[0] = True
    else:
        path_Check.config(text=Text_List[3],fg = "red") #Invalid file!
        valid[0] = False
    if valid[0]: ##WELCOME TO SPAGUETTI CODE LAND
        IslandsCheck = []
        with open(file_path, 'rb') as f:
            binary_data= zlib.decompress(binary_data_raw[0x2A444:])
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
        filetypes=[(".BIN", "*.*")]
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
        else:
            button_vars[index].set(0)

def select_command(upda):
    for var in button_vars:
        if var.get() != -1:
            var.set(upda)

def explore_command():
    if valid[2] == True:
        valid[2] = False
        explore_button.config(bg = "#303040")
    else:
        valid[2] = True
        valid[4] = False
        explore_button.config(bg = "#000070")
        hide_button.config(bg = "#303040")
        
def hide_command():
    if valid[4] == True:
        valid[4] = False
        hide_button.config(bg = "#303040")
    else:
        valid[4] = True
        valid[2] = False
        explore_button.config(bg = "#303040")
        hide_button.config(bg = "#000070")
        
def reset_command():
    valid[3] = valid[3] + 1
    reset_button.config(bg = "#000070")
    if valid[3] > 4:
        valid[3] = 0
    reset_button.config(text=f"{valid[3]}/4")
    
def Fix_button(button):
    if valid[5] == button:
        valid[5] = 0
        SoftFix_button.config(bg = "#303040")
        HardFix_button.config(bg = "#303040")
    else:
        valid[5] = button
        if button == 1:
            SoftFix_button.config(bg = "#000070")
            HardFix_button.config(bg = "#303040")
        else:
            SoftFix_button.config(bg = "#303040")
            HardFix_button.config(bg = "#000070")
def visible_command(button):
    #Visible click
    if valid[2] == button:
        valid[2] = 2
        visible_button.config(bg = "#303040")
        visibleFull_button.config(bg = "#303040")
    else:
        valid[2] = button
        if button == 1:
            visible_button.config(bg = "gold")
            visibleFull_button.config(bg = "#303040")
        else:
            visible_button.config(bg = "#303040")
            visibleFull_button.config(bg = "gold")

# Create the main window
root = tk.Tk()
root.title(Text_List[35])
root.configure(background="#303040")
root.iconbitmap('Data//icon2.ico')

#No comments get lost future me 
button_size = 100
button_vars = []
buttons = []

open_file_button = tk.Button(
    root,
    text=Text_List[8], #Open File
    command=open_file_dialog,
    bg = "#303040",
    fg = "#EEEEEE",
    activebackground="#666666"
)

open_file_button.pack(pady=20)

path_Label = tk.Label(root, width=100, bg = "Black", fg = "SystemButtonFace")
path_Label.pack(pady=0, padx=10)
path_Check = tk.Label(root, width=100, bg = "#303040")
path_Check.pack(pady=0, padx=10)

options_frame = tk.Frame(root)
options_frame.configure(background="#303040")
options_frame.pack(padx=0, pady=0)

select_button = tk.Button(
    options_frame,
    width = 13,
    text=Text_List[9], #Select All
    command=lambda i=True:select_command(i),
    bg = "#303040",
    fg = "#EEEEEE",
    activebackground="#666666"
)

select_button.pack(pady=0)
select_button.grid(row=0, column=0, padx=15, pady=0, sticky="nesw")

unselect_button = tk.Button(
    options_frame,
    width = 13,
    text=Text_List[10], #Unselect All
    command=lambda i=False:select_command(i),
    bg = "#303040",
    fg = "#EEEEEE",
    activebackground="#666666"
)

unselect_button.grid(row=1, column=0, padx=15, pady=0, sticky="nesw")

explore_button = tk.Button(
    options_frame,
    height = 3,
    width = 15,
    text= f"{Text_List[36]}\n{Text_List[37]}",#show
    command=explore_command,
    bg = "#303040",
    fg = "#EEEEEE",
    activebackground="#666666"
)

explore_button.grid(row=0,rowspan=2, column=1, padx=0, pady=0,sticky="nesw")

hide_button = tk.Button(
    options_frame,
    height = 3,
    width = 15,
    text= f"{Text_List[41]}\n{Text_List[37]}",#hide
    command=hide_command,
    bg = "#303040",
    fg = "#EEEEEE",
    activebackground="#666666"
)

hide_button.grid(row=0,rowspan=2, column=2, padx=0, pady=0,sticky="nesw")

SoftFix_button = tk.Button(
    options_frame,
    width = 35,
    text=f"{Text_List[42]} (Soft)",#soft fix
    command=lambda i=1:Fix_button(i),
    bg = "#303040",
    fg = "orange",
    activebackground="#666666"
)
HardFix_button = tk.Button(
    options_frame,
    width = 35,
    text=f"{Text_List[42]} (Brute force)",#soft fix
    command=lambda i=2:Fix_button(i),
    bg = "#303040",
    fg = "#FF3030",
    activebackground="#666666"
)

reset_button = tk.Button(
    options_frame,
    height = 3,
    width = 15,
    text=f"{Text_List[38]}\n{Text_List[39]}",#reset
    command=reset_command,
    bg = "#303040",
    fg = "#FF3030",
    activebackground="#666666"
)

debug = [False]
def on_key_press(event):
    if debug[0] == False:
        debug[0] = True
        path_Check.config(text=f"DEBUG MODE",fg = "red")
        root.title(Text_List[35]+" DEBUG")
    # Create a button if it's not already created
        SoftFix_button.grid(row=0, column=3, padx=25, pady=0,sticky="nesw")
        HardFix_button.grid(row=1, column=3, padx=25, pady=0,sticky="nesw")
        reset_button.grid(row=0,rowspan=2, column=4, padx=10, pady=0,sticky="nesw")
    else:
        debug[0] = False
        path_Check.config(text=f"Debug mode off",fg = "light green")
        SoftFix_button.grid_forget()
        HardFix_button.grid_forget()
        reset_button.grid_forget()
        root.title(Text_List[35])
        valid[3] = -1
        valid[5] = 0
    
root.bind('<d>', on_key_press)
button_frame = tk.Frame(root)
button_frame.configure(background="#303040")
button_frame.pack(padx=10, pady=10)

export_button = tk.Button(
    button_frame,
    width = 30,
    text=Text_List[40], #Export!
    command=export_check,
    bg = "#303040",
    fg = "#EEEEEE",
    activebackground="#666666"
)

export_button.grid(row=6,column=1,columnspan=3,padx=0, pady=20)

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
            command=lambda i=i: on_button_click(i),padx=0, pady=0,
            bg = "#303040",
            fg = "#EEEEEE",
            activebackground="#666666"
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
            command=lambda i=i: on_button_click(i),
            bg = "#303040",
            fg = "#EEEEEE",
            activebackground="#666666"
        )
        button.grid(row=(co//5)*3 , column=co%5, rowspan=3, padx=5, pady=5)
        co += 1
    buttons.append(button)

var = tk.IntVar()
button_vars.append(var)

battle_button = tk.Button(
    button_frame,
    width = button_size // 5,
    text=Island_names[12][1],
    command=lambda i=12: on_button_click(i),
    bg = "#303040",
    fg = "#EEEEEE",
    activebackground="#666666"
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
                button.config(bg='#303040')
            else:
                button.config(bg='#000000')

# "Attach the update_button_colors function to each IntVar" sure i believe u
for var in button_vars:
    var.trace_add("write", lambda *args: update_button_colors())

# Main loop
root.mainloop()
