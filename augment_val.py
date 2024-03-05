import os
from typing import Literal

import instructor

from datasets import load_dataset, Dataset
from dotenv import load_dotenv
from instructor.patch import wrap_chatcompletion
from litellm import completion
from pydantic import BaseModel

load_dotenv()

completion = wrap_chatcompletion(completion, mode=instructor.Mode.MD_JSON)

MODEL_NAME = "openrouter/mistralai/mistral-large"
# optionally you can manually set it here if you don't use a .env file
# os.environ["OPENROUTER_API_KEY"] = ""

base_ds_all = load_dataset("financial_phrasebank", "sentences_allagree", split="train")
base_ds = load_dataset("financial_phrasebank", "sentences_75agree", split="train")

allagree_sentences = set([r["sentence"] for r in base_ds_all])
exclude_idx = []
for i, row in enumerate(base_ds):
    if row["sentence"] in allagree_sentences:
        exclude_idx.append(i)

base_ds = base_ds.select(
    i for i in range(len(base_ds))
    if i not in set(exclude_idx)
)

label_map = {1: "neutral", 2: "positive", 0: "negative"}



class AugmentedLabels(BaseModel):
    reasoning: str
    conclusion: Literal["neutral", "positive", "negative"]


augmented_ds = []
for row in base_ds:
    # This is unoptimized loop for inferencing a model.
    # You should consider a queue/worker implementation for production workloads.

    try:
        prompt = f"""Sentence: {row["sentence"]}
        
    Analyze the sentence above and determine if the sentiment of the sentence is neutral, positive or negative. Explain your reasoning in detail before stating your conclusion of the sentiment. The conclusion should simply be the string value of the sentiment.
    
    Respond with JSON with fields `reasoning` and `conclusion`, i.e. {{ "reasoning": "...", "conclusion": "neutral|positive|negative" }}.
    """

        messages = [
            {"role": "user", "content": prompt}
        ]
        response = completion(
            model=MODEL_NAME,
            response_model=AugmentedLabels,
            messages=messages,
        )

        if response.conclusion == label_map[row["label"]]:

            new_row = {
                "sentence": row["sentence"],
                "label": row["label"],
                "label_text": label_map[row["label"]],
                "analysis": response.reasoning,
                "conversations": [
                    {"role": "user", "content": "Analyze the sentence and determine if the sentiment of the sentence is neutral, positive or negative.\n\n" + row["sentence"]},
                    {"role": "assistant", "content": response.reasoning + " Therefore, the sentiment of the sentence is " + label_map[row["label"]] + "."},
                ]
            }
            augmented_ds.append(new_row)
    except Exception as exc:
        print(row)
        print(exc)

new_ds = Dataset.from_list(augmented_ds)
new_ds.save_to_disk("./augmented_ds")

new_ds.push_to_hub("winglian/financial_phrasebank_augmented-validation")