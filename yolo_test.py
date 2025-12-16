from ultralytics import YOLO

model = YOLO('models/yolo11m.pt')

results  = model.predict('VideoData/test (13).mp4', save = True)

print(results[0])
print('==============================')
for box in results[0].boxes:
    print(box)