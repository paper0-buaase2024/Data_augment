import json
import time

import requests
import json
from tqdm import tqdm
import openai
import os
import qianfan

import requests
import json

QIANFAN_ACCESS_KEY = "IGrCD1JQf1nd3eEHfceFtG9t"
QIANFAN_SECRET_KEY = "L3LkYBd9yTtyn4TXv2A9wtbWWAvweMKP"

def get_access_token():
    """
    使用 API Key，Secret Key 获取access_token，替换下列示例中的应用API Key、应用Secret Key
    """
        
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={QIANFAN_ACCESS_KEY}&client_secret={QIANFAN_SECRET_KEY}"
    
    payload = json.dumps("")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json().get("access_token")

def ask_qianfan(payload):
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/llama_3_8b?access_token=" + get_access_token()
    
    payload = json.dumps(payload)
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

device = 'cuda'
OPENROUTER_API_KEY = "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"


os.environ["QIANFAN_ACCESS_KEY"] = "IGrCD1JQf1nd3eEHfceFtG9t"
os.environ["QIANFAN_SECRET_KEY"] = "L3LkYBd9yTtyn4TXv2A9wtbWWAvweMKP"


chat_comp = qianfan.ChatCompletion()


OPENAI_API = 'http://172.17.62.88:8010/v1'
OPENAI_KEY = 'none'

openai.api_base = OPENAI_API
openai.api_key = OPENAI_KEY

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def sliding_window_sampling(data, window_size):
    window_size = min(window_size, len(data))
    for i in range(int(len(data) / window_size)):
        window = data[i * window_size: (i + 1) * window_size]
        yield window


file_path = 'cscl_selected23.json'
output_path = './cscl_augmented_sele.json'
data = load_json(file_path)
print("json loaded!")
instrcut = "\nPlease generate a review report according to the content above, including the introduction, problem solving strategies, summary and outlook with the format of **Introduction**\n content\n **Problem solving strategies**\n content\n**Outlook**\n content"
window_size = 5

augmented_text = []

print(f"Sampling with window size {window_size}:")

with open(output_path, 'a') as file:  # Open the file in append mode
    pbar = tqdm(total=int(len(data) / window_size))
    start_from = 14  # Start from the beginning

    for idx, window in enumerate(sliding_window_sampling(data[start_from * window_size:], window_size)):
        prompt = "Now there are some papers in the field of computer science and natural language.\n\n"
        for i in range(window_size):
            s1 = window[i]['title'].replace('\n', ' ')
            s2 = window[i]['abstract'].replace('\n', ' ')
            prompt += f"Title:{s1}\nAbstract:{s2}\n"
        prompt += instrcut
        # print(prompt)
        # exit()

        try:
            # response = requests.post(
            #     url="https://openrouter.ai/api/v1/chat/completions",
            #     headers={
            #         "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            #     },
            #     data=json.dumps({
            #         "model": "mistralai/mistral-7b-instruct:free",
            #         "messages": [
            #             {"role": "user", "content": prompt}
            #         ]
            #     })
            # )
            messages = [
                        {"role": "user", "content": prompt}
                    ]
            
            response = ask_qianfan({ 'messages': messages})
            # response = openai.ChatCompletion.create(
            #         model='Qwen',
            #         messages=messages)
            # response.raise_for_status()  # Check response status code
            print(response, idx+start_from)
            # exit()
            new_item = {
                'prompt': prompt,
                'response': response['result']
            }
            # time.sleep(1)
        except requests.exceptions.RequestException as e:
            print(f"Error on window {idx}: {e}")
            continue  # Skip the current iteration and continue with the next window
        except openai.error.APIError as e:
            print(f"Error during request {idx}: {e}")
            continue
        json.dump(new_item, file)
        file.write('\n')
        file.flush()
        pbar.update()

    pbar.close()