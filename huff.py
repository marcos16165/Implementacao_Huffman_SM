#!/usr/bin/env python3
from collections import Counter, namedtuple, deque
from queue import PriorityQueue
from struct import pack, unpack, calcsize
from json import dumps, loads
from sys import argv
import sys

SMH = namedtuple('SMH', ['magic', 'padding', 'codebook_size', 'codebook_data', 'data'])
Huff = namedtuple('Huff', ['padding', 'codebook', 'data'])

#---------------------------------------------MENU---------------------------------------------

def menu():
    msg = """Compressão de Huffman – Análise de frequência símbolos e compressão de Huffman

Uso: huff [-options] <file>

Opções:

-h         Mostra este texto de ajuda
-c         Realiza a compressão
-d         Realiza a descompressão
-s         Realiza apenas a análise de frequência e imprime a tabela de símbolos
-f <file>  Indica o arquivo a ser processado (comprimido, descomprimido ou
           para apresentar a tabela de símbolos)
"""
    print(msg)
#----------------------------------------------------------------------------------------------


"""
Contagem de símbolos
"""
def frequencia(c=0,filename='exemplo.txt'):
    freq = Counter('')
    with open(filename, "rb") as file:
        freq.update(file.read())
    return freq

"""
Formação da árvore
"""
def arvore(freq):
    pq = PriorityQueue()
    for k, v in freq.items():
        pq.put([v,[[k, '']]])
    return pq

#    while not pq.empty():
#        item = pq.get()
#        print(item)

"""
Geração do codebook
"""

def codebook(arvore):
    pq = PriorityQueue()
    for item in arvore.queue:
        pq.put(item)
    while len(pq.queue) > 1:
        left = pq.get_nowait()
        right = pq.get_nowait()
        for sym in left[1:]:
            for code in sym:
                code[1] = '0' + code[1]
        for sym in right[1:]:
            for code in sym:
                code[1] = '1' + code[1]
        node = [ left[0] + right[0] ,  left[1] + right[1] ]
        print(node)
        pq.put(node)
    codes = {}
    for code in pq.queue[0][1]:
        codes[code[0]] = code[1]
    return codes

"""
Econde
"""
def encode(f, codebook):
    coded = ''
    with open(f, 'rb') as source_file:
        for sym in source_file.read():
 #           print(f"Lido {repr(sym)}")
 #           print(f"Codfificado {codebook[sym]}")
            coded += codebook[sym]
#            print(f"Armazenado {coded}")
    padding = 8 - len(coded) % 8
    for _ in range(padding):
        coded += '0'
    cb = codebook.copy()
    huff = Huff(padding, cb, coded)
    return huff


def save_compressed_to_file(encoded, filename='exemplo.txt.huff', magic="SMH1"):
    mime_magic = bytearray(magic.encode())                 # HEADER mime magic
    padding = pack('<B',encoded.padding)                   # HEADER padding
    codebook = bytearray(dumps(encoded.codebook).encode()) # HEADER coodebook
    codebook_size = pack('<H',len(codebook))           # HEADER codebook size

    bits_sequence = list(encoded.data)
    data_to_write = bytearray()                       # Compressed Data to File
    while (bits_sequence):
        read_byte_string = ''.join(bits_sequence[:8])
        byte_to_write = int(read_byte_string, 2)
        data_to_write.append(byte_to_write)
        bits_sequence = bits_sequence[8:]

    with open(filename, 'wb') as fp:
        fp.write(mime_magic)
        fp.write(padding)
        fp.write(codebook_size)
        fp.write(codebook)
        fp.write(data_to_write)

# encoded é a tupla retornada por encode()
# escrever HEADER + DATA
# formato de HEADER
# Byte Order: Little-endian
#       +------------+----------+---------------+-----------------+----------+
# field | mime magic | padding  | codebook size |    coodebook    |   data   |
# ------+------------+----------+---------------+-----------------+----------+
# value |    SMH1    |  0 - 7   |   0 - 65531   | serialized data |  data    |
# size  |   4 bytes  |  1 byte  |    2 bytes    |    variable     | variable |
#       +------------+----------+---------------+-----------------+----------+
# Ctype |  unsigned  | unsigned |   unsigned    |      JSON       | unsigned |
#       |    char    |   char   |     short     |    RFC 7159     |   char   |
#       +------------+----------+---------------+-----------------+----------+

def read_compressed_from_file(filename='exemplo.txt.huff'):
    with open(filename, 'rb') as fp:
        mime_magic = str(fp.read(4))[2:][:-1]        # HEADER mime magic
        padding = int(unpack('<B',fp.read(1))[0])    # HEADER padding
        codebook_size = unpack('<H',fp.read(2))[0]   # HEADER codebook size
        file_codebook = loads(fp.read(codebook_size))
        codebook = {}
        for k,v in file_codebook.items():
            codebook[int(k)] = v
        data = ''
        for octets in fp.read():
            data = data + f"{octets:08b}"
        coded = Huff(padding, codebook, data)
        return coded

"""
Decode
"""
def decode(coded):
    pad = coded.padding
    codebook = coded.codebook
    data_sequence = deque(coded.data[:-pad])
    data_decoded = []

    read_code = ''
    while (data_sequence):
        read_code += data_sequence.popleft()
#        print(f"Buscando Valor lido {read_code}")
        for codigo_huffman in coded[1].items():
            if read_code in codigo_huffman:
                print(f"Valor encontrado: {read_code} -> \
                    {codigo_huffman[0]} -> {chr(codigo_huffman[0])}")
                data_decoded.append(codigo_huffman[0])
                read_code = ''
                break
    return data_decoded


def maina():
    filename = argv[2]
    freq = frequencia(filename)
    ar = arvore(freq)
    cb = codebook(ar)
    coded = encode(filename, cb)
    save_compressed_to_file(coded, filename='exemplo.txt.huff', magic="SMH1")
    para_decodificar = read_compressed_from_file()
    decodificado = decode(para_decodificar)
    filename_decodificado = filename + '.decodificado'
    with open(filename_decodificado, 'wb') as fp:
        fp.write(bytearray(decodificado))
    print("Fim")


#---------------------------------------------MAIN---------------------------------------------
def main():

    if len(argv) == 1 or '-h' in argv:
        menu()

    elif argv[1] == '-f':
        arq=open(argv[2],'r')
        arquivo=open('exemplo.txt','w')
        arquivo.writelines(arq)
        print("Arquivo {} selecionado.".format(argv[2]))

    if argv[1] == '-c':
        ff=frequencia('exemplo.txt')
        ar=arvore(ff)
        cc=codebook(ar)
        comprimido=encode('exemplo.txt',cc)
        save_compressed_to_file(comprimido, filename="comp.txt.huff")

    elif argv[1] == '-d':
        final = read_compressed_from_file('exemplo.txt')
        fdv=decode(final)
        arquivo=open("descomprimido.txt","w")
        for i in range(len(fdv)):
            arquivo.writelines(chr(fdv[i]))
        arquivo.close()
        
    elif argv[1] == '-s':
        print(frequencia('exemplo.txt'))


if __name__ == '__main__':
    main()

