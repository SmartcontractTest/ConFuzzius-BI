/* @Labeled: [35] */
pragma solidity ^0.4.19;

contract PIGGY_BANK
{
    mapping (address => uint) public Accounts;

    uint public MinSum = 1 ether;


    uint putBlock;

    function PIGGY_BANK(address _log)
    public
    {

    }

    function Put(address to)
    public
    payable
    {
        Accounts[to]+=msg.value;

        putBlock = block.number;
    }

    function Collect(uint _am)
    public
    payable
    {
        if(Accounts[msg.sender]>=MinSum && _am<=Accounts[msg.sender] && block.number>putBlock)
        {
            msg.sender.call.value(_am)();
            Accounts[msg.sender]=-_am; //bug:Incorrect Arithmetic Operator

        }
    }

    function()
    public
    payable
    {
        Put(msg.sender);
    }

}