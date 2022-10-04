import json
import argparse
import os
import requests
import pandas as pd
from models import build_prompt_for_glm, filter_glm
from tqdm import tqdm

API_URL = "http://localhost:5452/cpm"


def query(test_version, payload):
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
    else:
        response = requests.post(API_URL, json=payload)
        return response.json()


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
        if len(past) > 8:
            past = past[1:]
            generated = generated[1:]
        gen_q_num += 1
    res_csv_path = os.path.join(args.data_dir, f'{args.test_version}_history_question.csv')
    json.dump(res_list, open(res_csv_path, "w"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Data for checked QA history on xiaomu')
    parser.add_argument('--course_question_num', help='每个课程的问题数量', default=20)
    parser.add_argument('--data_dir', help='数据地址', default='/data/tsq/xiaomu')
    parser.add_argument('--test_version', help='版本', default='cpm2')
    parser.add_argument('--task', help='任务类型', default='generate_his_answer',
                        choices=['generate_his_answer'])
    args = parser.parse_args()
    if args.task == "generate_his_answer":
        generate_his_answer(args)
