import ast
import astunparse


class CFGNode(dict):
    def __init__(self, parents, rid, ast_node=None):
        super().__init__()
        assert type(parents) is list
        self.parents = parents
        self.children = []
        self.ast_node = ast_node
        self.rid  = rid

        # dynamic attributes
        self.return_nodes = None
        self.exit_nodes = None

    def lineno(self):
        return self.ast_node.lineno if hasattr(self.ast_node, 'lineno') else 0

    def __str__(self):
        return ("id:%d line[%d] parents: %s : %s" %
                (self.rid, self.lineno(), str([p.rid for p in self.parents]), self.source()))

    def __repr__(self):
        return str(self)

    def add_child(self, c):
        if c not in self.children:
            self.children.append(c)

    def __eq__(self, other):
        return self.rid == other.rid

    def __neq__(self, other):
        return self.rid != other.rid

    def set_parents(self, p):
        self.parents = p

    def add_parent(self, p):
        if p not in self.parents:
            self.parents.append(p)

    def add_parents(self, ps):
        for p in ps:
            self.add_parent(p)

    def source(self):
        return astunparse.unparse(self.ast_node).strip()

    def to_json(self):
        return {
            'id':self.rid,
            'parents': [p.rid for p in self.parents],
            'children': [c.rid for c in self.children],
            'source':self.source()
        }

class StmtCFG:
    def __init__(self):
        self.registry = 0
        self.nodes = {}

        self.starter = self.gen_node(parents=[], ast_node=ast.parse('start').body[0])
        self.starter.ast_node.lineno = 0
        self.functions = {}
        self.last_node = None
        self.code_ast = None

    def parse(self, src):
        self.code_ast = ast.parse(src)
        return self.code_ast

    def gen_node(self, **kwargs):
        kwargs["rid"] = self.registry
        cfg_node = CFGNode(**kwargs)
        self.registry += 1
        self.nodes[cfg_node.rid] = cfg_node
        return cfg_node

    def walk(self, node, myparents):
        if node is None:
            return None
        fname = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, fname):
            fn = getattr(self, fname)
            v = fn(node, myparents)
            return v
        else:
            raise NotImplementedError(f"{fname} is not implemented")

    def on_module(self, node, myparents):
        """
        Module(stmt* body, type_ignore* type_ignores)
        """

        p = myparents
        for n in node.body:
            p = self.walk(n, p)
        return p

    def on_functiondef(self, node, myparents):
        """
        FunctionDef(identifier name, arguments args,
                       stmt* body, expr* decorator_list, expr? returns,
                       string? type_comment, type_param* type_params)
        """

        fname = node.name

        func_node = self.gen_node(parents=[], ast_node=node)
        func_node.return_nodes = []

        p = [func_node]
        for n in node.body:
            p = self.walk(n, p)

        for n in p:
            if n not in func_node.return_nodes:
                func_node.return_nodes.append(n)

        self.functions[fname] = func_node

        return myparents

    def on_return(self, node, myparents):
        """
        Return(expr? value)
        """

        parent = myparents[0]

        # on return look back to the function definition.
        while parent.return_nodes is None:
            parent = parent.parents[0]
        assert parent.return_nodes is not None

        p = self.gen_node(parents=myparents, ast_node=node)

        # make the return one of the parents of label node.
        parent.return_nodes.append(p)

        # return does not have immediate children
        return []

    def on_assign(self, node, myparents):
        """
        Assign(expr* targets, expr value, string? type_comment)
        """

        if len(node.targets) > 1:
            raise NotImplementedError('Parallel assignments')

        p = [self.gen_node(parents=myparents, ast_node=node)]

        return p

    def on_augassign(self, node, myparents):
        """
        AugAssign(expr target, operator op, expr value)
        """

        p = [self.gen_node(parents=myparents, ast_node=node)]
        return p

    def on_for(self, node, myparents):
        """
        For(expr target, expr iter, stmt* body, stmt* orelse, string? type_comment)
        """

        if len(node.orelse) > 0:
            raise NotImplementedError("For else usage not implemented")
        for_node = self.gen_node(parents=myparents, ast_node=node)

        # we attach the label node here so that break can find it.
        for_node.exit_nodes = []

        # now we evaluate the body, one at a time.
        p1 = [for_node]
        for n in node.body:
            p1 = self.walk(n, p1)

        for_node.add_parents(p1)

        return for_node.exit_nodes + p1

    def on_while(self, node, myparents):
        """
        While(expr test, stmt* body, stmt* orelse)
        """

        if len(node.orelse) > 0:
            raise NotImplementedError("While else usage not implemented")

        while_node = self.gen_node(parents=myparents, ast_node=node)


        # we attach the label node here so that break can find it.
        while_node.exit_nodes = []

        # now we evaluate the body, one at a time.
        p1 = [while_node]
        for n in node.body:
            p1 = self.walk(n, p1)

        while_node.add_parents(p1)

        return while_node.exit_nodes + p1

    def on_if(self, node, myparents):
        """
        If(expr test, stmt* body, stmt* orelse)
        """

        if_node = self.gen_node(parents=myparents, ast_node=node)
        ast.copy_location(if_node.ast_node, node.test)
        g1 = [if_node]
        for n in node.body:
            g1 = self.walk(n, g1)
        g2 = [if_node]
        for n in node.orelse:
            g2 = self.walk(n, g2)

        return g1 + g2

    def on_with(self, node, myparents):
        """
        With(withitem* items, stmt* body, string? type_comment)
        """

        p = [self.gen_node(parents=myparents, ast_node=node)]
        for n in node.body:
            p = self.walk(n,p)
        return p

    def on_import(self, node, myparents):
        """
        Import(alias* names)
        """

        p = self.gen_node(parents=myparents, ast_node=node)
        return [p]

    def on_importfrom(self, node, myparents):
        """
        ImportFrom(identifier? module, alias* names, int? level)
        """

        p = self.gen_node(parents=myparents, ast_node=node)
        return [p]

    def on_expr(self, node, myparents):
        """
        Expr(expr value)
        """

        p = [self.gen_node(parents=myparents, ast_node=node)]
        return p

    def on_pass(self, node, myparents):
        """
        Pass
        """

        return [self.gen_node(parents=myparents, ast_node=node)]

    def on_break(self, node, myparents):
        """
        Break
        """

        parent = myparents[0]
        while parent.exit_nodes is None:
            # we have ordered parents
            parent = parent.parents[0]

        assert parent.exit_nodes is not None
        p = self.gen_node(parents=myparents, ast_node=node)

        # make the break one of the parents of original test node.
        parent.exit_nodes.append(p)

        # break does not have immediate children
        return []

    def on_continue(self, node, myparents):
        """
        continue
        """

        parent = myparents[0]
        while parent.exit_nodes is None:
            # we have ordered parents
            parent = parent.parents[0]
        assert parent.exit_nodes is not None
        p = self.gen_node(parents=myparents, ast_node=node)

        # make continue one of the parents of the original test node.
        parent.add_parent(p)

        # return the parent because a stmt continue is not the parent
        # for the just next node
        return []

    def update_children(self):
        for nid,node in self.nodes.items():
            for p in node.parents:
                p.add_child(node)

    def get_function_by_name(self, name):
        """
        :param name:
        :return: the function def head node.
        """
        return self.functions[name]

    @classmethod
    def gen_cfg(cls, src):
        cfg = cls()
        node = cfg.parse(src)
        nodes = cfg.walk(node, [cfg.starter])
        cfg.last_node = cfg.gen_node(parents=nodes, ast_node=ast.parse('stop').body[0])
        ast.copy_location(cfg.last_node.ast_node, cfg.starter.ast_node)
        cfg.update_children()
        return cfg