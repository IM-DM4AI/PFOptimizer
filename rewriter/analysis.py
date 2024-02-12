from rewriter.cfg import PyCFG, CFGNode


def slurp(f):
    with open(f, 'r') as f: return f.read()

def get_cfg(pythonfile):
    cfg = PyCFG()
    cfg.gen_cfg(slurp(pythonfile).strip())
    cache = CFGNode.cache
    g = {}
    for k,v in cache.items():
        j = v.to_json()
        at = j['at']
        parents_at = [cache[p].to_json()['at'] for p in j['parents']]
        children_at = [cache[c].to_json()['at'] for c in j['children']]
        if at not in g:
            g[at] = {'parents':set(), 'children':set()}
        # remove dummy nodes
        ps = set([p for p in parents_at if p != at])
        cs = set([c for c in children_at if c != at])
        g[at]['parents'] |= ps
        g[at]['children'] |= cs
        if v.calls:
            g[at]['calls'] = v.calls
        g[at]['function'] = cfg.functions_node[v.lineno()]
    return g, cfg.founder.ast_node.lineno, cfg.last_node.ast_node.lineno

def compute_dominator(cfg, start = 0, key='parents'):
    dominator = {start: {start}}
    all_nodes = set(cfg.keys())
    rem_nodes = all_nodes - {start}
    for n in rem_nodes:
        dominator[n] = all_nodes

    c = True
    while c:
        c = False
        for n in rem_nodes:
            pred_n = cfg[n][key]
            doms = [dominator[p] for p in pred_n]
            i = set.intersection(*doms) if doms else set()
            v = {n} | i
            if dominator[n] != v:
                c = True
            dominator[n] = v
    return dominator


def compute_flow(pythonfile):
    cfg,first,last = get_cfg(pythonfile)
    return cfg, compute_dominator(cfg, start=first), compute_dominator(cfg, start=last, key='children')

