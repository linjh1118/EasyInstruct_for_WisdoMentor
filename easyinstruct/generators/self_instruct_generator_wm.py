import os
import json
import random
import re
import string
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool
from functools import partial
from rouge_score import rouge_scorer

from easyinstruct import BasePrompt
from .base_generator import BaseGenerator

generate_instructions_prompt_template = """You are asked to come up with a set of 20 diverse task instructions. These task instructions will be given to a GPT model and we will evaluate the GPT model for completing the instructions.

Here are the requirements:
1. Try not to repeat the verb for each instruction to maximize diversity.
2. The language used for the instruction also should be diverse. For example, you should combine questions with imperative instrucitons.
3. The type of instructions should be diverse. The list should include diverse types of tasks like open-ended generation, classification, editing, etc.
4. A GPT language model should be able to complete the instruction. For example, do not ask the assistant to create any visual or audio output. For another example, do not ask the assistant to wake you up at 5pm or set a reminder because it cannot perform any action.
5. The instructions should be in English.
6. The instructions should be 1 to 2 sentences long. Either an imperative sentence or a question is permitted.

List of 20 tasks:
"""

# linjh: final_prompt. At SelfInstructGeneratorWM.encode_prompt, we will add 8 example.
#        at decode stage, we will split the prompt by "###" and get the 12 result. at SelfInstructGeneratorWM.post_process_generations

"""You are asked to come up with a set of 20 diverse task instructions. These task instructions will be given to a GPT model and we will evaluate the GPT model for completing the instructions.

Here are the requirements:
1. Try not to repeat the verb for each instruction to maximize diversity.
2. The language used for the instruction also should be diverse. For example, you should combine questions with imperative instrucitons.
3. The type of instructions should be diverse. The list should include diverse types of tasks like open-ended generation, classification, editing, etc.
4. A GPT language model should be able to complete the instruction. For example, do not ask the assistant to create any visual or audio output. For another example, do not ask the assistant to wake you up at 5pm or set a reminder because it cannot perform any action.
5. The instructions should be in English.
6. The instructions should be 1 to 2 sentences long. Either an imperative sentence or a question is permitted.

List of 20 tasks:
###
1. Instruction: Write a short story about a detective.
###
2. Instruction: What are the top 5 most popular programming languages in 2022?
###
"""


generate_instances_prompt_template = """Come up with examples for the following tasks. You should generate an appropriate input to the instruction. The input field should contain a specific example provided for the instruction. It should involve realistic data and should not contain simple placeholders. The input should provide substantial content to make the instruction challenging but should ideally not exceed 100 words. Not all instructions require input. For example, when a instruction asks about some general information, "what is the highest peak in the world", it is not necssary to provide a specific context. The output should be an appropriate response to the instruction and the input. Make sure the output is less than 100 words.

Instruction: Which exercises are best for reducing belly fat at home?
Output:
- Lying Leg Raises
- Leg In And Out
- Plank
- Side Plank
- Sit-ups

Instruction: Extract all the country names in the paragraph, list them separated by commas.
Example 1
Input: Dr. No is the sixth novel by the English author Ian Fleming to feature his British Secret Service agent James Bond. Written at Fleming's Goldeneye estate in Jamaica, it was first published in the United Kingdom by Jonathan Cape in 1958. In the novel Bond looks into the disappearance in Jamaica of two fellow MI6 operatives who had been investigating Doctor No. Bond travels to No's Caribbean island and meets Honeychile Rider, who is there to collect shells. They are captured and taken to a luxurious facility carved into a mountain. The character of Doctor No, the son of a German missionary and a Chinese woman, was influenced by Sax Rohmer's Fu Manchu stories. Dr. No was the first of Fleming's novels to face widespread negative reviews in Britain, but it was received more favourably in the United States.
Output: English, British, Jamaica, the United Kingdom, German, Chinese, Britain, the United States.

Instruction: Converting 85 F to Celsius.
Output: 85°F = 29.44°C

Instruction: Sort the given list ascendingly. 
Example 1
Input: [10, 92, 2, 5, -4, 92, 5, 101]
Output: [-4, 2, 5, 5, 10, 92, 92, 101]
Example 2
Input: [9.99, 10, -5, -1000, 5e6, 999]
Output: [-1000, -5, 9.99, 10, 999, 5e6]

Instruction: Suggest a better and more professional rephrasing of the following sentence.
Example 1
Input: This house is surprisingly not constructed very well, and you probably need more money to fix it after you buy it. If you ask me, I would suggest you to consider other candidates.
Output: This house does not seem to be constructed well, so you may need to spend more money to fix it after you purchase it. I would suggest that you look at other properties.
Example 2
Input: Just so you know, we did an experiment last week and found really surprising results - language model can improve itself!
Output: Our experiments last week demonstrated surprising results, proving that the language model can improve itself.

Instruction: Read the following paragraph and answer a math question about the paragraph. You need to write out the calculation for getting the final answer.
Example 1
Input: Gun violence in the United States results in tens of thousands of deaths and injuries annually, and was the leading cause of death for children 19 and younger in 2020. In 2018, the most recent year for which data are available as of 2021, the Centers for Disease Control and Prevention's (CDC) National Center for Health Statistics reports 38,390 deaths by firearm, of which 24,432 were by suicide. The rate of firearm deaths per 100,000 people rose from 10.3 per 100,000 in 1999 to 12 per 100,000 in 2017, with 109 people dying per day or about 14,542 homicides in total, being 11.9 per 100,000 in 2018. In 2010, there were 19,392 firearm-related suicides, and 11,078 firearm-related homicides in the U.S. In 2010, 358 murders were reported involving a rifle while 6,009 were reported involving a handgun; another 1,939 were reported with an unspecified type of firearm. In 2011, a total of 478,400 fatal and nonfatal violent crimes were committed with a firearm. How many more firearm-related deaths were there in 2018 compared to 2010?
Output:
38390 - (19392 + 11078) = 38390 - 30470 = 7920. 
So, in 2018, there were 7920 more deaths by firearm than in 2010.

Instruction: Write Python code to solve this leetcode problem.
Example 1
Input: You are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order, and each of their nodes contains a single digit. Add the two numbers and return the sum as a linked list. You may assume the two numbers do not contain any leading zero, except the number 0 itself.
Output:
class Solution(object):
    def addTwoNumbers(self, l1, l2):
        carry = 0
        root = n = ListNode(0)
        while l1 or l2 or carry:
            v1 = v2 = 0
            if l1:
                v1 = l1.val
                l1 = l1.next
            if l2:
                v2 = l2.val
                l2 = l2.next
            carry, val = divmod(v1+v2+carry, 10)
            n.next = ListNode(val)
            n = n.next
        return root.next

Instruction: Solve the equation and find the value of X. Show your steps.
Example 1
Input: 10X + 5 = 10
Output: 10X = 5,  X = 0.5
Example 2
Input: X + Y + 120 = 100
Output: X + Y = -20, X = -20 - Y

Instruction: Write a program to compute the sum of integers from k to n.
Output:
def sum(k, n):
    sum = 0
    for i in range(k, n+1):
        sum += i
    return sum

Instruction: Select the oldest person from the given list.
Example 1
Input: George Washington, Confucius, Michael Jordan, Michelangelo
Output: Confucious
Example 2
Input: Alan Turing, Geoffrey Hinton, Yann LeCun, Yoshua Bengio
Output: Alan Turing

Instruction: Turn down a job offer by sending an email to a recruiter explaining the reason.
Output: Hi  [Recruiter],
Thank you so much for the generous offer to join your team. As we discussed, I've admired the company for a number of years, and am a proud endorser of its products. However, after further consideration of where I currently am in my career, I've decided to accept an offer at another company.
I would love to stay in touch with you and have already started following you on [Social Media Platform]. Again, thank you so much for your time and consideration.
Thanks again,
[Your Name]

"""


filter_instruction_word = [
    "image", "images", "graph", "graphs", "picture", "pictures",
    "file", "files",
    "map", "maps", "draw", "plot", 
    "go to", "program", 
    "sorry"
]

class SelfInstructGeneratorWM(BaseGenerator):
    def __init__(
        self,
        target_dir: str = "data/generations/",
        data_format: str = "alpaca",
        seed_tasks_path: str = "data/seed_tasks.jsonl",
        generated_instructions_path: str = "generated_instructions.jsonl",
        generated_instances_path: str = "generated_instances.jsonl",
        num_instructions_to_generate: int = 100,
        engine: str = "gpt-3.5-turbo",
        num_prompt_instructions: int = 8,
    ):
        super(SelfInstructGeneratorWM, self).__init__(target_dir, data_format)
        self.seed_tasks_path = seed_tasks_path
        self.generated_instructions_path = os.path.join(
            self.target_dir, generated_instructions_path
        )
        self.generated_instances_path = os.path.join(
            self.target_dir, generated_instances_path
        )
        self.num_instructions_to_generate = num_instructions_to_generate
        self.engine = engine
        self.num_prompt_instructions = num_prompt_instructions
        self.which_model_in_ollama = 'qwen:4b'

    def find_word_in_string(self, w, s):
        return re.compile(r"\b({0})\b".format(w), flags=re.IGNORECASE).search(s)
    
    def encode_prompt(self, prompt_instructions):
        """Encode multiple prompt instructions into a single string."""
        prompt = generate_instructions_prompt_template

        for idx, instruction in enumerate(prompt_instructions):
            instruction = re.sub(r"\s+", " ", instruction).strip().rstrip(":")  # 空白字符全部替换成空格
            prompt += f"###\n"
            prompt += f"{idx + 1}. Instruction: {instruction}\n"
        prompt += f"###\n"
        return prompt

    def is_valid_instruction(self, inst):
        # filter out too short or too long instructions
        if len(inst.split()) <= 3 or len(inst.split()) > 150:
            return False
        # filter based on keywords that are not suitable for language models.
        if any(
            self.find_word_in_string(word, inst) for word in filter_instruction_word
        ):
            return False
        # We found that the model tends to add "write a program" to some existing instructions, which lead to a lot of such instructions.
        # And it's a bit comfusing whether the model need to write a program or directly output the result.
        # Here we filter them out.
        # Note this is not a comprehensive filtering for all programming instructions.
        if inst.startswith("Write a program"):
            return False
        # filter those starting with punctuation
        if inst[0] in string.punctuation:
            return False
        # filter those starting with non-english character
        if not inst[0].isascii():
            return False
        return True
    
    def post_process_generations(self, num_prompt_instructions, chat_model_response):
        raw_instructions = re.split("###", chat_model_response)
        instructions = []
        for idx, inst in enumerate(raw_instructions):
            idx += num_prompt_instructions + 1
            splitted_data = re.split(f"{idx}\.\s+(Instruction):", inst) # 很少这么写，我一般是match后，replace。这里是分隔成三部分：分隔语句前的字符串，分隔语句的示例情况，分隔语句后的情况
            if len(splitted_data) != 3:
                continue
            else:
                inst = splitted_data[2].strip()
            inst = inst.strip().capitalize()
            
            if not self.is_valid_instruction(inst):
                continue
            instructions.append(inst)
        
        assert len(instructions) != 0, 'Linjh: no valid instructions generated. Please check your prompt or llm'
        
        return instructions

    def parse_input_output(self, response_text):
        if re.findall(r"Output\s*\d*\s*:", response_text):
            inst_input = re.split(r"Output\s*\d*\s*:", response_text)[0].strip()
            inst_output = re.split(r"Output\s*\d*\s*:", response_text)[1].strip()
        else:
            inst_input = ""
            inst_output = response_text.strip()
        # to avoid the case multiple input/output pairs are generated
        if re.findall(r"Input\s*\d*\s*:", inst_output):
            inst_output = re.split(r"Input\s*\d*\s*:", inst_output)[0].strip()
        # remove the prefix "Input:" from the string
        inst_input = re.sub(r"^Input\s*\d*\s*:", "", inst_input).strip()
        return inst_input, inst_output

    def generate_instructions(self):
        seed_instructions = [
            t["instruction"] for t in self.load_data_from_file(self.seed_tasks_path)
        ]
        print(f"Loaded {len(seed_instructions)} human-written seed instructions.")

        generated_instructions = []
        if os.path.exists(self.generated_instructions_path):
            generated_instructions = [
                inst["instruction"]
                for inst in self.load_data_from_file(self.generated_instructions_path)
            ]
            print(f"Loaded {len(generated_instructions)} generated instructions.")

        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)

        progress_bar = tqdm(total=self.num_instructions_to_generate)
        if len(generated_instructions) > 0:
            progress_bar.update(len(generated_instructions))

        with open(self.generated_instructions_path, "a") as fout:
            while len(generated_instructions) < self.num_instructions_to_generate:
                prompt_instructions = random.sample(
                    seed_instructions, self.num_prompt_instructions
                )
                random.shuffle(prompt_instructions)
                encoded_prompt = self.encode_prompt(prompt_instructions)
                prompt = BasePrompt()
                prompt.build_prompt(prompt=encoded_prompt)
                ### linjh
                prompt.get_local_ollama_llm_result(which_model_in_ollama=self.which_model_in_ollama)

                instructions = []
                new_instructions = self.post_process_generations(
                    self.num_prompt_instructions, prompt.chat_model_response # linjh
                )
                instructions += new_instructions

                for inst in instructions:
                    all_instructions = seed_instructions + generated_instructions
                    with Pool(4) as p:
                        rouge_scores = p.map(
                            partial(scorer.score, inst), all_instructions
                        )
                    rouge_scores = [score["rougeL"].fmeasure for score in rouge_scores]
                    if max(rouge_scores) > 0.7:
                        continue
                    most_similar_instructions = {
                        all_instructions[i]: rouge_scores[i]
                        for i in np.argsort(rouge_scores)[-10:][::-1]
                    }
                    generated_instructions.append(inst)
                    fout.write(
                        json.dumps(
                            {
                                "instruction": inst,
                                "most_similar": most_similar_instructions,
                                "avg_similarity_score": float(np.mean(rouge_scores)),
                            }
                        )
                        + "\n"
                    )
                    progress_bar.update(1)

    def generate_instances(self):
        generated_instructions = []
        if os.path.exists(self.generated_instructions_path):
            generated_instructions = [
                inst["instruction"]
                for inst in self.load_data_from_file(self.generated_instructions_path)
            ]
            if self.num_instructions_to_generate is not None:
                generated_instructions = generated_instructions[
                    : self.num_instructions_to_generate
                ]
            print(f"Loaded {len(generated_instructions)} generated instructions.")

        existing_requests = []
        if os.path.exists(self.generated_instances_path):
            existing_requests = [
                inst["instruction"]
                for inst in self.load_data_from_file(self.generated_instances_path)
            ]
            print(f"Loaded {len(existing_requests)} existing requests.")

        progress_bar = tqdm(total=len(generated_instructions))
        generated_instances = []
        with open(self.generated_instances_path, "w") as fout:
            for inst in generated_instructions:
                if inst in existing_requests:
                    progress_bar.update(1)
                    continue

                prompt = BasePrompt()
                prompt.build_prompt(f"{generate_instances_prompt_template} {inst}\n")
                # linjh
                prompt.get_local_ollama_llm_result(which_model_in_ollama=self.which_model_in_ollama)

                if (
                    prompt.response is None
                    or prompt.response.choices[0].finish_reason == "length"
                ):
                    continue

                data = {}
                data["instruction"] = inst
                raw_instance = prompt.output
                if re.findall("Example\s?\d*\.?", raw_instance):
                    if self.data_format == "self_instruct":
                        data["instances"] = []
                        for example in re.split(r"Example\s?\d*\.?", raw_instance):
                            if example.strip() == "":
                                continue
                            inst_input, inst_output = self.parse_input_output(example)
                            data["instances"].append(
                                {"input": inst_input, "output": inst_output}
                            )
                    elif self.data_format == "alpaca":
                        example = re.split(r"Example\s?\d*\.?", raw_instance)[1]
                        if example.strip() == "":
                            continue
                        inst_input, inst_output = self.parse_input_output(example)
                        data["input"] = inst_input
                        data["output"] = inst_output

                elif re.findall(r"Output\s*\d*\s*:", raw_instance):
                    inst_input, inst_output = self.parse_input_output(raw_instance)
                    if self.data_format == "self_instruct":
                        data["instances"] = [
                            {"input": inst_input, "output": inst_output}
                        ]
                    elif self.data_format == "alpaca":
                        data["input"] = inst_input
                        data["output"] = inst_output

                else:
                    if self.data_format == "self_instruct":
                        data["instances"] = [{"input": "", "output": raw_instance}]
                    elif self.data_format == "alpaca":
                        data["input"] = ""
                        data["output"] = raw_instance

                generated_instances.append(data)
                fout.write(json.dumps(data, ensure_ascii=False) + "\n")
                progress_bar.update(1)
        return generated_instances

    def generate(self):
        self.generate_instructions()
        generated_instances = self.generate_instances()
        return generated_instances
