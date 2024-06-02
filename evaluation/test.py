import json
import time
import ollama


file_path = "test.json"

with open(file_path, "r") as file:
    data = json.load(file)

total_time_elapsed = 0
for index, obj in enumerate(data):
    start_time = time.time()
    print(f"Processing object with id: {obj['id']} at index: {index}")

    prompt = f"""
    Give one line summary of following conversation. Only give summary without anything else.

    ```{obj["dialogue"]}```
    """
    response = ollama.chat(
        model="phi3",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    end_time = time.time() - start_time
    total_time_elapsed += end_time

    obj["model_response"] = response["message"]["content"]
    obj["time_elapsed"] = end_time

    running_average = total_time_elapsed / (index + 1)
    print(f"time_elapsed: {end_time}, running_average: {running_average}")
    # time.sleep(2)

output_file_path = "test_response_phi.json"
with open(output_file_path, "w") as file:
    json.dump(data, file, indent=4)

print("Updated JSON file with 'model_response' field.")
