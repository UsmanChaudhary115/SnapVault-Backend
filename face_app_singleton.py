from insightface.app import FaceAnalysis

face_app = FaceAnalysis(name='buffalo_l', root='./AI Models', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0)