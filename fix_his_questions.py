import json
import argparse
import os
import requests
import pandas as pd
from models import build_prompt_for_glm, filter_glm
from tqdm import tqdm

version2api = {
    "cpm2": "http://localhost:5452/cpm",
    "glm_base": "http://localhost:9628/glm",
    "glm130b_base": "http://103.238.162.37:9622/general",
    "cdail_gpt": "http://0.0.0.0:9600/cdail",
    "eva": "http://0.0.0.0:9601/eva",
}

type2tags = {
    "introduction": [0, 1, 2, 3],
    # "emotion": ['惊喜', '激动', '愤怒', '骄傲', '伤心', '工作上的烦恼', '感激'],
    "emotion": ['surprised', 'excited', 'angry', 'proud', 'sad', 'annoyed', 'grateful'],
    "logic": ['compare', 'why', 'how', 'enumerate', 'recommend'],
}

personas = ['学姐', '学长', '学弟', '学妹', '老师']


def merge_chat_history(past_user_inputs, generated_responses):
    history_len = min(len(past_user_inputs), len(generated_responses), 4)
    chat_history = []
    for i in range(history_len):
        chat_history.append(past_user_inputs[i])
        chat_history.append(generated_responses[i])
    return chat_history


def query(test_version, payload):
    API_URL = version2api[test_version]
    if test_version == "glm_base":
        prompt_str = build_prompt_for_glm(payload)
        payload = {"query": prompt_str, "limit": 30}
        response = requests.post(API_URL, json=payload)
        raw_str = response.json()['data']
        final_response = filter_glm(raw_str)
        return final_response
    elif test_version == "cpm2":
        prompt_str = build_prompt_for_glm(payload, mask_token='')
        payload = {"query": prompt_str, "limit": 30}
        response = requests.post(API_URL, json=payload)
        final_response = response.json()
        return final_response
    elif test_version == "glm130b_base":
        bsz = len(payload["contexts"])
        final_contexts = []
        for i in range(bsz):
            _payload = {
                "past_user_inputs": payload["past"][i],
                "generated_responses": payload["generated"][i],
                "text": payload["contexts"][i]["question"],
            }
            prompt_str = build_prompt_for_glm(_payload, mask_token='')
            if len(prompt_str) > 512:
                prompt_str = prompt_str[-512:]
            final_contexts.append(prompt_str)
        payload = {
            "contexts": final_contexts
        }
        print(f"send payload is {payload}")
        response = requests.post(API_URL, json=payload)
        raw_str_lst = response.json()['outputs']
        print(f"raw_str_lst is {raw_str_lst}")
        _lst = [filter_glm(raw_str) for raw_str in raw_str_lst]
        _lst = [''.join(res.split()) for res in _lst]
        return _lst, raw_str_lst
    else:
        _payload = {
            "question": payload["text"],
            "chat_history": merge_chat_history(payload["past_user_inputs"], payload["generated_responses"])
        }
        print(f"send payload is {_payload}")
        response = requests.post(API_URL, json=_payload)
        print("response", response)
        print("response.json()", response.json())
        raw_str = response.json()['answer']
        return "".join(raw_str.split())


def generate_his_answer(args):
    v1_csv_path = os.path.join(args.data_dir, f'xiaomu_v1.csv')
    v1_df = pd.read_csv(v1_csv_path, header=None)
    res_list = []
    gen_q_num = 0
    past = []
    generated = []
    prev_course = ""
    for index, row in tqdm(v1_df.iterrows()):
        if index == 0:
            continue
        if prev_course != row[4]:
            prev_course = row[4]
            gen_q_num = 0
            past = []
            generated = []
        if gen_q_num >= args.course_question_num:
            continue
        origin_id = int(row[2])
        category = row[3]
        course = row[4]
        question = row[5]
        answer = query(args.test_version, {
            "past_user_inputs": past,
            "generated_responses": generated,
            "text": question,
        })
        res_list.append({
            "origin_id": origin_id,
            "category": category,
            "course": course,
            "question": question,
            "answer": answer,
        })
        # add to history
        past.append(question)
        generated.append(answer)
        if len(past) > args.past_num:
            past = past[1:]
            generated = generated[1:]
        gen_q_num += 1
    res_csv_path = os.path.join(args.data_dir, f'{args.test_version}_history_question.csv')
    res_df = pd.DataFrame(res_list)
    # json.dump(res_list, open(res_csv_path, "w"))
    res_df.to_csv(res_csv_path)


def gen_batch(v1_df, batch_size, course_question_num):
    gen_q_num = 0
    prev_course = ""
    batches = []
    origin_questions = []
    for index, row in tqdm(v1_df.iterrows()):
        if index == 0:
            continue

        if prev_course != row[4]:
            prev_course = row[4]
            gen_q_num = 0

        if gen_q_num >= course_question_num:
            continue
        origin_id = int(row[2])
        category = row[3]
        course = row[4]
        question = row[5]
        origin_questions.append(
            {
                "origin_id": origin_id,
                "category": category,
                "course": course,
                "question": question,
            }
        )
        gen_q_num += 1
    num_course_batch = len(origin_questions) // (course_question_num * batch_size)
    for i in range(num_course_batch):
        begin_pos = (course_question_num * batch_size) * i
        for j in range(course_question_num):
            batch = []
            for k in range(batch_size):
                batch.append(origin_questions[begin_pos + j + k * course_question_num])
            batches.append(batch)
    # 0, 20, 40, 60
    # 1, 21, 41, 61,
    # ...
    # 80, 100, 120, 140
    # ...

    return batches


def generate_batch_answer(args):
    v1_csv_path = os.path.join(args.data_dir, f'xiaomu_v1.csv')
    v1_df = pd.read_csv(v1_csv_path, header=None)
    past = [[] for i in range(args.batch_size)]
    generated = [[] for i in range(args.batch_size)]
    batches = gen_batch(v1_df, args.batch_size, args.course_question_num)
    res_path = os.path.join(args.data_dir, f'{args.test_version}.json')
    fout = check_fout(res_path)
    print(f"total batch num is {len(batches)}")
    for batch in tqdm(batches):
        payload = {
            "contexts": batch,
            "past": past,
            "generated": generated,
        }
        answers, raw_str_lst = query(args.test_version, payload)
        # log to res_path
        for j in range(args.batch_size):
            res = batch[j]
            res["answer"] = answers[j]
            res["usr_history"] = past[j]
            res["bot_history"] = generated[j]
            res["raw_str"] = raw_str_lst[j]
            fout.write(json.dumps(res))
            fout.write("\n")
            past[j].append(batch[j]["question"])
            generated[j].append(answers[j])
        # control history length
        if len(past[0]) > args.past_num:
            for i in range(args.batch_size):
                # past[i] = past[i][1:]
                # generated[i] = generated[i][1:]
                past[i] = []
                generated[i] = []


def check_fout(file_path):
    if os.path.exists(file_path):
        return open(file_path, 'w')
    else:
        return open(file_path, 'a')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Data for checked QA history on xiaomu')
    parser.add_argument('--course_question_num', help='每个课程的问题数量', type=int, default=20)
    parser.add_argument('--past_num', help='历史轮数数量', type=int, default=8)
    parser.add_argument('--batch_size', help='发给130b的请求', type=int, default=4)
    parser.add_argument('--data_dir', help='数据地址', default='/data/tsq/xiaomu')
    parser.add_argument('--test_version', help='版本', default='cpm2')
    parser.add_argument('--task', help='任务类型', default='generate_his_answer',
                        choices=['generate_his_answer', 'generate_batch_answer'])
    args = parser.parse_args()
    if args.task == "generate_his_answer":
        generate_his_answer(args)
    elif args.task == "generate_batch_answer":
        generate_batch_answer(args)
