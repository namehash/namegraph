from argparse import ArgumentParser

import gensim

if __name__ == '__main__':
    parser = ArgumentParser(description="Convert text embeddings to Pickle.")
    parser.add_argument('input', help='input embeddings in text format (enwiki_20180420_100d.txt.processed)')
    parser.add_argument('output', help='output embeddings in Pickle format (enwiki_20180420_100d.txt.processed.pkl)')
    args = parser.parse_args()

    model = gensim.models.keyedvectors.KeyedVectors.load_word2vec_format(args.input, binary=False)
    model.save(args.output)
