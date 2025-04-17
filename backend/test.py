import json

# Example input
toolUseContent = {
    'completionId': 'e9e47924-d2af-4f60-abed-de32f82e9350',
    'content': '{"airpoints_number":"12345678"}',
    'contentId': 'af4e22b2-f33a-4bcd-81c9-aa92757b276b',
    'promptName': '19dd1db0-4fb0-4021-af98-2c2292680bc5',
    'role': 'TOOL',
    'sessionId': '31fab85f-fba9-4eb6-bdce-472862899afd',
    'toolName': 'userProfileSearch',
    'toolUseId': 'b57b27ac-b093-4e21-b082-a10e95bebc11'
}

# Assuming this is your class or module
class retrieve_user_profile:
    @staticmethod
    def search_booking_record(record_type, key_value):
        print(f"Searching by {record_type}: {key_value}")
        # Your actual implementation here

# Extract the content
content = json.loads(toolUseContent['content'])

# Determine the type and call the appropriate method
if 'booking_reference' in content:
    retrieve_user_profile.search_booking_record('booking', content['booking_reference'])
elif 'airpoints_number' in content:
    retrieve_user_profile.search_booking_record('airpoints', content['airpoints_number'])
else:
    print("Error: No valid key found in content.")
