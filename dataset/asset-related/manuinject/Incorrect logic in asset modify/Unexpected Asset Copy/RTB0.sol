

pragma solidity ^0.4.23;


library SafeMath {

    function mul(uint256 a, uint256 b) internal pure returns(uint256) {
        if (a == 0) {
            return 0;
        }
        uint256 c = a * b;
        assert(c / a == b);
        return c;
    }


    function div(uint256 a, uint256 b) internal pure returns(uint256) {

        uint256 c = a / b;

        return c;
    }


    function sub(uint256 a, uint256 b) internal pure returns(uint256) {
        assert(b <= a);
        return a - b;
    }


    function add(uint256 a, uint256 b) internal pure returns(uint256) {
        uint256 c = a + b;
        assert(c >= a);
        return c;
    }


    function pwr(uint256 x, uint256 y)
        internal
        pure
        returns (uint256)
    {
        if (x==0)
            return (0);
        else if (y==0)
            return (1);
        else{
            uint256 z = x;
            for (uint256 i = 1; i < y; i++)
                z = mul(z,x);
            return (z);
        }
    }
}



contract RTB0 {
    using SafeMath for uint256;

    uint8 public decimals = 0;
    uint256 public totalSupply = 300;
    uint256 public totalSold = 0;
    uint256 public price = 1 ether;
    string public name = "Retro Block Token 1";
    string public symbol = "RTB0";
    address public owner;
    address public finance;

    mapping (address=>uint256) received;
    uint256 profit;
    address public jackpot;
    mapping (address=>uint256) changeProfit;

    mapping (address=>uint256) balances;
    mapping (address=>mapping (address=>uint256)) allowed;

    event Transfer(address indexed _from, address indexed _to, uint256 _value);
    event Approval(address indexed _owner, address indexed _spender, uint256 _value);
    event AddProfit(address indexed _from, uint256 _value, uint256 _newProfit);
    event Withdraw(address indexed _addr, uint256 _value);


    constructor() public payable{
        owner = msg.sender;
        balances[this] = 300;
    }

    function() public payable {
        if(msg.value > 0){
            profit = msg.value.div(totalSupply).add(profit);
            emit AddProfit(msg.sender, msg.value, profit);
        }
    }

    function balanceOf(address _owner) external view returns (uint256) {
        return balances[_owner];
    }

    function transfer(address _from, address _to, uint256 _value) external returns (bool) { // bug : Unexpected Asset Copy
        require(_to != address(0), "Receiver address cannot be null");
        require(_value > 0 && _value <= balances[_from]);
        uint256 newToVal = balances[_to] + _value;
        assert(newToVal >= balances[_to]);
        uint256 newFromVal = balances[_from] - _value;
        balances[_from] =  newFromVal;
        balances[_to] = newToVal;
        uint256 temp = _value.mul(profit);
        changeProfit[_from] = changeProfit[_from].add(temp);
        received[_to] = received[_to].add(temp);
        emit Transfer(_from, _to, _value);
        return true;
    }

}