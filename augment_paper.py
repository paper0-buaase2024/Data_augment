import json
import time

import requests
import json
from tqdm import tqdm

device = 'cuda'
OPENROUTER_API_KEY = "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"


def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def sliding_window_sampling(data, window_size):
    window_size = min(window_size, len(data))
    for i in range(int(len(data) / window_size)):
        window = data[i * window_size: (i + 1) * window_size]
        yield window


file_path = 'cscl_organized.json'
output_path = './cscl_augmented.json'
data = load_json(file_path)
print("json loaded!")
instrcut = "\nPlease generate a review report according to the above content, including the introduction, problem solving strategies, summary and outlook with the format of **Introduction**\n content\n **Problem solving strategies**\n content\n**Outlook**\n content"
window_size = 5

augmented_text = []

print(f"Sampling with window size {window_size}:")

with open(output_path, 'a') as file:  # Open the file in append mode
    pbar = tqdm(total=int(len(data) / window_size))
    start_from = 0  # Start from the beginning

    for idx, window in enumerate(sliding_window_sampling(data[500:], window_size)):
        prompt = "Now there are some papers in the field of computer science and natural language.\n\n"
        for i in range(window_size):
            prompt += f"{window[i]['prompt']}\n{window[i]['response']}\n"
        prompt += instrcut

        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                },
                data=json.dumps({
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                })
            )
            response.raise_for_status()  # Check response status code
            new_item = {
                'prompt': prompt,
                'response': response.json()['choices'][0]['message']['content']
            }
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            print(f"Error on window {idx}: {e}")
            continue  # Skip the current iteration and continue with the next window

        json.dump(new_item, file)
        file.write('\n')
        file.flush()
        pbar.update()

    pbar.close()