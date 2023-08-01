import datetime
import hashlib
import json
from flask import Flask, jsonify, request
from uuid import uuid4
from urllib.parse import urlparse
import requests

# blockchain building

class Blockchain:
    def __init__(self): 
        self.chain = []
        self.transactions = []
        self.create_block(proof=1,previous_hash='0')
        self.nodes = set()
        
    def add_node(self,address,):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code==200:
                length = response.json()['length']
                chain = response.json()['chain']
                
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
                    
            if longest_chain:
                self.chain = longest_chain
                return True
            return False
    
    
    def create_block(self, proof, previous_hash):
        block = {'index':len(self.chain)+1,
                 'timestamp':str(datetime.datetime.now()),
                 'proof':proof,
                 'previous_hash':previous_hash,
                 'transactions':self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    
    
    def add_transactions(self, sender, receiver,amount):
        self.transactions.append({'sender':sender,
                                 'receiver':receiver,
                                 'amount':amount})
        previous_block = self.get_previous_block()
        return previous_block['index']+1
        
        
        
    def get_previous_block(self):
        return self.chain[-1]
        
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()            
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
        
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False

            previous_block = block
            block_index += 1

        return True
   
# mining blockchain

app = Flask(__name__)

#creando una direccion para el nodo del puerto 8000
node_address = str(uuid4()).replace('-','')

blockchain = Blockchain()

# mining new block

@app.route ('/mine_block', methods=['GET'])

def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactions(sender=node_address, receiver='Rol',amount=1)
    block = blockchain.create_block(proof,previous_hash)
    response = {'message':'Congratulations,you were able to mine a block',
               'index':block['index'],
               'timestamp':block['timestamp'],
               'proof':block['proof'],
               'previous_hash':block['previous_hash'],
               'transactions':block['transactions']}
    return jsonify(response), 200

# get full string

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain':blockchain.chain,
                'length':len(blockchain.chain)}
    return jsonify(response), 200

#checking the validity of the chain of blocks
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message':'Everything is fine, the block is valid '}
    else:
        response = {'message':'we have a problem, the block is not valid' }
    return jsonify(response),200



#agregamos nueva transaccion blockchain
@app.route('/add_transactions', methods=['POST'])

def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','receiver','amount']
    if not all(key in json for key in transaction_keys):
        return 'algun elemento de la transaccion esta fallando', 400
    
    index=blockchain.add_transactions(json['sender'], json['receiver'], json['amount'])
    response = {'message':f'La transaccion sera añadida al bloque {index} '}
    return jsonify(response), 201

#conectando los nodos

@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 401
    for node in nodes:
        blockchain.add_node(node)
    response = {'message':'Todos los nodos estan conectados. El titicoin contiene nos siguientes nodos: ',
                    'total_nodes':list(blockchain.nodes)}
    return jsonify(response),201
    
# remplazando la cadena por la cadena mas larga
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_replace_chain = blockchain.replace_chain()
    if is_replace_chain:
        response = {'message':'Los nodos tenian diferente cadena asi que la cadena fue remplazada por la mas larga',
                    'new_chain':blockchain.chain}
    else:
        response = {'message':'Todo en orden, la cadena es la mas larga',
                    'actual_chain':blockchain.chain}
    return jsonify(response),200

# running the app   
app.run('127.0.0.1',port ='8000')


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    