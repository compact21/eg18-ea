import logging

def generateUnlockKey(sn):
    salt = "$1${0}$".format(sn)
    c = crypt("SH_adb_quectel", salt)
    return c[12:27]

def main():
    key = input("Enter the AT+QADBKEY? response: ")
    c = generateUnlockKey(key)
    print('AT+QADBKEY="{0}"'.format(c))

if __name__ == "__main__":
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.ERROR)
    try:
        from crypt import crypt
        main()
    except ImportError as e:
        logging.error(e)
