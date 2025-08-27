import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class LocalLLM:
    def __init__(self):
        self.model_id = os.getenv("GEN_MODEL", "HuggingFaceTB/SmolLM3-3B")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, use_fast=True)
        load_4bit = (torch.cuda.is_available() and os.name != 'nt')
        quant_cfg = None
        if load_4bit:
            from bitsandbytes.config import BitsAndBytesConfig
            quant_cfg = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                low_cpu_mem_usage=True,
                device_map="auto",
                quantization_config=quant_cfg,
            )

    def generate(self, prompt: str) -> str:
        max_new = int(os.getenv("MAX_NEW_TOKENS", 512))
        temperature = float(os.getenv("TEMPERATURE", 0.3))
        top_p = float(os.getenv("TOP_P", 0.9))
        top_k = int(os.getenv("TOP_K", 50))
        rep_pen = float(os.getenv("REPETITION_PENALTY", 1.05))
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=rep_pen,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)