from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import time
import datetime

# Setup
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.body.write',
    'https://www.googleapis.com/auth/fitness.activity.write',
    'https://www.googleapis.com/auth/fitness.location.read'
]


# Load OAuth credentials
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)
service = build('fitness', 'v1', credentials=creds)

# Get step count from past hour
now = int(time.time() * 1e9)
one_hour_ago = now - int(3600 * 1e9)
dataset = f"{one_hour_ago}-{now}"

response = service.users().dataSources().datasets().get(
    userId='me',
    dataSourceId='derived:com.google.step_count.delta:com.google.android.gms:merge_step_deltas',
    datasetId=dataset
).execute()

total_steps = 0
for point in response.get("point", []):
    total_steps += point['value'][0]['intVal']

print("🦶 Steps in last hour:", total_steps)

# Emotion Detection Logic
if total_steps > 1500:
    emotion = "Overactive 😓"
    tip = "Slow down a bit, give your body a break."
elif total_steps < 100:
    emotion = "Fatigued 💤"
    tip = "Your body needs movement, try walking!"
else:
    emotion = "Balanced 😊"
    tip = "You're doing great today, keep going 💖"

print(f"\n🧠 Emotion: {emotion}\n💬 Tip: {tip}")
