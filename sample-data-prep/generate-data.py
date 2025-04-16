import pandas as pd
import json
import random 
import string
from datetime import datetime, timedelta

# Load the original CSV file
file_path = "results.csv"
df = pd.read_csv(file_path)

# Helper functions
def generate_unique_booking_ref(existing_refs):
    while True:
        ref = ''.join(random.choices(string.ascii_uppercase, k=5))
        if ref not in existing_refs:
            existing_refs.add(ref)
            return ref

def get_random_time():
    random_time = datetime.strptime("05:00", "%H:%M") + timedelta(minutes=random.randint(0, 1080))
    return random_time.strftime("%H:%M")

departure_airports = ["AKL", "SYD", "MEL", "WLG", "CHC", "BNE", "PER", "ADL"]

def get_random_airport_pair():
    dep, arr = random.sample(departure_airports, 2)
    return dep, arr

# Process data
updated_upcoming_travel = []
all_refs = set()

for travel_str in df["upcomingTravel"]:
    try:
        travel_data = json.loads(travel_str.replace("'", "\""))  # Clean up quotes
        updated_entries = []

        for entry in travel_data:
            # Generate unique booking ref and airports
            new_ref = generate_unique_booking_ref(all_refs)
            dep, arr = get_random_airport_pair()

            # Set values
            entry["M"]["bookingReference"]["S"] = new_ref
            entry["M"]["departureAirport"]["S"] = dep
            entry["M"]["arrivalAirport"]["S"] = arr
            entry["M"]["departureTime"] = {"S": get_random_time()}

            # Parse and preserve original date
            departure_date_str = entry["M"]["departureDate"]["S"]
            departure_date = datetime.strptime(departure_date_str, "%Y-%m-%d")

            updated_entries.append(entry)

            # Create return journey
            return_entry = {
                "M": {
                    "bookingReference": {"S": generate_unique_booking_ref(all_refs)},
                    "departureDate": {"S": (departure_date + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")},
                    "departureAirport": {"S": arr},
                    "arrivalAirport": {"S": dep},
                    "seatNumber": {"S": f"{random.randint(10, 30)}{random.choice(['A', 'B', 'C'])}"},
                    "flightNumber": {"S": f"NZ{random.randint(100, 999)}"},
                    "departureTime": {"S": get_random_time()}
                }
            }
            updated_entries.append(return_entry)

        updated_upcoming_travel.append(json.dumps(updated_entries))

    except Exception as e:
        updated_upcoming_travel.append(travel_str)
        print(f"Error: {e}")

# Update and save
df["upcomingTravel"] = updated_upcoming_travel
final_output_path = "final_updated_results_with_returns.csv"
df.to_csv(final_output_path, index=False)

print(f"✅ Updated CSV with return journeys saved to {final_output_path}")
