import sys, os, time, json
sys.path.insert(0, "/home/luiz/Documentos/Strata/Shared/_analysis/ontology")
import validate_ontology_v4 as v

t0 = time.time()
modules, shapes, instances, invalid, per = v.load_graphs()
full = modules + instances
v.full_graph = full
chosen, strata, total = v.select_confrontations(full, 3)
proj = v.build_projection(full, chosen)
print("projection triples:", len(proj), "build time", round(time.time() - t0, 2), flush=True)
t1 = time.time()
aux, decisions, epistemic, ties = v.build_mirror(proj, chosen)
print("mirror time", round(time.time() - t1, 2), flush=True)
mirror = v.read_mirror(aux, chosen)
print(json.dumps(mirror[chosen[0]], indent=1), flush=True)
print("decisions:", decisions, "epistemic:", epistemic, "ties:", ties, flush=True)
core = v.python_core_side(proj, chosen)
for c in chosen:
    mid, low = core[c]["central"], core[c]["pessimistic"]
    print(c, "core:", round(mid["aa"], 6), round(low["aa"], 6), round(mid["D"], 6),
          round(mid["S2"], 6), round(mid["S3"], 6), round(mid["S4"], 6), round(mid["u"], 6),
          round(mid["phi"], 6), round(low["ratio"], 6), core[c]["decision"], flush=True)
stored = v.stored_values(full, chosen)
for c in chosen:
    print(c, stored[c], flush=True)
print(json.dumps(v.compare(mirror, core, stored), indent=1), flush=True)
