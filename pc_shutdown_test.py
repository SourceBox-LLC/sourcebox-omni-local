import os

def shutdown_pc() :
    """
    Shut down the Windows PC.
    """
    print("Shutting down PC...")
    os.system("shutdown /s")

if __name__ == "__main__":
    shutdown_pc()