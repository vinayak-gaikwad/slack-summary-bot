import json
import statistics
from rouge_score import rouge_scorer

file_path = "test_response_phi_samsum.json"

with open(file_path, "r") as file:
    data = json.load(file)

scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

rouge1_scores = []
rouge2_scores = []
rougeL_scores = []

for obj in data:
    actual_summary = obj["summary"]
    llm_summary = obj["model_response"]

    scores = scorer.score(actual_summary, llm_summary)

    rouge1_scores.append(scores["rouge1"].fmeasure)
    rouge2_scores.append(scores["rouge2"].fmeasure)
    rougeL_scores.append(scores["rougeL"].fmeasure)

rouge1_avg = statistics.mean(rouge1_scores)
rouge1_med = statistics.median(rouge1_scores)

rouge2_avg = statistics.mean(rouge2_scores)
rouge2_med = statistics.median(rouge2_scores)

rougeL_avg = statistics.mean(rougeL_scores)
rougeL_med = statistics.median(rougeL_scores)

print("ROUGE-1 Average F-measure:", rouge1_avg)
print("ROUGE-1 Median F-measure:", rouge1_med)
print()
print("ROUGE-2 Average F-measure:", rouge2_avg)
print("ROUGE-2 Median F-measure:", rouge2_med)
print()
print("ROUGE-L Average F-measure:", rougeL_avg)
print("ROUGE-L Median F-measure:", rougeL_med)
