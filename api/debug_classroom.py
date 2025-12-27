from configs import dify_config
from services.feature_service import FeatureService

print("--- DEBUGGING CLASSROOM MODE ---")
print(f"ENV CLASSROOM_MODE: {dify_config.CLASSROOM_MODE}")
print(f"ENV CLASSROOM_TEACHERS: {dify_config.CLASSROOM_TEACHERS}")

sys_features = FeatureService.get_system_features()
print(f"SystemFeature.classroom_mode: {sys_features.classroom_mode}")
print(f"SystemFeature.classroom_teachers: {sys_features.classroom_teachers}")
print("--- END DEBUG ---")
