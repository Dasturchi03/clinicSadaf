import json
from datetime import datetime, timedelta

# Load the JSON data from the file
with open('data.json', 'r') as file:
    data = json.load(file)

# Loop through each reservation object
for reservation in data:
    # Convert reservation_time to datetime object
    reservation_start_time = datetime.strptime(reservation['fields']['reservation_time'], '%H:%M:%S')

    # Calculate end time by adding 1 hour
    reservation_end_time = reservation_start_time + timedelta(hours=1)

    # Update keys
    reservation['fields']['reservation_start_time'] = reservation_start_time.strftime('%H:%M:%S')
    reservation['fields']['reservation_end_time'] = reservation_end_time.strftime('%H:%M:%S')

    # Remove the old key
    del reservation['fields']['reservation_time']

# Save the modified data to a new file
with open('data.json', 'w') as file:
    json.dump(data, file, indent=2)
