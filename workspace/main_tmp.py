import sys
from util.tdsthread import TDSThread
from util.xml_parser import XmlParser
from util.util import Intrusion, Loitering, Queueing, PeopleCounting

class MyCCTV:
    def __init__(self):
        self.map_path = "/workspace/map/"

        self.xml_parser = XmlParser()
        self.intrustion = None
        self.loitering = None
        self.queueing = None
        self.people_counting = None

    def __del__(self):
        del self.map_path
        del self.xml_parser
        if self.intrustion:
            del self.intrustion
        if self.loitering:
            del self.loitering
        if self.queueing:
            del self.queueing
        if self.people_counting:
            del self.people_counting

    def parse_map(self, map_file_path):
        points = self.xml_parser.get_map(map_file_path)

        rtn_points = []
        for points_tag, detect_points in points.items():
            detect_points = [(int(point.split(',')[0]), int(point.split(',')[1])) for point in detect_points]
            if points_tag == "Intrusion":
                if self.intrustion is None:
                    self.intrustion = Intrusion()
                self.intrustion.set_detect_area(detect_points)
            elif points_tag == "Loitering":
                if self.loitering is None:
                    self.loitering = Loitering()
                self.loitering.set_detect_area(detect_points)
            elif points_tag == "Queueing":
                if self.queueing is None:
                    self.queueing = Queueing()
                self.queueing.set_detect_area(detect_points)
            elif points_tag == "PeopleCountingA":
                if self.people_counting is None:
                    self.people_counting = PeopleCounting()
                self.people_counting.set_detect_area_A(detect_points)
            elif points_tag == "PeopleCountingB":
                if self.people_counting is None:
                    self.people_counting = PeopleCounting()
                self.people_counting.set_detect_area_B(detect_points)
            else:
                continue

            rtn_points.append(detect_points)

        return rtn_points

    def cctv_func(self, x1, y1, x2, y2, id, time):
        result = (x1, y1, x2, y2, id, time)

        if self.intrustion:
            self.intrustion.cctv_detect(result)
        if self.loitering:
            self.loitering.cctv_detect(result)
        if self.queueing:
            self.queueing.cctv_detect(result)
        if self.people_counting:
            self.people_counting.cctv_detect(result)

    def get_reulst(self, filename):
        self.xml_parser.set_file_name(filename)
        if self.intrustion:
            self.xml_parser.set_alarm_intrusion(self.intrustion.get_result())
            print(self.intrustion.get_result())
        if self.loitering:
            self.xml_parser.set_alarm_loitering(self.loitering.get_result())
            print(self.loitering.get_result())
        if self.queueing:
            self.xml_parser.set_alarm_queueing(self.queueing.get_result())
            print(self.queueing.get_result())
        if self.people_counting:
            self.xml_parser.set_alarm_people_counting(self.people_counting.get_result())
            print(self.people_counting.get_result()) 
        
        alarm_count = self.xml_parser.count_alarms()
        self.xml_parser.set_alarm_events(str(alarm_count))

        xml_file_path = "xml/" + filename.rsplit(".", 1)[0] + ".xml"
        self.xml_parser.save_xml(xml_file_path)
        
def convert_to_lines(polygons):
    lines = []
    for polygon in polygons:
        for i in range(len(polygon)):
            # 다각형의 마지막 점과 첫 번째 점을 연결
            if i == len(polygon) - 1:
                lines.append((polygon[i][0], polygon[i][1], polygon[0][0], polygon[0][1]))
            else:
                lines.append((polygon[i][0], polygon[i][1], polygon[i + 1][0], polygon[i + 1][1]))
    return lines

def extract_prefix(file_name):
    parts = file_name.split('_')
    if len(parts) >= 2:
        return "_".join(parts[:2])
    else:
        return None
    
def main():
    model_config_path = "model/yolov8/config_infer_primary_yoloV8x.txt"
    tracker_config_path = "model/tracker/dstracker_config.txt"


    xml_parser = XmlParser()
    # file_list = xml_parser.get_file_list("file_list.xml")
    # del xml_parser

    for file_name in file_list:
        print(file_name)
        prefix = extract_prefix(file_name)
        my_cctv = MyCCTV()
        map_file = "map/" + prefix + ".map"
        points = my_cctv.parse_map(map_file)
        points = convert_to_lines(points)

        tds_thread = TDSThread()
        tds_thread.set_target_func(my_cctv.cctv_func)
        tds_thread.set_draw_points(points)
        # tds_thread.set_text(file_name)
        # tds_thread.create_source_bin(0, "rtsp", "rtsp://192.168.7.10:8554/")
        # tds_thread.create_source_bin(0, "rtsp", "rtsp://10.19.0.16:8554/")
        # tds_thread.create_source_bin(0, "rtsp", "rtsp://192.168.45.144:8554/")
        tds_thread.create_source_bin(0, "rtsp", "rtsp://192.168.0.2:8554/")
        tds_thread.create_gie(model_config_path)
        tds_thread.create_tracker(tracker_config_path)
        # tds_thread.create_sink_bin("rtmp", '"rtmp://tbond-lb.tlln.xyz/live/cctv live=1"')
        tds_thread.create_sink_bin("display")
        tds_thread.create_pipeline()
        
        tds_thread.start()
        try:
            tds_thread.join()
        except KeyboardInterrupt:
            tds_thread.stop()
            my_cctv.get_reulst(file_name)
            return 0
        my_cctv.get_reulst(file_name)
        del my_cctv
        del tds_thread



if __name__ == '__main__':
    sys.exit(main())
