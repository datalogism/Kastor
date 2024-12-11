class TokenNormalizer:
    def __init__(self):
        gpt2_tokenizer = AutoTokenizer.from_pretrained("gpt2", use_fast=False)
        self.byte_encoder = gpt2_tokenizer.byte_encoder

    def normalize(self, token):
        output = ""
        for c in token:
            if ord(c) > 255:
                raise ValueError(f"Token {token} contains non-ascii character {c}")
            new_c = self.byte_encoder[ord(c)]
            output += new_c
        return output