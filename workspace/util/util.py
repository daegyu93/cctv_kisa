
import cv2
import numpy as np
import pandas as pd
from collections import defaultdict

import xmltodict

class CCTV:
    def __init__(self):
        self.points = []
        self.points_arr = []
        self.scenario = ""
    
    def __del__(self):
        del self.points
        del self.points_arr
        del self.scenario
        
    def get_scenario(self, xml):
        with open(xml, 'r') as f:
            ret = xmltodict.parse(f.read())

        self.scenario = ret['KisaLibraryIndex']['Library']['Scenario']
        return self.scenario
    
    def set_detect_area(self, points):
        self.points = points
        self.points_arr = np.array(self.points, np.int32)
        self.points_arr = self.points_arr.reshape((-1, 1, 2))
    
    def point_in_detect_area(self, x1, y1, x2, y2):
        detect_points = []
        detect_points.append((x1, y1))
        detect_points.append((x2, y1))
        detect_points.append((x2, y2))
        detect_points.append((x1, y2))
        ret = 0
        for point in detect_points:
            if cv2.pointPolygonTest(np.array(self.points, np.int32), point, False) <= 0 :
                ret += 1
        return ret

    def format_time(self, time_seconds):
        # set minutes, seconds, and 
        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        formatted_time = "00:{:02d}:{:02d}".format(minutes, seconds)
        return formatted_time

    
class Loitering(CCTV):
    def __init__(self):
        super().__init__()
        self.pre_time_seconds = 0
        self.loitering_time = {}
        self.unloitering_person = []
        self.loitering_person = []
        self.start_time = 0

    def __del__(self):
        super().__del__()
        del self.pre_time_seconds
        del self.loitering_time
        del self.unloitering_person
        del self.loitering_person
        del self.start_time    
    
    def cctv_detect(self, result):
        x1, y1, x2, y2, id, time = result
        fps = 25
        if super().point_in_detect_area(x1, y1, x2, y2) == 0:
            if id in self.unloitering_person:
                self.loitering_time[id] += 1/fps
        else:
            self.loitering_time[id] = 0
            if id not in self.unloitering_person:
                self.unloitering_person.append(id)
        
        if id in self.loitering_time and self.loitering_time[id] > 10:
            if id not in self.loitering_person and id in self.unloitering_person:
                self.loitering_person.append(id)
                # print(self.format_time(time), id, 'loitering!!')
                self.start_time = time

    def get_result(self):
        return self.format_time(self.start_time)


class Intrusion(CCTV):
    def __init__(self):
        super().__init__()
        self.in_person = []
        self.out_person = []
        self.intrusion_person = {}

    def __del__(self):
        super().__del__()
        del self.intrusion_person
        del self.in_person
        del self.out_person
    
    def cctv_detect(self, result):
        x1, y1, x2, y2, id, time = result
        if super().point_in_detect_area(x1, y1, x2, y2) == 0 :
            if id not in self.in_person:
                self.in_person.append(id)
                if id in self.out_person:
                    self.intrusion_person[round(time)] = id
                    # print(self.format_time(time), id, 'intrusuion!!')
            if id not in self.in_person:
                self.in_person.append(id)
        else:
            if id not in self.out_person:
                self.out_person.append(id)  

    def get_result(self):
        grouped_dict = defaultdict(list)

        for key, value in self.intrusion_person.items():
            grouped_dict[value].append(key)

        min_max_values = {}
        for value, keys in grouped_dict.items():
            min_max_values[value] = (min(keys), max(keys))

        StartTime = 0
        AlarmDuration = 0
        for value, (min_value, max_value) in min_max_values.items():
            if StartTime < min_value:
                StartTime = min_value
                AlarmDuration = max_value - min_value
        
        # self.format_time(AlarmDuration)
        return self.format_time(StartTime)

class Queueing(CCTV):
    def __init__(self):
        super().__init__()
        self.in_out = []
        self.in_count = 1
        self.out_count = 1
        self.in_person = []
        self.out_person = []
    
    def __del__(self):
        super().__del__()
        del self.in_out
        del self.in_count
        del self.out_count
        del self.in_person
        del self.out_person

    
    def cctv_detect(self, result):
        x1, y1, x2, y2, id, time = result
        if super().point_in_detect_area(x1, y1, x2, y2) == 0 :
            color = (0, 255, 0)
            if id not in self.in_person:
                self.in_person.append(id)
                self.in_out.append((self.format_time(time), self.in_count, 'Ingress'))
                self.in_count += 1
        elif super().point_in_detect_area(x1, y1, x2, y2) == 4 :
            if id in self.in_person and id not in self.out_person:
                self.out_person.append(id)
                self.in_out.append((self.format_time(time), self.out_count, 'Outgress'))
                self.out_count += 1

    def get_result(self):
        return self.in_out
    
class PeopleCounting(CCTV):
    def __init__(self):
        super().__init__()
        self.points_A = []
        self.points_B = []
        self.points_arr_A = []
        self.points_arr_B = []
        
        self.a_b_person = {}
        self.a_person = {}
        self.b_person = {}   
        
        self.counted_person = []

        self.in_out = []
        self.in_count = 1
        self.out_count = 1
    
    def __del__(self):
        super().__del__()
        del self.points_A
        del self.points_B
        del self.points_arr_A
        del self.points_arr_B
        del self.a_b_person
        del self.a_person
        del self.b_person
        del self.counted_person
        del self.in_out
        del self.in_count
        del self.out_count
        
    def set_detect_area_A(self, points):
        for point in points:
            x = point[0]
            y = point[1]
            if point[0] < 10:
                x = 0
            elif point[0] > 1270:
                x = 1280
            if point[1] < 10:
                y = 0
            elif point[1] > 710:
                y = 720
            self.points_A.append((x, y))
            
        # self.points_A = points
        self.points_arr_A = np.array(self.points_A, np.int32)
        self.points_arr_A = self.points_arr_A.reshape((-1, 1, 2))

    def set_detect_area_B(self, points):
        for point in points:
            x = point[0]
            y = point[1]
            if point[0] < 10:
                x = 0
            elif point[0] > 1270:
                x = 1280
            if point[1] < 10:
                y = 0
            elif point[1] > 710:
                y = 720
            self.points_B.append((x, y))
        self.points_arr_B = np.array(self.points_B, np.int32)
        self.points_arr_B = self.points_arr_B.reshape((-1, 1, 2))
        
    def point_in_detect_area(self, x1, y1, x2, y2):
        detect_points = []
        detect_points.append((x1, y1))
        detect_points.append((x2, y1))
        detect_points.append((x2, y2))
        detect_points.append((x1, y2))

        in_area_A = False
        in_area_B = False
        in_area_AB = False

        in_A_count = 0
        in_B_count = 0

        for point in detect_points:
            if cv2.pointPolygonTest(np.array(self.points_A, np.int32), point, False) >= 0 :
                in_A_count += 1
            elif cv2.pointPolygonTest(np.array(self.points_B, np.int32), point, False) >= 0 :
                in_B_count += 1
        
        if in_A_count == 4:
            in_area_A = True
        elif in_B_count == 4:
            in_area_B = True
        elif in_A_count + in_B_count == 4:
            in_area_AB = True

        return in_area_A, in_area_B, in_area_AB
        
    def cctv_detect(self, result):
        x1, y1, x2, y2, id, time = result
        in_area_A, in_area_B, in_area_AB = self.point_in_detect_area(x1, y1, x2, y2)
        if in_area_A:
            self.a_person[id] = time
            # print(time, id, 'in_area_A')
        elif in_area_B:
            self.b_person[id] = time
            # print(time, id, 'in_area_B')
        elif in_area_AB:
            self.a_b_person[id] = time
            # print(time, id, 'in_area_AB')

        out_flag, in_flag = False, False
        if id not in self.counted_person:
            if id in self.b_person and id in self.a_person:
                if self.b_person[id] > self.a_person[id]:
                    in_flag = True
                else:
                    out_flag = True
            elif id in self.a_b_person and id in self.b_person:
                if self.b_person[id] > self.a_b_person[id]:
                    in_flag = True
            elif id in self.a_b_person and id in self.a_person:
                if self.a_person[id] > self.a_b_person[id]:
                    out_flag = True

            if in_flag:
                self.counted_person.append(id)
                self.in_out.append((self.format_time(time), self.in_count, 'InCount'))
                # print(self.format_time(time), self.in_count, 'InCount')
                # print(self.format_time(time), id, 'InCount')
                self.in_count += 1
            elif out_flag:
                self.counted_person.append(id)
                self.in_out.append((self.format_time(time), self.out_count, 'OutCount'))
                # print(self.format_time(time), self.out_count, 'OutCount')
                # print(self.format_time(time), id, 'OutCount')
                self.out_count += 1

    def get_result(self):
        return self.in_out
    
    
