import json
import argparse
import os
import pandas as pd


def dump_csv(args):
    res_path = os.path.join(args.data_dir, f'{args.test_version}.json')
    fin = open(res_path, 'r')
    lines = fin.readlines()
    res_list = []
    for line in lines:
        res = json.loads(line.strip())
        res_list.append(res)
    res_csv_path = os.path.join(args.data_dir, f'{args.test_version}_history_question.csv')
    res_df = pd.DataFrame(res_list)
    res_df.to_csv(res_csv_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyse for checked QA history experiment on xiaomu')
    parser.add_argument('--data_dir', help='数据地址', default='/data/tsq/xiaomu')
    parser.add_argument('--test_version', help='版本', default='cpm2')
    parser.add_argument('--task', help='任务类型', default='dump_csv',
                        choices=['dump_csv', 'generate_batch_answer'])
    args = parser.parse_args()
    if args.task == "dump_csv":
        dump_csv(args)
