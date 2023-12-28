import time
from tsp_models import *
import networkx as nx

def find_min_cut(graph):
    """
    Utilizza NetworkX o un'altra libreria per calcolare il min-cut (taglio minimo) nella rete
    'graph' è il grafo basato sulla soluzione corrente (utilizza il solver CPLEX per ottenere gli archi selezionati)
    """
    return nx.minimum_cut(graph, source=1, terminal=2)  # Esempio di calcolo minimo taglio con NetworkX

def add_violated_constraints(model, x, min_cut_partition):
    """
    Aggiungi i vincoli violati (archi nel min-cut) al modello PLI
    """
    (s_set, t_set) = min_cut_partition
    # compute arc list as list of {'from': v, 'to': q} dictionaries
    arc_list = [{'from': v, 'to': q} for v in s_set for q in t_set]
    violated_constraints = [x[(arc['from'], arc['to'])] for arc in arc_list]
    model.add_constraint(model.sum(violated_constraints) >= 1)

def create_graph(solution, num_vertices):
    graph = nx.DiGraph()
    
    for i in range(num_vertices):
        for j in range(num_vertices):
            if i != j:
                if solution.get_value(f"x_{i}_{j}") > 0.5:
                    graph.add_edge(i, j, capacity=1)

    return graph


def solve_with_max_flow(costs_matrix, visualize=True, print_time=True):
    print("Max Flow")

    num_vertices = len(costs_matrix)

    model, x = create_assignment_problem_model(costs_matrix)

    subtours_present = True

    start_time = time.time()

    solution = model.solve()

    while subtours_present:
        subtours_present = False
        for node in range(1, num_vertices):
            graph = create_graph(solution, num_vertices)
            max_flow_value = nx.maximum_flow_value(graph, 0, node)
            #max_flow= nx.maximum_flow(graph, 0, node) # TODO: remove
            #print(f"Max flow: {max_flow}") # TODO: remove
            if max_flow_value < 1:
                subtours_present = True
                _, partition = nx.minimum_cut(graph, 0, node)
                #print(f"Partition: {partition}")
                add_violated_constraints(model, x, partition)
        solution = model.solve()

    if print_time:
        print("\tTime:", time.time() - start_time)

    if visualize:
        utils.print_tours(solution, num_vertices, method_name="Max Flow")

    print("\tTotal Cost:   ", solution.get_objective_value())


def solve_with_cut_set(costs_matrix, visualize=True, print_time=True):
    print("Cut Set")
    num_vertices = len(costs_matrix)

    model = create_cut_set_model(costs_matrix)

    start_time = time.time()
    solution = model.solve()
    if print_time:
        print("\tTime:", time.time() - start_time)

    if visualize:
        utils.print_tours(solution, num_vertices, method_name="Cut Set")

    print("\tTotal Cost:   ", solution.get_objective_value())


def solve_with_subtour_elimination(costs_matrix, visualize=True, print_time=True):
    print("Subtour Elimination")
    num_vertices = len(costs_matrix)

    model = create_subtour_elimination_model(costs_matrix)

    start_time = time.time()
    solution = model.solve()
    if print_time:
        print("\tTime:", time.time() - start_time)

    if visualize:
        utils.print_tours(solution, num_vertices,
                          method_name="Subtour Elimination")

    print("\tTotal Cost:   ", solution.get_objective_value())


class BranchAndBoundType(Enum):
    BINARY = 0,
    TOTAL = 1


def solve_with_branch_and_bound(costs_matrix, bb_type, visualize=False, print_time=False):
    print("Branch and Bound Binary" if bb_type ==
          BranchAndBoundType.BINARY else "Branch and Bound Total")
    num_vertices = len(costs_matrix)

    start_time = time.time()

    if bb_type == BranchAndBoundType.BINARY:
        solution, num_added_nodes = branch_and_bound_binary(costs_matrix)
    else:
        solution, num_added_nodes = branch_and_bound_total(costs_matrix)

    t = time.time() - start_time
    if print_time:
        print("\tTime:", t)

    if visualize:
        utils.print_tours(solution, num_vertices,
                          method_name="Branch and Bound")

    print("\tTotal Cost:   ", solution.get_objective_value())
    print("\tNodes added:", num_added_nodes)

    return round(t, 2), num_added_nodes, int(solution.get_objective_value())


def solve_with_MTZ(costs_matrix, visualize=True, print_time=True):
    print("Miller–Tucker–Zemlin")
    num_vertices = len(costs_matrix)

    model = create_MTZ_model(costs_matrix)

    start_time = time.time()
    solution = model.solve()
    t = time.time() - start_time
    if print_time:
        print("\tTime:", t)

    if visualize:
        utils.print_tours(solution, num_vertices,
                          method_name="Miller–Tucker–Zemlin")

    print("\tTotal Cost:   ", solution.get_objective_value())

    return round(t, 2)