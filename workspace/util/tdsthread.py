import sys
import threading
import time as timecheck
import configparser

import gi
import pyds
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst

Gst.init(None)
class TDSThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self.number_sources = 0
        self.source_str = {}

        self.gie_str = ""
        self.tracker_str = ""
        
        self.tiler_str = ""
        self.sink_str = ""
        
        self.pipeline_str = ""
                
        self.pipeline = None

        self.frame_count = 0
        self.start_time = timecheck.time()
        self.fps = 0

        # self.nvosd = None
        self.time_check_elm = None
        self._video_time = 0
        self.loop = None
        self.target_func = None
        self.draw_points = []
        self.text = ""

    def __del__(self):
        self.stop()

    def run(self):
        print("Running pipeline")
        self.__run_pipeline()

    def stop(self):
        print("Stopping pipeline")
        self.__stop_pipeline()
        self._stop_event.set()

    def create_source_bin(self, index, type, uri):
        fps = 25
        if self.source_str.get(index) is not None:
            print("{} source bin already exists".format(index))
            return
        if type == "rtsp":
            source_str = "rtspsrc location={} ! queue ! rtph264depay ! h264parse ! nvv4l2decoder ! queue ! videorate ! video/x-raw(memory:NVMM), framerate=(fraction){}/1 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! m.sink_{} ".format(uri,fps, index)
            # source_str = "rtspsrc location={} ! queue ! rtph264depay ! h264parse ! nvv4l2decoder ! queue ! nvvideoconvert ! video/x-raw(memory:NVMM) ! m.sink_{} ".format(uri, index)
        elif type == "v4l2":
            source_str = "v4l2src device={} ! nvvideoconvert ! video/x-raw(memory:NVMM) ! m.sink_{} ".format(uri, index)
        elif type == "file":
            # source_str = "filesrc location={} ! qtdemux ! h264parse ! nvv4l2decoder ! queue ! videorate ! video/x-raw(memory:NVMM), framerate=(fraction)15/1 !  nvvideoconvert ! video/x-raw(memory:NVMM)! m.sink_{} ".format(uri, index)
            source_str = "filesrc location={} ! qtdemux ! h264parse ! nvv4l2decoder ! queue ! videorate ! video/x-raw(memory:NVMM), framerate=(fraction){}/1 !  nvvideoconvert ! video/x-raw(memory:NVMM)! m.sink_{} ".format(uri, fps, index)
            # source_str = "filesrc location={} ! qtdemux ! h264parse ! nvv4l2decoder ! queue ! nvvideoconvert ! video/x-raw(memory:NVMM) ! m.sink_{} ".format(uri, index)

        self.number_sources += 1
        self.source_str[index] = source_str

    def create_gie(self, model_path):
        gie_str = "! nvinfer config-file-path={} batch-size={} ".format(model_path, self.number_sources)
        self.gie_str += gie_str

    def create_tracker(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        config.sections()

        tracker_str = "! nvtracker "
        for key in config['tracker']:
            if key in ('ll-lib-file', 'll-config-file'):
                val = config.get('tracker', key)
            else:
                val = config.getint('tracker', key)
            # print(f'{key} : {val}')
            tracker_str += f"{key}={val} "
        
        self.tracker_str = tracker_str

    def create_tiler(self, rows, columns, width, height):
        tiler_str = "! nvmultistreamtiler rows={} columns={} width={} height={} ".format(rows, columns, width, height)
        self.tiler_str = tiler_str
        
    def create_sink_bin(self, type, uri=None):
        if type == "display":
            sink_str = "! nvdsosd name=nvosd ! nv3dsink name=sink sync=0 "
        elif type == "rtsp":
            sink_str = "! nvdsosd name=nvosd ! nvvideoconvert ! video/x-raw(memory:NVMM), format=I420 ! nvv4l2h264enc bitrate=2000000 ! rtph264pay ! udpsink name=sink host={} port=8554 sync=false async=false ".format(uri)
        elif type == "rtmp":
            sink_str = "! nvdsosd name=nvosd ! nvvideoconvert ! video/x-raw(memory:NVMM), format=I420 ! nvv4l2h264enc bitrate=2000000 ! h264parse ! flvmux streamable=1 ! rtmpsink name=sink location={} ".format(uri)

        self.sink_str = sink_str

    def create_pipeline(self):
        self.pipeline_str = ""
        for i in range(self.number_sources):
                self.pipeline_str += self.source_str[i]

        self.pipeline_str += "nvstreammux name=m width=1280 height=720 batch-size={} ! queue ".format(self.number_sources)
        # self.pipeline_str += "nvstreammux name=m width=1920 height=1080 batch-size=2 ! queue "
        self.pipeline_str += self.gie_str
        self.pipeline_str += self.tracker_str
        self.pipeline_str += self.tiler_str
        self.pipeline_str += self.sink_str

        print(self.pipeline_str)

        self.pipeline = Gst.parse_launch(self.pipeline_str)

        nvosd = self.pipeline.get_by_name("nvosd")
        nvosd_sinkpad = nvosd.get_static_pad("sink")
        nvosd_sinkpad.add_probe(Gst.PadProbeType.BUFFER, self.__osd_sink_pad_buffer_probe, 0)

        self.time_check_elm = self.pipeline.get_by_name("m")
        time_check_elm_pad = self.time_check_elm.get_static_pad("src")
        time_check_elm_pad.add_probe(Gst.PadProbeType.BUFFER, self.__time_check)

        dot_data = Gst.debug_bin_to_dot_data(self.pipeline, Gst.DebugGraphDetails.NON_DEFAULT_PARAMS )
        with open("pipeline.dot", 'w') as f:
            f.write(dot_data)

    def __time_check(self, sink, data):
        _, time = self.time_check_elm.query_position(Gst.Format.TIME)
        self._video_time = time/Gst.SECOND
        return Gst.PadProbeReturn.OK


    def __on_eos(self, bus, message):  
        self.__stop_pipeline()
    
    def __on_error(self, bus, message):
        self.__stop_pipeline()

    def __run_pipeline(self):
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos", self.__on_eos)
        bus.connect("message::error", self.__on_error)

        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop = GLib.MainLoop()
        try:
            self.loop.run()
        except:
            pass

    def set_draw_points(self, points):
        self.draw_points = points

    def set_target_func(self, target_func):
        self.target_func = target_func
    
    def set_text(self, text):
        self.text = text

    def __stop_pipeline(self): 
        self.pipeline.set_state(Gst.State.NULL)
        self.loop.quit()

    def __osd_sink_pad_buffer_probe(self, pad, info, u_data):
        self.frame_count += 1
        if self.frame_count >= 30:
            end_time = timecheck.time()
            self.fps = self.frame_count / (end_time - self.start_time)
            self.frame_count = 0
            self.start_time = end_time

        gst_buffer = info.get_buffer()
        if not gst_buffer:
            print("Unable to get GstBuffer ")
            return Gst.PadProbeReturn.OK

        # Retrieve batch metadata from the buffer
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        l_frame = batch_meta.frame_meta_list

        # print("time = {}".format(self._video_time))
        while l_frame is not None:
            try:
                # Get frame meta
                frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            except StopIteration:
                break

            # Get the frame number
            frame_number = frame_meta.frame_num
            l_obj = frame_meta.obj_meta_list
            while l_obj is not None:
                try:
                    # Get object meta
                    obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                except StopIteration:
                    break

                if obj_meta.class_id == 0:
                    # Draw bbox
                    obj_meta.rect_params.border_color.set(1.0, 0.0, 0.0, 1.0)
                    obj_meta.rect_params.border_width = 4
                    # print(f"Person {obj_meta.object_id} : {obj_meta.rect_params.left}, {obj_meta.rect_params.top} - {obj_meta.rect_params.width}, {obj_meta.rect_params.height}")
                    txt_params = obj_meta.text_params
                    txt_params.font_params.font_size = 30
                    txt_params.display_text = f"{obj_meta.object_id}"
                    
                    if self.target_func != None:
                        # x1, x2, y1, y2, id, time
                        x1 = obj_meta.rect_params.left
                        y1 = obj_meta.rect_params.top
                        x2 = x1 + obj_meta.rect_params.width
                        y2 = y1 + obj_meta.rect_params.height
                        id = obj_meta.object_id
                        time = self._video_time
                        
                        self.target_func(x1, y1, x2, y2, id, time)
                else:
                    # print(obj_meta.class_id)
                    obj_meta.rect_params.border_width = 0
                    txt_params = obj_meta.text_params
                    txt_params.display_text = ""
                try:
                    l_obj = l_obj.next
                except StopIteration:
                    break
            try:
                l_frame = l_frame.next
            except StopIteration:
                break
            # frame_data = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)

            display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            display_meta.num_labels = 1
            py_nvosd_text_params = display_meta.text_params[0]
            py_nvosd_text_params.display_text = "{}, FPS={:.1f} Current_time={:.1f}".format(self.text, round(self.fps, 1), round(self._video_time, 1))

            # Now set the offsets where the string should appear
            py_nvosd_text_params.x_offset = 10
            py_nvosd_text_params.y_offset = 12

            # Font , font-color and font-size
            py_nvosd_text_params.font_params.font_name = "Serif"
            py_nvosd_text_params.font_params.font_size = 10
            # set(red, green, blue, alpha); set to White
            py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

            # Text background color
            py_nvosd_text_params.set_bg_clr = 1
            # set(red, green, blue, alpha); set to Black
            py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
            # Using pyds.get_string() to get display_text as string
            # print(pyds.get_string(py_nvosd_text_params.display_text))

            if len(self.draw_points) > 0:
                display_meta.num_lines = len(self.draw_points)
                line_params = display_meta.line_params
                for i, point in enumerate(self.draw_points):
                    line_params[i].x1 = point[0]
                    line_params[i].y1 = point[1]
                    line_params[i].x2 = point[2]
                    line_params[i].y2 = point[3]
                    line_params[i].line_width = 4
                    line_params[i].line_color.set(0.0, 1.0, 0.0, 1.0)

            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        return Gst.PadProbeReturn.OK


def main():
    model_config_path = "/workspace/model/yolov8/config_infer_primary_yoloV8l.txt"
    # model_config_path = "/workspace/model/peoplenet/config_infer_primary_peoplenet.txt"
    tracker_config_path = "/workspace/model/tracker/dstracker_config.txt"
    
    tds_thread = TDSThread()
    # tds_thread.create_source_bin(0, "rtsp", "rtsp://192.168.7.10:8554/")
    tds_thread.create_source_bin(0, "file", "output.mp4")
    tds_thread.create_gie(model_config_path)
    tds_thread.create_tracker(tracker_config_path)
    # tds_thread.create_sink_bin("display")
    # tds_thread.create_sink_bin("rtsp", "192.168.45.140")
    tds_thread.create_sink_bin("rtmp", '"rtmp://tbond-lb.tlln.xyz/live/cctv live=1"')
    tds_thread.create_pipeline()

    tds_thread.start()
    try:
        tds_thread.join()
    except KeyboardInterrupt:
        tds_thread.stop()

if __name__ == '__main__':
    sys.exit(main())
