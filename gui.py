# Thư viện cho GUI
import tkinter as tk
from tkinter import ttk

# Thư viện tính thời gian
from datetime import datetime, timedelta

# Tính bù 2 của byte
def twos_comp(val, bits):
    if (val & (1 << (bits - 1))) != 0: # Nếu bit dấu là 1...
        val = val - (1 << bits)        # Tính giá trị âm
    return val                         # Trả về giá trị

# Lấy thuộc tính của file FAT32
def getAttributes(attributes):
    temp = ""
    for i in range(len(attributes)):
        if (attributes[i] == "0"):
            temp += "Read-Only"
        elif (attributes[i] == "1"):
            temp += "Hidden"
        elif (attributes[i] == "2"):
            temp += "System"
        elif (attributes[i] == "3"):
            temp += "Volume label"
        elif (attributes[i] == "4"):
            temp += "Directory"
        elif (attributes[i] == "5"):
            temp += "Archive"

        if (i < len(attributes) - 2 and attributes[i] >= '0' and attributes[i] <= '9'):
            temp += ", "
    return temp

# Class chứa thông tin của file FAT32
class FileFAT32:
    name = ""
    extension = "."
    attributes = ""
    
    created_time = ""
    created_date = ""

    location = 0
    beginning_cluster = 0
    size = 0
    father = -1
    #Check directory
    sentinal = False
    #Constructor
    def __init__(self, name):
        self.name = name

# Mảng chứa tất cả file FAT32
filesFAT32 = []

# Class chứa thông tin của file NTFS
class FileNTFS:
    def __init__(self, ID, ID_parent, name, attributes, date_created, time_created, size):
        self.ID = ID
        self.ID_parent = ID_parent
        self.name = name
        self.attributes = attributes
        self.date_created = date_created
        self.time_created = time_created
        self.size = size

# Mảng chứa tất cả file NTFS
filesNTFS = []

# Tạo cửa sổ
window = tk.Tk()
window.title('Partition Manager')
window.geometry('500x500')
window.iconbitmap('icon.ico')

# Tạo cây
tree = ttk.Treeview(window, height=20)
tree.pack()
tree.place(x=0, y=60)

# Tạo label chú thích thông tin
name_label = tk.Label(window, text='Name:')
name_label.place(x=220, y=60)

attribute_label = tk.Label(window, text='Attribute:')
attribute_label.place(x=220, y=90)

date_label = tk.Label(window, text='Date Created:')
date_label.place(x=220, y=120)

time_label = tk.Label(window, text='Time Created:')
time_label.place(x=220, y=150)

size_label = tk.Label(window, text='Size:')
size_label.place(x=220, y=180)

path_label = tk.Label(window, text='Path to file:')
path_label.place(x=220, y=210)

# Tạo label hiện thông tin
name_entry = tk.Label(window)
name_entry.place(x=300, y=60)

attribute_entry = tk.Label(window)
attribute_entry.place(x=300, y=90)

date_entry = tk.Label(window)
date_entry.place(x=300, y=120)

time_entry = tk.Label(window)
time_entry.place(x=300, y=150)

size_entry = tk.Label(window)
size_entry.place(x=300, y=180)

path_entry = tk.Label(window)
path_entry.place(x=300, y=210)

# Tạo phần nhập partition
partition_input_text = tk.Label(window, text='Enter a partition letter:')
partition_input_text.place(x=0, y=5)

partition_input = tk.Entry(window, width=5)
partition_input.place(x=125, y=5)

partition_type_text = tk.Label(window, text='Partition format:')
partition_type_text.place(x=0, y=30)

partition_type_entry = tk.Label(window)
partition_type_entry.place(x=90, y=30)

# Chèn thông tin file vào cây của GUI
def insert_tree(partition):
    # Empty cây
    tree.delete(*tree.get_children())

    # Chèn NTFS
    if partition == 'NTFS':
        for file in filesNTFS:
            if any(obj.ID == file.ID_parent for obj in filesNTFS):
                tree.insert(file.ID_parent, 'end', file.ID, text=file.name)
            else:
                tree.insert('', 'end', file.ID, text=file.name)

    # Chèn FAT32
    elif partition == 'FAT32':
        for fileID in range(1, len(filesFAT32)):
            file = filesFAT32[fileID]
            if any(ID_child == file.father for ID_child in range(len(filesFAT32))):
                tree.insert(file.father, 'end', fileID, text=file.name)
            else:
                tree.insert('', 'end', fileID, text=file.name)

partition_letter = ''

# Mở partition
def open_partition():
    global filesFAT32
    filesFAT32.clear()
    global filesNTFS
    filesNTFS.clear()
    global partition_letter
    partition_letter = partition_input.get()
    try:
        with open("\\\\.\\" + partition_letter + ":", "rb") as fp:
            # Đọc format
            fp.read(3)
            type = fp.read(5).decode("ascii")
            # Kiểu NTFS
            if type == "NTFS ":
                fp.seek(0x0B, 0)
                bytesPerSector = int.from_bytes(fp.read(2), 'little')
                fp.seek(0x0D, 0)
                sectorsPerCluster = int.from_bytes(fp.read(1), 'little')
                fp.seek(0x18, 0)
                sectorsPerTrack = int.from_bytes(fp.read(2), 'little')
                fp.seek(0x1A, 0)
                heads = int.from_bytes(fp.read(2), 'little')
                fp.seek(0x28, 0)
                sectorsInDisk = int.from_bytes(fp.read(8), 'little')
                fp.seek(0x30, 0)
                MFTstartCluster = int.from_bytes(fp.read(8), 'little')
                fp.seek(0x38, 0)
                MFTBstartCluster = int.from_bytes(fp.read(8), 'little')
                fp.seek(0x40, 0)
                bytesPerMFTEntryNC = int.from_bytes(fp.read(1), 'little')
                bytesPerMFTEntry = 2 ** abs(twos_comp(bytesPerMFTEntryNC, len(bin(bytesPerMFTEntryNC)[2:])))

                # In thông tin đĩa ra terminal
                print('Bytes per Sector: ' + str(bytesPerSector))
                print('Sectors per Cluster: ' + str(sectorsPerCluster))
                print('Sectors per Track: ' + str(sectorsPerTrack))
                print('Heads: ' + str(heads))
                print('Sectors in Disk: ' + str(sectorsInDisk))
                print('First MFT Cluster: ' + str(MFTstartCluster))
                print('First MFT Backup Cluster: ' + str(MFTBstartCluster))
                print('Bytes per MFT Entry: ' + str(bytesPerMFTEntry))
                print()

                MFTstartByte = MFTstartCluster * sectorsPerCluster * bytesPerSector
                startMFTEntry = MFTstartByte

                fp.seek(startMFTEntry, 0)
                fp.read(1)
                fp.seek(-1, 1)

                i = 0
                while True:
                    fp.seek(0x14, 1)
                    offsetFirstAttribute = int.from_bytes(fp.read(2), 'little')
                    fp.seek(-2 - 0x14, 1)

                    fp.seek(0x18, 1)
                    sizeMFTEntryUsed = int.from_bytes(fp.read(4), 'little')
                    fp.seek(-4 - 0x18, 1)

                    fp.seek(0x2C, 1)
                    fileID = int.from_bytes(fp.read(4), 'little')
                    fp.seek(-4 - 0x2C, 1)

                    fileName = ''
                    fileIDParent = ''
                    fileAttributes = []
                    fileDateCreated = ''
                    fileTimeCreated = ''
                    fileSize = 0

                    fp.seek(offsetFirstAttribute, 1)

                    if sizeMFTEntryUsed > 0:
                        totalAttributes = offsetFirstAttribute
                        while True:
                            typeAttribute = hex(int.from_bytes(fp.read(4), 'little'))
                            fp.seek(-4, 1)

                            if typeAttribute == "0xffffffff":
                                fp.seek(-totalAttributes, 1)
                                break

                            fp.seek(0x04, 1)
                            sizeAttribute = int.from_bytes(fp.read(4), 'little')
                            fp.seek(-4 - 0x04, 1)

                            fp.seek(0x10, 1)
                            sizeContent = int.from_bytes(fp.read(4), 'little')
                            fp.seek(-4 - 0x10, 1)

                            fp.seek(0x14, 1)
                            offsetContent = int.from_bytes(fp.read(2), 'little')
                            fp.seek(-2 - 0x14, 1)

                            # $STANDARD_INFORMATION
                            if typeAttribute == "0x10":
                                fp.seek(offsetContent, 1)
                                timeCreatedNS = int.from_bytes(fp.read(8), 'little')
                                fp.seek(-8 - offsetContent, 1)
                                organizedTime = datetime(1601, 1, 1, 0, 0, 0) + timedelta(seconds = timeCreatedNS / 1e7) + timedelta(hours = 7)
                                fileDateCreated = (str(organizedTime.day) + "/" + str(organizedTime.month) + "/" + str(organizedTime.year))
                                fileTimeCreated = (str(organizedTime.hour) + ":" + str(organizedTime.minute) + ":" + str(organizedTime.second) + "." + str(organizedTime.microsecond))

                            # $FILE_NAME
                            elif typeAttribute == "0x30":
                                fp.seek(offsetContent, 1)
                                fileIDParent = int.from_bytes(fp.read(6), 'little')
                                fp.seek(-6, 1)

                                fp.seek(0x38, 1)
                                stringAttribute = bin(int.from_bytes(fp.read(4), 'little'))[2:]
                                fp.seek(-4 - 0x38, 1)

                                bitPosition = 0
                                for bit in reversed(stringAttribute):
                                    if (bit == '1'):
                                        if (bitPosition == 0): fileAttributes.append('Read-Only')
                                        elif (bitPosition == 1): fileAttributes.append('Hidden')
                                        elif (bitPosition == 2): fileAttributes.append('System')
                                        elif (bitPosition == 5): fileAttributes.append('Archive')
                                        elif (bitPosition == 28): fileAttributes.append('Directory')
                                    bitPosition += 1

                                fp.seek(0x40, 1)
                                lengthFileName = int.from_bytes(fp.read(1), 'little')
                                fp.seek(-1 - 0x40, 1)

                                fp.seek(0x42, 1)
                                fileName = fp.read(lengthFileName * 2).replace(b'\x00', b'').decode('utf-8')
                                fp.seek(-(lengthFileName * 2) - 0x42, 1)

                                fp.seek(-offsetContent, 1)

                            # $DATA
                            elif typeAttribute == "0x80":
                                fp.seek(offsetContent, 1)

                                fp.seek(0x08, 1)
                                residentType = int.from_bytes(fp.read(1), 'little')
                                fp.seek(-1 - 0x08, 1)

                                if (residentType == 0):
                                    fileSize = sizeContent
                                else:
                                    fp.seek(0x38, 1)
                                    fileSize = int.from_bytes(fp.read(8), 'little')
                                    fp.seek(-8 - 0x38, 1)

                                fp.seek(-offsetContent, 1)

                            totalAttributes += sizeAttribute
                            fp.seek(sizeAttribute, 1)

                    i += 1

                    if i < 37:
                        fp.seek(bytesPerMFTEntry, 1)
                        fp.read(1)
                        fp.seek(-1, 1)
                        continue

                    if fileDateCreated == '': break

                    fileAttributesString = ''
                    if not fileAttributes: fileAttributesString = 'None'
                    else:
                        setAttributes = [*set(fileAttributes)]
                        fileAttributesString = ', '.join(setAttributes)

                    fileData = FileNTFS(fileID, fileIDParent, fileName, fileAttributesString, fileDateCreated, fileTimeCreated, fileSize)
                    filesNTFS.append(fileData)

                    fp.seek(bytesPerMFTEntry, 1)
                    fp.read(1)
                    fp.seek(-1, 1)

                partition_type_entry['text'] = 'NTFS'
                insert_tree('NTFS')

            # Kiểu FAT32
            elif (type == "MSDOS"):
                fp.seek(0x0B, 0)
                bytesPerSector = int.from_bytes(fp.read(2), 'little')
                fp.seek(0x0D, 0)
                sectorsPerCluster = int.from_bytes(fp.read(1), 'little')
                fp.seek(0x0E, 0)
                sectorsBeforeFAT = int.from_bytes(fp.read(2), 'little')
                fp.seek(0x10, 0)
                numberOfFATs = int.from_bytes(fp.read(1), 'little')

                fp.seek(0x52, 0)

                volumeSize = 0 
                sectorsPerFAT = 0

                FATtype = fp.read(5).decode("ascii")

                if (FATtype != "FAT32"):
                    partition_type_entry['text'] = "ERROR: Partition là FAT nhưng không phải FAT32"
                    
                else:
                    fp.seek(0x20, 0)
                    volumeSize = int.from_bytes(fp.read(4), 'little')

                    fp.seek(0x24, 0)
                    sectorsPerFAT = int.from_bytes(fp.read(4), 'little')

                    fp.seek(0x2C, 0)
                    RDETIndex = int.from_bytes(fp.read(4), 'little')

                    RDETLocation = (sectorsBeforeFAT + numberOfFATs*sectorsPerFAT)*bytesPerSector

                    # In thông tin đĩa ra terminal
                    print('Bytes per Sector: ' + str(bytesPerSector))
                    print('Sectors per Cluster: ' + str(sectorsPerCluster))
                    print('Sectors before FAT: ' + str(sectorsBeforeFAT))
                    print('Number of FAT table: ' + str(numberOfFATs))
                    print('Volume Size: ' + str(volumeSize))
                    print('Sector per FAT: ' + str(sectorsPerFAT))
                    print('First cluster of RDET: ' + str(RDETIndex))
                    print()
                    
                    filesFAT32 = FileFAT32("")
                    filesFAT32 = []
                    
                    list_length = 0
                    fp.seek(RDETLocation, 0)
                    fp.read(1)
                    temp_name = ""
                    index = RDETLocation
                    #Check if there are no more files to read by counting the file
                    cou = 0
                    sentinal = 0
                    father = [-1]
                    isRead = []
                    r_check = False
                    
                    while True:
                        fp.seek(index, 0)
                        isDeleted = fp.read(1)
                        #If the file is deleted
                        if (int.from_bytes(isDeleted,'little') == 229):
                            
                            index += 32
                        #If the entry is NULL
                        elif (int.from_bytes(isDeleted,'little') == 0):
                            if (cou >= list_length):
                                break

                            if (filesFAT32[cou].sentinal):
                                child_location = (filesFAT32[cou].beginning_cluster - RDETIndex) * sectorsPerCluster * bytesPerSector + RDETLocation
                                #If the children files havenot been read
                                
                                for j in range(len(isRead)):
                                    if (child_location == isRead[j]):
                                        r_check = True
                                if (r_check == False):
                                    index = child_location
                                                    
                                
                                r_check = False
                            cou += 1
                        else:
                            fp.seek(index + 0x0B, 0)
                            check = fp.read(1)

                            if (int.from_bytes(check, 'little') == 15):
                                name = ""

                                fp.seek(index + 0x01, 0)
                                tmp = fp.read(2)
                                check = tmp[1:]
                                
                                i = 0

                                while (int.from_bytes(check,'little') != 255 and i < 5):
                                    name = name + tmp.decode("utf-16")
                                    tmp = fp.read(2)
                                    check = tmp[1:]
                                    i += 1

                                fp.seek(index + 0x0E, 0)
                                tmp = fp.read(2)
                                check = tmp[1:]
                                i = 0
                                while (int.from_bytes(check, 'little') != 255 and i < 6):
                                    name = name + tmp.decode("utf-16")
                                    tmp = fp.read(2)
                                    check = tmp[1:]
                                    i += 1
                                fp.seek(index + 0x1C, 0)
                                tmp = fp.read(2)
                                check = tmp[1:]
                                i = 0
                                while (int.from_bytes(check, 'little') != 255 and i < 2):
                                    name = name + tmp.decode("utf-16")
                                    tmp = fp.read(2)
                                    check = tmp[1:]
                                    i += 1
                                #Reverse the file name
                                temp_name = name + temp_name
                            else:
                                #Check if there is any extra entries before this main entry
                                guard = False
                                if (temp_name == ""):
                                    fp.seek(index, 0)
                                    temp_name = fp.read(8).decode("utf-8")
                                    guard = True

                                temp_name = temp_name[::-1]

                                while (temp_name[0] == " "):
                                    temp_name = temp_name[1:]

                                if (guard == False): temp_name = temp_name[1:]

                                temp_name = temp_name[::-1]
                                
                                tmp = temp_name
                                if (temp_name == "."):
                                    fp.seek(index + 0x08, 0)
                                    temp_name = temp_name + fp.read(3).decode("utf-8").lower().replace(" ","")
                                
                                if (temp_name == "."):
                                    fp.seek(index + 32, 0)
                                    temp_name = fp.read(8).decode("utf-8").replace(" ","")
                                    fp.seek(index + 40, 0)
                                    temp_name = temp_name + fp.read(3).decode("utf-8").lower().replace(" ","")
                                    if (temp_name == ".."):
                                        sentinal += 1
                                        isRead.append(index)
                                
                                if (temp_name != "." and temp_name != ".." and tmp != "." and tmp != ".."):
                                    temp_name = tmp
                                    temp_extension = ""

                                    fp.seek(index + 0x08, 0)
                                    temp_extension =  fp.read(3).decode("utf-8").lower()

                                    if (guard and temp_extension != "   "):
                                        temp_name = temp_name + "." + temp_extension

                                    filesFAT32.append(FileFAT32(temp_name))
                                    list_length += 1

                                    filesFAT32[list_length - 1].location = index
                                    
                                    if (sentinal == len(father)):
                                        filesFAT32[list_length - 1].father = father[sentinal - 1]
                                    else:
                                        filesFAT32[list_length - 1].father = father[sentinal]

                                    filesFAT32[list_length - 1].extension = temp_extension

                                    fp.seek(index + 0x0B, 0)

                                    temp_attribute = bin(int.from_bytes(fp.read(1), 'little'))[2:]
                                    position = 0
                                    
                                    for bit in temp_attribute[::-1]:
                                        if (bit == "1"):
                                            if (position == 0 or position == 1 or position == 2 or position == 3 or position == 4 or position == 5): 
                                                if (position == 4): 
                                                    filesFAT32[list_length - 1].sentinal = True
                                                    father.append(list_length - 1)
                                                filesFAT32[list_length - 1].attributes += str(position) + " "
                                        position += 1
                                    
                                    t_attribute = getAttributes(filesFAT32[list_length - 1].attributes)

                                    filesFAT32[list_length - 1].attributes = t_attribute


                                    fp.seek(index + 0x0D, 0)

                                    t_time = '{0:b}'.format(int.from_bytes(fp.read(3), 'little'))
                                    

                                    for i in range(24 - len(t_time)):
                                        t_time = "0" + t_time
                                    #Extract hours, minutes, seconds... from binary string
                                    tmp_time = ""
                                    for i in range(5):
                                        tmp_time += t_time[i]

                                    filesFAT32[list_length - 1].created_time = filesFAT32[list_length - 1].created_time + str(int(tmp_time, 2)) + ":"
                                    tmp_time =""
                                    for i in range(5, 11):
                                        tmp_time += t_time[i]
                                    filesFAT32[list_length - 1].created_time = filesFAT32[list_length - 1].created_time + str(int(tmp_time, 2)) + ":"

                                    tmp_time =""
                                    for i in range(11, 17):
                                        tmp_time += t_time[i]
                                    filesFAT32[list_length - 1].created_time = filesFAT32[list_length - 1].created_time + str(int(tmp_time, 2)) + "."

                                    tmp_time =""
                                    for i in range(17, 24):
                                        tmp_time += t_time[i]
                                    filesFAT32[list_length - 1].created_time += str(int(tmp_time, 2))

                                    #Date
                                    tmp_time = ""
                                    fp.seek(index + 0x10, 0)

                                    t_time = '{0:b}'.format(int.from_bytes(fp.read(2), 'little'))

                                    for i in range(16 - len(t_time)):
                                        t_time = "0" + t_time
                                    
                                    for i in range(7):
                                        tmp_time += t_time[i]

                                    filesFAT32[list_length - 1].created_date = str(int(tmp_time, 2) + 1980) + filesFAT32[list_length - 1].created_date

                                    tmp_time =""
                                    for i in range(7, 11):
                                        tmp_time += t_time[i]
                                    if (int(tmp_time, 2) == 0):
                                        filesFAT32[list_length - 1].created_date = "1/" + filesFAT32[list_length - 1].created_date
                                    else:
                                        filesFAT32[list_length - 1].created_date = str(int(tmp_time, 2)) + "/" + filesFAT32[list_length - 1].created_date

                                    tmp_time =""
                                    for i in range(11, 16):
                                        tmp_time += t_time[i]
                                    if (int(tmp_time, 2) == 0):
                                        filesFAT32[list_length - 1].created_date = "1/" + filesFAT32[list_length - 1].created_date
                                    else:
                                        filesFAT32[list_length - 1].created_date = str(int(tmp_time, 2)) + "/" + filesFAT32[list_length - 1].created_date


                                    fp.seek(index + 0x1A, 0)

                                    filesFAT32[list_length - 1].beginning_cluster = int.from_bytes(fp.read(2), 'little')

                                    fp.seek(index + 0x1C, 0)
                                    filesFAT32[list_length - 1].size = int.from_bytes(fp.read(4), 'little')

                                temp_name = ""
                            
                            index += 32
                    
                    
                partition_type_entry['text'] = 'FAT32'
                insert_tree('FAT32')

            # Không phải cả 2
            else: partition_type_entry['text'] = 'ERROR: Partition không phải là FAT32 hay NTFS'
    except:
        tree.delete(*tree.get_children())
        partition_type_entry['text'] = 'ERROR: Partition không tồn tại'

# Tạo nút tìm partition
partition_input_button = tk.Button(window, text='Enter', command=open_partition)
partition_input_button.place(x=165, y=2)

# Hiện thông tin của một file
def display_info(self):
    # Lấy ID file được chọn
    item = tree.selection()[0]

    path_list = []

    # Đọc file NTFS
    if (len(filesNTFS) > 0):
        for file in filesNTFS:
            if file.ID == int(item):
                path_list.append(file.name)

                parent = file.ID_parent

                while True:
                    if not any(obj.ID == parent for obj in filesNTFS):
                        break
                    else:
                        for fileP in filesNTFS:
                            if fileP.ID == parent:
                                path_list.append(fileP.name)
                                parent = fileP.ID_parent

                path_list.reverse()
                path_list_string = ''
                for name in path_list:
                    path_list_string += name + '\\'

                name_entry['text'] = file.name
                attribute_entry['text'] = file.attributes
                date_entry['text'] = file.date_created
                time_entry['text'] = file.time_created
                size_entry['text'] = str(file.size) + ' bytes'
                path_entry['text'] = partition_letter + ':\\' + path_list_string[:-1]

    # Đọc file FAT32
    elif (len(filesFAT32) > 0):
        for fileID in range(len(filesFAT32)):
            file = filesFAT32[fileID]
            if fileID == int(item):
                path_list.append(file.name)

                parent = file.father

                while True:
                    if not any(index == parent for index in range(len(filesFAT32))):
                        break
                    else:
                        for filePID in range(len(filesFAT32)):
                            if filePID == parent:
                                fileP = filesFAT32[filePID]
                                path_list.append(fileP.name)
                                parent = fileP.father

                path_list.reverse()
                path_list_string = ''
                for name in path_list:
                    path_list_string += name + '\\'

                name_entry['text'] = file.name
                attribute_entry['text'] = file.attributes
                date_entry['text'] = file.created_date
                time_entry['text'] = file.created_time
                size_entry['text'] = str(file.size) + ' bytes'
                path_entry['text'] = partition_letter + ':\\' + path_list_string[:-1]

tree.bind('<<TreeviewSelect>>', display_info)
window.mainloop()