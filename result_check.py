import os
import xml.etree.ElementTree as ET
import glob

my_xml_path = "workspace/xml/"
kisa_xml_path = "/home/avs200/cctv/"
save_path = "xml_check/"
my_xml_files = glob.glob(os.path.join(my_xml_path, "*.xml"))
my_xml_files.sort()

for my_xml_file in my_xml_files:
    file_name = os.path.basename(my_xml_file)
    kisa_xml = os.path.join(kisa_xml_path, file_name)
    if kisa_xml is None:
        print("Not found answer file: ", kisa_xml)
        continue

    # print("file_name: ", file_name) 

    my_tree = ET.parse(my_xml_file)
    my_root = my_tree.getroot()

    kisa_tree = ET.parse(kisa_xml)
    kisa_root = kisa_tree.getroot()
    scen = kisa_root.find('.//Scenario').text 
    if scen == 'PeopleCounting' or scen == 'Queueing':
        # continue
        fp = open(save_path + file_name.split('.')[0] + ".txt", "w")
        my_in_time = []
        my_out_time = []
        kisa_in_time = []
        kisa_out_time = []
        
        for file_elem in my_root.findall('.//Alarm'):
            start_time = file_elem.find('StartTime').text
            if scen == 'PeopleCounting':
                in_out = file_elem.find('InCount')
            else:
                in_out = file_elem.find('Ingress')
            if in_out is not None:
                my_in_time.append(start_time)
            else:
                my_out_time.append(start_time)

        for file_elem in kisa_root.findall('.//Alarm'):
            start_time = file_elem.find('StartTime').text
            if scen == 'PeopleCounting':
                in_out = file_elem.find('InCount')
            else:
                in_out = file_elem.find('Ingress')
            if in_out is not None:
                kisa_in_time.append(start_time)
            else:
                kisa_out_time.append(start_time)
        
        max_count = max(len(my_in_time), len(kisa_in_time))
        index = 0

        for i in range(max_count):
            try:
                index += 1
                print("in", index, my_in_time[i], kisa_in_time[i])
                fp.write(str(index) + " " + my_in_time[i] + " " + kisa_in_time[i] + "\n")
            except:
                try:
                    print("in", index, my_in_time[i], "None")
                    fp.write(str(index) + " " + my_in_time[i] + " None\n")
                except:
                    print("in", index, "None", kisa_in_time[i])
                    fp.write(str(index) + " None " + kisa_in_time[i] + "\n")
        max_count = max(len(my_out_time), len(kisa_out_time))
        index = 0
        for i in range(max_count):
            try:
                index += 1
                print("out", index, my_out_time[i], kisa_out_time[i])
                fp.write(str(index) + " " + my_out_time[i] + " " + kisa_out_time[i] + "\n")
            except:
                try:
                    print("out", index, my_out_time[i], "None")
                    fp.write(str(index) + " " + my_out_time[i] + " None\n")
                except:
                    print("out", index, "None", kisa_out_time[i])
                    fp.write(str(index) + " None " + kisa_out_time[i] + "\n")
        
        fp.close()
        
    if scen == 'Intrusion' or scen == 'Loitering':
        continue
        fp = open(save_path + file_name.split('.')[0] + ".txt", "w")
        my_start_time = my_root.find('.//StartTime').text
        kisa_start_time = kisa_root.find('.//StartTime').text
        # hh:mm:ss to seconds   
        my_start_time_seconds = int(my_start_time.split(':')[0]) * 3600 + int(my_start_time.split(':')[1]) * 60 + int(my_start_time.split(':')[2])
        kisa_start_time_seconds = int(kisa_start_time.split(':')[0]) * 3600 + int(kisa_start_time.split(':')[1]) * 60 + int(kisa_start_time.split(':')[2])
        if my_start_time_seconds - kisa_start_time_seconds >= 10 or my_start_time_seconds - kisa_start_time_seconds <= -2:
            print(file_name, my_start_time, kisa_start_time,  my_start_time_seconds - kisa_start_time_seconds,"- error" )
        else:
            print(file_name, my_start_time, kisa_start_time, my_start_time_seconds - kisa_start_time_seconds)
        fp.write(my_start_time + " " + kisa_start_time + "\n")
        fp.close()



