from transformers import  AutoTokenizer

class TokenNormalizer:
    def __init__(self,model):
        tokenizer = AutoTokenizer.from_pretrained(model, use_fast=False)
        if(tokenizer.byte_encoder):
            self.byte_encoder = tokenizer.byte_encoder
        else:
            self.byte_encoder = None

    def normalize(self, token):
        output = ""
        for c in token:
            if ord(c) > 255:
                raise ValueError(f"Token {token} contains non-ascii character {c}")
            new_c = self.byte_encoder[ord(c)]
            output += new_c
        return output