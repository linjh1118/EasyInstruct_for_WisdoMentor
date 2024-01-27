from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from .base_selector import BaseSelector


class PPLSelector(BaseSelector):
    def __init__(
        self,
        source_file_path: str = "",
        target_dir: str = "data/selections/",
        target_file_name: str = "selected_instructions.jsonl",
        threshold: float = 200,
        model_name: str = "gpt2",
        device: str = "cuda",
    ):
        super(PPLSelector, self).__init__(
            source_file_path, target_dir, target_file_name
        )
        self.threshold = threshold
        self.model_name = model_name
        self.device = device

    def __process__(self, data):
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)

        selected_data = []

        for d in tqdm(data):
            if self.data_format == "self_instruct":
                input_text = d["instances"][0]["output"]
            elif self.data_format == "alpaca" or self.data_format == "alpaca_wo_input":
                input_text = d["output"]
            else:
                raise ValueError("Unknown data format")

            encodings = tokenizer(input_text, return_tensors="pt")
            max_length = model.config.n_positions
            stride = 512
            seq_len = encodings.input_ids.size(1)

            nlls = []
            prev_end_loc = 0
            for begin_loc in range(0, seq_len, stride):
                end_loc = min(begin_loc + max_length, seq_len)
                trg_len = (
                    end_loc - prev_end_loc
                )  # may be different from stride on last loop
                input_ids = encodings.input_ids[:, begin_loc:end_loc].to(self.device)
                target_ids = input_ids.clone()
                target_ids[:, :-trg_len] = -100

                with torch.no_grad():
                    outputs = model(input_ids, labels=target_ids)

                    # loss is calculated using CrossEntropyLoss which averages over valid labels
                    # N.B. the model only calculates loss over trg_len - 1 labels, because it internally shifts the labels
                    # to the left by 1.
                    neg_log_likelihood = outputs.loss

                nlls.append(neg_log_likelihood)

                prev_end_loc = end_loc
                if end_loc == seq_len:
                    break

            ppl = torch.exp(torch.stack(nlls).mean())

            if ppl <= self.threshold:
                d["ppl"] = ppl.item()
                selected_data.append(d)

        return selected_data
