import json

# Load experiences
with open('data/training/experiences_00000.json') as f:
    data = json.load(f)

print(f"Battle ID: {data['battle_id']}")
print(f"Winner: {data['winner']}")
print(f"Total experiences recorded: {len(data['experiences'])}")
print("\nSample experience:")
print(json.dumps(data['experiences'][0], indent=2))
