import os
import send2trash
import sys

def debug_delete():
    # Create a dummy file in the current directory
    filename = "debug_trash_test.txt"
    with open(filename, "w") as f:
        f.write("This is a test file for the recycle bin.")
    
    abs_path = os.path.abspath(filename)
    norm_path = os.path.normpath(abs_path)
    
    print(f"Created file: {abs_path}")
    print(f"Normalized path: {norm_path}")
    
    try:
        print("Attempting to send to trash...")
        send2trash.send2trash(norm_path)
        print("Success! Check your Recycle Bin.")
        
        if os.path.exists(norm_path):
            print("ERROR: File still exists!")
        else:
            print("File removed from folder.")
            
    except Exception as e:
        print(f"FAILED with error: {e}")

if __name__ == "__main__":
    debug_delete()
