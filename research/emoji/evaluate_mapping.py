from argparse import ArgumentParser
import json


def precision(tp, fp):
    return tp / (tp + fp) if tp + fp > 0 else 0.0


def recall(tp, fn):
    return tp / (tp + fn) if tp + fn > 0 else 0.0


def f1(tp, fp, fn):
    p, r = precision(tp, fp), recall(tp, fn)
    return 2 * (p * r) / (p + r) if p + r > 0 else 0.0


def evaluate_vulgarisms(mapping: dict[str, list[str]], print_examples: bool = True) -> None:
    # https://bestlifeonline.com/sex-emoji-combinations/
    # https://www.bustle.com/articles/118910-54-clever-new-ways-to-create-sex-emoji

    test = {
        'penis': ['🍆', '🥒', '🌭', '🍌', '🥖', '🕹'],
        'dick': ['🍆', '🥒', '🌭', '🍌', '🥖', '🕹'],
        'anal': ['👌', '🍩', '🕳'],
        'butthole': ['👌', '🍩', '🕳'],
        'blowjob': ['🌬️'],
        'bdsm': ['⛓', '🔒'],
        'cock': ['🍆', '🥒', '🌭', '🍌', '🥖', '🐓', '🕹'],
        'cunnilingus': ['👅', '😛'],
        'crap': ['💩'],
        'ass': ['🍑'],
        'butt': ['🍑'],
        'fuck': ['🖕'],  # todo add a sequence of emojis, do we want that? how can we achieve that?
        'tits': ['🍒', '🤗'],
        'boobs': ['🍒', '🤗'],
        'dildo': ['🍆', '🥒', '🌭', '🍌', '🥖', '🕹'],
        # 'hooker': [],   # some woman, girl?  👠?
        'nigga': ['👨🏿', '👦🏿', '🧔🏿‍♂️', '👴🏿', '🧑🏿'],
        'panties': ['👙'],
        'pussy': ['✌', '🌮', '🥟', '🐱', '😺'],
        'nude': ['👙', '🔞'],
        'semen': ['💦', '🍾'],
        'cum': ['💦', '🍾'],
        'shit': ['💩'],
        'spank': ['🏓'],
        'orgasm': ['💦', '🍾'],
        # 'slut': [],  # some woman, girl?  👠?
        # 'threesome': [],  # thought first of some family emoji with 3 people, but there are kids there, don't know if there is an emoji with 3 adults and whether it is ok
        'upskirt': ['✌', '🌮', '🥟'],
        'vagina': ['✌', '🌮', '🥟'],
        'wet': ['💦']
    }

    tp, fn, fp = 0, 0, 0

    print('============ VULGARISMS ============')
    for name, emojis in test.items():
        emojis = set(emojis)
        mapping_emojis = set(mapping.get(name, []))

        tps = emojis & mapping_emojis
        fns = emojis - mapping_emojis
        fps = mapping_emojis - emojis

        if print_examples:
            print(name)
            if name not in mapping:
                print(f'  not in the mapping')
            else:
                print(f'  {tps=}, {fns=}, {fps=}')

        tp += len(tps)
        fn += len(fns)
        fp += len(fps)

    print()
    print(f'tp: {tp}, fn: {fn}, fp: {fp}')
    print(f'recall: {recall(tp, fn):.4f}, precision: {precision(tp, fp):.4f}, f1: {f1(tp, fp, fn):.4f}')
    print(end='\n\n')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('mapping', type=str, help='path to the json mapping (name -> list of emojis)')
    parser.add_argument('--print_examples', action='store_true', help='print all the true positive, false positive and false negative examples')
    args = parser.parse_args()

    with open(args.mapping, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    evaluate_vulgarisms(mapping, args.print_examples)
