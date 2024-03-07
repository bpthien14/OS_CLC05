# Test mở ổ đĩa định dạng NTFS
from datetime import datetime, timedelta

# Tính toán dạng bù 2 cho chuỗi "val" có số lượng "bits" 
def twos_comp(val, bits):
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val

with open(r"\\.\E:", "rb") as fp: # Mở ổ đĩa dạng Binary
    # Lấy OEM ID 
    fp.read(3)
    type = fp.read(4).decode("ascii")


    if (type != "NTFS"):
        print("Not NTFS format!")
    else:
        # Lấy thông tin ổ đĩa (chuỗi byte dạng little edian)
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
        bytesPerMFTEntry = 2 ** abs(twos_comp(bytesPerMFTEntryNC, len(bin(bytesPerMFTEntryNC)[2:]))) # Tính số mũ là giá trị tuyệt đối của dạng bù 2 của giá trị tại 0x40

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

        # Tìm byte đầu tiên của bảng MFT:
        ## sector bắt đầu của MFT = MFTBstartCluster * sectorsPerCluster
        ## byte đầu tiên = sector bắt đầu của MFT * bytesPerSector
        MFTstartByte = MFTstartCluster * sectorsPerCluster * bytesPerSector
        fp.seek(MFTstartByte, 0)
        fp.read(1)

        startMFTEntry = MFTstartByte
        i = 0

        # Scan từng entry (mỗi bytesPerMFTEntry)
        while True:
            fp.seek(startMFTEntry, 0)
            if (fp.read(4).decode('ascii') != "FILE"): 
                startMFTEntry += bytesPerMFTEntry
                continue

            # Lấy offset của Attributes đầu tiên so với Entry
            fp.seek(startMFTEntry + 0x14, 0)
            offsetFirstAttribute = int.from_bytes(fp.read(2), 'little')

            # Lấy kích thước đã sử dụng của Entry
            fp.seek(startMFTEntry + 0x18, 0)
            sizeMFTEntryUsed = int.from_bytes(fp.read(4), 'little')

            # Lấy vị trí của Attributes so với toàn bộ đĩa
            startAttribute = startMFTEntry + offsetFirstAttribute

            # Khởi tạo thông tin cần lấy của từng file hay Directory
            fileName = ''
            fileAttributes = []
            fileDateCreated = ''
            fileTimeCreated = ''
            fileSize = 0

            # Nếu kích thước sử dụng > 0, lấy metadata của Entry
            if (sizeMFTEntryUsed > 0):
                while True:
                    # Đọc mã loại Attributes
                    fp.seek(startAttribute, 0)
                    typeAttribute = hex(int.from_bytes(fp.read(4), 'little'))

                    if typeAttribute == "0xffffffff": break # Mã kết thúc entry, ngừng đọc 

                    # Đọc kích thước của toàn bộ Attribute
                    fp.seek(startAttribute + 0x04, 0)
                    sizeAttribute = int.from_bytes(fp.read(4), 'little')

                    # Đọc kích thước phần nội dung Attribute
                    fp.seek(startAttribute + 0x10, 0)
                    sizeContent = int.from_bytes(fp.read(4), 'little')

                    # Đọc offset của nội dung Attribute so với Entry
                    fp.seek(startAttribute + 0x14, 0)
                    offsetContent = int.from_bytes(fp.read(2), 'little')

                    # Tính byte bắt đầu của nội dung Attribute so với toàn bộ đĩa
                    startContent = startAttribute + offsetContent

                    # $STANDARD_INFORMATION
                    if (typeAttribute == "0x10"):
                        fp.seek(startContent, 0)
                        timeCreatedNS = int.from_bytes(fp.read(8), 'little')
                        organizedTime = datetime(1601, 1, 1, 0, 0, 0) + timedelta(seconds = timeCreatedNS / 1e7) + timedelta(hours = 7)
                        fileDateCreated = (str(organizedTime.day) + "/" + str(organizedTime.month) + "/" + str(organizedTime.year))
                        fileTimeCreated = (str(organizedTime.hour) + ":" + str(organizedTime.minute) + ":" + str(organizedTime.second) + "." + str(organizedTime.microsecond))

                    # $FILE_NAME
                    elif (typeAttribute == "0x30"):
                        fp.seek(startContent + 0x38, 0)
                        stringAttribute = bin(int.from_bytes(fp.read(4), 'little'))[2:]

                        # Lấy giá trị cờ báo 
                        bitPosition = 0
                        for bit in reversed(stringAttribute):
                            if (bit == '1'):
                                if (bitPosition == 0): fileAttributes.append('Read-Only')
                                elif (bitPosition == 1): fileAttributes.append('Hidden')
                                elif (bitPosition == 2): fileAttributes.append('System')
                                elif (bitPosition == 5): fileAttributes.append('Archive')
                                elif (bitPosition == 28): fileAttributes.append('Directory')
                            bitPosition += 1

                        # Chiều dài tên tập tin
                        fp.seek(startContent + 0x40, 0)
                        lengthFileName = int.from_bytes(fp.read(1), 'little')

                        # Lấy tên tập tin
                        fp.seek(startContent + 0x42, 0)
                        fileName = fp.read(lengthFileName * 2).replace(b'\x00', b'').decode('utf-8')

                    # $DATA
                    elif (typeAttribute == "0x80"):
                        # Kiểm tra phần dữ liệu có là loại resident
                        fp.seek(startAttribute + 0x08, 0)
                        residentType = int.from_bytes(fp.read(1), 'little')

                        if (residentType == 0): # thuộc kiểu resident
                            fileSize = sizeContent
                        else:
                            fp.seek(startAttribute + 0x38, 0)
                            fileSize = int.from_bytes(fp.read(8), 'little')
                    # Qua Attribute tiếp theo
                    startAttribute += sizeAttribute
            # Qua entry tiếp theo
            startMFTEntry += bytesPerMFTEntry
            i += 1

            if (i < 37): continue

            if (fileDateCreated == ''): break

            print('File ' + str(i))
            print('Name: ' + fileName)

            if not fileAttributes: print('Attributes: None')
            else:
                setAttributes = [*set(fileAttributes)]
                print('Attributes: ' + ', '.join(setAttributes))

            print('Date created: ' + str(fileDateCreated))
            print('Time created: ' + str(fileTimeCreated))
            print('Size: ' + str(fileSize) + 'B')
            print()