"""
Cyclomatic complexity calculator for jinja2 templates
This is written with the primary usecase of quantifying complexity
in Ansible templates
"""
import argparse
import sys

import jinja2

class CFNode:
    """
    A node in a control flow graph
    """

    def __init__(self, graph, ast_node):
        self.id = graph._register_node(self)
        self.ast_node = ast_node


    def print_debug(self):
        """
        Print a representation for debugging
        """
        print("Node {}: {}".format(self.id, repr(self.ast_node)))


class CFEdge:
    """
    An edge in a control flow graph
    """

    def __init__(self, graph, from_node, to_node):
        self.id = graph._register_edge(self)
        self.from_node = from_node
        self.to_node = to_node


    def print_debug(self):
        """
        Print a representation for debugging
        """
        print("Edge {}: {} -> {}".format(
            self.id,
            self.from_node.id,
            self.to_node.id))


class CFGraph:
    """
    Generate a control flow graph from an abstract synatax tree
    """

    def __init__(self, ast):

        self.__ast = ast
        self.__nodes = []
        self.__edges = []
        # node/edge IDs to make debug printout make sense
        self.__next_node_id = 1
        self.__next_edge_id = 1

        self.__start_node, tails = self.__follow_node(self.__ast)

        # Connect all remaining tails to terminal node
        self.__end_node = CFNode(self, None)
        for tail in tails:
            edge = CFEdge(self, tail, self.__end_node)


    def get_cyclomatic_complexity(self):
        """
        Return the cyclomatic complexity of this graph
        https://en.wikipedia.org/wiki/Cyclomatic_complexity
        """
        return len(self.__edges) - len (self.__nodes) + 2


    def print_debug(self):
        """
        Print a text representation of the graph for debugging
        """
        print("Nodes:")
        for node in self.__nodes:
            node.print_debug()

        print("Edges:")
        for edge in self.__edges:
            edge.print_debug()
            

    def __follow_node(self, ast_node):
        """
        Dispatch by node type. Returns a new child node and a
        list of trailing child nodes
        """

        this_node = CFNode(self, ast_node)

        tails = None
        if isinstance(ast_node, jinja2.nodes.If):
            tails = self.__follow_if_node(ast_node, this_node)
        elif isinstance(ast_node, jinja2.nodes.For):
            tails = self.__follow_for_node(ast_node, this_node)
        else:
            tails = self.__follow_simple_node(ast_node, this_node)

        return this_node, tails


    def __follow_simple_node(self, ast_node, cfg_node):
        """
        Process subtree for a simple node and return tailing children
        A simple node is a node with one outgoing edge
        """

        # If a simple node has children, then the edge points to
        # the first child
        tails = self.__follow_children(ast_node.iter_child_nodes(), cfg_node)
        if not tails:
            tails = [cfg_node]
        return tails


    def __follow_if_node(self, ast_node, cfg_node):
        """
        Process subtree for an if  node and return tailing children
        A simple node is a node with one outgoing edge
        """

        tails = self.__follow_children(ast_node.body, cfg_node)

        # the elif_ elements of an if node are themselves if nodes
        for ast_elif_child in ast_node.elif_:
            elif_node, elif_tails = self.__follow_node(ast_elif_child)
            CFEdge(self, cfg_node, elif_node)
            tails.extend(elif_tails)

        if ast_node.else_:
            else_tails = self.__follow_children(ast_node.else_, cfg_node)
            tails.extend(else_tails)

        return tails


    def __follow_for_node(self, ast_node, cfg_node):
        """
        Process subtree for a for  node and return tailing children
        A simple node is a node with one outgoing edge
        """

        tails = self.__follow_children(ast_node.body, cfg_node) 
        # Connect tails of loop back to head
        for tail in tails:
            CFEdge(self, tail, cfg_node)

        if ast_node.else_:
            else_tails = self.__follow_children(ast_node.else_, cfg_node)
            tails.extend(else_tails)

        # TODO: test for x in y if z

        # TODO: break?
        # TODO: continue?

        return tails

    
    def __follow_children(self, ast_child_iter, cfg_node):
        """
        Process children of this node and move on to the next node.
        Links passed cfg node to first child, and each child to the
        next child. Returns trailing children.
        """

        tails = [cfg_node]
        for ast_child_node in ast_child_iter:

            new_head, new_tails = self.__follow_node(ast_child_node)

            # the tails of the last child point to this child
            for tail in tails:
                CFEdge(self, tail, new_head)

            tails = new_tails

        return tails


    def _register_node(self, node):
        """
        Add a node to the graph
        """
        self.__nodes.append(node)
        self.__next_node_id += 1
        return self.__next_node_id - 1


    def _register_edge(self, edge):
        """
        Add an edge to the graph
        """
        self.__edges.append(edge)
        self.__next_edge_id += 1
        return self.__next_edge_id - 1


def main():
    """
    Parse arguments, run script
    """

    arg_parser = argparse.ArgumentParser(description="Calculate cyclomatic "
            "complexity of a jinja2 template")
    arg_parser.add_argument('input_filename')
    args = arg_parser.parse_args()

    source = ""
    with open(args.input_filename) as input_file:
        for line in input_file:
            source += line
            source += "\n"

    # Features not currently in scope:
    # - template inheritance
    # - includes
    # - macros
    # - recursive loops
    # I'm sure somebody has a use for these, but I pray it's not in Ansible

    # TODO: put test cases into unit tests

    env = jinja2.Environment()
    ast = env.parse(source)

    print(repr(ast))
    graph = CFGraph(ast)
    graph.print_debug()
    print(graph.get_cyclomatic_complexity())

if __name__ == "__main__":
    main()
