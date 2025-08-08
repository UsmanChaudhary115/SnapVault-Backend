import os
from sqlalchemy.orm import Session
import numpy as np
import json, cv2
from sklearn.metrics.pairwise import cosine_similarity
from database import SessionLocal  
from models import Photo, Face, PhotoFace  
from constants import HIGHLIGHT_THRESHOLD, SIMILARITY_THRESHOLD 
from utils.highlight_utils import evaluate_image_quality 
from insightface.app import FaceAnalysis



face_app = FaceAnalysis(name='buffalo_l', root='./AI Models', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0) 

def process_faces(photo_id: int, img_bytes: bytes, group_id: int, db_session_maker=SessionLocal):
    db: Session = db_session_maker()
    try:
        # Convert image bytes to numpy image
        img_np = np.asarray(bytearray(img_bytes), dtype=np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        # Detect faces
        faces = face_app.get(img)

        if not faces or len(faces) == 0:
            # No faces → update photo with isHighlighted = False
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                photo.isHighlighted = False
                db.commit()
            return

        # Evaluate image quality score
        score = evaluate_image_quality(faces, img)
        highlight_status = (score >= HIGHLIGHT_THRESHOLD)

        # Update isHighlighted
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.isHighlighted = highlight_status
            db.commit()
        else:
            return  # Exit if photo not found

        # Face matching logic
        all_faces = db.query(Face).all()

        for face in faces:
            embedding = face.embedding  # numpy array

            found_match = False
            for existing in all_faces:
                existing_embedding = np.array(json.loads(existing.embedding), dtype=np.float32)
                sim = cosine_similarity([embedding], [existing_embedding])[0][0]

                if sim >= SIMILARITY_THRESHOLD:
                    # Average the embeddings
                    new_embedding = (embedding + existing_embedding) / 2
                    existing.embedding = json.dumps(new_embedding.tolist())
                    existing.embedding_count += 1
                    db.commit()

                    # Link face to photo
                    association = PhotoFace(photo_id=photo.id, face_id=existing.id)
                    db.add(association)
                    db.commit()
                    found_match = True
                    break

            if not found_match:
                # New face record
                new_face = Face(
                    user_id=None,
                    embedding=json.dumps(embedding.tolist())
                )
                db.add(new_face)
                db.commit()
                db.refresh(new_face)

                # Link new face with current photo
                association = PhotoFace(photo_id=photo.id, face_id=new_face.id)
                db.add(association)
                db.commit()

    except Exception as e:
        # You can log this
        print(f"[process_faces] Error: {e}")
    finally:
        db.close()