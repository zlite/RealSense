import pyrealsense2 as rs
import numpy as np
import transformations as tf
import math
import csv
import sys
import time
sys.path.append('../')

datalog_file = 'unitdata.csv'
initial_time = time.time()
# Declare RealSense pipeline, encapsulating the actual device and sensors
pipe = rs.pipeline()
H_aeroRef_T265Ref = np.array([[0,0,-1,0],[1,0,0,0],[0,-1,0,0],[0,0,0,1]])
H_T265body_aeroBody = np.linalg.inv(H_aeroRef_T265Ref)

# Build config object and request pose data
cfg = rs.config()
cfg.enable_stream(rs.stream.pose)

# Start streaming with requested config
pipe.start(cfg)

with open(datalog_file, 'w') as csvfile:  # overwrite original file
    recordwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
    recordwriter.writerow(["Time", "Frame", "X", "Y", "Heading"])


def get_heading(data):  # this is essentially magic ;-)
    H_T265Ref_T265body = tf.quaternion_matrix([data.rotation.w, data.rotation.x,data.rotation.y,data.rotation.z]) # in transformations, Quaternions w+ix+jy+kz are represented as [w, x, y, z]!
    # transform to aeronautic coordinates (body AND reference frame!)
    H_aeroRef_aeroBody = H_aeroRef_T265Ref.dot(H_T265Ref_T265body.dot( H_T265body_aeroBody ))
    rpy_rad = np.array(tf.euler_from_matrix(H_aeroRef_aeroBody, 'rxyz') )
    heading = rpy_rad[2]
    return heading

def save_datalog():
    with open(datalog_file, 'a') as csvfile:  # append to file
        recordwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        recordwriter.writerow([elapsed_time,pose.frame_number,round(x,2), round(y,2),round(heading,2)])

try:
    while True:
        frames = pipe.wait_for_frames()
        pose = frames.get_pose_frame()
        if pose:
            data = pose.get_pose_data()
            x = data.translation.x
            y = -1.000 * data.translation.z # don't ask me why, but in "VR space", y is z and it's reversed
            heading = get_heading(data)
            print("Frame #{}".format(pose.frame_number))
            print("data x", round(x,2), "y", round(y,2))
            print("heading", round(heading,2))
            elapsed_time = time.time() - initial_time
            save_datalog()
            time.sleep(0.1)

except KeyboardInterrupt:
	pipe.stop()
