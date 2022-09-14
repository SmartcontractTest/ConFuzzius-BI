class Generator:
    def __init__(self, interface, booking, bytecode, accounts, contract):

        self.interface = interface
        self.bytecode = bytecode
        self.accounts = accounts
        self.contract = contract
        self.booking = booking    # {'0x27e235e3': ['address'], '0x70a08231': ['address'], 'fallback': []}


        # Pools

        self.accounts_pool = {}
        self.amounts_pool = {}
        self.arguments_pool = {}
        self.timestamp_pool = {}
        self.blocknumber_pool = {}
        self.balance_pool = {}
        self.callresult_pool = {}
        self.gaslimit_pool = {}
        self.extcodesize_pool = {}
        self.returndatasize_pool = {}
        self.argument_array_sizes_pool = {}

    def add_account(self,input):
        self.accounts.append(input)
        print(self.accounts)

    def test(self):

        add=2
        self.add_account(add)
        print(self)

g = Generator(interface=1, booking=1, bytecode=1, accounts=[1], contract=1)
g.test()
print(g.accounts)