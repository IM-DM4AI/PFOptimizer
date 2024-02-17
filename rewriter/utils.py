import pygraphviz
from rewriter.cfg import StmtCFG
from examples.example_codes import aWhileLoop

def stmt_cfg_viz(cfg: StmtCFG):
    G = pygraphviz.AGraph(directed=True)
    nodes = cfg.nodes

    for nid, cnode in nodes.items():
        G.add_node(cnode.rid)
        n = G.get_node(cnode.rid)
        lineno = cnode.lineno()
        n.attr['label'] = "%d: %s" % (nid, lineno)
        for pn in cnode.parents:
            G.add_edge(pn.rid, cnode.rid, color='blue')

    return G


if __name__ == '__main__':
    acfg = StmtCFG.gen_cfg(aWhileLoop)
    g = stmt_cfg_viz(acfg)
    print(g)
    g.layout()
    g.draw("exp.png")