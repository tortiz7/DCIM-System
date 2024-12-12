# dev/coordinator/main.py
import time
import logging
from shared.workflow_coordinator import WorkflowCoordinator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    coordinator = WorkflowCoordinator()
    
    while True:
        try:
            logging.info("Starting workflow coordination cycle...")
            result = coordinator.run_workflow()
            
            if result.get("status") == "failed":
                logging.error("Workflow failed: %s", result.get("error"))
            else:
                logging.info("Workflow cycle completed successfully")
                
        except Exception as e:
            logging.error("Unexpected error in workflow coordination: %s", str(e))
            
        time.sleep(300)  # Run every 5 minutes

if __name__ == "__main__":
    main()