import pandas as pd
import json
import os
import shutil
from sklearn.model_selection import train_test_split

# configuration
CSV_FILE = 'annotations.csv'
SOURCE_IMG_DIR = 'raw_images'
OUTPUT_DIR = 'datasets'

# class mapping
class_map = {
    "maggi": 0,
    "Jim_jam": 1,
    "dairy_milk": 2,
    "pears_soap": 3,
    "plain_bhujia": 4
}

def convert_to_yolo(x, y, w, h):
    return ((x + w / 2) / 100, (y + h / 2) / 100, w / 100, h / 100)

def process_data():
    # 1. Setup Directories
    if os.path.exists(OUTPUT_DIR): shutil.rmtree(OUTPUT_DIR)
    for split in ['train', 'val']:
        os.makedirs(f"{OUTPUT_DIR}/images/{split}", exist_ok=True)
        os.makedirs(f"{OUTPUT_DIR}/labels/{split}", exist_ok=True)

    # 2. Get list of ACTUAL files in your folder
    if not os.path.exists(SOURCE_IMG_DIR):
        print(f"Error: '{SOURCE_IMG_DIR}' folder is missing!")
        return

    local_files = [f for f in os.listdir(SOURCE_IMG_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.JPG'))]
    print(f"Found {len(local_files)} images in '{SOURCE_IMG_DIR}' folder.")

    df = pd.read_csv(CSV_FILE)
    valid_entries = []

    print("Parsing CSV and matching filenames...")
    
    # Create a dictionary of annotations from CSV for faster lookup
    csv_annotations = {}
    for index, row in df.iterrows():
        csv_filename = row['image'].split('/')[-1]
        csv_annotations[csv_filename] = json.loads(row['label'])

    # Iterate over ALL local files (This includes your new background images!)
    for local_f in local_files:
        yolo_lines = []
        
        # Find if this local file has annotations in the CSV
        matched_csv_key = next((k for k in csv_annotations.keys() if local_f in k), None)
        
        if matched_csv_key:
            labels = csv_annotations[matched_csv_key]
            for label in labels:
                if 'rectanglelabels' not in label: continue
                class_name = label['rectanglelabels'][0]
                
                if class_name in class_map:
                    cid = class_map[class_name]
                    cx, cy, nw, nh = convert_to_yolo(label['x'], label['y'], label['width'], label['height'])
                    yolo_lines.append(f"{cid} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        # APPEND REGARDLESS OF LABELS! 
        # If yolo_lines is empty, YOLO treats it as a Background/Negative image.
        valid_entries.append({
            'src_path': os.path.join(SOURCE_IMG_DIR, local_f),
            'filename': local_f,
            'labels': yolo_lines
        })

    print(f"Successfully processed {len(valid_entries)} images (including background images).")

    if len(valid_entries) == 0:
        print("CRITICAL: No images matched! Check if your 'raw_images' folder is empty.")
        return

    # Split and Save
    train, val = train_test_split(valid_entries, test_size=0.2, random_state=42)
    
    def save_split(data, split):
        for item in data:
            shutil.copy(item['src_path'], f"{OUTPUT_DIR}/images/{split}/{item['filename']}")
            txt_name = item['filename'].rsplit('.', 1)[0] + ".txt"
            with open(f"{OUTPUT_DIR}/labels/{split}/{txt_name}", 'w') as f:
                f.write("\n".join(item['labels']))

    save_split(train, 'train')
    save_split(val, 'val')

    # Create YAML (No changes needed here, nc remains 5)
    yaml_content = f"path: ../{OUTPUT_DIR}\ntrain: images/train\nval: images/val\nnc: {len(class_map)}\nnames: {list(class_map.keys())}"
    with open('data.yaml', 'w') as f:
        f.write(yaml_content)
    
    print("Data parsing complete! Now run 'python train_yolo.py'")

if __name__ == "__main__":
    process_data()