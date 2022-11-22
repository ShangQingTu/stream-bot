import argparse
import os
import pandas as pd
from database import MongoDB
import json

version_ids = ['学姐_tsq22_2', '学长_tsq22_0']


def get_version_qa_lst(mdb, pid_lst):
    """
    :param mdb: db for persona generation
    :param pid_lst: persona qa record's id list
    :return: version_qa_dict_lst: [{'q':str, 'a':str}, ...]
    """
    # select df that has the _id in pid_lst
    res = mdb.get_many()
    res_lst = list(res)
    final = []
    for res in res_lst:
        res['_id'] = str(res['_id'])
        if res['_id'] in pid_lst:
            final.append(res)
    df = pd.DataFrame(final)
    query_lst = list(df["query"])
    answer_lst = list(df["answer"])
    qa_dict_lst = []
    for i, query in enumerate(query_lst):
        answer = answer_lst[i]
        qa_dict_lst.append({'talker': "user", 'text': query, 'is_bot': False})
        qa_dict_lst.append({'talker': "bot", 'text': answer, 'is_bot': True})
    return qa_dict_lst


def dump_persona_json(args):
    # open the database
    mdb = MongoDB(collection_name=f'persona_{args.model_version}')
    pid_mdb = MongoDB(collection_name=f'pid_list_{args.model_version}')
    res_lst = list(pid_mdb.get_many())
    # get vid2qa_dict_lst
    persona2qa_lst = {}
    for res in res_lst:
        vid = str(res['vid'])
        if vid in version_ids:
            pid_list = res['pid_list']
            version_qa_lst = get_version_qa_lst(mdb, pid_list)
            persona2qa_lst[vid.split("_")[0]] = version_qa_lst
    # dump to json
    dump_path = os.path.join(args.data_dir, f"{args.user}_{args.model_version}.json")
    with open(dump_path, 'w') as fout:
        json.dump(persona2qa_lst, fout)


def main():
    parser = argparse.ArgumentParser(description='Dump persona_qa_versions json from MongoDB')
    parser.add_argument('--data_dir', help='导出json的地址', type=str, default="/home/tsq/stream-bot/data/")
    parser.add_argument('--user', help='persona的创建者', type=str, default="tsq22")
    parser.add_argument('--model_version', help='大模型的版本', default='glm_base')
    args = parser.parse_args()
    dump_persona_json(args)


if __name__ == '__main__':
    main()
