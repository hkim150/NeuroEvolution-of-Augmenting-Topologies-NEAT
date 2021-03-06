import random
from math import exp


class Genome:
    c1, c2, c3 = 1.0, 1.0, 0.4
    d_t = 2.5
    cross_disable_chance = 0.75
    flip_enable_chance = 0.02
    weight_mutation_chance = 0.8
    add_node_mutation_chance = 0.08
    add_connection_mutation_chance = 0.12
    perturbation_chance = 0.9

    def __init__(self, num_input_nodes=0, num_output_nodes=0):
        self.nodes = []
        self.connections = []
        for _ in range(num_input_nodes):
            self.nodes.append(NodeGene(NodeGene.nextId, NodeGene.INPUT))
            NodeGene.nextId += 1

        for _ in range(num_output_nodes):
            self.nodes.append(NodeGene(NodeGene.nextId, NodeGene.OUTPUT))
            NodeGene.nextId += 1

    def mutate(self):
        if random.random() < Genome.weight_mutation_chance:
            self.weight_mutation()
        if random.random() < Genome.flip_enable_chance:
            self.flip_enable_mutation()
        if random.random() < Genome.add_node_mutation_chance:
            self.add_node_mutation()
        if random.random() < Genome.add_connection_mutation_chance:
            self.add_connection_mutation()

    def weight_mutation(self):
        for connection in self.connections:
            random_val = random.random() * 4 - 2
            if random.random() < Genome.perturbation_chance:
                connection.weight *= random_val
            else:
                connection.weight = random_val

    def flip_enable_mutation(self):
        if len(self.connections) < 1:
            return

        connection = random.choice(self.connections)
        connection.expressed = not connection.expressed

    def add_node_mutation(self):
        if len(self.connections) < 1:
            return

        connection = random.choice(self.connections)
        self.add_node(connection)

    def add_node(self, connection):
        outNodeId = connection.outNodeId
        middleNodeId = NodeGene.nextId
        inNodeId = connection.inNodeId
        weight = connection.weight

        connection.expressed = False
        self.nodes.append(NodeGene(middleNodeId, NodeGene.HIDDEN))
        NodeGene.nextId += 1

        self.add_connection(outNodeId, middleNodeId, 1.0)
        self.add_connection(middleNodeId, inNodeId, weight)

    def add_connection_mutation(self):
        count = [0, 0, 0]
        for node in self.nodes:
            count[node.type] += 1

        combinations = count[0] * count[1] + count[1] * count[2] + count[2] * count[0]

        if len(self.connections) >= combinations:
            return

        while True:
            node1, node2 = random.sample(self.nodes, 2)
            if node1.type == node2.type:
                continue
            outNodeId = node1.id if node1.type < node2.type else node2.id
            inNodeId = node2.id if node1.type < node2.type else node1.id
            if not self.check_connection_exists_from_node_ids(outNodeId, inNodeId):
                break

        self.add_connection(outNodeId, inNodeId, random.random() * 2 - 1)

    def add_connection(self, outNodeId, inNodeId, weight):
        self.connections.append(ConnectionGene(outNodeId, inNodeId, weight, ConnectionGene.nextInnovationNumber, True))
        ConnectionGene.nextInnovationNumber += 1

    def check_connection_exists_from_node_ids(self, id1, id2):
        for connection in self.connections:
            if connection.outNodeId == id1 and connection.inNodeId == id2:
                return True

        return False

    def __contains__(self, value):
        for connection in self.connections:
            if connection.innovationNumber == value:
                return True

        return False

    def get_connection_gene(self, innovationNumber):
        for connection in self.connections:
            if connection.innovationNumber == innovationNumber:
                return connection

    def copy(self):
        newGenome = Genome()
        for node in self.nodes:
            newGenome.nodes.append(node.copy())

        for connection in self.connections:
            newGenome.connections.append(connection.copy())

        return newGenome

    def get_genome_info(self):
        num_nodes = len(self.nodes)
        num_connection = 0
        for connection in self.connections:
            if connection.expressed:
                num_connection += 1

        return [num_nodes, num_connection, ConnectionGene.nextInnovationNumber - 1]

    @staticmethod
    def cross_over(parent1, parent2):
        child = Genome()
        child.nodes = [node.copy() for node in parent1.nodes]

        for connection in parent1.connections:
            if connection.innovationNumber in parent2:
                par2_connection = parent2.get_connection_gene(connection.innovationNumber)
                inherited_connection = connection.copy() if random.randint(0, 1) == 0 else par2_connection.copy()
                if connection.expressed != par2_connection.expressed:
                    inherited_connection.expressed = False if random.random() < Genome.cross_disable_chance else True
                child.connections.append(inherited_connection)
            else:
                child.connections.append(connection.copy())

        return child

    @staticmethod
    def get_compatibility_distance(genome1, genome2, n=1):
        set1 = set()
        set2 = set()
        for connection in genome1.connections:
            set1.add(connection.innovationNumber)
        max1 = max(set1)

        for connection in genome2.connections:
            set2.add(connection.innovationNumber)
        max2 = max(set2)

        E = 0
        excess_point = min(max1, max2)

        intersection_set = set1.intersection(set2)
        union_set = set1.union(set2)
        diff_set = union_set.difference(intersection_set)

        for num in diff_set:
            if num > excess_point:
                E += 1

        D = len(diff_set) - E

        weight_diff_sum = 0.0
        for num in intersection_set:
            weight1 = genome1.get_connection_gene(num).weight
            weight2 = genome2.get_connection_gene(num).weight
            weight_diff_sum += abs(weight1 - weight2)

        W = weight_diff_sum / max(len(intersection_set), 1)

        return (Genome.c1 * E + Genome.c2 * D) / n + Genome.c3 * W


class ConnectionGene:
    nextInnovationNumber = 0

    def __init__(self, outNodeId, inNodeId, weight, innovationNumber, expressed=False):
        self.outNodeId = outNodeId
        self.inNodeId = inNodeId
        self.weight = weight
        self.innovationNumber = innovationNumber
        self.expressed = expressed

    def copy(self):
        return ConnectionGene(self.outNodeId, self.inNodeId, self.weight, self.innovationNumber, self.expressed)


class NodeGene:
    nextId = 0
    INPUT, HIDDEN, OUTPUT = 0, 1, 2

    def __init__(self, id, type):
        self.id = id
        self.type = type

    def copy(self):
        return NodeGene(self.id, self.type)


class Generation:
    max_population = 100
    stale_tolerance = 15
    weak_tolerance = 0.9
    clone_chance = 0.25
    mate_chance = 0.75
    activation_threshold = 0.5
    min_con_champ_preserve = 2

    def __init__(self):
        self.generation_number = 1
        self.species = []
        self.population = 0

    def add_organism(self, organism):
        if self.population > 1:
            for s in self.species:
                if Genome.get_compatibility_distance(organism.genome, s.representative.genome) < Genome.d_t:
                    s.add_organism(organism)
                    self.population += 1
                    return

        self.species.append(Species(organism))
        self.population += 1

    def get_all_organisms(self):
        all_organisms = []
        for s in self.species:
            all_organisms.extend(s.organisms)

        return all_organisms

    def next_generation(self):
        sum_avg_species_fitness = 0.0
        for s in self.species:
            s.evaluate_self()
            s.cull_half()
            s.update_avg_fitness()
            sum_avg_species_fitness += s.average_fitness

        avg_species_fitness = sum_avg_species_fitness / len(self.species)

        self.species.sort(key=lambda x: x.max_fitness, reverse=True)
        for i in range(len(self.species)-1,-1,-1):
            if len(self.species) < 2:
                break
            if self.species[i].max_fitness < avg_species_fitness * Generation.weak_tolerance:
                del self.species[i]

        self.species.sort(key=lambda x: x.stale_generation_count)
        for i in range(len(self.species)-1,-1,-1):
            if len(self.species) < 2:
                break
            if self.species[i].stale_generation_count >= Generation.stale_tolerance:
                del self.species[i]

        self.population = 0
        sum_avg_species_fitness = 0.00
        for s in self.species:
            sum_avg_species_fitness += s.average_fitness
            self.population += s.population

        max_tot_offspring = Generation.max_population - self.population

        offsprings = []
        for s in self.species:
            max_offspring = round((s.average_fitness / sum_avg_species_fitness) * max_tot_offspring)
            offsprings.extend(s.get_offsprings(max_offspring))

        for offspring in offsprings:
            self.add_organism(offspring)

        self.generation_number += 1


class Species:
    def __init__(self, organism):
        self.organisms = [organism]
        self.population = 1
        self.representative = organism
        self.average_fitness = 0.0
        self.max_fitness = 0.0
        self.historical_max_fitness = 0.0
        self.stale_generation_count = 0

    def add_organism(self, organism):
        self.organisms.append(organism)
        self.population += 1

    def evaluate_self(self):
        self.update_avg_fitness()

        max_found = 0.0
        for organism in self.organisms:
            max_found = max(max_found, organism.fitness)

        self.max_fitness = max_found

        if self.max_fitness > self.historical_max_fitness:
            self.historical_max_fitness = self.max_fitness
            self.stale_generation_count = 0
        else:
            self.stale_generation_count += 1

    def update_avg_fitness(self):
        fitness_sum = 0.0
        for organism in self.organisms:
            fitness_sum += organism.fitness

        self.average_fitness = fitness_sum / self.population

    def cull_half(self):
        self.organisms.sort(key=lambda x: x.fitness, reverse=True)
        self.representative = self.organisms[0]
        cull_count = self.population // 2
        if cull_count > 0:
            for i in range(self.population-1, -1, self.population - cull_count):
                del self.organisms[i]

        self.population = len(self.organisms)

    def get_offsprings(self, max_offspring_num):
        offsprings = []
        num_offspring = min(self.population * 2, max_offspring_num)

        if num_offspring < 1:
            return offsprings

        self.organisms.sort(key=lambda x: x.fitness, reverse=True)
        champion = self.organisms[0].copy()

        con_count = 0
        for connection in champion.genome.connections:
            if connection.expressed:
                con_count += 1

        if con_count < Generation.min_con_champ_preserve:
            champion.genome.mutate()

        offsprings.append(champion)

        num_offspring -= 1

        if num_offspring < 1:
            return offsprings

        num_mate = 0 if self.population < 2 else round(num_offspring * Generation.mate_chance)
        num_clone = num_offspring - num_mate

        if num_clone > 0:
            for parent in random.sample(self.organisms, num_clone):
                offspring = parent.copy()
                offspring.genome.mutate()
                offsprings.append(offspring)

        for _ in range(num_mate):
            parent1, parent2 = random.sample(self.organisms, 2)
            if parent1.fitness > parent2.fitness:
                offspring = Organism(Genome.cross_over(parent1.genome, parent2.genome))
            else:
                offspring = Organism(Genome.cross_over(parent2.genome, parent1.genome))

            offspring.genome.mutate()
            offsprings.append(offspring)

        for organism in self.organisms:
            organism.genome.mutate()

        return offsprings


class Organism:
    def __init__(self, genome=None):
        self.genome = genome
        self.fitness = 1

    def copy(self):
        return Organism(self.genome.copy())

    def choose_action(self, state):
        input_ids = {}
        output_value = {}
        idx = 0
        output_node_ids = []
        for node in self.genome.nodes:
            if node.type == NodeGene.INPUT:
                output_value[node.id] = state[idx]
                idx += 1
            elif node.type == NodeGene.OUTPUT:
                output_node_ids.append(node.id)

        for connection in self.genome.connections:
            if connection.expressed:
                if connection.inNodeId in input_ids:
                    input_ids[connection.inNodeId].append(connection)
                else:
                    input_ids[connection.inNodeId] = [connection]

        while len(input_ids) > 0:
            to_del = []
            for node_id, connections in input_ids.items():
                output = 0.0
                know_all_input_values = True
                for connection in connections:
                    if connection.outNodeId in output_value:
                        output += output_value[connection.outNodeId] * connection.weight
                    else:
                        know_all_input_values = False
                        break

                if know_all_input_values:
                    output_value[node_id] = 1 / (1 + exp(output))
                    to_del.append(node_id)

            for node_id in to_del:
                del input_ids[node_id]

        actions = []
        for id in output_node_ids:
            if id in output_value:
                if output_value[id] > Generation.activation_threshold:
                    actions.append(id)

        return actions
