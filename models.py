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
