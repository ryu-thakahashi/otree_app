def num_of_coopeartors(decision_list: list):
    return sum([1 for decision in decision_list if decision == "C"])


def caluculate_payoff(decision_list: list, bc_ratio: float):
    coop_num = num_of_coopeartors(decision_list)
    return (coop_num * bc_ratio) / len(decision_list)


if __name__ == "__main__":
    from icecream import ic

    ic(num_of_coopeartors(["C"] * 5))
