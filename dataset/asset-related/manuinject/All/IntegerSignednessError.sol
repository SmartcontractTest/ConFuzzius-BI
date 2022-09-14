pragma solidity 0.4.26;

//based on Osiris

/*
If A is less than 0, the value of B will be large when A is converted to an 
unsigned integer B of the same width. Consider withdrawOnce function in this 
example, enter a negative value will lead to the contract when the balance 
of a roll out more than 1 ether.
*/

contract signednessError{
    mapping(address => uint) public balance;
    address public owner;

    constructor() public payable{
        owner = msg.sender;
        require(msg.value >= 0);
    }

    function withdrawOnce (int amount) public {
        if ( amount > 1 ether ) {
            revert() ;
        }
        //In Solidity, casting a negative integer to an unsigned integer results in an error and does not throw an exception. Avoid such conversions.
        msg.sender.transfer(uint64(amount));
        balance [msg.sender] -= uint64(amount) ;
    }
}
