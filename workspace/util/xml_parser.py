import xml.etree.ElementTree as ET

class XmlParser:
    def __init__(self):
        self.kisa_library_index = ET.Element("KisaLibraryIndex")
        self.library = ET.SubElement(self.kisa_library_index, "Library")
        self.clip = ET.SubElement(self.library, "Clip")
        self.header = ET.SubElement(self.clip, "Header")
        self.alarm_events = ET.SubElement(self.header, "AlarmEvents")
        self.filename = ET.SubElement(self.header, "Filename")
        self.alarms = ET.SubElement(self.clip, "Alarms")
    
    def set_alarm_events(self, alarm_events):
        self.alarm_events.text = alarm_events

    def set_file_name(self, file_name):
        self.filename.text = file_name

    def set_alarm_loitering(self, start_time_val):
        alarm = ET.SubElement(self.alarms, "Alarm")
        start_time = ET.SubElement(alarm, "StartTime")
        start_time.text = start_time_val
        alarm_desc = ET.SubElement(alarm, "AlarmDescription")
        alarm_desc.text = "Loitering"
        alarm_duration = ET.SubElement(alarm, "AlarmDuration")
        alarm_duration.text = "00:00:10"

    def set_alarm_intrusion(self, start_time_val):
        alarm = ET.SubElement(self.alarms, "Alarm")
        start_time = ET.SubElement(alarm, "StartTime")
        start_time.text = start_time_val
        alarm_desc = ET.SubElement(alarm, "AlarmDescription")
        alarm_desc.text = "Intrusion"
        alarm_duration = ET.SubElement(alarm, "AlarmDuration")
        alarm_duration.text = "00:00:10"
    
    def set_alarm_people_counting(self, results):
        for result in results:
            start_time_val, count, in_out = result
            alarm = ET.SubElement(self.alarms, "Alarm")
            start_time = ET.SubElement(alarm, "StartTime")
            start_time.text = start_time_val
            alarm_desc = ET.SubElement(alarm, "AlarmDescription")
            alarm_desc.text = "PeopleCounting"
            alarm_in_out = ET.SubElement(alarm, in_out)
            alarm_in_out.text = str(count)

    def set_alarm_queueing(self, results):
        for result in results:
            start_time_val, count, in_out = result
            alarm = ET.SubElement(self.alarms, "Alarm")
            start_time = ET.SubElement(alarm, "StartTime")
            start_time.text = start_time_val
            alarm_desc = ET.SubElement(alarm, "AlarmDescription")
            alarm_desc.text = "Queueing"
            alarm_in_out = ET.SubElement(alarm, in_out)
            alarm_in_out.text = str(count)
        
    def indent(self, elem, level=0): 
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def count_alarms(self):
        return len(self.alarms)
        
    def save_xml(self, file_name):
        self.indent(self.kisa_library_index)
        # XML 파일로 저장
        tree = ET.ElementTree(self.kisa_library_index)
        tree.write(file_name, encoding="utf-8", xml_declaration=True)

    def get_file_list(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # 파일 목록 추출
        file_list = []
        for file_elem in root.findall('.//File'):
            file_name = file_elem.find('Name').text
            file_list.append(file_name)
            
        return file_list

    def get_map(self, xml_path):
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_data = f.read()
            root = ET.fromstring(xml_data)
            points = {}
            for area in root:
                area_name = area.tag
                points[area_name] = [point.text for point in area.findall('Point')]
            return points
        
    
