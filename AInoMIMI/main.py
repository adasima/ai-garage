import sys
import os
from modules.pipeline import Pipeline

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <audio_file_path>")
        return

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        return

    print(f"--- Music Analysis Pipeline: Starting Phase 1 ---")
    pipeline = Pipeline()
    
    try:
        def logger(msg):
            print(f"[LOG] {msg}")

        out_dir = pipeline.run_phase1(input_path, logger)
        print(f"--- Phase 1 Complete ---")
        print(f"Output saved to: {out_dir}")
        
    except Exception as e:
        print(f"Fatal Error during execution: {e}")

if __name__ == "__main__":
    main()
