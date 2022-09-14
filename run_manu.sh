#! /bin/bash

python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/Essence.sol -c Essence --solc v0.4.26 --evm byzantium -g 20 &> result/Essence.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/Essence.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/ExoToken1.sol -c ExoToken --solc v0.4.26 --evm byzantium -g 20 &> result/ExoToken1.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/ExoToken1.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/ExoToken2.sol -c ExoToken --solc v0.4.26 --evm byzantium -g 20 &> result/ExoToken2.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/ExoToken2.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/batchTransfer.sol -c BToken --solc v0.4.26 --evm byzantium -g 20 &> result/batchTransfer.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/batchTransfer.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/insecure_transfer.sol -c IntegerOverflowAdd --solc v0.4.26 --evm byzantium -g 20 &> result/insecure_transfer.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/insecure_transfer.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/IntegerSignednessError.sol -c signednessError --solc v0.4.26 --evm byzantium -g 20 &> result/IntegerSignednessError.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/IntegerSignednessError.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/MyToken.sol -c MyToken --solc v0.4.26 --evm byzantium -g 20 &> result/MyToken.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/MyToken.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/PIGGY_with_worng_op_1.sol -c PIGGY_BANK --solc v0.4.26 --evm byzantium -g 20 &> result/PIGGY_with_worng_op_1.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/PIGGY_with_worng_op_1.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/PIGGY_with_worng_op_2.sol -c PIGGY_BANK --solc v0.4.26 --evm byzantium -g 20 &> result/PIGGY_with_worng_op_2.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/PIGGY_with_worng_op_2.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/RTB0.sol -c RTB0 --solc v0.4.26 --evm byzantium -g 20 &> result/RTB0.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/RTB0.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/TalentCard.sol -c TalentCard --solc v0.4.26 --evm byzantium -g 20 &> result/TalentCard.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/TalentCard.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/token.sol -c Token --solc v0.4.26 --evm byzantium -g 20 &> result/token.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/token.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/token2.sol -c Token --solc v0.4.26 --evm byzantium -g 20 &> result/token2.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/token2.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/token_with_wrong_op_1.sol -c Token --solc v0.4.26 --evm byzantium -g 20 &> result/token_with_wrong_op_1.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/token_with_wrong_op_1.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/token_with_wrong_op_2.sol -c Token --solc v0.4.26 --evm byzantium -g 20 &> result/token_with_wrong_op_2.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/token_with_wrong_op_2.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/tokensalechallenge.sol -c TokenSaleChallenge --solc v0.4.26 --evm byzantium -g 20 &> result/tokensalechallenge.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/tokensalechallenge.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/truncationError.sol -c truncationError --solc v0.4.26 --evm byzantium -g 20 &> result/truncationError.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/truncationError.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/underFlow.sol -c Token --solc v0.4.26 --evm byzantium -g 20 &> result/underFlow.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/underFlow.txt
python3 fuzzer/main.py -s dataset/asset-related/manuinject/All/overFlow.sol -c Token --solc v0.4.26 --evm byzantium -g 20 &> result/overFlow.txt
sed -i -r "s:\x1B\[[0-9;]*[mK]::g" result/overFlow.txt