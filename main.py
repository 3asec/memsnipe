from web3 import Web3
import json, time, requests, os, sys
from dotenv import load_dotenv

load_dotenv()
web3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))

with open('./abi.json') as f:
    abi = json.load(f)

with open('./erc20.json') as f_erc:
    abi_erc = json.load(f_erc)

os.system('cls' if os.name == 'nt' else 'clear')
if not web3.is_connected():
    print("Failed to Connect to Base")
    sys.exit()
print(f"Starting Sniper\nEnhanced Version")

privatekey = os.getenv("PRIVATE_KEY")
address = web3.eth.account.from_key(privatekey).address
amount = web3.to_wei(float(input("Enter Amount ETH to Snipe: ")), 'ether')
minfollowers = int(input("Enter Minimum Followers: "))
cl = int(input("Cut Loss Percent: "))
tp = int(input("Take Profit Percent: "))
amount_percentage = amount / 100
amount_cl = (amount_percentage * 98) - (amount_percentage * cl)
amount_tp = (amount_percentage * tp) + amount
print(f"Mempool Started From Block: {web3.eth.get_block('latest')['number']}")
contracts = web3.eth.contract(
    address='0x250c9FB2b411B48273f69879007803790A6AeA47',
    abi=abi
)

def get_price_sell(token_address_checksum, amount):
    try:
        response = requests.post("https://trading-api-labs.interface.gateway.uniswap.org/v1/quote", json={
            "type": "EXACT_INPUT",
        "gasStrategies": [{"limitInflationFactor": 1.15,"maxPriorityFeeGwei": 40,"minPriorityFeeGwei": 2,"percentileThresholdFor1559Fee": 75,"priceInflationFactor": 1.5}],
        "swapper": address,
        "amount": str(amount),
        "tokenOut": "0x0000000000000000000000000000000000000000",
        "tokenIn": token_address_checksum,
        "urgency": "normal",
        "tokenInChainId": 8453,
        "tokenOutChainId": 8453,
        "protocols": ["V3", "V2"],
    }, headers={
        "origin": "https://app.uniswap.org",
        "referer": "https://app.uniswap.org/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-api-key": "JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo",
        "x-app-version": "",
        "x-request-source": "uniswap-web",
        "x-universal-router-version": "1.2"
        })
        data = response.json()
        return int(data["quote"]["output"]["amount"])
    except Exception:
        return get_price_sell(token_address_checksum, amount)
    
def approve_tx(token_address_checksum, amounts):
    nonce = web3.eth.get_transaction_count(address)
    tx = {
        "to": web3.to_checksum_address(token_address_checksum),
        "value": 0,
        "gasPrice": int(web3.eth.gas_price * 3),
        "data": "0x095ea7b3000000000000000000000000c6836c774927fca021cb19f57e5d7bff7dcd0c34"+web3.to_hex(amounts)[2:].zfill(64),
        "chainId": 8453,
        "gas": 100000,
        "nonce": nonce
    }
    signed_txns = web3.eth.account.sign_transaction(tx, private_key=privatekey)
    tx_hash = web3.eth.send_raw_transaction(signed_txns.raw_transaction)
    print("Recipt Approve >> " + web3.to_hex(tx_hash) +"\nSubmitted on block: " + str(web3.eth.get_block('latest')['number']))
    web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction Confirmed on Block: " + str(web3.eth.get_block('latest')['number']))

def sell_tx(token_address_checksum):
    token_address = token_address_checksum.lower()
    erc20 = web3.eth.contract(address=web3.to_checksum_address(token_address_checksum), abi=abi_erc)
    allowances = erc20.functions.allowance(address, "0xc6836c774927FCA021CB19F57E5D7BFf7dcD0C34").call()
    amounts = erc20.functions.balanceOf(address).call()
    if allowances == 0:
        approve_tx(token_address_checksum, amounts)
    ahaaaa = int(get_price_sell(token_address, amounts))
    timeout = 0
    while True:
        if(ahaaaa <= int(amount_cl)):
            print("Cut Loss")
            break
        if(ahaaaa >= int(amount_tp)):
            print("Take Profit")
            break
        if(timeout >= 40):
            print("Timeout")
            break
        time.sleep(1)
        ahaaaa = int(get_price_sell(token_address, amounts))
        print(f"Estimated ETH : {str(web3.from_wei(ahaaaa, 'ether'))}")
        timeout += 1

    nonce = web3.eth.get_transaction_count(address)
    tx = {
        "to": "0xc6836c774927FCA021CB19F57E5D7BFf7dcD0C34", 
        "value": 0,
        "gasPrice": int(web3.eth.gas_price * 3),
        "data": "0x0091ad5c000000000000000000000000" + token_address[2:]+web3.to_hex(amounts)[2:].zfill(64),
        "chainId": 8453,
        "gas": 250000,
        "nonce": nonce
    }
    signed_txns = web3.eth.account.sign_transaction(tx, private_key=privatekey)
    tx_hash = web3.eth.send_raw_transaction(signed_txns.raw_transaction)
    print("Recipt Sell >> " + web3.to_hex(tx_hash) +"\nSubmitted on block: " + str(web3.eth.get_block('latest')['number']))
    web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction Confirmed on Block: " + str(web3.eth.get_block('latest')['number']))

def buy_tx(token_address_checksum):
    token_address = token_address_checksum.lower()
    nonce = web3.eth.get_transaction_count(address)
    tx = {
        "to": "0xc6836c774927FCA021CB19F57E5D7BFf7dcD0C34",
        "value": amount,
        "gasPrice": int(web3.eth.gas_price * 3),
        "data": "0x96bab5ea000000000000000000000000" + token_address[2:],
        "chainId": 8453,
        "gas": 250000,
        "nonce": nonce
    }
    signed_txns = web3.eth.account.sign_transaction(tx, private_key=privatekey)
    tx_hash = web3.eth.send_raw_transaction(signed_txns.raw_transaction)
    print("Recipt Swap >> " + web3.to_hex(tx_hash) +"\nSubmitted on block: " + str(web3.eth.get_block('latest')['number']))
    web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction Confirmed on Block: " + str(web3.eth.get_block('latest')['number']))

def check_deployer(deployer, token_address, name, symbol, supply):
    try:
        response = requests.get(f"https://relayer.host/api/{token_address}/{deployer}").json()
        Username = response["username"]
        followers = response["followers"]
        following = response["following"]
        data = (f"New Contract Detected\n>>> Contract Address: {token_address}\n>>> Name: {name}\n>>> Symbol: {symbol}\n>>> Deployer: {deployer}\n>>> Supply: {float(web3.from_wei(supply, 'ether'))}\n>>> Username: {Username}\n>>> Followers: {str(followers)}\n>>> Following: {str(following)}\n>>> Date: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC")
        print(data)
        if followers >= minfollowers:
            buy_tx(token_address)
            sell_tx(token_address)
        else:
            print("Not Enough Followers Skipping...")
    except Exception as error:
        print("Error:", error)

def handle_event(event):
    try:
        token_address = event['args']['tokenAddress']
        deployer = event['args']['deployer']
        name = event['args']['name']
        symbol = event['args']['symbol']
        supply = event['args']['supply']
        check_deployer(deployer, token_address, name, symbol, supply)
    except Exception as error:
        print("Error:", error)

event_filter = contracts.events.TokenCreated.create_filter(from_block='latest')
while True:
    try:
        for event in event_filter.get_new_entries():
            handle_event(event)
    except Exception as e:
        print("Error fetching new entries:", e)
    time.sleep(1)