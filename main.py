#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Made by Kasonnara
"""
    A simple script writen quickly, to find solutions of the magic hexagon of order 3.
    Copyright (C) 2019  Kasonnara <kasonnara@laposte.net>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from typing import List

"""
Tooltip: indexes of each cell:
  0  1  2
 3  4  5  6
7  8  9  10 11
 12 13 14 15
  16 17 18
"""

from datetime import datetime
import itertools
import sys
from time import sleep, time

EXPECTED_SUM = 38

line_lenght = [3, 4, 5, 4, 3]

lines_offsets = [sum(line_lenght[:k]) for k in range(5)]

DIAG_INDICES = [2, 1, 0, 0, 0]
DIAG_INDICES_2 = [[0,0,0], [0,1,1,1], [0,1,2,2,2], [0,1,2,2], [0,1,2]]

# Constants for special caracter for displaying progress
CURSOR_UP_ONE = '\x1b[1A'
CURSOR_DOWN_ONE = '\x1b[1B'
ERASE_LINE = '\x1b[2K'

found_solutions = []

# To reduce complexity we doesn't fill the entire board and compute check it entirely, but instead fill it line by line,
# while checking for new alignment each time to stop the checking process early
smart_places = [[0, 1, 2], [3, 7], [12, 16], [17, 18], [15, 11], [6], [4, 5], [13, 14], [8, 9, 10]]
"""List of the bord slots to fill at each step of the exploring process"""


def safe_check(configuration: List[int]) -> bool:
    """
    Wrapper around check function for catching errors at the root
    :param configuration: list[int]
    :return: bool, True if the configuration is a valid solution
    """
    try:
        check(configuration)
    except AssertionError:
        return False
    return True


def check(configuration: List[int]) -> bool:
    """
    Check all alignments and raise an error as soon as an alignment sum is incorrect.

    None values in the configuration (e.g. slot not filled yet) are ignored and do not throw errors

    :param configuration: list[int]
    :return: True, if the configuration is a valid solution
    :raise: AssertionError, if the configuration is not a valid solution
    """
    # TODO Alternatively make a checker using big matrix multiplication
    # check horizontal lines
    for x in range(5):
        check_line(configuration, [(x, y) for y in range(line_lenght[x])])

    # check descending diagonals
    for k in range(5):
        x0, y0 = DIAG_INDICES[k], DIAG_INDICES[-k-1]
        check_line(configuration, [(x0 + i, y0 + DIAG_INDICES_2[k][i]) for i in range(line_lenght[k])])

    # check ascending diagonals
    for k in range(5):
        x0, y0 = 4 - DIAG_INDICES[k], DIAG_INDICES[-k-1]
        l = line_lenght[k]
        check_line(configuration, [(x0 - i, y0 + DIAG_INDICES_2[k][i]) for i in range(l)])

    return True


def check_line(configuration, coords):
    """
    Check a specific alignments and raise an error if its sum is incorrect.

    None values (e.g. slot not filled yet) are ignored and do not throw errors

    :param configuration: list[int]
    :param coords: List[(int, int)]: lists of the coordinates of the slot to sum
    :return: True, if the alignment has a valid sum,
             None, if a slot is undefined
    :raise: AssertionError, if the alignment has an invalid sum
    """
    s = 0
    for x, y in coords:
        v = configuration[lines_offsets[x] + y]
        if v is None:
            # Undefined slot, abort this line check
            return None
        else:
            s += v
    if s != EXPECTED_SUM:
        # Invalid sum, abort this configuration check
        # print("KO at line {}".format(coords))
        raise AssertionError()
    return True


if __name__ == '__main__':
    # Test an invalid solution [1, 2, 3, ..., 18, 19]
    invalid_solution = [k+1 for k in range(19)]
    print("invalid_solution is {}".format("VALIDE" if safe_check(invalid_solution ) else "INVALIDE"))
    # Test the valid solution I found
    valid_solution = [9, 11, 18, 14, 6, 1, 17, 15, 8, 5, 7, 3, 13, 4, 2, 19, 10, 12, 16]
    print("valid_solution is {}".format("VALIDE" if safe_check(valid_solution ) else "INVALIDE"))


# =========================================================================================
def compute_possibility(number_of_slot_to_fill, number_of_possible_piece):
    """
    Compute the number of possible arrangement to bruteforce when filling k empty slots with a set of n possible pieces.
    """
    nb_possibilite = 1
    for i in range(number_of_possible_piece, number_of_possible_piece - number_of_slot_to_fill, -1):
        nb_possibilite *= i
    return nb_possibilite


# ================================FIRST TRY: NAIVE BRUTEFORCE================================
nb_bf_possiblilite = compute_possibility(19, 19)
"""Complexity of bruteforcing the entire board at the same time"""


def full_bruteforce():
    """
    [Deprecated]
    First attempt to solve the riddle by pure bruteforce
    :return:
    """
    for k, configuration in enumerate(itertools.permutations(range(1,20), 19)):
        try:
            check(configuration)
            print("found valid solution", configuration)
            found_solutions.append(configuration)
        except AssertionError:
            pass
        print(k/nb_bf_possiblilite*100, "%")


if __name__ == '__main__' and False:
    full_bruteforce()
    # ~190258 years of computation on my laptop


# ==================================SECOND TRY: Brute force line by line=================================
nb_line_possiblilies = [compute_possibility(line_lenght[line_index], sum(line_lenght[line_index:])) for line_index in range(5)]
"""List of the complexities for bruteforcing each line"""

lags = [10, 20, 4000, 1000, 1]
"""
List of 'how often we should update the display of the process state to the user' for each step of bruteforcing
The more deeper we are in recursion, the faster me make checks, so me must update slower.
"""


def bruteforce_by_line_recursively(preset_config=(), line_index=0, remaining_tiles=set(range(1, 20))):
    """Recurcive process to simplify the problem by solving line by line instead of filling the entire board"""
    t0 = datetime.now()
    j = 0
    for k, line_configuration in enumerate(itertools.permutations(remaining_tiles, line_lenght[line_index])):
        try:
            pre_configuration = preset_config + line_configuration
            configuration = pre_configuration + (None,)*(19 - len(pre_configuration))
            check(configuration)
            if line_index == 4:
                #print("found valid solution", configuration, "\n")
                found_solutions.append(configuration)
                print("{}{}Solution found: {}, {}{}".format(CURSOR_UP_ONE*(line_index+1), ERASE_LINE, len(found_solutions), found_solutions, CURSOR_DOWN_ONE*line_index))
            else:
                #print(pre_configuration, "line", line_index, "OK, continue")
                print("")
                bruteforce_by_line_recursively(preset_config=pre_configuration, line_index=line_index + 1, remaining_tiles=remaining_tiles - set(line_configuration))
                print(CURSOR_UP_ONE*2)
        except AssertionError:
            pass

        # Periodically display internal state to the user
        if j == lags[line_index]:
            j = 0
            # print the progress status as well as an estimation of the processing duration
            t1 = datetime.now()
            duration = t1 - t0
            progression = (k+1)/nb_line_possiblilies[line_index]
            remaining = duration * (1-progression)/progression
            print(CURSOR_UP_ONE + ERASE_LINE + "\t"*line_index, str(round(progression*100, 2))+ "%\t, approximated end at", t1 + remaining)
        j +=1


if __name__ == '__main__' and False:
    try:
        print("===== Bruteforcing by lines =====\nPROGRESSION:\nSolution found: 0,[]\n")
        bruteforce_by_line_recursively()
        # Result in approximately 2 days of processing on my laptop
    except Exception as e:
        print("Errors, already found solutions:")
        for solution in found_solutions:
            print("-", solution)
        raise


# ================================THIRD TRY: Bruteforce alignment by alignment==============================
# The idea here is to check for valid alignment as early as possible, especially in the first stages of the process
# by filling alignment that are almost full first and check immediately.

nb_smart_possiblilies = [compute_possibility(len(smart_places[progress_index]),
                                             sum([len(next_places) for next_places in smart_places[progress_index:]]))
                         for progress_index in range(len(smart_places))]
"""List of the complexities of bruteforcing each step of the smart filling process"""

smart_lags = [10,] * len(smart_places)
"""
List of 'how often we should update the display of the process state to the user' for each step of bruteforcing
"""
smart_lags[5] = 1
smart_lags[7] = 100


def smart_bruteforce_reursively(preset_config=(None,)*19, progress_index=0, remaining_tiles=set(range(1, 20))):
    t0 = datetime.now()
    j = 0
    # iterate over the possible configurations of the next slots to fill
    for k, configuration_add in enumerate(itertools.permutations(remaining_tiles, len(smart_places[progress_index]))):
        try:
            # Merge configuration from previous steps, with the new slots
            configuration = tuple((v if k not in smart_places[progress_index] else configuration_add[smart_places[progress_index].index(k)]) for k, v in enumerate(preset_config))
            # Check the merged configuration
            check(configuration)
            if progress_index == len(smart_places) - 1:
                #print("found valid solution", configuration, "\n")
                found_solutions.append(configuration)
                print("{}{}Solution found: {}, {}{}".format(CURSOR_UP_ONE*(progress_index+2), ERASE_LINE, len(found_solutions), found_solutions, CURSOR_DOWN_ONE*(progress_index+1)))
            else:
                #  We found a partial solution that seems valid until now
                # Proceed with the next filling step recusively
                #print(pre_configuration, "line", line_index, "OK, continue")
                print("")
                smart_bruteforce_reursively(preset_config=configuration, progress_index=progress_index + 1, remaining_tiles=remaining_tiles-set(configuration_add))
                print(CURSOR_UP_ONE*2)
        except AssertionError:
            pass

        # Periodically display internal state to the user
        if j == smart_lags[progress_index]:
            j = 0
            # print the progress status as well as an estimation of the processing duration
            t1 = datetime.now()
            duration = t1 - t0
            progression = (k+1)/nb_smart_possiblilies[progress_index]
            remaining = duration * (1-progression)/progression
            print(CURSOR_UP_ONE + ERASE_LINE + "\t"*progress_index, str(round(progression*100, 2))+ "%\t, approximated end at", t1 + remaining)
        j += 1


if __name__ == '__main__':
    try:
        print("===== Smart Bruteforcing =====\nPROGRESSION:\nSolution found: 0,[]\n")
        smart_bruteforce_reursively()
        # Process takes approximately 10 minutes on my laptop

    except Exception as e:
        print("Errors, already found solutions:")
        for solution in found_solutions:
            print("-", solution)
        raise

# Re-display the entire list of solution found (in the eventuality that I failed my display so that found solutions were
# erased or lost in an overly verbose log).
if __name__ == '__main__':
    print("DONE, SOLUTIONS:")
    for solution in found_solutions:
        print("-", solution)
