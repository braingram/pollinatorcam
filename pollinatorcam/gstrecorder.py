import os
import time
import threading

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject


url_string = "rtsp://{user}:{password}@{ip}:554/cam/realmonitor?channel=1&subtype=0"


cmd_string = (
    'rtspsrc location="{url}" !'
    'queue min-threshold-time=1000000000 !'
    'valve name=valve !'
    'rtph265depay !'
    'h265parse !'
    'mp4mux !'
    'filesink name=sink location=test.mp4')


class Recorder(threading.Thread):
    _inited = False
    def __init__(self, *args, **kwargs):
        ip = kwargs.pop('ip')
        filename = kwargs.pop('filename')
        if 'user' in kwargs:
            user = kwargs.pop('user')
        else:
            user = os.environ['PCAM_USER']
        if 'password' in kwargs:
            password = kargs.pop('password')
        else:
            password = os.environ['PCAM_PASSWORD']
        super(Recorder, self).__init__(*args, **kwargs)

        if not self._inited or not Gst.is_initialized():
            Gst.init([])
            self._inited = True

        url = url_string.format(user=user, password=password, ip=ip)
        cmd = cmd_string.format(url=url)
        self.pipeline = Gst.parse_launch(cmd)

        self.valve = self.pipeline.get_child_by_name("valve")
        self.valve.set_property('drop', True)
        self.sink = self.pipeline.get_child_by_name("sink")
        self.sink.set_property('location', filename)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        self.start_time = None
        self.recording = False

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.pipeline.set_state(Gst.State.NULL)
            print("!!! End of stream !!!")
            self.playmode = False
            self.loop.quit()
        elif t == Gst.MessageType.ERROR:
            self.pipeline.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Error: %s[%s]" % (err, debug))
            self.playmode = False
            self.loop.quit()

    def start_recording(self):
        print("Starting recording")
        #self.sink.set_property('location', filename)
        self.start_time = time.monotonic()
        self.valve.set_property('drop', False)
        self.recording = True

    def stop_recording(self, and_join=True):
        self.pipeline.send_event(Gst.Event.new_eos())
        self.recording = False
        if and_join:
            self.join()

    def run(self):
        self.playmode = True
        self.loop = GLib.MainLoop()
        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop.run()
        self.playmode = False


def test_recorder(ip='192.168.0.4'):
    # create recorder instance
    r = Recorder(filename='test_file.mp4', ip=ip)
    # start running (begins filling circular buffer)
    r.start()
    time.sleep(1)  # wait a bit

    # start actually recording (frames will be delayed by buffer)
    r.start_recording()
    time.sleep(3)
    # stop recording and join started thread
    r.stop_recording(and_join=False)
    # can the instance be re-used

    t0 = time.monotonic()
    r.join()
    t1 = time.monotonic()
    print("Joining took: %s" % (t1 - t0))
    time.sleep(2)
    r = Recorder(filename='test_file2.mp4', ip=ip)
    r.start()
    time.sleep(1)
    r.start_recording()
    time.sleep(3)
    r.stop_recording(and_join=False)
    t0 = time.monotonic()
    r.join()
    t1 = time.monotonic()
    print("Joining took: %s" % (t1 - t0))
    #loop.quit()


if __name__ == '__main__':
    test_recorder()
