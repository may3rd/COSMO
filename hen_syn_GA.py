import numpy as np
from collections import namedtuple
import pandas as pd

# Define data structure
Stream = namedtuple('Stream', ['type', 'Tin', 'Tout', 'CP'])
Utility = namedtuple('Utility', ['type', 'Tin', 'Tout', 'cost'])

# Function to load data from CSV files
def load_streams(streams_csv, utilities_csv):
    streams_df = pd.read_csv(streams_csv)
    utilities_df = pd.read_csv(utilities_csv)

    streams = [Stream(row['Type'], row['TIN_spec'], row['TOUT_spec'], row['Fcp'])
               for _, row in streams_df.iterrows()]

    utilities = {row['Type'].lower(): Utility(row['Type'], row['TIN_utility'], row['TOUT_utility'], row['Unit_Cost_Energy'])
                 for _, row in utilities_df.iterrows()}

    hot_streams = [s for s in streams if s.type.lower() == 'hot']
    cold_streams = [s for s in streams if s.type.lower() == 'cold']

    stage_num = max(len(hot_streams), len(cold_streams))
    
    return hot_streams, cold_streams, utilities, stage_num

# Example data (replace with actual streams)
hot_streams = [Stream('hot', 443, 333, 30.0), Stream('hot', 423, 303, 15.0)]
cold_streams = [Stream('cold', 293, 408, 20.0), Stream('cold', 353, 413, 40.0)]
U = 1.0  # overall heat transfer coefficient (assumed constant for simplicity)
stage_num = max(len(hot_streams), len(cold_streams))

# Genetic Algorithm Class
class GeneticAlgorithm:
    def __init__(self, hot_streams, cold_streams, utilities, stages, pop_size=20, gen=50):
        self.hot_streams = hot_streams
        self.cold_streams = cold_streams
        self.utilities = utilities
        self.stages = stages
        self.pop_size = pop_size
        self.gen = gen
        self.chromosome_length = stages * len(hot_streams) * len(cold_streams)
        self.population = [self.random_chromosome() for _ in range(pop_size)]

    def random_chromosome(self):
        return np.random.randint(0, 2, self.chromosome_length)

    def decode_chromosome(self, chromosome):
        # Reshape chromosome into 3D array (stages, hot, cold)
        return chromosome.reshape(self.stages, len(self.hot_streams), len(self.cold_streams))

    def fitness(self, chromosome):
        network = self.decode_chromosome(chromosome)
        # Perform heat balances, temperature feasibility checks
        # and calculate utility and exchanger area (use simplified pinch)
        total_cost = self.calculate_TAC(network)
        return total_cost

    def calculate_TAC(self, network):
        total_area = 0
        hot_util = 0
        cold_util = 0
        penalty = 0
        deltaT_min = 10  # Minimum temperature approach

        # Initialize temperatures for streams
        hot_temps = [hs.Tin for hs in self.hot_streams]
        cold_temps = [cs.Tin for cs in self.cold_streams]

        # Calculate heat exchange for each stage
        for k in range(self.stages):
            for i, hs in enumerate(self.hot_streams):
                for j, cs in enumerate(self.cold_streams):
                    if network[k, i, j] == 1:
                        # Feasibility check
                        hot_available = hs.CP * (hot_temps[i] - hs.Tout)
                        cold_available = cs.CP * (cs.Tout - cold_temps[j])

                        Q = min(hot_available, cold_available)
                        
                        if Q <= 0:
                            penalty += 1e6  # heavy penalty for infeasible exchanges
                            continue

                        # Calculate outlet temperatures for current exchange
                        hot_out_temp = hot_temps[i] - Q / hs.CP
                        cold_out_temp = cold_temps[j] + Q / cs.CP

                        # Enforce minimum temperature approach
                        dt1 = hot_temps[i] - cold_out_temp
                        dt2 = hot_out_temp - cold_temps[j]

                        if dt1 < deltaT_min or dt2 < deltaT_min:
                            penalty += 1e6  # heavy penalty for violating ΔT_min
                            continue

                        # LMTD calculation
                        if dt1 <= 0 or dt2 <= 0:
                            penalty += 1e6
                            continue
                        LMTD = (dt1 - dt2) / np.log(dt1 / dt2)

                        area = Q / (U * LMTD)
                        total_area += area

                        # Update stream temperatures
                        hot_temps[i] = hot_out_temp
                        cold_temps[j] = cold_out_temp

        # Utilities calculation (residual heating/cooling after heat recovery)
        for i, hs in enumerate(self.hot_streams):
            residual_hot = hs.CP * (hot_temps[i] - hs.Tout)
            if residual_hot > 0:
                cold_util += residual_hot

        for j, cs in enumerate(self.cold_streams):
            residual_cold = cs.CP * (cs.Tout - cold_temps[j])
            if residual_cold > 0:
                hot_util += residual_cold

        # Cost calculation
        area_cost_factor = 200  # cost per unit area
        hot_util_cost_factor = 100  # cost per unit hot utility
        cold_util_cost_factor = 10  # cost per unit cold utility

        total_cost = (total_area * area_cost_factor) + \
                    (hot_util * hot_util_cost_factor) + \
                    (cold_util * cold_util_cost_factor) + penalty

        return total_cost

    def run(self):
        for generation in range(self.gen):
            fitness_scores = [self.fitness(ch) for ch in self.population]
            best_idx = np.argmin(fitness_scores)
            best_fitness = fitness_scores[best_idx]

            new_pop = [self.population[best_idx]]  # elitism

            while len(new_pop) < self.pop_size:
                # parents = np.random.choice(self.population, 2, replace=False)
                parents_indices = np.random.choice(len(self.population), 2, replace=False)
                parents = [self.population[idx] for idx in parents_indices]

                child = self.crossover(parents[0], parents[1])
                child = self.mutate(child)
                new_pop.append(child)

            self.population = new_pop
            print(f'Generation {generation+1}, Best Fitness: {best_fitness}')

        best_chromosome = self.population[np.argmin([self.fitness(ch) for ch in self.population])]
        return best_chromosome, self.fitness(best_chromosome)

    def crossover(self, p1, p2):
        point = np.random.randint(1, len(p1))
        return np.concatenate((p1[:point], p2[point:]))

    def mutate(self, chromosome, rate=0.01):
        for idx in range(len(chromosome)):
            if np.random.rand() < rate:
                chromosome[idx] = 1 - chromosome[idx]
        return chromosome

# Execution example
if __name__ == "__main__":
    # Load streams and utilities from CSV files
    hot_streams, cold_streams, utilities, stage_num = load_streams('streams.csv', 'utilities.csv')
    ga = GeneticAlgorithm(hot_streams, cold_streams, utilities, stage_num)
    best_solution, best_cost = ga.run()
    optimal_network = ga.decode_chromosome(best_solution)

    print("\nOptimal Heat Exchanger Network Solution:\n")

    hot_temps = [hs.Tin for hs in hot_streams]
    cold_temps = [cs.Tin for cs in cold_streams]
    deltaT_min = 10  # consistent with your fitness function

    for k in range(stage_num):
        print(f"Stage {k+1}:")
        for i, hs in enumerate(hot_streams):
            for j, cs in enumerate(cold_streams):
                if optimal_network[k, i, j] == 1:
                    hot_available = hs.CP * (hot_temps[i] - hs.Tout)
                    cold_available = cs.CP * (cs.Tout - cold_temps[j])

                    Q = min(hot_available, cold_available)

                    if Q <= 0:
                        continue  # skip infeasible or zero exchanges

                    hot_out_temp = hot_temps[i] - Q / hs.CP
                    cold_out_temp = cold_temps[j] + Q / cs.CP

                    dt1 = hot_temps[i] - cold_out_temp
                    dt2 = hot_out_temp - cold_temps[j]

                    if dt1 < deltaT_min or dt2 < deltaT_min:
                        continue  # skip violating exchanges

                    print(f"  Exchanger: H{i+1} - C{j+1}")
                    print(f"    - Heat transferred (Q): {Q:.2f} kW")
                    print(f"    - Hot stream inlet temperature (H{i+1}): {hot_temps[i]:.2f}°C")
                    print(f"    - Hot stream outlet temperature (H{i+1}): {hot_out_temp:.2f}°C")
                    print(f"    - Cold stream inlet temperature (C{j+1}): {cold_temps[j]:.2f}°C")
                    print(f"    - Cold stream outlet temperature (C{j+1}): {cold_out_temp:.2f}°C\n")

                    # Update temperatures for next stage calculation
                    hot_temps[i] = hot_out_temp
                    cold_temps[j] = cold_out_temp

    # Display residual utilities clearly
    print("Utility Requirements after Heat Recovery:\n")

    total_hot_util = 0
    total_cold_util = 0

    for i, hs in enumerate(hot_streams):
        residual_hot = hs.CP * (hot_temps[i] - hs.Tout)
        if residual_hot > 0:
            total_cold_util += residual_hot
            print(f"  - Hot Stream H{i+1} requires cold utility: {residual_hot:.2f} kW")

    for j, cs in enumerate(cold_streams):
        residual_cold = cs.CP * (cs.Tout - cold_temps[j])
        if residual_cold > 0:
            total_hot_util += residual_cold
            print(f"  - Cold Stream C{j+1} requires hot utility: {residual_cold:.2f} kW")

    print(f"\nTotal Cold Utility required: {total_cold_util:.2f} kW")
    print(f"Total Hot Utility required: {total_hot_util:.2f} kW")

    print(f"\nOptimal Total Annual Cost (TAC): {best_cost:.2f}")

