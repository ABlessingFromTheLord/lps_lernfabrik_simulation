import math
import simpy
import numpy
import sqlite3
from decimal import Decimal
from Job import Job
from Order import Order
from OrderList import OrderList

# global variables
MTTR = 60

# part names / working strings
OBERTEIL = "Oberteil"
UNTERTEIL = "Unterteil"
HALTETEIL = "Halteteil"
RING = "Ring"

# Unilokk definition
UNILOKK = [OBERTEIL, UNTERTEIL, HALTETEIL, RING]

# optimization parameters
OBERTEIL_PRODUCTION = 17
UNTERTEIL_PRODUCTION = 11
HALTETEIL_PRODUCTION = 49
RING_PRODUCTION = 97

OBERTEIL_ORDER = 0
UNTERTEIL_ORDER = 0
HALTETEIL_ORDER = 0
RING_ORDER = 0

# parts produced
OBERTEIL_COUNT = 0
UNTERTEIL_COUNT = 0
HALTETEIL_COUNT = 0
RING_COUNT = 0

# order related stats
ORDERS_FULFILLED = 0
DEADLINES_MET = 0

# ruestungszeit
RUESTUNGS_ZEIT = 0

# unilokk just produced
UNILOKK_PRODUCED = 0

# unilokk created
UNILOKK_COUNT = 0

# simulation time stats
ACTIVE_SIM_TIME = 0


# global helper functions
def get_jobs_for_part(part_name):
    #  returns the jobs required to be done to create a certain part of Unilokk
    match part_name:
        case "Oberteil":
            return Oberteil_Jobs
        case "Unterteil":
            return Unterteil_Jobs
        case "Halteteil":
            return Halteteil_Jobs
        case "Ring":
            return Ring_Jobs


def increase_part_count(part_name, output):
    #  increase the respective part count after the machines for part by amount "output"
    match part_name:
        case "Oberteil":
            global OBERTEIL_COUNT
            OBERTEIL_COUNT += output
        case "Unterteil":
            global UNTERTEIL_COUNT
            UNTERTEIL_COUNT += output
        case "Halteteil":
            global HALTETEIL_COUNT
            HALTETEIL_COUNT += output
        case "Ring":
            global RING_COUNT
            RING_COUNT += output


def decrease_part_count():
    #  decrease respective part count after a partis used for order fulfillment
    global OBERTEIL_COUNT
    OBERTEIL_COUNT = OBERTEIL_COUNT - 1
    global UNTERTEIL_COUNT
    UNTERTEIL_COUNT = UNTERTEIL_COUNT - 1
    global HALTETEIL_COUNT
    HALTETEIL_COUNT = HALTETEIL_COUNT - 1
    global RING_COUNT
    RING_COUNT = RING_COUNT - 1


def get_mz(machine):
    # returns the Machinezuverlässigkeit for a machine while producing a certain part
    if machine == machine_jaespa:
        return 0.98
    elif machine == machine_gz200:
        return 0.85
    elif machine == machine_fz12:
        return 0.98
    elif machine == machine_arbeitsplatz_at_gz200 or machine == machine_arbeitsplatz_2:
        return 1


def get_quality_grade(machine):
    # returns the rate of error for a certain machine
    # i.e if quality grade is 98%, it means 98% of material produced are usable to the next stage
    # 2% are thrown away
    if machine == machine_jaespa:
        return 1
    elif machine == machine_gz200:
        return 0.98
    elif machine == machine_fz12:
        return 0.95
    elif machine == machine_arbeitsplatz_at_gz200:
        return 0.96
    elif machine == machine_arbeitsplatz_2:
        return 0.9 * 0.98 * 0.98 * 0.98


def get_cumulative_quality_grade(part_name):
    # ran at the beginning of the part creation process
    # returns cumulative quality grade of the machines used
    match part_name:
        case "Oberteil":
            return 1 * 0.98 * 0.98 * 0.95
        case "Unterteil":
            return 1 * 0.98 * 0.98
        case "Halteteil":
            return 1 * 0.98 * 0.98
        case "Ring":
            return 1 * 0.98 * 0.96


def get_human_error_by_part(loss_ratio, part_name):
    # a combined (1- 0.84) * amount is the human error
    # since different parts come in different quantities, use ratio to this amount
    loss_ratio = Decimal(loss_ratio)  # convert to decimal for ease of use

    match part_name:
        case "Oberteil":
            return Decimal(17 / 174) * loss_ratio
        case "Unterteil":
            return Decimal(11 / 174) * loss_ratio
        case "Halteteil":
            return Decimal(49 / 174) * loss_ratio
        case "Ring":
            return Decimal(97 / 174) * loss_ratio


def get_output_per_part(part_name):
    # returns amount of parts created from a 3000mm long rod of raw material
    match part_name:
        case "Oberteil":
            return 17
        case "Unterteil":
            return 11
        case "Halteteil":
            return 49
        case "Ring":
            return 97


def get_amount_to_produce(job):
    # returns the amount needed to be produced by job
    # we have to offset machine caused error and human caused error by calculating
    # the offset need, for example, if mz is 98% then it is known that 2% are damaged,
    # hence produced are 102% to offset the damage caused
    part_name = job.get_part_name()

    amount_produced = get_output_per_part(part_name)

    # defected parts due to machine error
    machine_caused_defects = 1 - Decimal(get_cumulative_quality_grade(part_name))

    # defected parts due to human error, i.e, in the Kleben, Montage, Pruefen and Verpacken processes
    machine_loss = math.ceil(amount_produced * machine_caused_defects)

    # offset loss due to machine errors
    amount_produced += machine_loss

    human_caused_defects = Decimal(get_human_error_by_part(
        math.floor(get_quality_grade(machine_arbeitsplatz_2)), part_name))
    human_loss = math.ceil(amount_produced * human_caused_defects)

    # offset loss due to human errors
    amount_produced += human_loss
    return amount_produced


def all_jobs_completed_for_part(part_name):
    # checks if the jobs necessary to complete  a certain part creation are done
    # when all jobs required for a certain part creation are done it returns true
    # resets all the booleans completed in jobs for the next round of part creation
    # if there are more of the same part to be created
    jobs_required = get_jobs_for_part(part_name)

    for job in jobs_required:
        if job.get_completed() == 0:
            return False

    for job in jobs_required:
        job.set_completed(job.get_completed() - 1)  # removing one job to combine to form a part
    print("completed jobs for ", part_name)
    return True


def insert_variable_into_table(table_name, ordered, produced, ruestungszeit):
    # inserts statistics into out sqlite database
    sqlite_connection = sqlite3.connect('statistics.db')
    try:
        cursor = sqlite_connection.cursor()
        print("Connected to SQLite")

        sqlite_insert_with_param = f"""INSERT INTO {table_name}
                          (ordered, produced, ruestungszeit) 
                          VALUES (?, ?, ?);"""

        data_tuple = (ordered, produced, ruestungszeit)
        cursor.execute(sqlite_insert_with_param, data_tuple)
        sqlite_connection.commit()
        print("Python Variables inserted successfully into SqliteDb_developers table")

        cursor.close()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("The SQLite connection is closed")


def amount_of_runs(order_list):
    # returns amount of runs needed to fulfill the order
    # it depends on how much order is left and how much is needed
    # at the beginning nothing is produced so nothing is left

    global OBERTEIL_COUNT
    global UNTERTEIL_COUNT
    global HALTETEIL_COUNT
    global RING_COUNT

    # showing remaining parts from previous execution
    print("\nOBERTEIL: ", OBERTEIL_COUNT)
    print("UNTERTEIL: ", UNTERTEIL_COUNT)
    print("HALTETEIL: ", HALTETEIL_COUNT)
    print("RING: ", RING_COUNT, "\n")

    # if we are just starting
    if OBERTEIL_COUNT == 0 and UNTERTEIL_COUNT == 0 and HALTETEIL_COUNT == 0 and RING_COUNT == 0:
        for order_instance in range(len(order_list)):
            if order_list[order_instance] == 0:
                order_list[order_instance] = 0
            else:
                match order_instance:
                    case 0:
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 17)
                    case 1:
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 11)
                    case 2:
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 49)
                    case 3:
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 97)

    # we already produced and have some leftovers
    else:
        # if the leftovers suffice, done produce more
        if OBERTEIL_COUNT > order_list[0]:
            order_list[0] = 0
        if UNTERTEIL_COUNT > order_list[1]:
            order_list[1] = 0
        if HALTETEIL_COUNT > order_list[2]:
            order_list[2] = 0
        if RING_COUNT > order_list[3]:
            order_list[3] = 0

        # else produce needed
        # to reduce order by what is available
        for order_instance in range(len(order_list)):
            if order_list[order_instance] > 0:
                match order_instance:
                    case 0:
                        order_list[order_instance] -= OBERTEIL_COUNT
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 17)
                    case 1:
                        order_list[order_instance] -= UNTERTEIL_COUNT
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 11)
                    case 2:
                        order_list[order_instance] -= HALTETEIL_COUNT
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 49)
                    case 3:
                        order_list[order_instance] -= RING_COUNT
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 97)

    return order_list


def sort_by_depth(jobs):
    # sorts the jobs in the list in ascending order of degree
    to_return = []
    jobs_copy = jobs[:]

    current_depth = 0
    max_depth = len(jobs)

    while current_depth < max_depth:
        for job in jobs_copy:
            if len(jobs_copy) == 0:
                break

            if job.get_depth() == current_depth:
                to_return.append(job)
                jobs_copy.remove(job)

        current_depth += 1

    return to_return


def get_parts_by_sequence(sequence):
    # returns part names in the amount their machines are needed to be executed
    # to get a batch that can fulfill an order
    to_return = []

    for j in range(len(sequence)):
        match j:
            case 0:
                while sequence[j] > 0:
                    to_return.append("Oberteil")
                    sequence[j] -= 1
            case 1:
                while sequence[j] > 0:
                    to_return.append("Unterteil")
                    sequence[j] -= 1
            case 2:
                while sequence[j] > 0:
                    to_return.append("Halteteil")
                    sequence[j] -= 1
            case 3:
                while sequence[j] > 0:
                    to_return.append("Ring")
                    sequence[j] -= 1
    return to_return


def get_jobs_from_execution_sequence(execution_sequence):
    # returns the jobs needed for a certain execution sequence

    jobs = []  # array of jobs needed to fulfill this order

    for part in execution_sequence:
        jobs_for_part = get_jobs_for_part(part)

        # unpacking jobs into one list full of all the jobs
        for job in jobs_for_part:
            jobs.append(job)

    print("\nBefore degree sort:")
    for job in jobs:
        print(job.get_name())
    print("\n")

    return jobs


def get_equipping_time(job_1, job_2):
    # returns the equipping time of the job about to be executed
    # if the job is a Drehjob, ie, a job that needs machine gz200
    # then argument job_1 is relevant, otherwise it is irrelevant although passed as argument

    if job_2.get_machine_required() == machine_gz200:
        if job_1 is None:
            return 0

        match job_1.get_name():
            case "Oberteil_Drehen":
                match job_2.get_name():
                    case "Oberteil_Drehen":
                        return 0
                    case "Unterteil_Drehen":
                        return 45 * 60
                    case "Halteteil_Drehen":
                        return 40 * 60
                    case "Ring_Drehen":
                        return 45 * 60

            case "Unterteil_Drehen":
                match job_2.get_name():
                    case "Oberteil_Drehen":
                        return 45 * 60
                    case "Unterteil_Drehen":
                        return 0
                    case "Halteteil_Drehen":
                        return 40 * 60
                    case "Ring_Drehen":
                        return 45 * 60

            case "Halteteil_Drehen":
                match job_2.get_name():
                    case "Oberteil_Drehen":
                        return 40 * 60
                    case "Unterteil_Drehen":
                        return 40 * 60
                    case "Halteteil_Drehen":
                        return 0
                    case "Ring_Drehen":
                        return 45 * 60

            case "Ring_Drehen":
                match job_2.get_name():
                    case "Oberteil_Drehen":
                        return 45 * 60
                    case "Unterteil_Drehen":
                        return 45 * 60
                    case "Halteteil_Drehen":
                        return 45 * 60
                    case "Ring_Drehen":
                        return 0

    elif job_2.get_machine_required() == machine_fz12:
        return 30 * 60
    elif job_2.get_machine_required() == machine_jaespa:
        return 0
    elif ((job_2.get_machine_required() == machine_arbeitsplatz_at_gz200)
          or (job_2.get_machine_required() == machine_arbeitsplatz_2)):
        return 0


def sort_jobs_by_machines(jobs_list):
    # returns a list of list with each inner list consisting of jobs that can be run by the same machine

    iteration_index = 0
    to_return = []

    while len(jobs_list) > 0:
        machine = jobs_list[iteration_index].get_machine_required()

        jobs_by_machine = [x for x in jobs_list if x.get_machine_required() == machine]

        for job in jobs_by_machine:
            jobs_list.remove(job)

        to_return.append(jobs_by_machine)

    return to_return


def get_transport_time_between_machines(part_name, machine):
    # returns the time taken to transport a part from previous machine to this one
    if machine == machine_jaespa:
        return 60  # 60 seconds are needed to get to the saw from the lager
    elif machine == machine_gz200:
        return 20  # 20 seconds are needed from the saw to the Lathe machine
    elif machine == machine_fz12:
        return 30  # 30 seconds are needed to the milling machine
    elif machine == machine_arbeitsplatz_at_gz200:
        return 0  # work done at GZ200 hence no transport
    elif machine == machine_arbeitsplatz_2 and part_name == "Oberteil":
        return 50  # 50 seconds are needed from the  milling machine to Arbeitsplatz 2
    elif machine == machine_arbeitsplatz_2 and part_name != "Oberteil":
        return 70  # 70 seconds are needed from the GZ200 to Arbeitsplatz 2


def get_next_job_with_minimal_runtime(job, job_list):
    # returns the next Drehjob that should be run after this one to get minimal equipping times
    next_job = job_list[0]
    min_runtime = get_equipping_time(job, job_list[0])

    for i in range(1, len(job_list)):
        if get_equipping_time(job, job_list[i]) < min_runtime:
            min_runtime = get_equipping_time(job, job_list[i])
            next_job = job_list[i]

    return next_job


def sort_drehjobs_by_minimal_runtime(previous_drehen, job_list):
    # return the job execution sequence of the Drehjobs with minimal Ruestungszeit
    if len(job_list) <= 1:
        return job_list

    min_run = []

    # execution is just starting out
    if previous_drehen is None:
        if Oberteil_Drehen in job_list:
            job_with_minimal_degree = Oberteil_Drehen
            min_run.append(job_with_minimal_degree)
            job_list.remove(job_with_minimal_degree)
        else:
            job_with_minimal_degree = get_job_with_minimal_duration(job_list)
            min_run.append(job_with_minimal_degree)
            job_list.remove(job_with_minimal_degree)

    else:
        # there was a previous execution, hence that is used as our first job only
        # if it is in the list
        if previous_drehen in job_list:
            job_with_minimal_degree = previous_drehen
            min_run.append(job_with_minimal_degree)
            job_list.remove(job_with_minimal_degree)
        # previous drehen not none but it is not in the list
        else:
            job_with_minimal_degree = get_next_job_with_minimal_runtime(previous_drehen, job_list)
            min_run.append(job_with_minimal_degree)
            job_list.remove(job_with_minimal_degree)

    job_index = 0
    n = len(job_list)

    while job_index < n:
        job_with_min_runtime = get_next_job_with_minimal_runtime(min_run[-1], job_list)
        min_run.append(job_with_min_runtime)
        job_list.remove(job_with_min_runtime)
        job_index += 1

    return min_run


def get_min_run(drehen_jobs):
    # returns a list of strings of part names in the order that produces minimal runtime on Drehen jobs
    to_return = []

    for job in drehen_jobs:
        to_return.append(job.get_part_name())

    return to_return


def get_jobs_by_min_set_up_sequence(min_set_up_sequence, jobs):
    # based on the minimal set upo time of Drehen jobs, sorts all jobs for execution in
    # accordance to the minimal set up sequence
    to_return = []

    for part_name in min_set_up_sequence:
        jobs_to_add = []

        for job in jobs:
            if job.get_part_name() == part_name:
                jobs_to_add.append(job)

        jobs_to_add = sort_by_depth(jobs_to_add)

        to_return.extend(jobs_to_add)

    return to_return


def sort_like_drehen(drehen_jobs, other_jobs):
    # arranges a list of jobs in the same order as the minimum Ruestungszeit determined by
    # drehen jobs
    other_jobs_copy = other_jobs[:]
    to_return = []

    for i in range(len(drehen_jobs)):
        for other_job in other_jobs_copy:
            if drehen_jobs[i].get_part_name() == other_job.get_part_name():
                to_return.append(other_job)
                other_jobs_copy.remove(other_job)

    return to_return


def get_job_with_minimal_duration(job_list):
    # returns the next job with the shortest duration or runtime
    next_job = job_list[0]

    for i in range(len(job_list)):
        if job_list[i].get_duration() < next_job.get_duration():
            next_job = job_list[i]

    return next_job


def is_runnable(job):
    # checks if a job is eligible to be run

    if job.get_depth() == 0:
        return True
    else:
        if job.get_job_before().get_completed() >= 1:
            return True
        else:
            return False


def machine_is_free(machine):
    # determines if a machine is free or not
    if machine.count < machine.capacity:
        return True

    else:
        return False


def arrange_jobs_by_min_setup_time(previous_drehen, job_list):
    # receives jobs after they have been sorted into list of list based on machines needed
    # to run respective job, returns all jobs in the list of list sorted by minimal runtime
    # bottleneck are the drehen jobs, so their sequence with minimal setup time is first found
    # then all other jobs are arranged in the same way

    # get the drehen jobs
    drehen_jobs = [x[0] for x in job_list if x[0].get_machine_required() == machine_gz200 for x[0] in x]

    # get their sequence of execution such that minimal set up time is achieved
    min_dreh_jobs_sequence = sort_drehjobs_by_minimal_runtime(previous_drehen, drehen_jobs)

    print("\n min drehjobs sequence: ")
    for job in min_dreh_jobs_sequence:
        print(job.get_name())

    print("\n")

    # sort all other jobs in the corresponding sequence
    for i in range(len(job_list)):
        if job_list[i][0].get_machine_required() != machine_gz200:
            job_list[i] = sort_like_drehen(min_dreh_jobs_sequence, job_list[i])
        else:
            # no need to sort like drehen since drehen min sequence is already determined
            job_list[i] = min_dreh_jobs_sequence

    return job_list


def get_parallel_runnable_jobs(jobs_list):
    # returns jobs that can be run in parallel as a list
    # "ran in parallel means" at the same time
    to_return = []

    for jobs_sublist in jobs_list:
        if len(jobs_sublist) > 0:
            machine_needed = jobs_sublist[0].get_machine_required()

            if machine_is_free(machine_needed) and is_runnable(jobs_sublist[0]):
                to_return.append(jobs_sublist[0])
                jobs_sublist.remove(jobs_sublist[0])

    return to_return


def get_depth(job_list):
    # depth is defined as the amount of machines that can be run at the same time
    # in contrast to degree which is the stage of a job in the sequence of execution
    depth = 0

    machines = []

    for job in job_list:
        if job.get_machine_required() not in machines:
            machines.append(job.get_machine_required())
            depth += 1

    return depth


def pre_processing_order_wo(jobs, previous_drehen_job):
    # returns jobs sported in the order of minimal set up time

    # ordering the drehjobs in the order of minimal Ruestungszeit
    drehen_jobs = [x for x in jobs if x.get_machine_required() == machine_gz200]
    drehen_jobs = sort_drehjobs_by_minimal_runtime(previous_drehen_job, drehen_jobs)
    min_run = get_min_run(drehen_jobs)

    sorted_jobs = get_jobs_by_min_set_up_sequence(min_run, jobs)

    return sorted_jobs


def pre_processing_order_wop(previous_drehen_job, execution_sequence):
    # returns jobs as well as their amount from the part production sequence
    # wop stands for with optimization of set up time and parallel execution of jobs

    jobs = get_jobs_from_execution_sequence(execution_sequence)

    amount_of_jobs_to_be_done = len(jobs)

    # sorting jobs based on what machine is needed to run them
    jobs_sorted_by_machines = sort_jobs_by_machines(jobs)

    # sort jobs based on the part production to achieve minimal set up time
    min_setup_time_jobs_sequence = (
        arrange_jobs_by_min_setup_time(previous_drehen_job, jobs_sorted_by_machines))

    return min_setup_time_jobs_sequence, amount_of_jobs_to_be_done


def serve_out_and_clear(order, rem_unilokk, day, time, done_jobs):
    # function to do post-processing such as serve orders and clear variables
    global UNILOKK_COUNT
    if UNILOKK_COUNT >= (order.amount - rem_unilokk):
        UNILOKK_COUNT -= (order.amount - rem_unilokk)
        global ORDERS_FULFILLED
        ORDERS_FULFILLED += 1

        if day <= order.delivery_date:
            global DEADLINES_MET
            DEADLINES_MET += 1

        done_jobs.clear()

        print(f"Order fulfilled completely at {time}, in day {day} \n\n")
    else:
        done_jobs.clear()

        print(f"Order unfulfilled at {time} in day {day} \n\n")


def get_parts_needed(order):
    # receives orders and sets the universal variables OBERTEIL_ORDER,
    # UNTERTEIL_ORDER, HALTETEIL_ORDER, RING_ORDER

    global OBERTEIL_ORDER
    OBERTEIL_ORDER = order
    global UNTERTEIL_ORDER
    UNTERTEIL_ORDER = order
    global HALTETEIL_ORDER
    HALTETEIL_ORDER = order
    global RING_ORDER
    RING_ORDER = order

    return [OBERTEIL_ORDER, UNTERTEIL_ORDER, HALTETEIL_ORDER, RING_ORDER]


def update_statistics(duration, machine):
    # updates resource statistics
    if machine == machine_jaespa:
        global MACHINE_JAESPA_ACTIVE_TIME
        MACHINE_JAESPA_ACTIVE_TIME += duration

    elif machine == machine_gz200:
        global MACHINE_GZ200_ACTIVE_TIME
        MACHINE_GZ200_ACTIVE_TIME += duration

    elif machine == machine_fz12:
        global MACHINE_FZ12_ACTIVE_TIME
        MACHINE_FZ12_ACTIVE_TIME += duration

    elif machine == machine_arbeitsplatz_at_gz200:
        global MACHINE_ARBEITSPLATZ_AT_GZ200_ACTIVE_TIME
        MACHINE_ARBEITSPLATZ_AT_GZ200_ACTIVE_TIME += duration

    elif machine == machine_arbeitsplatz_2:
        global MACHINE_ARBEITSPLATZ_2_ACTIVE_TIME
        MACHINE_ARBEITSPLATZ_2_ACTIVE_TIME += duration


def print_statistics():
    # prints out statistics at the end of the simulation
    print(f"\ntotal ruestungszeit: {RUESTUNGS_ZEIT}, or {(RUESTUNGS_ZEIT / ACTIVE_SIM_TIME) * 100}% of active sim time")
    print(f" Jaespa utilization: {(MACHINE_JAESPA_ACTIVE_TIME / ACTIVE_SIM_TIME) * 100}")
    print(f"GZ200 utilization: {(MACHINE_GZ200_ACTIVE_TIME / ACTIVE_SIM_TIME) * 100}")
    print(f"FZ12 utilization: {(MACHINE_FZ12_ACTIVE_TIME / ACTIVE_SIM_TIME) * 100}")
    print(f"Workstation at GZ200 utilization: "
          f"{(MACHINE_ARBEITSPLATZ_AT_GZ200_ACTIVE_TIME / ACTIVE_SIM_TIME) * 100}")
    print(f"Workstation 2 utilization: {(MACHINE_ARBEITSPLATZ_2_ACTIVE_TIME / ACTIVE_SIM_TIME) * 100}")


# simulation class
class Lernfabrik:
    # this class simulates all processes taking place in the factory
    def __init__(self, sim_env):
        self.process = None
        self.env = sim_env  # environment variable
        self.start_time = None
        self.duration = None
        self.shift_number = 1
        self.day = 1  # to keep track of day
        self.last_day = 0
        self.taken_break_1 = False
        self.start_of_break_1 = 7200
        self.end_of_break_1 = 0  # is set at end of break
        self.taken_break_2 = False
        self.start_of_break_2 = 19800
        self.end_of_break_2 = 19830 * self.day
        self.start_of_shift_1 = 1
        self.start_of_shift_2 = 50400
        self.end_of_shift_1 = 50400
        self.end_of_shift_2 = 79200 * self.day
        self.overtime_allowed = 3600 * self.day
        self.currently_broken = False  # boolean for denoting when a machine is broken
        self.previous_drehen_job = None
        self.orders = OrderList()  # custom data type to receive orders, initially Null
        self.done_jobs = []
        self.stop_simulation = False

    def time_management(self):
        # checks the time and day in which we are

        if self.start_of_break_1 <= self.env.now < self.start_of_break_2 and not self.taken_break_1:
            # taking first break of shift
            print(f"\nPause 1 at {self.env.now} for shift {self.shift_number} of day {self.day}")
            yield self.env.timeout(15)
            print(f"Break ends at {self.env.now}\n")

            self.taken_break_1 = True
            self.start_of_break_2 = self.env.now + 10815

        elif self.start_of_break_2 <= self.env.now < self.end_of_shift_1 and not self.taken_break_2:
            # taking second break of shift
            print(f"\nPause 2 at {self.env.now} for shift {self.shift_number} of day {self.day}")
            yield self.env.timeout(30)
            print(f"Break ends at {self.env.now}\n")

            self.taken_break_2 = True
            self.end_of_break_2 = self.env.now

        elif self.end_of_break_2 <= self.env.now < self.end_of_shift_1 and self.shift_number == 1:
            # ending shift 1
            print(f"\nSCHÖNES FEIERABEND! at {self.env.now} to shift {self.shift_number}! of day {self.day}")
            self.shift_number = 2
            print(f"Second shift starts at {self.env.now}\n")

            self.taken_break_1 = False
            self.taken_break_2 = False
            self.start_of_break_1 = self.env.now + 7200
            self.start_of_break_2 = self.env.now + 19800
            self.end_of_break_2 = self.env.now + 19830
            self.end_of_shift_2 = self.env.now + 79200

        elif self.end_of_break_2 <= self.env.now < self.end_of_shift_2 and self.shift_number == 2:
            # ending shift 2 and day
            print(f"\nSCHÖNES FEIERABEND! at {self.env.now} to shift {self.shift_number}! of day {self.day}\n")
            yield self.env.timeout(28800)

            # resetting variables for the next day
            self.shift_number = 1
            self.taken_break_1 = False
            self.taken_break_2 = False
            self.last_day = self.day
            self.day += 1  # a new day starts
            self.start_of_shift_1 = self.env.now
            self.end_of_shift_1 = self.env.now + 50400
            self.start_of_break_1 = self.env.now + 7200
            self.end_of_break_1 = self.env.now + 7215
            self.start_of_break_2 = self.env.now + 19800
            self.end_of_break_2 = self.env.now + 19830
            self.end_of_shift_2 = self.env.now + 79200
            print(f"\nShift {self.shift_number} of day {self.day} starts at {self.start_of_shift_1}")

        else:
            # pass over and continue working since no event is relevant at this time
            yield self.env.timeout(0)

    # operation
    def operation(self, machine, operating_time):
        #  simulates an operation, it is an abstract function

        # operating machine after equipping
        while operating_time:
            start = self.env.now
            try:
                yield self.env.timeout(operating_time)  # running operation

                self.process = None

                # updating resource statistics
                machine_active_time = self.env.now - start
                global ACTIVE_SIM_TIME
                ACTIVE_SIM_TIME += machine_active_time
                update_statistics(machine_active_time, machine)

                operating_time = 0

                yield self.env.process(self.time_management())

            except simpy.Interrupt:
                self.currently_broken = True

                print(f"\nMachine{machine} broke down at {self.env.now}")
                operating_time -= (self.env.now - start)  # remaining time from when breakdown occurred

                # producing random repair time in the gaussian distribution with mean 60 seconds and standard
                # deviation of 30 seconds
                repair_time = abs(numpy.floor(numpy.random.normal(60, 30, 1).item()).astype(int).item())
                yield self.env.timeout(repair_time)

                print(f"Machine repairs took {repair_time} seconds, remaining time for operation {operating_time} "
                      f"seconds, continues at {self.env.now}\n")

                self.currently_broken = False

    # Helper functions
    def break_machine(self, machine, priority, preempt):
        #  breaks down a certain machine based on it's break probability or Maschinenzuverlässigkeit
        while not self.stop_simulation:
            yield self.env.timeout(MTTR)  # Time between two successive machine breakdowns
            break_or_not = numpy.around(numpy.random.uniform(0, 1), 2) < (1 - get_mz(machine))

            # if true then machine breaks down, else continues running
            if break_or_not:
                with machine.request(priority=priority, preempt=preempt) as request:
                    assert isinstance(self.env.now, int), type(self.env.now)
                    yield request
                    assert isinstance(self.env.now, int), type(self.env.now)

                    if self.process is not None and not self.currently_broken:
                        self.process.interrupt()

    def do_job(self, job):
        # performs a certain job as subprocess in part creation process
        # getting values for use
        part_name = job.get_part_name()
        required_machine = job.get_machine_required()
        transport_time = get_transport_time_between_machines(job.get_part_name(), required_machine)

        # getting amount to be produced by job
        if job.get_depth() == 0:
            # this is the initial job in part production process
            amount_to_produce = get_amount_to_produce(job)
        else:
            # at least one job has been done so that amount can be propagated that amount to this job
            amount_to_produce = job.get_job_before().get_amount_produced()

        equipping_time = get_equipping_time(self.previous_drehen_job, job)
        operating_time = job.get_duration()

        if job.get_machine_required() == machine_gz200 and self.previous_drehen_job is not None:
            print("\n")
            print("Ruestungszeit from ", self.previous_drehen_job.get_name(),
                  " to ", job.get_name(), " is ", equipping_time)

        global RUESTUNGS_ZEIT
        RUESTUNGS_ZEIT += equipping_time  # collect Ruestungszeit for statistical purposes

        if required_machine == machine_gz200:
            self.previous_drehen_job = job  # storing what job came to calculate the Ruestungszeit

        with required_machine.request(priority=1, preempt=False) as request:
            yield request

            print("\nTransport time for ", job.get_name(), "is", transport_time)
            yield self.env.timeout(transport_time)
            yield self.env.timeout(equipping_time)

            self.env.process(self.break_machine(required_machine, 2, True))  # starting breakdown function

            print(f"{job.get_name()} of {amount_to_produce} parts will take {operating_time * amount_to_produce} "
                  f"seconds, started execution at {self.env.now}")

            for i in range(0, amount_to_produce):
                self.process = self.env.process(self.operation(
                    required_machine, operating_time))  # operating machinery

                yield self.process

                self.process = None

            print(f"Finishing time for {job.get_name()} is {self.env.now} seconds")

        job.set_completed(job.get_completed() + 1)  # incrementing times the job is done
        amount_produced = math.floor(amount_to_produce * get_quality_grade(required_machine))
        job.set_amount_produced(amount_produced)

        if all_jobs_completed_for_part(part_name):
            #  all machines required to produce a part have been operated part is created
            increase_part_count(part_name, amount_to_produce)  # add newly created part
            print(math.floor(amount_to_produce), part_name, "(s) was created at ", self.env.now, "\n")

        # simulating transport time between the machine and the finishing area

        global ACTIVE_SIM_TIME
        if job.get_part_name() == machine_fz12:
            # 50 seconds are needed between the mill and the Arbeitsplatz 2
            yield self.env.timeout(50)
            ACTIVE_SIM_TIME += (transport_time + equipping_time + (operating_time * amount_to_produce) + 50)
        else:
            # all other parts need the GZ200 as end machine hence can be grouped in else
            # 70 seconds are needed between the GZ200 and Arbeitsplatz 2
            yield self.env.timeout(70)
            ACTIVE_SIM_TIME += (transport_time + equipping_time + (operating_time * amount_to_produce) + 70)

        self.done_jobs.append(job)

    def series_job_execution(self, jobs_in_series):
        # called n times to execute the rest of the jobs that cannot be parallelized
        # its execution is in series
        for job in jobs_in_series:
            yield self.env.process(self.do_job(job))

    def parallel_job_execution(self, jobs_in_parallel):
        # called n times as our parallelized_jobs array to execute jobs in parallel
        for job in jobs_in_parallel:
            self.env.process(self.do_job(job))
            yield self.env.timeout(0)

    def finish_unilokk_creation(self):
        # simulates the Kleben, Montage, Pruefen and Verpacken processes
        # after parts have been created
        print("\nFinishing process has started")

        n = 1
        # then assemble them into Unilokk
        while True:
            if OBERTEIL_COUNT > 0 and UNTERTEIL_COUNT > 0 and HALTETEIL_COUNT > 0 and RING_COUNT > 0:
                yield self.env.process(self.operation(machine_arbeitsplatz_2, 180))

                # decrement for the parts used above to create a whole Unilokk
                decrease_part_count()

                # increase Unilokk count for the one that is created
                global UNILOKK_PRODUCED
                UNILOKK_PRODUCED = UNILOKK_PRODUCED + 1

                # simulating transporting the unilokk to the warehouse, 20 seconds are needed
                yield self.env.timeout(20)

                global ACTIVE_SIM_TIME
                ACTIVE_SIM_TIME += 20

                print("unilokk ", n, " was created at ", self.env.now, "\n")
                n = n + 1

            else:
                break

    def fulfill_orders_without_optimization_and_parallelization(self, order_number, order):
        # fulfillment of orders linearly without any optimization model or parallel
        # execution of machines

        global UNILOKK_COUNT
        remaining_unilokk = UNILOKK_COUNT
        UNILOKK_COUNT = 0

        # need to produce if our order exceeds what is available
        if order.amount > remaining_unilokk:
            working_order = order.amount - remaining_unilokk  # actual order needed to be produced

            print("leftover Unilokk ", remaining_unilokk)

            parts_needed = get_parts_needed(working_order)
            print(parts_needed)

            execution_sequence = amount_of_runs(parts_needed)
            print("execution sequence", execution_sequence)
            execution_sequence_in_parts = get_parts_by_sequence(execution_sequence)
            print("execution sequence by parts", execution_sequence_in_parts)
            # okay till here

            # getting jobs needed
            jobs = get_jobs_from_execution_sequence(execution_sequence_in_parts)

            # order or jobs for minimal Ruestungszeiten
            for job in jobs:
                yield self.env.process(self.do_job(job))

        yield self.env.process(self.finish_unilokk_creation())

        # increase based on what is produced minus damaged
        global UNILOKK_PRODUCED
        UNILOKK_PRODUCED = math.floor(UNILOKK_PRODUCED * get_quality_grade(machine_arbeitsplatz_2))

        UNILOKK_COUNT += UNILOKK_PRODUCED

        # reset the unilokk produced counter
        UNILOKK_PRODUCED = 0

        print("\nOrder", order_number, ":", order.amount, " , produced:", UNILOKK_COUNT,
              ", remaining:", remaining_unilokk, ", total:", remaining_unilokk + UNILOKK_COUNT)

        # fulfilling order
        serve_out_and_clear(order, remaining_unilokk, self.day, self.env.now, self.done_jobs)

    def fulfill_order_with_optimization_without_parallelization(self, order_number, order):
        # fulfillment of orders in such a way that minimal set up time is achieved

        global UNILOKK_COUNT
        remaining_unilokk = UNILOKK_COUNT
        UNILOKK_COUNT = 0

        # need to produce if our order exceeds what is available
        if order.amount > remaining_unilokk:
            working_order = order.amount - remaining_unilokk  # actual order needed to be produced

            print("leftover Unilokk ", remaining_unilokk)

            parts_needed = get_parts_needed(working_order)
            print(parts_needed)

            execution_sequence = amount_of_runs(parts_needed)
            print("execution sequence", execution_sequence)
            execution_sequence_in_parts = get_parts_by_sequence(execution_sequence)
            print("execution sequence by parts", execution_sequence_in_parts)
            # okay till here

            # getting jobs needed
            jobs = get_jobs_from_execution_sequence(execution_sequence_in_parts)

            # pre-processing for optimization without parallel execution
            jobs = pre_processing_order_wo(jobs, self.previous_drehen_job)

            # order or jobs for minimal Ruestungszeiten
            for job in jobs:
                yield self.env.process(self.do_job(job))

        yield self.env.process(self.finish_unilokk_creation())

        # increase based on what is produced minus damaged
        global UNILOKK_PRODUCED
        UNILOKK_PRODUCED = math.floor(UNILOKK_PRODUCED * get_quality_grade(machine_arbeitsplatz_2))

        UNILOKK_COUNT += UNILOKK_PRODUCED

        # reset the unilokk produced counter
        UNILOKK_PRODUCED = 0

        print("\nOrder", order_number, ":", order.amount, " , produced:", UNILOKK_COUNT,
              ", remaining:", remaining_unilokk, ", total:", remaining_unilokk + UNILOKK_COUNT)

        # fulfilling order
        serve_out_and_clear(order, remaining_unilokk, self.day, self.env.now, self.done_jobs)

    def fulfill_with_optimization_and_parallelization(self, order_number, order):
        # fulfillment of orders in such a way that minimal set up time is achieved
        # furthermore parallel execution of machines is done wherever possible

        global UNILOKK_COUNT
        remaining_unilokk = UNILOKK_COUNT
        UNILOKK_COUNT = 0

        if order is None:
            return

        # need to produce if our order exceeds what is available
        if order.amount > remaining_unilokk:
            working_order = order.amount - remaining_unilokk  # actual order needed to be produced

            print("leftover Unilokk ", remaining_unilokk)

            parts_needed = get_parts_needed(working_order)
            print(parts_needed)

            execution_sequence = amount_of_runs(parts_needed)
            print("execution sequence", execution_sequence)
            execution_sequence_in_parts = get_parts_by_sequence(execution_sequence)
            print("execution sequence by parts", execution_sequence_in_parts)

            # getting order necessities
            min_setup_time_jobs_sequence, amount_of_jobs_to_be_done = (
                pre_processing_order_wop(self.previous_drehen_job, execution_sequence_in_parts))

            # running the jobs
            while len(self.done_jobs) < amount_of_jobs_to_be_done:
                to_do = []

                # get jobs that can be run in parallel
                to_do.extend(get_parallel_runnable_jobs(min_setup_time_jobs_sequence))

                if len(to_do) > 0:
                    # do the jobs in parallel
                    yield self.env.process(self.parallel_job_execution(to_do))

                else:
                    # no jobs were found, move simulation forward
                    yield self.env.timeout(1)

        # else we already have enough to fulfill order, or we have produced enough
        # assembling parts

        yield self.env.process(self.finish_unilokk_creation())

        # increase based on what is produced minus damaged
        global UNILOKK_PRODUCED
        UNILOKK_PRODUCED = math.floor(UNILOKK_PRODUCED * get_quality_grade(machine_arbeitsplatz_2))

        UNILOKK_COUNT += UNILOKK_PRODUCED

        # reset the unilokk produced counter
        UNILOKK_PRODUCED = 0

        print("\nOrder", order_number, ":", order.amount, " , produced:", UNILOKK_COUNT,
              ", remaining:", remaining_unilokk, ", total:", remaining_unilokk + UNILOKK_COUNT)

        # fulfilling order
        serve_out_and_clear(order, remaining_unilokk, self.day, self.env.now, self.done_jobs)

    def fulfill_orders(self, orders_list):
        # the whole process from part creation to order fulfillment

        # receiving and prioritising orders
        self.orders.receive_order(orders_list)
        prioritized_list = self.orders.order_by_priority()

        # store starting time
        start = self.env.now

        for order_number in range(len(prioritized_list)):
            yield self.env.process(self.fulfill_with_optimization_and_parallelization(
                order_number + 1, prioritized_list[order_number]))

        end = self.env.now

        self.duration = end - start
        print("Fulfilling orders took ", self.duration, " units of time")
        self.stop_simulation = True

        print("\nOrders fulfilled:", ORDERS_FULFILLED, "/", len(prioritized_list))
        print("\nDeadlines met:", DEADLINES_MET, "/", len(prioritized_list))


# instantiate object of Lernfabrik class
env = simpy.Environment()

# instantiate machines as simpy resources
machine_jaespa = simpy.PreemptiveResource(env, capacity=1)  # Maschine zum Saegen
machine_gz200 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Drehen
machine_fz12 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Fräsen
machine_arbeitsplatz_at_gz200 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Montage
machine_arbeitsplatz_2 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Montage

# resource statistics
MACHINE_JAESPA_ACTIVE_TIME = 0
MACHINE_GZ200_ACTIVE_TIME = 0
MACHINE_FZ12_ACTIVE_TIME = 0
MACHINE_ARBEITSPLATZ_AT_GZ200_ACTIVE_TIME = 0
MACHINE_ARBEITSPLATZ_2_ACTIVE_TIME = 0

# instantiating jobs
# Oberteil creation jobs
Oberteil_Saegen = Job("Oberteil_Saegen", "Oberteil", 34, machine_jaespa)
Oberteil_Drehen = Job("Oberteil_Drehen", "Oberteil", 287, machine_gz200)
Oberteil_Fraesen = Job("Oberteil_Fraesen", "Oberteil", 376, machine_fz12)
Oberteil_Saegen.set_job_before(None)
Oberteil_Saegen.set_job_after(Oberteil_Drehen)
Oberteil_Saegen.set_depth(0)
Oberteil_Drehen.set_job_before(Oberteil_Saegen)
Oberteil_Drehen.set_job_after(Oberteil_Fraesen)
Oberteil_Drehen.set_depth(1)
Oberteil_Fraesen.set_job_before(Oberteil_Drehen)
Oberteil_Fraesen.set_job_after(None)
Oberteil_Fraesen.set_depth(2)
Oberteil_Jobs = [Oberteil_Saegen, Oberteil_Drehen, Oberteil_Fraesen]

# Unterteil creation jobs
Unterteil_Saegen = Job("Unterteil_Saegen", "Unterteil", 20, machine_jaespa)
Unterteil_Drehen = Job("Unterteil_Drehen", "Unterteil", 247, machine_gz200)
Unterteil_Saegen.set_job_before(None)
Unterteil_Saegen.set_job_after(Unterteil_Drehen)
Unterteil_Saegen.set_depth(0)
Unterteil_Drehen.set_job_before(Unterteil_Saegen)
Unterteil_Drehen.set_job_after(None)
Unterteil_Drehen.set_depth(1)
Unterteil_Jobs = [Unterteil_Saegen, Unterteil_Drehen]

# Halteteil creation jobs
Halteteil_Saegen = Job("Halteteil_Saegen", "Halteteil", 4, machine_jaespa)
Halteteil_Drehen = Job("Halteteil_Drehen", "Halteteil", 255, machine_gz200)
Halteteil_Saegen.set_job_before(None)
Halteteil_Saegen.set_job_after(Halteteil_Drehen)
Halteteil_Saegen.set_depth(0)
Halteteil_Drehen.set_job_before(Halteteil_Saegen)
Halteteil_Drehen.set_job_after(None)
Halteteil_Drehen.set_depth(1)
Halteteil_Jobs = [Halteteil_Saegen, Halteteil_Drehen]

# Ring creation jobs
Ring_Saegen = Job("Ring_Saegen", "Ring", 3, machine_jaespa)
Ring_Drehen = Job("Ring_Drehen", "Ring", 185, machine_gz200)
Ring_Senken = Job("Ring_Senken", "Ring", 20, machine_arbeitsplatz_at_gz200)
Ring_Saegen.set_job_before(None)
Ring_Saegen.set_job_after(Ring_Drehen)
Ring_Saegen.set_depth(0)
Ring_Drehen.set_job_before(Ring_Saegen)
Ring_Drehen.set_job_after(Ring_Senken)
Ring_Drehen.set_depth(1)
Ring_Senken.set_job_before(Ring_Drehen)
Ring_Senken.set_job_after(None)
Ring_Senken.set_depth(2)
Ring_Jobs = [Ring_Saegen, Ring_Drehen, Ring_Senken]

# Finishing jobs
Fertigstellung = Job("Kleben_Montage_Pruefen_Verpacken", "Not_Applicable", 180, machine_arbeitsplatz_2)
Fertigstellung.set_job_before(None)
Fertigstellung.set_job_after(None)
Finishing_Jobs = [Fertigstellung]

SIM_TIME = 86400
fabric = Lernfabrik(env)

# creating order and add them to order list
# orders could also be created randomly, so random amount and random priority
order_1 = Order(5, 2)
order_2 = Order(20, 15)
order_3 = Order(15, 20)
order_4 = Order(35, 27)
order_5 = Order(10, 3)
order_6 = Order(15, 38)
order_7 = Order(30, 45)
order_8 = Order(25, 10)
order_9 = Order(20, 55)
order_10 = Order(25, 65)

orders = [order_1, order_2, order_3, order_4, order_5, order_6, order_7, order_8, order_9, order_10]
env.process(fabric.fulfill_orders(orders))
env.run()
print_statistics()
