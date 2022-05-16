import json
import time
import tweepy
import numpy as np
import pandas as pd
from tqdm import tqdm
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("account 1", type=str, action="store")
parser.add_argument("account 2", type=str, action="store")
parser.add_argument("--max_followers", type=int, default=500, action="store")

args = parser.parse_args()
args_dict = vars(args)
acc1 = args_dict['account 1']
acc2 = args_dict['account 2']
max_followers = args_dict['max_followers']

def main():
    api = get_config()
    get_followers_followers(api, acc1, acc2, max_followers)

def get_config():
    # Load keys
    config = {}
    with open('config.json') as json_file:
            f = json.load(json_file)
            config.update(f)
            
    C_KEY = config['C_KEY']
    C_SECRET = config['C_SECRET']
    A_TOKEN = config['A_TOKEN']
    A_TOKEN_SECRET = config['A_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)

    # Set wait_on_rate_limit to True while connecting through Tweepy
    api = tweepy.API(auth, wait_on_rate_limit=True)
    return api

def dir_setup(acc1, acc2):
    # create dir to store data
    dataset_dir = 'scraped_ids' 
    os.makedirs(dataset_dir, exist_ok=True)
    # ctreate subdir for specific twitter accounts
    subdir = acc1 + "_" + acc2
    subdir_path = os.path.join(os.getcwd(), dataset_dir, subdir)
    # start var will be used to resume scraping 
    start = 0
    if os.path.exists(subdir_path):
        files_list = os.listdir(subdir_path)
        for f in files_list:
            if not f.startswith('.'):
                print(f)
                # f name is in format 'ids' + str(i+1) + "_" + acc1 + "_" + acc2 + '.json'
                f_string = f.split("_")[0][3:]
                print(f_string, start)
                start = max(int(f_string),start)
                print("new", start)
    else:
        os.makedirs(subdir_path)
    return subdir_path, start


def get_userids(api, user):
    # Get user ids of followers as a list
    # request for 5000 max follower ids in one request --> 75K ids in every 15 minute window
    # lim 1 request/ 1 min is allowed
    userids = []
    try:
        userids = api.get_follower_ids(user_id=user)
    except tweepy.errors.Unauthorized as e:
        print("Error catched ...", user, e)
        pass
    except tweepy.errors.NotFound as e:
        print("Error catched ...", user, e)
        pass

    print("N.o followers of ", str(user), len(userids))
    # add time delay to avoid connection error
    time.sleep(60)
    return userids

def userids_combine(api, acc1, acc2):
    # get ids of two accounts
    acc1_id = api.get_user(screen_name=acc1).id
    acc2_id = api.get_user(screen_name=acc2).id
    
    # fetch ids of account's followers
    userids_acc1  = get_userids(api, acc1_id)
    userids_acc2  = get_userids(api, acc2_id)
    
    # create a df with followers' ids from both accounts
    userids = list(set(userids_acc1 + userids_acc2))
    
    df = pd.DataFrame(userids, columns=['userids'])
    # create two cols filled with boolean vals (1 if follows account, 0 - if not)
    df[acc1] = df['userids'].isin(userids_acc1).astype(int)
    df[acc2] = df['userids'].isin(userids_acc2).astype(int)
    
    fname = acc1 + "_" + acc2 + "_userids.csv"
    df.to_csv(fname, sep='\t', index=False)
    return df

# get followers of each user
def get_followers_followers(api, acc1, acc2, max_followers):
    print("Scrape user ids of followers of each follower of accounts " + acc1 + " and " + acc2 + " ... ")
    # create a df with followers' ids from both accounts
    # or open df if it is already exist
    fname = acc1 + "_" + acc2 + "_userids.csv"
    if os.path.exists(fname):
        df = pd.read_csv(fname, sep='\t')
    else:
        df = userids_combine(api, acc1, acc2)
    userids = df['userids']
    
    max_val = len(userids) if len(userids)< max_followers else max_followers
    print("Scrape followers ids of " + str(max_val) + " followers of " + acc1 + " and/or " + acc2 + " ... ")
    
    # get user ids of followers of followers of two accounts
    subdir_path, start = dir_setup(acc1, acc2)
    max_iter = max_val//100 + 1
    for i in range(start,max_iter):
        followers = {}
        for user in tqdm(userids[i*100:i*100+100]):
            followers[user] = get_userids(api, user)
        print("First " + str(i*100+100) + " entries done ...")
        # save followers 
        name = 'ids' + str(i+1) + "_" + acc1 + "_" + acc2 + '.json'
        fpath = os.path.join(subdir_path, name)
        with open(fpath, 'w') as fp:
            json.dump(followers, fp)


if __name__ == '__main__':
    start_time = time.time()
    main()
    duration = (time.time() - start_time)
    print("---scrape_twitter_ids Ended in %0.2f hour (%.3f sec) " % (duration/float(3600), duration))

        
        


