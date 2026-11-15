"""Quick diagnostic: is the negative kappa between model decisions and the gold
consensus a real systematic disagreement or an artefact of label alignment?

Reads the first 3000 (case, persona) pairs from the r4 corpus and prints the
confusion matrix. Writes nothing; pure diagnostic.
"""
import json
import itertools
from collections import Counter

R4 = "/home/luiz/Documentos/Strata/Shared/Evaluacoes/r4"


def key_of(row):
    for k in ("persona_id", "profile_id", "agent", "persona"):
        if k in row:
            return (row["case_id"], row[k])
    return (row["case_id"], None)


def main():
    gold = {}
    with open(R4 + "/corpus_v5_gold.jsonl") as fh:
        for line in itertools.islice(fh, 5000):
            r = json.loads(line)
            gold[key_of(r)] = r
    cm, cg, conf = Counter(), Counter(), Counter()
    n = agree = 0
    with open(R4 + "/corpus_v5_confrontations.jsonl") as fh:
        for line in itertools.islice(fh, 5000):
            r = json.loads(line)
            k = key_of(r)
            if k not in gold:
                continue
            n += 1
            m, gdec = r["decision"], gold[k]["consensus"]
            cm[m] += 1
            cg[gdec] += 1
            conf[(m, gdec)] += 1
            agree += (m == gdec)
    print(f"pairs={n} agreement={agree/max(n,1):.4f}")
    print("model:", dict(cm))
    print("gold :", dict(cg))
    print("top confusion cells:")
    for (m, gdec), v in sorted(conf.items(), key=lambda x: -x[1])[:15]:
        print(f"  model={m:18} gold={gdec:18} {v}")
    print("gold keys sample:", list(gold)[:3])


if __name__ == "__main__":
    main()
