import os
import sys
import pickle
from colorama import Fore, Style, init
from string import punctuation


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
back = 0

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
    global num_tokens
    init()
    file = fp.read()
    words = file.split()
    num_tokens = len(words)
    for i, word in enumerate(words):
        get_tag(i, word, words)

    fps["stanfordnlp-out"].writelines(stanford_ann)
    pickle.dump(spacy_ann, fps["spacy-out"])
    fps["rawtext-out"].write(fileout)

    for key in fps:
        fps[key].close()



def get_tag(i, word, words):
    global back, pos
    print_status(i)
    print_tags()
    for j in range(i - 3, i):
        if j >= 0:
            print(words[j] + " ", end="")

    print(f"{Fore.GREEN} <<" + word + f">> {Style.RESET_ALL}", end="")

    for k in range(i + 1, i + 4):
        if k < len(words):
            print(" " + words[k], end="")

    tag = input("\n\tTAG? ")
    if tag == "b" and i > 0:
        back += 1
        curr = i-1
        pos -= len(words[curr]) + 1
        while (curr <= i):
            curr = get_tag(curr, words[curr], words) + 1
    elif tag == "" or tag in valid_inputs:
        write_annotation(word, tag)
    else:
        print(f"\n{Fore.RED}Sorry, not sure what that meant. Try again.{Style.RESET_ALL}")
        get_tag(i, word, words)

    if(back > 0):
        back -= 1
    print()
    return i

def add_spacy_ann(word, tag):
    word = word.strip(punctuation)
    if(len(spacy_ann) != 0 and spacy_ann[-1][1] == pos and spacy_ann[-1][2] == valid_inputs[tag]):
        spacy_ann.append((spacy_ann[-1][0], spacy_ann[-1][1] + 1 + len(word), valid_inputs[tag]))
        spacy_ann.pop(-2)
    else:
        spacy_ann.append((pos + 1, pos + 1 + len(word), valid_inputs[tag]))

def write_back_annotation(word, tag):
    global fileout, stanford_ann, spacy_ann, pos, back
    if tag == "":
        stanford_ann[-back] = word + "\t" + "O" + "\n"
    else:
        stanford_ann[-back] = word + "\t" + stanford_core_tags[valid_inputs[tag]] + "\n"
        word = word.strip(punctuation)
        replaced = False
        for i in range(back):
            print(pos)
            print(spacy_ann[-i][0])
            if(len(spacy_ann) != 0 and spacy_ann[-i][0] == pos + 1):
                print("doing something weird")
                spacy_ann.pop(-i)
                spacy_ann.insert(-i, ((pos + 1, pos + 1 + len(word), valid_inputs[tag])))
                replaced = True
        if not replaced:
            spacy_ann.append((pos + 1, pos + 1 + len(word), valid_inputs[tag]))
    pos = pos + 1 + len(word)


def write_annotation(word, tag):
    if(back != 0):
        return write_back_annotation(word, tag)

    global fileout, stanford_ann, spacy_ann, pos

    if tag == "":
        fileout += " " + word
        stanford_ann.append(word + "\t" + "O" + "\n")
    else:
        fileout += " " + word
        stanford_ann.append(word + "\t" + stanford_core_tags[valid_inputs[tag]] + "\n")
        add_spacy_ann(word, tag)

    pos = pos + 1 + len(word)

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