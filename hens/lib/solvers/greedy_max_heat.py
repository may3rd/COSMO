# Greedy Max Heat
"""
Proposed greedy algorithm  to calculate the maximum
amount of heat that can be possibly exchanged between
two stream h and c in T temperature intervals.
"""
from ..classes.temperature_interval import Temperature_Interval
from ..classes.stream import Stream
from typing import Any

def greedy_heat(T: Temperature_Interval, 
                h: Stream, 
                c: Stream, 
                sigma: dict[Stream, dict[Temperature_Interval, float]], 
                delta: dict[Stream, dict[Temperature_Interval, float]]) -> tuple[float, dict[Stream, dict[Temperature_Interval, dict[Stream, dict[Temperature_Interval, float]]]]]:
    """
    Greedily computes the maximum amount of heat
    exchange between hot stream h and cold stream
    c in intervals T.

    It does not modify the network sigmas and deltas.
    """

    heat = 0
    q = {}
    R = {}

    # Calculating the amount of heat exchanged in same interval
    for t in T:
        exchanged_heat = min(sigma[h, t], delta[c, t])
        heat += exchanged_heat
        q[h, t, c, t] = exchanged_heat
        R[h, t] = sigma[h, t] - exchanged_heat
        R[c, t] = delta[c, t] - exchanged_heat

    for s in T:
        if R[h, s] != 0:
            s_index = T.index(s)
            for t in T[(s_index + 1):]:
                if (R[c, t] != 0):
                    exchanged_heat = min(R[h, s], R[c, t])
                    heat += exchanged_heat
                    q[h, s, c, t] = exchanged_heat
                    R[h, s] -= exchanged_heat
                    R[c, t] -= exchanged_heat
                    if (R[h, s] == 0):
                        break
    
    return (heat, q)


# TODO: This method will be useful for a heuristic to complete greedy_minmax_delta
def greedy_heat_2(T: Temperature_Interval, 
                  h: Stream, 
                  c: Stream, 
                  sigmas: dict[Stream, dict[Temperature_Interval, float]], 
                  deltas: dict[Stream, dict[Temperature_Interval, float]]) -> tuple[float, dict[Stream, dict[Temperature_Interval, dict[Stream, dict[Temperature_Interval, float]]]]]:
    """
    Greedily computes the maximum amount of heat
    exchange between hot stream h and cold stream
    c in intervals T.

    It modifies the network sigmas and deltas.
    """

    heat = 0
    q = {}
    sigma = dict(sigmas)
    delta = dict(deltas)

    for s in T:
        if sigma[h, s] != 0:
            s_index = T.index(s)
            for t in T[s_index:]:
                if (delta[c, t] != 0):
                    exchanged_heat = min(sigma[h, s], delta[c, t])
                    heat += exchanged_heat
                    q[h, s, c, t] = exchanged_heat
                    sigma[h, s] -= exchanged_heat
                    delta[c, t] -= exchanged_heat
                    if (sigma[h, s] == 0):
                        break
    
    return (heat, q)
