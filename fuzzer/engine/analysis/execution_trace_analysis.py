#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import psutil
import copy
import sys

from eth_abi import encode_abi
from engine.environment import FuzzingEnvironment
from engine.plugin_interfaces import OnTheFlyAnalysis

from engine.fitness import fitness_function

from utils.utils import initialize_logger, get_fun_name_by_data,convert_stack_value_to_int, convert_stack_value_to_hex, normalize_32_byte_hex_address, get_function_signature_mapping,get_booking_function_from_abi
from eth._utils.address import force_bytes_to_address
from eth_utils import to_hex, to_int, int_to_big_endian, encode_hex, ValidationError, to_canonical_address, to_normalized_address

from z3 import simplify, BitVec, BitVecVal, Not, Optimize, sat, unsat, unknown, is_expr
from z3.z3util import get_vars

from utils import settings

class ExecutionTraceAnalyzer(OnTheFlyAnalysis):
    def __init__(self, fuzzing_environment: FuzzingEnvironment) -> None:
        self.logger = initialize_logger("Analysis")
        self.env = fuzzing_environment
        self.symbolic_execution_count = 0
        self.bug_fun_list = []

    def setup(self, ng, engine):
        pass

    def execute(self, population, engine):
        self.env.memoized_fitness.clear()
        self.env.memoized_storage.clear()
        self.env.memoized_symbolic_execution.clear()
        self.env.individual_branches.clear()
        # m = get_function_signature_mapping(self.env.abi)
        # print("@@@@@@@@get_function_signature_mapping get_function_signature_mapping s% 1111111111", m)
        """from utils.utils import get_function_signature_mapping
        m = get_function_signature_mapping(self.env.abi)

        for i in population:
            a = [c["arguments"] for c in i.chromosome]
            b = []
            for j in a:
                arg = j[0]
                if arg in m:
                    b.append(m[arg]+" "+j[0])
                else:
                    b.append(arg)
            print(b)"""


        executed_individuals = dict()
        for i, individual in enumerate(population.individuals):
            if i ==1:
                print("@@@@@@@@execution_trace_analysis: population.individuals  s% 1111111111") #, individual.solution
            if individual.hash in executed_individuals:
                population.individuals[i] = executed_individuals[individual.hash]
                continue
            self.execution_function(individual, self.env)
            executed_individuals[individual.hash] = individual
        executed_individuals.clear()

        # Update statistic variables.
        engine._update_statvars()


    def get_sum_booking(self):

        print("sum booking !!")

    def register_step(self, g, population, engine):
        self.execute(population, engine)

        code_coverage_percentage = 0
        if len(self.env.overall_pcs) > 0:
            code_coverage_percentage = (len(self.env.code_coverage) / len(self.env.overall_pcs)) * 100

        branch_coverage = 0
        for pc in self.env.visited_branches:
            branch_coverage += len(self.env.visited_branches[pc])
        branch_coverage_percentage = 0
        if len(self.env.overall_jumpis) > 0:
            branch_coverage_percentage = (branch_coverage / (len(self.env.overall_jumpis) * 2)) * 100

        msg = 'Generation number {} \t Code coverage: {:.2f}% ({}/{}) \t Branch coverage: {:.2f}% ({}/{}) \t ' \
              'Transactions: {} ({} unique)   \t Time: {}'.format(
            g + 1, code_coverage_percentage, len(self.env.code_coverage), len(self.env.overall_pcs),
            branch_coverage_percentage, branch_coverage, len(self.env.overall_jumpis) * 2, self.env.nr_of_transactions, len(self.env.unique_individuals),
            time.time() - self.env.execution_begin)
        self.logger.title(msg)

        # Save to results
        if "generations" not in self.env.results:
            self.env.results["generations"] = []

        self.env.results["generations"].append({
            "generation": g + 1,
            "time": time.time() - self.env.execution_begin,
            "total_transactions": self.env.nr_of_transactions,
            "unique_transactions": len(self.env.unique_individuals),
            "code_coverage": code_coverage_percentage,
            "branch_coverage": branch_coverage_percentage
        })

        if len(self.env.code_coverage) == self.env.previous_code_coverage_length:
            self.symbolic_execution(population.indv_generator)
            if self.symbolic_execution_count == settings.MAX_SYMBOLIC_EXECUTION:
                del population.individuals[:]
                population.init()
                self.logger.debug("Resetting population...")
                self.execute(population, engine)
                self.symbolic_execution_count = 0
            self.symbolic_execution_count += 1
        else:
            self.symbolic_execution_count = 0

        self.env.previous_code_coverage_length = len(self.env.code_coverage)

    # def get_fun_by_data(data):

    # def execution_function(self, indv, env: FuzzingEnvironment):
    #     env.unique_individuals.add(indv.hash)
    #
    #
    #     abi = self.env.abi
    #     booking_function = get_booking_function_from_abi(abi)
    #     accounts = self.env.instrumented_evm.get_accounts()
    #     booking_fun_with_argtype_list = list(booking_function.items())
    #     # print("booking_fun_with_argtype_list booking_fun_with_argtype_list", booking_fun_with_argtype_list)
    #     booking_fun_list = []
    #     booking_arguments_list = []  # a list containing the booking function with address
    #     data_list = []
    #
    #     for i in range(len(booking_fun_with_argtype_list)):
    #         booking_fun_list.append(booking_fun_with_argtype_list[i][0]) # booking fun signature
    #         booking_fun = booking_fun_with_argtype_list[i][0]
    #         booking_argument = [booking_fun]
    #         # print("@@@@@@@@ booking_argument  booking_argument s% !!!", booking_argument)
    #         data_list_i = []
    #
    #         for acc in accounts:  #
    #             # print("@@@@@@@@ get_account  get_account s% !!!", acc)
    #
    #             # b_a = copy.deepcopy(booking_argument)
    #             function =  copy.deepcopy(booking_argument) # fun signature
    #             data = function[0]
    #             arguments = [copy.deepcopy(acc)]
    #             try:
    #                 # print("interface interface interface", self.env.interface)
    #                 # print("data data data", data)
    #                 argument_types = [argument_type.replace(" storage", "").replace(" memory", "") for argument_type in
    #                                   self.env.interface[function[0]]]
    #
    #                 # print("@@@@@@@@ argument_types  s% 1111111111", argument_types)
    #                 # print("@@@@@@@@ arguments  s% 1111111111", arguments)
    #                 data += encode_abi(argument_types, arguments).hex()
    #                 # print("@@@@@@@@ data data data  s% 1111111111", data)
    #             except Exception as e:
    #                 # print(function)
    #                 self.logger.error("%s", e)
    #                 self.logger.error("%s: %s -> %s", function, self.env.interface[function[0]], arguments)
    #                 sys.exit(-6)
    #             data_list_i.append(data)
    #         data_list.append(data_list_i) # all function with arguments like balanceOf(0x11111111): 0x27e235e3000000000000000000000000cafebabecafebabecafebabecafebabecafebabe
    #
    #         #     b_a.append(acc)
    #         #     booking_argument_with_account = b_a
    #         #     print("@@@@@@@@ booking_argument_with_account  booking_argument_with_account  !!!", booking_argument_with_account)
    #         #     booking_arguments_list_i.append(booking_argument_with_account)
    #         # booking_arguments_list.append(booking_arguments_list_i)
    #     #
    #     # print("@@@@@@@@ data_list data_list data_list  s% 1111111111", data_list)
    #     # booking_fun = booking_fun_list[0][0]
    #     # booking_argument = [booking_fun]
    #     # # booking_arguments_list = []  # a list containing the balanceOf function
    #     # data_list = []
    #     # for acc in accounts: #
    #     #     # print("@@@@@@@@ get_account  get_account s% !!!", acc)
    #     #     print("@@@@@@@@ booking_argument  booking_argument s% !!!", booking_argument)
    #     #     b_a = copy.deepcopy(booking_argument)
    #     #     function = copy.deepcopy(booking_argument)
    #     #     data = function
    #     #     arguments = copy.deepcopy(acc)
    #     #     try:
    #     #         print("interface interface interface", self.env.interface)
    #     #         print("function function function", function)
    #     #         argument_types = [argument_type.replace(" storage", "").replace(" memory", "") for argument_type in self.env.interface[function[0]]]
    #     #         # print("@@@@@@@@ argument_types  s% 1111111111", argument_types)
    #     #         data += encode_abi(argument_types, arguments).hex()
    #     #     except Exception as e:
    #     #         print(function)
    #     #         self.logger.error("%s", e)
    #     #         self.logger.error("%s: %s -> %s", function, self.env.interface[function], arguments)
    #     #         sys.exit(-6)
    #     #     data_list.append(data)
    #     #     b_a.append(acc)
    #     #     booking_argument_with_account = b_a
    #     #     # print("@@@@@@@@ booking_argument_with_account  booking_argument_with_account  !!!", booking_argument_with_account)
    #     #     booking_arguments_list.append(booking_argument_with_account)
    #
    #
    #         # @@@ added by sjl at 20220905
    #
    #
    #
    #
    #
    #     # print("#####################################--------------------run execution_function now ------------------#####################################")
    #
    #
    #     # print("@@@@@@e_t_a: self.env.instrumented_evm.get_accouts()  " ,accouts )
    #     # Initialize metric
    #     branches = {}
    #     indv.data_dependencies = []
    #     contract_address = None
    #     precision = 10**5
    #
    #     chromosome = indv.chromosome
    #     env.detector_executor.initialize_detectors()
    #     fun_map = get_function_signature_mapping(env.abi)
    #     address_list = []
    #     # solution = indv.solution.checker
    #
    #     # print("@@@@@@@@get_function_signature_mapping get_function_signature_mapping s% 1111111111", fun_map)
    #
    #     for transaction_index, test in enumerate(indv.solution): # solution get by individual.decode()
    #
    #         transaction = test["transaction"]
    #         # print("@@@@@@@@transaction transaction  s% 1111111111", transaction)
    #         checker = test["checker"]  #    @@@ added by sjl at 20220905
    #
    #
    #
    #
    #         _function_hash = transaction["data"][:10] if transaction["data"].startswith("0x") else transaction["data"][:8]
    #         _function_hash = "fallback" if _function_hash == '' or _function_hash == '00000000'else _function_hash
    #         _array_size_indexes = dict()
    #
    #         fun_name = get_fun_name_by_data(transaction["data"],fun_map)#fun_map[_function_hash]
    #         fun_data = transaction["data"]
    #
    #         _book_function_hash = transaction["data"][:10] if transaction["data"].startswith("0x") else transaction["data"][:8]  #    @@@ added by sjl at 20220905
    #         _book_function_hash = "fallback" if _book_function_hash == '' else _book_function_hash
    #         _book_array_size_indexes = dict()
    #
    #         if transaction["to"] is None and contract_address is not None:
    #             transaction["to"] = contract_address
    #
    #         if transaction["to"] is None:
    #             continue
    #         if checker["to"] is None and contract_address is not None:  #    @@@ added by sjl at 20220905
    #             checker["to"] = contract_address
    #
    #         if checker["to"] is None:  #    @@@ added by sjl at 20220905
    #             continue
    #
    #         pre_sum_book_dic = {}
    #         pre_sum_map_dic = {}
    #         for i in range(len(data_list)):
    #
    #             checker["data_list"] = data_list[i]
    #             # print("checker[data_list] ",checker["data_list"] )
    #             try:  # #    @@@ added by sjl at 20220905  record the pre_book_balance
    #                 # here to record pre_booking value
    #
    #                 pre_sum_book, pre_book_map =  env.instrumented_evm.deploy_checker(test)
    #
    #                 # print("@@@@@@@@ record the sum  of booking balance before test: s% !!!", pre_sum_book)
    #                 # print("@@@@@@@@ record the map  of booking balance before test: s% !!!", pre_book_map)
    #
    #
    #             except ValidationError as e:
    #                 self.logger.error("Validation error in %s : %s (ignoring for now)", indv.hash, e)
    #                 continue
    #             book_fun_name = get_fun_name_by_data(data_list[i][0],fun_map)
    #             # print("book_fun_name book_fun_name",book_fun_name)
    #             pre_sum_book_dic[book_fun_name] = pre_sum_book
    #             pre_sum_map_dic[book_fun_name] = pre_book_map
    #
    #
    #         # if not result0.is_error and transaction["to"] == b'':
    #         #     contract_address = encode_hex(result0.msg.storage_address)
    #         #     self.logger.debug("(%s - %d) Contract deployed at %s", indv.hash, transaction_index, contract_address)
    #         addr_list = self.env.instrumented_evm.get_accounts()  # list of user's account  == self.env.instrumented_evm.get_accounts()
    #         # print("@@@@@e_t_a:  addr_list = pre_book_map.keys()",addr_list)
    #         # addr_list = self.env.instrumented_evm.get_accounts()
    #         # print("@@@@@e_t_a: addr_list: self.env.instrumented_evm.get_accouts()",self.env.instrumented_evm.get_accounts())
    #
    #         # record the ether in every account before test
    #
    #         pre_ether_map = {}
    #
    #         for addr in addr_list:
    #             addr1 = int(addr,16).to_bytes(20, 'big')
    #             # print("@@@@@@@@ addr addr addr  s%", addr1)
    #             # print("@@@@@@@@ type of addr   s%",type(addr1))
    #             # print("@@@@@@@@ len of addr   s%",len(addr1))
    #             ether_value = self.env.instrumented_evm.get_balance(addr1)
    #             pre_ether_map.update({addr:ether_value})
    #
    #
    #
    #         try:
    #
    #             result = env.instrumented_evm.deploy_transaction(test)
    #
    #             # print("@@@@@@@@ run s% by  env.instrumented_evm.deploy_transaction(test) s% " ,fun_name)
    #
    #             # print("@@@@@@@@ record the deploy_transaction  s% !!!", dir(result) )
    #             # print("@@@@@@@@@@@@@e_t_a: record the consume_gas  s% !!!", result.get_gas_used())
    #             # if result.should_burn_gas:
    #             #     print("@@@@@@@@@@@@@e_t_a: record the should_burn_gas  !!!", )
    #             # print("@@@@@@@@ record the return_data  s% !!!", result.return_data)
    #             # here to record after_booking value
    #         except ValidationError as e:
    #             self.logger.error("Validation error in %s : %s (ignoring for now)", indv.hash, e)
    #             continue
    #
    #
    #         # record the ether in every account after test
    #         post_ether_map = {}
    #
    #         for addr in addr_list:
    #             addr1 = int(addr,16).to_bytes(20,'big')
    #
    #             ether_value = self.env.instrumented_evm.get_balance(addr1)
    #             post_ether_map.update({addr:ether_value})
    #
    #         if not result.is_error and transaction["to"] == b'':
    #             contract_address = encode_hex(result.msg.storage_address)
    #             self.logger.debug("(%s - %d) Contract deployed at %s", indv.hash, transaction_index, contract_address)
    #         try:  # #    @@@ added by sjl at 20220905  record the pre_book_balance
    #             # here to post pre_booking value
    #             post_sum_book, post_book_map =  env.instrumented_evm.deploy_checker(test)
    #             # print("@@@@@@@@ record the sum  of booking balance before test: s% !!!", post_sum_book)
    #             # print("@@@@@@@@ record the map  of booking balance before test: s% !!!", post_book_map)
    #
    #
    #             # here to record after_booking value
    #         except ValidationError as e:
    #             self.logger.error("Validation error in %s : %s (ignoring for now)", indv.hash, e)
    #             continue
    #
    #         post_sum_book_dic = {}
    #         post_sum_map_dic = {}
    #         for i in range(len(data_list)):
    #
    #             checker["data_list"] = data_list[i]
    #             # print("checker[data_list] ",checker["data_list"] )
    #             try:  # #    @@@ added by sjl at 20220905  record the pre_book_balance
    #                 # here to record pre_booking value
    #
    #                 post_sum_book, post_book_map =  env.instrumented_evm.deploy_checker(test)
    #
    #                 # print("@@@@@@@@ record the sum  of booking balance before test: s% !!!", pre_sum_book)
    #                 # print("@@@@@@@@ record the map  of booking balance before test: s% !!!", pre_book_map)
    #
    #
    #             except ValidationError as e:
    #                 self.logger.error("Validation error in %s : %s (ignoring for now)", indv.hash, e)
    #                 continue
    #             book_fun_name = get_fun_name_by_data(data_list[i][0],fun_map)
    #             # print("book_fun_name book_fun_name",book_fun_name)
    #             if post_sum_map_dic != {}:
    #                 post_sum_book_dic[book_fun_name] = post_sum_book
    #                 post_sum_map_dic[book_fun_name] = post_book_map
    #                 # print("@@@@@@@@post_sum_book_dic", post_sum_book_dic)
    #                 # print("@@@@@@@@post_sum_map_dic", post_sum_map_dic)
    #
    #         transfer_invariants_flag = True
    #         exchange_invariants_flag = True
    #
    #         # check the sum balance  pre/d_value < 1000
    #         for i in range(len(pre_sum_map_dic)):
    #             book_fun_name = get_fun_name_by_data(data_list[i][0], fun_map)
    #             print("pre_sum_map_dic",pre_sum_map_dic)
    #             print("post_sum_map_dic",post_sum_map_dic)
    #             if pre_sum_map_dic != {}  and post_sum_map_dic != {}:
    #                 pre_sum_book = pre_sum_map_dic[book_fun_name]
    #                 post_sum_book= post_sum_map_dic[book_fun_name]
    #                 # print("pre_sum_book", pre_sum_book)
    #                 # print("post_sum_book", post_sum_book)
    #                 for acc in addr_list:
    #                     # print("account  ",acc)
    #                     pre_book = pre_sum_book[acc]
    #                     # print("pre_book  ",pre_book)
    #                     # print("account  ",acc)
    #                     post_book = post_sum_book[acc]
    #                     # print("pre_book  ",post_book)
    #
    #
    #                 if abs(pre_book-post_book) !=0 :
    #                 # if pre_sum_book/abs(pre_sum_book-post_sum_book) < 1000 :
    #         #     print("booking balance is equal!!!")
    #         # else:
    #                     transfer_invariants_flag = False
    #
    #                     print("@@@@@e_t_a: transfer_invariants_flag : s%", transfer_invariants_flag)
    #                     print("@@@@@e_t_a: accounts in env.instrumented_evm : s%", env.instrumented_evm.get_accounts())
    #                     print("@@@@@e_t_a: chromosome chromosome: s%", chromosome)
    #                     print("@@@@@e_t_a:  sender of checker and test : s%", transaction["from"])
    #                     print("@@@@@e_t_a:  data_list of checker : s%", checker["data_list"] )
    #                     print("@@@@@e_t_a: booking balance is modified!!! pre_sum_book: " ,pre_sum_book)
    #                     print("@@@@@e_t_a:  the map  of booking balance before test: s% !!!", pre_book_map)
    #
    #                     print("@@@@@e_t_a:  booking balance is modified!!! post_sum_book: " ,post_sum_book)
    #                     print("@@@@@e_t_a:  the map  of booking balance after test: s% !!!", post_book_map)
    #
    #                     print("@@@@@e_t_a: This function may contain bug :!!! s%",fun_name)
    #                     print("@@@@@e_t_a: Full data is:  s%",fun_data)
    #                     print("@@@@@e_t_a: solution solution solution s% 1111111111", test)
    #                     print("@@@@@e_t_a: checker checker  s% 1111111111", checker)
    #                     print("@@@@@e_t_a: checker.data_list checker.data_list  s% 1111111111", checker["data_list"])

    def execution_function(self, indv, env: FuzzingEnvironment):
        env.unique_individuals.add(indv.hash)


        abi = self.env.abi
        booking_function = get_booking_function_from_abi(abi)
        accounts = self.env.instrumented_evm.get_accounts()
        booking_fun_with_argtype_list = list(booking_function.items())
        # print("booking_fun_with_argtype_list booking_fun_with_argtype_list", booking_fun_with_argtype_list)
        booking_fun_list = []
        booking_arguments_list = []  # a list containing the booking function with address
        data_list = []

    # for i in range(len(booking_fun_with_argtype_list)):
        booking_fun_list.append(booking_fun_with_argtype_list[0][0]) # booking fun signature
        booking_fun = booking_fun_with_argtype_list[0][0]
        booking_argument = [booking_fun]
        # print("@@@@@@@@ booking_argument  booking_argument s% !!!", booking_argument)
        data_list = []

        for acc in accounts:  #
            # print("@@@@@@@@ get_account  get_account s% !!!", acc)

            # b_a = copy.deepcopy(booking_argument)
            function =  copy.deepcopy(booking_argument) # fun signature
            data = function[0]
            arguments = [copy.deepcopy(acc)]
            try:
                # print("interface interface interface", self.env.interface)
                # print("data data data", data)
                argument_types = [argument_type.replace(" storage", "").replace(" memory", "") for argument_type in
                                  self.env.interface[function[0]]]

                # print("@@@@@@@@ argument_types  s% 1111111111", argument_types)
                # print("@@@@@@@@ arguments  s% 1111111111", arguments)
                data += encode_abi(argument_types, arguments).hex()
                # print("@@@@@@@@ data data data  s% 1111111111", data)
            except Exception as e:
                # print(function)
                self.logger.error("%s", e)
                self.logger.error("%s: %s -> %s", function, self.env.interface[function[0]], arguments)
                sys.exit(-6)
            data_list.append(data)
        # all function with arguments like balanceOf(0x11111111): 0x27e235e3000000000000000000000000cafebabecafebabecafebabecafebabecafebabe

            #     b_a.append(acc)
            #     booking_argument_with_account = b_a
            #     print("@@@@@@@@ booking_argument_with_account  booking_argument_with_account  !!!", booking_argument_with_account)
            #     booking_arguments_list_i.append(booking_argument_with_account)
            # booking_arguments_list.append(booking_arguments_list_i)
        #
        # print("@@@@@@@@ data_list data_list data_list  s% 1111111111", data_list)
        # booking_fun = booking_fun_list[0][0]
        # booking_argument = [booking_fun]
        # # booking_arguments_list = []  # a list containing the balanceOf function
        # data_list = []
        # for acc in accounts: #
        #     # print("@@@@@@@@ get_account  get_account s% !!!", acc)
        #     print("@@@@@@@@ booking_argument  booking_argument s% !!!", booking_argument)
        #     b_a = copy.deepcopy(booking_argument)
        #     function = copy.deepcopy(booking_argument)
        #     data = function
        #     arguments = copy.deepcopy(acc)
        #     try:
        #         print("interface interface interface", self.env.interface)
        #         print("function function function", function)
        #         argument_types = [argument_type.replace(" storage", "").replace(" memory", "") for argument_type in self.env.interface[function[0]]]
        #         # print("@@@@@@@@ argument_types  s% 1111111111", argument_types)
        #         data += encode_abi(argument_types, arguments).hex()
        #     except Exception as e:
        #         print(function)
        #         self.logger.error("%s", e)
        #         self.logger.error("%s: %s -> %s", function, self.env.interface[function], arguments)
        #         sys.exit(-6)
        #     data_list.append(data)
        #     b_a.append(acc)
        #     booking_argument_with_account = b_a
        #     # print("@@@@@@@@ booking_argument_with_account  booking_argument_with_account  !!!", booking_argument_with_account)
        #     booking_arguments_list.append(booking_argument_with_account)


            # @@@ added by sjl at 20220905





        # print("#####################################--------------------run execution_function now ------------------#####################################")


        # print("@@@@@@e_t_a: self.env.instrumented_evm.get_accouts()  " ,accouts )
        # Initialize metric
        branches = {}
        indv.data_dependencies = []
        contract_address = None
        precision = 10**5

        chromosome = indv.chromosome
        env.detector_executor.initialize_detectors()
        fun_map = get_function_signature_mapping(env.abi)
        address_list = []
        # solution = indv.solution.checker

        # print("@@@@@@@@get_function_signature_mapping get_function_signature_mapping s% 1111111111", fun_map)

        for transaction_index, test in enumerate(indv.solution): # solution get by individual.decode()

            transaction = test["transaction"]
            # print("@@@@@@@@transaction transaction  s% 1111111111", transaction)
            checker = test["checker"]  #    @@@ added by sjl at 20220905




            _function_hash = transaction["data"][:10] if transaction["data"].startswith("0x") else transaction["data"][:8]
            _function_hash = "fallback" if _function_hash == '' or _function_hash == '00000000'else _function_hash
            _array_size_indexes = dict()

            fun_name = get_fun_name_by_data(transaction["data"],fun_map)#fun_map[_function_hash]
            fun_data = transaction["data"]

            _book_function_hash = transaction["data"][:10] if transaction["data"].startswith("0x") else transaction["data"][:8]  #    @@@ added by sjl at 20220905
            _book_function_hash = "fallback" if _book_function_hash == '' else _book_function_hash
            _book_array_size_indexes = dict()

            if transaction["to"] is None and contract_address is not None:
                transaction["to"] = contract_address

            if transaction["to"] is None:
                continue
            if checker["to"] is None and contract_address is not None:  #    @@@ added by sjl at 20220905
                checker["to"] = contract_address

            if checker["to"] is None:  #    @@@ added by sjl at 20220905
                continue




            checker["data_list"] = data_list
            # print("checker[data_list] ",checker["data_list"] )
            try:  # #    @@@ added by sjl at 20220905  record the pre_book_balance
                # here to record pre_booking value

                pre_book_sum, pre_book_map =  env.instrumented_evm.deploy_checker(test)

                # print("@@@@@@@@ record the sum  of booking balance before test: s% !!!", pre_sum_book)
                # print("@@@@@@@@ record the map  of booking balance before test: s% !!!", pre_book_map)


            except ValidationError as e:
                self.logger.error("Validation error in %s : %s (ignoring for now)", indv.hash, e)
                continue
            book_fun_name = get_fun_name_by_data(data_list[0],fun_map)
            # print("book_fun_name book_fun_name",book_fun_name)



            # if not result0.is_error and transaction["to"] == b'':
            #     contract_address = encode_hex(result0.msg.storage_address)
            #     self.logger.debug("(%s - %d) Contract deployed at %s", indv.hash, transaction_index, contract_address)
            addr_list = self.env.instrumented_evm.get_accounts()  # list of user's account  == self.env.instrumented_evm.get_accounts()
            # print("@@@@@e_t_a:  addr_list = pre_book_map.keys()",addr_list)
            # addr_list = self.env.instrumented_evm.get_accounts()
            # print("@@@@@e_t_a: addr_list: self.env.instrumented_evm.get_accouts()",self.env.instrumented_evm.get_accounts())

            # record the ether in every account before test

            pre_ether_map = {}

            for addr in addr_list:
                addr1 = int(addr,16).to_bytes(20, 'big')
                # print("@@@@@@@@ addr addr addr  s%", addr1)
                # print("@@@@@@@@ type of addr   s%",type(addr1))
                # print("@@@@@@@@ len of addr   s%",len(addr1))
                ether_value = self.env.instrumented_evm.get_balance(addr1)
                pre_ether_map.update({addr:ether_value})



            try:

                result = env.instrumented_evm.deploy_transaction(test)

                # print("@@@@@@@@ run s% by  env.instrumented_evm.deploy_transaction(test) s% " ,fun_name)

                # print("@@@@@@@@ record the deploy_transaction  s% !!!", dir(result) )
                # print("@@@@@@@@@@@@@e_t_a: record the consume_gas  s% !!!", result.get_gas_used())
                # if result.should_burn_gas:
                #     print("@@@@@@@@@@@@@e_t_a: record the should_burn_gas  !!!", )
                # print("@@@@@@@@ record the return_data  s% !!!", result.return_data)
                # here to record after_booking value
            except ValidationError as e:
                self.logger.error("Validation error in %s : %s (ignoring for now)", indv.hash, e)
                continue


            # record the ether in every account after test
            post_ether_map = {}

            for addr in addr_list:
                addr1 = int(addr,16).to_bytes(20,'big')

                ether_value = self.env.instrumented_evm.get_balance(addr1)
                post_ether_map.update({addr:ether_value})

            if not result.is_error and transaction["to"] == b'':
                contract_address = encode_hex(result.msg.storage_address)
                self.logger.debug("(%s - %d) Contract deployed at %s", indv.hash, transaction_index, contract_address)
            try:  # #    @@@ added by sjl at 20220905  record the pre_book_balance
                # here to post pre_booking value
                post_book_sum, post_book_map =  env.instrumented_evm.deploy_checker(test)
                # print("@@@@@@@@ record the sum  of booking balance before test: s% !!!", post_sum_book)
                # print("@@@@@@@@ record the map  of booking balance before test: s% !!!", post_book_map)


                # here to record after_booking value
            except ValidationError as e:
                self.logger.error("Validation error in %s : %s (ignoring for now)", indv.hash, e)
                continue





            transfer_invariants_flag = True
            exchange_invariants_flag = True

            # check the sum balance  pre/d_value < 1000



            if abs(pre_book_sum - post_book_sum) !=0 :
                    # if pre_sum_book/abs(pre_sum_book-post_sum_book) < 1000 :
            #     print("booking balance is equal!!!")
            # else:
                        transfer_invariants_flag = False

                        # print("@@@@@e_t_a: transfer_invariants_flag : s%", transfer_invariants_flag)
                        # print("@@@@@e_t_a: accounts in env.instrumented_evm : s%", env.instrumented_evm.get_accounts())
                        # print("@@@@@e_t_a: chromosome chromosome: s%", chromosome)
                        # print("@@@@@e_t_a:  sender of checker and test : s%", transaction["from"])
                        # print("@@@@@e_t_a:  data_list of checker : s%", checker["data_list"] )
                        # print("@@@@@e_t_a: booking balance is modified!!! pre_sum_book: " ,pre_book_sum)
                        # print("@@@@@e_t_a:  the map  of booking balance before test: s% !!!", pre_book_map)
                        #
                        # print("@@@@@e_t_a:  booking balance is modified!!! post_sum_book: " ,post_book_sum)
                        # print("@@@@@e_t_a:  the map  of booking balance after test: s% !!!", post_book_map)
                        #
                        if fun_name not in self.bug_fun_list:
                            self.bug_fun_list.append(fun_name)
                            print("@@@@@e_t_a: These function may contain bug :!!! @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ s%", self.bug_fun_list)
                        # print("@@@@@e_t_a: Full data is:  s%",fun_data)
                        # print("@@@@@e_t_a: solution solution solution s% 1111111111", test)
                        # print("@@@@@e_t_a: checker checker  s% 1111111111", checker)
                        # print("@@@@@e_t_a: checker.data_list checker.data_list  s% 1111111111", checker["data_list"])

            # check the exchange rate
            #
            change_of_balance = {}  # map of address and there change in booking balance
            # print('@@@@@e_t_a: post_book_map : s%', post_book_map)

            for addr in addr_list:
                if post_book_map != {} and pre_book_map != {}:
                    post = post_book_map[addr]
                    pre = pre_book_map[addr]
                    d_value = abs(post - pre)
                    if d_value != 0:
                        continue
                        # print('@@@@@e_t_a:  balance change !!! the value_of_change_balance is : s%', d_value)
                    # else:
                    #     print('@@@@@ balance not change !!! the value_of_change_balance is : s%', d_value)

                    change_of_balance.update({addr:d_value})
                # print('@@@@@e_t_a:  change_of_eth  : s%', change_of_balance)


            precision_wei = 1000000 # to ignore the gas change
            change_of_eth = {}
            for addr in addr_list:
                # print("@@@@@@@@ record the sum  of booking balance before test: s% !!!", post_sum_book)
                pre= pre_ether_map[addr]//precision_wei
                post= post_ether_map[addr]//precision_wei
                d_value = abs(post - pre)
                if d_value != 0 and d_value != 1:
                    # print('###@@@@@e_t_a:  ether change !!! the value_of_pre_ether is : s%', pre)
                    # print('###@@@@@e_t_a:  ether change !!! the value_of_post_ether is : s%', post)
                    # print('###@@@@@e_t_a:  ether change !!! the value_of_change_ether is : s%', d_value)
                    change_of_eth.update({addr: d_value})
                # else:
                #     print('###@@@@@ ehther not change !!! the value_of_change_ether is : s%', d_value)

            # print('@@@@@e_t_a:  change_of_eth  : s%', change_of_eth)
            # print("@@@@@e_t_a: This function may change ehther :!!! s%", fun_name)
            for addr in addr_list:
                if addr in change_of_balance and addr in change_of_eth:
                    if change_of_balance[addr] != 0 and change_of_eth[addr] != 0 :
                        print('###@@@@@e_t_a:  change_of_balance is : s%', change_of_balance[addr])
                        print('###@@@@@e_t_a:  change_of_eth is : s%', change_of_eth[addr])
                        rate = change_of_balance[addr]/change_of_eth[addr]
                        print('###@@@@@e_t_a:  exchange_rate is : s%' ,rate)




            #
            # print('@@@@@the map_of_change_balance is : s%', change_of_balance )
            # print('@@@@@the map_of_change_eth is : s%', change_of_eth )



            for child_computation in result.children:
                if child_computation.msg.to not in env.other_contracts:
                    continue
                if child_computation.msg.to not in env.children_code_coverage:
                    env.children_code_coverage[child_computation.msg.to] = set()
                env.children_code_coverage[child_computation.msg.to].update([x["pc"] for x in child_computation.trace])

            env.nr_of_transactions += 1

            previous_instruction = None
            previous_branch = []
            previous_branch_expression = None
            previous_branch_address = None
            previous_call_address = None
            sha3 = {}

            for i, instruction in enumerate(result.trace):

                env.symbolic_taint_analyzer.propagate_taint(instruction, contract_address)

                env.detector_executor.run_detectors(previous_instruction, instruction, env.results["errors"],
                                                env.symbolic_taint_analyzer.get_tainted_record(index=-2), indv, env, previous_branch,
                                                transaction_index)

                # If constructor, we don't have to take into account the constructor inputs because they will be part of the
                # state. We don't have to compute the code coverage, because the code is not the deployed one. We don't need
                # to compute the cfg because we are on a different code. We actlually don't need analyzing its traces.
                if indv.chromosome[transaction_index]["arguments"][0] == "constructor":
                    continue

                # Code coverage
                env.code_coverage.add(hex(instruction["pc"]))

                # Dynamically build control flow graph
                if env.cfg:
                    env.cfg.execute(instruction["pc"], instruction["stack"], instruction["op"], env.visited_branches,
                                    env.results["errors"].keys())

                if previous_instruction and previous_instruction["op"] == "SHA3":
                    sha3[instruction["stack"][-1][1]] = instruction["memory"]

                elif previous_instruction and previous_instruction["op"] == "ADD":
                    if previous_instruction["stack"][-1][1] in sha3:
                        sha3[instruction["stack"][-1][1]] = sha3[previous_instruction["stack"][-1][1]]
                    if previous_instruction["stack"][-2][1] in sha3:
                        sha3[instruction["stack"][-1][1]] = sha3[previous_instruction["stack"][-2][1]]

                if instruction["op"] == "JUMPI":
                    jumpi_pc = hex(instruction["pc"])
                    if jumpi_pc not in env.visited_branches:
                        env.visited_branches[jumpi_pc] = {}
                    if jumpi_pc not in branches:
                        branches[jumpi_pc] = dict()

                    destination = convert_stack_value_to_int(instruction["stack"][-1])
                    jumpi_condition = convert_stack_value_to_int(instruction["stack"][-2])

                    if jumpi_condition == 0:
                        # don't jump, but increase pc
                        branches[jumpi_pc][hex(destination)] = False
                        branches[jumpi_pc][hex(instruction["pc"] + 1)] = True
                    else:
                        # jump to destination
                        branches[jumpi_pc][hex(destination)] = True
                        branches[jumpi_pc][hex(instruction["pc"] + 1)] = False

                    env.visited_branches[jumpi_pc][jumpi_condition] = {}
                    env.visited_branches[jumpi_pc][jumpi_condition]["indv_hash"] = indv.hash
                    env.visited_branches[jumpi_pc][jumpi_condition]["chromosome"] = indv.chromosome
                    env.visited_branches[jumpi_pc][jumpi_condition]["transaction_index"] = transaction_index

                    tainted_record = env.symbolic_taint_analyzer.check_taint(instruction=instruction)
                    if tainted_record and tainted_record.stack and tainted_record.stack[-2]:
                        if jumpi_condition != 0:
                            previous_branch.append(tainted_record.stack[-2][0] != 0)
                        else:
                            previous_branch.append(tainted_record.stack[-2][0] == 0)
                        previous_branch_expression = previous_branch[-1]
                        env.visited_branches[jumpi_pc][jumpi_condition]["expression"] = previous_branch.copy()
                    else:
                        env.visited_branches[jumpi_pc][jumpi_condition]["expression"] = None
                        previous_branch_expression = None

                    previous_branch_address = jumpi_pc

                # Extract data dependencies (read-after-write)
                elif instruction["op"] == "SLOAD":
                    if instruction["stack"][-1][1] in sha3:
                        hash = instruction["stack"][-1][1]
                        while hash in sha3:
                            if len(sha3[hash]) == 64:
                                hash = sha3[hash][32:64]
                            else:
                                hash = sha3[hash]
                        storage_slot = int.from_bytes(hash, byteorder='big')
                    else:
                        storage_slot = convert_stack_value_to_int(instruction["stack"][-1])

                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                    if _function_hash not in self.env.data_dependencies:
                        self.env.data_dependencies[_function_hash] = {"read": set(), "write": set()}
                    self.env.data_dependencies[_function_hash]["read"].add(storage_slot)

                elif instruction["op"] == "SSTORE":
                    if instruction["stack"][-1][1] in sha3:
                        hash = instruction["stack"][-1][1]
                        while hash in sha3:
                            if len(sha3[hash]) == 64:
                                hash = sha3[hash][32:64]
                            else:
                                hash = sha3[hash]
                        storage_slot = int.from_bytes(hash, byteorder='big')
                    else:
                        storage_slot = convert_stack_value_to_int(instruction["stack"][-1])

                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                    if _function_hash not in self.env.data_dependencies:
                        self.env.data_dependencies[_function_hash] = {"read": set(), "write": set()}
                    self.env.data_dependencies[_function_hash]["write"].add(storage_slot)

                # If something goes wrong, we need to clean some pools
                elif instruction["op"] in ["REVERT", "INVALID", "ASSERTFAIL"]:
                    if previous_branch_expression is not None and is_expr(previous_branch_expression):
                        # Only remove from pool when you are sure which variable caused the exception
                        if len(get_vars(previous_branch_expression)) == 1:
                            for var in get_vars(previous_branch_expression):
                                _str_var = str(var)

                                if _str_var.startswith("calldataload_") or str(var).startswith("calldatacopy_"):
                                    _parameter_index = int(str(var).split("_")[-1])
                                    _transaction_index = int(str(var).split("_")[-2])
                                    _function_hash = indv.chromosome[_transaction_index]["arguments"][0]
                                    _argument = indv.chromosome[_transaction_index]["arguments"][_parameter_index + 1]
                                    indv.generator.remove_argument_from_pool(_function_hash, _parameter_index, _argument)

                                elif _str_var.startswith("callvalue_"):
                                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                                    _amount = transaction["value"]
                                    if _amount == 0 or _amount == 1:
                                        indv.generator.remove_amount_from_pool(_function_hash, _amount)

                                elif _str_var.startswith("caller_"):
                                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                                    _caller = transaction["from"]
                                    indv.generator.remove_account_from_pool(_function_hash, _caller)

                                elif _str_var.startswith("gas_"):
                                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                                    _gas_limit = indv.chromosome[transaction_index]["gaslimit"]
                                    indv.generator.remove_gaslimit_from_pool(_function_hash, _gas_limit)

                                elif _str_var.startswith("blocknumber_"):
                                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                                    _blocknumber = indv.chromosome[transaction_index]["blocknumber"]
                                    indv.generator.remove_blocknumber_from_pool(_function_hash, _blocknumber)

                                elif _str_var.startswith("timestamp_"):
                                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                                    _timestamp = indv.chromosome[transaction_index]["timestamp"]
                                    indv.generator.remove_timestamp_from_pool(_function_hash, _timestamp)

                                elif _str_var.startswith("call_"):
                                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                                    _var_split = str(var).split("_")
                                    _address = to_normalized_address(_var_split[2])
                                    _result = int(_var_split[3], 16)
                                    indv.generator.remove_callresult_from_pool(_function_hash, _address, _result)

                                elif _str_var.startswith("extcodesize"):
                                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                                    _var_split = str(var).split("_")
                                    _address = to_normalized_address(_var_split[2])
                                    _size = int(_var_split[3], 16)
                                    indv.generator.remove_extcodesize_from_pool(_function_hash, _address, _size)

                                elif _str_var.startswith("returndatasize"):
                                    _function_hash = indv.chromosome[transaction_index]["arguments"][0]
                                    _var_split = str(var).split("_")
                                    _address = to_normalized_address(_var_split[2])
                                    _size = int(_var_split[3], 16)
                                    indv.generator.remove_returndatasize_from_pool(_function_hash, _address, _size)

                elif instruction["op"] == "BALANCE":
                    taint = BitVec("_".join(["balance", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] in ["CALL", "STATICCALL"]:
                    _address_as_hex = to_hex(force_bytes_to_address(int_to_big_endian(convert_stack_value_to_int(result.trace[i]["stack"][-2]))))
                    if i + 1 < len(result.trace):
                        _result_as_hex = convert_stack_value_to_hex(result.trace[i + 1]["stack"][-1])
                    else:
                        _result_as_hex = ""
                    previous_call_address = _address_as_hex
                    call_type = "call"
                    if instruction["op"] == "STATICCALL":
                        call_type = "staticcall"
                    taint = BitVec("_".join([call_type, str(transaction_index), str(_address_as_hex), str(_result_as_hex), str(instruction["pc"])]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "CALLER":
                    taint = BitVec("_".join(["caller", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "CALLDATALOAD":
                    input_index = convert_stack_value_to_int(instruction["stack"][-1])
                    if input_index > 0 and _function_hash in env.interface:
                        input_index = int((input_index - 4) / 32)
                        if input_index < len(env.interface[_function_hash]):
                            parameter_type = env.interface[_function_hash][input_index]
                            if '[' in parameter_type:
                                array_size_index = convert_stack_value_to_int(result.trace[i + 1]["stack"][-1]) / 32
                                _array_size_indexes[array_size_index] = input_index
                            elif "bytes" in parameter_type:
                                pass
                            else:
                                taint = BitVec("_".join(["calldataload",
                                                         str(transaction_index),
                                                         str(input_index)
                                                         ]), 256)
                                env.symbolic_taint_analyzer.introduce_taint(taint, instruction)
                        else:
                            if input_index in _array_size_indexes:
                                array_size = convert_stack_value_to_int(result.trace[i + 1]["stack"][-1])
                                taint = BitVec("_".join(["inputarraysize",
                                                         str(transaction_index),
                                                         str(_array_size_indexes[input_index])
                                                         ]), 256)
                                env.symbolic_taint_analyzer.introduce_taint(taint, instruction)
                            else:
                                pass

                elif instruction["op"] == "CALLDATACOPY":
                    destOffset = convert_stack_value_to_int(instruction["stack"][-1])
                    offset = convert_stack_value_to_int(instruction["stack"][-2])
                    array_start_index = (offset - 4) / 32
                    lenght = convert_stack_value_to_int(instruction["stack"][-3])

                    if array_start_index - 1 in _array_size_indexes:
                        taint = BitVec("_".join(["calldatacopy",
                                                 str(transaction_index),
                                                 str(_array_size_indexes[array_start_index - 1])
                                                 ]), 256)
                        env.symbolic_taint_analyzer.introduce_taint(taint, instruction)
                    else:
                        pass

                elif instruction["op"] == "CALLDATASIZE":
                    taint = BitVec("_".join(["calldatasize", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "CALLVALUE":
                    taint = BitVec("_".join(["callvalue", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "GAS":
                    taint = BitVec("_".join(["gas", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                # BLOCK Opcodes
                elif instruction["op"] == "BLOCKHASH":
                    taint = BitVec("_".join(["blockhash", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "COINBASE":
                    taint = BitVec("_".join(["coinbase", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "TIMESTAMP":
                    taint = BitVec("_".join(["timestamp", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "NUMBER":
                    taint = BitVec("_".join(["blocknumber", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "DIFFICULTY":
                    taint = BitVec("_".join(["difficulty", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "GASLIMIT":
                    taint = BitVec("_".join(["gaslimit", str(transaction_index)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "EXTCODESIZE":
                    _address_as_hex = to_hex(
                        force_bytes_to_address(int_to_big_endian(convert_stack_value_to_int(result.trace[i]["stack"][-1]))))
                    if i + 1 < len(result.trace):
                        _result_as_hex = convert_stack_value_to_hex(result.trace[i + 1]["stack"][-1])
                    else:
                        _result_as_hex = ""
                    taint = BitVec("_".join(["extcodesize", str(transaction_index), str(_address_as_hex), str(_result_as_hex)]), 256)
                    env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                elif instruction["op"] == "RETURNDATASIZE":
                    if previous_call_address:
                        if i + 1 < len(result.trace):
                            _size = convert_stack_value_to_int(result.trace[i + 1]["stack"][-1])
                        else:
                            _size = 0
                        taint = BitVec("_".join(["returndatasize", str(transaction_index), previous_call_address, str(_size)]), 256)
                        env.symbolic_taint_analyzer.introduce_taint(taint, instruction)

                previous_instruction = instruction

            env.symbolic_taint_analyzer.clear_callstack()

            if not result.is_error and not transaction["to"]:
                contract_address = encode_hex(result.msg.storage_address)

        env.individual_branches[indv.hash] = branches

        env.symbolic_taint_analyzer.clear_storage()
        env.instrumented_evm.restore_from_snapshot()

    def get_coverage_with_children(self, children_code_coverage, code_coverage):
        code_coverage = len(code_coverage)

        for child_cc in children_code_coverage:
            code_coverage += len(child_cc)
        return code_coverage

    def symbolic_execution(self, indv_generator):
        if not self.env.args.constraint_solving:
            return

        for index, pc in enumerate(self.env.visited_branches):
            self.logger.debug("b(%d) pc : %s - visited branches : %s", index, pc,
                               self.env.visited_branches[pc].keys())

            if len(self.env.visited_branches[pc]) != 1:
                continue

            branch, _d = next(iter(self.env.visited_branches[pc].items()))

            if not _d["expression"]:
                self.logger.debug("No expression for b(%d) pc : %s", index, pc)
                continue

            negated_branch = simplify(Not(_d["expression"][-1]))

            if negated_branch in self.env.memoized_symbolic_execution:
                continue

            self.env.solver.reset()
            for expression_index in range(len(_d["expression"]) - 1):
                expression = simplify(_d["expression"][expression_index])
                self.env.solver.add(expression)
            self.env.solver.add(negated_branch)

            check = self.env.solver.check()

            if check == sat:
                model = self.env.solver.model()

                self.logger.debug("(%s) Symbolic Solution to branch %s: %s ", _d["indv_hash"], pc,
                                  "; ".join([str(x)+" ("+str(model[x])+")" for x in model]))

                for variable in model:
                    if str(variable).startswith("underflow"):
                        continue

                    var_split = str(variable).split("_")
                    transaction_index = int(var_split[1])

                    if str(variable).startswith("balance"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        opt = Optimize()
                        for expression_index in range(len(_d["expression"]) - 1):
                            opt.add(_d["expression"][expression_index])
                        opt.add(negated_branch)
                        check = opt.check()
                        if check == sat:
                            opt_model = opt.model()
                            balance = int(opt_model[variable].as_long())
                            if _d["chromosome"][transaction_index]["contract"]:
                                indv_generator.add_balance_to_pool(_function_hash, self.env.instrumented_evm.get_balance(
                                    to_canonical_address(_d["chromosome"][transaction_index]["contract"])))
                            indv_generator.add_balance_to_pool(_function_hash, balance)

                    elif str(variable).startswith("blocknumber"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        blocknumber = int(model[variable].as_long())
                        indv_generator.add_blocknumber_to_pool(_function_hash,
                                                               self.env.instrumented_evm.vm.state.block_number)
                        indv_generator.add_blocknumber_to_pool(_function_hash, blocknumber)

                    elif str(variable).startswith("call_") or str(variable).startswith("staticcall_"):
                        address = to_normalized_address(var_split[2])
                        old_result = int(var_split[3], 16)
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        new_result = 1 - old_result
                        indv_generator.add_callresult_to_pool(_function_hash, address, old_result)
                        indv_generator.add_callresult_to_pool(_function_hash, address, new_result)

                    elif str(variable).startswith("caller_"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        if model[variable].as_long() > 8 and model[variable].as_long() < 2**160:
                            account_address = normalize_32_byte_hex_address("0x"+hex(model[variable].as_long()).replace("0x", "").zfill(40))
                            if not self.env.instrumented_evm.has_account(account_address):
                                self.env.instrumented_evm.restore_from_snapshot()
                                self.env.instrumented_evm.accounts.append(self.env.instrumented_evm.create_fake_account(account_address))
                                self.env.instrumented_evm.create_snapshot()
                            indv_generator.add_account_to_pool(_function_hash, _d["chromosome"][transaction_index]["account"])
                            indv_generator.add_account_to_pool(_function_hash, account_address)

                    elif str(variable).startswith("calldatacopy_"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        parameter_index = int(var_split[2])
                        if "[" in indv_generator.interface[_function_hash][parameter_index]:
                            if indv_generator.interface[_function_hash][parameter_index].startswith("int"):
                                argument = model[variable].as_signed_long()
                            elif indv_generator.interface[_function_hash][parameter_index].startswith("address"):
                                try:
                                    _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                                    argument = normalize_32_byte_hex_address(hex(model[variable].as_long()))
                                    if not self.env.instrumented_evm.has_account(argument):
                                        self.env.instrumented_evm.restore_from_snapshot()
                                        self.env.instrumented_evm.accounts.append(self.env.instrumented_evm.create_fake_account(argument))
                                        self.env.instrumented_evm.create_snapshot()
                                except Exception as e:
                                    self.logger.error("(%s) [symbolic execution : calldatacopy ] %s", _function_hash,
                                                       e)
                                    continue
                            else:
                                argument = model[variable].as_long()
                            indv_generator.add_argument_to_pool(_function_hash, parameter_index, _d["chromosome"][transaction_index]["arguments"][parameter_index + 1])
                            indv_generator.add_argument_to_pool(_function_hash, parameter_index, argument)

                    elif str(variable).startswith("calldataload_"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        parameter_index = int(var_split[2])
                        # TODO: THE SOLVER DOES NOT CONSIDER THE MAX SIZE OF THE VARIABLE
                        #   GENERATING LATER A eth_abi.exceptions.ValueOutOfBounds
                        if "[" in indv_generator.interface[_function_hash][parameter_index]:
                            if indv_generator.interface[_function_hash][parameter_index].startswith("int"):
                                argument = model[variable].as_signed_long()
                            elif indv_generator.interface[_function_hash][parameter_index].startswith("address"):
                                try:
                                    _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                                    argument = normalize_32_byte_hex_address(hex(model[variable].as_long()))
                                    if not self.env.instrumented_evm.has_account(argument):
                                        self.env.instrumented_evm.restore_from_snapshot()
                                        self.env.instrumented_evm.accounts.append(self.env.instrumented_evm.create_fake_account(argument))
                                        self.env.instrumented_evm.create_snapshot()
                                except Exception as e:
                                    self.logger.error("(%s) [symbolic execution : calldataload ] %s", _function_hash,
                                                       e)
                                    continue

                        elif indv_generator.interface[_function_hash][parameter_index].startswith("int"):
                            argument = model[variable].as_signed_long()

                        elif indv_generator.interface[_function_hash][parameter_index] == "address":
                            try:
                                _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                                argument = to_hex(
                                    force_bytes_to_address(int_to_big_endian(int(model[variable].as_long()))))
                                if not self.env.instrumented_evm.has_account(argument):
                                    self.env.instrumented_evm.restore_from_snapshot()
                                    self.env.instrumented_evm.accounts.append(self.env.instrumented_evm.create_fake_account(argument))
                                    self.env.instrumented_evm.create_snapshot()
                            except Exception as e:
                                self.logger.error("(%s) [symbolic execution : calldataload ] %s", _function_hash, e)
                                continue

                        elif indv_generator.interface[_function_hash][parameter_index] == "string":
                            argument = _d["chromosome"][transaction_index]["arguments"][parameter_index + 1]
                        elif indv_generator.interface[_function_hash][parameter_index].startswith("uint"):
                            argument = model[variable].as_long()
                            bits = 256
                            if indv_generator.interface[_function_hash][parameter_index] != "uint":
                                bits = int(indv_generator.interface[_function_hash][parameter_index].replace("uint", ""))
                            base = 1 << bits
                            argument %= base
                        else:
                            argument = model[variable].as_long()
                            self.env.solver.add(BitVec(str(variable), 256) != BitVecVal(0, 256))
                            for variable_2 in model:
                                if variable_2 != variable and str(variable_2).startswith("callvalue"):
                                    callvalue_index = int(str(variable_2).split("_")[1])
                                    self.env.solver.add(BitVec(str(variable_2), 256) == BitVecVal(int(_d["chromosome"][callvalue_index]["amount"]), 256))
                            check = self.env.solver.check()
                            if check == sat:
                                model = self.env.solver.model()
                                argument = model[variable].as_long()

                        indv_generator.add_argument_to_pool(_function_hash, parameter_index, _d["chromosome"][transaction_index]["arguments"][parameter_index + 1])
                        indv_generator.add_argument_to_pool(_function_hash, parameter_index, argument)

                    elif str(variable).startswith("callvalue_"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        amount = model[variable].as_long()
                        if amount > settings.ACCOUNT_BALANCE:
                            amount = settings.ACCOUNT_BALANCE
                        indv_generator.remove_amount_from_pool(_function_hash, 0)
                        indv_generator.remove_amount_from_pool(_function_hash, 1)
                        indv_generator.add_amount_to_pool(_function_hash, _d["chromosome"][transaction_index]["amount"])
                        indv_generator.add_amount_to_pool(_function_hash, amount)

                    elif str(variable).startswith("gas_"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        indv_generator.add_gaslimit_to_pool(_function_hash, _d["chromosome"][transaction_index]["gaslimit"])
                        indv_generator.add_gaslimit_to_pool(_function_hash, model[variable].as_long())

                    elif str(variable).startswith("inputarraysize"):
                        opt = Optimize()
                        for expression_index in range(len(_d["expression"]) - 1):
                            opt.add(_d["expression"][expression_index])
                        opt.add(negated_branch)
                        check = opt.check()
                        if check == sat:
                            opt_model = opt.model()
                            array_size = opt_model[variable].as_long()
                            _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                            parameter_index = int(var_split[2])
                            indv_generator.add_parameter_array_size(_function_hash, parameter_index, len(
                                _d["chromosome"][transaction_index]["arguments"][parameter_index + 1]))
                            indv_generator.add_parameter_array_size(_function_hash, parameter_index, array_size)

                    elif str(variable).startswith("timestamp"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        timestamp = int(model[variable].as_long())
                        indv_generator.add_timestamp_to_pool(_function_hash, self.env.instrumented_evm.vm.state.timestamp)
                        indv_generator.add_timestamp_to_pool(_function_hash, timestamp)

                    elif str(variable).startswith("calldatasize"):
                        pass

                    elif str(variable).startswith("extcodesize"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        _address = to_normalized_address(var_split[2])
                        indv_generator.add_extcodesize_to_pool(_function_hash, _address, int(var_split[3], 16))
                        indv_generator.add_extcodesize_to_pool(_function_hash, _address, int(model[variable].as_long()))

                    elif str(variable).startswith("returndatasize"):
                        _function_hash = _d["chromosome"][transaction_index]["arguments"][0]
                        _address = to_normalized_address(var_split[2])
                        _size = int(var_split[3], 16)
                        indv_generator.add_returndatasize_to_pool(_function_hash, _address, int(var_split[3], 16))
                        indv_generator.add_returndatasize_to_pool(_function_hash, _address, int(model[variable].as_long()))

                    else:
                        self.logger.warning("Unknown symbolic variable: %s ", str(variable))

            self.env.memoized_symbolic_execution[negated_branch] = True

    def finalize(self, population, engine):
        execution_end = time.time()
        execution_delta = execution_end - self.env.execution_begin

        self.logger.title("-----------------------------------------------------")
        msg = 'Number of generations: \t {}'.format(engine.current_generation + 1)
        self.logger.info(msg)
        msg = 'Number of transactions: \t {} ({} unique)'.format(self.env.nr_of_transactions, len(self.env.unique_individuals))
        self.logger.info(msg)
        msg = 'Transactions per second: \t {:.0f}'.format(self.env.nr_of_transactions / execution_delta)
        self.logger.info(msg)
        code_coverage_percentage = 0
        if len(self.env.overall_pcs) > 0:
            code_coverage_percentage = (len(self.env.code_coverage) / len(self.env.overall_pcs)) * 100
        msg = 'Total code coverage: \t {:.2f}% ({}/{})'.format(code_coverage_percentage,
                                                                len(self.env.code_coverage),
                                                                len(self.env.overall_pcs))
        self.logger.info(msg)
        branch_coverage = 0
        for pc in self.env.visited_branches:
            branch_coverage += len(self.env.visited_branches[pc])
        branch_coverage_percentage = 0
        if len(self.env.overall_jumpis) > 0:
            branch_coverage_percentage = (branch_coverage / (len(self.env.overall_jumpis) * 2)) * 100
        msg = 'Total branch coverage: \t {:.2f}% ({}/{})'.format(branch_coverage_percentage,
                                                                 branch_coverage, len(self.env.overall_jumpis) * 2)
        self.logger.info(msg)
        msg = 'Total execution time: \t {:.2f} seconds'.format(execution_delta)
        self.logger.info(msg)
        msg = 'Total memory consumption: \t {:.2f} MB'.format(psutil.Process(os.getpid()).memory_info().rss/1024/1024)
        self.logger.info(msg)

        # Save to results
        self.env.results["transactions"] = {"total": self.env.nr_of_transactions,
                                            "per_second": self.env.nr_of_transactions / execution_delta}
        self.env.results["code_coverage"] = {"percentage": code_coverage_percentage,
                                             "covered": len(self.env.code_coverage),
                                             "total": len(self.env.overall_pcs),
                                             "covered_with_children": self.get_coverage_with_children(
                                                 self.env.children_code_coverage,
                                                 self.env.code_coverage),
                                             "total_with_children": self.env.len_overall_pcs_with_children
                                             }
        self.env.results["branch_coverage"] = {"percentage": branch_coverage_percentage,
                                               "covered": branch_coverage,
                                               "total": len(self.env.overall_jumpis) * 2}
        self.env.results["execution_time"] = execution_delta
        self.env.results["memory_consumption"] = psutil.Process(os.getpid()).memory_info().rss/1024/1024
        self.env.results["address_under_test"] = self.env.population.indv_generator.contract
        self.env.results["seed"] = self.env.seed

        #  Write results to file
        if self.env.args.results:
            results = {}
            if self.env.args.results.lower().endswith(".json"):
                if os.path.exists(self.env.args.results):
                    with open(self.env.args.results, 'r') as file:
                        results = json.load(file)
                results[self.env.contract_name] = self.env.results
                with open(self.env.args.results, 'w') as file:
                    json.dump(results, file)
            else:
                if os.path.exists(self.env.args.results + '/' + os.path.splitext(os.path.basename(self.env.contract_name))[0] + '.json'):
                    with open(self.env.args.results + '/' + os.path.splitext(os.path.basename(self.env.contract_name))[0] + '.json', 'r') as file:
                        results = json.load(file)
                results[self.env.contract_name] = self.env.results
                with open(self.env.args.results + '/' + os.path.splitext(os.path.basename(self.env.contract_name))[0] + '.json', 'w') as file:
                    json.dump(results, file)

        diff = list(set(self.env.code_coverage).symmetric_difference(set([hex(x) for x in self.env.overall_pcs])))
        self.logger.debug("Instructions not executed: %s", sorted(diff))