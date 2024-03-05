from math import log


def log_mean_temperature_diff(t_h_in: float, t_h_out: float, t_c_in: float, t_c_out: float,
                              cocurrent: bool = False) -> float:
    if cocurrent:
        diff_t_a = t_h_in - t_c_in
        diff_t_b = t_h_out - t_c_out
    else:
        diff_t_a = t_h_in - t_c_out
        diff_t_b = t_h_out - t_c_in

    if diff_t_a == diff_t_b:
        return diff_t_a
    else:
        return (diff_t_a - diff_t_b) / log(diff_t_a / diff_t_b)
