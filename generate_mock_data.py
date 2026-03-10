import pandas as pd
import numpy as np

np.random.seed(42)

n_subjects = 200

# Demographic variables
gender = np.random.choice(['Male', 'Female'], n_subjects, p=[0.45, 0.55])
age = np.random.normal(loc=22, scale=3, size=n_subjects).round().astype(int)
education = np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], n_subjects, p=[0.1, 0.6, 0.2, 0.1])

# Independent Variable (e.g., ad type)
ad_type = np.random.choice(['Control (Text)', 'Treatment (Image)', 'Treatment (Video)'], n_subjects)

# Covariate
baseline_stress = np.random.normal(loc=50, scale=10, size=n_subjects).round(2)

# Manipulation Check (e.g., perceived visual appeal)
visual_appeal = np.where(ad_type == 'Control (Text)', np.random.normal(loc=3, scale=1, size=n_subjects), 
                np.where(ad_type == 'Treatment (Image)', np.random.normal(loc=4.5, scale=1, size=n_subjects), 
                         np.random.normal(loc=5.5, scale=1, size=n_subjects)))
visual_appeal = np.clip(visual_appeal, 1, 7).round(1)

# Mediator (e.g., positive emotion)
positive_emotion = 0.5 * visual_appeal + np.random.normal(loc=1, scale=0.5, size=n_subjects)
positive_emotion = np.clip(positive_emotion, 1, 7).round(1)

# Moderator (e.g., product involvement)
product_involvement = np.random.choice(['Low', 'High'], n_subjects)

# Dependent Variable
base_intent = 2.0
ad_effect_val = np.where(ad_type == 'Treatment (Video)', 1.5, np.where(ad_type == 'Treatment (Image)', 0.8, 0))
med_effect = 0.6 * positive_emotion
mod_effect = np.where(product_involvement == 'High', 1.2 * ad_effect_val, 0.5 * ad_effect_val)
cov_effect = -0.05 * baseline_stress

purchase_intent = base_intent + mod_effect + med_effect + cov_effect + np.random.normal(loc=0, scale=0.8, size=n_subjects)
purchase_intent = np.clip(purchase_intent, 1, 10).round(1)

# Attention Check & Response Time (for data cleaning feature)
response_time_sec = np.random.exponential(scale=120, size=n_subjects).round(0)
response_time_sec = np.clip(response_time_sec, 10, 600)
attention_check = np.random.choice([1, 1, 1, 1, 0], n_subjects)  # 80% correct

# Scale items for CFA/AVE/CR testing (3 items measuring same latent factor)
latent_factor = np.random.normal(0, 1, n_subjects)
Scale_Q1 = (latent_factor * 0.8 + np.random.normal(2, 0.5, n_subjects)).round(1)
Scale_Q2 = (latent_factor * 0.7 + np.random.normal(2, 0.6, n_subjects)).round(1)
Scale_Q3 = (latent_factor * 0.9 + np.random.normal(2, 0.4, n_subjects)).round(1)
Scale_Q4 = (latent_factor * 0.6 + np.random.normal(2, 0.7, n_subjects)).round(1)

df = pd.DataFrame({
    'Participant_ID': range(1, n_subjects + 1),
    'Gender': gender,
    'Age': age,
    'Education': education,
    'Response_Time_Sec': response_time_sec,
    'Attention_Check': attention_check,
    'Ad_Type_IV': ad_type,
    'Visual_Appeal_ManCheck': visual_appeal,
    'Baseline_Stress_Covariate': baseline_stress,
    'Positive_Emotion_M': positive_emotion,
    'Product_Involvement_Mod': product_involvement,
    'Purchase_Intent_DV': purchase_intent,
    'Scale_Q1': Scale_Q1,
    'Scale_Q2': Scale_Q2,
    'Scale_Q3': Scale_Q3,
    'Scale_Q4': Scale_Q4,
})

df.to_csv('mock_data.csv', index=False)
print(f"Generated {n_subjects} rows of mock data with {df.shape[1]} columns in mock_data.csv.")

