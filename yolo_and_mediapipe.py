import cv2
import argparse
import numpy as np
import mediapipe as mp

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--image', required=False,
                help='path to input image', default='/Users/jana/Documents/GitHub/AS2-MLC-Project/sample/original.jpg')
ap.add_argument('-c', '--config', required=False,
                help='path to yolo config file', default='/Users/jana/Documents/GitHub/AS2-MLC-Project/yolov3.cfg')
ap.add_argument('-w', '--weights', required=False,
                help='path to yolo pre-trained weights', default='/Users/jana/Documents/GitHub/AS2-MLC-Project/yolov3.weights')
ap.add_argument('-cl', '--classes', required=False,
                help='path to text file containing class names', default='/Users/jana/Documents/GitHub/AS2-MLC-Project/yolov3.txt')
args = ap.parse_args()


def pose_mediapipe(image, segmentation):
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_pose = mp.solutions.pose
    BG_COLOR = (192, 192, 192)  # gray
    with mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=segmentation,
            min_detection_confidence=0.5) as pose:

        image_height, image_width, _ = image.shape
        # Convert the BGR image to RGB before processing.
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        annotated_image = image.copy()
        # Draw segmentation on the image.
        if segmentation:
            condition = np.stack(
                (results.segmentation_mask,) * 3, axis=-1) > 0.1
            bg_image = np.zeros(image.shape, dtype=np.uint8)
            bg_image[:] = BG_COLOR
            annotated_image = np.where(condition, annotated_image, bg_image)
        # Draw pose landmarks on the image.
        mp_drawing.draw_landmarks(
            annotated_image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
        return annotated_image


def get_output_layers(net):

    layer_names = net.getLayerNames()

    output_layers = [layer_names[i - 1]
                     for i in net.getUnconnectedOutLayers()]

    return output_layers


def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = str(classes[class_id])
    color = COLORS[class_id]
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
    cv2.putText(img, label, (x-10, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


image = cv2.imread(args.image)

Width = image.shape[1]
Height = image.shape[0]
scale = 0.00392

classes = None

with open(args.classes, 'r') as f:
    classes = [line.strip() for line in f.readlines()]

COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

net = cv2.dnn.readNet(args.weights, args.config)
blob = cv2.dnn.blobFromImage(
    image, scale, (416, 416), (0, 0, 0), True, crop=False)
net.setInput(blob)
outs = net.forward(get_output_layers(net))
class_ids = []
confidences = []
boxes = []
conf_threshold = 0.5
nms_threshold = 0.4

for out in outs:
    for detection in out:
        scores = detection[5:]
        class_id = np.argmax(scores)
        confidence = scores[class_id]
        if confidence > 0.5:
            center_x = int(detection[0] * Width)
            center_y = int(detection[1] * Height)
            w = int(detection[2] * Width)
            h = int(detection[3] * Height)
            x = center_x - w / 2
            y = center_y - h / 2
            class_ids.append(class_id)
            confidences.append(float(confidence))
            boxes.append([x, y, w, h])

indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

for i in indices:
    i = i
    box = boxes[i]
    x = box[0]
    y = box[1]
    w = box[2]
    h = box[3]
    draw_prediction(image, class_ids[i], confidences[i], round(
        x), round(y), round(x+w), round(y+h))
    if class_ids[i] == 'person':
        pose_mediapipe(image, segmentation=False)

cv2.imshow("object detection", image)
cv2.waitKey()

cv2.imwrite("sample/yolo.jpg", image)
cv2.destroyAllWindows()
