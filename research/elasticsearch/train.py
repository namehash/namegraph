
import json
from argparse import ArgumentParser
import subprocess
import copy
import re
import tqdm

GLOBAL_PARAMS = ["java", "-jar", "ranklib-ranklib-2.10.1/target/ranklib-2.10.1.jar"]

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--train', help='file with training data')
    parser.add_argument('--test', help='file with testing data')
    parser.add_argument('--reports', help='directory with training reports')
    parser.add_argument('--models', help='directory with created models')
    parser.add_argument('--metric', help='metric to optimize during training', default='NDCG@10')
    parser.add_argument('--experiment', help='the ID of the experiment used as a prefix to reports, models, etc.')
    args = parser.parse_args()


    def model_dir(args):
        return f"{args.models}/{args.experiment}-{args.metric}/"

    def model_path(args, model_id):
        return f"{model_dir(args)}{model_id}.model"

    def report_dir(args):
        return f"{args.reports}/{args.experiment}-{args.metric}/"

    def report_path(args, model_id):
        return f"{report_dir(args)}{model_id}.report"    

    MODEL_RANGE = 10

    # train the models
    #for i in {0..9}; do java -jar ranklib-ranklib-2.10.1/target/ranklib-2.10.1.jar \
    # -train data/features-11.05.2023-train.ranklib -test data/fetures-11.05.2023-test.ranklib \
    # -metric2t 'NDCG@10' -ranker $i -save data/ranklib-n10-imputed-$i.model  2>&1 | grep -v 'maj' | tee  data/ranklib-n10-imputed-$i.txt; done
    subprocess.run(["mkdir", "-p", model_dir(args)], capture_output=True)
    print("Training models")
    for model_id in tqdm.tqdm(range(MODEL_RANGE)):

        params = copy.copy(GLOBAL_PARAMS)
        params += ["-train", args.train]
        params += ["-test", args.test]
        params += ["-metric2t", args.metric]
        params += ["-ranker", str(model_id)]
        params += ["-save", model_path(args, model_id)]
        params += ["-gmax", "5"]

        result = subprocess.run(params, capture_output=True)


    # evaluate on train and test datasets
    #java -jar ranklib-ranklib-2.10.1/target/ranklib-2.10.1.jar 
    # -test data/features-11.05.2023-train.ranklib  -metric2T NDCG@10 -idv data/report-n10-$i-train.txt  
    # -load data/ranklib-n10-$i.mode
    subprocess.run(["mkdir", "-p", report_dir(args)], capture_output=True)

    params = copy.copy(GLOBAL_PARAMS)
    params += ["-test", args.test]
    params += ["-metric2T", args.metric]
    params += ["-idv", report_path(args, "baseline")]
    params += ["-gmax", "5"]
    result = subprocess.run(params, capture_output=True)

    print("Testing models")
    for model_id in tqdm.tqdm(range(MODEL_RANGE)):

        params = copy.copy(GLOBAL_PARAMS)
        params += ["-test", args.test]
        params += ["-metric2T", args.metric]
        params += ["-idv", report_path(args, model_id)]
        params += ["-load", model_path(args, model_id)]
        params += ["-gmax", "5"]

        result = subprocess.run(params, capture_output=True)


    # create an analysis
    # java -cp ranklib-ranklib-2.10.1/target/ranklib-2.10.1.jar ciir.umass.edu.eval.Analyzer 
    # -all data/reports/n10-train -base report-baseline.txt 2>&1 | grep -v 'maj'  > data/reports/n10-train-analysis.txt
    params = ["java", "-cp", "ranklib-ranklib-2.10.1/target/ranklib-2.10.1.jar", "ciir.umass.edu.eval.Analyzer"]
    params += ["-all", report_dir(args)]
    params += ["-base", "baseline.report"]

    result = subprocess.run(params, capture_output=True)
    with open(f"{args.reports}/{args.experiment}-{args.metric}-analysis.txt", "w") as output:
        for line in (str(result.stderr).split("\\n")):
            if(re.match("maj", line)):
                continue
            output.write(re.sub(r"\\t", "\t", line)[6:] + "\n")




