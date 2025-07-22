# import os
# import glob
# import cv2
# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity
# from insightface.app import FaceAnalysis
# import matplotlib.pyplot as plt

# # Setup insightface model (CPU only)
# face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
# face_app.prepare(ctx_id=0)

# # Path to folder with known faces
# photos_folder = r"D:\SnapVault-Backend\uploads\photos"
# query_path = r"D:\SnapVault-Backend\uploads\profile_pictures\a4bf17ae-9330-434c-b727-4c3ff234720c.png"

# # Load and embed all images in folder
# database = []
# for img_path in glob.glob(os.path.join(photos_folder, "*.[jJpP]*[gG]")):
#     img = cv2.imread(img_path)
#     faces = face_app.get(img)

#     for face in faces:
#         database.append({
#             'embedding': face.embedding,
#             'img_path': img_path,
#             'bbox': face.bbox.astype(int)
#         })
#         print(f"Found face in: {os.path.basename(img_path)}")

# # Embed query image
# query_img = cv2.imread(query_path)
# query_faces = face_app.get(query_img)

# if not query_faces:
#     print("No face detected in query.")
# else:
#     query_embedding = query_faces[0].embedding
#     print("Query face embedding extracted.")

#     # Compare and find best match
#     similarities = []
#     for record in database:
#         score = cosine_similarity([query_embedding], [record['embedding']])[0][0]
#         similarities.append((score, record))
#         print(f"{os.path.basename(record['img_path'])}: {score:.4f}")

#     # Get best match
#     best_match = max(similarities, key=lambda x: x[0])[1]

#     # Draw box
#     img = cv2.cvtColor(cv2.imread(best_match['img_path']), cv2.COLOR_BGR2RGB)
#     plt.imshow(img)
#     x1, y1, x2, y2 = best_match['bbox']
#     plt.gca().add_patch(plt.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor='red', linewidth=2))
#     plt.title(f"Best Match: {os.path.basename(best_match['img_path'])}")
#     plt.axis('off')
#     plt.show()


import os
import glob
import shutil
import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from insightface.app import FaceAnalysis

# Setup insightface model (CPU only)
face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0)

# Paths
photos_folder = r"D:\SnapVault-Backend\uploads\photos"
query_path = r"D:\SnapVault-Backend\uploads\profile_pictures\a4bf17ae-9330-434c-b727-4c3ff234720c.png"
THRESHOLD = 0.6

# Step 1: Embed all faces from photos folder
database = []
for img_path in glob.glob(os.path.join(photos_folder, "*.[jJpP]*[gG]")):
    img = cv2.imread(img_path)
    faces = face_app.get(img)

    for face in faces:
        database.append({
            'embedding': face.embedding,
            'img_path': img_path
        }) 

# Step 2: Embed query image
query_img = cv2.imread(query_path)
query_faces = face_app.get(query_img)

if not query_faces:
    print("No face detected in query image.")
else:
    query_embedding = query_faces[0].embedding
    print("\nQuery face embedding extracted.\n")

    # Step 3: Compare to database and print all above threshold
    for record in database:
        score = cosine_similarity([query_embedding], [record['embedding']])[0][0]
        if score >= THRESHOLD:
            print(f"Match: {os.path.basename(record['img_path'])} | Similarity: {score:.4f}")
            # Create a new folder for matched images
            matched_folder = os.path.join(photos_folder, "matched_images")
            if not os.path.exists(matched_folder):
                os.makedirs(matched_folder)

            # Copy matching image to matched folder
            img_name = os.path.basename(record['img_path'])
            dst_path = os.path.join(matched_folder, img_name)
            shutil.copy2(record['img_path'], dst_path)
            print(f"  Copied to: {dst_path}")
