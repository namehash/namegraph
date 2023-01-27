from argparse import ArgumentParser
from pathlib import Path
import json


def precision(tp, fp):
    return tp / (tp + fp) if tp + fp > 0 else 0.0


def recall(tp, fn):
    return tp / (tp + fn) if tp + fn > 0 else 0.0


def f1(tp, fp, fn):
    p, r = precision(tp, fp), recall(tp, fn)
    return 2 * (p * r) / (p + r) if p + r > 0 else 0.0


def evaluate(
        name: str,
        mapping: dict[str, list[str]],
        test_data: dict[str, list[str]],
        print_examples: bool = True
) -> None:
    # https://bestlifeonline.com/sex-emoji-combinations/
    # https://www.bustle.com/articles/118910-54-clever-new-ways-to-create-sex-emoji

    tp, fn, fp = 0, 0, 0

    print(f'============ {name} ============')
    for name, emojis in test_data.items():
        emojis = set(emojis)
        mapping_emojis = set(mapping.get(name, []))

        tps = emojis & mapping_emojis
        fns = emojis - mapping_emojis
        fps = mapping_emojis - emojis

        if print_examples and (tps or fns or fps):
            print(name)
            if name not in mapping:
                print(f'  not in the mapping fns={emojis}')
            else:
                print(f'  {tps=}, {fns=}, {fps=}')

        tp += len(tps)
        fn += len(fns)
        fp += len(fps)

    print()
    print(f'tp: {tp}, fn: {fn}, fp: {fp}')
    print(f'recall: {recall(tp, fn):.4f}, precision: {precision(tp, fp):.4f}, f1: {f1(tp, fp, fn):.4f}')
    # print(f'<td>{recall(tp, fn) * 100:05.2f}%</td> <td>{precision(tp, fp) * 100:05.2f}%</td> <td>{f1(tp, fp, fn) * 100:05.2f}%</td>')
    print(end='\n\n')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('mapping', type=str, help='path to the json mapping (name -> list of emojis)')
    parser.add_argument('test_data', type=str, nargs='+', help='path to the json mapping (name -> list of emojis)')
    parser.add_argument('--print_examples', action='store_true', help='print all the true positive, false positive and false negative examples')
    args = parser.parse_args()

    with open(args.mapping, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    for test_filepath in args.test_data:
        path = Path(test_filepath).resolve()

        with path.open('r', encoding='utf-8') as f:
            test_data = json.load(f)

        if isinstance(list(test_data.values())[0], dict):
            test_data = {k: v.get('green', []) for k, v in test_data.items()}

        evaluate(path.name, mapping, test_data, args.print_examples)
