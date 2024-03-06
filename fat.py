class File:
    name = ""
    extension = "."
    attributes = ""
    
    created_time = ""
    created_date = ""

    location = 0
    beginning_cluster = 0
    size = 0
    father = -1
    #Check if it is a directory
    sentinal = False
    #Constructor
    def __init__(self, name):
        self.name = name


def getAttributes(atributes):
    temp = ""
    for i in range(len(atributes)):
        if (atributes[i] == "0"):
            temp += "Read-Only"
        elif (atributes[i] == "1"):
            temp += "Hidden"
        elif (atributes[i] == "2"):
            temp += "System"
        elif (atributes[i] == "3"):
            temp += "Volume label"
        elif (atributes[i] == "4"):
            temp += "Directory"
        elif (atributes[i] == "5"):
            temp += "Archive"

        if (i < len(atributes) - 2):
            temp += ", "
    return temp

from datetime import datetime, timedelta

with open(r"\\.\F:", "rb") as fp:
    fp.read(3)
    type = fp.read(5).decode("ascii")
    if (type == "MSDOS"):
        fp.seek(0x0B, 0)
        bytesPerSector = int.from_bytes(fp.read(2), 'little')
        fp.seek(0x0D, 0)
        sectorsPerCluster = int.from_bytes(fp.read(1), 'little')
        fp.seek(0x0E, 0)
        sectorsBeforeFAT = int.from_bytes(fp.read(2), 'little')
        fp.seek(0x10, 0)
        numberOfFATs = int.from_bytes(fp.read(1), 'little')

        fp.seek(0x52, 0)

        numberOfEntriesofRDET = 0 
        volumeSize = 0 
        sectorsPerFAT = 0

        FATtype = fp.read(5).decode("ascii")

        if (FATtype == "FAT32"):
            fp.seek(0x20, 0)
            volumeSize = int.from_bytes(fp.read(4), 'little')

            fp.seek(0x24, 0)
            sectorsPerFAT = int.from_bytes(fp.read(4), 'little')

            fp.seek(0x2C, 0)
            RDETIndex = int.from_bytes(fp.read(4), 'little')
            
        else:
            print("Error! The disk partition is not FAT32")
        

        RDETLocation = (sectorsBeforeFAT + numberOfFATs*sectorsPerFAT)*bytesPerSector
        
        file_list = File("")
        file_list = []
        
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

                if (file_list[cou].sentinal):
                    child_location = (file_list[cou].beginning_cluster - RDETIndex) * sectorsPerCluster * bytesPerSector + RDETLocation
                    #If the children files havenot been read
                    if (index - child_location < 0):
                        index = child_location
                        father.append(cou)
                        sentinal += 1
                    #If the children files have been read
                    else:
                        for j in range(len(isRead)):
                            if (child_location == isRead[j]):
                                r_check = True
                        if (r_check == False):
                            index = child_location
                            father.append(cou)
                            sentinal += 1
                        else:
                            for j in range(cou,list_length):
                                if (file_list[j].location > child_location):
                                    file_list[j].father = cou
                    isRead.append(child_location)
                    
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
                    
                    if (temp_name != "." and temp_name != ".."):
                        temp_extension = ""

                        fp.seek(index + 0x08, 0)
                        temp_extension =  fp.read(3).decode("utf-8").lower()

                        if (guard and temp_extension != "   "):
                            temp_name = temp_name + "." + temp_extension

                        file_list.append(File(temp_name))
                        list_length += 1

                        file_list[list_length - 1].location = index
                        
                        file_list[list_length - 1].father = father[sentinal]

                        file_list[list_length - 1].extension = temp_extension

                        fp.seek(index + 0x0B, 0)

                        temp_attribute = bin(int.from_bytes(fp.read(1), 'little'))[2:]
                        position = 0
                        
                        for bit in temp_attribute[::-1]:
                            if (bit == "1"):
                                if (position == 0 or position == 1 or position == 2 or position == 3 or position == 4 or position == 5): 
                                    if (position == 4): file_list[list_length - 1].sentinal = True
                                    file_list[list_length - 1].attributes += str(position) + " "
                            position += 1
                        
                        t_attribute = getAttributes(file_list[list_length - 1].attributes)

                        file_list[list_length - 1].attributes = t_attribute


                        fp.seek(index + 0x0D, 0)

                        t_time = '{0:b}'.format(int.from_bytes(fp.read(3), 'little'))
                        #print(t_time)

                        for i in range(24 - len(t_time)):
                            t_time = "0" + t_time
                        #Extract hours, minutes, seconds... from binary string
                        tmp_time = ""
                        for i in range(5):
                            tmp_time += t_time[i]

                        file_list[list_length - 1].created_time = file_list[list_length - 1].created_time + str(int(tmp_time, 2)) + ":"
                        tmp_time =""
                        for i in range(5, 11):
                            tmp_time += t_time[i]
                        file_list[list_length - 1].created_time = file_list[list_length - 1].created_time + str(int(tmp_time, 2)) + ":"

                        tmp_time =""
                        for i in range(11, 17):
                            tmp_time += t_time[i]
                        file_list[list_length - 1].created_time = file_list[list_length - 1].created_time + str(int(tmp_time, 2)) + "."

                        tmp_time =""
                        for i in range(17, 24):
                            tmp_time += t_time[i]
                        file_list[list_length - 1].created_time += str(int(tmp_time, 2))

                        #Date
                        tmp_time = ""
                        fp.seek(index + 0x10, 0)

                        t_time = '{0:b}'.format(int.from_bytes(fp.read(2), 'little'))

                        for i in range(16 - len(t_time)):
                            t_time = "0" + t_time
                        
                        for i in range(7):
                            tmp_time += t_time[i]

                        file_list[list_length - 1].created_date = str(int(tmp_time, 2) + 1980) + file_list[list_length - 1].created_date

                        tmp_time =""
                        for i in range(7, 11):
                            tmp_time += t_time[i]
                        if (int(tmp_time, 2) == 0):
                            file_list[list_length - 1].created_date = "1/" + file_list[list_length - 1].created_date
                        else:
                            file_list[list_length - 1].created_date = str(int(tmp_time, 2)) + "/" + file_list[list_length - 1].created_date

                        tmp_time =""
                        for i in range(11, 16):
                            tmp_time += t_time[i]
                        if (int(tmp_time, 2) == 0):
                            file_list[list_length - 1].created_date = "1/" + file_list[list_length - 1].created_date
                        else:
                            file_list[list_length - 1].created_date = str(int(tmp_time, 2)) + "/" + file_list[list_length - 1].created_date


                        fp.seek(index + 0x1A, 0)

                        file_list[list_length - 1].beginning_cluster = int.from_bytes(fp.read(2), 'little')

                        fp.seek(index + 0x1C, 0)
                        file_list[list_length - 1].size = int.from_bytes(fp.read(4), 'little')

                    temp_name = ""
                    

                index += 32
        print(isRead)
        for j in range(list_length):
            print("File " + str(j))
            print("Name: " + file_list[j].name)
            print("Attributes: " + file_list[j].attributes)
            print("Time created: " + file_list[j].created_time)
            print("Date created: " + file_list[j].created_date)
            print("Size: " + str(file_list[j].size) + " bytes")
            print("Father: " + str(file_list[j].father))
            print()
      