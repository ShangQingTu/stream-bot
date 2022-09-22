import re


def build_prompt_for_glm(data_dict):
    past_user_inputs = data_dict["past_user_inputs"]
    generated_responses = data_dict["generated_responses"]
    query = data_dict["text"]
    his_turns = min(len(past_user_inputs), len(generated_responses))
    prompt_str = ""
    for i in range(his_turns):
        prompt_str += f"|USER:{past_user_inputs[i]}|BOT:{generated_responses[i]}"
    prompt_str += f"|USER:{query}|BOT:[gMASK]"
    return prompt_str


def filter_glm(text, prefix="(BOT:|USER:)", split="|"):
    if split == "|":
        regex_pattern = f"\<\|startofpiece\|\>([^\|]*)\{split}"
        reg = re.compile(regex_pattern)
    t = re.findall(reg, text)
    if not t:
        t = re.findall(f"<\|startofpiece\|>(.+)", text)

    res = "" if not t else t[0]
    res = res.strip()
    prefix = prefix
    reg = re.compile(prefix)
    t = re.split(reg, res)
    for i in t:
        if i and i not in prefix:
            res = i
            break
    else:
        pass

    res = res.strip()
    return res
