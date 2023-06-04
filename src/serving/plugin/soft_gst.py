"""
  Trueno Soft Gstreamer Pipeline

  Contact: arthur.r.song@gmail.com
"""

import logging

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import numpy as np

from serving.core import debug

def get_gst_pipeline(configs):
    if configs.get('address') is None:
        return None
    logging.debug("load SoftCPUGst Pipeline w/ %s", configs['address'])
    return SoftCPUGst(address=configs['address'])

class SoftCPUGst():
    """Soft CPU Gst
    """
    @debug.flow("SoftCPUGst::__init__")
    def __init__(self, address=""):
        Gst.init(None)

        self.address = address
        self._frame = None

        # RTSP video URL
        self.video_source = 'rtspsrc location={} latency=0'.format(self.address)
        # Cam -> CSI-2 -> H264 Raw (YUV 4-4-4 (12bits) I420)
        self.video_codec = '! rtph264depay ! h264parse ! avdec_h264'
        # Python don't have nibble, convert YUV nibbles (4-4-4) to OpenCV standard BGR bytes (8-8-8)
        self.video_decode = '! decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert'
        # Create a sink to get data
        self.video_sink_conf = '! appsink emit-signals=true sync=false max-buffers=2 drop=true'
        self.video_pipe = None
        self.video_sink = None

    @staticmethod
    def sample_to_opencv(sample):
        buf = sample.get_buffer()
        caps = sample.get_caps()
        return np.ndarray(
            (
                caps.get_structure(0).get_value('height'),
                caps.get_structure(0).get_value('width'),
                3
            ), buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)

    def frame(self):
        return self._frame

    def available(self):
        #logging.debug("availabe frame idx: %s", id(self._frame))
        return self._frame is not None

    @debug.flow("SoftCPUGst::run")
    def run(self):
        gst_command = ' '.join([
            self.video_source,
            self.video_codec,
            self.video_decode,
            self.video_sink_conf
        ])
        self.video_pipe = Gst.parse_launch(gst_command)
        self.video_pipe.set_state(Gst.State.PLAYING)
        self.video_sink = self.video_pipe.get_by_name('appsink0')
        self.video_sink.connect('new-sample', self._callback)

    def _callback(self, sink):
        sample = sink.emit('pull-sample')
        new_frame = self.sample_to_opencv(sample)
        self._frame = new_frame
        #logging.debug("callback frame idx: %s", id(self._frame))
        return Gst.FlowReturn.OK
