#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import random

from copy import deepcopy, copy
from eth_abi import encode_abi
from eth_abi.exceptions import EncodingTypeError, ValueOutOfBounds, ParseError

from utils.utils import initialize_logger

class Individual():
    def __init__(self, generator):
        self.logger = initialize_logger("Individual")
        self.chromosome = []
        self.bookingfun = []   #@@@@@sjl: init here!
        self.solution = []
        self.generator = generator

    @property
    def hash(self):
        if not self.solution:
            self.solution = self.decode()
        return str(hash(str([tx for tx in self.solution])))

    def init(self, chromosome=None):
        # self.bookingfun = self.generator.generate_random_individual()   #@@@@@sjl: init here!
        if not chromosome:
            self.chromosome = self.generator.generate_random_individual()
        else:
            self.chromosome = chromosome
            # print("@@@@@@@@ individuals: chromosome in def init(self, chromosome=None) s% 1111111111",
            #       self.chromosome)
        self.solution = self.decode()
        return self

    def clone(self):
        indv = self.__class__(generator=self.generator)
        indv.init(chromosome=deepcopy(self.chromosome))
        return indv

    def decode(self):
        solution = []

        for i in range(len(self.chromosome)):
            transaction = {}
            # print("@@@@@@@@ individuals: accounts in function decode to get solution s% 1111111111", self.generator.accounts)

            transaction["from"] = copy(self.chromosome[i]["account"])
            transaction["to"] = copy(self.chromosome[i]["contract"])
            transaction["value"] = copy(self.chromosome[i]["amount"])
            transaction["gaslimit"] = copy(self.chromosome[i]["gaslimit"])
            transaction["data"] = self.get_transaction_data_from_chromosome(i)

            checker = {}  # @@@ added by sjl at 20220905 , to check the asset number
            checker["from"] = copy(self.chromosome[i]["account"])   # @@@ added by sjl at 20220905
            checker["to"] = copy(self.chromosome[i]["contract"])   # @@@ added by sjl at 20220905
            checker["value"] = copy(self.chromosome[i]["amount"])   # @@@ added by sjl at 20220905
            checker["gaslimit"] = copy(self.chromosome[i]["gaslimit"])    # @@@ added by sjl at 20220905
            booking_arguments_list = self.chromosome[i]["booking_arguments_list"]  # function balanceOf
            # print("@@@@@@@@individuals: booking_arguments_list_from_chromosome  s% 1111111111", booking_arguments_list)
            data_list = self.get_chcker_data_from_chromosome(i)
            # print("@@@@@@@@individuals  data_list data_list  s% 1111111111", data_list)
            checker["data_list"] = data_list    # @@@ added by sjl at 20220905 :



            block = {}
            if "timestamp" in self.chromosome[i] and self.chromosome[i]["timestamp"] is not None:
                block["timestamp"] = copy(self.chromosome[i]["timestamp"])
            if "blocknumber" in self.chromosome[i] and self.chromosome[i]["blocknumber"] is not None:
                block["blocknumber"] = copy(self.chromosome[i]["blocknumber"])

            global_state = {}
            if "balance" in self.chromosome[i] and self.chromosome[i]["balance"] is not None:
                global_state["balance"] = copy(self.chromosome[i]["balance"])
            if "call_return" in self.chromosome[i] and self.chromosome[i]["call_return"] is not None\
                    and len(self.chromosome[i]["call_return"]) > 0:
                global_state["call_return"] = copy(self.chromosome[i]["call_return"])
            if "extcodesize" in self.chromosome[i] and self.chromosome[i]["extcodesize"] is not None\
                    and len(self.chromosome[i]["extcodesize"]) > 0:
                global_state["extcodesize"] = copy(self.chromosome[i]["extcodesize"])

            environment = {}
            if "returndatasize" in self.chromosome[i] and self.chromosome[i]["returndatasize"] is not None:
                environment["returndatasize"] = copy(self.chromosome[i]["returndatasize"])

            input = {"transaction":transaction, "checker":checker, "block" : block, "global_state" : global_state, "environment": environment}
            solution.append(input)
        # print("@@@@@@@@solution: Decode  s% 1111111111", solution)
        return solution

    def get_transaction_data_from_chromosome(self, chromosome_index):
        # print("@@@@@@@@individuals: get_transaction_data_from_chromosome  s% 1111111111", self.chromosome)
        data = ""
        arguments = []
        function = None

        for j in range(len(self.chromosome[chromosome_index]["arguments"])):
            # print("@@@@@@@@individuals: self.chromosome[chromosome_index][arguments]  s% 1111111111", j,self.chromosome[chromosome_index]["arguments"])
            if self.chromosome[chromosome_index]["arguments"][j] == "fallback":
                function = "fallback"
                data += random.choice(["", "00000000"])
                # print("@@@@@@@@ transaction_data from if  s% 1111111111", data)
            elif self.chromosome[chromosome_index]["arguments"][j] == "constructor":
                function = "constructor"
                data += self.generator.bytecode
                # print("@@@@@@@@ transaction_data from elif111  s% 1111111111", data)
            elif not type(self.chromosome[chromosome_index]["arguments"][j]) is bytearray and \
                    not type(self.chromosome[chromosome_index]["arguments"][j]) is list and \
                    self.chromosome[chromosome_index]["arguments"][j] in self.generator.interface:
                function = self.chromosome[chromosome_index]["arguments"][j]
                data += self.chromosome[chromosome_index]["arguments"][j]
                # print("@@@@@@@@ transaction_data from elif2222  s% 1111111111", data)
            else:
                arguments.append(self.chromosome[chromosome_index]["arguments"][j])
                # print("@@@@@@@@ transaction_arguments from else  s% 1111111111", arguments)
        # print("@@@@@@@@ transaction_function  s% 1111111111", function)
        # print("@@@@@@@@ transaction_arguments transaction_arguments s% 1111111111", arguments)
        try:
            argument_types = [argument_type.replace(" storage", "").replace(" memory", "") for argument_type in self.generator.interface[function]]
            data += encode_abi(argument_types, arguments).hex()  #  original data is function, after this , data contain encoded arguments
        except Exception as e:
            self.logger.error("%s", e)
            self.logger.error("%s: %s -> %s", function, self.generator.interface[function], arguments)
            sys.exit(-6)
        # print("@@@@@@@@individuals: transaction_data transaction_data s% 1111111111", data)
        return data

    def get_chcker_data_from_chromosome(self, chromosome_index):
        # print("@@@@@@@@individuals: get_transaction_data_from_chromosome  s% 1111111111", self.chromosome)
        data_list =[]
        accouts_in_env = self.generator.accounts


        for j in range(len(self.chromosome[chromosome_index]["booking_arguments_list"])): #[['0x70a08231', '0xcafebabecafebabecafebabecafebabecafebabe'], ['0x70a08231', '0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef'], ['0x70a08231', '0xffffffffffffffffffffffffffffffffffffffff']]

            data = ""

            # print("self.chromosome[chromosome_index][booking_arguments_list] s%" ,self.chromosome[chromosome_index]["booking_arguments_list"])

            function = self.chromosome[chromosome_index]["booking_arguments_list"][j][0]
            # print("@@@@@@@@ checker_function  s% 1111111111", function)
            arguments = [self.chromosome[chromosome_index]["booking_arguments_list"][j][1]]
            # print("@@@@@@@@ checker_arguments  s% 1111111111", arguments)
            data = function
            # print("@@@@@@@@ checker_data checker_data  s% 1111111111", data)
            try:
                argument_types = [argument_type.replace(" storage", "").replace(" memory", "") for argument_type in self.generator.interface[function]]
                # print("@@@@@@@@ argument_types  s% 1111111111", argument_types)
                data += encode_abi(argument_types, arguments).hex()
                # print("@@@@@@@@individuals: data data data  s% 1111111111",
                #       data)
                # print("@@@@@@@@individuals:  argument_types  s% 1111111111", argument_types)
                # print("@@@@@@@@individuals:  arguments  s% 1111111111", arguments)
            except Exception as e:
                self.logger.error("%s", e)
                self.logger.error("%s: %s -> %s", function, self.generator.interface[function], arguments)
                sys.exit(-6)
            data_list.append(data)
        # print("@@@@@@@@individuals: checker_data_list checker_data_list checker_data_list  s% 1111111111", data_list)
        return data_list


    # def get_chcker_data_from_chromosome(self, chromosome_index):
    #     # print("@@@@@@@@individuals: get_transaction_data_from_chromosome  s% 1111111111", self.chromosome)
    #     data = ""
    #     arguments = []
    #     function = None
    #     if len(self.chromosome[chromosome_index]["booking_arguments"]) == 2: #for j in range(len(self.chromosome[chromosome_index]["booking_arguments"])):
    #         # print("@@@@@@@@individuals: self.chromosome[chromosome_index][booking_argumentsbooking_arguments]  s% 1111111111", self.chromosome[chromosome_index]["booking_arguments"][0])
    #         if self.chromosome[chromosome_index]["booking_arguments"][0] == "fallback":
    #             function = "fallback"
    #             data += random.choice(["", "00000000"])
    #         elif self.chromosome[chromosome_index]["booking_arguments"][0] == "constructor":
    #             function = "constructor"
    #             data += self.generator.bytecode
    #         elif not type(self.chromosome[chromosome_index]["booking_arguments"][0]) is bytearray and \
    #                 not type(self.chromosome[chromosome_index]["booking_arguments"][0]) is list and \
    #                 self.chromosome[chromosome_index]["booking_arguments"][0] in self.generator.interface:
    #             function = self.chromosome[chromosome_index]["booking_arguments"][0]
    #             data += self.chromosome[chromosome_index]["booking_arguments"][0]
    #         else:
    #             arguments.append(self.chromosome[chromosome_index]["booking_arguments"][0])
    #     try:
    #         argument_types = [argument_type.replace(" storage", "").replace(" memory", "") for argument_type in self.generator.interface[function]]
    #         data += encode_abi(argument_types, arguments).hex()
    #     except Exception as e:
    #         self.logger.error("%s", e)
    #         self.logger.error("%s: %s -> %s", function, self.generator.interface[function], arguments)
    #         sys.exit(-6)
    #     # print("@@@@@@@@individuals: datadatadatadatadatadatadata  s% 1111111111", data)
    #     # print("@@@@@@@@individuals: booking_arguments_data booking_arguments_data booking_arguments_data s% 1111111111", data)
    #     return data
