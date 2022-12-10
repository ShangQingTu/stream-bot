import time
import argparse
import os
import requests
import pandas as pd
from models import build_prompt_for_glm, filter_glm
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import json
import jieba
from rouge_chinese import Rouge
import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import csv

USE_MRC = False
if USE_MRC:
    from transformers import AutoTokenizer, AutoModelForQuestionAnswering

    model_name = "chinese_pretrain_mrc_roberta_wwm_ext_large"
    tokenizer = AutoTokenizer.from_pretrained(f"luhua/{model_name}")
    model = AutoModelForQuestionAnswering.from_pretrained(f"luhua/{model_name}")
    from transformers import QuestionAnsweringPipeline

    qap = QuestionAnsweringPipeline(model, tokenizer)

rouge = Rouge()

version2api = {
    "cpm2": "http://localhost:5452/cpm",
    "glm_base": "http://localhost:9546/glm",
    "glm130b_base": "http://103.238.162.37:9622/general",
    "cdail_gpt": "http://0.0.0.0:9600/cdail",
    "eva": "http://0.0.0.0:9601/eva",
    "gpt3": "http://0.0.0.0:9602/gpt",
    "bm25": "http://0.0.0.0:9200",
}


def search_bm(query):
    client = Elasticsearch()
    s = Search(using=client)
    s = s.query("multi_match", query=query, fields=['title', 'body'])
    res = [hit.body for hit in s]
    res_str = "".join(res)[:500]
    return res_str


type2tags = {
    "introduction": [0, 1],
    # "emotion": ['惊喜', '激动', '愤怒', '骄傲', '伤心', '工作上的烦恼', '感激'],
    # "emotion": ['surprised', 'excited', 'angry', 'proud', 'sad', 'annoyed', 'grateful'],
    # Top 10 frequent emotion in dialog history
    "emotion": ['surprised', 'angry', 'sad', 'annoyed', 'lonely',
                'afraid', 'guilty', 'joyful', 'disappointed', 'sentimental'],
    # At least once occur in history
    # [
    #     'surprised', 'excited', 'angry', 'sad', 'annoyed', 'grateful',
    #     'lonely', 'afraid', 'guilty', 'impressed', 'disgusted', 'hopeful',
    #     'furious', 'anxious', 'anticipating', 'joyful', 'disappointed', 'content',
    #     'embarrassed', 'caring', 'sentimental', 'trusting', 'apprehensive'
    # ],
    "logic": ['compare', 'why', 'how', 'enumerate', 'recommend'],
}

personas = ['同学', '朋友', '助教', '老师', '学弟', '学妹', '学长', '学姐']


def merge_chat_history(past_user_inputs, generated_responses):
    history_len = min(len(past_user_inputs), len(generated_responses), 4)
    chat_history = []
    for i in range(history_len):
        if past_user_inputs[i] and generated_responses[i]:
            chat_history.append(past_user_inputs[i])
            chat_history.append(generated_responses[i])
    if len(chat_history) < 1:
        return ['Hi', '你好，我是你的学习助理小木，可以为您解释概念名词']
    return chat_history


def test130b(texts, strategy="BaseStrategy", stop=[], regix=""):
    # If TOPK/TOPP are 0 it defaults to greedy sampling, top-k will also override top-p
    data = {
        "prompt": texts,
        "max_tokens": 64,
        "min_tokens": 0,
        "top_k": 1,
        "top_p": 0,
        "temperature": 1,
        "seed": 1453,
        "sampling_strategy": strategy,
        "num_beams": 4,
        "length_penalty": 0.9,
        "no_repeat_ngram_size": 3,
        "regix": regix
    }

    t = time.time()
    res = requests.post("http://180.184.97.60:9624/generate", json=data).content.decode()
    t = time.time() - t

    res = json.loads(res)
    # print(res['text'], end='\n\n')
    text_res = []

    for generate, text in zip(res['text'], texts):
        generate.append('')
        generate = generate[0]
        # generate = "\x1B[4m" + generate.replace("[[gMASK]]", "") + "\x1B[0m"
        if "MASK" in text:
            text_res.append(text.replace("[gMASK]", "[[gMASK]]" + generate).replace("[MASK]", generate))
        else:
            text_res.append(text + generate)
    # print("glm130b", text_res)
    return text_res


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
        final_contexts = []
        prompt_str = build_prompt_for_glm(payload)
        final_contexts.append(prompt_str)
        # bsz = len(payload["contexts"])
        # for i in range(bsz):
        #     _payload = {
        #         "past_user_inputs": payload["past"][i],
        #         "generated_responses": payload["generated"][i],
        #         "text": payload["contexts"][i]["question"],
        #     }
        #     prompt_str = build_prompt_for_glm(_payload, mask_token='')
        #     if len(prompt_str) > 512:
        #         prompt_str = prompt_str[-512:]
        #     final_contexts.append(prompt_str)
        # payload = {
        #     "contexts": final_contexts
        # }
        # print(f"send payload is {payload}")
        # response = requests.post(API_URL, json=payload)
        # raw_str_lst = response.json()['outputs']
        # print(f"raw_str_lst is {raw_str_lst}")
        # _lst = [filter_glm(raw_str) for raw_str in raw_str_lst]
        # _lst = [''.join(res.split()) for res in _lst]
        # print(final_contexts)
        text_res_lst = test130b(final_contexts)
        filtered = [filter_glm(t + "|A:不知道") for t in text_res_lst]
        # print("130b filtered", filtered)
        if len(filtered) == 1:
            return filtered[0]
        return filtered
    elif test_version == "bm25":
        question = payload["text"]
        # print("q:", question)
        text = search_bm(question)
        # print("text", text)
        ans = qap(
            {'question': question,
             'context': text}
        )
        # print("a:", ans)
        return ans
    else:
        _payload = {
            "question": payload["text"],
            "chat_history": merge_chat_history(payload["past_user_inputs"], payload["generated_responses"])
        }
        print(f"send payload is {_payload}")
        print(API_URL)
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
        try:
            answer = query(args.test_version, {
                "past_user_inputs": past,
                "generated_responses": generated,
                "text": question,
            })
        except Exception:
            answer = ""
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


def get_qa_answer(question, raw_answer):
    past = []
    generated = []
    # try:
    answer = query(args.test_version, {
        "past_user_inputs": past,
        "generated_responses": generated,
        "text": question,
    })
    # except Exception:
    #     answer = ""

    hypothesis = str(answer)
    hypothesis = ' '.join(jieba.cut(hypothesis))
    if not hypothesis:
        hypothesis = "我 不 知道"

    reference = ' '.join(jieba.cut(str(raw_answer)))
    scores = rouge.get_scores(hypothesis, reference)
    res = {"question": question, "real_answer": raw_answer, "new_answer": answer,
           "rouge-1": scores[0]["rouge-1"], "rouge-2": scores[0]["rouge-2"], "rouge-l": scores[0]["rouge-l"]}
    return res


def QA_pipeline_answer(args):
    datapath = '/home/tsq/user/lcy/RocketQA/问题答案标注.xlsx'
    raw_data = pd.read_excel(datapath, sheet_name='Sheet1')
    questions = raw_data['question']
    answers = raw_data['答案']
    result = []
    num = len(answers)
    for q, a in tqdm(zip(questions, answers), total=num):
        if a != 'cannot_answer':
            score = get_qa_answer(str(q).replace('\n', ''), str(a).replace('\n', ''))
            result.append(score)

    # write result
    outputpath = f'{args.data_dir}/scores_of_{args.test_version}.csv'
    with open(outputpath, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='|')
        writer.writerow(['question', 'real_answer', 'new_answer', 'rouge-1', 'rouge-2', 'rouge-l'])
        for res in result:
            writer.writerow([res['question'], res['real_answer'], res['new_answer'], res['rouge-1'], res['rouge-2'],
                             res['rouge-l']])


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
    parser.add_argument('--data_dir', help='数据地址', default='/data/tsq/xiaomu/general_dialogue_test')
    parser.add_argument('--test_file', help='数据文件', default='xiaomu_v1.csv')
    parser.add_argument('--test_version', help='版本', default='gpt3')
    parser.add_argument('--task', help='任务类型', default='generate_his_answer',
                        choices=['generate_his_answer', 'generate_batch_answer'])
    args = parser.parse_args()
    if args.task == "generate_his_answer":
        if args.test_file == 'xiaomu_v1.csv':
            generate_his_answer(args)
        elif args.test_file == '问题答案标注.xlsx':
            QA_pipeline_answer(args)
    elif args.task == "generate_batch_answer":
        generate_batch_answer(args)
