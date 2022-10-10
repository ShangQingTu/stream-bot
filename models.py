import re

USER = "Q"
BOT = "A"


def build_prompt_for_glm(data_dict, mask_token='[gMASK]', background=''):
    past_user_inputs = data_dict["past_user_inputs"]
    generated_responses = data_dict["generated_responses"]
    query = data_dict["text"]
    # shorten history
    his_turns = min(len(past_user_inputs), len(generated_responses), 8)
    past_user_inputs = past_user_inputs[-his_turns:]
    generated_responses = generated_responses[-his_turns:]
    # init
    prompt_str = f"{background}|{USER}:你好|{BOT}:你好, 我是你的智能学习助理小木~|{USER}:最近怎么样|{BOT}:还是老样子|{USER}:你有什么功能|{BOT}:我可以为你解释知识点概念、查询课程资源、回答平台使用常见问题,推荐学术资源,还可以为你作诗哦～"
    for i in range(his_turns):
        if len(generated_responses[i]) < 1:
            continue
        prompt_str += f"|{USER}:{past_user_inputs[i]}|{BOT}:{generated_responses[i]}"
    prompt_str += f"|{USER}:{query}|{BOT}:{mask_token}"
    return prompt_str


def filter_glm(text, prefix=f"({BOT}:|{USER}:)", split="|"):
    if split == "|":
        regex_pattern = f"\<\|startofpiece\|\>([^\|]*)\{split}"
        reg = re.compile(regex_pattern)
    t = re.findall(reg, text)
    if not t:
        t = re.findall(f"<\|startofpiece\|>(.+)", text)
    if not t:
        regex_pattern = f"\[\[gMASK\]\]([^\|]*)\{split}"
        reg = re.compile(regex_pattern)
        t = re.findall(reg, text)
    res = "" if not t else t[0]
    res = res.strip()
    res = re.sub("\[.*\]", "", res)
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
