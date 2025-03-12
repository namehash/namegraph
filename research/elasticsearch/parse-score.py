
from argparse import ArgumentParser
import csv
import pprint
import json

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--scores', default='data/relevance-score.csv', help='Input file with relevance scores (CSV)')
    parser.add_argument('--output', default='data/relevance-score.jsonl', help='Output file with relevance scores (JSONL)')
    args = parser.parse_args()

    with open(args.scores) as input:
        reader = csv.reader(input)
        keywords = {}
        keyword = None
        for row in reader:
            raw_row = row
            row = [e for e in row if len(e) > 0]
            if(len(row) == 0):
                # empty row
                continue
            elif(len(row) == 1):
                # new section
                keyword = row[0]
                continue
            elif(row[0] == 'score' or row[0] == 'MH'):
                # header
                continue
            elif('.' not in raw_row[4]):
                # relevance value on invalid position or no relevance value
                continue
            elif(row[0] not in ['0', '1', '2', '3', '4', '5']):
                # no score or invalid score
                continue
            elif(len(row) < 3):
                print(f"Unknown error: {row}")
                continue

            assert len(row) >= 3, f"Row too short #{row}"
            if(keyword not in keywords):
                keywords[keyword] = {}


            values = [int(e) for e in raw_row[1:4] if len(str(e)) > 0]
            value = sum(values) / len(values)
            features = {
                "user_score": value,
                "elastic_score": float(raw_row[4]),
                "rank": int(raw_row[6]),
                "members rank mean": float(raw_row[10]),
                "members rank median": float(raw_row[11]),
                "members system interesting score mean": float(raw_row[12]),
                "members system interesting score median": float(raw_row[13]),
                "valid members count": int(raw_row[14]),
                "invalid members count": int(raw_row[15]),
                "valid members ratio": float(raw_row[16]),
                "nonavailable members count": int(raw_row[17]),
                "nonavailable members ratio": float(raw_row[18]),
                "is merged": raw_row[10] == "TRUE",
                }
            keywords[keyword][raw_row[5]] = features

    with open(args.output, "w") as output:
        for key, values in keywords.items():
            output.write(json.dumps({key: values}) + "\n")


    print(f"Number of keywords: {len(keywords)}")