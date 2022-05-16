import json
import numpy as np
import pandas as pd
import argparse
import os
import networkx as nx
from pyvis.network import Network

parser = argparse.ArgumentParser()
parser.add_argument("account 1", type=str, action="store")
parser.add_argument("account 2", type=str, action="store")

args = parser.parse_args()
args_dict = vars(args)
account1 = args_dict['account 1']
account2 = args_dict['account 2']

# check if data is scraped
dataset_dir = 'scraped_ids' 
subdir = account1 + "_" + account2
subdir_path = os.path.join(os.getcwd(), dataset_dir, subdir)
if os.path.exists(subdir_path):
    print("Fetching scraped data ...")
else:
    print("Scrape data first!")

# open JSON files with scraped followers
followers = {}
files_list = os.listdir(subdir_path)
for f in files_list:
    if not f.startswith('.'):
        fpath = os.path.join(subdir_path, f)
        with open(fpath) as json_file:
            f = json.load(json_file)
        followers.update(f)
nodes = list(followers.keys())

# open df with info about accounts' followers
fname = account1 + "_" + account2 + "_userids.csv"
df = pd.read_csv(fname, sep='\t')

# assign colors
color_map = []

for node in nodes:
    if (df[df['userids']==int(node)][str(account1)]==1).values and (df[df['userids']==int(node)][str(account2)]==1).values:
        color_map.append('#D85678')
    elif (df[df['userids']==int(node)][str(account1)]==1).values:
        color_map.append('#FFA500')
    else:
        color_map.append('#6495ed')

# create graph
G = nx.DiGraph()
# add color to each node according to its belonging to acc1, acc2 or acc1+acc2
for i, node in enumerate(nodes):
    G.add_node(node, color=color_map[i])

for node in nodes:
    # nodes is a list of strings
    # followers[node] returns list of ints
    for follower in followers[node]:
        if str(follower) in followers:
            # iteration of followers returns keys, which are strings
            # nodes in G are str
            G.add_edge(str(follower), node)

print("n.o. nodes & n.o. edges before deleting singletons", G.number_of_nodes(), G.number_of_edges())
G.remove_nodes_from(list(nx.isolates(G)))
print("n.o. nodes & n.o. edges after deleting singletons", G.number_of_nodes(), G.number_of_edges())

# create a network
net = Network(height='800px', width='100%', directed=True, notebook=False)

net.add_node(account1, size=20, color='#f54242', label=account1, font='30px arial black')
net.add_node(account2, size=20, color='#427ef5', label=account2, font='30px arial black')

for n in G.nodes:
    color = G.nodes[n]['color']
    net.add_node(n, size=20, color=color)
    if G.nodes[n]['color'] == '#D85678':
        net.add_edge(n, account1)
        net.add_edge(n, account2)
    elif  G.nodes[n]['color'] == '#FFA500':
        net.add_edge(n, account1)
    else:
        net.add_edge(n, account2)
        
for n1,n2, attrs in G.edges.data():
    net.add_edge(n1, n2)

net.toggle_physics(True)
# net.show_buttons()
# net.show('mygraph.html')

net.show_buttons(filter_=['physics'])
net.show(account1 + "_" + account2 + '_graph.html')