import os
import sys
import pickle
from colorama import Fore, Style, init
from string import punctuation

from token import Token


fps = {}
valid_inputs = {"0": "PERSON", "1": "NORP", "2": "LOC", "3": "FAC",
                "4": "ORG", "5": "GPE", "6": "EVENT", "7": "QUANTITY"}

stanford_core_tags = {"PERSON": "PERSON", "NORP": "O", "LOC": "LOCATION", "FAC": "O",
                       "ORG": "O", "GPE": "LOCATION", "EVENT": "O", "QUANTITY": "O"}

stanford_ann = []
spacy_ann = []
fileout = ""

num_tokens = 0
pos = 0
window = 5
back = 0
curr_token = 0
internal = []


def print_status(token_idx):
    num_blocks_filled = int((token_idx/num_tokens) * 10)
    blocks_filled = '=' * num_blocks_filled
    blocks_empty = ' ' * (10 - num_blocks_filled)
    print(f"Progress: {Fore.BLUE}[{blocks_filled}{blocks_empty}]{Style.RESET_ALL} - {int(token_idx / num_tokens * 100)}% of {num_tokens} tokens")


def print_tags():
    print("TAG OPTIONS: (press enter to leave untagged, b to go back)")
    print("0 people, including fictional\t\t4 companies, institutions, etc.")
    print("1 nationalities, religions\t\t5 countries, cities, states")
    print("2 mountains, rivers, etc.\t\t6 events--named hurricanes, etc")
    print("3 buildings, airports, etc.\t\t7 measurements (e.g. weight, distance)")


def annotate(fp):
    global num_tokens, curr_token, internal
    init()
    file = fp.read()
    words = file.split()
    num_tokens = len(words)
    while(curr_token < num_tokens):
        get_tag(words[curr_token], words)

    compute_all()

    fps["stanfordnlp-out"].writelines(stanford_ann)
    pickle.dump(spacy_ann, fps["spacy-out"])
    fps["rawtext-out"].write(fileout)

    for key in fps:
        fps[key].close()

    for tok in internal:
        print(tok)

def get_tag(curr_token_word, words):
    global back, pos, internal, curr_token
    print_status(curr_token)
    print_tags()
    for j in range(curr_token - window, curr_token):
        if j >= 0:
            print(words[j] + " ", end="")

    print(f"{Fore.GREEN} <<" + curr_token_word + f">> {Style.RESET_ALL}", end="")

    for k in range(curr_token + 1, curr_token + window + 1):
        if k < len(words):
            print(" " + words[k], end="")

    if len(internal) <= curr_token:
        # add current token to internal list
        internal.append(Token(words[curr_token], pos, len(words[curr_token])))

    tag = input("\n\tTAG? ")
    if tag == "b" and curr_token > 0:
        pos -= internal[curr_token - 1].length + 1 # step back to the beginning of last word
        curr_token -= 1
    elif tag == "" or tag in valid_inputs:
        if tag in valid_inputs:
            internal[curr_token].tag = tag
        pos += internal[curr_token].length + 1
        curr_token += 1
    else:
        print(f"\n{Fore.RED}Sorry, not sure what that meant. Try again.{Style.RESET_ALL}")
    print()

def compute_spacy_ann():
    global internal, spacy_ann
    for tok in internal:
        if tok.tag != -1:
            spacy_ann.append((tok.pos, tok.pos + tok.length, valid_inputs[tok.tag]))


def compute_stanford_ann():
    global internal, stanford_ann
    for tok in internal:
        stanford_tag = 'O'
        if tok.tag != -1:
            stanford_tag = stanford_core_tags[valid_inputs[tok.tag]]
        stanford_ann.append(tok.word + "\t" + stanford_tag + "\n")

def compute_rawtext():
    global fileout
    for tok in internal:
        fileout += tok.word + " "

def compute_all():
    global internal, spacy_ann, stanford_ann, fileout
    for tok in internal:
        fileout += tok.word + " "
        stanford_tag = '0'
        if tok.tag != -1:
            stanford_tag = stanford_core_tags[valid_inputs[tok.tag]]
            spacy_ann.append((tok.pos, tok.pos + tok.length, valid_inputs[tok.tag]))
        stanford_ann.append(tok.word + "\t" + stanford_tag + "\n")

def prompt_for_file_or_dir():
    pass


if __name__ == "__main__":
    filename = ""
    write_dir = ""
    init()
    if len(sys.argv) < 3:
        filename = prompt_for_file_or_dir()
    else:
        filename = sys.argv[1]
        write_dir = sys.argv[2]
        if len(sys.argv) > 3:
            window = int(sys.argv[3])

    fps["input"] = open(filename, encoding="utf8")
    fps["stanfordnlp-out"] = open(os.path.join(write_dir, filename.split("/")[-1].split(".")[0]+ "-stanfordnlp.tsv"), "w+", encoding="utf8")
    fps["spacy-out"] = open(os.path.join(write_dir, filename.split("/")[-1].split(".")[0]+ "-spacy.pkl"), "wb+")
    fps["rawtext-out"] = open(os.path.join(write_dir, filename.split("/")[-1].split(".")[0]+ "-rawtext.txt"), "w+", encoding="utf8")

    annotate(open(filename, encoding="utf8"))


"""
error handling for files
write to out formats
pause mid-annotating file
strip punctuation from spacy distances ?
fix line endings
make going back work for tags
combine spacy tags
"""